"""
Pydantic schemas for goal tracking API requests/responses
"""
from datetime import datetime, time
from datetime import date as date_type
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class TrackingMethod(str, Enum):
    """Method used to track progress on a goal"""
    scale = "scale"
    frequency = "frequency"
    duration = "duration"
    binary = "binary"
    assessment = "assessment"


class TrackingFrequency(str, Enum):
    """How often progress should be tracked"""
    daily = "daily"
    weekly = "weekly"
    session = "session"
    custom = "custom"


class TargetDirection(str, Enum):
    """Direction of desired change for a goal"""
    increase = "increase"
    decrease = "decrease"
    maintain = "maintain"


class EntryContext(str, Enum):
    """Context in which a progress entry was created"""
    session = "session"
    self_report = "self_report"
    assessment = "assessment"


class TrendDirection(str, Enum):
    """Direction of progress trend"""
    improving = "improving"
    stable = "stable"
    declining = "declining"
    insufficient_data = "insufficient_data"


class GoalStatus(str, Enum):
    """Current status of a treatment goal"""
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


class AggregationPeriod(str, Enum):
    """Period for aggregating progress data"""
    none = "none"
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


# ============================================================================
# Request Schemas
# ============================================================================

class TreatmentGoalCreate(BaseModel):
    """Request to create a new treatment goal"""
    description: str = Field(..., min_length=1, max_length=500, description="Goal description")
    category: Optional[str] = Field(None, max_length=100, description="Goal category (e.g., 'Anxiety management')")
    baseline_value: Optional[float] = Field(None, description="Starting value for tracking")
    target_value: Optional[float] = Field(None, description="Target value to achieve")
    target_date: Optional[date_type] = Field(None, description="Target completion date")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        """Ensure description is not empty after stripping"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Description cannot be empty')
        return v.strip()

    @field_validator('target_date')
    @classmethod
    def validate_target_date_not_past(cls, v: Optional[date_type]) -> Optional[date_type]:
        """Ensure target date is not in the past"""
        if v and v < date_type.today():
            raise ValueError('Target date cannot be in the past')
        return v


class TreatmentGoalUpdate(BaseModel):
    """Request to update an existing treatment goal"""
    description: Optional[str] = Field(None, min_length=1, max_length=500, description="Goal description")
    category: Optional[str] = Field(None, max_length=100, description="Goal category")
    baseline_value: Optional[float] = Field(None, description="Starting value for tracking")
    target_value: Optional[float] = Field(None, description="Target value to achieve")
    target_date: Optional[date_type] = Field(None, description="Target completion date")
    status: Optional[GoalStatus] = Field(None, description="Goal status")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Ensure description is not empty after stripping if provided"""
        if v is not None and len(v.strip()) == 0:
            raise ValueError('Description cannot be empty')
        return v.strip() if v else None


class TrackingConfigCreate(BaseModel):
    """Request to create or update tracking configuration for a goal"""
    tracking_method: TrackingMethod = Field(..., description="Method for tracking progress")
    tracking_frequency: TrackingFrequency = Field(..., description="How often to track")
    scale_min: Optional[int] = Field(None, description="Minimum value for scale tracking (e.g., 1)")
    scale_max: Optional[int] = Field(None, description="Maximum value for scale tracking (e.g., 10)")
    scale_labels: Optional[Dict[str, str]] = Field(None, description="Labels for scale values (e.g., {'1': 'Not at all', '10': 'Extremely'})")
    frequency_unit: Optional[str] = Field(None, max_length=50, description="Unit for frequency tracking (e.g., 'times per day')")
    duration_unit: Optional[str] = Field(None, max_length=50, description="Unit for duration tracking (e.g., 'minutes')")
    target_direction: TargetDirection = Field(..., description="Desired direction of change")
    reminder_enabled: bool = Field(default=False, description="Whether to send tracking reminders")

    @field_validator('scale_min', 'scale_max')
    @classmethod
    def validate_scale_range(cls, v: Optional[int], info) -> Optional[int]:
        """Ensure scale values are reasonable"""
        if v is not None and (v < -100 or v > 100):
            raise ValueError('Scale values must be between -100 and 100')
        return v

    def model_post_init(self, __context):
        """Validate scale_min < scale_max if both are provided"""
        if self.scale_min is not None and self.scale_max is not None:
            if self.scale_min >= self.scale_max:
                raise ValueError('scale_min must be less than scale_max')


