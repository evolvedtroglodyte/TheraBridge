# Hackathon Demo Mode Implementation Plan

## Overview

Build a fully-functional demo mode for TherapyBridge hackathon presentation where users can explore the platform with 10 pre-loaded therapy sessions (fully AI-analyzed) and upload 2 additional demo transcripts to showcase real-time AI processing. No authentication required - each visitor gets an isolated demo environment via localStorage token.

## Current State Analysis

**Existing Infrastructure:**
- Backend: FastAPI with Supabase PostgreSQL database
- Frontend: Next.js 16 with React 19, dashboard at `/dashboard`
- Database tables: `users`, `therapy_sessions`, `breakthrough_history`
- AI Analysis pipeline: Mood, Topics, Breakthrough, Deep Analysis (GPT-4o-mini)
- Upload flow: `/upload` page with FileUploader and AudioRecorder components
- Navigation: NavigationBar component with Dashboard/Sessions/Upload/Ask AI tabs
- Mock data: 12 complete therapy session JSONs in `mock-therapy-data/sessions/`

**Current Limitations:**
- No demo/temporary user support
- No token-based authentication alternative
- No pre-seeded session data
- No data cleanup mechanism
- Upload page only handles audio files (not JSON transcripts)

## Desired End State

**User Experience:**
1. User visits Railway deployment → Dashboard loads with 10 pre-analyzed sessions
2. User browses sessions, views transcripts, sees AI insights (mood, topics, breakthroughs)
3. User navigates to `/upload` → Clicks "Upload Demo Session" → Selects from dropdown
4. Real AI analysis runs (7-10 seconds) with progress indicators
5. Dashboard auto-refreshes showing new session card with all AI features
6. User can repeat upload for 2nd demo session
7. User clicks "Reset Demo" in navbar → Confirmation modal → Fresh 10 sessions restored
8. After 24 hours, demo data auto-deletes via Supabase cron function

**Technical Implementation:**
- Demo user created on first visit with UUID token stored in localStorage
- Each demo user gets isolated copy of 10 sessions in Supabase
- Backend accepts `X-Demo-Token` header for demo authentication
- Frontend tracks demo state and manages token lifecycle
- SQL seed script populates demo sessions with full AI analysis data
- SQL cleanup function removes demo users/sessions older than 24h

### Key Discoveries:

**Database Schema (`backend/app/database.py`, `backend/app/routers/sessions.py`):**
- `users` table: Contains both therapists and patients with `role` field
- `therapy_sessions` table: Requires `patient_id`, `therapist_id` foreign keys
- Sessions have extensive AI fields: `mood_score`, `topics`, `action_items`, `breakthrough_data`, etc.
- No existing demo/temporary user infrastructure

**Upload Flow (`frontend/app/upload/page.tsx:26-32`):**
- Currently handles File objects from FileUploader/AudioRecorder
- Triggers ProcessingContext to track status
- Needs extension to handle JSON transcript uploads

**Navigation (`frontend/components/NavigationBar.tsx:81-174`):**
- Top bar with logo, theme toggle, nav links, and right-side branding
- Right section (170-173) is perfect location for Reset Demo button

**Mock Data Structure (`mock-therapy-data/sessions/session_01_crisis_intake.json:1-100`):**
- Each JSON has: `id`, `status`, `filename`, `metadata`, `speakers`, `segments`
- Segments format: `{start, end, text, speaker, speaker_id}`
- Ready to use for transcript uploads

## What We're NOT Doing

- ❌ Real user authentication or login system (demo only)
- ❌ WebSocket connections for real-time updates (using polling)
- ❌ Audio file uploads (JSON transcripts only for demo)
- ❌ Therapist view or multi-role support (patient view only)
- ❌ Data persistence beyond 24 hours
- ❌ Production-grade security (demo tokens are not encrypted)
- ❌ Email notifications or verification
- ❌ Payment or subscription features
- ❌ Mobile app or responsive optimization beyond existing
- ❌ Multiple demo environments (single shared database)

## Implementation Approach

**Strategy:** Start with database foundation, build backend API layer, then frontend integration. Each phase is independently testable.

**Key Principles:**
1. **Isolation First**: Each demo user gets completely separate data
2. **Real AI Analysis**: No mocking - hit actual OpenAI APIs for demo uploads
3. **Minimal Schema Changes**: Add demo fields to existing tables vs new tables
4. **Reuse Existing Code**: Leverage ProcessingContext, SessionDataProvider, API client
5. **Progressive Enhancement**: Demo mode doesn't break existing functionality

---

## Phase 1: Database Schema & Demo Data Preparation

### Overview
Add demo support to Supabase schema and create seed script with 10 fully-analyzed sessions per demo user.

### Changes Required:

#### 1.1 Database Schema Migration

**File**: `backend/supabase/migrations/007_add_demo_mode_support.sql` ✅
**Changes**: Add demo fields to users table

```sql
-- Migration: Add demo mode support
-- Date: 2025-12-23
-- Purpose: Enable temporary demo users with token-based access

-- Add demo fields to users table
ALTER TABLE users
ADD COLUMN IF NOT EXISTS demo_token UUID UNIQUE,
ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS demo_created_at TIMESTAMP DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS demo_expires_at TIMESTAMP;

-- Index for fast demo token lookups
CREATE INDEX IF NOT EXISTS idx_users_demo_token
ON users(demo_token)
WHERE demo_token IS NOT NULL;

-- Index for cleanup queries
CREATE INDEX IF NOT EXISTS idx_users_demo_expiry
ON users(demo_expires_at)
WHERE is_demo = TRUE;

-- Comments for documentation
COMMENT ON COLUMN users.demo_token IS 'Unique UUID for demo user authentication (stored in localStorage)';
COMMENT ON COLUMN users.is_demo IS 'Flag indicating temporary demo user (auto-deleted after 24h)';
COMMENT ON COLUMN users.demo_created_at IS 'Timestamp when demo user was created';
COMMENT ON COLUMN users.demo_expires_at IS 'Timestamp when demo user should be deleted (24h after creation)';
```

#### 1.2 Demo Data Seed Script

**File**: `backend/supabase/seed_demo_data.sql` ✅
**Changes**: Create reusable function to populate demo user with 10 sessions

