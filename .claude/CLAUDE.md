# Repository Organization Rules

## 🚨 CRITICAL RULE - GIT FIRST, ALWAYS
**BEFORE MAKING ANY CHANGES (deletions, modifications, cleanup):**
1. **STOP** - Do not proceed with any deletions or modifications
2. **CHECK GIT STATUS** - Run `git status` to see what is tracked vs untracked
3. **COMMIT EVERYTHING** - Run `git add -A && git commit -m "Backup before cleanup"`
4. **VERIFY COMMIT** - Run `git log -1` to confirm commit was created
5. **THEN AND ONLY THEN** - Proceed with changes

**This rule applies to:**
- Deleting any files or folders
- Major refactoring or reorganization
- Consolidating documentation
- Cleaning up code
- ANY operation that removes or significantly modifies files

**Why this matters:**
- Untracked files CANNOT be recovered from git
- A commit creates a safety net for ALL files (tracked and untracked)
- Users may have work-in-progress that isn't committed yet
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
- [ ] Test frontend with live backend (set NEXT_PUBLIC_USE_REAL_API=true)
- [ ] Fix remaining ESLint errors in pre-existing components
- [ ] Deploy backend to AWS Lambda
- [ ] Implement Feature 2: Analytics Dashboard
- [ ] Test Vast.ai GPU pipeline for production workloads

---

## Session Log

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
