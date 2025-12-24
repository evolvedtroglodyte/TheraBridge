---
date: 2025-12-28T01:46:12+0000
researcher: NewdlDewdl
git_commit: 227586ba678cfd478bfb8842da75512d76a97e39
branch: main
repository: peerbridge proj
topic: "Comprehensive Codebase State Analysis"
tags: [research, codebase, architecture, backend, frontend, audio-pipeline, monorepo]
status: complete
last_updated: 2025-12-28
last_updated_by: NewdlDewdl
---

# Research: Comprehensive Codebase State Analysis

**Date**: 2025-12-28T01:46:12+0000
**Researcher**: NewdlDewdl
**Git Commit**: 227586ba678cfd478bfb8842da75512d76a97e39
**Branch**: main
**Repository**: peerbridge proj

## Research Question

Analyze the current state of the codebase - its architecture, implementation status, recent changes, and overall health.

## Summary

TherapyBridge is a mature, production-ready monorepo containing 4 independent projects for AI-powered therapy session management. The backend implements a sophisticated two-wave AI analysis pipeline using GPT-5 series models for extracting clinical insights from therapy transcripts. The frontend provides a polished patient dashboard with real-time chat, progress tracking, and session management. The audio pipeline offers both CPU/API and GPU-accelerated transcription with speaker diarization. All projects are well-documented with comprehensive testing infrastructure.

**Current State**: The codebase is in active development with recent improvements to UI consistency, demo mode functionality, and breakthrough detection systems. The backend Wave 1 + Wave 2 analysis pipeline is fully operational, and the frontend has been enhanced with dark mode, auto-refresh capabilities, and improved accessibility.

**Key Metrics**:
- 4 independent deployable projects
- 3 programming languages (Python, TypeScript, Shell)
- 100+ backend test files with 80% coverage requirement
- 19 frontend E2E tests using Playwright
- 18+ audio pipeline tests with smart fixture skipping
- Recent commits focused on UI polish and demo mode enhancements

---

## Detailed Findings

### 1. Repository Structure & Organization

**Location**: `/Users/newdldewdl/Global Domination 2/peerbridge proj/`

**Architecture Pattern**: Monorepo with 4 independent projects, each self-contained and deployable

**Root-Level Organization**:
- `.claude/` - Claude Code configuration, agents, commands, skills, orchestration system
- `Project MDs/` - Comprehensive feature specifications and master documentation
- `README.md` - Monorepo overview
- Multiple feature-specific documentation files (MOOD_ANALYSIS_README.md, TOPIC_EXTRACTION_README.md, etc.)
- Deployment and architecture documentation (DEPLOYMENT.md, ARCHITECTURE_ANALYSIS.md)

**Python Version Standardization**:
- Root: 3.13.9
- Backend: 3.13.9
- Audio Pipeline: 3.13.9
- Scrapping: 3.11 (legacy, not yet upgraded)

**Current Git Status**:
- Branch: main
- Recent commit: 227586b "Remove test button and replace brain emoji with Dobby logo"
- Modified files: backend/app/routers/sessions.py, multiple frontend components
- Untracked files: New markdown documentation, backend services, frontend hooks

**Repository Organization Principles** (from .claude/CLAUDE.md):
- Minimize file count - every file must earn its place
- One README per component
- No archive folders - git history preserves everything
- No duplicate configs - single .claude/ folder at root
- Value over volume - only keep information valuable for project longevity

---

### 2. Backend API State (FastAPI + PostgreSQL)

**Location**: `backend/`

**Entry Point**: `backend/app/main.py:22-40` - FastAPI application with CORS, routers

**Technology Stack**:
- FastAPI 0.115.0
- Supabase (Neon PostgreSQL)
- OpenAI GPT-5 series models
- Python 3.13.9

#### API Endpoints

**Sessions Router** (`backend/app/routers/sessions.py`):

**Session CRUD**:
- `GET /api/sessions/{session_id}` (lines 138-154) - Fetch session with breakthrough details
- `GET /api/sessions/patient/{patient_id}` (lines 157-199) - List all sessions for patient
- `POST /api/sessions/` (lines 202-226) - Create new therapy session

**Transcript & Audio Upload**:
- `POST /api/sessions/{session_id}/upload-transcript` (lines 233-301) - Stores transcript, triggers breakthrough detection
- `POST /api/sessions/{session_id}/upload-audio` (lines 304-370) - Uploads audio to Supabase Storage

**Wave 1 Analysis (Parallel)**:
- `POST /api/sessions/{session_id}/analyze-mood` (lines 686-781) - AI mood scoring (0.0-10.0)
- `POST /api/sessions/{session_id}/extract-topics` (lines 964-1057) - Topics, action items, technique, summary
- `POST /api/sessions/{session_id}/analyze-breakthrough` (lines 377-483) - Therapeutic breakthrough detection

**Wave 2 Analysis (Sequential)**:
- `POST /api/sessions/{session_id}/analyze-deep` (lines 1173-1260) - Comprehensive clinical synthesis
- `POST /api/sessions/{session_id}/generate-prose-analysis` (lines 1263-1327) - Patient-facing narrative

**Pipeline Management**:
- `POST /api/sessions/{session_id}/analyze-full-pipeline` (lines 1064-1138) - Orchestrates Wave 1 + Wave 2
- `GET /api/sessions/{session_id}/analysis-status` (lines 1141-1170) - Pipeline status tracking