```sql
-- Demo Data Seed Function
-- Creates a demo user (therapist + patient) and populates 10 fully-analyzed sessions
-- Call this function for each new demo user initialization

CREATE OR REPLACE FUNCTION seed_demo_user_sessions(p_demo_token UUID)
RETURNS TABLE(patient_id UUID, session_ids UUID[])
LANGUAGE plpgsql
AS $$
DECLARE
    v_therapist_id UUID;
    v_patient_id UUID;
    v_session_id UUID;
    v_session_ids UUID[] := '{}';
    v_session_date TIMESTAMP;
BEGIN
    -- Create demo therapist
    INSERT INTO users (
        email,
        first_name,
        last_name,
        role,
        is_demo,
        demo_token,
        demo_created_at,
        demo_expires_at,
        hashed_password
    ) VALUES (
        'therapist_' || p_demo_token || '@demo.therapybridge.com',
        'Dr. Sarah',
        'Rodriguez',
        'therapist',
        TRUE,
        p_demo_token,
        NOW(),
        NOW() + INTERVAL '24 hours',
        'demo_no_password'
    ) RETURNING id INTO v_therapist_id;

    -- Create demo patient
    INSERT INTO users (
        email,
        first_name,
        last_name,
        role,
        is_demo,
        demo_token,
        demo_created_at,
        demo_expires_at,
        hashed_password
    ) VALUES (
        'patient_' || p_demo_token || '@demo.therapybridge.com',
        'Alex',
        'Chen',
        'patient',
        TRUE,
        p_demo_token,
        NOW(),
        NOW() + INTERVAL '24 hours',
        'demo_no_password'
    ) RETURNING id INTO v_patient_id;

    -- Session 1: Crisis Intake (2025-01-10)
    v_session_date := '2025-01-10 14:00:00'::TIMESTAMP;
    INSERT INTO therapy_sessions (
        patient_id, therapist_id, session_date, duration_minutes,
        processing_status, analysis_status,
        transcript, mood_score, mood_confidence, mood_rationale,
        mood_indicators, emotional_tone, mood_analyzed_at,
        topics, action_items, technique, summary, extraction_confidence, topics_extracted_at,
        has_breakthrough, breakthrough_label, breakthrough_data, breakthrough_analyzed_at
    ) VALUES (
        v_patient_id, v_therapist_id, v_session_date, 60,
        'completed', 'deep_complete',
        (SELECT jsonb_agg(jsonb_build_object(
            'start', (row_number() OVER () - 1) * 30.0,
            'end', row_number() OVER () * 30.0,
            'speaker', CASE WHEN row_number() OVER () % 2 = 0 THEN 'SPEAKER_00' ELSE 'SPEAKER_01' END,
            'text', text
        )) FROM (VALUES
            ('Hi Alex, welcome. I''m Dr. Rodriguez. Everything we discuss is private unless you''re in danger.'),
            ('Yeah, I''m really nervous. My roommate pushed me to make this appointment.'),
            ('It takes courage to reach out. What brings you in today?'),
            ('Everything feels overwhelming. I broke up with my partner two weeks ago, and school is a mess.')
        ) AS t(text)),
        3.5, 0.92, 'Patient presenting with acute distress following relationship breakup. Passive suicidal ideation noted without plan or intent. Severe overwhelm and functional impairment.',
        '["passive suicidal ideation", "relationship loss", "academic stress", "social withdrawal"]'::jsonb,
        'Distressed, overwhelmed, hopeless',
        v_session_date,
        '["Crisis Assessment", "Suicidal Ideation"]'::jsonb,
        '["Create safety plan with emergency contacts", "Schedule follow-up within 3 days"]'::jsonb,
        'CBT - Safety Planning',
        'Crisis intake for recent breakup with passive SI, safety plan created',
        0.95,
        v_session_date,
        TRUE,
        'Crisis Intake',
        '{"type": "First Session", "description": "Initial crisis assessment revealing significant distress", "confidence": 0.95}'::jsonb,
        v_session_date
    ) RETURNING id INTO v_session_id;
    v_session_ids := array_append(v_session_ids, v_session_id);

    -- Session 2: Emotional Regulation (2025-01-13)
    v_session_date := '2025-01-13 14:00:00'::TIMESTAMP;
    INSERT INTO therapy_sessions (
        patient_id, therapist_id, session_date, duration_minutes,
        processing_status, analysis_status,
        transcript, mood_score, mood_confidence, mood_rationale,
        mood_indicators, emotional_tone, mood_analyzed_at,
        topics, action_items, technique, summary, extraction_confidence, topics_extracted_at,
        has_breakthrough, breakthrough_analyzed_at
    ) VALUES (
        v_patient_id, v_therapist_id, v_session_date, 60,
        'completed', 'deep_complete',
        '[]'::jsonb,
        4.0, 0.88, 'Patient showing slight improvement in distress tolerance. Beginning to engage with DBT skills.',
        '["emotional dysregulation", "skill practice", "reduced SI"]'::jsonb,
        'Cautiously hopeful',
        v_session_date,
        '["DBT Skills Training", "Emotional Regulation"]'::jsonb,
        '["Practice TIPP skill daily", "Complete thought record for breakup grief"]'::jsonb,
        'DBT - Distress Tolerance',
        'Introduced TIPP and distress tolerance skills, reduced SI',
        0.91,
        v_session_date,
        FALSE,
        v_session_date
    ) RETURNING id INTO v_session_id;
    v_session_ids := array_append(v_session_ids, v_session_id);

    -- Session 3: ADHD Discovery (2025-01-20)
    v_session_date := '2025-01-20 14:00:00'::TIMESTAMP;
    INSERT INTO therapy_sessions (
        patient_id, therapist_id, session_date, duration_minutes,
        processing_status, analysis_status,
        transcript, mood_score, mood_confidence, mood_rationale,
        mood_indicators, emotional_tone, mood_analyzed_at,
        topics, action_items, technique, summary, extraction_confidence, topics_extracted_at,
        has_breakthrough, breakthrough_label, breakthrough_data, breakthrough_analyzed_at
    ) VALUES (
        v_patient_id, v_therapist_id, v_session_date, 60,
        'completed', 'deep_complete',
        '[]'::jsonb,
        5.5, 0.94, 'Major breakthrough: Patient connected lifelong struggles to potential ADHD. Significant relief and validation.',
        '["ADHD recognition", "validation", "reframing past failures"]'::jsonb,
        'Relieved, validated, hopeful',
        v_session_date,
        '["ADHD Assessment", "Executive Function"]'::jsonb,
        '["Complete ADHD screening questionnaire", "Research psychiatrists for evaluation"]'::jsonb,
        'Psychoeducation - ADHD',
        'Patient recognized ADHD patterns, major reframing of past struggles',
        0.97,
        v_session_date,
        TRUE,
        'ADHD Discovery',
        '{"type": "Insight Breakthrough", "description": "Patient connected lifelong executive function struggles to ADHD, major cognitive reframe", "confidence": 0.97}'::jsonb,
        v_session_date
    ) RETURNING id INTO v_session_id;
    v_session_ids := array_append(v_session_ids, v_session_id);

    -- Session 4: Medication Start (2025-01-27)
    v_session_date := '2025-01-27 14:00:00'::TIMESTAMP;
    INSERT INTO therapy_sessions (
        patient_id, therapist_id, session_date, duration_minutes,
        processing_status, analysis_status,
        transcript, mood_score, mood_confidence, mood_rationale,
        mood_indicators, emotional_tone, mood_analyzed_at,
        topics, action_items, technique, summary, extraction_confidence, topics_extracted_at,
        has_breakthrough, breakthrough_analyzed_at
    ) VALUES (
        v_patient_id, v_therapist_id, v_session_date, 60,
        'completed', 'deep_complete',
        '[]'::jsonb,
        6.0, 0.89, 'Patient started ADHD medication. Experiencing initial positive effects on focus and task completion.',
        '["medication adjustment", "improved focus", "reduced overwhelm"]'::jsonb,
        'Optimistic, energized',
        v_session_date,
        '["Medication Management", "ADHD Treatment"]'::jsonb,
        '["Track medication effects in journal", "Monitor sleep and appetite"]'::jsonb,
        'Psychopharmacology - Stimulant Meds',
        'Started Adderall, noticing improved focus and task completion',
        0.90,
        v_session_date,
        FALSE,
        v_session_date
    ) RETURNING id INTO v_session_id;
    v_session_ids := array_append(v_session_ids, v_session_id);

    -- Session 5: Family Conflict (2025-02-03)
    v_session_date := '2025-02-03 14:00:00'::TIMESTAMP;
    INSERT INTO therapy_sessions (
        patient_id, therapist_id, session_date, duration_minutes,
        processing_status, analysis_status,
        transcript, mood_score, mood_confidence, mood_rationale,
        mood_indicators, emotional_tone, mood_analyzed_at,
        topics, action_items, technique, summary, extraction_confidence, topics_extracted_at,
        has_breakthrough, breakthrough_analyzed_at
    ) VALUES (
        v_patient_id, v_therapist_id, v_session_date, 60,
        'completed', 'deep_complete',
        '[]'::jsonb,
        5.0, 0.87, 'Family tension around coming out. Patient navigating identity disclosure fears.',
        '["family conflict", "identity anxiety", "anticipatory grief"]'::jsonb,
        'Anxious, conflicted',
        v_session_date,
        '["Family Dynamics", "LGBTQ+ Identity"]'::jsonb,
        '["Draft coming out letter (not to send yet)", "Identify support network"]'::jsonb,
        'ACT - Values Clarification',
        'Processed family tension and coming out fears, values work',
        0.88,
        v_session_date,
        FALSE,
        v_session_date
    ) RETURNING id INTO v_session_id;
    v_session_ids := array_append(v_session_ids, v_session_id);

    -- Session 6: Spring Break Hope (2025-02-17)
    v_session_date := '2025-02-17 14:00:00'::TIMESTAMP;
    INSERT INTO therapy_sessions (
        patient_id, therapist_id, session_date, duration_minutes,
        processing_status, analysis_status,
        transcript, mood_score, mood_confidence, mood_rationale,
        mood_indicators, emotional_tone, mood_analyzed_at,
        topics, action_items, technique, summary, extraction_confidence, topics_extracted_at,
        has_breakthrough, breakthrough_analyzed_at
    ) VALUES (
        v_patient_id, v_therapist_id, v_session_date, 60,
        'completed', 'deep_complete',
        '[]'::jsonb,
        7.0, 0.91, 'Sustained improvement. Patient experiencing joy and hope about future. ADHD medication effective.',
        '["sustained improvement", "future orientation", "social engagement"]'::jsonb,
        'Hopeful, energized',
        v_session_date,
        '["Progress Consolidation", "Spring Break Planning"]'::jsonb,
        '["Plan one social activity over break", "Continue medication compliance"]'::jsonb,
        'Positive Psychology - Savoring',
        'Celebrated progress, spring break planning with hope',
        0.93,
        v_session_date,
        FALSE,
        v_session_date
    ) RETURNING id INTO v_session_id;
    v_session_ids := array_append(v_session_ids, v_session_id);

    -- Session 7: Dating Anxiety (2025-03-03)
    v_session_date := '2025-03-03 14:00:00'::TIMESTAMP;
    INSERT INTO therapy_sessions (
        patient_id, therapist_id, session_date, duration_minutes,
        processing_status, analysis_status,
        transcript, mood_score, mood_confidence, mood_rationale,
        mood_indicators, emotional_tone, mood_analyzed_at,
        topics, action_items, technique, summary, extraction_confidence, topics_extracted_at,
        has_breakthrough, breakthrough_analyzed_at
    ) VALUES (
        v_patient_id, v_therapist_id, v_session_date, 60,
        'completed', 'deep_complete',
        '[]'::jsonb,
        6.5, 0.86, 'New dating relationship triggering attachment anxieties. Navigating vulnerability.',
        '["relationship anxiety", "attachment patterns", "vulnerability"]'::jsonb,
        'Anxious but engaged',
        v_session_date,
        '["Dating Anxiety", "Attachment"]'::jsonb,
        '["Practice self-soothing when anxious", "Communicate needs to partner"]'::jsonb,
        'Attachment Theory - Secure Base',
        'New relationship triggering attachment anxiety, practiced grounding',
        0.89,
        v_session_date,
        FALSE,
        v_session_date
    ) RETURNING id INTO v_session_id;
    v_session_ids := array_append(v_session_ids, v_session_id);

    -- Session 8: Relationship Boundaries (2025-03-10)
    v_session_date := '2025-03-10 14:00:00'::TIMESTAMP;
    INSERT INTO therapy_sessions (
        patient_id, therapist_id, session_date, duration_minutes,
        processing_status, analysis_status,
        transcript, mood_score, mood_confidence, mood_rationale,
        mood_indicators, emotional_tone, mood_analyzed_at,
        topics, action_items, technique, summary, extraction_confidence, topics_extracted_at,
        has_breakthrough, breakthrough_analyzed_at
    ) VALUES (
        v_patient_id, v_therapist_id, v_session_date, 60,
        'completed', 'deep_complete',
        '[]'::jsonb,
        7.5, 0.90, 'Patient successfully set boundaries in new relationship. Feeling empowered and secure.',
        '["boundary setting", "assertiveness", "relationship health"]'::jsonb,
        'Proud, confident',
        v_session_date,
        '["Healthy Boundaries", "Communication Skills"]'::jsonb,
        '["Continue assertive communication practice", "Notice boundary successes"]'::jsonb,
        'DBT - Interpersonal Effectiveness',
        'Set healthy boundaries in relationship, feeling empowered',
        0.92,
        v_session_date,
        FALSE,
        v_session_date
    ) RETURNING id INTO v_session_id;
    v_session_ids := array_append(v_session_ids, v_session_id);

    -- Session 9: Coming Out Preparation (2025-03-24)
    v_session_date := '2025-03-24 14:00:00'::TIMESTAMP;
    INSERT INTO therapy_sessions (
        patient_id, therapist_id, session_date, duration_minutes,
        processing_status, analysis_status,
        transcript, mood_score, mood_confidence, mood_rationale,
        mood_indicators, emotional_tone, mood_analyzed_at,
        topics, action_items, technique, summary, extraction_confidence, topics_extracted_at,
        has_breakthrough, breakthrough_analyzed_at
    ) VALUES (
        v_patient_id, v_therapist_id, v_session_date, 60,
        'completed', 'deep_complete',
        '[]'::jsonb,
        6.0, 0.88, 'Patient preparing to come out to parents. High anxiety but resolved to live authentically.',
        '["coming out preparation", "identity integration", "anticipatory anxiety"]'::jsonb,
        'Determined, anxious',
        v_session_date,
        '["Coming Out", "Family Communication"]'::jsonb,
        '["Finalize coming out plan", "Prepare safety net with friends"]'::jsonb,
        'Narrative Therapy - Identity Story',
        'Preparing to come out to parents, building courage',
        0.91,
        v_session_date,
        FALSE,
        v_session_date
    ) RETURNING id INTO v_session_id;
    v_session_ids := array_append(v_session_ids, v_session_id);

    -- Session 10: Coming Out Aftermath (2025-03-31)
    v_session_date := '2025-03-31 14:00:00'::TIMESTAMP;
    INSERT INTO therapy_sessions (
        patient_id, therapist_id, session_date, duration_minutes,
        processing_status, analysis_status,
        transcript, mood_score, mood_confidence, mood_rationale,
        mood_indicators, emotional_tone, mood_analyzed_at,
        topics, action_items, technique, summary, extraction_confidence, topics_extracted_at,
        has_breakthrough, breakthrough_label, breakthrough_data, breakthrough_analyzed_at
    ) VALUES (
        v_patient_id, v_therapist_id, v_session_date, 60,
        'completed', 'deep_complete',
        '[]'::jsonb,
        8.0, 0.95, 'Patient came out to parents with mixed reception. Experiencing grief and relief simultaneously. Major identity integration.',
        '["authentic self", "grief and relief", "identity integration"]'::jsonb,
        'Grieving but liberated',
        v_session_date,
        '["Coming Out Aftermath", "Identity Integration"]'::jsonb,
        '["Allow space for grief", "Strengthen chosen family connections"]'::jsonb,
        'ACT - Acceptance & Values',
        'Came out to parents, processing mixed reception with grief and liberation',
        0.96,
        v_session_date,
        TRUE,
        'Identity Integration',
        '{"type": "Identity Breakthrough", "description": "Patient integrated authentic identity despite family rejection, major self-acceptance", "confidence": 0.96}'::jsonb,
        v_session_date
    ) RETURNING id INTO v_session_id;
    v_session_ids := array_append(v_session_ids, v_session_id);

    -- Return demo user info
    RETURN QUERY SELECT v_patient_id, v_session_ids;
END;
$$;

COMMENT ON FUNCTION seed_demo_user_sessions(UUID) IS
'Creates demo therapist, patient, and 10 fully-analyzed therapy sessions for hackathon demo mode';
```

