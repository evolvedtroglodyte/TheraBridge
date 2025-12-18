"""
Test helper utilities for goal tracking tests.

This module provides reusable test utilities for:
- Creating test goals with defaults
- Creating progress entries
- Validating response schemas
- Mocking services
- Generating trend data

All utilities are fully typed and documented for easy reuse across test suites.
"""

from datetime import datetime, date, time, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4
from decimal import Decimal

from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import (
    GoalTrackingConfig,
    ProgressEntry,
    AssessmentScore,
    ProgressMilestone,
    GoalReminder,
)
from app.schemas.tracking_schemas import (
    TreatmentGoalResponse,
    ProgressEntryResponse,
    ProgressStatistics,
    TrendDirection,
    GoalStatus,
    TrackingMethod,
    TrackingFrequency,
    TargetDirection,
    EntryContext,
)


# ============================================================================
# Goal Creation Helpers
# ============================================================================

def create_test_goal(
    patient_id: UUID,
    therapist_id: UUID,
    description: str = "Practice mindfulness meditation daily",
    category: Optional[str] = "Anxiety management",
    status: str = "assigned",
    baseline_value: Optional[float] = 3.0,
    target_value: Optional[float] = 8.0,
    target_date: Optional[date] = None,
    session_id: Optional[UUID] = None,
    **kwargs
) -> TreatmentGoal:
    """
    Create a TreatmentGoal instance with sensible defaults for testing.

    This helper simplifies goal creation by providing reasonable defaults
    while allowing full customization through kwargs.

    Args:
        patient_id: UUID of the patient this goal belongs to (required)
        therapist_id: UUID of the therapist who created the goal (required)
        description: Goal description (default: "Practice mindfulness meditation daily")
        category: Goal category (default: "Anxiety management")
        status: Goal status (default: "assigned")
        baseline_value: Starting value for tracking (default: 3.0)
        target_value: Target value to achieve (default: 8.0)
        target_date: Target completion date (default: 30 days from now)
        session_id: Optional session ID if goal was created during a session
        **kwargs: Additional fields to override (e.g., created_at, completed_at)

    Returns:
        TreatmentGoal instance ready for database insertion

    Example:
        >>> goal = create_test_goal(
        ...     patient_id=patient.id,
        ...     therapist_id=therapist.id,
        ...     description="Reduce anxiety attacks",
        ...     baseline_value=5.0,
        ...     target_value=2.0
        ... )
        >>> db.add(goal)
        >>> db.commit()
    """
    if target_date is None:
        target_date = date.today() + timedelta(days=30)

    goal_data = {
        "id": kwargs.pop("id", uuid4()),
        "patient_id": patient_id,
        "therapist_id": therapist_id,
        "session_id": session_id,
        "description": description,
        "category": category,
        "status": status,
        "baseline_value": baseline_value,
        "target_value": target_value,
        "target_date": target_date,
        "created_at": kwargs.pop("created_at", datetime.utcnow()),
        "updated_at": kwargs.pop("updated_at", datetime.utcnow()),
        "completed_at": kwargs.pop("completed_at", None),
    }

    # Override with any additional kwargs
    goal_data.update(kwargs)

    return TreatmentGoal(**goal_data)


