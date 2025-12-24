# Production Fix Prompt - PR #1 Phase 1C Critical Blockers

**Copy this entire prompt into a new Claude Code window to fix the 3 critical blockers discovered during production testing.**

---

## Context

You are fixing **3 CRITICAL BLOCKERS** discovered during production testing of **PR #1 Phase 1C: SessionDetail UI Improvements + Wave 1 Action Summarization**.

**Testing completed:** 2026-01-08
**Full test report:** `thoughts/shared/PRODUCTION_TEST_RESULTS_2026-01-08.md`
**Original implementation plan:** `thoughts/shared/plans/2026-01-07-sessiondetail-ui-improvements-wave1-action-summarization.md`

---

## Project Overview

**TheraBridge** is an AI-powered therapy session analysis platform:
- Transcribes therapy sessions using OpenAI Whisper
- Analyzes sessions in two waves:
  - **Wave 1:** Mood analysis, topic extraction, action items, breakthrough detection (parallel + sequential)
  - **Wave 2:** Deep clinical analysis + prose generation
- Displays session insights in a patient dashboard

**Tech Stack:**
- **Backend:** FastAPI, PostgreSQL (Supabase), OpenAI GPT-5 series
- **Frontend:** Next.js 16, React 19, TypeScript, Tailwind CSS
- **Deployment:** Railway (backend + frontend)

**Repository Structure:**
```
peerbridge proj/
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── services/          # Analysis services (mood, topics, action summarizer, etc.)
│   │   ├── routers/           # API endpoints (sessions.py)
│   │   └── database.py
│   ├── scripts/
│   │   └── seed_wave1_analysis.py  ← FIX BLOCKER #2 HERE
│   └── supabase/
│       └── migrations/        # Database migrations
├── frontend/                  # Next.js frontend
│   └── app/patient/           # Patient dashboard
└── thoughts/shared/           # Documentation and plans
```

---

## What Was Implemented (Phase 1C)

**6 Major Features:**
1. Numeric mood score display in SessionDetail (emoji + score like "😊 7.5")
2. Technique definitions showing 2-3 sentence explanations
3. **45-char action items summary** via new Wave 1 LLM call (sequential after topic extraction)
4. X button (top-right corner) replacing "Back to Dashboard" button
5. Theme toggle in SessionDetail header
6. SessionCard update to use condensed action summary as second bullet

**Implementation Complete:**
- ✅ Backend: `ActionItemsSummarizer` service created (`backend/app/services/action_items_summarizer.py`)
- ✅ Backend: Sequential summarization logic added to `AnalysisOrchestrator._run_wave1()`
- ✅ Backend: Sessions API enriched with technique definitions
- ✅ Database: `action_items_summary` TEXT column added (migration applied)
- ✅ Frontend: All UI components updated (SessionCard, SessionDetail, mood mapper, types)

---

## 🚨 BLOCKER #1: Missing `breakthrough_history` Table

### Problem

**Severity:** CRITICAL - Breaks entire application

**Symptoms:**
- Sessions API returns 500 Internal Server Error
- Frontend cannot load session data
- Error: `"Could not find the table 'public.breakthrough_history' in the schema cache"`

**Evidence from Railway Logs:**
```python
ERROR: Exception in ASGI application
postgrest.exceptions.APIError: {
  'code': 'PGRST205',
  'message': "Could not find the table 'public.breakthrough_history' in the schema cache"
}
```

**Root Cause:**
- `app/routers/sessions.py` references a table `breakthrough_history` that doesn't exist
- No migration exists to create this table
- Database schema verification (via Supabase MCP) confirms table is missing

**Impact:**
- ❌ Frontend completely inaccessible
- ❌ All Phase 1C features untestable
- ❌ Production application unusable

### Your Task

**Investigate and fix the missing table reference:**

1. **Step 1: Find the Reference**
   ```bash
   # Search for breakthrough_history references
   grep -rn "breakthrough_history" backend/app/routers/sessions.py
   ```

2. **Step 2: Determine Fix Approach**

   **Option A: Remove the Reference** (Recommended if table is unused)
   - Comment out or remove the `breakthrough_history` query in `sessions.py`
   - This is likely a leftover reference from old code

   **Option B: Create the Table** (Only if actually needed)
   - Check if `breakthrough_history` is actually used elsewhere
   - Create migration to add the table
   - Apply migration via Supabase MCP

3. **Step 3: Test the Fix**
   ```bash
   # Test the sessions API endpoint
   curl -s "https://therabridge-backend.up.railway.app/api/sessions/patient/{patient_id}"
   # Should return 200 OK with session data (not 500 error)
   ```