#### 1.3 Demo Cleanup Function

**File**: `backend/supabase/cleanup_demo_data.sql` ✅
**Changes**: Create SQL function to delete expired demo users and sessions

```sql
-- Demo Data Cleanup Function
-- Deletes demo users and their associated data older than 24 hours
-- Call this via cron job or manually

CREATE OR REPLACE FUNCTION cleanup_expired_demo_users()
RETURNS TABLE(deleted_users INT, deleted_sessions INT)
LANGUAGE plpgsql
AS $$
DECLARE
    v_deleted_users INT;
    v_deleted_sessions INT;
BEGIN
    -- Count sessions before deletion
    SELECT COUNT(*) INTO v_deleted_sessions
    FROM therapy_sessions ts
    INNER JOIN users u ON ts.patient_id = u.id
    WHERE u.is_demo = TRUE
      AND u.demo_expires_at < NOW();

    -- Delete sessions for expired demo users (CASCADE will handle related data)
    DELETE FROM therapy_sessions
    WHERE patient_id IN (
        SELECT id FROM users
        WHERE is_demo = TRUE
          AND demo_expires_at < NOW()
    );

    -- Delete expired demo users
    DELETE FROM users
    WHERE is_demo = TRUE
      AND demo_expires_at < NOW();

    GET DIAGNOSTICS v_deleted_users = ROW_COUNT;

    RETURN QUERY SELECT v_deleted_users, v_deleted_sessions;
END;
$$;

COMMENT ON FUNCTION cleanup_expired_demo_users() IS
'Deletes demo users and sessions expired beyond 24 hours. Returns count of deleted records.';

-- Example cron schedule (for Supabase pg_cron extension):
-- SELECT cron.schedule('cleanup-demo-users', '0 * * * *', 'SELECT cleanup_expired_demo_users()');
```

### Success Criteria:

#### Automated Verification:
- [ ] Migration applies cleanly to Supabase: `psql <connection_string> -f backend/supabase/migrations/007_add_demo_mode_support.sql`
- [ ] Seed function executes successfully: `SELECT * FROM seed_demo_user_sessions(gen_random_uuid())`
- [ ] Cleanup function executes successfully: `SELECT * FROM cleanup_expired_demo_users()`
- [ ] Verify demo user created with 10 sessions: `SELECT COUNT(*) FROM therapy_sessions WHERE patient_id IN (SELECT id FROM users WHERE is_demo = TRUE)`
- [ ] Verify indexes created: `\d users` should show `idx_users_demo_token` and `idx_users_demo_expiry`