def create_test_tracking_config(
    goal_id: UUID,
    tracking_method: str = "scale",
    tracking_frequency: str = "daily",
    scale_min: int = 1,
    scale_max: int = 10,
    target_direction: str = "increase",
    reminder_enabled: bool = True,
    **kwargs
) -> GoalTrackingConfig:
    """
    Create a GoalTrackingConfig instance with defaults for testing.

    Args:
        goal_id: UUID of the goal this config belongs to (required)
        tracking_method: Method for tracking ('scale', 'frequency', 'duration', 'binary', 'assessment')
        tracking_frequency: How often to track ('daily', 'weekly', 'session', 'custom')
        scale_min: Minimum scale value (default: 1)
        scale_max: Maximum scale value (default: 10)
        target_direction: Desired direction of change ('increase', 'decrease', 'maintain')
        reminder_enabled: Whether to send reminders (default: True)
        **kwargs: Additional fields to override

    Returns:
        GoalTrackingConfig instance ready for database insertion

    Example:
        >>> config = create_test_tracking_config(
        ...     goal_id=goal.id,
        ...     tracking_method="scale",
        ...     scale_min=1,
        ...     scale_max=10
        ... )
        >>> db.add(config)
        >>> db.commit()
    """
    config_data = {
        "id": kwargs.pop("id", uuid4()),
        "goal_id": goal_id,
        "tracking_method": tracking_method,
        "tracking_frequency": tracking_frequency,
        "scale_min": scale_min,
        "scale_max": scale_max,
        "target_direction": target_direction,
        "reminder_enabled": reminder_enabled,
        "created_at": kwargs.pop("created_at", datetime.utcnow()),
    }

    # Add optional fields if provided
    if "custom_frequency_days" in kwargs:
        config_data["custom_frequency_days"] = kwargs.pop("custom_frequency_days")
    if "scale_labels" in kwargs:
        config_data["scale_labels"] = kwargs.pop("scale_labels")
    if "frequency_unit" in kwargs:
        config_data["frequency_unit"] = kwargs.pop("frequency_unit")
    if "duration_unit" in kwargs:
        config_data["duration_unit"] = kwargs.pop("duration_unit")

    # Override with any additional kwargs
    config_data.update(kwargs)

    return GoalTrackingConfig(**config_data)


# ============================================================================
# Progress Entry Helpers
# ============================================================================

def create_test_progress_entry(
    goal_id: UUID,
    value: float,
    entry_date: Optional[date] = None,
    entry_time: Optional[time] = None,
    context: str = "self_report",
    notes: Optional[str] = None,
    value_label: Optional[str] = None,
    tracking_config_id: Optional[UUID] = None,
    session_id: Optional[UUID] = None,
    recorded_by: Optional[UUID] = None,
    **kwargs
) -> ProgressEntry:
    """
    Create a ProgressEntry instance with defaults for testing.

    Args:
        goal_id: UUID of the goal this entry belongs to (required)
        value: Numeric progress value (required)
        entry_date: Date of entry (default: today)
        entry_time: Time of entry (optional)
        context: Entry context ('session', 'self_report', 'assessment')
        notes: Additional notes about this entry
        value_label: Human-readable label for the value
        tracking_config_id: Optional tracking config ID
        session_id: Optional session ID if recorded during a session
        recorded_by: Optional user ID who recorded the entry
        **kwargs: Additional fields to override

    Returns:
        ProgressEntry instance ready for database insertion

    Example:
        >>> entry = create_test_progress_entry(
        ...     goal_id=goal.id,
        ...     value=7.5,
        ...     notes="Feeling much better today",
        ...     context="self_report"
        ... )
        >>> db.add(entry)
        >>> db.commit()
    """
    if entry_date is None:
        entry_date = date.today()

    entry_data = {
        "id": kwargs.pop("id", uuid4()),
        "goal_id": goal_id,
        "tracking_config_id": tracking_config_id,
        "session_id": session_id,
        "recorded_by": recorded_by,
        "entry_date": entry_date,
        "entry_time": entry_time,
        "value": value,
        "value_label": value_label,
        "notes": notes,
        "context": context,
        "recorded_at": kwargs.pop("recorded_at", datetime.utcnow()),
    }

    # Override with any additional kwargs
    entry_data.update(kwargs)

    return ProgressEntry(**entry_data)


