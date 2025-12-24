# Demo System - Complete Architecture Summary

## Overview

The demo system allows users to instantly experience TherapyBridge with 10 pre-loaded therapy sessions, complete with AI analysis (mood tracking, topic extraction, breakthrough detection, and deep clinical insights).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Experience                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Clicks "Try Demo" on landing page                          │
│  2. Gets unique demo_token (stored in localStorage)            │
│  3. Redirected to dashboard with 10 sessions                   │
│  4. AI analysis runs in background (10-20 min)                 │
│  5. Dashboard progressively enhances as analysis completes     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Components:                                                    │
│  • app/page.tsx - Landing page with "Try Demo" button          │
│  • lib/demo-api-client.ts - Demo API wrapper                   │
│  • lib/demo-token-storage.ts - localStorage management         │
│                                                                 │
│  Flow:                                                          │
│  1. demoApiClient.initialize() → POST /api/demo/initialize     │
│  2. Store demo_token in localStorage                           │
│  3. Auto-inject X-Demo-Token header in all API calls           │
│  4. Poll /api/demo/status for analysis progress                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Backend Layer                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Middleware: app/middleware/demo_auth.py                        │
│  • Extracts X-Demo-Token from headers                          │
│  • Validates token and checks expiry                           │
│  • Injects demo_user into request                              │
│                                                                 │
│  Router: app/routers/demo.py                                    │
│  • POST /api/demo/initialize - Create demo user                │
│  • GET /api/demo/status - Check analysis progress              │
│  • POST /api/demo/reset - Reset demo sessions                  │
│                                                                 │
│  Background Tasks:                                              │
│  • run_wave1_analysis_background() - Calls Wave 1 script       │
│  • run_wave2_analysis_background() - Calls Wave 2 script       │
│  • run_full_analysis_pipeline() - Runs both sequentially       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Database Layer                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SQL Function: seed_demo_user_sessions(p_demo_token UUID)      │
│  • Creates demo patient user (demo_token, demo_expires_at)     │
│  • Creates demo therapist user (Dr. Maria Rodriguez)           │
│  • Inserts 10 therapy sessions with transcript excerpts        │
│  • Returns user_id, session_ids[], sessions_created            │
│                                                                 │
│  Tables:                                                        │
│  • users - demo_token, demo_expires_at fields                  │
│  • therapy_sessions - All Wave 1 & Wave 2 fields               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Analysis Pipeline (Async)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Wave 1: scripts/seed_wave1_analysis.py                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ For each of 10 sessions:                                │   │
│  │ 1. Mood Analyzer (GPT-4o-mini)                          │   │
│  │    → mood_score, confidence, rationale, indicators      │   │
│  │ 2. Topic Extractor (GPT-4o-mini)                        │   │
│  │    → topics, action_items, technique, summary           │   │
│  │ 3. Breakthrough Detector (GPT-4)                        │   │
│  │    → has_breakthrough, breakthrough_data                │   │
│  │                                                          │   │
│  │ Result: 30 AI calls, ~$0.03, 5-10 minutes               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Wave 2: scripts/seed_wave2_analysis.py                        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ For each session (chronologically):                     │   │
│  │ 1. Build cumulative context from all previous sessions  │   │
│  │    Session 1: No context                                │   │
│  │    Session 2: {session_01_wave1, session_01_wave2}      │   │
│  │    Session 3: {prev_ctx, session_02_wave1, wave2}       │   │
│  │    Session 4: {prev_ctx: {prev_ctx}, session_03...}     │   │
│  │                                                          │   │
│  │ 2. Deep Analyzer (GPT-4o) with cumulative context       │   │
│  │    → progress_indicators, therapeutic_insights,         │   │
│  │      coping_skills, therapeutic_relationship,           │   │
│  │      recommendations                                    │   │
│  │                                                          │   │
│  │ Result: 10 AI calls, ~$0.03, 5-10 minutes               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Total: 40 AI calls, ~$0.06, 10-20 minutes                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagram

