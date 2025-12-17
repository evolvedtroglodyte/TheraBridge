# Audio Pipeline Architecture - Visual Diagrams

This document contains text-based architecture diagrams for the unified pipeline design.

---

## 1. Current State (Before Consolidation)

```
Current Architecture: 4 Separate Pipeline Implementations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────────┐
│                            pipeline.py                               │
│                         (CPU/API Variant)                            │
├─────────────────────────────────────────────────────────────────────┤
│  AudioPreprocessor                                                   │
│    ├─ pydub.AudioSegment                                            │
│    ├─ detect_leading_silence()                                      │
│    └─ effects.normalize()                                           │
│                                                                      │
│  WhisperTranscriber                                                  │
│    └─ OpenAI Whisper API                                            │
│                                                                      │
│  No Diarization                                                      │
│                                                                      │
│  Use Case: Production, cloud deployment                             │
│  Dependencies: pydub, openai, ffmpeg                                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         pipeline_gpu.py                              │
│                   (Provider-Agnostic GPU Variant)                    │
├─────────────────────────────────────────────────────────────────────┤
│  GPUAudioProcessor                                                   │
│    ├─ torchaudio.load()                                             │
│    ├─ torch GPU operations                                          │
│    └─ julius.resample_frac()                                        │
│                                                                      │
│  GPUTranscriptionPipeline                                            │
│    └─ faster-whisper.WhisperModel                                   │
│                                                                      │
│  PyAnnote Diarization                                                │
│    └─ pyannote.audio.Pipeline                                       │
│                                                                      │
│  GPUConfig (auto-detection)                                          │
│    └─ Detects: Vast.ai, RunPod, Lambda, Paperspace                 │
│                                                                      │
│  Use Case: GPU cloud providers                                      │
│  Dependencies: torch, faster-whisper, pyannote, CUDA                │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      pipeline_enhanced.py                            │
│                  (Performance Logging Variant)                       │
├─────────────────────────────────────────────────────────────────────┤
│  Same as pipeline.py BUT:                                            │
│    ├─ PerformanceLogger integration                                 │
│    ├─ Detailed subprocess timing                                    │
│    ├─ GPU utilization tracking                                      │
│    └─ Memory usage monitoring                                       │
│                                                                      │
│  SpeakerDiarizer (optional)                                          │
│    ├─ GPU-aware (CUDA/MPS)                                          │
│    └─ pyannote.audio.Pipeline                                       │
│                                                                      │
│  Speaker Alignment                                                   │
│    └─ CPU or GPU vectorized                                         │
│                                                                      │
│  Use Case: Research, debugging, optimization                        │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       pipeline_colab.py                              │
│                     (Colab L4 Optimized)                             │
├─────────────────────────────────────────────────────────────────────┤
│  Same as pipeline_gpu.py BUT:                                        │
│    ├─ Hardcoded paths: /content/...                                 │
│    ├─ L4-specific optimizations                                     │
│    └─ float16 compute type                                          │
│                                                                      │
│  Use Case: Google Colab notebooks only                              │
└─────────────────────────────────────────────────────────────────────┘

PROBLEMS:
  ❌ ~70% code duplication across files
  ❌ Bug fixes require changes in 4 places
  ❌ Features must be added 4 times
  ❌ Inconsistent behavior and APIs
  ❌ Confusing for users (which one to use?)
```

---

## 2. Proposed State (After Consolidation)

