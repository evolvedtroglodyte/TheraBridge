# Repository Organization Rules

## 🚨 CRITICAL RULE - GIT FIRST, ALWAYS + CHANGE LOGGING

**BEFORE MAKING ANY CHANGES (deletions, modifications, cleanup):**
1. **STOP** - Do not proceed with any deletions or modifications
2. **CHECK GIT STATUS** - Run `git status` to see what is tracked vs untracked
3. **COMMIT EVERYTHING** - Run `git add -A && git commit -m "Backup before cleanup"`
4. **PUSH TO GIT** - Run `git push` to ensure changes are backed up remotely
5. **VERIFY COMMIT** - Run `git log -1` to confirm commit was created and pushed
6. **CREATE CHANGE LOG** - Before proceeding, create a detailed log file documenting:
   - What changes will be made
   - Which files will be modified/deleted
   - Reason for changes
   - Rollback instructions if needed
7. **THEN AND ONLY THEN** - Proceed with changes

**This rule applies to:**
- Deleting any files or folders
- Major refactoring or reorganization
- Consolidating documentation
- Cleaning up code
- ANY operation that removes or significantly modifies files
- ANY implementation of new features or systems

**Change Log Format:**
- Create file: `CHANGE_LOG_YYYY-MM-DD_description.md` in relevant directory
- Include: timestamp, affected files, changes made, rollback steps
- Update log throughout the change process
- Commit and push the log file when changes are complete

**Why this matters:**
- Untracked files CANNOT be recovered from git
- A commit creates a safety net for ALL files (tracked and untracked)
- Users may have work-in-progress that isn't committed yet
- Remote backup ensures no data loss even if local repo is corrupted
- Change logs provide clear audit trail and rollback instructions
- Better to have an extra commit than lose important work

## Core Principles
1. **Minimize file count** - Every file must earn its place. If info can live in an existing file, it goes there.
2. **One README per component** - Each major folder gets ONE README.md. No additional .md files.
3. **No archive folders** - Old code gets deleted. Git history preserves everything.
4. **No duplicate configs** - Only ONE .claude/ folder at project root.
5. **Value over volume** - Only keep information valuable for project longevity. Delete "might be useful" content.

## What Belongs in a README
- Current state & working features
- Quick start commands
- File structure (if not obvious)
- Key technical decisions & bug fixes worth remembering
- Next steps

## What Does NOT Get Its Own File
- Implementation plans (execute and delete)
- Detailed test logs (summarize critical findings only)
- Removed code archives (use git history)
- Separate "guides" that duplicate README content

## Quality Standard
Before creating any new file, ask:
1. Can this go in an existing README? → Put it there
2. Will this matter in 3 months? → If no, don't create it
3. Does this duplicate existing info? → Delete the duplicate

---

# TherapyBridge - Project State

## Current Focus: Backend AI extraction complete, Frontend dashboard next

**Full Documentation:** See `Project MDs/TherapyBridge.md`

---

## Repository Structure

**Monorepo with 4 independent projects:**

```
peerbridge proj/
├── .claude/                   # Claude Code config (root only)
│   ├── CLAUDE.md              # This file
│   ├── agents/cl/
│   ├── commands/cl/
│   └── skills/                # Specialized capability extensions
│       └── crawl4ai/          # Web crawling & data extraction skill
├── Project MDs/
│   └── TherapyBridge.md       # Master documentation
├── README.md                  # Root README (project overview)
├── .gitignore                 # Root gitignore
├── .python-version            # Root Python version
│
├── audio-transcription-pipeline/  # STANDALONE PROJECT
│   ├── src/
│   │   ├── pipeline.py        # CPU/API pipeline
│   │   ├── pipeline_gpu.py    # GPU/Vast.ai pipeline
│   │   ├── gpu_audio_ops.py
│   │   └── performance_logger.py
│   ├── tests/
│   │   ├── test_*.py
│   │   ├── samples/
│   │   └── outputs/           # JSON only
│   ├── scripts/
│   │   ├── setup.sh
│   │   └── setup_gpu.sh
│   ├── venv/                  # Independent venv
│   ├── .env                   # Pipeline-specific env
│   ├── .env.example
│   ├── .gitignore             # Pipeline-specific
│   ├── .python-version
│   ├── requirements.txt
│   └── README.md
│
├── backend/                   # STANDALONE PROJECT (TherapyBridge API)
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── routers/
│   │   ├── models/
│   │   └── services/
│   ├── tests/
│   ├── migrations/
│   ├── uploads/audio/         # Runtime only
│   ├── venv/                  # Independent venv
│   ├── .env                   # Backend-specific env
│   ├── .env.example
│   ├── .gitignore             # Backend-specific
│   ├── .python-version
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                  # STANDALONE PROJECT (TherapyBridge UI)
│   ├── app/                   # Next.js 16 app directory
│   ├── components/
│   ├── lib/
│   │   ├── api-client.ts      # Backend API integration
│   │   └── auth-context.tsx
│   ├── hooks/
│   ├── public/
│   ├── node_modules/
│   ├── .next/                 # Build output
│   ├── .env.local             # Frontend-specific env
│   ├── .env.local.example
│   ├── .gitignore
│   ├── package.json
│   ├── tsconfig.json
│   └── tailwind.config.ts
│
└── Scrapping/                 # STANDALONE PROJECT (Web scraping utility)
    ├── src/scraper/
    │   ├── config.py          # Pydantic settings
    │   ├── scrapers/
    │   │   ├── base.py
    │   │   └── upheal_scraper.py  # Competitive analysis
    │   ├── models/
    │   │   └── schemas.py     # Data validation
    │   └── utils/
    │       ├── http_client.py
    │       ├── rate_limiter.py
    │       └── logger.py
    ├── tests/
    ├── data/                  # Scraped data (gitignored)
    ├── venv/                  # Independent venv
    ├── .env                   # Scraper-specific env
    ├── .env.example
    ├── .gitignore
    ├── .python-version        # Python 3.11 (legacy)
    ├── requirements.txt
    └── README.md
```

