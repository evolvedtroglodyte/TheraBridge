-- Seed data for breakthrough detection demo
-- This populates users with realistic therapy session breakthroughs
-- Based on actual therapy transcripts from audio pipeline

-- Note: Run this AFTER schema.sql and 001_add_breakthrough_detection.sql

-- ============================================================================
-- DEMO USER SETUP
-- ============================================================================

-- Demo Patient: Alex Chen (same as mock data)
INSERT INTO users (id, email, password_hash, first_name, last_name, role)
VALUES (
  '00000000-0000-0000-0000-000000000001',
  'alex.chen@demo.com',
  '$2b$12$demo_hash_for_testing_only',
  'Alex',
  'Chen',
  'patient'
) ON CONFLICT (email) DO NOTHING;

-- Demo Therapist: Dr. Sarah Mitchell
INSERT INTO users (id, email, password_hash, first_name, last_name, role)
VALUES (
  '00000000-0000-0000-0000-000000000002',
  'dr.mitchell@demo.com',
  '$2b$12$demo_hash_for_testing_only',
  'Sarah',
  'Mitchell',
  'therapist'
) ON CONFLICT (email) DO NOTHING;

-- Create patient record
INSERT INTO patients (id, user_id, therapist_id, date_of_birth, phone)
VALUES (
  '00000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000002',
  '1998-05-15',
  '555-0123'
) ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SESSION 1: Initial Phase - Eating Disorder Discovery
-- Based on: Initial Phase and Interpersonal Inventory 1 [A1XJeciqyL8].mp3
-- ============================================================================

INSERT INTO therapy_sessions (
  id,
  patient_id,
  therapist_id,
  session_date,
  duration_minutes,
  processing_status,
  transcript,
  summary,
  mood,
  topics,
  key_insights,
  action_items,
  has_breakthrough,
  breakthrough_data,
  breakthrough_analyzed_at
) VALUES (
  '10000000-0000-0000-0000-000000000001',
  '00000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000002',
  NOW() - INTERVAL '12 days',
  50,
  'completed',
  '[]'::jsonb, -- Full transcript would be here
  'Initial intake session focusing on eating disorder history. Patient identified bulimia nervosa patterns and explored family dynamics contributing to body image issues.',
  'neutral',
  ARRAY['Eating disorder', 'Family dynamics', 'Body image'],
  ARRAY['Mother''s pressure linked to eating issues', 'Divorce trauma at age 10', 'Private school transition difficulties'],
  ARRAY['Begin food diary', 'Identify trigger situations', 'Practice mindful eating'],
  TRUE,
  jsonb_build_object(
    'type', 'cognitive_insight',
    'description', 'Patient connected mother''s critical comments about appearance to development of eating disorder in middle school',
    'evidence', 'Patient verbalized "I felt like more pressure from my mom. She was very vocal towards me about my eating and my looks" with recognition of causal relationship between maternal criticism and bulimic behaviors',
    'confidence', 0.87,
    'timestamp_start', 512.3,
    'timestamp_end', 645.8,
    'dialogue_excerpt', jsonb_build_array(
      jsonb_build_object('speaker', 'Therapist', 'text', 'When did you first start feeling pressure from your mom about your appearance?'),
      jsonb_build_object('speaker', 'Patient', 'text', 'I think it started when we moved to the private school. She wanted me to look good, to fit in.'),
      jsonb_build_object('speaker', 'Therapist', 'text', 'And how did that pressure affect your eating?'),
      jsonb_build_object('speaker', 'Patient', 'text', 'I started restricting, trying to eat only healthy food. But then there was junk food around from my stepdad, and I''d binge on it.')
    )
  ),
  NOW() - INTERVAL '12 days'
);

