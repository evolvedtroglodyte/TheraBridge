"""
Comprehensive tests for trend_calculator service.

Tests cover:
- calculate_slope() - Linear regression calculation
- calculate_trend() - Trend direction determination with target direction
- calculate_progress_percentage() - Progress percentage computation
- Mathematical accuracy validation
- Edge cases (insufficient data, identical values, extreme outliers)
- Target direction consideration (increase vs decrease goals)
"""
import pytest
from datetime import datetime, timedelta, date
from decimal import Decimal

from app.services.trend_calculator import (
    calculate_slope,
    calculate_trend,
    calculate_progress_percentage,
)
from app.models.tracking_models import ProgressEntry
from tests.utils.test_helpers import (
    create_test_progress_entry,
    assert_progress_statistics,
)


# ============================================================================
# Test calculate_slope() - Linear Regression
# ============================================================================

@pytest.mark.goal_tracking
class TestCalculateSlope:
    """Test linear regression slope calculation."""

    def test_perfect_linear_increase(self):
        """Test slope calculation with perfect linear increasing data."""
        x = [0, 1, 2, 3, 4]
        y = [10.0, 11.0, 12.0, 13.0, 14.0]

        slope = calculate_slope(x, y)

        # Should be exactly 1.0 (increasing by 1 per unit)
        assert abs(slope - 1.0) < 0.0001, f"Expected slope 1.0, got {slope}"

    def test_perfect_linear_decrease(self):
        """Test slope calculation with perfect linear decreasing data."""
        x = [0, 1, 2, 3, 4]
        y = [10.0, 9.0, 8.0, 7.0, 6.0]

        slope = calculate_slope(x, y)

        # Should be exactly -1.0 (decreasing by 1 per unit)
        assert abs(slope - (-1.0)) < 0.0001, f"Expected slope -1.0, got {slope}"

    def test_steep_positive_slope(self):
        """Test slope calculation with steep positive slope."""
        x = [0, 1, 2, 3]
        y = [1.0, 4.0, 7.0, 10.0]

        slope = calculate_slope(x, y)

        # Should be exactly 3.0 (increasing by 3 per unit)
        assert abs(slope - 3.0) < 0.0001, f"Expected slope 3.0, got {slope}"

    def test_steep_negative_slope(self):
        """Test slope calculation with steep negative slope."""
        x = [0, 1, 2, 3]
        y = [20.0, 15.0, 10.0, 5.0]

        slope = calculate_slope(x, y)

        # Should be exactly -5.0 (decreasing by 5 per unit)
        assert abs(slope - (-5.0)) < 0.0001, f"Expected slope -5.0, got {slope}"

    def test_zero_slope_horizontal_line(self):
        """Test slope calculation with all identical y values (horizontal line)."""
        x = [0, 1, 2, 3, 4]
        y = [5.0, 5.0, 5.0, 5.0, 5.0]

        slope = calculate_slope(x, y)

        # Should be exactly 0.0 (no change)
        assert abs(slope) < 0.0001, f"Expected slope 0.0, got {slope}"

    def test_realistic_noisy_increase(self):
        """Test slope calculation with realistic noisy increasing data."""
        x = [0, 1, 2, 3, 4, 5, 6]
        y = [3.0, 3.5, 4.2, 4.8, 5.1, 5.9, 6.5]  # ~0.6 increase per unit

        slope = calculate_slope(x, y)

        # Should be approximately 0.6
        assert 0.5 < slope < 0.7, f"Expected slope ~0.6, got {slope}"

    def test_realistic_noisy_decrease(self):
        """Test slope calculation with realistic noisy decreasing data."""
        x = [0, 1, 2, 3, 4, 5]
        y = [8.0, 7.6, 7.0, 6.4, 6.1, 5.5]  # ~-0.5 decrease per unit

        slope = calculate_slope(x, y)

        # Should be approximately -0.5
        assert -0.6 < slope < -0.4, f"Expected slope ~-0.5, got {slope}"

    def test_two_points_minimum(self):
        """Test slope calculation with minimum 2 data points."""
        x = [0, 1]
        y = [5.0, 7.0]

        slope = calculate_slope(x, y)

        # Should be exactly 2.0
        assert abs(slope - 2.0) < 0.0001, f"Expected slope 2.0, got {slope}"

    def test_error_on_single_point(self):
        """Test that single data point raises ValueError."""
        x = [0]
        y = [5.0]

        with pytest.raises(ValueError, match="at least 2 data points"):
            calculate_slope(x, y)

    def test_error_on_empty_lists(self):
        """Test that empty lists raise ValueError."""
        x = []
        y = []

        with pytest.raises(ValueError, match="at least 2 data points"):
            calculate_slope(x, y)

    def test_error_on_mismatched_lengths(self):
        """Test that mismatched x and y lengths raise ValueError."""
        x = [0, 1, 2]
        y = [5.0, 6.0]

        with pytest.raises(ValueError, match="same length"):
            calculate_slope(x, y)

    def test_edge_case_vertical_line(self):
        """Test slope with all identical x values (vertical line)."""
        x = [5, 5, 5, 5]  # All same x
        y = [1.0, 2.0, 3.0, 4.0]

        slope = calculate_slope(x, y)

        # Should return 0.0 (denominator is 0, handled by edge case check)
        assert slope == 0.0, f"Expected slope 0.0 for vertical line, got {slope}"

    def test_large_numbers(self):
        """Test slope calculation with large numbers."""
        x = [0, 100, 200, 300]
        y = [1000.0, 2000.0, 3000.0, 4000.0]

        slope = calculate_slope(x, y)

        # Should be exactly 10.0 (increasing by 1000 per 100 units)
        assert abs(slope - 10.0) < 0.0001, f"Expected slope 10.0, got {slope}"

    def test_small_incremental_changes(self):
        """Test slope calculation with very small incremental changes."""
        x = [0, 1, 2, 3, 4]
        y = [5.0, 5.01, 5.02, 5.03, 5.04]

        slope = calculate_slope(x, y)

        # Should be exactly 0.01
        assert abs(slope - 0.01) < 0.0001, f"Expected slope 0.01, got {slope}"