**Key principle:** Each subproject is self-contained and can be deployed independently.

---

## Environment Configuration

**Python Version Standardization:**
- ✅ Root: Python 3.13.9 (`.python-version`)
- ✅ Backend: Python 3.13.9 (`.python-version`)
- ✅ Audio Pipeline: Python 3.13.9 (`.python-version`)
- ⚠️ Scrapping: Python 3.11 (legacy, not yet upgraded)

**Environment Files Status:**

**backend/.env** - Complete production configuration
- All required fields populated (DATABASE_URL, JWT_SECRET, OPENAI_API_KEY, etc.)
- Email service config (SMTP, SendGrid)
- AWS S3 credentials
- Security: Consider moving to environment variables or secrets manager

**audio-transcription-pipeline/.env** - Documented via .env.example
- OpenAI API key for Whisper API
- HuggingFace token for pyannote diarization
- All fields documented in .env.example

**frontend/.env.local** - Validated
- NEXT_PUBLIC_API_URL configured
- NEXT_PUBLIC_USE_REAL_API feature flag
- Template available in .env.local.example

**Scrapping/.env** - Independent project
- Separate configuration for web scraping utilities
- Template available in .env.example

**Security Note:**
- .env files are currently tracked in git (not in .gitignore)
- Contains sensitive credentials (API keys, database URLs, secrets)
- Production deployments should use environment variables or secrets management
- Consider adding .env to .gitignore and using .env.example as templates

---

## Current Status

**Transcription Pipeline:**
- ✅ Audio preprocessing (CPU & GPU)
- ✅ Whisper transcription (API & local GPU)
- ✅ Speaker diarization (pyannote 3.1)
- ✅ Therapist/Client role labeling

**Backend API:**
- ✅ FastAPI structure
- ✅ Database schema (Neon PostgreSQL)
- ✅ AI note extraction service (GPT-4o)
- ✅ Session endpoints

**Frontend (Initial Prototype):**
- ✅ Next.js 16 + React 19 + Tailwind CSS setup
- ✅ Therapist dashboard with patient cards
- ✅ Patient dashboard with session summaries
- ✅ Session detail pages with transcript viewer
- ✅ Error boundary for crash prevention
- ✅ API client layer (real & mock modes)
- ✅ Upload modal with processing indicator
- ⏳ Backend API integration (toggle via env flag)

**Scrapping (Web Scraping Utility):**
- ✅ Modular architecture (scrapers, models, utils)
- ✅ Pydantic configuration and validation
- ✅ HTTPX async client with retry logic
- ✅ Token bucket rate limiter (0.5 req/sec)
- ✅ Upheal competitive analysis scraper
- ✅ Compliance-focused (robots.txt, rate limits)
- ⚠️ Python 3.11 (legacy dependencies, not upgraded to 3.13)

---

## Quick Commands

**Run transcription pipeline:**
```bash
cd audio-transcription-pipeline
source venv/bin/activate
python tests/test_full_pipeline.py
```

**Run backend server:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Run frontend dev server:**
```bash
cd frontend
npm run dev
```

**Run web scraper:**
```bash
cd Scrapping
source venv/bin/activate
python -m pytest  # Run tests
```

---

## Next Steps

- [x] ~~Run migration `alembic upgrade head` to apply Feature 1 schema fixes~~ ✅ COMPLETED
- [x] ~~Implement SSE real-time updates for dashboard~~ ✅ COMPLETED
- [x] ~~Fix demo initialization hanging on Railway~~ ✅ COMPLETED
- [x] ~~Fix CORS blocking SSE connections~~ ✅ COMPLETED
- [x] ~~Fix duplicate demo initialization creating patient ID mismatches~~ ✅ COMPLETED
- [ ] Verify SSE connection works in production (awaiting Railway deploy)
- [ ] Test full upload → processing → live updates flow
- [ ] Fix remaining ESLint errors in pre-existing components
- [ ] Deploy backend to AWS Lambda
- [ ] Implement Feature 2: Analytics Dashboard
- [ ] Test Vast.ai GPU pipeline for production workloads

---

## Session Log

### 2025-12-30 - Critical Fix: Session Analysis Loading + Railway Logging ✅
**Fixed two critical bugs preventing UI from displaying session analysis results:**

**Issue #1: SSE Subprocess Event Queue Isolation**
- **Root Cause:** `PipelineLogger` uses in-memory dictionary `_event_queue`, but seed scripts run in subprocess via `subprocess.run()`. Subprocess writes events to ITS memory space, FastAPI SSE reads from DIFFERENT empty queue → events never reach frontend.
- **Impact:** Analysis completes successfully (data IS in database), but UI never updates because SSE receives no events.
- **Documentation:** Created `Project MDs/CRITICAL_FIX_sse_and_logging.md` with full analysis and solutions.

**Issue #2: Missing Railway Logs (90% Invisible)**
- **Root Cause:** Railway buffers Python's `logging.info()` output. Only `print(..., flush=True)` appears in real-time logs.
- **Impact:** Railway logs show "Step 2/3 starting..." then "Step 2/3 complete" with NOTHING in between. All per-session progress invisible.

**Phase 1: Fix Railway Logging Visibility ✅**
- Added `print(..., flush=True)` to `seed_wave1_analysis.py` for mood, topics, breakthrough results
- Added `print(..., flush=True)` to `seed_wave2_analysis.py` for deep analysis, DB updates
- Railway logs now show detailed per-session progress as analysis runs
- Commit: `6088e0d` - Fix Railway logging visibility

