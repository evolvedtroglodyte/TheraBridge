"""add anonymous mode and AI summary columns

Revision ID: k2l3m4n5o6p7
Revises: k1l2m3n4o5p6
Create Date: 2025-12-19 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k2l3m4n5o6p7'
down_revision = 'k1l2m3n4o5p6'
branch_labels = None
depends_on = None


def upgrade():
    """
    Add anonymous mode and AI summary columns to therapy_sessions table.

    Features:
        - is_anonymous: BOOLEAN column to support "Anonymous individual" mode
          (Upheal-inspired privacy feature where client name is not stored)
        - ai_summary: TEXT column for 1-2 sentence AI-generated session summaries
          (displayed on session cards, populated after GPT-4 extraction)

    Impact:
        - Enables privacy-first session recording without client identification
        - Provides quick session overview on dashboard cards
        - Index on is_anonymous for filtering anonymous sessions
        - Both columns nullable/defaulted for backwards compatibility

    References:
        - ORCHESTRATOR_PROMPT_UPHEAL_IMPLEMENTATION.md (lines 69-107)
        - UPHEAL_SESSIONS_PIPELINE_ANALYSIS.md (lines 43-73)
    """
    # Add is_anonymous column with default FALSE
    # Normal sessions show client name; anonymous sessions hide it
    op.add_column('therapy_sessions', sa.Column(
        'is_anonymous',
        sa.Boolean(),
        nullable=False,
        server_default=sa.false()  # Default to showing client name
    ))

    # Add ai_summary column (nullable)
    # Populated after AI extraction; provides 1-2 sentence overview for session cards
    # Example: "Client discusses feeling separate from family due to life choices
    #           and work conflict with passive-aggressive colleague."
    op.add_column('therapy_sessions', sa.Column(
        'ai_summary',
        sa.Text(),
        nullable=True  # Populated asynchronously after GPT-4 extraction
    ))

    # Add index for filtering anonymous sessions
    # Optimizes queries like: SELECT * FROM therapy_sessions WHERE is_anonymous = true
    op.create_index(
        'ix_therapy_sessions_is_anonymous',  # Index name
        'therapy_sessions',                   # Table name
        ['is_anonymous'],                     # Column to index
        unique=False                          # Not a unique constraint
    )


def downgrade():
    """
    Remove anonymous mode and AI summary columns from therapy_sessions table.
    """
    # Drop index first (before dropping column)
    op.drop_index('ix_therapy_sessions_is_anonymous', table_name='therapy_sessions')

    # Drop columns in reverse order
    op.drop_column('therapy_sessions', 'ai_summary')
    op.drop_column('therapy_sessions', 'is_anonymous')
