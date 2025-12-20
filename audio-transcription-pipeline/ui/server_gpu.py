#!/usr/bin/env python3
"""
GPU-only FastAPI server for transcription pipeline
Checks GPU availability and refuses to process without GPU
Supports both local GPU and remote Vast.ai instances
"""

import os
import json
import uuid
import asyncio
import subprocess
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import sys

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configuration
UPLOAD_DIR = Path("uploads")
TEMP_DIR = UPLOAD_DIR / "temp"
RESULTS_DIR = UPLOAD_DIR / "results"
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm', '.mp4'}

# Pipeline script path
PIPELINE_SCRIPT = Path(__file__).parent.parent / "src" / "pipeline_gpu.py"

# Vast.ai configuration (from environment or .env)
VAST_INSTANCE_ID = os.getenv("VAST_INSTANCE_ID", "")
VAST_API_KEY = os.getenv("VAST_API_KEY", "")
USE_VAST_AI = bool(VAST_INSTANCE_ID and VAST_API_KEY)

# Job storage
jobs: Dict[str, Dict] = {}

# GPU status cache
gpu_status_cache = {
    "checked": False,
    "available": False,
    "type": "none",  # "local", "vast", "none"
    "details": {},
    "last_check": None
}

# Initialize FastAPI
app = FastAPI(
    title="GPU-Only Transcription Pipeline",
    description="Audio transcription with GPU acceleration (no CPU fallback)",
    version="2.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========================================
# Models
# ========================================
class UploadResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: int
    step: str
    error: Optional[str] = None

class GPUStatus(BaseModel):
    available: bool
    type: str  # "local", "vast", "none"
    cuda_available: bool
    cuda_version: Optional[str] = None
    gpu_name: Optional[str] = None
    gpu_memory: Optional[str] = None
    vast_instance: Optional[str] = None
    message: str

# ========================================
# GPU Detection
# ========================================
def check_local_gpu():
    """Check if local GPU is available"""
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        if cuda_available:
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = f"{torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB"
            cuda_version = torch.version.cuda
            return {
                "available": True,
                "cuda_available": True,
                "cuda_version": cuda_version,
                "gpu_name": gpu_name,
                "gpu_memory": gpu_memory
            }
    except ImportError:
        pass
    except Exception as e:
        print(f"GPU check error: {e}")

    return {
        "available": False,
        "cuda_available": False,
        "cuda_version": None,
        "gpu_name": None,
        "gpu_memory": None
    }

def check_vast_connection():
    """Check if Vast.ai instance is available"""
    if not USE_VAST_AI:
        return {"available": False, "instance": None}

    try:
        # Check if vastai CLI is available
        result = subprocess.run(
            ["vastai", "show", "instances"],
            capture_output=True,
            text=True,
            timeout=5,
            env={**os.environ, "VAST_API_KEY": VAST_API_KEY}
        )

        if result.returncode == 0 and VAST_INSTANCE_ID in result.stdout:
            # Parse instance info
            for line in result.stdout.split('\n'):
                if line.startswith(VAST_INSTANCE_ID):
                    parts = line.split()
                    if len(parts) > 7:
                        status = parts[7]
                        if status == "running":
                            return {
                                "available": True,
                                "instance": VAST_INSTANCE_ID,
                                "status": status
                            }
            return {"available": False, "instance": VAST_INSTANCE_ID, "error": "Instance not running"}
    except subprocess.TimeoutExpired:
        return {"available": False, "error": "Vast.ai connection timeout"}
    except Exception as e:
        return {"available": False, "error": str(e)}

    return {"available": False, "instance": None}

def get_gpu_status():
    """Get comprehensive GPU status"""
    global gpu_status_cache

    # Check cache (refresh every 30 seconds)
    if gpu_status_cache["checked"]:
        if gpu_status_cache["last_check"]:
            time_since_check = (datetime.now() - gpu_status_cache["last_check"]).seconds
            if time_since_check < 30:
                return gpu_status_cache

    # Check local GPU first
    local_gpu = check_local_gpu()
    if local_gpu["available"]:
        gpu_status_cache.update({
            "checked": True,
            "available": True,
            "type": "local",
            "details": local_gpu,
            "last_check": datetime.now()
        })
        return gpu_status_cache

    # Check Vast.ai connection
    if USE_VAST_AI:
        vast_status = check_vast_connection()
        if vast_status["available"]:
            gpu_status_cache.update({
                "checked": True,
                "available": True,
                "type": "vast",
                "details": {
                    **local_gpu,  # Include local check results
                    "vast": vast_status
                },
                "last_check": datetime.now()
            })
            return gpu_status_cache

    # No GPU available
    gpu_status_cache.update({
        "checked": True,
        "available": False,
        "type": "none",
        "details": {
            **local_gpu,
            "vast": check_vast_connection() if USE_VAST_AI else {"available": False}
        },
        "last_check": datetime.now()
    })
    return gpu_status_cache

# ========================================
# API Endpoints
# ========================================

@app.get("/api/gpu-status", response_model=GPUStatus)
async def get_gpu_status_endpoint():
    """
    Check GPU availability (local or Vast.ai)
    """
    status = get_gpu_status()

    if status["available"]:
        if status["type"] == "local":
            return GPUStatus(
                available=True,
                type="local",
                cuda_available=status["details"]["cuda_available"],
                cuda_version=status["details"]["cuda_version"],
                gpu_name=status["details"]["gpu_name"],
                gpu_memory=status["details"]["gpu_memory"],
                message=f"Local GPU available: {status['details']['gpu_name']}"
            )
        elif status["type"] == "vast":
            return GPUStatus(
                available=True,
                type="vast",
                cuda_available=False,  # Remote GPU
                vast_instance=status["details"]["vast"]["instance"],
                message=f"Vast.ai GPU available: Instance {status['details']['vast']['instance']}"
            )

    # No GPU available
    error_msg = "No GPU available. "
    if not status["details"]["cuda_available"]:
        error_msg += "CUDA not found locally. "
    if USE_VAST_AI and not status["details"]["vast"]["available"]:
        error_msg += f"Vast.ai instance {VAST_INSTANCE_ID} not accessible. "
    elif not USE_VAST_AI:
        error_msg += "Vast.ai not configured (set VAST_INSTANCE_ID and VAST_API_KEY). "

    return GPUStatus(
        available=False,
        type="none",
        cuda_available=False,
        message=error_msg.strip()
    )

@app.post("/api/upload", response_model=UploadResponse)
async def upload_audio(
    file: UploadFile = File(...),
    num_speakers: int = 2,
    background_tasks: BackgroundTasks = None
):
    """
    Upload audio file and start GPU processing (no CPU fallback)
    """
    # Check GPU availability first
    gpu_status = get_gpu_status()
    if not gpu_status["available"]:
        raise HTTPException(
            status_code=503,
            detail="GPU not available. This server requires GPU for processing. " +
                   "Please ensure either local CUDA GPU or Vast.ai instance is available."
        )

    # Validate file
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate job ID and save file
    job_id = str(uuid.uuid4())

    # Ensure directories exist
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Save uploaded file
    temp_path = TEMP_DIR / f"{job_id}{file_ext}"
    content = await file.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
        )

    with open(temp_path, "wb") as f:
        f.write(content)

    # Initialize job
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "step": "Initializing GPU pipeline",
        "created_at": datetime.now().isoformat(),
        "file_path": str(temp_path),
        "num_speakers": num_speakers,
        "gpu_type": gpu_status["type"]
    }

    # Start processing in background
    if gpu_status["type"] == "local":
        background_tasks.add_task(run_local_gpu_pipeline, job_id, temp_path, num_speakers)
    elif gpu_status["type"] == "vast":
        background_tasks.add_task(run_vast_pipeline, job_id, temp_path, num_speakers)

    return UploadResponse(
        job_id=job_id,
        status="queued",
        message=f"File uploaded. Processing on {gpu_status['type']} GPU."
    )

