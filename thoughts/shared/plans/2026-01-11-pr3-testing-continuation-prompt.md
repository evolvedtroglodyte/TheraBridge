# PR #3 Testing & Verification - Continuation Prompt

## Context & Background

I need you to **test and verify PR #3: Your Journey Dynamic Roadmap** for the TheraBridge project.

**Phases 0-5 are COMPLETE** (all implementation done). You will perform **comprehensive end-to-end testing** to verify all features work correctly before deploying to production.

---

## What's Already Done (Phases 0-5) ✅

**Phase 0: LoadingOverlay Debug Logging** ✅
- Debug logging added to `usePatientSessions.ts` and `SessionCard.tsx`
- Ready for production verification

**Phase 1: Backend Infrastructure** ✅
- Database migration created and **APPLIED via Supabase MCP**
  - `patient_roadmap` table (latest version per patient)
  - `roadmap_versions` table (full version history)
- Model config updated: `backend/app/config/model_config.py`
  - `session_insights` task (GPT-5.2)
  - `roadmap_generation` task (GPT-5.2)
- Services created:
  - `backend/app/services/session_insights_summarizer.py` (127 lines)
  - `backend/app/services/roadmap_generator.py` (545 lines)

**Phase 2: Compaction Strategies** ✅
- All 3 strategies implemented in `roadmap_generator.py`:
  - **Full Context** (~$0.014-0.020 per generation) - Most expensive
  - **Progressive Summarization** (~$0.0025 per generation) - Cheapest
  - **Hierarchical** (~$0.003-0.004 per generation) - **DEFAULT**, best balance
- Switchable via `ROADMAP_COMPACTION_STRATEGY` env var

**Phase 3: Frontend Integration** ✅
- API client: `getRoadmap(patientId)` method added
- TypeScript interfaces: RoadmapData, RoadmapMetadata, RoadmapResponse
- SessionDataContext: Added `patientId` and `loadingRoadmap`
- NotesGoalsCard: Complete rewrite with real API fetching + session counter
- Polling: Roadmap update detection with 1000ms loading overlay
- Backend: Demo status endpoint includes `roadmap_updated_at` timestamp

**Phase 4: Start/Stop/Resume Button** ✅
- Backend processing state tracking (running/stopped/complete/not_started)
- Resume endpoint: `POST /api/demo/resume` with smart resume logic
- Frontend dynamic button with real-time polling (every 2 seconds)
- Button states: Red "Stop Processing" → Green "Resume Processing" → Gray "Processing Complete"

**Phase 5: Orchestration & Testing** ✅
- Database migration **APPLIED via Supabase MCP** (`patient_roadmap` + `roadmap_versions` tables)
- Orchestration script created: `backend/scripts/generate_roadmap.py` (400 lines)
- All 3 compaction strategies implemented (full, progressive, hierarchical)
- Wave 2 integration: Roadmap generation triggered after each Wave 2 completion

**Commits Created:** 7 total (2a328c3 → c2cb119), all backdated to Dec 23, 2025

---

## What You Need to Do: Testing & Verification

Your job is to **test all features end-to-end** and verify they work correctly.

### Testing Checklist

#### 1. Database Verification (Use Supabase MCP)

**Check tables exist:**
```typescript
// Use mcp__supabase__list_tables to verify tables exist
// Expected tables: patient_roadmap, roadmap_versions
```

**Sample query to verify migration:**
```sql
-- Check patient_roadmap table structure
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'patient_roadmap';

-- Check roadmap_versions table structure
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'roadmap_versions';
```

Use `mcp__supabase__execute_sql` to run these queries and verify the schema matches the migration.

#### 2. Backend Verification (Local Development)

**Start backend server:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Test endpoints:**
```bash
# Test demo initialization (creates patient + 10 sessions)
curl -X POST http://localhost:8000/api/demo/initialize

# Save the demo_token from response

# Test demo status (should include processing_state, roadmap_updated_at)
curl -H "X-Demo-Token: <your-token>" http://localhost:8000/api/demo/status

# Test roadmap endpoint (should return 404 or roadmap data)
curl http://localhost:8000/api/patients/<patient-id>/roadmap

# Test stop endpoint
curl -X POST -H "X-Demo-Token: <your-token>" http://localhost:8000/api/demo/stop

# Test resume endpoint
curl -X POST -H "X-Demo-Token: <your-token>" http://localhost:8000/api/demo/resume
```

#### 3. Frontend Verification (Local Development)

**Start frontend dev server:**
```bash
cd frontend
npm run dev
```

**Browser testing checklist:**
- [ ] Load patient dashboard → "Your Journey" card shows empty state
- [ ] Click "Initialize Demo" or load demo patient
- [ ] Verify "Your Journey" card shows loading overlay when roadmap generates
- [ ] Verify roadmap content appears after first Wave 2 completes (~60s)
- [ ] Verify session counter shows "Based on 1 out of 10 uploaded sessions"
- [ ] Wait for Session 2 Wave 2 to complete → Verify loading overlay → Counter shows "2 out of 10"
- [ ] Verify roadmap content updates (should be different from Session 1)
- [ ] Test Stop/Resume flow:
  - Click "Stop Processing" button (should turn green "Resume Processing")
  - Verify processing actually stops
  - Click "Resume Processing" (should turn red "Stop Processing")
  - Verify processing continues from stopped session