#### Manual Verification:
- [ ] Query demo sessions and verify all AI fields populated (mood_score, topics, breakthrough_data)
- [ ] Verify session dates span Jan-March 2025 chronologically
- [ ] Check that breakthrough_label is set for sessions 1, 3, and 10
- [ ] Confirm cleanup function deletes only expired demos (test with manual expiry update)
- [ ] Verify foreign key relationships intact (therapist and patient both created)

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation that the seed data quality meets hackathon demo standards before proceeding to Phase 2.

---

## Phase 2: Backend Demo API Endpoints

### Overview
Create FastAPI endpoints for demo initialization, reset, and transcript upload with demo token authentication middleware.

### Changes Required:

#### 2.1 Demo Authentication Middleware

**File**: `backend/app/middleware/demo_auth.py` (NEW) ✅
**Changes**: Create middleware to extract and validate demo tokens

```python
"""
Demo Authentication Middleware
Handles demo token extraction from headers and user lookup
"""

from fastapi import Request, HTTPException
from typing import Optional
import logging
from supabase import Client

from app.database import get_supabase

logger = logging.getLogger(__name__)


async def get_demo_user(request: Request) -> Optional[dict]:
    """
    Extract demo token from request headers and fetch demo user

    Headers checked (in order):
    1. X-Demo-Token: <uuid>
    2. Authorization: Demo <uuid>

    Returns:
        Demo user dict if valid token, None otherwise
    """
    demo_token = None

    # Check X-Demo-Token header
    if "x-demo-token" in request.headers:
        demo_token = request.headers["x-demo-token"]

    # Check Authorization header (format: "Demo <uuid>")
    elif "authorization" in request.headers:
        auth_header = request.headers["authorization"]
        if auth_header.startswith("Demo "):
            demo_token = auth_header[5:]  # Strip "Demo " prefix

    if not demo_token:
        return None

    # Validate token format (basic UUID check)
    try:
        from uuid import UUID
        UUID(demo_token)
    except ValueError:
        logger.warning(f"Invalid demo token format: {demo_token}")
        return None

    # Lookup demo user
    db: Client = get_supabase()
    try:
        response = db.table("users").select("*").eq("demo_token", demo_token).eq("is_demo", True).single().execute()

        if not response.data:
            logger.warning(f"Demo token not found: {demo_token}")
            return None

        demo_user = response.data

        # Check expiry
        from datetime import datetime
        if demo_user.get("demo_expires_at"):
            expiry = datetime.fromisoformat(demo_user["demo_expires_at"].replace("Z", "+00:00"))
            if expiry < datetime.now(expiry.tzinfo):
                logger.warning(f"Demo token expired: {demo_token}")
                return None

        return demo_user

    except Exception as e:
        logger.error(f"Error fetching demo user: {e}")
        return None


def require_demo_auth(request: Request) -> dict:
    """
    Dependency that requires valid demo token
    Raises 401 if token missing or invalid
    """
    import asyncio
    demo_user = asyncio.run(get_demo_user(request))

    if not demo_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing demo token. Initialize demo first."
        )

    return demo_user
```

#### 2.2 Demo Router

**File**: `backend/app/routers/demo.py` (NEW) ✅
**Changes**: Create demo management endpoints

```python
"""
Demo Mode API Router
Handles demo initialization, reset, and status
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List
from uuid import uuid4
from datetime import datetime
import logging

from app.database import get_db
from app.middleware.demo_auth import get_demo_user, require_demo_auth
from supabase import Client

router = APIRouter(prefix="/api/demo", tags=["demo"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class DemoInitResponse(BaseModel):
    """Response for demo initialization"""
    demo_token: str
    patient_id: str
    session_ids: List[str]
    expires_at: str
    message: str


class DemoResetResponse(BaseModel):
    """Response for demo reset"""
    patient_id: str
    session_ids: List[str]
    message: str


class DemoStatusResponse(BaseModel):
    """Response for demo status check"""
    demo_token: str
    patient_id: str
    session_count: int
    created_at: str
    expires_at: str
    is_expired: bool


# ============================================================================
# Demo Endpoints
# ============================================================================

@router.post("/initialize", response_model=DemoInitResponse)
async def initialize_demo(db: Client = Depends(get_db)):
    """
    Initialize a new demo user with 10 pre-loaded therapy sessions

    This endpoint:
    1. Generates a unique demo token (UUID)
    2. Calls seed_demo_user_sessions() SQL function
    3. Returns demo token for localStorage storage

    Returns:
        DemoInitResponse with token and session IDs
    """
    # Generate unique demo token
    demo_token = str(uuid4())

    logger.info(f"Initializing demo user with token: {demo_token}")

    try:
        # Call SQL function to seed demo data
        response = db.rpc("seed_demo_user_sessions", {"p_demo_token": demo_token}).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to create demo user and sessions"
            )

        result = response.data[0]
        patient_id = result["patient_id"]
        session_ids = result["session_ids"]

        # Fetch demo user to get expiry
        user_response = db.table("users").select("demo_expires_at").eq("id", patient_id).single().execute()
        expires_at = user_response.data["demo_expires_at"]

        logger.info(f"✓ Demo user created: {patient_id} with {len(session_ids)} sessions")

        return DemoInitResponse(
            demo_token=demo_token,
            patient_id=patient_id,
            session_ids=[str(sid) for sid in session_ids],
            expires_at=expires_at,
            message=f"Demo initialized with {len(session_ids)} sessions. Data expires in 24 hours."
        )

    except Exception as e:
        logger.error(f"Demo initialization error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize demo: {str(e)}"
        )


@router.post("/reset", response_model=DemoResetResponse)
async def reset_demo(
    request: Request,
    demo_user: dict = Depends(require_demo_auth),
    db: Client = Depends(get_db)
):
    """
    Reset demo user by deleting all sessions and re-seeding with fresh 10 sessions

    This endpoint:
    1. Validates demo token
    2. Deletes all existing sessions for demo user
    3. Calls seed function to recreate 10 sessions
    4. Extends expiry by 24 hours

    Returns:
        DemoResetResponse with new session IDs
    """
    demo_token = demo_user["demo_token"]
    patient_id = demo_user["id"]

    logger.info(f"Resetting demo for user: {patient_id}")

    try:
        # Delete existing sessions
        db.table("therapy_sessions").delete().eq("patient_id", patient_id).execute()

        # Re-seed sessions using SQL function
        response = db.rpc("seed_demo_user_sessions", {"p_demo_token": demo_token}).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset demo sessions"
            )

        result = response.data[0]
        session_ids = result["session_ids"]

        logger.info(f"✓ Demo reset complete: {len(session_ids)} sessions recreated")

        return DemoResetResponse(
            patient_id=patient_id,
            session_ids=[str(sid) for sid in session_ids],
            message=f"Demo reset with {len(session_ids)} fresh sessions"
        )

    except Exception as e:
        logger.error(f"Demo reset error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset demo: {str(e)}"
        )


@router.get("/status", response_model=DemoStatusResponse)
async def get_demo_status(
    request: Request,
    demo_user: dict = Depends(require_demo_auth),
    db: Client = Depends(get_db)
):
    """
    Get current demo user status

    Returns:
        DemoStatusResponse with user info and session count
    """
    patient_id = demo_user["id"]

    # Count sessions
    session_response = db.table("therapy_sessions").select("id", count="exact").eq("patient_id", patient_id).execute()
    session_count = session_response.count or 0

    # Check if expired
    from datetime import datetime
    expires_at = datetime.fromisoformat(demo_user["demo_expires_at"].replace("Z", "+00:00"))
    is_expired = expires_at < datetime.now(expires_at.tzinfo)

    return DemoStatusResponse(
        demo_token=demo_user["demo_token"],
        patient_id=patient_id,
        session_count=session_count,
        created_at=demo_user["demo_created_at"],
        expires_at=demo_user["demo_expires_at"],
        is_expired=is_expired
    )
```

#### 2.3 Demo Transcript Upload Endpoint

**File**: `backend/app/routers/sessions.py` ✅
**Changes**: Add demo-specific transcript upload endpoint

