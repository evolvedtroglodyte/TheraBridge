# TherapyBridge Architecture - Quick Reference

**Status:** Comprehensive architecture map created - see ARCHITECTURE.md for full details

---

## System Layers

```
┌─────────────────────────────────────────────┐
│ FRONTEND (Next.js 16 + React 19 + Tailwind) │
│ app/patient/dashboard-v3/page.tsx           │
└────────────────────┬────────────────────────┘
                     │ HTTP REST APIs
┌────────────────────▼────────────────────────┐
│ BACKEND (FastAPI + Python 3.13.9)           │
│ app/routers/sessions.py                     │
│ app/services/*.py (Mood, Topics, etc.)      │
└────────────────────┬────────────────────────┘
                     │ Webhook/Events
┌────────────────────▼────────────────────────┐
│ AUDIO PIPELINE (CPU/GPU Transcription)      │
│ Whisper API + pyannote 3.1 diarization      │
└─────────────────────────────────────────────┘
```

---

## Data Flow (Audio Upload → Display)

```
User uploads MP3
    ↓
POST /api/upload
    ├─ Store in Supabase Storage
    ├─ Create therapy_sessions record
    └─ Return session_id
    ↓
POST /api/process
    ├─ Download audio from storage
    ├─ Call backend: Whisper + pyannote
    ├─ Get diarized transcript
    ├─ Detect speaker roles
    └─ Store transcript in DB
    ↓
WAVE 1 Analysis (Async)
    ├─ Topic extraction (GPT-4o-mini)
    ├─ Mood analysis (GPT-4o-mini)
    └─ Update DB immediately
    ↓
WAVE 2 Analysis (Background)
    ├─ Deep clinical analysis
    ├─ Breakthrough detection
    └─ Prose generation
    ↓
Frontend usePatientSessions() hook
    ├─ Fetches sessions from API (or uses mock)
    └─ Displays in SessionCardsGrid
```

---

## Backend API Endpoints

### Sessions Router (`/api/sessions`)

**Session CRUD:**
- `POST /` - Create session
- `GET /` - List all
- `GET /{id}` - Get single
- `GET /patient/{id}` - Get patient's sessions

**Analysis:**
- `POST /{id}/analyze-mood` - Mood analysis
- `POST /{id}/extract-topics` - Topic extraction
- `POST /{id}/detect-breakthrough` - Breakthrough detection
- `POST /{id}/analyze-deep` - Wave 2 analysis

**Processing:**
- `POST /{id}/upload-transcript` - Store transcript
- `GET /{id}/analysis-status` - Check status (Wave 1 & 2)

---

## Frontend Components

### Dashboard V3 (`app/patient/dashboard-v3/`)

```
Dashboard
├── SessionCardsGrid
│   └── SessionCard (x12)
│       ├── Mood indicator
│       ├── Topics
│       ├── Strategy
│       └── Actions
├── TimelineSidebar
│   └── Session chronology with search
├── ProgressPatternsCard
│   └── Mood/topic trends
├── NotesGoalsCard
│   └── Treatment goals
└── ToDoCard
    └── Action items
```

---

## Key Services

| Service | File | Input | Output | Cost |
|---------|------|-------|--------|------|
| Mood Analyzer | `mood_analyzer.py` | Transcript | Score, indicators | $0.01/session |
| Topic Extractor | `topic_extractor.py` | Transcript | Topics, actions, summary | $0.01/session |
| Breakthrough Detector | `breakthrough_detector.py` | Transcript | Breakthroughs, confidence | $0.01/session |
| Deep Analyzer | `deep_analyzer.py` | Transcript | Progress, insights, skills | $0.02/session |
| Speaker Labeler | `speaker_labeler.py` | Diarized segments | Therapist/Client labels | Free |

---

## Database Key Tables

```
users                          therapy_sessions
├─ id (UUID)                  ├─ id (UUID)
├─ email                       ├─ patient_id (FK)
├─ first_name                  ├─ therapist_id (FK)
├─ last_name                   ├─ session_date
├─ role (therapist|patient)    ├─ transcript (JSONB)
└─ created_at                  ├─ topics (TEXT[])
                               ├─ mood_score (0.0-10.0)
                               ├─ summary (max 150 chars)
                               ├─ deep_analysis (JSONB)
                               ├─ wave1_analyzed_at
                               ├─ wave2_analyzed_at
                               └─ processing_status
```

