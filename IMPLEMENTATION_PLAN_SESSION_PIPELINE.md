# TherapyBridge Session Pipeline Fix - Implementation Plan

**Date:** 2025-12-28
**Status:** Ready for Implementation

---

## Overview

Fix the session data pipeline on Railway to populate demo sessions with transcripts and AI-generated analysis. Currently, demo initialization creates 10 empty sessions but background tasks fail to populate them with data.

---

## Current State Analysis

### What Works:
- ✅ `seed_demo_v4()` SQL function creates 10 sessions with correct dates
- ✅ Backend `/api/sessions/` endpoint returns sessions from database
- ✅ Frontend displays session cards with dates
- ✅ All AI services exist and work (mood analyzer, topic extractor, etc.)

### What's Broken:
- ❌ Background tasks don't execute on Railway (scripts can't find JSON files)
- ❌ Transcripts remain empty (`[]`)
- ❌ No AI analysis data (topics, summary, mood all NULL)
- ❌ Frontend shows placeholder data instead of real sessions

### Key Discoveries:
- **Railway Deployment:** Only `/backend` folder is deployed (Root Directory = `/backend`)
- **Mock Data Location:** `mock-therapy-data/sessions/*.json` is at repo root (NOT deployed to Railway)
- **Working Reference:** Commit `21730f7` had working vertical integration fetching Session 1 from database
- **Database State:** 50+ sessions exist, most empty except 5 with hardcoded crisis intake data

---

## Desired End State

When a user initializes demo:
1. **Immediate:** 10 sessions created with correct dates
2. **0-30 seconds:** Transcripts populated from JSON files
3. **30-180 seconds:** Wave 1 analysis completes (mood, topics, summary)
4. **180-480 seconds:** Wave 2 analysis completes (deep insights)
5. **Result:** Frontend displays 10 fully populated session cards with real data

**Verification:**
- Visit `https://therabridge.up.railway.app`
- Click "Try Demo"
- Wait ~3 minutes
- All 10 session cards show: mood emoji, topics, strategy, summary
- Click any session → full transcript loads

---

## What We're NOT Doing

- ❌ Not adding task queues (Celery, Redis) - background tasks are sufficient for demo
- ❌ Not changing database schema - all fields already exist
- ❌ Not modifying AI services - they work correctly
- ❌ Not changing Railway configuration (root directory stays `/backend`)
- ❌ Not duplicating data - JSON files moved once, scripts read from new location

---

## Implementation Approach

**Strategy:** Move mock data into backend deployment, keep existing Python scripts that read JSON files.

**Why this approach:**
- Minimal code changes (just update file paths)
- Data stays in GitHub (single source of truth)
- Scripts already work (tested locally in commit history)
- No Railway config changes needed

---

## Phase 1: Move Mock Data into Backend Deployment

### Overview
Relocate `mock-therapy-data/` directory into `backend/` so Railway deployment includes the JSON files.

### Changes Required:

#### 1.1 Move Directory Structure

**Command:**
```bash
mv mock-therapy-data backend/mock-therapy-data
```

**Result:**
```
backend/
├── app/
├── scripts/
├── mock-therapy-data/    ← MOVED HERE
│   └── sessions/
│       ├── session_01_crisis_intake.json
│       ├── session_02_emotional_regulation.json
│       └── ... (10 files total)
├── requirements.txt
└── ...
```

#### 1.2 Update .gitignore (if needed)

**File:** `backend/.gitignore`

**Check:** Ensure `mock-therapy-data/` is NOT ignored. If it's listed, remove that line.

#### 1.3 Update seed_all_sessions.py Path Resolution

**File:** `backend/scripts/seed_all_sessions.py`

**Change:** Lines 58-59 (path calculation)

**Before:**
```python
# Find the mock-therapy-data directory (should be at repo root)
repo_root = Path(__file__).parent.parent.parent
sessions_dir = repo_root / "mock-therapy-data" / "sessions"
```

**After:**
```python
# Find the mock-therapy-data directory (now in backend/)
backend_root = Path(__file__).parent.parent
sessions_dir = backend_root / "mock-therapy-data" / "sessions"
```

