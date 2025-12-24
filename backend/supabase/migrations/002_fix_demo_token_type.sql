-- ============================================================================
-- Migration: Fix demo_token column type (UUID -> TEXT)
-- ============================================================================
-- Purpose: Change demo_token from UUID to TEXT to support string tokens
--          Required by seed_demo_v4 function which generates string tokens
--
-- Date: 2025-12-23
-- ============================================================================

-- Change demo_token column type from UUID to TEXT
ALTER TABLE users
ALTER COLUMN demo_token TYPE TEXT USING demo_token::TEXT;

-- ============================================================================
-- Verification query (run after migration):
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'users' AND column_name = 'demo_token';
-- ============================================================================
