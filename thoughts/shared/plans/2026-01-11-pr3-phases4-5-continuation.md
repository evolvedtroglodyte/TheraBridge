# PR #3 Continuation Prompt - Phases 4-5 (Button + Orchestration)

**Use this prompt to start a new Claude window for completing PR #3: Your Journey Dynamic Roadmap.**

---

## Context & Background

I need you to **continue implementation of PR #3: Your Journey Dynamic Roadmap** for the TheraBridge project.

**Phases 0-3 are COMPLETE** (backend infrastructure, compaction strategies, and frontend integration). You will implement **Phases 4-5** (Start/Stop/Resume button and orchestration/testing).

---

## What's Already Done (Phases 0-3) ✅

**Phase 0: LoadingOverlay Debug Logging**
- Debug logging added to `usePatientSessions.ts` and `SessionCard.tsx`
- Ready for production verification

**Phase 1: Backend Infrastructure**
- Database migration created: `backend/supabase/migrations/013_create_roadmap_tables.sql`
  - `patient_roadmap` table (latest version)
  - `roadmap_versions` table (full history)
- Model config updated: `backend/app/config/model_config.py`
  - `session_insights` task (GPT-5.2)
  - `roadmap_generation` task (GPT-5.2)
- Services created:
  - `backend/app/services/session_insights_summarizer.py` (127 lines)
  - `backend/app/services/roadmap_generator.py` (545 lines)

**Phase 2: Compaction Strategies**
- All 3 strategies implemented in `roadmap_generator.py`:
  - Full Context (~$0.014-0.020 per generation)
  - Progressive Summarization (~$0.0025 per generation)
  - Hierarchical (~$0.003-0.004 per generation) - DEFAULT
- Switchable via `ROADMAP_COMPACTION_STRATEGY` env var

**Phase 3: Frontend Integration**
- API client: `getRoadmap(patientId)` method added
- TypeScript interfaces: RoadmapData, RoadmapMetadata, RoadmapResponse
- SessionDataContext: Added `patientId` and `loadingRoadmap`
- NotesGoalsCard: Complete rewrite with real API fetching + session counter
- Polling: Roadmap update detection with 1000ms loading overlay
- Backend: Demo status endpoint includes `roadmap_updated_at` timestamp

**Commits Created:** 7 total (2a328c3 → b993320), all backdated to Dec 23, 2025

---

## What You Need to Do (Phases 4-5)

**Phase 4: Start/Stop/Resume Button Enhancement**
- Upgrade "Stop Processing" to dynamic button
- Add resume endpoint: `POST /api/demo/resume`
- Smart resume logic (re-run incomplete, continue with remaining)
- Processing state tracking in status response
- Button text changes: "Stop Processing" → "Resume Processing"

**Phase 5: Orchestration & Testing**
- **CRITICAL:** Apply database migration via Supabase MCP FIRST
- Create `backend/scripts/generate_roadmap.py` orchestration script
- Integrate roadmap generation into Wave 2 flow
- Implement tier compaction logic for hierarchical strategy
- End-to-end testing (all 3 strategies)
- Manual verification of UI behavior

---

## Implementation Plan (CRITICAL - READ THIS FIRST)

**The complete, detailed implementation plan is located at:**
```
thoughts/shared/plans/2026-01-11-your-journey-dynamic-roadmap.md
```

**YOU MUST READ THE FULL PLAN BEFORE STARTING.** It contains:
- Step-by-step instructions for each phase
- Complete code examples for all changes
- Success criteria (automated + manual verification)
- Architecture diagrams and data flow
- File-by-file change specifications with line numbers

**Plan Structure:**
- 2,621 lines total
- Phases 4-5 start at line ~1535
- Each phase has detailed subsections with code snippets

**Key Sections for Phases 4-5:**
- Phase 4: Lines 1535-1750 (Button enhancement, resume endpoint)
- Phase 5: Lines 1750-2350 (Migration, orchestration, testing)

---

## Critical Requirements