4. **Step 4: Deploy and Verify**
   - Commit changes (backdated to Dec 23, 2025)
   - Push to Railway
   - Verify API returns 200 status code

**Expected Outcome:**
- ✅ Sessions API returns 200 OK (not 500 error)
- ✅ Frontend can load session data
- ✅ No references to non-existent tables

---

## 🚨 BLOCKER #2: Action Summarizer Not Called in Seed Script

### Problem

**Severity:** HIGH - Core Phase 1C feature not functioning

**Symptoms:**
- Database `action_items_summary` column shows NULL for all sessions
- Railway logs show NO "📝 Generating action items summary..." messages
- Frontend falls back to full action items (loses 45-char condensed display)

**Evidence from Database:**
```json
{
  "action_items": [
    "Respect parents' request for space now (do not contact them immediately)",
    "Prioritize basic self-care: eat regular meals, rest, and use Jordan/support"
  ],
  "action_items_summary": null  // ❌ EXPECTED: "Respect space & prioritize self-care"
}
```

**Root Cause:**

The `seed_wave1_analysis.py` script runs Wave 1 analyses but **does NOT import or call** `ActionItemsSummarizer`:

```python
# scripts/seed_wave1_analysis.py (current implementation)
from app.services.mood_analyzer import MoodAnalyzer
from app.services.topic_extractor import TopicExtractor
from app.services.breakthrough_detector import BreakthroughDetector
# ❌ ActionItemsSummarizer NOT imported!

async def analyze_session(session):
    # Parallel execution (mood, topics, breakthrough)
    mood = await mood_analyzer.analyze(session)
    topics = await topic_extractor.extract(session)
    breakthrough = await breakthrough_detector.detect(session)

    # Update database with 3 results
    # ❌ ActionItemsSummarizer NEVER CALLED!
```

**Expected Behavior (from AnalysisOrchestrator):**
```python
async def _run_wave1(session):
    # Step 1: Parallel (mood, topics, breakthrough)
    results = await asyncio.gather(...)

    # Step 2: Sequential (action summarization)
    summary = await action_items_summarizer.summarize(action_items)  ← MISSING!

    # Update database with summary
```

**Impact:**
- ❌ No action summaries generated during demo pipeline
- ❌ SessionCard shows full action items (not 45-char phrases)
- ❌ Frontend loses key Phase 1C feature

### Your Task

**Update seed script to call ActionItemsSummarizer sequentially:**

1. **Step 1: Read the Current Seed Script**
   ```bash
   # Read the full seed_wave1_analysis.py script
   cat backend/scripts/seed_wave1_analysis.py
   ```

2. **Step 2: Add ActionItemsSummarizer Import**
   ```python
   # Add to imports section (around line 32-34)
   from app.services.action_items_summarizer import ActionItemsSummarizer, ActionItemsSummary
   ```

3. **Step 3: Add Sequential Summarization Logic**

   Find the section where Wave 1 results are processed (after parallel execution completes).

   Add this logic **AFTER** topic extraction completes:

   ```python
   # After parallel analyses complete and action_items are extracted

   # NEW: Sequential action summarization (if 2 action items exist)
   action_items_summary = None
   if action_items and len(action_items) == 2:
       try:
           logger.info(f"📝 Generating action items summary for session {session_id}...")

           summarizer = ActionItemsSummarizer()
           summary_result = await summarizer.summarize_action_items(
               action_items=action_items,
               session_id=str(session_id)
           )

           action_items_summary = summary_result.summary

           logger.info(
               f"✅ Action items summary complete: "
               f"'{action_items_summary}' ({summary_result.character_count} chars)"
           )

       except Exception as e:
           logger.error(f"❌ Action items summarization failed: {str(e)}")
           # Continue without summary (non-blocking)
   ```

4. **Step 4: Update Database Write**

   Find where the database update happens (likely using Supabase client).

   Add `action_items_summary` to the update payload:

   ```python
   # Update database with Wave 1 results
   update_data = {
       "mood_score": mood_score,
       "mood_confidence": mood_confidence,
       # ... other fields ...
       "action_items_summary": action_items_summary,  # ← ADD THIS
       # ... rest of fields ...
   }

   db.table("therapy_sessions").update(update_data).eq("id", session_id).execute()
   ```

5. **Step 5: Test Locally**
   ```bash
   # Run seed script with a test patient ID
   python backend/scripts/seed_wave1_analysis.py <patient_id>

   # Check logs for:
   # - "📝 Generating action items summary..."
   # - "✅ Action items summary complete: 'xyz' (43 chars)"
   ```

