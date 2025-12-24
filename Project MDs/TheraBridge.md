# TheraBridge - Project State

## Current Focus: Font Standardization & UI Consistency (PR #1)

**Recent Completion (2026-01-03):**
- ✅ Real-time granular session updates (per-session loading overlays)
- ✅ SSE event queue with database backing
- ✅ Adaptive polling (1s Wave 1 → 3s Wave 2)
- ✅ SessionDetail scroll preservation
- ✅ Card scaling fix (capped at 1.0x)
- ✅ Loading overlay debounce bug fix
- ✅ "Stop Processing" button to terminate pipeline

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
- **Per Session:** ~$0.042 (4.2¢)
  - Wave 1: ~$0.0102 (mood + topics + breakthrough)
  - Wave 2: ~$0.0318 (deep analysis + prose)
- **Full Demo (10 sessions):** ~$0.42
- **With Whisper transcription:** +$3.60 (60-min sessions)
- **Stop after Wave 1:** Saves ~$0.32

**Next Steps:**
- ✅ Review Font Standardization plan (PR #1)
- ✅ Implement Phase 1A (SessionDetail + DeepAnalysis fonts)
- [ ] Test font consistency in light/dark modes (Phase 1A testing)
- [ ] Implement Phase 1B (Header + Timeline deprecation)
- [ ] Merge PR #1
- [ ] Implement PR #2 (Prose Analysis UI with Toggle)
- [ ] Implement Feature 2: Analytics Dashboard

**Full Documentation:** See `.claude/SESSION_LOG.md` for detailed session history

---

## Development Status

### Active PRs
- **PR #1:** Font Standardization - SessionDetail & DeepAnalysis
  - Status: Testing (Phase 1A complete, Phase 1B pending)
  - Plan: `thoughts/shared/plans/2025-01-06-font-standardization-sessiondetail.md`
  - Sessions: SESSION_LOG.md (2025-01-06, 2026-01-07)
  - Scope: 3 files (SessionDetail.tsx, DeepAnalysisSection.tsx, Header.tsx) + 2 deprecations
  - Phase 1A: ✅ Complete (commit d3f7390)
  - Phase 1B: ⏳ Pending user approval after testing

### Completed PRs
- None yet

### Planned PRs
- **PR #2:** Prose Analysis UI with Toggle
  - Status: Planned (depends on PR #1)
  - Description: Add tab toggle between structured analysis cards and prose narrative view
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