-- Add breakthrough history entry
INSERT INTO breakthrough_history (
  session_id,
  breakthrough_type,
  description,
  evidence,
  confidence_score,
  timestamp_start,
  timestamp_end,
  dialogue_excerpt,
  is_primary
) VALUES (
  '10000000-0000-0000-0000-000000000001',
  'cognitive_insight',
  'Patient connected mother''s critical comments about appearance to development of eating disorder in middle school',
  'Patient verbalized "I felt like more pressure from my mom. She was very vocal towards me about my eating and my looks" with recognition of causal relationship',
  0.87,
  512.3,
  645.8,
  jsonb_build_array(
    jsonb_build_object('speaker', 'Therapist', 'text', 'When did you first start feeling pressure from your mom?'),
    jsonb_build_object('speaker', 'Patient', 'text', 'She wanted me to look good, to fit in.')
  ),
  TRUE
);

-- ============================================================================
-- SESSION 2: Carl Rogers Style - Emotional Processing
-- Based on: Carl Rogers and Gloria - Counselling 1965 Full Session
-- ============================================================================

INSERT INTO therapy_sessions (
  id,
  patient_id,
  therapist_id,
  session_date,
  duration_minutes,
  processing_status,
  summary,
  mood,
  topics,
  key_insights,
  action_items,
  has_breakthrough,
  breakthrough_data,
  breakthrough_analyzed_at
) VALUES (
  '10000000-0000-0000-0000-000000000002',
  '00000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000002',
  NOW() - INTERVAL '9 days',
  45,
  'completed',
  'Session focused on emotional processing and self-acceptance. Patient explored feelings of inadequacy and made progress toward self-compassion.',
  'positive',
  ARRAY['Self-worth', 'Emotional expression', 'Self-acceptance'],
  ARRAY['Recognition of self-critical patterns', 'Validation of emotional experiences', 'Emerging self-compassion'],
  ARRAY['Practice self-compassion meditation', 'Journal about positive qualities'],
  TRUE,
  jsonb_build_object(
    'type', 'self_compassion',
    'description', 'Patient experienced shift from harsh self-criticism to beginning self-acceptance and recognition of inherent worth',
    'evidence', 'Patient expressed "I think I''ve been really hard on myself. Maybe I don''t have to be perfect to be okay" with visible emotional relief',
    'confidence', 0.82,
    'timestamp_start', 1245.6,
    'timestamp_end', 1398.2
  ),
  NOW() - INTERVAL '9 days'
);

INSERT INTO breakthrough_history (
  session_id,
  breakthrough_type,
  description,
  evidence,
  confidence_score,
  timestamp_start,
  timestamp_end,
  is_primary
) VALUES (
  '10000000-0000-0000-0000-000000000002',
  'self_compassion',
  'Patient shifted from harsh self-criticism to beginning self-acceptance',
  'Patient expressed "Maybe I don''t have to be perfect to be okay" with visible relief',
  0.82,
  1245.6,
  1398.2,
  TRUE
);

-- ============================================================================
-- SESSION 3: CBT Session - Cognitive Restructuring
-- Based on: LIVE Cognitive Behavioral Therapy Session
-- ============================================================================

INSERT INTO therapy_sessions (
  id,
  patient_id,
  therapist_id,
  session_date,
  duration_minutes,
  processing_status,
  summary,
  mood,
  topics,
  key_insights,
  action_items,
  has_breakthrough,
  breakthrough_data,
  breakthrough_analyzed_at
) VALUES (
  '10000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000002',
  NOW() - INTERVAL '5 days',
  55,
  'completed',
  'CBT-focused session on identifying and challenging negative thought patterns. Patient learned to recognize cognitive distortions.',
  'positive',
  ARRAY['Cognitive distortions', 'Anxiety management', 'Thought records'],
  ARRAY['Identified catastrophizing pattern', 'Learned thought challenging technique', 'Recognized all-or-nothing thinking'],
  ARRAY['Complete daily thought records', 'Practice cognitive restructuring', 'Identify three alternative thoughts'],
  TRUE,
  jsonb_build_object(
    'type', 'cognitive_insight',
    'description', 'Patient recognized pattern of catastrophizing and learned to identify automatic negative thoughts in real-time',
    'evidence', 'Patient said "Oh wow, I''m doing it right now! I''m jumping to the worst possible outcome without any evidence" demonstrating meta-cognitive awareness',
    'confidence', 0.91,
    'timestamp_start', 1678.4,
    'timestamp_end', 1752.9
  ),
  NOW() - INTERVAL '5 days'
);