def create_test_assessment_score(
    patient_id: UUID,
    assessment_type: str = "PHQ-9",
    score: int = 12,
    severity: str = "moderate",
    administered_date: Optional[date] = None,
    goal_id: Optional[UUID] = None,
    administered_by: Optional[UUID] = None,
    **kwargs
) -> AssessmentScore:
    """
    Create an AssessmentScore instance with defaults for testing.

    Args:
        patient_id: UUID of the patient (required)
        assessment_type: Type of assessment (default: "PHQ-9")
        score: Total assessment score (default: 12)
        severity: Severity classification (default: "moderate")
        administered_date: Date administered (default: today)
        goal_id: Optional goal ID this assessment relates to
        administered_by: Optional user ID who administered the assessment
        **kwargs: Additional fields to override

    Returns:
        AssessmentScore instance ready for database insertion

    Example:
        >>> assessment = create_test_assessment_score(
        ...     patient_id=patient.id,
        ...     assessment_type="GAD-7",
        ...     score=15,
        ...     severity="severe"
        ... )
        >>> db.add(assessment)
        >>> db.commit()
    """
    if administered_date is None:
        administered_date = date.today()

    assessment_data = {
        "id": kwargs.pop("id", uuid4()),
        "patient_id": patient_id,
        "goal_id": goal_id,
        "administered_by": administered_by,
        "assessment_type": assessment_type,
        "score": score,
        "severity": severity,
        "administered_date": administered_date,
        "created_at": kwargs.pop("created_at", datetime.utcnow()),
    }

    # Add optional fields if provided
    if "subscores" in kwargs:
        assessment_data["subscores"] = kwargs.pop("subscores")
    if "notes" in kwargs:
        assessment_data["notes"] = kwargs.pop("notes")

    # Override with any additional kwargs
    assessment_data.update(kwargs)

    return AssessmentScore(**assessment_data)


# ============================================================================
# Response Validation Helpers
# ============================================================================

def assert_goal_response(
    response_data: Dict[str, Any],
    expected_patient_id: Optional[UUID] = None,
    expected_therapist_id: Optional[UUID] = None,
    expected_status: Optional[str] = None,
    expected_description: Optional[str] = None,
) -> None:
    """
    Validate that a goal response matches the expected schema and values.

    This helper performs comprehensive validation of goal response data,
    checking both schema compliance and optional expected values.

    Args:
        response_data: Goal response dictionary from API
        expected_patient_id: Optional patient ID to verify
        expected_therapist_id: Optional therapist ID to verify
        expected_status: Optional status to verify
        expected_description: Optional description to verify

    Raises:
        AssertionError: If validation fails

    Example:
        >>> response = client.get(f"/api/goals/{goal_id}")
        >>> assert_goal_response(
        ...     response.json(),
        ...     expected_patient_id=patient.id,
        ...     expected_status="in_progress"
        ... )
    """
    # Check required fields exist
    assert "id" in response_data, "Response missing 'id' field"
    assert "patient_id" in response_data, "Response missing 'patient_id' field"
    assert "therapist_id" in response_data, "Response missing 'therapist_id' field"
    assert "description" in response_data, "Response missing 'description' field"
    assert "status" in response_data, "Response missing 'status' field"
    assert "created_at" in response_data, "Response missing 'created_at' field"
    assert "updated_at" in response_data, "Response missing 'updated_at' field"

    # Validate field types
    assert isinstance(response_data["description"], str), "description must be a string"
    assert len(response_data["description"]) > 0, "description cannot be empty"
    assert response_data["status"] in ["assigned", "in_progress", "completed", "abandoned"], \
        f"Invalid status: {response_data['status']}"

    # Validate optional numeric fields if present
    if response_data.get("baseline_value") is not None:
        assert isinstance(response_data["baseline_value"], (int, float)), \
            "baseline_value must be numeric"
    if response_data.get("target_value") is not None:
        assert isinstance(response_data["target_value"], (int, float)), \
            "target_value must be numeric"

    # Check expected values if provided
    if expected_patient_id is not None:
        assert str(response_data["patient_id"]) == str(expected_patient_id), \
            f"Expected patient_id {expected_patient_id}, got {response_data['patient_id']}"
    if expected_therapist_id is not None:
        assert str(response_data["therapist_id"]) == str(expected_therapist_id), \
            f"Expected therapist_id {expected_therapist_id}, got {response_data['therapist_id']}"
    if expected_status is not None:
        assert response_data["status"] == expected_status, \
            f"Expected status {expected_status}, got {response_data['status']}"
    if expected_description is not None:
        assert response_data["description"] == expected_description, \
            f"Expected description {expected_description}, got {response_data['description']}"