class ProgressEntryCreate(BaseModel):
    """Request to create a new progress entry"""
    entry_date: date_type = Field(..., description="Date of the entry")
    entry_time: Optional[time] = Field(None, description="Time of the entry")
    value: float = Field(..., description="Numeric value for progress (scale, frequency, duration, or 0/1 for binary)")
    value_label: Optional[str] = Field(None, max_length=100, description="Optional label for the value")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes about this entry")
    context: EntryContext = Field(..., description="Context in which entry was created")

    @field_validator('entry_date')
    @classmethod
    def validate_entry_date_not_future(cls, v: date_type) -> date_type:
        """Ensure entry date is not in the future"""
        if v > date_type.today():
            raise ValueError('Entry date cannot be in the future')
        return v

    @field_validator('value')
    @classmethod
    def validate_value_reasonable(cls, v: float) -> float:
        """Ensure value is a reasonable number"""
        if v < -1000 or v > 10000:
            raise ValueError('Value must be between -1000 and 10000')
        return v


class ProgressHistoryQuery(BaseModel):
    """Query parameters for retrieving progress history"""
    start_date: Optional[date_type] = Field(None, description="Start date for filtering entries")
    end_date: Optional[date_type] = Field(None, description="End date for filtering entries")
    aggregation: Optional[AggregationPeriod] = Field(None, description="Period for aggregating data")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: Optional[date_type], info) -> Optional[date_type]:
        """Ensure end_date is after start_date if both are provided"""
        start_date = info.data.get('start_date')
        if v and start_date and v < start_date:
            raise ValueError('end_date must be after start_date')
        return v


# ============================================================================
# Response Schemas
# ============================================================================

class TreatmentGoalResponse(BaseModel):
    """Complete treatment goal data returned by API"""
    id: UUID = Field(..., description="Unique goal identifier")
    patient_id: UUID = Field(..., description="Associated patient ID")
    therapist_id: UUID = Field(..., description="Associated therapist ID")
    description: str = Field(..., description="Goal description")
    category: Optional[str] = Field(None, description="Goal category")
    baseline_value: Optional[float] = Field(None, description="Starting value")
    target_value: Optional[float] = Field(None, description="Target value")
    target_date: Optional[date_type] = Field(None, description="Target completion date")
    status: GoalStatus = Field(..., description="Current goal status")
    created_at: datetime = Field(..., description="When goal was created")
    updated_at: datetime = Field(..., description="When goal was last updated")
    completed_at: Optional[datetime] = Field(None, description="When goal was completed")

    model_config = ConfigDict(from_attributes=True)


class TrackingConfigResponse(BaseModel):
    """Tracking configuration data returned by API"""
    id: UUID = Field(..., description="Unique config identifier")
    goal_id: UUID = Field(..., description="Associated goal ID")
    tracking_method: TrackingMethod = Field(..., description="Method for tracking progress")
    tracking_frequency: TrackingFrequency = Field(..., description="How often to track")
    scale_min: Optional[int] = Field(None, description="Minimum scale value")
    scale_max: Optional[int] = Field(None, description="Maximum scale value")
    scale_labels: Optional[Dict[str, str]] = Field(None, description="Labels for scale values")
    frequency_unit: Optional[str] = Field(None, description="Unit for frequency tracking")
    duration_unit: Optional[str] = Field(None, description="Unit for duration tracking")
    target_direction: TargetDirection = Field(..., description="Desired direction of change")
    reminder_enabled: bool = Field(..., description="Whether reminders are enabled")
    created_at: datetime = Field(..., description="When config was created")
    updated_at: datetime = Field(..., description="When config was last updated")

    model_config = ConfigDict(from_attributes=True)