### Success Criteria:

#### Automated Verification:
- [ ] Directory move completes: `ls backend/mock-therapy-data/sessions/*.json` returns 10 files
- [ ] Git tracking updated: `git status` shows move operation
- [ ] Script path resolves: `python backend/scripts/seed_all_sessions.py --help` (should not crash with import error)

#### Manual Verification:
- [ ] Commit and push changes to GitHub
- [ ] Verify files appear in GitHub web UI at `backend/mock-therapy-data/sessions/`
- [ ] Railway deployment succeeds (check deployment logs)

**Implementation Note:** After completing this phase, verify Railway deployment builds successfully before proceeding to Phase 2. Check Railway logs to confirm mock-therapy-data files are included in deployment.

---

## Phase 2: Fix Background Task Execution

### Overview
Update demo router background tasks to use absolute paths that work in Railway's deployment environment.

### Changes Required:

#### 2.1 Add Path Import to demo.py

**File:** `backend/app/routers/demo.py`

**Change:** Add to imports section (top of file)

```python
from pathlib import Path
```

#### 2.2 Fix populate_session_transcripts_background()

**File:** `backend/app/routers/demo.py:61-87`

**Change:** Replace lines 66-72

**Before:**
```python
# Get Python executable from current environment
python_exe = sys.executable

# Run transcript population script
result = subprocess.run(
    [python_exe, "backend/scripts/seed_all_sessions.py", patient_id],
    capture_output=True,
    text=True,
    timeout=300  # 5 minute timeout
)
```

**After:**
```python
# Get Python executable from current environment
python_exe = sys.executable

# Resolve absolute path to script
script_path = Path(__file__).parent.parent.parent / "scripts" / "seed_all_sessions.py"

logger.info(f"Running transcript population: {python_exe} {script_path} {patient_id}")

# Run transcript population script
result = subprocess.run(
    [python_exe, str(script_path), patient_id],
    capture_output=True,
    text=True,
    timeout=300  # 5 minute timeout
)
```

#### 2.3 Fix run_wave1_analysis_background()

**File:** `backend/app/routers/demo.py:89-114`

**Change:** Replace lines 94-99

**Before:**
```python
# Get Python executable from current environment
python_exe = sys.executable

# Run Wave 1 script
result = subprocess.run(
    [python_exe, "backend/scripts/seed_wave1_analysis.py", patient_id],
    capture_output=True,
```

**After:**
```python
# Get Python executable from current environment
python_exe = sys.executable

# Resolve absolute path to script
script_path = Path(__file__).parent.parent.parent / "scripts" / "seed_wave1_analysis.py"

logger.info(f"Running Wave 1 analysis: {python_exe} {script_path} {patient_id}")

# Run Wave 1 script
result = subprocess.run(
    [python_exe, str(script_path), patient_id],
    capture_output=True,
```

#### 2.4 Fix run_wave2_analysis_background()

**File:** `backend/app/routers/demo.py:116-141`

**Change:** Replace lines 121-126

**Before:**
```python
# Get Python executable from current environment
python_exe = sys.executable

# Run Wave 2 script
result = subprocess.run(
    [python_exe, "backend/scripts/seed_wave2_analysis.py", patient_id],
    capture_output=True,
```

**After:**
```python
# Get Python executable from current environment
python_exe = sys.executable

# Resolve absolute path to script
script_path = Path(__file__).parent.parent.parent / "scripts" / "seed_wave2_analysis.py"

logger.info(f"Running Wave 2 analysis: {python_exe} {script_path} {patient_id}")

# Run Wave 2 script
result = subprocess.run(
    [python_exe, str(script_path), patient_id],
    capture_output=True,
```

### Success Criteria:

#### Automated Verification:
- [ ] Python syntax valid: `python -m py_compile backend/app/routers/demo.py`
- [ ] No import errors: `cd backend && python -c "from app.routers.demo import router"`
- [ ] Backend starts: `cd backend && uvicorn app.main:app --reload` (check startup logs for errors)

