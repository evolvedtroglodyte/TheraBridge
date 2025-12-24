-- ============================================================================
-- Migration: Add is_demo column to users table
-- ============================================================================
-- Purpose: Differentiate demo users from real authenticated users
--          Required by demo authentication middleware
--
-- Date: 2025-12-23
-- ============================================================================

-- Add is_demo column if it doesn't exist
ALTER TABLE users
ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;

-- Update users with demo_token to be marked as demo users
UPDATE users
SET is_demo = TRUE
WHERE demo_token IS NOT NULL;

-- ============================================================================
-- Verification query (run after migration):
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'users' AND column_name = 'is_demo';
-- ============================================================================