class ProgressEntryResponse(BaseModel):
    """Progress entry data returned by API"""
    id: UUID = Field(..., description="Unique entry identifier")
    goal_id: UUID = Field(..., description="Associated goal ID")
    entry_date: date_type = Field(..., description="Date of entry")
    entry_time: Optional[time] = Field(None, description="Time of entry")
    value: float = Field(..., description="Progress value")
    value_label: Optional[str] = Field(None, description="Label for the value")
    notes: Optional[str] = Field(None, description="Additional notes")
    context: EntryContext = Field(..., description="Entry context")
    session_id: Optional[UUID] = Field(None, description="Associated session ID if context is 'session'")
    created_at: datetime = Field(..., description="When entry was created")

    model_config = ConfigDict(from_attributes=True)


class ProgressStatistics(BaseModel):
    """Statistical summary of progress data"""
    baseline: Optional[float] = Field(None, description="Baseline value from goal")
    current: Optional[float] = Field(None, description="Most recent entry value")
    target: Optional[float] = Field(None, description="Target value from goal")
    average: Optional[float] = Field(None, description="Average of all entries")
    min: Optional[float] = Field(None, description="Minimum entry value")
    max: Optional[float] = Field(None, description="Maximum entry value")
    trend_slope: Optional[float] = Field(None, description="Linear regression slope (positive = improving if target_direction is increase)")
    trend_direction: TrendDirection = Field(..., description="Overall trend direction")


class ProgressHistoryResponse(BaseModel):
    """Complete progress history for a goal"""
    goal_id: UUID = Field(..., description="Goal identifier")
    tracking_method: TrackingMethod = Field(..., description="Tracking method used")
    entries: List[ProgressEntryResponse] = Field(..., description="List of progress entries")
    statistics: ProgressStatistics = Field(..., description="Statistical summary")


class TrendData(BaseModel):
    """Data point for trend visualization"""
    date: date_type = Field(..., description="Date of data point")
    value: float = Field(..., description="Progress value at this date")


class GoalDashboardItem(BaseModel):
    """Goal summary for dashboard display"""
    id: UUID = Field(..., description="Goal identifier")
    description: str = Field(..., description="Goal description")
    category: Optional[str] = Field(None, description="Goal category")
    status: GoalStatus = Field(..., description="Goal status")
    current_value: Optional[float] = Field(None, description="Most recent progress value")
    baseline_value: Optional[float] = Field(None, description="Starting value")
    target_value: Optional[float] = Field(None, description="Target value")
    progress_percentage: Optional[float] = Field(None, description="Percentage toward goal (0-100)")
    trend: TrendDirection = Field(..., description="Recent trend direction")
    trend_data: List[TrendData] = Field(..., description="Recent trend data points for visualization")
    last_entry: Optional[datetime] = Field(None, description="When last entry was made")
    next_check_in: Optional[date_type] = Field(None, description="Suggested next check-in date based on tracking frequency")


class TrackingSummary(BaseModel):
    """Summary of tracking activity"""
    entries_this_week: int = Field(..., description="Number of progress entries this week")
    streak_days: int = Field(..., description="Current streak of consecutive tracking days")
    completion_rate: float = Field(..., description="Percentage of expected entries completed (0-100)")


class GoalDashboardResponse(BaseModel):
    """Complete dashboard view for a patient's goals"""
    patient_id: UUID = Field(..., description="Patient identifier")
    active_goals: int = Field(..., description="Number of active goals")
    tracking_summary: TrackingSummary = Field(..., description="Overall tracking activity summary")
    goals: List[GoalDashboardItem] = Field(..., description="List of all goals with progress")
    recent_milestones: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent achievements and milestones"
    )
    assessments_due: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Upcoming assessments that need to be completed"
    )
