# GPU Integration Quick Start

## 5-Minute Integration Guide

### Step 1: Import the Wrapper
```python
# In app/routers/sessions.py or wherever you process audio
from app.services.gpu_pipeline_wrapper import transcribe_audio_file
```

### Step 2: Use It (Replace Existing CPU Calls)
```python
# OLD (CPU only):
from app.services.transcription import transcribe_audio_file
result = await transcribe_audio_file(audio_path)

# NEW (GPU/CPU auto-select):
from app.services.gpu_pipeline_wrapper import transcribe_audio_file
result = await transcribe_audio_file(audio_path)  # Same API!
```

### Step 3: Add Shutdown Hook
```python
# In app/main.py
from app.services.gpu_pipeline_wrapper import shutdown_gpu_executor

@app.on_event("shutdown")
async def shutdown_event():
    await shutdown_gpu_executor()
```

### Step 4: Configure Environment
```bash
# For CPU-only deployment (default)
USE_GPU_PIPELINE=false

# For GPU deployment
USE_GPU_PIPELINE=true
```

**That's it!** The wrapper handles everything else automatically.

---

## Quick API Reference

### Primary Function
```python
async def transcribe_audio_file(audio_path: str, force_cpu: bool = False) -> Dict
```

**Automatic behavior:**
- If `USE_GPU_PIPELINE=false` → Uses CPU
- If `USE_GPU_PIPELINE=true` → Tries GPU, falls back to CPU on error
- If `force_cpu=True` → Always uses CPU (useful for testing)

**Returns:**
```python
{
    "full_text": str,              # Complete transcription
    "segments": List[Dict],        # Timestamped segments
    "aligned_segments": List[Dict],# Speaker-labeled segments (GPU only)
    "language": str,               # Detected language
    "duration": float,             # Audio duration (seconds)
    "speaker_turns": List[Dict],   # Speaker turns (GPU only)
    "provider": str,               # GPU provider (GPU only)
    "performance_metrics": Dict    # Performance stats (GPU only)
}
```

---

## Deployment Checklist

### CPU-Only Deployment
- [x] Set `USE_GPU_PIPELINE=false` in `.env`
- [x] Start server: `uvicorn app.main:app --reload`
- [x] Done! No GPU dependencies needed

### GPU Deployment (Vast.ai/RunPod)
- [ ] Provision GPU instance (NVIDIA L4, 8GB VRAM recommended)
- [ ] Install GPU dependencies: `pip install -r audio-transcription-pipeline/requirements.txt`
- [ ] Verify CUDA: `python -c "import torch; print(torch.cuda.is_available())"` → Should print `True`
- [ ] Set `USE_GPU_PIPELINE=true` in `.env`
- [ ] Start server: `uvicorn app.main:app --workers 1` ← **IMPORTANT: --workers 1**
- [ ] Monitor logs: `grep "GPU" logs/app.log`

---

## Verification Commands

### Check GPU availability
```python
from app.services.gpu_pipeline_wrapper import is_gpu_available
print(is_gpu_available())  # True if GPU ready, False otherwise
```

### Test CPU fallback
```python
# Force CPU to verify fallback works
result = await transcribe_audio_file("test.mp3", force_cpu=True)
```

### Monitor GPU usage
```bash
# Watch GPU memory logs
tail -f logs/app.log | grep "GPU Memory"

# Check NVIDIA GPU stats
nvidia-smi
```

---

## Common Issues

### Issue: "CUDA not available"
**Cause:** No GPU or CUDA drivers not installed
**Solution:** Set `USE_GPU_PIPELINE=false` or install CUDA drivers

### Issue: "CUDA out of memory"
**Cause:** Insufficient VRAM
**Solution:** Use smaller Whisper model or set `USE_GPU_PIPELINE=false`

### Issue: Tests failing
**Cause:** Import path incorrect
**Solution:** Verify `from app.services.gpu_pipeline_wrapper import transcribe_audio_file`

---

## Performance Expectations

| Deployment | 60s Audio | Throughput | Cost/1000 Sessions |
|------------|-----------|------------|-------------------|
| **CPU (API)** | 60-120s | High (parallel) | $360 |
| **GPU (L4)** | 2-6s | Sequential | $0.80 |
| **Speedup** | **10-30x** | - | **99.8% savings** |

---

## For More Details

- **Complete docs:** `GPU_INTEGRATION.md`
- **Integration report:** `INTEGRATION_REPORT.md`
- **Tests:** `tests/test_gpu_integration.py`
- **Code:** `gpu_pipeline_wrapper.py`

---

## Support

**GPU not working?**
1. Check logs: `grep "GPU" logs/app.log`
2. Verify CUDA: `python -c "import torch; print(torch.cuda.is_available())"`
3. Force CPU: `USE_GPU_PIPELINE=false`

**Questions?**
- Read: `GPU_INTEGRATION.md` (600+ lines of docs)
- Test: `pytest tests/test_gpu_integration.py -v`
