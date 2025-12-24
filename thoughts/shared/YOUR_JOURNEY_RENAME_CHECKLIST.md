# Your Journey Rename - Comprehensive Checklist

**Date:** 2026-01-14
**Status:** Prepared (not yet executed)
**Scope:** Rename ALL "roadmap" / "NotesGoalsCard" references to "Your Journey" / "YourJourneyCard"
**Migration:** Create 014_rename_roadmap_to_your_journey.sql (before Session Bridge migration 015)

---

## Overview

User confirmed: **"This is worth it"** - comprehensive rename from "roadmap" to "Your Journey" across entire codebase.

**Why rename first?**
- Session Bridge planning document already references "Your Journey" throughout
- Avoids confusion between old naming (roadmap) and new naming (Your Journey)
- Migration 014 renames tables/columns before Session Bridge migration 015

**Estimated scope:** ~100+ references across 25+ files

---

## Phase 1: Database Migration (CRITICAL - DO FIRST)

### Migration 014: Rename Roadmap Tables & Columns

**File:** `backend/supabase/migrations/014_rename_roadmap_to_your_journey.sql`

```sql
-- ============================================================
-- Migration 014: Rename Roadmap to Your Journey
-- ============================================================
-- Renames all "roadmap" references to "your_journey" in database
-- This migration runs BEFORE Session Bridge migration (015)
-- ============================================================

-- Step 1: Rename patient_roadmap table
ALTER TABLE patient_roadmap RENAME TO patient_your_journey;

-- Step 2: Rename roadmap_versions table
ALTER TABLE roadmap_versions RENAME TO your_journey_versions;

-- Step 3: Rename indexes (patient_roadmap)
ALTER INDEX idx_roadmap_patient RENAME TO idx_your_journey_patient;
ALTER INDEX idx_roadmap_updated RENAME TO idx_your_journey_updated;

-- Step 4: Rename indexes (roadmap_versions)
ALTER INDEX idx_roadmap_versions_patient RENAME TO idx_your_journey_versions_patient;
ALTER INDEX idx_roadmap_versions_created RENAME TO idx_your_journey_versions_created;

-- Step 5: Update table comments
COMMENT ON TABLE patient_your_journey IS 'Current Your Journey roadmap data for each patient';
COMMENT ON TABLE your_journey_versions IS 'Version history of all Your Journey roadmap generations';

-- Step 6: Rename columns in patient_your_journey
ALTER TABLE patient_your_journey RENAME COLUMN roadmap_data TO journey_data;

-- Step 7: Update column comments
COMMENT ON COLUMN patient_your_journey.journey_data IS 'Your Journey data: {summary, milestones, themes, achievements, next_steps}';
COMMENT ON COLUMN patient_your_journey.metadata IS 'Metadata: {sessions_analyzed: int, total_sessions: int, model_used: str, generation_timestamp: str, last_session_id: uuid, generation_duration_ms: int}';

-- Step 8: Rename columns in your_journey_versions
ALTER TABLE your_journey_versions RENAME COLUMN roadmap_data TO journey_data;

-- Step 9: Update column comments
COMMENT ON COLUMN your_journey_versions.journey_data IS 'Your Journey data for this version';
COMMENT ON COLUMN your_journey_versions.generation_context IS 'Context passed to LLM for debugging (tier1, tier2, tier3, previous_sessions)';

-- Step 10: Verify constraints still work
-- Foreign key constraints should auto-update, but verify:
-- patient_your_journey.patient_id -> patients(id) ON DELETE CASCADE
-- your_journey_versions.patient_id -> patients(id) ON DELETE CASCADE
```

**Apply via Supabase MCP:**
```bash
mcp__supabase__apply_migration(
  name="rename_roadmap_to_your_journey",
  query="<full SQL above>"
)
```

**Verification checklist:**
- [ ] Both tables renamed successfully
- [ ] All 4 indexes renamed successfully
- [ ] Foreign key constraints preserved
- [ ] UNIQUE constraint on (patient_id, version) still enforced
- [ ] Table/column comments updated
- [ ] No errors in Supabase logs

---

## Phase 2: Backend Service Files

### File: `backend/app/services/roadmap_generator.py`

**Rename to:** `backend/app/services/your_journey_generator.py`

**Git command:**
```bash
git mv backend/app/services/roadmap_generator.py backend/app/services/your_journey_generator.py
```