**Additional Features**:
- `GET /api/sessions/patient/{patient_id}/consistency` (lines 526-679) - Session attendance consistency
- `GET /api/sessions/patient/{patient_id}/mood-history` (lines 784-812) - Mood trend data
- `GET /api/sessions/patient/{patient_id}/breakthroughs` (lines 486-523) - All breakthroughs
- `POST /api/sessions/sessions/{session_id}/label-speakers` (lines 819-898) - Therapist/Client labeling
- `GET /api/sessions/techniques/{technique_name}/definition` (lines 1355-1391) - Clinical technique definitions
- `GET /api/sessions/patient/{patient_id}/progress-metrics` (lines 1398-1506) - Progress visualization data

**Demo Router** (`backend/app/routers/demo.py`):
- `POST /api/demo/initialize` (lines 132-199) - Creates demo user with 10 pre-loaded sessions
- `POST /api/demo/reset` (lines 202-254) - Resets demo by deleting and re-seeding sessions
- `GET /api/demo/status` (lines 257-308) - Returns demo user status

#### AI Services

**Two-Wave Analysis Architecture**:
- **Wave 1 (Parallel)**: Mood, Topics, Breakthrough - run simultaneously via `asyncio.gather()`
- **Wave 2 (Sequential)**: Deep Analysis - requires Wave 1 complete, synthesizes all prior data

**Service Implementations**:

1. **MoodAnalyzer** (`backend/app/services/mood_analyzer.py`)
   - Model: gpt-5-nano (~$0.0005 per session)
   - Analyzes patient dialogue only (SPEAKER_01)
   - Returns: score (0.0-10.0 in 0.5 increments), confidence, rationale, indicators
   - Scale: 0-2 (severe distress) → 4.5-5.5 (neutral) → 8-10 (very positive)

2. **TopicExtractor** (`backend/app/services/topic_extractor.py`)
   - Model: gpt-5-mini (~$0.0013 per session)
   - Extracts: 1-2 topics, 2 action items, 1 technique, summary (<150 chars)
   - Validates techniques against centralized library
   - Direct, active voice summaries (no meta-commentary)

3. **BreakthroughDetector** (`backend/app/services/breakthrough_detector.py`)
   - Model: gpt-5 (~$0.0084 per session)
   - Ultra-strict detection: 0 or 1 breakthrough per session
   - Breakthrough types: Root cause discovery, pattern recognition, identity insight, reframe revelation
   - Returns: label (2-3 words), evidence (quotes), timestamp range, dialogue excerpt
   - Confidence scoring: 1.0 = clear transformative discovery, <0.8 = probably not genuine

4. **DeepAnalyzer** (`backend/app/services/deep_analyzer.py`)
   - Model: gpt-5.2 (~$0.0200 per session)
   - Synthesizes: Wave 1 results + patient history + cumulative context
   - 5 Analysis Dimensions:
     - Progress indicators: Symptom reduction, skill development, goal progress
     - Therapeutic insights: Key realizations, patterns, growth areas, strengths
     - Coping skills: Learned skills, proficiency levels, practice recommendations
     - Therapeutic relationship: Engagement, openness, alliance strength
     - Recommendations: Practices, resources, reflection prompts
   - Patient history queries: Last 5 sessions, 90-day mood trend, recurring topics, technique history, breakthrough history

5. **ProseGenerator** (`backend/app/services/prose_generator.py`)
   - Model: gpt-5.2 (~$0.0118 per session)
   - Generates: 500-750 word patient-facing narrative from deep analysis
   - Auto-triggered by orchestrator after Wave 2 completes

6. **SpeakerLabeler** (`backend/app/services/speaker_labeler.py`)
   - Model: gpt-5-mini (~$0.0009 per session)
   - Detects roles: Therapist vs Patient (Client)
   - Heuristics: Opening statements, clinical language, question patterns, speaking ratio (30-40% vs 60-70%)
   - Merges consecutive same-speaker segments
   - Formats timestamps as MM:SS

7. **AnalysisOrchestrator** (`backend/app/services/analysis_orchestrator.py`)
   - Manages: Multi-wave analysis pipeline with dependency resolution
   - Retry logic: MAX_RETRIES=3, exponential backoff, 300s timeout per wave
   - Status tracking: wave1_running → wave1_complete → wave2_running → complete
   - Logging: All executions logged to `analysis_processing_log` table
   - Returns: PipelineStatus with completion flags and timing

8. **TechniqueLibrary** (`backend/app/services/technique_library.py`)
   - Centralized library of clinical techniques organized by modality
   - Functions: get_technique_library(), validate_and_standardize(), get_technique_definition()

9. **ProgressMetricsExtractor** (`backend/app/services/progress_metrics_extractor.py`)
   - Extracts: Mood Trends, Session Consistency charts
   - Returns: Recharts-compatible chart data for visualization

**Total Cost Per Session**: ~$0.042 (4.2 cents for full Wave 1 + Wave 2 analysis)

#### Database Schema

**Primary Tables**:

**users**:
- Standard fields: id, email, password_hash, role (patient/therapist)
- Demo mode: demo_token (UUID), is_demo (boolean), demo_created_at, demo_expires_at
- Added by migration `007_add_demo_mode_support.sql`

**therapy_sessions**:
- Core: id, patient_id, therapist_id, session_date, duration_minutes
- Transcript: transcript (JSONB array), audio_file_url
- Processing: processing_status, analysis_status
- Wave 1 fields:
  - Mood: mood_score, mood_confidence, mood_rationale, mood_indicators, emotional_tone, mood_analyzed_at
  - Topics: topics (array), action_items (array), technique, summary, extraction_confidence, raw_meta_summary, topics_extracted_at
  - Breakthrough: has_breakthrough, breakthrough_data (JSONB), breakthrough_label, breakthrough_analyzed_at
