"""
Patient self-report endpoints for goal tracking check-ins.
Allows patients to submit progress updates and view their trackable goals.
Feature 6 - Goal Tracking (Wave 3).
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from typing import List, Dict, Any

from app.database import get_db
from app.auth.dependencies import require_role
from app.models.db_models import User
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import GoalTrackingConfig
from app.schemas.report_schemas import SelfReportCheckIn, GoalCheckInItem
from app.schemas.tracking_schemas import ProgressEntryCreate
from app.services.tracking_service import record_progress_entry
from app.middleware.rate_limit import limiter

router = APIRouter()


@router.post("/check-in")
@limiter.limit("20/minute")
async def submit_check_in(
    request: Request,
    check_in: SelfReportCheckIn,
    current_user: User = Depends(require_role(["patient"])),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Submit patient self-report check-in with progress updates for multiple goals.

    **Patient-only endpoint.** Records progress entries for all goals in check-in.
    Auto-filters to current user's goals only for security.

    Args:
        request: FastAPI request (required for rate limiter)
        check_in: SelfReportCheckIn with check-in date, goals, mood, and notes
        current_user: Authenticated patient user (auto-injected)
        db: Database session (auto-injected)

    Returns:
        Dict with success message and count of entries created

    Raises:
        HTTPException 400: If any goal_id doesn't belong to current patient
        HTTPException 404: If any goal has no tracking configuration
        HTTPException 500: Database error during transaction

    Validation:
        - All goal_ids must belong to current patient
        - All goals must have tracking configurations
        - Check-in date cannot be in future (handled by tracking_service)
        - Values must be within configured scale ranges (handled by tracking_service)

    Example Request:
        POST /self-report/check-in
        {
            "check_in_date": "2024-03-10",
            "goals": [
                {"goal_id": "uuid1", "value": 7.5, "notes": "Better today"},
                {"goal_id": "uuid2", "value": 3, "notes": "Completed exercise"}
            ],
            "general_mood": 6,
            "additional_notes": "Feeling more optimistic"
        }

    Example Response:
        {
            "message": "Check-in recorded successfully",
            "entries_created": 2
        }
    """
    # Extract all goal IDs from check-in
    goal_ids = [item.goal_id for item in check_in.goals]

    # 1. Validate all goals belong to current patient
    goals_query = select(TreatmentGoal).where(
        and_(
            TreatmentGoal.id.in_(goal_ids),
            TreatmentGoal.patient_id == current_user.id
        )
    )
    result = await db.execute(goals_query)
    valid_goals = result.scalars().all()

    # Check if any goal_ids were invalid (don't belong to patient)
    valid_goal_ids = {goal.id for goal in valid_goals}
    invalid_goal_ids = set(goal_ids) - valid_goal_ids

    if invalid_goal_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid goal IDs or goals do not belong to you: {[str(gid) for gid in invalid_goal_ids]}"
        )

    # 2. Record progress entry for each goal
    entries_created = 0
    errors = []

    try:
        for goal_item in check_in.goals:
            # Create progress entry using tracking service
            entry_data = ProgressEntryCreate(
                entry_date=check_in.check_in_date,
                entry_time=None,  # Patient check-ins don't require specific time
                value=goal_item.value,
                value_label=None,  # Optional, can be populated by service
                notes=goal_item.notes,
                context="self_report"  # Always self_report for this endpoint
            )

            # Call tracking service to record entry
            # This handles validation (scale range, tracking config exists, etc.)
            await record_progress_entry(
                goal_id=goal_item.goal_id,
                entry_data=entry_data,
                recorded_by_id=current_user.id,
                db=db
            )

            entries_created += 1

    except HTTPException as e:
        # Re-raise HTTP exceptions from tracking service
        await db.rollback()
        raise e
    except Exception as e:
        # Handle unexpected errors
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record check-in: {str(e)}"
        )

    # 3. Optionally store general mood and additional notes
    # TODO: Future enhancement - create a CheckIn table to store mood and notes
    # For now, we only record the goal progress entries

    return {
        "message": "Check-in recorded successfully",
        "entries_created": entries_created
    }


@router.get("/goals")
@limiter.limit("100/minute")
async def get_patient_trackable_goals(
    request: Request,
    current_user: User = Depends(require_role(["patient"])),
    db: AsyncSession = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get all trackable goals for current patient.

    **Patient-only endpoint.** Returns active/in-progress goals with their tracking
    configurations. Auto-filters to current patient only for security.

    Args:
        request: FastAPI request (required for rate limiter)
        current_user: Authenticated patient user (auto-injected)
        db: Database session (auto-injected)

    Returns:
        List of goals with tracking info, each containing:
        - goal_id: UUID
        - goal_description: str
        - status: str (assigned/in_progress)
        - baseline_value: float
        - target_value: float
        - tracking_method: str (scale/frequency/duration/binary/assessment)
        - tracking_frequency: str (daily/weekly/session)
        - scale_min: int (if scale method)
        - scale_max: int (if scale method)
        - target_direction: str (increase/decrease/maintain)

    Filters:
        - Only goals belonging to current patient
        - Only goals with status "assigned" or "in_progress"
        - Left joins tracking config (returns goals even without config)

    Example Response:
        [
            {
                "goal_id": "uuid1",
                "goal_description": "Reduce anxiety levels",
                "status": "in_progress",
                "baseline_value": 8.0,
                "target_value": 4.0,
                "tracking_method": "scale",
                "tracking_frequency": "daily",
                "scale_min": 1,
                "scale_max": 10,
                "target_direction": "decrease"
            },
            {
                "goal_id": "uuid2",
                "goal_description": "Practice mindfulness meditation",
                "status": "assigned",
                "baseline_value": 0,
                "target_value": 20,
                "tracking_method": "frequency",
                "tracking_frequency": "daily",
                "scale_min": null,
                "scale_max": null,
                "target_direction": "increase"
            }
        ]
    """
    # Query active goals for current patient with tracking configs
    query = select(TreatmentGoal, GoalTrackingConfig).outerjoin(
        GoalTrackingConfig,
        GoalTrackingConfig.goal_id == TreatmentGoal.id
    ).where(
        and_(
            TreatmentGoal.patient_id == current_user.id,
            TreatmentGoal.status.in_(["assigned", "in_progress"])
        )
    )

    result = await db.execute(query)
    rows = result.all()

    # Build response list
    goals_list = []
    for goal, config in rows:
        goal_data = {
            "goal_id": goal.id,
            "goal_description": goal.goal_description,
            "status": goal.status,
            "baseline_value": float(goal.baseline_value) if goal.baseline_value else None,
            "target_value": float(goal.target_value) if goal.target_value else None,
            "tracking_method": config.tracking_method if config else None,
            "tracking_frequency": config.tracking_frequency if config else None,
            "scale_min": config.scale_min if config else None,
            "scale_max": config.scale_max if config else None,
            "target_direction": config.target_direction if config else None
        }
        goals_list.append(goal_data)

    return goals_list
