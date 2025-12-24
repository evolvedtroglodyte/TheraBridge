# TherapyBridge Demo Plan - Quick Reference

## 30-Second Summary

**Goal:** Each browser user gets their own "Demo" account with 10 pre-analyzed therapy sessions.

**Current Status:**
- ✅ 12 mock therapy sessions with real dialogue
- ✅ Wave 1 AI (mood, topics, breakthroughs) - ready to run
- ✅ Wave 2 AI (deep clinical analysis) - ready to run
- ✅ Demo API endpoints (`/api/demo/initialize`, `/api/demo/reset`, `/api/demo/status`)
- ✅ Frontend demo token storage and header injection
- ✅ Database schema with demo_token and analysis fields
- ❌ **MISSING:** Script to actually seed Wave 1 analysis data
- ❌ **MISSING:** Script to seed Wave 2 analysis data
- ❌ **MISSING:** SQL function to create demo user + load sessions

## What Exists

### Backend Services (Ready to Use)
```python
# These work, just need to be called by a script:
mood_analyzer.analyze_session_mood(session_id, segments)
topic_extractor.extract_metadata(session_id, segments)
breakthrough_detector.analyze_session(transcript, metadata)
deep_analyzer.analyze_session(session_id, context, cumulative_context)
```

### Mock Data (Ready to Use)
```
/mock-therapy-data/sessions/
  - session_01_crisis_intake.json
  - session_02_emotional_regulation.json
  - ... (all 12 sessions with full dialogue)
```

Each has:
- `segments[]` with speaker_id, text, timestamps
- Real therapy dialogue (not AI-generated)

### Database Schema (Ready to Use)
```sql
therapy_sessions table has columns:
- mood_score, mood_confidence, mood_rationale, mood_indicators
- topics[], action_items[], technique, summary
- has_breakthrough, breakthrough_data
- deep_analysis (JSONB with all clinical dimensions)
```

### Frontend Integration (Ready to Use)
```typescript
// Token management
demoTokenStorage.saveToken(token, patientId, expiresAt)
demoTokenStorage.getToken()  // Returns token or null

// API calls
demoApiClient.initialize()  // Creates demo user
demoApiClient.reset()       // Clears and re-seeds
demoApiClient.getStatus()   // Checks expiry

// Automatic header injection
// X-Demo-Token header added to all API requests when token exists
```

## What's Missing

### 1. SQL Function to Seed User + Sessions
**Where:** Supabase migration
**What it does:**
- Creates demo user with demo_token (UUID)
- Sets demo_expires_at to NOW() + 24 hours
- Inserts 10 therapy_sessions records with transcripts
- Returns patient_id and session_ids

**To create:**
```sql
CREATE FUNCTION seed_demo_user_sessions(p_demo_token UUID)
RETURNS TABLE (patient_id UUID, session_ids UUID[])
AS $$
  -- Create user
  -- Load Sessions 1-10 into therapy_sessions
  -- Return patient_id and session IDs
$$ LANGUAGE plpgsql;
```

### 2. Python Script: Seed Wave 1 Analysis
**File:** `backend/scripts/seed_wave1_analysis.py`
**What it does:**
```python
for session_number in [1..10]:
    session_data = load_json(f"session_{session_number:02d}.json")
    
    # Run Wave 1 (3 parallel operations)
    mood = mood_analyzer.analyze_session_mood(session_id, segments)
    topics = topic_extractor.extract_metadata(session_id, segments)
    breakthrough = breakthrough_detector.analyze_session(transcript, metadata)
    
    # Save to database
    db.therapy_sessions.update(session_id, {
        "mood_score": mood.mood_score,
        "topics": topics.topics,
        "has_breakthrough": breakthrough.has_breakthrough,
        ...
    })
```

**Usage:**
```bash
python backend/scripts/seed_wave1_analysis.py --patient-id <uuid>
```