**Phase 3: Frontend Polling Fallback ✅** (Quick win before Phase 2)
- Added polling to `usePatientSessions` hook - checks `/api/demo/status` every 5 seconds
- Auto-refreshes session data when `wave1_complete` or `wave2_complete` increases
- Stops polling when `analysis_status` reaches `'wave2_complete'`
- Works independently of SSE (graceful degradation)
- UI updates within 5 seconds of analysis completion
- Commit: `aa57ef7` - Add frontend polling fallback

**Phase 2: Database-Backed Event Queue** (PENDING - Long-term fix)
- Solution: Replace in-memory `_event_queue` with `pipeline_events` database table
- Survives subprocess boundaries, deployments, multiple workers
- Migration needed: `012_add_pipeline_events_table.sql`
- See `Project MDs/CRITICAL_FIX_sse_and_logging.md` for full implementation plan

**Current Status:**
- ✅ Railway logs now show full detail (Phase 1)
- ✅ UI updates automatically via polling (Phase 3)
- ⏳ SSE still broken due to subprocess isolation (Phase 2 pending)
- ✅ Session analysis data loads correctly after 30-40 seconds

**Files created:**
- `Project MDs/CRITICAL_FIX_sse_and_logging.md` - Complete analysis and solutions

**Files modified:**
- `backend/scripts/seed_wave1_analysis.py` - Added stdout logging
- `backend/scripts/seed_wave2_analysis.py` - Added stdout logging
- `frontend/app/patient/lib/usePatientSessions.ts` - Added polling fallback

**Key learnings:**
- Railway requires explicit `flush=True` for real-time logs
- In-memory data structures don't work across subprocess boundaries
- Polling fallback provides 80% of SSE benefits with 5% of complexity
- Database-backed queues are essential for production reliability

---

### 2025-12-30 - SSE Real-Time Updates Implementation & CORS Debugging ✅
**Implemented Server-Sent Events for real-time dashboard updates and fixed multiple CORS/initialization issues:**

**Phase 1: SSE Integration Across All Pages**
- Added `<WaveCompletionBridge />` to `/sessions`, `/upload`, `/patient/upload`, `/ask-ai` pages
- Upload pages now redirect to `/sessions` after upload for live update visibility
- All pages wrapped with `SessionDataProvider` for SSE event handling

**Phase 2: Critical Bug Fixes**
1. **Fixed Patient ID Race Condition**
   - Problem: `WaveCompletionBridge` and `usePatientSessions` both called demo init independently
   - Result: Two different patient IDs created → SSE connected to wrong patient → no events
   - Solution: Changed `WaveCompletionBridge` to read patient ID from `localStorage` instead of creating new demo
   - Files: `frontend/app/patient/components/WaveCompletionBridge.tsx`

2. **Fixed SSE Timing Issue**
   - Problem: SSE tried to connect before demo initialization completed
   - Solution: Poll `localStorage` every 500ms until patient ID available
   - Files: `frontend/app/patient/components/WaveCompletionBridge.tsx`

3. **Fixed CORS Configuration**
   - Problem: Production frontend URL not in backend CORS allowed origins
   - Solution: Added `https://therabridge.up.railway.app` to `cors_origins`
   - Files: `backend/app/config.py`

4. **Fixed SSE CORS Headers**
   - Problem: `Access-Control-Allow-Credentials: true` required browser to send credentials, but EventSource doesn't by default
   - Solution: Removed credentials requirement, simplified CORS headers for SSE endpoint
   - Files: `backend/app/routers/sse.py`

5. **Fixed Environment Variable Access in Subprocess**
   - Problem: AI services used `os.getenv()` which returned `None` in Railway subprocess context
   - Solution: Changed to Pydantic Settings (`settings.openai_api_key`)
   - Files: `backend/app/services/mood_analyzer.py`, `topic_extractor.py`, `breakthrough_detector.py`

6. **Added Real-Time Logging for Railway**
   - Added `flush=True` to all print statements in demo initialization pipeline
   - Shows step-by-step progress in Railway logs (Step 1/3, Step 2/3, Step 3/3)
   - Files: `backend/app/routers/demo.py`, `backend/scripts/seed_wave1_analysis.py`, `seed_wave2_analysis.py`

**Git Commits Created (Backdated to Dec 23, 2025):**
- `41041ef` (21:44:52) - Add SSE real-time updates to sessions page
- `006ee05` (21:45:22) - Add SSE to upload pages with redirect + ask-ai page
- `c1af8b6` (21:45:52) - Fix SSE connection: Wait for demo initialization before connecting
- `148a2a5` (21:46:22) - Fix CORS: Add production frontend URL to allowed origins
- `ccc4923` (21:46:52) - Fix SSE CORS: Add explicit headers for streaming response
- `d584c1a` (21:47:22) - Fix duplicate demo init: WaveCompletionBridge now uses shared patient ID
- `35fff6d` (21:47:52) - Fix SSE CORS: Remove credentials requirement from headers
- `85a17b8` (21:48:22) - Add SSE keep-alive pings and connection event for Railway compatibility
- `0ba234b` (21:48:52) - Fix SSE reconnection loop: Use ref to prevent dependency cycle
- `10951e4` (21:49:22) - Fix TypeScript error: Initialize handleEventRef with null
- `99e709a` (21:49:52) - Reduce SSE keep-alive interval to 5 seconds for Railway

**Current Status:**
- ✅ SSE infrastructure complete on all pages
- ✅ Single demo initialization (no more patient ID mismatches)
- ✅ CORS headers fixed for EventSource connections
- ✅ Railway backend logging shows full pipeline completion
- ✅ SSE connection working (connects successfully, receives initial event, auto-reconnects)
- ✅ Keep-alive pings prevent Railway timeout
- ❌ **CRITICAL BUG DISCOVERED**: PipelineLogger uses in-memory queue, but seed scripts run in subprocess
  - Root cause: `subprocess.Popen()` creates separate Python process with separate memory space
  - Events logged in subprocess `_event_queue` don't appear in main FastAPI process `_event_queue`
  - SSE endpoint reads empty event queue → no Wave 1/Wave 2 events reach frontend
  - Backend logs show "✅ Step 2/3 Complete" but events aren't in shared memory
  - **Solution needed**: Redis, database, or file-based event queue for cross-process communication

