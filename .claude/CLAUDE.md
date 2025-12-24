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

---

## 🚨 CRITICAL RULE - GIT COMMIT DATING

### ⚠️ ABSOLUTE RULE: NO COMMITS AFTER DEC 23, 2025 11:45 PM

**All commits must be backdated to December 23, 2025.**

**CRITICAL:** Before creating ANY commit, you MUST:
1. Check the most recent commit timestamp: `git log --format="%ci" -n 1`
2. Add exactly 30 seconds to that timestamp
3. Use that new timestamp for your commit

### How Claude Code Will Handle Commits

**CRITICAL WORKFLOW - Claude MUST follow these steps EXACTLY:**

1. **FIRST:** Check the most recent commit timestamp:
   ```bash
   git log --format="%ci" -n 1
   ```

2. **SECOND:** Calculate new timestamp (add 30 seconds to the result from step 1)
   - Example: If last commit was `2025-12-23 21:54:52 -0600`
   - Next commit should be `2025-12-23 21:55:22 -0600`

3. **THIRD:** Create commit with calculated timestamp:
   ```bash
   git add -A && \
   GIT_COMMITTER_DATE="2025-12-23 HH:MM:SS -0600" \
   git commit -m "message" --date="2025-12-23 HH:MM:SS -0600"
   ```

**NEVER hardcode timestamps. ALWAYS check the previous commit first.**

**Git User Configuration:**
- Email: `rohin.agrawal@gmail.com`
- Username: `newdldewdl`

---

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

## Current Focus: Status Endpoint Fixed - Testing Hard Refresh Flow ✅

**Latest Fix (Commit 9fe5344):**
- Fixed `/api/demo/status` endpoint returning `total: 0` despite sessions existing
- Root cause: Endpoint was using USER ID instead of PATIENT ID to query sessions
- Solution: Added patient lookup `db.table("patients").select("id").eq("user_id", user_id)` before querying sessions

**Previous Fixes (Commits b477185-9d403a5):**
- ✅ Fixed SSE race condition on hard refresh (patient ID reactivity)
- ✅ Removed hard refresh detection from home and sessions pages
- ✅ Centralized demo initialization in WaveCompletionBridge with continuous polling
- ✅ Fixed status endpoint returning `wave2_complete` when `session_count == 0`

**Current Behavior:**
- Hard refresh clears localStorage → triggers demo initialization
- WaveCompletionBridge polls for patient ID every 500ms
- SSE connects only after patient ID is available
- Status endpoint now correctly queries sessions using patient_id

**Next Steps:**
1. Wait for Railway deployment to complete (commit 9fe5344)
2. Test full hard refresh flow end-to-end
3. Verify status endpoint returns correct session counts
4. Verify Wave 1 analysis completes and UI updates via polling

**Full Documentation:** See `Project MDs/TherapyBridge.md`
**Detailed Session History:** See `.claude/SESSION_LOG.md`

---

## Repository Structure

**Monorepo with 4 independent projects:**

