"""Add export tables for Feature 7

Revision ID: e4f5g6h7i8j9
Revises: c3d4e5f6g7h8
Create Date: 2025-12-17 19:00:00.000000

This migration adds the export tables for Feature 7:
1. export_templates - Custom export template configurations
2. export_jobs - Export job tracking and status
3. export_audit_log - Audit trail for PHI export compliance
4. scheduled_reports - Automated recurring report generation
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e4f5g6h7i8j9'
down_revision: Union[str, Sequence[str], None] = 'c3d4e5f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add export tables with defensive checks."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # ==========================================================================
    # STEP 1: Create ENUM types for export tables
    # ==========================================================================

    # Create export_type enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'export_type_enum') THEN
                CREATE TYPE export_type_enum AS ENUM (
                    'session_notes',
                    'progress_report',
                    'treatment_summary',
                    'full_record'
                );
            END IF;
        END$$;
    """)

    # Create export_format enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'export_format_enum') THEN
                CREATE TYPE export_format_enum AS ENUM (
                    'pdf',
                    'docx',
                    'json',
                    'csv'
                );
            END IF;
        END$$;
    """)

    # Create export_status enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'export_status_enum') THEN
                CREATE TYPE export_status_enum AS ENUM (
                    'pending',
                    'processing',
                    'completed',
                    'failed'
                );
            END IF;
        END$$;
    """)

    # Create schedule_type enum
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'schedule_type_enum') THEN
                CREATE TYPE schedule_type_enum AS ENUM (
                    'daily',
                    'weekly',
                    'monthly'
                );
            END IF;
        END$$;
    """)

    # ==========================================================================
    # STEP 2: Create export_templates table
    # ==========================================================================

    if 'export_templates' not in tables:
        op.create_table(
            'export_templates',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('export_type', postgresql.ENUM(
                'session_notes', 'progress_report', 'treatment_summary', 'full_record',
                name='export_type_enum', create_type=False
            ), nullable=False),
            sa.Column('format', postgresql.ENUM(
                'pdf', 'docx', 'json', 'csv',
                name='export_format_enum', create_type=False
            ), nullable=False),
            sa.Column('template_content', sa.Text(), nullable=True),
            sa.Column('include_sections', postgresql.JSONB(), nullable=True),
            sa.Column('is_system', sa.Boolean(), server_default='false', nullable=False),
            sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign key for created_by
        op.create_foreign_key(
            'fk_export_templates_created_by',
            'export_templates',
            'users',
            ['created_by'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add partial unique constraint (unique name per user)
        op.execute("""
            CREATE UNIQUE INDEX uq_export_templates_created_by_name
            ON export_templates (created_by, name)
            WHERE created_by IS NOT NULL
        """)

        # Add index for querying templates
        op.create_index(
            'idx_export_templates_export_type',
            'export_templates',
            ['export_type']
        )

    # ==========================================================================
    # STEP 3: Create export_jobs table
    # ==========================================================================

    if 'export_jobs' not in tables:
        op.create_table(
            'export_jobs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('export_type', sa.String(50), nullable=False),
            sa.Column('format', sa.String(20), nullable=False),
            sa.Column('status', postgresql.ENUM(
                'pending', 'processing', 'completed', 'failed',
                name='export_status_enum', create_type=False
            ), server_default='pending', nullable=False),
            sa.Column('parameters', postgresql.JSONB(), nullable=True),
            sa.Column('file_path', sa.String(500), nullable=True),
            sa.Column('file_size_bytes', sa.BigInteger(), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_export_jobs_user_id',
            'export_jobs',
            'users',
            ['user_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_export_jobs_patient_id',
            'export_jobs',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_export_jobs_template_id',
            'export_jobs',
            'export_templates',
            ['template_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add indexes for common queries
        op.create_index(
            'idx_export_jobs_user_id_created_at',
            'export_jobs',
            ['user_id', sa.text('created_at DESC')]
        )
        op.create_index(
            'idx_export_jobs_status',
            'export_jobs',
            ['status']
        )
        op.create_index(
            'idx_export_jobs_patient_id',
            'export_jobs',
            ['patient_id']
        )
        # Index for cleanup job (find expired exports)
        op.create_index(
            'idx_export_jobs_expires_at',
            'export_jobs',
            ['expires_at']
        )

    # ==========================================================================
    # STEP 4: Create export_audit_log table
    # ==========================================================================

    if 'export_audit_log' not in tables:
        op.create_table(
            'export_audit_log',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('export_job_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('action', sa.String(50), nullable=False),
            sa.Column('ip_address', sa.String(45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('metadata', postgresql.JSONB(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_export_audit_log_export_job_id',
            'export_audit_log',
            'export_jobs',
            ['export_job_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_export_audit_log_user_id',
            'export_audit_log',
            'users',
            ['user_id'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_export_audit_log_patient_id',
            'export_audit_log',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add indexes for audit queries
        op.create_index(
            'idx_export_audit_log_export_job_id',
            'export_audit_log',
            ['export_job_id']
        )
        op.create_index(
            'idx_export_audit_log_user_id_created_at',
            'export_audit_log',
            ['user_id', sa.text('created_at DESC')]
        )
        op.create_index(
            'idx_export_audit_log_patient_id',
            'export_audit_log',
            ['patient_id']
        )
        op.create_index(
            'idx_export_audit_log_action',
            'export_audit_log',
            ['action']
        )

    # ==========================================================================
    # STEP 5: Create scheduled_reports table
    # ==========================================================================

    if 'scheduled_reports' not in tables:
        op.create_table(
            'scheduled_reports',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('schedule_type', postgresql.ENUM(
                'daily', 'weekly', 'monthly',
                name='schedule_type_enum', create_type=False
            ), nullable=False),
            sa.Column('schedule_config', postgresql.JSONB(), nullable=True),
            sa.Column('parameters', postgresql.JSONB(), nullable=True),
            sa.Column('delivery_method', sa.String(20), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
            sa.Column('last_run_at', sa.DateTime(), nullable=True),
            sa.Column('next_run_at', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_scheduled_reports_user_id',
            'scheduled_reports',
            'users',
            ['user_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_scheduled_reports_template_id',
            'scheduled_reports',
            'export_templates',
            ['template_id'],
            ['id'],
            ondelete='CASCADE'
        )
        op.create_foreign_key(
            'fk_scheduled_reports_patient_id',
            'scheduled_reports',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add partial unique constraint (one active scheduled report per user/template/patient combo)
        op.execute("""
            CREATE UNIQUE INDEX uq_scheduled_reports_user_template_patient
            ON scheduled_reports (user_id, template_id, patient_id)
            WHERE is_active = true
        """)

        # Add indexes for scheduled report processing
        op.create_index(
            'idx_scheduled_reports_next_run_at',
            'scheduled_reports',
            ['next_run_at']
        )
        op.create_index(
            'idx_scheduled_reports_user_id',
            'scheduled_reports',
            ['user_id']
        )
        op.create_index(
            'idx_scheduled_reports_is_active',
            'scheduled_reports',
            ['is_active']
        )


def downgrade() -> None:
    """Reverse the changes."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Drop scheduled_reports table if it exists
    if 'scheduled_reports' in tables:
        op.execute("DROP INDEX IF EXISTS uq_scheduled_reports_user_template_patient")
        op.drop_index('idx_scheduled_reports_is_active', table_name='scheduled_reports')
        op.drop_index('idx_scheduled_reports_user_id', table_name='scheduled_reports')
        op.drop_index('idx_scheduled_reports_next_run_at', table_name='scheduled_reports')
        op.drop_constraint('fk_scheduled_reports_patient_id', 'scheduled_reports', type_='foreignkey')
        op.drop_constraint('fk_scheduled_reports_template_id', 'scheduled_reports', type_='foreignkey')
        op.drop_constraint('fk_scheduled_reports_user_id', 'scheduled_reports', type_='foreignkey')
        op.drop_table('scheduled_reports')

    # Drop export_audit_log table if it exists
    if 'export_audit_log' in tables:
        op.drop_index('idx_export_audit_log_action', table_name='export_audit_log')
        op.drop_index('idx_export_audit_log_patient_id', table_name='export_audit_log')
        op.drop_index('idx_export_audit_log_user_id_created_at', table_name='export_audit_log')
        op.drop_index('idx_export_audit_log_export_job_id', table_name='export_audit_log')
        op.drop_constraint('fk_export_audit_log_patient_id', 'export_audit_log', type_='foreignkey')
        op.drop_constraint('fk_export_audit_log_user_id', 'export_audit_log', type_='foreignkey')
        op.drop_constraint('fk_export_audit_log_export_job_id', 'export_audit_log', type_='foreignkey')
        op.drop_table('export_audit_log')

    # Drop export_jobs table if it exists
    if 'export_jobs' in tables:
        op.drop_index('idx_export_jobs_expires_at', table_name='export_jobs')
        op.drop_index('idx_export_jobs_patient_id', table_name='export_jobs')
        op.drop_index('idx_export_jobs_status', table_name='export_jobs')
        op.drop_index('idx_export_jobs_user_id_created_at', table_name='export_jobs')
        op.drop_constraint('fk_export_jobs_template_id', 'export_jobs', type_='foreignkey')
        op.drop_constraint('fk_export_jobs_patient_id', 'export_jobs', type_='foreignkey')
        op.drop_constraint('fk_export_jobs_user_id', 'export_jobs', type_='foreignkey')
        op.drop_table('export_jobs')

    # Drop export_templates table if it exists
    if 'export_templates' in tables:
        op.drop_index('idx_export_templates_export_type', table_name='export_templates')
        op.execute("DROP INDEX IF EXISTS uq_export_templates_created_by_name")
        op.drop_constraint('fk_export_templates_created_by', 'export_templates', type_='foreignkey')
        op.drop_table('export_templates')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS schedule_type_enum")
    op.execute("DROP TYPE IF EXISTS export_status_enum")
    op.execute("DROP TYPE IF EXISTS export_format_enum")
    op.execute("DROP TYPE IF EXISTS export_type_enum")
