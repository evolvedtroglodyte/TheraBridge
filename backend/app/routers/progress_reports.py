"""
Progress Report API Router

Provides endpoints for generating patient progress reports with:
- Treatment goal progress summaries
- Assessment score changes and interpretations
- Clinical observations and recommendations
- Patient treatment statistics

Therapist-only access with data isolation and rate limiting.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date as date_type, timedelta
from typing import Optional

from app.database import get_db
from app.auth.dependencies import require_role
from app.models.db_models import User, TherapistPatient
from app.schemas.report_schemas import (
    ProgressReportResponse,
    ReportFormat
)
from app.services.report_generator import generate_progress_report
from app.middleware.rate_limit import limiter

router = APIRouter(prefix="/progress-reports", tags=["Progress Reports"])


@router.get("/patients/{patient_id}/progress-report", response_model=ProgressReportResponse)
@limiter.limit("10/minute")
async def get_progress_report(
    request: Request,
    patient_id: UUID,
    start_date: date_type = Query(..., description="Report start date"),
    end_date: date_type = Query(..., description="Report end date"),
    format: ReportFormat = Query(ReportFormat.json, description="Report format (json or pdf)"),
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate comprehensive progress report for a patient over a date range.

    **Therapist-only endpoint** with data isolation checks.

    **Features:**
    - Treatment goal progress summaries with status categorization
    - Assessment score changes with clinical interpretations
    - Patient treatment statistics (sessions attended/missed)
    - Auto-generated clinical observations
    - Treatment recommendations

    **Validations:**
    - Patient must be assigned to requesting therapist
    - end_date must be after start_date
    - Date range cannot exceed 1 year

    **Rate Limit:** 10 requests per minute (intensive operation)

    **Query Parameters:**
    - start_date: Report period start date (YYYY-MM-DD)
    - end_date: Report period end date (YYYY-MM-DD)
    - format: Output format (json or pdf) - default: json

    **Response:**
    - JSON: ProgressReportResponse with complete report data
    - PDF: Not yet implemented (returns 501)

    **Example:**
    ```
    GET /progress-reports/patients/123e4567-e89b-12d3-a456-426614174000/progress-report?start_date=2024-01-01&end_date=2024-03-10&format=json
    ```

    **Status Codes:**
    - 200: Report generated successfully
    - 400: Invalid date range or validation error
    - 403: Patient not assigned to therapist or access denied
    - 404: Patient not found
    - 429: Rate limit exceeded
    - 501: PDF format not yet implemented
    """
    # Validate date range: end_date must be after start_date
    if end_date <= start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date"
        )

    # Validate date range: cannot exceed 1 year
    max_date_range = timedelta(days=365)
    if (end_date - start_date) > max_date_range:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Date range cannot exceed 1 year"
        )

    # Verify patient exists
    patient_query = select(User).where(User.id == patient_id)
    patient_result = await db.execute(patient_query)
    patient = patient_result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )

    # Data isolation: Verify patient is assigned to current therapist
    assignment_query = select(TherapistPatient).where(
        TherapistPatient.therapist_id == current_user.id,
        TherapistPatient.patient_id == patient_id,
        TherapistPatient.is_active == True
    )
    assignment_result = await db.execute(assignment_query)
    assignment = assignment_result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Patient {patient_id} is not assigned to you"
        )

    # PDF format placeholder
    if format == ReportFormat.pdf:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="PDF format not yet implemented. Use format=json"
        )

    # Generate progress report
    report = await generate_progress_report(
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )

    return report