# ============================================================================
# Test calculate_trend() - Trend Direction with Target
# ============================================================================

@pytest.mark.goal_tracking
class TestCalculateTrend:
    """Test trend direction calculation considering target direction."""

    def test_improving_trend_for_increase_goal(self):
        """Test improving trend when goal is to increase and values are increasing."""
        from uuid import uuid4

        goal_id = uuid4()
        # Create entries showing increasing trend
        entries = []
        base_date = date.today() - timedelta(days=10)
        values = [3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]  # Increasing values

        for i, value in enumerate(values):
            entry = create_test_progress_entry(
                goal_id=goal_id,
                value=value,
                entry_date=base_date + timedelta(days=i)
            )
            entries.append(entry)

        # Target direction is "increase" - values are going up, so it's improving
        result = calculate_trend(entries, target_direction="increase", days=30)

        assert result["direction"] == "improving", \
            f"Expected 'improving' for increasing values with increase target, got {result['direction']}"
        assert result["slope"] is not None
        assert result["slope"] > 0, "Slope should be positive for increasing values"

    def test_improving_trend_for_decrease_goal(self):
        """Test improving trend when goal is to decrease and values are decreasing."""
        from uuid import uuid4

        goal_id = uuid4()
        # Create entries showing decreasing trend
        entries = []
        base_date = date.today() - timedelta(days=10)
        values = [8.0, 7.5, 7.0, 6.5, 6.0, 5.5, 5.0]  # Decreasing values

        for i, value in enumerate(values):
            entry = create_test_progress_entry(
                goal_id=goal_id,
                value=value,
                entry_date=base_date + timedelta(days=i)
            )
            entries.append(entry)

        # Target direction is "decrease" - values are going down, so it's improving
        result = calculate_trend(entries, target_direction="decrease", days=30)

        assert result["direction"] == "improving", \
            f"Expected 'improving' for decreasing values with decrease target, got {result['direction']}"
        assert result["slope"] is not None
        assert result["slope"] < 0, "Slope should be negative for decreasing values"

    def test_declining_trend_for_increase_goal(self):
        """Test declining trend when goal is to increase but values are decreasing."""
        from uuid import uuid4

        goal_id = uuid4()
        # Create entries showing decreasing trend (bad for increase goal)
        entries = []
        base_date = date.today() - timedelta(days=10)
        values = [6.0, 5.5, 5.0, 4.5, 4.0, 3.5, 3.0]  # Decreasing values

        for i, value in enumerate(values):
            entry = create_test_progress_entry(
                goal_id=goal_id,
                value=value,
                entry_date=base_date + timedelta(days=i)
            )
            entries.append(entry)

        result = calculate_trend(entries, target_direction="increase", days=30)

        assert result["direction"] == "declining", \
            f"Expected 'declining' for decreasing values with increase target, got {result['direction']}"
        assert result["slope"] < 0, "Slope should be negative"

    def test_declining_trend_for_decrease_goal(self):
        """Test declining trend when goal is to decrease but values are increasing."""
        from uuid import uuid4

        goal_id = uuid4()
        # Create entries showing increasing trend (bad for decrease goal)
        entries = []
        base_date = date.today() - timedelta(days=10)
        values = [3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]  # Increasing values

        for i, value in enumerate(values):
            entry = create_test_progress_entry(
                goal_id=goal_id,
                value=value,
                entry_date=base_date + timedelta(days=i)
            )
            entries.append(entry)

        result = calculate_trend(entries, target_direction="decrease", days=30)

        assert result["direction"] == "declining", \
            f"Expected 'declining' for increasing values with decrease target, got {result['direction']}"
        assert result["slope"] > 0, "Slope should be positive"

    def test_stable_trend_small_positive_slope(self):
        """Test stable trend when slope is small positive (< 0.05)."""
        from uuid import uuid4

        goal_id = uuid4()
        # Create entries with very small positive slope
        entries = []
        base_date = date.today() - timedelta(days=20)
        values = [5.0, 5.02, 5.04, 5.03, 5.05, 5.06, 5.04]  # ~0.01 slope

        for i, value in enumerate(values):
            entry = create_test_progress_entry(
                goal_id=goal_id,
                value=value,
                entry_date=base_date + timedelta(days=i * 3)
            )
            entries.append(entry)

        result = calculate_trend(entries, target_direction="increase", days=30)

        assert result["direction"] == "stable", \
            f"Expected 'stable' for small slope {result['slope']}, got {result['direction']}"
        assert abs(result["slope"]) < 0.05, "Slope should be less than threshold"

    def test_stable_trend_small_negative_slope(self):
        """Test stable trend when slope is small negative (> -0.05)."""
        from uuid import uuid4

        goal_id = uuid4()
        # Create entries with very small negative slope
        entries = []
        base_date = date.today() - timedelta(days=20)
        values = [5.0, 4.98, 4.96, 4.97, 4.95, 4.94, 4.96]  # ~-0.01 slope

        for i, value in enumerate(values):
            entry = create_test_progress_entry(
                goal_id=goal_id,
                value=value,
                entry_date=base_date + timedelta(days=i * 3)
            )
            entries.append(entry)

        result = calculate_trend(entries, target_direction="decrease", days=30)

        assert result["direction"] == "stable", \
            f"Expected 'stable' for small slope {result['slope']}, got {result['direction']}"
        assert abs(result["slope"]) < 0.05, "Slope should be less than threshold"

    def test_insufficient_data_less_than_3_entries(self):
        """Test insufficient_data when less than 3 entries provided."""
        from uuid import uuid4

        goal_id = uuid4()
        # Create only 2 entries
        entries = []
        base_date = date.today() - timedelta(days=5)

        for i in range(2):
            entry = create_test_progress_entry(
                goal_id=goal_id,
                value=5.0 + i,
                entry_date=base_date + timedelta(days=i)
            )
            entries.append(entry)

        result = calculate_trend(entries, target_direction="increase", days=30)

        assert result["direction"] == "insufficient_data", \
            f"Expected 'insufficient_data' for 2 entries, got {result['direction']}"
        assert result["slope"] is None, "Slope should be None for insufficient data"

    def test_insufficient_data_empty_entries(self):
        """Test insufficient_data when no entries provided."""
        result = calculate_trend([], target_direction="increase", days=30)

        assert result["direction"] == "insufficient_data"
        assert result["slope"] is None

    def test_date_filtering_excludes_old_entries(self):
        """Test that entries outside the days window are filtered out."""
        from uuid import uuid4

        goal_id = uuid4()
        entries = []

        # Add 2 old entries (outside 7-day window)
        old_date = date.today() - timedelta(days=10)
        for i in range(2):
            entry = create_test_progress_entry(
                goal_id=goal_id,
                value=3.0,
                entry_date=old_date + timedelta(days=i)
            )
            entries.append(entry)

        # Add 4 recent entries (within 7-day window)
        recent_date = date.today() - timedelta(days=5)
        for i in range(4):
            entry = create_test_progress_entry(
                goal_id=goal_id,
                value=5.0 + i * 0.5,  # Increasing trend
                entry_date=recent_date + timedelta(days=i)
            )
            entries.append(entry)

        result = calculate_trend(entries, target_direction="increase", days=7)

        # Should only use the 4 recent entries
        assert result["direction"] == "improving", \
            "Should detect improving trend from recent entries only"

    def test_entries_sorted_chronologically(self):
        """Test that entries are sorted by date before slope calculation."""
        from uuid import uuid4

        goal_id = uuid4()
        # Create entries in random order
        base_date = date.today() - timedelta(days=10)
        entries = [
            create_test_progress_entry(goal_id, 6.0, base_date + timedelta(days=4)),
            create_test_progress_entry(goal_id, 3.0, base_date),
            create_test_progress_entry(goal_id, 5.0, base_date + timedelta(days=3)),
            create_test_progress_entry(goal_id, 4.0, base_date + timedelta(days=1)),
        ]

        result = calculate_trend(entries, target_direction="increase", days=30)

        # Should correctly identify positive trend despite unsorted input
        assert result["direction"] == "improving"
        assert result["slope"] > 0

    def test_slope_exactly_at_threshold(self):
        """Test behavior when slope is exactly at the 0.05 threshold."""
        from uuid import uuid4

        goal_id = uuid4()
        # Create entries with slope of exactly 0.05
        entries = []
        base_date = date.today() - timedelta(days=10)

        for i in range(5):
            entry = create_test_progress_entry(
                goal_id=goal_id,
                value=5.0 + (i * 0.05),  # Exactly 0.05 per day
                entry_date=base_date + timedelta(days=i)
            )
            entries.append(entry)

        result = calculate_trend(entries, target_direction="increase", days=30)

        # At exactly 0.05, should NOT be stable (threshold is < 0.05)
        assert result["direction"] in ["improving", "declining"], \
            "Slope of exactly 0.05 should not be considered stable"


