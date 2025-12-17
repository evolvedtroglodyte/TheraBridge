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
- ✅ Vast.ai - Verified working
- ⏳ RunPod - Not yet tested
- ⏳ Lambda Labs - Not yet tested
- ⏳ Paperspace - Not yet tested

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

## Dependencies

### CPU/API Version (`requirements.txt`)
- pydub - Audio processing
- openai - Whisper API
- pyannote.audio - Speaker diarization
- python-dotenv - Environment variables

### GPU Version (`requirements.txt`)
- torch, torchaudio - GPU operations
- faster-whisper - Local Whisper inference
- pyannote.audio - Speaker diarization
- julius - GPU audio resampling
- ctranslate2 - Optimized inference

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