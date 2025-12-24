-- Migration 016: Remove CHECK constraint from analysis_processing_log.wave
--
-- This migration removes the CHECK constraint that limits wave names to specific values.
-- Rationale: Allows adding new waves ("your_journey", "session_bridge", future waves)
--            without requiring database migrations for each new wave.
--
-- Date: 2026-01-18
-- Related: Session Bridge Backend Integration (Wave 3 logging)
-- User Decision: Q16, Q80 - REMOVE constraint entirely for maximum flexibility

-- ================================================================
-- STEP 1: Remove CHECK constraint (if exists)
-- ================================================================
-- Original constraint from migration 004:
-- CONSTRAINT check_wave CHECK (wave IN ('mood', 'topics', 'breakthrough', 'deep'))
--
-- Using IF EXISTS for idempotency (migration can run multiple times safely)

ALTER TABLE analysis_processing_log
DROP CONSTRAINT IF EXISTS check_wave;

-- ================================================================
-- STEP 2: Add comment documenting valid wave values
-- ================================================================
-- Since we're removing the database-level constraint, document the expected values
-- Application-level validation can be added if needed

COMMENT ON COLUMN analysis_processing_log.wave IS 'Wave identifier: mood, topics, breakthrough, deep, your_journey, session_bridge. No CHECK constraint to allow future waves without migrations.';

-- ================================================================
-- NOTES
-- ================================================================
-- After this migration, the following wave names can be inserted:
-- - "mood" (Wave 1)
-- - "topics" (Wave 1)
-- - "breakthrough" (Wave 1)
-- - "deep" (Wave 2)
-- - "your_journey" (Wave 3)
-- - "session_bridge" (Wave 3)
-- - Any future wave names without requiring schema migrations
--
-- Application-level validation should be added in service layer if needed
-- (e.g., VALID_WAVE_NAMES set in analysis_orchestrator.py)
