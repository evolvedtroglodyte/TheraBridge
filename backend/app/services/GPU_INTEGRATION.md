# GPU Pipeline Integration Documentation

## Overview

The GPU pipeline integration provides async wrappers for the CUDA-accelerated audio transcription pipeline, enabling high-performance transcription for production deployments on GPU infrastructure (Vast.ai, RunPod, Lambda Labs).

## Architecture

```
FastAPI Backend (async)
    ↓
gpu_pipeline_wrapper.py (async wrapper)
    ↓
ThreadPoolExecutor (1 worker)
    ↓
audio-transcription-pipeline/src/pipeline_gpu.py (sync GPU operations)
    ↓
CUDA GPU (PyTorch + faster-whisper + pyannote)
```

## Key Components

### 1. `gpu_pipeline_wrapper.py`
Main integration module providing:
- **`transcribe_audio_file()`** - Primary async API with GPU/CPU auto-selection
- **`async_transcribe_gpu()`** - Async wrapper for GPU pipeline
- **`_sync_transcribe_gpu()`** - Synchronous GPU execution (runs in thread)
- **`is_gpu_available()`** - Runtime GPU availability check
- **`shutdown_gpu_executor()`** - Cleanup on application shutdown

### 2. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_GPU_PIPELINE` | `false` | Enable GPU transcription (requires CUDA) |
| `AUDIO_PIPELINE_DIR` | (auto) | Path to pipeline (optional, auto-detected in monorepo) |

### 3. GPU Selection Logic

```python
# Automatic selection (respects USE_GPU_PIPELINE)
result = await transcribe_audio_file("audio.mp3")

# Force CPU (useful for testing/debugging)
result = await transcribe_audio_file("audio.mp3", force_cpu=True)
```

**Decision tree:**
1. If `force_cpu=True` → Use CPU
2. If `USE_GPU_PIPELINE=true` → Try GPU, fallback to CPU on error
3. If `USE_GPU_PIPELINE=false` → Use CPU only

## Fallback Strategy

GPU transcription automatically falls back to CPU on:

| Error Type | Trigger | Fallback Behavior |
|------------|---------|-------------------|
| `ImportError` | GPU dependencies not installed | Log warning, use CPU |
| `RuntimeError` (CUDA) | CUDA not available / GPU not found | Log warning, use CPU |
| `RuntimeError` (OOM) | GPU out of memory | Log warning, use CPU |
| `Exception` | Any unexpected GPU error | Log error with traceback, use CPU |

**Example fallback log:**
```
WARNING: GPU transcription failed, falling back to CPU: CUDA out of memory (tried to allocate 2.5GB)
INFO: Using CPU transcription
```

## Performance Characteristics

### GPU Transcription (Vast.ai L4 GPU)
- **Speed:** 10-30x real-time (60-second audio in 2-6 seconds)
- **Throughput:** Sequential (1 thread to prevent GPU contention)
- **VRAM:** 4-8GB for Whisper large-v3 + pyannote diarization
- **Cost:** $0.20-0.50/hour on Vast.ai

### CPU Transcription (OpenAI Whisper API)
- **Speed:** ~0.5-1x real-time (60-second audio in 60-120 seconds)
- **Throughput:** Parallel (limited by API rate limits)
- **Memory:** Minimal (API-based)
- **Cost:** $0.006/minute ($0.36/hour for continuous processing)

## Thread Pool Design

### Why Single Thread?
```python
_gpu_executor = ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="gpu_transcription"
)
```

**Rationale:**
1. **GPU contention prevention** - Multiple threads compete for GPU memory
2. **OOM avoidance** - Loading multiple models simultaneously causes out-of-memory
3. **Predictable performance** - Sequential processing ensures consistent latency
4. **Resource efficiency** - GPU is bottleneck, not CPU threads

### Async Execution Flow
```python
async def async_transcribe_gpu(audio_path: str) -> Dict:
    loop = asyncio.get_event_loop()
    executor = _get_gpu_executor()

    # Run GPU operation in thread pool (non-blocking)
    result = await loop.run_in_executor(
        executor,
        _sync_transcribe_gpu,  # Blocking GPU function
        audio_path
    )
    return result
```

**Benefits:**
- FastAPI event loop remains responsive
- Other async requests can process while GPU works
- Proper async/await integration with backend

## GPU Memory Management

### Automatic Cleanup
The GPU pipeline uses context managers for guaranteed cleanup:

```python
with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
    result = pipeline.process(audio_path)
# GPU memory automatically freed here
```

**Cleanup stages:**
1. After transcription: Unload Whisper model
2. After diarization: Unload pyannote model + free waveform tensors
3. After alignment: Free all GPU tensors
4. On pipeline exit: Final cache clear

