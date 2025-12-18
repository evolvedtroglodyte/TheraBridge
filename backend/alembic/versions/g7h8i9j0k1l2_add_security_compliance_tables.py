"""Add security and compliance tables for Feature 8 HIPAA Compliance

Revision ID: g7h8i9j0k1l2
Revises: f6g7h8i9j0k1
Create Date: 2025-12-17 18:27:56.000000

This migration adds 8 comprehensive security and compliance tables for Feature 8:
1. audit_logs - Comprehensive activity tracking with partitioning indices
2. security_events - Authentication/authorization events
3. mfa_config - TOTP secrets and backup codes
4. user_sessions - Session management with device tracking
5. access_requests - HIPAA right of access requests
6. emergency_access - Break-the-glass access grants
7. consent_records - Patient consent with signatures
8. encryption_keys - Key rotation management

Note: Implements HIPAA-compliant audit logging, MFA, session management, and consent tracking.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'g7h8i9j0k1l2'
down_revision: Union[str, Sequence[str], None] = 'f6g7h8i9j0k1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add security and compliance tables with defensive checks."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # ==========================================================================
    # STEP 1: Create audit_logs table
    # ==========================================================================

    if 'audit_logs' not in tables:
        op.create_table(
            'audit_logs',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('timestamp', sa.TIMESTAMP(), nullable=False, server_default=sa.text('NOW()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('session_id', sa.String(length=100), nullable=True),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('resource_type', sa.String(length=50), nullable=False),
            sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('request_method', sa.String(length=10), nullable=True),
            sa.Column('request_path', sa.String(length=500), nullable=True),
            sa.Column('request_body_hash', sa.String(length=64), nullable=True),
            sa.Column('response_status', sa.Integer(), nullable=True),
            sa.Column('details', postgresql.JSONB(), nullable=True),
            sa.Column('risk_level', sa.String(length=20), server_default='normal', nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_audit_logs_user_id',
            'audit_logs',
            'users',
            ['user_id'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_audit_logs_patient_id',
            'audit_logs',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add indices for partitioned performance
        op.create_index(
            'idx_audit_logs_timestamp',
            'audit_logs',
            ['timestamp']
        )
        op.create_index(
            'idx_audit_logs_user',
            'audit_logs',
            ['user_id', 'timestamp']
        )
        op.create_index(
            'idx_audit_logs_patient',
            'audit_logs',
            ['patient_id', 'timestamp']
        )
        op.create_index(
            'idx_audit_logs_action',
            'audit_logs',
            ['action']
        )

        # Add check constraint for risk_level
        op.create_check_constraint(
            'ck_audit_logs_risk_level',
            'audit_logs',
            "risk_level IN ('normal', 'elevated', 'high')"
        )

    # ==========================================================================
    # STEP 2: Create security_events table
    # ==========================================================================

    if 'security_events' not in tables:
        op.create_table(
            'security_events',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('event_type', sa.String(length=50), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('success', sa.Boolean(), nullable=False),
            sa.Column('failure_reason', sa.String(length=200), nullable=True),
            sa.Column('metadata', postgresql.JSONB(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        )

        # Add foreign key
        op.create_foreign_key(
            'fk_security_events_user_id',
            'security_events',
            'users',
            ['user_id'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add indices
        op.create_index(
            'idx_security_events_type',
            'security_events',
            ['event_type', 'created_at']
        )
        op.create_index(
            'idx_security_events_user',
            'security_events',
            ['user_id', 'created_at']
        )

    # ==========================================================================
    # STEP 3: Create mfa_config table
    # ==========================================================================

    if 'mfa_config' not in tables:
        op.create_table(
            'mfa_config',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, unique=True),
            sa.Column('mfa_type', sa.String(length=20), nullable=False),
            sa.Column('secret_encrypted', sa.LargeBinary(), nullable=True),
            sa.Column('phone_number', sa.String(length=20), nullable=True),
            sa.Column('backup_codes_hash', postgresql.ARRAY(sa.String(length=255)), nullable=True),
            sa.Column('is_enabled', sa.Boolean(), server_default='false', nullable=True),
            sa.Column('verified_at', sa.TIMESTAMP(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
            sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        )

        # Add foreign key with CASCADE delete
        op.create_foreign_key(
            'fk_mfa_config_user_id',
            'mfa_config',
            'users',
            ['user_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add check constraint for mfa_type
        op.create_check_constraint(
            'ck_mfa_config_mfa_type',
            'mfa_config',
            "mfa_type IN ('totp', 'sms', 'email')"
        )

        # Add index on user_id (though unique constraint already indexes it)
        op.create_index(
            'idx_mfa_config_user_id',
            'mfa_config',
            ['user_id']
        )

    # ==========================================================================
    # STEP 4: Create user_sessions table
    # ==========================================================================

    if 'user_sessions' not in tables:
        op.create_table(
            'user_sessions',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('session_token_hash', sa.String(length=64), nullable=False),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('user_agent', sa.Text(), nullable=True),
            sa.Column('device_info', postgresql.JSONB(), nullable=True),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
            sa.Column('last_activity_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
            sa.Column('expires_at', sa.TIMESTAMP(), nullable=False),
            sa.Column('revoked_at', sa.TIMESTAMP(), nullable=True),
            sa.Column('revoke_reason', sa.String(length=100), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        )

        # Add foreign key with CASCADE delete
        op.create_foreign_key(
            'fk_user_sessions_user_id',
            'user_sessions',
            'users',
            ['user_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add indices
        op.create_index(
            'idx_sessions_user',
            'user_sessions',
            ['user_id', 'is_active']
        )
        # Partial index on active sessions only
        op.execute(
            "CREATE INDEX idx_sessions_expires ON user_sessions(expires_at) WHERE is_active = true"
        )

    # ==========================================================================
    # STEP 5: Create access_requests table
    # ==========================================================================

    if 'access_requests' not in tables:
        op.create_table(
            'access_requests',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('request_type', sa.String(length=50), nullable=False),
            sa.Column('status', sa.String(length=20), server_default='pending', nullable=True),
            sa.Column('requested_data', sa.Text(), nullable=True),
            sa.Column('request_reason', sa.Text(), nullable=True),
            sa.Column('response_notes', sa.Text(), nullable=True),
            sa.Column('processed_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('processed_at', sa.TIMESTAMP(), nullable=True),
            sa.Column('due_date', sa.Date(), nullable=False),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_access_requests_patient_id',
            'access_requests',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_access_requests_processed_by',
            'access_requests',
            'users',
            ['processed_by'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add check constraints
        op.create_check_constraint(
            'ck_access_requests_request_type',
            'access_requests',
            "request_type IN ('access', 'amendment', 'restriction', 'accounting')"
        )
        op.create_check_constraint(
            'ck_access_requests_status',
            'access_requests',
            "status IN ('pending', 'approved', 'denied', 'completed')"
        )

        # Add indices
        op.create_index(
            'idx_access_requests_patient_id',
            'access_requests',
            ['patient_id']
        )
        op.create_index(
            'idx_access_requests_status',
            'access_requests',
            ['status']
        )
        op.create_index(
            'idx_access_requests_due_date',
            'access_requests',
            ['due_date']
        )

    # ==========================================================================
    # STEP 6: Create emergency_access table
    # ==========================================================================

    if 'emergency_access' not in tables:
        op.create_table(
            'emergency_access',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('reason', sa.Text(), nullable=False),
            sa.Column('duration_minutes', sa.Integer(), server_default='60', nullable=True),
            sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('approved_at', sa.TIMESTAMP(), nullable=True),
            sa.Column('expires_at', sa.TIMESTAMP(), nullable=True),
            sa.Column('access_revoked_at', sa.TIMESTAMP(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        )

        # Add foreign keys
        op.create_foreign_key(
            'fk_emergency_access_user_id',
            'emergency_access',
            'users',
            ['user_id'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_emergency_access_patient_id',
            'emergency_access',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='SET NULL'
        )
        op.create_foreign_key(
            'fk_emergency_access_approved_by',
            'emergency_access',
            'users',
            ['approved_by'],
            ['id'],
            ondelete='SET NULL'
        )

        # Add indices
        op.create_index(
            'idx_emergency_access_user_id',
            'emergency_access',
            ['user_id']
        )
        op.create_index(
            'idx_emergency_access_patient_id',
            'emergency_access',
            ['patient_id']
        )
        op.create_index(
            'idx_emergency_access_expires_at',
            'emergency_access',
            ['expires_at']
        )

    # ==========================================================================
    # STEP 7: Create consent_records table
    # ==========================================================================

    if 'consent_records' not in tables:
        op.create_table(
            'consent_records',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('patient_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('consent_type', sa.String(length=50), nullable=False),
            sa.Column('version', sa.String(length=20), nullable=True),
            sa.Column('consented', sa.Boolean(), nullable=False),
            sa.Column('consent_text', sa.Text(), nullable=True),
            sa.Column('signature_data', sa.Text(), nullable=True),
            sa.Column('ip_address', sa.String(length=45), nullable=True),
            sa.Column('consented_at', sa.TIMESTAMP(), nullable=True),
            sa.Column('expires_at', sa.TIMESTAMP(), nullable=True),
            sa.Column('revoked_at', sa.TIMESTAMP(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        )

        # Add foreign key with CASCADE delete
        op.create_foreign_key(
            'fk_consent_records_patient_id',
            'consent_records',
            'users',
            ['patient_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add check constraint for consent_type
        op.create_check_constraint(
            'ck_consent_records_consent_type',
            'consent_records',
            "consent_type IN ('treatment', 'hipaa_notice', 'telehealth', 'recording')"
        )

        # Add indices
        op.create_index(
            'idx_consent_records_patient_id',
            'consent_records',
            ['patient_id']
        )
        op.create_index(
            'idx_consent_records_consent_type',
            'consent_records',
            ['consent_type']
        )
        op.create_index(
            'idx_consent_records_consented_at',
            'consent_records',
            ['consented_at']
        )

    # ==========================================================================
    # STEP 8: Create encryption_keys table
    # ==========================================================================

    if 'encryption_keys' not in tables:
        op.create_table(
            'encryption_keys',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False,
                      server_default=sa.text('gen_random_uuid()')),
            sa.Column('key_type', sa.String(length=50), nullable=False),
            sa.Column('key_version', sa.Integer(), nullable=False),
            sa.Column('key_encrypted', sa.LargeBinary(), nullable=False),
            sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
            sa.Column('activated_at', sa.TIMESTAMP(), nullable=True),
            sa.Column('deactivated_at', sa.TIMESTAMP(), nullable=True),
            sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('NOW()'), nullable=True),
        )

        # Add check constraint for key_type
        op.create_check_constraint(
            'ck_encryption_keys_key_type',
            'encryption_keys',
            "key_type IN ('data', 'field', 'backup')"
        )

        # Add indices
        op.create_index(
            'idx_encryption_keys_key_type',
            'encryption_keys',
            ['key_type']
        )
        op.create_index(
            'idx_encryption_keys_is_active',
            'encryption_keys',
            ['is_active']
        )
        # Composite index for finding active key by type and version
        op.create_index(
            'idx_encryption_keys_type_version_active',
            'encryption_keys',
            ['key_type', 'key_version', 'is_active']
        )


def downgrade() -> None:
    """Reverse the changes."""

    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Drop tables in reverse order to handle foreign key dependencies

    # Drop encryption_keys (no dependencies)
    if 'encryption_keys' in tables:
        op.drop_index('idx_encryption_keys_type_version_active', table_name='encryption_keys')
        op.drop_index('idx_encryption_keys_is_active', table_name='encryption_keys')
        op.drop_index('idx_encryption_keys_key_type', table_name='encryption_keys')
        op.drop_check_constraint('ck_encryption_keys_key_type', 'encryption_keys', type_='check')
        op.drop_table('encryption_keys')

    # Drop consent_records
    if 'consent_records' in tables:
        op.drop_index('idx_consent_records_consented_at', table_name='consent_records')
        op.drop_index('idx_consent_records_consent_type', table_name='consent_records')
        op.drop_index('idx_consent_records_patient_id', table_name='consent_records')
        op.drop_check_constraint('ck_consent_records_consent_type', 'consent_records', type_='check')
        op.drop_constraint('fk_consent_records_patient_id', 'consent_records', type_='foreignkey')
        op.drop_table('consent_records')

    # Drop emergency_access
    if 'emergency_access' in tables:
        op.drop_index('idx_emergency_access_expires_at', table_name='emergency_access')
        op.drop_index('idx_emergency_access_patient_id', table_name='emergency_access')
        op.drop_index('idx_emergency_access_user_id', table_name='emergency_access')
        op.drop_constraint('fk_emergency_access_approved_by', 'emergency_access', type_='foreignkey')
        op.drop_constraint('fk_emergency_access_patient_id', 'emergency_access', type_='foreignkey')
        op.drop_constraint('fk_emergency_access_user_id', 'emergency_access', type_='foreignkey')
        op.drop_table('emergency_access')

    # Drop access_requests
    if 'access_requests' in tables:
        op.drop_index('idx_access_requests_due_date', table_name='access_requests')
        op.drop_index('idx_access_requests_status', table_name='access_requests')
        op.drop_index('idx_access_requests_patient_id', table_name='access_requests')
        op.drop_check_constraint('ck_access_requests_status', 'access_requests', type_='check')
        op.drop_check_constraint('ck_access_requests_request_type', 'access_requests', type_='check')
        op.drop_constraint('fk_access_requests_processed_by', 'access_requests', type_='foreignkey')
        op.drop_constraint('fk_access_requests_patient_id', 'access_requests', type_='foreignkey')
        op.drop_table('access_requests')

    # Drop user_sessions
    if 'user_sessions' in tables:
        op.execute("DROP INDEX IF EXISTS idx_sessions_expires")
        op.drop_index('idx_sessions_user', table_name='user_sessions')
        op.drop_constraint('fk_user_sessions_user_id', 'user_sessions', type_='foreignkey')
        op.drop_table('user_sessions')

    # Drop mfa_config
    if 'mfa_config' in tables:
        op.drop_index('idx_mfa_config_user_id', table_name='mfa_config')
        op.drop_check_constraint('ck_mfa_config_mfa_type', 'mfa_config', type_='check')
        op.drop_constraint('fk_mfa_config_user_id', 'mfa_config', type_='foreignkey')
        op.drop_table('mfa_config')

    # Drop security_events
    if 'security_events' in tables:
        op.drop_index('idx_security_events_user', table_name='security_events')
        op.drop_index('idx_security_events_type', table_name='security_events')
        op.drop_constraint('fk_security_events_user_id', 'security_events', type_='foreignkey')
        op.drop_table('security_events')

    # Drop audit_logs
    if 'audit_logs' in tables:
        op.drop_index('idx_audit_logs_action', table_name='audit_logs')
        op.drop_index('idx_audit_logs_patient', table_name='audit_logs')
        op.drop_index('idx_audit_logs_user', table_name='audit_logs')
        op.drop_index('idx_audit_logs_timestamp', table_name='audit_logs')
        op.drop_check_constraint('ck_audit_logs_risk_level', 'audit_logs', type_='check')
        op.drop_constraint('fk_audit_logs_patient_id', 'audit_logs', type_='foreignkey')
        op.drop_constraint('fk_audit_logs_user_id', 'audit_logs', type_='foreignkey')
        op.drop_table('audit_logs')
