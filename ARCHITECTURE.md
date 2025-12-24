# TherapyBridge Architecture Map

Comprehensive guide to the entire codebase structure, data flow, and integration points.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Backend Structure](#backend-structure)
4. [Frontend Structure](#frontend-structure)
5. [Audio Pipeline](#audio-pipeline)
6. [Data Flow](#data-flow)
7. [Key Integration Points](#key-integration-points)
8. [Current Implementation Status](#current-implementation-status)
9. [Critical Files Reference](#critical-files-reference)

---

## System Overview

TherapyBridge is a three-layer distributed system:

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1: FRONTEND (Next.js 16 + React 19 + Tailwind)       │
│  - Patient Dashboard (dashboard-v3)                          │
│  - Session Visualization & Analysis                          │
│  - AI Chat (Dobby)                                           │
│  - Audio Upload Interface                                    │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST APIs
┌────────────────────────▼────────────────────────────────────┐
│  LAYER 2: BACKEND (FastAPI + Supabase PostgreSQL)           │
│  - Session Management                                        │
│  - AI Extraction Services (Mood, Topics, Breakthroughs)     │
│  - Analysis Orchestration (Wave 1 & Wave 2)                 │
│  - Progress Metrics & Deep Analysis                          │
└────────────────────────┬────────────────────────────────────┘
                         │ File I/O & Data
┌────────────────────────▼────────────────────────────────────┐
│  LAYER 3: AUDIO PIPELINE (Python + OpenAI + pyannote)       │
│  - Audio Upload & Preprocessing                             │
│  - Whisper Transcription (API or GPU)                        │
│  - Speaker Diarization (pyannote 3.1)                       │
│  - Speaker Role Detection (Therapist/Client)                │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Role |
|-----------|-----------|------|
| Frontend | Next.js 16 + React 19 + Tailwind CSS + shadcn/ui | UI/UX, client-side logic |
| Backend | FastAPI + Python 3.13.9 | API endpoints, AI services |
| Database | Supabase (PostgreSQL) + pgvector | Sessions, users, analysis results |
| Auth | Demo mode (frontend) | Development auth flow |
| Transcription | OpenAI Whisper API | Audio to text |
| Diarization | pyannote.audio 3.1 | Speaker detection |
| AI Analysis | GPT-4o / GPT-4o-mini | Topic extraction, mood, breakthroughs |
| Storage | Supabase Storage | Audio file storage |

---

## Architecture Diagram

### Complete Request/Response Flow

```
FRONTEND                          BACKEND                      DATABASE
┌──────────────┐                ┌──────────────┐              ┌──────────┐
│   Upload     │                │   Upload     │              │ Therapy  │
│   Page       │───POST audio──▶│   Endpoint   │─────────────▶│ Sessions │
│              │                │              │              │ Table    │
└──────────────┘                └──────────────┘              └──────────┘
      │                               │
      │                               ├─▶ Call OpenAI Whisper (CPU/API)
      │                               │
      │                               ├─▶ pyannote Diarization
      │                               │
      │                               └─▶ Speaker Role Detection
      │
┌──────────────┐                ┌──────────────┐
│   Status     │                │   Status     │
│   Polling    │◀──GET status──│   Endpoint   │
│  (every 2s)  │                │              │
└──────────────┘                └──────────────┘
      │
      ├─▶ When complete: triggers analysis
      │
┌──────────────┐                ┌──────────────┐
│   Dashboard  │                │   Demo Init  │
│   Loads      │───GET data────▶│   Endpoint   │
│   Sessions   │                │              │
└──────────────┘                └──────────────┘
      │
      ├─▶ usePatientSessions hook
      ├─▶ Fetches 12 mock sessions OR real API data
      ├─▶ Displays in SessionCardsGrid
      │
      └─▶ AI Chat (Dobby) with context injection
           ├─▶ Mood trends (from analysis)
           ├─▶ Technique history
           ├─▶ Progress indicators
           └─▶ Crisis detection keywords
```

---

## Backend Structure

### Directory Layout

```
backend/
├── app/
│   ├── main.py                      # FastAPI app entry point
│   ├── config.py                    # Environment configuration
│   ├── database.py                  # Supabase client & helpers
│   ├── middleware/
│   │   ├── demo_auth.py             # Demo mode authentication
│   │   └── __init__.py
│   ├── routers/
│   │   ├── sessions.py              # Session CRUD + analysis endpoints
│   │   └── demo.py                  # Demo initialization endpoints
│   └── services/
│       ├── breakthrough_detector.py # AI breakthrough detection
│       ├── mood_analyzer.py         # AI mood analysis service
│       ├── topic_extractor.py       # AI topic extraction
│       ├── deep_analyzer.py         # Wave 2 deep clinical analysis
│       ├── prose_generator.py       # Prose narrative generation
│       ├── speaker_labeler.py       # Therapist/Client role detection
│       ├── technique_library.py     # Therapeutic technique definitions
│       ├── analysis_orchestrator.py # Coordinates all analyses
│       └── progress_metrics_extractor.py  # Progress tracking
├── tests/
│   ├── test_full_pipeline.py        # Complete pipeline test
│   ├── test_mood_analysis.py        # Mood analyzer tests
│   ├── test_topic_extraction.py     # Topic extractor tests
│   └── test_breakthrough_detection.py
├── requirements.txt                 # Python dependencies
├── .env                             # Environment variables
└── README.md
```

### API Endpoints (Sessions Router)

**Base URL:** `http://localhost:8000/api/sessions`

#### Session CRUD
```
GET    /                            # List all sessions (paginated)
POST   /                            # Create new session
GET    /{session_id}                # Get single session with breakthrough details
GET    /patient/{patient_id}        # Get all sessions for a patient
```

#### Transcript & Processing
```
POST   /{session_id}/upload-transcript      # Upload transcript + trigger analysis
POST   /{session_id}/process                # Manually trigger processing
GET    /{session_id}/analysis-status        # Get Wave 1 & Wave 2 status
```

#### Analysis Endpoints
```
POST   /{session_id}/analyze-mood           # Analyze session mood
GET    /patient/{id}/mood-history           # Get mood timeline
POST   /{session_id}/extract-topics         # Extract topics + action items
POST   /{session_id}/analyze-deep           # Wave 2 deep clinical analysis
POST   /{session_id}/detect-breakthrough    # Breakthrough detection
POST   /{session_id}/label-speakers         # Speaker role detection
GET    /{session_id}/techniques             # Get session techniques
GET    /techniques/{technique}/definition   # Look up technique definition
```

#### Reporting
```
GET    /patient/{patient_id}/consistency    # Consistency metrics
GET    /patient/{patient_id}/progress       # Progress metrics summary
```

### Demo Router

**Base URL:** `http://localhost:8000/api/demo`

```
POST   /init               # Initialize demo with token + 12 mock sessions
GET    /status             # Check demo status + analysis progress
POST   /reset              # Clear demo data + reinitialize
```

### Core Services

#### 1. Breakthrough Detector (`breakthrough_detector.py`)
**Purpose:** AI detection of therapeutic breakthroughs (genuine insights, shifts)

**Key Classes:**
- `BreakthroughDetector` - Main service class
- `BreakthroughCandidate` - Detected breakthrough moment
- `SessionBreakthroughAnalysis` - Complete session analysis

**Key Methods:**
```python
analyzer = BreakthroughDetector(api_key)
analysis = analyzer.analyze_session(transcript, session_metadata)

# Returns:
# - has_breakthrough: bool
# - breakthrough_candidates: List[BreakthroughCandidate]
# - primary_breakthrough: BreakthroughCandidate (highest confidence)
# - session_summary: str
# - emotional_trajectory: str
```

**Model:** GPT-4o-mini (cost: ~$0.01/session)

#### 2. Mood Analyzer (`mood_analyzer.py`)
**Purpose:** AI analysis of patient emotional state

**Key Classes:**
- `MoodAnalyzer` - Main service
- `MoodAnalysis` - Mood data with score (0.0-10.0)

**Key Methods:**
```python
analyzer = MoodAnalyzer(api_key)
mood = analyzer.analyze_session(transcript)

# Returns:
# - mood_score: float (0.0-10.0, increments of 0.5)
# - confidence: float (0.0-1.0)
# - rationale: str (why this score)
# - key_indicators: List[str] (emotional signals detected)
# - emotional_tone: str (descriptive label)
```

**Model:** GPT-4o-mini (cost: ~$0.01/session)

#### 3. Topic Extractor (`topic_extractor.py`)
**Purpose:** Extract main topics and action items from session

**Key Classes:**
- `TopicExtractor` - Main service
- `SessionMetadata` - Extracted topics, actions, summary

**Key Methods:**
```python
extractor = TopicExtractor(api_key)
metadata = extractor.extract_session_metadata(transcript)

# Returns:
# - topics: List[str] (1-2 main topics)
# - action_items: List[str] (2 action items)
# - technique: str (primary therapeutic technique)
# - summary: str (max 150 chars, active voice)
# - confidence: float
```

**Model:** GPT-4o-mini (cost: ~$0.01/session)

#### 4. Deep Analyzer (`deep_analyzer.py`)
**Purpose:** Wave 2 analysis - comprehensive clinical insights

**Key Components:**
- Progress indicators (symptom reduction, skill development)
- Therapeutic insights (key realizations, patterns)
- Coping skills assessment
- Therapeutic relationship evaluation
- Recommendations for practice

**Complex nested JSONB structure** stored in database.

#### 5. Analysis Orchestrator (`analysis_orchestrator.py`)
**Purpose:** Coordinates all analyses across waves

**Two-Wave Pipeline:**

**Wave 1 (Immediate):**
- Topic extraction (topics, action items, technique, summary)
- Mood analysis (score, confidence, indicators)
- Completed within seconds

**Wave 2 (Async):**
- Deep clinical analysis (progress, insights, skills, relationship)
- Prose narrative generation
- Breakthrough detection
- Completed within minutes

**Key Functions:**
```python
# Full pipeline (both waves)
result = await analyze_session_full_pipeline(
    session_id, 
    transcript, 
    ai_client
)

# Returns orchestrated results from all services
```

#### 6. Speaker Labeler (`speaker_labeler.py`)
**Purpose:** Identify Therapist vs Client speakers in diarized segments

**Detection Heuristics:**
- First-speaker heuristic (therapist usually opens)
- Speaking ratio heuristic (therapist ~30-40%, client ~60-70%)
- Combined confidence scoring

**Key Functions:**
```python
result = label_session_transcript(
    diarized_segments,  # From pyannote
    therapist_name     # Optional
)

# Returns:
# - therapist_speaker_id: str (e.g., "SPEAKER_00")
# - patient_speaker_id: str (e.g., "SPEAKER_01")
# - confidence: float
# - labeled_transcript: List[Dict]  # With speaker roles
```

#### 7. Technique Library (`technique_library.py`)
**Purpose:** Lookup definitions of therapeutic techniques

**Database:**
```python
TECHNIQUE_DATABASE = {
    "CBT - Cognitive Restructuring": "Identifies and challenges automatic negative thoughts...",
    "DBT - Mindfulness": "Focuses on present-moment awareness...",
    "Motivational Interviewing": "Uses reflective listening to evoke behavior change...",
    # ... 50+ techniques
}
```

---

## Frontend Structure

### Directory Layout

```
frontend/
├── app/
│   ├── layout.tsx                   # Root layout with providers
│   ├── api/                         # API routes (server-side)
│   │   ├── upload/route.ts          # Audio upload to Supabase Storage
│   │   ├── process/route.ts         # Transcription + diarization
│   │   ├── status/[sessionId]/route.ts  # Processing status polling
│   │   └── chat/route.ts            # AI chat endpoint
│   ├── patient/
│   │   ├── layout.tsx               # Patient routes layout
│   │   ├── dashboard-v3/
│   │   │   ├── page.tsx             # Main dashboard (V3)
│   │   │   ├── components/
│   │   │   │   ├── SessionCardsGrid.tsx      # Session grid
│   │   │   │   ├── SessionCard.tsx           # Individual session card
│   │   │   │   ├── ProgressPatternsCard.tsx  # Mood/topic trends
│   │   │   │   ├── NotesGoalsCard.tsx        # Goals display
│   │   │   │   ├── ToDoCard.tsx              # Action items
│   │   │   │   ├── TimelineSidebar.tsx       # Session timeline
│   │   │   │   ├── MajorEventModal.tsx       # Major event details
│   │   │   │   └── ExportDropdown.tsx        # Export options
│   │   │   └── lib/
│   │   │       ├── types.ts                  # Type definitions
│   │   │       ├── usePatientSessions.ts     # Session data hook
│   │   │       ├── mockData.ts               # Mock sessions (12)
│   │   │       ├── utils.ts                  # UI utilities
│   │   │       └── timelineSearch.ts         # Search functionality
│   │   ├── upload/
│   │   │   ├── page.tsx             # Upload page
│   │   │   └── components/
│   │   │       ├── FileUploader.tsx           # File input
│   │   │       ├── UploadProgress.tsx         # Progress bar
│   │   │       └── ResultsView.tsx            # Results display
│   │   ├── hooks/
│   │   │   ├── useMoodAnalysis.ts            # Mood data hook
│   │   │   ├── useProgressMetrics.ts         # Progress metrics
│   │   │   └── useConsistencyData.ts         # Consistency metrics
│   │   └── contexts/
│   │       └── SessionDataContext.tsx        # Session state context
│   └── ask-ai/
│       └── page.tsx                 # Chat interface
├── lib/
│   ├── supabase.ts                  # Supabase client + types
│   ├── api-client.ts                # Authenticated API client
│   ├── api-types.ts                 # API type definitions
│   ├── token-storage.ts             # Token management
│   ├── demo-token-storage.ts        # Demo mode tokens
│   ├── env-validation.ts            # Environment validation
│   ├── dobby-system-prompt.ts       # AI chat system prompt
│   ├── speaker-role-detection.ts    # Speaker identification
│   ├── chat-context.ts              # AI context enrichment
│   └── types.ts                     # Global types
├── hooks/
│   ├── use-processing-status.ts     # Processing status polling
│   ├── use-conversation-messages.ts # Chat messages
│   └── [30+ other hooks]
├── components/
│   ├── NavigationBar.tsx            # Top navigation
│   ├── error-boundary.tsx           # Error handling
│   ├── MarkdownMessage.tsx          # Markdown rendering
│   └── [many UI components]
├── contexts/
│   ├── AuthContext.tsx              # Auth state
│   └── ProcessingContext.tsx        # Processing notifications
└── package.json
```

### Key Pages

#### 1. Patient Dashboard (dashboard-v3)
**File:** `app/patient/dashboard-v3/page.tsx`

**Components:**
- `SessionCardsGrid` - Displays 12 mock sessions in 4x3 grid
- `SessionCard` - Individual card with mood, topics, actions
- `TimelineSidebar` - Chronological view with search
- `ProgressPatternsCard` - Mood/topic trends visualization
- `NotesGoalsCard` - Treatment goals display
- `ToDoCard` - Actionable next steps

**Data Flow:**
1. `usePatientSessions()` hook loads mock data (or real API if enabled)
2. Sessions rendered in cards
3. Click session → opens expanded modal
4. Timeline sidebar for date navigation
5. Trend analysis shows improving/declining patterns

#### 2. Upload Page
**File:** `app/patient/upload/page.tsx`

**Flow:**
1. Drag-drop audio file
2. `FileUploader` validates file type
3. `POST /api/upload` → Supabase Storage
4. Session record created in DB
5. `POST /api/process` triggered
6. `UploadProgress` polls status every 2 seconds
7. When complete: dashboard refreshes automatically

#### 3. AI Chat (Dobby)
**File:** `app/ask-ai/page.tsx`

**Features:**
- Context-injected conversation
- Mood trends analysis
- Technique memory
- Goal progress indicators
- Crisis detection
- Session history integration

### Key Hooks

#### usePatientSessions
**File:** `app/patient/lib/usePatientSessions.ts`

```typescript
const {
  sessions,      // Session[]
  tasks,         // Task[]
  unifiedTimeline, // TimelineEvent[] (mixed sessions + events)
  majorEvents,   // MajorEventEntry[]
  isLoading,     // boolean
  refresh        // () => void
} = usePatientSessions();
```

**Features:**
- Toggle between mock data and real API
- Simulated network delay (300ms)
- Fallback to mock if API fails

#### useProcessingStatus
**File:** `hooks/use-processing-status.ts`

```typescript
const {
  status,           // 'pending' | 'processing' | 'completed' | 'failed'
  progress,         // 0-100
  estimatedTime,    // remaining seconds
  isComplete        // boolean
} = useProcessingStatus(sessionId);
```

**Features:**
- Polls `/api/status/{sessionId}` every 2 seconds
- Auto-stops when complete
- Exponential backoff on error

#### useMoodAnalysis
**File:** `app/patient/hooks/useMoodAnalysis.ts`

```typescript
const {
  moodHistory,      // Array of { date, score, trend }
  trend,            // 'improving' | 'stable' | 'declining'
  isLoading,        // boolean
} = useMoodAnalysis(patientId);
```

### Type Definitions

**Core Types:** `app/patient/lib/types.ts`

```typescript
interface Session {
  id: string;
  date: string;
  mood: MoodType;           // 'positive' | 'neutral' | 'low'
  topics: string[];         // AI-extracted topics
  strategy: string;         // Primary technique
  actions: string[];        // Action items
  summary?: string;         // AI summary (max 150 chars)
  deep_analysis?: DeepAnalysis;  // Wave 2 results
}

interface DeepAnalysis {
  progress_indicators: ProgressIndicator;
  therapeutic_insights: TherapeuticInsights;
  coping_skills: CopingSkills;
  therapeutic_relationship: TherapeuticRelationship;
  recommendations: Recommendations;
}
```

---

## Audio Pipeline

### Purpose
Convert raw audio files to transcribed, diarized, role-labeled segments.

### Flow

```
Audio File (MP3/WAV/M4A)
    ↓
┌─────────────────────────────┐
│ 1. Audio Preprocessing      │
│ - Load & validate           │
│ - Trim silence              │
│ - Normalize volume          │
│ - Convert to WAV (16kHz)    │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ 2. Transcription            │
│ - OpenAI Whisper API        │
│ - Or: faster-whisper (GPU)  │
│ - Output: timestamped text  │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ 3. Speaker Diarization      │
│ - pyannote.audio 3.1        │
│ - Identifies SPEAKER_00,    │
│   SPEAKER_01, etc.          │
└─────────────────────────────┘
    ↓
┌─────────────────────────────┐
│ 4. Speaker Role Detection   │
│ - First-speaker heuristic   │
│ - Speaking ratio heuristic  │
│ - Assigns Therapist/Client  │
└─────────────────────────────┘
    ↓
JSON Transcript
[
  {
    "speaker": "Therapist",
    "text": "How are you feeling today?",
    "start": 0.0,
    "end": 2.5
  },
  ...
]
```

### Two Implementations

#### CPU/API Version (Production)
**File:** `src/pipeline.py`

- Uses OpenAI Whisper API (requires internet + API key)
- Speed: 5-7 minutes for 23-minute session
- Cost: ~$0.02 per session
- Works anywhere, no GPU needed

#### GPU Version (Research)
**File:** `src/pipeline_gpu.py`

- Uses faster-whisper locally on GPU
- Speed: 1.5 minutes for 23-minute session (10-15x realtime)
- Cost: Only Vast.ai/cloud instance fees
- Requires 16+ GB VRAM, CUDA 12.1

### Key Classes

#### AudioPreprocessor
```python
processor = AudioPreprocessor()
audio = processor.load_audio("session.mp3")
audio = processor.trim_silence(audio)
audio = processor.normalize_volume(audio)
```

#### WhisperTranscriber
```python
transcriber = WhisperTranscriber(api_key)
transcript = transcriber.transcribe(audio)
# Returns: List[Dict] with text, start, end
```

#### SpeakerDiarizer
```python
diarizer = SpeakerDiarizer(hf_token)
diarization = diarizer.diarize(audio)
# Returns: Annotation with speaker labels
```

---

## Data Flow

### Complete Audio Upload → Display Pipeline

```
STEP 1: USER UPLOADS AUDIO
┌─────────────────────────────────────────┐
│ Frontend: app/patient/upload/page.tsx   │
│ - Drag-drop audio file                  │
│ - Select therapist from dropdown        │
│ - Click "Upload"                        │
└──────────────┬──────────────────────────┘
               │
               ▼
        POST /api/upload
        (FormData: file, patient_id, therapist_id)
               │
               ▼
┌─────────────────────────────────────────┐
│ Frontend: app/api/upload/route.ts       │
│ - Validate file type                    │
│ - Generate unique filename              │
│ - Upload to Supabase Storage            │
│ - Create therapy_sessions record (DB)   │
│ - Return: session_id, file_url          │
└──────────────┬──────────────────────────┘
               │
               ▼
STEP 2: PROCESS AUDIO
        Frontend: FileUploader.tsx
        - Show "Upload complete" message
        - Display processing status
        - Start polling /api/status/{session_id}

        POST /api/process
        (JSON: { session_id })
               │
               ▼
┌─────────────────────────────────────────┐
│ Frontend: app/api/process/route.ts      │
│ - Get session from DB                   │
│ - Download audio from Supabase Storage  │
│ - Call BACKEND at http://localhost:8000│
│   (for REAL pyannote diarization)       │
│                                          │
│ OR: Use mock diarization (if backend    │
│     not running)                        │
└──────────────┬──────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│ BACKEND: app/api/transcribe (FastAPI)   │
│ - Receive audio file                     │
│ - Run Whisper transcription              │
│ - Run pyannote diarization               │
│ - Detect speaker roles (Therapist/Client)
│ - Return diarized + role-labeled trans.  │
└──────────────┬───────────────────────────┘
               │
               ▼
STEP 3: STORE TRANSCRIPT
        Frontend: app/api/process/route.ts
        - Receive labeled transcript
        - Update therapy_sessions.transcript
        - Set processing_status = "completed"
        - Return session data to client
               │
               ▼
STEP 4: TRIGGER ANALYSIS
        Backend: analyze_session_full_pipeline()
        
        WAVE 1 (Immediate):
        ├─ Topic Extractor: topics, action_items, technique, summary
        ├─ Mood Analyzer: mood_score, confidence, indicators
        └─ Update DB: wave1_analyzed_at, analysis data
        
        WAVE 2 (Async background task):
        ├─ Deep Analyzer: progress, insights, skills, relationship
        ├─ Prose Generator: narrative prose
        ├─ Breakthrough Detector: breakthrough moments
        └─ Update DB: wave2_analyzed_at, deep_analysis data
               │
               ▼
STEP 5: DISPLAY ON DASHBOARD
        Frontend: dashboard-v3/page.tsx
        - Load sessions via usePatientSessions()
        - Display SessionCards with:
          ├─ Mood indicator (green/blue/rose)
          ├─ Topics (from Wave 1)
          ├─ Strategy (technique)
          ├─ Action items
          └─ Deep analysis (Wave 2)
        - Display ProgressPatternsCard with:
          ├─ Mood trend (improving/stable/declining)
          ├─ Topic frequency chart
          └─ Technique usage history
```

### Database Schema (Key Tables)

```sql
-- Users & Patients
users:
  id UUID (PK)
  email VARCHAR
  first_name VARCHAR
  last_name VARCHAR
  role ('therapist' | 'patient')
  created_at TIMESTAMP

-- Therapy Sessions
therapy_sessions:
  id UUID (PK)
  patient_id UUID (FK users.id)
  therapist_id UUID (FK users.id)
  session_date TIMESTAMP
  duration_minutes INT
  
  -- Audio Processing
  audio_file_url VARCHAR
  processing_status VARCHAR ('pending' | 'processing' | 'completed' | 'failed')
  processing_progress INT (0-100)
  
  -- Transcription Results
  transcript JSONB  -- [{speaker, text, start, end}]
  
  -- Wave 1 Analysis (Immediate)
  topics TEXT[]  -- AI-extracted topics
  action_items TEXT[]  -- AI-extracted action items
  technique VARCHAR  -- Primary therapeutic technique
  summary TEXT  -- Ultra-brief summary (max 150 chars)
  mood_score FLOAT (0.0-10.0)
  mood_confidence FLOAT (0.0-1.0)
  mood_indicators TEXT[]
  emotional_tone VARCHAR
  wave1_analyzed_at TIMESTAMP
  
  -- Wave 2 Analysis (Async)
  deep_analysis JSONB  -- {progress_indicators, insights, coping_skills, ...}
  wave2_analyzed_at TIMESTAMP
  
  -- Breakthrough Detection
  has_breakthrough BOOLEAN
  breakthrough_data JSONB
  breakthrough_analyzed_at TIMESTAMP
  
  created_at TIMESTAMP
  updated_at TIMESTAMP

-- Session Transcripts (detailed)
session_transcripts:
  id UUID (PK)
  session_id UUID (FK therapy_sessions.id)
  speaker VARCHAR ('Therapist' | 'Client')
  text TEXT
  start_time FLOAT
  end_time FLOAT
  created_at TIMESTAMP

-- Session Notes (clinical)
session_notes:
  id UUID (PK)
  session_id UUID (FK therapy_sessions.id)
  therapist_id UUID (FK users.id)
  subjective TEXT
  objective TEXT
  assessment TEXT
  plan TEXT
  created_by VARCHAR ('ai' | 'therapist')
  created_at TIMESTAMP
  updated_at TIMESTAMP

-- Treatment Goals
treatment_goals:
  id UUID (PK)
  patient_id UUID (FK users.id)
  title VARCHAR
  description TEXT
  target_date DATE
  status VARCHAR ('active' | 'completed' | 'paused')
  progress INT (0-100)
  created_at TIMESTAMP
  updated_at TIMESTAMP

-- Breakthrough History
breakthrough_history:
  id UUID (PK)
  session_id UUID (FK therapy_sessions.id)
  breakthrough_type VARCHAR
  description TEXT
  evidence TEXT
  confidence_score FLOAT
  timestamp_start FLOAT
  timestamp_end FLOAT
  dialogue_excerpt JSONB
  is_primary BOOLEAN
  created_at TIMESTAMP

-- Mood Trends (for visualization)
patient_mood_trends:
  -- View: Rolling 7-day, 30-day, 90-day mood averages
  patient_id UUID
  period VARCHAR ('7_day' | '30_day' | '90_day')
  avg_mood FLOAT
  trend VARCHAR ('improving' | 'stable' | 'declining')
```

---

## Key Integration Points

### 1. Audio Upload → Processing

**Frontend:**
```typescript
// app/patient/upload/page.tsx
const handleUpload = async (file: File) => {
  // 1. Upload file to Supabase Storage
  const uploadResponse = await fetch('/api/upload', {
    method: 'POST',
    body: formData,  // includes file, patient_id, therapist_id
  });
  
  const { session_id } = await uploadResponse.json();
  
  // 2. Trigger processing
  const processResponse = await fetch('/api/process', {
    method: 'POST',
    body: JSON.stringify({ session_id }),
  });
  
  // 3. Poll status
  useProcessingStatus(session_id);  // Polls every 2 seconds
};
```

**Backend:**
```python
# app/routers/sessions.py
@router.post("/upload-transcript")
async def upload_transcript(session_id, data, background_tasks):
    # 1. Store transcript
    db.table("therapy_sessions").update({
        "transcript": data.transcript,
        "processing_status": "completed"
    }).eq("id", session_id).execute()
    
    # 2. Trigger Wave 1 analysis immediately
    # 3. Queue Wave 2 for background processing
    background_tasks.add_task(
        analyze_session_full_pipeline,
        session_id,
        data.transcript
    )
```

### 2. Analysis Results → Database

**Backend Service:**
```python
# app/services/mood_analyzer.py
class MoodAnalyzer:
    def analyze_session(self, transcript):
        # Call GPT-4o-mini
        response = openai.ChatCompletion.create(...)
        
        return MoodAnalysis(
            mood_score=extracted_score,  # 0.0-10.0
            confidence=confidence,
            rationale=rationale,
            key_indicators=indicators
        )
```

**Router Integration:**
```python
# app/routers/sessions.py
@router.post("/{session_id}/analyze-mood")
async def analyze_mood_endpoint(session_id):
    # 1. Get transcript
    session = db.table("therapy_sessions").select("transcript").eq("id", session_id).single().execute()
    
    # 2. Run mood analysis
    analyzer = MoodAnalyzer(api_key)
    mood = analyzer.analyze_session(session["transcript"])
    
    # 3. Store in database
    db.table("therapy_sessions").update({
        "mood_score": mood.mood_score,
        "mood_confidence": mood.confidence,
        "mood_indicators": mood.key_indicators,
        "emotional_tone": mood.emotional_tone,
        "wave1_analyzed_at": datetime.now()
    }).eq("id", session_id).execute()
    
    return mood
```

### 3. Mock Data → Real Data Toggle

**Frontend Hook:**
```typescript
// app/patient/lib/usePatientSessions.ts
const USE_MOCK_DATA = true;  // Set to false for real API

export function usePatientSessions() {
  useEffect(() => {
    if (USE_MOCK_DATA) {
      // Use mock sessions (12 predefined)
      setSessions(mockSessions);
    } else {
      // Call real API
      const result = await apiClient.get(
        `/api/sessions/patient/${patientId}`
      );
      setSessions(result.data.sessions);
    }
  }, []);
}
```

### 4. Demo Mode Flow

**Step 1: Initialize**
```typescript
// Frontend
const demoResponse = await fetch('/api/demo/init', {
  method: 'POST'
});

const { demo_token, patient_id, session_ids } = await demoResponse.json();
demoTokenStorage.save(demo_token, patient_id);
```

**Step 2: Backend Creates Sessions**
```python
# app/routers/demo.py
@router.post("/init")
async def init_demo(db: Client = Depends(get_db)):
    # 1. Create demo patient
    patient = db.table("users").insert({
        "email": "demo@example.com",
        "role": "patient"
    }).execute()
    
    # 2. Create 12 mock sessions
    sessions = []
    for i in range(12):
        session = db.table("therapy_sessions").insert({
            "patient_id": patient["id"],
            "session_date": generate_date(i),
            "transcript": MOCK_TRANSCRIPTS[i],
            "processing_status": "completed"
        }).execute()
        sessions.append(session)
    
    # 3. Trigger Wave 1 analysis for all
    background_tasks.add_task(
        run_wave1_analysis_background,
        patient["id"]
    )
    
    # 4. Queue Wave 2 analysis
    background_tasks.add_task(
        run_wave2_analysis_background,
        patient["id"]
    )
```

### 5. AI Chat Context Injection

**System Prompt Injection:**
```typescript
// lib/chat-context.ts
const enrichContext = async (patientId: string) => {
  // Fetch mood trends
  const moodHistory = await fetch(`/api/sessions/patient/${patientId}/mood-history`);
  
  // Fetch recent breakthroughs
  const breakthroughs = await fetch(`/api/sessions/patient/${patientId}/breakthroughs`);
  
  // Fetch goal progress
  const goals = await fetch(`/api/patient/${patientId}/goals`);
  
  // Build context string
  const context = `
    Recent mood trend: ${calculateTrend(moodHistory)}
    Recent techniques: ${extractTechniques(breakthroughs)}
    Goal progress: ${formatGoals(goals)}
  `;
  
  return context;
};

// Inject into system prompt
const systemPrompt = `${DOBBY_BASE_PROMPT}\n\nContext:\n${context}`;
```

---

## Current Implementation Status

### COMPLETE ✅

**Backend:**
- [x] FastAPI application structure
- [x] Supabase integration
- [x] Session CRUD endpoints
- [x] Mood analyzer service (GPT-4o-mini)
- [x] Topic extractor service (GPT-4o-mini)
- [x] Breakthrough detector service (GPT-4o-mini)
- [x] Deep analyzer service (Wave 2)
- [x] Speaker labeler service
- [x] Analysis orchestrator
- [x] Progress metrics extraction
- [x] Demo mode endpoints
- [x] Authenticated API client (frontend)

**Frontend:**
- [x] Next.js 16 + React 19 setup
- [x] Dashboard V3 with session cards
- [x] Session card components
- [x] Upload page
- [x] Processing status polling
- [x] Timeline visualization
- [x] Major event modal
- [x] Mood trend visualization
- [x] Export functionality (PDF)
- [x] Mock data system (12 sessions)

**Audio Pipeline:**
- [x] Audio preprocessing (trim silence, normalize)
- [x] Whisper transcription (API)
- [x] pyannote diarization (3.1)
- [x] Speaker role detection

### PARTIAL / IN PROGRESS 🔄

**Backend:**
- [ ] Full authentication system (using demo mode)
- [ ] Email notifications
- [ ] Session search/filtering

**Frontend:**
- [ ] Real API integration (toggle available, not fully tested)
- [ ] Therapist dashboard (patient view exists)
- [ ] Session editing/deletion
- [ ] Note taking interface

**Audio Pipeline:**
- [ ] GPU version (Vast.ai) - documented but not tested
- [ ] Background job processing (manual triggering works)

### NOT STARTED ⏳

**Backend:**
- [ ] Session deletion cascade
- [ ] Semantic search (pgvector)
- [ ] Real-time WebSocket updates
- [ ] File upload to S3

**Frontend:**
- [ ] Therapist note-taking
- [ ] Patient goal management
- [ ] Subscription/billing
- [ ] Mobile responsive design

---

## Critical Files Reference

### Must-Know Backend Files

| File | Purpose | Lines | Status |
|------|---------|-------|--------|
| `app/main.py` | FastAPI app entry point | 89 | ✅ Complete |
| `app/config.py` | Environment configuration | 84 | ✅ Complete |
| `app/database.py` | Supabase client + helpers | 201 | ✅ Complete |
| `app/routers/sessions.py` | Session endpoints | 700+ | ✅ Complete |
| `app/routers/demo.py` | Demo mode endpoints | 300+ | ✅ Complete |
| `app/services/breakthrough_detector.py` | AI breakthrough detection | 300+ | ✅ Complete |
| `app/services/mood_analyzer.py` | AI mood analysis | 200+ | ✅ Complete |
| `app/services/topic_extractor.py` | AI topic extraction | 250+ | ✅ Complete |
| `app/services/deep_analyzer.py` | Wave 2 clinical analysis | 500+ | ✅ Complete |
| `app/services/speaker_labeler.py` | Therapist/Client detection | 250+ | ✅ Complete |
| `app/services/analysis_orchestrator.py` | Analysis coordination | 400+ | ✅ Complete |

### Must-Know Frontend Files

| File | Purpose | Status |
|------|---------|--------|
| `app/patient/dashboard-v3/page.tsx` | Main dashboard | ✅ Complete |
| `app/patient/dashboard-v3/components/SessionCardsGrid.tsx` | Session grid | ✅ Complete |
| `app/patient/dashboard-v3/components/SessionCard.tsx` | Individual card | ✅ Complete |
| `app/patient/lib/usePatientSessions.ts` | Session data hook | ✅ Complete |
| `app/patient/lib/mockData.ts` | 12 mock sessions | ✅ Complete |
| `app/api/upload/route.ts` | File upload endpoint | ✅ Complete |
| `app/api/process/route.ts` | Audio processing | ✅ Complete |
| `app/api/status/[sessionId]/route.ts` | Status polling | ✅ Complete |
| `lib/api-client.ts` | Authenticated API client | ✅ Complete |
| `lib/supabase.ts` | Supabase client + types | ✅ Complete |
| `lib/dobby-system-prompt.ts` | AI chat system prompt | ✅ Complete |
| `lib/speaker-role-detection.ts` | Speaker identification | ✅ Complete |

### Must-Know Configuration Files

| File | Purpose | Status |
|------|---------|--------|
| `backend/.env` | Backend secrets (complete) | ✅ Configured |
| `frontend/.env.local` | Frontend config | ✅ Configured |
| `audio-transcription-pipeline/.env` | Pipeline config | ✅ Configured |
| `.python-version` | Python version (root, backend) | ✅ 3.13.9 |
| `backend/requirements.txt` | Python dependencies | ✅ Complete |
| `frontend/package.json` | Node dependencies | ✅ Complete |

---

## Development Workflow

### To Add a New Backend Service

1. Create file: `app/services/my_service.py`
2. Implement service class with `__init__` and analysis method
3. Add response model to `app/routers/sessions.py`
4. Add endpoint to sessions router
5. Test with `pytest` or manual `curl` request
6. Document in this file

### To Add a New Frontend Component

1. Create component in appropriate folder
2. Import types from `app/patient/lib/types.ts`
3. Use `usePatientSessions()` or other hooks for data
4. Add to appropriate page or card
5. Test with mock data first
6. Enable real API when ready

### To Deploy

**Backend (FastAPI):**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend (Next.js):**
```bash
cd frontend
npm install
npm run dev
```

**Audio Pipeline:**
```bash
cd audio-transcription-pipeline
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python tests/test_full_pipeline.py
```

---

## Troubleshooting

### Backend not responding
- Check if FastAPI is running: `ps aux | grep uvicorn`
- Verify Supabase URL and keys in `.env`
- Check CORS settings in `app/main.py`

### Audio processing fails
- Verify OpenAI API key is set
- Check audio file format (MP3, WAV, M4A supported)
- Ensure pyannote models are cached (~1GB)

### Frontend shows "Connection refused"
- Start backend first (`uvicorn app.main:app --reload`)
- Check `API_BASE_URL` in `lib/api-client.ts` (default: localhost:8000)
- Verify CORS allows frontend origin

### Wave 2 analysis slow
- Deep analysis can take 1-2 minutes
- Check backend logs for API rate limits
- Wave 2 runs asynchronously after Wave 1

---

## Next Steps

1. **Real API Integration Test**
   - Set `USE_MOCK_DATA = false` in `usePatientSessions.ts`
   - Verify all sessions load from backend
   - Test with real session data

2. **End-to-End Testing**
   - Upload real audio file
   - Verify transcription works
   - Confirm all analysis waves complete
   - Check results display on dashboard

3. **Performance Optimization**
   - Implement session pagination
   - Add caching for frequently-accessed data
   - Optimize database queries with proper indexes

4. **Feature Completion**
   - Implement therapist dashboard
   - Add session note-taking
   - Build goal management interface
   - Add semantic search

---

## Document History

- **2025-12-27**: Initial comprehensive architecture map created
- **Status**: Current to git commit `227586b`
- **Coverage**: All 3 systems (backend, frontend, audio pipeline)

