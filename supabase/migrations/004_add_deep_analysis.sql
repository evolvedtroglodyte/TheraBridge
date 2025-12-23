-- Add deep analysis fields to therapy_sessions table
-- Migration: 004_add_deep_analysis.sql
-- Description: Adds AI-powered deep clinical analysis with multi-wave orchestration

-- =============================================================================
-- Add deep analysis result columns
-- =============================================================================

ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS deep_analysis JSONB,
ADD COLUMN IF NOT EXISTS analysis_confidence DECIMAL(3,2) CHECK (analysis_confidence >= 0 AND analysis_confidence <= 1),
ADD COLUMN IF NOT EXISTS deep_analyzed_at TIMESTAMP WITH TIME ZONE;

-- Add analysis orchestration status columns
ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS analysis_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS wave1_completed_at TIMESTAMP WITH TIME ZONE;

-- Add check constraint for analysis_status values
ALTER TABLE therapy_sessions
ADD CONSTRAINT check_analysis_status
CHECK (analysis_status IN ('pending', 'wave1_running', 'wave1_complete', 'wave2_running', 'complete', 'failed'));

-- =============================================================================
-- Create analysis processing log table
-- =============================================================================

CREATE TABLE IF NOT EXISTS analysis_processing_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID NOT NULL REFERENCES therapy_sessions(id) ON DELETE CASCADE,
  wave VARCHAR(20) NOT NULL,  -- 'mood', 'topics', 'breakthrough', 'deep'
  status VARCHAR(20) NOT NULL,  -- 'started', 'completed', 'failed'
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0,
  processing_duration_ms INTEGER,  -- Duration in milliseconds
  CONSTRAINT check_wave CHECK (wave IN ('mood', 'topics', 'breakthrough', 'deep')),
  CONSTRAINT check_status CHECK (status IN ('started', 'completed', 'failed'))
);

-- =============================================================================
-- Add indexes for performance
-- =============================================================================

-- Index for analysis status queries
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_analysis_status
ON therapy_sessions(analysis_status);

-- Index for deep analysis queries
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_deep_analyzed
ON therapy_sessions(deep_analyzed_at)
WHERE deep_analyzed_at IS NOT NULL;

-- Index for wave1 completion queries
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_wave1_completed
ON therapy_sessions(wave1_completed_at)
WHERE wave1_completed_at IS NOT NULL;

-- Index for processing log queries by session
CREATE INDEX IF NOT EXISTS idx_analysis_log_session
ON analysis_processing_log(session_id, started_at DESC);

-- Index for processing log queries by status
CREATE INDEX IF NOT EXISTS idx_analysis_log_status
ON analysis_processing_log(status, started_at DESC);

-- Index for failed analysis tracking
CREATE INDEX IF NOT EXISTS idx_analysis_log_failed
ON analysis_processing_log(session_id, wave)
WHERE status = 'failed';

-- =============================================================================
-- Add comments for documentation
-- =============================================================================

COMMENT ON COLUMN therapy_sessions.deep_analysis IS 'AI-generated deep clinical analysis with progress indicators, insights, coping skills, relationship quality, and recommendations (JSONB)';
COMMENT ON COLUMN therapy_sessions.analysis_confidence IS 'AI confidence score for deep analysis (0.0 to 1.0)';
COMMENT ON COLUMN therapy_sessions.deep_analyzed_at IS 'Timestamp when deep analysis was last run';
COMMENT ON COLUMN therapy_sessions.analysis_status IS 'Current status of analysis pipeline: pending, wave1_running, wave1_complete, wave2_running, complete, failed';
COMMENT ON COLUMN therapy_sessions.wave1_completed_at IS 'Timestamp when all Wave 1 analyses (mood, topics, breakthrough) completed';

COMMENT ON TABLE analysis_processing_log IS 'Tracks status of each analysis wave for debugging and retry logic';
COMMENT ON COLUMN analysis_processing_log.wave IS 'Analysis wave type: mood, topics, breakthrough, or deep';
COMMENT ON COLUMN analysis_processing_log.status IS 'Current status: started, completed, or failed';
COMMENT ON COLUMN analysis_processing_log.retry_count IS 'Number of retry attempts for this wave';
COMMENT ON COLUMN analysis_processing_log.processing_duration_ms IS 'Processing time in milliseconds';

-- =============================================================================
-- Create helper functions
-- =============================================================================

-- Function to check if Wave 1 is complete for a session
CREATE OR REPLACE FUNCTION is_wave1_complete(p_session_id UUID)
RETURNS BOOLEAN AS $$
DECLARE
  v_session RECORD;
