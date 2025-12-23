-- Add topic extraction fields to therapy_sessions table
-- Migration: 003_add_topic_extraction.sql
-- Description: Adds AI-powered topic extraction with metadata (topics, action items, technique, summary)

-- Add topic extraction fields
ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS topics TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS action_items TEXT[] DEFAULT '{}',
ADD COLUMN IF NOT EXISTS technique VARCHAR(255),
ADD COLUMN IF NOT EXISTS summary TEXT,
ADD COLUMN IF NOT EXISTS extraction_confidence DECIMAL(3,2) CHECK (extraction_confidence >= 0 AND extraction_confidence <= 1),
ADD COLUMN IF NOT EXISTS raw_meta_summary TEXT,
ADD COLUMN IF NOT EXISTS topics_extracted_at TIMESTAMP WITH TIME ZONE;

-- Add index for topic searches
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_topics
ON therapy_sessions USING GIN(topics)
WHERE topics IS NOT NULL AND array_length(topics, 1) > 0;

-- Add index for technique searches
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_technique
ON therapy_sessions(technique)
WHERE technique IS NOT NULL;

-- Add index for extraction timestamp
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_topics_extracted
ON therapy_sessions(topics_extracted_at)
WHERE topics_extracted_at IS NOT NULL;

-- Add index for patient+extraction queries
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_patient_topics
ON therapy_sessions(patient_id, session_date)
WHERE topics IS NOT NULL AND array_length(topics, 1) > 0;

-- Comment on columns
COMMENT ON COLUMN therapy_sessions.topics IS '1-2 main topics discussed in the session (AI-extracted)';
COMMENT ON COLUMN therapy_sessions.action_items IS '2 concrete action items or homework assignments (AI-extracted)';
COMMENT ON COLUMN therapy_sessions.technique IS 'Primary therapeutic technique used (e.g., CBT, DBT, psychoeducation)';
COMMENT ON COLUMN therapy_sessions.summary IS 'Ultra-brief clinical summary (max 150 characters) of the session';
COMMENT ON COLUMN therapy_sessions.extraction_confidence IS 'AI confidence score for topic extraction (0.0 to 1.0)';
COMMENT ON COLUMN therapy_sessions.raw_meta_summary IS 'Full AI response for debugging and future processing';
COMMENT ON COLUMN therapy_sessions.topics_extracted_at IS 'Timestamp when topic extraction was last run';

-- Create view for topic frequency analysis
CREATE OR REPLACE VIEW patient_topic_frequency AS
SELECT
  ts.patient_id,
  unnest(ts.topics) as topic,
  COUNT(*) as frequency,
  MAX(ts.session_date) as last_discussed,
  ARRAY_AGG(ts.id ORDER BY ts.session_date DESC) as session_ids
FROM therapy_sessions ts
WHERE ts.topics IS NOT NULL
  AND array_length(ts.topics, 1) > 0
GROUP BY ts.patient_id, topic
ORDER BY ts.patient_id, frequency DESC;

-- Grant access to view
GRANT SELECT ON patient_topic_frequency TO authenticated;

-- Create view for technique usage tracking
CREATE OR REPLACE VIEW patient_technique_history AS
SELECT
  ts.patient_id,
  ts.technique,
  COUNT(*) as usage_count,
  MAX(ts.session_date) as last_used,
  MIN(ts.session_date) as first_used,
  ARRAY_AGG(ts.id ORDER BY ts.session_date DESC) as session_ids,
  AVG(ts.mood_score) as avg_mood_when_used
FROM therapy_sessions ts
WHERE ts.technique IS NOT NULL
  AND ts.technique != ''
GROUP BY ts.patient_id, ts.technique
ORDER BY ts.patient_id, usage_count DESC;

-- Grant access to view
GRANT SELECT ON patient_technique_history TO authenticated;

-- Create function to get action items for a patient
CREATE OR REPLACE FUNCTION get_patient_action_items(
  p_patient_id UUID,
  p_limit INTEGER DEFAULT 10,
  p_recent_days INTEGER DEFAULT 30
)
RETURNS TABLE (
  session_id UUID,
  session_date TIMESTAMP WITH TIME ZONE,
  action_item TEXT,
  technique VARCHAR,
  extraction_confidence DECIMAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ts.id as session_id,
    ts.session_date,
    unnest(ts.action_items) as action_item,
    ts.technique,
    ts.extraction_confidence
  FROM therapy_sessions ts
  WHERE ts.patient_id = p_patient_id
    AND ts.action_items IS NOT NULL
    AND array_length(ts.action_items, 1) > 0
    AND ts.session_date >= NOW() - (p_recent_days || ' days')::INTERVAL
  ORDER BY ts.session_date DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION get_patient_action_items TO authenticated;

-- Create function to search sessions by topic
CREATE OR REPLACE FUNCTION search_sessions_by_topic(
  p_patient_id UUID,
  p_topic_pattern TEXT
)
RETURNS TABLE (
  session_id UUID,
  session_date TIMESTAMP WITH TIME ZONE,
  topics TEXT[],
  summary TEXT,
  mood_score DECIMAL
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ts.id as session_id,
    ts.session_date,
    ts.topics,
    ts.summary,
    ts.mood_score
  FROM therapy_sessions ts
  WHERE ts.patient_id = p_patient_id
    AND ts.topics IS NOT NULL
    AND EXISTS (
      SELECT 1
      FROM unnest(ts.topics) as topic
      WHERE topic ILIKE '%' || p_topic_pattern || '%'
    )
  ORDER BY ts.session_date DESC;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION search_sessions_by_topic TO authenticated;
