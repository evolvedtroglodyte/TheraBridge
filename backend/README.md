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
│   │   ├── cleanup.py          # Cleanup endpoints (248 lines)
│   │   ├── analytics.py        # Analytics endpoints (200+ lines)
│   │   └── email_verification.py # Email verification endpoints
│   ├── auth/
│   │   ├── router.py           # Authentication routes (signup, login, logout)
│   │   ├── utils.py            # Auth utilities (JWT, password hashing)
│   │   ├── models.py           # Auth database models
│   │   ├── schemas.py          # Auth request/response models
│   │   ├── dependencies.py     # Auth dependencies (get_current_user)
│   │   └── config.py           # Auth configuration
│   ├── services/
│   │   ├── transcription.py         # Whisper/Pipeline wrapper (27 lines)
│   │   ├── note_extraction.py       # GPT-4o extraction service (187 lines)
│   │   ├── cleanup.py               # Audio cleanup service (574 lines)
│   │   ├── analytics_service.py     # Analytics computation service
│   │   ├── analytics_scheduler.py   # Background job scheduler (APScheduler)
│   │   ├── email_service.py         # Email sending service (SMTP/SendGrid/SES)
│   │   └── __init__.py              # Service initialization
│   ├── templates/
│   │   └── emails/              # Email templates (Jinja2 HTML)
│   │       ├── verification.html     # Email verification template
│   │       └── password_reset.html   # Password reset template (ready)
│   ├── middleware/
│   │   ├── rate_limit.py       # Rate limiting middleware
│   │   └── __init__.py         # Middleware initialization
├── alembic/                    # Database migrations
│   ├── env.py                  # Migration environment
│   ├── versions/               # Migration files
│   └── alembic.ini            # Alembic config
├── tests/
│   ├── test_extraction_service.py    # Note extraction service tests
│   ├── test_e2e_auth_flow.py         # End-to-end authentication flow tests
│   ├── test_auth_integration.py      # Integration tests for auth endpoints
│   ├── test_auth_rbac.py             # Role-based access control tests
│   ├── test_analytics_endpoints.py   # Analytics API endpoint tests
│   ├── test_analytics_scheduler.py   # Background scheduler tests
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

### Cleanup - Audio File Management
- `POST /api/admin/cleanup/orphaned-files` - Clean up orphaned audio files (with dry-run option)
- `POST /api/admin/cleanup/failed-sessions` - Clean up audio from old failed sessions (with dry-run option)
- `POST /api/admin/cleanup/all` - Run all cleanup operations
- `GET /api/admin/cleanup/status` - Get cleanup statistics without deleting
- `GET /api/admin/cleanup/config` - View current cleanup configuration

**Security:** All cleanup endpoints require therapist or admin role.

