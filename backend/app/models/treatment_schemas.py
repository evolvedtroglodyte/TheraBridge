"""
Pydantic schemas for Treatment Plans Feature (Feature 4)
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class PlanStatus(str, Enum):
    """Treatment plan status"""
    active = "active"
    completed = "completed"
    discontinued = "discontinued"
    on_hold = "on_hold"


class GoalType(str, Enum):
    """Treatment goal type (hierarchy support)"""
    long_term = "long_term"
    short_term = "short_term"
    objective = "objective"


class GoalStatus(str, Enum):
    """Treatment goal status"""
    not_started = "not_started"
    in_progress = "in_progress"
    achieved = "achieved"
    modified = "modified"
    discontinued = "discontinued"


class EvidenceLevel(str, Enum):
    """Intervention evidence level"""
    strong = "strong"
    moderate = "moderate"
    emerging = "emerging"


# ============================================================================
# Treatment Plan Schemas
# ============================================================================

class TreatmentPlanBase(BaseModel):
    """Base treatment plan fields"""
    title: str = Field(..., min_length=1, max_length=200, description="Plan title")
    diagnosis_codes: Optional[List[Dict[str, str]]] = Field(
        default_factory=list,
        description="ICD-10 codes with descriptions [{code: 'F41.1', description: '...'}]"
    )
    presenting_problems: List[str] = Field(
        default_factory=list,
        description="List of presenting problems"
    )
    start_date: date = Field(..., description="Plan start date")
    target_end_date: Optional[date] = Field(None, description="Target completion date")
    review_frequency_days: int = Field(
        default=90,
        ge=1,
        le=365,
        description="Days between reviews (1-365)"
    )
    notes: Optional[str] = Field(None, description="Additional notes or context")

    @field_validator('title')
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        """Ensure title is not just whitespace"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        return v.strip()

    @field_validator('target_end_date')
    @classmethod
    def validate_target_after_start(cls, v: Optional[date], info) -> Optional[date]:
        """Ensure target_end_date is after start_date"""
        if v is not None:
            start_date = info.data.get('start_date')
            if start_date and v <= start_date:
                raise ValueError('target_end_date must be after start_date')
        return v


class TreatmentPlanCreate(TreatmentPlanBase):
    """Request to create a treatment plan"""
    pass


class TreatmentPlanUpdate(BaseModel):
    """Request to update a treatment plan (partial updates allowed)"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated plan title")
    diagnosis_codes: Optional[List[Dict[str, str]]] = Field(None, description="Updated diagnosis codes")
    presenting_problems: Optional[List[str]] = Field(None, description="Updated presenting problems")
    target_end_date: Optional[date] = Field(None, description="Updated target end date")
    status: Optional[PlanStatus] = Field(None, description="Updated plan status")
    review_frequency_days: Optional[int] = Field(None, ge=1, le=365, description="Updated review frequency")
    notes: Optional[str] = Field(None, description="Updated notes")


class TreatmentPlanResponse(TreatmentPlanBase):
    """Complete treatment plan data returned by API"""
    id: UUID = Field(..., description="Unique plan identifier")
    patient_id: UUID = Field(..., description="Associated patient ID")
    therapist_id: UUID = Field(..., description="Associated therapist ID")
    status: PlanStatus = Field(..., description="Current plan status")
    version: int = Field(..., description="Plan version number")
    next_review_date: Optional[date] = Field(None, description="Next scheduled review date")
    actual_end_date: Optional[date] = Field(None, description="Actual completion date")
    created_at: datetime = Field(..., description="Plan creation timestamp")
    updated_at: datetime = Field(..., description="Plan last update timestamp")

    # Optional nested goals (included in full plan GET)
    goals: Optional[List['GoalResponse']] = Field(None, description="Associated goals (optional)")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Treatment Goal Schemas
# ============================================================================

class GoalBase(BaseModel):
    """Base treatment goal fields"""
    description: str = Field(..., min_length=1, description="Goal description")
    goal_type: GoalType = Field(..., description="Goal type (long_term, short_term, objective)")
    measurable_criteria: Optional[str] = Field(None, description="How to measure success")
    baseline_value: Optional[str] = Field(None, max_length=100, description="Starting point")
    target_value: Optional[str] = Field(None, max_length=100, description="Target outcome")
    target_date: Optional[date] = Field(None, description="Target achievement date")
    priority: int = Field(default=1, ge=1, le=10, description="Priority (1=highest, 10=lowest)")

    @field_validator('description')
    @classmethod
    def validate_description_not_empty(cls, v: str) -> str:
        """Ensure description is not just whitespace"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Description cannot be empty')
        return v.strip()


class GoalCreate(GoalBase):
    """Request to create a treatment goal"""
    plan_id: UUID = Field(..., description="Associated treatment plan ID")
    parent_goal_id: Optional[UUID] = Field(None, description="Parent goal ID (for hierarchies)")
    interventions: Optional[List['GoalInterventionCreate']] = Field(
        default_factory=list,
        description="Interventions to link to this goal"
    )