#### Manual Verification:
- [ ] Deploy to Railway
- [ ] Initialize demo via frontend
- [ ] Check Railway logs for:
  - ✅ `Running transcript population: ...` log message
  - ✅ `✅ Session transcripts populated for patient {uuid}` success message
  - ✅ `Running Wave 1 analysis: ...` log message
  - ✅ `✅ Wave 1 analysis complete for patient {uuid}` success message
  - ✅ No Python exceptions or file not found errors
- [ ] Wait 5 minutes after demo init
- [ ] Refresh frontend
- [ ] Verify session cards show populated data (not empty)

**Implementation Note**: If background tasks still fail, use debug endpoint `/api/debug/populate-transcripts/{patient_id}` to get detailed error output. The synchronous debug endpoint will show exact errors that background tasks silently swallow.

---

## Phase 3: Verify End-to-End Pipeline

### Overview
Test the complete demo initialization → data population → frontend display flow on Railway production.

### Testing Steps:

#### 3.1 Test Demo Initialization

**Action:** Initialize new demo from frontend

**URL:** `https://therabridge.up.railway.app`

**Steps:**
1. Open browser DevTools (Network tab)
2. Click "Try Demo" button
3. Verify `POST /api/demo/initialize` returns 200 with session IDs
4. Note the `patient_id` from response

**Expected:**
- Response includes `demo_token`, `patient_id`, `session_ids` (array of 10 UUIDs)
- `analysis_status: "processing"`

#### 3.2 Monitor Railway Logs

**Action:** Watch Railway backend logs in real-time

**Railway Dashboard:** Backend Service → Deployments → View Logs

**Expected Log Sequence:**
```
[Timestamp] 📝 Populating session transcripts for patient {uuid}
[Timestamp] Running transcript population: /usr/local/bin/python /app/scripts/seed_all_sessions.py {uuid}
[Timestamp] [1/10] Processing session_01_crisis_intake.json...
[Timestamp] ✓ Loaded: 45 segments, 55 minutes
[Timestamp] ✓ Updated session 2025-01-10
...
[Timestamp] ✅ Session transcripts populated for patient {uuid}
[Timestamp] 🚀 Starting Wave 1 analysis for patient {uuid}
[Timestamp] Running Wave 1 analysis: /usr/local/bin/python /app/scripts/seed_wave1_analysis.py {uuid}
[Timestamp] [1/10] Processing session 2025-01-10 (...)
[Timestamp]   ✓ Mood analysis complete: 6.5/10.0 (confidence: 0.85)
[Timestamp]   ✓ Topic extraction complete: 2 topics, CBT - Cognitive Restructuring
...
[Timestamp] ✅ Wave 1 analysis complete for patient {uuid}
[Timestamp] 🚀 Starting Wave 2 analysis for patient {uuid}
...
[Timestamp] ✅ Wave 2 analysis complete for patient {uuid}
```

**Failure Indicators:**
- ❌ `FileNotFoundError: [Errno 2] No such file or directory`
- ❌ `❌ Transcript population failed:`
- ❌ Python stack traces with import errors

#### 3.3 Verify Database Population

**Action:** Query Supabase database directly

**Using Supabase SQL Editor:**
```sql
-- Get latest demo patient sessions
SELECT
  id,
  session_date,
  array_length(transcript, 1) as transcript_segments,
  topics,
  technique,
  mood_score,
  summary
FROM therapy_sessions
WHERE patient_id = '{patient_id_from_step_3.1}'
ORDER BY session_date;
```

**Expected Result:** 10 rows with:
- `transcript_segments`: 30-50 (not NULL or 0)
- `topics`: `["Topic 1", "Topic 2"]` (not NULL)
- `technique`: "MODALITY - TECHNIQUE" (not NULL)
- `mood_score`: 5.0-8.5 (not NULL)
- `summary`: Text summary (not NULL or empty)

#### 3.4 Verify Frontend Display

**Action:** Test session cards in dashboard

**URL:** `https://therabridge.up.railway.app/patient/dashboard-v3`

**Expected Display:**
- **Session Card 1 (Jan 10):**
  - Date: "Jan 10"
  - Mood: 😔 or 😐 (based on mood_score)
  - Topic: "Crisis Support" or similar
  - Strategy: "TIPP Skills" or similar
  - Summary: 2-sentence summary
  - Star icon if breakthrough detected

