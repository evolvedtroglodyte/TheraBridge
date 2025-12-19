# GPU Memory Management - Quick Reference Card

## 🎯 Best Practice: Always Use Context Manager

```python
# ✅ RECOMMENDED - Automatic cleanup guaranteed
with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
    result = pipeline.process("audio.mp3")
```

## 📊 Memory Logging Checkpoints: 19 Total

### Pipeline Flow
1. **Pipeline Initialization** - Starting baseline
2. **Before Audio Preprocessing** → 3. **After Audio Preprocessing**
4. **Before Transcription** → 5. **After Transcription (post-cleanup)**
6. **Before Diarization** → 7. **After Diarization (post-cleanup)**
8. **Before Speaker Alignment** → 9. **After Speaker Alignment (post-cleanup)**
10. **Before Final Cleanup** → 11. **After Final Cleanup**

### Cleanup Operations (8 additional checkpoints)
- Before/After Whisper Cleanup (2)
- Before/After Waveform Cleanup (2)
- Before/After Diarization Model Cleanup (2)
- Before/After Alignment Tensors Cleanup (2)

## ⚠️ Warning Thresholds

| Usage | Level | Action Required |
|-------|-------|-----------------|
| <70% | ✅ Normal | No action needed |
| 70-85% | ⚠️ Notice | Monitor closely |
| >85% | 🚨 Critical | Use smaller model or split files |

## 🔧 GPU Memory by Model Size

| GPU VRAM | Recommended Model | Headroom |
|----------|-------------------|----------|
| 8 GB | `base` or `small` | Tight |
| 12 GB | `medium` | Comfortable |
| 16 GB | `large-v3` | Tight |
| 24 GB+ | `large-v3` | Plenty |

## 📈 Expected Memory Pattern (24GB GPU, large-v3)

```
Init:            0.1 GB  ━━━━━━━━━━━━━━━━━━━━━━━━━
Preprocessing:   0.2 GB  ━━━━━━━━━━━━━━━━━━━━━━━━━
Whisper Loaded:  7.5 GB  ████████━━━━━━━━━━━━━━━━━
After Cleanup:   0.2 GB  ━━━━━━━━━━━━━━━━━━━━━━━━━  ✅ 97% freed
Pyannote Loaded: 5.8 GB  ██████━━━━━━━━━━━━━━━━━━━
After Cleanup:   0.2 GB  ━━━━━━━━━━━━━━━━━━━━━━━━━  ✅ 96% freed
Final:           0.1 GB  ━━━━━━━━━━━━━━━━━━━━━━━━━
```

## 🔍 Verify Cleanup Effectiveness

**Good Cleanup** (>95% memory recovered):
```
[GPU Memory] Before Whisper Cleanup: Allocated: 7.23GB (30.1%)
[GPU Memory] After Whisper Cleanup:  Allocated: 0.18GB (0.7%)   ✅
```

**Memory Leak** (<50% memory recovered):
```
[GPU Memory] Before Whisper Cleanup: Allocated: 7.23GB (30.1%)
[GPU Memory] After Whisper Cleanup:  Allocated: 5.42GB (22.6%)  ❌
```

## 🚨 Troubleshooting OOM Errors

### 1. Check Current GPU Usage
```bash
nvidia-smi
```

### 2. Use Smaller Model
```python
pipeline = GPUTranscriptionPipeline(whisper_model="medium")  # Instead of large-v3
```

### 3. Monitor Memory in Real-Time
```bash
python src/pipeline_gpu.py audio.mp3 | grep "GPU Memory"
```

### 4. Force Cache Clear Between Files
```python
import torch

for audio_file in files:
    with GPUTranscriptionPipeline() as pipeline:
        result = pipeline.process(audio_file)
    torch.cuda.empty_cache()  # Extra cleanup
```

## 💡 Common Patterns

### Sequential Processing (Multiple Files)
```python
# ✅ Correct - cleanup between files
for audio_file in audio_files:
    with GPUTranscriptionPipeline() as pipeline:
        result = pipeline.process(audio_file)
    # Automatic cleanup before next iteration
```

### Error Handling
```python
# ✅ Correct - cleanup even on error
try:
    with GPUTranscriptionPipeline() as pipeline:
        result = pipeline.process("audio.mp3")
except RuntimeError as e:
    if "out of memory" in str(e):
        print("OOM - try smaller model")
    # Cleanup automatic via context manager
```

### Manual Cleanup (Not Recommended)
```python
# ⚠️ Use only if context manager not possible
pipeline = GPUTranscriptionPipeline()
try:
    result = pipeline.process("audio.mp3")
finally:
    pipeline.cleanup_models()  # Must be in finally block
```

## 📋 Memory Log Parsing

### Extract memory timeline
```bash
grep "GPU Memory" performance_log.txt | awk '{print $4, $6}'
```

### Find peak usage
```bash
grep "GPU Memory" performance_log.txt | awk '{print $6}' | sort -n | tail -1
```

### Verify all cleanups succeeded
```bash
grep "After.*Cleanup" performance_log.txt
```

## 📖 Full Documentation

- **Complete Guide**: `GPU_MEMORY_MONITORING_GUIDE.md` (detailed troubleshooting, best practices)
- **Wave 5 Changes**: `WAVE5_GPU_MEMORY_IMPROVEMENTS.md` (technical implementation details)

## 🎓 Key Takeaways

1. ✅ **Use context managers** - Guarantees cleanup
2. ✅ **Monitor logs** - Watch for 70%/85% warnings
3. ✅ **Match model to GPU** - Don't use large-v3 on 8GB GPUs
4. ✅ **Verify cleanup** - Should recover 95%+ memory
5. ✅ **Process sequentially** - One file at a time with cleanup between

---

**Quick Check**: Are your memory logs showing >95% recovery after cleanup?
- **Yes** → Everything working correctly ✅
- **No** → Check for external references or restart Python process
