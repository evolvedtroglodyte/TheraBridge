# TherapyBridge - Project Documentation

**Repository Rules:** See `.claude/CLAUDE.md` for organization standards.

---

## Current State

**Status:** ✅ Audio transcription pipeline complete. ✅ Backend FastAPI with AI extraction fully implemented and tested. Frontend dashboard pending.

**Latest:** Day 3 complete - AI note extraction with GPT-4o working. Server running on port 8000.

**Next:** Build frontend dashboard (Day 4)

---

## MVP Tech Stack

| Layer | Technology | Cost | Status |
|-------|------------|------|--------|
| Frontend | Next.js 14 + Tailwind + shadcn/ui | Free | Pending |
| Hosting (Frontend) | Vercel | Free | Pending |
| Backend | Python FastAPI | Free | ✅ Complete with AI extraction |
| Hosting (Backend) | AWS Lambda | ~$1-5/mo | Pending |
| Database | Neon PostgreSQL + pgvector | Free tier | ✅ Deployed and working |
| Auth | Auth.js (NextAuth v5) | Free | Pending |
| LLM | GPT-4o (OpenAI) | ~$0.02/session | ✅ Working |
| Transcription | OpenAI Whisper API | Usage-based | ✅ Working |
| Diarization | pyannote-audio 3.1 | Free (local) | ✅ Working |
| Storage | AWS S3 | ~$1-2/mo | Pending |

**Estimated Monthly Cost:** $5-20/month

### MVP Features

- [x] Audio upload (MP3, WAV, M4A)
- [x] Transcription with Whisper API
- [x] Speaker diarization (pyannote)
- [x] AI note extraction (GPT-4o) - ✅ **Day 3 Complete**
- [x] Backend API with all endpoints
- [x] Database schema with sessions, notes, patients
- [ ] Therapist/Patient dashboards
- [ ] Semantic search

### Deferred to Post-MVP

- Auto speaker diarization improvements
- Background job processing (sync for MVP)
- Real-time transcription
- Advanced cross-session insights
- Crisis detection system
- Mobile app

---

## Audio Transcription Pipeline

**Location:** `audio-transcription-pipeline/`
**Full docs:** See `audio-transcription-pipeline/README.md`

### Quick Reference

**Two implementations available:**

1. **CPU/API** - Production-ready, uses OpenAI Whisper API (~5-7 min for 23 min audio)
2. **GPU/Vast.ai** - Research, uses faster-whisper locally on GPU (~1.5 min for 23 min audio)

**Pipeline stages:**
- Audio preprocessing (silence trim, normalize, format conversion) ✅
- Whisper transcription (API or local GPU) ✅
- Speaker diarization (pyannote 3.1, 2-speaker detection) ✅
- Therapist/Client role labeling ✅

**Output:** JSON with timestamped, speaker-labeled segments

**Quick start:**
```bash
cd audio-transcription-pipeline
source venv/bin/activate
python tests/test_full_pipeline.py
```

### GPU Pipeline (Vast.ai)

**Provider:** Vast.ai (NOT Google Colab)
**Instance Type:** GPU with CUDA 12.1 support
**Cost:** Billed per second (must destroy instance to stop charges)

**Files:**
- `pipeline_gpu.py` - GPU-optimized pipeline
- `gpu_audio_ops.py` - GPU audio operations
- `requirements.txt` - Includes GPU dependencies

**Key Constraints (2025-12):**
- `ctranslate2==4.4.0` required (>= 4.5.0 needs cuDNN 9.x, unavailable on most cloud GPUs)
- Google Colab L4 has compatibility issues with pyannote.audio >= 3.3.x (torchaudio.AudioMetaData error)
- Vast.ai recommended for production GPU workloads

**Performance:** 10-15x realtime for 52-min audio files

---

## Environment Setup

### Required API Keys (.env)

```bash
OPENAI_API_KEY=sk-xxx           # Whisper transcription
HF_TOKEN=hf_xxx                 # HuggingFace (pyannote models)
```

### HuggingFace Model Access

Must accept terms for both:
1. https://huggingface.co/pyannote/speaker-diarization-3.1
2. https://huggingface.co/pyannote/speaker-diarization-community-1

### Local Development (Future)

