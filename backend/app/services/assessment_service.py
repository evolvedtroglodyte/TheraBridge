"""
Assessment tracking service for standardized clinical assessments (Feature 6)

Handles recording, severity calculation, and tracking of standardized assessments
including PHQ-9, GAD-7, BDI-II, BAI, PCL-5, and AUDIT.
"""
from typing import Optional, Dict, List
from datetime import date, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.tracking_models import AssessmentScore
from app.schemas.assessment_schemas import (
    AssessmentScoreCreate,
    AssessmentScoreResponse,
    AssessmentHistoryItem,
    AssessmentHistoryResponse,
    Severity,
    AssessmentType
)
from app.schemas.report_schemas import AssessmentDueItem


# Assessment frequency configuration (in days)
ASSESSMENT_FREQUENCIES = {
    "PHQ-9": 28,      # Every 4 weeks
    "GAD-7": 28,      # Every 4 weeks
    "BDI-II": 30,     # Monthly
    "BAI": 30,        # Monthly
    "PCL-5": None,    # As needed (no fixed frequency)
    "AUDIT": 90,      # Quarterly (after initial intake)
}


async def record_assessment(
    patient_id: UUID,
    assessment_data: AssessmentScoreCreate,
    db: Session,
    administered_by: Optional[UUID] = None
) -> AssessmentScoreResponse:
    """
    Record a new assessment score for a patient.

    Automatically calculates severity if not provided based on assessment-specific
    scoring ranges (PHQ-9, GAD-7, BDI-II).

    Args:
        patient_id: Patient UUID
        assessment_data: Assessment score data (type, score, subscores, etc.)
        db: Database session
        administered_by: UUID of user who administered assessment (optional)

    Returns:
        AssessmentScoreResponse with complete assessment data

    Example:
        >>> data = AssessmentScoreCreate(
        ...     assessment_type="GAD-7",
        ...     score=8,
        ...     administered_date=date(2024, 3, 10)
        ... )
        >>> result = await record_assessment(patient_id, data, db, therapist_id)
        >>> print(result.severity)
        "mild"
    """
    # Calculate severity if not provided
    severity = assessment_data.severity
    if severity is None:
        severity = calculate_severity(
            assessment_type=assessment_data.assessment_type.value,
            score=assessment_data.score
        )

    # Create assessment score record
    assessment_score = AssessmentScore(
        patient_id=patient_id,
        goal_id=assessment_data.goal_id,
        assessment_type=assessment_data.assessment_type.value,
        score=assessment_data.score,
        severity=severity.value if severity else None,
        subscores=assessment_data.subscores,
        administered_date=assessment_data.administered_date,
        administered_by=administered_by,
        notes=assessment_data.notes
    )

    db.add(assessment_score)
    db.commit()
    db.refresh(assessment_score)

    return AssessmentScoreResponse.model_validate(assessment_score)


def calculate_severity(assessment_type: str, score: int) -> Optional[Severity]:
    """
    Calculate severity level based on assessment type and score.

    Uses standardized severity ranges for PHQ-9, GAD-7, and BDI-II.
    Returns None for assessment types without defined severity ranges.

    Severity Ranges:
    - PHQ-9: 0-4 minimal, 5-9 mild, 10-14 moderate, 15-19 moderately_severe, 20+ severe
    - GAD-7: 0-4 minimal, 5-9 mild, 10-14 moderate, 15+ severe
    - BDI-II: 0-13 minimal, 14-19 mild, 20-28 moderate, 29+ severe

    Args:
        assessment_type: Assessment type (e.g., "PHQ-9", "GAD-7", "BDI-II")
        score: Total assessment score

    Returns:
        Severity enum value or None if assessment type not supported

    Example:
        >>> calculate_severity("GAD-7", 8)
        <Severity.mild: 'mild'>
        >>> calculate_severity("PHQ-9", 16)
        <Severity.moderately_severe: 'moderately_severe'>
    """
    if assessment_type == "PHQ-9":
        if score <= 4:
            return Severity.minimal
        elif score <= 9:
            return Severity.mild
        elif score <= 14:
            return Severity.moderate
        elif score <= 19:
            return Severity.moderately_severe
        else:  # 20+
            return Severity.severe

    elif assessment_type == "GAD-7":
        if score <= 4:
            return Severity.minimal
        elif score <= 9:
            return Severity.mild
        elif score <= 14:
            return Severity.moderate
        else:  # 15+
            return Severity.severe

    elif assessment_type == "BDI-II":
        if score <= 13:
            return Severity.minimal
        elif score <= 19:
            return Severity.mild
        elif score <= 28:
            return Severity.moderate
        else:  # 29+
            return Severity.severe

    # Return None for assessment types without defined severity ranges
    # (BAI, PCL-5, AUDIT)
    return None


