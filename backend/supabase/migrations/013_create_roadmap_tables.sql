-- Patient roadmap data (latest version)
CREATE TABLE IF NOT EXISTS patient_roadmap (
    patient_id UUID PRIMARY KEY REFERENCES patients(id) ON DELETE CASCADE,
    roadmap_data JSONB NOT NULL,
    metadata JSONB NOT NULL,  -- sessions_analyzed, total_sessions, compaction_strategy, model_used, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_roadmap_patient ON patient_roadmap(patient_id);
CREATE INDEX idx_roadmap_updated ON patient_roadmap(updated_at);

-- Add comment
COMMENT ON TABLE patient_roadmap IS 'Current roadmap data for each patient (Your Journey card)';
COMMENT ON COLUMN patient_roadmap.metadata IS 'Metadata: {sessions_analyzed: int, total_sessions: int, compaction_strategy: str, model_used: str, generation_timestamp: str, last_session_id: uuid}';

-- Roadmap version history (all previous roadmaps)
CREATE TABLE IF NOT EXISTS roadmap_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    version INT NOT NULL,  -- Incremental version number (1, 2, 3, ...)
    roadmap_data JSONB NOT NULL,
    metadata JSONB NOT NULL,  -- Same structure as patient_roadmap.metadata
    generation_context JSONB,  -- What context was passed to LLM (for debugging)
    cost FLOAT,  -- Track cost per generation
    generation_duration_ms INT,  -- Track performance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(patient_id, version)  -- Ensure unique version numbers per patient
);

-- Indexes
CREATE INDEX idx_roadmap_versions_patient ON roadmap_versions(patient_id);
CREATE INDEX idx_roadmap_versions_created ON roadmap_versions(created_at);

-- Add comment
COMMENT ON TABLE roadmap_versions IS 'Version history of all roadmap generations for debugging and analysis';
COMMENT ON COLUMN roadmap_versions.generation_context IS 'Context passed to LLM (tier summaries, session data, etc.) for debugging';
