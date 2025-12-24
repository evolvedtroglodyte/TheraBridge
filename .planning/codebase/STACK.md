# Technology Stack

**Analysis Date:** 2026-01-08

## Languages

**Primary:**
- TypeScript 5+ - All frontend application code (`frontend/tsconfig.json`)
- Python 3.13.9 - All backend services (`.python-version`, `backend/.python-version`, `audio-transcription-pipeline/.python-version`)

**Secondary:**
- JavaScript - Build scripts, Next.js config files (`frontend/next.config.ts`)
- Python 3.11 (legacy) - Web scraping utility only (`Scrapping/.python-version`)

## Runtime

**Environment:**
- Node.js 20.9.0+ - Frontend Next.js application (`frontend/package.json`)
- Python 3.13.9 - Backend API and audio pipeline
- Python 3.11 - Legacy scraping utility

**Package Manager:**
- npm 10.0.0+ - Frontend dependencies
- Lockfile: `frontend/package-lock.json` present
- pip - Python package management
- Lockfiles: `requirements.txt` in each Python project

## Frameworks

**Core:**
- Next.js 15.5.9 - Full-stack React framework (`frontend/package.json`, `frontend/next.config.ts`)
- React 19.2.1 - UI library (`frontend/package.json`)
- FastAPI 0.115.0 - Python async web framework (`backend/requirements.txt`, `backend/app/main.py`)
- Uvicorn 0.32.0 - ASGI server for FastAPI (`backend/requirements.txt`)

**Testing:**
- Playwright 1.57.0 - E2E testing (`frontend/package.json`, `frontend/tests/*.spec.ts`)
- pytest 8.1.1+ - Python unit/integration tests (`backend/requirements.txt`, `audio-transcription-pipeline/pytest.ini`)
- pytest-asyncio - Async test support (`backend/requirements.txt`)
- pytest-cov 4.1.0 - Coverage reporting (`Scrapping/requirements.txt`)

**Build/Dev:**
- TypeScript 5+ - Compilation (`frontend/tsconfig.json`)
- Tailwind CSS 3.4.0 - Utility-first CSS framework (`frontend/tailwind.config.ts`)
- PostCSS 8 - CSS processing (`frontend/package.json`)
- ESLint 9 - Linting with Next.js config (`frontend/eslint.config.mjs`)
- Black 23.12.1 - Python code formatter (`.pre-commit-config.yaml`)
- isort 5.13.2 - Python import sorting (`.pre-commit-config.yaml`)
- Prettier 3.1.0 - Frontend code formatting (`.pre-commit-config.yaml`)

## Key Dependencies

**Critical:**
- OpenAI 1.54.4 (backend) / 6.15.0 (frontend) - GPT-5 series LLM analysis, Whisper transcription (`backend/app/services/mood_analyzer.py`, `backend/app/services/topic_extractor.py`)
- Supabase 2.9.0 (Python) / 2.89.0 (JavaScript) - PostgreSQL database client with RLS (`backend/app/database.py`, `frontend/lib/api-client.ts`)
- PyAnnote.audio 3.3.2+ - Speaker diarization (`audio-transcription-pipeline/requirements.txt`)

**Infrastructure:**
- Celery 5.4.0 - Background task queue (`backend/requirements.txt`)
- Redis 5.2.0 - Caching and task broker (`backend/requirements.txt`)
- Pydantic 2.10.2 - Data validation (`backend/requirements.txt`)
- Zod 3.23.8 - TypeScript schema validation (`frontend/package.json`)

**Frontend Data & UI:**
- SWR 2.3.7 - Data fetching hooks (`frontend/package.json`)
- Framer Motion 12.23.26 - Animations (`frontend/package.json`)
- Radix UI - Component primitives (`frontend/package.json`)
- Recharts 3.6.0 - Charting library (`frontend/package.json`)
- Sonner 2.0.7 - Toast notifications (`frontend/package.json`)
- date-fns 4.1.0 - Date utilities (`frontend/package.json`)

**Audio Processing:**
- PyDub 0.25.1 - Audio manipulation (`audio-transcription-pipeline/ui-web/backend/requirements.txt`)
- Torch 2.0.0+ - ML framework (`audio-transcription-pipeline/ui-web/backend/requirements.txt`)
- TorchAudio 2.0.0+ - Audio ML operations (`audio-transcription-pipeline/ui-web/backend/requirements.txt`)

**Web Scraping:**
- Crawl4ai 0.7.4+ - JavaScript-rendering scraper (`Scrapping/requirements.txt`)
- Playwright 1.42.0 - Browser automation (`Scrapping/requirements.txt`)
- HTTPX 0.27.0 - Async HTTP client (`Scrapping/requirements.txt`)

## Configuration

**Environment:**
- .env files for all services (backend, frontend, audio-pipeline)
- Backend: `DATABASE_URL`, `OPENAI_API_KEY`, `JWT_SECRET`, Supabase credentials (`backend/.env.example`)
- Frontend: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_USE_REAL_API`, feature flags (`frontend/.env.local.example`)
- Audio: `OPENAI_API_KEY`, `HUGGINGFACE_TOKEN` (`audio-transcription-pipeline/.env.example`)

**Build:**
- TypeScript: `frontend/tsconfig.json` - strict mode, ES2017 target
- Next.js: `frontend/next.config.ts` - TypeScript config
- Tailwind: `frontend/tailwind.config.ts` - custom theme, Inter font
- ESLint: `frontend/eslint.config.mjs` - Next.js + TypeScript rules
- pytest: `audio-transcription-pipeline/pytest.ini` - markers, asyncio mode

## Platform Requirements

**Development:**
- macOS/Linux/Windows - Any platform with Node.js 20+ and Python 3.13
- Docker optional - No container orchestration required
- Local Supabase instance optional - Can use cloud instance

**Production:**
- Railway.app - Primary deployment platform (`frontend/railway.json`, `backend/railway.json`)
- Neon PostgreSQL via Supabase - Managed database with RLS
- Node.js 20+ for frontend hosting
- Python 3.13 for backend/audio pipeline
- No Redis required (configured but optional)

---

*Stack analysis: 2026-01-08*
*Update after major dependency changes*