```
Unified Architecture: Single Pipeline with Pluggable Backends
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌───────────────────────────────────────────────────────────────────┐
│                      USER INTERFACE LAYER                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  AudioTranscriptionPipeline                                 │  │
│  │  - Single entry point                                       │  │
│  │  - Auto-detects optimal backend                             │  │
│  │  - Consistent API across all modes                          │  │
│  │                                                             │  │
│  │  Methods:                                                   │  │
│  │  - __init__(config: PipelineConfig)                        │  │
│  │  - process(audio_path: str) -> TranscriptionResult         │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────────┐
│                   CONFIGURATION & SELECTION                        │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  BackendSelector                                            │  │
│  │  - Auto-detect GPU availability                             │  │
│  │  - Check for model installations                            │  │
│  │  - Validate API credentials                                 │  │
│  │  - Select optimal backend                                   │  │
│  │                                                             │  │
│  │  Decision Logic:                                            │  │
│  │  1. GPU + faster-whisper? → GPU backend                    │  │
│  │  2. GPU + no models?      → Cloud backend                  │  │
│  │  3. No GPU + API key?     → Cloud backend                  │  │
│  │  4. No GPU + no API?      → CPU backend (warn)             │  │
│  └─────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  PipelineConfig                                             │  │
│  │  - backend: Optional[str]                                   │  │
│  │  - whisper_model: str                                       │  │
│  │  - enable_diarization: bool                                 │  │
│  │  - num_speakers: int                                        │  │
│  │  - enable_performance_logging: bool                         │  │
│  │  - ... other settings                                       │  │
│  └─────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────────┐
│                   ABSTRACTION LAYER (INTERFACES)                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│  │Preprocessor  │    │ Transcriber  │    │  Diarizer    │        │
│  │  Interface   │    │  Interface   │    │  Interface   │        │
│  ├──────────────┤    ├──────────────┤    ├──────────────┤        │
│  │ (ABC)        │    │ (ABC)        │    │ (ABC)        │        │
│  │              │    │              │    │              │        │
│  │ preprocess() │    │ transcribe() │    │ diarize()    │        │
│  │ validate()   │    │ cleanup()    │    │ cleanup()    │        │
│  └──────────────┘    └──────────────┘    └──────────────┘        │
└───────────────────────────────────────────────────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────────┐
│                 BACKEND IMPLEMENTATIONS (CONCRETE)                 │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    CPU BACKEND                              │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  CPUPreprocessor               (pydub)                      │  │
│  │  WhisperAPITranscriber         (OpenAI API)                 │  │
│  │  PyAnnoteDiarizer or Null      (optional)                   │  │
│  │                                                             │  │
│  │  Use Case: No GPU, has API key                             │  │
│  │  Performance: Preprocessing fast, transcription slow       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    GPU BACKEND                              │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  GPUPreprocessor               (torch/torchaudio)           │  │
│  │  FasterWhisperTranscriber      (local GPU)                  │  │
│  │  PyAnnoteDiarizer              (GPU-accelerated)            │  │
│  │                                                             │  │
│  │  Use Case: GPU available, local models installed           │  │
│  │  Performance: All operations GPU-accelerated (fastest)     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                   CLOUD BACKEND                             │  │
│  ├────────────────────────────────────────────────────────────┤  │
│  │  CPUPreprocessor               (pydub, minimal)             │  │
│  │  WhisperAPITranscriber         (OpenAI API)                 │  │
│  │  PyAnnoteDiarizer              (local CPU/GPU)              │  │
│  │                                                             │  │
│  │  Use Case: GPU available but no local models, or no GPU    │  │
│  │  Performance: Transcription offloaded to cloud             │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────┘
                               ↓
┌───────────────────────────────────────────────────────────────────┐
│                  CROSS-CUTTING CONCERNS (UTILITIES)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │
│  │ Performance  │  │   Speaker    │  │    Audio     │            │
│  │   Logger     │  │  Alignment   │  │  Chunking    │            │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤            │
│  │ - Timing     │  │ - Overlap    │  │ - Split for  │            │
│  │ - GPU stats  │  │   calculation│  │   API limits │            │
│  │ - Memory     │  │ - Threshold  │  │ - Merge      │            │
│  │ - Reports    │  │   matching   │  │   results    │            │
│  └──────────────┘  └──────────────┘  └──────────────┘            │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐                              │
│  │  GPU Config  │  │    Logging   │                              │
│  │  Detection   │  │    System    │                              │
│  ├──────────────┤  ├──────────────┤                              │
│  │ - Provider   │  │ - Structured │                              │
│  │   detection  │  │ - Levels     │                              │
│  │ - Optimal    │  │ - Formatters │                              │
│  │   settings   │  │              │                              │
│  └──────────────┘  └──────────────┘                              │
└───────────────────────────────────────────────────────────────────┘

BENEFITS:
  ✅ ~50% code reduction (single implementation)
  ✅ Bug fixes in one place
  ✅ Features added once
  ✅ Consistent behavior across all modes
  ✅ Simple, clear API for users
  ✅ Easy to extend (new backends = new concrete class)
```

