"""add deletion tracking columns to therapy_sessions

Revision ID: k1l2m3n4o5p6
Revises: j0k1l2m3n4o5
Create Date: 2025-12-19 10:00:00.000000

This migration adds granular deletion tracking to therapy_sessions table,
enabling Upheal-inspired soft-delete functionality. Allows tracking when
recordings and transcripts are deleted separately from the session itself.

Rationale:
- Therapists can delete audio files to save storage while keeping transcripts
- Transcripts can be deleted for privacy while keeping recordings for reprocessing
- Session metadata and notes are preserved even if recording/transcript deleted
- Supports compliance with varying retention policies (e.g., "delete recordings
  after 30 days but keep notes for 7 years")

NULL values indicate the data has NOT been deleted.
Timestamp values indicate WHEN the data was deleted (soft-delete pattern).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k1l2m3n4o5p6'
down_revision = 'j0k1l2m3n4o5'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add deletion tracking columns to therapy_sessions table.

    Columns:
        - recording_deleted_at: TIMESTAMP when audio file was deleted (NULL = not deleted)
        - transcript_deleted_at: TIMESTAMP when transcript was deleted (NULL = not deleted)

    These columns enable granular deletion of session components without removing
    the entire session record, supporting flexible data retention policies.
    """
    # Add recording deletion timestamp
    op.add_column(
        'therapy_sessions',
        sa.Column('recording_deleted_at', sa.DateTime(), nullable=True)
    )

    # Add transcript deletion timestamp
    op.add_column(
        'therapy_sessions',
        sa.Column('transcript_deleted_at', sa.DateTime(), nullable=True)
    )


def downgrade():
    """
    Remove deletion tracking columns from therapy_sessions table.

    Warning: This will permanently delete all deletion timestamp data.
    """
    # Remove deletion tracking columns
    op.drop_column('therapy_sessions', 'transcript_deleted_at')
    op.drop_column('therapy_sessions', 'recording_deleted_at')
