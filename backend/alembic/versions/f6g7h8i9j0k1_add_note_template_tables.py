"""Add note template tables for Feature 3

Revision ID: f6g7h8i9j0k1
Revises: e5f6g7h8i9j0
Create Date: 2025-12-17 22:00:00.000000

This migration adds 3 note template tables for Feature 3 (Note Templates):
1. note_templates - Template definitions with JSONB structure
2. session_notes - Clinical notes with template-based content
3. template_usage - Tracking for template usage analytics

Note: Supports custom templates, system templates, and template sharing.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6g7h8i9j0k1'
down_revision: Union[str, Sequence[str], None] = 'e5f6g7h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add note template tables with defensive checks."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # ==========================================================================
    # STEP 1: Create note_templates table
    # ==========================================================================

    if 'note_templates' not in tables:
        op.create_table(
            'note_templates',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('template_type', sa.String(length=50), nullable=False),
            sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('is_shared', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('structure', postgresql.JSONB(), nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        )

        # Add foreign key to users
        op.create_foreign_key(
            'fk_note_templates_created_by',
            'note_templates',
            'users',
            ['created_by'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add check constraint for template_type
        op.create_check_constraint(
            'ck_note_templates_template_type',
            'note_templates',
            "template_type IN ('soap', 'dap', 'birp', 'girp', 'progress', 'intake', 'discharge', 'custom')"
        )

        # Add index on created_by for user queries
        op.create_index(
            'idx_note_templates_created_by',
            'note_templates',
            ['created_by']
        )

        # Add index on template_type for filtering
        op.create_index(
            'idx_note_templates_type',
            'note_templates',
            ['template_type']
        )

        # Add index on is_shared for finding shared templates
        op.create_index(
            'idx_note_templates_shared',
            'note_templates',
            ['is_shared']
        )

    # ==========================================================================
    # STEP 2: Create session_notes table
    # ==========================================================================

    if 'session_notes' not in tables:
        op.create_table(
            'session_notes',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('content', postgresql.JSONB(), nullable=False),
            sa.Column('status', sa.String(length=20), server_default='draft', nullable=False),
            sa.Column('signed_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('signed_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_session_notes_session_id',
            'session_notes',
            'therapy_sessions',
            ['session_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_session_notes_template_id',
            'session_notes',
            'note_templates',
            ['template_id'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_session_notes_signed_by',
            'session_notes',
            'users',
            ['signed_by'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add check constraint for status values
        op.create_check_constraint(
            'ck_session_notes_status',
            'session_notes',
            "status IN ('draft', 'final', 'signed', 'amended')"
        )

        # Add index on session_id for session queries
        op.create_index(
            'idx_session_notes_session_id',
            'session_notes',
            ['session_id']
        )

        # Add index on template_id for template queries
        op.create_index(
            'idx_session_notes_template_id',
            'session_notes',
            ['template_id']
        )

        # Add index on status for filtering
        op.create_index(
            'idx_session_notes_status',
            'session_notes',
            ['status']
        )

    # ==========================================================================
    # STEP 3: Create template_usage table
    # ==========================================================================

    if 'template_usage' not in tables:
        op.create_table(
            'template_usage',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('used_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_template_usage_template_id',
            'template_usage',
            'note_templates',
            ['template_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_template_usage_user_id',
            'template_usage',
            'users',
            ['user_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add index on template_id for usage analytics
        op.create_index(
            'idx_template_usage_template_id',
            'template_usage',
            ['template_id']
        )

        # Add index on user_id for user analytics
        op.create_index(
            'idx_template_usage_user_id',
            'template_usage',
            ['user_id']
        )

        # Add composite index for template usage by user over time
        op.create_index(
            'idx_template_usage_template_user_time',
            'template_usage',
            ['template_id', 'user_id', sa.text('used_at DESC')]
        )


def downgrade() -> None:
    """Reverse the changes."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Drop template_usage table if it exists (must be first due to foreign keys)
    if 'template_usage' in tables:
        op.drop_index('idx_template_usage_template_user_time', table_name='template_usage')
        op.drop_index('idx_template_usage_user_id', table_name='template_usage')
        op.drop_index('idx_template_usage_template_id', table_name='template_usage')
        op.drop_constraint('fk_template_usage_user_id', 'template_usage', type_='foreignkey')
        op.drop_constraint('fk_template_usage_template_id', 'template_usage', type_='foreignkey')
        op.drop_table('template_usage')

    # Drop session_notes table if it exists (must be second due to foreign keys)
    if 'session_notes' in tables:
        op.drop_index('idx_session_notes_status', table_name='session_notes')
        op.drop_index('idx_session_notes_template_id', table_name='session_notes')
        op.drop_index('idx_session_notes_session_id', table_name='session_notes')
        op.drop_check_constraint('ck_session_notes_status', 'session_notes', type_='check')
        op.drop_constraint('fk_session_notes_signed_by', 'session_notes', type_='foreignkey')
        op.drop_constraint('fk_session_notes_template_id', 'session_notes', type_='foreignkey')
        op.drop_constraint('fk_session_notes_session_id', 'session_notes', type_='foreignkey')
        op.drop_table('session_notes')

    # Drop note_templates table if it exists (must be last due to foreign keys)
    if 'note_templates' in tables:
        op.drop_index('idx_note_templates_shared', table_name='note_templates')
        op.drop_index('idx_note_templates_type', table_name='note_templates')
        op.drop_index('idx_note_templates_created_by', table_name='note_templates')
        op.drop_check_constraint('ck_note_templates_template_type', 'note_templates', type_='check')
        op.drop_constraint('fk_note_templates_created_by', 'note_templates', type_='foreignkey')
        op.drop_table('note_templates')
