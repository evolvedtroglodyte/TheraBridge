"""
Treatment Plans endpoints for Feature 4
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import List
from datetime import date, timedelta

from app.database import get_db
from app.auth.dependencies import require_role, verify_treatment_plan_access
from app.models.db_models import User, TherapistPatient
from app.models.treatment_models import TreatmentPlan, TreatmentPlanGoal, PlanReview
from app.models.treatment_schemas import (
    TreatmentPlanCreate,
    TreatmentPlanUpdate,
    TreatmentPlanResponse,
    TreatmentPlanListItem,
    PlanWithGoalsResponse,
    PlanReviewCreate,
    PlanReviewResponse,
    ProgressSummary,
    GoalStatus,
    PlanStatus
)
from app.middleware.rate_limit import limiter

router = APIRouter()


async def verify_therapist_patient_access(
    therapist_id: UUID,
    patient_id: UUID,
    db: AsyncSession
) -> None:
    """
    Verify that therapist has access to patient.

    Args:
        therapist_id: UUID of the therapist
        patient_id: UUID of the patient
        db: AsyncSession database dependency

    Raises:
        HTTPException 403: If therapist does not have access to patient
        HTTPException 404: If patient not found
    """
    query = select(TherapistPatient).where(
        TherapistPatient.therapist_id == therapist_id,
        TherapistPatient.patient_id == patient_id,
        TherapistPatient.is_active == True
    )
    result = await db.execute(query)
    relationship = result.scalar_one_or_none()

    if not relationship:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied. Therapist does not have access to patient {patient_id}"
        )


def calculate_progress_summary(goals: List[TreatmentPlanGoal]) -> ProgressSummary:
    """
    Calculate progress summary from list of goals.

    Args:
        goals: List of TreatmentPlanGoal objects

    Returns:
        ProgressSummary: Calculated progress metrics
    """
    total_goals = len(goals)

    if total_goals == 0:
        return ProgressSummary(
            total_goals=0,
            achieved=0,
            in_progress=0,
            not_started=0,
            modified=0,
            discontinued=0,
            overall_progress=0
        )

    # Count goals by status
    achieved = sum(1 for g in goals if g.status == GoalStatus.achieved)
    in_progress = sum(1 for g in goals if g.status == GoalStatus.in_progress)
    not_started = sum(1 for g in goals if g.status == GoalStatus.not_started)
    modified = sum(1 for g in goals if g.status == GoalStatus.modified)
    discontinued = sum(1 for g in goals if g.status == GoalStatus.discontinued)

    # Calculate overall progress percentage (average of all goal progress percentages)
    total_progress = sum(g.progress_percentage for g in goals)
    overall_progress = round(total_progress / total_goals) if total_goals > 0 else 0

    return ProgressSummary(
        total_goals=total_goals,
        achieved=achieved,
        in_progress=in_progress,
        not_started=not_started,
        modified=modified,
        discontinued=discontinued,
        overall_progress=overall_progress
    )


@router.post("/patients/{patient_id}/treatment-plans", response_model=TreatmentPlanResponse)
@limiter.limit("20/minute")
async def create_treatment_plan(
    request: Request,
    patient_id: UUID,
    plan_data: TreatmentPlanCreate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new treatment plan for a patient.

    Creates a treatment plan with diagnosis codes, presenting problems, and timeline.
    Automatically calculates next_review_date from start_date + review_frequency_days.

    Auth:
        Requires therapist role
        Validates therapist has access to patient

    Rate Limit:
        20 requests per minute per IP address

    Args:
        patient_id: UUID of the patient to create plan for
        plan_data: TreatmentPlanCreate schema with plan details
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        TreatmentPlanResponse: The newly created treatment plan

    Raises:
        HTTPException 403: If therapist does not have access to patient
        HTTPException 404: If patient not found
        HTTPException 400: If validation fails
        HTTPException 429: Rate limit exceeded
    """
    # Verify therapist has access to patient
    await verify_therapist_patient_access(current_user.id, patient_id, db)

    # Calculate next review date
    next_review_date = plan_data.start_date + timedelta(days=plan_data.review_frequency_days)

    # Create treatment plan
    new_plan = TreatmentPlan(
        patient_id=patient_id,
        therapist_id=current_user.id,
        title=plan_data.title,
        diagnosis_codes=plan_data.diagnosis_codes,
        presenting_problems=plan_data.presenting_problems,
        start_date=plan_data.start_date,
        target_end_date=plan_data.target_end_date,
        review_frequency_days=plan_data.review_frequency_days,
        next_review_date=next_review_date,
        notes=plan_data.notes,
        status=PlanStatus.active,
        version=1
    )

    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)

    return TreatmentPlanResponse.model_validate(new_plan)


