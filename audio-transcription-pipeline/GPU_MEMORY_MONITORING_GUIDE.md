# GPU Memory Monitoring Guide

## Overview

This guide explains how to monitor and optimize GPU memory usage in the audio transcription pipeline to prevent Out-of-Memory (OOM) errors and maximize performance.

## Memory Management Architecture

### Automatic Cleanup (Wave 5 Improvements)

The pipeline implements **automatic memory cleanup** using `try/finally` blocks at critical stages:

1. **Transcription Stage**: Whisper model is automatically unloaded after transcription
2. **Diarization Stage**: Pyannote model and waveform tensors are freed after diarization
3. **Alignment Stage**: All GPU tensors used for speaker alignment are cleaned up
4. **Pipeline Completion**: Final cleanup ensures all models are unloaded

**Key Benefits:**
- Prevents memory leaks between pipeline stages
- Enables sequential processing of multiple files
- Reduces VRAM requirements by not keeping models in memory
- Guarantees cleanup even if errors occur (try/finally pattern)

### Memory Logging Points

The pipeline logs GPU memory usage at **19 strategic checkpoints**:

#### Pipeline Initialization
1. **Pipeline Initialization** - Baseline memory state

#### Audio Preprocessing Stage
2. **Before Audio Preprocessing** - Memory state before GPU audio operations
3. **After Audio Preprocessing** - Memory after audio processing completes

#### Transcription Stage
4. **Before Transcription** - Memory before loading Whisper model
5. **Before Whisper Cleanup** - Memory state with Whisper model loaded
6. **After Whisper Cleanup** - Memory after Whisper model unloaded
7. **After Transcription (post-cleanup)** - Final transcription stage memory

#### Diarization Stage (if enabled)
8. **Before Diarization** - Memory before loading pyannote model
9. **Before Waveform Cleanup** - Memory with waveform tensor loaded
10. **After Waveform Cleanup** - Memory after waveform freed
11. **Before Diarization Model Cleanup** - Memory with pyannote model loaded
12. **After Diarization Model Cleanup** - Memory after pyannote unloaded
13. **After Diarization (post-cleanup)** - Final diarization stage memory

#### Speaker Alignment Stage (if diarization enabled)
14. **Before Speaker Alignment** - Memory before creating alignment tensors
15. **Before Alignment Tensors Cleanup** - Memory with alignment tensors loaded
16. **After Alignment Tensors Cleanup** - Memory after tensors freed
17. **After Speaker Alignment (post-cleanup)** - Final alignment stage memory

#### Final Cleanup
18. **Before Final Cleanup** - Memory state before final cleanup
19. **After Final Cleanup** - Final memory state after all cleanup

## Log Output Format

Each memory checkpoint logs:

```
[GPU Memory] <Stage Name>: Allocated: X.XXgb (XX.X%) | Reserved: X.XXgb (XX.X%) | Free: X.XXgb | Total: X.XXgb
```

**Field Definitions:**
- **Allocated**: GPU memory currently in use by PyTorch tensors
- **Reserved**: GPU memory reserved by PyTorch's caching allocator (includes allocated + cache)
- **Free**: Available VRAM for new allocations
- **Total**: Total GPU VRAM capacity
- **Percentages**: Allocated/Reserved as % of total VRAM

## Memory Usage Warnings

The pipeline provides automatic warnings based on memory pressure:

### Critical Warning (>85% allocated)
```
WARNING: GPU memory usage is critically high (XX.X%). Consider reducing batch size or using a smaller model.
```

**Actions to take:**
- Switch to a smaller Whisper model (`medium` instead of `large-v3`)
- Process shorter audio files (split long files into chunks)
- Ensure no other GPU processes are running
- Consider using a GPU with more VRAM

### Elevated Warning (>70% allocated)
```
NOTICE: GPU memory usage is elevated (XX.X%). Monitor for potential OOM conditions.
```

**Actions to take:**
- Monitor subsequent stages carefully
- Be prepared to restart if OOM occurs
- Consider preventive measures for future runs

## Expected Memory Usage Patterns

### Typical Memory Profile (24GB GPU, large-v3 model)

