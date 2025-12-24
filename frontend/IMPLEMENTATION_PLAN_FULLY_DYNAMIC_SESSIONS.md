# Implementation Plan: Fully Dynamic Session Loading (Remove All Hardcoded Mock Data)

**Date**: 2025-12-27
**Context**: User wants ALL sessions to load dynamically from the database/API, not hardcoded mock data
**Current State**: Only Session 1 loads from database, Sessions 2-10 are hardcoded in mockData.ts

---

## Problem Statement

**Current Implementation (WRONG):**
- ❌ Session 1: Loaded from database via API ✅
- ❌ Sessions 2-10: Hardcoded in `mockData.ts` (fake data, not real)
- ❌ Number of cards: Fixed at 10 (hardcoded)
- ❌ Dates: Hardcoded in mockData.ts
- ❌ Topics, summaries, strategies: All hardcoded

**Desired Implementation (CORRECT):**
- ✅ ALL sessions: Load from database via API
- ✅ Number of cards: Dynamic based on database records
- ✅ Dates: From database `session_date` field
- ✅ Topics, summaries, strategies: From AI analysis stored in database
- ✅ Transcripts: From `mock-therapy-data/sessions/*.json` files, stored in database

---

## Key Questions & Answers

### Q1: Should all 10 sessions be created in the database on demo initialization?
**Answer**: YES - Create all 10 sessions with full transcripts in database

### Q2: Should AI analysis run on all 10 sessions?
**Answer**: YES - Run Wave 1 (topic extraction, mood analysis) on all 10 sessions
- Wave 2 (deep analysis) can be optional/background

### Q3: How long will this take?
**Answer**:
- Creating 10 sessions: ~1 second
- Wave 1 AI analysis (10 sessions): ~30-60 seconds total
- Solution: Run in background, show loading states

### Q4: What data comes from the transcripts?
**Answer**:
- Transcript segments (speaker, text, timestamps)
- Session metadata (date, duration, filename)
- Performance metrics (processing time, quality stats)

---

## Current Architecture Analysis

**Database Tables:**
- `therapy_sessions` - Stores session records
  - Fields: id, patient_id, session_date, duration_minutes, status, transcript (JSONB)
  - AI fields: topics[], action_items[], technique, summary, mood_score, extraction_confidence

**API Endpoints:**
- `/api/demo/initialize` - Creates demo user (currently creates 1 session)
- `/api/sessions/{id}` - Fetches single session
- **MISSING**: `/api/sessions?patient_id={id}` - Fetch all sessions for patient

**Frontend Hook:**
- `usePatientSessions()` - Currently mixes 1 real + 9 fake sessions

---

## Implementation Plan

### Phase 1: Backend - Create Seed Script for All 10 Sessions

**Goal**: Load all 10 session transcripts from `mock-therapy-data/sessions/` into database

**Files to Create:**
1. `backend/scripts/seed_all_sessions.py` - Main script to seed all sessions
2. `backend/supabase/migrations/005_seed_demo_v4_all_sessions.sql` - SQL function

**Script Logic:**
```python
# backend/scripts/seed_all_sessions.py
import json
from pathlib import Path
from datetime import datetime

def seed_all_sessions(patient_id: str, therapist_id: str):
    """
    Load all 10 session transcripts from mock-therapy-data folder
    Insert into therapy_sessions table
    """
    sessions_dir = Path("mock-therapy-data/sessions")

    # Map session files to database records
    session_files = [
        "session_01_crisis_intake.json",
        "session_02_emotional_regulation.json",
        "session_03_adhd_discovery.json",
        "session_04_medication_start.json",
        "session_05_family_conflict.json",
        "session_06_spring_break_hope.json",
        "session_07_dating_anxiety.json",
        "session_08_relationship_boundaries.json",
        "session_09_coming_out_preparation.json",
        "session_10_coming_out_aftermath.json",
    ]

    session_ids = []
    for filename in session_files:
        # Read transcript JSON
        with open(sessions_dir / filename) as f:
            data = json.load(f)

        # Extract metadata
        timestamp = data["metadata"]["timestamp"]  # "20250110_140000"
        session_date = datetime.strptime(timestamp[:8], "%Y%m%d").date()
        duration = int(data["metadata"]["duration"]) // 60  # Convert to minutes

        # Extract transcript segments
        segments = data["segments"]  # Array of {speaker, text, start, end}

        # Insert into database
        session_id = insert_session(
            patient_id=patient_id,
            therapist_id=therapist_id,
            session_date=session_date,
            duration_minutes=duration,
            transcript=segments,
            status="completed"
        )

        session_ids.append(session_id)

    return session_ids
```