### Memory Monitoring
The pipeline logs GPU memory at each stage:
```
[GPU Memory] Before Transcription: Allocated: 0.2GB (2.5%) | Free: 7.8GB
[GPU Memory] After Transcription: Allocated: 4.1GB (51.2%) | Free: 3.9GB
[GPU Memory] After Whisper Cleanup: Allocated: 0.3GB (3.8%) | Free: 7.7GB
```

## Error Handling

### GPU-Specific Errors

```python
try:
    result = await async_transcribe_gpu(audio_path)
except RuntimeError as e:
    if "CUDA out of memory" in str(e):
        logger.error("GPU OOM - reduce batch size or use CPU")
    elif "CUDA not available" in str(e):
        logger.error("CUDA drivers not installed or GPU not accessible")
    elif "GPU transcription failed" in str(e):
        logger.error(f"GPU error: {e}")
    raise
```

### Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `CUDA not available: No NVIDIA GPU detected` | No GPU hardware | Use CPU pipeline or deploy to GPU instance |
| `CUDA out of memory` | Insufficient VRAM | Use smaller Whisper model or CPU pipeline |
| `GPU pipeline dependencies not installed` | Missing PyTorch/CUDA | Install GPU requirements |
| `CUDA version mismatch` | PyTorch CUDA vs driver CUDA | Reinstall matching PyTorch version |

## Integration Testing

### Unit Tests (Mock GPU)
```bash
cd backend
pytest tests/test_gpu_integration.py -v
```

**Test coverage:**
- ✅ Pipeline directory resolution (monorepo + env var)
- ✅ GPU availability checks
- ✅ Forced CPU transcription
- ✅ GPU disabled (USE_GPU_PIPELINE=false)
- ✅ GPU fallback on error
- ✅ Executor shutdown
- ✅ Import error handling
- ✅ CUDA error handling

### Integration Tests (Real GPU)
```bash
# Requires GPU hardware and sample audio
USE_GPU_PIPELINE=true pytest tests/test_gpu_integration.py::TestGPUWrapperIntegration -v
```

## Deployment Guide

### Option 1: CPU-Only Deployment (Default)
```bash
# .env configuration
USE_GPU_PIPELINE=false

# Install CPU dependencies only
pip install -r requirements.txt

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Option 2: GPU Deployment (Vast.ai/RunPod)

**Step 1: Provision GPU instance**
```bash
# Vast.ai: NVIDIA L4 (8GB VRAM, $0.20/hour)
# Select image: pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime
```

**Step 2: Install GPU dependencies**
```bash
# Clone monorepo
git clone <repo-url>
cd peerbridge-proj

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install GPU pipeline dependencies
cd ../audio-transcription-pipeline
pip install -r requirements.txt

# Verify CUDA
python -c "import torch; print(torch.cuda.is_available())"  # Should print: True
```

**Step 3: Configure environment**
```bash
# backend/.env
USE_GPU_PIPELINE=true
# AUDIO_PIPELINE_DIR auto-detected (monorepo structure)
```

**Step 4: Start server**
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

**WARNING: Always use --workers 1 with GPU to prevent GPU memory contention**

### Option 3: Separate Backend/Pipeline Deployment

**Backend server (CPU):**
```bash
# backend/.env
USE_GPU_PIPELINE=false
```

**GPU processing server (separate instance):**
```bash
# Deploy audio-transcription-pipeline separately
# Backend calls GPU server via HTTP API (requires custom integration)
```

## Monitoring & Logging

### GPU Utilization Logs
```
INFO: GPU transcription enabled (USE_GPU_PIPELINE=true)
INFO: GPU hardware detected and available
INFO: Starting GPU transcription for: /uploads/audio/session_123.mp3
INFO: GPU transcription successful. Speed: 15.2x real-time, Provider: vast_ai
```

### Performance Metrics
The GPU pipeline returns detailed metrics:
```json
{
  "performance_metrics": {
    "total_duration": 4.2,
    "stages": {
      "GPU Audio Preprocessing": {"duration": 0.3},
      "GPU Transcription": {"duration": 2.1},
      "GPU Speaker Diarization": {"duration": 1.5},
      "Speaker Alignment": {"duration": 0.3}
    }
  }
}
```

### Health Check
```python
from app.services.gpu_pipeline_wrapper import is_gpu_available

if is_gpu_available():
    print("GPU acceleration enabled")
else:
    print("Using CPU transcription")
