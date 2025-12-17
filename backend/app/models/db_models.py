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
    name = Column(String(255))
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to auth sessions (for refresh token management)
    auth_sessions = relationship("AuthSession", back_populates="user", cascade="all, delete-orphan")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("patients.id"))
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id"))
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