1. **Database Migration FIRST:** Apply migration via Supabase MCP before testing
2. **Sequential Execution:** Complete Phase 4 fully before moving to Phase 5
3. **Verification:** Run ALL success criteria after each phase
4. **Git Commits:** Follow backdating rules from `.claude/CLAUDE.md`
5. **Three Strategies:** Test all 3 compaction strategies work
6. **Tier Compaction:** Implement hierarchical tier logic in orchestration

---

## Important Context Files

**Read these for full context:**
1. `.claude/CLAUDE.md` - Repository rules, git commit dating, PR tracking
2. `Project MDs/TheraBridge.md` - Project state, development status
3. `.claude/SESSION_LOG.md` - Session history (see 2026-01-11 entries for Phases 0-3)
4. `thoughts/shared/plans/2026-01-11-your-journey-dynamic-roadmap.md` - **THE IMPLEMENTATION PLAN**

**Existing Code to Reference:**
- Session card loading overlay: `frontend/app/patient/components/SessionCard.tsx:563`
- Polling detection: `frontend/app/patient/lib/usePatientSessions.ts:48-90`
- Wave 2 cumulative context: `backend/scripts/seed_wave2_analysis.py:105-143`
- NotesGoalsCard (now uses real data): `frontend/app/patient/components/NotesGoalsCard.tsx`
- Demo status endpoint: `backend/app/routers/demo.py` (for /api/demo/status updates)
- Stop button: `frontend/app/patient/components/DashboardHeader.tsx` or similar

---

## Key Architecture Decisions (From Planning)

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

**Database:**
- `patient_roadmap` table: Latest roadmap for each patient
- `roadmap_versions` table: Full version history with metadata

**Models:**
- Session Insights: GPT-5.2 (maximum quality, reusable service)
- Roadmap Generation: GPT-5.2 (configurable in `model_config.py`)

**Cost Estimate:**
- Current (10 sessions): ~$0.42
- With Roadmap (hierarchical): ~$0.77 (+$0.35, +83%)
- Full context strategy: +$0.80 (most expensive)
- Progressive strategy: +$0.25 (cheapest)

---

## Git Commit Dating Rules

**CRITICAL:** Before creating ANY commit, you MUST:
1. Check the most recent commit timestamp: `git log --format="%ci" -n 1`
2. Add exactly 30 seconds to that timestamp
3. Use that new timestamp for your commit

**Example:**
```bash
# Last commit: 2025-12-23 22:46:22 -0600
# Next commit: 2025-12-23 22:46:52 -0600

git add <files> && \
GIT_COMMITTER_DATE="2025-12-23 22:46:52 -0600" \
git commit -m "message" --date="2025-12-23 22:46:52 -0600"
```

**NEVER hardcode timestamps. ALWAYS check the previous commit first.**

---

## Phase 4 Details: Start/Stop/Resume Button

**Current State:**
- "Stop Processing" button exists (terminates running processes)
- No resume functionality

**What to Build:**
- Dynamic button text based on processing state
- Resume endpoint that continues from last incomplete session
- Processing state tracking in demo status response
- Frontend button state management

**Button States:**
- "Stop Processing" - When analysis is running
- "Resume Processing" - When analysis was stopped mid-way
- Hidden/Disabled - When no demo or all complete

**Backend Changes:**
- Add `POST /api/demo/resume` endpoint
- Track processing state (running, stopped, complete)
- Smart resume logic: Find first incomplete session, continue from there

**Frontend Changes:**
- Update button component to show dynamic text
- Handle resume button click (call resume endpoint)
- Poll for processing state changes

---

## Phase 5 Details: Orchestration & Testing

**Critical First Step:**
Apply the database migration using Supabase MCP:
```typescript
mcp__supabase__apply_migration({
  name: "create_roadmap_tables",
  query: <contents of 013_create_roadmap_tables.sql>
})
```