**SQL Function Update:**
```sql
-- backend/supabase/migrations/005_seed_demo_v4_all_sessions.sql
CREATE OR REPLACE FUNCTION seed_demo_v4(p_demo_token TEXT)
RETURNS TABLE (
  patient_id UUID,
  session_ids UUID[]
) AS $$
DECLARE
  v_therapist_id UUID;
  v_user_id UUID;
  v_patient_id UUID;
  v_session_ids UUID[] := '{}';
  v_session_dates DATE[] := ARRAY[
    '2025-01-10'::date,  -- Session 1
    '2025-01-17'::date,  -- Session 2
    '2025-01-31'::date,  -- Session 3
    '2025-02-14'::date,  -- Session 4
    '2025-02-28'::date,  -- Session 5
    '2025-03-14'::date,  -- Session 6
    '2025-04-04'::date,  -- Session 7
    '2025-04-18'::date,  -- Session 8
    '2025-05-02'::date,  -- Session 9
    '2025-05-09'::date   -- Session 10
  ];
  v_session_id UUID;
  v_session_date DATE;
BEGIN
  -- Create therapist and patient users (same as v3)
  -- ...

  -- Loop through all 10 sessions
  FOREACH v_session_date IN ARRAY v_session_dates
  LOOP
    INSERT INTO therapy_sessions (
      id, patient_id, therapist_id, session_date,
      duration_minutes, status, transcript,
      created_at, updated_at
    ) VALUES (
      gen_random_uuid(),
      v_patient_id,
      v_therapist_id,
      v_session_date,
      60,
      'completed',
      '[]'::jsonb,  -- Empty transcript initially, will be populated by Python script
      NOW(),
      NOW()
    ) RETURNING id INTO v_session_id;

    v_session_ids := array_append(v_session_ids, v_session_id);
  END LOOP;

  RETURN QUERY SELECT v_patient_id, v_session_ids;
END;
$$ LANGUAGE plpgsql;
```

**Changes Required:**
1. Create `backend/scripts/seed_all_sessions.py`
2. Create SQL migration `005_seed_demo_v4_all_sessions.sql`
3. Update `demo.py` to call `seed_demo_v4` instead of `seed_demo_v3`
4. After SQL function creates sessions, call Python script to populate transcripts

**Success Criteria:**
- [ ] SQL function creates 10 sessions with correct dates
- [ ] Python script reads all 10 JSON files from mock-therapy-data
- [ ] Transcripts are stored in database (verify with SQL query)
- [ ] All 10 sessions have `status = 'completed'`

---

### Phase 2: Backend - Add "Fetch All Sessions" API Endpoint

**Goal**: Create endpoint to fetch all sessions for a patient (not just one)

**File**: `backend/app/routers/sessions.py`

**New Endpoint:**
```python
@router.get("/api/sessions", response_model=List[SessionResponse])
async def get_patient_sessions(
    request: Request,
    demo_user: dict = Depends(require_demo_auth),
    db: Client = Depends(get_db)
):
    """
    Fetch ALL sessions for the current demo patient

    Returns:
        List of sessions with all fields (transcript, topics, summary, etc.)
    """
    patient_id = demo_user["id"]

    # Fetch all sessions for this patient, ordered by date DESC (newest first)
    response = db.table("therapy_sessions") \
        .select("*") \
        .eq("patient_id", patient_id) \
        .order("session_date", desc=True) \
        .execute()

    if not response.data:
        return []

    return response.data
```

**Response Schema:**
```python
class SessionResponse(BaseModel):
    id: str
    patient_id: str
    therapist_id: str
    session_date: str  # ISO format: "2025-01-10"
    duration_minutes: int
    status: str
    transcript: List[TranscriptSegment]
    # AI Analysis fields (may be null if not analyzed yet)
    topics: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    technique: Optional[str] = None
    summary: Optional[str] = None
    mood_score: Optional[float] = None
    extraction_confidence: Optional[float] = None
    topics_extracted_at: Optional[str] = None
```

**Success Criteria:**
- [ ] Endpoint returns all sessions for patient
- [ ] Sessions sorted by date (newest first)
- [ ] Response includes all fields (transcript, topics, summary)
- [ ] Returns empty array if no sessions found
- [ ] Test with Postman/curl: `curl -H "Demo-Token: XXX" http://localhost:8000/api/sessions`