```

## Cost Analysis

### 1000 Sessions (60 seconds each)

| Method | Processing Time | Cost | Notes |
|--------|----------------|------|-------|
| **GPU (Vast.ai L4)** | 4 hours | $0.80 | Batch processing (15x RT) |
| **CPU (Whisper API)** | 1000 hours | $360 | Parallel processing |
| **Savings** | - | **$359.20** | **99.8% cost reduction** |

**Recommendation:**
- **< 100 sessions/day:** Use CPU (simpler, no GPU management)
- **> 100 sessions/day:** Use GPU (significant cost savings)

## Troubleshooting

### GPU Not Detected
```bash
# Check CUDA installation
nvidia-smi

# Check PyTorch CUDA support
python -c "import torch; print(torch.cuda.is_available())"

# Reinstall PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Out of Memory Errors
```python
# Option 1: Use smaller Whisper model
with GPUTranscriptionPipeline(whisper_model="medium") as pipeline:
    ...

# Option 2: Disable diarization
result = pipeline.process(audio_path, enable_diarization=False)

# Option 3: Fall back to CPU
result = await transcribe_audio_file(audio_path, force_cpu=True)
```

### Import Errors
```bash
# Verify pipeline directory
python -c "from app.services.gpu_pipeline_wrapper import _get_pipeline_directory; print(_get_pipeline_directory())"

# Set explicit path
export AUDIO_PIPELINE_DIR=/path/to/audio-transcription-pipeline
```

## API Reference

### `transcribe_audio_file(audio_path, force_cpu=False)`

**Primary transcription API with automatic GPU/CPU selection.**

**Parameters:**
- `audio_path` (str): Path to audio file
- `force_cpu` (bool): Force CPU transcription (default: False)

**Returns:**
- `Dict`: Transcription results
  - `full_text` (str): Complete transcription
  - `segments` (List[Dict]): Timestamped segments
  - `aligned_segments` (List[Dict]): Speaker-labeled segments (GPU only)
  - `language` (str): Detected language
  - `duration` (float): Audio duration (seconds)
  - `speaker_turns` (List[Dict]): Speaker turns (GPU only)
  - `provider` (str): GPU provider name (GPU only)
  - `performance_metrics` (Dict): Processing stats (GPU only)

**Raises:**
- `RuntimeError`: If transcription fails

**Example:**
```python
# Automatic selection
result = await transcribe_audio_file("/uploads/session.mp3")

# Force CPU
result = await transcribe_audio_file("/uploads/session.mp3", force_cpu=True)
```

---

### `is_gpu_available()`

**Check if GPU is available for transcription.**

**Returns:**
- `bool`: True if GPU available and configured, False otherwise

**Example:**
```python
if is_gpu_available():
    print("GPU acceleration enabled")
```

---

### `shutdown_gpu_executor()`

**Shutdown GPU thread pool executor (cleanup on app shutdown).**

**Example:**
```python
@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_gpu_executor()
```

## Best Practices

### 1. Always Use Context Managers
```python
# ✅ Good - Guarantees cleanup
with GPUTranscriptionPipeline() as pipeline:
    result = pipeline.process(audio_path)

# ❌ Bad - Memory leak risk
pipeline = GPUTranscriptionPipeline()
result = pipeline.process(audio_path)
# cleanup_models() might not be called on exception
```

### 2. Handle GPU Errors Gracefully
```python
try:
    result = await transcribe_audio_file(audio_path)
except RuntimeError as e:
    logger.error(f"Transcription failed: {e}")
    # Notify user, retry with CPU, or queue for later
```

### 3. Monitor GPU Memory
```python
# Enable verbose logging
import logging
logging.getLogger("app.services.gpu_pipeline_wrapper").setLevel(logging.INFO)
```

### 4. Test Both Paths
```python
# Test CPU fallback
await transcribe_audio_file(audio_path, force_cpu=True)

# Test GPU path (if available)
if is_gpu_available():
    await transcribe_audio_file(audio_path)
```

## Future Enhancements

### Potential Improvements
1. **Multi-GPU support** - Distribute workload across multiple GPUs
2. **Batch processing** - Process multiple files in single GPU load
3. **Model caching** - Keep models loaded for subsequent requests
4. **Streaming transcription** - Real-time processing for live sessions
5. **GPU queue management** - Queue requests during peak load

### Performance Optimizations
1. **TensorRT optimization** - Faster inference with TensorRT
2. **Mixed precision** - Use FP16 for 2x speedup on modern GPUs
3. **Persistent models** - Load models once, reuse for all requests
4. **Batch inference** - Process multiple segments simultaneously

## Support

For issues or questions:
1. Check logs: `backend/logs/` and GPU memory warnings
2. Verify GPU availability: `is_gpu_available()`
3. Test CPU fallback: `force_cpu=True`
4. Review GPU pipeline docs: `audio-transcription-pipeline/README.md`