# ============================================================================
# Test calculate_progress_percentage() - Progress Calculation
# ============================================================================

@pytest.mark.goal_tracking
class TestCalculateProgressPercentage:
    """Test progress percentage calculation from baseline to target."""

    def test_at_baseline(self):
        """Test progress percentage when current equals baseline (0% progress)."""
        baseline = 10.0
        current = 10.0
        target = 20.0

        progress = calculate_progress_percentage(baseline, current, target)

        assert progress == 0.0, f"Expected 0.0 at baseline, got {progress}"

    def test_halfway_to_target(self):
        """Test progress percentage halfway between baseline and target (50%)."""
        baseline = 10.0
        current = 15.0
        target = 20.0

        progress = calculate_progress_percentage(baseline, current, target)

        assert abs(progress - 0.5) < 0.0001, f"Expected 0.5 at midpoint, got {progress}"

    def test_at_target(self):
        """Test progress percentage when current equals target (100% progress)."""
        baseline = 10.0
        current = 20.0
        target = 20.0

        progress = calculate_progress_percentage(baseline, current, target)

        assert abs(progress - 1.0) < 0.0001, f"Expected 1.0 at target, got {progress}"

    def test_exceeded_target(self):
        """Test progress percentage when current exceeds target (> 100%)."""
        baseline = 10.0
        current = 25.0
        target = 20.0

        progress = calculate_progress_percentage(baseline, current, target)

        assert abs(progress - 1.5) < 0.0001, f"Expected 1.5 when exceeding target, got {progress}"

    def test_negative_progress_regression(self):
        """Test progress percentage when current is below baseline (negative progress)."""
        baseline = 10.0
        current = 5.0
        target = 20.0

        progress = calculate_progress_percentage(baseline, current, target)

        assert abs(progress - (-0.5)) < 0.0001, \
            f"Expected -0.5 for regression below baseline, got {progress}"

    def test_decreasing_goal_at_target(self):
        """Test progress for decreasing goal (baseline > target)."""
        baseline = 20.0
        current = 10.0
        target = 10.0

        progress = calculate_progress_percentage(baseline, current, target)

        assert abs(progress - 1.0) < 0.0001, \
            f"Expected 1.0 when reaching lower target, got {progress}"

    def test_decreasing_goal_halfway(self):
        """Test progress for decreasing goal at 50%."""
        baseline = 20.0
        current = 15.0
        target = 10.0

        progress = calculate_progress_percentage(baseline, current, target)

        assert abs(progress - 0.5) < 0.0001, \
            f"Expected 0.5 halfway to lower target, got {progress}"

    def test_none_baseline_returns_zero(self):
        """Test that None baseline returns 0.0."""
        progress = calculate_progress_percentage(None, 15.0, 20.0)

        assert progress == 0.0, f"Expected 0.0 for None baseline, got {progress}"

    def test_none_current_returns_zero(self):
        """Test that None current returns 0.0."""
        progress = calculate_progress_percentage(10.0, None, 20.0)

        assert progress == 0.0, f"Expected 0.0 for None current, got {progress}"

    def test_none_target_returns_zero(self):
        """Test that None target returns 0.0."""
        progress = calculate_progress_percentage(10.0, 15.0, None)

        assert progress == 0.0, f"Expected 0.0 for None target, got {progress}"

    def test_all_none_returns_zero(self):
        """Test that all None values return 0.0."""
        progress = calculate_progress_percentage(None, None, None)

        assert progress == 0.0, f"Expected 0.0 for all None values, got {progress}"

    def test_baseline_equals_target_returns_zero(self):
        """Test that baseline == target returns 0.0 (no room for progress)."""
        baseline = 15.0
        current = 15.0
        target = 15.0

        progress = calculate_progress_percentage(baseline, current, target)

        assert progress == 0.0, \
            f"Expected 0.0 when baseline == target (no progress possible), got {progress}"

    def test_large_numbers(self):
        """Test progress calculation with large numbers."""
        baseline = 1000.0
        current = 1500.0
        target = 2000.0

        progress = calculate_progress_percentage(baseline, current, target)

        assert abs(progress - 0.5) < 0.0001, \
            f"Expected 0.5 for large numbers, got {progress}"

    def test_small_decimal_differences(self):
        """Test progress calculation with small decimal differences."""
        baseline = 3.14
        current = 3.64
        target = 4.14

        progress = calculate_progress_percentage(baseline, current, target)

        assert abs(progress - 0.5) < 0.0001, \
            f"Expected 0.5 for small decimals, got {progress}"

    def test_negative_baseline_and_target(self):
        """Test progress calculation with negative baseline and target."""
        baseline = -10.0
        current = -5.0
        target = 0.0

        progress = calculate_progress_percentage(baseline, current, target)

        assert abs(progress - 0.5) < 0.0001, \
            f"Expected 0.5 with negative baseline, got {progress}"

    def test_zero_baseline_positive_target(self):
        """Test progress calculation with zero baseline."""
        baseline = 0.0
        current = 5.0
        target = 10.0

        progress = calculate_progress_percentage(baseline, current, target)

        assert abs(progress - 0.5) < 0.0001, \
            f"Expected 0.5 with zero baseline, got {progress}"