def assert_progress_statistics(
    stats: Dict[str, Any],
    expected_trend: Optional[str] = None,
    min_entries: int = 0,
) -> None:
    """
    Validate progress statistics structure and values.

    Args:
        stats: Statistics dictionary from API response
        expected_trend: Optional expected trend direction to verify
        min_entries: Minimum number of data points expected for valid stats

    Raises:
        AssertionError: If validation fails

    Example:
        >>> response = client.get(f"/api/goals/{goal_id}/progress")
        >>> stats = response.json()["statistics"]
        >>> assert_progress_statistics(
        ...     stats,
        ...     expected_trend="improving",
        ...     min_entries=3
        ... )
    """
    # Check required fields
    assert "trend_direction" in stats, "Statistics missing 'trend_direction' field"

    # Validate trend direction
    valid_trends = ["improving", "stable", "declining", "insufficient_data"]
    assert stats["trend_direction"] in valid_trends, \
        f"Invalid trend_direction: {stats['trend_direction']}"

    # If we have numeric statistics, validate them
    if stats.get("average") is not None:
        assert isinstance(stats["average"], (int, float)), "average must be numeric"
    if stats.get("min") is not None:
        assert isinstance(stats["min"], (int, float)), "min must be numeric"
    if stats.get("max") is not None:
        assert isinstance(stats["max"], (int, float)), "max must be numeric"

    # Validate min/max relationship if both present
    if stats.get("min") is not None and stats.get("max") is not None:
        assert stats["min"] <= stats["max"], "min must be less than or equal to max"

    # Check expected trend if provided
    if expected_trend is not None:
        assert stats["trend_direction"] == expected_trend, \
            f"Expected trend {expected_trend}, got {stats['trend_direction']}"

    # Validate sufficient data if minimum entries specified
    if min_entries > 0 and stats["trend_direction"] == "insufficient_data":
        assert False, f"Expected at least {min_entries} entries but got insufficient_data"


def assert_progress_entry_response(
    entry_data: Dict[str, Any],
    expected_goal_id: Optional[UUID] = None,
    expected_value: Optional[float] = None,
    expected_context: Optional[str] = None,
) -> None:
    """
    Validate progress entry response structure and values.

    Args:
        entry_data: Progress entry dictionary from API response
        expected_goal_id: Optional goal ID to verify
        expected_value: Optional value to verify
        expected_context: Optional context to verify

    Raises:
        AssertionError: If validation fails

    Example:
        >>> response = client.post("/api/goals/{goal_id}/progress", json={...})
        >>> assert_progress_entry_response(
        ...     response.json(),
        ...     expected_goal_id=goal.id,
        ...     expected_context="self_report"
        ... )
    """
    # Check required fields
    assert "id" in entry_data, "Entry missing 'id' field"
    assert "goal_id" in entry_data, "Entry missing 'goal_id' field"
    assert "entry_date" in entry_data, "Entry missing 'entry_date' field"
    assert "value" in entry_data, "Entry missing 'value' field"
    assert "context" in entry_data, "Entry missing 'context' field"
    assert "created_at" in entry_data, "Entry missing 'created_at' field"

    # Validate field types
    assert isinstance(entry_data["value"], (int, float)), "value must be numeric"
    assert entry_data["context"] in ["session", "self_report", "assessment"], \
        f"Invalid context: {entry_data['context']}"

    # Check expected values if provided
    if expected_goal_id is not None:
        assert str(entry_data["goal_id"]) == str(expected_goal_id), \
            f"Expected goal_id {expected_goal_id}, got {entry_data['goal_id']}"
    if expected_value is not None:
        assert abs(entry_data["value"] - expected_value) < 0.01, \
            f"Expected value {expected_value}, got {entry_data['value']}"
    if expected_context is not None:
        assert entry_data["context"] == expected_context, \
            f"Expected context {expected_context}, got {entry_data['context']}"


# ============================================================================
# Mock Service Helpers
# ============================================================================