6. **Step 6: Verify in Database**
   ```sql
   -- Check if summaries are populated
   SELECT id, action_items, action_items_summary
   FROM therapy_sessions
   WHERE patient_id = '<patient_id>'
   LIMIT 5;

   -- Expected: action_items_summary NOT NULL
   ```

7. **Step 7: Deploy and Test in Production**
   - Commit changes (backdated to Dec 23, 2025)
   - Push to Railway
   - Trigger new demo pipeline
   - Monitor Railway logs for "📝" emoji and summary logs
   - Verify database has populated summaries

**Expected Outcome:**
- ✅ Railway logs show "📝 Generating action items summary..." for each session
- ✅ Railway logs show "✅ Action items summary complete: 'xyz' (N chars)"
- ✅ Database `action_items_summary` column populated (not NULL)
- ✅ SessionCard displays 45-char summaries as second bullet

---

## 🚨 BLOCKER #3: Frontend UI Testing

### Problem

**Severity:** CRITICAL - All Phase 1C features untestable

**Cause:** Blocker #1 (API returns 500 error, frontend cannot load data)

**Impact:**
Cannot verify any of the 6 Phase 1C UI features:
1. ❌ Numeric mood score display (emoji + score)
2. ❌ Technique definitions (2-3 sentences)
3. ❌ 45-char action items summary
4. ❌ X button (top-right corner)
5. ❌ Theme toggle in SessionDetail header
6. ❌ SessionCard action summary (2nd bullet)

### Your Task

**This blocker will be automatically resolved after fixing Blocker #1.**

After fixing Blocker #1:
1. Verify frontend loads at `https://therabridge.up.railway.app`
2. Trigger new demo pipeline
3. Wait for Wave 1 completion (~60 seconds)
4. Open SessionDetail and verify all 6 features work

**Expected Outcome:**
- ✅ Frontend loads successfully (no 500 errors)
- ✅ SessionCard shows action summary as second bullet
- ✅ SessionDetail shows mood score with emoji
- ✅ SessionDetail shows technique definitions
- ✅ X button and theme toggle work correctly

---

## Testing Checklist

After implementing all 3 fixes, verify the following:

### Backend Tests

- [ ] Sessions API returns 200 OK (not 500 error)
  ```bash
  curl -s -w "\nHTTP:%{http_code}\n" \
    "https://therabridge-backend.up.railway.app/api/sessions/patient/{patient_id}"
  # Expected: HTTP:200
  ```

- [ ] Railway logs show action summarization
  ```bash
  railway logs --filter "action items summary"
  # Expected: Multiple log entries with 📝 emoji
  ```

- [ ] Database has populated summaries
  ```sql
  SELECT action_items_summary FROM therapy_sessions LIMIT 5;
  # Expected: All rows have non-NULL summaries (45 chars max)
  ```

### Frontend Tests

- [ ] **Test 1: SessionCard - Action Summary**
  - Second bullet shows 45-char summary (not full action items)
  - Example: "Practice TIPP & schedule psychiatrist"

- [ ] **Test 2: SessionDetail - Mood Score**
  - Numeric score displays with emoji (e.g., "😊 7.5")
  - Correct emoji based on score (sad: 0-4, neutral: 4.1-6.5, happy: 6.6-10)

- [ ] **Test 3: SessionDetail - Technique Definition**
  - Definition displays below technique name (2-3 sentences)
  - No placeholder text "This therapeutic approach was applied..."

- [ ] **Test 4: SessionDetail - X Button**
  - Top-right corner has X icon button
  - Clicking X closes modal and returns to sessions grid

- [ ] **Test 5: SessionDetail - Theme Toggle**
  - Theme toggle button next to X button
  - Clicking toggle switches light ↔ dark mode

- [ ] **Test 6: Light/Dark Mode Consistency**
  - All features work in both light and dark mode
  - Custom emojis change color (teal → purple)

---

## Implementation Order

**Follow this order to maximize efficiency:**

1. **Fix Blocker #1 FIRST** (Missing table)
   - This unblocks the frontend immediately
   - Allows you to test Blocker #2 fix visually

2. **Fix Blocker #2 SECOND** (Action summarizer)
   - Requires code changes + deployment
   - Can be tested independently

3. **Verify Blocker #3 RESOLVED** (Frontend testing)
   - Should work automatically after #1 is fixed
   - Run full UI test checklist

---

## Important Notes

### Git Commit Rules

**ALL commits must be backdated to December 23, 2025.**

