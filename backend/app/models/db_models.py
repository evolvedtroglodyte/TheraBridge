"""
SQLAlchemy ORM models for database tables
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Enum, Boolean
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

    status = Column(String(50), default="pending")
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    processed_at = Column(DateTime)


# Backwards compatibility alias - allows existing code to use 'Session' name
Session = TherapySession