### Authentication - User Management
- `POST /api/auth/signup` - Register new user (therapist, patient, or admin)
- `POST /api/auth/login` - Authenticate with email/password
- `POST /api/auth/refresh` - Get new access token using refresh token
- `POST /api/auth/logout` - Revoke refresh token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/verify-email` - Verify email address using token
- `POST /api/auth/resend-verification` - Resend verification email
- `GET /api/auth/verify-status` - Check email verification status

### Analytics - Therapist Insights
- `GET /api/v1/analytics/overview` - Practice overview (total/active patients, sessions, completion rate)
- `GET /api/v1/analytics/patients/{patient_id}/progress` - Patient progress metrics (sessions, trends, topics)
- `GET /api/v1/analytics/session-trends` - Session activity over time (daily/weekly aggregates)
- `GET /api/v1/analytics/common-topics` - Most discussed topics across patients

**Security:** All analytics endpoints require therapist role and authentication.

### Export & Reporting - Documentation Export
- `POST /api/v1/export/session-notes` - Export session notes (PDF/DOCX)
- `POST /api/v1/export/progress-report` - Export progress report for patient (PDF/DOCX)
- `GET /api/v1/export/jobs` - List export jobs with status
- `GET /api/v1/export/jobs/{job_id}` - Get export job status
- `GET /api/v1/export/download/{job_id}` - Download completed export
- `DELETE /api/v1/export/jobs/{job_id}` - Delete export job

**Features:** Background processing, HIPAA audit logging, rate limiting (20/hour), 7-day file expiration
**Security:** All export endpoints require therapist role. Downloads logged with IP/user agent.

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

## Analytics Dashboard

Feature 2 provides therapists with insights into patient progress, session patterns, and treatment effectiveness through pre-computed analytics and background aggregation.

### API Endpoints

#### GET /api/v1/analytics/overview

Returns practice overview for the authenticated therapist.

**Authentication:** Required (Therapist role)

**Response:**
```json
{
  "total_patients": 24,
  "active_patients": 18,
  "sessions_this_week": 12,
  "sessions_this_month": 48,
  "upcoming_sessions": 5,
  "completion_rate": 0.92
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/analytics/overview" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### GET /api/v1/analytics/patients/{patient_id}/progress

Returns detailed progress metrics for a specific patient.

**Authentication:** Required (Therapist role, patient must be assigned to therapist)

**Query Parameters:**
- `weeks` (optional, default: 12) - Number of weeks of historical data

**Response:**
```json
{
  "patient_id": "uuid",
  "patient_name": "Jane Smith",
  "total_sessions": 24,
  "recent_sessions": [
    {
      "date": "2025-12-15",
      "mood": "positive",
      "key_topics": ["anxiety", "work stress"],
      "progress_notes": "Improved coping skills"
    }
  ],
  "mood_trend": {
    "current": "positive",
    "trajectory": "improving",
    "change_percent": 15
  },
  "common_topics": [
    {"topic": "anxiety", "frequency": 18},
    {"topic": "work stress", "frequency": 12}
  ],
  "attendance_rate": 0.96
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/analytics/patients/PATIENT_UUID/progress?weeks=8" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### GET /api/v1/analytics/session-trends

Returns session activity trends over time (daily/weekly aggregates).

**Authentication:** Required (Therapist role)

**Query Parameters:**
- `period` (optional, default: "30d") - Time period: "7d", "30d", "90d", "1y"
- `granularity` (optional, default: "day") - Aggregation level: "day", "week", "month"

**Response:**
```json
{
  "period": "30d",
  "granularity": "day",
  "data_points": [
    {
      "date": "2025-12-01",
      "sessions_completed": 5,
      "sessions_cancelled": 1,
      "avg_session_duration_min": 52,
      "completion_rate": 0.83
    }
  ],
  "summary": {
    "total_sessions": 48,
    "avg_per_day": 1.6,
    "peak_day": "2025-12-10",
    "completion_rate": 0.92
  }
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/analytics/session-trends?period=30d&granularity=week" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### GET /api/v1/analytics/common-topics

Returns most frequently discussed topics across all patients.

**Authentication:** Required (Therapist role)

**Query Parameters:**
- `limit` (optional, default: 20) - Maximum topics to return
- `weeks` (optional, default: 12) - Number of weeks to analyze

**Response:**
```json
{
  "time_period_weeks": 12,
  "topics": [
    {
      "topic": "anxiety",
      "frequency": 42,
      "patients_affected": 15,
      "trend": "increasing"
    },
    {
      "topic": "work stress",
      "frequency": 35,
      "patients_affected": 12,
      "trend": "stable"
    }
  ]
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/analytics/common-topics?limit=10&weeks=8" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Background Jobs & Scheduler

Analytics uses **APScheduler** to pre-compute daily statistics and reduce query load. The scheduler runs automatically when the server starts (if enabled).

**Scheduled Jobs:**

1. **Daily Stats Aggregation** - Runs daily at midnight UTC (configurable)
   - Aggregates session metrics per therapist
   - Computes completion rates, patient counts, session trends
   - Stores results in `daily_stats` table for fast retrieval

2. **Weekly Progress Snapshot** - Runs Sundays at 1:00 AM UTC
   - Creates patient progress snapshots (mood trends, topic frequencies)
   - Enables historical comparison without recalculating
   - Stores results in `patient_progress` table

**Configuration (`.env`):**
```bash
# Enable background scheduler (default: true)
ENABLE_ANALYTICS_SCHEDULER=true

# Hour to run daily aggregation (0-23, default: 0 = midnight UTC)
DAILY_AGGREGATION_HOUR=0

# Timezone for scheduler (default: UTC)
SCHEDULER_TIMEZONE=UTC
```

**Disable Scheduler:**
```bash
# In .env
ENABLE_ANALYTICS_SCHEDULER=false
```

**Manual Trigger:**
```bash
# Run aggregation manually via Python REPL
cd backend
source venv/bin/activate
python -c "
from app.services.analytics_scheduler import run_daily_aggregation
import asyncio
asyncio.run(run_daily_aggregation())
"
```

**Scheduler Logs:**
```
INFO:     Scheduler started: Daily stats at 00:00 UTC
INFO:     Running daily analytics aggregation...
INFO:     Daily stats computed for 3 therapists
INFO:     Next run: 2025-12-18 00:00:00 UTC
```

### Database Tables

Analytics data is stored in three dedicated tables:

**session_metrics** - Per-session analytics metrics
- `id` (UUID) - Primary key
- `session_id` (UUID) - Foreign key to sessions
- `therapist_id` (UUID) - Foreign key to users
- `patient_id` (UUID) - Foreign key to patients
- `session_date` (DATE) - Session date
- `duration_minutes` (INTEGER) - Session length
- `mood_score` (INTEGER) - Numeric mood (1-5)
- `mood_label` (VARCHAR) - Mood label (very_low, low, neutral, positive, very_positive)
- `topic_count` (INTEGER) - Number of topics discussed
- `topics` (JSONB) - Array of key topics
- `strategies_count` (INTEGER) - Number of coping strategies identified
- `action_items_count` (INTEGER) - Number of action items assigned
- `has_risk_flags` (BOOLEAN) - Whether session contains risk flags
- `created_at` (TIMESTAMP)

**daily_stats** - Aggregated daily statistics per therapist
- `id` (UUID) - Primary key
- `therapist_id` (UUID) - Foreign key to users
- `stat_date` (DATE) - Date of aggregation (unique per therapist)
- `total_sessions` (INTEGER) - Sessions on this date
- `completed_sessions` (INTEGER) - Completed sessions
- `cancelled_sessions` (INTEGER) - Cancelled sessions
- `active_patients` (INTEGER) - Patients with sessions this day
- `avg_duration_minutes` (FLOAT) - Average session duration
- `completion_rate` (FLOAT) - Percentage of completed sessions
- `created_at`, `updated_at` (TIMESTAMP)

**patient_progress** - Weekly patient progress snapshots
- `id` (UUID) - Primary key
- `patient_id` (UUID) - Foreign key to patients
- `therapist_id` (UUID) - Foreign key to users
- `week_start_date` (DATE) - Start of week (Monday)
- `sessions_count` (INTEGER) - Sessions this week
- `avg_mood_score` (FLOAT) - Average mood score (1-5)
- `mood_trajectory` (VARCHAR) - improving, declining, stable, fluctuating
- `common_topics` (JSONB) - Array of {topic, frequency}
- `attendance_rate` (FLOAT) - Percentage of scheduled sessions attended
- `created_at` (TIMESTAMP)

**Indexes:**
- `session_metrics`: (therapist_id, session_date), (patient_id, session_date)
- `daily_stats`: (therapist_id, stat_date) - UNIQUE
- `patient_progress`: (patient_id, week_start_date), (therapist_id, week_start_date)

### Migration

Apply analytics database schema:
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

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

# Run specific test suite
pytest tests/test_extraction_service.py -v      # Note extraction tests
pytest tests/test_e2e_auth_flow.py -v           # End-to-end auth flow
pytest tests/test_auth_integration.py -v        # Auth endpoint integration
pytest tests/test_auth_rbac.py -v               # Role-based access control
pytest tests/test_analytics_endpoints.py -v     # Analytics API tests
pytest tests/test_analytics_scheduler.py -v     # Background job tests

# Run specific test
pytest tests/test_extraction_service.py::test_extract_notes_basic -v

# With coverage report
pytest tests/ --cov=app --cov-report=html
```

**Analytics Test Fixtures:**
- `analytics_patient` - Patient with historical session data
- `sample_sessions` - 10+ sessions with varying moods and topics
- `mock_scheduler` - APScheduler mock for testing background jobs

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
    "password": "SecurePass123!",
    "first_name": "Jane",
    "last_name": "Smith",
    "role": "therapist"
  }'
```

**Note:** Password must be 12+ characters with uppercase, lowercase, number, and special character.

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

### Verify Email Address

```bash
# User receives verification email after signup
# Email contains a link like: http://localhost:3000/auth/verify?token=VERIFICATION_TOKEN

# Frontend calls backend with token:
curl -X POST http://localhost:8000/api/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "VERIFICATION_TOKEN"}'
```

Response: `{"message": "Email verified successfully", "email": "user@example.com", "is_verified": true}`

### Resend Verification Email

```bash
curl -X POST http://localhost:8000/api/auth/resend-verification \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

### Get Practice Analytics Overview

```bash
curl "http://localhost:8000/api/v1/analytics/overview" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response includes total patients, active patients, sessions this week/month, and completion rate.

### Get Patient Progress Report

```bash
curl "http://localhost:8000/api/v1/analytics/patients/PATIENT_UUID/progress?weeks=12" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

Response includes session history, mood trends, common topics, and attendance rate for the past 12 weeks.

## Authentication

TherapyBridge uses JWT-based authentication with refresh token rotation and email verification.

### User Registration Flow

1. User signs up with `first_name`, `last_name`, `email`, `password`, and `role`
2. Account created with `is_verified=false`
3. Verification email sent automatically (if email service configured)
4. User clicks link in email to verify account
5. Account status updated to `is_verified=true`

### Email Service Configuration

TherapyBridge supports multiple email providers for sending verification emails, password resets, and notifications.

**Supported Providers:**
1. **SMTP** (default) - Standard SMTP server (Gmail, Mailgun, custom servers)
2. **SendGrid** - API-based email delivery with analytics
3. **AWS SES** - Amazon Simple Email Service (cost-effective for high volume)

---

#### Setup Guide: SMTP (Recommended for Development)

SMTP works with any standard email server. Great for development and small deployments.

**Common SMTP Providers:**
- **Gmail**: smtp.gmail.com:587 (requires App Password)
- **Mailgun**: smtp.mailgun.org:587
- **SendInBlue**: smtp-relay.sendinblue.com:587

**Configuration** (add to `.env`):
```bash
EMAIL_PROVIDER=smtp
EMAIL_FROM=noreply@therapybridge.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FRONTEND_URL=http://localhost:3000
```

**Gmail Setup:**
1. Enable 2-factor authentication on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use the 16-character App Password as `SMTP_PASSWORD`

**Test SMTP:**
```bash
# Create test account (triggers verification email)
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "Test",
    "last_name": "User",
    "role": "therapist"
  }'
```

---

#### Setup Guide: SendGrid (Recommended for Production)

SendGrid provides reliable API-based email delivery with deliverability analytics.

**Setup Steps:**
1. Sign up at https://sendgrid.com (free tier: 100 emails/day)
2. Create API key: Settings → API Keys → Create API Key
3. Select "Mail Send" permission
4. Verify sender email or domain

**Configuration** (add to `.env`):
```bash
EMAIL_PROVIDER=sendgrid
EMAIL_FROM=noreply@therapybridge.com  # Must be verified in SendGrid
EMAIL_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
FRONTEND_URL=http://localhost:3000
```

**Install SendGrid SDK:**
```bash
pip install sendgrid
pip freeze > requirements.txt
```

**Test SendGrid:**
```bash
# Check SendGrid dashboard after signup: https://app.sendgrid.com/email_activity
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com", "password": "SecurePass123!", "first_name": "Test", "last_name": "User", "role": "therapist"}'
```

---

#### Setup Guide: AWS SES (Recommended for AWS Deployments)

AWS SES is cost-effective for high-volume email ($0.10 per 1,000 emails).

**Setup Steps:**
1. Sign in to AWS Console → Amazon SES
2. Verify email address: Identities → Create Identity
3. Request production access (initially in sandbox mode)
4. Create IAM user with `AmazonSESFullAccess` permission
5. Generate access key and secret key

**Configuration** (add to `.env`):
```bash
EMAIL_PROVIDER=ses
EMAIL_FROM=noreply@therapybridge.com  # Must be verified in SES
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-east-1
FRONTEND_URL=http://localhost:3000
```

**Install boto3 (AWS SDK):**
```bash
pip install boto3
pip freeze > requirements.txt
```

**Test AWS SES:**
```bash
# Verify AWS credentials
aws ses get-send-quota

# Test email sending (sandbox mode: recipient must be verified)
curl -X POST http://localhost:8000/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "verified-recipient@example.com", "password": "SecurePass123!", "first_name": "Test", "last_name": "User", "role": "therapist"}'
```

---

#### Provider Comparison

| Provider | Best For | Cost | Setup Complexity | Deliverability |
|----------|----------|------|------------------|----------------|
| **SMTP** | Development, small deployments | Free (Gmail) | Low | Medium |
| **SendGrid** | Production, analytics | Free tier, then $15/mo | Medium | High |
| **AWS SES** | AWS deployments, high volume | $0.10 per 1K emails | Medium-High | High |

**Recommendations:**
- **Development**: Gmail SMTP (quick setup)
- **Production (non-AWS)**: SendGrid (best deliverability)
- **Production (AWS)**: AWS SES (lowest cost)

---

#### Email Templates

TherapyBridge uses Jinja2 HTML templates for professional emails.

**Available Templates:**
- `app/templates/emails/verification.html` - Email verification
- `app/templates/emails/password_reset.html` - Password reset (ready for future use)

**Customizing Templates:**
1. Edit HTML files in `app/templates/emails/`
2. Use variables: `{{ user_name }}`, `{{ verification_url }}`, `{{ frontend_url }}`
3. Test by triggering verification emails

---

#### Troubleshooting

**SMTP Issues:**
- **"Authentication failed"**: Check SMTP_USERNAME and SMTP_PASSWORD
- **Gmail blocking**: Use App Password, not regular password
- **Connection refused**: Verify SMTP_PORT is 587

**SendGrid Issues:**
- **"Unauthorized"**: Verify EMAIL_API_KEY is correct
- **"From email not verified"**: Verify sender in SendGrid dashboard
- **403 error**: Check API key has Mail Send permission

**AWS SES Issues:**
- **"Email not verified"**: Verify sender email in SES console
- **"MessageRejected"**: In sandbox mode, recipient must be verified
- **"AccessDenied"**: Check IAM permissions for ses:SendEmail

**Check Logs:**
```bash
# Server logs show email status
uvicorn app.main:app --reload
# Look for: "Email sent via SMTP/SendGrid/SES: user@example.com"
```

---

#### Environment Variables Reference

**Required (all providers):**
```bash
EMAIL_PROVIDER=smtp              # smtp, sendgrid, or ses
EMAIL_FROM=noreply@example.com   # Sender email
FRONTEND_URL=http://localhost:3000  # For verification links
```

**SMTP-specific:**
```bash
SMTP_HOST=smtp.gmail.com         # SMTP server
SMTP_PORT=587                    # Port (587 for TLS)
SMTP_USERNAME=user@example.com   # Auth username
SMTP_PASSWORD=your-password      # Auth password
```

**SendGrid-specific:**
```bash
EMAIL_API_KEY=SG.xxxxxxxxx       # SendGrid API key
```

**AWS SES-specific:**
```bash
AWS_ACCESS_KEY_ID=AKIAxxxxx      # AWS access key
AWS_SECRET_ACCESS_KEY=xxxxxx     # AWS secret key
AWS_DEFAULT_REGION=us-east-1     # AWS region
```

---

### Token Details

- **Access Token**: 30 minutes validity (use for API requests)
- **Refresh Token**: 7 days validity (single-use, rotated on each refresh)
- **Verification Token**: 24 hours validity (single-use)
- **Signing**: HS256 with 32-byte secret key
- **Password**: Bcrypt hashing with 12 rounds

### Security Features

- Automatic token rotation (old refresh token revoked when new one issued)
- Rate limiting: 5 login attempts per minute per IP
- Password requirements: 12+ characters with uppercase, lowercase, number, special character
- SQL injection protection via SQLAlchemy ORM
- CORS configured for frontend origin only
- Refresh tokens stored in database for revocation support
- Email verification prevents unauthorized account creation

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
- `first_name` (VARCHAR) - User's first name
- `last_name` (VARCHAR) - User's last name
- `full_name` (VARCHAR) - Computed full name (backward compatibility)
- `role` (ENUM) - therapist, patient, or admin
- `is_active` (BOOLEAN) - Account status
- `is_verified` (BOOLEAN) - Email verification status
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

**session_metrics** - Analytics metrics per session (Feature 2)
- `id` (UUID) - Primary key
- `session_id` (UUID) - Foreign key to sessions
- `therapist_id` (UUID) - Foreign key to users
- `patient_id` (UUID) - Foreign key to patients
- `session_date` (DATE) - Session date
- `mood_score` (INTEGER) - Numeric mood (1-5)
- `topics` (JSONB) - Array of key topics
- `has_risk_flags` (BOOLEAN) - Risk flag indicator
- `created_at` (TIMESTAMP)

**daily_stats** - Aggregated daily statistics (Feature 2)
- `id` (UUID) - Primary key
- `therapist_id` (UUID) - Foreign key to users
- `stat_date` (DATE) - Date of aggregation
- `total_sessions` (INTEGER) - Sessions count
- `completion_rate` (FLOAT) - Success rate
- `active_patients` (INTEGER) - Patient count
- `created_at`, `updated_at` (TIMESTAMP)

**patient_progress** - Weekly progress snapshots (Feature 2)
- `id` (UUID) - Primary key
- `patient_id` (UUID) - Foreign key to patients
- `week_start_date` (DATE) - Start of week
- `avg_mood_score` (FLOAT) - Average mood
- `mood_trajectory` (VARCHAR) - Trend direction
- `common_topics` (JSONB) - Topic frequencies
- `created_at` (TIMESTAMP)

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

## Audio File Cleanup

The backend includes an automated cleanup service to manage orphaned audio files and prevent storage bloat.

### Cleanup Features

**Orphaned File Cleanup:**
- Identifies audio files in `uploads/audio/` not referenced in database
- Deletes files older than configured retention period (default: 24 hours)
- Includes both original and processed file variants

**Failed Session Cleanup:**
- Finds sessions with `status='failed'` older than retention period (default: 7 days)
- Deletes associated audio files to free storage
- Preserves session records for audit trail

**Safety Features:**
- Dry-run mode for testing before actual deletion
- Configurable retention periods
- Comprehensive logging of all operations
- Role-based access control (therapist/admin only)

### Configuration

Add to `.env`:

```bash
# Retention period for failed sessions (days, default: 7)
FAILED_SESSION_RETENTION_DAYS=7

# Retention period for orphaned files (hours, default: 24)
ORPHANED_FILE_RETENTION_HOURS=24

# Enable automatic cleanup on startup (default: false)
AUTO_CLEANUP_ON_STARTUP=false
```

### Manual Cleanup

**Check cleanup status (dry-run):**
```bash
curl "http://localhost:8000/api/admin/cleanup/status" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Run cleanup with dry-run:**
```bash
curl -X POST "http://localhost:8000/api/admin/cleanup/all?dry_run=true" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Run actual cleanup:**
```bash
curl -X POST "http://localhost:8000/api/admin/cleanup/all" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response includes:**
- Files deleted and sessions cleaned
- Total space freed (MB)
- Any errors encountered
- Dry-run flag status

### Scheduled Cleanup

For production environments, set up a cron job or scheduled task:

```bash
# Run cleanup daily at 3 AM
0 3 * * * cd /path/to/backend && source venv/bin/activate && python -c "import asyncio; from app.services.cleanup import run_scheduled_cleanup; asyncio.run(run_scheduled_cleanup())"
```

Or use Celery Beat, APScheduler, or cloud scheduler (AWS EventBridge, GCP Cloud Scheduler).

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

## Security & Testing

### Security Audit Summary (2025-12-17)

**Overall Security Score: 9.5/10** - Production-ready with minor improvements

**Strengths:**
- ✅ Bcrypt password hashing (12 rounds)
- ✅ JWT with refresh token rotation
- ✅ Rate limiting on auth endpoints (5 login/min, 3 signup/hour)
- ✅ SQL injection prevention (100% ORM usage)
- ✅ Comprehensive input validation (Pydantic)
- ✅ Refresh tokens hashed before storage
- ✅ Generic error messages prevent user enumeration

**Production Checklist:**
- [ ] Generate strong SECRET_KEY (32+ bytes) for production
- [ ] Update CORS allow_origins to production domain
- [ ] Add security event logging (failed logins, token failures)
- [ ] Run `pip audit` for dependency vulnerabilities
- [ ] Add database index on `auth_sessions.user_id` (optional performance)

### Test Coverage

**Authentication Tests: 59 total**
- `test_auth_integration.py` - 25 tests (happy paths, error cases, token rotation)
- `test_e2e_auth_flow.py` - 7 tests (complete user journeys, multi-device sessions)
- `test_auth_rbac.py` - 30 tests (role-based access control)

**Analytics Tests: 20+ total (Feature 2)**
- `test_analytics_endpoints.py` - API endpoint tests (overview, progress, trends, topics)
- `test_analytics_scheduler.py` - Background job tests (daily aggregation, weekly snapshots)

**Service Tests:**
- `test_extraction_service.py` - Note extraction service tests

**Key Test Scenarios:**
- Complete auth flow (signup → login → refresh → logout)
- Token rotation security (old tokens revoked)
- Multi-device session support
- Rate limiting enforcement
- Role-based access control (therapist, patient, admin)
- Password security (hashing, validation)
- Analytics data aggregation and trend calculation
- Background scheduler job execution
- Patient progress tracking over time

### Dependency Status

**Removed Dependencies:**
- `pytest-cov` - Not used (no coverage configuration)

**Confirmed Required:**
- `psycopg2-binary` - Used by admin scripts (backup, migrations)
- `alembic` - Database migrations
- `pydub` + `audioop-lts` - Audio pipeline dependencies

## Production Deployment

### Worker Scaling & Database Connections

When deploying TherapyBridge to production, understanding the relationship between application workers and database connections is critical to prevent "too many connections" errors.

#### Connection Pool Math

Each application worker maintains its own database connection pool. The total number of database connections is:

```
Total Connections = WORKERS × (DB_POOL_SIZE + DB_MAX_OVERFLOW)
```

**Example Calculations:**

| Workers | Pool Size | Max Overflow | Connections per Worker | Total Connections |
|---------|-----------|--------------|------------------------|-------------------|
| 1       | 10        | 20           | 30                     | 30                |
| 2       | 10        | 20           | 30                     | 60                |
| 4       | 10        | 20           | 30                     | 120               |
| 8       | 10        | 20           | 30                     | 240               |

#### Neon PostgreSQL Connection Limits

Neon PostgreSQL enforces connection limits based on your tier:

| Tier          | Max Connections | Notes                                    |
|---------------|-----------------|------------------------------------------|
| Free          | ~100            | Shared across all databases              |
| Paid (Scale)  | 200-500         | Varies by plan, check dashboard          |
| Enterprise    | 1000+           | Custom limits available                  |

**CRITICAL:** Exceeding your database connection limit causes the error:
```
FATAL: sorry, too many clients already
```

#### Recommended Worker Scaling Settings

**Single Worker (Development/Low Traffic)**
```bash
WORKERS=1
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
# Total: 30 connections (safe for all tiers)
```

**2 Workers (Small Production)**
```bash
WORKERS=2
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
# Total: 30 connections (safe for free tier)
```

**4 Workers (Medium Production)**
```bash
WORKERS=4
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
# Total: 60 connections (safe for free tier with headroom)
```

**8 Workers (High Traffic)**
```bash
WORKERS=8
DB_POOL_SIZE=3
DB_MAX_OVERFLOW=7
# Total: 80 connections (requires paid tier)
```

**16 Workers (Very High Traffic)**
```bash
WORKERS=16
DB_POOL_SIZE=3
DB_MAX_OVERFLOW=5
# Total: 128 connections (requires paid tier with 200+ limit)
```

#### Deployment Checklist

**Before Deploying:**

1. **Calculate Total Connections**
   ```bash
   # Formula: WORKERS * (DB_POOL_SIZE + DB_MAX_OVERFLOW)
   # Example: 4 * (5 + 10) = 60 connections
   ```

2. **Check Database Connection Limit**
   - Log into Neon dashboard
   - Navigate to your database settings
   - Verify connection limit for your tier
   - Ensure: `Total Connections < Database Limit - 10` (leave headroom)

3. **Configure Environment Variables**
   ```bash
   # In .env or deployment config
   WORKERS=4                    # Based on traffic requirements
   DB_POOL_SIZE=5              # Calculated from formula above
   DB_MAX_OVERFLOW=10          # Calculated from formula above
   DB_POOL_TIMEOUT=30          # Seconds to wait for connection
   ```

4. **Test Under Load**
   ```bash
   # Run load test to verify connection handling
   ab -n 1000 -c 50 http://your-api.com/health

   # Monitor database connections in Neon dashboard
   # Watch for "too many connections" errors in logs
   ```

**Production Environment Variables:**

```bash
# ============================================
# Production Deployment Configuration
# ============================================

# Environment
ENVIRONMENT=production
DEBUG=false                      # CRITICAL: Never enable in production (exposes PHI)

# Database
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
DB_POOL_SIZE=5                  # Adjust based on worker count
DB_MAX_OVERFLOW=10              # Adjust based on worker count
DB_POOL_TIMEOUT=30
SQL_ECHO=false                  # CRITICAL: Never enable in production (exposes PHI)

# Server
WORKERS=4                        # Scale based on traffic and database limits
HOST=0.0.0.0
PORT=8000

# Security
JWT_SECRET_KEY=CHANGE_THIS      # Generate with: openssl rand -hex 32
CORS_ORIGINS=https://your-frontend.com

# OpenAI
OPENAI_API_KEY=sk-production-key-here
OPENAI_TIMEOUT=120
OPENAI_MAX_RETRIES=3

# Logging
LOG_LEVEL=INFO                  # Use INFO or WARNING in production

# Cleanup
AUTO_CLEANUP_ON_STARTUP=false
FAILED_SESSION_RETENTION_DAYS=7
ORPHANED_FILE_RETENTION_HOURS=24

# Analytics
ENABLE_ANALYTICS_SCHEDULER=true
DAILY_AGGREGATION_HOUR=3        # 3 AM UTC (low traffic period)
SCHEDULER_TIMEZONE=UTC
```

### Deployment Platforms

**AWS Lambda (Serverless)**
- No worker configuration needed (auto-scales)
- Use RDS Proxy to manage database connections
- Connection pooling handled by proxy

**Render/Railway (Container)**
```bash
# Set environment variables in dashboard
WORKERS=4
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
```

**Docker Deployment**
```bash
# Dockerfile
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Gunicorn (Production WSGI)**
```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --timeout 120
```

### Monitoring Database Connections

**Query Active Connections (PostgreSQL)**
```sql
-- View current connection count
SELECT COUNT(*) FROM pg_stat_activity;

-- View connections by application
SELECT application_name, COUNT(*)
FROM pg_stat_activity
GROUP BY application_name;

-- View connection limit
SHOW max_connections;
```

**Neon Dashboard Monitoring:**
1. Navigate to Neon Console → Database → Monitoring
2. Check "Active Connections" graph
3. Set alerts for when connections approach limit
4. Review "Connection Pool" metrics

**Application Logging:**
```python
# Add to app/main.py for connection monitoring
@app.get("/api/health/connections")
async def connection_health(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT COUNT(*) FROM pg_stat_activity"))
    active_connections = result.scalar()
    return {
        "active_connections": active_connections,
        "pool_size": DB_POOL_SIZE,
        "max_overflow": DB_MAX_OVERFLOW,
        "worker_count": WORKERS,
        "theoretical_max": WORKERS * (DB_POOL_SIZE + DB_MAX_OVERFLOW)
    }
```

### Scaling Strategy

**Horizontal Scaling (Add Workers):**
1. Calculate new total connections: `NEW_WORKERS * (POOL_SIZE + MAX_OVERFLOW)`
2. Verify database can handle new total
3. If exceeding limit, reduce `DB_POOL_SIZE` or `DB_MAX_OVERFLOW`
4. Update environment variables
5. Deploy with rolling restart
6. Monitor connection count and error rates

**Vertical Scaling (Upgrade Database):**
1. Upgrade Neon tier to increase connection limit
2. Keep worker count and pool settings constant
3. Provides headroom for future growth

### Troubleshooting

**"Too Many Connections" Error**

```bash
# Symptom: FATAL: sorry, too many clients already

# Step 1: Check current configuration
echo "Total connections: $WORKERS * ($DB_POOL_SIZE + $DB_MAX_OVERFLOW)"

# Step 2: Reduce connections immediately
# Option A: Reduce workers (fastest)
WORKERS=2  # Deploy immediately

# Option B: Reduce pool size (requires restart)
DB_POOL_SIZE=3
DB_MAX_OVERFLOW=5

# Step 3: Upgrade database tier (long-term solution)
# Upgrade Neon plan in dashboard
```

**Connection Pool Exhausted**

```bash
# Symptom: QueuePool limit of size X overflow Y reached

# Increase pool size (verify total doesn't exceed database limit)
DB_MAX_OVERFLOW=30  # Allow more overflow connections
DB_POOL_TIMEOUT=60  # Wait longer for available connection
```

**Slow Queries Blocking Connections**

```sql
-- Find long-running queries
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active'
ORDER BY duration DESC
LIMIT 10;

-- Kill slow query (if safe)
SELECT pg_terminate_backend(PID);
```

## Next Steps

1. **Test Analytics Integration** - Verify analytics endpoints with frontend dashboard
2. **Monitor Scheduler Performance** - Ensure background jobs complete successfully
3. **Deploy Backend** - Move from local to cloud (AWS Lambda, Railway, Render)
4. **Add Production Authentication** - Implement Auth.js on frontend
5. **Performance Testing** - Load test with concurrent sessions
6. **Monitoring** - Add error tracking (Sentry), metrics (DataDog)
7. **Compliance** - HIPAA compliance review for healthcare data
