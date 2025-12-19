# Audio Transcription Pipeline

A comprehensive therapy session transcription system with speaker diarization, supporting both CPU and GPU acceleration.

## Overview

This pipeline processes therapy session audio to produce timestamped transcripts with speaker identification (Therapist vs Client). Two implementations are available:

1. **CPU/API-based** (`src/pipeline.py`) - Uses OpenAI Whisper API, portable and cloud-ready
2. **GPU-accelerated** (`src/pipeline_gpu.py`) - Uses faster-whisper locally, optimized for Vast.ai L4 GPUs

## Features

- Audio preprocessing (silence trimming, normalization, format conversion)
- High-quality transcription (Whisper large-v3)
- Speaker diarization (pyannote 3.1)
- Therapist/Client role identification
- Performance monitoring with GPU utilization tracking
- Chunking support for long audio files (>25MB/52 minutes)

## Quick Start

### CPU/API Version (Default)

```bash
cd audio-transcription-pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up OpenAI API key
echo "OPENAI_API_KEY=your_key_here" > .env

# Run pipeline
python tests/test_full_pipeline.py tests/samples/onemintestvid.mp3
```

### GPU Version (Provider-Agnostic)

**NEW: Works on Vast.ai, RunPod, Lambda Labs, and Paperspace**

Quick GPU setup (universal, works on any provider):

```bash
# Clone and setup
git clone https://github.com/yourusername/audio-transcription-pipeline.git
cd audio-transcription-pipeline
bash scripts/setup_gpu.sh

# Configure HuggingFace token
echo "HF_TOKEN=your_token_here" >> .env

# Process audio
source venv/bin/activate
python transcribe_gpu.py audio.mp3 --speakers 2
```

**Note:** `setup_gpu.sh` auto-detects your GPU provider (Vast.ai, RunPod, Lambda, Paperspace) and configures accordingly.

## Project Structure

```
audio-transcription-pipeline/
├── src/
│   ├── pipeline.py               # CPU/API-based pipeline
│   ├── pipeline_gpu.py           # NEW: Provider-agnostic GPU pipeline
│   ├── gpu_config.py             # NEW: Auto-detect GPU provider & optimize
│   ├── gpu_audio_ops.py          # GPU-accelerated audio operations
│   └── performance_logger.py     # Performance monitoring
│
├── scripts/
│   ├── setup.sh                  # CPU setup
│   └── setup_gpu.sh              # Universal GPU setup (auto-detects provider)
│
├── tests/
│   ├── test_full_pipeline.py     # Complete pipeline test
│   ├── samples/                  # Test audio files
│   └── outputs/                  # Generated transcripts
│
├── requirements.txt              # CPU/API dependencies
└── README.md                     # This file
```

## Implementation Details

### CPU/API Pipeline (`src/pipeline.py`)

**Components:**
- `AudioPreprocessor`: Handles audio loading, silence trimming, normalization using pydub
- `WhisperTranscriber`: Manages OpenAI API calls with automatic chunking for large files
- `SpeakerDiarizer`: Implements pyannote speaker diarization with GPU support when available

**Performance:**
- Processing time: ~5-7 minutes for 23-minute session
- API-dependent (requires internet connection)
- Lower resource requirements

### GPU Pipeline (`src/pipeline_gpu.py`)

**Components:**
- `GPUAudioProcessor`: All audio operations on GPU (torch-based)
- `GPUTranscriptionPipeline`: faster-whisper with int8 quantization
- Integrated pyannote diarization on GPU

**Performance:**
- Processing speed: 10-15x real-time on L4 GPU
- No API calls (fully local)
- Requires 22+ GB VRAM for large-v3 model

### Key Differences

| Feature | CPU/API Version | GPU Version |
|---------|----------------|-------------|
| Transcription | OpenAI Whisper API | faster-whisper (local) |
| Audio Processing | pydub (CPU) | torch (GPU) |
| Speed | 5-7 min for 23 min audio | 1.5-2 min for 23 min audio |
| Requirements | Internet, API key | GPU with 16+ GB VRAM |
| Best For | Production, cloud deployment | Research, batch processing |

## GPU Provider Detection

