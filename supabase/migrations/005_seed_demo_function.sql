-- ============================================================================
-- Demo User Seeding Function
-- ============================================================================
-- Creates a demo user with 10 therapy sessions pre-loaded with transcripts
-- Used by /api/demo/initialize endpoint for instant demo access
-- ============================================================================

-- Drop function if exists (for re-running migration)
DROP FUNCTION IF EXISTS seed_demo_user_sessions(UUID);

-- Create function to seed demo user with sessions
CREATE OR REPLACE FUNCTION seed_demo_user_sessions(p_demo_token UUID)
RETURNS TABLE (
    user_id UUID,
    session_ids UUID[],
    sessions_created INTEGER
) AS $$
DECLARE
    v_user_id UUID;
    v_patient_id UUID;
    v_therapist_id UUID;
    v_session_ids UUID[] := ARRAY[]::UUID[];
    v_session_id UUID;
    v_session_count INTEGER := 0;
BEGIN
    -- Check if demo user already exists for this token
    SELECT id INTO v_user_id
    FROM users
    WHERE demo_token = p_demo_token;

    -- Create demo user if doesn't exist
    IF v_user_id IS NULL THEN
        INSERT INTO users (
            email,
            first_name,
            last_name,
            role,
            demo_token,
            demo_expires_at,
            is_verified,
            created_at
        ) VALUES (
            'demo_' || p_demo_token || '@therapybridge.demo',
            'Demo',
            'Patient',
            'patient',
            p_demo_token,
            NOW() + INTERVAL '24 hours',
            false,
            NOW()
        ) RETURNING id INTO v_user_id;

        v_patient_id := v_user_id;

        -- Create demo therapist
        INSERT INTO users (
            email,
            first_name,
            last_name,
            role,
            is_verified,
            created_at
        ) VALUES (
            'demo_therapist_' || p_demo_token || '@therapybridge.demo',
            'Dr. Maria',
            'Rodriguez',
            'therapist',
            true,
            NOW()
        ) RETURNING id INTO v_therapist_id;

        -- Session 1: Crisis Intake (2025-01-10)
        INSERT INTO therapy_sessions (
            patient_id,
            therapist_id,
            session_date,
            duration_minutes,
            status,
            transcript,
            audio_file_url,
            created_at
        ) VALUES (
            v_patient_id,
            v_therapist_id,
            '2025-01-10 14:00:00',
            60,
            'completed',
            '[{"start": 0.0, "end": 28.4, "text": "Hi Alex, welcome. I''m Dr. Rodriguez. Thanks for coming in today. Before we start, I want to explain a bit about confidentiality and how therapy works. Everything we discuss here is private unless you''re in danger of hurting yourself or someone else, or if there''s child abuse involved. Does that make sense?", "speaker": "SPEAKER_00", "speaker_id": "SPEAKER_00"}, {"start": 28.4, "end": 45.8, "text": "Yeah, that makes sense. Um, I''m really nervous. I''ve never done therapy before. My roommate kind of pushed me to make this appointment.", "speaker": "SPEAKER_01", "speaker_id": "SPEAKER_01"}]'::jsonb,
            'demo_audio/session_01.mp3',
            NOW()
        ) RETURNING id INTO v_session_id;
        v_session_ids := array_append(v_session_ids, v_session_id);
        v_session_count := v_session_count + 1;

        -- Session 2: Emotional Regulation (2025-01-17)
        INSERT INTO therapy_sessions (
            patient_id,
            therapist_id,
            session_date,
            duration_minutes,
            status,
            transcript,
            audio_file_url,
            created_at
        ) VALUES (
            v_patient_id,
            v_therapist_id,
            '2025-01-17 14:00:00',
            60,
            'completed',
            '[{"start": 0.0, "end": 15.2, "text": "Hi Alex! Good to see you again. How was your week?", "speaker": "SPEAKER_00", "speaker_id": "SPEAKER_00"}, {"start": 15.2, "end": 42.8, "text": "It was... rough. I had a couple panic attacks this week. One was in class, which was really embarrassing. I had to leave in the middle of my chemistry lecture.", "speaker": "SPEAKER_01", "speaker_id": "SPEAKER_01"}]'::jsonb,
            'demo_audio/session_02.mp3',
            NOW()
        ) RETURNING id INTO v_session_id;
        v_session_ids := array_append(v_session_ids, v_session_id);
        v_session_count := v_session_count + 1;

        -- Session 3: ADHD Discovery (2025-01-24)
        INSERT INTO therapy_sessions (
            patient_id,
            therapist_id,
            session_date,
            duration_minutes,
            status,
            transcript,
            audio_file_url,
            created_at
        ) VALUES (
            v_patient_id,
            v_therapist_id,
            '2025-01-24 14:00:00',
            60,
            'completed',
            '[{"start": 0.0, "end": 18.3, "text": "Hey Alex. You mentioned you wanted to talk about something specific today?", "speaker": "SPEAKER_00", "speaker_id": "SPEAKER_00"}, {"start": 18.3, "end": 58.7, "text": "Yeah. So, I''ve been doing some reading online - which I know, Dr. Google isn''t always great - but I came across information about ADHD and... a lot of it really resonated with me. Like, way more than I expected.", "speaker": "SPEAKER_01", "speaker_id": "SPEAKER_01"}]'::jsonb,
            'demo_audio/session_03.mp3',
            NOW()
        ) RETURNING id INTO v_session_id;
        v_session_ids := array_append(v_session_ids, v_session_id);
        v_session_count := v_session_count + 1;

        -- Session 4: Medication Start (2025-01-31)
        INSERT INTO therapy_sessions (
            patient_id,
            therapist_id,
            session_date,
            duration_minutes,
            status,
            transcript,
            audio_file_url,
            created_at
        ) VALUES (
            v_patient_id,
            v_therapist_id,
            '2025-01-31 14:00:00',
            60,
            'completed',
            '[{"start": 0.0, "end": 22.1, "text": "Hi Alex! I''m excited to hear how your appointment with Dr. Kim went. Did you get a chance to talk about the ADHD assessment?", "speaker": "SPEAKER_00", "speaker_id": "SPEAKER_00"}, {"start": 22.1, "end": 54.3, "text": "Yes! So... it''s official. Dr. Kim confirmed the ADHD diagnosis - combined type, which means both inattentive and hyperactive symptoms. It was such a weird mix of relief and ''oh crap'' when she told me.", "speaker": "SPEAKER_01", "speaker_id": "SPEAKER_01"}]'::jsonb,
            'demo_audio/session_04.mp3',
            NOW()
        ) RETURNING id INTO v_session_id;
        v_session_ids := array_append(v_session_ids, v_session_id);
        v_session_count := v_session_count + 1;

        -- Session 5: Family Conflict (2025-02-07)
        INSERT INTO therapy_sessions (
            patient_id,
            therapist_id,
            session_date,
            duration_minutes,
            status,
            transcript,
            audio_file_url,
            created_at
        ) VALUES (
            v_patient_id,
            v_therapist_id,
            '2025-02-07 14:00:00',
            60,
            'completed',
            '[{"start": 0.0, "end": 12.8, "text": "Hey Alex. You look upset. What''s going on?", "speaker": "SPEAKER_00", "speaker_id": "SPEAKER_00"}, {"start": 12.8, "end": 48.2, "text": "I had a fight with my mom this week. Like, a really bad one. I finally told her about the ADHD diagnosis and that I''m on medication now, and she... she didn''t take it well.", "speaker": "SPEAKER_01", "speaker_id": "SPEAKER_01"}]'::jsonb,
            'demo_audio/session_05.mp3',
            NOW()
        ) RETURNING id INTO v_session_id;
        v_session_ids := array_append(v_session_ids, v_session_id);
        v_session_count := v_session_count + 1;

        -- Session 6: Spring Break Hope (2025-03-14)
        INSERT INTO therapy_sessions (
            patient_id,
            therapist_id,
            session_date,
            duration_minutes,
            status,
            transcript,
            audio_file_url,
            created_at
        ) VALUES (
            v_patient_id,
            v_therapist_id,
            '2025-03-14 14:00:00',
            60,
            'completed',
            '[{"start": 0.0, "end": 18.7, "text": "Hi Alex! Welcome back from spring break. You seem lighter today - how was the break?", "speaker": "SPEAKER_00", "speaker_id": "SPEAKER_00"}, {"start": 18.7, "end": 52.3, "text": "It was really good, actually. I spent the week with my roommate Sarah and some friends. We went to the beach, just relaxed, didn''t think about school for a whole week. It was exactly what I needed.", "speaker": "SPEAKER_01", "speaker_id": "SPEAKER_01"}]'::jsonb,
            'demo_audio/session_06.mp3',
            NOW()
        ) RETURNING id INTO v_session_id;
        v_session_ids := array_append(v_session_ids, v_session_id);
        v_session_count := v_session_count + 1;

        -- Session 7: Dating Anxiety (2025-03-21)
        INSERT INTO therapy_sessions (
            patient_id,
            therapist_id,
            session_date,
            duration_minutes,
            status,
            transcript,
            audio_file_url,
            created_at
        ) VALUES (
            v_patient_id,
            v_therapist_id,
            '2025-03-21 14:00:00',
            60,
            'completed',
            '[{"start": 0.0, "end": 15.2, "text": "Hey Alex. You texted that you wanted to talk about something new today?", "speaker": "SPEAKER_00", "speaker_id": "SPEAKER_00"}, {"start": 15.2, "end": 48.9, "text": "Yeah. Um. So there''s this person in my study group. Jordan. And I... I think I might have feelings for them? Which is kind of freaking me out because I''ve never really dated anyone seriously.", "speaker": "SPEAKER_01", "speaker_id": "SPEAKER_01"}]'::jsonb,
            'demo_audio/session_07.mp3',
            NOW()
        ) RETURNING id INTO v_session_id;
        v_session_ids := array_append(v_session_ids, v_session_id);
        v_session_count := v_session_count + 1;

        -- Session 8: Relationship Boundaries (2025-03-28)
        INSERT INTO therapy_sessions (
            patient_id,
            therapist_id,
            session_date,
            duration_minutes,
            status,
            transcript,
            audio_file_url,
            created_at
        ) VALUES (
            v_patient_id,
            v_therapist_id,
            '2025-03-28 14:00:00',
            60,
            'completed',
            '[{"start": 0.0, "end": 18.3, "text": "Hi Alex! I''ve been thinking about you this week. How did things go with Jordan?", "speaker": "SPEAKER_00", "speaker_id": "SPEAKER_00"}, {"start": 18.3, "end": 52.7, "text": "We went on a date! It was... really nice, actually. We got coffee and then walked around campus for like three hours just talking. It felt really easy and natural.", "speaker": "SPEAKER_01", "speaker_id": "SPEAKER_01"}]'::jsonb,
            'demo_audio/session_08.mp3',
            NOW()
        ) RETURNING id INTO v_session_id;
        v_session_ids := array_append(v_session_ids, v_session_id);
        v_session_count := v_session_count + 1;

        -- Session 9: Coming Out Preparation (2025-04-04)
        INSERT INTO therapy_sessions (
            patient_id,
            therapist_id,
            session_date,
            duration_minutes,
            status,
            transcript,
            audio_file_url,
            created_at
        ) VALUES (
            v_patient_id,
            v_therapist_id,
            '2025-04-04 14:00:00',
            60,
            'completed',
            '[{"start": 0.0, "end": 14.8, "text": "Hey Alex. You mentioned wanting to talk about your family today?", "speaker": "SPEAKER_00", "speaker_id": "SPEAKER_00"}, {"start": 14.8, "end": 58.2, "text": "Yeah. So... Jordan and I have been together for a few weeks now, and it''s going really well. Like, really well. And I''ve been thinking... I want to tell my parents about them. But I''m terrified.", "speaker": "SPEAKER_01", "speaker_id": "SPEAKER_01"}]'::jsonb,
            'demo_audio/session_09.mp3',
            NOW()
        ) RETURNING id INTO v_session_id;
        v_session_ids := array_append(v_session_ids, v_session_id);
        v_session_count := v_session_count + 1;

        -- Session 10: Coming Out Aftermath (2025-04-11)
        INSERT INTO therapy_sessions (
            patient_id,
            therapist_id,
            session_date,
            duration_minutes,
            status,
            transcript,
            audio_file_url,
            created_at
        ) VALUES (
            v_patient_id,
            v_therapist_id,
            '2025-04-11 14:00:00',
            60,
            'completed',
            '[{"start": 0.0, "end": 12.3, "text": "Alex. Come in. How are you doing?", "speaker": "SPEAKER_00", "speaker_id": "SPEAKER_00"}, {"start": 12.3, "end": 38.7, "text": "I told them. I came out to my parents this past weekend. About Jordan, about me being queer, all of it.", "speaker": "SPEAKER_01", "speaker_id": "SPEAKER_01"}]'::jsonb,
            'demo_audio/session_10.mp3',
            NOW()
        ) RETURNING id INTO v_session_id;
        v_session_ids := array_append(v_session_ids, v_session_id);
        v_session_count := v_session_count + 1;

    ELSE
        -- Demo user already exists, fetch their sessions
        SELECT array_agg(id)
        INTO v_session_ids
        FROM therapy_sessions
        WHERE patient_id = v_user_id
        ORDER BY session_date;

        v_session_count := array_length(v_session_ids, 1);
    END IF;

    -- Return results
    RETURN QUERY SELECT v_user_id, v_session_ids, v_session_count;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION seed_demo_user_sessions(UUID) TO authenticated, anon;

-- Add helpful comment
COMMENT ON FUNCTION seed_demo_user_sessions(UUID) IS
'Seeds a demo user with 10 therapy sessions. Used by /api/demo/initialize endpoint. Returns user_id, session_ids array, and count.';
