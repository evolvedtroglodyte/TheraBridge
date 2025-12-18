"""
Assessment endpoints for recording and tracking standardized assessments (Feature 6)
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from typing import Optional, List
from datetime import date

from app.database import get_db
from app.auth.dependencies import require_role
from app.models.db_models import User, TherapistPatient
from app.schemas.assessment_schemas import (
    AssessmentScoreCreate,
    AssessmentScoreResponse,
    AssessmentHistoryResponse
)
from app.schemas.report_schemas import AssessmentDueItem
from app.services.assessment_service import (
    record_assessment,
    get_assessment_history,
    check_assessments_due
)
from app.middleware.rate_limit import limiter

router = APIRouter()


@router.post("/patients/{patient_id}/assessments", response_model=AssessmentScoreResponse)
@limiter.limit("20/minute")
async def create_assessment_score(
    request: Request,
    patient_id: UUID,
    assessment_data: AssessmentScoreCreate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Record a new assessment score for a patient.

    Creates a new standardized assessment record (PHQ-9, GAD-7, BDI-II, BAI, PCL-5, AUDIT).
    Automatically calculates severity level based on score if not provided.

    Auth:
        Requires therapist role
        Validates patient is assigned to current therapist

    Rate Limit:
        20 requests per minute per IP address

    Args:
        patient_id: UUID of patient to record assessment for
        assessment_data: Assessment score data (type, score, administered_date, etc.)
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        AssessmentScoreResponse: Created assessment record with calculated severity

    Raises:
        HTTPException 403: If therapist does not have access to patient
        HTTPException 400: If assessment data is invalid
        HTTPException 429: Rate limit exceeded

    Example Request:
        POST /patients/{patient_id}/assessments
        {
            "assessment_type": "GAD-7",
            "score": 8,
            "administered_date": "2024-03-10",
            "notes": "Patient reports improvement"
        }
    """
    # Check therapist has access to patient
    access_query = select(TherapistPatient).where(
        and_(
            TherapistPatient.therapist_id == current_user.id,
            TherapistPatient.patient_id == patient_id,
            TherapistPatient.is_active == True
        )
    )
    result = await db.execute(access_query)
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail="Access denied: Patient not assigned to current therapist"
        )

    # Record the assessment
    return await record_assessment(
        patient_id=patient_id,
        assessment_data=assessment_data,
        db=db,
        administered_by=current_user.id
    )


@router.get("/patients/{patient_id}/assessments", response_model=AssessmentHistoryResponse)
@limiter.limit("100/minute")
async def get_patient_assessment_history(
    request: Request,
    patient_id: UUID,
    assessment_type: Optional[str] = Query(None, description="Filter by assessment type (e.g., 'GAD-7', 'PHQ-9')"),
    start_date: Optional[date] = Query(None, description="Filter from this date"),
    end_date: Optional[date] = Query(None, description="Filter to this date"),
    current_user: User = Depends(require_role(["therapist", "patient"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve assessment history for a patient.

    Returns all assessment scores for a patient, optionally filtered by:
    - Assessment type (PHQ-9, GAD-7, etc.)
    - Date range (start_date, end_date)

    Results are grouped by assessment type for trend visualization.

    Auth:
        Requires therapist or patient role
        Therapist: Must have patient assigned
        Patient: Can only access own data

    Rate Limit:
        100 requests per minute per IP address

    Args:
        patient_id: UUID of patient to retrieve history for
        assessment_type: Optional filter by assessment type
        start_date: Optional filter from this date
        end_date: Optional filter to this date
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        AssessmentHistoryResponse: Assessment history grouped by type

    Raises:
        HTTPException 403: If user does not have access to patient data
        HTTPException 404: If patient not found
        HTTPException 429: Rate limit exceeded

    Query Examples:
        GET /patients/{patient_id}/assessments - all assessments
        GET /patients/{patient_id}/assessments?assessment_type=GAD-7 - GAD-7 only
        GET /patients/{patient_id}/assessments?start_date=2024-01-01&end_date=2024-03-31 - Q1 2024
    """
    # Data isolation: Check access based on role
    if current_user.role.value == "therapist":
        # Therapist: verify patient is assigned
        access_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == patient_id,
                TherapistPatient.is_active == True
            )
        )
        result = await db.execute(access_query)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=403,
                detail="Access denied: Patient not assigned to current therapist"
            )
    elif current_user.role.value == "patient":
        # Patient: verify accessing own data
        if patient_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Patients can only access their own assessment history"
            )

    # Retrieve assessment history
    return await get_assessment_history(
        patient_id=patient_id,
        db=db,
        assessment_type=assessment_type,
        start_date=start_date,
        end_date=end_date
    )


@router.get("/patients/{patient_id}/assessments/due", response_model=List[AssessmentDueItem])
@limiter.limit("50/minute")
async def get_assessments_due(
    request: Request,
    patient_id: UUID,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Check which standardized assessments are due for a patient.

    Calculates which assessments need administration based on:
    - Last administration date
    - Recommended frequency (PHQ-9/GAD-7: 28 days, BDI-II/BAI: 30 days, AUDIT: 90 days)

    Useful for scheduling assessment administration and ensuring timely tracking.

    Auth:
        Requires therapist role
        Validates patient is assigned to current therapist

    Rate Limit:
        50 requests per minute per IP address

    Args:
        patient_id: UUID of patient to check assessments for
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        List[AssessmentDueItem]: Assessments that are due or overdue

    Raises:
        HTTPException 403: If therapist does not have access to patient
        HTTPException 404: If patient not found
        HTTPException 429: Rate limit exceeded

    Example Response:
        [
            {
                "type": "GAD-7",
                "last_administered": "2024-02-10",
                "due_date": "2024-03-10"
            },
            {
                "type": "PHQ-9",
                "last_administered": null,
                "due_date": "2024-03-10"
            }
        ]
    """
    # Check therapist has access to patient
    access_query = select(TherapistPatient).where(
        and_(
            TherapistPatient.therapist_id == current_user.id,
            TherapistPatient.patient_id == patient_id,
            TherapistPatient.is_active == True
        )
    )
    result = await db.execute(access_query)
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=403,
            detail="Access denied: Patient not assigned to current therapist"
        )

    # Check which assessments are due
    return await check_assessments_due(patient_id=patient_id, db=db)
