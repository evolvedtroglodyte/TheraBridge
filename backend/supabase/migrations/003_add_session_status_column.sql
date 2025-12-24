-- ============================================================================
-- Migration: Add status column to therapy_sessions table
-- ============================================================================
-- Purpose: Track session completion status
--          Required by seed_demo_v4 function
--
-- Date: 2025-12-23
-- ============================================================================

-- Add status column if it doesn't exist
-- Valid values: 'scheduled', 'in_progress', 'completed', 'cancelled'
ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'completed';

-- Update existing sessions to 'completed' (backwards compatibility)
UPDATE therapy_sessions
SET status = 'completed'
WHERE status IS NULL;

-- ============================================================================
-- Verification query (run after migration):
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'therapy_sessions' AND column_name = 'status';
-- ============================================================================
