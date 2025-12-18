"""
Dashboard Service for Goal Tracking

Provides dashboard data aggregation including:
- Complete goal dashboard for patient view
- Tracking activity summaries
- Per-goal dashboard items with progress metrics
- Recent milestones and upcoming assessments
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import date as date_type, datetime, timedelta
from typing import List, Optional
from decimal import Decimal
import logging

from app.schemas.tracking_schemas import (
    GoalDashboardResponse,
    GoalDashboardItem,
    TrackingSummary,
    TrendData,
    TrendDirection,
    GoalStatus,
    TrackingFrequency
)
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import (
    GoalTrackingConfig,
    ProgressEntry,
    ProgressMilestone,
    AssessmentScore
)

# Configure logger
logger = logging.getLogger(__name__)


async def get_goal_dashboard(
    patient_id: UUID,
    db: AsyncSession
) -> GoalDashboardResponse:
    """
    Get complete goal tracking dashboard for a patient.

    Aggregates data from multiple sources:
    - Active goals with current progress
    - Tracking activity summary (entries, streak, completion rate)
    - Recent milestones achieved
    - Assessments due for administration

    Args:
        patient_id: UUID of the patient
        db: Async database session

    Returns:
        GoalDashboardResponse: Complete dashboard with all goal tracking data

    Example:
        >>> dashboard = await get_goal_dashboard(patient_id=uuid, db=db)
        >>> print(f"Active goals: {dashboard.active_goals}")
        >>> print(f"Streak: {dashboard.tracking_summary.streak_days} days")
    """
    logger.info(f"Getting goal dashboard for patient {patient_id}")

    # Count active goals
    active_goals_query = select(func.count(TreatmentGoal.id)).where(
        and_(
            TreatmentGoal.patient_id == patient_id,
            TreatmentGoal.status.in_(['assigned', 'in_progress'])
        )
    )
    active_goals_result = await db.execute(active_goals_query)
    active_goals = active_goals_result.scalar() or 0

    # Calculate tracking summary
    tracking_summary = await aggregate_tracking_summary(
        patient_id=patient_id,
        db=db
    )

    # Get per-goal dashboard items
    goals = await get_goal_dashboard_items(
        patient_id=patient_id,
        db=db
    )

    # Get recent milestones (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    milestones_query = select(ProgressMilestone, TreatmentGoal).join(
        TreatmentGoal,
        ProgressMilestone.goal_id == TreatmentGoal.id
    ).where(
        and_(
            TreatmentGoal.patient_id == patient_id,
            ProgressMilestone.achieved_at.isnot(None),
            ProgressMilestone.achieved_at >= thirty_days_ago
        )
    ).order_by(desc(ProgressMilestone.achieved_at)).limit(10)

    milestones_result = await db.execute(milestones_query)
    milestones_rows = milestones_result.all()

    recent_milestones = [
        {
            "date": milestone.achieved_at.date().isoformat(),
            "goal": goal.description,
            "milestone": milestone.title
        }
        for milestone, goal in milestones_rows
    ]

    # Get assessments due (placeholder logic - assessments due every 4 weeks)
    # OPTIMIZATION: Single query to fetch latest assessments for all types (replaces N+1 loop)
    # Fetch all assessments for this patient, filter to latest per type in Python
    assessment_types = ["GAD-7", "PHQ-9"]  # Common assessment types

    all_assessments_query = select(AssessmentScore).where(
        and_(
            AssessmentScore.patient_id == patient_id,
            AssessmentScore.assessment_type.in_(assessment_types)
        )
    ).order_by(AssessmentScore.assessment_type, desc(AssessmentScore.administered_date))

    all_assessments_result = await db.execute(all_assessments_query)
    all_assessments = all_assessments_result.scalars().all()

    # Group by assessment_type and get latest for each
    latest_by_type = {}
    for assessment in all_assessments:
        if assessment.assessment_type not in latest_by_type:
            latest_by_type[assessment.assessment_type] = assessment

    # Build assessments_due list
    assessments_due = []
    for assessment_type in assessment_types:
        last_assessment = latest_by_type.get(assessment_type)

        if last_assessment:
            # Check if due (4 weeks = 28 days since last administration)
            days_since = (date_type.today() - last_assessment.administered_date).days
            if days_since >= 28:
                assessments_due.append({
                    "type": assessment_type,
                    "last_administered": last_assessment.administered_date.isoformat(),
                    "due_date": (last_assessment.administered_date + timedelta(days=28)).isoformat()
                })
        else:
            # No baseline - assessment is due
            assessments_due.append({
                "type": assessment_type,
                "last_administered": None,
                "due_date": date_type.today().isoformat()
            })

    return GoalDashboardResponse(
        patient_id=patient_id,
        active_goals=active_goals,
        tracking_summary=tracking_summary,
        goals=goals,
        recent_milestones=recent_milestones,
        assessments_due=assessments_due
    )


async def aggregate_tracking_summary(
    patient_id: UUID,
    db: AsyncSession
) -> TrackingSummary:
    """
    Calculate overall tracking activity summary for patient.

    Metrics calculated:
    - entries_this_week: Number of progress entries in current week
    - streak_days: Consecutive days with at least one entry
    - completion_rate: Percentage of expected entries completed based on tracking frequency

    Args:
        patient_id: UUID of the patient
        db: Async database session

    Returns:
        TrackingSummary: Activity metrics for tracking engagement

    Streak Calculation:
    - Counts consecutive days (ending today) where at least one entry exists
    - Resets to 0 if any day is missed
    - Only counts days where tracking is expected based on frequency

    Completion Rate:
    - Calculates expected entries based on goal tracking frequencies
    - Daily goals: 7 entries expected per week
    - Weekly goals: 1 entry expected per week
    - Session goals: Based on session frequency (estimated 1/week)
    - Rate = actual entries / expected entries * 100
    """
    logger.info(f"Calculating tracking summary for patient {patient_id}")

    # Calculate current week boundaries
    now = datetime.utcnow()
    week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

    # Count entries this week
    entries_this_week_query = select(func.count(ProgressEntry.id)).where(
        and_(
            ProgressEntry.goal_id.in_(
                select(TreatmentGoal.id).where(TreatmentGoal.patient_id == patient_id)
            ),
            ProgressEntry.recorded_at >= week_start
        )
    )
    entries_this_week_result = await db.execute(entries_this_week_query)
    entries_this_week = entries_this_week_result.scalar() or 0

    # Calculate streak days
    # Get all progress entries for patient, ordered by date descending
    streak_query = select(ProgressEntry.entry_date).where(
        ProgressEntry.goal_id.in_(
            select(TreatmentGoal.id).where(TreatmentGoal.patient_id == patient_id)
        )
    ).distinct().order_by(desc(ProgressEntry.entry_date))

    streak_result = await db.execute(streak_query)
    entry_dates = [row[0] for row in streak_result.all()]

    streak_days = 0
    if entry_dates:
        # Check if today has an entry
        today = date_type.today()
        current_date = today

        # If no entry today, check yesterday (allow 1-day grace)
        if entry_dates[0] == today:
            streak_days = 1
            current_date = today - timedelta(days=1)
        elif entry_dates[0] == today - timedelta(days=1):
            streak_days = 1
            current_date = today - timedelta(days=2)
        else:
            # No recent entries, streak is 0
            streak_days = 0
            current_date = None

        # Count consecutive days
        if current_date:
            for entry_date in entry_dates[1:]:
                if entry_date == current_date:
                    streak_days += 1
                    current_date -= timedelta(days=1)
                elif entry_date < current_date:
                    # Gap found, break streak
                    break

    # Calculate completion rate
    # Get all active goals with tracking configs
    goals_query = select(TreatmentGoal, GoalTrackingConfig).outerjoin(
        GoalTrackingConfig,
        TreatmentGoal.id == GoalTrackingConfig.goal_id
    ).where(
        and_(
            TreatmentGoal.patient_id == patient_id,
            TreatmentGoal.status.in_(['assigned', 'in_progress'])
        )
    )

    goals_result = await db.execute(goals_query)
    goals_with_configs = goals_result.all()

    # Calculate expected entries this week based on tracking frequency
    expected_entries = 0
    for goal, config in goals_with_configs:
        if config:
            if config.tracking_frequency == 'daily':
                expected_entries += 7  # 7 days per week
            elif config.tracking_frequency == 'weekly':
                expected_entries += 1  # 1 entry per week
            elif config.tracking_frequency == 'session':
                expected_entries += 1  # Estimate 1 session per week
            elif config.tracking_frequency == 'custom' and config.custom_frequency_days:
                # Calculate entries based on custom frequency
                entries_per_week = 7 / config.custom_frequency_days
                expected_entries += entries_per_week

    # Calculate completion rate percentage
    if expected_entries > 0:
        completion_rate = min((entries_this_week / expected_entries) * 100, 100.0)
    else:
        completion_rate = 0.0

    logger.info(f"Tracking summary: {entries_this_week} entries, {streak_days} day streak, {completion_rate:.1f}% completion")

    return TrackingSummary(
        entries_this_week=entries_this_week,
        streak_days=streak_days,
        completion_rate=completion_rate
    )


async def get_goal_dashboard_items(
    patient_id: UUID,
    db: AsyncSession
) -> List[GoalDashboardItem]:
    """
    Get per-goal dashboard data with progress metrics.

    For each active goal:
    - Current value (latest progress entry)
    - Progress percentage toward target
    - Trend direction (improving/stable/declining)
    - Trend data for visualization (last 30 days)
    - Next check-in date based on tracking frequency

    Args:
        patient_id: UUID of the patient
        db: Async database session

    Returns:
        List[GoalDashboardItem]: Dashboard item for each goal with metrics

    Progress Percentage Calculation:
    - (current - baseline) / (target - baseline) * 100
    - Capped at 0-100 range
    - Accounts for direction (increase vs decrease goals)

    Trend Calculation:
    - Uses last 30 days of data
    - Applies simple linear regression for slope
    - Direction: improving (slope aligns with target), stable, or declining
    """
    logger.info(f"Getting goal dashboard items for patient {patient_id}")

    # Get all active goals with tracking configs
    # Eager load progress_entries to avoid N+1 queries (loads all entries in single query)
    goals_query = select(TreatmentGoal, GoalTrackingConfig).outerjoin(
        GoalTrackingConfig,
        TreatmentGoal.id == GoalTrackingConfig.goal_id
    ).where(
        and_(
            TreatmentGoal.patient_id == patient_id,
            TreatmentGoal.status.in_(['assigned', 'in_progress', 'completed'])
        )
    ).options(
        selectinload(TreatmentGoal.progress_entries)
    ).order_by(TreatmentGoal.created_at)

    goals_result = await db.execute(goals_query)
    goals_with_configs = goals_result.all()

    dashboard_items = []

    for goal, config in goals_with_configs:
        # Use pre-loaded progress_entries to get latest entry (avoids N+1 query)
        # Filter and sort in Python since entries are already loaded
        latest_entry = None
        if goal.progress_entries:
            latest_entry = max(goal.progress_entries, key=lambda e: e.entry_date)

        current_value = float(latest_entry.value) if latest_entry else None

        # Calculate progress percentage
        progress_percentage = None
        if goal.baseline_value and goal.target_value and current_value is not None:
            baseline = float(goal.baseline_value)
            target = float(goal.target_value)

            if target != baseline:
                # Calculate progress as percentage of distance from baseline to target
                progress = (current_value - baseline) / (target - baseline) * 100
                # Cap at 0-100
                progress_percentage = max(0.0, min(100.0, progress))

        # Get trend data (last 30 days)
        # Use pre-loaded progress_entries and filter by date in Python (avoids N+1 query)
        thirty_days_ago = date_type.today() - timedelta(days=30)
        trend_entries = [
            entry for entry in goal.progress_entries
            if entry.entry_date >= thirty_days_ago
        ]
        # Sort by entry_date in Python (already optimized since entries are in memory)
        trend_entries = sorted(trend_entries, key=lambda e: e.entry_date)

        # Build trend data points
        trend_data = [
            TrendData(date=entry.entry_date, value=float(entry.value))
            for entry in trend_entries
        ]

        # Calculate trend direction
        trend = TrendDirection.insufficient_data
        if len(trend_entries) >= 3:
            # Simple trend calculation: compare first half vs second half
            mid_point = len(trend_entries) // 2
            first_half_avg = sum(float(e.value) for e in trend_entries[:mid_point]) / mid_point
            second_half_avg = sum(float(e.value) for e in trend_entries[mid_point:]) / (len(trend_entries) - mid_point)

            change = second_half_avg - first_half_avg
            change_percentage = (change / first_half_avg * 100) if first_half_avg != 0 else 0

            # Determine if improving based on target direction
            target_direction = config.target_direction if config else 'decrease'

            if abs(change_percentage) < 5:
                trend = TrendDirection.stable
            elif target_direction == 'decrease':
                trend = TrendDirection.improving if change < 0 else TrendDirection.declining
            elif target_direction == 'increase':
                trend = TrendDirection.improving if change > 0 else TrendDirection.declining
            else:
                # Maintain direction
                trend = TrendDirection.stable

        # Calculate next check-in date
        next_check_in = None
        if config and latest_entry:
            if config.tracking_frequency == 'daily':
                next_check_in = latest_entry.entry_date + timedelta(days=1)
            elif config.tracking_frequency == 'weekly':
                next_check_in = latest_entry.entry_date + timedelta(days=7)
            elif config.tracking_frequency == 'custom' and config.custom_frequency_days:
                next_check_in = latest_entry.entry_date + timedelta(days=config.custom_frequency_days)
            elif config.tracking_frequency == 'session':
                # Estimate next session in 7 days
                next_check_in = latest_entry.entry_date + timedelta(days=7)

        # Get last entry datetime (for last_entry field)
        last_entry_datetime = latest_entry.recorded_at if latest_entry else None

        dashboard_items.append(GoalDashboardItem(
            id=goal.id,
            description=goal.description,
            category=goal.category,
            status=GoalStatus(goal.status),
            current_value=current_value,
            baseline_value=float(goal.baseline_value) if goal.baseline_value else None,
            target_value=float(goal.target_value) if goal.target_value else None,
            progress_percentage=progress_percentage,
            trend=trend,
            trend_data=trend_data,
            last_entry=last_entry_datetime,
            next_check_in=next_check_in
        ))

    logger.info(f"Generated {len(dashboard_items)} dashboard items")
    return dashboard_items