**Changes inside file:**
- [ ] Line 15: Class name `RoadmapGenerator` → `YourJourneyGenerator`
- [ ] Line 18: Docstring "Generates roadmap" → "Generates Your Journey roadmap"
- [ ] Line 30: `get_model_name("roadmap"` → `get_model_name("your_journey"`
- [ ] Line 40: Method `generate_roadmap(` → `generate_journey(`
- [ ] Line 50: Comment "Generate roadmap" → "Generate Your Journey"
- [ ] Line 65: Docstring references "roadmap" → "Your Journey"
- [ ] Line 85: Return dict key `"roadmap"` → `"journey"`
- [ ] Lines 100-120: All method names with "roadmap" → "your_journey"
  - `_build_full_context_roadmap()` → `_build_full_context_journey()`
  - `_build_progressive_context_roadmap()` → `_build_progressive_context_journey()`
  - `_build_hierarchical_context_roadmap()` → `_build_hierarchical_context_journey()`
- [ ] Lines 150-300: All variable names `roadmap_*` → `journey_*`
- [ ] Lines 320-340: All string references "roadmap" → "Your Journey"
- [ ] Lines 342-349: DELETE `estimate_cost()` function entirely
- [ ] Line 169: DELETE usage of `estimate_cost(context, roadmap)` - replace with actual cost

**Import updates needed in other files:**
```python
# OLD:
from app.services.roadmap_generator import RoadmapGenerator

# NEW:
from app.services.your_journey_generator import YourJourneyGenerator
```

---

### File: `backend/app/config/model_config.py`

**Changes:**
- [ ] Line 98: `"roadmap": "gpt-5.2"` → `"your_journey": "gpt-5.2"`
- [ ] Line 112: `"roadmap": {...}` → `"your_journey": {...}`
- [ ] Comment: "Roadmap generation" → "Your Journey generation"

---

### File: `backend/scripts/generate_roadmap.py`

**Rename to:** `backend/scripts/generate_your_journey.py`

**Git command:**
```bash
git mv backend/scripts/generate_roadmap.py backend/scripts/generate_your_journey.py
```

**Changes inside file:**
- [ ] Line 3: Docstring "Generate Roadmap" → "Generate Your Journey"
- [ ] Line 5: Usage comment `generate_roadmap.py` → `generate_your_journey.py`
- [ ] Line 20: Import `RoadmapGenerator` → `YourJourneyGenerator`
- [ ] Line 45: Function `generate_roadmap_for_session(` → `generate_your_journey_for_session(`
- [ ] Line 50: Print "ROADMAP GENERATION" → "YOUR JOURNEY GENERATION"
- [ ] Line 80: Variable `roadmap_result` → `journey_result`
- [ ] Line 85: Table query `"patient_roadmap"` → `"patient_your_journey"`
- [ ] Line 90: Column `roadmap_data` → `journey_data`
- [ ] Lines 100-120: All print messages "roadmap" → "Your Journey"
- [ ] Line 130: Generator instantiation `RoadmapGenerator()` → `YourJourneyGenerator()`
- [ ] Line 140: Method call `generate_roadmap(` → `generate_journey(`
- [ ] Lines 150-180: Variable names `roadmap_*` → `journey_*`
- [ ] Line 200: Table `"roadmap_versions"` → `"your_journey_versions"`
- [ ] Line 210: Table `"patient_roadmap"` → `"patient_your_journey"`
- [ ] Line 220: Column `roadmap_data` → `journey_data`
- [ ] Lines 230-250: All context building function names (if any)
- [ ] Lines 342-349: DELETE `estimate_cost()` function
- [ ] Line 169: DELETE usage of `estimate_cost()`
- [ ] Replace cost with: `"cost": result["cost_info"]["cost"] if result.get("cost_info") else None`
- [ ] Line 400: CLI usage message updated

---

### File: `backend/scripts/seed_wave2_analysis.py`

**Changes:**
- [ ] Line ~440: Variable `roadmap_script` → `journey_script`
- [ ] Line ~441: Script path `"generate_roadmap.py"` → `"generate_your_journey.py"`
- [ ] Line ~445: Print message "Roadmap" → "Your Journey"
- [ ] Line ~446: Comment "roadmap" → "Your Journey"

---

### File: `backend/app/routers/demo.py`

**Changes:**
- [ ] Line ~570: Table query `"patient_roadmap"` → `"patient_your_journey"`
- [ ] Line ~572: Variable `roadmap_response` → `journey_response`
- [ ] Line ~575: Status field `"roadmap_updated_at"` → `"journey_updated_at"`
- [ ] Line ~577: Comment "roadmap" → "Your Journey"

