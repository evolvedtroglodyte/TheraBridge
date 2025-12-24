# TheraBridge

## What This Is

TheraBridge is an AI-powered therapy session analysis platform that transforms audio transcripts into comprehensive clinical insights. It provides therapists with automated session summaries, mood tracking, therapeutic technique identification, and deep clinical analysis, while giving patients a personalized dashboard to review their progress and session insights.

## Core Value

**Therapists must be able to review 10 therapy sessions in under 5 minutes with complete confidence in the AI-generated insights.**

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ **Audio Transcription Pipeline** — Whisper API transcription with speaker diarization (pyannote 3.1) — v1.0
- ✓ **Wave 1 Analysis** — Topic extraction, mood analysis (0-10 scale), action items, breakthrough detection — v1.0
- ✓ **Wave 2 Analysis** — Deep clinical analysis (JSONB structure) + prose narrative generation — v1.0
- ✓ **Patient Dashboard** — Session cards with topics, mood, technique, action summaries — v1.0
- ✓ **SessionDetail Modal** — Two-column layout with transcript viewer and analysis panel — v1.0
- ✓ **Real-Time Updates** — Granular per-session polling with loading overlays, adaptive intervals (1s → 3s) — v1.0
- ✓ **Demo Flow** — Non-blocking initialization, seed data with 10 pre-analyzed sessions — v1.0
- ✓ **Font Standardization** — Inter + Crimson Pro typography across SessionDetail and analysis components — PR #1
- ✓ **Action Summarization** — 45-char condensed action summaries via gpt-5-nano — PR #1
- ✓ **Enhanced SessionDetail UI** — Numeric mood score + emoji, technique definitions, X button, theme toggle — PR #1
- ✓ **Prose Analysis Toggle** — Tab switcher between narrative prose and structured analysis views with localStorage persistence — PR #2

### Active

<!-- Current scope. Building toward these. -->

- [ ] **Analytics Dashboard** — Progress metrics, trend visualization, therapist insights (Feature 2)
- [ ] **Session Upload** — Therapist audio file upload with processing pipeline integration
- [ ] **Multi-Patient Support** — Therapist view of all patients with session aggregation
- [ ] **Authentication** — JWT-based auth for therapists and patients

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- **Timeline Feature** — Deferred (mixed session + life event timeline adds complexity without clear user need)
- **Chatbot Integration** — Deferred to v2.0 (requires major event detection and patient confirmation flows)
- **Real-Time SSE** — Disabled in production (subprocess isolation bug, polling provides 95% of benefits)
- **Email Notifications** — Not needed for MVP (therapists check dashboard manually)
- **PDF Export** — Deferred to v2.0 (users haven't requested it yet)
- **Multi-Language Support** — English-only for MVP (no international users yet)
- **Mobile App** — Responsive web first (99% of usage is desktop)
- **Audio Player** — Not needed (transcripts are sufficient for review)

## Context

### Technical Environment

- **Stack**: Next.js 16 (App Router) + React 19 + TypeScript + Tailwind CSS
- **Backend**: FastAPI (Python 3.13.9) + Neon PostgreSQL (Supabase)
- **Deployment**: Railway (backend + database) + Vercel/Railway (frontend)
- **AI Services**: OpenAI GPT-5 series (gpt-5-nano, gpt-5-flash, gpt-5-preview) + Whisper API
- **Transcription**: Whisper API (CPU/API) or local GPU pipeline (Vast.ai)
- **Monorepo**: 4 independent projects (backend, frontend, audio-transcription-pipeline, Scrapping)

### Prior Work

- **v1.0 Launch** (Jan 2026): Full pipeline working in production with 10-session demo
- **Critical Bug Fix** (Jan 8-9): Fixed breakthrough_history references, GPT-5-nano parameter constraints, ActionItemsSummarizer integration
- **Granular Updates** (Jan 3): Per-session loading overlays with adaptive polling, database-backed SSE (disabled)
- **Font Standardization** (Jan 6-7): Inter + Crimson Pro across SessionDetail and DeepAnalysisSection

### User Feedback

- **Patients prefer narrative over structured** → Default to prose view in PR #2
- **Mood score numbers add context** → Added numeric mood (0-10) in PR #1
- **Technique names without definitions are confusing** → Added 2-3 sentence definitions from library in PR #1
- **Loading states unclear** → Added per-session overlays with Wave 1/2 awareness

### Known Issues

- **SSE subprocess isolation** — In-memory event queue doesn't work across subprocess.run() boundaries → Polling fallback active
- **Railway log buffering** — Python logging.info() invisible, requires print(..., flush=True) for real-time logs
- **GPT-5-nano API constraints** — Empty responses when ANY optional parameters used (temperature, max_completion_tokens)
- **DeepAnalysisSection verbosity** — Cards are dense, users might prefer summary view

## Constraints

- **Tech Stack**: Next.js 16 + React 19 (bleeding edge) — Required for App Router and modern patterns
- **AI Budget**: $0.0423/session (4.23¢) max — Cost must stay under $0.50/session to be sustainable
- **Timeline**: No hard deadlines — Quality over speed, validate before shipping
- **Database**: Neon PostgreSQL via Supabase — Free tier limits (500MB storage, 10GB bandwidth)
- **Git History**: All commits backdated to Dec 23, 2025 11:45 PM or earlier — Repository organization requirement
- **Python Version**: 3.13.9 for backend and pipeline (legacy 3.11 for Scrapping) — Standardized across projects
- **Performance**: Demo initialization must complete in <30s — User experience requirement
- **Accessibility**: WCAG 2.1 AA minimum — Keyboard nav, ARIA labels, screen reader support

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use GPT-5 series for all analysis | Better quality + lower cost than GPT-4, 5-nano is 80% cheaper than 4o-mini | ✓ Good — Quality excellent, costs sustainable |
| Sequential action summarization after topic extraction | Preserve parallel efficiency for topics/mood/breakthrough, add summary as 4th step | ✓ Good — +0.7% cost, maintains quality |
| Default to prose view in analysis toggle | User research shows patients prefer narrative over structured cards | — Pending (PR #2 not shipped yet) |
| Disable SSE in production, use polling | Subprocess isolation bug unfixable without major refactor, polling works well | ✓ Good — Reliable, 95% of SSE benefits |
| Database-backed event queue for SSE | In-memory queues don't work across subprocess boundaries | — Pending (implemented but not tested) |
| Backdate all commits to Dec 23, 2025 | Repository organization and historical consistency | — Pending (workflow requirement) |
| Use Crimson Pro + Inter fonts | Professional serif/sans pairing, matches therapy industry aesthetic | ✓ Good — Looks polished, readable |
| Store prose_analysis as TEXT column | Simpler than JSONB, supports multi-paragraph content | ✓ Good — Works perfectly for GPT output |
| localStorage for UI preferences | Simple client-side persistence, no backend state needed | — Pending (PR #2 uses this) |
| Framer Motion for UI transitions | Best-in-class animation library, already in stack | ✓ Good — Smooth, professional animations |

---
*Last updated: 2026-01-11 after PR #2 planning phase*
