"""Fix auth table naming and add missing tables for Feature 1 completion

Revision ID: a1b2c3d4e5f6
Revises: 42ef48f739a4
Create Date: 2025-12-17 14:00:00.000000

This migration fixes:
1. Table naming conflict: renames 'sessions' (auth) to 'auth_sessions'
2. Creates proper 'therapy_sessions' table for therapy session data
3. Adds missing columns to 'users': first_name, last_name, is_verified
4. Creates 'therapist_patients' junction table for many-to-many relationships
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '42ef48f739a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix authentication schema and add missing tables.

    1. Rename 'sessions' table to 'auth_sessions' (for refresh tokens)
    2. Create 'therapy_sessions' table (for therapy session data)
    3. Add missing columns to 'users' table
    4. Create 'therapist_patients' junction table
    """

    # ==========================================================================
    # STEP 1: Rename 'sessions' to 'auth_sessions' (fixes table naming conflict)
    # ==========================================================================

    # Drop existing constraints first
    op.drop_constraint('uq_sessions_refresh_token', 'sessions', type_='unique')
    op.drop_constraint('fk_sessions_user_id', 'sessions', type_='foreignkey')

    # Rename the table
    op.rename_table('sessions', 'auth_sessions')

    # Recreate constraints with new table name
    op.create_unique_constraint(
        'uq_auth_sessions_refresh_token',
        'auth_sessions',
        ['refresh_token']
    )
    op.create_foreign_key(
        'fk_auth_sessions_user_id',
        'auth_sessions',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Add index on user_id for faster lookups
    op.create_index('ix_auth_sessions_user_id', 'auth_sessions', ['user_id'])

    # ==========================================================================
    # STEP 2: Create 'therapy_sessions' table (for therapy session data)
    # ==========================================================================

    op.create_table(
        'therapy_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('therapist_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('session_date', sa.DateTime(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('audio_filename', sa.String(255), nullable=True),
        sa.Column('audio_url', sa.Text(), nullable=True),
        sa.Column('transcript_text', sa.Text(), nullable=True),
        sa.Column('transcript_segments', postgresql.JSONB(), nullable=True),
        sa.Column('extracted_notes', postgresql.JSONB(), nullable=True),
        sa.Column('therapist_summary', sa.Text(), nullable=True),
        sa.Column('patient_summary', sa.Text(), nullable=True),
        sa.Column('risk_flags', postgresql.JSONB(), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending', nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
    )

    # Add foreign keys for therapy_sessions
    op.create_foreign_key(
        'fk_therapy_sessions_patient_id',
        'therapy_sessions',
        'patients',
        ['patient_id'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_therapy_sessions_therapist_id',
        'therapy_sessions',
        'users',
        ['therapist_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add indexes for therapy_sessions
    op.create_index('ix_therapy_sessions_patient_id', 'therapy_sessions', ['patient_id'])
    op.create_index('ix_therapy_sessions_therapist_id', 'therapy_sessions', ['therapist_id'])
    op.create_index('ix_therapy_sessions_status', 'therapy_sessions', ['status'])
    op.create_index(
        'ix_therapy_sessions_patient_date',
        'therapy_sessions',
        ['patient_id', sa.text('session_date DESC')]
    )

    # ==========================================================================
    # STEP 3: Add missing columns to 'users' table
    # ==========================================================================

    # Add first_name column (split from full_name)
    op.add_column('users', sa.Column('first_name', sa.String(100), nullable=True))

    # Add last_name column (split from full_name)
    op.add_column('users', sa.Column('last_name', sa.String(100), nullable=True))

    # Add is_verified column for email verification
    op.add_column('users', sa.Column(
        'is_verified',
        sa.Boolean(),
        server_default='false',
        nullable=False
    ))

    # Populate first_name and last_name from full_name
    # This is a data migration - split full_name on first space
    op.execute("""
        UPDATE users
        SET first_name = SPLIT_PART(full_name, ' ', 1),
            last_name = CASE
                WHEN POSITION(' ' IN full_name) > 0
                THEN SUBSTRING(full_name FROM POSITION(' ' IN full_name) + 1)
                ELSE ''
            END
        WHERE first_name IS NULL
    """)

    # ==========================================================================
    # STEP 4: Create 'therapist_patients' junction table
    # ==========================================================================

    op.create_table(
        'therapist_patients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('therapist_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(50), server_default='primary', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    )

    # Add foreign keys for therapist_patients
    op.create_foreign_key(
        'fk_therapist_patients_therapist_id',
        'therapist_patients',
        'users',
        ['therapist_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_therapist_patients_patient_id',
        'therapist_patients',
        'users',
        ['patient_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Add unique constraint (one relationship per therapist-patient pair)
    op.create_unique_constraint(
        'uq_therapist_patients_therapist_patient',
        'therapist_patients',
        ['therapist_id', 'patient_id']
    )

    # Add indexes
    op.create_index('ix_therapist_patients_therapist_id', 'therapist_patients', ['therapist_id'])
    op.create_index('ix_therapist_patients_patient_id', 'therapist_patients', ['patient_id'])


def downgrade() -> None:
    """
    Reverse all changes made in upgrade.
    """

    # Drop therapist_patients table
    op.drop_index('ix_therapist_patients_patient_id', table_name='therapist_patients')
    op.drop_index('ix_therapist_patients_therapist_id', table_name='therapist_patients')
    op.drop_constraint('uq_therapist_patients_therapist_patient', 'therapist_patients', type_='unique')
    op.drop_constraint('fk_therapist_patients_patient_id', 'therapist_patients', type_='foreignkey')
    op.drop_constraint('fk_therapist_patients_therapist_id', 'therapist_patients', type_='foreignkey')
    op.drop_table('therapist_patients')

    # Remove added columns from users
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'first_name')

    # Drop therapy_sessions table
    op.drop_index('ix_therapy_sessions_patient_date', table_name='therapy_sessions')
    op.drop_index('ix_therapy_sessions_status', table_name='therapy_sessions')
    op.drop_index('ix_therapy_sessions_therapist_id', table_name='therapy_sessions')
    op.drop_index('ix_therapy_sessions_patient_id', table_name='therapy_sessions')
    op.drop_constraint('fk_therapy_sessions_therapist_id', 'therapy_sessions', type_='foreignkey')
    op.drop_constraint('fk_therapy_sessions_patient_id', 'therapy_sessions', type_='foreignkey')
    op.drop_table('therapy_sessions')

    # Rename auth_sessions back to sessions
    op.drop_index('ix_auth_sessions_user_id', table_name='auth_sessions')
    op.drop_constraint('fk_auth_sessions_user_id', 'auth_sessions', type_='foreignkey')
    op.drop_constraint('uq_auth_sessions_refresh_token', 'auth_sessions', type_='unique')
    op.rename_table('auth_sessions', 'sessions')
    op.create_unique_constraint('uq_sessions_refresh_token', 'sessions', ['refresh_token'])
    op.create_foreign_key(
        'fk_sessions_user_id',
        'sessions',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )
