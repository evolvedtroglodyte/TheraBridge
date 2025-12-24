# PR #3 Testing Plan - Your Journey Dynamic Roadmap

## Plan Metadata
- **Phase:** PR #3 Testing
- **Created:** 2026-01-11
- **Status:** Ready for Execution
- **Type:** Testing & Verification

## Context

All implementation for PR #3 (Phases 0-5) is complete. This plan systematically tests and verifies all features work correctly before production deployment.

**What's been built:**
- Database migration (patient_roadmap + roadmap_versions tables)
- Backend orchestration script with 3 compaction strategies
- Frontend integration with polling and loading states
- Start/Stop/Resume button with smart resume logic

## Testing Tasks

### Task 1: Database Schema Verification
**Verify database tables exist and schema is correct**

**Steps:**
1. Use `mcp__supabase__list_tables` to verify both tables exist
2. Use `mcp__supabase__execute_sql` to check column structure for patient_roadmap
3. Use `mcp__supabase__execute_sql` to check column structure for roadmap_versions
4. Verify indexes exist (idx_roadmap_patient, idx_roadmap_updated, etc.)

**Success criteria:**
- Both tables present in database
- All columns match migration spec
- All indexes created successfully

**Files to check:**
- `backend/supabase/migrations/013_create_roadmap_tables.sql`

---

### Task 2: Backend Service Code Review
**Review implementation quality of core services**

**Steps:**
1. Review `backend/app/services/roadmap_generator.py` (545 lines)
   - Verify all 3 compaction strategies implemented
   - Check error handling and validation
   - Verify JSON schema validation
2. Review `backend/app/services/session_insights_summarizer.py` (127 lines)
   - Check prompt engineering for insight extraction
   - Verify OpenAI API integration
3. Review `backend/scripts/generate_roadmap.py` (400 lines)
   - Check 5-step orchestration logic
   - Verify database insert/upsert operations
   - Check logging and error handling

**Success criteria:**
- All services follow established patterns
- Error handling is comprehensive
- Logging provides adequate visibility
- Code is production-ready

**Files to review:**
- `backend/app/services/roadmap_generator.py`
- `backend/app/services/session_insights_summarizer.py`
- `backend/scripts/generate_roadmap.py`
- `backend/app/config/model_config.py`

---

### Task 3: API Endpoint Verification
**Verify all new endpoints are implemented correctly**

**Steps:**
1. Check `/api/demo/status` includes new fields:
   - `processing_state`
   - `roadmap_updated_at`
   - `can_resume`
2. Check `/api/demo/stop` endpoint exists
3. Check `/api/demo/resume` endpoint exists
4. Verify `/api/patients/{patientId}/roadmap` endpoint exists
5. Review endpoint implementations in `backend/app/routers/demo.py`

**Success criteria:**
- All endpoints present in code
- Response structures match frontend expectations
- Error handling is appropriate

**Files to check:**
- `backend/app/routers/demo.py`
- `backend/app/routers/patients.py` (for roadmap endpoint)

---

### Task 4: Frontend Component Review
**Review frontend implementation quality**

**Steps:**
1. Review `NotesGoalsCard.tsx` implementation
   - Check empty state handling
   - Check loading state handling
   - Check error handling
   - Verify modal functionality
   - Check accessibility (focus trap, escape key)
2. Review API client `getRoadmap()` method
3. Review SessionDataContext updates (patientId, loadingRoadmap)
4. Check polling logic in `usePatientSessions.ts`

**Success criteria:**
- Component follows established patterns
- Error states handled gracefully
- Loading states provide good UX
- Accessibility requirements met

**Files to review:**
- `frontend/app/patient/components/NotesGoalsCard.tsx`
- `frontend/lib/api-client.ts`
- `frontend/app/patient/lib/usePatientSessions.ts`
- `frontend/components/NavigationBar.tsx` (Stop/Resume button)

---

### Task 5: Local Backend Testing
**Test backend endpoints locally**

