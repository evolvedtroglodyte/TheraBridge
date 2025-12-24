-- Migration: Add action_items_summary field for condensed action display
-- Created: 2026-01-07
-- Description: Stores 45-character max summary combining both action items

ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS action_items_summary TEXT;

COMMENT ON COLUMN therapy_sessions.action_items_summary IS
'AI-generated 45-character max summary combining both action items for compact display';