---

## 3. Component Interaction Flow

```
Complete Pipeline Execution Flow
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────────────────────────────────────────────────────────┐
│ USER CODE                                                        │
├─────────────────────────────────────────────────────────────────┤
│ from src.pipeline import AudioTranscriptionPipeline             │
│ from src.config import PipelineConfig                           │
│                                                                  │
│ config = PipelineConfig(enable_diarization=True)                │
│ pipeline = AudioTranscriptionPipeline(config)                   │
│ result = pipeline.process("therapy_session.mp3")                │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ PIPELINE INITIALIZATION                                          │
├─────────────────────────────────────────────────────────────────┤
│ 1. PipelineConfig validates settings                            │
│    ├─ Check API keys (if needed)                                │
│    ├─ Check GPU availability                                    │
│    └─ Validate parameters                                       │
│                                                                  │
│ 2. BackendSelector.select_backend()                             │
│    ├─ Check torch.cuda.is_available()                           │
│    ├─ Check for faster-whisper                                  │
│    ├─ Check for OPENAI_API_KEY                                  │
│    └─ Return: "gpu" | "cpu" | "cloud"                           │
│                                                                  │
│ 3. BackendSelector.create_components(backend)                   │
│    ├─ Create Preprocessor instance                              │
│    ├─ Create Transcriber instance                               │
│    └─ Create Diarizer instance                                  │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 1: AUDIO VALIDATION                                         │
├─────────────────────────────────────────────────────────────────┤
│ preprocessor.validate("therapy_session.mp3")                     │
│    ↓                                                             │
│ Return: AudioMetadata                                            │
│    ├─ duration_seconds: 1380.0                                  │
│    ├─ sample_rate: 44100                                        │
│    ├─ channels: 2 (stereo)                                      │
│    ├─ format: "mp3"                                             │
│    ├─ file_size_mb: 15.2                                        │
│    └─ valid: True                                               │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 2: PREPROCESSING                                            │
├─────────────────────────────────────────────────────────────────┤
│ preprocessor.preprocess("therapy_session.mp3")                   │
│    ↓                                                             │
│ Sub-steps:                                                       │
│    1. Load audio file                                            │
│       └─ CPUPreprocessor: pydub.AudioSegment.from_file()        │
│       └─ GPUPreprocessor: torchaudio.load() → GPU tensor        │
│                                                                  │
│    2. Trim silence                                               │
│       └─ CPU: detect_leading_silence()                          │
│       └─ GPU: Vectorized dB threshold on GPU                    │
│                                                                  │
│    3. Normalize volume                                           │
│       └─ CPU: effects.normalize()                               │
│       └─ GPU: Peak detection + scaling on GPU                   │
│                                                                  │
│    4. Convert to mono 16kHz                                      │
│       └─ CPU: set_channels(1).set_frame_rate(16000)            │
│       └─ GPU: torch.mean() + julius.resample_frac()            │
│                                                                  │
│    5. Export to temp file                                        │
│       └─ Both: Save as WAV or MP3                               │
│    ↓                                                             │
│ Return: "/tmp/processed_audio.wav"                              │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 3: TRANSCRIPTION                                            │
├─────────────────────────────────────────────────────────────────┤
│ transcriber.transcribe("/tmp/processed_audio.wav")               │
│    ↓                                                             │
│ WhisperAPITranscriber (Cloud):                                   │
│    1. Check file size (< 25MB?)                                 │
│    2. If > 25MB: chunk into 10-min segments                     │
│    3. Upload to OpenAI API                                       │
│    4. Receive response (JSON)                                    │
│    5. Parse segments with timestamps                             │
│                                                                  │
│ FasterWhisperTranscriber (GPU/CPU):                              │
│    1. Load model (if not cached)                                 │
│       └─ WhisperModel("large-v3", device="cuda")                │
│    2. Run inference                                              │
│       └─ model.transcribe(audio, vad_filter=True)               │
│    3. Convert generator to list                                  │
│    4. Extract segments with timestamps                           │
│    ↓                                                             │
│ Return: TranscriptionData                                        │
│    ├─ segments: [                                                │
│    │     {start: 0.0, end: 3.2, text: "Hello, how are you?"},  │
│    │     {start: 3.5, end: 7.8, text: "I've been okay..."},    │
│    │     ...                                                     │
│    │   ]                                                         │
│    ├─ full_text: "Hello, how are you? I've been okay..."        │
│    ├─ language: "en"                                             │
│    └─ duration: 1380.0                                           │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 4: SPEAKER DIARIZATION (if enabled)                         │
├─────────────────────────────────────────────────────────────────┤
│ diarizer.diarize("/tmp/processed_audio.wav", num_speakers=2)    │
│    ↓                                                             │
│ PyAnnoteDiarizer:                                                │
│    1. Load pyannote model (if not cached)                        │
│       └─ Pipeline.from_pretrained("speaker-diarization-3.1")    │
│    2. Move to GPU if available                                   │
│       └─ pipeline.to(torch.device("cuda"))                       │
│    3. Load audio with torchaudio                                 │
│    4. Run diarization inference                                  │
│       └─ diarization = pipeline(audio, num_speakers=2)          │
│    5. Extract speaker turns                                      │
│    ↓                                                             │
│ Return: List[SpeakerTurn]                                        │
│    [                                                             │
│      {speaker: "SPEAKER_00", start: 0.0, end: 3.5},            │
│      {speaker: "SPEAKER_01", start: 3.8, end: 8.2},            │
│      {speaker: "SPEAKER_00", start: 8.5, end: 12.1},           │
│      ...                                                         │
│    ]                                                             │
│                                                                  │
│ NullDiarizer:                                                    │
│    └─ Return: [] (empty list)                                   │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 5: SPEAKER ALIGNMENT                                        │
├─────────────────────────────────────────────────────────────────┤
│ utils.alignment.align_speakers(segments, speaker_turns)          │
│    ↓                                                             │
│ For each transcription segment:                                  │
│    1. Find all overlapping speaker turns                         │
│    2. Calculate overlap duration for each turn                   │
│    3. Select speaker with maximum overlap                        │
│    4. If overlap < 50% of segment → "UNKNOWN"                   │
│    5. Assign speaker label to segment                            │
│                                                                  │
│ CPU Implementation:                                               │
│    └─ Nested loops (Python)                                     │
│                                                                  │
│ GPU Implementation (for large datasets):                         │
│    └─ Vectorized operations on GPU (torch)                      │
│    ↓                                                             │
│ Return: List[TranscriptionSegment]                               │
│    [                                                             │
│      {start: 0.0, end: 3.2, text: "Hello...", speaker: "00"},  │
│      {start: 3.5, end: 7.8, text: "I've...", speaker: "01"},   │
│      ...                                                         │
│    ]                                                             │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ STEP 6: RESULT COMPILATION                                       │
├─────────────────────────────────────────────────────────────────┤
│ Build TranscriptionResult:                                        │
│    ├─ segments: Original transcription segments                  │
│    ├─ aligned_segments: Segments with speaker labels             │
│    ├─ speaker_turns: Raw diarization output                      │
│    ├─ full_text: Complete transcription                          │
│    ├─ language: Detected language                                │
│    ├─ duration: Audio duration                                   │
│    ├─ metadata: Processing info                                  │
│    └─ performance_metrics: Timing data (if enabled)              │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ CLEANUP                                                           │
├─────────────────────────────────────────────────────────────────┤
│ 1. Delete temp files                                             │
│ 2. Clear GPU cache (if applicable)                               │
│ 3. Generate performance report (if enabled)                      │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│ RETURN TO USER                                                    │
├─────────────────────────────────────────────────────────────────┤
│ result: TranscriptionResult                                       │
│    .full_text                                                    │
│    .aligned_segments                                             │
│    .speaker_turns                                                │
│    .performance_metrics (if enabled)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Backend Selection Decision Tree

```
Backend Auto-Selection Algorithm
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