---

### File: `backend/app/main.py`

**Changes:**
- [ ] Line ~80: Endpoint path `/roadmap` → `/your-journey` (BREAKING CHANGE - consider keeping both)
- [ ] Line ~82: Function name `get_roadmap(` → `get_your_journey(`
- [ ] Line ~85: Docstring "roadmap" → "Your Journey"
- [ ] Line ~90: Table query `"patient_roadmap"` → `"patient_your_journey"`
- [ ] Line ~92: Column `roadmap_data` → `journey_data`
- [ ] Line ~95: Return dict key `"roadmap"` → `"journey"`
- [ ] Line ~97: Error message "roadmap" → "Your Journey"

**IMPORTANT:** Consider keeping `/roadmap` as deprecated alias for backwards compatibility:
```python
@app.get("/api/patients/{patient_id}/roadmap")
async def get_roadmap_deprecated(patient_id: str, db=Depends(get_supabase)):
    """DEPRECATED: Use /your-journey instead"""
    return await get_your_journey(patient_id, db)
```

---

## Phase 3: Frontend Files

### File: `frontend/app/patient/components/NotesGoalsCard.tsx`

**Rename to:** `frontend/app/patient/components/YourJourneyCard.tsx`

**Git command:**
```bash
git mv frontend/app/patient/components/NotesGoalsCard.tsx frontend/app/patient/components/YourJourneyCard.tsx
```

**Changes inside file:**
- [ ] Line 10: Component name `NotesGoalsCard` → `YourJourneyCard`
- [ ] Line 15: Export name `NotesGoalsCard` → `YourJourneyCard`
- [ ] Line 25: Variable `roadmapData` → `journeyData`
- [ ] Line 30: Variable `roadmapMetadata` → `journeyMetadata`
- [ ] Line 40: Context field `loadingRoadmap` → `loadingJourney`
- [ ] Line 45: Context field `roadmapRefreshTrigger` → `journeyRefreshTrigger`
- [ ] Line 55: Function name `fetchRoadmap` → `fetchJourney`
- [ ] Line 60: API call `apiClient.getRoadmap(` → `apiClient.getYourJourney(`
- [ ] Line 70: State setter `setRoadmapData` → `setJourneyData`
- [ ] Line 75: State setter `setRoadmapMetadata` → `setJourneyMetadata`
- [ ] Lines 80-100: All variable names with "roadmap" → "journey"
- [ ] Lines 110-150: All string literals "roadmap" → "Your Journey"
- [ ] Line 160: Card title "Notes & Goals" → "Your Journey" (if not already)
- [ ] Lines 200-300: All comments mentioning "roadmap"

---

### File: `frontend/lib/api-client.ts`

**Changes:**
- [ ] Line ~545: Method name `getRoadmap(` → `getYourJourney(`
- [ ] Line ~547: Comment "roadmap" → "Your Journey"
- [ ] Line ~549: Endpoint `/roadmap` → `/your-journey`
- [ ] Line ~555: Return type (update if needed)

**Keep backwards compatibility method:**
```typescript
/**
 * @deprecated Use getYourJourney() instead
 */
async getRoadmap(patientId: string) {
  return this.getYourJourney(patientId);
}
```

---

### File: `frontend/lib/types.ts`

**Changes:**
- [ ] Line ~350: Interface `RoadmapData` → `YourJourneyData`
- [ ] Line ~360: Interface `RoadmapMetadata` → `YourJourneyMetadata`
- [ ] Line ~365: Interface `RoadmapResponse` → `YourJourneyResponse`
- [ ] Line ~370: Property `roadmap` → `journey`
- [ ] All comments mentioning "roadmap"

**Keep type aliases for backwards compatibility:**
```typescript
/** @deprecated Use YourJourneyData */
export type RoadmapData = YourJourneyData;
/** @deprecated Use YourJourneyMetadata */
export type RoadmapMetadata = YourJourneyMetadata;
/** @deprecated Use YourJourneyResponse */
export type RoadmapResponse = YourJourneyResponse;
```

---

### File: `frontend/app/patient/contexts/SessionDataContext.tsx`

**Changes:**
- [ ] Line ~40: Field `roadmapRefreshTrigger` → `journeyRefreshTrigger`
- [ ] Line ~42: Field `setRoadmapRefreshTrigger` → `setJourneyRefreshTrigger`
- [ ] Line ~44: Field `loadingRoadmap` → `loadingJourney`
- [ ] Comments mentioning "roadmap"

---

