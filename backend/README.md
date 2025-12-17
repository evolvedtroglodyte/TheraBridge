# TherapyBridge Backend

FastAPI backend for therapy session management, audio transcription, and AI-powered note extraction.

## Quick Start

### 1. Setup (One-Time)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

The backend uses the `.env` file. Copy `.env.example` and fill in your credentials:

```bash
# Database
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require

# OpenAI API
OPENAI_API_KEY=sk-xxx
```

### 3. Initialize Database & Run Server

```bash
# Apply database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

Server runs at: http://localhost:8000
API docs at: http://localhost:8000/docs

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI application & lifespan
│   ├── database.py             # Database connection & session management
│   ├── config.py               # Configuration (if created)
│   ├── models/
│   │   ├── schemas.py          # Pydantic request/response models
│   │   └── db_models.py        # SQLAlchemy ORM models
│   ├── routers/
│   │   ├── sessions.py         # Session upload & management (324 lines)
│   │   ├── patients.py         # Patient endpoints (71 lines)
│   │   └── auth.py             # Authentication (signup, login, logout)
│   ├── services/
│   │   ├── transcription.py    # Whisper/Pipeline wrapper (27 lines)
│   │   ├── note_extraction.py  # GPT-4o extraction service (187 lines)
│   │   └── __init__.py         # Service initialization
│   ├── middleware/
│   │   └── auth.py             # JWT verification middleware
│   └── middleware.py           # CORS, rate limiting
├── alembic/                    # Database migrations
│   ├── env.py                  # Migration environment
│   ├── versions/               # Migration files
│   └── alembic.ini            # Alembic config
├── tests/
│   ├── test_extraction_service.py    # Note extraction service tests
│   ├── test_e2e_auth_flow.py         # End-to-end authentication flow tests
│   ├── test_auth_integration.py      # Integration tests for auth endpoints
│   ├── test_auth_rbac.py             # Role-based access control tests
│   ├── conftest.py                   # Pytest configuration & fixtures
│   ├── fixtures/
│   │   ├── sample_transcripts.py      # Sample transcript data for tests
│   │   └── __init__.py
│   └── __init__.py
├── migrations/
│   └── analysis/               # Migration documentation
├── .env                        # Environment variables (local)
├── .env.example               # Environment template
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## API Endpoints

### Sessions - Audio Upload & Processing
- `POST /api/sessions/upload` - Upload audio file → returns session_id immediately
- `GET /api/sessions` - List all sessions (supports filtering by patient_id, status)
- `GET /api/sessions/{id}` - Get session details (status, transcript, extracted notes)
- `GET /api/sessions/{id}/notes` - Get extracted notes only
- `POST /api/sessions/{id}/extract-notes` - Manually trigger re-extraction

### Patients - Patient Management
- `POST /api/patients` - Create patient
- `GET /api/patients` - List all patients
- `GET /api/patients/{id}` - Get patient details

### Authentication - User Management
- `POST /api/auth/signup` - Register new user (therapist, patient, or admin)
- `POST /api/auth/login` - Authenticate with email/password
- `POST /api/auth/refresh` - Get new access token using refresh token
- `POST /api/auth/logout` - Revoke refresh token
- `GET /api/auth/me` - Get current user info

### Health & Status
- `GET /` - Simple health check
- `GET /health` - Detailed health status (database, services)

## Processing Pipeline

Sessions are processed asynchronously through these stages:

1. **Upload** (instant) - Audio file received, session created with status `uploading`
2. **Transcription** (30-120s) - Whisper API transcribes audio → status `transcribing` → `transcribed`
3. **Extraction** (20-60s) - GPT-4o extracts clinical notes → status `extracting_notes` → `processed`
4. **Complete** - All data saved to database, ready for review

**Status Progression:** `uploading` → `transcribing` → `transcribed` → `extracting_notes` → `processed`

## Testing

### Quick Test (Automated Script)

```bash
cd backend
source venv/bin/activate

# Run the automated pipeline test
./test_pipeline.sh

# Or with your own audio file
./test_pipeline.sh /path/to/your/audio.mp3
```

### Manual Testing Steps

**Terminal 1 - Start Server:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Terminal 2 - Run Tests:**
```bash
# Health check
curl http://localhost:8000/health | jq