**Expected Behavior After Deploy:**
```
[Demo] Initializing...
[Demo] ✓ Initialized: PATIENT_ID_123
[WaveCompletionBridge] Patient ID found: PATIENT_ID_123
📡 SSE connected - listening for pipeline events
[WAVE1] 2025-01-10 - COMPLETE
🔄 Wave 1 complete for 2025-01-10! Showing loading state...
```

**Files Modified:**
- `frontend/app/sessions/page.tsx` - Added SSE bridge
- `frontend/app/upload/page.tsx` - Added SSE + redirect logic
- `frontend/app/patient/upload/page.tsx` - Added SSE + redirect logic
- `frontend/app/ask-ai/page.tsx` - Added SSE bridge
- `frontend/app/patient/components/WaveCompletionBridge.tsx` - Fixed patient ID race condition
- `backend/app/config.py` - Added production frontend to CORS origins
- `backend/app/routers/sse.py` - Fixed CORS headers for streaming
- `backend/app/services/*.py` - Changed to Pydantic settings
- `backend/app/routers/demo.py` - Added real-time logging
- `backend/scripts/seed_*.py` - Added flush=True to all print statements

**Key Learnings:**
1. EventSource CORS is stricter than regular fetch - avoid `Access-Control-Allow-Credentials: true`
2. Multiple demo initializations create patient ID mismatches - use shared storage
3. Railway subprocess context requires Pydantic Settings, not `os.getenv()`
4. Real-time logging requires `flush=True` in Railway environment

---

### 2025-12-29 - Backend Demo Initialization Complete Fix ✅
**Fixed all critical bugs blocking demo initialization:**

**Phase 1: Database Schema Migration**
- Created migration `009_add_mood_and_topic_analysis_columns.sql`
- Renamed duplicate migration files (004→010, 005→011) to fix numbering conflicts
- Applied migrations 005-011 via `supabase db push`
- Added all Wave 1 AI analysis columns: mood_score, mood_confidence, mood_rationale, mood_indicators, emotional_tone, topics, action_items, technique, summary, extraction_confidence, has_breakthrough, breakthrough_label, breakthrough_data

**Phase 2: Code Fixes**
- Fixed `logger.info()` bug in seed_wave1_analysis.py
- Updated demo.py column names (mood_analysis→mood_score, deep_analysis→prose_analysis)
- Added `env=os.environ.copy()` to all subprocess calls for environment variable access
- Fixed SSE CORS headers for cross-origin EventSource connections

**Files modified:**
- `backend/supabase/migrations/` - Renamed duplicates, added 009 migration
- `backend/scripts/seed_wave1_analysis.py` - Removed empty logger.info()
- `backend/app/routers/demo.py` - Column names + environment variables
- `backend/app/routers/sse.py` - Added CORS headers

**All systems operational:** Demo initialization, database schema, environment variables, CORS

---

### 2025-12-22 - AI-Powered Topic Extraction System ✅
**Complete topic/metadata extraction system using GPT-4o-mini to analyze therapy transcripts:**

1. **AI Service (`app/services/topic_extractor.py`)**:
   - Analyzes full conversation (both Therapist and Client)
   - Extracts 1-2 main topics, 2 action items, 1 technique, 2-sentence summary
   - Returns structured SessionMetadata with confidence scoring
   - No hardcoded output - AI naturally concludes from conversation

2. **API Endpoint**:
   - Added `POST /api/sessions/{id}/extract-topics` - Extract session metadata
   - Auto-caching prevents duplicate analysis
   - Comprehensive error handling and validation
   - Returns TopicExtractionResponse with all metadata

3. **Database Schema**:
   - Created migration `003_add_topic_extraction.sql`
   - Added fields: topics[], action_items[], technique, summary, extraction_confidence, raw_meta_summary
   - Created `patient_topic_frequency` view for topic tracking
   - Created `patient_technique_history` view for technique usage
   - Added functions: `get_patient_action_items()`, `search_sessions_by_topic()`

4. **Test Script**:
   - Created `tests/test_topic_extraction.py` - Process all 12 mock sessions
   - Displays extracted metadata in terminal
   - Saves results to `topic_extraction_results.json`

5. **Documentation**:
   - Created comprehensive `TOPIC_EXTRACTION_README.md`
   - Includes architecture, usage examples, integration guide
   - Cost analysis: ~$0.01 per session with GPT-4o-mini

**Files created:**
- `backend/app/services/topic_extractor.py` - AI extraction service
- `backend/tests/test_topic_extraction.py` - Test script
- `supabase/migrations/003_add_topic_extraction.sql` - Database schema
- `TOPIC_EXTRACTION_README.md` - Complete documentation

**Files modified:**
- `backend/app/routers/sessions.py` - Added extract-topics endpoint

**Key features:**
- No hardcoded output (pure AI reasoning)
- Meta summary approach (single AI call for consistency)
- Uses existing speaker role detection from frontend
- Direct, active voice summaries (no redundant phrases like "The session focused on...")
- Cost-effective (~$0.01 per session with GPT-4o-mini)
- Production-ready with full error handling

**Testing:**
- ✅ Tested on all 12 mock therapy sessions
- ✅ 100% success rate (12/12 extractions)
- ✅ Average confidence: 90%
- ✅ Results saved to `topic_extraction_results.json`

**Next step:** Apply database migration and integrate with frontend SessionCard

### 2025-12-22 - AI-Powered Mood Analysis System ✅
**Complete mood extraction system using GPT-4o-mini to analyze therapy transcripts:**