class GoalUpdate(BaseModel):
    """Request to update a goal (partial updates allowed)"""
    description: Optional[str] = Field(None, min_length=1, description="Updated description")
    measurable_criteria: Optional[str] = Field(None, description="Updated criteria")
    baseline_value: Optional[str] = Field(None, max_length=100, description="Updated baseline")
    target_value: Optional[str] = Field(None, max_length=100, description="Updated target")
    current_value: Optional[str] = Field(None, max_length=100, description="Updated current value")
    target_date: Optional[date] = Field(None, description="Updated target date")
    status: Optional[GoalStatus] = Field(None, description="Updated status")
    progress_percentage: Optional[int] = Field(None, ge=0, le=100, description="Updated progress (0-100)")
    priority: Optional[int] = Field(None, ge=1, le=10, description="Updated priority")


class GoalResponse(GoalBase):
    """Complete goal data returned by API"""
    id: UUID = Field(..., description="Unique goal identifier")
    plan_id: UUID = Field(..., description="Associated treatment plan ID")
    parent_goal_id: Optional[UUID] = Field(None, description="Parent goal ID (for hierarchies)")
    current_value: Optional[str] = Field(None, max_length=100, description="Current progress value")
    status: GoalStatus = Field(default=GoalStatus.not_started, description="Current goal status")
    progress_percentage: int = Field(default=0, ge=0, le=100, description="Progress percentage (0-100)")
    created_at: datetime = Field(..., description="Goal creation timestamp")
    updated_at: datetime = Field(..., description="Goal last update timestamp")

    # Optional nested sub-goals and interventions
    sub_goals: Optional[List['GoalResponse']] = Field(None, description="Child goals in hierarchy")
    interventions: Optional[List['InterventionResponse']] = Field(None, description="Linked interventions")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Intervention Schemas
# ============================================================================

class InterventionBase(BaseModel):
    """Base intervention fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Intervention name")
    description: Optional[str] = Field(None, description="Detailed description")
    modality: Optional[str] = Field(None, max_length=50, description="Therapy modality (e.g., CBT, DBT)")
    evidence_level: Optional[EvidenceLevel] = Field(None, description="Evidence strength")

    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not just whitespace"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Name cannot be empty')
        return v.strip()


class InterventionCreate(InterventionBase):
    """Request to create a custom intervention"""
    pass


class InterventionResponse(InterventionBase):
    """Complete intervention data returned by API"""
    id: UUID = Field(..., description="Unique intervention identifier")
    is_system: bool = Field(default=False, description="Whether this is a system intervention")
    created_by: Optional[UUID] = Field(None, description="Creator user ID (null for system interventions)")
    created_at: datetime = Field(..., description="Intervention creation timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Goal-Intervention Link Schemas
# ============================================================================

class GoalInterventionCreate(BaseModel):
    """Request to link an intervention to a goal"""
    intervention_id: UUID = Field(..., description="Intervention to link")
    frequency: Optional[str] = Field(None, max_length=50, description="How often to use (e.g., 'every session')")
    notes: Optional[str] = Field(None, description="Notes about this intervention usage")


class GoalInterventionUpdate(BaseModel):
    """Request to update goal-intervention link"""
    frequency: Optional[str] = Field(None, max_length=50, description="Updated frequency")
    notes: Optional[str] = Field(None, description="Updated notes")
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5, description="Effectiveness rating (1-5)")


class GoalInterventionResponse(BaseModel):
    """Goal-intervention link data returned by API"""
    id: UUID = Field(..., description="Unique link identifier")
    goal_id: UUID = Field(..., description="Associated goal ID")
    intervention_id: UUID = Field(..., description="Associated intervention ID")
    frequency: Optional[str] = Field(None, description="Usage frequency")
    notes: Optional[str] = Field(None, description="Notes about usage")
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5, description="Effectiveness rating (1-5)")
    created_at: datetime = Field(..., description="Link creation timestamp")

    # Optional nested intervention details
    intervention: Optional[InterventionResponse] = Field(None, description="Full intervention details")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Goal Progress Schemas
# ============================================================================

class GoalProgressCreate(BaseModel):
    """Request to record goal progress"""
    progress_note: str = Field(..., min_length=1, description="Progress description")
    progress_value: Optional[str] = Field(None, max_length=100, description="Measurable progress value")
    rating: int = Field(..., ge=1, le=10, description="Progress rating (1-10)")
    session_id: Optional[UUID] = Field(None, description="Associated session ID (optional)")

    @field_validator('progress_note')
    @classmethod
    def validate_progress_note_not_empty(cls, v: str) -> str:
        """Ensure progress note is not just whitespace"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Progress note cannot be empty')
        return v.strip()


class GoalProgressResponse(BaseModel):
    """Goal progress entry data returned by API"""
    id: UUID = Field(..., description="Unique progress entry identifier")
    goal_id: UUID = Field(..., description="Associated goal ID")
    session_id: Optional[UUID] = Field(None, description="Associated session ID")
    progress_note: str = Field(..., description="Progress description")
    progress_value: Optional[str] = Field(None, description="Measurable progress value")
    rating: int = Field(..., ge=1, le=10, description="Progress rating (1-10)")
    recorded_by: UUID = Field(..., description="User ID who recorded this progress")
    recorded_at: datetime = Field(..., description="When progress was recorded")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Plan Review Schemas
