-- Add breakthrough detection fields to therapy_sessions table
-- Migration: 001_add_breakthrough_detection.sql
-- Description: Adds breakthrough detection support with JSONB storage

-- Add breakthrough fields
ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS has_breakthrough BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS breakthrough_data JSONB,
ADD COLUMN IF NOT EXISTS breakthrough_analyzed_at TIMESTAMP WITH TIME ZONE;

-- Add index for breakthrough queries
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_has_breakthrough
ON therapy_sessions(has_breakthrough)
WHERE has_breakthrough = TRUE;

-- Add index for JSONB breakthrough data queries
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_breakthrough_type
ON therapy_sessions USING gin ((breakthrough_data -> 'type'));

-- Create breakthrough_history table for tracking multiple breakthroughs per session
CREATE TABLE IF NOT EXISTS breakthrough_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES therapy_sessions(id) ON DELETE CASCADE,

  -- Breakthrough details
  breakthrough_type VARCHAR(50) NOT NULL CHECK (
    breakthrough_type IN (
      'cognitive_insight',
      'emotional_shift',
      'behavioral_commitment',
      'relational_realization',
      'self_compassion'
    )
  ),
  description TEXT NOT NULL,
  evidence TEXT NOT NULL,
  confidence_score DECIMAL(3,2) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),

  -- Timestamp in session
  timestamp_start DECIMAL(10,2) NOT NULL,
  timestamp_end DECIMAL(10,2) NOT NULL,

  -- Dialogue excerpt
  dialogue_excerpt JSONB, -- Array of {speaker, text}

  -- Metadata
  is_primary BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for session breakthroughs
CREATE INDEX IF NOT EXISTS idx_breakthrough_history_session_id
ON breakthrough_history(session_id);

-- Index for primary breakthroughs
CREATE INDEX IF NOT EXISTS idx_breakthrough_history_primary
ON breakthrough_history(session_id, is_primary)
WHERE is_primary = TRUE;

-- RLS for breakthrough_history
ALTER TABLE breakthrough_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY breakthrough_history_select_policy ON breakthrough_history FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM therapy_sessions ts
    JOIN patients p ON ts.patient_id = p.id
    WHERE ts.id = session_id AND (auth.uid() = p.user_id OR auth.uid() = ts.therapist_id)
  )
);

-- Comment on columns
COMMENT ON COLUMN therapy_sessions.has_breakthrough IS 'Whether session contains at least one breakthrough moment';
COMMENT ON COLUMN therapy_sessions.breakthrough_data IS 'Primary breakthrough details in JSONB format';
COMMENT ON COLUMN therapy_sessions.breakthrough_analyzed_at IS 'Timestamp when breakthrough detection was last run';
COMMENT ON TABLE breakthrough_history IS 'Historical record of all breakthroughs detected across sessions';

-- Create view for easy breakthrough querying
CREATE OR REPLACE VIEW session_breakthroughs AS
SELECT
  ts.id as session_id,
  ts.session_date,
  ts.patient_id,
  ts.has_breakthrough,
  ts.breakthrough_data ->> 'type' as primary_breakthrough_type,
  ts.breakthrough_data ->> 'description' as primary_breakthrough_description,
  (ts.breakthrough_data ->> 'confidence')::decimal as primary_breakthrough_confidence,
  COUNT(bh.id) as total_breakthroughs,
  json_agg(
    json_build_object(
      'type', bh.breakthrough_type,
      'description', bh.description,
      'confidence', bh.confidence_score,
      'timestamp', bh.timestamp_start
    )
  ) FILTER (WHERE bh.id IS NOT NULL) as all_breakthroughs
FROM therapy_sessions ts
LEFT JOIN breakthrough_history bh ON ts.id = bh.session_id
WHERE ts.has_breakthrough = TRUE
GROUP BY ts.id, ts.session_date, ts.patient_id, ts.has_breakthrough, ts.breakthrough_data;

-- Grant access to view
GRANT SELECT ON session_breakthroughs TO authenticated;