---

### Phase 3: Frontend - Update API Client

**Goal**: Add method to fetch all sessions (not just one)

**File**: `frontend/lib/api-client.ts`

**New Method:**
```typescript
async getAllSessions(): Promise<{
  success: boolean;
  data?: Session[];
  error?: string;
}> {
  try {
    const response = await fetch(`${this.baseUrl}/api/sessions`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      return {
        success: false,
        error: `HTTP ${response.status}: ${response.statusText}`,
      };
    }

    const sessions = await response.json();
    return { success: true, data: sessions };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    };
  }
}
```

**Success Criteria:**
- [ ] Method fetches all sessions from `/api/sessions`
- [ ] Uses demo token from headers
- [ ] Returns typed response with success/error
- [ ] TypeScript compilation passes

---

### Phase 4: Frontend - Update usePatientSessions Hook (FULLY DYNAMIC)

**Goal**: Remove ALL hardcoded mock data, load everything from API

**File**: `frontend/app/patient/lib/usePatientSessions.ts`

**Complete Rewrite:**
```typescript
export function usePatientSessions() {
  const [isLoading, setIsLoading] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAllSessions = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Step 1: Initialize demo if needed
        if (!demoTokenStorage.isInitialized()) {
          console.log('[Demo] Initializing...');
          const initResult = await apiClient.initializeDemo();

          if (!initResult.success || !initResult.data) {
            throw new Error(initResult.error || 'Failed to initialize demo');
          }

          const { demo_token, patient_id, session_ids, expires_at } = initResult.data;
          demoTokenStorage.store(demo_token, patient_id, session_ids, expires_at);
          console.log('[Demo] ✓ Initialized:', { patient_id, sessionCount: session_ids.length });
        }

        // Step 2: Fetch ALL sessions from API
        console.log('[Sessions] Fetching all sessions from API...');
        const result = await apiClient.getAllSessions();

        if (!result.success || !result.data) {
          throw new Error(result.error || 'Failed to fetch sessions');
        }

        // Step 3: Transform backend sessions to frontend Session type
        const transformedSessions: Session[] = result.data.map((backendSession) => {
          const sessionDate = new Date(backendSession.session_date);

          return {
            id: backendSession.id,
            date: sessionDate.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            }), // "Jan 10"
            rawDate: sessionDate,
            duration: `${backendSession.duration_minutes} min`,
            therapist: 'Dr. Rodriguez',
            mood: mapMoodScore(backendSession.mood_score), // Map 0-10 score to MoodType
            topics: backendSession.topics || [],
            strategy: backendSession.technique || 'Not yet analyzed',
            actions: backendSession.action_items || [],
            summary: backendSession.summary || 'Summary not yet generated.',
            transcript: backendSession.transcript || [],
            extraction_confidence: backendSession.extraction_confidence,
            topics_extracted_at: backendSession.topics_extracted_at,
          };
        });

        // Step 4: Sort by date (newest first) - already sorted by backend, but ensure
        const sortedSessions = transformedSessions.sort((a, b) => {
          if (!a.rawDate || !b.rawDate) return 0;
          return b.rawDate.getTime() - a.rawDate.getTime();
        });

        console.log('[Sessions] ✓ Loaded:', sortedSessions.length, 'sessions');
        console.log('[Sessions] ✓ Date range:', sortedSessions[sortedSessions.length - 1]?.date, '→', sortedSessions[0]?.date);

        setSessions(sortedSessions);

      } catch (err) {
        console.error('[usePatientSessions] Error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load sessions');
        setSessions([]); // Empty state on error (no fallback to mock)
      } finally {
        setIsLoading(false);
      }
    };

    loadAllSessions();
  }, []);

  return {
    sessions,
    isLoading,
    isError: error !== null,
    error,
    sessionCount: sessions.length, // DYNAMIC: Based on database count
    isEmpty: !isLoading && sessions.length === 0,
  };
}

// Helper function to map mood_score (0-10) to MoodType ('positive' | 'neutral' | 'low')
function mapMoodScore(score: number | null | undefined): MoodType {
  if (score === null || score === undefined) return 'neutral';
  if (score >= 7) return 'positive';
  if (score >= 4) return 'neutral';
  return 'low';
}
```

**Key Changes:**
- ❌ REMOVED: `mockSessions`, `mockTasks`, `mockTimeline` imports
- ❌ REMOVED: Hybrid mode logic (no more mixing real + fake)
- ❌ REMOVED: `USE_HYBRID_MODE` flag
- ✅ ADDED: Fetch ALL sessions from `/api/sessions`
- ✅ ADDED: Transform all backend sessions to frontend type
- ✅ ADDED: Dynamic session count (not hardcoded at 10)