### File: `frontend/app/patient/lib/usePatientSessions.ts`

**Changes:**
- [ ] Line ~170: State `roadmapRefreshTrigger` → `journeyRefreshTrigger`
- [ ] Line ~172: Setter `setRoadmapRefreshTrigger` → `setJourneyRefreshTrigger`
- [ ] Line ~545: Return field names
- [ ] Line ~547: `loadingRoadmap` → `loadingJourney`
- [ ] Comments mentioning "roadmap"

---

### File: `frontend/app/patient/components/WaveCompletionBridge.tsx`

**Changes:**
- [ ] Line ~165: Console log "Roadmap" → "Your Journey"
- [ ] Line ~167: Variable name if any
- [ ] Line ~169: `setRoadmapRefreshTrigger` → `setJourneyRefreshTrigger`
- [ ] Comments mentioning "roadmap"

---

### File: `frontend/app/patient/page.tsx`

**Changes:**
- [ ] Line ~15: Import `NotesGoalsCard` → `YourJourneyCard`
- [ ] Line ~85: Component usage `<NotesGoalsCard />` → `<YourJourneyCard />`

---

## Phase 4: Documentation Files

### File: `.claude/SESSION_LOG.md`

**Changes:**
- [ ] All session entries mentioning "roadmap" → "Your Journey"
- [ ] PR #3 title: "Your Journey Dynamic Roadmap" (keep "roadmap" in subtitle for context)
- [ ] Technical references: Update where appropriate (e.g., "roadmap_generator.py" → "your_journey_generator.py")
- [ ] Keep historical context intact (don't erase that it was called "roadmap" before)

---

### File: `.claude/CLAUDE.md`

**Changes:**
- [ ] Current Focus section: "roadmap" → "Your Journey"
- [ ] PR #3 references
- [ ] File path references (update to new filenames)

---

### File: `Project MDs/TheraBridge.md`

**Changes:**
- [ ] Feature name: "Dynamic Roadmap" → "Your Journey"
- [ ] All technical references
- [ ] API endpoint documentation
- [ ] Database table names

---

### File: `thoughts/shared/DECISIONS_AND_FEATURES.md`

**Changes:**
- [ ] Line ~45: "NotesGoalsCard" → "Your Journey card"
- [ ] Line ~130: "NotesGoalsCard" → "Your Journey"
- [ ] All references to component name

---

### File: `thoughts/shared/plans/2026-01-14-session-bridge-backend-integration.md`

**Changes:**
- [ ] Already updated with "Your Journey" references
- [ ] Verify no remaining "roadmap" references (except in historical context)
- [ ] Update context building section if needed

---

## Phase 5: Wave 3 Logging Update

### File: `backend/app/services/your_journey_generator.py` (after rename)

**Add logging calls:**
```python
# At start of generation:
_log_analysis_start(session_id=str(patient_id), wave="your_journey", retry_count=0)

# On success:
_log_analysis_complete(
    session_id=str(patient_id),
    wave="your_journey",
    processing_duration_ms=cost_info.duration_ms
)

# On failure:
_log_analysis_failure(
    session_id=str(patient_id),
    wave="your_journey",
    error_message=str(error),
    retry_count=0
)
```

**Need to import logging functions from analysis_orchestrator or create shared utility.**

---

## Phase 6: Update analysis_processing_log Constraint

### File: Migration 014 (add to end)

```sql
-- Update wave column constraint to include "your_journey"
ALTER TABLE analysis_processing_log DROP CONSTRAINT IF EXISTS check_wave;
ALTER TABLE analysis_processing_log ADD CONSTRAINT check_wave
  CHECK (wave IN ('mood', 'topics', 'breakthrough', 'deep', 'your_journey', 'session_bridge'));
```

---

## Phase 7: Environment Variables (if any)

**Check for:**
- [ ] `.env` files with "ROADMAP" variables
- [ ] `frontend/.env.local` with "ROADMAP" variables
- [ ] Railway environment variables

**Note:** Currently no environment variables use "roadmap" - verify this.

---

## Testing Checklist

### Backend Tests
- [ ] Run backend server: `python -m uvicorn app.main:app --reload`
- [ ] Test endpoint: `GET /api/patients/{id}/your-journey` returns data
- [ ] Verify database queries work with new table names
- [ ] Test generation script: `python scripts/generate_your_journey.py <patient_id> <session_id>`
- [ ] Verify logs in Railway console
- [ ] Check `analysis_processing_log` for "your_journey" wave entries
- [ ] Verify cost tracking writes to `generation_costs` table with task="your_journey"

### Frontend Tests
- [ ] Build frontend: `npm run build`
- [ ] Verify no TypeScript errors
- [ ] Test YourJourneyCard renders
- [ ] Test empty state shows correctly
- [ ] Test loading state works
- [ ] Test error state works
- [ ] Test API integration fetches data
- [ ] Test SSE triggers refresh
- [ ] Verify console logs show "Your Journey" (not "roadmap")

### Database Tests
- [ ] Verify tables renamed: `patient_your_journey`, `your_journey_versions`
- [ ] Verify indexes renamed
- [ ] Verify foreign keys still work
- [ ] Verify UNIQUE constraint still enforced
- [ ] Query old data from new tables
- [ ] Insert new data into new tables
- [ ] Verify migrations folder shows 014 applied

### End-to-End Tests
- [ ] Upload session → Wait for Wave 2 → Verify Your Journey generates
- [ ] Check card updates automatically
- [ ] Verify version history saves to `your_journey_versions`
- [ ] Check Railway logs for generation messages
- [ ] Verify no errors in browser console
- [ ] Test on production (Railway deployment)

---

## Rollback Plan

If issues arise after rename:

1. **Revert migration 014:**
   ```sql
   -- Revert all table renames back to original names
   ALTER TABLE patient_your_journey RENAME TO patient_roadmap;
   ALTER TABLE your_journey_versions RENAME TO roadmap_versions;
   -- (continue with all index and column reverts)
   ```

2. **Revert git commits:**
   ```bash
   git log --oneline  # Find commit hashes for rename
   git revert <hash1> <hash2> <hash3>
   ```

3. **Restore old filenames:**
   ```bash
   git mv backend/app/services/your_journey_generator.py backend/app/services/roadmap_generator.py
   git mv backend/scripts/generate_your_journey.py backend/scripts/generate_roadmap.py
   git mv frontend/app/patient/components/YourJourneyCard.tsx frontend/app/patient/components/NotesGoalsCard.tsx
   ```

---

## Execution Order

**CRITICAL:** Follow this exact order:

1. **Commit current work** - Ensure clean git state
2. **Create migration 014** - Database rename SQL
3. **Apply migration 014** - via Supabase MCP
4. **Verify migration** - Check Supabase tables
5. **Rename backend files** - Service, script, config
6. **Update backend imports** - All files importing renamed modules
7. **Update backend string references** - Table names, column names, variables
8. **Delete estimate_cost()** - From your_journey_generator.py
9. **Test backend** - Run server, test endpoint, test script
10. **Rename frontend files** - Component file
11. **Update frontend imports** - All files importing renamed component
12. **Update frontend string references** - Variables, types, comments
13. **Test frontend** - Build, run dev server, test in browser
14. **Update docs** - SESSION_LOG, CLAUDE, TheraBridge, plans
15. **Test end-to-end** - Full flow from upload to display
16. **Deploy to Railway** - Push to main branch
17. **Verify production** - Test live deployment

---

## Completion Criteria

**All items checked = rename complete:**

- [ ] Migration 014 applied successfully
- [ ] All 3 backend files renamed (service, script, config)
- [ ] All 1 frontend file renamed (component)
- [ ] All imports updated (backend + frontend)
- [ ] All table references updated
- [ ] All variable names updated
- [ ] All string literals updated
- [ ] All comments updated
- [ ] All docs updated
- [ ] estimate_cost() deleted
- [ ] Wave 3 logging uses "your_journey"
- [ ] Backend tests pass
- [ ] Frontend builds without errors
- [ ] End-to-end tests pass
- [ ] Production deployment verified
- [ ] No console errors
- [ ] No TypeScript errors
- [ ] No broken API calls

**Estimated time:** 2-3 hours (if done carefully with testing at each step)

---

## Notes

**User confirmed:** "This is worth it" - comprehensive rename justified by:
1. Better UX terminology ("Your Journey" > "roadmap")
2. Aligns with patient-facing dashboard language
3. Session Bridge planning already uses "Your Journey" terminology
4. Avoids confusion in future development

**Breaking changes:**
- API endpoint: `/roadmap` → `/your-journey` (keep deprecated alias)
- Database tables: `patient_roadmap` → `patient_your_journey`
- TypeScript interfaces: `RoadmapData` → `YourJourneyData` (keep type aliases)

**Non-breaking:**
- Add deprecated aliases for backwards compatibility
- Keep historical context in SESSION_LOG.md
- Document migration path for any external consumers