The GPU pipeline automatically detects which cloud GPU provider you're using and optimizes settings accordingly. This happens transparently when you run `pipeline_gpu.py` or `transcribe_gpu.py`.

### Supported Providers

The detection logic in `src/gpu_config.py` identifies the following providers:

| Provider | Detection Method | Priority |
|----------|------------------|----------|
| **Google Colab** | `/content` directory exists AND `COLAB_GPU` env variable | 1st |
| **Vast.ai** | `VAST_CONTAINERLABEL` OR `VAST_CONTAINER_USER` env variables | 2nd |
| **RunPod** | `RUNPOD_POD_ID` env variable | 3rd |
| **Paperspace** | `PAPERSPACE_METRIC_URL` env variable OR `/storage` directory | 4th |
| **Lambda Labs** | Hostname contains `lambda` or `lambdalabs` | 5th |
| **Local/Docker** | `/.dockerenv` file exists | 6th |
| **Unknown** | None of the above match | Fallback |

### Environment Variables Checked

The detection logic checks these environment variables (in order):

1. **`COLAB_GPU`** - Set by Google Colab when GPU runtime is enabled
2. **`VAST_CONTAINERLABEL`** - Vast.ai container label identifier
3. **`VAST_CONTAINER_USER`** - Vast.ai container user identifier
4. **`RUNPOD_POD_ID`** - RunPod pod instance identifier
5. **`PAPERSPACE_METRIC_URL`** - Paperspace metrics endpoint URL

Additionally checks:
- **Filesystem paths**: `/content` (Colab), `/storage` (Paperspace), `/.dockerenv` (Docker)
- **Hostname patterns**: `vast`, `vps`, `lambda`, `lambdalabs`

### What Happens When Provider is Detected

When a provider is successfully detected, the GPU config automatically optimizes:

1. **Model Cache Directory** - Sets persistent storage location for model files:
   - Colab: `/content/models`
   - Vast.ai/RunPod: `/workspace/models`
   - Paperspace: `/storage/models`
   - Local/Unknown: `~/.cache/huggingface`

2. **Compute Type & Batch Size** - Based on GPU model (detected via `torch.cuda.get_device_name()`):
   - A100/H100: `float16`, batch size 16, TF32 enabled
   - RTX 3090/4090/A6000: `int8`, batch size 8, TF32 disabled
   - Other GPUs: `int8`, batch size 4, TF32 disabled

3. **Environment Variables** - Sets caching paths:
   - `TRANSFORMERS_CACHE={model_cache_dir}`
   - `HF_HOME={model_cache_dir}`

### What Happens if Provider is UNKNOWN

If detection fails and provider is `UNKNOWN`, the pipeline will:

1. **Use conservative defaults**:
   - Model cache: `~/.cache/huggingface` (user home directory)
   - Compute type: `int8` (safe for most GPUs)
   - Batch size: 4 (low memory usage)
   - TF32: Disabled

2. **Continue processing** - The pipeline will still work, just with less optimal settings

3. **Print warning** in GPU info output showing `Provider: unknown`

**Impact of UNKNOWN provider:**
- Slightly slower processing (smaller batch size)
- May use more disk space (cache in home directory)
- Still fully functional for transcription

### Troubleshooting Detection Failures

If your provider is showing as `UNKNOWN` when it shouldn't be:

#### Check GPU Configuration
```bash
# Run diagnostic script
cd audio-transcription-pipeline
source venv/bin/activate
python src/gpu_config.py
```

This prints:
- Detected provider
- GPU device name
- VRAM available
- Optimized settings (compute type, batch size, cache directory)

#### Verify Environment Variables

**For Vast.ai:**
```bash
# Check if Vast.ai env vars exist
env | grep VAST
# Should show VAST_CONTAINERLABEL or VAST_CONTAINER_USER
```

**For RunPod:**
```bash
# Check if RunPod env var exists
env | grep RUNPOD
# Should show RUNPOD_POD_ID
```

**For Paperspace:**
```bash
# Check if Paperspace env var or directory exists
env | grep PAPERSPACE
ls -la /storage
# Should show PAPERSPACE_METRIC_URL or /storage directory
```

**For Google Colab:**
```bash
# Check if Colab env var exists
env | grep COLAB
ls -la /content
# Should show COLAB_GPU and /content directory
```

