"""
Milestone detection service for goal progress tracking.

Detects when progress entries trigger achievement milestones including:
- Percentage improvement milestones (25%, 50%, 75%, 100%)
- Consecutive check-in streak milestones (7, 14, 30, 60, 90 days)

Implements Feature 6 Goal Tracking specification (lines 401-420).
"""

from datetime import datetime, timedelta
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload


# Milestone thresholds
PERCENTAGE_THRESHOLDS = [0.25, 0.50, 0.75, 1.0]  # 25%, 50%, 75%, 100%
STREAK_THRESHOLDS = [7, 14, 30, 60, 90]  # Days


async def check_milestones(goal, new_entry, db: AsyncSession) -> List:
    """
    Check if a new progress entry triggers any milestone achievements.

    Detects percentage improvement milestones based on progress from baseline
    to target value. Only marks milestones as achieved once.

    Args:
        goal: TreatmentGoal object with baseline_value and target_value
        new_entry: ProgressEntry object with the new value
        db: Async database session

    Returns:
        List of newly achieved ProgressMilestone objects

    Example:
        >>> goal.baseline_value = 8.0  # Starting anxiety level
        >>> goal.target_value = 2.0    # Target anxiety level
        >>> new_entry.value = 5.0      # Current anxiety level
        >>> milestones = await check_milestones(goal, new_entry, db)
        >>> len(milestones)
        1  # Achieved 50% improvement milestone
    """
    milestones_achieved = []

    # Validate required fields
    if goal.baseline_value is None or goal.target_value is None:
        return milestones_achieved

    if new_entry.value is None:
        return milestones_achieved

    # Convert to Decimal for precise calculation
    baseline = Decimal(str(goal.baseline_value))
    target = Decimal(str(goal.target_value))
    current = Decimal(str(new_entry.value))

    # Handle edge case: baseline equals target (no progress possible)
    if baseline == target:
        return milestones_achieved

    # Calculate improvement percentage
    # Formula: (baseline - current) / (baseline - target)
    # This works for both increasing and decreasing targets
    total_distance = baseline - target
    progress_distance = baseline - current

    # Avoid division by zero (defensive check)
    if total_distance == 0:
        return milestones_achieved

    improvement = progress_distance / total_distance

    # Check each percentage threshold
    for threshold in PERCENTAGE_THRESHOLDS:
        if improvement >= Decimal(str(threshold)):
            # Get or create milestone record
            milestone = await get_or_create_milestone(
                goal_id=goal.id,
                threshold=threshold,
                db=db
            )

            # Only mark as achieved if not already achieved
            if milestone and milestone.achieved_at is None:
                milestone.achieved_at = datetime.utcnow()
                milestones_achieved.append(milestone)

    # Commit changes if any milestones were achieved
    if milestones_achieved:
        await db.commit()

    return milestones_achieved


async def get_or_create_milestone(
    goal_id,
    threshold: float,
    db: AsyncSession
):
    """
    Get existing milestone or create new one for a goal and threshold.

    Searches for existing ProgressMilestone of type "percentage" with the
    specified target_value (threshold). Creates a new record if not found.

    Args:
        goal_id: UUID of the TreatmentGoal
        threshold: Float threshold value (e.g., 0.25, 0.50, 0.75, 1.0)
        db: Async database session

    Returns:
        ProgressMilestone object (existing or newly created)

    Example:
        >>> milestone = await get_or_create_milestone(goal_id, 0.50, db)
        >>> milestone.milestone_type
        'percentage'
        >>> milestone.target_value
        Decimal('0.50')
        >>> milestone.title
        '50% Improvement Achieved'
    """
    # Import models inside function to avoid circular imports
    # Models will be created by Backend Dev #2
    try:
        from app.models.db_models import ProgressMilestone
    except ImportError:
        # Fallback: try alternate location
        from app.models.tracking_models import ProgressMilestone

    # Query for existing milestone
    threshold_decimal = Decimal(str(threshold))

    result = await db.execute(
        select(ProgressMilestone).where(
            and_(
                ProgressMilestone.goal_id == goal_id,
                ProgressMilestone.milestone_type == 'percentage',
                ProgressMilestone.target_value == threshold_decimal
            )
        )
    )

    milestone = result.scalar_one_or_none()

    # Create if doesn't exist
    if milestone is None:
        # Format threshold as percentage for display
        percentage = int(threshold * 100)

        milestone = ProgressMilestone(
            goal_id=goal_id,
            milestone_type='percentage',
            title=f'{percentage}% Improvement Achieved',
            description=f'Reached {percentage}% progress toward goal target',
            target_value=threshold_decimal,
            achieved_at=None  # Will be set when milestone is achieved
        )

        db.add(milestone)
        await db.flush()  # Get ID without committing

    return milestone


async def check_streak_milestones(
    goal_id,
    entries: List,
    db: AsyncSession
) -> List:
    """
    Detect consecutive check-in streak milestones.

    Calculates the longest consecutive streak of days with progress entries
    and creates milestones for achieved streak thresholds (7, 14, 30, 60, 90 days).

    Args:
        goal_id: UUID of the TreatmentGoal
        entries: List of ProgressEntry objects sorted by entry_date
        db: Async database session

    Returns:
        List of newly achieved streak milestone objects

    Example:
        >>> # User has logged progress for 15 consecutive days
        >>> streak_milestones = await check_streak_milestones(goal_id, entries, db)
        >>> len(streak_milestones)
        2  # Achieved 7-day and 14-day streak milestones
    """
    milestones_achieved = []

    # Need at least 1 entry to have a streak
    if not entries:
        return milestones_achieved

    # Sort entries by date (ascending)
    sorted_entries = sorted(entries, key=lambda e: e.entry_date)

    # Calculate current streak
    current_streak = 1
    max_streak = 1

    for i in range(1, len(sorted_entries)):
        prev_date = sorted_entries[i - 1].entry_date
        curr_date = sorted_entries[i].entry_date

        # Check if dates are consecutive
        expected_date = prev_date + timedelta(days=1)

        if curr_date == expected_date:
            # Continue streak
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        elif curr_date == prev_date:
            # Same day (multiple entries) - don't break streak
            continue
        else:
            # Streak broken
            current_streak = 1

    # Use the current streak (most recent consecutive days)
    streak_length = current_streak

    # Import models
    try:
        from app.models.db_models import ProgressMilestone
    except ImportError:
        from app.models.tracking_models import ProgressMilestone

    # Check each streak threshold
    for threshold in STREAK_THRESHOLDS:
        if streak_length >= threshold:
            # Query for existing streak milestone
            result = await db.execute(
                select(ProgressMilestone).where(
                    and_(
                        ProgressMilestone.goal_id == goal_id,
                        ProgressMilestone.milestone_type == 'streak',
                        ProgressMilestone.target_value == Decimal(str(threshold))
                    )
                )
            )

            milestone = result.scalar_one_or_none()

            # Create if doesn't exist
            if milestone is None:
                milestone = ProgressMilestone(
                    goal_id=goal_id,
                    milestone_type='streak',
                    title=f'{threshold}-Day Streak Achieved',
                    description=f'Logged progress for {threshold} consecutive days',
                    target_value=Decimal(str(threshold)),
                    achieved_at=datetime.utcnow()
                )

                db.add(milestone)
                milestones_achieved.append(milestone)

            elif milestone.achieved_at is None:
                # Mark as achieved if not already
                milestone.achieved_at = datetime.utcnow()
                milestones_achieved.append(milestone)

    # Commit changes if any milestones were achieved
    if milestones_achieved:
        await db.flush()

    return milestones_achieved
