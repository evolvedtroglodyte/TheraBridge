-- Migration: Add breakthrough_label field to therapy_sessions
-- Date: 2025-12-23
-- Purpose: Store concise 2-3 word AI-generated label for UI display

-- Add breakthrough_label column (nullable, since existing sessions won't have it)
ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS breakthrough_label VARCHAR(50);

-- Add comment for documentation
COMMENT ON COLUMN therapy_sessions.breakthrough_label IS
'Concise 2-3 word AI-generated label for breakthrough moments (e.g., "ADHD Discovery", "Attachment Pattern")';

-- Index for filtering sessions with breakthroughs
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_breakthrough_label
ON therapy_sessions(breakthrough_label)
WHERE breakthrough_label IS NOT NULL;
