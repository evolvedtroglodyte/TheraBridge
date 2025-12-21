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
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configuration
UPLOAD_DIR = Path(__file__).parent / "uploads"  # Make it absolute
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
                    if len(parts) > 2:
                        status = parts[2]  # Status is at index 2
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

        # Get SSH connection details using vastai ssh-url
        result = subprocess.run(
            ["vastai", "ssh-url", VAST_INSTANCE_ID],
            capture_output=True,
            text=True,
            timeout=5,
            env={**os.environ, "VAST_API_KEY": VAST_API_KEY}
        )

        ssh_host = None
        ssh_port = None

        if result.returncode == 0 and result.stdout.strip():
            # Parse ssh://root@host:port format
            ssh_url = result.stdout.strip()
            if ssh_url.startswith("ssh://"):
                # Extract host and port from ssh://root@host:port
                import re
                match = re.match(r'ssh://root@([^:]+):(\d+)', ssh_url)
                if match:
                    ssh_host = match.group(1)
                    ssh_port = match.group(2)

        if not ssh_host or not ssh_port:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = "Could not get SSH details for Vast.ai instance"
            return

        jobs[job_id]["progress"] = 20
        jobs[job_id]["step"] = f"Uploading to Vast.ai ({ssh_host}:{ssh_port})"

        # Upload audio file via SCP
        upload_cmd = [
            "scp",
            "-i", os.path.expanduser("~/.ssh/id_rsa"),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "IdentitiesOnly=yes",
            "-P", ssh_port,
            str(audio_path),
            f"root@{ssh_host}:/root/audio_input.mp3"
        ]

        print(f"[Vast.ai] Uploading audio to instance...")
        print(f"[Vast.ai] Upload command: {' '.join(upload_cmd)}")

        jobs[job_id]["progress"] = 30
        jobs[job_id]["step"] = "Transferring audio file to GPU instance"

        upload_process = await asyncio.create_subprocess_exec(
            *upload_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await upload_process.communicate()

        if upload_process.returncode != 0:
            print(f"[Vast.ai] Upload failed: {stderr.decode()}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = f"Failed to upload audio: {stderr.decode()}"
            return

        jobs[job_id]["progress"] = 40
        jobs[job_id]["step"] = "Audio uploaded to GPU instance"

        # Create remote processing script
        remote_script = f"""#!/bin/bash
set -e

echo "==> Checking environment..."
if [ ! -d "TheraBridge" ]; then
    echo "==> Cloning repository..."
    git clone -q https://github.com/evolvedtroglodyte/TheraBridge.git
else
    echo "==> Updating repository to latest version..."
    cd TheraBridge
    git fetch origin
    git reset --hard origin/main
    cd ..
fi

cd TheraBridge/audio-transcription-pipeline

echo "==> Installing dependencies with CUDA 12.4 + cuDNN 9 support..."

# Install PyTorch with CUDA 12.4 support FIRST (critical for cuDNN 9 compatibility)
pip install -q torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124

# Install ctranslate2 (requires cuDNN 9, compatible with PyTorch 2.5.1)
pip install -q ctranslate2>=4.6.1

# Install NVIDIA CUDA libraries for cuDNN 9 (REQUIRED)
pip install -q nvidia-cublas-cu12 nvidia-cudnn-cu12==9.*

# Set library path for cuDNN 9
export LD_LIBRARY_PATH=$(python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))')

# Install faster-whisper (will use existing PyTorch and ctranslate2)
pip install -q faster-whisper>=1.2.0

# Install pyannote.audio 4.x (uses 'token=' parameter)
pip install -q pyannote.audio>=4.0.0

# Install additional dependencies
pip install -q pydub julius python-dotenv

# Verify CUDA setup
echo "==> Verifying CUDA/cuDNN installation..."
python3 -c "import torch; print(f'PyTorch: {{torch.__version__}}, CUDA: {{torch.cuda.is_available()}}, cuDNN: {{torch.backends.cudnn.version()}}')" || echo "Warning: Could not verify PyTorch"
python3 -c "import ctranslate2; print(f'ctranslate2: {{ctranslate2.__version__}}, CUDA devices: {{ctranslate2.get_cuda_device_count()}}')" || echo "Warning: Could not verify ctranslate2"

export HF_TOKEN={os.getenv('HF_TOKEN', '')}

echo "==> Processing audio with GPU pipeline..."
python3 << 'EOF'
import os
import json
import sys
from pathlib import Path

sys.path.insert(0, 'src')

from pipeline_gpu import GPUTranscriptionPipeline

with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
    results = pipeline.process(
        audio_path="/root/audio_input.mp3",
        num_speakers={num_speakers},
        language="en",
        enable_diarization=True
    )

with open('/root/results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("Processing complete!")
EOF
"""

        # Save script locally
        script_path = TEMP_DIR / f"{job_id}_remote.sh"
        script_path.write_text(remote_script)

        # Upload script
        script_upload_cmd = [
            "scp",
            "-i", os.path.expanduser("~/.ssh/id_rsa"),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "IdentitiesOnly=yes",
            "-P", ssh_port,
            str(script_path),
            f"root@{ssh_host}:/root/process.sh"
        ]

        script_upload_process = await asyncio.create_subprocess_exec(
            *script_upload_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await script_upload_process.communicate()

        if script_upload_process.returncode != 0:
            print(f"[Vast.ai] Script upload failed: {stderr.decode()}")
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = f"Failed to upload script: {stderr.decode()}"
            return

        jobs[job_id]["progress"] = 50
        jobs[job_id]["step"] = "Starting remote GPU pipeline"

        # Execute script on remote
        ssh_cmd = [
            "ssh",
            "-i", os.path.expanduser("~/.ssh/id_rsa"),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "IdentitiesOnly=yes",
            "-p", ssh_port,
            f"root@{ssh_host}",
            "bash /root/process.sh"
        ]

        print(f"[Vast.ai] Executing pipeline on remote GPU...")
        print(f"[Vast.ai] SSH command: {' '.join(ssh_cmd)}")
        process = await asyncio.create_subprocess_exec(
            *ssh_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Read stdout line-by-line (non-blocking)
        stdout_lines = []
        while True:
            line = await process.stdout.readline()
            if not line:
                break

            line_str = line.decode().strip()
            stdout_lines.append(line_str)
            print(f"[Vast.ai] {line_str}")

            # Parse output for progress indicators
            if "Checking environment" in line_str:
                jobs[job_id]["progress"] = 55
                jobs[job_id]["step"] = "Checking environment on GPU instance"
            elif "Cloning repository" in line_str:
                jobs[job_id]["progress"] = 60
                jobs[job_id]["step"] = "Cloning pipeline repository"
            elif "Installing dependencies" in line_str:
                jobs[job_id]["progress"] = 65
                jobs[job_id]["step"] = "Installing GPU dependencies"
            elif "Processing audio with GPU pipeline" in line_str:
                jobs[job_id]["progress"] = 70
                jobs[job_id]["step"] = "Running GPU transcription pipeline"
            elif "GPU Audio Preprocessing" in line_str:
                jobs[job_id]["progress"] = 75
                jobs[job_id]["step"] = "Preprocessing audio on GPU"
            elif "GPU Transcription" in line_str or "Transcribing" in line_str:
                jobs[job_id]["progress"] = 80
                jobs[job_id]["step"] = "Transcribing with Whisper large-v3"
            elif "GPU Speaker Diarization" in line_str or "Diarization" in line_str:
                jobs[job_id]["progress"] = 85
                jobs[job_id]["step"] = "Running pyannote speaker diarization"
            elif "Speaker Alignment" in line_str or "Aligning" in line_str:
                jobs[job_id]["progress"] = 90
                jobs[job_id]["step"] = "Aligning speakers with transcript"
            elif "Processing complete" in line_str:
                jobs[job_id]["progress"] = 93
                jobs[job_id]["step"] = "GPU processing complete, preparing results"

        # Read stderr
        stderr_lines = []
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            stderr_lines.append(line.decode().strip())

        # Wait for process to complete
        await process.wait()

        # Join for error checking
        stdout = '\n'.join(stdout_lines)
        stderr = '\n'.join(stderr_lines)

        if process.returncode != 0:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = f"Remote execution failed: {stderr}"
            print(f"[Vast.ai] Failed: {stderr}")
            return

        jobs[job_id]["progress"] = 95
        jobs[job_id]["step"] = "Downloading results from GPU instance"

        # Download results
        output_file = RESULTS_DIR / f"{job_id}.json"
        download_cmd = [
            "scp",
            "-i", os.path.expanduser("~/.ssh/id_rsa"),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "IdentitiesOnly=yes",
            "-P", ssh_port,
            f"root@{ssh_host}:/root/results.json",
            str(output_file)
        ]

        download_process = await asyncio.create_subprocess_exec(
            *download_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        await download_process.communicate()

        if output_file.exists():
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["step"] = "Processing complete"
            jobs[job_id]["output_file"] = str(output_file)
            print(f"[Vast.ai] Completed: {output_file}")
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = "Could not download results from Vast.ai"

        # Cleanup remote files
        cleanup_cmd = [
            "ssh",
            "-i", os.path.expanduser("~/.ssh/id_rsa"),
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "IdentitiesOnly=yes",
            "-p", ssh_port,
            f"root@{ssh_host}",
            "rm -f /root/audio_input.mp3 /root/results.json /root/process.sh"
        ]

        await asyncio.create_subprocess_exec(
            *cleanup_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)
        print(f"[Vast.ai] Exception: {e}")

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