@router.get("/patients/{patient_id}/treatment-plans", response_model=List[TreatmentPlanListItem])
@limiter.limit("50/minute")
async def list_patient_treatment_plans(
    request: Request,
    patient_id: UUID,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    List all treatment plans for a patient.

    Returns minimal plan data suitable for list views, including goal counts
    and overall progress percentages.

    Auth:
        Requires therapist role
        Validates therapist has access to patient

    Rate Limit:
        50 requests per minute per IP address

    Args:
        patient_id: UUID of the patient to list plans for
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        List[TreatmentPlanListItem]: List of treatment plans with summary data

    Raises:
        HTTPException 403: If therapist does not have access to patient
        HTTPException 404: If patient not found
        HTTPException 429: Rate limit exceeded
    """
    # Verify therapist has access to patient
    await verify_therapist_patient_access(current_user.id, patient_id, db)

    # Query treatment plans with goals eagerly loaded
    query = select(TreatmentPlan).where(
        TreatmentPlan.patient_id == patient_id
    ).options(
        selectinload(TreatmentPlan.goals)
    ).order_by(TreatmentPlan.created_at.desc())

    result = await db.execute(query)
    plans = result.scalars().all()

    # Convert to list items with calculated fields
    list_items = []
    for plan in plans:
        goals = plan.goals or []
        progress_summary = calculate_progress_summary(goals)

        list_items.append(
            TreatmentPlanListItem(
                id=plan.id,
                patient_id=plan.patient_id,
                title=plan.title,
                status=plan.status,
                start_date=plan.start_date,
                target_end_date=plan.target_end_date,
                next_review_date=plan.next_review_date,
                goal_count=len(goals),
                overall_progress=progress_summary.overall_progress,
                created_at=plan.created_at
            )
        )

    return list_items


@router.get("/treatment-plans/{plan_id}", response_model=PlanWithGoalsResponse)
@limiter.limit("50/minute")
async def get_treatment_plan(
    request: Request,
    plan_id: UUID,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full treatment plan with goals and progress summary.

    Returns complete plan details including all goals with their interventions
    and a calculated progress summary showing goal status distribution and
    overall progress percentage.

    Auth:
        Requires therapist role
        Validates therapist owns plan via patient relationship

    Rate Limit:
        50 requests per minute per IP address

    Args:
        plan_id: UUID of the treatment plan to retrieve
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        PlanWithGoalsResponse: Full treatment plan with nested goals and progress summary

    Raises:
        HTTPException 404: If plan not found
        HTTPException 403: If therapist does not have access to plan
        HTTPException 429: Rate limit exceeded
    """
    # Load plan with goals and interventions
    query = select(TreatmentPlan).where(
        TreatmentPlan.id == plan_id
    ).options(
        selectinload(TreatmentPlan.goals).selectinload(TreatmentPlanGoal.interventions),
        selectinload(TreatmentPlan.goals).selectinload(TreatmentPlanGoal.sub_goals)
    )

    result = await db.execute(query)
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"Treatment plan {plan_id} not found")

    # Verify therapist has access
    await verify_therapist_patient_access(current_user.id, plan.patient_id, db)

    # Calculate progress summary
    goals = plan.goals or []
    progress_summary = calculate_progress_summary(goals)

    # Convert to response model
    plan_dict = {
        "id": plan.id,
        "patient_id": plan.patient_id,
        "therapist_id": plan.therapist_id,
        "title": plan.title,
        "diagnosis_codes": plan.diagnosis_codes,
        "presenting_problems": plan.presenting_problems,
        "start_date": plan.start_date,
        "target_end_date": plan.target_end_date,
        "review_frequency_days": plan.review_frequency_days,
        "notes": plan.notes,
        "status": plan.status,
        "version": plan.version,
        "next_review_date": plan.next_review_date,
        "actual_end_date": plan.actual_end_date,
        "created_at": plan.created_at,
        "updated_at": plan.updated_at,
        "goals": goals,
        "progress_summary": progress_summary
    }

    return PlanWithGoalsResponse(**plan_dict)