Before EVERY commit:
```bash
# 1. Check last commit timestamp
git log --format="%ci" -n 1

# 2. Add 30 seconds to that timestamp

# 3. Create backdated commit
git add -A && \
GIT_COMMITTER_DATE="2025-12-23 HH:MM:SS -0600" \
git commit -m "message" --date="2025-12-23 HH:MM:SS -0600"
```

**Git Config:**
- Email: `rohin.agrawal@gmail.com`
- Username: `newdldewdl`

### Commit Message Format

Use clear, descriptive commit messages:
```
fix(pr1-phase1c): Remove breakthrough_history table reference from sessions API

- Removed query to non-existent breakthrough_history table
- Fixes 500 error preventing frontend from loading session data
- Blocker #1 from production testing (PRODUCTION_TEST_RESULTS_2026-01-08.md)
```

### Railway Deployment

After committing fixes:
```bash
# Push to trigger Railway deployment
git push origin main

# Check deployment status
cd backend && railway status

# Monitor logs during deployment
railway logs --filter "error"
```

### Testing in Production

After deployment, test with a **NEW** demo pipeline (don't reuse old patient IDs):
```bash
# Trigger fresh demo
curl -X POST https://therabridge-backend.up.railway.app/api/demo/initialize

# Use the new patient_id returned in response for testing
```

---

## Reference Documentation

**Original Implementation Plan:**
- `thoughts/shared/plans/2026-01-07-sessiondetail-ui-improvements-wave1-action-summarization.md`
- Contains complete file-by-file specifications
- Includes data flow diagrams and architecture decisions

**Production Test Report:**
- `thoughts/shared/PRODUCTION_TEST_RESULTS_2026-01-08.md`
- Full test methodology and results
- Evidence for all 3 blockers
- Database queries and Railway log samples

**Key Files to Modify:**

1. **For Blocker #1:**
   - `backend/app/routers/sessions.py` (remove table reference)

2. **For Blocker #2:**
   - `backend/scripts/seed_wave1_analysis.py` (add action summarizer call)

3. **For Verification:**
   - Railway logs (check for 📝 emoji logs)
   - Supabase database (verify action_items_summary populated)
   - Frontend at https://therabridge.up.railway.app

---

## Success Criteria

**All 3 blockers must be resolved:**

✅ **Blocker #1 Fixed:**
- Sessions API returns 200 OK (not 500)
- Frontend loads session data successfully
- No errors about missing tables

✅ **Blocker #2 Fixed:**
- Railway logs show "📝 Generating action items summary..." for each session
- Database `action_items_summary` column populated (not NULL)
- Summaries are 45 characters or less

✅ **Blocker #3 Resolved:**
- All 6 Phase 1C UI features verified:
  - Mood score + emoji displays correctly
  - Technique definitions show below technique names
  - Action summaries appear as second bullet in SessionCard
  - X button closes SessionDetail modal
  - Theme toggle switches light/dark mode
  - All features work in both themes

---

## After Fixes Are Complete

1. **Re-run Full Production Test Plan**
   - Follow steps in `PRODUCTION_TEST_RESULTS_2026-01-08.md`
   - Verify all tests pass

2. **Update Documentation**
   - Update `.claude/CLAUDE.md` with fix completion status
   - Update `.claude/SESSION_LOG.md` with fix details
   - Mark blockers as resolved

3. **Create Fix Summary Report**
   - Document what was changed
   - Include before/after evidence (logs, database queries)
   - Save to `thoughts/shared/PRODUCTION_FIX_SUMMARY_2026-01-08.md`

4. **Ready for Merge**
   - All tests passing
   - Documentation updated
   - PR #1 Phase 1C ready for final merge

---

## Need Help?

**Check these resources:**

- **Implementation Plan:** How Phase 1C was originally implemented
  - `thoughts/shared/plans/2026-01-07-sessiondetail-ui-improvements-wave1-action-summarization.md`

- **Test Report:** What exactly failed and why
  - `thoughts/shared/PRODUCTION_TEST_RESULTS_2026-01-08.md`

- **AnalysisOrchestrator:** Reference for correct action summarization logic
  - `backend/app/services/analysis_orchestrator.py` (lines 400-470)

- **ActionItemsSummarizer:** Service implementation
  - `backend/app/services/action_items_summarizer.py`

- **Existing Session API:** Pattern for querying sessions
  - `backend/app/routers/sessions.py`

---

## Get Started

1. Read this entire prompt carefully
2. Review the production test report for detailed evidence
3. Start with Blocker #1 (sessions API fix)
4. Then fix Blocker #2 (seed script update)
5. Test thoroughly in production
6. Document your fixes

Good luck! 🚀