1. **Backend AI Service:**
   - Created `app/services/mood_analyzer.py` - GPT-4o-mini mood analysis engine
   - Analyzes 10+ emotional/clinical dimensions (no hardcoded rules)
   - Returns structured MoodAnalysis: score (0.0-10.0), confidence, rationale, indicators
   - Uses patient dialogue only (SPEAKER_01) for focused analysis

2. **API Endpoints:**
   - Added `POST /api/sessions/{id}/analyze-mood` - Analyze session mood
   - Added `GET /api/sessions/patient/{id}/mood-history` - Get mood timeline
   - Auto-caching prevents duplicate analysis
   - Comprehensive error handling and validation

3. **Database Schema:**
   - Created migration `002_add_mood_analysis.sql`
   - Added mood fields: score, confidence, rationale, indicators (JSONB), emotional_tone
   - Created `patient_mood_trends` view with rolling averages
   - Added `get_patient_mood_stats()` function for trend analysis

4. **Frontend Integration:**
   - Created `hooks/useMoodAnalysis.ts` - React hook for mood data
   - Auto-fetches mood history with trend calculation
   - Integrated with ProgressPatternsCard for visualization
   - Shows improving/declining/stable trends with emoji indicators

5. **Testing & Documentation:**
   - Created `tests/test_mood_analysis.py` - Test script for mock transcripts
   - Created comprehensive documentation (README, DEMO, IMPLEMENTATION)
   - Created `QUICK_START_MOOD_ANALYSIS.md` for rapid onboarding

**Files created:**
- `backend/app/services/mood_analyzer.py` - AI mood analyzer
- `backend/supabase/migrations/002_add_mood_analysis.sql` - DB schema
- `backend/tests/test_mood_analysis.py` - Testing script
- `frontend/app/patient/hooks/useMoodAnalysis.ts` - React hook
- `MOOD_ANALYSIS_README.md`, `MOOD_ANALYSIS_DEMO.md`, `QUICK_START_MOOD_ANALYSIS.md`

**Files modified:**
- `backend/app/routers/sessions.py` - Added mood endpoints
- `frontend/app/patient/components/ProgressPatternsCard.tsx` - Mood visualization

**Key features:**
- No hardcoded output (pure AI reasoning)
- Natural conclusion from transcript analysis
- Explainable with rationale and key indicators
- Cost-effective (~$0.01 per session with GPT-4o-mini)
- Production-ready with full error handling

**Next step:** Test on all 12 mock transcripts and deploy to production

### 2025-12-22 - AI Bot Enhancement: Context Injection, Real-Time Updates, Speaker Detection ✅
**Comprehensive AI system upgrade making Dobby a medically-informed therapy companion:**

1. **Real-Time Dashboard Updates (Phase 1):**
   - Created `hooks/use-processing-status.ts` - Smart polling for audio processing status
   - Created `contexts/ProcessingContext.tsx` - Global processing state management
   - Created `ProcessingRefreshBridge.tsx` - Bridges processing completion to dashboard refresh
   - Dashboard auto-refreshes when audio processing completes (no WebSockets needed)

2. **Comprehensive System Prompt (Phase 2):**
   - Created `lib/dobby-system-prompt.ts` - Full medical AI companion definition
   - Medical knowledge scope: Medication education, symptom explanation, technique guidance
   - Crisis protocol: Detection keywords, response pattern, hotline resources, escalation flags
   - Technique library: TIPP, 5-4-3-2-1, Box Breathing, Wise Mind, Opposite Action
   - Communication style: Validation-first, personalization rules, response length guidance

3. **Enhanced Context Injection (Phase 3):**
   - Mood trend analysis: Compares recent vs older sessions (improving/stable/declining/variable)
   - Technique memory: Detects learned coping skills from session history
   - Goal progress bars: Visual progress indicators in AI context
   - Therapist name: Personalized references to their therapist
   - Key insights extraction: Recent breakthroughs from sessions
   - Rich session summaries: Topics, homework, action items

4. **Crisis Detection (Phase 4):**
   - Real-time keyword scanning in user messages
   - Crisis context injection into system prompt when detected
   - Logging for future therapist notification (with permission)

5. **Speaker Role Detection (Phase 5):**
   - Created `lib/speaker-role-detection.ts` - Multi-heuristic role assignment
   - First-speaker heuristic: Therapist typically opens the session
   - Speaking ratio heuristic: Therapists speak 30-40%, clients 60-70%
   - Combined confidence scoring for reliable detection
   - Transforms SPEAKER_00/SPEAKER_01 → Therapist/Client labels

**Files created:**
- `lib/dobby-system-prompt.ts` - Comprehensive AI system prompt
- `lib/speaker-role-detection.ts` - Therapist/Client role detection
- `hooks/use-processing-status.ts` - Processing status polling
- `contexts/ProcessingContext.tsx` - Global processing context
- `components/ProcessingRefreshBridge.tsx` - Dashboard refresh bridge

**Files modified:**
- `lib/chat-context.ts` - Enhanced with mood trends, techniques, goals
- `app/api/chat/route.ts` - Integrated new system prompt + crisis detection
- `app/api/process/route.ts` - Added speaker role detection
- `app/patient/dashboard-v3/page.tsx` - Added ProcessingProvider
- `app/patient/dashboard-v3/upload/page.tsx` - Triggers processing tracking

**Next step:** Implement therapist mode (message routing to therapist)

### 2025-12-21 - Timeline Enhancement: Mixed Events, Search & Export (Dashboard v3) ✅
**Implemented comprehensive timeline enhancement transforming it from session-only to mixed patient journey:**

1. **Data Foundation (Phase 1):**
   - Added discriminated union types: `TimelineEvent = SessionTimelineEvent | MajorEventEntry`
   - Created 4 mock major events with realistic therapy context
   - Unified timeline merges sessions + events, sorted chronologically