START
  │
  ├─ Backend explicitly specified in config?
  │    ├─ YES → Use specified backend (skip auto-detection)
  │    │         └─ Validate: Is backend valid? ("cpu", "gpu", "cloud")
  │    │              ├─ YES → Proceed
  │    │              └─ NO → Raise ValueError
  │    │
  │    └─ NO → Auto-detect optimal backend
  │              │
  │              ├─ Check: GPU available?
  │              │    └─ torch.cuda.is_available() == True?
  │              │         │
  │              │         ├─ YES (GPU available)
  │              │         │    │
  │              │         │    ├─ Check: faster-whisper installed?
  │              │         │    │    └─ try: import faster_whisper
  │              │         │    │         │
  │              │         │    │         ├─ YES → ✅ SELECT: GPU BACKEND
  │              │         │    │         │         (Best option: local GPU inference)
  │              │         │    │         │         - Fast preprocessing
  │              │         │    │         │         - Fast transcription (10-30x real-time)
  │              │         │    │         │         - Fast diarization
  │              │         │    │         │
  │              │         │    │         └─ NO (import fails)
  │              │         │    │              │
  │              │         │    │              ├─ Check: OpenAI API key?
  │              │         │    │              │    └─ os.getenv("OPENAI_API_KEY") exists?
  │              │         │    │              │         │
  │              │         │    │              │         ├─ YES → ✅ SELECT: CLOUD BACKEND
  │              │         │    │              │         │         (Good option: API for transcription)
  │              │         │    │              │         │         - GPU preprocessing
  │              │         │    │              │         │         - Cloud transcription
  │              │         │    │              │         │         - GPU diarization
  │              │         │    │              │         │
  │              │         │    │              │         └─ NO → ❌ RAISE ERROR
  │              │         │    │              │                   "GPU available but no faster-whisper
  │              │         │    │              │                    and no OPENAI_API_KEY. Please install
  │              │         │    │              │                    faster-whisper or set API key."
  │              │         │    │              │
  │              │         └─ NO (no GPU)
  │              │              │
  │              │              ├─ Check: OpenAI API key?
  │              │              │    └─ os.getenv("OPENAI_API_KEY") exists?
  │              │              │         │
  │              │              │         ├─ YES → ✅ SELECT: CLOUD BACKEND
  │              │              │         │         (Acceptable: API transcription)
  │              │              │         │         - CPU preprocessing
  │              │              │         │         - Cloud transcription
  │              │              │         │         - CPU/GPU diarization (if available)
  │              │              │         │
  │              │              │         └─ NO → ⚠️  SELECT: CPU BACKEND
  │              │              │                   (Slow but works)
  │              │              │                   - CPU preprocessing
  │              │              │                   - No transcription available!
  │              │              │                   - CPU diarization (if enabled)
  │              │              │                   + WARN: "No GPU and no API key.
  │              │              │                     Performance will be very slow.
  │              │              │                     Consider setting OPENAI_API_KEY."
  │              │              │
  │              └─ Validate components can be created
  │                    │
  │                    ├─ Diarization enabled?
  │                    │    └─ Check: HF_TOKEN available?
  │                    │         ├─ YES → OK
  │                    │         └─ NO → WARN: "HF_TOKEN not set.
  │                    │                  Diarization will fail."
  │                    │
  │                    └─ Return selected backend
  │
