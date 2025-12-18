"""
Pydantic schemas for progress reports and patient check-ins
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, List
from datetime import date as date_type, datetime
from uuid import UUID
from enum import Enum


# Request Schemas
class ReportFormat(str, Enum):
    """Progress report output format"""
    json = "json"
    pdf = "pdf"


class ProgressReportRequest(BaseModel):
    """Schema for requesting a progress report"""
    start_date: date_type = Field(..., description="Report period start date")
    end_date: date_type = Field(..., description="Report period end date")
    format: ReportFormat = Field(
        default=ReportFormat.json,
        description="Output format (json or pdf)"
    )

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: date_type, info) -> date_type:
        """Ensure end_date is after start_date"""
        if 'start_date' in info.data and v < info.data['start_date']:
            raise ValueError("end_date must be after start_date")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-03-10",
                "format": "json"
            }
        }
    )


class GoalCheckInItem(BaseModel):
    """Single goal progress entry in self-report check-in"""
    goal_id: UUID
    value: float = Field(..., description="Progress value (numeric)")
    notes: Optional[str] = Field(default=None, max_length=500)


class SelfReportCheckIn(BaseModel):
    """Schema for patient self-report check-in"""
    check_in_date: date_type = Field(..., description="Date of check-in")
    goals: List[GoalCheckInItem] = Field(
        ...,
        min_length=1,
        description="Progress updates for tracked goals"
    )
    general_mood: int = Field(
        ...,
        ge=1,
        le=10,
        description="Overall mood rating (1-10 scale)"
    )
    additional_notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional free-text notes"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "check_in_date": "2024-03-10",
                "goals": [
                    {
                        "goal_id": "550e8400-e29b-41d4-a716-446655440000",
                        "value": 4,
                        "notes": "Better day today"
                    },
                    {
                        "goal_id": "550e8400-e29b-41d4-a716-446655440001",
                        "value": 1,
                        "notes": "Completed my homework"
                    }
                ],
                "general_mood": 6,
                "additional_notes": "Feeling more optimistic this week"
            }
        }
    )


# Response Schemas
class ReportPeriod(BaseModel):
    """Report time period"""
    start: date_type
    end: date_type


class PatientSummary(BaseModel):
    """Patient treatment summary for report"""
    name: str
    treatment_start: date_type
    sessions_attended: int = Field(..., ge=0)
    sessions_missed: int = Field(..., ge=0)


class GoalStatus(str, Enum):
    """Goal progress status categories"""
    significant_improvement = "significant_improvement"
    improvement = "improvement"
    stable = "stable"
    decline = "decline"


class GoalSummaryItem(BaseModel):
    """Summary of a single goal's progress"""
    goal: str = Field(..., description="Goal description")
    baseline: float = Field(..., description="Starting value")
    current: float = Field(..., description="Most recent value")
    change: float = Field(..., description="Absolute change from baseline")
    change_percentage: float = Field(..., description="Percentage change from baseline")
    status: GoalStatus = Field(..., description="Overall progress status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "goal": "Reduce anxiety levels",
                "baseline": 8.0,
                "current": 4.0,
                "change": -4.0,
                "change_percentage": -50.0,
                "status": "significant_improvement"
            }
        }
    )


class AssessmentChange(BaseModel):
    """Assessment score change over report period"""
    baseline: int = Field(..., description="Score at report start")
    current: int = Field(..., description="Score at report end")
    change: int = Field(..., description="Absolute change")
    interpretation: str = Field(
        ...,
        description="Clinical interpretation of change",
        max_length=500
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "baseline": 14,
                "current": 8,
                "change": -6,
                "interpretation": "Moved from moderate to mild anxiety"
            }
        }
    )


class ProgressReportResponse(BaseModel):
    """Complete progress report response"""
    report_period: ReportPeriod
    patient_summary: PatientSummary
    goals_summary: List[GoalSummaryItem]
    assessment_summary: Dict[str, AssessmentChange] = Field(
        ...,
        description="Assessment changes by type, e.g., {'GAD-7': {...}, 'PHQ-9': {...}}"
    )
    clinical_observations: str = Field(
        ...,
        description="Clinician's observations and analysis",
        max_length=2000
    )
    recommendations: str = Field(
        ...,
        description="Treatment recommendations",
        max_length=2000
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "report_period": {
                    "start": "2024-01-01",
                    "end": "2024-03-10"
                },
                "patient_summary": {
                    "name": "John Doe",
                    "treatment_start": "2024-01-10",
                    "sessions_attended": 10,
                    "sessions_missed": 1
                },
                "goals_summary": [
                    {
                        "goal": "Reduce anxiety levels",
                        "baseline": 8.0,
                        "current": 4.0,
                        "change": -4.0,
                        "change_percentage": -50.0,
                        "status": "significant_improvement"
                    }
                ],
                "assessment_summary": {
                    "GAD-7": {
                        "baseline": 14,
                        "current": 8,
                        "change": -6,
                        "interpretation": "Moved from moderate to mild anxiety"
                    }
                },
                "clinical_observations": "Patient has shown consistent engagement...",
                "recommendations": "Continue current treatment approach..."
            }
        }
    )


# Milestone Schemas
class MilestoneResponse(BaseModel):
    """Recent milestone achievement"""
    date: date_type = Field(..., description="Date milestone was achieved")
    goal: str = Field(..., description="Goal description")
    milestone: str = Field(..., description="Milestone title/description")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "date": "2024-03-08",
                "goal": "Reduce anxiety levels",
                "milestone": "50% improvement from baseline"
            }
        }
    )


class AssessmentDueItem(BaseModel):
    """Assessment due for administration"""
    type: str = Field(..., description="Assessment type (e.g., GAD-7, PHQ-9)")
    last_administered: Optional[date_type] = Field(
        None,
        description="Date of last administration"
    )
    due_date: date_type = Field(..., description="Date assessment is due")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "type": "GAD-7",
                "last_administered": "2024-02-10",
                "due_date": "2024-03-10"
            }
        }
    )
