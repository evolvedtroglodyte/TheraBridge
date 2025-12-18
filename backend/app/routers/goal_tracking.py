"""
Goal tracking endpoints for treatment goal management and progress monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from typing import List, Optional
from datetime import date as date_type

from app.database import get_db
from app.auth.dependencies import require_role
from app.models.db_models import User, TherapistPatient
from app.models.goal_models import TreatmentGoal
from app.schemas.tracking_schemas import (
    TrackingConfigCreate,
    TrackingConfigResponse,
    ProgressEntryCreate,
    ProgressEntryResponse,
    ProgressHistoryQuery,
    ProgressHistoryResponse,
    GoalDashboardResponse,
    TreatmentGoalCreate,
    TreatmentGoalResponse,
    GoalStatus,
    AggregationPeriod
)
from app.services import tracking_service, dashboard_service
from app.middleware.rate_limit import limiter

router = APIRouter()


@router.post("/goals/{goal_id}/tracking/config", response_model=TrackingConfigResponse)
@limiter.limit("20/minute")
async def create_goal_tracking_config(
    request: Request,
    goal_id: UUID,
    config_data: TrackingConfigCreate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Configure tracking method for a goal.

    Sets up how progress will be tracked for a specific goal including:
    - Tracking method (scale, frequency, duration, binary, assessment)
    - Tracking frequency (daily, weekly, session, custom)
    - Scale ranges and labels (if using scale method)
    - Units (if using frequency or duration method)
    - Target direction (increase, decrease, maintain)
    - Reminder settings

    Auth:
        Requires therapist role

    Rate Limit:
        20 requests per minute per IP address

    Args:
        goal_id: UUID of the goal to configure tracking for
        config_data: TrackingConfigCreate schema with configuration details
        current_user: Authenticated therapist user
        db: AsyncSession database dependency

    Returns:
        TrackingConfigResponse: Created/updated tracking configuration

    Raises:
        HTTPException 403: If user is not a therapist
        HTTPException 404: If goal not found
        HTTPException 400: If tracking method requirements not met (e.g., missing scale_min/max)
        HTTPException 429: Rate limit exceeded

    Example Request:
        POST /goals/{goal_id}/tracking/config
        {
            "tracking_method": "scale",
            "tracking_frequency": "daily",
            "scale_min": 1,
            "scale_max": 10,
            "target_direction": "decrease",
            "reminder_enabled": true
        }
    """
    return await tracking_service.create_tracking_config(
        goal_id=goal_id,
        config_data=config_data,
        db=db
    )