INSERT INTO breakthrough_history (
  session_id,
  breakthrough_type,
  description,
  evidence,
  confidence_score,
  timestamp_start,
  timestamp_end,
  is_primary
) VALUES (
  '10000000-0000-0000-0000-000000000003',
  'cognitive_insight',
  'Patient recognized catastrophizing pattern with real-time meta-cognitive awareness',
  'Patient demonstrated insight: "I''m jumping to the worst possible outcome without any evidence"',
  0.91,
  1678.4,
  1752.9,
  TRUE
);

-- ============================================================================
-- SESSION 4: Boundary Setting - Behavioral Breakthrough
-- ============================================================================

INSERT INTO therapy_sessions (
  id,
  patient_id,
  therapist_id,
  session_date,
  duration_minutes,
  processing_status,
  summary,
  mood,
  topics,
  key_insights,
  action_items,
  has_breakthrough,
  breakthrough_data,
  breakthrough_analyzed_at
) VALUES (
  '10000000-0000-0000-0000-000000000004',
  '00000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000002',
  NOW() - INTERVAL '2 days',
  48,
  'completed',
  'Session focused on assertiveness and boundary-setting skills. Patient successfully practiced saying no.',
  'positive',
  ARRAY['Boundaries', 'Assertiveness', 'Family relationships'],
  ARRAY['First successful boundary with mother', 'Reduced people-pleasing behavior', 'Recognized right to say no'],
  ARRAY['Continue practicing boundaries', 'Notice feelings when setting limits'],
  TRUE,
  jsonb_build_object(
    'type', 'behavioral_commitment',
    'description', 'Patient successfully set first clear boundary with mother by declining babysitting request',
    'evidence', 'Patient reported "I actually said no to my mom for the first time. It was scary at first, but then relieving. Like a weight lifted." with visible pride and relief',
    'confidence', 0.85,
    'timestamp_start', 245.1,
    'timestamp_end', 312.7
  ),
  NOW() - INTERVAL '2 days'
);

INSERT INTO breakthrough_history (
  session_id,
  breakthrough_type,
  description,
  evidence,
  confidence_score,
  timestamp_start,
  timestamp_end,
  is_primary
) VALUES (
  '10000000-0000-0000-0000-000000000004',
  'behavioral_commitment',
  'First successful boundary-setting with mother',
  'Patient said no to babysitting request with reported relief and empowerment',
  0.85,
  245.1,
  312.7,
  TRUE
);

-- ============================================================================
-- SESSION 5: Attachment Patterns - Relational Insight
-- ============================================================================

INSERT INTO therapy_sessions (
  id,
  patient_id,
  therapist_id,
  session_date,
  duration_minutes,
  processing_status,
  summary,
  mood,
  topics,
  key_insights,
  action_items,
  has_breakthrough,
  breakthrough_data,
  breakthrough_analyzed_at
) VALUES (
  '10000000-0000-0000-0000-000000000005',
  '00000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000002',
  NOW() - INTERVAL '1 day',
  52,
  'completed',
  'Deep exploration of relationship patterns and attachment style. Patient connected childhood experiences to adult romantic anxiety.',
  'neutral',
  ARRAY['Attachment patterns', 'Relationship anxiety', 'Childhood trauma'],
  ARRAY['Identified anxious attachment style', 'Connected parental divorce to relationship fears', 'Recognized compulsive reassurance-seeking'],
  ARRAY['Notice anxious thoughts in relationships', 'Practice self-soothing', 'Read about attachment theory'],
  TRUE,
  jsonb_build_object(
    'type', 'relational_realization',
    'description', 'Patient recognized connection between childhood abandonment fears (father''s unpredictable departures) and current anxious attachment pattern in romantic relationships',
    'evidence', 'Patient had emotional "aha moment": "Oh my god. I''m that little kid watching out the window for my dad. When my boyfriend doesn''t text back, I''m doing the exact same thing."',
    'confidence', 0.94,
    'timestamp_start', 1834.2,
    'timestamp_end', 1923.6
  ),
  NOW() - INTERVAL '1 day'
);