async def get_assessment_history(
    patient_id: UUID,
    db: Session,
    assessment_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> AssessmentHistoryResponse:
    """
    Retrieve assessment history for a patient, optionally filtered by type and date range.

    Returns assessments grouped by type with date, score, and severity for each entry.
    Useful for trend visualization and progress tracking.

    Args:
        patient_id: Patient UUID
        db: Database session
        assessment_type: Filter by specific assessment type (optional)
        start_date: Filter from this date (optional)
        end_date: Filter to this date (optional)

    Returns:
        AssessmentHistoryResponse with assessments grouped by type

    Example:
        >>> history = await get_assessment_history(
        ...     patient_id=patient_id,
        ...     db=db,
        ...     start_date=date(2024, 1, 1),
        ...     end_date=date(2024, 3, 31)
        ... )
        >>> print(history.assessments["GAD-7"])
        [
            AssessmentHistoryItem(date="2024-01-10", score=14, severity="moderate"),
            AssessmentHistoryItem(date="2024-02-10", score=10, severity="moderate"),
            AssessmentHistoryItem(date="2024-03-10", score=8, severity="mild")
        ]
    """
    # Build query with filters
    query = db.query(AssessmentScore).filter(
        AssessmentScore.patient_id == patient_id
    )

    if assessment_type:
        query = query.filter(AssessmentScore.assessment_type == assessment_type)

    if start_date:
        query = query.filter(AssessmentScore.administered_date >= start_date)

    if end_date:
        query = query.filter(AssessmentScore.administered_date <= end_date)

    # Order by date ascending for chronological trend
    query = query.order_by(AssessmentScore.administered_date.asc())

    # Execute query
    assessments = query.all()

    # Group assessments by type
    grouped: Dict[AssessmentType, List[AssessmentHistoryItem]] = {}

    for assessment in assessments:
        # Convert assessment_type string to enum
        try:
            type_enum = AssessmentType(assessment.assessment_type)
        except ValueError:
            # Skip unknown assessment types
            continue

        if type_enum not in grouped:
            grouped[type_enum] = []

        # Create history item
        history_item = AssessmentHistoryItem(
            date=assessment.administered_date,
            score=assessment.score,
            severity=Severity(assessment.severity) if assessment.severity else None
        )

        grouped[type_enum].append(history_item)

    return AssessmentHistoryResponse(assessments=grouped)


async def check_assessments_due(
    patient_id: UUID,
    db: Session
) -> List[AssessmentDueItem]:
    """
    Calculate which assessments need administration based on last completion date.

    Uses recommended frequencies:
    - PHQ-9: Every 4 weeks (28 days)
    - GAD-7: Every 4 weeks (28 days)
    - BDI-II: Monthly (30 days)
    - BAI: Monthly (30 days)
    - PCL-5: As needed (not included in due checks)
    - AUDIT: Quarterly (90 days, after intake)

    Args:
        patient_id: Patient UUID
        db: Database session

    Returns:
        List of AssessmentDueItem for assessments that are due

    Example:
        >>> due_assessments = await check_assessments_due(patient_id, db)
        >>> for item in due_assessments:
        ...     print(f"{item.type} due on {item.due_date}")
        "GAD-7 due on 2024-03-10"
        "PHQ-9 due on 2024-03-10"
    """
    today = date.today()
    due_items: List[AssessmentDueItem] = []

    # Check each assessment type with a defined frequency
    for assessment_type, frequency_days in ASSESSMENT_FREQUENCIES.items():
        if frequency_days is None:
            # Skip "as needed" assessments like PCL-5
            continue

        # Get last administration date for this assessment type
        last_assessment = db.query(AssessmentScore).filter(
            and_(
                AssessmentScore.patient_id == patient_id,
                AssessmentScore.assessment_type == assessment_type
            )
        ).order_by(AssessmentScore.administered_date.desc()).first()

        if last_assessment:
            # Calculate due date based on last administration
            last_date = last_assessment.administered_date
            due_date = last_date + timedelta(days=frequency_days)

            # Check if assessment is due (due date is today or in the past)
            if due_date <= today:
                due_items.append(AssessmentDueItem(
                    type=assessment_type,
                    last_administered=last_date,
                    due_date=due_date
                ))
        else:
            # No prior assessment - due immediately for initial baseline
            due_items.append(AssessmentDueItem(
                type=assessment_type,
                last_administered=None,
                due_date=today
            ))

    return due_items


async def get_latest_assessments(
    patient_id: UUID,
    db: Session
) -> Dict[str, AssessmentScoreResponse]:
    """
    Get the most recent assessment score for each assessment type.

    Useful for dashboard displays and quick status overviews.
    Returns a dictionary keyed by assessment type.

    Args:
        patient_id: Patient UUID
        db: Database session

    Returns:
        Dictionary mapping assessment type to latest AssessmentScoreResponse

    Example:
        >>> latest = await get_latest_assessments(patient_id, db)
        >>> print(latest["GAD-7"].score)
        8
        >>> print(latest["PHQ-9"].severity)
        "mild"
    """
    # Subquery to get max administered_date for each assessment type
    subquery = db.query(
        AssessmentScore.assessment_type,
        func.max(AssessmentScore.administered_date).label('max_date')
    ).filter(
        AssessmentScore.patient_id == patient_id
    ).group_by(
        AssessmentScore.assessment_type
    ).subquery()

    # Query to get full assessment records for the latest dates
    latest_assessments = db.query(AssessmentScore).join(
        subquery,
        and_(
            AssessmentScore.assessment_type == subquery.c.assessment_type,
            AssessmentScore.administered_date == subquery.c.max_date,
            AssessmentScore.patient_id == patient_id
        )
    ).all()

    # Convert to dictionary keyed by assessment type
    result: Dict[str, AssessmentScoreResponse] = {}
    for assessment in latest_assessments:
        result[assessment.assessment_type] = AssessmentScoreResponse.model_validate(assessment)

    return result
