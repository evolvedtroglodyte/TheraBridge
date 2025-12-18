"""
SQLAlchemy ORM models for goal tracking tables (Feature 6)
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Date, Time, Numeric, Boolean, CheckConstraint, Index, JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as SQLUUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class IntegerArray(TypeDecorator):
    """
    SQLite-compatible ARRAY type that stores integers as JSON.
    On PostgreSQL, uses native ARRAY(Integer).
    On SQLite, stores as JSON array of integers.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(ARRAY(Integer))
        else:
            return dialect.type_descriptor(JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        # Already a list, return as-is (will be serialized to JSON automatically)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        # Already a list from JSON deserialization
        return value


class GoalTrackingConfig(Base):
    """
    Configuration for how treatment goals are tracked.
    Defines tracking method, frequency, scales, and reminder settings.
    Each goal can have one tracking configuration.
    """
    __tablename__ = "goal_tracking_config"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    goal_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("treatment_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Tracking method configuration
    tracking_method = Column(String(50), nullable=False)  # 'scale', 'frequency', 'duration', 'binary', 'assessment'
    tracking_frequency = Column(String(20), default='session', nullable=False)  # 'daily', 'weekly', 'session', 'custom'
    custom_frequency_days = Column(Integer, nullable=True)  # Used when tracking_frequency='custom'

    # Scale configuration (for tracking_method='scale')
    scale_min = Column(Integer, default=1, nullable=False)
    scale_max = Column(Integer, default=10, nullable=False)
    scale_labels = Column(JSONB, nullable=True)  # Custom labels for scale points

    # Unit configuration (for frequency/duration tracking)
    frequency_unit = Column(String(20), nullable=True)  # 'times_per_day', 'times_per_week', etc.
    duration_unit = Column(String(20), nullable=True)   # 'minutes', 'hours', etc.

    # Target direction for progress evaluation
    target_direction = Column(String(10), nullable=True)  # 'increase', 'decrease', 'maintain'

    # Reminder settings
    reminder_enabled = Column(Boolean, default=True, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    goal = relationship("TreatmentGoal", foreign_keys=[goal_id], backref="tracking_config")
    progress_entries = relationship("ProgressEntry", back_populates="tracking_config", cascade="all, delete-orphan")

    # Check constraints
    __table_args__ = (
        CheckConstraint("tracking_method IN ('scale', 'frequency', 'duration', 'binary', 'assessment')", name='ck_goal_tracking_config_tracking_method'),
        CheckConstraint("tracking_frequency IN ('daily', 'weekly', 'session', 'custom')", name='ck_goal_tracking_config_frequency'),
        CheckConstraint('scale_min < scale_max', name='ck_goal_tracking_config_scale_range'),
        CheckConstraint('scale_min >= 1', name='ck_goal_tracking_config_scale_min'),
        CheckConstraint('scale_max <= 10', name='ck_goal_tracking_config_scale_max'),
        CheckConstraint("target_direction IS NULL OR target_direction IN ('increase', 'decrease', 'maintain')", name='ck_goal_tracking_config_direction'),
    )

    def __repr__(self):
        return f"<GoalTrackingConfig(id={self.id}, goal_id={self.goal_id}, method={self.tracking_method}, frequency={self.tracking_frequency})>"


class ProgressEntry(Base):
    """
    Individual progress data points for goal tracking.
    Records measurements, self-reports, or assessment results over time.
    Supports multiple recording contexts: session, self_report, assessment.
    """
    __tablename__ = "progress_entries"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    goal_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("treatment_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tracking_config_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("goal_tracking_config.id", ondelete="SET NULL"),
        nullable=True
    )
    session_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("therapy_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    recorded_by = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Entry details
    entry_date = Column(Date, nullable=False)
    entry_time = Column(Time, nullable=True)
    value = Column(Numeric(10, 2), nullable=False)  # Numeric value (scale score, frequency count, duration, etc.)
    value_label = Column(String(100), nullable=True)  # Human-readable label for value
    notes = Column(Text, nullable=True)  # Additional context or notes

    # Context tracking
    context = Column(String(50), nullable=True)  # 'session', 'self_report', 'assessment'

    # Timestamps
    recorded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    goal = relationship("TreatmentGoal", foreign_keys=[goal_id], backref="progress_entries")
    tracking_config = relationship("GoalTrackingConfig", foreign_keys=[tracking_config_id], back_populates="progress_entries")
    session = relationship("TherapySession", foreign_keys=[session_id])
    recorder = relationship("User", foreign_keys=[recorded_by])

    # Check constraints and indexes
    __table_args__ = (
        CheckConstraint("context IS NULL OR context IN ('session', 'self_report', 'assessment')", name='ck_progress_entries_context'),
        Index('idx_progress_entries_goal_date', 'goal_id', 'entry_date', postgresql_ops={'entry_date': 'DESC'}),
    )

    def __repr__(self):
        return f"<ProgressEntry(id={self.id}, goal_id={self.goal_id}, date={self.entry_date}, value={self.value}, context={self.context})>"


class AssessmentScore(Base):
    """
    Standardized assessment results (PHQ-9, GAD-7, BDI, etc.).
    Tracks clinical assessments over time with scoring and severity classification.
    Can be linked to specific treatment goals or tracked independently.
    """
    __tablename__ = "assessment_scores"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    patient_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    goal_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("treatment_goals.id", ondelete="SET NULL"),
        nullable=True
    )
    administered_by = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )

    # Assessment details
    assessment_type = Column(String(50), nullable=False, index=True)  # 'PHQ-9', 'GAD-7', 'BDI', 'BAI', etc.
    score = Column(Integer, nullable=False)  # Total score
    severity = Column(String(20), nullable=True)  # 'minimal', 'mild', 'moderate', 'severe', etc.
    subscores = Column(JSONB, nullable=True)  # Subscale scores or item-level responses

    # Administration details
    administered_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id])
    goal = relationship("TreatmentGoal", foreign_keys=[goal_id], backref="assessments")
    administrator = relationship("User", foreign_keys=[administered_by])

    # Check constraints and indexes
    __table_args__ = (
        CheckConstraint('score >= 0', name='ck_assessment_scores_score'),
        Index('idx_assessment_scores_patient_date', 'patient_id', 'administered_date', postgresql_ops={'administered_date': 'DESC'}),
    )

    def __repr__(self):
        return f"<AssessmentScore(id={self.id}, patient_id={self.patient_id}, type={self.assessment_type}, score={self.score}, date={self.administered_date})>"


