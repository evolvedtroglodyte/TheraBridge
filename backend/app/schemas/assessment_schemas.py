"""
Pydantic schemas for assessment scoring and tracking
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, List
from datetime import date as date_type, datetime
from uuid import UUID
from enum import Enum


class AssessmentType(str, Enum):
    """Standardized assessment types"""
    PHQ9 = "PHQ-9"
    GAD7 = "GAD-7"
    BDI2 = "BDI-II"
    BAI = "BAI"
    PCL5 = "PCL-5"
    AUDIT = "AUDIT"


class Severity(str, Enum):
    """Assessment severity levels"""
    minimal = "minimal"
    mild = "mild"
    moderate = "moderate"
    moderately_severe = "moderately_severe"
    severe = "severe"


# Request Schemas
class AssessmentScoreCreate(BaseModel):
    """Schema for creating a new assessment score"""
    assessment_type: AssessmentType
    score: int = Field(..., description="Total assessment score")
    severity: Optional[Severity] = None
    subscores: Optional[Dict[str, int]] = Field(
        default=None,
        description="Individual item scores, e.g., {'feeling_nervous': 2, 'cant_stop_worrying': 1}"
    )
    administered_date: date_type
    goal_id: Optional[UUID] = Field(
        default=None,
        description="Link assessment to a specific treatment goal"
    )
    notes: Optional[str] = Field(default=None, max_length=1000)

    @field_validator('score')
    @classmethod
    def validate_score_positive(cls, v: int) -> int:
        """Ensure score is non-negative"""
        if v < 0:
            raise ValueError("Score must be non-negative")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "assessment_type": "GAD-7",
                "score": 8,
                "severity": "mild",
                "subscores": {
                    "feeling_nervous": 2,
                    "cant_stop_worrying": 1,
                    "worrying_too_much": 2
                },
                "administered_date": "2024-03-10",
                "goal_id": "550e8400-e29b-41d4-a716-446655440000",
                "notes": "Patient reported improvement in worry frequency"
            }
        }
    )


# Response Schemas
class AssessmentScoreResponse(BaseModel):
    """Schema for assessment score responses"""
    id: UUID
    patient_id: UUID
    goal_id: Optional[UUID] = None
    assessment_type: AssessmentType
    score: int
    severity: Optional[Severity] = None
    subscores: Optional[Dict[str, int]] = None
    administered_date: date_type
    administered_by: Optional[UUID] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssessmentHistoryItem(BaseModel):
    """Single assessment data point for trend visualization"""
    date: date_type = Field(..., description="Date assessment was administered")
    score: int = Field(..., description="Total score")
    severity: Optional[Severity] = Field(None, description="Severity category")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "date": "2024-03-10",
                "score": 8,
                "severity": "mild"
            }
        }
    )


class AssessmentHistoryResponse(BaseModel):
    """Assessment history grouped by type"""
    assessments: Dict[AssessmentType, List[AssessmentHistoryItem]] = Field(
        ...,
        description="Assessment history grouped by type, e.g., {'GAD-7': [...], 'PHQ-9': [...]}"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "assessments": {
                    "GAD-7": [
                        {"date": "2024-01-10", "score": 14, "severity": "moderate"},
                        {"date": "2024-02-10", "score": 10, "severity": "moderate"},
                        {"date": "2024-03-10", "score": 8, "severity": "mild"}
                    ],
                    "PHQ-9": [
                        {"date": "2024-01-10", "score": 12, "severity": "moderate"},
                        {"date": "2024-03-10", "score": 7, "severity": "mild"}
                    ]
                }
            }
        }
    )