#### Manual Provider Override

If detection fails but you want provider-specific optimizations, you can manually set the environment variable before running:

```bash
# For Vast.ai
export VAST_CONTAINERLABEL=manual_override

# For RunPod
export RUNPOD_POD_ID=manual_override

# For Paperspace
export PAPERSPACE_METRIC_URL=manual_override

# For Colab (usually auto-detected, but if needed)
export COLAB_GPU=1

# Then run pipeline
python transcribe_gpu.py audio.mp3
```

#### Common Detection Issues

1. **Container/VM without provider env vars**
   - Some bare-metal GPU instances may not have provider-specific variables
   - Solution: Detection will show `UNKNOWN` but pipeline will still work with safe defaults

2. **Custom Docker containers**
   - Custom containers may not include provider environment variables
   - Solution: Pass env vars when launching container (`docker run -e VAST_CONTAINERLABEL=...`)

3. **SSH into GPU instance**
   - Direct SSH connections may have different environment than container
   - Solution: Check `env` output and manually export missing variables

4. **Hostname-based detection fails**
   - Some providers use generic hostnames
   - Solution: Environment variable detection takes priority over hostname

### Optimal Settings Per Provider

Based on successful detection, here are the optimized configurations:

#### Google Colab
```python
GPUConfig(
    provider=COLAB,
    device_name="Tesla T4",  # typical
    compute_type="int8",     # T4 works best with int8
    batch_size=4,
    model_cache_dir="/content/models",
    enable_tf32=False
)
```

#### Vast.ai (tested on RTX 3090)
```python
GPUConfig(
    provider=VASTAI,
    device_name="NVIDIA GeForce RTX 3090",
    compute_type="int8",     # cuDNN compatibility
    batch_size=8,            # 24GB VRAM supports larger batches
    model_cache_dir="/workspace/models",
    enable_tf32=False
)
```

#### RunPod
```python
GPUConfig(
    provider=RUNPOD,
    device_name="NVIDIA A100",  # typical
    compute_type="float16",      # A100 optimized for FP16
    batch_size=16,
    model_cache_dir="/workspace/models",
    enable_tf32=True            # A100 supports TF32
)
```

#### Paperspace
```python
GPUConfig(
    provider=PAPERSPACE,
    device_name="varies",
    compute_type="int8",
    batch_size=4,
    model_cache_dir="/storage/models",
    enable_tf32=False
)
```

#### Lambda Labs
```python
GPUConfig(
    provider=LAMBDA,
    device_name="NVIDIA A6000",  # typical
    compute_type="int8",
    batch_size=8,
    model_cache_dir="~/.cache/huggingface",
    enable_tf32=False
)
```

**Note:** Actual settings vary based on detected GPU model. These are examples with typical hardware for each provider.

## GPU Performance Testing Results

**Tested on Vast.ai - RTX 3090 (December 2025)**

| Metric | Result |
|--------|--------|
| Provider Detection | ✅ Correctly identifies Vast.ai |
| GPU Optimization | ✅ Auto-selected int8, batch size 8 |
| Processing Speed | **34-42x real-time** |
| Audio Duration | 23 minutes (1389 seconds) |
| Processing Time (1st run) | 40.7 seconds (includes model download) |
| Processing Time (2nd run) | 33.3 seconds (18% faster, cached) |
| Model Caching | ✅ Working correctly |
| Cost | $0.006 for full test suite |

**Speedup vs CPU:** 17-34x faster than CPU-based transcription

**Tested Providers:**
- ✅ Vast.ai - Verified working (RTX 3090)
- ⏳ RunPod - Not yet tested
- ⏳ Lambda Labs - Not yet tested
- ⏳ Paperspace - Not yet tested
- ⏳ Google Colab - Not yet tested

## Performance Monitoring

Both implementations include comprehensive performance logging:

```python
from src.performance_logger import PerformanceLogger

logger = PerformanceLogger()
with logger.track_stage("transcription"):
    # Your transcription code here
    pass

# Get performance summary
print(logger.get_summary())
```

Output includes:
- Stage-by-stage timing breakdown
- GPU utilization (when available)
- Memory usage statistics
- Processing throughput metrics

## Output Format

The pipeline generates JSON output with the following structure:

