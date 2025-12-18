"""
Report Generator Service for Progress Reports

Generates comprehensive progress reports aggregating:
- Treatment goals progress over time period
- Assessment score changes and interpretations
- Clinical observations and recommendations
- Patient summary statistics
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from uuid import UUID
from datetime import date as date_type, datetime, timedelta
from typing import List, Dict, Optional
from decimal import Decimal
import logging

from app.schemas.report_schemas import (
    ProgressReportResponse,
    ReportPeriod,
    PatientSummary,
    GoalSummaryItem,
    AssessmentChange,
    GoalStatus
)
from app.models.db_models import User, TherapySession
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import ProgressEntry, AssessmentScore

# Configure logger
logger = logging.getLogger(__name__)


async def generate_progress_report(
    patient_id: UUID,
    start_date: date_type,
    end_date: date_type,
    db: AsyncSession
) -> ProgressReportResponse:
    """
    Generate comprehensive progress report for a patient over a date range.

    Aggregates data from multiple sources:
    - Treatment goals with baseline and current values
    - Therapy sessions attended and missed
    - Assessment scores and changes
    - Clinical observations

    Args:
        patient_id: UUID of the patient
        start_date: Report period start date
        end_date: Report period end date
        db: Async database session

    Returns:
        ProgressReportResponse: Complete progress report with all aggregated data

    Example:
        >>> report = await generate_progress_report(
        ...     patient_id=uuid,
        ...     start_date=date(2024, 1, 1),
        ...     end_date=date(2024, 3, 10),
        ...     db=db
        ... )
        >>> print(f"Goals: {len(report.goals_summary)}")
    """
    logger.info(f"Generating progress report for patient {patient_id} from {start_date} to {end_date}")

    # Create report period
    report_period = ReportPeriod(start=start_date, end=end_date)

    # Get patient details
    patient_query = select(User).where(User.id == patient_id)
    patient_result = await db.execute(patient_query)
    patient = patient_result.scalar_one_or_none()

    if not patient:
        logger.error(f"Patient {patient_id} not found")
        raise ValueError(f"Patient {patient_id} not found")

    # Calculate patient summary statistics
    # Find earliest treatment goal or session as treatment start
    earliest_goal_query = select(func.min(TreatmentGoal.created_at)).where(
        TreatmentGoal.patient_id == patient_id
    )
    earliest_goal_result = await db.execute(earliest_goal_query)
    earliest_goal_date = earliest_goal_result.scalar()

    earliest_session_query = select(func.min(TherapySession.session_date)).where(
        TherapySession.patient_id == patient_id
    )
    earliest_session_result = await db.execute(earliest_session_query)
    earliest_session_date = earliest_session_result.scalar()

    # Use earliest date from goals or sessions
    treatment_start = earliest_goal_date.date() if earliest_goal_date else None
    if earliest_session_date:
        if not treatment_start or earliest_session_date < treatment_start:
            treatment_start = earliest_session_date

    # Default to report start date if no treatment history found
    if not treatment_start:
        treatment_start = start_date

    # Count sessions in report period
    sessions_attended_query = select(func.count(TherapySession.id)).where(
        and_(
            TherapySession.patient_id == patient_id,
            TherapySession.session_date >= start_date,
            TherapySession.session_date <= end_date,
            TherapySession.status == 'completed'
        )
    )
    sessions_attended_result = await db.execute(sessions_attended_query)
    sessions_attended = sessions_attended_result.scalar() or 0

    # Estimate missed sessions (scheduled but not completed)
    sessions_missed_query = select(func.count(TherapySession.id)).where(
        and_(
            TherapySession.patient_id == patient_id,
            TherapySession.session_date >= start_date,
            TherapySession.session_date <= end_date,
            or_(
                TherapySession.status == 'cancelled',
                TherapySession.status == 'missed'
            )
        )
    )
    sessions_missed_result = await db.execute(sessions_missed_query)
    sessions_missed = sessions_missed_result.scalar() or 0

    patient_summary = PatientSummary(
        name=patient.full_name,
        treatment_start=treatment_start,
        sessions_attended=sessions_attended,
        sessions_missed=sessions_missed
    )

    # Calculate goals summary
    goals_summary = await calculate_goal_summaries(
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )

    # Calculate assessment summary
    assessment_summary = await format_assessment_summary(
        patient_id=patient_id,
        start_date=start_date,
        end_date=end_date,
        db=db
    )

    # Generate clinical observations based on data
    clinical_observations = await generate_clinical_observations(
        goals_summary=goals_summary,
        assessment_summary=assessment_summary
    )

    # Generate recommendations (placeholder for now)
    recommendations = "Continue current treatment approach. Monitor progress on active goals. Consider adjusting intervention strategies for goals showing limited progress."

    return ProgressReportResponse(
        report_period=report_period,
        patient_summary=patient_summary,
        goals_summary=goals_summary,
        assessment_summary=assessment_summary,
        clinical_observations=clinical_observations,
        recommendations=recommendations
    )


async def calculate_goal_summaries(
    patient_id: UUID,
    start_date: date_type,
    end_date: date_type,
    db: AsyncSession
) -> List[GoalSummaryItem]:
    """
    Calculate per-goal progress analysis for report period.

    For each goal:
    - Retrieves baseline value from goal or earliest entry
    - Retrieves current value from latest entry in period
    - Calculates absolute and percentage change
    - Determines status (significant_improvement, improvement, stable, decline)

    Args:
        patient_id: UUID of the patient
        start_date: Report period start date
        end_date: Report period end date
        db: Async database session

    Returns:
        List[GoalSummaryItem]: Summary for each goal with progress data

    Status Determination:
    - significant_improvement: >= 30% positive change
    - improvement: 10-29% positive change
    - stable: -9% to +9% change
    - decline: >= 10% negative change
    """
    logger.info(f"Calculating goal summaries for patient {patient_id}")

    # Get all active goals for patient
    goals_query = select(TreatmentGoal).where(
        and_(
            TreatmentGoal.patient_id == patient_id,
            TreatmentGoal.status.in_(['assigned', 'in_progress', 'completed'])
        )
    ).order_by(TreatmentGoal.created_at)

    goals_result = await db.execute(goals_query)
    goals = goals_result.scalars().all()

    goal_summaries = []

    for goal in goals:
        # Get baseline value (earliest entry before or at start_date, or goal.baseline_value)
        baseline_value = None
        if goal.baseline_value:
            baseline_value = float(goal.baseline_value)
        else:
            # Try to get earliest progress entry
            baseline_query = select(ProgressEntry).where(
                and_(
                    ProgressEntry.goal_id == goal.id,
                    ProgressEntry.entry_date <= start_date
                )
            ).order_by(ProgressEntry.entry_date.asc()).limit(1)

            baseline_result = await db.execute(baseline_query)
            baseline_entry = baseline_result.scalar_one_or_none()

            if baseline_entry:
                baseline_value = float(baseline_entry.value)

        # Get current value (latest entry in report period)
        current_value = None
        current_query = select(ProgressEntry).where(
            and_(
                ProgressEntry.goal_id == goal.id,
                ProgressEntry.entry_date >= start_date,
                ProgressEntry.entry_date <= end_date
            )
        ).order_by(ProgressEntry.entry_date.desc()).limit(1)

        current_result = await db.execute(current_query)
        current_entry = current_result.scalar_one_or_none()

        if current_entry:
            current_value = float(current_entry.value)

        # Skip goal if we don't have both baseline and current values
        if baseline_value is None or current_value is None:
            continue

        # Calculate change
        change = current_value - baseline_value
        change_percentage = (change / baseline_value * 100) if baseline_value != 0 else 0

        # Determine status based on change percentage
        # Note: Assumes target_direction is "decrease" for symptom reduction
        # For increase-type goals, logic would be inverted
        if abs(change_percentage) >= 30:
            status = GoalStatus.significant_improvement if change_percentage < 0 else GoalStatus.decline
        elif abs(change_percentage) >= 10:
            status = GoalStatus.improvement if change_percentage < 0 else GoalStatus.decline
        else:
            status = GoalStatus.stable

        goal_summaries.append(GoalSummaryItem(
            goal=goal.description,
            baseline=baseline_value,
            current=current_value,
            change=change,
            change_percentage=change_percentage,
            status=status
        ))

    logger.info(f"Generated {len(goal_summaries)} goal summaries")
    return goal_summaries


async def format_assessment_summary(
    patient_id: UUID,
    start_date: date_type,
    end_date: date_type,
    db: AsyncSession
) -> Dict[str, AssessmentChange]:
    """
    Format assessment trend interpretation for report period.

    For each assessment type (PHQ-9, GAD-7, etc.):
    - Gets baseline score (earliest in period)
    - Gets current score (latest in period)
    - Calculates change and provides clinical interpretation

    Args:
        patient_id: UUID of the patient
        start_date: Report period start date
        end_date: Report period end date
        db: Async database session

    Returns:
        Dict[str, AssessmentChange]: Assessment changes keyed by type
            e.g., {"GAD-7": AssessmentChange(...), "PHQ-9": AssessmentChange(...)}

    Interpretation Guidelines:
    - PHQ-9: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-19 moderately severe, 20-27 severe
    - GAD-7: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-21 severe
    """
    logger.info(f"Formatting assessment summary for patient {patient_id}")

    # Get all distinct assessment types for this patient in date range
    assessment_types_query = select(AssessmentScore.assessment_type).where(
        and_(
            AssessmentScore.patient_id == patient_id,
            AssessmentScore.administered_date >= start_date,
            AssessmentScore.administered_date <= end_date
        )
    ).distinct()

    assessment_types_result = await db.execute(assessment_types_query)
    assessment_types = [row[0] for row in assessment_types_result.all()]

    assessment_summary = {}

    for assessment_type in assessment_types:
        # Get baseline (earliest in period)
        baseline_query = select(AssessmentScore).where(
            and_(
                AssessmentScore.patient_id == patient_id,
                AssessmentScore.assessment_type == assessment_type,
                AssessmentScore.administered_date >= start_date,
                AssessmentScore.administered_date <= end_date
            )
        ).order_by(AssessmentScore.administered_date.asc()).limit(1)

        baseline_result = await db.execute(baseline_query)
        baseline_assessment = baseline_result.scalar_one_or_none()

        # Get current (latest in period)
        current_query = select(AssessmentScore).where(
            and_(
                AssessmentScore.patient_id == patient_id,
                AssessmentScore.assessment_type == assessment_type,
                AssessmentScore.administered_date >= start_date,
                AssessmentScore.administered_date <= end_date
            )
        ).order_by(AssessmentScore.administered_date.desc()).limit(1)

        current_result = await db.execute(current_query)
        current_assessment = current_result.scalar_one_or_none()

        if baseline_assessment and current_assessment:
            baseline_score = baseline_assessment.score
            current_score = current_assessment.score
            change = current_score - baseline_score

            # Generate interpretation text
            baseline_severity = baseline_assessment.severity or "unknown"
            current_severity = current_assessment.severity or "unknown"

            if change < 0:
                interpretation = f"Improved from {baseline_severity} ({baseline_score}) to {current_severity} ({current_score}). Score decreased by {abs(change)} points."
            elif change > 0:
                interpretation = f"Worsened from {baseline_severity} ({baseline_score}) to {current_severity} ({current_score}). Score increased by {change} points."
            else:
                interpretation = f"Remained stable at {current_severity} severity ({current_score} points)."

            assessment_summary[assessment_type] = AssessmentChange(
                baseline=baseline_score,
                current=current_score,
                change=change,
                interpretation=interpretation
            )

    logger.info(f"Generated assessment summary for {len(assessment_summary)} assessment types")
    return assessment_summary


async def generate_clinical_observations(
    goals_summary: List[GoalSummaryItem],
    assessment_summary: Dict[str, AssessmentChange]
) -> str:
    """
    Generate AI-powered clinical observations from progress data.

    Currently returns template-based observations. Future enhancement:
    - Call OpenAI API to generate narrative clinical summary
    - Include contextualized insights based on progress patterns
    - Highlight significant improvements or areas of concern

    Args:
        goals_summary: List of goal progress summaries
        assessment_summary: Dict of assessment changes by type

    Returns:
        str: Clinical observations narrative (max 2000 characters)
    """
    logger.info("Generating clinical observations")

    # Count goals by status
    significant_improvements = sum(1 for g in goals_summary if g.status == GoalStatus.significant_improvement)
    improvements = sum(1 for g in goals_summary if g.status == GoalStatus.improvement)
    stable = sum(1 for g in goals_summary if g.status == GoalStatus.stable)
    declines = sum(1 for g in goals_summary if g.status == GoalStatus.decline)

    # Build observation text
    observations = []

    if significant_improvements > 0:
        observations.append(f"Patient has shown significant improvement in {significant_improvements} goal(s), demonstrating strong engagement with treatment.")

    if improvements > 0:
        observations.append(f"Moderate progress observed in {improvements} goal(s), indicating positive response to interventions.")

    if stable > 0:
        observations.append(f"{stable} goal(s) remain stable, suggesting maintenance of current functioning.")

    if declines > 0:
        observations.append(f"{declines} goal(s) show decline, warranting review of treatment approach and potential barriers.")

    # Add assessment observations
    if assessment_summary:
        improved_assessments = [k for k, v in assessment_summary.items() if v.change < 0]
        if improved_assessments:
            observations.append(f"Standardized assessments ({', '.join(improved_assessments)}) show improvement in symptom severity.")

    if not observations:
        observations.append("Patient has shown consistent engagement with treatment. Continue monitoring progress on established goals.")

    # TODO: Future enhancement - call OpenAI API for narrative generation
    # clinical_narrative = await call_openai_for_observations(goals_summary, assessment_summary)

    return " ".join(observations)
