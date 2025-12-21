#!/usr/bin/env python3
"""
Lightweight FastAPI server for GPU Pipeline Web UI
Bridges the web interface with the GPU transcription pipeline
"""

import os
import json
import uuid
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configuration
UPLOAD_DIR = Path("uploads")
TEMP_DIR = UPLOAD_DIR / "temp"
RESULTS_DIR = UPLOAD_DIR / "results"
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm', '.mp4'}

# Pipeline script path (relative to project root)
PIPELINE_SCRIPT = Path(__file__).parent.parent / "src" / "pipeline_gpu.py"

# Job storage (in-memory for development - use Redis/DB for production)
jobs: Dict[str, Dict] = {}

# Initialize FastAPI
app = FastAPI(
    title="GPU Transcription Pipeline API",
    description="Web API for audio transcription with GPU acceleration",
    version="1.0.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
UPLOAD_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)


# ========================================
# Pydantic Models
# ========================================

class UploadResponse(BaseModel):
    job_id: str
    status: str
    message: str


class StatusResponse(BaseModel):
    job_id: str
    status: str  # queued, processing, completed, failed
    progress: int  # 0-100
    step: str
    error: Optional[str] = None


class ResultsResponse(BaseModel):
    job_id: str
    status: str
    segments: list
    aligned_segments: list
    full_text: str
    language: str
    duration: float
    speaker_turns: list
    provider: str
    performance_metrics: dict


# ========================================
# Helper Functions
# ========================================

def validate_audio_file(filename: str) -> bool:
    """Validate file extension"""
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def cleanup_temp_files(job_id: str):
    """Delete temporary files for a job"""
    temp_path = TEMP_DIR / job_id
    if temp_path.exists():
        import shutil
        shutil.rmtree(temp_path, ignore_errors=True)
        print(f"[Cleanup] Removed temp files for job {job_id}")


async def run_pipeline(job_id: str, audio_path: Path, num_speakers: int = 2):
    """
    Run GPU pipeline as subprocess and track progress
    """
    try:
        # Update job status
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["step"] = "Starting GPU pipeline"

        # Output file path
        output_file = RESULTS_DIR / f"{job_id}.json"

        # Build command
        # Note: Pipeline outputs to its working directory as "transcription_result.json"
        cmd = [
            "python3",
            str(PIPELINE_SCRIPT),
            str(audio_path),
            "--num-speakers", str(num_speakers)
        ]

        print(f"[Pipeline] Running: {' '.join(cmd)}")
        print(f"[Pipeline] Working directory: {PIPELINE_SCRIPT.parent}")

        # Run pipeline in its source directory (so it can import modules)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PIPELINE_SCRIPT.parent)
        )

        # Track progress by monitoring stdout
        stdout_lines = []
        stderr_lines = []

        # Read stdout
        while True:
            line = await process.stdout.readline()
            if not line:
                break

            line_str = line.decode().strip()
            stdout_lines.append(line_str)
            print(f"[Pipeline] {line_str}")

            # Update progress based on pipeline stages
            if "GPU Audio Preprocessing" in line_str:
                jobs[job_id]["progress"] = 25
                jobs[job_id]["step"] = "Preprocessing audio"
            elif "GPU Transcription" in line_str:
                jobs[job_id]["progress"] = 50
                jobs[job_id]["step"] = "Transcribing with Whisper"
            elif "GPU Speaker Diarization" in line_str:
                jobs[job_id]["progress"] = 75
                jobs[job_id]["step"] = "Analyzing speakers"
            elif "Speaker Alignment" in line_str:
                jobs[job_id]["progress"] = 90
                jobs[job_id]["step"] = "Aligning speakers"

        # Read stderr
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            stderr_lines.append(line.decode().strip())

        # Wait for process to complete
        await process.wait()

        # Check if pipeline succeeded
        if process.returncode == 0:
            # Look for transcription_result.json in pipeline's working directory
            default_output = PIPELINE_SCRIPT.parent / "transcription_result.json"
            if default_output.exists():
                # Move to results directory
                import shutil
                shutil.move(str(default_output), str(output_file))

                # Load results
                with open(output_file, 'r') as f:
                    results = json.load(f)

                jobs[job_id]["status"] = "completed"
                jobs[job_id]["progress"] = 100
                jobs[job_id]["step"] = "Complete"
                jobs[job_id]["results"] = results
                jobs[job_id]["output_file"] = str(output_file)

                print(f"[Pipeline] Job {job_id} completed successfully")
            else:
                raise Exception(f"Pipeline did not generate output file at {default_output}")
        else:
            error_msg = "\n".join(stderr_lines[-10:])  # Last 10 lines
            raise Exception(f"Pipeline failed with code {process.returncode}: {error_msg}")

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["step"] = "Failed"
        print(f"[Pipeline] Job {job_id} failed: {str(e)}")

    finally:
        # Cleanup temp files after completion (success or failure)
        cleanup_temp_files(job_id)


