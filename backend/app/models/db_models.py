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
import logging
import os

logger = logging.getLogger(__name__)


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

    # Note Templates relationship (Feature 3)
    note_templates = relationship(
        "NoteTemplate",
        back_populates="creator",
        foreign_keys="NoteTemplate.created_by"
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

    # Primary key and foreign keys
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), index=True)
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True)

    # Session metadata
    session_date = Column(DateTime, nullable=False)
    duration_seconds = Column(Integer)
    duration_mins = Column(Integer, nullable=True)  # Duration in minutes (derived from duration_seconds)

    # Audio recording
    audio_filename = Column(String(255))
    audio_url = Column(Text)

    # Transcript data
    transcript_text = Column(Text)
    transcript_segments = Column(JSONB)

    # AI-generated content
    extracted_notes = Column(JSONB)
    therapist_summary = Column(Text)
    patient_summary = Column(Text)
    ai_summary = Column(Text, nullable=True)  # AI-generated session summary for session cards
    risk_flags = Column(JSONB)

    # Processing status
    status = Column(String(50), default="pending", index=True)
    processing_status = Column(String(50), nullable=False, default="pending")  # Detailed processing status (pending/processing/completed/failed)
    processing_progress = Column(Integer, nullable=False, default=0)  # Processing progress percentage (0-100)
    error_message = Column(Text)

    # Privacy and deletion tracking (Upheal-inspired features)
    is_anonymous = Column(Boolean, nullable=False, default=False)  # Hide client name in anonymous mode
    recording_deleted_at = Column(DateTime, nullable=True)  # Timestamp when audio file was deleted (soft delete)
    transcript_deleted_at = Column(DateTime, nullable=True)  # Timestamp when transcript was deleted (soft delete)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)

    # Relationships for export service eager loading
    patient = relationship("Patient", foreign_keys=[patient_id])
    therapist = relationship("User", foreign_keys=[therapist_id])

    def mark_anonymous(self, is_anonymous: bool) -> bool:
        """
        Mark this session as anonymous or non-anonymous.

        When anonymous mode is enabled, the client name will be hidden and replaced
        with "Anonymous individual" in the UI. This provides privacy protection for
        sensitive sessions while maintaining the clinical record.

        Args:
            is_anonymous: True to hide client name, False to show it

        Returns:
            The new is_anonymous status

        Example:
            >>> session.mark_anonymous(True)
            True
            >>> session.client_display_name
            'Anonymous individual'
        """
        old_status = self.is_anonymous
        self.is_anonymous = is_anonymous

        if old_status != is_anonymous:
            status_str = "anonymous" if is_anonymous else "non-anonymous"
            logger.info(
                f"Session {self.id} marked as {status_str}",
                extra={"session_id": str(self.id), "is_anonymous": is_anonymous}
            )

        return self.is_anonymous

    @property
    def client_display_name(self) -> str:
        """
        Get the display name for the client.

        Returns "Anonymous individual" if the session is marked anonymous,
        otherwise returns the patient's name from the associated Patient record.

        Returns:
            str: Display name for the client
                - "Anonymous individual" if is_anonymous=True
                - Patient name if is_anonymous=False and patient exists
                - "Unknown" if no patient relationship exists

        Example:
            >>> session.is_anonymous = True
            >>> session.client_display_name
            'Anonymous individual'

            >>> session.is_anonymous = False
            >>> session.client_display_name
            'John Doe'  # from patient.name
        """
        if self.is_anonymous:
            return "Anonymous individual"

        if self.patient:
            # Patient model has 'name' field
            return getattr(self.patient, 'name', 'Unknown')

        return "Unknown"

    def delete_recording(self, remove_file: bool = True) -> bool:
        """
        Soft-delete the audio recording for this session.

        Implements Upheal-inspired granular deletion pattern, allowing therapists
        to delete expensive audio files while preserving transcripts and clinical notes.
        Supports compliance with varying retention policies (e.g., "delete recordings
        after 30 days but keep notes for 7 years").

        Args:
            remove_file: If True, delete actual audio file from disk. Default is True.
                        Set to False if you only want to mark as deleted without
                        removing the file (useful for backup/recovery scenarios).

        Returns:
            True if recording was successfully deleted, False if already deleted.

        Example:
            >>> session.delete_recording()  # Soft-delete and remove file
            True
            >>> session.delete_recording(remove_file=False)  # Soft-delete only
            True
        """
        if self.recording_deleted_at is not None:
            logger.warning(f"Recording already deleted for session {self.id}")
            return False

        # Set deletion timestamp
        self.recording_deleted_at = datetime.utcnow()

        # Optionally remove file from disk
        if remove_file and self.audio_url:
            try:
                if os.path.exists(self.audio_url):
                    os.remove(self.audio_url)
                    logger.info(f"Deleted audio file: {self.audio_url}")
            except OSError as e:
                logger.error(f"Failed to delete audio file {self.audio_url}: {e}")

        logger.info(f"Soft-deleted recording for session {self.id}")
        return True

    def delete_transcript(self, clear_data: bool = True) -> bool:
        """
        Soft-delete the transcript for this session.

        Implements Upheal-inspired granular deletion pattern, allowing therapists
        to delete transcripts containing PHI while preserving audio recordings
        (for reprocessing) and clinical notes.

        Args:
            clear_data: If True, clear transcript_text and transcript_segments from database.
                       Default is True for privacy compliance. Set to False if you only
                       want to mark as deleted without clearing the actual text
                       (useful for backup/recovery scenarios).

        Returns:
            True if transcript was successfully deleted, False if already deleted.

        Example:
            >>> session.delete_transcript()  # Soft-delete and clear data
            True
            >>> session.delete_transcript(clear_data=False)  # Soft-delete only
            True
        """
        if self.transcript_deleted_at is not None:
            logger.warning(f"Transcript already deleted for session {self.id}")
            return False

        # Set deletion timestamp
        self.transcript_deleted_at = datetime.utcnow()

        # Optionally clear transcript data
        if clear_data:
            self.transcript_text = None
            self.transcript_segments = None
            logger.info(f"Cleared transcript data for session {self.id}")

        logger.info(f"Soft-deleted transcript for session {self.id}")
        return True

    @property
    def has_recording(self) -> bool:
        """
        Check if audio recording is available (not soft-deleted).

        Returns:
            True if recording is available, False if deleted.

        Example:
            >>> if session.has_recording:
            ...     play_audio(session.audio_url)
        """
        return self.recording_deleted_at is None

    @property
    def has_transcript(self) -> bool:
        """
        Check if transcript is available (not soft-deleted).

        Returns:
            True if transcript is available, False if deleted.

        Example:
            >>> if session.has_transcript:
            ...     display_transcript(session.transcript_text)
        """
        return self.transcript_deleted_at is None


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

    # Relationships
    creator = relationship("User", back_populates="note_templates", foreign_keys=[created_by])

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"<NoteTemplate(id={self.id}, name='{self.name}', type='{self.template_type}')>"

    def validate_structure(self) -> bool:
        """
        Validate template structure JSON.

        Returns:
            bool: True if structure is valid, False otherwise
        """
        if not isinstance(self.structure, dict):
            return False
        # TODO: Add more comprehensive validation logic based on template_type
        return True


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