- Wave 2 fields:
  - Deep: deep_analysis (JSONB), analysis_confidence, deep_analyzed_at
  - Prose: prose_analysis (text), prose_generated_at
  - Tracking: wave1_completed_at

**analysis_processing_log**:
- Tracks: session_id, wave, status, retry_count
- Timing: started_at, completed_at, processing_duration_ms
- Error tracking: error_message

**Views & Functions**:
- `patient_topic_frequency` - Topic aggregation across sessions
- `patient_technique_history` - Technique usage tracking
- `get_patient_mood_stats` RPC - Mood trend calculations
- `get_analysis_pipeline_status` RPC - Comprehensive pipeline status
- `seed_demo_user_sessions` RPC - Demo user initialization

**Recent Migrations**:
- `005_add_breakthrough_label.sql` - Quick filtering on breakthrough type
- `006_add_prose_analysis.sql` - Patient-facing narrative storage
- `007_add_demo_mode_support.sql` - Demo mode infrastructure

#### Configuration & Model Selection

**Model Configuration** (`backend/app/config/model_config.py`):
- GPT-5 model registry with cost tracking
- Task-to-model assignments for optimal cost/quality
- Cost estimation functions
- **Important**: GPT-5 series does NOT support custom temperature parameters

**Settings Management** (`backend/app/config.py`):
- Pydantic BaseSettings for environment variables
- Validates required configuration on import
- CORS origins, JWT settings, Supabase connection, OpenAI API key
- Breakthrough detection thresholds, auto-analyze flags

#### Testing Infrastructure

**Test Framework**: pytest with fixtures in `backend/tests/conftest.py`

**Fixtures**:
- `openai_api_key()` - Auto-skip tests if missing
- `db()` - Supabase client
- `demo_session_id()` - First session with transcript
- `session_without_transcript_id()` - Error testing

**Test Files** (20+ files):
- Unit tests: test_mood_analysis.py, test_topic_extraction.py, test_breakthrough_detection.py
- Integration tests: test_deep_analysis_pipeline.py, test_complete_demo.py
- Demo scripts: batch_process_all_sessions.py

**CI/CD** (`.github/workflows/backend-tests.yml`):
- Runs on: Ubuntu latest, Python 3.11 & 3.12 matrix
- Services: PostgreSQL 15 container
- Steps: Install deps → Run migrations → Execute pytest with coverage
- Coverage: Minimum 80% required, reports uploaded to Codecov
- Artifacts: HTML coverage reports (30-day retention), JUnit XML

**Current Status**: Modified `backend/app/routers/sessions.py` according to git status

---

### 3. Frontend Dashboard State (Next.js 16 + React 19)

**Location**: `frontend/`

**Entry Point**: `frontend/app/page.tsx:8-48` - Auto-initializes demo user, redirects to dashboard

**Technology Stack**:
- Next.js 15.5.9 with App Router
- React 19.2.1
- TypeScript 5
- Tailwind CSS 3.4.0
- Framer Motion 12.23.26 (animations)
- Supabase JS 2.89.0 (auth + database)
- OpenAI 6.15.0 (AI chat)
- Recharts 3.6.0 (data visualization)
- SWR 2.3.7 (data fetching)

#### Main Pages

**Dashboard Page** (`frontend/app/dashboard/page.tsx:24-52`):
- 5 interactive cards in grid layout
- Top row (50/50): NotesGoalsCard, AIChatCard
- Bottom row (3 equal): ToDoCard, ProgressPatternsCard, TherapistBridgeCard
- Wrapped in: ProcessingProvider → SessionDataProvider → Auto-refresh on upload

**Upload Page** (`frontend/app/patient/upload/page.tsx:22-86`):
- 3 view states: upload, processing, results
- Upload: FileUploader (drag-drop), AudioRecorder (in-browser recording)
- Processing: UploadProgress (real-time polling)
- Results: ResultsView (transcript display)
- Integrated with ProcessingContext for dashboard refresh

**Sessions Page**: Lists all therapy sessions with search/filter

**Ask AI Page**: Direct chat interface with Dobby AI

#### Key Components

