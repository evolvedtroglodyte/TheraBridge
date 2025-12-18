"""Fix Feature 4 table naming conflict

Revision ID: 637a7e420a77
Revises: 4da5acd78939
Create Date: 2025-12-18 05:29:12.936688

This migration fixes the table naming conflict in Feature 4:
- The migration 4da5acd78939 incorrectly created 'treatment_goals' table
- The model TreatmentPlanGoal expects 'treatment_plan_goals' table
- This causes conflict with Feature 6's legitimate 'treatment_goals' table
- Foreign keys in goal_interventions and goal_progress point to wrong table

Solution:
1. Rename 'treatment_goals' (from Feature 4 migration) to 'treatment_plan_goals'
2. Update foreign keys in goal_interventions and goal_progress to reference correct table
3. This preserves Feature 6's treatment_goals table which has different schema

IMPORTANT: This assumes Feature 6's migration (d5e6f7g8h9i0) has NOT been applied yet.
If it has been applied, manual intervention is needed to separate the two tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '637a7e420a77'
down_revision: Union[str, Sequence[str], None] = '4da5acd78939'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix Feature 4 table and FK naming."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Check current state
    has_treatment_goals = 'treatment_goals' in tables
    has_treatment_plan_goals = 'treatment_plan_goals' in tables

    # CASE 1: treatment_plan_goals already exists (manual fix was applied)
    # Just need to update foreign keys to point to correct table
    if has_treatment_plan_goals and has_treatment_goals:
        print("INFO: Both tables exist - updating foreign keys only")

        # Fix goal_interventions FK
        op.drop_constraint('fk_goal_interventions_goal_id', 'goal_interventions', type_='foreignkey')
        op.create_foreign_key(
            'fk_goal_interventions_goal_id',
            'goal_interventions',
            'treatment_plan_goals',  # Changed from treatment_goals
            ['goal_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Fix goal_progress FK
        op.drop_constraint('fk_goal_progress_goal_id', 'goal_progress', type_='foreignkey')
        op.create_foreign_key(
            'fk_goal_progress_goal_id',
            'goal_progress',
            'treatment_plan_goals',  # Changed from treatment_goals
            ['goal_id'],
            ['id'],
            ondelete='CASCADE'
        )

    # CASE 2: Only treatment_goals exists (clean state, no Feature 6 applied yet)
    # Rename the table
    elif has_treatment_goals and not has_treatment_plan_goals:
        print("INFO: Renaming treatment_goals to treatment_plan_goals")
        op.rename_table('treatment_goals', 'treatment_plan_goals')

        # Update FK names to match new table name
        op.drop_constraint('fk_treatment_goals_plan_id', 'treatment_plan_goals', type_='foreignkey')
        op.create_foreign_key(
            'fk_treatment_plan_goals_plan_id',
            'treatment_plan_goals',
            'treatment_plans',
            ['plan_id'],
            ['id'],
            ondelete='CASCADE'
        )

        op.drop_constraint('fk_treatment_goals_parent_goal_id', 'treatment_plan_goals', type_='foreignkey')
        op.create_foreign_key(
            'fk_treatment_plan_goals_parent_goal_id',
            'treatment_plan_goals',
            'treatment_plan_goals',
            ['parent_goal_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Update index names
        op.drop_index('idx_treatment_goals_plan_id', table_name='treatment_plan_goals')
        op.create_index('idx_treatment_plan_goals_plan_id', 'treatment_plan_goals', ['plan_id'])

        op.drop_index('idx_treatment_goals_parent_goal_id', table_name='treatment_plan_goals')
        op.create_index('idx_treatment_plan_goals_parent_goal_id', 'treatment_plan_goals', ['parent_goal_id'])

        op.drop_index('idx_treatment_goals_status', table_name='treatment_plan_goals')
        op.create_index('idx_treatment_plan_goals_status', 'treatment_plan_goals', ['status'])

        # Update check constraint
        op.drop_check_constraint('ck_treatment_goals_progress_range', 'treatment_plan_goals')
        op.create_check_constraint(
            'ck_treatment_plan_goals_progress_range',
            'treatment_plan_goals',
            'progress_percentage >= 0 AND progress_percentage <= 100'
        )

    # CASE 3: Something unexpected
    else:
        print(f"WARNING: Unexpected state - treatment_goals={has_treatment_goals}, treatment_plan_goals={has_treatment_plan_goals}")


def downgrade() -> None:
    """Reverse the fix."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    has_treatment_goals = 'treatment_goals' in tables
    has_treatment_plan_goals = 'treatment_plan_goals' in tables

    # If both exist, just revert FKs
    if has_treatment_plan_goals and has_treatment_goals:
        # Revert goal_interventions FK
        op.drop_constraint('fk_goal_interventions_goal_id', 'goal_interventions', type_='foreignkey')
        op.create_foreign_key(
            'fk_goal_interventions_goal_id',
            'goal_interventions',
            'treatment_goals',  # Back to original (wrong) reference
            ['goal_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Revert goal_progress FK
        op.drop_constraint('fk_goal_progress_goal_id', 'goal_progress', type_='foreignkey')
        op.create_foreign_key(
            'fk_goal_progress_goal_id',
            'goal_progress',
            'treatment_goals',  # Back to original (wrong) reference
            ['goal_id'],
            ['id'],
            ondelete='CASCADE'
        )

    # If only treatment_plan_goals exists, rename back
    elif has_treatment_plan_goals and not has_treatment_goals:
        # Update check constraint first
        op.drop_check_constraint('ck_treatment_plan_goals_progress_range', 'treatment_plan_goals')
        op.create_check_constraint(
            'ck_treatment_goals_progress_range',
            'treatment_plan_goals',
            'progress_percentage >= 0 AND progress_percentage <= 100'
        )

        # Update indexes
        op.drop_index('idx_treatment_plan_goals_status', table_name='treatment_plan_goals')
        op.create_index('idx_treatment_goals_status', 'treatment_plan_goals', ['status'])

        op.drop_index('idx_treatment_plan_goals_parent_goal_id', table_name='treatment_plan_goals')
        op.create_index('idx_treatment_goals_parent_goal_id', 'treatment_plan_goals', ['parent_goal_id'])

        op.drop_index('idx_treatment_plan_goals_plan_id', table_name='treatment_plan_goals')
        op.create_index('idx_treatment_goals_plan_id', 'treatment_plan_goals', ['plan_id'])

        # Update FK names
        op.drop_constraint('fk_treatment_plan_goals_parent_goal_id', 'treatment_plan_goals', type_='foreignkey')
        op.create_foreign_key(
            'fk_treatment_goals_parent_goal_id',
            'treatment_plan_goals',
            'treatment_plan_goals',  # Still self-referencing
            ['parent_goal_id'],
            ['id'],
            ondelete='SET NULL'
        )

        op.drop_constraint('fk_treatment_plan_goals_plan_id', 'treatment_plan_goals', type_='foreignkey')
        op.create_foreign_key(
            'fk_treatment_goals_plan_id',
            'treatment_plan_goals',
            'treatment_plans',
            ['plan_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Rename table back
        op.rename_table('treatment_plan_goals', 'treatment_goals')
