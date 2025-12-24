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

## Pull Request Tracking

**Hybrid System:** PR information tracked in TWO places:

1. **SESSION_LOG.md** (Full narrative)
   - Detailed session notes for every status change
   - Full context and decision history
   - New entry per PR status update (Planned → In Progress → Testing → Review → Merged → Deployed)
   - Links to implementation sessions, testing sessions, etc.
   - Format: `## YYYY-MM-DD - [Title] (PR #X)`

2. **TheraBridge.md "Development Status" section** (Quick reference)
   - Current state of all PRs (Active / Completed / Planned)
   - Minimal info: PR number, title, status, plan link, related sessions
   - Single source of truth for "what's happening NOW"
   - Update this section as PR status changes

**PR Numbering:** Sequential (PR #1, PR #2, PR #3...)

**Status Lifecycle:** Planned → In Progress → Testing → Review → Merged → Deployed

**Session Entry Required:** Create new SESSION_LOG entry for each status change (even solo implementation work without Claude)

**Documentation Files:**
- Implementation plans live in `thoughts/shared/plans/YYYY-MM-DD-description.md`
- Plans are detailed (file-by-file changes, line numbers, code snippets)
- Plans are preserved for reference (not deleted after execution)

---

# TheraBridge - Project State

## Current Focus: Feature Development Pipeline

**PR #1 Status:** ✅ COMPLETE - SessionDetail UI Improvements + Wave 1 Action Summarization (2026-01-09)
**PR #2 Status:** ✅ COMPLETE - Prose Analysis UI Toggle (2026-01-11) - Awaiting Railway verification
**PR #3 Status:** 🚧 IN PROGRESS - Your Journey Dynamic Roadmap (2026-01-11)

**PR #3 Progress (Phases 0-2 COMPLETE):**
- ✅ Phase 0: LoadingOverlay debug logging added
- ✅ Phase 1: Backend infrastructure (database, services, model config)
- ✅ Phase 2: All 3 compaction strategies implemented
- ⏳ Phase 3: Frontend integration (NEXT)
- ⏳ Phase 4: Start/Stop/Resume button
- ⏳ Phase 5: Orchestration & testing

**Next:** Execute Phases 3-5 in separate Claude window

**Production Fix Results - BLOCKER #2 FINAL FIX (2026-01-09):**
- ✅ **BLOCKER #1 FIXED:** Removed all `breakthrough_history` table references - API now returns 200 OK
- ✅ **BLOCKER #2 FINALLY FIXED:** GPT-5-nano working with minimal parameters - summaries generating (39-45 chars)
- ✅ **BLOCKER #3 RESOLVED:** Frontend accessible - API working correctly
- 📋 **Initial Test Report:** `thoughts/shared/PRODUCTION_TEST_RESULTS_2026-01-08.md`
- 🔧 **Fix Summary:** `thoughts/shared/PRODUCTION_FIX_SUMMARY_2026-01-08.md`
- 📝 **Final Testing Prompt:** `thoughts/shared/PR1_FINAL_TESTING_PROMPT_2026-01-08.md`

**Critical Discovery - GPT-5-nano API Constraints (2026-01-09):**
- **Root Cause:** GPT-5-nano returns empty strings when ANY optional parameters are used
- **Issue:** `temperature=X` OR `max_completion_tokens=X` → empty response
- **Solution:** Call API with ONLY `model` + `messages` (no optional params)
- **Evidence:** mood_analyzer (also gpt-5-nano) uses same minimal parameter approach
- **Commits:** 6 iterations to discover issue (a9cc104 → 7ff3cab → e73fbbc → 12a61f7 → ab52d2a)
- **Final Fix:** Commit `ab52d2a` - Switch to gpt-5-nano with NO parameters ✅

**Final Testing Complete (2026-01-09):**
- ✅ All 6 Phase 1C UI features verified in production browser
- ✅ Action summaries displaying correctly in SessionCard (39-45 chars)
- ✅ Mood score + emoji working in SessionDetail (teal → purple theme switching)
- ✅ Technique definitions showing correctly (2-3 sentences from library)
- ✅ X button functional, "Back to Dashboard" removed
- ✅ Theme toggle working with custom icons (orange sun/blue moon with glows)
- ✅ No regressions found in existing features
- 🐛 **2 visual bugs fixed (commit f97286e):** Emoji color theme switching + theme toggle styling
- 📋 **Final Test Report:** `thoughts/shared/PR1_FINAL_TEST_REPORT_2026-01-09.md`

**Phase 1C Implementation Complete (2026-01-08):**
- ✅ Database migration applied - `action_items_summary` TEXT column added via Supabase MCP
- ✅ Backend: ActionItemsSummarizer service (gpt-5-nano, 45-char max)
- ✅ Backend: Sequential action summarization integrated into Wave 1 orchestration
- ✅ Backend: Sessions API enriched with technique definitions from technique_library.json
- ✅ Frontend: Mood mapper utility (numeric 0-10 → categorical sad/neutral/happy)
- ✅ Frontend: Session interface extended with 8 new fields
- ✅ Frontend: SessionCard uses condensed action summary (45 chars)
- ✅ Frontend: SessionDetail displays mood score + emoji, technique definitions, X button, theme toggle
- ✅ Build verified successful, TypeScript compiles without errors
- ✅ Git commits pushed (be21ae3 implementation, 6d22548 documentation)
- ✅ CRITICAL BUG FIX (04fd884): Added missing Wave 1 fields to refresh() transformation

**Implementation Details (2026-01-08):**
- Wave 0 research: Custom emoji logic, data flow verification, Railway logs
- Implementation plan: `thoughts/shared/plans/2026-01-07-sessiondetail-ui-improvements-wave1-action-summarization.md`
- Architecture: Sequential action summarization after topic extraction (preserves quality)
- Cost impact: +0.7% increase (+$0.0003/session) - negligible
- Files modified: 10 total (3 new, 7 modified)

**Critical Bug Fix (2026-01-08):**
- **Root Cause:** `refresh()` function in `usePatientSessions.ts` was missing 3 critical field mappings
- **Impact:** After polling refresh, UI would lose mood_score, action_items_summary, technique_definition
- **Symptoms:** SessionDetail missing mood score/emoji and technique definition; SessionCard missing action summary
- **Fix:** Added missing field mappings to `refresh()` transformation (lines 450-461)
- **File:** `frontend/app/patient/lib/usePatientSessions.ts`

**Previous Phases:**
- ✅ Phase 1A Complete (2026-01-07): Font standardization for SessionDetail + DeepAnalysisSection
- ⏳ Phase 1B Deferred: Header fonts + Timeline deprecation (non-critical)

**Commits (PR #1):**
- `f97286e` - fix(pr1-phase1c): Fix theme toggle styling and emoji color switching ✅ FINAL UI FIX
- `ab52d2a` - fix(pr1-phase1c): Switch action_summary to gpt-5-nano with no parameters ✅ BACKEND FIX
- `12a61f7` - fix(pr1-phase1c): Switch action_summary to gpt-4o-mini (GPT-5-nano broken)
- `e73fbbc` - fix(pr1-phase1c): Increase max_completion_tokens to allow GPT-5-nano output
- `7ff3cab` - fix(pr1-phase1c): Remove temperature parameter for GPT-5-nano compatibility
- `a9cc104` - fix(pr1-phase1c): Update OpenAI API parameter for GPT-5 compatibility
- `8e3bd82` - fix(pr1-phase1c): Add ActionItemsSummarizer to Wave 1 seed script (Blocker #2)
- `3e9ea89` - fix(pr1-phase1c): Remove breakthrough_history table references (Blocker #1)
- `8d50165` - docs: Production testing results and fix handoff documentation
- `04fd884` - fix(pr1-phase1c): Add missing Wave 1 fields to refresh() transformation
- `eb485d8` - docs: Update CLAUDE.md with Phase 1C completion status
- `6d22548` - docs: Update SESSION_LOG and TheraBridge.md with Phase 1C completion
- `be21ae3` - Feature: PR #1 Phase 1C - SessionDetail UI improvements + Wave 1 action summarization
- `d3f7390` - Feature: PR #1 Phase 1A - Font standardization for SessionDetail and DeepAnalysisSection
- `87098f6` - Fix: Complete Tailwind font class removal in SessionDetail.tsx
- `c2eea93` - Fix: Add missing fontFamily to badges in DeepAnalysisSection
- `e7f8e6a` - Fix: Metadata values use Inter font for consistency

**Previous Focus (COMPLETE ✅):** Real-Time Granular Session Updates

**Implementation Complete (2026-01-03):**
- ✅ Backend `/api/demo/status` enhanced with full analysis data per session
- ✅ Frontend granular polling with per-session loading overlays
- ✅ Adaptive polling: 1s during Wave 1 → 3s during Wave 2 → stop
- ✅ Database-backed SSE event queue (fixes subprocess isolation bug)
- ✅ SSE integration with feature flags (disabled by default)
- ✅ SessionDetail scroll preservation with smooth animation
- ✅ Test endpoint removed, documentation updated
- ✅ Fixed card scaling (capped at 1.0 to prevent blown-up cards)
- ✅ Fixed stuck loading overlays (debouncing bug)
- ✅ Fixed SessionDetail stale data (updates live while open)
- ✅ Added "Stop Processing" button to terminate pipeline

**Production Behavior:**
1. **Demo Init (0-3s)**: Demo initialized, patient ID stored, SSE connects
2. **Transcripts Loading (0-30s)**: Sessions endpoint may timeout, SSE detects sessions
3. **Wave 1 Complete (~60s)**: Individual cards show loading overlay as each session completes
4. **1s delay before refresh**: Allows backend database writes to complete
5. **Cards update with Wave 1 data**: Topics, summary, mood, technique populate
6. **Wave 2 Complete (~9.6 min)**: Individual cards update with prose analysis
7. **Stop button**: Terminates all running processes to save API costs

**Critical Fixes (Jan 3):**
- **Card scaling**: Changed max scale from 1.5x → 1.0x (cards now correct size on large monitors)
- **Debounce bug**: Removed clearTimeout() that broke promise resolution (overlays now clear properly)
- **1s DB delay**: Added delay before refresh to ensure backend writes complete
- **SessionDetail live updates**: Added effect to update selectedSession when sessions array changes
- **Stop button**: POST /api/demo/stop terminates transcript/wave1/wave2 processes gracefully

**Feature Flags:**
- `NEXT_PUBLIC_GRANULAR_UPDATES=true` - Per-session updates enabled
- `NEXT_PUBLIC_SSE_ENABLED=false` - SSE disabled (polling fallback active)
- `NEXT_PUBLIC_POLLING_INTERVAL_WAVE1=1000` - 1s during Wave 1
- `NEXT_PUBLIC_POLLING_INTERVAL_WAVE2=3000` - 3s during Wave 2

**API Cost Breakdown (OpenAI GPT-5 series):**
- **Per Session**: ~$0.0423 (4.23¢)
  - Wave 1: ~$0.0105 (mood + topics + action summary + breakthrough)
  - Wave 2: ~$0.0318 (deep analysis + prose)
- **Full Demo (10 sessions)**: ~$0.423
- **With Whisper transcription**: +$3.60 (60-min sessions)
- **Stop after Wave 1**: Saves ~$0.32
- **Phase 1C Cost Increase**: +0.7% (+$0.0003/session) - negligible

**Next Steps:**
- [x] ~~Monitor production logs for granular update behavior~~ ✅ COMPLETE
- [x] ~~Verify stop button works in production~~ ✅ COMPLETE
- [x] ~~Add OpenAI credits for testing~~ ✅ COMPLETE
- [x] ~~**PR #1 Phase 1A:** Font standardization~~ ✅ COMPLETE
- [x] ~~**PR #1 Phase 1C:** Planning for UI improvements + Wave 1 action summarization~~ ✅ COMPLETE
- [x] ~~**PR #1 Phase 1C:** Execute implementation (backend + frontend + database)~~ ✅ COMPLETE
- [x] ~~**PR #1 Phase 1C:** Apply database migration via Supabase MCP~~ ✅ COMPLETE
- [x] ~~**PR #1 Phase 1C:** Update documentation (SESSION_LOG, TheraBridge, CLAUDE)~~ ✅ COMPLETE
- [x] ~~**PR #1 Production Testing:** Test in production~~ ❌ FAILED (3 blockers found)
- [x] ~~**PR #1 CRITICAL FIXES:** Fix 3 production blockers~~ ✅ COMPLETE (2026-01-08)
  - [x] ~~Fix #1: Removed `breakthrough_history` table references~~ ✅ COMPLETE
  - [x] ~~Fix #2: Added ActionItemsSummarizer to seed script~~ ✅ COMPLETE
  - [x] ~~Fix #3: Frontend accessible, API returns 200 OK~~ ✅ COMPLETE
- [x] ~~**PR #1 Final Testing:** Verify all 6 Phase 1C UI features in production~~ ✅ COMPLETE (2026-01-09)
- [x] ~~**PR #1 Theme Fixes:** Fix emoji color switching + theme toggle styling~~ ✅ COMPLETE (2026-01-09)
- [ ] **PR #1:** Archive PR #1 documentation and mark complete
- [ ] **PR #1 Phase 1B:** Header fonts + Timeline deprecation (deferred to future)
- [ ] **PR #2:** Implement Prose Analysis UI with Toggle
- [ ] Implement Feature 2: Analytics Dashboard

**Full Documentation:** See `Project MDs/TheraBridge.md`
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

### 2026-01-07 - SessionDetail UI Improvements Planning (PR #1 Phase 1C) 📋
**Comprehensive planning for SessionDetail enhancements and Wave 1 action summarization:**

**Scope Expansion:**
- Original PR #1 focused on font standardization (Phase 1A complete)
- User requested additional SessionDetail improvements (Phase 1C)
- Combines UI enhancements with backend Wave 1 extension

**Features Planned:**
1. Numeric mood score display (emoji + score like "😊 7.5")
2. Technique definitions (2-3 sentence explanations)
3. 45-char action items summary (new Wave 1 LLM call)
4. X button in top-right corner (replace "Back to Dashboard")
5. Theme toggle in SessionDetail header
6. SessionCard update to use condensed action summary

**Research Phase (Wave 0):**
- ✅ Custom emoji system verified (3 SVG emojis: happy/neutral/sad)
- ✅ SessionCard data flow traced (backend → API → frontend mapping)
- ✅ Technique library analyzed (107 techniques in technique_library.json)
- ✅ Wave 1 architecture documented (3 parallel + sequential summarization)

**Technical Decisions:**
- Action summarization: Sequential after topic extraction (preserves quality)
- Mood mapping: Numeric (0-10) → Categorical (sad/neutral/happy)
- Technique definitions: Included in API response (no extra calls)
- Cost impact: +0.7% (+$0.0003/session)

**Deliverables:**
- ✅ Implementation plan: `thoughts/shared/plans/2026-01-07-sessiondetail-ui-improvements-wave1-action-summarization.md`
- ✅ Architecture documentation with data flow diagrams
- ✅ Complete file-by-file change specifications
- ✅ Testing strategy and rollback plan

**Next:** Execute implementation in separate Claude window (full-stack changes)

---

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