```
User Action                  System Response                      Database State
───────────                  ───────────────                      ──────────────

Click "Try Demo"
      │
      ├─────────────────→  Generate demo_token (UUID)
      │                   Call seed_demo_user_sessions()
      │                                                    ─────→  INSERT users
      │                                                            INSERT therapy_sessions × 10
      │                   Return: patient_id, session_ids
      │                   Queue: run_full_analysis_pipeline()
      │
      ←─────────────────  Response: demo_token, session_ids
                          analysis_status: "processing"

Store token in localStorage
Redirect to /patient/dashboard-v3
      │
      ├─────────────────→  GET /api/sessions?patient_id=...
      │                   (X-Demo-Token header auto-injected)
      │                                                    ─────→  SELECT therapy_sessions
      ←─────────────────  Return: 10 sessions (no AI data yet)    WHERE patient_id = ?

Dashboard renders sessions
(AI fields empty/loading)

─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─
Background Process (async)
─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─

      │
      ├─────────────────→  Wave 1 Analysis (5-10 min)
      │                   For each session:
      │                   • Mood Analyzer
      │                   • Topic Extractor
      │                   • Breakthrough Detector
      │                                                    ─────→  UPDATE therapy_sessions
      │                                                            SET mood_score, topics, etc.

Poll /api/demo/status
      │
      ├─────────────────→  GET /api/demo/status
      │                                                    ─────→  COUNT sessions WHERE mood_score IS NOT NULL
      ←─────────────────  analysis_status: "wave1_complete"
                          wave1_complete: 10, wave2_complete: 0

Dashboard refreshes
(Wave 1 data now visible)

      │
      ├─────────────────→  Wave 2 Analysis (5-10 min)
      │                   For each session (chronological):
      │                   • Build cumulative context
      │                   • Deep Analyzer with context
      │                                                    ─────→  UPDATE therapy_sessions
      │                                                            SET deep_analysis = {...}

Poll /api/demo/status
      │
      ├─────────────────→  GET /api/demo/status
      │                                                    ─────→  COUNT sessions WHERE deep_analysis IS NOT NULL
      ←─────────────────  analysis_status: "wave2_complete"
                          wave1_complete: 10, wave2_complete: 10

Dashboard refreshes
(All AI data visible) ✅
```

---

## Multi-Browser Isolation

```
Browser A                      Browser B (Incognito)
─────────                      ──────────────────────

localStorage:                  localStorage:
  demo_token: abc-123            demo_token: xyz-789
       │                              │
       │                              │
       ├──────────────┐               ├──────────────┐
       │              │               │              │
       ▼              ▼               ▼              ▼
  X-Demo-Token:  X-Demo-Token:   X-Demo-Token:  X-Demo-Token:
    abc-123        abc-123          xyz-789        xyz-789
       │              │               │              │
       ▼              ▼               ▼              ▼
Middleware:       Middleware:     Middleware:    Middleware:
 Validate token    Validate token  Validate token Validate token
       │              │               │              │
       ▼              ▼               ▼              ▼
WHERE patient_id  WHERE patient_id WHERE patient_id WHERE patient_id
  = user_1          = user_1         = user_2         = user_2
       │              │               │              │
       ▼              ▼               ▼              ▼
  10 sessions     10 sessions      10 sessions    10 sessions
  (User 1 data)   (User 1 data)    (User 2 data)  (User 2 data)

  ✅ Isolated                       ✅ Isolated
```

**Result:** Each browser gets completely separate demo data. No cross-contamination.

---

## Cumulative Context Structure (Wave 2)

```
Session 1
├─ Context: None
└─ Analysis: Deep insights based only on Session 1

Session 2
├─ Context:
│  ├─ session_01_wave1: {mood, topics, breakthrough}
│  └─ session_01_wave2: {deep_analysis}
└─ Analysis: Deep insights comparing Session 2 to Session 1

Session 3
├─ Context:
│  ├─ previous_context:
│  │  ├─ session_01_wave1
│  │  └─ session_01_wave2
│  ├─ session_02_wave1
│  └─ session_02_wave2
└─ Analysis: Deep insights tracking progress across 3 sessions

Session 4
├─ Context:
│  ├─ previous_context:
│  │  ├─ previous_context:
│  │  │  ├─ session_01_wave1
│  │  │  └─ session_01_wave2
│  │  ├─ session_02_wave1
│  │  └─ session_02_wave2
│  ├─ session_03_wave1
│  └─ session_03_wave2
└─ Analysis: Deep insights tracking full therapeutic journey

...continues nesting through Session 10
```

**Result:** Each session analysis has full awareness of all previous sessions, creating a coherent "therapeutic journey" narrative.

---

## File Structure