```yaml
# docker-compose.yml structure
services:
  frontend:   # Next.js on port 3000
  backend:    # FastAPI on port 8000
```

---

## Key Technical Decisions

### Why 64kbps MP3?

- Speech doesn't need high bitrate
- Reduces 1-hour file from ~120MB to ~27MB
- Whisper's sweet spot for quality vs. size

### Why pyannote over alternatives?

- Best open-source diarization accuracy
- Runs locally (no API costs)
- Active development, good community

### Pyannote 4.0 Breaking Changes (Critical)

```python
# API parameter changed
Pipeline.from_pretrained(..., token=hf_token)  # NOT use_auth_token

# Output access changed
annotation = diarization.speaker_diarization  # NOT diarization directly
for turn, _, speaker in annotation.itertracks(yield_label=True):
    ...

# TorchCodec workaround - pre-load audio as tensor
import torchaudio
waveform, sample_rate = torchaudio.load(audio_file_path)
audio_dict = {"waveform": waveform, "sample_rate": sample_rate}
diarization = pipeline(audio_dict)  # NOT pipeline(file_path)
```

### File Size Handling

| Duration | MP3 @ 64kbps | Whisper Chunks |
|----------|--------------|----------------|
| 23 min   | ~11 MB       | 1 (no split)   |
| 45 min   | ~22 MB       | 1 (no split)   |
| 60 min   | ~29 MB       | 3 chunks       |
| 90 min   | ~43 MB       | 5 chunks       |

---

## Cost Breakdown (Estimated)

| Service | Free Tier | Overage Cost |
|---------|-----------|--------------|
| Vercel | 100GB bandwidth | $20/100GB |
| Neon | 0.5GB storage | $0.25/GB |
| Claude Haiku | N/A | $0.25/1M input, $1.25/1M output |
| OpenAI Whisper | N/A | $0.006/min |
| AWS S3 | 5GB (12mo) | $0.023/GB |

**Realistic MVP usage (10 sessions/week):** ~$5-10/month

---

## Backend API (Day 3 - Complete)

**Location:** `backend/`
**Server:** http://localhost:8000
**Docs:** http://localhost:8000/docs

### Quick Start

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### API Endpoints

**Sessions:**
- `POST /api/sessions/upload` - Upload audio, creates session (returns immediately, processes in background)
- `GET /api/sessions/{id}` - Get session details with extracted notes
- `GET /api/sessions/{id}/notes` - Get extracted notes only
- `GET /api/sessions/` - List all sessions (filterable by patient, status)
- `POST /api/sessions/{id}/extract-notes` - Manually re-extract notes

**Patients:**
- `POST /api/patients/` - Create patient
- `GET /api/patients/{id}` - Get patient details
- `GET /api/patients/` - List all patients

**Health:**
- `GET /` - Simple status
- `GET /health` - Detailed health check

### AI Extraction

Powered by OpenAI GPT-4o. Extracts from transcripts:
- Key topics (3-7 items)
- Topic summary (2-3 sentences)
- Strategies (breathing, cognitive, behavioral, etc.)
- Emotional themes
- Triggers (with severity)
- Action items (homework/tasks)
- Significant quotes from patient
- Session mood (very_low → very_positive)
- Mood trajectory (improving, declining, stable, fluctuating)
- Follow-up topics
- Unresolved concerns
- Risk flags (self-harm, suicidal ideation, crisis)
- **Therapist summary** - 150-200 words, clinical
- **Patient summary** - 100-150 words, warm/supportive

**Extraction time:** ~20 seconds per session
**Cost:** ~$0.02-0.03 per session

### Database Tables

1. **users** - Therapists and patients (with roles)
2. **patients** - Patient records linked to therapists
3. **sessions** - Full session pipeline (audio → transcript → notes)
4. **action_items** - Homework/tasks assigned to patients
5. **patient_strategies** - Longitudinal tracking of coping strategies
6. **patient_triggers** - Longitudinal tracking of triggers

### Processing Pipeline

Upload → Transcribing → Transcribed → Extracting Notes → Processed

Background processing with status updates. Client can poll GET `/api/sessions/{id}` to check progress.

### Testing

