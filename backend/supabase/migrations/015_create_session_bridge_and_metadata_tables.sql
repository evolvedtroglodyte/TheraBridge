-- Migration 015: Create Session Bridge tables + generation_metadata table
--
-- This migration creates:
-- 1. generation_metadata table (shared metadata for Your Journey + Session Bridge)
-- 2. patient_session_bridge table (1 per patient)
-- 3. session_bridge_versions table (append-only version history)
--
-- Date: 2026-01-18
-- Related: Session Bridge Backend Integration
-- Prerequisites: Migration 014 (Your Journey rename) must be applied first

-- ================================================================
-- STEP 1: Create generation_metadata table (shared across features)
-- ================================================================
CREATE TABLE generation_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Polymorphic foreign keys (exactly one must be set)
    your_journey_version_id UUID REFERENCES your_journey_versions(id) ON DELETE CASCADE,
    session_bridge_version_id UUID REFERENCES session_bridge_versions(id) ON DELETE CASCADE,

    -- Metadata fields (shared across both features)
    sessions_analyzed INTEGER NOT NULL,
    total_sessions INTEGER NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    generation_timestamp TIMESTAMPTZ NOT NULL,
    generation_duration_ms INTEGER NOT NULL,
    last_session_id UUID REFERENCES therapy_sessions(id),

    -- Feature-specific fields (nullable for compatibility)
    compaction_strategy VARCHAR(50),  -- Your Journey only (hierarchical, progressive, full)

    -- Additional flexible metadata (for future extensions)
    metadata_json JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Constraint: exactly one foreign key must be set
    CHECK (
        (your_journey_version_id IS NOT NULL AND session_bridge_version_id IS NULL) OR
        (your_journey_version_id IS NULL AND session_bridge_version_id IS NOT NULL)
    )
);

-- ================================================================
-- STEP 2: Create Session Bridge main table
-- ================================================================
CREATE TABLE patient_session_bridge (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL UNIQUE REFERENCES patients(id) ON DELETE CASCADE,

    -- Current version reference (updated when new version created)
    current_version_id UUID REFERENCES session_bridge_versions(id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ================================================================
-- STEP 3: Create Session Bridge versions table (append-only history)
-- ================================================================
CREATE TABLE session_bridge_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    session_bridge_id UUID NOT NULL REFERENCES patient_session_bridge(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,

    -- Bridge data (contains shareConcerns, shareProgress, setGoals arrays)
    bridge_data JSONB NOT NULL,

    -- Generation context (input data used for generation)
    generation_context JSONB,

    -- Model and cost tracking
    model_used VARCHAR(50),
    cost FLOAT,  -- Actual cost from track_generation_cost()
    generation_duration_ms INTEGER,

    -- Link to shared metadata table
    generation_metadata_id UUID REFERENCES generation_metadata(id),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Unique constraint: one version per patient per version number
    UNIQUE(patient_id, version_number)
);

-- ================================================================
-- STEP 4: Create indexes for optimal query performance
-- ================================================================

-- Partial indexes for polymorphic FK (only index non-NULL values)
CREATE INDEX idx_generation_metadata_your_journey
ON generation_metadata(your_journey_version_id)
WHERE your_journey_version_id IS NOT NULL;

CREATE INDEX idx_generation_metadata_session_bridge
ON generation_metadata(session_bridge_version_id)
WHERE session_bridge_version_id IS NOT NULL;

-- Generation metadata timestamp index (for sorting by generation time)
CREATE INDEX idx_generation_metadata_timestamp
ON generation_metadata(generation_timestamp);

-- Session Bridge version lookups
CREATE INDEX idx_session_bridge_versions_patient
ON session_bridge_versions(patient_id);

CREATE INDEX idx_session_bridge_versions_session_bridge
ON session_bridge_versions(session_bridge_id);

CREATE INDEX idx_session_bridge_versions_version_number
ON session_bridge_versions(patient_id, version_number);

-- ================================================================
-- STEP 5: Add generation_metadata_id column to existing tables
-- ================================================================
-- Link existing Your Journey versions to new metadata table (nullable for backward compatibility)

ALTER TABLE your_journey_versions
ADD COLUMN generation_metadata_id UUID REFERENCES generation_metadata(id) ON DELETE SET NULL;

-- ================================================================
-- COMMENTS
-- ================================================================
COMMENT ON TABLE generation_metadata IS 'Shared metadata for Your Journey and Session Bridge generations. Editing this table affects both features.';
COMMENT ON COLUMN generation_metadata.your_journey_version_id IS 'Foreign key to your_journey_versions (mutually exclusive with session_bridge_version_id)';
COMMENT ON COLUMN generation_metadata.session_bridge_version_id IS 'Foreign key to session_bridge_versions (mutually exclusive with your_journey_version_id)';
COMMENT ON COLUMN generation_metadata.compaction_strategy IS 'Your Journey only: hierarchical, progressive, or full compaction strategy used';
COMMENT ON COLUMN generation_metadata.metadata_json IS 'Flexible JSONB field for future extensions without schema changes';

COMMENT ON TABLE patient_session_bridge IS 'Session Bridge main table (one per patient). Tracks current version of bridge data.';
COMMENT ON TABLE session_bridge_versions IS 'Session Bridge version history (append-only). New version created after each session.';

COMMENT ON COLUMN session_bridge_versions.bridge_data IS 'JSONB containing shareConcerns (4 items), shareProgress (4 items), setGoals (4 items) arrays';
COMMENT ON COLUMN session_bridge_versions.generation_context IS 'Context data used for generation (e.g., tier1_insights, tier2_insights, tier3_insights)';
COMMENT ON COLUMN session_bridge_versions.cost IS 'Actual cost from track_generation_cost() (not estimated)';
