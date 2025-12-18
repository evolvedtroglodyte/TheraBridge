"""Add goal tracking tables for Feature 6

Revision ID: e5f6g7h8i9j0
Revises: d5e6f7g8h9i0
Create Date: 2025-12-17 21:00:00.000000

This migration adds 5 goal tracking tables for Feature 6 (Goal Tracking):
1. goal_tracking_config - Configuration for how goals are tracked
2. progress_entries - Individual progress data points
3. assessment_scores - Standardized assessment results (PHQ-9, GAD-7, etc.)
4. progress_milestones - Achievement markers for goals
5. goal_reminders - Patient reminder configurations

Note: Depends on treatment_goals table from previous migration.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7g8h9i0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add goal tracking tables with defensive checks."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # ==========================================================================
    # STEP 1: Create goal_tracking_config table
    # ==========================================================================

    if 'goal_tracking_config' not in tables:
        op.create_table(
            'goal_tracking_config',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('goal_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('tracking_method', sa.String(length=50), nullable=False),
            sa.Column('tracking_frequency', sa.String(length=20), server_default='session', nullable=False),
            sa.Column('custom_frequency_days', sa.Integer(), nullable=True),
            sa.Column('scale_min', sa.Integer(), server_default='1', nullable=False),
            sa.Column('scale_max', sa.Integer(), server_default='10', nullable=False),
            sa.Column('scale_labels', postgresql.JSONB(), nullable=True),
            sa.Column('frequency_unit', sa.String(length=20), nullable=True),
            sa.Column('duration_unit', sa.String(length=20), nullable=True),
            sa.Column('target_direction', sa.String(length=10), nullable=True),
            sa.Column('reminder_enabled', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        )

        # Add foreign key to treatment_goals
        op.create_foreign_key(
            'fk_goal_tracking_config_goal_id',
            'goal_tracking_config',
            'treatment_goals',
            ['goal_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add check constraints for tracking_method
        op.create_check_constraint(
            'ck_goal_tracking_config_tracking_method',
            'goal_tracking_config',
            "tracking_method IN ('scale', 'frequency', 'duration', 'binary', 'assessment')"
        )

        # Add check constraints for scale values
        op.create_check_constraint(
            'ck_goal_tracking_config_scale_range',
            'goal_tracking_config',
            'scale_min < scale_max'
        )
        op.create_check_constraint(
            'ck_goal_tracking_config_scale_min',
            'goal_tracking_config',
            'scale_min >= 1'
        )
        op.create_check_constraint(
            'ck_goal_tracking_config_scale_max',
            'goal_tracking_config',
            'scale_max <= 10'
        )

        # Add check constraint for tracking_frequency
        op.create_check_constraint(
            'ck_goal_tracking_config_frequency',
            'goal_tracking_config',
            "tracking_frequency IN ('daily', 'weekly', 'session', 'custom')"
        )

        # Add check constraint for target_direction
        op.create_check_constraint(
            'ck_goal_tracking_config_direction',
            'goal_tracking_config',
            "target_direction IS NULL OR target_direction IN ('increase', 'decrease', 'maintain')"
        )

        # Add index on goal_id for queries
        op.create_index(
            'idx_goal_tracking_config_goal',
            'goal_tracking_config',
            ['goal_id']
        )

    # ==========================================================================
    # STEP 2: Create progress_entries table
    # ==========================================================================

    if 'progress_entries' not in tables:
        op.create_table(
            'progress_entries',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('goal_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('tracking_config_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('entry_date', sa.Date(), nullable=False),
            sa.Column('entry_time', sa.Time(), nullable=True),
            sa.Column('value', sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column('value_label', sa.String(length=100), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('context', sa.String(length=50), nullable=True),
            sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('recorded_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('recorded_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_progress_entries_goal_id',
            'progress_entries',
            'treatment_goals',
            ['goal_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_progress_entries_tracking_config_id',
            'progress_entries',
            'goal_tracking_config',
            ['tracking_config_id'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_progress_entries_session_id',
            'progress_entries',
            'therapy_sessions',
            ['session_id'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_progress_entries_recorded_by',
            'progress_entries',
            'users',
            ['recorded_by'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add check constraint for context values
        op.create_check_constraint(
            'ck_progress_entries_context',
            'progress_entries',
            "context IS NULL OR context IN ('session', 'self_report', 'assessment')"
        )

        # Add composite index for goal_id and entry_date (most common query pattern)
        op.create_index(
            'idx_progress_entries_goal_date',
            'progress_entries',
            ['goal_id', sa.text('entry_date DESC')]
        )

        # Add index on session_id for session-based queries
        op.create_index(
            'idx_progress_entries_session',
            'progress_entries',
            ['session_id']
        )

    # ==========================================================================
    # STEP 3: Create assessment_scores table
    # ==========================================================================

    if 'assessment_scores' not in tables:
        op.create_table(
            'assessment_scores',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('goal_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('assessment_type', sa.String(length=50), nullable=False),
            sa.Column('score', sa.Integer(), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=True),
            sa.Column('subscores', postgresql.JSONB(), nullable=True),
            sa.Column('administered_date', sa.Date(), nullable=False),
            sa.Column('administered_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_assessment_scores_patient_id',
            'assessment_scores',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_assessment_scores_goal_id',
            'assessment_scores',
            'treatment_goals',
            ['goal_id'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_assessment_scores_administered_by',
            'assessment_scores',
            'users',
            ['administered_by'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add check constraint for score (must be non-negative)
        op.create_check_constraint(
            'ck_assessment_scores_score',
            'assessment_scores',
            'score >= 0'
        )

        # Add composite index for patient_id and administered_date
        op.create_index(
            'idx_assessment_scores_patient_date',
            'assessment_scores',
            ['patient_id', sa.text('administered_date DESC')]
        )

        # Add index on assessment_type for filtering by assessment type
        op.create_index(
            'idx_assessment_scores_type',
            'assessment_scores',
            ['assessment_type']
        )

    # ==========================================================================
    # STEP 4: Create progress_milestones table
    # ==========================================================================

    if 'progress_milestones' not in tables:
        op.create_table(
            'progress_milestones',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('goal_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('milestone_type', sa.String(length=50), nullable=True),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('target_value', sa.Numeric(precision=10, scale=2), nullable=True),
            sa.Column('achieved_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        )

        # Add foreign key to treatment_goals
        op.create_foreign_key(
            'fk_progress_milestones_goal_id',
            'progress_milestones',
            'treatment_goals',
            ['goal_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add check constraint for milestone_type
        op.create_check_constraint(
            'ck_progress_milestones_type',
            'progress_milestones',
            "milestone_type IS NULL OR milestone_type IN ('percentage', 'value', 'streak', 'custom')"
        )

        # Add index on goal_id
        op.create_index(
            'idx_progress_milestones_goal',
            'progress_milestones',
            ['goal_id']
        )

        # Add composite index for achieved milestones (partial index)
        op.execute(
            """
            CREATE INDEX idx_progress_milestones_goal_achieved
            ON progress_milestones (goal_id, achieved_at DESC)
            WHERE achieved_at IS NOT NULL
            """
        )

    # ==========================================================================
    # STEP 5: Create goal_reminders table
    # ==========================================================================

    if 'goal_reminders' not in tables:
        op.create_table(
            'goal_reminders',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('goal_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('reminder_type', sa.String(length=20), nullable=True),
            sa.Column('scheduled_time', sa.Time(), nullable=True),
            sa.Column('scheduled_days', sa.JSON(), nullable=True),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('last_sent_at', sa.TIMESTAMP(timezone=True), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_goal_reminders_goal_id',
            'goal_reminders',
            'treatment_goals',
            ['goal_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_goal_reminders_patient_id',
            'goal_reminders',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add check constraint for reminder_type
        op.create_check_constraint(
            'ck_goal_reminders_type',
            'goal_reminders',
            "reminder_type IS NULL OR reminder_type IN ('check_in', 'progress', 'motivation')"
        )

        # Add index on patient_id for patient queries
        op.create_index(
            'idx_goal_reminders_patient',
            'goal_reminders',
            ['patient_id']
        )

        # Add composite index for active reminders by goal
        op.create_index(
            'idx_goal_reminders_goal_active',
            'goal_reminders',
            ['goal_id', 'is_active']
        )


def downgrade() -> None:
    """Reverse the changes."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Drop goal_reminders table if it exists
    if 'goal_reminders' in tables:
        op.drop_index('idx_goal_reminders_goal_active', table_name='goal_reminders')
        op.drop_index('idx_goal_reminders_patient', table_name='goal_reminders')
        op.drop_check_constraint('ck_goal_reminders_type', 'goal_reminders', type_='check')
        op.drop_constraint('fk_goal_reminders_patient_id', 'goal_reminders', type_='foreignkey')
        op.drop_constraint('fk_goal_reminders_goal_id', 'goal_reminders', type_='foreignkey')
        op.drop_table('goal_reminders')

    # Drop progress_milestones table if it exists
    if 'progress_milestones' in tables:
        op.execute('DROP INDEX IF EXISTS idx_progress_milestones_goal_achieved')
        op.drop_index('idx_progress_milestones_goal', table_name='progress_milestones')
        op.drop_check_constraint('ck_progress_milestones_type', 'progress_milestones', type_='check')
        op.drop_constraint('fk_progress_milestones_goal_id', 'progress_milestones', type_='foreignkey')
        op.drop_table('progress_milestones')

    # Drop assessment_scores table if it exists
    if 'assessment_scores' in tables:
        op.drop_index('idx_assessment_scores_type', table_name='assessment_scores')
        op.drop_index('idx_assessment_scores_patient_date', table_name='assessment_scores')
        op.drop_check_constraint('ck_assessment_scores_score', 'assessment_scores', type_='check')
        op.drop_constraint('fk_assessment_scores_administered_by', 'assessment_scores', type_='foreignkey')
        op.drop_constraint('fk_assessment_scores_goal_id', 'assessment_scores', type_='foreignkey')
        op.drop_constraint('fk_assessment_scores_patient_id', 'assessment_scores', type_='foreignkey')
        op.drop_table('assessment_scores')

    # Drop progress_entries table if it exists
    if 'progress_entries' in tables:
        op.drop_index('idx_progress_entries_session', table_name='progress_entries')
        op.drop_index('idx_progress_entries_goal_date', table_name='progress_entries')
        op.drop_check_constraint('ck_progress_entries_context', 'progress_entries', type_='check')
        op.drop_constraint('fk_progress_entries_recorded_by', 'progress_entries', type_='foreignkey')
        op.drop_constraint('fk_progress_entries_session_id', 'progress_entries', type_='foreignkey')
        op.drop_constraint('fk_progress_entries_tracking_config_id', 'progress_entries', type_='foreignkey')
        op.drop_constraint('fk_progress_entries_goal_id', 'progress_entries', type_='foreignkey')
        op.drop_table('progress_entries')

    # Drop goal_tracking_config table if it exists
    if 'goal_tracking_config' in tables:
        op.drop_index('idx_goal_tracking_config_goal', table_name='goal_tracking_config')
        op.drop_check_constraint('ck_goal_tracking_config_direction', 'goal_tracking_config', type_='check')
        op.drop_check_constraint('ck_goal_tracking_config_frequency', 'goal_tracking_config', type_='check')
        op.drop_check_constraint('ck_goal_tracking_config_scale_max', 'goal_tracking_config', type_='check')
        op.drop_check_constraint('ck_goal_tracking_config_scale_min', 'goal_tracking_config', type_='check')
        op.drop_check_constraint('ck_goal_tracking_config_scale_range', 'goal_tracking_config', type_='check')
        op.drop_check_constraint('ck_goal_tracking_config_tracking_method', 'goal_tracking_config', type_='check')
        op.drop_constraint('fk_goal_tracking_config_goal_id', 'goal_tracking_config', type_='foreignkey')
        op.drop_table('goal_tracking_config')