async def run_local_gpu_pipeline(job_id: str, audio_path: Path, num_speakers: int = 2):
    """Run GPU pipeline locally"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["step"] = "Starting local GPU pipeline"

        output_file = RESULTS_DIR / f"{job_id}.json"

        # Run pipeline
        cmd = [
            "python3",
            str(PIPELINE_SCRIPT),
            str(audio_path),
            "--num-speakers", str(num_speakers)
        ]

        print(f"[GPU Pipeline] Running: {' '.join(cmd)}")

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PIPELINE_SCRIPT.parent)
        )

        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Pipeline failed"
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = f"GPU pipeline error: {error_msg}"
            print(f"[GPU Pipeline] Failed: {error_msg}")
            return

        # Look for result file
        result_file = PIPELINE_SCRIPT.parent / "transcription_result.json"
        if result_file.exists():
            # Move to results directory
            import shutil
            shutil.move(str(result_file), str(output_file))

            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["step"] = "Processing complete"
            jobs[job_id]["output_file"] = str(output_file)
            print(f"[GPU Pipeline] Completed: {output_file}")
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = "Result file not generated"

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        print(f"[GPU Pipeline] Exception: {e}")

    finally:
        # Cleanup temp file
        if audio_path.exists():
            audio_path.unlink()

async def run_vast_pipeline(job_id: str, audio_path: Path, num_speakers: int = 2):
    """Run GPU pipeline on Vast.ai instance"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["step"] = f"Connecting to Vast.ai instance {VAST_INSTANCE_ID}"

        # This would need to be implemented based on your Vast.ai setup
        # Could use SSH, API, or other remote execution method

        # For now, return an error indicating implementation needed
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = "Vast.ai pipeline execution not yet implemented. Use local GPU or implement remote execution."

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)

    finally:
        # Cleanup temp file
        if audio_path.exists():
            audio_path.unlink()

