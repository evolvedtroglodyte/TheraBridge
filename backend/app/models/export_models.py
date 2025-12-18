"""
SQLAlchemy ORM models for export and reporting tables
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, BigInteger, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as SQLUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import text
from datetime import datetime
from app.database import Base


class ExportTemplate(Base):
    """
    Export template configurations.
    Defines reusable templates for PDF/DOCX/JSON exports with customizable sections.
    Supports both system templates (SOAP, progress reports) and user-created custom templates.
    """
    __tablename__ = 'export_templates'

    id = Column(SQLUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    export_type = Column(String(50), nullable=False)  # 'session_notes', 'progress_report', 'treatment_summary', 'full_record'
    format = Column(String(20), nullable=False)  # 'pdf', 'docx', 'json', 'csv'
    template_content = Column(Text, nullable=True)  # Jinja2 template HTML (for custom templates)
    include_sections = Column(JSONB, nullable=True)  # Configurable sections to include: {transcript: true, goals: false}
    is_system = Column(Boolean, default=False, nullable=False)  # True for built-in templates
    created_by = Column(SQLUUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    created_at = Column(DateTime, server_default=text('now()'), nullable=False)
    updated_at = Column(DateTime, server_default=text('now()'), nullable=False, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by], back_populates="export_templates")
    jobs = relationship("ExportJob", back_populates="template", cascade="all, delete-orphan")


class ExportJob(Base):
    """
    Export job tracking and status.
    Tracks background export generation with status, file paths, and expiration.
    Supports audit logging for HIPAA compliance.
    """
    __tablename__ = 'export_jobs'

    id = Column(SQLUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = Column(SQLUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    template_id = Column(SQLUUID(as_uuid=True), ForeignKey('export_templates.id', ondelete='SET NULL'), nullable=True, index=True)
    export_type = Column(String(50), nullable=False)  # 'session_notes', 'progress_report', 'treatment_summary', 'full_record'
    format = Column(String(20), nullable=False)  # 'pdf', 'docx', 'json', 'csv'
    status = Column(String(20), default='pending', nullable=False)  # 'pending', 'processing', 'completed', 'failed'
    parameters = Column(JSONB, nullable=True)  # Export options, filters, date ranges: {include_transcript: true, start_date: "2025-01-01"}
    file_path = Column(String(500), nullable=True)  # Path to generated export file
    file_size_bytes = Column(BigInteger, nullable=True)  # Size of generated file
    error_message = Column(Text, nullable=True)  # Error details if status='failed'
    started_at = Column(DateTime, nullable=True)  # When processing began
    completed_at = Column(DateTime, nullable=True)  # When processing completed
    expires_at = Column(DateTime, nullable=True)  # Auto-delete file after this timestamp
    created_at = Column(DateTime, server_default=text('now()'), nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="export_jobs")
    patient = relationship("User", foreign_keys=[patient_id])
    template = relationship("ExportTemplate", back_populates="jobs")
    audit_logs = relationship("ExportAuditLog", back_populates="export_job", cascade="all, delete-orphan")


class ExportAuditLog(Base):
    """
    Audit trail for PHI export compliance.
    Records all actions on export files (created, downloaded, deleted, shared) with IP and user agent.
    Required for HIPAA compliance and security monitoring.
    """
    __tablename__ = 'export_audit_log'

    id = Column(SQLUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    export_job_id = Column(SQLUUID(as_uuid=True), ForeignKey('export_jobs.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = Column(SQLUUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = Column(String(50), nullable=False)  # 'created', 'downloaded', 'deleted', 'shared', 'failed'
    ip_address = Column(String(45), nullable=True)  # IPv4 (15 chars) or IPv6 (45 chars)
    user_agent = Column(Text, nullable=True)  # Browser/client user agent string
    action_metadata = Column(JSONB, nullable=True)  # Additional context: {error_code: 500, bytes_downloaded: 10240}
    created_at = Column(DateTime, server_default=text('now()'), nullable=False)

    # Relationships
    export_job = relationship("ExportJob", back_populates="audit_logs")


class ScheduledReport(Base):
    """
    Automated recurring report generation.
    Supports daily, weekly, monthly schedules with configurable delivery methods.
    Generates ExportJob records automatically based on schedule configuration.
    """
    __tablename__ = 'scheduled_reports'

    id = Column(SQLUUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = Column(SQLUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    template_id = Column(SQLUUID(as_uuid=True), ForeignKey('export_templates.id', ondelete='CASCADE'), nullable=False, index=True)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    schedule_type = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    schedule_config = Column(JSONB, nullable=False)  # Schedule parameters: {day_of_week: 1, hour: 8, minute: 0}
    parameters = Column(JSONB, nullable=True)  # Export parameters to pass to job: {include_sections: {...}}
    delivery_method = Column(String(20), nullable=True)  # 'email', 'storage' (for future email integration)
    is_active = Column(Boolean, default=True, nullable=False)  # Enable/disable schedule without deletion
    last_run_at = Column(DateTime, nullable=True)  # When last executed
    next_run_at = Column(DateTime, nullable=True)  # When next execution should occur
    created_at = Column(DateTime, server_default=text('now()'), nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="scheduled_reports")
    template = relationship("ExportTemplate")
    patient = relationship("User", foreign_keys=[patient_id])