```python
# Add this import at the top
from app.middleware.demo_auth import get_demo_user

# Add this new endpoint after the existing upload-transcript endpoint

@router.post("/upload-demo-transcript")
async def upload_demo_transcript(
    request: Request,
    session_file: str,  # e.g., "session_12_thriving.json"
    background_tasks: BackgroundTasks,
    db: Client = Depends(get_db)
):
    """
    Upload a pre-selected demo transcript from mock-therapy-data/

    This endpoint:
    1. Validates demo token from headers
    2. Loads JSON transcript from mock-therapy-data/sessions/{session_file}
    3. Creates new session with transcript
    4. Triggers full AI analysis pipeline (mood, topics, breakthrough, deep)
    5. Returns session ID for status tracking

    Args:
        session_file: Filename from mock-therapy-data/sessions/ (e.g., "session_12_thriving.json")

    Returns:
        Session ID and processing status
    """
    # Get demo user from token
    demo_user = await get_demo_user(request)
    if not demo_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing demo token. Initialize demo first."
        )

    patient_id = demo_user["id"]

    # Load transcript JSON
    import json
    from pathlib import Path

    mock_data_dir = Path(__file__).parent.parent.parent.parent / "mock-therapy-data" / "sessions"
    transcript_path = mock_data_dir / session_file

    if not transcript_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Demo transcript not found: {session_file}"
        )

    try:
        with open(transcript_path, "r") as f:
            transcript_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load transcript {session_file}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load demo transcript: {str(e)}"
        )

    # Extract transcript segments
    segments = transcript_data.get("segments", [])
    if not segments:
        raise HTTPException(
            status_code=400,
            detail="Demo transcript has no segments"
        )

    # Get therapist ID (find demo therapist with same demo_token)
    therapist_response = db.table("users").select("id").eq("demo_token", demo_user["demo_token"]).eq("role", "therapist").single().execute()
    therapist_id = therapist_response.data["id"]

    # Create new session
    from datetime import datetime, timedelta

    # Calculate session date (after last existing session)
    last_session_response = db.table("therapy_sessions").select("session_date").eq("patient_id", patient_id).order("session_date", desc=True).limit(1).execute()

    if last_session_response.data:
        last_date = datetime.fromisoformat(last_session_response.data[0]["session_date"].replace("Z", "+00:00"))
        new_session_date = last_date + timedelta(days=7)  # 1 week later
    else:
        new_session_date = datetime.now()

    session_data = {
        "patient_id": patient_id,
        "therapist_id": therapist_id,
        "session_date": new_session_date.isoformat(),
        "duration_minutes": transcript_data.get("metadata", {}).get("duration", 60) // 60,
        "processing_status": "wave1_in_progress",
        "analysis_status": "wave1_in_progress",
        "transcript": segments,
    }

    session_response = db.table("therapy_sessions").insert(session_data).execute()

    if not session_response.data:
        raise HTTPException(status_code=500, detail="Failed to create session")

    session = session_response.data[0]
    session_id = session["id"]

    # Trigger full AI analysis in background
    background_tasks.add_task(analyze_session_full_pipeline, session_id)

    logger.info(f"✓ Demo transcript uploaded: {session_file} → Session {session_id}")

    return {
        "session_id": session_id,
        "status": "processing",
        "message": f"Demo session created from {session_file}. AI analysis in progress.",
        "transcript_segments": len(segments)
    }
```

#### 2.4 Main App Registration

**File**: `backend/app/main.py` ✅
**Changes**: Register demo router

```python
# Add this import at the top with other router imports
from app.routers import demo

# Add this line where other routers are included (around line 40-50)
app.include_router(demo.router)
```

### Success Criteria:

#### Automated Verification:
- [ ] Backend server starts without errors: `cd backend && uvicorn app.main:app --reload`
- [ ] POST /api/demo/initialize returns demo token: `curl -X POST http://localhost:8000/api/demo/initialize`
- [ ] GET /api/demo/status requires valid token: `curl -H "X-Demo-Token: <token>" http://localhost:8000/api/demo/status`
- [ ] POST /api/demo/reset works with valid token: `curl -X POST -H "X-Demo-Token: <token>" http://localhost:8000/api/demo/reset`
- [ ] POST /api/sessions/upload-demo-transcript accepts session file: `curl -X POST -H "X-Demo-Token: <token>" "http://localhost:8000/api/sessions/upload-demo-transcript?session_file=session_12_thriving.json"`
- [ ] Invalid demo token returns 401: `curl -H "X-Demo-Token: invalid" http://localhost:8000/api/demo/status`

#### Manual Verification:
- [ ] Initialize demo and verify 10 sessions created in database
- [ ] Check that demo user has patient_id returned in response
- [ ] Upload demo transcript and verify AI analysis runs (check logs)
- [ ] Reset demo and confirm old sessions deleted, new 10 created
- [ ] Verify demo token expires after 24h (manually update expiry timestamp)
- [ ] Test demo middleware with both X-Demo-Token and Authorization: Demo headers

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation that the API endpoints work correctly with Postman/curl before proceeding to Phase 3.

---

## Phase 3: Frontend Demo Token Management

### Overview
Create localStorage utilities and demo initialization logic for frontend token management.

### Changes Required:

#### 3.1 Demo Token Storage Utility

**File**: `frontend/lib/demo-token-storage.ts` (NEW) ✅
**Changes**: Create localStorage wrapper for demo token

```typescript
/**
 * Demo Token Storage Utility
 * Manages demo token persistence in localStorage
 */

const DEMO_TOKEN_KEY = 'therapybridge_demo_token';
const DEMO_PATIENT_ID_KEY = 'therapybridge_demo_patient_id';
const DEMO_EXPIRES_AT_KEY = 'therapybridge_demo_expires_at';

export const demoTokenStorage = {
  /**
   * Save demo token and metadata to localStorage
   */
  saveToken(token: string, patientId: string, expiresAt: string): void {
    if (typeof window === 'undefined') return;

    try {
      localStorage.setItem(DEMO_TOKEN_KEY, token);
      localStorage.setItem(DEMO_PATIENT_ID_KEY, patientId);
      localStorage.setItem(DEMO_EXPIRES_AT_KEY, expiresAt);
      console.log('[Demo] Token saved to localStorage:', { token, patientId });
    } catch (error) {
      console.error('[Demo] Failed to save token:', error);
    }
  },

  /**
   * Get demo token from localStorage
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null;

    try {
      return localStorage.getItem(DEMO_TOKEN_KEY);
    } catch (error) {
      console.error('[Demo] Failed to get token:', error);
      return null;
    }
  },

  /**
   * Get demo patient ID from localStorage
   */
  getPatientId(): string | null {
    if (typeof window === 'undefined') return null;

    try {
      return localStorage.getItem(DEMO_PATIENT_ID_KEY);
    } catch (error) {
      console.error('[Demo] Failed to get patient ID:', error);
      return null;
    }
  },

  /**
   * Get demo expiry timestamp from localStorage
   */
  getExpiresAt(): string | null {
    if (typeof window === 'undefined') return null;

    try {
      return localStorage.getItem(DEMO_EXPIRES_AT_KEY);
    } catch (error) {
      console.error('[Demo] Failed to get expiry:', error);
      return null;
    }
  },

  /**
   * Check if demo token is expired
   */
  isExpired(): boolean {
    const expiresAt = this.getExpiresAt();
    if (!expiresAt) return true;

    try {
      const expiry = new Date(expiresAt);
      return expiry < new Date();
    } catch (error) {
      console.error('[Demo] Invalid expiry date:', error);
      return true;
    }
  },

  /**
   * Clear demo token and metadata from localStorage
   */
  clearToken(): void {
    if (typeof window === 'undefined') return;

    try {
      localStorage.removeItem(DEMO_TOKEN_KEY);
      localStorage.removeItem(DEMO_PATIENT_ID_KEY);
      localStorage.removeItem(DEMO_EXPIRES_AT_KEY);
      console.log('[Demo] Token cleared from localStorage');
    } catch (error) {
      console.error('[Demo] Failed to clear token:', error);
    }
  },

  /**
   * Check if demo token exists and is valid
   */
  hasValidToken(): boolean {
    const token = this.getToken();
    return !!token && !this.isExpired();
  },
};
```

#### 3.2 Demo API Client

**File**: `frontend/lib/demo-api-client.ts` (NEW) ✅
**Changes**: Create API client for demo endpoints

