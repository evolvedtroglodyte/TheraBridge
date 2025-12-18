"""
SQLAlchemy ORM models for treatment plans, goals, and interventions.
Implements Feature 4 Treatment Plans specification.
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Date, CheckConstraint, Boolean, Index, JSON, TypeDecorator
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
            return dialect.type_descriptor(ARRAY(String()))
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


class TreatmentPlan(Base):
    """
    Treatment plans for patients with diagnosis-linked goals and progress tracking.
    Supports plan versioning, periodic reviews, and status management.
    """
    __tablename__ = "treatment_plans"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    patient_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    therapist_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Plan details
    title = Column(String(200), nullable=False)
    diagnosis_codes = Column(JSONB, nullable=True)  # ICD-10 codes: [{"code": "F41.1", "description": "..."}]
    presenting_problems = Column(StringArray, nullable=True)  # Array of problem descriptions

    # Timeline
    start_date = Column(Date, nullable=False)
    target_end_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)

    # Status and review tracking
    status = Column(String(20), default='active', nullable=False)  # 'active', 'completed', 'discontinued', 'on_hold'
    review_frequency_days = Column(Integer, default=90, nullable=False)
    next_review_date = Column(Date, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    goals = relationship("TreatmentPlanGoal", back_populates="plan", cascade="all, delete-orphan")
    reviews = relationship("PlanReview", back_populates="plan", cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index('ix_treatment_plans_patient_status', 'patient_id', 'status'),
        Index('ix_treatment_plans_therapist_status', 'therapist_id', 'status'),
        {'extend_existing': True}
    )


class TreatmentPlanGoal(Base):
    """
    Treatment plan goals with SMART framework support.
    Supports goal hierarchies (long-term → short-term → objectives) and progress tracking.
    Note: Uses table name 'treatment_plan_goals' to avoid conflict with goal_models.TreatmentGoal.
    """
    __tablename__ = "treatment_plan_goals"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    plan_id = Column(SQLUUID(as_uuid=True), ForeignKey("treatment_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_goal_id = Column(SQLUUID(as_uuid=True), ForeignKey("treatment_plan_goals.id", ondelete="CASCADE"), nullable=True, index=True)  # For goal hierarchy

    # Goal classification
    goal_type = Column(String(20), nullable=False)  # 'long_term', 'short_term', 'objective'
    description = Column(Text, nullable=False)

    # SMART criteria
    measurable_criteria = Column(Text, nullable=True)
    baseline_value = Column(String(100), nullable=True)
    target_value = Column(String(100), nullable=True)
    current_value = Column(String(100), nullable=True)
    target_date = Column(Date, nullable=True)

    # Status and progress
    status = Column(String(20), default='not_started', nullable=False)  # 'not_started', 'in_progress', 'achieved', 'modified', 'discontinued'
    progress_percentage = Column(Integer, default=0, nullable=False)
    priority = Column(Integer, default=1, nullable=False)  # 1=highest priority

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    plan = relationship("TreatmentPlan", back_populates="goals")
    parent_goal = relationship("TreatmentPlanGoal", remote_side=[id], back_populates="sub_goals")
    sub_goals = relationship("TreatmentPlanGoal", back_populates="parent_goal", cascade="all, delete-orphan")
    interventions = relationship("GoalIntervention", back_populates="goal", cascade="all, delete-orphan")
    progress_entries = relationship("GoalProgress", back_populates="goal", cascade="all, delete-orphan")

    # Indexes for hierarchy and status queries
    __table_args__ = (
        Index('ix_treatment_plan_goals_plan_status', 'plan_id', 'status'),
        Index('ix_treatment_plan_goals_parent_goal', 'parent_goal_id'),
        {'extend_existing': True}
    )


class Intervention(Base):
    """
    Evidence-based intervention library.
    Supports system-defined and custom user-created interventions.
    Categorized by modality and evidence level.
    """
    __tablename__ = "interventions"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Intervention details
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    modality = Column(String(50), nullable=True)  # 'CBT', 'DBT', 'psychodynamic', 'mindfulness', etc.
    evidence_level = Column(String(20), nullable=True)  # 'strong', 'moderate', 'emerging'

    # System vs custom interventions
    is_system = Column(Boolean, default=False, nullable=False)  # True for built-in library interventions
    created_by = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    goal_interventions = relationship("GoalIntervention", back_populates="intervention", cascade="all, delete-orphan")

    # Indexes for searching and filtering
    __table_args__ = (
        Index('ix_interventions_modality', 'modality'),
        Index('ix_interventions_is_system', 'is_system'),
        {'extend_existing': True}
    )


class GoalIntervention(Base):
    """
    Junction table linking goals to interventions.
    Tracks frequency, effectiveness, and usage notes.
    """
    __tablename__ = "goal_interventions"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    goal_id = Column(SQLUUID(as_uuid=True), ForeignKey("treatment_plan_goals.id", ondelete="CASCADE"), nullable=False, index=True)
    intervention_id = Column(SQLUUID(as_uuid=True), ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Intervention application details
    frequency = Column(String(50), nullable=True)  # 'every session', 'weekly', 'bi-weekly', 'as needed'
    notes = Column(Text, nullable=True)
    effectiveness_rating = Column(Integer, CheckConstraint('effectiveness_rating >= 1 AND effectiveness_rating <= 5'), nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    goal = relationship("TreatmentPlanGoal", back_populates="interventions")
    intervention = relationship("Intervention", back_populates="goal_interventions")

    # Indexes for junction table queries
    __table_args__ = (
        Index('ix_goal_interventions_goal', 'goal_id'),
        Index('ix_goal_interventions_intervention', 'intervention_id'),
        {'extend_existing': True}
    )


class GoalProgress(Base):
    """
    Progress tracking entries for treatment goals.
    Links to therapy sessions and allows rating-based progress measurement.
    """
    __tablename__ = "goal_progress"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    goal_id = Column(SQLUUID(as_uuid=True), ForeignKey("treatment_plan_goals.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(SQLUUID(as_uuid=True), ForeignKey("therapy_sessions.id", ondelete="SET NULL"), nullable=True, index=True)  # SET NULL to preserve progress history
    recorded_by = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Progress details
    progress_note = Column(Text, nullable=False)
    progress_value = Column(String(100), nullable=True)  # Current value for measurable goals
    rating = Column(Integer, CheckConstraint('rating >= 1 AND rating <= 10'), nullable=True)  # 1-10 progress rating

    # Timestamp
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    goal = relationship("TreatmentPlanGoal", back_populates="progress_entries")

    # Indexes for chronological queries
    __table_args__ = (
        Index('ix_goal_progress_goal_date', 'goal_id', 'recorded_at'),
        Index('ix_goal_progress_session', 'session_id'),
        {'extend_existing': True}
    )


class PlanReview(Base):
    """
    Treatment plan review records.
    Tracks periodic reviews, goal assessments, and modifications to treatment plans.
    """
    __tablename__ = "plan_reviews"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    plan_id = Column(SQLUUID(as_uuid=True), ForeignKey("treatment_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(SQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Review details
    review_date = Column(Date, nullable=False)
    summary = Column(Text, nullable=False)
    goals_reviewed = Column(Integer, nullable=True)  # Total goals reviewed
    goals_on_track = Column(Integer, nullable=True)  # Goals meeting progress expectations
    modifications_made = Column(Text, nullable=True)  # Description of plan modifications
    next_review_date = Column(Date, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    plan = relationship("TreatmentPlan", back_populates="reviews")

    # Indexes for review tracking
    __table_args__ = (
        Index('ix_plan_reviews_plan_date', 'plan_id', 'review_date'),
        {'extend_existing': True}
    )
