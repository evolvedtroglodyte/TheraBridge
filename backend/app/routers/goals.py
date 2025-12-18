"""
Treatment goals endpoints with hierarchy support and progress tracking.
Implements Feature 4 Treatment Plans - Goals management.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, joinedload
from uuid import UUID
from typing import List

from app.database import get_db
from app.auth.dependencies import require_role
from app.models.db_models import User, TreatmentPlan, TreatmentGoal, GoalProgress, GoalIntervention, Intervention
from app.models.treatment_schemas import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalProgressCreate,
    GoalProgressResponse
)

router = APIRouter()


async def verify_plan_ownership(plan_id: UUID, therapist_id: UUID, db: AsyncSession) -> TreatmentPlan:
    """
    Verify that a therapist owns a treatment plan via patient relationship.

    Args:
        plan_id: Treatment plan ID to verify
        therapist_id: Therapist user ID
        db: Database session

    Returns:
        TreatmentPlan if ownership verified

    Raises:
        HTTPException 404: Plan not found
        HTTPException 403: Therapist not authorized for this plan
    """
    # Load plan with patient relationship
    result = await db.execute(
        select(TreatmentPlan)
        .options(joinedload(TreatmentPlan.patient))
        .where(TreatmentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()

    if not plan:
        raise HTTPException(status_code=404, detail=f"Treatment plan {plan_id} not found")

    # Verify therapist owns this plan
    if plan.therapist_id != therapist_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this treatment plan"
        )

    return plan


async def verify_goal_ownership(goal_id: UUID, therapist_id: UUID, db: AsyncSession) -> TreatmentGoal:
    """
    Verify that a therapist owns a goal via plan ownership.

    Args:
        goal_id: Goal ID to verify
        therapist_id: Therapist user ID
        db: Database session

    Returns:
        TreatmentGoal if ownership verified

    Raises:
        HTTPException 404: Goal not found
        HTTPException 403: Therapist not authorized for this goal
    """
    # Load goal with plan relationship
    result = await db.execute(
        select(TreatmentGoal)
        .options(joinedload(TreatmentGoal.plan))
        .where(TreatmentGoal.id == goal_id)
    )
    goal = result.scalar_one_or_none()

    if not goal:
        raise HTTPException(status_code=404, detail=f"Goal {goal_id} not found")

    # Verify therapist owns the plan
    if goal.plan.therapist_id != therapist_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this goal"
        )

    return goal


@router.post("/treatment-plans/{plan_id}/goals", response_model=GoalResponse, status_code=201)
async def add_goal_to_plan(
    plan_id: UUID,
    goal_data: GoalCreate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Add a new goal to a treatment plan.

    Supports goal hierarchies via parent_goal_id (validates parent exists in same plan).
    Can link interventions to the goal during creation.

    Authorization:
        - Requires therapist role
        - Therapist must own the treatment plan

    Args:
        plan_id: Treatment plan ID to add goal to
        goal_data: Goal creation data (type, description, SMART criteria, etc.)
        current_user: Authenticated therapist user
        db: Database session

    Returns:
        GoalResponse: Newly created goal with ID and timestamps

    Raises:
        HTTPException 404: Plan not found or parent goal not found
        HTTPException 403: Not authorized to modify this plan
        HTTPException 400: Parent goal not in same plan or invalid data
    """
    # Verify plan ownership
    plan = await verify_plan_ownership(plan_id, current_user.id, db)

    # Validate parent_goal_id if provided (must exist in same plan)
    if goal_data.parent_goal_id:
        parent_result = await db.execute(
            select(TreatmentGoal).where(
                TreatmentGoal.id == goal_data.parent_goal_id,
                TreatmentGoal.plan_id == plan_id
            )
        )
        parent_goal = parent_result.scalar_one_or_none()

        if not parent_goal:
            raise HTTPException(
                status_code=400,
                detail=f"Parent goal {goal_data.parent_goal_id} not found in plan {plan_id}"
            )

    # Create TreatmentGoal
    new_goal = TreatmentGoal(
        plan_id=plan_id,
        parent_goal_id=goal_data.parent_goal_id,
        goal_type=goal_data.goal_type.value,
        description=goal_data.description,
        measurable_criteria=goal_data.measurable_criteria,
        baseline_value=goal_data.baseline_value,
        target_value=goal_data.target_value,
        target_date=goal_data.target_date,
        priority=goal_data.priority,
        status='not_started',
        progress_percentage=0
    )

    db.add(new_goal)
    await db.flush()  # Get goal ID before creating interventions

    # Create GoalIntervention links if interventions provided
    if goal_data.interventions:
        for intervention_data in goal_data.interventions:
            # Verify intervention exists
            intervention_result = await db.execute(
                select(Intervention).where(Intervention.id == intervention_data.intervention_id)
            )
            intervention = intervention_result.scalar_one_or_none()

            if not intervention:
                raise HTTPException(
                    status_code=404,
                    detail=f"Intervention {intervention_data.intervention_id} not found"
                )

            # Create link
            goal_intervention = GoalIntervention(
                goal_id=new_goal.id,
                intervention_id=intervention_data.intervention_id,
                frequency=intervention_data.frequency,
                notes=intervention_data.notes
            )
            db.add(goal_intervention)

    await db.commit()
    await db.refresh(new_goal)

    return GoalResponse.model_validate(new_goal)