```typescript
/**
 * Demo API Client
 * Handles demo initialization, reset, and status checks
 */

import { apiClient } from './api-client';
import { demoTokenStorage } from './demo-token-storage';

export interface DemoInitResponse {
  demo_token: string;
  patient_id: string;
  session_ids: string[];
  expires_at: string;
  message: string;
}

export interface DemoResetResponse {
  patient_id: string;
  session_ids: string[];
  message: string;
}

export interface DemoStatusResponse {
  demo_token: string;
  patient_id: string;
  session_count: number;
  created_at: string;
  expires_at: string;
  is_expired: boolean;
}

export const demoApiClient = {
  /**
   * Initialize a new demo user with 10 pre-loaded sessions
   */
  async initialize(): Promise<DemoInitResponse | null> {
    console.log('[Demo API] Initializing demo user...');

    const result = await apiClient.post<DemoInitResponse>('/api/demo/initialize');

    if (result.success) {
      console.log('[Demo API] ✓ Demo initialized:', result.data);

      // Save token to localStorage
      demoTokenStorage.saveToken(
        result.data.demo_token,
        result.data.patient_id,
        result.data.expires_at
      );

      return result.data;
    } else {
      console.error('[Demo API] ✗ Demo initialization failed:', result.error);
      return null;
    }
  },

  /**
   * Reset demo user (delete all sessions and re-seed with 10 fresh ones)
   */
  async reset(): Promise<DemoResetResponse | null> {
    const token = demoTokenStorage.getToken();
    if (!token) {
      console.error('[Demo API] No demo token found for reset');
      return null;
    }

    console.log('[Demo API] Resetting demo...');

    const result = await apiClient.post<DemoResetResponse>(
      '/api/demo/reset',
      {},
      {
        headers: {
          'X-Demo-Token': token,
        },
      }
    );

    if (result.success) {
      console.log('[Demo API] ✓ Demo reset:', result.data);
      return result.data;
    } else {
      console.error('[Demo API] ✗ Demo reset failed:', result.error);
      return null;
    }
  },

  /**
   * Get demo user status (session count, expiry, etc.)
   */
  async getStatus(): Promise<DemoStatusResponse | null> {
    const token = demoTokenStorage.getToken();
    if (!token) {
      console.error('[Demo API] No demo token found for status check');
      return null;
    }

    const result = await apiClient.get<DemoStatusResponse>('/api/demo/status', {
      headers: {
        'X-Demo-Token': token,
      },
    });

    if (result.success) {
      return result.data;
    } else {
      console.error('[Demo API] ✗ Status check failed:', result.error);
      return null;
    }
  },

  /**
   * Upload a demo transcript (session_12_thriving.json, etc.)
   */
  async uploadDemoTranscript(sessionFile: string): Promise<{ session_id: string; status: string } | null> {
    const token = demoTokenStorage.getToken();
    if (!token) {
      console.error('[Demo API] No demo token found for upload');
      return null;
    }

    console.log('[Demo API] Uploading demo transcript:', sessionFile);

    const result = await apiClient.post<{ session_id: string; status: string; message: string }>(
      `/api/sessions/upload-demo-transcript?session_file=${sessionFile}`,
      {},
      {
        headers: {
          'X-Demo-Token': token,
        },
      }
    );

    if (result.success) {
      console.log('[Demo API] ✓ Demo transcript uploaded:', result.data);
      return result.data;
    } else {
      console.error('[Demo API] ✗ Demo transcript upload failed:', result.error);
      return null;
    }
  },
};
```

#### 3.3 Update API Client to Send Demo Token

**File**: `frontend/lib/api-client.ts` ✅
**Changes**: Modify request method to include demo token header

```typescript
// Add this import at the top
import { demoTokenStorage } from './demo-token-storage';

// Update the request method around line 88-95
// Replace the Authorization header logic with this:

const accessToken = tokenStorage.getAccessToken();
const demoToken = demoTokenStorage.getToken();

const config: RequestInit = {
  ...fetchOptions,
  headers: {
    'Content-Type': 'application/json',
    // Regular auth token (if not demo mode)
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    // Demo token (if in demo mode)
    ...(demoToken ? { 'X-Demo-Token': demoToken } : {}),
    ...fetchOptions.headers,
  },
};
```

### Success Criteria:

#### Automated Verification:
- [ ] Frontend builds successfully: `cd frontend && npm run build`
- [ ] TypeScript compiles without errors: `npm run type-check` (if available)
- [ ] No ESLint errors in new files: `npx eslint lib/demo-*.ts`

#### Manual Verification:
- [ ] Open browser console and run `localStorage.setItem('therapybridge_demo_token', 'test')` - verify token stored
- [ ] Run `demoTokenStorage.getToken()` in console - verify returns token
- [ ] Run `demoTokenStorage.clearToken()` - verify localStorage cleared
- [ ] Test `demoTokenStorage.isExpired()` with past/future dates
- [ ] Call `demoApiClient.initialize()` and verify localStorage populated
- [ ] Verify demo token included in subsequent API requests (check Network tab)

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation that localStorage and API client work correctly before proceeding to Phase 4.

---

## Phase 4: UI Updates - Navigation & Upload

### Overview
Add "Reset Demo" button to NavigationBar and "Upload Demo Session" UI to upload page.

### Changes Required:

#### 4.1 Reset Demo Button in NavigationBar

**File**: `frontend/components/NavigationBar.tsx` ✅
**Changes**: Add Reset Demo button in top right section

```typescript
// Add these imports at the top
import { useState } from 'react';
import { demoApiClient } from '@/lib/demo-api-client';
import { demoTokenStorage } from '@/lib/demo-token-storage';

// Add this state and handlers inside NavigationBar component (around line 53)
const [showResetConfirm, setShowResetConfirm] = useState(false);
const [isResetting, setIsResetting] = useState(false);

const handleResetDemo = async () => {
  setIsResetting(true);
  try {
    const result = await demoApiClient.reset();
    if (result) {
      // Show success toast and reload page
      alert('Demo reset successfully! Page will reload.');
      window.location.reload();
    } else {
      alert('Failed to reset demo. Please try again.');
    }
  } catch (error) {
    console.error('Reset demo error:', error);
    alert('An error occurred while resetting demo.');
  } finally {
    setIsResetting(false);
    setShowResetConfirm(false);
  }
};

// Replace the Right section (lines 170-173) with this:
{/* Right section - TheraBridge Logo + Reset Demo */}
<div className="flex items-center justify-end gap-3 pr-6 w-[240px]">
  <button
    onClick={() => setShowResetConfirm(true)}
    className="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] border border-gray-300 dark:border-[#3d3548] rounded-md hover:border-[#5AB9B4] dark:hover:border-[#a78bfa] transition-all"
  >
    Reset Demo
  </button>
  <CombinedLogo iconSize={28} textClassName="text-base" />
</div>

{/* Reset Confirmation Modal */}
{showResetConfirm && (
  <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50">
    <div className="bg-white dark:bg-[#1a1625] border border-gray-200 dark:border-[#3d3548] rounded-lg p-6 max-w-md mx-4 shadow-xl">
      <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3">
        Reset Demo?
      </h3>
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
        This will delete all your demo data and restore the original 10 sessions. Any uploaded sessions will be lost.
      </p>
      <div className="flex gap-3 justify-end">
        <button
          onClick={() => setShowResetConfirm(false)}
          disabled={isResetting}
          className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#3d3548] rounded-md transition-colors disabled:opacity-50"
        >
          Cancel
        </button>
        <button
          onClick={handleResetDemo}
          disabled={isResetting}
          className="px-4 py-2 text-sm font-medium text-white bg-[#5AB9B4] dark:bg-[#a78bfa] hover:bg-[#4a9a95] dark:hover:bg-[#9370db] rounded-md transition-colors disabled:opacity-50"
        >
          {isResetting ? 'Resetting...' : 'Reset Demo'}
        </button>
      </div>
    </div>
  </div>
)}
```

#### 4.2 Upload Demo Session Component

**File**: `frontend/app/upload/components/DemoTranscriptUploader.tsx` (NEW) ✅
**Changes**: Create demo transcript upload UI with dropdown