# ========================================
# API Endpoints
# ========================================

@app.post("/api/upload", response_model=UploadResponse)
async def upload_audio(
    file: UploadFile = File(...),
    num_speakers: int = 2,
    background_tasks: BackgroundTasks = None
):
    """
    Upload audio file and start processing

    Returns job_id for tracking progress
    """
    # Validate file type
    if not validate_audio_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Validate file size (read in chunks to avoid memory issues)
    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    # Read and save file
    job_id = str(uuid.uuid4())
    job_dir = TEMP_DIR / job_id
    job_dir.mkdir(exist_ok=True)

    audio_path = job_dir / file.filename

    try:
        with open(audio_path, 'wb') as f:
            while chunk := await file.read(chunk_size):
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
                    )
                f.write(chunk)
    except HTTPException:
        # Cleanup on error
        cleanup_temp_files(job_id)
        raise
    except Exception as e:
        cleanup_temp_files(job_id)
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Create job entry
    jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "step": "Queued",
        "filename": file.filename,
        "file_size": file_size,
        "num_speakers": num_speakers,
        "created_at": datetime.now().isoformat(),
        "audio_path": str(audio_path)
    }

    # Start processing in background
    background_tasks.add_task(run_pipeline, job_id, audio_path, num_speakers)

    return UploadResponse(
        job_id=job_id,
        status="queued",
        message=f"File uploaded successfully. Processing started."
    )


@app.get("/api/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """
    Get processing status for a job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    return StatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        step=job.get("step", "Unknown"),
        error=job.get("error")
    )


@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """
    Get transcription results for a completed job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] == "processing" or job["status"] == "queued":
        raise HTTPException(status_code=202, detail="Job still processing")

    if job["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Job failed: {job.get('error', 'Unknown error')}"
        )

    if job["status"] == "completed":
        return job["results"]

    raise HTTPException(status_code=500, detail="Unknown job status")


@app.get("/api/jobs")
async def list_jobs():
    """
    List all jobs (for debugging)
    """
    return {
        "total": len(jobs),
        "jobs": [
            {
                "job_id": job_id,
                "status": job["status"],
                "filename": job.get("filename"),
                "created_at": job.get("created_at")
            }
            for job_id, job in jobs.items()
        ]
    }


@app.delete("/api/jobs/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job and its results
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    # Delete results file
    output_file = RESULTS_DIR / f"{job_id}.json"
    if output_file.exists():
        output_file.unlink()

    # Cleanup temp files
    cleanup_temp_files(job_id)

    # Remove from jobs dict
    del jobs[job_id]

    return {"message": "Job deleted successfully"}


# ========================================
# Static File Serving
# ========================================

# Serve static files from root (CSS, JS, etc.)
# Mount BEFORE the catch-all route, but exclude index.html
app.mount("/", StaticFiles(directory=str(Path(__file__).parent), html=True), name="static")


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "pipeline_script": str(PIPELINE_SCRIPT),
        "pipeline_exists": PIPELINE_SCRIPT.exists(),
        "active_jobs": len([j for j in jobs.values() if j["status"] == "processing"])
    }


# ========================================
# Main Entry Point
# ========================================

if __name__ == "__main__":
    import uvicorn

    print("=" * 60)
    print("GPU Transcription Pipeline Server")
    print("=" * 60)
    print(f"UI: http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    print(f"Pipeline: {PIPELINE_SCRIPT}")
    print(f"Upload Dir: {UPLOAD_DIR.absolute()}")
    print("=" * 60)

    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
