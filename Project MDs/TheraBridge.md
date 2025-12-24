# TheraBridge - Project State

## Current Focus: SessionDetail UI Improvements + Wave 1 Action Summarization (PR #1)

**PR #1 Status:** Phase 1C Complete ✅ | Ready for Production Testing

**Phase 1C Complete (2026-01-08):**
- ✅ Database migration applied - `action_items_summary` TEXT column added
- ✅ Backend: ActionItemsSummarizer service (gpt-5-nano, 45-char max)
- ✅ Backend: Sequential action summarization integrated into Wave 1 orchestration
- ✅ Backend: Sessions API enriched with technique definitions from technique_library.json
- ✅ Frontend: Mood mapper utility (numeric 0-10 → categorical sad/neutral/happy)
- ✅ Frontend: Session interface extended with 8 new fields
- ✅ Frontend: SessionCard uses condensed action summary (45 chars)
- ✅ Frontend: SessionDetail displays mood score + emoji, technique definitions, X button, theme toggle
- ✅ Build verified successful, commit `be21ae3` pushed to remote

**Phase 1A Complete (2026-01-07):**
- ✅ SessionDetail.tsx - All fonts standardized (Inter + Crimson Pro)
- ✅ DeepAnalysisSection.tsx - All fonts standardized, badges fixed
- ✅ Removed all `system-ui` fallbacks and Tailwind font classes
- ✅ Fixed metadata font mismatch between SessionCard and SessionDetail
- ✅ Build verified successful, 4 commits pushed to remote

**Phase 1B Deferred:**
- ⏳ Header fonts + Timeline deprecation (non-critical, deferred to future)

**Commits (PR #1):**
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
1. **Demo Init (0-3s):** Patient ID stored, SSE connects
2. **Transcripts Loading (0-30s):** Sessions endpoint may timeout, SSE detects sessions
3. **Wave 1 Complete (~60s):** Individual cards show loading overlay, update with topics/summary/mood
4. **1s delay before refresh:** Allows backend database writes to complete
5. **Wave 2 Complete (~9.6 min):** Individual cards update with prose analysis
6. **Stop button:** Terminates all running processes to save API costs

**Feature Flags:**
- `NEXT_PUBLIC_GRANULAR_UPDATES=true` - Per-session updates enabled
- `NEXT_PUBLIC_SSE_ENABLED=false` - SSE disabled (polling fallback active)
- `NEXT_PUBLIC_POLLING_INTERVAL_WAVE1=1000` - 1s during Wave 1
- `NEXT_PUBLIC_POLLING_INTERVAL_WAVE2=3000` - 3s during Wave 2

**API Cost Breakdown (OpenAI GPT-5 series):**
- **Per Session:** ~$0.0423 (4.23¢)
  - Wave 1: ~$0.0105 (mood + topics + action summary + breakthrough)
  - Wave 2: ~$0.0318 (deep analysis + prose)
- **Full Demo (10 sessions):** ~$0.423
- **With Whisper transcription:** +$3.60 (60-min sessions)
- **Stop after Wave 1:** Saves ~$0.32
- **Phase 1C Cost Increase:** +0.7% (+$0.0003/session) - negligible

**Next Steps:**
- ✅ Review Font Standardization plan (PR #1)
- ✅ Implement Phase 1A (SessionDetail + DeepAnalysis fonts)
- ✅ Implement Phase 1C (SessionDetail UI improvements + action summarization)
- [ ] Test in production: Trigger demo pipeline, verify action summaries, mood scores, technique definitions
- [ ] Monitor Railway logs for sequential action summarization execution
- [ ] Verify UI renders correctly (mood emoji + score, technique definitions, X button, theme toggle)
- [ ] Complete Phase 1B (Header + Timeline deprecation) - deferred
- [ ] Merge PR #1
- [ ] Implement PR #2 (Prose Analysis UI with Toggle)
- [ ] Implement Feature 2: Analytics Dashboard

**Full Documentation:** See `.claude/SESSION_LOG.md` for detailed session history

---

## Development Status

### Active PRs
- None currently

### Completed PRs
- **PR #1:** SessionDetail UI Improvements + Wave 1 Action Summarization
  - Status: ✅ Complete (2026-01-09)
  - Plans:
    - `thoughts/shared/plans/2025-01-06-font-standardization-sessiondetail.md`
    - `thoughts/shared/plans/2026-01-07-sessiondetail-ui-improvements-wave1-action-summarization.md`
  - Sessions: SESSION_LOG.md (2025-01-06, 2026-01-07 Phase 1A, 2026-01-07 Phase 1C Planning, 2026-01-08 Phase 1C Implementation, 2026-01-09 Final Testing)
  - Scope: 10 files modified (3 new, 7 modified)
  - Phase 1A: ✅ Complete (commits d3f7390, 87098f6, c2eea93, e7f8e6a)
  - Phase 1B: ⏳ Deferred (Header fonts + Timeline deprecation)
  - Phase 1C: ✅ Complete (commit be21ae3, fixes: 3e9ea89, 8e3bd82, a9cc104-ab52d2a, f97286e)

- **PR #2:** Prose Analysis UI with Toggle
  - Status: ✅ Complete (2026-01-11) - Awaiting Railway deployment verification
  - Plan: `thoughts/shared/plans/2026-01-11-pr2-prose-analysis-ui-toggle.md`
  - Session: SESSION_LOG.md (2026-01-11)
  - Scope: 1 file modified (SessionDetail.tsx)
  - Features: Tab toggle, localStorage persistence, theme-aware colors, Framer Motion transitions
  - Commit: `8271286`

### Planned PRs
  - Default view: Prose (with localStorage persistence)
  - Color palette: Unified theme based on dashboard teal/purple

---

## Repository Structure

**Monorepo with 4 independent projects:**

```
peerbridge proj/
├── .claude/                   # Claude Code config (root only)
│   ├── CLAUDE.md              # This file
│   └── SESSION_LOG.md         # Detailed session history
├── Project MDs/
│   └── TheraBridge.md         # This file (master documentation)
├── thoughts/shared/plans/     # Implementation plans
├── README.md                  # Root README (project overview)
│
├── audio-transcription-pipeline/  # STANDALONE PROJECT
├── backend/                   # STANDALONE PROJECT (TheraBridge API)
├── frontend/                  # STANDALONE PROJECT (TheraBridge UI)
└── Scrapping/                 # STANDALONE PROJECT (Web scraping utility)
```

**Key principle:** Each subproject is self-contained and can be deployed independently.

---

## Quick Commands

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

**Run transcription pipeline:**
```bash
cd audio-transcription-pipeline
source venv/bin/activate
python tests/test_full_pipeline.py
```

---

## Environment Configuration

**Python Version Standardization:**
- ✅ Root: Python 3.13.9
- ✅ Backend: Python 3.13.9
- ✅ Audio Pipeline: Python 3.13.9
- ⚠️ Scrapping: Python 3.11 (legacy, not yet upgraded)

**Environment Files Status:**
- `backend/.env` - Complete production configuration (all fields populated)
- `audio-transcription-pipeline/.env` - Documented via .env.example
- `frontend/.env.local` - Validated (API URL + feature flags)
- `Scrapping/.env` - Independent project

**Security Note:** .env files currently tracked in git. Production deployments should use environment variables or secrets management.
