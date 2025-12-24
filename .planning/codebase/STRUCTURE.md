# Codebase Structure

**Analysis Date:** 2026-01-08

## Directory Layout

```
peerbridge proj/
├── .claude/                    # Claude Code config (root only)
│   ├── CLAUDE.md              # Repository rules + commit dating
│   ├── SESSION_LOG.md         # Detailed session history
│   └── [agents, commands, skills]
├── .planning/                 # Planning artifacts
│   └── codebase/             # THIS analysis output
├── Project MDs/              # Master documentation
│   └── TherapyBridge.md      # Full project state
├── frontend/                 # Next.js 16 + React 19 UI
│   ├── app/                  # Next.js App Router pages
│   ├── components/           # Reusable UI components
│   ├── lib/                  # API client + utilities
│   ├── hooks/                # Custom React hooks
│   ├── contexts/             # React contexts
│   ├── tests/                # Playwright E2E tests
│   ├── public/               # Static assets
│   └── [config files]
├── backend/                  # FastAPI + Supabase API
│   ├── app/                  # Application code
│   │   ├── routers/          # API endpoints
│   │   ├── services/         # AI analysis services
│   │   ├── middleware/       # Auth validation
│   │   └── [main.py, database.py, config.py]
│   ├── scripts/              # Background seed scripts
│   ├── tests/                # pytest unit tests
│   ├── supabase/             # Database migrations
│   └── venv/                 # Independent Python env
├── audio-transcription-pipeline/  # Speech-to-text service
│   ├── src/                  # Pipeline code
│   ├── tests/                # pytest tests
│   └── venv/                 # Independent Python env
└── Scrapping/                # Web scraping utility
    ├── src/scraper/          # Scraper modules
    ├── tests/                # pytest tests
    └── venv/                 # Independent Python env
```

## Directory Purposes