| Stage | Allocated | Reserved | Notes |
|-------|-----------|----------|-------|
| Pipeline Init | ~0.1 GB | ~0.5 GB | Minimal baseline |
| Audio Preprocessing | ~0.2 GB | ~0.7 GB | Small tensors for audio |
| Before Transcription | ~0.2 GB | ~0.7 GB | Clean slate |
| Whisper Loaded | ~6-8 GB | ~8-10 GB | Large transformer model |
| After Whisper Cleanup | ~0.2 GB | ~1.0 GB | Memory reclaimed |
| Before Diarization | ~0.2 GB | ~1.0 GB | Clean slate |
| Pyannote Loaded | ~4-6 GB | ~6-8 GB | Diarization model |
| After Diarization Cleanup | ~0.2 GB | ~1.5 GB | Memory reclaimed |
| Speaker Alignment | ~0.5 GB | ~2.0 GB | Small tensors |
| Final Cleanup | ~0.1 GB | ~0.5 GB | Back to baseline |

### Memory Recovery Verification

**Good cleanup** (memory properly freed):
```
[GPU Memory] Before Whisper Cleanup: Allocated: 7.23GB (30.1%)
[GPU Memory] After Whisper Cleanup: Allocated: 0.18GB (0.7%)
```
**Expected recovery**: 95%+ of model memory should be freed

**Poor cleanup** (potential memory leak):
```
[GPU Memory] Before Whisper Cleanup: Allocated: 7.23GB (30.1%)
[GPU Memory] After Whisper Cleanup: Allocated: 5.42GB (22.6%)
```
**Problem**: Only 25% freed - indicates memory leak

## OOM Prevention Best Practices

### 1. Use Context Managers (Recommended)

```python
# GOOD: Guarantees cleanup even on exceptions
with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
    result = pipeline.process("audio.mp3")
```

```python
# BAD: Cleanup not guaranteed if exception occurs
pipeline = GPUTranscriptionPipeline(whisper_model="large-v3")
result = pipeline.process("audio.mp3")
pipeline.cleanup_models()  # May not execute if process() raises exception
```

### 2. Choose Appropriate Model Size

Match model size to your GPU VRAM:

| GPU VRAM | Recommended Whisper Model | Memory Headroom |
|----------|---------------------------|-----------------|
| 8 GB | `base` or `small` | Tight |
| 12 GB | `medium` | Comfortable |
| 16 GB | `large-v3` | Tight |
| 24 GB+ | `large-v3` | Comfortable |

### 3. Monitor Logs During Processing

Watch for memory warnings in real-time:

```bash
python src/pipeline_gpu.py audio.mp3 | grep "GPU Memory"
```

### 4. Process Files Sequentially

```python
# GOOD: Cleanup between files
files = ["audio1.mp3", "audio2.mp3", "audio3.mp3"]
for audio_file in files:
    with GPUTranscriptionPipeline() as pipeline:
        result = pipeline.process(audio_file)
    # Context manager ensures cleanup before next file
```

```python
# BAD: Models accumulate in memory
pipeline = GPUTranscriptionPipeline()
for audio_file in files:
    result = pipeline.process(audio_file)  # Memory leak!
```

### 5. Clear GPU Cache Between Runs

If running multiple pipelines in the same Python process:

```python
import torch

with GPUTranscriptionPipeline() as pipeline:
    result1 = pipeline.process("audio1.mp3")

# Ensure GPU cache is cleared
torch.cuda.empty_cache()

with GPUTranscriptionPipeline() as pipeline:
    result2 = pipeline.process("audio2.mp3")
```

## Troubleshooting OOM Errors

### Symptom: RuntimeError: CUDA out of memory

**Diagnosis Steps:**

1. **Check memory logs** to identify which stage failed:
   ```
   [GPU Memory] Before Transcription: Allocated: 0.23GB (1.0%)
   RuntimeError: CUDA out of memory. Tried to allocate 7.50GB
   ```
   → Whisper model is too large for available VRAM

2. **Verify cleanup is working** by checking before/after logs:
   ```
   [GPU Memory] After Whisper Cleanup: Allocated: 6.42GB (26.8%)
   ```
   → Cleanup failed, memory leak present

3. **Check for other GPU processes**:
   ```bash
   nvidia-smi
   ```
   → Other processes may be using VRAM

