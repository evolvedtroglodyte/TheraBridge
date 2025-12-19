"""
SQLAlchemy ORM models for database tables
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID as SQLUUID, JSONB
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.models.schemas import UserRole
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)  # Added for Feature 1 spec compliance
    last_name = Column(String(100), nullable=True)   # Added for Feature 1 spec compliance
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # Added for email verification
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to auth sessions (for refresh token management)
    auth_sessions = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")

    # Relationship to therapist-patient assignments (for many-to-many)
    # As therapist: patients I treat
    patients_assigned = relationship(
        "TherapistPatient",
        foreign_keys="TherapistPatient.therapist_id",
        back_populates="therapist",
        cascade="all, delete-orphan"
    )
    # As patient: therapists treating me
    therapists_assigned = relationship(
        "TherapistPatient",
        foreign_keys="TherapistPatient.patient_id",
        back_populates="patient",
        cascade="all, delete-orphan"
    )

    # Export & Reporting relationships (Feature 7)
    export_templates = relationship(
        "ExportTemplate",
        back_populates="creator",
        foreign_keys="ExportTemplate.created_by"
    )
    export_jobs = relationship(
        "ExportJob",
        back_populates="user",
        foreign_keys="ExportJob.user_id"
    )
    scheduled_reports = relationship(
        "ScheduledReport",
        back_populates="user",
        foreign_keys="ScheduledReport.user_id"
    )


class Patient(Base):
    __tablename__ = "patients"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TherapistPatient(Base):
    """
    Junction table for many-to-many therapist-patient relationships.
    Allows multiple therapists per patient and vice versa.
    """
    __tablename__ = "therapist_patients"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_type = Column(String(50), default="primary")  # 'primary', 'secondary', 'consulting'
    is_active = Column(Boolean, default=True, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships back to User
    therapist = relationship("User", foreign_keys=[therapist_id], back_populates="patients_assigned")
    patient = relationship("User", foreign_keys=[patient_id], back_populates="therapists_assigned")


class TherapySession(Base):
    """
    Therapy session records (renamed from Session to avoid conflict with auth sessions).
    Stores transcripts, notes, and processing status.
    """
    __tablename__ = "therapy_sessions"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), index=True)
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)
    session_date = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer)

    audio_filename = Column(String(255))
    audio_url = Column(Text)

    transcript_text = Column(Text)
    transcript_segments = Column(JSONB)

    extracted_notes = Column(JSONB)
    therapist_summary = Column(Text)
    patient_summary = Column(Text)
    risk_flags = Column(JSONB)

    status = Column(String(50), default="pending", index=True)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)

    # Relationships for export service eager loading
    patient = relationship("Patient", foreign_keys=[patient_id])
    therapist = relationship("User", foreign_keys=[therapist_id])


# Backwards compatibility alias - allows existing code to use 'Session' name
Session = TherapySession


class TimelineEvent(Base):
    """
    Timeline events for patient treatment history.
    Tracks sessions, milestones, clinical events, goals, assessments, and administrative notes.
    Supports filtering, searching, and chronological display of patient care journey.
    """
    __tablename__ = "timeline_events"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys with cascade delete
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)

    # Event classification
    event_type = Column(String(50), nullable=False, index=True)  # 'session', 'milestone', 'clinical', 'administrative', 'goal', 'assessment', 'note'
    event_subtype = Column(String(50), nullable=True)  # Specific subtype within event_type

    # Event details
    event_date = Column(DateTime, nullable=False)  # When the event occurred
    title = Column(String(200), nullable=False)  # Short event title
    description = Column(Text, nullable=True)  # Detailed description
    event_metadata = Column(JSONB, nullable=True)  # Type-specific data (e.g., session metrics, goal progress)

    # Polymorphic reference to related entities
    related_entity_type = Column(String(50), nullable=True)  # e.g., 'session', 'goal', 'plan'
    related_entity_id = Column(SQLUUID(as_uuid=True), nullable=True)  # UUID of related entity

    # Event attributes
    importance = Column(String(20), default='normal', nullable=False)  # 'low', 'normal', 'high', 'milestone'
    is_private = Column(Boolean, default=False, nullable=False)  # Therapist-only visibility flag

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Composite index for efficient timeline queries (patient_id, event_date DESC)
    __table_args__ = (
        Index('ix_timeline_events_patient_date', 'patient_id', 'event_date', postgresql_ops={'event_date': 'DESC'}),
    )


class NoteTemplate(Base):
    """
    Note templates for structured clinical documentation.
    Supports system templates (SOAP, DAP, BIRP) and custom user-created templates.
    Templates define the structure for SessionNote records.
    """
    __tablename__ = "note_templates"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(50), nullable=False)  # 'soap', 'dap', 'birp', 'progress', 'custom'
    is_system = Column(Boolean, default=False, nullable=False)  # True for built-in templates
    created_by = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_shared = Column(Boolean, default=False, nullable=False)  # Shared within practice
    structure = Column(JSONB, nullable=False)  # Template structure definition
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionNote(Base):
    """
    Clinical notes for therapy sessions.
    Links sessions to note templates and stores filled template content.
    Supports draft/completed/signed workflow with audit trail.
    """
    __tablename__ = "session_notes"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(SQLUUID(as_uuid=True), ForeignKey("therapy_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    template_id = Column(SQLUUID(as_uuid=True), ForeignKey("note_templates.id", ondelete="SET NULL"), nullable=True, index=True)
    content = Column(JSONB, nullable=False)  # Filled template data
    status = Column(String(20), default='draft', nullable=False)  # 'draft', 'completed', 'signed'
    signed_at = Column(DateTime, nullable=True)
    signed_by = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TemplateUsage(Base):
    """
    Tracks template usage for analytics and recommendations.
    Records each time a template is used by a user.
    """
    __tablename__ = "template_usage"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    template_id = Column(SQLUUID(as_uuid=True), ForeignKey("note_templates.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    used_at = Column(DateTime, default=datetime.utcnow)
