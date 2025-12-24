-- ============================================================================
-- Migration: seed_demo_v3 - Fixed Session Date
-- ============================================================================
-- Purpose: Update demo initialization to use fixed date (2025-01-10) for
--          Session 1, ensuring consistency with mock-therapy-data files.
--
-- Changes from seed_demo_v2:
-- - Session 1 date: random → fixed '2025-01-10'::date
-- - Ensures Session 1 displays at oldest position (not newest)
--
-- Author: System
-- Date: 2025-12-23
-- ============================================================================

CREATE OR REPLACE FUNCTION seed_demo_v3(p_demo_token TEXT)
RETURNS TABLE (
  patient_id UUID,
  session_ids UUID[]
) AS $$
DECLARE
  v_therapist_id UUID;
  v_user_id UUID;
  v_patient_id UUID;
  v_session_id UUID;
  v_session_ids UUID[] := '{}';
  v_demo_expires_at TIMESTAMPTZ;
BEGIN
  -- Calculate expiration (24 hours from now)
  v_demo_expires_at := NOW() + INTERVAL '24 hours';

  -- ========================================
  -- Step 1: Create Therapist User
  -- ========================================
  INSERT INTO users (
    email,
    first_name,
    last_name,
    role,
    password_hash,
    is_verified,
    created_at,
    updated_at
  ) VALUES (
    'demo_therapist_' || gen_random_uuid() || '@demo.therapybridge.com',
    'Dr. Sarah',
    'Rodriguez',
    'therapist',
    NULL,  -- password_hash is nullable
    TRUE,
    NOW(),
    NOW()
  ) RETURNING id INTO v_therapist_id;

  -- ========================================
  -- Step 2: Create Patient User
  -- ========================================
  INSERT INTO users (
    email,
    first_name,
    last_name,
    role,
    password_hash,
    is_verified,
    demo_token,           -- ONLY patient gets demo_token
    demo_expires_at,      -- ONLY patient gets expiry
    created_at,
    updated_at
  ) VALUES (
    'demo_patient_' || gen_random_uuid() || '@demo.therapybridge.com',
    'Alex',
    'Chen',
    'patient',
    NULL,  -- password_hash is nullable
    TRUE,
    p_demo_token,
    v_demo_expires_at,
    NOW(),
    NOW()
  ) RETURNING id INTO v_user_id;

  -- ========================================
  -- Step 3: Create Patient Record
  -- ========================================
  INSERT INTO patients (
    user_id,
    therapist_id,
    created_at,
    updated_at
  ) VALUES (
    v_user_id,
    v_therapist_id,
    NOW(),
    NOW()
  ) RETURNING id INTO v_patient_id;

  -- ========================================
  -- Step 4: Create Session 1 with FIXED DATE
  -- ========================================
  -- Session 1: January 10, 2025 (OLDEST session)
  -- This ensures Session 1 displays at oldest position, not newest
  INSERT INTO therapy_sessions (
    id,
    patient_id,
    therapist_id,
    session_date,          -- FIXED: '2025-01-10' (was random)
    duration_minutes,
    status,
    created_at,
    updated_at
  ) VALUES (
    gen_random_uuid(),
    v_patient_id,
    v_therapist_id,
    '2025-01-10'::date,   -- FIXED DATE: January 10, 2025
    60,
    'completed',
    NOW(),
    NOW()
  ) RETURNING id INTO v_session_id;

  -- Add session ID to array
  v_session_ids := array_append(v_session_ids, v_session_id);

  -- ========================================
  -- Return Results
  -- ========================================
  RETURN QUERY SELECT v_patient_id, v_session_ids;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Test Query (commented out - run manually to test)
-- ============================================================================
-- SELECT * FROM seed_demo_v3('test_demo_token_' || gen_random_uuid()::text);
--
-- Expected result:
-- | patient_id | session_ids |
-- | <uuid>     | {<uuid>}    |
--
-- Verify session date:
-- SELECT session_date FROM therapy_sessions WHERE patient_id = '<patient_id>';
-- Expected: 2025-01-10
-- ============================================================================