**Solutions:**

1. **Reduce model size**:
   ```python
   pipeline = GPUTranscriptionPipeline(whisper_model="medium")  # Instead of large-v3
   ```

2. **Use API-based transcription** (offload to OpenAI):
   ```python
   # Switch to pipeline.py (CPU/API) instead of pipeline_gpu.py
   ```

3. **Split long audio files**:
   ```python
   # Process in 10-minute chunks instead of full file
   ```

4. **Restart Python process**:
   ```bash
   # If memory leak suspected, restart clears all GPU memory
   exit()
   python src/pipeline_gpu.py audio.mp3
   ```

### Symptom: Memory usage keeps growing across files

**Diagnosis:**
Check if cleanup is being called:
```
[GPU Memory] After Final Cleanup: Allocated: 0.15GB (0.6%)  # GOOD
[GPU Memory] After Final Cleanup: Allocated: 12.34GB (51.4%)  # BAD - leak!
```

**Solutions:**

1. **Use context managers** (see section 1 above)

2. **Manually verify cleanup**:
   ```python
   pipeline = GPUTranscriptionPipeline()
   try:
       result = pipeline.process("audio.mp3")
   finally:
       pipeline.cleanup_models()  # Guaranteed cleanup
   ```

3. **Check for external references**:
   ```python
   # BAD: Keeps reference to models
   my_transcriber = pipeline.transcriber
   pipeline.cleanup_models()  # Won't free memory!

   # GOOD: No external references
   pipeline.cleanup_models()  # Memory freed
   ```

## Performance Optimization Tips

### 1. Enable TF32 (Tensor Float 32) on Compatible GPUs

TF32 is automatically enabled for A100/A6000 GPUs. Verify in logs:
```
TF32: True
```

**Benefit**: 2-3x faster matrix operations with minimal accuracy loss

### 2. Monitor GPU Utilization

Check the performance summary:
```
GPU Utilization: 87.3%
```

- **<50%**: GPU underutilized, may be bottlenecked by CPU or I/O
- **50-85%**: Good utilization
- **>85%**: Excellent utilization

### 3. Batch Multiple Files (Advanced)

For advanced users processing many files:

```python
import torch

files = [f"audio{i}.mp3" for i in range(100)]

for i, audio_file in enumerate(files):
    with GPUTranscriptionPipeline() as pipeline:
        result = pipeline.process(audio_file)

    # Every 10 files, force full cleanup
    if (i + 1) % 10 == 0:
        torch.cuda.empty_cache()
```

## Monitoring in Production

### Log Analysis

Parse GPU memory logs to detect issues:

```bash
# Extract memory usage timeline
grep "GPU Memory" performance_log.txt | awk '{print $4, $6}'

# Find peak memory usage
grep "GPU Memory" performance_log.txt | awk '{print $6}' | sort -n | tail -1

# Verify cleanup effectiveness
grep "After.*Cleanup" performance_log.txt
```

### Alerting Thresholds

Set up alerts for production systems:

- **Warning**: Allocated memory >70% for >30 seconds
- **Critical**: Allocated memory >85% at any point
- **Error**: Memory leak detected (allocated >10% after cleanup)

## Memory Profiling (Advanced)

For deep memory analysis:

```python
import torch

# Before running pipeline
torch.cuda.reset_peak_memory_stats()

with GPUTranscriptionPipeline() as pipeline:
    result = pipeline.process("audio.mp3")

# After completion
peak_memory = torch.cuda.max_memory_allocated() / (1024 ** 3)
print(f"Peak GPU memory: {peak_memory:.2f} GB")
```

## Summary

**Key Takeaways:**
1. ✅ Always use context managers for automatic cleanup
2. ✅ Monitor memory logs for warnings and leaks
3. ✅ Match model size to available VRAM
4. ✅ Process files sequentially with cleanup between runs
5. ✅ Verify cleanup effectiveness by checking before/after logs

**Memory Logging Points**: 19 checkpoints across all pipeline stages

**Automatic Cleanup**: try/finally blocks guarantee memory recovery

**Warning System**: Automatic alerts at 70% and 85% memory usage

For questions or issues, refer to the performance logs in `outputs/performance_logs/` for detailed memory usage timelines.