```bash
# Test AI extraction
pytest tests/test_extraction_service.py -v

# Test server
curl http://localhost:8000/health

# Upload session
curl -X POST "http://localhost:8000/api/sessions/upload?patient_id=UUID" \
  -F "file=@audio.mp3"
```

See `backend/README.md` and `backend/QUICKSTART.md` for full details.

---

## Session Log

### 2025-12-17 - Authentication Integration via 15-Instance Parallel Workflow

**Summary:** Successfully implemented comprehensive authentication system using 15 parallel Claude Code instances executing 63 ultra-fine-grained tasks across 7 phases.

**Key Changes:**
- **Database Migration:** Alembic-based schema migration adding authentication columns to `users` table and creating `auth_sessions` table
- **Authentication Endpoints:** Complete JWT-based auth system with signup, login, refresh (with token rotation), logout, and /me endpoints
- **Security Features:** Bcrypt password hashing (12 rounds), refresh token rotation, rate limiting (5/min on login), SQL injection protection
- **Middleware:** Rate limiting middleware using slowapi (100 req/min default, 5 req/min on login)
- **Test Infrastructure:** Pytest fixtures for auth testing with in-memory SQLite database
- **Documentation:** Comprehensive auth documentation in backend README with curl examples

**Files Created:**
- `backend/app/auth/` - Complete auth module (7 files)
  - `router.py` - Auth endpoints (signup, login, refresh, logout, /me)
  - `models.py` - User and AuthSession SQLAlchemy models
  - `schemas.py` - Pydantic validation schemas
  - `utils.py` - Password hashing and JWT token utilities
  - `config.py` - Auth configuration (token expiration, secret key)
  - `dependencies.py` - Auth dependency injection (get_current_user)
  - `__init__.py` - Module initialization
- `backend/app/middleware/` - Middleware module
  - `rate_limit.py` - Rate limiting configuration using slowapi
  - `__init__.py` - Module initialization
- `backend/alembic/` - Database migration infrastructure
  - `alembic.ini` - Alembic configuration
  - `alembic/versions/7cce0565853d_create_auth_tables.py` - Initial auth migration
  - `alembic/versions/808b6192c57c_add_authentication_schema_and_missing_.py` - Complete schema migration
  - `alembic/env.py` - Migration environment
- `backend/scripts/` - Database management scripts
  - `backup_database.py` - Pre-migration backup script
  - `restore_database.py` - Emergency restore script
  - `export_users_schema.py` - Schema export utilities
  - `check_auth_sessions.py` - Session validation script
- `backend/migrations/` - Migration analysis and backups
  - `ROLLBACK_GUIDE.md` - Emergency rollback procedures
  - `backups/` - JSON database backups
  - `analysis/` - Schema comparison reports
- `backend/tests/conftest.py` - Pytest fixtures for auth testing (therapist_user, patient_user, admin_user, auth tokens)

**Technical Details:**
- **Password Requirements:** Minimum 8 characters, validated via Pydantic
- **Token Expiration:** Access tokens 30 minutes, refresh tokens 7 days
- **Token Rotation:** Old refresh token revoked when new token issued (security best practice)
- **Rate Limits:** Login endpoint 5 req/min, general endpoints 100 req/min
- **Database:** PostgreSQL with Alembic migrations, SQLAlchemy ORM
- **Testing:** In-memory SQLite for tests, pytest fixtures for all user roles

**Test Results:**
- Manual testing of all endpoints completed successfully
- Security validation passed (password hashing, JWT verification, SQL injection protection, rate limiting)
- Database migration executed successfully with pre-migration backups
- All auth endpoints functional with proper error handling

**Execution Stats:**
- **Method:** 15 parallel Claude Code instances (Wave-based coordination)
- **Estimated Time:** ~90 minutes (parallel execution with checkpoint synchronization)
- **Phases:** 7 waves (Pre-flight → Discovery → Infrastructure → Backend Dev → Testing → Migration → Validation)
- **Task Granularity:** 63 ultra-fine-grained prompts (3-5 minutes each)
- **Speedup:** 5x faster than sequential approach (~450 minutes)

**Next Steps:**
- Add frontend authentication integration (login/signup forms)
- Implement password reset flow (forgot password email)
- Add session management UI (view active sessions, revoke tokens)
- Consider adding OAuth providers (Google, GitHub)