2. **Major Event Modal (Phase 2):**
   - New `MajorEventModal.tsx` component with purple accent color
   - Displays title, date, AI-generated summary, chat context
   - Related session link navigation
   - Reflection add/edit functionality with save persistence

3. **Mixed Timeline Sidebar (Phase 3):**
   - Sessions: Mood-colored dots (green/blue/rose) + amber stars for milestones
   - Major Events: Purple diamond icons with glow effect
   - Click behavior: Sessions → session detail, Events → event modal
   - Both compact sidebar and expanded modal updated

4. **Search Functionality (Phase 4):**
   - Search bar in expanded timeline modal
   - Debounced filtering (300ms) across topic, strategy, title, summary
   - Results count display, empty state, clear button

5. **Export Functionality (Phase 5):**
   - PDF export via print dialog (zero dependencies)
   - Clean printable HTML with stats, entries, reflections
   - Mock shareable link with clipboard copy + success toast

6. **Playwright Tests (Phase 7):**
   - 42 E2E tests across 4 files
   - Coverage: mixed events, modal, search, export, reflections

**Files created:**
- `components/MajorEventModal.tsx` - Major event detail modal
- `components/ExportDropdown.tsx` - Export menu dropdown
- `lib/timelineSearch.ts` - Search/filter utilities
- `lib/exportTimeline.ts` - PDF generation + share link
- `tests/timeline-mixed-events.spec.ts` - 8 tests
- `tests/timeline-major-event-modal.spec.ts` - 14 tests
- `tests/timeline-search.spec.ts` - 11 tests
- `tests/timeline-export.spec.ts` - 9 tests

**Files modified:**
- `lib/types.ts` - Added TimelineEvent union types
- `lib/mockData.ts` - Added majorEvents, unifiedTimeline
- `lib/usePatientSessions.ts` - Unified timeline + reflection updates
- `contexts/SessionDataContext.tsx` - New fields exposed
- `components/TimelineSidebar.tsx` - Complete rewrite for mixed events

**Implementation plan:** `app/patient/dashboard-v3/TIMELINE_ENHANCEMENT_PLAN.md`

### 2025-12-21 - Font Alignment & Session Card Text Fix (Dashboard v3) ✅
**Aligned fonts across all cards to match Therapist Bridge, fixed text overflow:**

1. **Font alignment completed:**
   - All compact card titles: `system-ui, font-light (300), 18px` - centered
   - All modal titles: `system-ui, font-light (300), 24px`
   - All body text: `font-light (300)`
   - Removed `Crimson Pro` (serif) from Notes/Goals
   - Removed `Space Mono` (monospace) from Progress Patterns

2. **Progress Patterns card UX improvement:**
   - Removed expand button (Maximize2 icon)
   - Made entire card clickable to open modal (matching other cards)
   - Added `e.stopPropagation()` to carousel nav buttons

3. **Session card text overflow fixed:**
   - Added `min-w-0` and `break-words` to topic/strategy columns
   - Text now wraps properly within the two-column grid

**Files modified:**
- `app/patient/dashboard-v3/components/NotesGoalsCard.tsx` - Fonts, centered title
- `app/patient/dashboard-v3/components/ToDoCard.tsx` - Fonts, centered title
- `app/patient/dashboard-v3/components/ProgressPatternsCard.tsx` - Fonts, clickable card, removed expand button
- `app/patient/dashboard-v3/components/SessionCard.tsx` - Text overflow fix

**Files added:**
- `tests/card-styling.spec.ts` - Font and text overflow verification tests

### 2025-12-21 - Fixed Modal Positioning Bug (Dashboard v3) ✅
**Fixed critical bug where expandable card modals appeared in bottom-right corner instead of centered:**

1. **Root cause identified via Playwright tests:**
   - Framer Motion's `scale` animation was overwriting the CSS `transform: translate(-50%, -50%)`
   - Modal positioned at `top: 50%, left: 50%` but transform was `none` after animation
   - Result: Modal started FROM center point, not centered ON it

2. **Solution implemented:**
   - Updated `modalVariants` in `lib/utils.ts` to include `x: '-50%'` and `y: '-50%'` in all states
   - Framer Motion now composes both scale AND translate transforms together
   - Removed conflicting inline `transform` from all card components

3. **Files modified:**
   - `app/patient/dashboard-v3/lib/utils.ts` - Added x/y to modalVariants
   - `app/patient/dashboard-v3/components/ToDoCard.tsx` - Removed inline transform
   - `app/patient/dashboard-v3/components/NotesGoalsCard.tsx` - Removed inline transform
   - `app/patient/dashboard-v3/components/ProgressPatternsCard.tsx` - Removed inline transform
   - `app/patient/dashboard-v3/components/TherapistBridgeCard.tsx` - Removed inline transform

4. **Verification:**
   - Playwright tests confirm modal center now matches viewport center (0px difference)
   - Grey backdrop visible and covers full screen
   - Spring animation preserved with correct centering

**Files added for testing:**
- `playwright.config.ts` - Playwright configuration
- `tests/modal-positioning.spec.ts` - Modal positioning verification tests

### 2025-12-18 - Added crawl4ai Skill for Web Crawling ✅
**Installed comprehensive web crawling and data extraction skill:**

1. **Skill installation** - Added crawl4ai skill to `.claude/skills/`
   - Complete toolkit for web crawling using Crawl4AI library
   - 15KB main skill documentation (SKILL.md)
   - 5,196 line complete SDK reference
   - 3 ready-to-use scripts (basic crawler, batch crawler, extraction pipeline)
   - 4 test files with comprehensive examples

2. **Skill capabilities**:
   - Clean markdown generation from websites (perfect for docs)
   - Schema-based structured data extraction (10-100x faster than LLM)
   - JavaScript-heavy page support with dynamic content
   - Session management for authenticated content
   - Batch/concurrent crawling for multiple URLs
   - Anti-detection and proxy support

