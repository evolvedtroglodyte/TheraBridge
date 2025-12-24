# Implementation Handoff Prompt - PR #1 Phase 1C

**Copy this entire prompt into a new Claude Code window to execute the implementation.**

---

## Context

You are implementing **PR #1 Phase 1C: SessionDetail UI Improvements + Wave 1 Action Summarization** for the TheraBridge project. This is a full-stack implementation involving backend (Python/FastAPI), frontend (Next.js/React/TypeScript), and database (PostgreSQL) changes.

**Planning session completed:** 2026-01-07
**Implementation plan:** `thoughts/shared/plans/2026-01-07-sessiondetail-ui-improvements-wave1-action-summarization.md`

---

## Project Overview

**TheraBridge** is an AI-powered therapy session analysis platform that:
- Transcribes therapy sessions using OpenAI Whisper
- Analyzes sessions in two waves:
  - **Wave 1:** Mood analysis, topic extraction, breakthrough detection (parallel)
  - **Wave 2:** Deep clinical analysis + prose generation
- Displays session insights in a patient dashboard

**Tech Stack:**
- **Backend:** FastAPI, PostgreSQL (Supabase), OpenAI GPT-5 series
- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS
- **Deployment:** Railway (backend), Vercel (frontend)

---

## What You're Building

### 6 Major Features:

1. **Numeric mood score display** in SessionDetail (emoji + score like "😊 7.5")
2. **Technique definitions** showing 2-3 sentence explanations below technique names
3. **45-char action items summary** via new Wave 1 LLM call (sequential after topic extraction)
4. **X button** (top-right corner) replacing "Back to Dashboard" button
5. **Theme toggle** in SessionDetail header (next to X button)
6. **SessionCard update** to use condensed action summary as second bullet

### Key Architectural Decisions:

- **Action summarization:** Sequential separate LLM call after topic extraction (preserves quality of verbose action items)
- **Model:** gpt-5-nano ($0.0003/session, total +0.7% cost increase)
- **Mood mapping:** Numeric (0-10) → Categorical (sad/neutral/happy) using existing 3 custom SVG emojis
- **Technique definitions:** Included in API response (no extra calls)
- **Cost impact:** Negligible (+$0.003 per 10-session demo)

---

## Implementation Plan Reference

**CRITICAL:** Read the full implementation plan before starting:

**File:** `thoughts/shared/plans/2026-01-07-sessiondetail-ui-improvements-wave1-action-summarization.md`

This plan contains:
- Complete file-by-file changes with exact line numbers
- Full code snippets for all new files
- Database migration SQL
- Testing procedures
- Rollback instructions

---

## Your Task

Execute the implementation following the plan's 3 phases:

### Phase 1: Backend Changes (45-60 min)

1. **Database Migration**
   - Create `backend/supabase/migrations/010_add_action_items_summary.sql`
   - Add `action_items_summary TEXT` column to `therapy_sessions` table

2. **Action Items Summarizer Service**
   - Create `backend/app/services/action_items_summarizer.py`
   - Implement GPT-5-nano summarization (max 45 chars)
   - Verbose logging matching Wave 1 format (📝 emoji)

3. **Model Configuration**
   - Update `backend/app/config/model_config.py`
   - Add `"action_summary": "gpt-5-nano"` to TASK_MODEL_ASSIGNMENTS

4. **Orchestrator Integration**
   - Update `backend/app/services/analysis_orchestrator.py`
   - Import ActionItemsSummarizer
   - Add `_summarize_action_items()` method
   - Update `_run_wave1()` to call summarization sequentially after core Wave 1

5. **Sessions API Enhancement**
   - Update `backend/app/routers/sessions.py`
   - Import TechniqueLibrary
   - Add technique definition lookup to GET /api/sessions/ response
   - Enrich each session with `technique_definition` field

### Phase 2: Frontend Changes (45-60 min)

1. **Mood Mapper Utility**
   - Create `frontend/lib/mood-mapper.ts`
   - Implement `mapNumericMoodToCategory()` (0-3.5→sad, 4-6.5→neutral, 7-10→happy)
   - Implement `formatMoodScore()` (returns "7.5" or "N/A")

2. **Session Type Updates**
   - Update `frontend/app/patient/lib/types.ts`
   - Add fields: `mood_score`, `mood_confidence`, `mood_rationale`, `mood_indicators`, `emotional_tone`
   - Add fields: `action_items_summary`, `technique_definition`

3. **Frontend Data Mapping**
   - Update `frontend/app/patient/lib/usePatientSessions.ts`
   - Map new backend fields in transformedSessions (lines 235-265)

4. **SessionCard Update**
   - Update `frontend/app/patient/components/SessionCard.tsx`
   - Change line 74 to use `session.action_items_summary` with fallback to `session.actions[0]`

5. **SessionDetail Enhancements**
   - Update `frontend/app/patient/components/SessionDetail.tsx`
   - Import: `mapNumericMoodToCategory`, `formatMoodScore`, `renderMoodEmoji`, `X`, `ThemeToggle`
   - Add mood score section (emoji + numeric score + optional emotional tone)
   - Update technique section to show definition from `session.technique_definition`
   - Replace "Back to Dashboard" button with header containing:
     - Left: "Session Details" title
     - Right: ThemeToggle + X button (top-right corner)

### Phase 3: Testing & Verification (30-45 min)

1. **Database Verification**
   - Connect to Railway Postgres
   - Verify `action_items_summary` column exists
   - Check existing sessions (should be NULL initially)

