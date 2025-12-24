-- Migration 014: Rename Roadmap tables to Your Journey
--
-- This migration preserves all production data (10 patient_roadmap rows + 56 roadmap_versions rows)
-- using PostgreSQL's ALTER TABLE RENAME which is a metadata-only operation.
--
-- Date: 2026-01-18
-- Related: Session Bridge Backend Integration (Your Journey foundation)

-- ================================================================
-- STEP 1: Rename main tables
-- ================================================================
-- Note: PostgreSQL ALTER TABLE RENAME preserves all data, indexes, and constraints automatically
-- No manual data migration needed - this is a metadata operation only

ALTER TABLE patient_roadmap RENAME TO patient_your_journey;
ALTER TABLE roadmap_versions RENAME TO your_journey_versions;

-- ================================================================
-- STEP 2: Rename foreign key constraints for clarity
-- ================================================================
-- Update constraint names to match new table names

ALTER TABLE patient_your_journey
RENAME CONSTRAINT patient_roadmap_patient_id_fkey
TO patient_your_journey_patient_id_fkey;

ALTER TABLE your_journey_versions
RENAME CONSTRAINT roadmap_versions_patient_id_fkey
TO your_journey_versions_patient_id_fkey;

-- ================================================================
-- VERIFICATION QUERIES (Run after migration to verify data preserved)
-- ================================================================
-- SELECT COUNT(*) FROM patient_your_journey;  -- Should return 10
-- SELECT COUNT(*) FROM your_journey_versions;  -- Should return 56
-- SELECT * FROM patient_your_journey LIMIT 1;  -- Verify structure
-- SELECT * FROM your_journey_versions LIMIT 1;  -- Verify structure

-- ================================================================
-- COMMENTS
-- ================================================================
COMMENT ON TABLE patient_your_journey IS 'Your Journey dynamic roadmap for each patient (renamed from patient_roadmap in migration 014)';
COMMENT ON TABLE your_journey_versions IS 'Version history for Your Journey roadmaps (renamed from roadmap_versions in migration 014)';
