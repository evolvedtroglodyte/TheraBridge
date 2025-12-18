"""add_treatment_plan_tables

Revision ID: 4da5acd78939
Revises: f6g7h8i9j0k1
Create Date: 2025-12-17 18:25:20.577884

This migration adds the treatment plan tables for Feature 4:
1. treatment_plans - Core treatment plan data
2. treatment_goals - SMART goals with hierarchy support
3. interventions - Evidence-based intervention library
4. goal_interventions - Many-to-many mapping between goals and interventions
5. goal_progress - Progress tracking entries
6. plan_reviews - Periodic plan reviews
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '4da5acd78939'
down_revision: Union[str, Sequence[str], None] = 'f6g7h8i9j0k1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add treatment plan tables with defensive checks."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # ==========================================================================
    # STEP 1: Create treatment_plans table
    # ==========================================================================

    if 'treatment_plans' not in tables:
        op.create_table(
            'treatment_plans',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('therapist_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('diagnosis_codes', postgresql.JSONB(), nullable=True),
            sa.Column('presenting_problems', postgresql.ARRAY(sa.Text()), nullable=True),
            sa.Column('start_date', sa.Date(), nullable=False),
            sa.Column('target_end_date', sa.Date(), nullable=True),
            sa.Column('actual_end_date', sa.Date(), nullable=True),
            sa.Column('status', sa.String(20), server_default='active', nullable=False),
            sa.Column('review_frequency_days', sa.Integer(), server_default='90', nullable=False),
            sa.Column('next_review_date', sa.Date(), nullable=True),
            sa.Column('version', sa.Integer(), server_default='1', nullable=False),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_treatment_plans_patient_id',
            'treatment_plans',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_treatment_plans_therapist_id',
            'treatment_plans',
            'users',
            ['therapist_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add indexes for performance
        op.create_index(
            'idx_treatment_plans_patient_created',
            'treatment_plans',
            ['patient_id', sa.text('created_at DESC')]
        )
        op.create_index(
            'idx_treatment_plans_therapist',
            'treatment_plans',
            ['therapist_id']
        )
        op.create_index(
            'idx_treatment_plans_status',
            'treatment_plans',
            ['status']
        )

    # ==========================================================================
    # STEP 2: Create treatment_goals table
    # ==========================================================================

    if 'treatment_goals' not in tables:
        op.create_table(
            'treatment_goals',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('parent_goal_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('goal_type', sa.String(20), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.Column('measurable_criteria', sa.Text(), nullable=True),
            sa.Column('baseline_value', sa.String(100), nullable=True),
            sa.Column('target_value', sa.String(100), nullable=True),
            sa.Column('current_value', sa.String(100), nullable=True),
            sa.Column('target_date', sa.Date(), nullable=True),
            sa.Column('status', sa.String(20), server_default='not_started', nullable=False),
            sa.Column('progress_percentage', sa.Integer(), server_default='0', nullable=False),
            sa.Column('priority', sa.Integer(), server_default='1', nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_treatment_goals_plan_id',
            'treatment_goals',
            'treatment_plans',
            ['plan_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_treatment_goals_parent_goal_id',
            'treatment_goals',
            'treatment_goals',
            ['parent_goal_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add check constraint for progress percentage
        op.create_check_constraint(
            'ck_treatment_goals_progress_range',
            'treatment_goals',
            'progress_percentage >= 0 AND progress_percentage <= 100'
        )

        # Add indexes for performance
        op.create_index(
            'idx_treatment_goals_plan_id',
            'treatment_goals',
            ['plan_id']
        )
        op.create_index(
            'idx_treatment_goals_parent_goal_id',
            'treatment_goals',
            ['parent_goal_id']
        )
        op.create_index(
            'idx_treatment_goals_status',
            'treatment_goals',
            ['status']
        )

    # ==========================================================================
    # STEP 3: Create interventions table
    # ==========================================================================

    if 'interventions' not in tables:
        op.create_table(
            'interventions',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('name', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('modality', sa.String(50), nullable=True),
            sa.Column('evidence_level', sa.String(20), nullable=True),
            sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign key
        op.create_foreign_key(
            'fk_interventions_created_by',
            'interventions',
            'users',
            ['created_by'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add indexes for performance
        op.create_index(
            'idx_interventions_modality',
            'interventions',
            ['modality']
        )
        op.create_index(
            'idx_interventions_is_system',
            'interventions',
            ['is_system']
        )
        op.create_index(
            'idx_interventions_created_by',
            'interventions',
            ['created_by']
        )

    # ==========================================================================
    # STEP 4: Create goal_interventions table
    # ==========================================================================

    if 'goal_interventions' not in tables:
        op.create_table(
            'goal_interventions',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('goal_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('intervention_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('frequency', sa.String(50), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('effectiveness_rating', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_goal_interventions_goal_id',
            'goal_interventions',
            'treatment_goals',
            ['goal_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_goal_interventions_intervention_id',
            'goal_interventions',
            'interventions',
            ['intervention_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add check constraint for effectiveness rating
        op.create_check_constraint(
            'ck_goal_interventions_effectiveness_range',
            'goal_interventions',
            'effectiveness_rating IS NULL OR (effectiveness_rating >= 1 AND effectiveness_rating <= 5)'
        )

        # Add unique constraint (one mapping per goal-intervention pair)
        op.create_unique_constraint(
            'uq_goal_interventions_goal_intervention',
            'goal_interventions',
            ['goal_id', 'intervention_id']
        )

        # Add indexes for performance
        op.create_index(
            'idx_goal_interventions_goal_id',
            'goal_interventions',
            ['goal_id']
        )
        op.create_index(
            'idx_goal_interventions_intervention_id',
            'goal_interventions',
            ['intervention_id']
        )

    # ==========================================================================
    # STEP 5: Create goal_progress table
    # ==========================================================================

    if 'goal_progress' not in tables:
        op.create_table(
            'goal_progress',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('goal_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('progress_note', sa.Text(), nullable=False),
            sa.Column('progress_value', sa.String(100), nullable=True),
            sa.Column('rating', sa.Integer(), nullable=True),
            sa.Column('recorded_by', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('recorded_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_goal_progress_goal_id',
            'goal_progress',
            'treatment_goals',
            ['goal_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_goal_progress_session_id',
            'goal_progress',
            'therapy_sessions',
            ['session_id'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_goal_progress_recorded_by',
            'goal_progress',
            'users',
            ['recorded_by'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add check constraint for rating
        op.create_check_constraint(
            'ck_goal_progress_rating_range',
            'goal_progress',
            'rating IS NULL OR (rating >= 1 AND rating <= 10)'
        )

        # Add indexes for performance
        op.create_index(
            'idx_goal_progress_goal_recorded',
            'goal_progress',
            ['goal_id', sa.text('recorded_at DESC')]
        )
        op.create_index(
            'idx_goal_progress_session_id',
            'goal_progress',
            ['session_id']
        )

    # ==========================================================================
    # STEP 6: Create plan_reviews table
    # ==========================================================================

    if 'plan_reviews' not in tables:
        op.create_table(
            'plan_reviews',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('plan_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('review_date', sa.Date(), nullable=False),
            sa.Column('reviewer_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('summary', sa.Text(), nullable=False),
            sa.Column('goals_reviewed', sa.Integer(), nullable=True),
            sa.Column('goals_on_track', sa.Integer(), nullable=True),
            sa.Column('modifications_made', sa.Text(), nullable=True),
            sa.Column('next_review_date', sa.Date(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_plan_reviews_plan_id',
            'plan_reviews',
            'treatment_plans',
            ['plan_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_plan_reviews_reviewer_id',
            'plan_reviews',
            'users',
            ['reviewer_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add indexes for performance
        op.create_index(
            'idx_plan_reviews_plan_date',
            'plan_reviews',
            ['plan_id', sa.text('review_date DESC')]
        )
        op.create_index(
            'idx_plan_reviews_reviewer_id',
            'plan_reviews',
            ['reviewer_id']
        )


def downgrade() -> None:
    """Reverse the changes."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Drop tables in reverse order (handle FK dependencies)

    # Step 6: Drop plan_reviews table
    if 'plan_reviews' in tables:
        op.drop_index('idx_plan_reviews_reviewer_id', table_name='plan_reviews')
        op.drop_index('idx_plan_reviews_plan_date', table_name='plan_reviews')
        op.drop_constraint('fk_plan_reviews_reviewer_id', 'plan_reviews', type_='foreignkey')
        op.drop_constraint('fk_plan_reviews_plan_id', 'plan_reviews', type_='foreignkey')
        op.drop_table('plan_reviews')

    # Step 5: Drop goal_progress table
    if 'goal_progress' in tables:
        op.drop_index('idx_goal_progress_session_id', table_name='goal_progress')
        op.drop_index('idx_goal_progress_goal_recorded', table_name='goal_progress')
        op.drop_check_constraint('ck_goal_progress_rating_range', 'goal_progress')
        op.drop_constraint('fk_goal_progress_recorded_by', 'goal_progress', type_='foreignkey')
        op.drop_constraint('fk_goal_progress_session_id', 'goal_progress', type_='foreignkey')
        op.drop_constraint('fk_goal_progress_goal_id', 'goal_progress', type_='foreignkey')
        op.drop_table('goal_progress')

    # Step 4: Drop goal_interventions table
    if 'goal_interventions' in tables:
        op.drop_index('idx_goal_interventions_intervention_id', table_name='goal_interventions')
        op.drop_index('idx_goal_interventions_goal_id', table_name='goal_interventions')
        op.drop_constraint('uq_goal_interventions_goal_intervention', 'goal_interventions', type_='unique')
        op.drop_check_constraint('ck_goal_interventions_effectiveness_range', 'goal_interventions')
        op.drop_constraint('fk_goal_interventions_intervention_id', 'goal_interventions', type_='foreignkey')
        op.drop_constraint('fk_goal_interventions_goal_id', 'goal_interventions', type_='foreignkey')
        op.drop_table('goal_interventions')

    # Step 3: Drop interventions table
    if 'interventions' in tables:
        op.drop_index('idx_interventions_created_by', table_name='interventions')
        op.drop_index('idx_interventions_is_system', table_name='interventions')
        op.drop_index('idx_interventions_modality', table_name='interventions')
        op.drop_constraint('fk_interventions_created_by', 'interventions', type_='foreignkey')
        op.drop_table('interventions')

    # Step 2: Drop treatment_goals table
    if 'treatment_goals' in tables:
        op.drop_index('idx_treatment_goals_status', table_name='treatment_goals')
        op.drop_index('idx_treatment_goals_parent_goal_id', table_name='treatment_goals')
        op.drop_index('idx_treatment_goals_plan_id', table_name='treatment_goals')
        op.drop_check_constraint('ck_treatment_goals_progress_range', 'treatment_goals')
        op.drop_constraint('fk_treatment_goals_parent_goal_id', 'treatment_goals', type_='foreignkey')
        op.drop_constraint('fk_treatment_goals_plan_id', 'treatment_goals', type_='foreignkey')
        op.drop_table('treatment_goals')

    # Step 1: Drop treatment_plans table
    if 'treatment_plans' in tables:
        op.drop_index('idx_treatment_plans_status', table_name='treatment_plans')
        op.drop_index('idx_treatment_plans_therapist', table_name='treatment_plans')
        op.drop_index('idx_treatment_plans_patient_created', table_name='treatment_plans')
        op.drop_constraint('fk_treatment_plans_therapist_id', 'treatment_plans', type_='foreignkey')
        op.drop_constraint('fk_treatment_plans_patient_id', 'treatment_plans', type_='foreignkey')
        op.drop_table('treatment_plans')
