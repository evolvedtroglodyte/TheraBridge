# Next Session Context - TherapyBridge Session Pipeline Fix

## Current Status (Dec 28, 2025)

### ✅ What's Working:
1. **10 Sessions Created in Database** - Demo initialization creates 10 empty sessions (Jan 10 → May 9, 2025)
2. **Frontend Loading Sessions** - Dashboard displays 10 session cards with dates from database
3. **SessionCardsGrid Layout** - Fixed to use proper grid layout (not inline-grid)
4. **Backend Endpoint** - `GET /api/sessions/` returns all 10 sessions for demo user
5. **Patient ID Lookup** - Fixed to lookup patient_id from user_id correctly

### ❌ What's NOT Working:
1. **Transcripts Empty** - Sessions have `transcript: []` because background pipeline isn't running
2. **Summaries Empty** - Showing "Summary not yet generated" (default values)
3. **Topics/Actions Empty** - Wave 1 analysis hasn't run
4. **Mood Scores Empty** - Mood analysis hasn't run
5. **Deep Analysis Empty** - Wave 2 analysis hasn't run

### 🔍 Root Cause:
**Background tasks on Railway are not completing.** When demo is initialized:
1. `seed_demo_v4()` creates 10 sessions with empty transcripts ✅
2. Background task queued to run pipeline ✅
3. **Pipeline fails silently** ❌ (Railway likely kills process or scripts fail)

---

## The Pipeline (Already Implemented)

### Step 1: Transcript Population
**Script:** `backend/scripts/seed_all_sessions.py`
- Reads JSON files from `mock-therapy-data/sessions/`
- Populates `transcript` field in database
- **Input:** patient_id
- **Output:** All 10 sessions have populated transcripts

### Step 2: Wave 1 Analysis (Parallel)
**Script:** `backend/scripts/seed_wave1_analysis.py`
- Runs 3 AI services in parallel per session:
  1. **Mood Analysis** → mood_score, mood_confidence, emotional_tone
  2. **Topic Extraction** → topics, action_items, technique, summary
  3. **Breakthrough Detection** → milestone label if transformative
- **Input:** patient_id
- **Output:** All sessions have Wave 1 metadata

### Step 3: Wave 2 Analysis (Deep Insights)
**Script:** `backend/scripts/seed_wave2_analysis.py`
- Runs deep analysis and prose generation
- **Input:** patient_id
- **Output:** All sessions have Wave 2 insights

---

## Implementation Plan

### Goal: Get Pipeline Running on Railway

#### Option A: Fix Background Tasks (Recommended)
**Problem:** FastAPI background tasks don't persist on Railway
**Solution:** Use a task queue (Celery, Redis Queue) or cron job

**Steps:**
1. Add Redis to Railway project
2. Install celery in backend requirements
3. Convert background tasks to Celery tasks
4. Configure worker dyno on Railway

#### Option B: Manual Trigger Endpoint (Quick Fix)
**Problem:** Can't debug background tasks
**Solution:** Create synchronous endpoint to run pipeline on-demand

**Steps:**
1. Create `POST /api/demo/run-pipeline/{patient_id}` endpoint
2. Run all 3 scripts synchronously with proper error handling
3. Return detailed results/errors
4. Frontend can poll this endpoint after demo init

#### Option C: Use Debug Endpoints (Current)
**Already Created:** `/api/debug/populate-transcripts/{patient_id}`

**Steps:**
1. Test debug endpoint to see exact errors
2. Fix file path issues or dependencies
3. Re-enable background tasks once working

---

## Database Schema (Already Complete)

### therapy_sessions table has all needed fields:
```sql
- id (uuid)
- patient_id (uuid)
- therapist_id (uuid)
- session_date (date)
- duration_minutes (int)
- status (varchar) ✅ FIXED
- transcript (jsonb) ← EMPTY, needs population
- topics (text[]) ← EMPTY, needs Wave 1
- action_items (text[]) ← EMPTY, needs Wave 1
- technique (text) ← EMPTY, needs Wave 1
- summary (text) ← EMPTY, needs Wave 1
- mood_score (numeric) ← EMPTY, needs Wave 1
- mood_confidence (numeric) ← EMPTY, needs Wave 1
- emotional_tone (text) ← EMPTY, needs Wave 1
- mood_rationale (text) ← EMPTY, needs Wave 1
- mood_indicators (jsonb) ← EMPTY, needs Wave 1
- extraction_confidence (numeric) ← EMPTY, needs Wave 1
- milestone (text) ← EMPTY, needs Wave 1 (breakthrough detection)
- deep_analysis (jsonb) ← EMPTY, needs Wave 2
- prose_analysis (text) ← EMPTY, needs Wave 2
```

---

## Files to Check

### Backend Scripts (All Exist):
- `backend/scripts/seed_all_sessions.py` - Populates transcripts
- `backend/scripts/seed_wave1_analysis.py` - Mood + Topics + Breakthrough
- `backend/scripts/seed_wave2_analysis.py` - Deep analysis + Prose

