-- ============================================================================
-- Migration: Update seed_demo_v4 to include is_demo flag
-- ============================================================================
-- Purpose: Ensure demo users are properly marked with is_demo = TRUE
--          Required by demo authentication middleware
--
-- Date: 2025-12-23
-- ============================================================================

CREATE OR REPLACE FUNCTION seed_demo_v4(p_demo_token TEXT)
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

  -- Session dates from mock-therapy-data/sessions/*.json metadata
  v_session_dates DATE[] := ARRAY[
    '2025-01-10'::date,  -- session_01_crisis_intake.json
    '2025-01-17'::date,  -- session_02_emotional_regulation.json
    '2025-01-31'::date,  -- session_03_adhd_discovery.json
    '2025-02-14'::date,  -- session_04_medication_start.json
    '2025-02-28'::date,  -- session_05_family_conflict.json
    '2025-03-14'::date,  -- session_06_spring_break_hope.json
    '2025-04-04'::date,  -- session_07_dating_anxiety.json
    '2025-04-18'::date,  -- session_08_relationship_boundaries.json
    '2025-05-02'::date,  -- session_09_coming_out_preparation.json
    '2025-05-09'::date   -- session_10_coming_out_aftermath.json
  ];

  v_session_date DATE;
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
    NULL,
    TRUE,
    NOW(),
    NOW()
  ) RETURNING id INTO v_therapist_id;

  -- ========================================
  -- Step 2: Create Patient User (with is_demo flag)
  -- ========================================
  INSERT INTO users (
    email,
    first_name,
    last_name,
    role,
    password_hash,
    is_verified,
    is_demo,
    demo_token,
    demo_expires_at,
    created_at,
    updated_at
  ) VALUES (
    'demo_patient_' || gen_random_uuid() || '@demo.therapybridge.com',
    'Alex',
    'Chen',
    'patient',
    NULL,
    TRUE,
    TRUE,  -- Mark as demo user
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
  -- Step 4: Create ALL 10 Sessions
  -- ========================================
  -- Loop through all session dates and create sessions
  FOREACH v_session_date IN ARRAY v_session_dates
  LOOP
    INSERT INTO therapy_sessions (
      id,
      patient_id,
      therapist_id,
      session_date,
      duration_minutes,
      status,
      transcript,         -- Empty JSONB array (populated by Python script)
      created_at,
      updated_at
    ) VALUES (
      gen_random_uuid(),
      v_patient_id,
      v_therapist_id,
      v_session_date,
      60,                 -- All sessions are 60 minutes
      'completed',
      '[]'::jsonb,        -- Empty transcript initially
      NOW(),
      NOW()
    ) RETURNING id INTO v_session_id;

    -- Add to session IDs array
    v_session_ids := array_append(v_session_ids, v_session_id);
  END LOOP;

  -- ========================================
  -- Return Results
  -- ========================================
  RETURN QUERY SELECT v_patient_id, v_session_ids;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Verification: Function should now include is_demo = TRUE for patient user
-- ============================================================================