2. **Backend Logging Verification**
   - Trigger demo pipeline
   - Use Railway MCP to check logs
   - Verify Wave 1 logs show new summarization step with 📝 emoji
   - Confirm log format matches existing Wave 1 patterns

3. **Frontend UI Testing**
   - Test mood score display in SessionDetail
   - Test technique definition display
   - Test X button closes modal correctly
   - Test theme toggle works in SessionDetail
   - Test SessionCard shows 45-char summary
   - Test light/dark mode consistency

4. **Integration Testing**
   - Run full demo pipeline
   - Verify end-to-end data flow
   - Check all edge cases (missing data, null values, etc.)

---

## Critical Git Requirements

**BEFORE making ANY changes:**

1. Check last commit timestamp:
   ```bash
   git log --format="%ci" -n 1
   ```

2. Add 30 seconds to that timestamp (NEVER use a date after Dec 23, 2025 11:45 PM)

3. All commits MUST use backdated timestamps:
   ```bash
   git add -A && \
   GIT_COMMITTER_DATE="2025-12-23 HH:MM:SS -0600" \
   git commit -m "Feature: PR #1 Phase 1C - SessionDetail UI improvements + Wave 1 action summarization" --date="2025-12-23 HH:MM:SS -0600"
   ```

4. Push to remote:
   ```bash
   git push
   ```

**Git User Config:**
- Email: `rohin.agrawal@gmail.com`
- Username: `newdldewdl`

---

## File Locations Reference

### New Files to Create (3):
- `backend/supabase/migrations/010_add_action_items_summary.sql`
- `backend/app/services/action_items_summarizer.py`
- `frontend/lib/mood-mapper.ts`

### Files to Modify (7):
- `backend/app/config/model_config.py`
- `backend/app/services/analysis_orchestrator.py`
- `backend/app/routers/sessions.py`
- `frontend/app/patient/lib/types.ts`
- `frontend/app/patient/lib/usePatientSessions.ts`
- `frontend/app/patient/components/SessionCard.tsx`
- `frontend/app/patient/components/SessionDetail.tsx`

---

## Important Context

### Custom Emojis (SessionIcons.tsx)
The project uses 3 custom SVG emojis (NOT Unicode):
- **HappyEmoji**: Smiling face (lines 38-49)
- **NeutralEmoji**: Straight mouth (lines 52-63)
- **SadEmoji**: Frowning face (lines 66-77)

Colors: Teal (#4ECDC4) in light mode, Purple (#a78bfa) in dark mode

**Usage:** `renderMoodEmoji(moodCategory: string, size: number, isDark: boolean)`

### Wave 1 Architecture
Current Wave 1 runs **3 parallel analyses**:
1. Mood analysis (gpt-5-nano)
2. Topic extraction (gpt-5-mini) - generates 2 action items
3. Breakthrough detection (gpt-5)

**New:** After parallel execution, run **sequential** action summarization:
4. Action items summary (gpt-5-nano) - uses output from #2

### SessionCard Data Flow (Verified Real Data)
```
Backend Wave 1 → Database → API → usePatientSessions (mapping) → SessionCard
- backend.technique → frontend.strategy
- backend.action_items → frontend.actions
```

SessionCard displays:
- First bullet: `session.strategy` (technique name)
- Second bullet: `session.actions[0]` → **UPDATE TO** `session.action_items_summary || session.actions[0]`

---

## Success Criteria

**Backend:**
- [ ] Migration applies successfully (no errors)
- [ ] Action items summarizer generates 45-char phrases
- [ ] Wave 1 logs show summarization step with proper emoji (📝)
- [ ] API returns `action_items_summary` and `technique_definition` fields
- [ ] Railway logs match existing format

**Frontend:**
- [ ] SessionCard displays 45-char summary as second bullet
- [ ] SessionDetail shows numeric mood score with emoji
- [ ] SessionDetail shows technique definitions (2-3 sentences)
- [ ] X button closes modal correctly
- [ ] Theme toggle works in SessionDetail header
- [ ] Light/dark mode consistent across all elements

**Integration:**
- [ ] End-to-end flow works: Wave 1 → DB → API → Frontend
- [ ] All edge cases handled (null values, missing data)
- [ ] No breaking changes to existing functionality
- [ ] Cost increase < 1% verified

---

## Commands to Run

### Backend Server (for testing):
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Frontend Dev Server (for testing):
```bash
cd frontend
npm run dev
```

### Database Migration (via Railway):
```bash
# Connect to Railway project
railway link

# Run migration
railway run python -m alembic upgrade head
```

### Check Railway Logs:
Use the Railway MCP tool:
```typescript
mcp__Railway__get-logs({
  workspacePath: "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend",
  logType: "deploy",
  lines: 200,
  filter: "Wave 1",
  json: false
})
```

---

## Rollback Plan

If issues arise:

1. **Database:** Column is additive, safe to leave
2. **Backend:** Comment out summarization call in `_run_wave1()`
3. **Frontend:** Revert SessionCard to use `session.actions[0]`
4. **Git:** `git revert <commit-hash>`

---

## Final Notes

- **Read the full implementation plan** in `thoughts/shared/plans/2026-01-07-sessiondetail-ui-improvements-wave1-action-summarization.md` before starting
- **Follow the plan exactly** - it has detailed code snippets and line numbers
- **Test incrementally** - verify each phase before moving to the next
- **Update documentation** after completion (SESSION_LOG.md, CLAUDE.md)
- **Ask questions** if anything is unclear in the plan

**Estimated time:** 2-3 hours total

---

## Start Implementation

Begin with Phase 1 (Backend), following the detailed implementation plan. Good luck! 🚀