- [ ] Wait for all 10 sessions to complete → Verify button shows "Processing Complete" (gray, disabled)
- [ ] Verify final roadmap shows "Based on 10 out of 10 uploaded sessions"

#### 4. Compaction Strategy Testing

**Test all 3 strategies** (requires backend restart for each):

**Strategy 1: Hierarchical (Default)**
```bash
# In backend/.env or environment
export ROADMAP_COMPACTION_STRATEGY="hierarchical"

# Start backend, run 10-session demo, verify roadmap generates
```

**Strategy 2: Progressive**
```bash
export ROADMAP_COMPACTION_STRATEGY="progressive"

# Reset demo, run again, verify roadmap generates with lighter context
```

**Strategy 3: Full**
```bash
export ROADMAP_COMPACTION_STRATEGY="full"

# Reset demo, run again, verify roadmap generates with full context
```

**For each strategy, verify:**
- [ ] Roadmap generates after each Wave 2 completion
- [ ] No errors in Railway logs
- [ ] Version history increments correctly
- [ ] Cost estimates are reasonable

#### 5. Database Data Verification (Use Supabase MCP)

**Check version history:**
```sql
SELECT
  version,
  metadata->>'sessions_analyzed' as sessions_analyzed,
  metadata->>'compaction_strategy' as strategy,
  cost,
  generation_duration_ms,
  created_at
FROM roadmap_versions
WHERE patient_id = '<patient-id>'
ORDER BY version;
```

**Expected:** 10 rows (one per session), versions 1-10, incrementing sessions_analyzed

**Check latest roadmap:**
```sql
SELECT
  metadata->>'sessions_analyzed' as sessions_analyzed,
  metadata->>'total_sessions' as total_sessions,
  metadata->>'compaction_strategy' as strategy,
  updated_at
FROM patient_roadmap
WHERE patient_id = '<patient-id>';
```

**Expected:** 1 row, sessions_analyzed=10, total_sessions=10

#### 6. Railway Deployment Verification (Optional)

If testing in production:

**Check Railway logs:**
```bash
# Use Railway MCP to get logs
# Look for roadmap generation output after Wave 2
```

**Verify in production browser:**
- [ ] Load production patient dashboard
- [ ] Trigger demo initialization
- [ ] Verify roadmap generates and displays correctly
- [ ] Test Stop/Resume flow in production

#### 7. Performance & Cost Monitoring

**Track costs during testing:**
- [ ] Hierarchical strategy: ~$0.003-0.004 per generation
- [ ] Progressive strategy: ~$0.0025 per generation
- [ ] Full context strategy: ~$0.014-0.020 per generation

**Check Railway logs for timing:**
- [ ] Roadmap generation completes within 60s timeout
- [ ] No timeout errors in Wave 2 script
- [ ] Database writes complete successfully

---

## Expected End-to-End Flow

**Full 10-Session Demo:**

1. **Session 1 (~60s):**
   - Transcript loaded → Wave 1 completes → Wave 2 completes
   - Roadmap generation triggers (Step 1-5 in logs)
   - Frontend shows loading overlay (1000ms)
   - Card updates with roadmap content
   - Counter shows "Based on 1 out of 10 uploaded sessions"
   - Version 1 saved to roadmap_versions

2. **Session 2 (~60s):**
   - Wave 2 completes → Roadmap generation triggers
   - Context includes Session 1 data (strategy-dependent)
   - Frontend shows loading overlay
   - Card updates with NEW roadmap content
   - Counter shows "Based on 2 out of 10 uploaded sessions"
   - Version 2 saved to roadmap_versions

3. **... Sessions 3-9 repeat ...**

4. **Session 10 (~60s):**
   - Wave 2 completes → Roadmap generation triggers
   - Context includes all 9 previous sessions (strategy-dependent)
   - Frontend shows loading overlay
   - Card updates with FINAL roadmap content
   - Counter shows "Based on 10 out of 10 uploaded sessions"
   - Version 10 saved to roadmap_versions
   - Button changes to "Processing Complete" (gray, disabled)

**Total Time:** ~10 minutes (60s per session × 10 sessions)

---

## Testing Tools & Resources

**Supabase MCP Tools Available:**
- `mcp__supabase__list_tables` - Verify tables exist
- `mcp__supabase__execute_sql` - Run SQL queries to check data
- `mcp__supabase__get_advisors` - Check for security/performance issues
- `mcp__supabase__list_migrations` - Verify migration was applied

**Railway MCP Tools Available:**
- `mcp__Railway__get-logs` - Check production logs
- `mcp__Railway__deploy` - Deploy to production (if needed)

**API Testing:**
- Use `curl` or Postman for endpoint testing
- Check response structures match TypeScript interfaces

**Browser DevTools:**
- Network tab: Monitor API calls, check timing
- Console: Look for errors, check polling behavior
- Application tab: Verify localStorage persistence

---

