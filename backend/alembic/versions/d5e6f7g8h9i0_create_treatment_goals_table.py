"""Create treatment_goals table

Revision ID: d5e6f7g8h9i0
Revises: d4e5f6g7h8i9
Create Date: 2025-12-17 20:30:00.000000

This migration creates the treatment_goals table for Feature 6 goal tracking.
Goals are being migrated from action_items in therapy_sessions.extracted_notes JSONB
to a proper relational table with structured tracking capabilities.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd5e6f7g8h9i0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create treatment_goals table with defensive checks."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # ==========================================================================
    # Create treatment_goals table
    # ==========================================================================

    if 'treatment_goals' not in tables:
        op.create_table(
            'treatment_goals',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('therapist_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('category', sa.String(50), nullable=True),
            sa.Column('status', sa.String(20), server_default='assigned', nullable=False),
            sa.Column('baseline_value', sa.Numeric(10, 2), nullable=True),
            sa.Column('target_value', sa.Numeric(10, 2), nullable=True),
            sa.Column('target_date', sa.Date(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_treatment_goals_patient_id',
            'treatment_goals',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_treatment_goals_therapist_id',
            'treatment_goals',
            'users',
            ['therapist_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_treatment_goals_session_id',
            'treatment_goals',
            'therapy_sessions',
            ['session_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add indexes for performance
        op.create_index(
            'idx_treatment_goals_patient_created',
            'treatment_goals',
            ['patient_id', sa.text('created_at DESC')]
        )
        op.create_index(
            'idx_treatment_goals_therapist_status',
            'treatment_goals',
            ['therapist_id', 'status']
        )


def downgrade() -> None:
    """Reverse the changes."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Drop treatment_goals table if it exists
    if 'treatment_goals' in tables:
        op.drop_index('idx_treatment_goals_therapist_status', table_name='treatment_goals')
        op.drop_index('idx_treatment_goals_patient_created', table_name='treatment_goals')
        op.drop_constraint('fk_treatment_goals_session_id', 'treatment_goals', type_='foreignkey')
        op.drop_constraint('fk_treatment_goals_therapist_id', 'treatment_goals', type_='foreignkey')
        op.drop_constraint('fk_treatment_goals_patient_id', 'treatment_goals', type_='foreignkey')
        op.drop_table('treatment_goals')