def mock_milestone_detection(
    goal: TreatmentGoal,
    entries: List[ProgressEntry],
) -> List[Dict[str, Any]]:
    """
    Mock milestone detection logic for testing without full service.

    Simulates the milestone detector service by checking for common
    milestone patterns (percentage completion, streaks, etc.).

    Args:
        goal: TreatmentGoal instance
        entries: List of ProgressEntry instances

    Returns:
        List of detected milestones as dictionaries

    Example:
        >>> milestones = mock_milestone_detection(goal, entries)
        >>> assert len(milestones) > 0
        >>> assert milestones[0]["milestone_type"] == "percentage"
    """
    milestones = []

    if not entries:
        return milestones

    # Sort entries by date
    sorted_entries = sorted(entries, key=lambda e: e.entry_date)

    # Check for percentage completion milestones
    if goal.baseline_value is not None and goal.target_value is not None:
        current_value = sorted_entries[-1].value
        total_change_needed = goal.target_value - goal.baseline_value
        current_change = current_value - goal.baseline_value

        if total_change_needed != 0:
            percentage = (current_change / total_change_needed) * 100

            # 25%, 50%, 75% milestones
            for threshold in [25, 50, 75]:
                if percentage >= threshold:
                    milestones.append({
                        "milestone_type": "percentage",
                        "title": f"{threshold}% Progress",
                        "description": f"Reached {threshold}% toward goal target",
                        "target_value": goal.baseline_value + (total_change_needed * threshold / 100),
                        "achieved_at": sorted_entries[-1].recorded_at,
                    })

    # Check for streak milestones (consecutive days)
    if len(sorted_entries) >= 3:
        streak_count = 1
        for i in range(1, len(sorted_entries)):
            days_diff = (sorted_entries[i].entry_date - sorted_entries[i-1].entry_date).days
            if days_diff == 1:
                streak_count += 1
            else:
                streak_count = 1

        # 7-day, 14-day, 30-day streaks
        for threshold in [7, 14, 30]:
            if streak_count >= threshold:
                milestones.append({
                    "milestone_type": "streak",
                    "title": f"{threshold}-Day Streak",
                    "description": f"Tracked progress for {threshold} consecutive days",
                    "target_value": threshold,
                    "achieved_at": sorted_entries[-1].recorded_at,
                })

    return milestones


# ============================================================================
# Test Data Generators
# ============================================================================