- **Session Cards 2-10:** Similar populated data

**Not Expected:**
- Empty topics: `[]`
- Placeholder summary: "Summary not yet generated"
- Empty strategy: "Not yet analyzed"

#### 3.5 Test Session Detail Modal

**Action:** Click on Session 1 card

**Expected:**
- Modal opens with full session details
- Transcript shows speaker-labeled dialogue (30-50 segments)
- Summary matches card summary
- Topics and action items displayed
- Mood analysis shown with rationale

### Success Criteria:

#### Automated Verification:
- [ ] Demo initialization API returns 200: `curl -X POST https://therabridge-backend.up.railway.app/api/demo/initialize`
- [ ] Sessions endpoint returns populated data: `curl https://therabridge-backend.up.railway.app/api/sessions/ -H "X-Demo-Token: {token}"`
- [ ] All 10 sessions have non-empty transcripts in response JSON

#### Manual Verification:
- [ ] Railway logs show complete pipeline execution (transcripts → Wave 1 → Wave 2)
- [ ] No errors or exceptions in Railway logs
- [ ] Supabase database query shows all 10 sessions populated
- [ ] Frontend displays 10 session cards with real data (not placeholders)
- [ ] Session detail modal shows full transcript
- [ ] Mood emojis display correctly based on mood_score
- [ ] Breakthrough sessions (if any) show star icon
- [ ] Total pipeline time: 3-8 minutes from demo init to completion

**Implementation Note:** Pipeline timing depends on OpenAI API response times. Wave 1 makes 30 API calls (10 sessions × 3 analyses), Wave 2 makes 10 calls. Normal completion time is 5-8 minutes. If it takes longer than 15 minutes, check Railway logs for timeout errors.

---

## Testing Strategy

### Local Testing (Optional):
Can be skipped since we're deploying directly to Railway with existing tested scripts.

### Integration Testing on Railway:

**Test 1: Fresh Demo Initialization**
1. Clear browser localStorage
2. Visit frontend, click "Try Demo"
3. Monitor Railway logs
4. Wait 5 minutes
5. Verify data appears

**Test 2: Multiple Demo Initializations**
1. Initialize demo 3 times in a row
2. Verify each gets unique patient_id
3. Verify no data bleeding between demos

**Test 3: Error Recovery**
1. Initialize demo
2. If pipeline fails, check debug endpoint:
   ```bash
   curl -X POST https://therabridge-backend.up.railway.app/api/debug/populate-transcripts/{patient_id} \
     -H "X-Demo-Token: {demo_token}"
   ```
3. Analyze error output
4. Fix and redeploy

### Edge Cases to Test:
- ✅ Railway cold start (first request after deployment)
- ✅ Concurrent demo initializations (2 users at once)
- ✅ OpenAI API rate limit handling
- ✅ Transcript files missing (should fail gracefully)

---

## Performance Considerations

### Pipeline Execution Time:
- **Transcript Population:** ~10 seconds (read 10 JSON files, insert into DB)
- **Wave 1 Analysis:** ~120-180 seconds (30 OpenAI API calls in sequence)
- **Wave 2 Analysis:** ~180-300 seconds (10 OpenAI API calls with larger context)
- **Total:** 5-8 minutes end-to-end

### Optimization Opportunities (Future):
- Parallelize Wave 1 analyses across sessions (reduce to ~30 seconds)
- Use GPT-4o-mini batch API (reduce cost by 50%)
- Cache common analyses (same transcript → same results)
- Pre-populate demo database with analysis results (instant load)

**Note:** Current sequential approach is acceptable for demo. Railway background tasks have 15-minute timeout, well within limits.

### Railway Resource Usage:
- **Memory:** ~200MB during pipeline execution (well within free tier 512MB limit)
- **CPU:** Minimal (I/O bound, waiting for OpenAI API responses)
- **Database:** 10 sessions × ~50KB transcript data = ~500KB per demo

---

## Migration Notes