# ============================================================================

class PlanReviewCreate(BaseModel):
    """Request to create a plan review"""
    review_date: date = Field(..., description="Date of review")
    summary: str = Field(..., min_length=1, description="Review summary")
    goals_reviewed: int = Field(..., ge=0, description="Number of goals reviewed")
    goals_on_track: int = Field(..., ge=0, description="Number of goals on track")
    modifications_made: Optional[str] = Field(None, description="Modifications made to plan")
    next_review_date: Optional[date] = Field(None, description="Next scheduled review date")

    @field_validator('summary')
    @classmethod
    def validate_summary_not_empty(cls, v: str) -> str:
        """Ensure summary is not just whitespace"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Summary cannot be empty')
        return v.strip()

    @field_validator('goals_on_track')
    @classmethod
    def validate_goals_on_track_not_exceeds_reviewed(cls, v: int, info) -> int:
        """Ensure goals_on_track doesn't exceed goals_reviewed"""
        goals_reviewed = info.data.get('goals_reviewed')
        if goals_reviewed is not None and v > goals_reviewed:
            raise ValueError('goals_on_track cannot exceed goals_reviewed')
        return v

    @field_validator('next_review_date')
    @classmethod
    def validate_next_review_after_current(cls, v: Optional[date], info) -> Optional[date]:
        """Ensure next_review_date is after review_date"""
        if v is not None:
            review_date = info.data.get('review_date')
            if review_date and v <= review_date:
                raise ValueError('next_review_date must be after review_date')
        return v


class PlanReviewResponse(BaseModel):
    """Plan review data returned by API"""
    id: UUID = Field(..., description="Unique review identifier")
    plan_id: UUID = Field(..., description="Associated treatment plan ID")
    review_date: date = Field(..., description="Date of review")
    reviewer_id: UUID = Field(..., description="User ID who conducted review")
    summary: str = Field(..., description="Review summary")
    goals_reviewed: int = Field(..., ge=0, description="Number of goals reviewed")
    goals_on_track: int = Field(..., ge=0, description="Number of goals on track")
    modifications_made: Optional[str] = Field(None, description="Modifications made to plan")
    next_review_date: Optional[date] = Field(None, description="Next scheduled review date")
    created_at: datetime = Field(..., description="Review creation timestamp")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Nested/Composite Schemas
# ============================================================================

class GoalWithInterventions(GoalResponse):
    """Goal with full intervention details (not just IDs)"""
    interventions: List[InterventionResponse] = Field(
        default_factory=list,
        description="Full intervention details linked to this goal"
    )


class ProgressSummary(BaseModel):
    """Progress summary for a treatment plan"""
    total_goals: int = Field(..., description="Total number of goals")
    achieved: int = Field(..., description="Number of achieved goals")
    in_progress: int = Field(..., description="Number of in-progress goals")
    not_started: int = Field(..., description="Number of not-started goals")
    modified: int = Field(default=0, description="Number of modified goals")
    discontinued: int = Field(default=0, description="Number of discontinued goals")
    overall_progress: int = Field(..., ge=0, le=100, description="Overall progress percentage (0-100)")


class PlanWithGoalsResponse(TreatmentPlanResponse):
    """Full treatment plan with nested goals and progress summary"""
    goals: List[GoalWithInterventions] = Field(
        default_factory=list,
        description="All goals with interventions"
    )
    progress_summary: ProgressSummary = Field(..., description="Overall progress metrics")


# ============================================================================
# List/Filter Schemas
# ============================================================================

class TreatmentPlanListItem(BaseModel):
    """Minimal plan data for list views"""
    id: UUID = Field(..., description="Unique plan identifier")
    patient_id: UUID = Field(..., description="Associated patient ID")
    title: str = Field(..., description="Plan title")
    status: PlanStatus = Field(..., description="Current plan status")
    start_date: date = Field(..., description="Plan start date")
    target_end_date: Optional[date] = Field(None, description="Target completion date")
    next_review_date: Optional[date] = Field(None, description="Next scheduled review date")
    goal_count: int = Field(default=0, description="Number of goals in plan")
    overall_progress: int = Field(default=0, ge=0, le=100, description="Overall progress percentage")
    created_at: datetime = Field(..., description="Plan creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class InterventionListItem(BaseModel):
    """Minimal intervention data for list views"""
    id: UUID = Field(..., description="Unique intervention identifier")
    name: str = Field(..., description="Intervention name")
    modality: Optional[str] = Field(None, description="Therapy modality")
    evidence_level: Optional[EvidenceLevel] = Field(None, description="Evidence strength")
    is_system: bool = Field(..., description="Whether this is a system intervention")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Update forward references for nested models
# ============================================================================

TreatmentPlanResponse.model_rebuild()
GoalResponse.model_rebuild()
GoalInterventionResponse.model_rebuild()
GoalWithInterventions.model_rebuild()
PlanWithGoalsResponse.model_rebuild()