### AI Services (All Exist):
- `backend/app/services/mood_analyzer.py`
- `backend/app/services/topic_extractor.py`
- `backend/app/services/breakthrough_detector.py`
- `backend/app/services/deep_analyzer.py`
- `backend/app/services/prose_generator.py`

### Mock Data (All Exist):
- `mock-therapy-data/sessions/session_01_crisis_intake.json`
- `mock-therapy-data/sessions/session_02_emotional_regulation.json`
- ... (sessions 03-10)

### Frontend Components (All Work):
- `frontend/app/patient/components/SessionCard.tsx` - Displays session cards
- `frontend/app/patient/components/SessionDetail.tsx` - Shows full session details
- `frontend/app/patient/lib/usePatientSessions.ts` - Fetches sessions from API
- `frontend/app/sessions/page.tsx` - Sessions page

---

## Quick Diagnostic Steps

### 1. Check if mock-therapy-data exists on Railway:
```bash
curl https://therabridge-backend.up.railway.app/api/debug/check-paths
```

### 2. Check if scripts can run:
```bash
curl -X POST https://therabridge-backend.up.railway.app/api/debug/populate-transcripts/{patient_id} \
  -H "X-Demo-Token: {your-demo-token}"
```

### 3. Check Railway logs:
- Go to Railway dashboard
- Click backend service
- View deployment logs
- Search for "transcript" or "wave1" or errors

---

## Next Session Prompt

**Use this prompt in the next chat window:**

```
I need help debugging why the TherapyBridge session pipeline isn't running on Railway.

**Current State:**
- Demo initialization creates 10 sessions successfully ✅
- Sessions load in frontend with correct dates ✅
- BUT all fields are empty (transcripts, summaries, topics, mood) ❌

**What Should Happen:**
After demo init, background tasks should run 3 scripts:
1. `seed_all_sessions.py` - Populate transcripts from mock JSON files
2. `seed_wave1_analysis.py` - Run AI analysis (mood, topics, summary)
3. `seed_wave2_analysis.py` - Generate deep insights

**The Problem:**
Background tasks are queued but not completing. Railway might be killing them.

**What Exists:**
- All 3 scripts exist in `backend/scripts/`
- All AI services exist in `backend/app/services/`
- All mock data exists in `mock-therapy-data/sessions/`
- Debug endpoints exist at `/api/debug/populate-transcripts` and `/api/debug/check-paths`

**What I Need:**
1. Test debug endpoints to see exact error
2. Fix whatever is preventing scripts from running on Railway
3. Get all 10 sessions populated with real data

**Context Document:** See NEXT_SESSION_CONTEXT.md for full details.

**Important:** Don't recreate anything - just fix the pipeline execution issue.
```

---

## Key Insights

1. **Nothing Needs to be Built** - All algorithms, scripts, and services already exist
2. **Backend Deployment Issue** - Scripts aren't running on Railway (likely subprocess or file path issue)
3. **Frontend is Ready** - SessionCard and SessionDetail already show all fields when populated
4. **Database is Ready** - All columns exist with correct schema
5. **Mock Data is Ready** - All 10 session JSON files committed to repo

---

## Expected Behavior After Fix

Once pipeline runs successfully:

### Session Cards Will Show:
- ✅ Date from database (already working)
- ✅ Mood emoji (happy/neutral/sad based on mood_score)
- ✅ Topics from AI extraction
- ✅ Strategy/technique from AI extraction
- ✅ Summary from AI extraction
- ✅ Breakthrough star if milestone detected

### Session Detail Modal Will Show:
- ✅ Full transcript with speaker labels
- ✅ Complete summary
- ✅ All topics and action items
- ✅ Mood analysis with rationale
- ✅ Deep insights from Wave 2
- ✅ Breakthrough moment details (if applicable)

---

## Commit History Reference

Recent commits (all backdated to Dec 23, 2025):
- `dfd6dfb` - Add debug endpoints to diagnose pipeline failures
- `6e9c5e9` - Restore actual SessionCardsGrid layout from earlier today
- `6f636ab` - Fix getAllSessions to lookup patient_id from user_id
- `9a524ff` - Add is_demo column and update seed_demo_v4
- `3dbce00` - Add status column to therapy_sessions table
- `78fb5ba` - Phase 1: Create backend seed script for all 10 sessions

---

## Environment Info

- **Frontend:** Railway deployment at https://therabridge.up.railway.app
- **Backend:** Railway deployment at https://therabridge-backend.up.railway.app
- **Database:** Supabase (PostgreSQL)
- **Python:** 3.13.9
- **Node:** Latest (Next.js 16, React 19)

---

## Final Note

The ONLY thing that needs fixing is getting the 3 pipeline scripts to run successfully on Railway. Everything else is complete and working. Once the scripts run, the entire app will light up with real AI-generated data.