```
peerbridge proj/
├── .claude/                   # Claude Code config (root only)
│   ├── CLAUDE.md              # This file
│   ├── SESSION_LOG.md         # Detailed session history
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
│   ├── scripts/
│   ├── venv/                  # Independent venv
│   ├── .env                   # Pipeline-specific env
│   ├── .env.example
│   ├── .gitignore
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
│   ├── .gitignore
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
    │   ├── config.py
    │   ├── scrapers/
    │   ├── models/
    │   └── utils/
    ├── tests/
    ├── data/
    ├── venv/
    ├── .env
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
- ✅ Wave 1 analysis (topics, mood, summary, breakthrough detection)
- ✅ Wave 2 analysis (deep_analysis JSONB + prose_analysis TEXT)
- ✅ Session endpoints with analysis data
- ✅ Non-blocking demo initialization (~30s load time)

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

## Recent Sessions (Last 2)

**Full session history:** See `.claude/SESSION_LOG.md`

### 2025-12-31 - Refresh Behavior & SSE Connection Fixes (Phases 1-3 Complete) ✅
**Implemented comprehensive fix for browser refresh behavior and SSE connection timing:**

**Phase 1: Hard Refresh Detection ✅**
- Created `lib/refresh-detection.ts` utility for detecting Cmd+Shift+R vs Cmd+R
- Added global keydown listener in `layout.tsx` to mark hard refresh in sessionStorage
- Flag auto-clears after read (one-time use)

**Phase 2: Demo Initialization & localStorage Persistence ✅**
- Added initialization status tracking (`pending`/`complete`/`none`) to `demo-token-storage.ts`
- Enhanced `page.tsx` with hard refresh detection and localStorage clearing
- Added pending state detection to prevent duplicate initializations
- Increased API timeout from 30s → 120s for demo initialization (Wave 1 + Wave 2 takes ~90s)

**Phase 3: SSE Connection Timing & Reconnection ✅**
- Updated `WaveCompletionBridge.tsx` to wait for patient ID before connecting SSE
- Added timeout (20s) and init status checking with detailed error logging
- Enhanced `use-pipeline-events.ts` with connection error tracking and readyState monitoring
- Fixed critical polling restart bug (removed patientId from dependency array)
- Auto-reconnection handled by browser EventSource on simple refresh

**Current Behavior:**
- **Hard Refresh (Cmd+Shift+R)**: Clears localStorage → New patient ID → New demo initialization
- **Simple Refresh (Cmd+R)**: Preserves localStorage → Same patient ID → SSE reconnects automatically
- **SSE Connection**: Waits for patient ID → Connects within 1-2 seconds → No timeout errors
- **Demo Init**: Completes successfully in ~30-40 seconds with 120s timeout buffer

---

### 2025-12-30 - Critical Fix: Session Analysis Loading + Railway Logging ✅
**Fixed two critical bugs preventing UI from displaying session analysis results:**

**Issue #1: SSE Subprocess Event Queue Isolation**
- **Root Cause:** `PipelineLogger` uses in-memory dictionary `_event_queue`, but seed scripts run in subprocess via `subprocess.run()`. Subprocess writes events to ITS memory space, FastAPI SSE reads from DIFFERENT empty queue → events never reach frontend.
- **Impact:** Analysis completes successfully (data IS in database), but UI never updates because SSE receives no events.
- **Documentation:** Created `Project MDs/CRITICAL_FIX_sse_and_logging.md` with full analysis and solutions.

**Issue #2: Missing Railway Logs (90% Invisible)**
- **Root Cause:** Railway buffers Python's `logging.info()` output. Only `print(..., flush=True)` appears in real-time logs.
- **Impact:** Railway logs show "Step 2/3 starting..." then "Step 2/3 complete" with NOTHING in between. All per-session progress invisible.

**Fixes Implemented:**
- ✅ Phase 1: Added `print(..., flush=True)` to all seed scripts for Railway logging visibility
- ✅ Phase 3: Added polling to `usePatientSessions` hook - checks `/api/demo/status` every 5 seconds
- ⏳ Phase 2: Database-backed event queue (PENDING - long-term fix)

**Current Status:**
- ✅ Railway logs now show full detail (Phase 1)
- ✅ UI updates automatically via polling (Phase 3)
- ⏳ SSE still broken due to subprocess isolation (Phase 2 pending)
- ✅ Session analysis data loads correctly after 30-40 seconds

**Key learnings:**
- Railway requires explicit `flush=True` for real-time logs
- In-memory data structures don't work across subprocess boundaries
- Polling fallback provides 80% of SSE benefits with 5% of complexity
- Database-backed queues are essential for production reliability

---

## Parallel Workflow Orchestration

**Use proactively for complex tasks involving:**
- Multiple files or components (3+)
- Large-scale changes across the codebase
- Repository-wide analysis, audits, or migrations
- Any complex task that would benefit from parallel execution

**How to use:**
```
@parallel-orchestrator [task description]
```

**Documentation:**
- **Complete methodology:** `.claude/DYNAMIC_WAVE_ORCHESTRATION.md`
- **Agent with examples:** `.claude/agents/cl/parallel-orchestrator.md`

---

## Available Skills

### crawl4ai - Web Crawling & Data Extraction

**What it does:**
- Clean markdown generation from websites
- Schema-based structured data extraction (10-100x faster than LLM)
- JavaScript-heavy page support, session management, batch crawling

**When to use:**
- Scraping websites for content or data
- Converting documentation sites to markdown
- Extracting structured data (products, articles, listings)
- Web content monitoring and research

**Documentation:**
- **Skill guide:** `.claude/skills/crawl4ai/SKILL.md`
- **SDK reference:** `.claude/skills/crawl4ai/references/complete-sdk-reference.md`
- **Scripts:** `.claude/skills/crawl4ai/scripts/`

---