INSERT INTO breakthrough_history (
  session_id,
  breakthrough_type,
  description,
  evidence,
  confidence_score,
  timestamp_start,
  timestamp_end,
  is_primary
) VALUES (
  '10000000-0000-0000-0000-000000000005',
  'relational_realization',
  'Connected childhood abandonment to adult anxious attachment',
  'Patient: "I''m that little kid watching out the window. I''m doing the exact same thing."',
  0.94,
  1834.2,
  1923.6,
  TRUE
);

-- ============================================================================
-- SESSION 6: Maintenance Session (NO BREAKTHROUGH)
-- ============================================================================

INSERT INTO therapy_sessions (
  id,
  patient_id,
  therapist_id,
  session_date,
  duration_minutes,
  processing_status,
  summary,
  mood,
  topics,
  key_insights,
  action_items,
  has_breakthrough,
  breakthrough_analyzed_at
) VALUES (
  '10000000-0000-0000-0000-000000000006',
  '00000000-0000-0000-0000-000000000003',
  '00000000-0000-0000-0000-000000000002',
  NOW(),
  45,
  'completed',
  'Check-in session reviewing progress on recent goals. Discussed ongoing practice of boundary-setting and cognitive restructuring techniques.',
  'positive',
  ARRAY['Progress review', 'Skill consolidation', 'Homework review'],
  ARRAY['Consistent use of thought records', 'Improved boundary-setting confidence'],
  ARRAY['Continue current practices', 'Monitor mood daily'],
  FALSE,
  NOW()
);

-- ============================================================================
-- Create treatment goals based on breakthrough insights
-- ============================================================================

INSERT INTO treatment_goals (patient_id, title, description, target_date, status, progress)
VALUES
  (
    '00000000-0000-0000-0000-000000000003',
    'Reduce bulimic episodes',
    'Decrease binge/purge cycles through identification of triggers and alternative coping strategies',
    NOW() + INTERVAL '3 months',
    'active',
    45
  ),
  (
    '00000000-0000-0000-0000-000000000003',
    'Practice self-compassion',
    'Replace self-critical thoughts with self-compassionate responses',
    NOW() + INTERVAL '2 months',
    'active',
    60
  ),
  (
    '00000000-0000-0000-0000-000000000003',
    'Set healthy boundaries',
    'Practice assertiveness with family members, especially mother',
    NOW() + INTERVAL '6 weeks',
    'active',
    70
  ),
  (
    '00000000-0000-0000-0000-000000000003',
    'Develop secure attachment patterns',
    'Reduce anxious behaviors in romantic relationships through self-soothing and reality-testing',
    NOW() + INTERVAL '4 months',
    'active',
    30
  );

-- ============================================================================
-- Helper function to count breakthroughs by type
-- ============================================================================

CREATE OR REPLACE FUNCTION get_patient_breakthrough_summary(p_patient_id UUID)
RETURNS TABLE (
  breakthrough_type VARCHAR,
  count BIGINT,
  avg_confidence DECIMAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    bh.breakthrough_type,
    COUNT(bh.id) as count,
    ROUND(AVG(bh.confidence_score), 2) as avg_confidence
  FROM breakthrough_history bh
  JOIN therapy_sessions ts ON bh.session_id = ts.id
  WHERE ts.patient_id = p_patient_id
  GROUP BY bh.breakthrough_type
  ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- Example usage: SELECT * FROM get_patient_breakthrough_summary('00000000-0000-0000-0000-000000000003');