**NotesGoalsCard** (`frontend/app/patient/components/NotesGoalsCard.tsx:23-178`):
- Compact: AI summary paragraph, top 3 achievements, top 3 focus areas
- Expanded modal: Full achievements list, all focus areas, additional sections
- Fonts: Crimson Pro (serif) for content, Inter (sans) for labels
- Colors: Teal (#5AB9B4) light, purple (#a78bfa) dark
- Accessibility: Focus trap, Escape handler, scroll lock

**AIChatCard** (`frontend/app/patient/components/AIChatCard.tsx:147-682`):
- Compact features:
  - DobbyLogo with illuminating glow effect
  - Fullscreen button
  - Functional chat input (500 char limit)
  - Mode toggle: AI vs Therapist
  - Long-press (7 seconds) to expand - video game style loading bar
  - Text selection detection prevents accidental expansion
- Fullscreen: Immersive chat via FullscreenChat component, conversation history sidebar
- Message rendering: User bubbles (solid color), AI bubbles (with avatar + markdown)
- Streaming: Word-by-word SSE responses
- Shared state: Between collapsed and fullscreen

**SessionCard** (`frontend/app/patient/components/SessionCard.tsx:38-495`):
- Fixed dimensions: 329.3px × 290.5px
- Two variants:
  1. Normal: Mood emoji, date, duration, summary (3 line clamp), 1 strategy, 1 action
  2. Breakthrough: Gold star instead of mood, full-screen overlay effect on hover, border changes to gold
- Colors: Teal/Purple accent, Gold (#FFCA00/#FFE066) for breakthroughs
- Data: Summary from Wave 1 AI or fallback, techniques/actions from session data
- Hover: Scale (1.01x) and shadow

**NavigationBar** (`frontend/components/NavigationBar.tsx:52-259`):
- Sticky header (60px height)
- Left: TheraBridge logo + theme toggle
- Center: Nav links (Dashboard, Sessions, Upload, Ask AI) with active page indicator
- Right: Reset Demo button + full logo
- Theme toggle: Sun/moon icon with glow
- Reset confirmation modal
- Recently modified according to git status

#### State Management

**AuthContext** (`frontend/contexts/AuthContext.tsx:50-143`):
- Converts Supabase Auth user to application User type
- Derives data from `auth.user_metadata`: first_name, last_name, default role 'patient'
- Dev bypass mode: Creates mock user when `NEXT_PUBLIC_DEV_BYPASS_AUTH=true`
- Provides: user, session, loading, isAuthenticated, signOut(), logout()

**SessionDataContext** (`frontend/app/patient/contexts/SessionDataContext.tsx:46-72`):
- Wraps `usePatientSessions` hook
- Auto-refreshes when processing completes
- Exposes: sessions, tasks, timeline, unifiedTimeline, majorEvents, refresh(), updateMajorEventReflection()
- Computed: sessionCount, majorEventCount, isEmpty

**ProcessingContext** (`frontend/contexts/ProcessingContext.tsx:49-161`):
- Global context for audio processing status
- Wraps `useProcessingStatus` hook
- Poll interval: 3 seconds, max poll time: 10 minutes
- Functions: startTracking(sessionId), isSessionProcessing(sessionId), getSessionProgress(sessionId)
- Callbacks: onComplete(callback), lastCompletedSessionId
- Fires callbacks on processing complete/failed

**ThemeContext**:
- Provided by `next-themes` library
- Dark/light mode switching
- Persists in localStorage

#### AI Chat System

**Chat API** (`frontend/app/api/chat/route.ts:31-350`):
- `POST /api/chat` - Streaming GPT-4o chat with context injection
- Processing flow:
  1. Usage tracking via Supabase RPC
  2. Get or create conversation in `chat_conversations`
  3. Save user message to `chat_messages`
  4. Crisis detection via `detectCrisisIndicators(message)`
  5. Build patient context (profile, sessions, goals, analytics, timeline)
  6. Format context for AI
  7. Combine Dobby prompt + patient context + crisis context
  8. Load previous 20 messages
  9. Stream GPT-4o response
  10. Save assistant response
  11. Auto-generate title on first exchange
- Stateless bypass: Skip database if `ENABLE_CHAT_DB_PERSISTENCE !== 'true'`
- Returns: SSE stream with JSON payloads

**Context Builder** (`frontend/lib/chat-context.ts:50-151`):
- `buildChatContext(userId, sessionId?)` returns ChatContext:
  - user: name, firstName, role, therapistName
  - sessions: count, recent (5), summary, topTopics (5), learnedTechniques, moodTrend, averageMood, keyInsights
  - goals: Active and completed with progress bars
  - timeline: milestones count, recentEvents, daysInTherapy
  - currentSession: Full data if viewing specific session
- Analytics: analyzeSessionHistory(), calculateMoodTrend(), countMilestones(), extractRecentEvents()
- Formatting: formatContextForAI() creates structured prompt sections

**Dobby System Prompt** (`frontend/lib/dobby-system-prompt.ts`):
- Medical knowledge: Medication education, symptom explanation, technique guidance
- Crisis protocol: Detection keywords, response pattern, hotline resources (988, Crisis Text Line), escalation flags
- Techniques: TIPP, 5-4-3-2-1, Box Breathing, Wise Mind, Opposite Action
- Communication: Validation-first, personalization rules, response length guidance

**Speaker Role Detection** (`frontend/lib/speaker-role-detection.ts`):
- Multi-heuristic role assignment: First-speaker heuristic, speaking ratio heuristic
- Transforms SPEAKER_00/SPEAKER_01 → Therapist/Client

#### Upload & Processing Flow

**FileUploader** (`frontend/app/patient/upload/components/FileUploader.tsx:22-240`):
- Drag-and-drop interface
- Accepted: MP3, WAV, M4A, OGG, FLAC, AAC, WEBM
- Max size: 100MB
- Validation: File type + size check
- Upload: POST to `/api/upload` → receive session_id → call onUploadSuccess(sessionId, file)
- Mock IDs: MOCK_PATIENT_ID, MOCK_THERAPIST_ID
- Recently modified according to git status

**Processing Status Tracking**:
1. Upload page calls `startTracking(sessionId)` on success
2. `ProcessingContext` polls via `useProcessingStatus` hook (3s interval, 10min max)
3. Status: pending → processing (0-100%) → completed/failed
4. On completion: Fire callbacks
5. `ProcessingRefreshBridge` listens for completion
6. Triggers `SessionDataContext.refresh()` to reload dashboard

#### Styling

**Tailwind Configuration** (`frontend/tailwind.config.ts:3-63`):
- Dark mode: Class-based
- Extended theme: Font families (inter, crimson, jakarta, dm, nunito), HSL-based colors, variable border radius
- Content paths: pages, components, app directories

**Color System**:
- Light mode: Background (#ECEAE5 cream), cards (white to #FFF9F5), primary (#5AB9B4 teal), text (#1a1a1a)
- Dark mode: Background (#1a1625 purple-black), cards (#2a2435 to #1a1625), primary (#a78bfa purple), text (#e3e4e6)
- Accent by component: Dashboard teal/purple, breakthrough gold, mood green/blue/rose, therapist orange

**Typography**:
- Card titles: system-ui, font-light (300), 18px, centered
- Modal titles: system-ui, font-light (300), 24px
- Session content: Crimson Pro (serif), 13-14px, light weight
- UI labels: Inter (sans), 11px uppercase, 500 weight, 1px letter-spacing
- Body: font-light (300) across components

#### Testing Infrastructure

**Test Framework**: Playwright v1.57.0 (E2E)

**Configuration** (`frontend/playwright.config.ts`):
- Test directory: ./tests
- Fully parallel execution
- HTML reporter
- CI: 2 retries, 1 worker, forbidOnly
- Dev: 0 retries, parallel workers
- Browser: Chromium (Desktop Chrome)
- Base URL: http://localhost:3000
- Trace: on-first-retry
- Screenshots: only-on-failure
- Web server: `npm run dev` with reuse

**Test Files** (19 files in `frontend/tests/`):
- Layout: modal-positioning.spec.ts, pagination-position.spec.ts, sessions-page-layout.spec.ts
- Timeline: timeline-mixed-events.spec.ts (8 tests), timeline-major-event-modal.spec.ts (14 tests), timeline-search.spec.ts (11 tests), timeline-export.spec.ts (9 tests)
- UI: card-styling.spec.ts, tooltip-visibility.spec.ts, tooltip-alignment.spec.ts, ui-regression-check.spec.ts
- Features: dobby-chat.spec.ts, demo-button.spec.ts variants
- Navigation: navigation-debug.spec.ts

**Recent Changes** (from git status):
- Modified: NavigationBar.tsx, AddSessionCard.tsx, DeepAnalysisSection.tsx, ProgressPatternsCard.tsx
- Modified upload components: AudioRecorder.tsx, FileUploader.tsx, TranscriptUploader.tsx
- Modified: DemoTranscriptUploader.tsx
- New hook: useProgressMetrics.ts

**No CI/CD**: Tests run locally with `npx playwright test`

---

### 4. Audio Transcription Pipeline State

**Location**: `audio-transcription-pipeline/`

**Entry Points**:
- CPU/API: `src/pipeline.py:309-344` - AudioTranscriptionPipeline.process()
- GPU: `src/pipeline_gpu.py:116-206` - GPUTranscriptionPipeline.process() with provider auto-detection

**Technology Stack**:
- Python 3.13.9
- OpenAI Whisper (API) or faster-whisper (local GPU)
- PyAnnote 3.1+ for speaker diarization
- PyTorch + CUDA for GPU acceleration
- pydub, librosa, torchaudio for audio processing

#### Pipeline Stages

**1. Audio Preprocessing** (`src/pipeline.py:29-145`):
- AudioPreprocessor.preprocess() (lines 42-91):
  - Loads audio with pydub
  - Trims leading/trailing silence (-40dB threshold)
  - Normalizes volume to -20dBFS with 0.1dB headroom
  - Converts to mono 16kHz (Whisper requirement)
  - Exports as MP3 at 64kbps
  - Validates file size < 25MB (Whisper API limit)

**2A. CPU/API Transcription** (`src/pipeline.py:147-306`):
- WhisperTranscriber class:
  - Model: "whisper-1" (OpenAI)
  - Rate limiting: 0.5s delay between calls
  - Retry logic: MAX_RETRIES=5, exponential backoff
  - Response format: verbose_json for segment timestamps
  - Returns: {segments: [{start, end, text}], full_text, language, duration}

**2B. GPU Transcription** (`src/pipeline_gpu.py:250-357`):
- _transcribe_gpu():
  - Model: faster-whisper "large-v3"
  - Lazy loading with GPU/CPU fallback on cuDNN errors
  - Config-determined compute type (int8/float16/float32) and batch size
  - VAD filtering: min_silence_duration_ms=500, speech_pad_ms=400
  - Beam size=5, temperature=0 for quality
  - GPU memory cleanup after transcription
  - Returns: {segments, text, language, duration}

**3. Speaker Diarization** (`src/pipeline_gpu.py:358-440`):
- _diarize_gpu():
  - Model: pyannote/speaker-diarization-3.1
  - Requires HF_TOKEN environment variable
  - Loads audio with torchaudio, moves to GPU
  - Returns speaker turns: [{speaker: "SPEAKER_00", start, end}, ...]
  - GPU cleanup: free tensors, unload model, clear CUDA cache

**4. Speaker Alignment** (`src/pipeline_gpu.py:441-506`):
- _align_speakers_gpu():
  - GPU tensor setup for segment and turn times
  - Vectorized overlap computation: max(seg_start, turn_start), min(seg_end, turn_end)
  - Finds turn with maximum overlap per segment
  - 50% threshold: Only assign speaker if overlap > 50% of segment duration
  - Marks "UNKNOWN" if threshold not met
  - Returns: [{start, end, text, speaker}, ...]

#### GPU Configuration & Provider Detection

**Provider Detection** (`src/gpu_config.py:75-109`):
- Checks in priority order:
  1. Google Colab: /content directory + COLAB_GPU env var
  2. Vast.ai: VAST_CONTAINERLABEL or VAST_CONTAINER_USER
  3. RunPod: RUNPOD_POD_ID
  4. Paperspace: PAPERSPACE_METRIC_URL or /storage directory
  5. Lambda Labs: hostname contains "lambda"
  6. Docker: /.dockerenv file
  7. Fallback: UNKNOWN

**Optimal Configuration** (`src/gpu_config.py:112-187`):
- GPU detection via torch.cuda (device name, VRAM)
- Compute type selection:
  - A100/H100: float16 + TF32 enabled, batch size 16
  - RTX 3090/4090/A6000: int8, TF32 disabled, batch size 8
  - Others: int8, TF32 disabled, batch size 4
- Cache directory by provider:
  - Colab: /content/models
  - Vast.ai/RunPod: /workspace/models
  - Paperspace: /storage/models
  - Other: ~/.cache/huggingface
- Sets TRANSFORMERS_CACHE and HF_HOME env vars

#### Performance Logging

**PerformanceLogger** (`src/performance_logger.py`):
- Pipeline-level tracking: start_pipeline(), end_pipeline()
- Stage tracking: start_stage(), end_stage()
- GPU monitoring: Background thread sampling GPU utilization and memory
- Subprocess tracking: context manager for subprocess timing
- Report generation: JSON and text reports with stage breakdowns, percentages
- Saves to: outputs/performance_logs/

#### GPU Audio Operations

**GPUAudioProcessor** (`src/gpu_audio_ops.py`):
- load_audio() (lines 65-96): Load to GPU, convert to mono
- resample_gpu() (lines 98-107): High-quality via julius library
- normalize_gpu() (lines 178-198): Peak normalization to -20dBFS
- trim_silence_gpu() (lines 134-176): Silence detection via dB thresholding (disabled by default)
- detect_silence_gpu() (lines 109-132): dB scale conversion, morphological operations
- save_audio_gpu() (lines 200-231): Move to CPU, save via torchaudio

#### Key Patterns

1. **Provider-Agnostic GPU Abstraction**: Strategy pattern for optimal config across Vast.ai, RunPod, Paperspace, Colab, Lambda
2. **GPU Memory Management**: Context manager with __enter__/__exit__ for guaranteed cleanup
3. **Automatic Fallback**: Transcriber catches cuDNN errors, falls back to CPU
4. **Version Compatibility**: Adapter pattern in pyannote_compat.py for 3.x vs 4.x
5. **GPU Tensor Vectorization**: Batch processing via torch.maximum/minimum for parallel overlap calculation

#### Testing Infrastructure

**Test Framework**: pytest with smart skipping

**Fixtures** (`audio-transcription-pipeline/tests/conftest.py`):
- Sample audio: sample_cbt_session(), sample_person_centered(), sample_compressed_cbt(), any_sample_audio()
- Environment: openai_api_key(), hf_token()
- Directories: outputs_dir(), processed_dir()
- Mock GPU: mock_gpu_available(), mock_cudnn_error(), mock_whisper_model_with_cudnn_error()

**Custom Markers**:
- @pytest.mark.requires_sample_audio
- @pytest.mark.requires_openai
- @pytest.mark.requires_hf
- @pytest.mark.integration

**Auto-Skip Logic**: pytest_collection_modifyitems() automatically skips tests if resources missing

**Test Files** (18+ files):
- Full pipeline: test_full_pipeline.py, test_full_pipeline_improved.py, test_full_pipeline_demo.py
- Components: test_diarization.py, test_performance_logging.py
- Format: test_formatted_output.py variants
- API: test_wave2_whisper_api.py
- CPU: test_cpu_pipeline_file1.py, test_quick_pipeline.py
- YouTube: test_youtube_pipeline.py
- GPU: test_gpu_optimizations.py
- Validation: test_hf_token.py, validate_fixtures.py, validate_optimizations.py
- Docker: test_docker_build.py
- Config: test_mood_config.py, verify_model_config.py, verify_model_imports.py
- Technique: test_technique_validation.py
- Integration: batch_process_all_sessions.py, test_complete_demo.py
- Logging: test_logging_simple.py, test_fixtures_example.py

**No CI/CD**: Tests run locally with `pytest` commands

#### Configuration

**Audio Preprocessing**:
- Target format: MP3 (CPU), WAV (GPU)
- Sample rate: 16000 Hz (Whisper requirement)
- Bitrate: 64kbps (MP3)
- Max file size: 25MB (Whisper API limit)

**Whisper API**:
- Model: whisper-1
- Language: en
- Response format: verbose_json
- Max retries: 5
- Exponential backoff: 1-60s
- Rate limit delay: 0.5s

**Faster-Whisper GPU**:
- Model: large-v3
- Beam size: 5
- Temperature: 0
- VAD filter: Enabled
- VAD min silence: 500ms
- VAD speech padding: 400ms

**Speaker Diarization**:
- Model: pyannote/speaker-diarization-3.1
- Num speakers: 2 (default, configurable)
- Token: HF_TOKEN environment variable

**Speaker Alignment**:
- Minimum overlap: 50% of segment duration
- Fallback: "UNKNOWN" if threshold not met

**GPU Performance Tuning**:
- A100/H100: float16 + TF32 enabled
- RTX 3090/4090: int8, TF32 disabled
- Others: int8, conservative batch size 4

#### Scripts for Execution

**CPU Setup** (`scripts/setup.sh`):
- Checks Python 3, ffmpeg
- Creates and activates virtual environment
- Interactive Whisper selection (API vs local)
- Creates output directories
- Creates .env with API key template

**GPU Setup** (`scripts/setup_gpu.sh`):
- Detects Python and GPU (nvidia-smi)
- Verifies NVIDIA GPU, displays CUDA version
- Creates virtual environment
- Installs PyTorch with matching CUDA version (11.x or 12.x)
- Installs GPU dependencies (faster-whisper, pyannote.audio, julius)
- Verifies installation (CUDA availability, module imports)
- Creates .env with HF_TOKEN template

**Running**:
- CPU: `python tests/test_full_pipeline.py tests/samples/audio.mp3`
- GPU: `python src/pipeline_gpu.py audio.mp3 --num-speakers 2`

---

### 5. Recent Changes & Git History

**Current Branch**: main

**Recent Commits** (from git status and Session Log):
- **227586b** (HEAD) - "Remove test button and replace brain emoji with Dobby logo"
- **ff143ae** - "Fix fullscreen session card header font alignment and centering"
- **5b30516** - "Fix therapist mode work-in-progress message in collapsed chat"
- **508d760** - "Fix expanded session card header fonts to match collapsed cards"
- **b91c45f** - "Fix dark mode consistency: match session cards to Your Journey card"

**Modified Files** (not yet committed):
- `backend/app/routers/sessions.py` - Recent endpoint changes
- `frontend/app/patient/components/AddSessionCard.tsx`
- `frontend/app/patient/components/DeepAnalysisSection.tsx`
- `frontend/app/patient/components/ProgressPatternsCard.tsx`
- `frontend/app/patient/upload/components/AudioRecorder.tsx`
- `frontend/app/patient/upload/components/FileUploader.tsx`
- `frontend/app/patient/upload/components/TranscriptUploader.tsx`
- `frontend/app/upload/components/DemoTranscriptUploader.tsx`
- `frontend/components/NavigationBar.tsx`

**Untracked Files** (new, not yet committed):
- Multiple hackathon submission markdown files
- Progress metrics documentation (PROGRESS_METRICS_README.md, QUICK_START_PROGRESS_METRICS.md)
- Backend service: `backend/app/services/progress_metrics_extractor.py`
- Backend results: `backend/progress_metrics_extraction_results.json`
- Frontend hook: `frontend/app/patient/hooks/useProgressMetrics.ts`

**Session Log Highlights** (from .claude/CLAUDE.md):

**2025-12-22** - AI-Powered Topic Extraction System ✅
- Complete topic/metadata extraction using GPT-4o-mini
- Database schema additions: topics[], action_items[], technique, summary, extraction_confidence
- Created views: patient_topic_frequency, patient_technique_history
- POST /api/sessions/{id}/extract-topics endpoint
- 100% success rate on 12 mock sessions

**2025-12-22** - AI-Powered Mood Analysis System ✅
- Complete mood extraction using GPT-4o-mini
- Database schema: mood fields + patient_mood_trends view
- POST /api/sessions/{id}/analyze-mood, GET /api/sessions/patient/{id}/mood-history endpoints
- Frontend hook: useMoodAnalysis.ts
- Integrated with ProgressPatternsCard

**2025-12-22** - AI Bot Enhancement ✅
- Real-time dashboard updates with ProcessingContext
- Comprehensive Dobby system prompt (medical knowledge, crisis protocol, techniques)
- Enhanced context injection (mood trends, technique memory, goal progress, therapist name, insights)
- Crisis detection in user messages
- Speaker role detection (multi-heuristic)

**2025-12-21** - Timeline Enhancement ✅
- Mixed timeline (sessions + major events)
- MajorEventModal, ExportDropdown components
- Timeline search/filter with debouncing
- PDF export via print dialog
- 42 Playwright E2E tests

**2025-12-21** - Font Alignment & Session Card Text Fix ✅
- All cards aligned to system-ui, font-light (300), 18px centered
- Removed Crimson Pro from Notes/Goals (now matches)
- Fixed session card text overflow with min-w-0 and break-words

**2025-12-21** - Fixed Modal Positioning Bug ✅
- Framer Motion scale animation overwriting CSS transform
- Updated modalVariants to include x: '-50%', y: '-50%' in all states
- Removed conflicting inline transform from card components

**2025-12-18** - Added crawl4ai Skill ✅
- Comprehensive web crawling and data extraction skill
- Schema-based extraction (10-100x faster than LLM)
- JavaScript-heavy page support
- Batch/concurrent crawling

**2025-12-17** - Feature 1 Authentication Completion ✅
- Fixed table naming conflict (sessions vs auth_sessions)
- Added missing user columns: first_name, last_name, is_verified
- Created therapist_patients junction table
- Applied migration successfully

**2025-12-11** - Frontend Fixes & API Integration Layer
- Added ErrorBoundary, ComingSoonButton
- Created API layer: api-config.ts, api-client.ts
- useSessionProcessing, useSessionData hooks
- UploadModal component
- Build verified

---

### 6. Build & Test Status

**Backend**:
- Python 3.13.9 standardized
- Dependencies: requirements.txt with FastAPI, OpenAI, Supabase, pytest
- CI/CD: GitHub Actions with PostgreSQL service, coverage (80% minimum), 2 retries
- Test files: 20+ with fixtures for API keys, database, demo sessions
- Coverage reports: Terminal, XML, HTML (30-day retention)

**Frontend**:
- Node >=20.9.0, npm >=10.0.0
- TypeScript 5 with strict mode
- Build scripts: dev, dev:network, build, start, lint
- Test framework: Playwright v1.57.0 (19 E2E test files)
- Config: Fully parallel execution, HTML reporter, trace on-first-retry
- No CI/CD (local testing only)

**Audio Pipeline**:
- Python 3.13.9 standardized
- Dependencies: OpenAI Whisper, PyAnnote 3.1+, PyTorch + CUDA
- Test framework: pytest with smart auto-skip logic
- Custom markers: requires_sample_audio, requires_openai, requires_hf, integration
- Test files: 18+ with component, integration, validation, GPU tests
- Execution scripts: Shell scripts for CPU/GPU setup and execution
- No CI/CD (local testing only)

---

## Code References

### Backend Key Files
- `backend/app/main.py:22-40` - FastAPI initialization
- `backend/app/routers/sessions.py` - All session endpoints (recently modified)
- `backend/app/services/mood_analyzer.py` - GPT-5-nano mood analysis
- `backend/app/services/topic_extractor.py` - GPT-5-mini topic extraction
- `backend/app/services/breakthrough_detector.py` - GPT-5 breakthrough detection
- `backend/app/services/deep_analyzer.py` - GPT-5.2 deep synthesis
- `backend/app/services/analysis_orchestrator.py` - Wave 1 + Wave 2 orchestration
- `backend/app/config/model_config.py:39-80` - GPT-5 model registry
- `backend/.github/workflows/backend-tests.yml` - CI/CD pipeline

### Frontend Key Files
- `frontend/app/page.tsx:8-48` - Demo initialization and redirect
- `frontend/app/dashboard/page.tsx:24-52` - Main dashboard layout
- `frontend/app/patient/upload/page.tsx:22-86` - Upload with processing states
- `frontend/app/patient/components/SessionCard.tsx:38-495` - Session card with breakthrough variant
- `frontend/app/patient/components/AIChatCard.tsx:147-682` - Dobby chat with long-press
- `frontend/app/api/chat/route.ts:31-350` - Streaming GPT-4o chat API
- `frontend/lib/chat-context.ts:50-151` - Context builder
- `frontend/lib/dobby-system-prompt.ts` - Dobby AI companion definition
- `frontend/contexts/ProcessingContext.tsx:49-161` - Global processing context
- `frontend/components/NavigationBar.tsx:52-259` - Navigation (recently modified)
- `frontend/playwright.config.ts` - E2E test configuration

### Audio Pipeline Key Files
- `audio-transcription-pipeline/src/pipeline.py:309-344` - CPU/API pipeline entry
- `audio-transcription-pipeline/src/pipeline_gpu.py:116-206` - GPU pipeline entry
- `audio-transcription-pipeline/src/gpu_config.py:75-109` - Provider detection
- `audio-transcription-pipeline/src/performance_logger.py` - Performance monitoring
- `audio-transcription-pipeline/tests/conftest.py` - Test fixtures with auto-skip
- `audio-transcription-pipeline/scripts/setup.sh` - CPU environment setup
- `audio-transcription-pipeline/scripts/setup_gpu.sh` - GPU environment setup

---

## Architecture Documentation

### Monorepo Pattern
- Single repository with 4 independent projects
- Each project has own virtual environment, dependencies, configuration
- Shared documentation at root level
- Independent deployment capabilities

### Two-Wave AI Analysis Pipeline (Backend)
- **Wave 1 (Parallel)**: Mood, Topics, Breakthrough - run simultaneously for speed
- **Wave 2 (Sequential)**: Deep Analysis - requires Wave 1 complete, synthesizes all data
- **Dependency Management**: Orchestrator enforces Wave 1 completion before Wave 2 starts
- **Retry Logic**: Exponential backoff, 300s timeout per wave, comprehensive logging

### Real-Time Dashboard Updates (Frontend)
- ProcessingContext tracks upload status via polling (3s interval)
- ProcessingRefreshBridge listens for completion events
- SessionDataContext refreshes on completion
- Dashboard auto-updates without page reload

### GPU Provider Abstraction (Audio Pipeline)
- Single codebase works across Vast.ai, RunPod, Paperspace, Colab, Lambda, local
- Auto-detection via environment variables and filesystem checks
- Optimal configuration per GPU type (A100/H100 float16, RTX int8)
- Automatic CPU fallback for cuDNN compatibility issues

### AI Context Injection (Frontend)
- buildChatContext() aggregates: user profile, session history, goals, timeline
- formatContextForAI() structures context into prompt sections
- Full transcripts for recent 3 sessions
- Mood trend analysis compares recent vs older sessions
- Technique memory detects learned coping skills from history

### Version Compatibility (Audio Pipeline)
- pyannote_compat.py adapter pattern handles 3.x vs 4.x differences
- Single extract_annotation() function works across versions
- No duplicate code paths

---

## Open Questions

None - all research tasks completed successfully. The codebase is well-documented and organized, with clear separation of concerns across the monorepo structure.

---

## Related Research

This is the first comprehensive codebase analysis. Future research documents should be stored in this directory with format: `YYYY-MM-DD-description.md`

---

*This research document captures the complete state of the TherapyBridge codebase as of December 28, 2025. All findings are based on live code analysis across backend, frontend, and audio pipeline projects.*