@router.put("/goals/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: UUID,
    goal_update: GoalUpdate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a treatment goal.

    All fields are optional (partial updates supported). If progress_percentage
    is updated and the goal has a parent goal, the parent's progress is
    automatically recalculated as the weighted average of sub-goals.

    Authorization:
        - Requires therapist role
        - Therapist must own the plan containing this goal

    Args:
        goal_id: Goal ID to update
        goal_update: Fields to update (all optional)
        current_user: Authenticated therapist user
        db: Database session

    Returns:
        GoalResponse: Updated goal data

    Raises:
        HTTPException 404: Goal not found
        HTTPException 403: Not authorized to modify this goal
    """
    # Verify goal ownership
    goal = await verify_goal_ownership(goal_id, current_user.id, db)

    # Track if progress_percentage changed (for parent recalculation)
    progress_changed = False
    old_progress = goal.progress_percentage

    # Update fields from GoalUpdate (all fields optional)
    update_data = goal_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if hasattr(goal, field):
            setattr(goal, field, value)
            if field == 'progress_percentage':
                progress_changed = True

    await db.commit()
    await db.refresh(goal)

    # Recalculate parent goal progress if progress changed and parent exists
    if progress_changed and goal.parent_goal_id:
        await recalculate_parent_progress(goal.parent_goal_id, db)

    return GoalResponse.model_validate(goal)


async def recalculate_parent_progress(parent_goal_id: UUID, db: AsyncSession):
    """
    Recalculate parent goal progress as weighted average of sub-goals.

    Args:
        parent_goal_id: Parent goal ID to recalculate
        db: Database session
    """
    # Load parent goal with all sub-goals
    result = await db.execute(
        select(TreatmentGoal)
        .options(selectinload(TreatmentGoal.sub_goals))
        .where(TreatmentGoal.id == parent_goal_id)
    )
    parent_goal = result.scalar_one_or_none()

    if not parent_goal or not parent_goal.sub_goals:
        return

    # Calculate weighted average (all sub-goals equally weighted for now)
    total_progress = sum(sub_goal.progress_percentage for sub_goal in parent_goal.sub_goals)
    avg_progress = total_progress / len(parent_goal.sub_goals)

    parent_goal.progress_percentage = int(avg_progress)
    await db.commit()


@router.post("/goals/{goal_id}/progress", response_model=GoalProgressResponse, status_code=201)
async def record_goal_progress(
    goal_id: UUID,
    progress_data: GoalProgressCreate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Record a progress entry for a treatment goal.

    Progress calculation logic:
    - If progress_value matches target_value: sets progress to 100%
    - Uses rating (1-10) to update progress_percentage proportionally
    - Recalculates parent goal progress if goal has parent

    Authorization:
        - Requires therapist role
        - Therapist must own the plan containing this goal

    Args:
        goal_id: Goal ID to record progress for
        progress_data: Progress note, value, rating, and optional session ID
        current_user: Authenticated therapist user
        db: Database session

    Returns:
        GoalProgressResponse: Newly created progress entry

    Raises:
        HTTPException 404: Goal not found
        HTTPException 403: Not authorized to modify this goal
    """
    # Verify goal ownership
    goal = await verify_goal_ownership(goal_id, current_user.id, db)

    # Create GoalProgress entry
    progress_entry = GoalProgress(
        goal_id=goal_id,
        session_id=progress_data.session_id,
        recorded_by=current_user.id,
        progress_note=progress_data.progress_note,
        progress_value=progress_data.progress_value,
        rating=progress_data.rating
    )

    db.add(progress_entry)

    # Auto-calculate progress_percentage based on rating and target achievement
    progress_changed = False

    # Check if target achieved (progress_value == target_value)
    if progress_data.progress_value and goal.target_value:
        if progress_data.progress_value == goal.target_value:
            goal.progress_percentage = 100
            goal.status = 'achieved'
            progress_changed = True

    # Update progress based on rating (1-10 scale)
    if progress_data.rating:
        new_progress = int((progress_data.rating / 10) * 100)

        # Only update if rating suggests higher progress than current
        if new_progress > goal.progress_percentage:
            goal.progress_percentage = new_progress
            progress_changed = True

            # Update status based on progress
            if goal.progress_percentage == 0:
                goal.status = 'not_started'
            elif goal.progress_percentage == 100:
                goal.status = 'achieved'
            elif goal.progress_percentage > 0:
                goal.status = 'in_progress'

    # Update current_value if provided
    if progress_data.progress_value:
        goal.current_value = progress_data.progress_value

    await db.commit()
    await db.refresh(progress_entry)

    # Recalculate parent progress if applicable
    if progress_changed and goal.parent_goal_id:
        await recalculate_parent_progress(goal.parent_goal_id, db)

    return GoalProgressResponse.model_validate(progress_entry)


@router.get("/goals/{goal_id}/history", response_model=List[GoalProgressResponse])
async def get_goal_progress_history(
    goal_id: UUID,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get progress history for a treatment goal.

    Returns all progress entries for the goal, ordered by most recent first.
    Includes session details if progress was recorded during a therapy session.

    Authorization:
        - Requires therapist role
        - Therapist must own the plan containing this goal

    Args:
        goal_id: Goal ID to get history for
        current_user: Authenticated therapist user
        db: Database session

    Returns:
        List[GoalProgressResponse]: Progress entries ordered by recorded_at DESC

    Raises:
        HTTPException 404: Goal not found
        HTTPException 403: Not authorized to access this goal
    """
    # Verify goal ownership
    goal = await verify_goal_ownership(goal_id, current_user.id, db)

    # Query GoalProgress filtered by goal_id, ordered by recorded_at DESC
    result = await db.execute(
        select(GoalProgress)
        .where(GoalProgress.goal_id == goal_id)
        .order_by(GoalProgress.recorded_at.desc())
    )
    progress_entries = result.scalars().all()

    return [GoalProgressResponse.model_validate(entry) for entry in progress_entries]