END

BACKEND CHARACTERISTICS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GPU Backend:
  ✅ Best performance (all operations GPU-accelerated)
  ✅ No API costs
  ✅ Privacy (all local)
  ⚠️  Requires GPU + CUDA
  ⚠️  Requires faster-whisper installation
  ⚠️  Requires model downloads (~3GB)

Cloud Backend:
  ✅ Good performance (API transcription is fast)
  ✅ No GPU required
  ✅ No model downloads
  ⚠️  API costs (pay per minute)
  ⚠️  Requires internet connection
  ⚠️  Data sent to OpenAI (privacy concern)

CPU Backend:
  ✅ No dependencies (besides pydub)
  ✅ Works everywhere
  ❌ Very slow (0.1x real-time)
  ❌ No transcription (needs API key)
  ⚠️  Only use as fallback
```

---

## 5. Data Flow Diagram

```
Data Structures Through Pipeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INPUT: audio_path (str)
   "therapy_session.mp3"
       │
       ↓
┌──────────────────────────────────────────────────────────┐
│ VALIDATION                                                │
└──────────────────────────────────────────────────────────┘
       │
       ↓
   AudioMetadata {
       duration_seconds: 1380.0,
       sample_rate: 44100,
       channels: 2,
       format: "mp3",
       file_size_mb: 15.2,
       valid: true
   }
       │
       ↓