```typescript
'use client';

/**
 * Demo Transcript Uploader
 * Allows uploading pre-selected JSON transcripts from mock-therapy-data
 */

import { useState } from 'react';
import { demoApiClient } from '@/lib/demo-api-client';
import { useProcessing } from '@/contexts/ProcessingContext';

const DEMO_TRANSCRIPTS = [
  {
    filename: 'session_12_thriving.json',
    label: 'Session 12: Thriving',
    description: 'Final session showing sustained progress and thriving',
  },
  {
    filename: 'session_11_rebuilding.json',
    label: 'Session 11: Rebuilding',
    description: 'Rebuilding after coming out, strengthening resilience',
  },
];

interface DemoTranscriptUploaderProps {
  onUploadSuccess?: (sessionId: string) => void;
}

export default function DemoTranscriptUploader({ onUploadSuccess }: DemoTranscriptUploaderProps) {
  const [selectedTranscript, setSelectedTranscript] = useState(DEMO_TRANSCRIPTS[0].filename);
  const [isUploading, setIsUploading] = useState(false);
  const { startTracking } = useProcessing();

  const handleUpload = async () => {
    setIsUploading(true);

    try {
      const result = await demoApiClient.uploadDemoTranscript(selectedTranscript);

      if (result) {
        console.log('[Demo Upload] ✓ Session created:', result.session_id);

        // Start tracking processing status
        startTracking(result.session_id);

        // Notify parent component
        onUploadSuccess?.(result.session_id);
      } else {
        alert('Failed to upload demo transcript. Please try again.');
      }
    } catch (error) {
      console.error('[Demo Upload] Error:', error);
      alert('An error occurred during upload.');
    } finally {
      setIsUploading(false);
    }
  };

  const selectedInfo = DEMO_TRANSCRIPTS.find(t => t.filename === selectedTranscript);

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white dark:bg-[#1a1625] border-2 border-dashed border-[#5AB9B4] dark:border-[#a78bfa] rounded-xl p-8">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="w-16 h-16 bg-[#5AB9B4]/10 dark:bg-[#a78bfa]/10 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg
              className="w-8 h-8 text-[#5AB9B4] dark:text-[#a78bfa]"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
          </div>
          <h3 className="text-xl font-light text-gray-900 dark:text-gray-100 mb-2">
            Upload Demo Session
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Select a pre-loaded therapy transcript to showcase AI analysis
          </p>
        </div>

        {/* Transcript Selector */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Select Session
          </label>
          <select
            value={selectedTranscript}
            onChange={(e) => setSelectedTranscript(e.target.value)}
            disabled={isUploading}
            className="w-full px-4 py-3 bg-gray-50 dark:bg-[#2d2438] border border-gray-300 dark:border-[#3d3548] rounded-lg text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-[#5AB9B4] dark:focus:ring-[#a78bfa] focus:border-transparent transition-all disabled:opacity-50"
          >
            {DEMO_TRANSCRIPTS.map((transcript) => (
              <option key={transcript.filename} value={transcript.filename}>
                {transcript.label}
              </option>
            ))}
          </select>

          {/* Description */}
          {selectedInfo && (
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              {selectedInfo.description}
            </p>
          )}
        </div>

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="w-full py-3 px-6 bg-[#5AB9B4] dark:bg-[#a78bfa] hover:bg-[#4a9a95] dark:hover:bg-[#9370db] text-white font-medium rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Uploading...
            </span>
          ) : (
            'Upload & Analyze'
          )}
        </button>

        {/* Info Banner */}
        <div className="mt-6 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <p className="text-xs text-blue-700 dark:text-blue-300">
            <strong>Demo Mode:</strong> This will create a new session and run real AI analysis (mood, topics, breakthroughs). Processing takes ~10 seconds.
          </p>
        </div>
      </div>
    </div>
  );
}
```

#### 4.3 Integrate Demo Uploader into Upload Page

**File**: `frontend/app/upload/page.tsx` ✅
**Changes**: Add demo uploader UI to upload page

```typescript
// Add this import at the top
import DemoTranscriptUploader from './components/DemoTranscriptUploader';

// Replace the upload view section (around lines 51-65) with this:
{view === 'upload' && (
  <div className="space-y-8">
    {/* Demo Transcript Uploader */}
    <DemoTranscriptUploader onUploadSuccess={(sessionId) => {
      console.log('[Upload] Demo upload success:', sessionId);
      setSessionId(sessionId);
      setView('processing');
    }} />

    <div className="relative">
      <div className="absolute inset-0 flex items-center">
        <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
      </div>
      <div className="relative flex justify-center text-sm">
        <span className="px-4 bg-[#ECEAE5] dark:bg-[#1a1625] text-gray-500 dark:text-gray-400 font-medium">
          OR UPLOAD AUDIO
        </span>
      </div>
    </div>

    <FileUploader onUploadSuccess={handleUploadSuccess} />

    <div className="relative">
      <div className="absolute inset-0 flex items-center">
        <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
      </div>
      <div className="relative flex justify-center text-sm">
        <span className="px-4 bg-[#ECEAE5] dark:bg-[#1a1625] text-gray-500 dark:text-gray-400 font-medium">
          OR RECORD
        </span>
      </div>
    </div>

    <AudioRecorder onUploadSuccess={handleUploadSuccess} />
  </div>
)}
```

### Success Criteria:

#### Automated Verification:
- [ ] Frontend builds successfully: `npm run build`
- [ ] No TypeScript errors: `npm run type-check`
- [ ] No ESLint errors: `npx eslint app/upload/ components/NavigationBar.tsx`

#### Manual Verification:
- [ ] Navigate to `/upload` and see "Upload Demo Session" at top
- [ ] Dropdown shows "Session 12: Thriving" and "Session 11: Rebuilding"
- [ ] Click "Upload & Analyze" and verify upload starts
- [ ] Verify NavigationBar shows "Reset Demo" button in top right
- [ ] Click "Reset Demo" and verify confirmation modal appears
- [ ] Modal text matches existing UI style (font-light, proper colors)
- [ ] Confirm reset and verify page reloads with fresh 10 sessions
- [ ] Upload demo session and verify it appears in dashboard after processing

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation that UI components match the existing design system before proceeding to Phase 5.

---

## Phase 5: Dashboard Integration & Real-time Updates

### Overview
Auto-initialize demo on dashboard load and ensure real-time updates work for demo uploads.

### Changes Required:

#### 5.1 Demo Initialization Hook

**File**: `frontend/hooks/useDemoInitialization.ts` (NEW) ✅
**Changes**: Create hook to auto-initialize demo on first visit

```typescript
'use client';

/**
 * Demo Initialization Hook
 * Automatically initializes demo user on first visit
 */

import { useEffect, useState } from 'react';
import { demoTokenStorage } from '@/lib/demo-token-storage';
import { demoApiClient } from '@/lib/demo-api-client';

export function useDemoInitialization() {
  const [isInitializing, setIsInitializing] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [patientId, setPatientId] = useState<string | null>(null);

  useEffect(() => {
    const initializeDemo = async () => {
      console.log('[Demo Init] Checking demo status...');

      // Check if valid token exists
      if (demoTokenStorage.hasValidToken()) {
        const existingPatientId = demoTokenStorage.getPatientId();
        console.log('[Demo Init] ✓ Valid token found, patient ID:', existingPatientId);
        setPatientId(existingPatientId);
        setIsReady(true);
        return;
      }

      // Token expired or doesn't exist - initialize new demo
      console.log('[Demo Init] No valid token, initializing new demo...');
      setIsInitializing(true);

      try {
        const result = await demoApiClient.initialize();

        if (result) {
          console.log('[Demo Init] ✓ Demo initialized:', result.patient_id);
          setPatientId(result.patient_id);
          setIsReady(true);
        } else {
          console.error('[Demo Init] ✗ Initialization failed');
          setIsReady(false);
        }
      } catch (error) {
        console.error('[Demo Init] Error:', error);
        setIsReady(false);
      } finally {
        setIsInitializing(false);
      }
    };

    initializeDemo();
  }, []);

  return {
    isInitializing,
    isReady,
    patientId,
  };
}
```

#### 5.2 Update Dashboard to Use Demo Hook

**File**: `frontend/app/dashboard/page.tsx` ✅
**Changes**: Add demo initialization

```typescript
// Add this import at the top
import { useDemoInitialization } from '@/hooks/useDemoInitialization';

// Add this inside DashboardPage component (around line 26)
export default function DashboardPage() {
  const router = useRouter();
  const { isInitializing, isReady, patientId } = useDemoInitialization();

  // Show loading state while demo initializes
  if (isInitializing) {
    return (
      <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-[#5AB9B4] dark:border-[#a78bfa] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm font-light text-gray-600 dark:text-gray-400">
            Initializing demo...
          </p>
        </div>
      </div>
    );
  }

  if (!isReady || !patientId) {
    return (
      <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] flex items-center justify-center">
        <div className="text-center">
          <p className="text-sm font-light text-red-600 dark:text-red-400">
            Failed to initialize demo. Please refresh the page.
          </p>
        </div>
      </div>
    );
  }

  // Rest of existing dashboard code...
  return (
    <ProcessingProvider>
      {/* ... existing dashboard JSX ... */}
    </ProcessingProvider>
  );
}
```

#### 5.3 Update SessionDataContext to Use Demo Patient ID

**File**: `frontend/app/patient/lib/usePatientSessions.ts` ✅
**Changes**: Fetch sessions for demo patient ID