---

## Critical Files Map

### Must-Know Backend
- **Entry:** `backend/app/main.py` (FastAPI setup)
- **Config:** `backend/app/config.py` (env vars)
- **Database:** `backend/app/database.py` (Supabase client)
- **Routes:** `backend/app/routers/sessions.py` (700+ lines, all endpoints)
- **Services:** `backend/app/services/*.py` (AI extraction)

### Must-Know Frontend
- **Dashboard:** `frontend/app/patient/dashboard-v3/page.tsx`
- **Components:** `frontend/app/patient/dashboard-v3/components/*.tsx`
- **Data Hook:** `frontend/app/patient/lib/usePatientSessions.ts`
- **Mock Data:** `frontend/app/patient/lib/mockData.ts` (12 sessions)
- **Types:** `frontend/app/patient/lib/types.ts`
- **API Client:** `frontend/lib/api-client.ts`
- **Upload:** `frontend/app/api/upload/route.ts`
- **Process:** `frontend/app/api/process/route.ts`

---

## Development Commands

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev

# Audio Pipeline
cd audio-transcription-pipeline
source venv/bin/activate
python tests/test_full_pipeline.py audio.mp3
```

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | ✅ Complete | All endpoints working |
| Frontend Dashboard | ✅ Complete | V3 with all cards |
| Mood Analysis | ✅ Complete | Wave 1 immediate |
| Topic Extraction | ✅ Complete | Wave 1 immediate |
| Breakthrough Detection | ✅ Complete | Wave 2 async |
| Deep Analysis | ✅ Complete | Wave 2 async |
| Audio Processing | ✅ Complete | Whisper + pyannote |
| Speaker Role Detection | ✅ Complete | Heuristic-based |
| Demo Mode | ✅ Complete | 12 mock sessions |
| Real API Integration | 🔄 Partial | Toggle available, not fully tested |
| Therapist Dashboard | ⏳ Pending | Patient view complete |
| Authentication | 🔄 Partial | Demo mode only |

---

## Key Facts

- **Three independent systems** that communicate via HTTP REST APIs
- **12 mock therapy sessions** built into frontend for development
- **Two-wave analysis pipeline:** Wave 1 (immediate), Wave 2 (async background)
- **No hardcoded output** - all AI responses from GPT-4o-mini
- **Speaker role detection** uses heuristics (not AI)
- **Cost:** ~$0.04 per session (all AI services)
- **Processing time:** 10-30 seconds for Wave 1, 2-5 minutes for Wave 2

---

## Common Tasks

### To enable real API data (instead of mock)
```typescript
// app/patient/lib/usePatientSessions.ts
const USE_MOCK_DATA = false;  // Change this
```

### To add a new analysis service
1. Create `backend/app/services/my_service.py`
2. Add response model to `backend/app/routers/sessions.py`
3. Add endpoint: `@router.post("/{session_id}/my-endpoint")`
4. Return response and store in DB

### To modify dashboard layout
1. Edit `frontend/app/patient/dashboard-v3/page.tsx`
2. Adjust component order/grid layout
3. Update component props in `components/` files

### To add a therapist dashboard
1. Create `frontend/app/therapist/dashboard/page.tsx`
2. Use `SessionCardsGrid` with therapist view filters
3. Add therapist-specific routes in navigation

---

## Contact Points Between Systems

| Frontend Action | Backend Endpoint | Data Returned |
|---|---|---|
| Load dashboard | `GET /api/sessions/patient/{id}` | Array of sessions |
| Upload audio | `POST /api/upload` | `{ session_id, file_url }` |
| Process audio | `POST /api/process` | `{ transcript, status }` |
| Check status | `GET /api/status/{id}` | `{ progress, status, analysis }` |
| Get mood history | `GET /api/sessions/patient/{id}/mood-history` | `[{ date, score }]` |

---

For complete details, see: **ARCHITECTURE.md**