**Orchestration Script:**
Create `backend/scripts/generate_roadmap.py`:
- Integrate with Wave 2 seed script OR standalone orchestration
- After each Wave 2 completion:
  1. Call SessionInsightsSummarizer
  2. Call RoadmapGenerator
  3. Save to patient_roadmap + roadmap_versions
- Implement tier compaction for hierarchical strategy:
  - Tier 1: Recent sessions (last 1-3 sessions, full insights)
  - Tier 2: Mid-range (sessions 4-7, paragraph summaries)
  - Tier 3: Long-term (sessions 8-10, journey arc summary)

**Testing Checklist:**
- [ ] Database migration applies successfully
- [ ] Orchestration script runs after Wave 2
- [ ] All 3 compaction strategies work (switch via env var)
- [ ] Tier compaction logic works for hierarchical
- [ ] Frontend shows loading overlay when roadmap updates
- [ ] Session counter increments correctly (1/10 → 2/10 → ... → 10/10)
- [ ] Roadmap content changes as sessions accumulate
- [ ] Version history stored in roadmap_versions table

---

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

---

## Verification Checklist

After completing all phases, verify:

**Phase 4:**
- [ ] "Stop Processing" button halts pipeline
- [ ] "Resume Processing" button continues from last incomplete session
- [ ] Button text changes dynamically based on processing state
- [ ] `POST /api/demo/resume` endpoint works

**Phase 5:**
- [ ] Database migration applied successfully
- [ ] Orchestration script generates roadmaps after Wave 2
- [ ] All 3 compaction strategies work when env var changed
- [ ] Tier compaction logic works for hierarchical strategy
- [ ] 10-session demo completes end-to-end
- [ ] Roadmap content evolves as sessions accumulate
- [ ] Version history persists in roadmap_versions table

---

## User Preferences (From Planning Session)

The user wants:
- **High quality output** (GPT-5.2 for both insights and roadmap)
- **Experimentation** (all 3 compaction strategies, easy to switch)
- **Version history** ("for my own satisfaction" to see how roadmaps evolve)
- **Start/Stop/Resume** button (save API costs, control processing)
- **Spinner overlay** (visual feedback like session cards)

---

## Questions?

If anything is unclear:
1. **First:** Read the full implementation plan (`thoughts/shared/plans/2026-01-11-your-journey-dynamic-roadmap.md`)
2. **Second:** Check existing code patterns (referenced above)
3. **Third:** Read SESSION_LOG.md entries (2026-01-11) for Phases 0-3 context
4. **Last resort:** Ask clarifying questions before proceeding

---

## Start Command

When ready to start, say:

"I've read the implementation plan at `thoughts/shared/plans/2026-01-11-your-journey-dynamic-roadmap.md`. I understand Phases 0-3 are complete (backend infrastructure + frontend integration). Starting with Phase 4: Start/Stop/Resume Button Enhancement."

---

## Additional Notes

**Database Migration:**
- The migration file exists: `backend/supabase/migrations/013_create_roadmap_tables.sql`
- You MUST apply it via Supabase MCP before Phase 5 testing
- Use the `mcp__supabase__apply_migration` tool
- Migration creates both `patient_roadmap` and `roadmap_versions` tables

**Orchestration Integration:**
- Orchestration script should be called after Wave 2 completes
- Can be integrated into `seed_wave2_analysis.py` OR standalone
- Should handle errors gracefully (LLM failures, database errors)
- Should log progress for debugging

**Testing Strategy:**
- After Phase 4: Test button state changes in UI
- After Phase 5: Full end-to-end with 10-session demo
- Test all 3 strategies by changing `ROADMAP_COMPACTION_STRATEGY` env var
- Verify version history by querying `roadmap_versions` table

**Cost Monitoring:**
- Track API costs during testing
- Hierarchical strategy should be ~$0.003-0.004 per generation
- Full context strategy will be most expensive (~$0.014-0.020)
- Progressive strategy should be cheapest (~$0.0025)

---

**Good luck! Execute each phase carefully, verify thoroughly, and follow the detailed implementation plan.** 🚀
