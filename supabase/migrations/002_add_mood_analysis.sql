-- Add mood analysis fields to therapy_sessions table
-- Migration: 002_add_mood_analysis.sql
-- Description: Adds AI-powered mood analysis support with 0.0-10.0 scoring

-- Add mood analysis fields
ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS mood_score DECIMAL(3,1) CHECK (mood_score >= 0 AND mood_score <= 10 AND MOD(mood_score::NUMERIC * 10, 5) = 0),
ADD COLUMN IF NOT EXISTS mood_confidence DECIMAL(3,2) CHECK (mood_confidence >= 0 AND mood_confidence <= 1),
ADD COLUMN IF NOT EXISTS mood_rationale TEXT,
ADD COLUMN IF NOT EXISTS mood_indicators JSONB,
ADD COLUMN IF NOT EXISTS emotional_tone VARCHAR(100),
ADD COLUMN IF NOT EXISTS mood_analyzed_at TIMESTAMP WITH TIME ZONE;

-- Add index for mood score queries (for mood history visualization)
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_mood_score
ON therapy_sessions(patient_id, session_date)
WHERE mood_score IS NOT NULL;

-- Add index for mood analysis timestamp
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_mood_analyzed
ON therapy_sessions(mood_analyzed_at)
WHERE mood_analyzed_at IS NOT NULL;

-- Comment on columns
COMMENT ON COLUMN therapy_sessions.mood_score IS 'Patient mood score from 0.0 (severe distress) to 10.0 (very positive) in 0.5 increments';
COMMENT ON COLUMN therapy_sessions.mood_confidence IS 'AI confidence score for mood analysis (0.0 to 1.0)';
COMMENT ON COLUMN therapy_sessions.mood_rationale IS 'AI explanation for the mood score';
COMMENT ON COLUMN therapy_sessions.mood_indicators IS 'Key indicators that influenced the mood score (JSONB array)';
COMMENT ON COLUMN therapy_sessions.emotional_tone IS 'Overall emotional quality (e.g., anxious, hopeful, flat)';
COMMENT ON COLUMN therapy_sessions.mood_analyzed_at IS 'Timestamp when mood analysis was last run';

-- Create view for mood trends
CREATE OR REPLACE VIEW patient_mood_trends AS
SELECT
  ts.patient_id,
  ts.id as session_id,
  ts.session_date,
  ts.mood_score,
  ts.mood_confidence,
  ts.emotional_tone,
  LAG(ts.mood_score, 1) OVER (PARTITION BY ts.patient_id ORDER BY ts.session_date) as previous_mood_score,
  LEAD(ts.mood_score, 1) OVER (PARTITION BY ts.patient_id ORDER BY ts.session_date) as next_mood_score,
  ts.mood_score - LAG(ts.mood_score, 1) OVER (PARTITION BY ts.patient_id ORDER BY ts.session_date) as mood_change,
  AVG(ts.mood_score) OVER (
    PARTITION BY ts.patient_id
    ORDER BY ts.session_date
    ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
  ) as rolling_avg_4_sessions
FROM therapy_sessions ts
WHERE ts.mood_score IS NOT NULL
ORDER BY ts.patient_id, ts.session_date;

-- Grant access to view
GRANT SELECT ON patient_mood_trends TO authenticated;

-- Create function to get mood statistics for a patient
CREATE OR REPLACE FUNCTION get_patient_mood_stats(p_patient_id UUID, p_days INTEGER DEFAULT 90)
RETURNS TABLE (
  avg_mood DECIMAL,
  min_mood DECIMAL,
  max_mood DECIMAL,
  mood_range DECIMAL,
  trend VARCHAR,
  session_count INTEGER,
  recent_avg DECIMAL,
  historical_avg DECIMAL
) AS $$
DECLARE
  v_midpoint_date TIMESTAMP WITH TIME ZONE;
BEGIN
  -- Calculate midpoint date for trend analysis
  SELECT NOW() - (p_days / 2 || ' days')::INTERVAL INTO v_midpoint_date;

  RETURN QUERY
  WITH mood_data AS (
    SELECT
      ts.mood_score,
      ts.session_date
    FROM therapy_sessions ts
    WHERE ts.patient_id = p_patient_id
      AND ts.mood_score IS NOT NULL
      AND ts.session_date >= NOW() - (p_days || ' days')::INTERVAL
  ),
  recent_data AS (
    SELECT AVG(mood_score) as avg_recent
    FROM mood_data
    WHERE session_date >= v_midpoint_date
  ),
  historical_data AS (
    SELECT AVG(mood_score) as avg_historical
    FROM mood_data
    WHERE session_date < v_midpoint_date
  )
  SELECT
    ROUND(AVG(m.mood_score)::NUMERIC, 1)::DECIMAL as avg_mood,
    MIN(m.mood_score) as min_mood,
    MAX(m.mood_score) as max_mood,
    ROUND((MAX(m.mood_score) - MIN(m.mood_score))::NUMERIC, 1)::DECIMAL as mood_range,
    CASE
      WHEN r.avg_recent > h.avg_historical + 1 THEN 'improving'
      WHEN r.avg_recent < h.avg_historical - 1 THEN 'declining'
      WHEN r.avg_recent > h.avg_historical + 0.5 THEN 'slightly_improving'
      WHEN r.avg_recent < h.avg_historical - 0.5 THEN 'slightly_declining'
      ELSE 'stable'
    END as trend,
    COUNT(*)::INTEGER as session_count,
    ROUND(r.avg_recent::NUMERIC, 1)::DECIMAL as recent_avg,
    ROUND(h.avg_historical::NUMERIC, 1)::DECIMAL as historical_avg
  FROM mood_data m
  CROSS JOIN recent_data r
  CROSS JOIN historical_data h
  GROUP BY r.avg_recent, h.avg_historical;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION get_patient_mood_stats TO authenticated;