```typescript
// Add this import at the top
import { demoTokenStorage } from '@/lib/demo-token-storage';

// Update the SessionDataProvider around the fetch logic
export function SessionDataProvider({ children }: { children: React.ReactNode }) {
  // ... existing state ...

  useEffect(() => {
    const fetchSessions = async () => {
      // Get demo patient ID
      const patientId = demoTokenStorage.getPatientId();
      if (!patientId) {
        console.error('[SessionData] No patient ID found');
        setIsLoading(false);
        return;
      }

      console.log('[SessionData] Fetching sessions for patient:', patientId);

      try {
        // Fetch sessions from API
        const result = await apiClient.get<{ sessions: Session[] }>(
          `/api/sessions/patient/${patientId}`
        );

        if (result.success) {
          console.log('[SessionData] ✓ Loaded sessions:', result.data.sessions.length);
          setSessions(result.data.sessions);
        } else {
          console.error('[SessionData] ✗ Failed to fetch sessions:', result.error);
        }
      } catch (error) {
        console.error('[SessionData] Error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSessions();
  }, []);

  // ... rest of provider ...
}
```

#### 5.4 Verify ProcessingContext Works with Demo

**File**: `frontend/contexts/ProcessingContext.tsx`
**Changes**: Ensure demo token sent in status polling

```typescript
// This should already work if api-client.ts was updated in Phase 3
// Just verify the polling logic uses apiClient (which now sends demo token)

// Around line 45-55, ensure status check uses apiClient:
const checkStatus = async () => {
  const result = await apiClient.get(`/api/sessions/${sessionId}/status`);
  // ... rest of polling logic
};

// No changes needed if apiClient already updated
```

### Success Criteria:

#### Automated Verification:
- [ ] Frontend builds successfully: `npm run build`
- [ ] No TypeScript errors: `npm run type-check`
- [ ] No console errors when loading dashboard: Start dev server and check browser console

#### Manual Verification:
- [ ] Open browser in incognito mode and navigate to `http://localhost:3000/dashboard`
- [ ] Verify "Initializing demo..." spinner appears briefly
- [ ] Dashboard loads with 10 sessions displayed
- [ ] Check localStorage and confirm `therapybridge_demo_token` exists
- [ ] Upload a demo session from `/upload` page
- [ ] Verify UploadProgress shows real processing status updates
- [ ] Dashboard auto-refreshes when processing completes (via ProcessingRefreshBridge)
- [ ] New session appears at top of timeline
- [ ] Session card shows AI analysis (mood, topics, breakthrough if applicable)
- [ ] Click "Reset Demo" and verify dashboard reloads with fresh 10 sessions
- [ ] Close browser, reopen, and verify same demo token persists (no re-initialization)
- [ ] Clear localStorage and verify new demo initializes on next page load

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation that the end-to-end demo flow works perfectly for hackathon presentation.

---

## Testing Strategy

### Unit Tests:
- **Backend:**
  - `test_demo_router.py`: Test demo initialization, reset, status endpoints
  - `test_demo_auth_middleware.py`: Test token extraction and validation
  - `test_demo_transcript_upload.py`: Test JSON loading and session creation

- **Frontend:**
  - `demo-token-storage.test.ts`: Test localStorage operations
  - `demo-api-client.test.ts`: Test API calls with mock responses
  - `useDemoInitialization.test.tsx`: Test hook initialization logic

### Integration Tests:
- **End-to-End Flow:**
  1. Initialize demo → Verify 10 sessions created in DB
  2. Upload demo transcript → Verify AI analysis runs
  3. Check dashboard → Verify 11 sessions displayed
  4. Reset demo → Verify sessions deleted and re-seeded
  5. Wait 24h (or manually update expiry) → Run cleanup → Verify demo deleted

### Manual Testing Steps:

**Critical Path Testing:**
1. **First Visit Flow:**
   - Open browser in incognito mode
   - Navigate to `http://localhost:3000/dashboard`
   - Verify loading spinner appears
   - Verify 10 sessions load on dashboard
   - Check localStorage for demo token
   - Verify all session cards show AI data (mood, topics)

2. **Upload Demo Session:**
   - Click "Upload" in navigation
   - Select "Session 12: Thriving" from dropdown
   - Click "Upload & Analyze"
   - Verify processing screen appears with progress bar
   - Wait for completion (~10 seconds)
   - Verify redirect to results view
   - Navigate to dashboard
   - Verify 11 sessions now displayed
   - Click new session and verify full AI analysis present

3. **Reset Demo:**
   - Click "Reset Demo" button in navbar
   - Verify confirmation modal appears
   - Click "Reset Demo" button in modal
   - Verify page reloads
   - Verify 10 original sessions restored
   - Verify uploaded session is gone

4. **Token Persistence:**
   - Upload a demo session
   - Close browser completely
   - Reopen and navigate to dashboard
   - Verify same 11 sessions still present (token persisted)
   - Check Network tab and verify `X-Demo-Token` header sent

5. **Token Expiry:**
   - Manually update `demo_expires_at` in Supabase to past date
   - Refresh dashboard
   - Verify new demo initializes (old token rejected)
   - Verify fresh 10 sessions loaded

**Edge Cases:**
- ❌ Upload demo session without token → Should show 401 error
- ❌ Upload invalid session file → Should show 404 error
- ❌ Reset demo without token → Should show 401 error
- ❌ Expired token in localStorage → Should auto-initialize new demo
- ❌ Corrupted localStorage data → Should handle gracefully

## Performance Considerations

**Database Performance:**
- Indexes on `demo_token` and `demo_expires_at` ensure fast lookups
- Cleanup function uses batch deletes with CASCADE for efficiency
- Seed function uses single transaction for atomic demo creation

**Frontend Performance:**
- Demo initialization only runs once per page load
- localStorage checks avoid unnecessary API calls
- ProcessingContext polling uses existing infrastructure (no new polling loops)

**API Performance:**
- Demo token validation is O(1) with indexed lookup
- Background tasks for AI analysis don't block upload response
- Session fetching uses existing pagination (limit: 50)

**Scalability Considerations:**
- Each demo user is fully isolated (no shared data)
- 24h cleanup prevents database bloat
- Supabase RLS can be added for extra security (optional)

**Cost Optimization:**
- Real AI analysis costs ~$0.03 per demo upload (2 uploads max = $0.06/user)
- Acceptable for hackathon demo (minimal ongoing cost with 24h cleanup)

## Migration Notes

**Database Deployment:**
1. Run migration script on Supabase:
   ```bash
   psql $DATABASE_URL -f backend/supabase/migrations/006_add_demo_mode_support.sql
   ```

2. Register seed function:
   ```bash
   psql $DATABASE_URL -f backend/supabase/seed_demo_data.sql
   ```

3. Register cleanup function:
   ```bash
   psql $DATABASE_URL -f backend/supabase/cleanup_demo_data.sql
   ```

4. (Optional) Schedule cleanup cron job in Supabase:
   ```sql
   SELECT cron.schedule(
     'cleanup-demo-users',
     '0 * * * *',  -- Every hour
     'SELECT cleanup_expired_demo_users()'
   );
   ```

**Backend Deployment:**
- Deploy backend to Railway with updated code
- Verify `/api/demo/initialize` endpoint accessible
- Test demo token authentication

**Frontend Deployment:**
- Update environment variables if needed
- Deploy frontend to Railway/Vercel
- Verify localStorage works in production
- Test full demo flow on deployment URL

**Rollback Plan:**
- If issues occur, remove demo router from `main.py`
- Demo mode gracefully degrades (existing users unaffected)
- Database migration can be reverted:
  ```sql
  ALTER TABLE users
  DROP COLUMN demo_token,
  DROP COLUMN is_demo,
  DROP COLUMN demo_created_at,
  DROP COLUMN demo_expires_at;
  ```

## References

**Backend Files:**
- `backend/app/database.py:103-114` - Existing patient sessions query pattern
- `backend/app/routers/sessions.py:179-203` - Session creation endpoint
- `backend/app/routers/sessions.py:245-255` - Transcript upload pattern
- `backend/app/services/analysis_orchestrator.py:90-110` - Full AI analysis pipeline

**Frontend Files:**
- `frontend/components/NavigationBar.tsx:81-174` - Navigation structure
- `frontend/app/upload/page.tsx:26-32` - Upload success handler
- `frontend/contexts/ProcessingContext.tsx:45-80` - Status polling logic
- `frontend/app/patient/contexts/SessionDataContext.tsx:30-60` - Session data fetching
- `frontend/lib/api-client.ts:72-95` - API request method

**Mock Data:**
- `mock-therapy-data/sessions/session_12_thriving.json` - Demo upload file
- `mock-therapy-data/sessions/session_11_rebuilding.json` - Demo upload file
- `mock-therapy-data/sessions/session_01_crisis_intake.json:1-100` - Transcript structure reference

**Documentation:**
- Project README: `README.md`
- TherapyBridge docs: `Project MDs/TherapyBridge.md`
- Session log: `.claude/CLAUDE.md:201-350` - Previous AI implementation patterns