@router.put("/treatment-plans/{plan_id}", response_model=TreatmentPlanResponse)
@limiter.limit("20/minute")
async def update_treatment_plan(
    request: Request,
    plan_id: UUID,
    plan_update: TreatmentPlanUpdate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a treatment plan.

    Allows partial updates to plan fields. Increments version number when
    significant changes are made (title, diagnosis_codes, presenting_problems).

    Auth:
        Requires therapist role
        Validates therapist owns plan via patient relationship

    Rate Limit:
        20 requests per minute per IP address

    Args:
        plan_id: UUID of the treatment plan to update
        plan_update: TreatmentPlanUpdate schema with fields to update
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        TreatmentPlanResponse: Updated treatment plan

    Raises:
        HTTPException 404: If plan not found
        HTTPException 403: If therapist does not have access to plan
        HTTPException 400: If validation fails
        HTTPException 429: Rate limit exceeded
    """
    # Verify ownership and load plan
    plan = await verify_treatment_plan_access(plan_id, current_user.id, db)

    # Track if significant changes were made (warrant version increment)
    significant_changes = False

    # Update fields if provided
    update_data = plan_update.model_dump(exclude_unset=True)

    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")

    # Check for significant changes
    if any(field in update_data for field in ['title', 'diagnosis_codes', 'presenting_problems']):
        significant_changes = True

    # Apply updates
    for field, value in update_data.items():
        setattr(plan, field, value)

    # Increment version if significant changes
    if significant_changes:
        plan.version += 1

    await db.commit()
    await db.refresh(plan)

    return TreatmentPlanResponse.model_validate(plan)


@router.post("/treatment-plans/{plan_id}/review", response_model=PlanReviewResponse)
@limiter.limit("20/minute")
async def create_plan_review(
    request: Request,
    plan_id: UUID,
    review_data: PlanReviewCreate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Record a treatment plan review.

    Creates a review record tracking goals reviewed, goals on track, and any
    modifications made to the plan. Updates the plan's next_review_date if
    provided in the review data.

    Auth:
        Requires therapist role
        Validates therapist owns plan via patient relationship

    Rate Limit:
        20 requests per minute per IP address

    Args:
        plan_id: UUID of the treatment plan being reviewed
        review_data: PlanReviewCreate schema with review details
        current_user: Authenticated user (injected by require_role dependency)
        db: AsyncSession database dependency

    Returns:
        PlanReviewResponse: The newly created plan review

    Raises:
        HTTPException 404: If plan not found
        HTTPException 403: If therapist does not have access to plan
        HTTPException 400: If validation fails (e.g., goals_on_track > goals_reviewed)
        HTTPException 429: Rate limit exceeded
    """
    # Verify ownership and load plan
    plan = await verify_treatment_plan_access(plan_id, current_user.id, db)

    # Create review record
    new_review = PlanReview(
        plan_id=plan_id,
        reviewer_id=current_user.id,
        review_date=review_data.review_date,
        summary=review_data.summary,
        goals_reviewed=review_data.goals_reviewed,
        goals_on_track=review_data.goals_on_track,
        modifications_made=review_data.modifications_made,
        next_review_date=review_data.next_review_date
    )

    db.add(new_review)

    # Update plan's next_review_date if provided
    if review_data.next_review_date:
        plan.next_review_date = review_data.next_review_date

    await db.commit()
    await db.refresh(new_review)

    return PlanReviewResponse.model_validate(new_review)
