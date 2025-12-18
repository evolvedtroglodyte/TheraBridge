"""
SQLAlchemy ORM models for goal tracking and progress monitoring
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Date, Numeric
from sqlalchemy.dialects.postgresql import UUID as SQLUUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class TreatmentGoal(Base):
    """
    Treatment goals for patients.
    Tracks goals assigned by therapists with status, progress metrics, and deadlines.
    Migrated from action_items in therapy_sessions.extracted_notes JSONB to relational table.
    """
    __tablename__ = "treatment_goals"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    patient_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    therapist_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("therapy_sessions.id", ondelete="SET NULL"),
        nullable=True
    )

    # Goal details
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=True)  # homework, reflection, behavioral, emotional, etc.
    status = Column(String(20), default='assigned', nullable=False)  # assigned, in_progress, completed, abandoned

    # Progress tracking metrics
    baseline_value = Column(Numeric(10, 2), nullable=True)  # Starting measurement
    target_value = Column(Numeric(10, 2), nullable=True)    # Target measurement
    target_date = Column(Date, nullable=True)               # Deadline for goal completion

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    therapist = relationship("User", foreign_keys=[therapist_id])
    session = relationship("TherapySession", foreign_keys=[session_id])

    def __repr__(self):
        return f"<TreatmentGoal(id={self.id}, patient_id={self.patient_id}, status={self.status}, description={self.description[:50]}...)>"