**Steps:**
1. Start backend server: `cd backend && source venv/bin/activate && uvicorn app.main:app --reload`
2. Test POST /api/demo/initialize - verify creates patient + sessions
3. Test GET /api/demo/status - verify includes new fields
4. Monitor logs for Wave 1 completion
5. Monitor logs for Wave 2 completion + roadmap generation
6. Test GET /api/patients/{patientId}/roadmap - verify returns roadmap data
7. Test POST /api/demo/stop - verify processes terminate
8. Test POST /api/demo/resume - verify smart resume logic

**Success criteria:**
- All endpoints return expected responses
- Roadmap generation triggers after Wave 2
- Logs show 5-step orchestration
- Database contains roadmap data

**Environment setup:**
- Ensure `ROADMAP_COMPACTION_STRATEGY=hierarchical` (default)
- Ensure OpenAI API key is set

---

### Task 6: Compaction Strategy Testing
**Test all 3 compaction strategies produce valid output**

**Steps:**
1. Test hierarchical strategy (default):
   - Set `ROADMAP_COMPACTION_STRATEGY=hierarchical`
   - Run 10-session demo
   - Verify roadmap generates after each Wave 2
   - Check logs for tier compaction messages
   - Verify cost is ~$0.003-0.004 per generation
2. Test progressive strategy:
   - Set `ROADMAP_COMPACTION_STRATEGY=progressive`
   - Run new demo (different patient)
   - Verify roadmap evolves with each session
   - Verify cost is ~$0.0025 per generation
3. Test full context strategy:
   - Set `ROADMAP_COMPACTION_STRATEGY=full`
   - Run new demo
   - Verify all previous data included
   - Verify cost is ~$0.014-0.020 per generation

**Success criteria:**
- All 3 strategies generate valid roadmaps
- Cost estimates match actual costs
- No errors in logs for any strategy
- Output quality is appropriate for each strategy

**Files to monitor:**
- Backend logs (Railway or local)
- Database `roadmap_versions` table (metadata->compaction_strategy)

---

### Task 7: Database Data Verification
**Verify database contains correct data after test runs**

**Steps:**
1. Query `roadmap_versions` table for test patient:
   ```sql
   SELECT version, metadata->>'sessions_analyzed',
          metadata->>'compaction_strategy', cost,
          generation_duration_ms
   FROM roadmap_versions
   WHERE patient_id = '<test-patient-id>'
   ORDER BY version;
   ```
2. Verify 10 rows exist (one per session)
3. Verify versions increment correctly (1, 2, 3, ..., 10)
4. Verify sessions_analyzed increments (1, 2, 3, ..., 10)
5. Query `patient_roadmap` table:
   ```sql
   SELECT metadata->>'sessions_analyzed',
          metadata->>'total_sessions',
          updated_at
   FROM patient_roadmap
   WHERE patient_id = '<test-patient-id>';
   ```
6. Verify latest roadmap reflects 10/10 sessions

**Success criteria:**
- Version history is complete and accurate
- Latest roadmap is up-to-date
- Metadata fields are populated correctly
- Timestamps are reasonable

**Tools:**
- `mcp__supabase__execute_sql` for queries

---

### Task 8: Frontend Integration Testing
**Test frontend displays roadmap correctly**

**Steps:**
1. Start frontend: `cd frontend && npm run dev`
2. Navigate to patient dashboard
3. Verify "Your Journey" card shows empty state initially
4. Click "Initialize Demo" or load existing demo patient
5. Monitor card for loading overlay when roadmap generates
6. Verify roadmap content displays after first Wave 2 (~60s)
7. Verify session counter shows "Based on 1 out of 10 uploaded sessions"
8. Wait for Session 2 Wave 2 to complete
9. Verify loading overlay appears again
10. Verify roadmap updates with new content
11. Verify counter shows "2 out of 10"
12. Test expanded modal view
13. Test Stop/Resume button flow

**Success criteria:**
- Loading states appear at correct times
- Roadmap content updates after each Wave 2
- Session counter increments correctly
- Modal works properly
- Stop/Resume button changes states correctly

**Browser testing:**
- Check Network tab for API polling
- Check Console for errors
- Verify localStorage persistence

---

### Task 9: Stop/Resume Flow Testing
**Verify Stop/Resume button works end-to-end**

