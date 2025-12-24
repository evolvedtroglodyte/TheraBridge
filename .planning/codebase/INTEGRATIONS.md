# External Integrations

**Analysis Date:** 2026-01-08

## APIs & External Services

**AI/LLM Services:**
- **OpenAI GPT-5 Series** - Session analysis (mood, topics, breakthrough detection, prose generation)
  - SDK/Client: OpenAI 1.54.4 (backend), OpenAI 6.15.0 (frontend)
  - Auth: API key in `OPENAI_API_KEY` env var
  - Files: `backend/app/services/mood_analyzer.py`, `backend/app/services/topic_extractor.py`, `backend/app/services/breakthrough_detector.py`, `backend/app/services/deep_analyzer.py`, `backend/app/services/prose_generator.py`
  - Cost: ~$0.042/session (Wave 1 + Wave 2 combined)

- **OpenAI Whisper API** - Audio transcription
  - SDK/Client: OpenAI 1.59.6
  - Auth: API key in `OPENAI_API_KEY` env var
  - Files: `audio-transcription-pipeline/src/pipeline.py`
  - Cost: ~$3.60 for 60-minute sessions

**Speech Processing:**
- **PyAnnote.audio 3.1** - Speaker diarization (local ML model)
  - Integration method: Python library via HuggingFace
  - Auth: HuggingFace token in `HUGGINGFACE_TOKEN` env var
  - Files: `audio-transcription-pipeline/src/`
  - No API costs (runs locally or on GPU)

**Web Scraping:**
- **Crawl4ai 0.7.4+** - JavaScript-rendering web scraper
  - Integration method: Python library with Playwright backend
  - Files: `Scrapping/src/scraper/`
  - No external API (runs locally)

## Data Storage

**Databases:**
- **PostgreSQL on Supabase** - Primary data store
  - Connection: via `DATABASE_URL` env var (Neon PostgreSQL)
  - Client: Supabase 2.9.0 (Python), Supabase.js 2.89.0 (JavaScript)
  - Files: `backend/app/database.py`, `frontend/lib/api-client.ts`
  - Migrations: 11 migration files in `backend/supabase/migrations/`
  - Schema: Users, therapy_sessions, transcripts, analysis results, breakthrough history

**File Storage:**
- **Local filesystem** - Audio uploads (development)
  - Location: `backend/uploads/audio/` (runtime only, gitignored)
  - Files: `backend/app/routers/sessions.py`

**Caching:**
- **Redis 5.2.0** - Optional task queue backend
  - Connection: via `REDIS_URL` env var
  - Client: redis-py 5.2.0
  - Files: `backend/app/config.py`
  - Status: Configured but not required for core functionality

## Authentication & Identity

**Auth Provider:**
- **JWT-based authentication** - Custom token system
  - Implementation: python-jose 3.3.0 for JWT encoding/decoding
  - Token storage: httpOnly cookies (future), localStorage for demo tokens
  - Session management: JWT with configurable expiration
  - Files: `backend/app/middleware/demo_auth.py`, `frontend/lib/demo-token-storage.ts`

**Demo Mode:**
- **Custom demo tokens** - UUID-based temporary access
  - Implementation: X-Demo-Token header validation
  - Files: `backend/app/middleware/demo_auth.py`, `frontend/lib/demo-api-client.ts`
  - Expiration: Configurable via JWT_EXPIRE_MINUTES

**OAuth Integrations:**
- None currently implemented

## Monitoring & Observability

**Error Tracking:**
- None (planned: Sentry)

**Analytics:**
- None (planned: Mixpanel)

**Logs:**
- **Railway.app logs** - stdout/stderr streaming
  - Integration: Automatic via Railway platform
  - Retention: Based on Railway plan
  - Files: All Python scripts use `print(..., flush=True)` for Railway visibility
  - Frontend: Browser console logging (debug mode via `NEXT_PUBLIC_DEBUG_POLLING`)

## CI/CD & Deployment

**Hosting:**
- **Railway.app** - Full-stack hosting platform
  - Deployment: Automatic on main branch push
  - Environment vars: Configured in Railway dashboard
  - Files: `frontend/railway.json`, `backend/railway.json`
  - Services: Next.js frontend + FastAPI backend

**CI Pipeline:**
- **Pre-commit hooks** - Local quality gates
  - Workflows: `.pre-commit-config.yaml`
  - Checks: Black, isort, Prettier, ESLint, detect-secrets
  - No GitHub Actions (local-only enforcement)

## Environment Configuration

**Development:**
- Required env vars: `DATABASE_URL`, `OPENAI_API_KEY`, `NEXT_PUBLIC_API_URL`
- Secrets location: `.env` files (gitignored: `.env.example` as template)
- Mock/stub services: Demo mode with mock transcripts (`backend/scripts/seed_all_sessions.py`)

**Staging:**
- Not currently configured (production-only deployment)

**Production:**
- Secrets management: Railway environment variables
- Database: Neon PostgreSQL via Supabase (managed, daily backups)
- Failover/redundancy: Single-region deployment (no HA)

## Webhooks & Callbacks

**Incoming:**
- None currently implemented

**Outgoing:**
- None currently implemented

## Real-Time Updates

**Server-Sent Events (SSE):**
- **Event stream** - Real-time session analysis updates
  - Endpoint: `/api/sse/demo-events` (`backend/app/routers/sse.py`)
  - Events: Wave 1 complete, Wave 2 complete, analysis ready
  - Client: `frontend/hooks/use-pipeline-events.ts`
  - Status: Disabled by default (polling fallback active via `NEXT_PUBLIC_SSE_ENABLED=false`)
  - Issue: Subprocess isolation breaks in-memory event queue

**Polling Fallback:**
- **Status endpoint** - Polls `/api/demo/status` every 5 seconds
  - Files: `frontend/app/patient/lib/usePatientSessions.ts`
  - Configuration: `frontend/lib/polling-config.ts` (1s Wave 1, 3s Wave 2)

---

*Integration audit: 2026-01-08*
*Update when adding/removing external services*