BEGIN
  SELECT
    mood_analyzed_at,
    topics_extracted_at,
    breakthrough_analyzed_at
  INTO v_session
  FROM therapy_sessions
  WHERE id = p_session_id;

  -- Wave 1 is complete if all three analyses have completed
  RETURN (
    v_session.mood_analyzed_at IS NOT NULL AND
    v_session.topics_extracted_at IS NOT NULL AND
    v_session.breakthrough_analyzed_at IS NOT NULL
  );
END;
$$ LANGUAGE plpgsql;

-- Function to get analysis pipeline status for a session
CREATE OR REPLACE FUNCTION get_analysis_pipeline_status(p_session_id UUID)
RETURNS TABLE (
  session_id UUID,
  analysis_status VARCHAR,
  mood_complete BOOLEAN,
  topics_complete BOOLEAN,
  breakthrough_complete BOOLEAN,
  wave1_complete BOOLEAN,
  deep_complete BOOLEAN,
  wave1_completed_at TIMESTAMP WITH TIME ZONE,
  deep_analyzed_at TIMESTAMP WITH TIME ZONE,
  recent_logs JSONB
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    ts.id as session_id,
    ts.analysis_status,
    (ts.mood_analyzed_at IS NOT NULL) as mood_complete,
    (ts.topics_extracted_at IS NOT NULL) as topics_complete,
    (ts.breakthrough_analyzed_at IS NOT NULL) as breakthrough_complete,
    is_wave1_complete(ts.id) as wave1_complete,
    (ts.deep_analyzed_at IS NOT NULL) as deep_complete,
    ts.wave1_completed_at,
    ts.deep_analyzed_at,
    (
      SELECT jsonb_agg(
        jsonb_build_object(
          'wave', apl.wave,
          'status', apl.status,
          'started_at', apl.started_at,
          'completed_at', apl.completed_at,
          'retry_count', apl.retry_count,
          'error_message', apl.error_message
        ) ORDER BY apl.started_at DESC
      )
      FROM analysis_processing_log apl
      WHERE apl.session_id = ts.id
      LIMIT 10
    ) as recent_logs
  FROM therapy_sessions ts
  WHERE ts.id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get failed analyses for retry
CREATE OR REPLACE FUNCTION get_failed_analyses(
  p_max_retries INTEGER DEFAULT 3,
  p_limit INTEGER DEFAULT 50
)
RETURNS TABLE (
  session_id UUID,
  wave VARCHAR,
  retry_count INTEGER,
  last_error TEXT,
  last_attempt TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
  RETURN QUERY
  SELECT DISTINCT ON (apl.session_id, apl.wave)
    apl.session_id,
    apl.wave,
    apl.retry_count,
    apl.error_message as last_error,
    apl.started_at as last_attempt
  FROM analysis_processing_log apl
  WHERE apl.status = 'failed'
    AND apl.retry_count < p_max_retries
  ORDER BY apl.session_id, apl.wave, apl.started_at DESC
  LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Grant permissions
-- =============================================================================

GRANT SELECT ON analysis_processing_log TO authenticated;
GRANT INSERT ON analysis_processing_log TO authenticated;
GRANT UPDATE ON analysis_processing_log TO authenticated;

GRANT EXECUTE ON FUNCTION is_wave1_complete TO authenticated;
GRANT EXECUTE ON FUNCTION get_analysis_pipeline_status TO authenticated;
GRANT EXECUTE ON FUNCTION get_failed_analyses TO authenticated;

-- =============================================================================
-- Create view for monitoring analysis pipeline health
-- =============================================================================

CREATE OR REPLACE VIEW analysis_pipeline_health AS
SELECT
  ts.analysis_status,
  COUNT(*) as session_count,
  AVG(EXTRACT(EPOCH FROM (ts.wave1_completed_at - ts.created_at))) as avg_wave1_duration_seconds,
  AVG(EXTRACT(EPOCH FROM (ts.deep_analyzed_at - ts.wave1_completed_at))) as avg_wave2_duration_seconds,
  COUNT(*) FILTER (WHERE ts.analysis_status = 'complete') as completed_count,
  COUNT(*) FILTER (WHERE ts.analysis_status = 'failed') as failed_count,
  COUNT(*) FILTER (WHERE ts.analysis_status IN ('wave1_running', 'wave2_running')) as in_progress_count
FROM therapy_sessions ts
WHERE ts.created_at >= NOW() - INTERVAL '30 days'
GROUP BY ts.analysis_status
ORDER BY session_count DESC;

GRANT SELECT ON analysis_pipeline_health TO authenticated;

COMMENT ON VIEW analysis_pipeline_health IS 'Monitor analysis pipeline performance and health metrics (last 30 days)';
