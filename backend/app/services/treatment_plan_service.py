"""
Treatment Plan Service Layer

Provides business logic functions for treatment plan management including:
- Goal progress calculation (weighted by sub-goals and progress entries)
- Review due date checking and reminder logic
- Comprehensive progress report generation
- Plan-level progress recalculation
- Goal filtering and status queries

Follows patterns from analytics.py with async/await, structured logging,
comprehensive error handling, and complex SQLAlchemy aggregations.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from uuid import UUID
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict
import logging

from app.models.treatment_models import (
    TreatmentPlan,
    TreatmentPlanGoal as TreatmentGoal,  # Aliased for convenience
    GoalProgress,
    Intervention,
    GoalIntervention
)

# Configure logger
logger = logging.getLogger(__name__)


async def calculate_goal_progress(goal: TreatmentGoal, db: AsyncSession) -> int:
    """
    Calculate goal progress based on sub-goals and progress entries.

    Implements intelligent progress calculation using a hierarchical approach:
    1. If goal has sub_goals: weighted average based on priority (higher priority = more weight)
    2. If goal has progress_entries: latest rating / 10 * 100
    3. Otherwise: return current progress_percentage

    Args:
        goal: TreatmentGoal object with loaded sub_goals and progress_entries relationships
        db: Async database session

    Returns:
        int: Progress percentage from 0-100

    Algorithm Details:
        - Sub-goal weighting: Inverted priority (priority 1 = highest weight)
        - Weight formula: (max_priority - priority + 1)
        - Progress = sum(sub_goal_progress * weight) / sum(weights)
        - Rating conversion: (rating / 10) * 100 to get percentage

    Example:
        >>> # Goal with 3 sub-goals:
        >>> # Sub-goal A: priority=1, progress=80% -> weight=3
        >>> # Sub-goal B: priority=2, progress=60% -> weight=2
        >>> # Sub-goal C: priority=3, progress=40% -> weight=1
        >>> # Total progress = (80*3 + 60*2 + 40*1) / (3+2+1) = 400/6 = 67%
        >>> progress = await calculate_goal_progress(goal, db)
        >>> print(progress)  # 67
    """
    logger.debug(f"Calculating progress for goal {goal.id} (type={goal.goal_type})")

    # Strategy 1: Calculate from sub-goals using weighted average
    if goal.sub_goals and len(goal.sub_goals) > 0:
        logger.debug(f"Goal {goal.id} has {len(goal.sub_goals)} sub-goals, calculating weighted average")

        # Calculate max priority for weighting (inverted: lower number = higher priority)
        max_priority = max(sub_goal.priority for sub_goal in goal.sub_goals)

        weighted_sum = 0
        total_weight = 0

        for sub_goal in goal.sub_goals:
            # Invert priority: priority 1 gets highest weight
            weight = max_priority - sub_goal.priority + 1
            weighted_sum += sub_goal.progress_percentage * weight
            total_weight += weight

            logger.debug(
                f"Sub-goal {sub_goal.id}: priority={sub_goal.priority}, "
                f"progress={sub_goal.progress_percentage}%, weight={weight}"
            )

        if total_weight > 0:
            progress = int(weighted_sum / total_weight)
            logger.info(
                f"Goal {goal.id} progress from sub-goals: {progress}% "
                f"(weighted_sum={weighted_sum}, total_weight={total_weight})"
            )
            return progress
        else:
            logger.warning(f"Goal {goal.id} has sub-goals but total weight is 0, returning 0")
            return 0

    # Strategy 2: Calculate from latest progress entry rating
    if goal.progress_entries and len(goal.progress_entries) > 0:
        # Sort by recorded_at to get latest entry
        sorted_entries = sorted(
            goal.progress_entries,
            key=lambda e: e.recorded_at,
            reverse=True
        )
        latest_entry = sorted_entries[0]

        if latest_entry.rating is not None:
            # Convert rating (1-10) to percentage (0-100)
            progress = int((latest_entry.rating / 10.0) * 100)
            logger.info(
                f"Goal {goal.id} progress from latest entry: {progress}% "
                f"(rating={latest_entry.rating}, recorded_at={latest_entry.recorded_at})"
            )
            return progress
        else:
            logger.debug(f"Latest progress entry for goal {goal.id} has no rating")

    # Strategy 3: Return current stored progress_percentage
    logger.debug(
        f"Goal {goal.id} using stored progress_percentage: {goal.progress_percentage}%"
    )
    return goal.progress_percentage


async def check_review_due(plan: TreatmentPlan, db: AsyncSession) -> Dict:
    """
    Check if treatment plan review is due or overdue.

    Determines review status based on next_review_date and calculates
    days until/past due date. Provides actionable status for reminder logic.

    Args:
        plan: TreatmentPlan object with next_review_date set
        db: Async database session

    Returns:
        dict: Review status information with keys:
            - is_due (bool): True if review is due soon or overdue
            - days_overdue (int): Positive if overdue, negative if upcoming, 0 if today
            - status (str): 'current', 'due_soon', 'overdue'
            - next_review_date (str): ISO date string or None

    Status Logic:
        - 'current': More than 7 days until next_review_date
        - 'due_soon': Within 7 days of next_review_date (reminder phase)
        - 'overdue': Past next_review_date (urgent reminder)

    Edge Cases:
        - No next_review_date set: returns status='current', is_due=False
        - Review date is today: status='due_soon', days_overdue=0

    Example:
        >>> review_status = await check_review_due(plan, db)
        >>> if review_status['is_due']:
        ...     if review_status['status'] == 'overdue':
        ...         send_urgent_reminder(plan)
        ...     else:
        ...         send_reminder(plan)
    """
    logger.debug(f"Checking review status for plan {plan.id}")

    # Handle case where next_review_date is not set
    if plan.next_review_date is None:
        logger.debug(f"Plan {plan.id} has no next_review_date set")
        return {
            'is_due': False,
            'days_overdue': 0,
            'status': 'current',
            'next_review_date': None
        }

    # Calculate days until/past review date
    today = date.today()
    next_review = plan.next_review_date
    days_diff = (next_review - today).days

    # Determine status
    if days_diff < 0:
        # Past due date - overdue
        status = 'overdue'
        is_due = True
        days_overdue = abs(days_diff)
        logger.warning(
            f"Plan {plan.id} review is OVERDUE by {days_overdue} days "
            f"(next_review_date={next_review})"
        )
    elif days_diff <= 7:
        # Within 7 days - due soon
        status = 'due_soon'
        is_due = True
        days_overdue = -days_diff  # Negative indicates upcoming
        logger.info(
            f"Plan {plan.id} review is DUE SOON in {days_diff} days "
            f"(next_review_date={next_review})"
        )
    else:
        # More than 7 days away - current
        status = 'current'
        is_due = False
        days_overdue = -days_diff  # Negative indicates upcoming
        logger.debug(
            f"Plan {plan.id} review is CURRENT, {days_diff} days until review "
            f"(next_review_date={next_review})"
        )

    return {
        'is_due': is_due,
        'days_overdue': days_overdue if days_diff < 0 else -days_diff,
        'status': status,
        'next_review_date': next_review.isoformat()
    }


async def generate_progress_report(plan_id: UUID, db: AsyncSession) -> Dict:
    """
    Generate comprehensive progress report for treatment plan.

    Aggregates data across all goals and progress entries to provide
    holistic view of treatment plan effectiveness and patient progress.

    Args:
        plan_id: UUID of the treatment plan
        db: Async database session

    Returns:
        dict: Comprehensive progress report with keys:
            - plan_id (UUID): Treatment plan ID
            - total_goals (int): Count of all goals
            - achieved_goals (int): Goals with status='achieved'
            - in_progress_goals (int): Goals with status='in_progress'
            - not_started_goals (int): Goals with status='not_started'
            - overall_progress_percentage (int): Average progress across all goals
            - goals_on_track (int): Goals with progress >= 50%
            - goals_behind (int): Goals with progress < 50% (excluding not_started)
            - recent_progress_entries (list): Last 5 progress entries across all goals
            - top_performing_goals (list): Top 3 goals by progress (excluding achieved)
            - needs_attention_goals (list): Bottom 3 goals by progress (excluding not_started)

    Report Sections:
        1. Goal Status Counts: Breakdown by status (achieved/in_progress/not_started)
        2. Overall Progress: Average progress percentage across all goals
        3. On Track vs Behind: Goals meeting expectations vs needing attention
        4. Recent Activity: Latest progress entries for visibility into recent work
        5. Performance Analysis: Identifying best performing and struggling goals

    Edge Cases:
        - Plan not found: Returns empty report with zeros
        - No goals: Returns zeros for all metrics
        - No progress entries: recent_progress_entries is empty list

    Example:
        >>> report = await generate_progress_report(plan_uuid, db)
        >>> print(f"Overall progress: {report['overall_progress_percentage']}%")
        >>> print(f"Goals on track: {report['goals_on_track']}/{report['total_goals']}")
        >>> for goal in report['needs_attention_goals']:
        ...     print(f"⚠️ {goal['description']}: {goal['progress']}%")
    """
    logger.info(f"Generating progress report for plan {plan_id}")

    try:
        # Load treatment plan with all goals
        plan_query = select(TreatmentPlan).where(
            TreatmentPlan.id == plan_id
        )
        plan_result = await db.execute(plan_query)
        plan = plan_result.scalar_one_or_none()

        if not plan:
            logger.error(f"Treatment plan {plan_id} not found")
            return _empty_progress_report(plan_id)

        # Load all goals for the plan
        goals_query = select(TreatmentGoal).where(
            TreatmentGoal.plan_id == plan_id
        ).order_by(TreatmentGoal.created_at)

        goals_result = await db.execute(goals_query)
        goals = goals_result.scalars().all()

        if not goals or len(goals) == 0:
            logger.info(f"Plan {plan_id} has no goals, returning empty report")
            return _empty_progress_report(plan_id)

        # 1. Calculate goal status counts
        total_goals = len(goals)
        achieved_goals = sum(1 for g in goals if g.status == 'achieved')
        in_progress_goals = sum(1 for g in goals if g.status == 'in_progress')
        not_started_goals = sum(1 for g in goals if g.status == 'not_started')

        # 2. Calculate overall progress percentage
        progress_sum = sum(g.progress_percentage for g in goals)
        overall_progress = int(progress_sum / total_goals) if total_goals > 0 else 0

        # 3. Calculate on track vs behind
        goals_on_track = sum(1 for g in goals if g.progress_percentage >= 50)
        goals_behind = sum(
            1 for g in goals
            if g.progress_percentage < 50 and g.status != 'not_started'
        )

        # 4. Fetch recent progress entries (last 5 across all goals)
        progress_query = select(GoalProgress).where(
            GoalProgress.goal_id.in_([g.id for g in goals])
        ).order_by(GoalProgress.recorded_at.desc()).limit(5)

        progress_result = await db.execute(progress_query)
        recent_entries = progress_result.scalars().all()

        recent_progress_entries = [
            {
                'id': str(entry.id),
                'goal_id': str(entry.goal_id),
                'progress_note': entry.progress_note,
                'rating': entry.rating,
                'recorded_at': entry.recorded_at.isoformat()
            }
            for entry in recent_entries
        ]

        # 5. Top performing goals (highest progress, excluding achieved)
        top_performers = sorted(
            [g for g in goals if g.status != 'achieved'],
            key=lambda g: g.progress_percentage,
            reverse=True
        )[:3]

        top_performing_goals = [
            {
                'id': str(goal.id),
                'description': goal.description,
                'goal_type': goal.goal_type,
                'progress': goal.progress_percentage,
                'status': goal.status
            }
            for goal in top_performers
        ]

        # 6. Needs attention goals (lowest progress, excluding not_started)
        struggling = sorted(
            [g for g in goals if g.status != 'not_started'],
            key=lambda g: g.progress_percentage
        )[:3]

        needs_attention_goals = [
            {
                'id': str(goal.id),
                'description': goal.description,
                'goal_type': goal.goal_type,
                'progress': goal.progress_percentage,
                'status': goal.status
            }
            for goal in struggling
        ]

        logger.info(
            f"Progress report generated for plan {plan_id}: "
            f"total_goals={total_goals}, overall_progress={overall_progress}%, "
            f"on_track={goals_on_track}, behind={goals_behind}"
        )

        return {
            'plan_id': str(plan_id),
            'total_goals': total_goals,
            'achieved_goals': achieved_goals,
            'in_progress_goals': in_progress_goals,
            'not_started_goals': not_started_goals,
            'overall_progress_percentage': overall_progress,
            'goals_on_track': goals_on_track,
            'goals_behind': goals_behind,
            'recent_progress_entries': recent_progress_entries,
            'top_performing_goals': top_performing_goals,
            'needs_attention_goals': needs_attention_goals
        }

    except Exception as e:
        logger.error(
            f"Error generating progress report for plan {plan_id}: {str(e)}",
            exc_info=True
        )
        # Return empty report on error rather than failing
        return _empty_progress_report(plan_id)


async def recalculate_plan_progress(plan_id: UUID, db: AsyncSession) -> int:
    """
    Recalculate progress for all goals in a plan and return average.

    Iterates through all goals in the plan, recalculates their progress using
    calculate_goal_progress(), and returns the average progress across all goals.
    This is useful after adding new progress entries or updating goal hierarchies.

    Args:
        plan_id: UUID of the treatment plan
        db: Async database session

    Returns:
        int: Average progress percentage across all goals (0-100)

    Process:
        1. Load all goals for the plan
        2. For each goal, call calculate_goal_progress()
        3. Calculate average of all goal progress percentages
        4. Return overall plan progress

    Use Cases:
        - After recording new progress entries
        - After updating goal hierarchies
        - During periodic plan reviews
        - When generating progress reports

    Edge Cases:
        - Plan not found: returns 0
        - No goals: returns 0
        - Goals with no progress data: returns stored progress_percentage

    Example:
        >>> # After recording progress entry
        >>> await db.add(progress_entry)
        >>> await db.commit()
        >>> # Recalculate plan progress
        >>> new_progress = await recalculate_plan_progress(plan_uuid, db)
        >>> print(f"Updated plan progress: {new_progress}%")
    """
    logger.info(f"Recalculating progress for all goals in plan {plan_id}")

    try:
        # Load all goals for the plan with relationships
        goals_query = select(TreatmentGoal).where(
            TreatmentGoal.plan_id == plan_id
        )

        goals_result = await db.execute(goals_query)
        goals = goals_result.scalars().all()

        if not goals or len(goals) == 0:
            logger.info(f"Plan {plan_id} has no goals, returning 0% progress")
            return 0

        # Calculate progress for each goal
        total_progress = 0
        for goal in goals:
            goal_progress = await calculate_goal_progress(goal, db)
            total_progress += goal_progress
            logger.debug(
                f"Goal {goal.id} ({goal.goal_type}): {goal_progress}% progress"
            )

        # Calculate average
        average_progress = int(total_progress / len(goals))

        logger.info(
            f"Plan {plan_id} recalculated progress: {average_progress}% "
            f"(total={total_progress}, goals={len(goals)})"
        )

        return average_progress

    except Exception as e:
        logger.error(
            f"Error recalculating progress for plan {plan_id}: {str(e)}",
            exc_info=True
        )
        return 0


async def get_goals_by_status(
    plan_id: UUID,
    status: str,
    db: AsyncSession
) -> List[TreatmentGoal]:
    """
    Query goals filtered by plan_id and status.

    Retrieves all goals for a specific treatment plan that match the given
    status. Results are ordered by priority (ascending, so priority 1 first)
    and then by creation date.

    Args:
        plan_id: UUID of the treatment plan
        status: Goal status to filter by ('not_started', 'in_progress', 'achieved',
                'modified', 'discontinued')
        db: Async database session

    Returns:
        List[TreatmentGoal]: List of goals matching criteria, ordered by priority

    Ordering Logic:
        - Primary sort: priority (ascending - priority 1 = highest priority comes first)
        - Secondary sort: created_at (ascending - older goals first)

    Valid Status Values:
        - 'not_started': Goals not yet begun
        - 'in_progress': Goals currently being worked on
        - 'achieved': Goals that have been completed
        - 'modified': Goals that have been changed from original definition
        - 'discontinued': Goals that are no longer being pursued

    Example:
        >>> # Get all in-progress goals
        >>> in_progress = await get_goals_by_status(
        ...     plan_uuid, 'in_progress', db
        ... )
        >>> for goal in in_progress:
        ...     print(f"Priority {goal.priority}: {goal.description}")

        >>> # Get all achieved goals for celebration/review
        >>> achieved = await get_goals_by_status(
        ...     plan_uuid, 'achieved', db
        ... )
    """
    logger.info(f"Querying goals for plan {plan_id} with status '{status}'")

    try:
        query = select(TreatmentGoal).where(
            and_(
                TreatmentGoal.plan_id == plan_id,
                TreatmentGoal.status == status
            )
        ).order_by(
            TreatmentGoal.priority.asc(),  # Priority 1 first
            TreatmentGoal.created_at.asc()  # Older goals first
        )

        result = await db.execute(query)
        goals = result.scalars().all()

        logger.info(
            f"Found {len(goals)} goals with status '{status}' for plan {plan_id}"
        )

        return list(goals)

    except Exception as e:
        logger.error(
            f"Error querying goals by status for plan {plan_id}: {str(e)}",
            exc_info=True
        )
        return []


def _empty_progress_report(plan_id: UUID) -> Dict:
    """
    Generate empty progress report structure.

    Helper function to return consistent empty report when plan not found
    or has no goals.

    Args:
        plan_id: UUID of the treatment plan

    Returns:
        dict: Empty progress report with zero values
    """
    return {
        'plan_id': str(plan_id),
        'total_goals': 0,
        'achieved_goals': 0,
        'in_progress_goals': 0,
        'not_started_goals': 0,
        'overall_progress_percentage': 0,
        'goals_on_track': 0,
        'goals_behind': 0,
        'recent_progress_entries': [],
        'top_performing_goals': [],
        'needs_attention_goals': []
    }
