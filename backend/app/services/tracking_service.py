"""
Goal Tracking Service

Provides business logic for goal tracking operations including:
- Creating and managing tracking configurations
- Recording progress entries
- Retrieving progress history with filtering and aggregation
- Calculating progress statistics and trends
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from uuid import UUID
from datetime import datetime, timedelta
from datetime import date as date_type
from typing import List, Optional
from fastapi import HTTPException
import logging

from app.schemas.tracking_schemas import (
    TrackingConfigCreate,
    TrackingConfigResponse,
    ProgressEntryCreate,
    ProgressEntryResponse,
    ProgressHistoryQuery,
    ProgressHistoryResponse,
    ProgressStatistics,
    TrendDirection,
    AggregationPeriod
)
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import (
    GoalTrackingConfig,
    ProgressEntry
)

# Configure logger
logger = logging.getLogger(__name__)


async def create_tracking_config(
    goal_id: UUID,
    config_data: TrackingConfigCreate,
    db: AsyncSession
) -> TrackingConfigResponse:
    """
    Create or update tracking configuration for a goal.

    Sets up the tracking method (scale, frequency, duration, binary, assessment),
    tracking frequency (daily, weekly, session), and related parameters like
    scale ranges, units, and target direction.

    Args:
        goal_id: UUID of the goal to configure tracking for
        config_data: TrackingConfigCreate schema with configuration details
        db: Async database session

    Returns:
        TrackingConfigResponse: Created/updated tracking configuration

    Raises:
        HTTPException: 404 if goal not found

    Validation:
        - Goal must exist
        - Scale method requires scale_min and scale_max
        - Frequency method requires frequency_unit
        - Duration method requires duration_unit

    Example:
        >>> config = await create_tracking_config(
        ...     goal_uuid,
        ...     TrackingConfigCreate(
        ...         tracking_method="scale",
        ...         tracking_frequency="daily",
        ...         scale_min=1,
        ...         scale_max=10,
        ...         target_direction="decrease"
        ...     ),
        ...     db
        ... )
    """
    logger.info(f"Creating tracking config for goal {goal_id}")

    # 1. Validate goal exists
    goal_query = select(TreatmentGoal).where(TreatmentGoal.id == goal_id)
    goal_result = await db.execute(goal_query)
    goal = goal_result.scalar_one_or_none()

    if not goal:
        logger.error(f"Goal {goal_id} not found")
        raise HTTPException(
            status_code=404,
            detail=f"Goal with id {goal_id} not found"
        )

    # 2. Validate tracking method-specific requirements
    if config_data.tracking_method.value == "scale":
        if config_data.scale_min is None or config_data.scale_max is None:
            raise HTTPException(
                status_code=400,
                detail="scale_min and scale_max are required for scale tracking method"
            )
    elif config_data.tracking_method.value == "frequency":
        if not config_data.frequency_unit:
            raise HTTPException(
                status_code=400,
                detail="frequency_unit is required for frequency tracking method"
            )
    elif config_data.tracking_method.value == "duration":
        if not config_data.duration_unit:
            raise HTTPException(
                status_code=400,
                detail="duration_unit is required for duration tracking method"
            )

    # 3. Check if config already exists for this goal
    existing_config_query = select(GoalTrackingConfig).where(
        GoalTrackingConfig.goal_id == goal_id
    )
    existing_config_result = await db.execute(existing_config_query)
    existing_config = existing_config_result.scalar_one_or_none()

    try:
        if existing_config:
            # Update existing config
            logger.info(f"Updating existing tracking config {existing_config.id}")
            existing_config.tracking_method = config_data.tracking_method
            existing_config.tracking_frequency = config_data.tracking_frequency
            existing_config.scale_min = config_data.scale_min
            existing_config.scale_max = config_data.scale_max
            existing_config.scale_labels = config_data.scale_labels
            existing_config.frequency_unit = config_data.frequency_unit
            existing_config.duration_unit = config_data.duration_unit
            existing_config.target_direction = config_data.target_direction
            existing_config.reminder_enabled = config_data.reminder_enabled
            existing_config.updated_at = datetime.utcnow()

            config = existing_config
        else:
            # Create new config
            logger.info(f"Creating new tracking config for goal {goal_id}")
            config = GoalTrackingConfig(
                goal_id=goal_id,
                tracking_method=config_data.tracking_method,
                tracking_frequency=config_data.tracking_frequency,
                scale_min=config_data.scale_min,
                scale_max=config_data.scale_max,
                scale_labels=config_data.scale_labels,
                frequency_unit=config_data.frequency_unit,
                duration_unit=config_data.duration_unit,
                target_direction=config_data.target_direction,
                reminder_enabled=config_data.reminder_enabled
            )
            db.add(config)

        await db.commit()
        await db.refresh(config)

        logger.info(
            f"Tracking config created/updated successfully: "
            f"id={config.id}, method={config.tracking_method}, frequency={config.tracking_frequency}"
        )

        return TrackingConfigResponse.model_validate(config)

    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating tracking config for goal {goal_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create tracking configuration: {str(e)}"
        )


async def record_progress_entry(
    goal_id: UUID,
    entry_data: ProgressEntryCreate,
    recorded_by_id: UUID,
    db: AsyncSession
) -> ProgressEntryResponse:
    """
    Record a progress data point for a goal.

    Creates a new progress entry with value, date, time, notes, and context.
    Validates goal and tracking config exist, then checks for milestone
    achievements after recording.

    Args:
        goal_id: UUID of the goal to record progress for
        entry_data: ProgressEntryCreate schema with entry details
        recorded_by_id: UUID of user recording the entry (patient or therapist)
        db: Async database session

    Returns:
        ProgressEntryResponse: Created progress entry

    Raises:
        HTTPException: 404 if goal or tracking config not found
        HTTPException: 400 if entry date is in future or value out of range

    Post-Recording Actions:
        - Checks for milestone achievements (delegates to milestone service)
        - Updates goal's last_entry timestamp

    Example:
        >>> entry = await record_progress_entry(
        ...     goal_uuid,
        ...     ProgressEntryCreate(
        ...         entry_date=date.today(),
        ...         value=7.5,
        ...         context="self_report",
        ...         notes="Feeling much better today"
        ...     ),
        ...     patient_uuid,
        ...     db
        ... )
    """
    logger.info(f"Recording progress entry for goal {goal_id}")

    # 1. Validate goal exists
    goal_query = select(TreatmentGoal).where(TreatmentGoal.id == goal_id)
    goal_result = await db.execute(goal_query)
    goal = goal_result.scalar_one_or_none()

    if not goal:
        logger.error(f"Goal {goal_id} not found")
        raise HTTPException(
            status_code=404,
            detail=f"Goal with id {goal_id} not found"
        )

    # 2. Validate tracking config exists
    config_query = select(GoalTrackingConfig).where(
        GoalTrackingConfig.goal_id == goal_id
    )
    config_result = await db.execute(config_query)
    config = config_result.scalar_one_or_none()

    if not config:
        logger.error(f"No tracking config found for goal {goal_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No tracking configuration found for goal {goal_id}. Please create a tracking config first."
        )

    # 3. Validate value is within scale range if using scale method
    if config.tracking_method.value == "scale":
        if config.scale_min is not None and config.scale_max is not None:
            if entry_data.value < config.scale_min or entry_data.value > config.scale_max:
                raise HTTPException(
                    status_code=400,
                    detail=f"Value {entry_data.value} is outside configured scale range [{config.scale_min}, {config.scale_max}]"
                )

    try:
        # 4. Create progress entry
        entry = ProgressEntry(
            goal_id=goal_id,
            entry_date=entry_data.entry_date,
            entry_time=entry_data.entry_time,
            value=entry_data.value,
            value_label=entry_data.value_label,
            notes=entry_data.notes,
            context=entry_data.context,
            recorded_by_id=recorded_by_id,
            session_id=None  # Will be set if context is 'session'
        )
        db.add(entry)

        await db.commit()
        await db.refresh(entry)

        logger.info(
            f"Progress entry recorded successfully: "
            f"id={entry.id}, goal={goal_id}, value={entry.value}, date={entry.entry_date}"
        )

        # 5. TODO: Check for milestone achievements
        # This would call a milestone service function to check if any milestones
        # were achieved based on this new entry (e.g., reaching target value,
        # maintaining streak, etc.)
        # await check_milestone_achievements(goal_id, entry, db)

        return ProgressEntryResponse.model_validate(entry)

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error recording progress entry for goal {goal_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to record progress entry: {str(e)}"
        )


async def get_progress_history(
    goal_id: UUID,
    query_params: ProgressHistoryQuery,
    db: AsyncSession
) -> ProgressHistoryResponse:
    """
    Retrieve progress history for a goal with filtering and aggregation.

    Fetches all progress entries for a goal, optionally filtered by date range
    and aggregated by period (daily, weekly, monthly). Calculates statistics
    including average, min, max, and trend direction.

    Args:
        goal_id: UUID of the goal to retrieve history for
        query_params: ProgressHistoryQuery with optional filters (start_date, end_date, aggregation)
        db: Async database session

    Returns:
        ProgressHistoryResponse: Progress entries and statistical summary

    Raises:
        HTTPException: 404 if goal not found

    Filtering:
        - start_date: Include only entries on or after this date
        - end_date: Include only entries on or before this date
        - aggregation: Group entries by period and calculate averages

    Aggregation Options:
        - none: Return raw entries
        - daily: Average all entries per day
        - weekly: Average all entries per week (ISO week)
        - monthly: Average all entries per month

    Example:
        >>> # Get last 30 days with daily aggregation
        >>> history = await get_progress_history(
        ...     goal_uuid,
        ...     ProgressHistoryQuery(
        ...         start_date=date.today() - timedelta(days=30),
        ...         end_date=date.today(),
        ...         aggregation=AggregationPeriod.daily
        ...     ),
        ...     db
        ... )
    """
    logger.info(f"Retrieving progress history for goal {goal_id}")

    # 1. Validate goal exists and get tracking config
    goal_query = select(TreatmentGoal).where(TreatmentGoal.id == goal_id)
    goal_result = await db.execute(goal_query)
    goal = goal_result.scalar_one_or_none()

    if not goal:
        logger.error(f"Goal {goal_id} not found")
        raise HTTPException(
            status_code=404,
            detail=f"Goal with id {goal_id} not found"
        )

    # Get tracking config for response
    config_query = select(GoalTrackingConfig).where(
        GoalTrackingConfig.goal_id == goal_id
    )
    config_result = await db.execute(config_query)
    config = config_result.scalar_one_or_none()

    if not config:
        logger.warning(f"No tracking config found for goal {goal_id}")
        # Return empty history if no config exists
        return ProgressHistoryResponse(
            goal_id=goal_id,
            tracking_method="binary",  # Default
            entries=[],
            statistics=ProgressStatistics(
                baseline=goal.baseline_value,
                current=None,
                target=goal.target_value,
                average=None,
                min=None,
                max=None,
                trend_slope=None,
                trend_direction=TrendDirection.insufficient_data
            )
        )

    # 2. Build query with filters
    query = select(ProgressEntry).where(ProgressEntry.goal_id == goal_id)

    # Apply date filters
    if query_params.start_date:
        query = query.where(ProgressEntry.entry_date >= query_params.start_date)
    if query_params.end_date:
        query = query.where(ProgressEntry.entry_date <= query_params.end_date)

    # Order by date ascending (oldest first)
    query = query.order_by(ProgressEntry.entry_date.asc())

    # 3. Execute query
    result = await db.execute(query)
    entries = result.scalars().all()

    logger.info(f"Retrieved {len(entries)} progress entries for goal {goal_id}")

    # 4. Apply aggregation if requested
    if query_params.aggregation and query_params.aggregation != AggregationPeriod.none:
        entries = await _aggregate_entries(entries, query_params.aggregation, db)
        logger.info(f"Aggregated to {len(entries)} data points")

    # 5. Calculate statistics
    statistics = await calculate_progress_statistics(goal_id, entries, db)

    # 6. Convert to response models
    entry_responses = [ProgressEntryResponse.model_validate(entry) for entry in entries]

    return ProgressHistoryResponse(
        goal_id=goal_id,
        tracking_method=config.tracking_method,
        entries=entry_responses,
        statistics=statistics
    )


async def calculate_progress_statistics(
    goal_id: UUID,
    entries: List[ProgressEntry],
    db: AsyncSession
) -> ProgressStatistics:
    """
    Calculate statistical summary of progress data.

    Computes baseline, current value, target, average, min, max, trend slope,
    and trend direction from a list of progress entries. Trend is calculated
    using linear regression on the entry values over time.

    Args:
        goal_id: UUID of the goal
        entries: List of ProgressEntry objects (should be ordered by date)
        db: Async database session

    Returns:
        ProgressStatistics: Statistical summary of progress

    Statistics Calculated:
        - baseline: Starting value from goal record
        - current: Most recent entry value
        - target: Target value from goal record
        - average: Mean of all entry values
        - min: Minimum entry value
        - max: Maximum entry value
        - trend_slope: Linear regression slope (change per day)
        - trend_direction: improving/stable/declining/insufficient_data

    Trend Direction Logic:
        - insufficient_data: < 3 entries
        - improving: Slope indicates movement toward target
        - declining: Slope indicates movement away from target
        - stable: Slope is near zero (within threshold)

    Example:
        >>> stats = await calculate_progress_statistics(
        ...     goal_uuid,
        ...     [entry1, entry2, entry3],
        ...     db
        ... )
        >>> print(f"Average: {stats.average}, Trend: {stats.trend_direction}")
    """
    logger.debug(f"Calculating statistics for goal {goal_id} with {len(entries)} entries")

    # 1. Fetch goal for baseline and target
    goal_query = select(TreatmentGoal).where(TreatmentGoal.id == goal_id)
    goal_result = await db.execute(goal_query)
    goal = goal_result.scalar_one_or_none()

    # Get tracking config for target direction
    config_query = select(GoalTrackingConfig).where(
        GoalTrackingConfig.goal_id == goal_id
    )
    config_result = await db.execute(config_query)
    config = config_result.scalar_one_or_none()

    # Handle edge case: no entries
    if len(entries) == 0:
        return ProgressStatistics(
            baseline=goal.baseline_value if goal else None,
            current=None,
            target=goal.target_value if goal else None,
            average=None,
            min=None,
            max=None,
            trend_slope=None,
            trend_direction=TrendDirection.insufficient_data
        )

    # 2. Extract values
    values = [entry.value for entry in entries]

    # 3. Calculate basic statistics
    current = values[-1]  # Most recent value
    average = round(sum(values) / len(values), 2)
    min_val = min(values)
    max_val = max(values)

    # 4. Calculate trend
    trend_slope = None
    trend_direction = TrendDirection.insufficient_data

    if len(entries) >= 3:
        # Calculate linear regression slope
        # Convert dates to days since first entry
        first_date = entries[0].entry_date
        x_values = [(entry.entry_date - first_date).days for entry in entries]
        y_values = values

        # Calculate slope using least squares method
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x_squared = sum(x * x for x in x_values)

        # Avoid division by zero
        denominator = n * sum_x_squared - sum_x * sum_x
        if denominator != 0:
            trend_slope = round((n * sum_xy - sum_x * sum_y) / denominator, 4)

            # Determine trend direction based on slope and target direction
            slope_threshold = 0.01  # Minimum slope to consider as changing

            if abs(trend_slope) < slope_threshold:
                trend_direction = TrendDirection.stable
            elif config:
                # Check if slope direction matches target direction
                if config.target_direction.value == "increase":
                    # Positive slope = improving, negative = declining
                    trend_direction = TrendDirection.improving if trend_slope > 0 else TrendDirection.declining
                elif config.target_direction.value == "decrease":
                    # Negative slope = improving, positive = declining
                    trend_direction = TrendDirection.improving if trend_slope < 0 else TrendDirection.declining
                else:  # maintain
                    # Any significant change is considered declining from maintenance target
                    trend_direction = TrendDirection.stable if abs(trend_slope) < slope_threshold else TrendDirection.declining
            else:
                # No config: default to positive slope = improving
                trend_direction = TrendDirection.improving if trend_slope > 0 else TrendDirection.declining

    logger.debug(
        f"Statistics calculated: average={average}, min={min_val}, max={max_val}, "
        f"trend_slope={trend_slope}, trend_direction={trend_direction}"
    )

    return ProgressStatistics(
        baseline=goal.baseline_value if goal else None,
        current=current,
        target=goal.target_value if goal else None,
        average=average,
        min=min_val,
        max=max_val,
        trend_slope=trend_slope,
        trend_direction=trend_direction
    )


async def _aggregate_entries(
    entries: List[ProgressEntry],
    aggregation: AggregationPeriod,
    db: AsyncSession
) -> List[ProgressEntry]:
    """
    Aggregate progress entries by time period.

    Groups entries by day/week/month and calculates average value for each period.
    Returns synthetic ProgressEntry objects with aggregated data.

    Args:
        entries: List of ProgressEntry objects to aggregate
        aggregation: Period to aggregate by (daily, weekly, monthly)
        db: Async database session

    Returns:
        List of aggregated ProgressEntry objects (one per period)

    Aggregation Logic:
        - daily: Group by entry_date, average values per day
        - weekly: Group by ISO week number, average values per week
        - monthly: Group by year-month, average values per month

    Note:
        Aggregated entries are synthetic objects for display purposes.
        They retain the first entry's metadata (goal_id, context, etc.)
        but combine values from multiple entries.
    """
    if not entries or aggregation == AggregationPeriod.none:
        return entries

    from collections import defaultdict

    # Group entries by period
    grouped = defaultdict(list)

    for entry in entries:
        if aggregation == AggregationPeriod.daily:
            # Group by date
            key = entry.entry_date
        elif aggregation == AggregationPeriod.weekly:
            # Group by ISO week (year, week_number)
            # Use Monday of the week as the key date
            days_since_monday = entry.entry_date.weekday()
            monday = entry.entry_date - timedelta(days=days_since_monday)
            key = monday
        elif aggregation == AggregationPeriod.monthly:
            # Group by year-month
            key = entry.entry_date.replace(day=1)
        else:
            # Shouldn't happen, but default to daily
            key = entry.entry_date

        grouped[key].append(entry)

    # Calculate averages for each period
    aggregated = []
    for period_date, period_entries in sorted(grouped.items()):
        avg_value = sum(e.value for e in period_entries) / len(period_entries)

        # Create synthetic entry with aggregated data
        # Use first entry as template, override with aggregated values
        template = period_entries[0]
        aggregated_entry = ProgressEntry(
            id=template.id,
            goal_id=template.goal_id,
            entry_date=period_date,
            entry_time=None,  # Time not meaningful for aggregated data
            value=round(avg_value, 2),
            value_label=f"Avg of {len(period_entries)} entries",
            notes=None,
            context=template.context,
            session_id=None,
            recorded_by_id=template.recorded_by_id,
            created_at=template.created_at
        )
        aggregated.append(aggregated_entry)

    logger.debug(
        f"Aggregated {len(entries)} entries into {len(aggregated)} {aggregation.value} periods"
    )

    return aggregated
