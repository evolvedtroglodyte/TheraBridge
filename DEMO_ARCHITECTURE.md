# TherapyBridge Demo Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Landing Page              Patient Dashboard                     │
│  ┌──────────────┐         ┌──────────────────┐                  │
│  │ "Try Demo" ──┼─────────▶ Sessions List     │                  │
│  │   Button     │         │ - Mood cards     │                  │
│  └──────────────┘         │ - Topics display │                  │
│         │                 │ - Insights view  │                  │
│         │                 └──────────────────┘                  │
│         │                                                         │
│  localStorage              Session Detail                        │
│  ┌──────────────────────┐  ┌──────────────────┐                  │
│  │ demo_token (UUID)    │  │ - Transcript     │                  │
│  │ demo_patient_id      │  │ - Wave 1 data    │                  │
│  │ demo_expires_at      │  │ - Wave 2 data    │                  │
│  └──────────────────────┘  └──────────────────┘                  │
│         │                          │                             │
│         └──────────┬───────────────┘                             │
│                    │                                             │
│         X-Demo-Token header injected by api-client.ts           │
│                    │                                             │
└────────────────────┼─────────────────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │  FastAPI Backend       │
        │  /api/demo/*           │
        │  /api/sessions/*       │
        └────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
   ┌─────────┐  ┌──────────┐  ┌──────────────┐
   │ Demo    │  │ Sessions │  │ Middleware   │
   │ Router  │  │ Router   │  │ demo_auth    │
   │         │  │          │  │              │
   └─────────┘  └──────────┘  └──────────────┘
      │              │              │
      └──────────────┼──────────────┘
                     │
                     ▼
   ┌─────────────────────────────────────┐
   │  Supabase PostgreSQL Database       │
   ├─────────────────────────────────────┤
   │                                      │
   │  Users Table (with demo fields)     │
   │  ├── id, email, first_name          │
   │  ├── demo_token (unique)            │
   │  ├── demo_created_at                │
   │  ├── demo_expires_at                │
   │  └── role (therapist/patient)       │
   │                                      │
   │  Therapy Sessions Table             │
   │  ├── id, patient_id (FK→users)      │
   │  ├── therapist_id, session_date     │
   │  ├── transcript (JSON)              │
   │  ├── WAVE 1 DATA:                   │
   │  │   ├── mood_score, confidence     │
   │  │   ├── mood_rationale             │
   │  │   ├── mood_indicators[], tone    │
   │  │   ├── topics[], action_items[]   │
   │  │   ├── technique, summary         │
   │  │   ├── extraction_confidence      │
   │  │   ├── has_breakthrough           │
   │  │   ├── breakthrough_data          │
   │  │   └── wave1_completed_at         │
   │  ├── WAVE 2 DATA:                   │
   │  │   ├── deep_analysis (JSONB)      │
   │  │   └── deep_analyzed_at           │
   │  └── Timestamps...                  │
   │                                      │
   │  Breakthrough History Table         │
   │  ├── session_id (FK→sessions)       │
   │  ├── breakthrough_type, label       │
   │  ├── description, evidence          │
   │  ├── confidence_score, timestamp    │
   │  └── is_primary                     │
   │                                      │
   └─────────────────────────────────────┘
```

## Demo Initialization Flow

### Sequence Diagram

```
User             Frontend         Backend          Database
 │                  │                │                 │
 │ Click "Try Demo" │                │                 │
 ├─────────────────▶│                │                 │
 │                  │ POST           │                 │
 │                  │ /api/demo/init │                 │
 │                  ├───────────────▶│                 │
 │                  │                │ seed_demo_      │
 │                  │                │ user_sessions()│
 │                  │                ├────────────────▶│
 │                  │                │                 │
 │                  │                │ ✓ Create user  │
 │                  │                │ ✓ Set token    │
 │                  │                │ ✓ Load sessions│
 │                  │                │◀─────────────────
 │                  │ Return token   │
 │                  │◀───────────────┤
 │                  │                │
 │                  │ Save token to  │
 │                  │ localStorage   │
 │ Redirect to dashboard
 │◀─────────────────┤
 │                  │                │
 │ Visit /patient/  │                │
 │ dashboard        │                │
 │                  │ GET /api/      │
 │                  │ sessions/      │
 │                  │ patient/{id}   │
 │                  │ + X-Demo-Token │
 │                  ├───────────────▶│
 │                  │                │ Validate token│
 │                  │                │ Get patient_id│
 │                  │                │
 │                  │                │ SELECT * FROM │
 │                  │                │ therapy_      │
 │                  │                │ sessions      │
 │                  │                │ WHERE patient │
 │                  │                │ _id = ? 
 │                  │                ├────────────────▶│
 │                  │                │                 │
 │                  │                │ Return 10      │
 │                  │                │ sessions       │
 │                  │                │◀─────────────────
 │                  │ Sessions +     │
 │                  │ Analysis       │
 │                  │◀───────────────┤
 │                  │                │
 │ Display sessions│
 │ with mood,     │
 │ topics, deep   │
 │ insights       │
 │◀─────────────────┤
 │                  │                │
```

## Wave 1 & Wave 2 Analysis Pipeline

### What Happens During Demo Initialization

```
POST /api/demo/initialize
├── Generate demo_token (UUID)
├── Call seed_demo_user_sessions(demo_token) [SQL]
│   ├── Create user with demo_token
│   └── Load Sessions 1-10 (raw transcripts only)
│
├── OPTION A: Return immediately (Fast - user sees empty sessions)
│   └── Frontend shows "Loading analysis..." spinners
│
└── OPTION B: Run analysis before returning (Slow - ~15-30 min wait)
    ├── Wave 1 - FOR EACH SESSION 1-10:
    │   ├── MoodAnalyzer
    │   │   ├── Input: segments (patient only)
    │   │   ├── Call: GPT (gpt-5-nano) "Analyze mood"
    │   │   └── Output: mood_score, confidence, rationale, indicators
    │   │
    │   ├── TopicExtractor
    │   │   ├── Input: segments (therapist + patient)
    │   │   ├── Call: GPT (gpt-5-mini) "Extract topics"
    │   │   └── Output: topics[], actions[], technique, summary
    │   │
    │   └── BreakthroughDetector
    │       ├── Input: transcript, metadata
    │       ├── Call: GPT (gpt-5-mini) "Detect breakthroughs"
    │       └── Output: has_breakthrough, breakthrough_data
    │
    ├── Store Wave 1 Results in Database
    │   └── UPDATE therapy_sessions SET mood_score, topics, etc.
    │
    ├── Wave 2 - FOR EACH SESSION 1-10:
    │   ├── Get previous sessions from database (for context)
    │   ├── Build cumulative_context from Wave 2 results
    │   │   Session 1: None
    │   │   Session 2: {session_01_wave1, session_01_wave2}
    │   │   Session 3: {previous_context: {...}, session_02_wave1, session_02_wave2}
    │   │   ...and so on (nested structure)
    │   │
    │   └── DeepAnalyzer
    │       ├── Input: session, previous_sessions, cumulative_context
    │       ├── Call: GPT (gpt-5-mini) "Deep clinical analysis"
    │       └── Output: progress_indicators, insights, coping_skills
    │
    ├── Store Wave 2 Results in Database
    │   └── UPDATE therapy_sessions SET deep_analysis = {...}
    │
    └── Return demo_token to frontend
```

## Data Isolation Per Browser

### How Multiple Users Get Independent Data

```
Browser 1 (Chrome)          Browser 2 (Safari)
┌──────────────────┐        ┌──────────────────┐
│ localStorage     │        │ localStorage     │
│ ┌──────────────┐ │        │ ┌──────────────┐ │
│ │ demo_token   │ │        │ │ demo_token   │ │
│ │ abc-123-def  │ │        │ │ xyz-789-uvw  │ │
│ └──────────────┘ │        │ └──────────────┘ │
└────────┬─────────┘        └────────┬─────────┘
         │                           │
         │ X-Demo-Token: abc-123    │ X-Demo-Token: xyz-789
         ▼                           ▼
    Backend                      Backend
    Validates token             Validates token
    Gets patient_id: 111        Gets patient_id: 222
         │                           │
         ▼                           ▼
    Database                    Database
    SELECT * FROM therapy_sessions    SELECT * FROM therapy_sessions
    WHERE patient_id = 111            WHERE patient_id = 222
         │                           │
         ▼                           ▼
    Returns 10 sessions         Returns 10 sessions
    for Patient 111             for Patient 222
         │                           │
    Data completely            Data completely
    separate                    separate
```

## Component Interaction

### Demo Token Lifecycle

```
1. GENERATE
   ├─ UUID.generate() → unique demo_token
   └─ Store in users.demo_token

2. PERSIST
   ├─ Frontend saves to localStorage
   ├─ Key: therapybridge_demo_token
   └─ Persists across page reloads

3. USE
   ├─ API client reads from localStorage
   ├─ Adds X-Demo-Token header to every request
   └─ Backend validates token exists in users table

4. VALIDATE
   ├─ Demo middleware checks X-Demo-Token
   ├─ Looks up user by demo_token
   ├─ Gets patient_id from that user
   └─ All queries filtered by patient_id

5. EXPIRE
   ├─ Check: NOW() > users.demo_expires_at?
   ├─ If yes: Show "Demo expired" message
   ├─ If no: Continue using normally
   └─ Set to NOW() + 24 hours on creation

6. CLEAR
   ├─ User logs out or token expires
   ├─ Frontend calls demoTokenStorage.clearToken()
   ├─ Removes from localStorage
   └─ Can re-initialize for fresh demo
```

## Session Data Structure (One Session)

```
therapy_sessions.{session_id} =
{
  // Metadata
  "id": "session_01_abc123",
  "patient_id": "patient_111",
  "therapist_id": "therapist_222",
  "session_date": "2025-01-10T14:00:00Z",
  
  // Raw Data
  "transcript": [
    {
      "start": 0.0,
      "end": 28.4,
      "speaker": "SPEAKER_00",
      "speaker_id": "SPEAKER_00",
      "text": "Hi Alex, welcome..."
    },
    {
      "start": 28.4,
      "end": 45.8,
      "speaker": "SPEAKER_01",
      "speaker_id": "SPEAKER_01",
      "text": "Yeah, that makes sense. Um, I'm really nervous..."
    }
    // ... more segments
  ],
  
  // WAVE 1 RESULTS
  "mood_score": 3.5,
  "mood_confidence": 0.92,
  "mood_rationale": "Patient expresses overwhelming feelings and suicidal ideation...",
  "mood_indicators": ["hopelessness", "anhedonia", "suicidal thoughts", "overwhelm"],
  "emotional_tone": "distressed",
  
  "topics": ["Depression and suicidal ideation", "Relationship breakup"],
  "action_items": ["Safety planning", "Consider psychiatric evaluation"],
  "technique": "Crisis intervention",
  "summary": "First session focuses on crisis management. Patient presents with suicidal ideation.",
  "extraction_confidence": 0.88,
  
  "has_breakthrough": false,
  "breakthrough_data": null,
  
  "wave1_completed_at": "2025-12-23T18:30:00Z",
  
  // WAVE 2 RESULTS
  "deep_analysis": {
    "progress_indicators": {
      "symptom_reduction": {
        "description": "Patient still experiencing acute symptoms...",
        "trend": "worsening"
      },
      "skill_development": [
        "Basic grounding techniques introduced",
        "Coping strategies discussed"
      ],
      "goal_progress": [
        {
          "goal": "Maintain safety",
          "progress": 50,
          "status": "in_progress"
        }
      ]
    },
    "therapeutic_insights": {
      "key_realizations": [
        "Breakup triggered existing depression symptoms",
        "Perfectionism contributes to overwhelm"
      ],
      "patterns_identified": ["avoidance", "rumination"],
      "therapeutic_focus": "Crisis stabilization and safety"
    },
    "coping_skills": {
      "learned": ["grounding", "breathing_exercises"],
      "proficiency": {
        "grounding": "introduced",
        "breathing_exercises": "practicing"
      },
      "needs_reinforcement": ["distress_tolerance"]
    },
    "therapeutic_relationship": {
      "engagement_level": "cautious",
      "openness": "moderate",
      "alliance_strength": "developing",
      "client_comfort": "building"
    },
    "recommendations": {
      "practices": [
        "Daily safety check-ins",
        "Grounding exercise 3x daily",
        "Consider psychiatric evaluation for medication"
      ],
      "interventions": ["DBT skills", "Safety planning"],
      "session_focus_next": "Safety planning and coping skills"
    }
  },
  
  "deep_analyzed_at": "2025-12-23T18:45:00Z"
}
```

## Files That Work Together

### Backend

```
app/routers/demo.py
├── POST /api/demo/initialize
│   ├── Calls seed_demo_user_sessions() [SQL]
│   ├── Returns demo_token + patient_id
│   └── (Future: trigger Wave 1+2 scripts)
│
├── POST /api/demo/reset
│   ├── Deletes all sessions for demo user
│   └── Re-seeds with fresh 10 sessions
│
└── GET /api/demo/status
    └── Returns session count, expiry date

app/routers/sessions.py
├── GET /api/sessions/patient/{patient_id}
│   ├── Middleware validates X-Demo-Token
│   ├── Gets patient_id from demo user
│   ├── Returns sessions WHERE patient_id = ?
│   └── Includes Wave 1 + Wave 2 data
│
├── GET /api/sessions/{session_id}
│   └── Returns single session with all analysis
│
└── ... other endpoints

app/middleware/demo_auth.py
├── get_demo_user() - Validates X-Demo-Token
├── require_demo_auth - Forces token validation
└── Sets demo_user context for session

database.py
├── get_supabase() - Main client
├── get_supabase_admin() - Bypasses RLS
└── Query helpers

scripts/seed_wave1_analysis.py [MISSING]
├── Takes patient_id
├── Loads Sessions 1-10 JSON
├── Runs Wave 1 for each session
└── Updates database

scripts/seed_wave2_analysis.py [MISSING]
├── Takes patient_id
├── Loads Sessions from database
├── Builds cumulative context
├── Runs Wave 2 for each session
└── Updates database

services/mood_analyzer.py
├── analyze_session_mood(session_id, segments)
└── Returns MoodAnalysis

services/topic_extractor.py
├── extract_metadata(session_id, segments)
└── Returns SessionMetadata

services/breakthrough_detector.py
├── analyze_session(transcript, metadata)
└── Returns BreakthroughAnalysis

services/deep_analyzer.py
├── analyze_session(session_id, context, cumulative_context)
└── Returns DeepAnalysis
```

### Frontend

```
lib/demo-token-storage.ts
├── saveToken(token, patientId, expiresAt)
├── getToken()
├── getPatientId()
├── getExpiresAt()
├── isExpired()
├── clearToken()
└── hasValidToken()

lib/demo-api-client.ts
├── initialize() - Calls /api/demo/initialize
├── reset() - Calls /api/demo/reset
├── getStatus() - Calls /api/demo/status
└── uploadDemoTranscript() - For future use

lib/api-client.ts
├── Reads demo token from localStorage
├── Adds X-Demo-Token header if exists
├── Falls back to Bearer auth if no demo token
└── All authenticated requests use demo token

lib/auth.ts
├── signUp() - Regular auth
├── signIn() - Regular auth
├── signOut() - Regular auth
└── (Demo bypasses this entirely)

app/page.tsx [NEEDS DEMO BUTTON]
├── "Try Demo" button
└── Calls demoApiClient.initialize()

app/patient/dashboard-v3/page.tsx
├── Loads sessions via api-client.get()
├── X-Demo-Token header auto-injected
├── Displays mood, topics, insights
└── All data filtered by patient_id from token
```

---

## Cost Analysis

### Per Demo User (One-Time Cost)

**Wave 1 Analysis:**
- 10 sessions × 3 calls (mood, topics, breakthrough)
- = 30 GPT calls
- gpt-5-nano @ $0.0006/1K tokens
- gpt-5-mini @ $0.001/1K tokens
- Average cost: ~$0.03

**Wave 2 Analysis:**
- 10 sessions × 1 deep analysis call
- = 10 GPT calls
- gpt-5-mini @ $0.001/1K tokens
- Average cost: ~$0.03

**Total per user:** ~$0.06

### Optimization Options

1. **Pre-seed all analysis** (run once at deploy)
   - Cost: $0.06 initial
   - Cost per demo user: $0 (just copy database rows)

2. **Cache results** (store pre-analyzed sessions)
   - Cost: $0.06 initial
   - Cost per demo user: $0 (use cache)

3. **Batch parallel processing** (run all 10 at once)
   - Cost: $0.06 initial
   - Speed: 5-10 min instead of 15-30 min

---

## Security Considerations

### Demo Token Validation

1. **Frontend:** localStorage contains demo_token
   - SameSite cookie policies don't apply (localStorage)
   - XSS vulnerability could steal token
   - Mitigation: Don't store sensitive data in localStorage for production

2. **Backend:** Validates X-Demo-Token header
   - Checks token exists in users.demo_token
   - Gets patient_id from that user
   - All queries filtered by patient_id (RLS enforces)

3. **Database:** Row-level security policies
   - therapy_sessions.patient_id must match authenticated user
   - Demo auth sets patient_id context
   - Prevents cross-user data leakage

### No Demo Data Leakage

- Each browser gets unique demo_token
- Each token maps to unique patient_id
- Queries filtered by patient_id
- Timeout after 24 hours
- No shared data between demo users