@router.post("/goals/{goal_id}/progress", response_model=ProgressEntryResponse)
@limiter.limit("50/minute")
async def record_progress(
    request: Request,
    goal_id: UUID,
    entry_data: ProgressEntryCreate,
    current_user: User = Depends(require_role(["therapist", "patient"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Record a progress entry for a goal.

    Creates a new progress data point with value, date, time, notes, and context.
    Validates that the goal exists and belongs to the current user (patient) or
    their assigned therapist.

    Auth:
        Requires therapist or patient role
        Data isolation: Goal must belong to current user or their therapist

    Rate Limit:
        50 requests per minute per IP address

    Args:
        goal_id: UUID of the goal to record progress for
        entry_data: ProgressEntryCreate schema with entry details
        current_user: Authenticated user (therapist or patient)
        db: AsyncSession database dependency

    Returns:
        ProgressEntryResponse: Created progress entry

    Raises:
        HTTPException 403: If user not authorized to record progress for this goal
        HTTPException 404: If goal or tracking config not found
        HTTPException 400: If entry date is in future or value out of range
        HTTPException 429: Rate limit exceeded

    Data Isolation:
        - Patients: Can only record progress for their own goals
        - Therapists: Can only record progress for goals of assigned patients

    Example Request:
        POST /goals/{goal_id}/progress
        {
            "entry_date": "2025-12-17",
            "entry_time": "14:30:00",
            "value": 7.5,
            "value_label": "Better today",
            "notes": "Feeling much more in control",
            "context": "self_report"
        }
    """
    # Verify goal exists and user has access
    goal_query = select(TreatmentGoal).where(TreatmentGoal.id == goal_id)
    goal_result = await db.execute(goal_query)
    goal = goal_result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=404,
            detail=f"Goal with id {goal_id} not found"
        )

    # Data isolation check
    if current_user.role.value == "patient":
        # Patients can only record progress for their own goals
        if goal.patient_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to record progress for this goal"
            )
    elif current_user.role.value == "therapist":
        # Therapists can only record progress for goals of assigned patients
        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == goal.patient_id,
                TherapistPatient.is_active == True
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to record progress for this patient's goal"
            )

    return await tracking_service.record_progress_entry(
        goal_id=goal_id,
        entry_data=entry_data,
        recorded_by_id=current_user.id,
        db=db
    )


@router.get("/goals/{goal_id}/progress", response_model=ProgressHistoryResponse)
@limiter.limit("100/minute")
async def get_goal_progress_history(
    request: Request,
    goal_id: UUID,
    start_date: Optional[date_type] = Query(None, description="Start date for filtering entries"),
    end_date: Optional[date_type] = Query(None, description="End date for filtering entries"),
    aggregation: Optional[AggregationPeriod] = Query(None, description="Period for aggregating data (none, daily, weekly, monthly)"),
    current_user: User = Depends(require_role(["therapist", "patient"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get progress history for a goal with filtering and aggregation.

    Retrieves all progress entries for a goal, optionally filtered by date range
    and aggregated by period (daily, weekly, monthly). Includes statistical summary
    with average, min, max, trend slope, and trend direction.

    Auth:
        Requires therapist or patient role
        Data isolation: Goal must belong to current user or their therapist

    Rate Limit:
        100 requests per minute per IP address

    Query Parameters:
        - start_date: Include only entries on or after this date (ISO 8601 format)
        - end_date: Include only entries on or before this date (ISO 8601 format)
        - aggregation: Group entries by period (none, daily, weekly, monthly)

    Args:
        goal_id: UUID of the goal to retrieve history for
        start_date: Optional start date filter
        end_date: Optional end date filter
        aggregation: Optional aggregation period
        current_user: Authenticated user (therapist or patient)
        db: AsyncSession database dependency

    Returns:
        ProgressHistoryResponse: Progress entries and statistical summary

    Raises:
        HTTPException 403: If user not authorized to view this goal's progress
        HTTPException 404: If goal not found
        HTTPException 429: Rate limit exceeded

    Data Isolation:
        - Patients: Can only view progress for their own goals
        - Therapists: Can only view progress for goals of assigned patients

    Example Request:
        GET /goals/{goal_id}/progress?start_date=2025-11-01&end_date=2025-12-17&aggregation=weekly
    """
    # Verify goal exists and user has access
    goal_query = select(TreatmentGoal).where(TreatmentGoal.id == goal_id)
    goal_result = await db.execute(goal_query)
    goal = goal_result.scalar_one_or_none()

    if not goal:
        raise HTTPException(
            status_code=404,
            detail=f"Goal with id {goal_id} not found"
        )

    # Data isolation check
    if current_user.role.value == "patient":
        # Patients can only view progress for their own goals
        if goal.patient_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view progress for this goal"
            )
    elif current_user.role.value == "therapist":
        # Therapists can only view progress for goals of assigned patients
        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == goal.patient_id,
                TherapistPatient.is_active == True
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this patient's goal progress"
            )

    # Build query parameters
    query_params = ProgressHistoryQuery(
        start_date=start_date,
        end_date=end_date,
        aggregation=aggregation
    )

    return await tracking_service.get_progress_history(
        goal_id=goal_id,
        query_params=query_params,
        db=db
    )


@router.get("/patients/{patient_id}/goals/dashboard", response_model=GoalDashboardResponse)
@limiter.limit("50/minute")
async def get_patient_goal_dashboard(
    request: Request,
    patient_id: UUID,
    current_user: User = Depends(require_role(["therapist", "patient"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete goal tracking dashboard for a patient.

    Aggregates data from multiple sources including:
    - Active goals count
    - Tracking activity summary (entries this week, streak days, completion rate)
    - Per-goal dashboard items with progress metrics and trends
    - Recent milestones achieved (last 30 days)
    - Assessments due for administration

    Auth:
        Requires therapist or patient role
        Data isolation: Therapist must have access to patient, or patient must be current user

    Rate Limit:
        50 requests per minute per IP address

    Args:
        patient_id: UUID of the patient to retrieve dashboard for
        current_user: Authenticated user (therapist or patient)
        db: AsyncSession database dependency

    Returns:
        GoalDashboardResponse: Complete dashboard with all goal tracking data

    Raises:
        HTTPException 403: If user not authorized to view this patient's dashboard
        HTTPException 404: If patient not found
        HTTPException 429: Rate limit exceeded

    Data Isolation:
        - Patients: Can only view their own dashboard
        - Therapists: Can only view dashboards of assigned patients

    Example Response:
        {
            "patient_id": "uuid",
            "active_goals": 3,
            "tracking_summary": {
                "entries_this_week": 12,
                "streak_days": 7,
                "completion_rate": 85.7
            },
            "goals": [...],
            "recent_milestones": [...],
            "assessments_due": [...]
        }
    """
    # Data isolation check
    if current_user.role.value == "patient":
        # Patients can only view their own dashboard
        if patient_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Patients can only view their own goal dashboard"
            )
    elif current_user.role.value == "therapist":
        # Therapists can only view dashboards of assigned patients
        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == patient_id,
                TherapistPatient.is_active == True
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this patient's goal dashboard"
            )

    return await dashboard_service.get_goal_dashboard(
        patient_id=patient_id,
        db=db
    )


@router.post("/patients/{patient_id}/goals", response_model=TreatmentGoalResponse)
@limiter.limit("20/minute")
async def create_treatment_goal(
    request: Request,
    patient_id: UUID,
    goal_data: TreatmentGoalCreate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new treatment goal for a patient.

    Creates a goal record with description, category, baseline/target values,
    and target date. Goals are initially assigned status 'assigned' and can be
    updated to 'in_progress', 'completed', or 'abandoned' later.

    Auth:
        Requires therapist role

    Rate Limit:
        20 requests per minute per IP address

    Args:
        patient_id: UUID of the patient to create goal for
        goal_data: TreatmentGoalCreate schema with goal details
        current_user: Authenticated therapist user
        db: AsyncSession database dependency

    Returns:
        TreatmentGoalResponse: Created treatment goal

    Raises:
        HTTPException 403: If user is not a therapist
        HTTPException 404: If patient not found
        HTTPException 400: If validation fails (e.g., target date in past)
        HTTPException 429: Rate limit exceeded

    Example Request:
        POST /patients/{patient_id}/goals
        {
            "description": "Reduce anxiety symptoms to manageable levels",
            "category": "Anxiety management",
            "baseline_value": 8.5,
            "target_value": 3.0,
            "target_date": "2026-03-15"
        }
    """
    # Verify patient exists
    patient_query = select(User).where(
        and_(
            User.id == patient_id,
            User.role == "patient"
        )
    )
    patient_result = await db.execute(patient_query)
    patient = patient_result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient with id {patient_id} not found"
        )

    # Create treatment goal
    new_goal = TreatmentGoal(
        patient_id=patient_id,
        therapist_id=current_user.id,
        description=goal_data.description,
        category=goal_data.category,
        baseline_value=goal_data.baseline_value,
        target_value=goal_data.target_value,
        target_date=goal_data.target_date,
        status='assigned'
    )

    db.add(new_goal)
    await db.commit()
    await db.refresh(new_goal)

    return TreatmentGoalResponse.model_validate(new_goal)


@router.get("/patients/{patient_id}/goals", response_model=List[TreatmentGoalResponse])
@limiter.limit("100/minute")
async def list_patient_goals(
    request: Request,
    patient_id: UUID,
    status: Optional[GoalStatus] = Query(None, description="Filter by goal status (assigned, in_progress, completed, abandoned)"),
    current_user: User = Depends(require_role(["therapist", "patient"])),
    db: AsyncSession = Depends(get_db)
):
    """
    List all treatment goals for a patient with optional status filtering.

    Retrieves goals ordered by creation date (newest first). Can be filtered
    by status to show only assigned, in_progress, completed, or abandoned goals.

    Auth:
        Requires therapist or patient role
        Data isolation: Therapist must have access to patient, or patient must be current user

    Rate Limit:
        100 requests per minute per IP address

    Query Parameters:
        - status: Optional filter by goal status (assigned, in_progress, completed, abandoned)

    Args:
        patient_id: UUID of the patient to list goals for
        status: Optional GoalStatus filter
        current_user: Authenticated user (therapist or patient)
        db: AsyncSession database dependency

    Returns:
        List[TreatmentGoalResponse]: List of treatment goals matching filters

    Raises:
        HTTPException 403: If user not authorized to view this patient's goals
        HTTPException 404: If patient not found
        HTTPException 429: Rate limit exceeded

    Data Isolation:
        - Patients: Can only view their own goals
        - Therapists: Can only view goals of assigned patients

    Example Request:
        GET /patients/{patient_id}/goals
        GET /patients/{patient_id}/goals?status=in_progress
    """
    # Data isolation check
    if current_user.role.value == "patient":
        # Patients can only view their own goals
        if patient_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Patients can only view their own goals"
            )
    elif current_user.role.value == "therapist":
        # Therapists can only view goals of assigned patients
        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == patient_id,
                TherapistPatient.is_active == True
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this patient's goals"
            )

    # Build query
    query = select(TreatmentGoal).where(
        TreatmentGoal.patient_id == patient_id
    ).order_by(TreatmentGoal.created_at.desc())

    # Apply status filter if provided
    if status:
        query = query.where(TreatmentGoal.status == status.value)

    # Execute query
    result = await db.execute(query)
    goals = result.scalars().all()

    return [TreatmentGoalResponse.model_validate(goal) for goal in goals]