┌──────────────────────────────────────────────────────────┐
│ PREPROCESSING                                             │
└──────────────────────────────────────────────────────────┘
       │
       ↓
   Processed Audio File (str)
   "/tmp/processed_audio.wav"
       - Mono (1 channel)
       - 16kHz sample rate
       - Silence trimmed
       - Volume normalized
       │
       ↓
┌──────────────────────────────────────────────────────────┐
│ TRANSCRIPTION                                             │
└──────────────────────────────────────────────────────────┘
       │
       ↓
   TranscriptionData {
       segments: [
           TranscriptionSegment {
               start: 0.0,
               end: 3.2,
               text: "Hello, how are you feeling today?",
               speaker: None  // Not assigned yet
           },
           TranscriptionSegment {
               start: 3.5,
               end: 7.8,
               text: "I've been having a difficult week.",
               speaker: None
           },
           ...
       ],
       full_text: "Hello, how are you feeling today? I've been...",
       language: "en",
       duration: 1380.0
   }
       │
       ↓
┌──────────────────────────────────────────────────────────┐
│ DIARIZATION (if enabled)                                  │
└──────────────────────────────────────────────────────────┘
       │
       ↓
   List[SpeakerTurn] [
       SpeakerTurn {
           speaker: "SPEAKER_00",
           start: 0.0,
           end: 3.5
       },
       SpeakerTurn {
           speaker: "SPEAKER_01",
           start: 3.8,
           end: 8.2
       },
       SpeakerTurn {
           speaker: "SPEAKER_00",
           start: 8.5,
           end: 12.1
       },
       ...
   ]
       │
       ↓
┌──────────────────────────────────────────────────────────┐
│ SPEAKER ALIGNMENT                                         │
│ (Combine segments + speaker_turns)                       │
└──────────────────────────────────────────────────────────┘
       │
       ↓
   List[TranscriptionSegment] [
       TranscriptionSegment {
           start: 0.0,
           end: 3.2,
           text: "Hello, how are you feeling today?",
           speaker: "SPEAKER_00"  // ← Assigned
       },
       TranscriptionSegment {
           start: 3.5,
           end: 7.8,
           text: "I've been having a difficult week.",
           speaker: "SPEAKER_01"  // ← Assigned
       },
       ...
   ]
       │
       ↓