def generate_progress_trend(
    goal_id: UUID,
    num_entries: int = 10,
    start_date: Optional[date] = None,
    trend_type: str = "improving",
    baseline: float = 3.0,
    target: float = 8.0,
    noise_level: float = 0.5,
) -> List[ProgressEntry]:
    """
    Generate realistic progress trend data for testing visualizations.

    Creates a series of progress entries following a specified trend pattern
    with realistic variation (noise) for testing charts and analytics.

    Args:
        goal_id: UUID of the goal
        num_entries: Number of entries to generate (default: 10)
        start_date: Starting date (default: 30 days ago)
        trend_type: Type of trend ('improving', 'declining', 'stable', 'fluctuating')
        baseline: Starting value (default: 3.0)
        target: Target value (default: 8.0)
        noise_level: Amount of random variation (default: 0.5)

    Returns:
        List of ProgressEntry instances with trend pattern

    Example:
        >>> entries = generate_progress_trend(
        ...     goal_id=goal.id,
        ...     num_entries=20,
        ...     trend_type="improving",
        ...     baseline=3.0,
        ...     target=8.0
        ... )
        >>> for entry in entries:
        ...     db.add(entry)
        >>> db.commit()
    """
    import random

    if start_date is None:
        start_date = date.today() - timedelta(days=30)

    entries = []
    total_change = target - baseline

    for i in range(num_entries):
        entry_date = start_date + timedelta(days=i * (30 // num_entries))

        # Calculate base value based on trend type
        if trend_type == "improving":
            # Linear improvement from baseline to target
            progress_ratio = i / max(num_entries - 1, 1)
            base_value = baseline + (total_change * progress_ratio)
        elif trend_type == "declining":
            # Linear decline from baseline
            progress_ratio = i / max(num_entries - 1, 1)
            base_value = baseline - (abs(total_change) * progress_ratio * 0.5)
        elif trend_type == "stable":
            # Stays near baseline
            base_value = baseline
        elif trend_type == "fluctuating":
            # Oscillates around midpoint
            midpoint = baseline + (total_change / 2)
            amplitude = abs(total_change) * 0.3
            base_value = midpoint + (amplitude * (1 if i % 2 == 0 else -1))
        else:
            base_value = baseline

        # Add noise
        noise = random.uniform(-noise_level, noise_level)
        value = max(0, min(10, base_value + noise))  # Clamp to 0-10 range

        entry = ProgressEntry(
            id=uuid4(),
            goal_id=goal_id,
            entry_date=entry_date,
            value=value,
            context="self_report",
            recorded_at=datetime.combine(entry_date, time(12, 0)),
        )
        entries.append(entry)

    return entries


def generate_assessment_series(
    patient_id: UUID,
    assessment_type: str = "PHQ-9",
    num_assessments: int = 5,
    start_date: Optional[date] = None,
    trend: str = "improving",
) -> List[AssessmentScore]:
    """
    Generate a series of assessment scores showing a trend over time.

    Useful for testing assessment tracking and progress visualization.

    Args:
        patient_id: UUID of the patient
        assessment_type: Type of assessment (default: "PHQ-9")
        num_assessments: Number of assessments to generate (default: 5)
        start_date: Starting date (default: 90 days ago)
        trend: Score trend ('improving', 'declining', 'stable')

    Returns:
        List of AssessmentScore instances

    Example:
        >>> assessments = generate_assessment_series(
        ...     patient_id=patient.id,
        ...     assessment_type="GAD-7",
        ...     num_assessments=4,
        ...     trend="improving"
        ... )
        >>> for assessment in assessments:
        ...     db.add(assessment)
        >>> db.commit()
    """
    if start_date is None:
        start_date = date.today() - timedelta(days=90)

    # Score ranges by assessment type
    score_ranges = {
        "PHQ-9": (0, 27),  # Depression
        "GAD-7": (0, 21),  # Anxiety
        "BDI": (0, 63),    # Beck Depression Inventory
        "BAI": (0, 63),    # Beck Anxiety Inventory
    }

    min_score, max_score = score_ranges.get(assessment_type, (0, 27))

    assessments = []

    # Starting score (moderate severity)
    if trend == "improving":
        start_score = int(max_score * 0.6)  # Start at 60% of max
    elif trend == "declining":
        start_score = int(max_score * 0.3)  # Start at 30% of max
    else:  # stable
        start_score = int(max_score * 0.4)  # Start at 40% of max

    for i in range(num_assessments):
        assessment_date = start_date + timedelta(days=i * (90 // num_assessments))

        # Calculate score based on trend
        if trend == "improving":
            # Decrease score over time (lower is better for these assessments)
            score = max(min_score, start_score - int(start_score * 0.15 * i))
        elif trend == "declining":
            # Increase score over time (worsening)
            score = min(max_score, start_score + int((max_score - start_score) * 0.2 * i))
        else:  # stable
            # Stay roughly the same with minor variation
            import random
            score = start_score + random.randint(-2, 2)
            score = max(min_score, min(max_score, score))

        # Determine severity based on score and assessment type
        if assessment_type in ["PHQ-9", "GAD-7"]:
            if score < 5:
                severity = "minimal"
            elif score < 10:
                severity = "mild"
            elif score < 15:
                severity = "moderate"
            else:
                severity = "severe"
        else:
            # Generic severity for other assessments
            percent = score / max_score
            if percent < 0.25:
                severity = "minimal"
            elif percent < 0.5:
                severity = "mild"
            elif percent < 0.75:
                severity = "moderate"
            else:
                severity = "severe"

        assessment = AssessmentScore(
            id=uuid4(),
            patient_id=patient_id,
            assessment_type=assessment_type,
            score=score,
            severity=severity,
            administered_date=assessment_date,
            created_at=datetime.combine(assessment_date, time(10, 0)),
        )
        assessments.append(assessment)

    return assessments
