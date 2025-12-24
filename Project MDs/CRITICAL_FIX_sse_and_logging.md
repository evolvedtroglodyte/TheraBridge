# CRITICAL FIX: SSE Event Queue + Railway Logging

**Date:** 2025-12-30
**Priority:** CRITICAL - System appears broken to users
**Impact:** Session analysis completes but UI never updates, 90% of logs invisible

---

## Executive Summary

The session analysis system has **two critical bugs**:

1. **SSE events never reach frontend** - subprocess writes to isolated memory queue
2. **90% of Railway logs invisible** - missing stdout flush on detailed progress logs

**User Experience Impact:**
- Demo initialization appears to hang (no visible progress)
- Session cards never show analysis results (even though data IS in database)
- Impossible to debug in production (logs don't show)

**Backend Reality:**
- Analysis completes successfully in 30-40 seconds
- All data written to database correctly
- Scripts work perfectly when run manually

---

## Issue #1: SSE Subprocess Event Queue Isolation

### Root Cause

**The Problem:**
```python
# backend/app/utils/pipeline_logger.py:31
_event_queue: Dict[str, list] = {}  # IN-MEMORY, PER-PROCESS

# backend/app/routers/demo.py:128-134
result = subprocess.run([python_exe, str(script_path), patient_id], ...)
# ☝️ Creates NEW Python process with SEPARATE _event_queue

# backend/app/routers/sse.py:42
events = PipelineLogger.get_events(patient_id)
# ☝️ Reads from FastAPI process's _event_queue (always empty)
```

**What Happens:**
1. FastAPI receives `/api/demo/initialize`
2. Spawns subprocess to run `seed_wave1_analysis.py`
3. Subprocess creates `PipelineLogger`, writes events to ITS `_event_queue`
4. Frontend connects to SSE at `/api/sse/events/{patient_id}`
5. SSE reads from FastAPI process's `_event_queue` → **always empty**
6. Frontend never receives wave1_complete/wave2_complete events
7. UI never knows to refresh and show analysis results

**Evidence:**
- Session log (Dec 30) notes: "CRITICAL BUG DISCOVERED: PipelineLogger uses in-memory queue, but seed scripts run in subprocess"
- Railway logs show "Step 2/3 Complete" but frontend SSE receives nothing
- Database HAS the analysis data, proving scripts completed successfully

### Solution Options

#### Option A: Database-Backed Event Queue (RECOMMENDED)
**Pros:**
- Survives process boundaries
- Persists across deployments
- Can query historical events
- Scales to multiple workers

**Cons:**
- Requires migration
- Slightly slower than memory

**Implementation:**
```sql
-- Migration: 012_add_pipeline_events_table.sql
CREATE TABLE pipeline_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
  phase VARCHAR(20) NOT NULL,  -- TRANSCRIPT, WAVE1, WAVE2
  event VARCHAR(50) NOT NULL,   -- START, COMPLETE, MOOD_ANALYSIS, etc
  session_id UUID REFERENCES therapy_sessions(id) ON DELETE CASCADE,
  session_date DATE,
  status VARCHAR(20) DEFAULT 'success',
  details JSONB,
  duration_ms NUMERIC(10,2),
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pipeline_events_patient ON pipeline_events(patient_id, created_at);
CREATE INDEX idx_pipeline_events_session ON pipeline_events(session_id);
```

**Code Changes:**
```python
# backend/app/utils/pipeline_logger.py
class PipelineLogger:
    def log_event(self, event: LogEvent, ...):
        # Write to database instead of memory
        db = get_supabase_admin()
        db.table("pipeline_events").insert({
            "patient_id": self.patient_id,
            "phase": self.phase.value,
            "event": event.value,
            "session_id": session_id,
            "session_date": session_date,
            "status": status,
            "details": details,
            "duration_ms": duration_ms
        }).execute()

    @staticmethod
    def get_events(patient_id: str, since: Optional[datetime] = None) -> list:
        db = get_supabase_admin()
        query = db.table("pipeline_events").select("*").eq("patient_id", patient_id)
        if since:
            query = query.gte("created_at", since.isoformat())
        return query.order("created_at").execute().data
```

#### Option B: File-Based Event Queue
**Pros:**
- No migration needed
- Simple implementation

**Cons:**
- Requires file I/O on every event
- Not scalable to multiple workers
- No persistence across container restarts

#### Option C: Redis Event Queue
**Pros:**
- Fast
- Survives process boundaries
- Pub/sub built-in

**Cons:**
- Requires Redis instance (additional infrastructure cost)
- Overkill for current scale

**Recommendation:** **Option A** - Database-backed queue is the right long-term solution.

---

## Issue #2: Missing Railway Logs (90% Not Visible)

### Root Cause

**The Problem:**
Railway buffers Python's `logging.info()` output. Only `print(..., flush=True)` appears in real-time logs.

**Current State:**
```python
# ✅ These appear in Railway logs (have flush=True)
print(f"🚀 Step 2/3: Starting Wave 1 analysis...", flush=True)
print(f"✅ Step 2/3 Complete", flush=True)

# ❌ These DON'T appear in Railway logs (no flush)
logger.info(f"[1/10] Processing session 2025-01-10")  # Buffered!
logger.info(f"  ✓ Mood analysis complete: 6.5/10.0")  # Buffered!
logger.info(f"  ✓ Topic extraction complete")        # Buffered!
```

**What You See in Railway:**
```
🚀 Step 2/3: Starting Wave 1 analysis...
✅ Step 2/3 Complete: Wave 1 analysis complete
```

**What You SHOULD See:**
```
🚀 Step 2/3: Starting Wave 1 analysis...
[1/10] Processing session 2025-01-10
  ✓ Mood analysis complete: 6.5/10.0 (confidence: 0.92)
  ✓ Topic extraction complete: 2 topics, CBT
  ✓ Breakthrough detection complete: true
[2/10] Processing session 2025-01-17
  ✓ Mood analysis complete: 7.2/10.0 (confidence: 0.89)
  ...
[10/10] Processing session 2025-03-20
✅ Step 2/3 Complete: Wave 1 analysis complete
```

### Solution

**Add print statements with flush=True alongside all logger.info() calls in seed scripts.**

**Files to modify:**
1. `backend/scripts/seed_wave1_analysis.py`
2. `backend/scripts/seed_wave2_analysis.py`
3. `backend/scripts/seed_all_sessions.py`

**Pattern to apply:**
```python
# BEFORE:
logger.info(f"[{i+1}/{total}] Processing session {date}")

# AFTER:
logger.info(f"[{i+1}/{total}] Processing session {date}")
print(f"[{i+1}/{total}] Processing session {date}", flush=True)  # Add this!
```

**Locations to add print statements:**

#### seed_wave1_analysis.py
- Line 223: Session start
- Line 86-87: Mood analysis result
- Line 131-132: Topic extraction result
- Line 175-176: Breakthrough detection result
- Line 361: Session complete

#### seed_wave2_analysis.py
- Similar pattern for deep analysis progress

#### seed_all_sessions.py
- Transcript population progress (if not already present)

---

## Implementation Plan

### Phase 1: Fix Railway Logging (Quick Win - 30 minutes)

**Why first:** Gives us visibility into what's actually happening RIGHT NOW.

**Steps:**
1. Add `print(..., flush=True)` to all key progress points in seed scripts
2. Commit and push to Railway
3. Verify Railway logs now show detailed progress

**Expected outcome:** Full visibility into analysis pipeline execution.

### Phase 2: Implement Database Event Queue (2-3 hours)

**Steps:**
1. Create migration `012_add_pipeline_events_table.sql`
2. Apply migration to Supabase
3. Update `PipelineLogger` to write to database
4. Update SSE endpoint to read from database
5. Add event cleanup job (delete events older than 24 hours)
6. Test locally
7. Deploy to Railway

**Expected outcome:** SSE events reach frontend, UI updates in real-time.

### Phase 3: Frontend Independent Session Loading (1 hour)

**Current State:**
Frontend waits for SSE events to trigger refresh. If events don't arrive (due to Issue #1), UI never updates even though data IS in database.

**Solution:**
Add **polling fallback** to session data context:

```typescript
// frontend/app/patient/contexts/SessionDataContext.tsx
useEffect(() => {
  // Poll every 5 seconds during analysis
  const pollInterval = setInterval(() => {
    if (analysisStatus === 'processing') {
      refresh(); // Fetch latest session data from API
    }
  }, 5000);

  return () => clearInterval(pollInterval);
}, [analysisStatus, refresh]);
```

**Why this helps:**
- UI updates even if SSE fails
- Graceful degradation
- Works immediately (no backend changes needed)

---

## Testing Strategy

### Phase 1 Verification (Logging)
```bash
# 1. Deploy with new print statements
git push origin main

# 2. Watch Railway logs
railway logs --follow

# 3. Initialize demo
curl -X POST "https://your-backend.railway.app/api/demo/initialize"

# Expected: See [1/10] through [10/10] session progress in Railway logs
```

### Phase 2 Verification (SSE Events)
```bash
# 1. Connect to SSE endpoint
curl -N "https://your-backend.railway.app/api/sse/events/{patient_id}"

# Expected: Receive wave1_complete and wave2_complete events in real-time
```

### Phase 3 Verification (Frontend)
```bash
# 1. Open frontend
# 2. Initialize demo
# 3. Watch session cards update as analysis completes
# Expected: Mood scores, topics, techniques appear within 40 seconds
```

---

## Rollback Plan

### Phase 1 (Logging)
No rollback needed - adding print statements is safe.

### Phase 2 (Database Events)
```bash
# Revert migration
supabase db reset  # Nuclear option
# OR
DROP TABLE pipeline_events;  # Surgical option

# Revert code
git revert <commit-hash>
git push origin main
```

### Phase 3 (Frontend Polling)
```bash
# Revert frontend changes
git revert <commit-hash>
# Redeploy frontend
```

---

## Success Criteria

**After all phases complete:**

1. **Railway Logs:**
   - ✅ Show detailed progress for every session
   - ✅ Show [1/10] through [10/10] processing
   - ✅ Show mood scores, topics, breakthroughs as they complete

2. **SSE Events:**
   - ✅ Frontend receives wave1_complete events in real-time
   - ✅ Frontend receives wave2_complete events in real-time
   - ✅ Events trigger UI refresh

3. **Frontend UI:**
   - ✅ Session cards show "Analyzing..." during processing
   - ✅ Session cards update with analysis results within 40 seconds
   - ✅ Mood scores, topics, techniques all visible
   - ✅ No manual refresh required

4. **Database:**
   - ✅ All analysis data persists correctly (already working)
   - ✅ pipeline_events table tracks progress
   - ✅ Old events cleaned up automatically

---

## Cost Analysis

### Current State:
- **Developer time:** 2-3 hours per bug report debugging invisible logs
- **User experience:** Appears broken, users report "stuck" initialization
- **Support burden:** High - users think system is broken

### After Fix:
- **Database storage:** ~100 events per demo user × 100 bytes = 10KB per user (negligible)
- **Railway logs:** Increased log volume (still under free tier limits)
- **Developer time:** Near-zero debugging time (full visibility)
- **User experience:** Professional, real-time updates
- **Support burden:** Low - users see progress, understand what's happening

**ROI:** Massive. This fix is worth 10x its implementation cost.

---

## Next Steps

**Immediate (Today):**
1. Implement Phase 1 (logging) - 30 minutes
2. Verify Railway logs show full detail
3. Deploy and test on production

**This Week:**
1. Implement Phase 2 (database events) - 2-3 hours
2. Implement Phase 3 (frontend polling fallback) - 1 hour
3. Full end-to-end testing

**Validation:**
1. Fresh demo initialization
2. Watch Railway logs (should see all 10 sessions)
3. Watch frontend SSE connection (should receive events)
4. Watch session cards (should update with analysis)
5. User testing (does it feel responsive and professional?)

---

## References

- **Session Log Entry:** `.claude/CLAUDE.md` - Dec 30, 2025 - SSE Real-Time Updates Implementation
- **Root Cause:** Subprocess isolation for `_event_queue` dictionary
- **Evidence:** Railway logs show "Complete" but SSE receives no events
- **Database Evidence:** Analysis data IS present, proving scripts work
- **User Reports:** "UI never loads the data even though backend logs say complete"

---

## Appendix: Alternative Quick Fix (If Under Time Pressure)

**If you need something working TODAY and can't do database migration:**

**Option: Polling-Only Mode (No SSE)**

Remove SSE entirely, rely on frontend polling `/api/sessions/patient/{id}` every 5 seconds.

**Pros:**
- Works immediately
- No backend changes needed
- Simple, reliable

**Cons:**
- Less responsive than SSE
- More API calls
- Not "real-time"

**Implementation:**
```typescript
// frontend/app/patient/lib/usePatientSessions.ts
useEffect(() => {
  const interval = setInterval(() => {
    fetch(`/api/sessions/patient/${patientId}`)
      .then(res => res.json())
      .then(data => setSessions(data));
  }, 5000);

  return () => clearInterval(interval);
}, [patientId]);
```

**This gets you 80% of the way there with 5% of the effort.**

But **Phase 1 (logging) + Phase 3 (polling fallback)** can be done in 1 hour and dramatically improves UX.