┌──────────────────────────────────────────────────────────┐
│ RESULT COMPILATION                                        │
└──────────────────────────────────────────────────────────┘
       │
       ↓
OUTPUT: TranscriptionResult {
    segments: [Original segments without speakers],
    aligned_segments: [Segments with speaker labels],
    speaker_turns: [Raw diarization output],
    full_text: "Hello, how are you feeling today? I've been...",
    language: "en",
    duration: 1380.0,
    metadata: {
        source_file: "therapy_session.mp3",
        backend_used: "gpu",
        processing_time_seconds: 45.2,
        num_segments: 142,
        num_speaker_turns: 87
    },
    performance_metrics: {  // If enabled
        stages: {
            "preprocessing": {duration: 2.1, ...},
            "transcription": {duration: 38.5, ...},
            "diarization": {duration: 3.8, ...},
            "alignment": {duration: 0.8, ...}
        },
        ...
    }
}
```

---

## 6. File Organization (Before vs. After)

```
File Structure Comparison
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

BEFORE (Current):                    AFTER (Proposed):
───────────────────────────────      ─────────────────────────────────

audio-transcription-pipeline/        audio-transcription-pipeline/
├── src/                              ├── src/
│   ├── pipeline.py           289 LOC│   ├── pipeline.py          NEW
│   ├── pipeline_gpu.py       442 LOC│   ├── config.py            NEW
│   ├── pipeline_enhanced.py  656 LOC│   ├── interfaces.py        NEW
│   ├── pipeline_colab.py     322 LOC│   ├── models.py            NEW
│   ├── gpu_audio_ops.py      196 LOC│   │
│   ├── performance_logger.py 535 LOC│   ├── backends/            NEW
│   └── gpu_config.py         153 LOC│   │   ├── preprocessing/
│                                     │   │   │   ├── cpu.py
│                                     │   │   │   └── gpu.py
│                                     │   │   ├── transcription/
│                                     │   │   │   ├── whisper_api.py
│                                     │   │   │   └── faster_whisper.py
│                                     │   │   └── diarization/
│                                     │   │       ├── pyannote.py
│                                     │   │       └── null.py
│                                     │   │
│                                     │   ├── utils/             NEW
│                                     │   │   ├── alignment.py
│                                     │   │   └── chunking.py
│                                     │   │
│                                     │   ├── gpu_audio_ops.py   KEEP
│                                     │   ├── performance_logger.py KEEP
│                                     │   └── gpu_config.py      KEEP
│                                     │
├── tests/                            ├── tests/
│   ├── test_full_pipeline.py         │   ├── unit/             NEW
│   ├── test_performance_logging.py   │   │   ├── test_interfaces.py
│   ├── test_diarization.py           │   │   ├── test_config.py
│   └── ...                           │   │   └── test_models.py
│                                     │   ├── integration/       NEW
│                                     │   │   ├── test_cpu_backend.py
│                                     │   │   ├── test_gpu_backend.py
│                                     │   │   └── test_cloud_backend.py
│                                     │   ├── regression/        NEW
│                                     │   │   └── test_output_parity.py
│                                     │   └── e2e/              NEW
│                                     │       └── test_full_pipeline.py
│                                     │
├── transcribe_gpu.py                 ├── transcribe.py          NEW
└── ...                               └── ...

LOC REDUCTION:                        ESTIMATED FINAL:
  Total: ~1,709 LOC (4 pipelines)       Core: ~800 LOC
  Duplicated: ~1,200 LOC (70%)          Backends: ~400 LOC
                                        Utils: ~200 LOC
                                        ─────────────────
                                        Total: ~1,400 LOC

                                      Reduction: ~18% total LOC
                                      But 70% duplication eliminated!
                                      (Maintenance burden reduced by 4x)
```

---

*These diagrams illustrate the transformation from 4 duplicate implementations to a unified, extensible architecture with pluggable backends.*