```json
{
  "audio_duration": 123.45,
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Hello, how are you feeling today?",
      "speaker": "Therapist"
    },
    {
      "start": 5.5,
      "end": 12.3,
      "text": "I've been having a difficult week.",
      "speaker": "Client"
    }
  ],
  "metadata": {
    "total_segments": 42,
    "therapist_segments": 20,
    "client_segments": 22,
    "processing_time": 95.3
  }
}
```

## Environment Variables

Create a `.env` file in the project root with the following variables:

### Required Variables

**OPENAI_API_KEY** (CPU/API version only)
- Get from: https://platform.openai.com/api-keys
- Required for: Whisper API transcription in CPU mode
- Example: `OPENAI_API_KEY=sk-your-key-here`

**HF_TOKEN** (All versions)
- Get from: https://hf.co/settings/tokens (free account required)
- Required for: Pyannote speaker diarization model access
- Setup: Accept terms at https://huggingface.co/pyannote/speaker-diarization-3.1
- Example: `HF_TOKEN=hf_your-token-here`

### Optional Variables

**VAST_API_KEY** (GPU version only)
- Get from: https://cloud.vast.ai/account/ (Account → API Key)
- Required for: Automated Vast.ai GPU instance management
- Used by: `run_gpu_vast.py`, `batch_youtube_vast.py`, parallel processing scripts
- Example: `VAST_API_KEY=your-vast-api-key`
- Note: Not needed if manually connecting to GPU instances

**Quick setup:**
```bash
# Copy example file
cp .env.example .env

# Edit with your keys
nano .env
```

## Dependencies

### CPU/API Version (`requirements.txt`)
- pydub - Audio processing
- openai - Whisper API
- pyannote.audio >=3.1.0 - Speaker diarization (supports 3.1.0 - 4.x)
- python-dotenv - Environment variables

### GPU Version (`requirements_gpu.txt`)
- torch, torchaudio - GPU operations
- faster-whisper - Local Whisper inference
- pyannote.audio >=3.1.0 - Speaker diarization (supports 3.1.0 - 4.x)
- julius - GPU audio resampling
- ctranslate2 - Optimized inference

### Pyannote Version Compatibility

The pipeline includes automatic version detection for pyannote.audio:

- **Supported versions:** pyannote.audio 3.1.0 through 4.x
- **Version detection:** Automatic via `src/pyannote_compat.py`
- **Compatibility layer:** Handles API differences transparently
  - pyannote 3.x: Returns `Annotation` object directly from pipeline
  - pyannote 4.x: Returns `DiarizeOutput` dataclass with `speaker_diarization` and `exclusive_speaker_diarization` attributes
- **Preferred mode:** Uses `exclusive_speaker_diarization` (no overlapping speech) when available for cleaner alignment

The compatibility layer automatically detects the installed version and uses the correct API, requiring no manual configuration.

## Known Issues and Solutions

### GPU Version

1. **cuDNN Error with float16**
   - Solution: Use `compute_type="int8"` instead

2. **NumPy Compatibility**
   - Solution: Use numpy==1.26.4

3. **HuggingFace Token Required**
   - Sign up at huggingface.co (free)
   - Set `HF_TOKEN` environment variable

### Both Versions

1. **Unknown Speaker Labels**
   - Occurs with poor audio quality
   - Solution: Adjust VAD parameters or num_speakers

2. **Memory Issues with Long Files**
   - CPU version: Automatic chunking handles this
   - GPU version: May need to reduce batch size

## Testing

Run the test suite:

```bash
# CPU version tests (default, uses Whisper API)
python tests/test_full_pipeline.py

# Performance logging tests (includes GPU performance monitoring)
python tests/test_performance_logging.py
```

**Note:** GPU pipeline testing is performed on Vast.ai or equivalent provider. See GPU_PROVIDER_SETUP_GUIDE.md for setup instructions.

## Next Steps

- [ ] Add real-time streaming support
- [ ] Implement speaker embedding storage for consistent identification
- [ ] Add support for multi-party conversations (>2 speakers)
- [ ] Create web interface for easier usage
- [ ] Add support for more audio formats

## License

Proprietary - TherapyBridge Project

## Support

For issues or questions, see the main project documentation in `Project MDs/TherapyBridge.md`