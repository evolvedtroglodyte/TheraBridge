"""add processing_status and processing_progress columns to therapy_sessions

Revision ID: l2m3n4o5p6q7
Revises: k2l3m4n5o6p7
Create Date: 2025-12-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'l2m3n4o5p6q7'
down_revision = 'k2l3m4n5o6p7'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add processing_status and processing_progress columns to therapy_sessions table.

    These columns enable real-time UI updates during session processing:
    - processing_status: Tracks detailed processing stages (uploading, preprocessing,
      transcribing, diarizing, generating_notes, completed, failed)
    - processing_progress: Percentage completion (0-100%) for progress indicators

    Reference: ORCHESTRATOR_PROMPT_UPHEAL_IMPLEMENTATION.md (lines 88-99)

    Implementation notes:
    - Uses VARCHAR(50) instead of PostgreSQL ENUM for flexibility
    - SessionStatus enum is defined in Python (schemas.py), not at DB level
    - CHECK constraint ensures progress stays within 0-100 range
    - Index on processing_status improves filtering performance
    """

    # Add processing_status column (VARCHAR, not ENUM)
    op.add_column('therapy_sessions', sa.Column(
        'processing_status',
        sa.String(length=50),
        nullable=False,
        server_default='pending'
    ))

    # Add processing_progress column with default value
    op.add_column('therapy_sessions', sa.Column(
        'processing_progress',
        sa.Integer(),
        nullable=False,
        server_default='0'
    ))

    # Add CHECK constraint to ensure progress is between 0 and 100
    op.create_check_constraint(
        'ck_therapy_sessions_processing_progress_range',
        'therapy_sessions',
        'processing_progress >= 0 AND processing_progress <= 100'
    )

    # Add index on processing_status for efficient filtering/querying
    op.create_index(
        'ix_therapy_sessions_processing_status',
        'therapy_sessions',
        ['processing_status'],
        unique=False
    )


def downgrade():
    """
    Remove processing_status and processing_progress columns.
    """
    # Drop index first
    op.drop_index('ix_therapy_sessions_processing_status', table_name='therapy_sessions')

    # Drop CHECK constraint
    op.drop_constraint('ck_therapy_sessions_processing_progress_range', 'therapy_sessions', type_='check')

    # Drop columns
    op.drop_column('therapy_sessions', 'processing_progress')
    op.drop_column('therapy_sessions', 'processing_status')