# Get patient ID
PATIENT_ID=$(curl -s http://localhost:8000/api/patients/ | jq -r '.[0].id')

# Upload audio
SESSION_ID=$(curl -s -X POST "http://localhost:8000/api/sessions/upload?patient_id=$PATIENT_ID" \
  -F "file=@sample.mp3" | jq -r '.id')

# Monitor status
curl "http://localhost:8000/api/sessions/$SESSION_ID" | jq '.status'

# Get extracted notes (when status is "processed")
curl "http://localhost:8000/api/sessions/$SESSION_ID/notes" | jq
```

### Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_extraction_service.py -v

# Run specific test
pytest tests/test_extraction_service.py::test_extract_notes_basic -v

# With coverage
pytest tests/ --cov=app
```

### Interactive API Testing

Open http://localhost:8000/docs in your browser for interactive Swagger UI:
1. Try each endpoint without writing code
2. See request/response schemas
3. Built-in authorization (when tokens are set)

## Usage Examples

### Upload a Session

```bash
curl -X POST "http://localhost:8000/api/sessions/upload?patient_id=PATIENT_UUID" \
  -F "file=@session.mp3" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response: `{"id": "SESSION_ID", "status": "uploading", ...}`

### Check Processing Status

```bash
curl "http://localhost:8000/api/sessions/SESSION_ID" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | jq '.status'
```

### Get Extracted Clinical Notes

```bash
curl "http://localhost:8000/api/sessions/SESSION_ID/notes" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" | jq
```

Response includes:
- `key_topics` - Main subjects discussed (3-7 items)
- `topic_summary` - 2-3 sentence overview
- `strategies` - Coping techniques identified
- `action_items` - Homework/tasks assigned
- `session_mood` - Overall emotional tone (very_low, low, neutral, positive, very_positive)
- `mood_trajectory` - Direction of mood (improving, declining, stable, fluctuating)
- `therapist_notes` - Professional clinical summary (150-200 words)
- `patient_summary` - Warm, supportive summary (100-150 words)
- `risk_flags` - Safety concerns (if any)

### Sign Up New User

```bash
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "therapist@example.com",
    "password": "securepass123",
    "full_name": "Dr. Jane Smith",
    "role": "therapist"
  }'
```

Response: `{"access_token": "...", "refresh_token": "...", "expires_in": 1800}`

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "therapist@example.com",
    "password": "securepass123"
  }'
```

### Refresh Access Token

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

## Authentication

TherapyBridge uses JWT-based authentication with refresh token rotation.

### Token Details

- **Access Token**: 30 minutes validity (use for API requests)
- **Refresh Token**: 7 days validity (single-use, rotated on each refresh)
- **Signing**: HS256 with 32-byte secret key
- **Password**: Bcrypt hashing with 12 rounds

### Security Features

- Automatic token rotation (old refresh token revoked when new one issued)
- Rate limiting: 5 login attempts per minute per IP
- Password minimum: 8 characters
- SQL injection protection via SQLAlchemy ORM
- CORS configured for frontend origin only
- Refresh tokens stored in database for revocation support

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| POST /auth/login | 5 requests | 1 minute |
| All other endpoints | 100 requests | 1 minute |

## Database Schema

### Key Tables

**users** - Authentication & user info
- `id` (UUID) - Primary key
- `email` (VARCHAR) - Unique email
- `hashed_password` (TEXT) - Bcrypt hash
- `full_name` (VARCHAR) - User's name
- `role` (ENUM) - therapist, patient, or admin
- `is_active` (BOOLEAN) - Account status
- `created_at`, `updated_at` (TIMESTAMP)

**auth_sessions** - Refresh token management
- `id` (UUID) - Primary key
- `user_id` (UUID) - Foreign key to users
- `refresh_token` (VARCHAR) - Token hash
- `expires_at` (TIMESTAMP) - Token expiration
- `is_revoked` (BOOLEAN) - Revocation status
- `created_at` (TIMESTAMP)

**patients** - Patient information
- `id` (UUID) - Primary key
- `name` (VARCHAR) - Patient name
- `email` (VARCHAR) - Contact email
- `phone` (VARCHAR) - Contact phone
- `therapist_id` (UUID) - Foreign key to users

**sessions** - Therapy session records
- `id` (UUID) - Primary key
- `patient_id` (UUID) - Foreign key
- `therapist_id` (UUID) - Foreign key
- `status` (ENUM) - uploading, transcribing, transcribed, extracting_notes, processed, failed
- `audio_filename` (VARCHAR) - Uploaded file name
- `transcript_text` (TEXT) - Full transcript
- `extracted_notes` (JSONB) - AI-extracted data
- `created_at`, `updated_at` (TIMESTAMP)

