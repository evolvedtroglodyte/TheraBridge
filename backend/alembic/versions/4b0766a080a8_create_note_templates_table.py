"""create_note_templates_table

Revision ID: 4b0766a080a8
Revises: db710499da37
Create Date: 2025-12-19 06:34:40.569911

This migration creates the note_templates table for customizable note formats.
Therapists can create and manage templates (SOAP, DAP, custom) with JSON structure
for GPT-4 prompt generation.

Table: note_templates
- Stores template definitions with JSONB structure
- Foreign key to users.id with CASCADE delete
- Unique constraint on (user_id, name) - no duplicate template names per user
- Supports multiple template types (soap, dap, custom)
- Tracks default templates per user
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4b0766a080a8'
down_revision: Union[str, Sequence[str], None] = 'db710499da37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create note_templates table with defensive checks."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Only create table if it doesn't exist
    if 'note_templates' not in tables:
        op.create_table(
            'note_templates',
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('template_type', sa.String(length=50), nullable=False),
            sa.Column('template_content', postgresql.JSONB(), nullable=False),
            sa.Column('is_default', sa.Boolean(), nullable=False,
                      server_default=sa.false()),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False,
                      server_default=sa.text('NOW()')),
            sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False,
                      server_default=sa.text('NOW()')),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.UniqueConstraint('user_id', 'name', name='uq_note_templates_user_name')
        )

        # Add index on user_id for fast user template lookups
        op.create_index(
            'ix_note_templates_user_id',
            'note_templates',
            ['user_id']
        )


def downgrade() -> None:
    """Drop note_templates table."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Only drop table if it exists
    if 'note_templates' in tables:
        op.drop_index('ix_note_templates_user_id', table_name='note_templates')
        op.drop_table('note_templates')