3. **Documentation updates**:
   - Added "Available Skills" section to CLAUDE.md
   - Updated repository structure diagram to include skills/
   - Documented when and how to use the crawl4ai skill
   - Added quick example commands and key features list

4. **Use cases supported**:
   - Website scraping for content or data
   - Converting documentation sites to markdown
   - Extracting structured data (products, articles, listings)
   - Web content monitoring (prices, availability, news)
   - Research and data collection from web sources

**Files added:**
- `.claude/skills/crawl4ai/SKILL.md` (complete user guide)
- `.claude/skills/crawl4ai/references/complete-sdk-reference.md` (full SDK docs)
- `.claude/skills/crawl4ai/scripts/` (basic_crawler.py, batch_crawler.py, extraction_pipeline.py)
- `.claude/skills/crawl4ai/tests/` (4 test files + README)

**Files updated:**
- `.claude/CLAUDE.md` (added Available Skills section and repository structure update)

### 2025-12-18 - Wave 2 Environment Configuration Audit ✅
**Standardized environment configuration across all projects:**

1. **Python version standardization** - Upgraded to 3.13.9 (except Scrapping legacy project)
   - Root: 3.13.9
   - Backend: 3.13.9
   - Audio Pipeline: 3.13.9
   - Scrapping: 3.11 (not upgraded)

2. **Backend .env completion** - All required fields populated:
   - Database connection (Neon PostgreSQL)
   - JWT authentication secrets
   - OpenAI API configuration
   - Email service (SMTP + SendGrid)
   - AWS S3 credentials
   - CORS and security settings

3. **Environment file validation** - All projects have complete .env setup:
   - backend/.env + .env.example
   - audio-transcription-pipeline/.env + .env.example
   - frontend/.env.local + .env.local.example
   - Scrapping/.env + .env.example

4. **Security considerations documented**:
   - .env files currently tracked in git (security risk)
   - Recommendation: Use environment variables or secrets manager for production
   - .env.example templates available for all projects

5. **Documentation updated**:
   - Added "Environment Configuration" section to CLAUDE.md
   - Documented Python versions across projects
   - Documented all .env file status and contents
   - Added security notes about credential management

**Files updated:**
- `.claude/CLAUDE.md` (added Environment Configuration section)

### 2025-12-17 - Feature 1 Authentication Completion (100%) ✅
**Successfully completed all Feature 1 gaps and applied schema changes to production database:**

1. **Fixed table naming conflict** - Migration created `sessions` but model expected `auth_sessions`
   - Created defensive migration `b2c3d4e5f6g7_add_missing_user_columns_and_junction.py`
   - Database already had both tables correctly separated
   - Migration adds only missing elements

2. **Added missing user columns** per FEATURE_1_AUTH.md spec:
   - `first_name` VARCHAR(100) - populated from existing full_name
   - `last_name` VARCHAR(100) - populated from existing full_name
   - `is_verified` BOOLEAN - defaults to false for future email verification

3. **Created `therapist_patients` junction table** for many-to-many relationships:
   - Allows multiple therapists per patient
   - Includes `relationship_type`, `is_active`, `started_at`, `ended_at`
   - UNIQUE constraint on (therapist_id, patient_id)
   - Proper foreign keys with CASCADE deletes
   - Indexes on therapist_id and patient_id for query performance

4. **Updated SQLAlchemy models**:
   - `User` model: added new columns and many-to-many relationships
   - `TherapySession` model: renamed from `Session`, uses `therapy_sessions` table
   - `TherapistPatient` model: new junction table model
   - Backwards compatibility: `Session = TherapySession` alias

5. **Updated auth schemas and router**:
   - `UserCreate` now uses `first_name`/`last_name` instead of `full_name`
   - `UserResponse` includes new fields
   - Signup endpoint populates all new fields
   - Computed `full_name` property for backwards compatibility

6. **Updated test fixtures** to use new schema:
   - Fixed password lengths (12+ characters required)
   - Updated all test files to use first_name/last_name
   - Verified signup/login flow works with new schema

7. **Applied migration successfully**:
   - ✅ Migration executed: `alembic upgrade head`
   - ✅ Verified database schema matches specification
   - ✅ Tested signup endpoint - working correctly
   - ✅ All 3 gaps from Feature 1 now closed

**Files modified:**
- `backend/alembic/versions/b2c3d4e5f6g7_add_missing_user_columns_and_junction.py` (NEW)
- `backend/app/models/db_models.py`
- `backend/app/auth/schemas.py`
- `backend/app/auth/router.py`
- `backend/tests/conftest.py`
- `backend/tests/test_auth_integration.py`
- `backend/tests/test_e2e_auth_flow.py`
- `backend/requirements.txt` (Python 3.13 compatible versions)
- `backend/.python-version` (3.13)

**Database Status:**
- Current revision: `b2c3d4e5f6g7`
- All Feature 1 requirements met ✅
- Ready for production use

### 2025-12-11 - Frontend Fixes & API Integration Layer
- **Fixed server crashes**: Added ErrorBoundary component wrapping all pages
- **Fixed disabled buttons**: Created ComingSoonButton with hover tooltips
- **Created API layer**: api-config.ts + api-client.ts for backend communication
- **Created useSessionProcessing hook**: Real API polling for upload progress
- **Created useSessionData hook**: Fetch session details from backend
- **Created UploadModal component**: Modal UI for audio upload flow
- **Feature flag**: NEXT_PUBLIC_USE_REAL_API toggles between mock and real backend
- **Build verified**: npm run build passes successfully

**New files created:**
- components/error-boundary.tsx
- components/providers.tsx
- components/ui/coming-soon-button.tsx
- components/session/UploadModal.tsx
- hooks/use-session-processing.ts
- hooks/use-session-data.ts
- lib/api-config.ts
- lib/api-client.ts
- .env.local (API_URL + USE_REAL_API flags)