No database schema changes required. All fields already exist:
- `transcript` (JSONB) - stores segment array
- `topics`, `action_items`, `technique`, `summary` (TEXT/TEXT[])
- `mood_score`, `mood_confidence`, `emotional_tone` (NUMERIC/TEXT)
- `deep_analysis` (JSONB) - stores Wave 2 results

**Data Migration:**
- Existing empty sessions will be populated when pipeline runs
- Old demo sessions with hardcoded data can be deleted manually via Supabase SQL:
  ```sql
  DELETE FROM therapy_sessions WHERE summary = 'Crisis intake for recent breakup with passive SI, safety plan created';
  ```

---

## Rollback Plan

If deployment fails:

1. **Revert directory move:**
   ```bash
   git revert HEAD
   mv backend/mock-therapy-data mock-therapy-data
   git add . && git commit -m "Rollback: Move mock-therapy-data back to root"
   git push
   ```

2. **Disable background tasks:**
   - Set `run_analysis=False` in demo initialization endpoint
   - Sessions will be created but not populated (safe state)

3. **Use debug endpoints for manual population:**
   - Call `/api/debug/populate-transcripts/{patient_id}` manually
   - Analyze errors without time pressure

---

## References

- **Working Vertical Integration:** Git commit `21730f7` (Session 1 fetch from database)
- **Backend Endpoint:** Git commit `bb95e5f` (GET /api/sessions/)
- **Seed Demo v4:** `backend/supabase/migrations/008_seed_demo_v4_all_sessions.sql`
- **Seeding Scripts:**
  - `backend/scripts/seed_all_sessions.py`
  - `backend/scripts/seed_wave1_analysis.py`
  - `backend/scripts/seed_wave2_analysis.py`
- **Context Document:** `NEXT_SESSION_CONTEXT.md`
- **Database CSV:** `/Users/newdldewdl/Downloads/therapy_sessions_rows.csv`

---

## Implementation Checklist

### Phase 1: Move Mock Data
- [ ] Move `mock-therapy-data/` to `backend/mock-therapy-data/`
- [ ] Update `seed_all_sessions.py` path resolution
- [ ] Verify `.gitignore` doesn't exclude mock data
- [ ] Commit and push changes
- [ ] Verify Railway deployment includes mock-therapy-data files

### Phase 2: Fix Background Tasks
- [ ] Add `from pathlib import Path` to `demo.py`
- [ ] Update `populate_session_transcripts_background()` with absolute path
- [ ] Update `run_wave1_analysis_background()` with absolute path
- [ ] Update `run_wave2_analysis_background()` with absolute path
- [ ] Add logging statements for debugging
- [ ] Commit and push changes
- [ ] Deploy to Railway

### Phase 3: Verify Pipeline
- [ ] Initialize demo from frontend
- [ ] Monitor Railway logs for successful execution
- [ ] Query Supabase database to verify data population
- [ ] Test frontend session cards display
- [ ] Test session detail modal transcript view
- [ ] Verify all 10 sessions populated correctly

### Phase 4: Cleanup (Optional)
- [ ] Delete old hardcoded demo sessions from database
- [ ] Remove debug endpoints (if no longer needed)
- [ ] Update documentation with final approach

---

## Success Metrics

**Pipeline is considered successful when:**
1. ✅ Demo initialization completes without errors
2. ✅ All 10 sessions have populated transcripts (30+ segments each)
3. ✅ Wave 1 analysis completes for all sessions (topics, mood, summary)
4. ✅ Wave 2 analysis completes for all sessions (deep insights)
5. ✅ Frontend displays real data (not placeholders)
6. ✅ Total execution time: 3-8 minutes
7. ✅ Railway logs show no errors or exceptions

**User Experience Success:**
- User clicks "Try Demo"
- Sees 10 session cards with dates immediately
- Within 30 seconds, transcripts populate (cards still show loading)
- Within 3-5 minutes, all cards show mood/topics/summary
- User can click any session and see full transcript
- No error messages or loading states persist after 8 minutes

---

**Plan Status:** Ready for Implementation
**Estimated Implementation Time:** 30 minutes
**Estimated Testing Time:** 15 minutes (waiting for pipeline to complete)
**Total Time:** 45 minutes