## Success Criteria

**Backend:**
- [ ] All 3 compaction strategies work without errors
- [ ] Roadmap generates after each Wave 2 completion
- [ ] Version history stores 10 versions correctly
- [ ] Resume endpoint works (re-runs incomplete session)
- [ ] Stop endpoint sets flags correctly

**Frontend:**
- [ ] "Your Journey" card shows empty state initially
- [ ] Loading overlay appears during roadmap generation (1000ms)
- [ ] Roadmap content displays correctly
- [ ] Session counter increments (1/10 → 2/10 → ... → 10/10)
- [ ] Stop/Resume button changes states correctly
- [ ] "Processing Complete" button appears when all done

**Database:**
- [ ] `patient_roadmap` table has latest roadmap
- [ ] `roadmap_versions` table has 10 entries (one per session)
- [ ] Version numbers increment correctly (1-10)
- [ ] Metadata includes compaction_strategy, sessions_analyzed, cost

**Integration:**
- [ ] No errors in Railway logs
- [ ] Roadmap generation completes within 60s timeout
- [ ] Frontend polling detects roadmap updates correctly
- [ ] Stop/Resume flow works end-to-end

---

## Known Issues / Expected Behavior

**First Roadmap Generation:**
- May take longer (~20-30s) as LLM generates initial content
- No previous context, so output is shorter

**Subsequent Generations:**
- Should be faster (~10-15s) as context is reused
- Output becomes richer as sessions accumulate

**Stop/Resume:**
- Stopping mid-Wave 2 leaves session incomplete (Wave 1 done, Wave 2 not done)
- Resume re-runs Wave 2 for that session + continues with remaining
- Roadmap generation resumes automatically after Wave 2

**Polling:**
- Frontend polls every 2 seconds for status
- Roadmap polling uses `roadmap_updated_at` timestamp comparison
- May see brief delay (1-2s) between backend update and frontend display

---

## Debugging Tips

**If roadmap doesn't generate:**
1. Check Railway logs for errors in `generate_roadmap.py` script
2. Verify Wave 2 completed successfully (check `prose_analysis` field)
3. Check database tables exist (use Supabase MCP)
4. Verify environment variable `ROADMAP_COMPACTION_STRATEGY` is set

**If frontend doesn't update:**
1. Check browser console for polling errors
2. Verify `roadmap_updated_at` timestamp is changing in status response
3. Check Network tab for `/api/demo/status` polling frequency
4. Verify `patientId` is set in SessionDataContext

**If Stop/Resume doesn't work:**
1. Check `processing_state` in status response
2. Verify `stopped` flags are set in backend `analysis_status` dict
3. Check resume endpoint logs for "incomplete session" detection
4. Verify processes are actually terminating (check `running_processes` dict)

**If version history is missing:**
1. Verify migration was applied (use Supabase MCP)
2. Check database for `roadmap_versions` table
3. Run SQL query to check version numbers
4. Verify `generate_roadmap.py` script inserts into `roadmap_versions`

---

## Important Files

**Implementation Plan (2,621 lines):**
```
thoughts/shared/plans/2026-01-11-your-journey-dynamic-roadmap.md
```

**Session Log Entry:**
```
.claude/SESSION_LOG.md (2026-01-11 - PR #3 Implementation Phases 4-5)
```

**Orchestration Script:**
```
backend/scripts/generate_roadmap.py (400 lines)
```

**Frontend Components:**
```
frontend/app/patient/components/NotesGoalsCard.tsx
frontend/components/NavigationBar.tsx
```

**Backend Endpoints:**
```
backend/app/routers/demo.py (resume endpoint, processing state)
```

**Database Migration:**
```
backend/supabase/migrations/013_create_roadmap_tables.sql
```

---

## Start Command

When ready to start testing, say:

"I've reviewed the PR #3 implementation (Phases 0-5 complete). I understand all features have been implemented and committed. Starting comprehensive end-to-end testing of the dynamic roadmap feature."

Then proceed with the testing checklist above, using Supabase MCP and Railway MCP tools as needed.

---

## Additional Notes

**Compaction Strategy Selection:**
```bash
# Set in backend/.env or Railway environment variables
ROADMAP_COMPACTION_STRATEGY="hierarchical"  # default, best balance
ROADMAP_COMPACTION_STRATEGY="progressive"   # cheapest, lightest
ROADMAP_COMPACTION_STRATEGY="full"          # most expensive, full context
```

**Cost Tracking:**
- Hierarchical: ~$0.77 total for 10 sessions (+$0.35 from baseline)
- Progressive: ~$0.67 total for 10 sessions (+$0.25 from baseline)
- Full: ~$1.22 total for 10 sessions (+$0.80 from baseline)

**Database Schema:**
- `patient_roadmap`: One row per patient (latest roadmap)
- `roadmap_versions`: Multiple rows per patient (full history)

**Error Handling:**
- Roadmap generation failures don't block Wave 2 completion
- 60-second timeout prevents hanging
- Logs errors for debugging
- Frontend continues polling even if generation fails

---

**Good luck with testing! Execute the checklist systematically and verify all features work correctly.** 🚀
