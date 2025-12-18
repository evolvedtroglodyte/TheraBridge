"""
SQLAlchemy ORM models for HIPAA security and compliance tables.
Implements comprehensive audit logging, MFA, session management, and access controls.
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean, LargeBinary, JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as SQLUUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class StringArray(TypeDecorator):
    """
    SQLite-compatible ARRAY type that stores strings as JSON.
    On PostgreSQL, uses native ARRAY(String()).
    On SQLite, stores as JSON array of strings.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(String(255)))
        else:
            return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value


class AuditLog(Base):
    """
    Comprehensive audit logging for all system activities.
    Records PHI access, user actions, and security events for HIPAA compliance.
    Partitioned by month for performance on large datasets.
    """
    __tablename__ = "audit_logs"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    user_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(String(100), nullable=True)
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(SQLUUID(as_uuid=True), nullable=True)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)
    request_path = Column(String(500), nullable=True)
    request_body_hash = Column(String(64), nullable=True)  # SHA-256 hash
    response_status = Column(Integer, nullable=True)
    details = Column(JSONB, nullable=True)
    risk_level = Column(String(20), default='normal', nullable=False)  # 'normal', 'elevated', 'high'
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="audit_logs")
    patient = relationship("User", foreign_keys=[patient_id], backref="phi_access_logs")


class SecurityEvent(Base):
    """
    Security events tracking authentication and authorization activities.
    Records login attempts, MFA validation, session creation, and security violations.
    """
    __tablename__ = "security_events"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)  # 'login', 'logout', 'mfa_verify', 'password_change', etc.
    user_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    email = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(200), nullable=True)
    event_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="security_events")


class MFAConfig(Base):
    """
    Multi-factor authentication configuration for users.
    Supports TOTP (Google Authenticator), SMS, and email-based MFA.
    Stores encrypted secrets and backup codes for account recovery.
    """
    __tablename__ = "mfa_config"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    mfa_type = Column(String(20), nullable=False)  # 'totp', 'sms', 'email'
    secret_encrypted = Column(LargeBinary, nullable=True)  # Encrypted TOTP secret
    phone_number = Column(String(20), nullable=True)
    backup_codes_hash = Column(StringArray, nullable=True)  # Array of hashed backup codes
    is_enabled = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="mfa_config", uselist=False)


class UserSession(Base):
    """
    Active user sessions with automatic timeout and device tracking.
    Enforces session limits, idle timeout, and supports multi-device management.
    Users can view and revoke sessions for security.
    """
    __tablename__ = "user_sessions"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token_hash = Column(String(64), nullable=False, unique=True)  # SHA-256 hash of session token
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_info = Column(JSONB, nullable=True)  # Parsed device/browser information
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_activity_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    revoked_at = Column(DateTime, nullable=True)
    revoke_reason = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="sessions")


class AccessRequest(Base):
    """
    Patient access requests for PHI under HIPAA right of access.
    Tracks requests for record access, amendments, restrictions, and accounting of disclosures.
    Must be processed within 30 days per HIPAA requirements.
    """
    __tablename__ = "access_requests"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    request_type = Column(String(50), nullable=False)  # 'access', 'amendment', 'restriction', 'accounting'
    status = Column(String(20), default='pending', nullable=False)  # 'pending', 'approved', 'denied', 'completed'
    requested_data = Column(Text, nullable=True)
    request_reason = Column(Text, nullable=True)
    response_notes = Column(Text, nullable=True)
    processed_by = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    processed_at = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=False)  # 30 days from request per HIPAA
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="access_requests")
    processor = relationship("User", foreign_keys=[processed_by], backref="processed_access_requests")


class EmergencyAccess(Base):
    """
    Break-the-glass emergency access for urgent situations.
    Grants temporary elevated access to patient records with full audit trail.
    Requires justification and can be approved by authorized personnel.
    """
    __tablename__ = "emergency_access"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    duration_minutes = Column(Integer, default=60, nullable=False)
    approved_by = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    access_revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="emergency_access_requests")
    patient = relationship("User", foreign_keys=[patient_id], backref="emergency_access_grants")
    approver = relationship("User", foreign_keys=[approved_by], backref="emergency_access_approvals")


class ConsentRecord(Base):
    """
    Patient consent records for treatment, HIPAA notices, and data sharing.
    Tracks consent versions, signatures, and expiration dates.
    Supports consent revocation with audit trail.
    """
    __tablename__ = "consent_records"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    consent_type = Column(String(50), nullable=False)  # 'treatment', 'hipaa_notice', 'telehealth', 'recording'
    version = Column(String(20), nullable=True)
    consented = Column(Boolean, nullable=False)
    consent_text = Column(Text, nullable=True)
    signature_data = Column(Text, nullable=True)  # Base64 encoded signature image
    ip_address = Column(String(45), nullable=True)
    consented_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], backref="consent_records")


class EncryptionKey(Base):
    """
    Encryption key management for data encryption and key rotation.
    Stores encrypted keys with versioning for field-level encryption.
    Supports key activation, deactivation, and rotation workflows.
    """
    __tablename__ = "encryption_keys"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key_type = Column(String(50), nullable=False)  # 'data', 'field', 'backup'
    key_version = Column(Integer, nullable=False)
    key_encrypted = Column(LargeBinary, nullable=False)  # Encrypted with master key
    is_active = Column(Boolean, default=True, nullable=False)
    activated_at = Column(DateTime, nullable=True)
    deactivated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