**Success Criteria:**
- [ ] Hook fetches all sessions from API (not just 1)
- [ ] No hardcoded mock data used
- [ ] Number of cards matches database count
- [ ] All dates come from database
- [ ] All summaries/topics come from database
- [ ] TypeScript compilation passes
- [ ] Console logs show correct session count

---

### Phase 5: Backend - Run Wave 1 Analysis on All Sessions

**Goal**: Populate AI fields (topics, summary, technique) for all 10 sessions

**File**: `backend/scripts/seed_wave1_all_sessions.py`

**Script Logic:**
```python
import sys
from app.services.topic_extractor import TopicExtractor
from app.services.mood_analyzer import MoodAnalyzer
from app.database import get_supabase_admin

def analyze_all_sessions(patient_id: str):
    """
    Run Wave 1 analysis on all sessions for a patient
    - Extract topics, action items, technique, summary
    - Analyze mood score
    """
    db = get_supabase_admin()
    topic_extractor = TopicExtractor()
    mood_analyzer = MoodAnalyzer()

    # Fetch all sessions
    response = db.table("therapy_sessions") \
        .select("id, transcript") \
        .eq("patient_id", patient_id) \
        .execute()

    sessions = response.data

    for session in sessions:
        session_id = session["id"]
        transcript = session["transcript"]

        print(f"Analyzing session {session_id}...")

        # Extract topics
        metadata = topic_extractor.extract(transcript)

        # Analyze mood
        mood_analysis = mood_analyzer.analyze(transcript)

        # Update database
        db.table("therapy_sessions").update({
            "topics": metadata.topics,
            "action_items": metadata.action_items,
            "technique": metadata.technique,
            "summary": metadata.summary,
            "extraction_confidence": metadata.confidence,
            "topics_extracted_at": datetime.now().isoformat(),
            "mood_score": mood_analysis.score,
            "mood_confidence": mood_analysis.confidence,
        }).eq("id", session_id).execute()

        print(f"✓ Session {session_id} analyzed")

    print(f"✓ All {len(sessions)} sessions analyzed")

if __name__ == "__main__":
    patient_id = sys.argv[1]
    analyze_all_sessions(patient_id)
```

**Integration:**
Update `demo.py` to trigger analysis after creating sessions:

```python
@router.post("/initialize", response_model=DemoInitResponse)
async def initialize_demo(
    background_tasks: BackgroundTasks,
    db: Client = Depends(get_db),
    run_analysis: bool = True
):
    # ... create demo user and sessions ...

    if run_analysis:
        # Trigger Wave 1 analysis for all sessions
        background_tasks.add_task(run_wave1_all_sessions, str(patient_id))
        analysis_status = "processing"

    # ...
```

