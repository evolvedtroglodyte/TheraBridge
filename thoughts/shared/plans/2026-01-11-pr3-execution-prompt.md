# PR #3 Execution Prompt - Your Journey Dynamic Roadmap

**Use this prompt to start a new Claude window for implementing PR #3.**

---

## Context

I need you to implement **PR #3: Your Journey Dynamic Roadmap** for the TheraBridge project. This feature makes the "Your Journey" card on the patient dashboard update dynamically after each session's Wave 2 analysis completes, showing cumulative therapeutic progress.

## Implementation Plan

**READ THIS PLAN FIRST (CRITICAL):**

The complete, detailed implementation plan is located at:
```
thoughts/shared/plans/2026-01-11-your-journey-dynamic-roadmap.md
```

**YOU MUST READ THE ENTIRE PLAN BEFORE STARTING.** It contains:
- 5 phases with step-by-step instructions
- Complete code examples for all changes
- Success criteria (automated + manual verification) for each phase
- Architecture diagrams and data flow explanations
- Cost analysis and performance considerations

## Implementation Phases

**Phase 0: Fix LoadingOverlay Bug** (MUST DO FIRST)
- Debug why spinner overlay isn't showing on session cards
- Add logging to track overlay state changes
- Verify feature flags and polling detection
- **Critical:** This must work before building roadmap features

**Phase 1: Backend Infrastructure**
- Create database tables (`patient_roadmap`, `roadmap_versions`)
- Implement `SessionInsightsSummarizer` service (GPT-5.2)
- Implement `RoadmapGenerator` service (GPT-5.2, 3 strategies)
- Update `model_config.py`

**Phase 2: Compaction Strategies**
- Strategy 1: Full Context (all previous sessions)
- Strategy 2: Progressive Summarization (previous roadmap + current)
- Strategy 3: Hierarchical (multi-tier summaries) - **Recommended**
- Switchable via env var `ROADMAP_COMPACTION_STRATEGY`

**Phase 3: Frontend Integration**
- Update `NotesGoalsCard.tsx` with API fetching
- Add "Based on X out of Y sessions" counter
- Integrate loading overlay (reuse session card pattern)
- Update polling to detect roadmap updates

**Phase 4: Start/Stop/Resume Button**
- Upgrade "Stop Processing" to dynamic button
- Add resume endpoint: `POST /api/demo/resume`
- Smart resume logic (re-run incomplete, continue with remaining)
- Processing state tracking in status response

**Phase 5: Orchestration & Testing**
- Create `backend/scripts/generate_roadmap.py` orchestration script
- Integrate roadmap generation into Wave 2 flow
- End-to-end testing (all 3 strategies)
- Manual verification of UI behavior

## Key Architecture Decisions

**Flow:**
```
Wave 2 completes (Session N)
  ↓
SessionInsightsSummarizer (GPT-5.2) - Extract 3-5 key insights
  ↓
RoadmapGenerator (GPT-5.2) - Generate roadmap using selected strategy
  ↓
Database UPDATE (patient_roadmap + roadmap_versions)
  ↓
Frontend polling detects change (roadmap_updated_at)
  ↓
Show loading overlay (1000ms spinner)
  ↓
Fetch updated roadmap, update counter
```

**Models:**
- Session Insights: GPT-5.2 (maximum quality, reusable service)
- Roadmap Generation: GPT-5.2 (configurable in `model_config.py`)

**Database:**
- `patient_roadmap` table: Latest roadmap for each patient
- `roadmap_versions` table: Full version history with metadata

**Cost Estimate:**
- Current (10 sessions): ~$0.42
- With Roadmap (hierarchical): ~$0.77 (+$0.35, +83%)
- Full context strategy: +$0.80 (most expensive)
- Progressive strategy: +$0.25 (cheapest)

## Critical Requirements

1. **Sequential Execution:** Complete each phase fully before moving to next
2. **Verification:** Run ALL success criteria (automated + manual) after each phase
3. **Phase 0 First:** LoadingOverlay MUST work before building roadmap
4. **Three Strategies:** Implement all 3 compaction strategies (user wants to experiment)
5. **Version History:** Store ALL roadmap versions (user wants to see evolution)
6. **Git Commits:** Follow backdating rules from `.claude/CLAUDE.md`

## Important Context Files

**Read these for full context:**
1. `.claude/CLAUDE.md` - Repository rules, git commit dating, PR tracking
2. `Project MDs/TheraBridge.md` - Project state, development status
3. `.claude/SESSION_LOG.md` - Session history (see 2026-01-11 entry for planning details)
4. `thoughts/shared/plans/2026-01-11-your-journey-dynamic-roadmap.md` - **THE IMPLEMENTATION PLAN**

**Existing Code to Reference:**
- Wave 2 cumulative context: `backend/scripts/seed_wave2_analysis.py:105-143`
- Session card loading overlay: `frontend/app/patient/components/SessionCard.tsx:562`
- Polling detection: `frontend/app/patient/lib/usePatientSessions.ts:48-90`
- LoadingOverlay component: `frontend/app/patient/components/LoadingOverlay.tsx`

## What Success Looks Like

**End-to-End Flow:**
1. User loads patient dashboard → "Your Journey" card shows empty state
2. User triggers demo (10 sessions)
3. After Session 1 Wave 2 completes (~60s) → Card shows loading overlay (1000ms spinner)
4. Card updates with roadmap based on Session 1 → Counter shows "Based on 1 out of 10 uploaded sessions"
5. After Session 2 Wave 2 completes → Loading overlay → Roadmap updates → Counter shows "2 out of 10"
6. Process continues through all 10 sessions
7. User can stop/resume at any time → Button changes dynamically
8. All 3 compaction strategies work (switchable via env var)
9. Version history stored in database (10 versions for 10 sessions)

## User Preferences

From planning session, the user wants:
- **High quality output** (GPT-5.2 for both insights and roadmap)
- **Experimentation** (all 3 compaction strategies, easy to switch)
- **Version history** ("for my own satisfaction" to see how roadmaps evolve)
- **Start/Stop/Resume** button (save API costs, control processing)
- **Spinner overlay** (visual feedback like session cards)

## Questions?

If anything is unclear:
1. **First:** Read the full implementation plan (`thoughts/shared/plans/2026-01-11-your-journey-dynamic-roadmap.md`)
2. **Second:** Check existing code patterns (referenced above)
3. **Third:** Read SESSION_LOG.md entry (2026-01-11) for planning context
4. **Last resort:** Ask clarifying questions before proceeding

## Start Command

When ready to start, say:

"I've read the implementation plan at `thoughts/shared/plans/2026-01-11-your-journey-dynamic-roadmap.md`. Starting with Phase 0: Fix LoadingOverlay Bug. I will debug the spinner overlay issue before building any roadmap features."

---

**Good luck! Execute each phase carefully, verify thoroughly, and don't skip Phase 0.** 🚀