**Steps:**
1. Start new demo
2. Wait for Session 3 to start processing
3. Click "Stop Processing" button
4. Verify button turns green "Resume Processing"
5. Verify processing actually stops (check logs)
6. Verify `GET /api/demo/status` returns `processing_state: "stopped"`
7. Wait 30 seconds (confirm no new sessions process)
8. Click "Resume Processing"
9. Verify button returns to red "Stop Processing"
10. Verify processing continues from incomplete session
11. Verify roadmap generation resumes after Wave 2
12. Let all 10 sessions complete
13. Verify button shows "Processing Complete" (gray, disabled)

**Success criteria:**
- Stop actually terminates processes
- Resume detects incomplete sessions correctly
- Roadmap generation resumes properly
- Final state is correct (Processing Complete)

**Files to monitor:**
- Backend logs for process termination/restart
- Frontend Network tab for status polling

---

### Task 10: Performance & Cost Analysis
**Measure actual performance and costs**

**Steps:**
1. Run full 10-session demo with hierarchical strategy
2. Record generation_duration_ms for each roadmap generation
3. Calculate average generation time
4. Record cost for each generation from logs
5. Calculate total cost for 10 sessions
6. Compare against estimates:
   - Hierarchical: ~$0.003-0.004 per generation
   - Total with roadmap: ~$0.77 for 10 sessions
7. Check for any timeouts (60s limit)
8. Verify all generations complete successfully

**Success criteria:**
- Average generation time < 20 seconds
- No timeouts occur
- Actual costs match estimates (±20%)
- All 10 roadmaps generate successfully

**Data sources:**
- Database `roadmap_versions` table
- Backend logs
- OpenAI API dashboard (optional)

---

## Testing Summary Template

After completing all tasks, create summary:

```markdown
# PR #3 Testing Summary

## Test Results

### Database Schema ✅/❌
- Tables created: ✅/❌
- Schema correct: ✅/❌
- Indexes present: ✅/❌

### Backend Services ✅/❌
- RoadmapGenerator: ✅/❌
- SessionInsightsSummarizer: ✅/❌
- Orchestration script: ✅/❌

### API Endpoints ✅/❌
- /api/demo/status: ✅/❌
- /api/demo/stop: ✅/❌
- /api/demo/resume: ✅/❌
- /api/patients/{id}/roadmap: ✅/❌

### Frontend Components ✅/❌
- NotesGoalsCard: ✅/❌
- API client integration: ✅/❌
- Polling logic: ✅/❌
- Stop/Resume button: ✅/❌

### Compaction Strategies ✅/❌
- Hierarchical: ✅/❌
- Progressive: ✅/❌
- Full context: ✅/❌

### Integration Testing ✅/❌
- End-to-end flow: ✅/❌
- Stop/Resume flow: ✅/❌
- Database persistence: ✅/❌

### Performance ✅/❌
- Generation time: avg Xms ✅/❌
- Cost accuracy: ✅/❌
- No timeouts: ✅/❌

## Issues Found

List any bugs, issues, or deviations discovered during testing.

## Recommendations

List any recommendations for improvements or follow-up work.

## Sign-off

- [ ] All critical tests passed
- [ ] No blockers for production deployment
- [ ] Documentation is accurate
- [ ] Ready to deploy to Railway
```

---

## Deviation Handling

If issues are discovered during testing:

1. **Critical bugs** (prevent deployment):
   - Fix immediately
   - Document in testing summary
   - Re-test affected areas

2. **Minor bugs** (cosmetic, non-blocking):
   - Log to ISSUES.md
   - Continue testing
   - Fix in follow-up PR

3. **Performance issues**:
   - Document metrics
   - Assess if blocking
   - Recommend optimizations

4. **Documentation errors**:
   - Fix inline
   - Update relevant .md files

---

## Success Criteria

- [ ] All 10 tasks completed
- [ ] No critical bugs found
- [ ] Database schema verified
- [ ] All endpoints functional
- [ ] Frontend displays correctly
- [ ] All 3 compaction strategies work
- [ ] Stop/Resume flow works
- [ ] Performance meets expectations
- [ ] Testing summary created
- [ ] Ready for production deployment