@app.get("/api/status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get processing status for a job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress", 0),
        step=job.get("step", ""),
        error=job.get("error")
    )

@app.get("/api/results/{job_id}")
async def get_results(job_id: str):
    """Get processing results"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs[job_id]

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not completed. Status: {job['status']}"
        )

    output_file = Path(job.get("output_file", ""))
    if not output_file.exists():
        raise HTTPException(status_code=404, detail="Result file not found")

    with open(output_file, "r") as f:
        results = json.load(f)

    return results

# ========================================
# Static File Serving
# ========================================

# Serve static files
app.mount("/", StaticFiles(directory=str(Path(__file__).parent), html=True), name="static")

# ========================================
# Startup
# ========================================

@app.on_event("startup")
async def startup_event():
    """Check GPU on startup"""
    print("\n" + "="*60)
    print("GPU-Only Transcription Pipeline Server")
    print("="*60)

    status = get_gpu_status()

    if status["available"]:
        if status["type"] == "local":
            print(f"✓ Local GPU detected: {status['details']['gpu_name']}")
            print(f"  CUDA Version: {status['details']['cuda_version']}")
            print(f"  Memory: {status['details']['gpu_memory']}")
        elif status["type"] == "vast":
            print(f"✓ Vast.ai GPU available: Instance {status['details']['vast']['instance']}")
    else:
        print("✗ WARNING: No GPU available!")
        print("  The server will reject processing requests.")
        if not status["details"]["cuda_available"]:
            print("  - Local CUDA not found")
        if USE_VAST_AI:
            print(f"  - Vast.ai instance {VAST_INSTANCE_ID} not accessible")
        else:
            print("  - Vast.ai not configured (set VAST_INSTANCE_ID and VAST_API_KEY)")

    print("="*60 + "\n")

if __name__ == "__main__":
    import uvicorn

    # Create upload directories
    UPLOAD_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    print("\n" + "="*60)
    print("Starting GPU-Only Transcription Server")
    print("="*60)
    print(f"UI: http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    print(f"GPU Status: http://localhost:8000/api/gpu-status")
    print("="*60 + "\n")

    uvicorn.run(app, host="0.0.0.0", port=8000)