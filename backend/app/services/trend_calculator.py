"""
Trend analysis service for goal progress tracking.

Provides linear regression-based trend calculation to determine if goal progress
is improving, declining, or stable over time.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from app.models.tracking_models import ProgressEntry


def calculate_trend(
    entries: List[ProgressEntry],
    target_direction: str,
    days: int = 30
) -> Dict[str, Any]:
    """
    Calculate trend direction using linear regression on recent progress entries.

    Args:
        entries: List of ProgressEntry objects to analyze
        target_direction: Either "increase" or "decrease" - desired direction for improvement
        days: Number of recent days to include in analysis (default: 30)

    Returns:
        Dictionary with:
            - direction: "improving", "declining", "stable", or "insufficient_data"
            - slope: Float representing rate of change per day, or None if insufficient data

    Examples:
        >>> calculate_trend(entries, "decrease", days=30)
        {"direction": "improving", "slope": -0.15}  # Decreasing trend when decrease is target

        >>> calculate_trend(entries, "increase", days=30)
        {"direction": "insufficient_data", "slope": None}  # < 3 entries
    """
    # Filter to recent N days
    today = datetime.utcnow().date()
    cutoff_date = today - timedelta(days=days)
    recent = [e for e in entries if e.entry_date >= cutoff_date]

    # Need at least 3 data points for meaningful regression
    if len(recent) < 3:
        return {"direction": "insufficient_data", "slope": None}

    # Sort by date to ensure chronological order
    recent.sort(key=lambda e: e.entry_date)

    # Prepare data for linear regression
    # x: days since first entry
    # y: progress values
    x = [(e.entry_date - recent[0].entry_date).days for e in recent]
    y = [float(e.value) for e in recent]

    # Calculate slope using linear regression
    slope = calculate_slope(x, y)

    # Determine direction based on slope and target
    # Threshold for "stable": absolute slope < 0.05 per day
    if abs(slope) < 0.05:
        direction = "stable"
    elif slope < 0:
        # Negative slope: decreasing over time
        direction = "improving" if target_direction == "decrease" else "declining"
    else:
        # Positive slope: increasing over time
        direction = "improving" if target_direction == "increase" else "declining"

    return {"direction": direction, "slope": slope}


def calculate_slope(x: List[int], y: List[float]) -> float:
    """
    Calculate linear regression slope using least squares method.

    Formula: slope = Σ((x - x̄)(y - ȳ)) / Σ((x - x̄)²)

    Args:
        x: List of x-coordinates (typically days since start)
        y: List of y-coordinates (typically progress values)

    Returns:
        Float representing slope (rate of change of y per unit x)

    Raises:
        ValueError: If x and y have different lengths or < 2 points

    Examples:
        >>> calculate_slope([0, 1, 2, 3], [10.0, 9.0, 8.0, 7.0])
        -1.0  # Decreasing by 1 unit per day

        >>> calculate_slope([0, 1, 2], [5.0, 5.1, 4.9])
        -0.1  # Nearly stable, slight decrease
    """
    if len(x) != len(y):
        raise ValueError("x and y must have the same length")

    if len(x) < 2:
        raise ValueError("Need at least 2 data points to calculate slope")

    # Calculate means
    n = len(x)
    x_mean = sum(x) / n
    y_mean = sum(y) / n

    # Calculate slope components
    numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

    # Handle edge case: all x values are identical (vertical line)
    if denominator == 0:
        return 0.0

    slope = numerator / denominator
    return slope


def calculate_progress_percentage(
    baseline: Optional[float],
    current: Optional[float],
    target: Optional[float]
) -> float:
    """
    Calculate progress percentage from baseline to target.

    Formula: (current - baseline) / (target - baseline)

    Args:
        baseline: Starting value
        current: Current value
        target: Goal target value

    Returns:
        Progress as percentage (0.0 to 1.0+)
        - 0.0 = at baseline
        - 0.5 = halfway to target
        - 1.0 = reached target
        - > 1.0 = exceeded target
        Returns 0.0 for edge cases (missing values, division by zero)

    Examples:
        >>> calculate_progress_percentage(10.0, 15.0, 20.0)
        0.5  # Halfway from 10 to 20

        >>> calculate_progress_percentage(10.0, 25.0, 20.0)
        1.5  # Exceeded target by 50%

        >>> calculate_progress_percentage(10.0, 10.0, 20.0)
        0.0  # Still at baseline

        >>> calculate_progress_percentage(None, 15.0, 20.0)
        0.0  # Missing baseline
    """
    # Handle missing values
    if baseline is None or current is None or target is None:
        return 0.0

    # Handle edge case: baseline equals target (no room for progress)
    if baseline == target:
        return 0.0

    # Calculate progress
    total_distance = target - baseline
    current_distance = current - baseline

    # Avoid division by zero (should be caught by baseline == target check, but defensive)
    if total_distance == 0:
        return 0.0

    progress = current_distance / total_distance

    # Return as-is (can be negative if regressing, > 1.0 if exceeded)
    return progress