**frontend/**
- Purpose: Next.js patient dashboard application
- Contains: TypeScript React components, pages, hooks, utilities
- Key files:
  - `frontend/app/page.tsx` - Entry point (demo init)
  - `frontend/app/patient/layout.tsx` - Dashboard layout
  - `frontend/lib/api-client.ts` - HTTP client
  - `frontend/lib/demo-token-storage.ts` - localStorage wrapper
- Subdirectories:
  - `app/` - Next.js 16 App Router (pages, layouts, route handlers)
  - `app/patient/` - Main dashboard routes
  - `app/patient/components/` - SessionCard, SessionDetail, DeepAnalysisSection
  - `app/patient/contexts/` - SessionDataContext, ThemeContext
  - `app/patient/lib/` - usePatientSessions hook, types
  - `components/` - Shared components (NavigationBar, etc.)
  - `lib/` - API client, storage, types, utilities
  - `tests/` - Playwright E2E tests (*.spec.ts)

**backend/**
- Purpose: FastAPI REST API with AI analysis services
- Contains: Python async web framework, Supabase database client
- Key files:
  - `backend/app/main.py` - FastAPI app initialization
  - `backend/app/database.py` - Supabase client singleton
  - `backend/app/config.py` - Environment settings
- Subdirectories:
  - `app/routers/` - sessions.py, demo.py, sse.py, debug.py
  - `app/services/` - mood_analyzer.py, topic_extractor.py, breakthrough_detector.py, deep_analyzer.py, prose_generator.py
  - `app/middleware/` - demo_auth.py
  - `scripts/` - seed_all_sessions.py, seed_wave1_analysis.py, seed_wave2_analysis.py
  - `tests/` - test_mood_analysis.py, test_breakthrough_detection.py
  - `supabase/migrations/` - 11 SQL migration files

**audio-transcription-pipeline/**
- Purpose: Whisper transcription + pyannote diarization
- Contains: CPU and GPU pipeline variants
- Key files:
  - `audio-transcription-pipeline/src/pipeline.py` - CPU pipeline
  - `audio-transcription-pipeline/src/pipeline_gpu.py` - GPU/Vast.ai pipeline
  - `audio-transcription-pipeline/pytest.ini` - Test config
- Subdirectories:
  - `src/` - pipeline.py, gpu_audio_ops.py, performance_logger.py
  - `tests/` - test_full_pipeline.py

**Scrapping/**
- Purpose: Competitive analysis web scraper
- Contains: Crawl4ai + Playwright scraping utilities
- Key files:
  - `Scrapping/src/scraper/config.py` - Scraper configuration
  - `Scrapping/src/scraper/scrapers/upheal_scraper.py` - Upheal competitive scraper
- Subdirectories:
  - `src/scraper/scrapers/` - Individual scraper modules
  - `src/scraper/models/` - Pydantic data models
  - `src/scraper/utils/` - HTTP client, rate limiter
  - `tests/` - pytest tests

**.claude/**
- Purpose: Claude Code configuration and history
- Contains: Repository rules, session logs, agents, skills
- Key files:
  - `.claude/CLAUDE.md` - Critical repository rules (git commit dating, backup protocol)
  - `.claude/SESSION_LOG.md` - Detailed session history
- Subdirectories:
  - `agents/cl/` - Agent definitions
  - `commands/cl/` - Custom commands
  - `skills/crawl4ai/` - Web crawling skill

**.planning/**
- Purpose: Project planning artifacts
- Contains: Codebase analysis (this output)
- Subdirectories:
  - `codebase/` - STACK.md, ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, INTEGRATIONS.md, CONCERNS.md

**Project MDs/**
- Purpose: Master documentation directory
- Contains: TheraBridge.md with full project state
- Key files:
  - `Project MDs/TheraBridge.md` - Current focus, development status, commands

## Key File Locations

**Entry Points:**
- `backend/app/main.py` - FastAPI app initialization + startup events
- `frontend/app/page.tsx` - Next.js root page (demo init entry point)
- `audio-transcription-pipeline/src/pipeline.py` - CPU transcription pipeline

**Configuration:**
- `frontend/tsconfig.json` - TypeScript compiler options
- `frontend/next.config.ts` - Next.js configuration
- `frontend/tailwind.config.ts` - Tailwind CSS theme
- `frontend/eslint.config.mjs` - ESLint rules
- `backend/app/config.py` - Backend settings from environment
- `audio-transcription-pipeline/pytest.ini` - Test runner config
- `.pre-commit-config.yaml` - Pre-commit hooks (Black, isort, Prettier, ESLint)
- `.python-version` - Python 3.13.9 (root + backend + audio-pipeline)
- `Scrapping/.python-version` - Python 3.11 (legacy)

**Core Logic:**
- `frontend/lib/api-client.ts` - Authenticated HTTP client
- `frontend/app/patient/lib/usePatientSessions.ts` - Core data fetching hook with polling
- `backend/app/routers/sessions.py` - Session CRUD + analysis endpoints (1707 lines)
- `backend/app/routers/demo.py` - Demo init + background orchestration (727 lines)
- `backend/app/services/analysis_orchestrator.py` - Wave 1/2 coordination
- `backend/app/database.py` - Supabase client wrapper

**Testing:**
- `frontend/tests/*.spec.ts` - Playwright E2E tests (42+ test files)
- `backend/tests/test_*.py` - pytest unit tests (10+ test files)
- `audio-transcription-pipeline/tests/test_full_pipeline.py` - End-to-end pipeline test

**Documentation:**
- `README.md` - Root project overview
- `.claude/CLAUDE.md` - Repository organization rules
- `.claude/SESSION_LOG.md` - Detailed session history
- `Project MDs/TheraBridge.md` - Full project state + current focus
- `frontend/app/patient/README.md` - Dashboard documentation
- `backend/README.md` - Backend quickstart
- `audio-transcription-pipeline/README.md` - Pipeline usage guide

## Naming Conventions

**Files:**
- Components: PascalCase.tsx (SessionCard.tsx, DeepAnalysisSection.tsx)
- Utilities: kebab-case.ts (refresh-detection.ts, demo-token-storage.ts)
- Custom hooks: use + PascalCase (usePatientSessions.ts, useMoodAnalysis.ts)
- Pages: lowercase (page.tsx, layout.tsx)
- Python modules: snake_case.py (mood_analyzer.py, demo_auth.py)
- Tests: *.spec.ts (frontend), test_*.py (backend)
- Deprecated: *.DEPRECATED.tsx

**Directories:**
- kebab-case for feature directories
- Plural for collections (components/, routers/, services/, tests/)
- Lowercase for Next.js conventions (app/, lib/, hooks/)

**Special Patterns:**
- index.tsx for component barrel exports
- layout.tsx for Next.js layouts
- page.tsx for Next.js pages
- route.ts for Next.js API routes
- __tests__/ for inline test directories (not used)

## Where to Add New Code

**New Frontend Feature:**
- Primary code: `frontend/app/patient/components/{FeatureName}.tsx`
- Types: `frontend/app/patient/lib/types.ts` or `frontend/lib/types.ts`
- API client: `frontend/lib/api-client.ts` or `frontend/lib/demo-api-client.ts`
- Tests: `frontend/tests/{feature-name}.spec.ts`

**New Backend API Endpoint:**
- Route: `backend/app/routers/{resource}.py` (sessions, demo, debug)
- Service: `backend/app/services/{analyzer_name}.py`
- Tests: `backend/tests/test_{service_name}.py`
- Config: `backend/app/config.py` (if new env var needed)

**New Analysis Service:**
- Implementation: `backend/app/services/{name}_analyzer.py`
- Orchestration: Update `backend/app/services/analysis_orchestrator.py`
- Database: Add migration in `backend/supabase/migrations/{version}_{name}.sql`
- Tests: `backend/tests/test_{name}_analysis.py`

**New Background Job:**
- Script: `backend/scripts/seed_{job_name}.py`
- Invocation: Update `backend/app/routers/demo.py` subprocess calls
- Logging: Use `print(..., flush=True)` for Railway visibility

**Utilities:**
- Shared frontend helpers: `frontend/lib/{utility-name}.ts`
- Shared backend helpers: `backend/app/utils/` (create if needed)
- Type definitions: `frontend/lib/types.ts` or `backend/app/models/`

## Special Directories

**.next/**
- Purpose: Next.js build output
- Source: Auto-generated by `next build`
- Committed: No (in .gitignore)

**venv/ (multiple instances)**
- Purpose: Python virtual environments
- Source: `python -m venv venv` in each Python project
- Committed: No (in .gitignore)

**node_modules/**
- Purpose: npm package installations
- Source: `npm install`
- Committed: No (in .gitignore)

**.planning/codebase/**
- Purpose: Generated codebase analysis documents
- Source: This workflow (gsd:map-codebase)
- Committed: Yes (documentation for planning)

---

*Structure analysis: 2026-01-08*
*Update when directory structure changes*
