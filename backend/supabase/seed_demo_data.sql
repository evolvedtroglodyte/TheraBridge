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
        demo_expires_at
    ) VALUES (
        'therapist_' || p_demo_token || '@demo.therapybridge.com',
        'Dr. Sarah',
        'Rodriguez',
        'therapist',
        TRUE,
        p_demo_token,
        NOW(),
        NOW() + INTERVAL '24 hours'
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
        demo_expires_at
    ) VALUES (
        'patient_' || p_demo_token || '@demo.therapybridge.com',
        'Alex',
        'Chen',
        'patient',
        TRUE,
        p_demo_token,
        NOW(),
        NOW() + INTERVAL '24 hours'
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