```
peerbridge proj/
├── backend/
│   ├── app/
│   │   ├── routers/
│   │   │   └── demo.py ✨ Demo API endpoints + background tasks
│   │   ├── middleware/
│   │   │   └── demo_auth.py ✨ Token validation
│   │   └── services/
│   │       ├── mood_analyzer.py ✨ Wave 1: Mood analysis
│   │       ├── topic_extractor.py ✨ Wave 1: Topic extraction
│   │       ├── breakthrough_detector.py ✨ Wave 1: Breakthrough detection
│   │       └── deep_analyzer.py ✨ Wave 2: Deep clinical insights
│   └── scripts/
│       ├── seed_wave1_analysis.py ✨ NEW - Wave 1 pipeline
│       └── seed_wave2_analysis.py ✨ NEW - Wave 2 pipeline
│
├── frontend/
│   ├── app/
│   │   └── page.tsx ✨ UPDATED - Landing page with "Try Demo"
│   └── lib/
│       ├── demo-api-client.ts ✨ Demo API wrapper
│       └── demo-token-storage.ts ✨ localStorage management
│
├── supabase/
│   └── migrations/
│       └── 005_seed_demo_function.sql ✨ NEW - Demo user seeding
│
└── Documentation/
    ├── DEMO_INTEGRATION_COMPLETE.md ✨ NEW - Full documentation
    ├── DEMO_QUICK_START.md ✨ NEW - Quick start guide
    └── DEMO_SYSTEM_SUMMARY.md ✨ NEW - This file
```

---

## API Endpoints

### POST `/api/demo/initialize?run_analysis=true`
**Purpose:** Create demo user with 10 sessions
**Auth:** None required
**Response:**
```json
{
  "demo_token": "abc-123",
  "patient_id": "user-uuid",
  "session_ids": ["session-1", "session-2", ...],
  "expires_at": "2025-12-24T...",
  "analysis_status": "processing",
  "message": "Demo initialized with 10 sessions..."
}
```

### GET `/api/demo/status`
**Purpose:** Check analysis progress
**Auth:** X-Demo-Token header
**Response:**
```json
{
  "demo_token": "abc-123",
  "patient_id": "user-uuid",
  "session_count": 10,
  "analysis_status": "wave2_complete",
  "wave1_complete": 10,
  "wave2_complete": 10,
  "is_expired": false
}
```

### POST `/api/demo/reset`
**Purpose:** Delete sessions and re-seed
**Auth:** X-Demo-Token header
**Response:**
```json
{
  "patient_id": "user-uuid",
  "session_ids": ["new-session-1", ...],
  "message": "Demo reset with 10 fresh sessions"
}
```

---

## Performance Characteristics

| Phase | Duration | Cost | Blocking |
|-------|----------|------|----------|
| User clicks "Try Demo" | <1 sec | $0 | ✅ Yes (fast) |
| SQL seed function | <1 sec | $0 | ✅ Yes (fast) |
| Redirect to dashboard | <1 sec | $0 | ✅ Yes (fast) |
| Wave 1 analysis | 5-10 min | $0.03 | ❌ No (background) |
| Wave 2 analysis | 5-10 min | $0.03 | ❌ No (background) |
| **Total** | **10-20 min** | **$0.06** | **Non-blocking** |

**User Experience:** Instant access to dashboard, AI analysis progressively appears.

---

## Security & Expiry

- **Token format:** UUID v4 (cryptographically random)
- **Expiry:** 24 hours from creation
- **Storage:** Browser localStorage (client-side only)
- **Validation:** Every API call checks token validity and expiry
- **Cleanup:** Expired demo users can be purged via cron job

---

## Scalability

### Current (On-Demand):
- 1 demo user = 40 AI calls = $0.06
- 100 users/day = $6/day = $180/month
- Analysis time: 10-20 minutes per user

### Future (Pre-Seeded):
- Pre-create 100 demo users offline
- Assign next available user on `/initialize`
- Result: $6 upfront cost, instant access for 100 users
- Replenish pool when count drops below threshold

---

## Next Steps

1. **Apply SQL migration:** `005_seed_demo_function.sql`
2. **Test initialization:** `POST /api/demo/initialize`
3. **Test Wave 1 script:** `python scripts/seed_wave1_analysis.py <patient_id>`
4. **Test Wave 2 script:** `python scripts/seed_wave2_analysis.py <patient_id>`
5. **Test frontend:** Click "Try Demo" button
6. **Test isolation:** Multiple browsers get separate data
7. **Monitor progress:** Poll `/api/demo/status`

---

**Status:** ✅ All components built and integrated. Ready for testing.