**Success Criteria:**
- [ ] All 10 sessions have topics, summary, technique populated
- [ ] All 10 sessions have mood_score populated
- [ ] Analysis runs in background (doesn't block demo initialization)
- [ ] Console logs show progress: "Analyzing 1/10... 2/10... ✓ Complete"

---

### Phase 6: Frontend - Add Loading States & Empty States

**Goal**: Show proper UI during loading and when no sessions exist

**File**: `frontend/app/patient/dashboard-v3/page.tsx`

**Loading State:**
```typescript
if (isLoading) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500 mx-auto mb-4"></div>
        <p className="text-gray-600">Loading your sessions...</p>
      </div>
    </div>
  );
}
```

**Empty State:**
```typescript
if (isEmpty) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <p className="text-gray-600 text-lg">No sessions found</p>
        <p className="text-gray-500 text-sm mt-2">Your therapy sessions will appear here</p>
      </div>
    </div>
  );
}
```

**Error State:**
```typescript
if (isError) {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <p className="text-red-600 text-lg">Error loading sessions</p>
        <p className="text-gray-500 text-sm mt-2">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="mt-4 px-4 py-2 bg-teal-500 text-white rounded"
        >
          Retry
        </button>
      </div>
    </div>
  );
}
```

**Success Criteria:**
- [ ] Loading spinner shows while fetching sessions
- [ ] Empty state shows if no sessions in database
- [ ] Error state shows if API call fails
- [ ] Retry button reloads the page

---

## Testing Strategy

### Backend Testing:
```bash
# Test SQL function creates all 10 sessions
psql -d therapybridge -c "SELECT * FROM seed_demo_v4('test_token_123');"

# Verify all 10 sessions exist
psql -d therapybridge -c "SELECT id, session_date, topics, summary FROM therapy_sessions WHERE patient_id = '<patient_id>' ORDER BY session_date;"

# Test API endpoint
curl -H "Demo-Token: <token>" http://localhost:8000/api/sessions
```

### Frontend Testing:
1. Open browser console
2. Clear localStorage: `localStorage.clear()`
3. Reload page
4. Watch console logs:
   - `[Demo] Initializing...`
   - `[Demo] ✓ Initialized: { sessionCount: 10 }`
   - `[Sessions] Fetching all sessions from API...`
   - `[Sessions] ✓ Loaded: 10 sessions`
   - `[Sessions] ✓ Date range: Jan 10 → May 9`
5. Verify dashboard shows all 10 cards
6. Click each card, verify:
   - Correct date format (short on card, full in modal)
   - Transcript loads
   - Summary displays
   - Topics display

---

## Migration Path (For Existing Demo Users)

**Problem**: Existing demo users only have 1 session

**Solution**: Auto-upgrade on next login
```python
# In demo middleware
if session_count < 10:
    # User has old demo data, upgrade them
    await upgrade_demo_to_v4(patient_id)
```

Or simpler: Just clear demo token and force re-initialization:
```typescript
// In frontend
if (sessionCount === 1) {
  console.log('[Demo] Old demo detected, clearing...');
  demoTokenStorage.clear();
  window.location.reload();
}
```

---

## Rollback Plan

If issues occur:
1. Revert `demo.py` to use `seed_demo_v3` (creates 1 session only)
2. Revert `usePatientSessions.ts` to hybrid mode
3. Set `USE_HYBRID_MODE = true`
4. Frontend falls back to 1 real + 9 mock sessions

---

## Summary of Changes

**Backend:**
- ✅ Create `seed_demo_v4` SQL function (creates 10 sessions)
- ✅ Create `seed_all_sessions.py` script (populates transcripts)
- ✅ Create `seed_wave1_all_sessions.py` script (runs AI analysis)
- ✅ Add `/api/sessions` endpoint (fetch all sessions)
- ✅ Update `demo.py` to use v4 function + trigger analysis

**Frontend:**
- ✅ Add `getAllSessions()` method to API client
- ✅ Rewrite `usePatientSessions` hook (remove all mock data)
- ✅ Add loading/empty/error states
- ✅ Remove `USE_HYBRID_MODE` flag
- ✅ Remove mock data imports

**Database:**
- ✅ Migration 005: `seed_demo_v4` function
- ✅ All 10 sessions stored with transcripts
- ✅ All 10 sessions analyzed with AI

---

## Next Session Handoff

**To continue this work in a new session, tell Claude:**

> "Continue implementing the plan in `frontend/IMPLEMENTATION_PLAN_FULLY_DYNAMIC_SESSIONS.md`. We need to make all sessions load dynamically from the database instead of using hardcoded mock data. Start with Phase 1: Backend seed script for all 10 sessions. Use the mock-therapy-data/sessions/*.json files to populate the database. All commits should be backdated to Dec 23, 2025 starting at 21:07:00."

**Key Context to Provide:**
- Implementation plan location: `frontend/IMPLEMENTATION_PLAN_FULLY_DYNAMIC_SESSIONS.md`
- Mock data location: `mock-therapy-data/sessions/` (10 JSON files)
- Current state: Only Session 1 loads from DB, rest are hardcoded
- Goal: ALL sessions from database, dynamic count

**Files to Focus On:**
- Backend: `backend/scripts/seed_all_sessions.py` (create new)
- Backend: `backend/supabase/migrations/005_seed_demo_v4_all_sessions.sql` (create new)
- Backend: `backend/app/routers/sessions.py` (add `/api/sessions` endpoint)
- Frontend: `frontend/lib/api-client.ts` (add `getAllSessions()` method)
- Frontend: `frontend/app/patient/lib/usePatientSessions.ts` (rewrite to be fully dynamic)

**Testing Checklist:**
- [ ] 10 sessions created in database
- [ ] All transcripts populated from JSON files
- [ ] `/api/sessions` returns all 10 sessions
- [ ] Frontend displays all 10 cards dynamically
- [ ] Dates are correct (Jan 10 → May 9)
- [ ] AI analysis runs on all sessions

Good luck! 🚀