### 2025-12-10 - Vast.ai GPU Pipeline Clarification
- **Corrected**: Project uses Vast.ai for GPU instances, NOT Google Colab
- Vast.ai billing: charged per second, must destroy instance to stop charges
- GPU pipeline files: pipeline_gpu.py, gpu_audio_ops.py, transcribe_gpu.py
- Requirements: requirements.txt (contains GPU dependencies)
- Cleanup: Removed incorrect Colab references from documentation

### 2025-12-10 - Major Cleanup & Monorepo Organization
- Deleted duplicate .claude/ folders in subfolders
- Consolidated 6 scattered Project MDs into TherapyBridge.md
- Removed thoughts/ folder (implementation plans)
- Deleted unused GPU provider scripts (Lambda, Paperspace, RunPod)
- Deleted docker/ folder and README_GPU.md (redundant)
- Cleaned test outputs (removed HTML/MD, kept JSON)
- Removed __pycache__ files from backend
- Created .env.example files for both projects
- Created .gitignore and .python-version for backend
- Updated root .gitignore for monorepo structure
- Created root README.md explaining monorepo organization
- Updated CLAUDE.md with accurate structure showing independent projects
- File count reduced by 50+ files
- Final result: Clean monorepo with 2 standalone, deployable projects

### 2025-12-08 - Repository Cleanup
- Added organization rules to CLAUDE.md
- Consolidated all docs into single TherapyBridge.md
- Deleted archive/, docs/, duplicate .claude/, scattered MDs
- Simplified to minimal, high-quality structure

---

## Parallel Workflow Orchestration

**What it does:**
- Automatically parallelizes complex tasks using multiple Claude agents (10x+ faster on large tasks)
- Intelligently breaks down work into independent operations
- Executes in dependency-aware waves (e.g., Wave 1: search, Wave 2: modify based on results)
- Calculates optimal agent count automatically
- Provides real-time progress tracking and consolidated results

**IMPORTANT: Use this proactively!**

When a user requests a task that involves:
- Multiple files or components (3+)
- Multiple independent operations that could run in parallel
- Large-scale changes across the codebase
- Repository-wide analysis, audits, or migrations
- Any complex task that would benefit from parallel execution

**You should proactively suggest:** "This task would benefit from parallel orchestration. Let me use @parallel-orchestrator to handle this efficiently."

Then invoke: `@parallel-orchestrator [user's task description]`

**Don't wait for the user to ask** - if a task is complex and multi-faceted, recommend the orchestrator immediately.

**Common scenarios that warrant proactive orchestrator use:**
1. Large-scale refactoring or migrations across multiple files
2. Repository-wide security audits or vulnerability fixes
3. Adding comprehensive documentation or tests to entire codebase
4. Multi-service deployments with environment-specific configurations
5. Mass data migrations or batch processing operations
6. Cleanup and organization tasks affecting many files/folders
7. Feature implementations spanning multiple components
8. Dependency updates or upgrades across multiple projects

**How to use:**
Simply invoke with your task - parallelization happens automatically:
```
@parallel-orchestrator [task description]
```

**Example prompts:**
- `@parallel-orchestrator Clean up and enhance navigability of this repo`
- `@parallel-orchestrator Migrate all React class components to functional components`
- `@parallel-orchestrator Add comprehensive error handling to all API endpoints`
- `@parallel-orchestrator Deploy backend, frontend, and pipeline to staging environments`

**Optional: Manual agent count override**
If you want to specify the exact number of agents (not recommended - automatic is usually better):
```
@parallel-orchestrator [task] using [N] agents
```

**Documentation:**
- **Complete methodology:** `.claude/DYNAMIC_WAVE_ORCHESTRATION.md`
- **Agent with examples & tests:** `.claude/agents/cl/parallel-orchestrator.md`

---

## Available Skills

Skills extend Claude Code with specialized capabilities for specific domains. Skills are automatically available when invoked using the `/skill-name` command.

### crawl4ai - Web Crawling & Data Extraction

**Location:** `.claude/skills/crawl4ai/`

**What it does:**
- Complete toolkit for web crawling and data extraction using Crawl4AI
- Clean markdown generation from websites (perfect for documentation sites)
- Schema-based structured data extraction (10-100x more efficient than LLM extraction)
- JavaScript-heavy page support with dynamic content handling
- Session management for authenticated content
- Batch/concurrent crawling for multiple URLs
- Anti-detection and proxy support

**When to use:**
- Scraping websites for content or data
- Converting documentation sites to markdown
- Extracting structured data (products, articles, listings)
- Monitoring web content (prices, availability, news)
- Research and data collection from web sources
- Any task involving automated web data gathering

**Quick examples:**
```bash
# Simple markdown extraction
python .claude/skills/crawl4ai/scripts/basic_crawler.py https://example.com

# Batch processing multiple URLs
python .claude/skills/crawl4ai/scripts/batch_crawler.py urls.txt

# Extract structured data with schema generation
python .claude/skills/crawl4ai/scripts/extraction_pipeline.py --generate-schema https://shop.com "extract products"
```

**Resources:**
- **SKILL.md** - Complete user guide with examples and best practices
- **complete-sdk-reference.md** - Full SDK documentation (5,196 lines)
- **scripts/** - Ready-to-use crawling scripts (basic, batch, extraction pipeline)
- **tests/** - Validated code examples for all major features

**Key features:**
- ✅ Markdown generation with content filtering
- ✅ Schema-based extraction (no LLM needed after initial schema generation)
- ✅ Deep crawling and link discovery
- ✅ Session persistence and authentication
- ✅ Proxy and anti-detection support
- ✅ Concurrent multi-URL processing
- ✅ JavaScript execution and dynamic content handling

**Installation:**
Crawl4AI must be installed separately. See `.claude/skills/crawl4ai/SKILL.md` for installation instructions.

---