### Migrations

Alembic manages database migrations:

```bash
# View migration history
alembic history --verbose

# Apply all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Generate new migration (auto-detect model changes)
alembic revision --autogenerate -m "Description"
```

## Cost Estimation

Per 30-minute therapy session:

- **Whisper API**: $0.006/min → ~$0.18 per session
- **GPT-4o Extraction**: ~$0.01-0.03 per session
- **Total**: ~$0.20 per session

Monitor costs in OpenAI dashboard: https://platform.openai.com/usage

## Services Layer Architecture

### Note Extraction Service (187 lines)

**File:** `app/services/note_extraction.py`

Extracts structured clinical notes from transcripts using GPT-4o.

**Features:**
- Async extraction with timeout protection
- JSON response validation (Pydantic)
- Cost estimation (`estimate_cost()`)
- Comprehensive prompt engineering
- Type hints throughout

**Known Issues (To Fix):**
- Currently uses sync OpenAI client (should be async)
- Global singleton pattern (should use dependency injection)
- Environment loading scattered across files
- Missing error handling for API failures

### Transcription Service (27 lines)

**File:** `app/services/transcription.py`

Wrapper around the audio transcription pipeline.

**Features:**
- Supports Whisper API or local GPU transcription
- Returns structured transcript with segments
- Async interface

**Known Issues (To Fix):**
- Path navigation is brittle (hardcoded relative paths)
- No error handling
- No logging

## Troubleshooting

### Server Won't Start

```bash
# Check database connection
echo $DATABASE_URL

# Test migrations
alembic current

# Apply missing migrations
alembic upgrade head
```

### "401 Unauthorized" - Token Invalid or Expired

```bash
# Get new access token using refresh token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'

# Or login again
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "pass123"}'
```

### "429 Too Many Requests" - Rate Limited

Wait for the `retry_after` seconds before retrying. Rate limit is 5 login attempts per minute.

### Upload Fails

```bash
# Check patient exists
curl http://localhost:8000/api/patients/

# Verify audio file format
file /path/to/audio.mp3

# Check file size (max 100MB)
ls -lh /path/to/audio.mp3
```

### Processing Stuck or Failed

```bash
# Check error message
curl "http://localhost:8000/api/sessions/SESSION_ID" | jq '.error_message'

# Check server logs (view terminal where uvicorn is running)

# Verify OpenAI API key is set
echo $OPENAI_API_KEY
```

## Development Notes

### Adding New Endpoints

1. Create router in `app/routers/`
2. Add routes with proper type hints
3. Use `Depends(get_db)` for database access
4. Add middleware authentication if needed
5. Document with docstrings
6. Add tests in `tests/`

### Modifying Database Schema

1. Update models in `app/models/db_models.py`
2. Generate migration: `alembic revision --autogenerate -m "Description"`
3. Review generated migration file
4. Test locally: `alembic upgrade head`
5. Commit migration file with code changes

### Adding New Services

1. Create class in `app/services/`
2. Implement async methods with type hints
3. Initialize in `app/main.py` lifespan
4. Inject via `Depends()` in routers
5. Add error handling (try-catch, timeouts)
6. Write unit tests with mocks
7. Add logging for debugging

## Known Technical Debt

### Critical (Fix Before Production)
- [ ] Upgrade to AsyncOpenAI client (currently blocking event loop)
- [ ] Add error handling with retry logic in background tasks
- [ ] Add timeouts to OpenAI API calls
- [ ] Implement proper dependency injection (replace global singleton)

### Important (Next Sprint)
- [ ] Create base service class for common patterns
- [ ] Write service unit tests (target 80%+ coverage)
- [ ] Add structured logging (replace print statements)
- [ ] Centralize environment configuration

### Nice to Have (Post-MVP)
- [ ] Implement caching for identical extractions
- [ ] Add request telemetry/observability
- [ ] Support multiple LLM providers (fallback)
- [ ] Batch processing queue for high load

## Next Steps

1. **Deploy Backend** - Move from local to cloud (AWS Lambda, Railway, Render)
2. **Add Production Authentication** - Implement Auth.js on frontend
3. **Performance Testing** - Load test with concurrent sessions
4. **Monitoring** - Add error tracking (Sentry), metrics (DataDog)
5. **Compliance** - HIPAA compliance review for healthcare data