### 3. Python Script: Seed Wave 2 Analysis
**File:** `backend/scripts/seed_wave2_analysis.py`
**What it does:**
```python
cumulative_context = None

for session_number in [1..10]:
    session = db.get_session(session_number)
    prev_sessions = db.get_previous_sessions(session_number, limit=2)
    
    # Build cumulative context from previous sessions
    if cumulative_context:
        cumulative_context = {
            "previous_context": cumulative_context,
            f"session_{session_number-1:02d}_wave1": {...},
            f"session_{session_number-1:02d}_wave2": {...}
        }
    
    # Run Wave 2 with context
    deep = deep_analyzer.analyze_session(
        session_id,
        context,
        cumulative_context=cumulative_context
    )
    
    # Save to database
    db.therapy_sessions.update(session_id, {
        "deep_analysis": deep.to_dict(),
        "deep_analyzed_at": NOW()
    })
```

**Usage:**
```bash
python backend/scripts/seed_wave2_analysis.py --patient-id <uuid>
```

## The Flow (What Happens When User Clicks "Try Demo")

1. **Frontend:** User clicks "Try Demo" button
2. **Frontend → Backend:** Call `POST /api/demo/initialize`
3. **Backend:**
   - Generate unique demo_token (UUID)
   - Call SQL function: `seed_demo_user_sessions(demo_token)`
   - SQL creates user + loads 10 sessions
   - **OPTION A (Fast):** Return immediately with demo_token
   - **OPTION B (Complete):** Run Wave 1+2 scripts, then return
4. **Backend → Frontend:** Return demo_token, patient_id, session_ids, expires_at
5. **Frontend:**
   - Save demo_token to localStorage
   - Redirect to /patient/dashboard
6. **Frontend → Backend:** Load sessions for patient_id
   - Include X-Demo-Token header automatically
7. **Backend:** Validates token, filters sessions by patient_id
8. **Frontend:** Displays sessions in dashboard

## Key Architecture Decisions

### Per-Browser Isolation
Each browser localStorage gets a unique:
- `demo_token` (UUID) 
- `demo_patient_id` (UUID)
- `demo_expires_at` (datetime)

All API requests include `X-Demo-Token` header. Backend:
1. Validates token exists in users.demo_token
2. Gets patient_id from that user
3. Filters all queries by `WHERE patient_id = ?`

Result: Multiple browsers get different data even from same IP

### 24-Hour Expiry
Demo users have `demo_expires_at` timestamp. When demo:
- Check: `NOW() > demo_expires_at`?
- If yes, either show "expired" or allow re-initialize

### Cumulative Context (Session Dependency)
Each session analysis references previous ones:
```
Session 1: No context
Session 2: Context = {session_01_wave1, session_01_wave2}
Session 3: Context = {previous_context: {...}, session_02_wave1, session_02_wave2}
Session 4: Context = {previous_context: {previous_context: {...}...}, session_03_wave1, session_03_wave2}
```

This creates a "therapeutic journey" where later insights reference earlier breakthroughs.

## File Locations (Quick Lookup)

| What | Where |
|------|-------|
| Mock sessions | `/mock-therapy-data/sessions/session_*.json` |
| Wave 1 services | `/backend/app/services/mood_analyzer.py`, `topic_extractor.py`, `breakthrough_detector.py` |
| Wave 2 service | `/backend/app/services/deep_analyzer.py` |
| Demo API | `/backend/app/routers/demo.py` |
| Demo middleware | `/backend/app/middleware/demo_auth.py` |
| Frontend token storage | `/frontend/lib/demo-token-storage.ts` |
| Frontend API client | `/frontend/lib/demo-api-client.ts` |
| Existing test | `/backend/tests/test_full_pipeline_demo.py` (shows full flow) |

## One-Liner Summary

"Create 2 Python scripts (wave1 seeding, wave2 seeding) + 1 SQL function, then hook them into `/api/demo/initialize` endpoint"