class ProgressMilestone(Base):
    """
    Achievement markers for treatment goals.
    Tracks significant progress events like reaching target values, maintaining streaks,
    or achieving percentage-based completion.
    """
    __tablename__ = "progress_milestones"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key
    goal_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("treatment_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Milestone details
    milestone_type = Column(String(50), nullable=True)  # 'percentage', 'value', 'streak', 'custom'
    title = Column(String(200), nullable=False)  # Short milestone title
    description = Column(Text, nullable=True)  # Detailed description
    target_value = Column(Numeric(10, 2), nullable=True)  # Target value for this milestone

    # Achievement tracking
    achieved_at = Column(DateTime, nullable=True)  # When milestone was achieved (NULL = not yet achieved)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    goal = relationship("TreatmentGoal", foreign_keys=[goal_id], backref="milestones")

    # Check constraint
    __table_args__ = (
        CheckConstraint("milestone_type IS NULL OR milestone_type IN ('percentage', 'value', 'streak', 'custom')", name='ck_progress_milestones_type'),
    )

    def __repr__(self):
        status = "achieved" if self.achieved_at else "pending"
        return f"<ProgressMilestone(id={self.id}, goal_id={self.goal_id}, title={self.title}, status={status})>"


class GoalReminder(Base):
    """
    Reminder configurations for treatment goals.
    Enables patients to receive check-in, progress, or motivation reminders
    on scheduled days and times.
    """
    __tablename__ = "goal_reminders"

    # Primary key
    id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    goal_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("treatment_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    patient_id = Column(
        SQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Reminder configuration
    reminder_type = Column(String(20), nullable=True)  # 'check_in', 'progress', 'motivation'
    scheduled_time = Column(Time, nullable=True)  # Time of day to send reminder
    scheduled_days = Column(JSONB, nullable=True)  # Days of week as JSON array: [0, 1, 2] (0=Monday, 6=Sunday)
    message = Column(Text, nullable=True)  # Custom reminder message

    # Status tracking
    is_active = Column(Boolean, default=True, nullable=False)
    last_sent_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    goal = relationship("TreatmentGoal", foreign_keys=[goal_id], backref="reminders")
    patient = relationship("User", foreign_keys=[patient_id])

    # Check constraint and indexes
    __table_args__ = (
        CheckConstraint("reminder_type IS NULL OR reminder_type IN ('check_in', 'progress', 'motivation')", name='ck_goal_reminders_type'),
        Index('idx_goal_reminders_goal_active', 'goal_id', 'is_active'),
    )

    def __repr__(self):
        status = "active" if self.is_active else "inactive"
        return f"<GoalReminder(id={self.id}, goal_id={self.goal_id}, type={self.reminder_type}, status={status})>"
