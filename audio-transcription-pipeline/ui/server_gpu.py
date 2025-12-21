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

        # Parse SSH connection details from Vast.ai API
        # Note: vastai ssh-url returns direct IP, we need the proxy details instead
        # Use Vast.ai REST API to get correct ssh_host and ssh_port
        ssh_host = None
        ssh_port = None

        try:
            import requests
            api_url = f"https://console.vast.ai/api/v0/instances/{VAST_INSTANCE_ID}/"
            headers = {"Authorization": f"Bearer {VAST_API_KEY}"}
            response = requests.get(api_url, headers=headers, timeout=5)
            if response.status_code == 200:
                instance_data = response.json().get("instances", {})
                ssh_host = instance_data.get("ssh_host", "ssh1.vast.ai")
                api_port = instance_data.get("ssh_port")

                # IMPORTANT: Vast.ai API returns port N, but working proxy port is N+1
                # This appears to be a quirk of Vast.ai's proxy routing
                if api_port:
                    ssh_port = str(int(api_port) + 1)
                    print(f"[Vast.ai] Using proxy: {ssh_host}:{ssh_port} (API returned {api_port}, using +1)")
        except Exception as e:
            print(f"[Vast.ai] API error: {e}, falling back to environment check")

        if not ssh_host or not ssh_port:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = f"Could not get SSH details for Vast.ai instance. API response: {result.stdout}"
            return

        jobs[job_id]["progress"] = 20
        jobs[job_id]["step"] = f"Uploading to Vast.ai ({ssh_host}:{ssh_port})"

        # Upload audio file via SCP
        # NOTE: Do NOT use -i flag - Vast.ai proxy requires default SSH config
        upload_cmd = [
            "scp",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-P", ssh_port,
            str(audio_path),
            f"root@{ssh_host}:/root/audio_input.mp3"
        ]

        print(f"[Vast.ai] Uploading audio to instance...")
        print(f"[Vast.ai] Upload command: {' '.join(upload_cmd)}")

        jobs[job_id]["progress"] = 30
        jobs[job_id]["step"] = "Transferring audio file to GPU instance"

        # Retry logic for SSH connection (handles rate limiting)
        max_retries = 3
        retry_delay = 2  # seconds
        upload_success = False

        for attempt in range(max_retries):
            if attempt > 0:
                print(f"[Vast.ai] Retry attempt {attempt + 1}/{max_retries} after {retry_delay}s...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

            upload_process = await asyncio.create_subprocess_exec(
                *upload_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await upload_process.communicate()

            if upload_process.returncode == 0:
                upload_success = True
                break
            else:
                error_msg = stderr.decode()
                print(f"[Vast.ai] Upload attempt {attempt + 1} failed: {error_msg[:200]}")

                # Check if it's a rate limit error
                if "Permission denied (publickey)" in error_msg or "Connection closed" in error_msg:
                    continue  # Retry
                else:
                    break  # Different error, don't retry

        if not upload_success:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = f"Failed to upload audio after {max_retries} attempts: {stderr.decode()}"
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

# Clear pip cache to avoid version conflicts
echo "Purging pip cache..."
pip cache purge 2>/dev/null || true

# Install NVIDIA CUDA libraries FIRST (required by PyTorch)
echo "==> [STEP 1/5] Installing CUDA libraries (cuDNN 9)..."
pip install --no-cache-dir nvidia-cublas-cu12 nvidia-cudnn-cu12==9.*
echo "✓ CUDA libraries installed"

# Set library path for cuDNN 9 (with error handling)
echo "==> [STEP 2/5] Setting CUDA library path..."
export LD_LIBRARY_PATH=$(python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))' 2>/dev/null || echo "/usr/local/lib/python3.12/dist-packages/nvidia/cudnn/lib:/usr/local/lib/python3.12/dist-packages/nvidia/cublas/lib")
echo "✓ LD_LIBRARY_PATH=$LD_LIBRARY_PATH"

# Install pyannote.audio 4.x (will install PyTorch 2.8.0 as dependency)
echo "==> [STEP 3/6] Installing pyannote.audio 4.x with PyTorch 2.8.0..."
pip install --no-cache-dir --upgrade "pyannote.audio>=4.0.0"
echo "✓ pyannote.audio installed"

# Install torchvision compatible with PyTorch 2.8.0
echo "==> [STEP 4/6] Installing torchvision 0.21.0 (compatible with PyTorch 2.8.0)..."
pip install --no-cache-dir torchvision==0.21.0
echo "✓ torchvision 0.21.0 installed"

# Install faster-whisper (compatible with PyTorch 2.8.0)
echo "==> [STEP 5/6] Installing faster-whisper..."
pip install --no-cache-dir faster-whisper>=1.2.0
echo "✓ faster-whisper installed"

# Install additional dependencies
echo "==> [STEP 6/6] Installing additional dependencies (pydub, julius, python-dotenv)..."
pip install --no-cache-dir pydub julius python-dotenv
echo "✓ All dependencies installed"

# Verify CUDA setup
echo "==> [VERIFICATION] Checking CUDA/cuDNN installation..."
python3 -c "import torch; print(f'✓ PyTorch: {{torch.__version__}}, CUDA: {{torch.cuda.is_available()}}, cuDNN: {{torch.backends.cudnn.version()}}')" || echo "❌ Warning: Could not verify PyTorch"
python3 -c "import ctranslate2; print(f'✓ ctranslate2: {{ctranslate2.__version__}}, CUDA devices: {{ctranslate2.get_cuda_device_count()}}')" || echo "❌ Warning: Could not verify ctranslate2"
echo ""

echo "==> [ENVIRONMENT] Setting up HuggingFace token..."
export HF_TOKEN={os.getenv('HF_TOKEN', '')}
echo "✓ HF_TOKEN configured (length: ${{#HF_TOKEN}})"
echo ""

echo "============================================================"
echo "==> [PIPELINE] Starting GPU transcription pipeline..."
echo "============================================================"
python3 << 'EOF'
import os
import json
import sys
from pathlib import Path

# Enable detailed logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("==> [INIT] Initializing pipeline modules...")
sys.path.insert(0, 'src')

from pipeline_gpu import GPUTranscriptionPipeline

print("==> [INIT] Creating GPUTranscriptionPipeline (model: large-v3)...")
with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
    print("==> [PROCESSING] Starting audio processing...")
    print("    - Input: /root/audio_input.mp3")
    print("    - Speakers: {num_speakers}")
    print("    - Language: en")
    print("    - Diarization: enabled")
    print("")

    results = pipeline.process(
        audio_path="/root/audio_input.mp3",
        num_speakers={num_speakers},
        language="en",
        enable_diarization=True
    )

    print("")
    print("==> [OUTPUT] Writing results to /root/results.json...")

with open('/root/results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

print("✓ Processing complete!")
print("✓ Results saved to /root/results.json")
EOF

echo ""
echo "============================================================"
echo "✓ GPU pipeline execution finished"
echo "============================================================"
"""

        # Save script locally
        script_path = TEMP_DIR / f"{job_id}_remote.sh"
        script_path.write_text(remote_script)

        # Upload script
        script_upload_cmd = [
            "scp",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
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
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
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

        # Read stderr (print ALL errors/warnings)
        stderr_lines = []
        while True:
            line = await process.stderr.readline()
            if not line:
                break
            line_str = line.decode().strip()
            stderr_lines.append(line_str)
            # Print ALL stderr output for maximum visibility
            if line_str:
                print(f"[Vast.ai STDERR] {line_str}")

        # Wait for process to complete
        await process.wait()

        # Join for error checking
        stdout = '\n'.join(stdout_lines)
        stderr = '\n'.join(stderr_lines)

        if process.returncode != 0:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = f"Remote execution failed (exit code {process.returncode}): {stderr}"
            print(f"[Vast.ai] ❌ FAILED (exit code {process.returncode})")
            print(f"[Vast.ai] Full stderr output:")
            print(stderr)
            return

        jobs[job_id]["progress"] = 95
        jobs[job_id]["step"] = "Downloading results from GPU instance"

        # Download results
        output_file = RESULTS_DIR / f"{job_id}.json"
        download_cmd = [
            "scp",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-P", ssh_port,
            f"root@{ssh_host}:/root/results.json",
            str(output_file)
        ]

        print(f"[Vast.ai] Downloading results from {ssh_host}:{ssh_port}...")
        download_process = await asyncio.create_subprocess_exec(
            *download_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        download_stdout, download_stderr = await download_process.communicate()

        if download_process.returncode != 0:
            print(f"[Vast.ai] ❌ Download failed (exit code {download_process.returncode})")
            print(f"[Vast.ai] Download stderr: {download_stderr.decode()}")

        if output_file.exists():
            file_size = output_file.stat().st_size
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["step"] = "Processing complete"
            jobs[job_id]["output_file"] = str(output_file)
            print(f"[Vast.ai] ✓ Completed successfully!")
            print(f"[Vast.ai] Results saved: {output_file} ({file_size} bytes)")
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["error"] = f"Could not download results from Vast.ai (download exit code: {download_process.returncode})"
            print(f"[Vast.ai] ❌ Results file not found after download: {output_file}")

        # Cleanup remote files
        cleanup_cmd = [
            "ssh",
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
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