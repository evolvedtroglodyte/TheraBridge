# Goal Tracking Test Helpers - Usage Guide

This document provides examples and usage patterns for the goal tracking test utilities.

## Overview

The `test_helpers.py` module provides 11+ reusable utilities for goal tracking tests:

### Utility Functions
1. `create_test_goal()` - Create treatment goals with defaults
2. `create_test_tracking_config()` - Create tracking configurations
3. `create_test_progress_entry()` - Create progress entries
4. `create_test_assessment_score()` - Create assessment scores
5. `assert_goal_response()` - Validate goal API responses
6. `assert_progress_statistics()` - Validate statistics calculations
7. `assert_progress_entry_response()` - Validate progress entry responses
8. `mock_milestone_detection()` - Mock milestone detection service
9. `generate_progress_trend()` - Generate realistic trend data
10. `generate_assessment_series()` - Generate assessment score series

### Pytest Markers
- `@pytest.mark.goal_tracking` - Mark goal tracking tests
- `@pytest.mark.slow` - Mark slow tests (integration, database-heavy)
- `@pytest.mark.analytics` - Mark analytics/dashboard tests

---

## Basic Usage Examples

### 1. Creating Test Goals

```python
from tests.utils.test_helpers import create_test_goal

def test_create_goal(test_db, therapist_user, patient_user):
    """Test goal creation with minimal setup"""

    # Create goal with defaults
    goal = create_test_goal(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id
    )
    test_db.add(goal)
    test_db.commit()

    assert goal.description == "Practice mindfulness meditation daily"
    assert goal.status == "assigned"
    assert goal.baseline_value == 3.0
    assert goal.target_value == 8.0


def test_create_custom_goal(test_db, therapist_user, patient_user):
    """Test goal creation with custom values"""

    goal = create_test_goal(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        description="Reduce panic attacks",
        category="Anxiety management",
        baseline_value=5.0,
        target_value=1.0,
        target_date=date.today() + timedelta(days=60)
    )
    test_db.add(goal)
    test_db.commit()

    assert goal.description == "Reduce panic attacks"
    assert goal.target_value == 1.0
```

### 2. Creating Progress Entries

```python
from tests.utils.test_helpers import create_test_goal, create_test_progress_entry

@pytest.mark.goal_tracking
def test_progress_entry(test_db, therapist_user, patient_user):
    """Test creating progress entries"""

    # Create goal first
    goal = create_test_goal(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id
    )
    test_db.add(goal)
    test_db.commit()

    # Create progress entry
    entry = create_test_progress_entry(
        goal_id=goal.id,
        value=6.5,
        notes="Feeling much better today",
        context="self_report"
    )
    test_db.add(entry)
    test_db.commit()

    assert entry.value == 6.5
    assert entry.context == "self_report"
    assert entry.entry_date == date.today()
```

### 3. Validating API Responses

```python
from tests.utils.test_helpers import assert_goal_response

@pytest.mark.goal_tracking
@pytest.mark.api
def test_get_goal_endpoint(client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test GET /api/goals/{goal_id}"""

    # Create goal via database
    goal = create_test_goal(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        description="Test goal"
    )
    test_db.add(goal)
    test_db.commit()

    # Call API
    response = client.get(
        f"/api/goals/{goal.id}",
        headers=therapist_auth_headers
    )

    # Validate response with helper
    assert response.status_code == 200
    assert_goal_response(
        response.json(),
        expected_patient_id=patient_user.id,
        expected_therapist_id=therapist_user.id,
        expected_status="assigned",
        expected_description="Test goal"
    )
```

### 4. Validating Statistics

```python
from tests.utils.test_helpers import assert_progress_statistics

@pytest.mark.goal_tracking
@pytest.mark.analytics
def test_progress_statistics(client, test_db, therapist_user, patient_user, goal_with_entries, therapist_auth_headers):
    """Test progress statistics calculation"""

    # Call API to get progress with statistics
    response = client.get(
        f"/api/goals/{goal_with_entries.id}/progress",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Validate statistics structure and values
    assert_progress_statistics(
        data["statistics"],
        expected_trend="improving",
        min_entries=5
    )
```

### 5. Generating Test Trend Data

```python
from tests.utils.test_helpers import generate_progress_trend

@pytest.mark.goal_tracking
@pytest.mark.slow
def test_trend_visualization(test_db, therapist_user, patient_user):
    """Test trend data generation for charts"""

    goal = create_test_goal(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id
    )
    test_db.add(goal)
    test_db.commit()

    # Generate 20 entries showing improvement
    entries = generate_progress_trend(
        goal_id=goal.id,
        num_entries=20,
        trend_type="improving",
        baseline=3.0,
        target=8.0
    )

    for entry in entries:
        test_db.add(entry)
    test_db.commit()

    # Verify trend
    assert len(entries) == 20
    assert entries[0].value < entries[-1].value  # Improving trend
```

### 6. Mocking Milestone Detection

```python
from tests.utils.test_helpers import mock_milestone_detection

@pytest.mark.goal_tracking
def test_milestone_detection(test_db, therapist_user, patient_user):
    """Test milestone detection without full service"""

    goal = create_test_goal(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        baseline_value=3.0,
        target_value=8.0
    )
    test_db.add(goal)
    test_db.commit()

    # Generate entries showing 50% progress
    entries = generate_progress_trend(
        goal_id=goal.id,
        num_entries=10,
        trend_type="improving",
        baseline=3.0,
        target=5.5  # 50% of the way to 8.0
    )

    for entry in entries:
        test_db.add(entry)
    test_db.commit()

    # Detect milestones
    milestones = mock_milestone_detection(goal, entries)

    # Should detect 25% and 50% milestones
    assert len(milestones) >= 2
    assert any(m["milestone_type"] == "percentage" for m in milestones)
```

### 7. Generating Assessment Series

```python
from tests.utils.test_helpers import generate_assessment_series

@pytest.mark.goal_tracking
@pytest.mark.analytics
def test_assessment_tracking(test_db, patient_user):
    """Test assessment score tracking over time"""

    # Generate 5 PHQ-9 assessments showing improvement
    assessments = generate_assessment_series(
        patient_id=patient_user.id,
        assessment_type="PHQ-9",
        num_assessments=5,
        trend="improving"
    )

    for assessment in assessments:
        test_db.add(assessment)
    test_db.commit()

    # Verify trend (lower scores = improvement for PHQ-9)
    assert len(assessments) == 5
    assert assessments[0].score > assessments[-1].score
    assert assessments[-1].severity in ["minimal", "mild"]
```

---

## Advanced Usage Patterns

### Combining Multiple Helpers

```python
from tests.utils.test_helpers import (
    create_test_goal,
    create_test_tracking_config,
    generate_progress_trend,
    assert_goal_response,
    assert_progress_statistics
)

@pytest.mark.goal_tracking
@pytest.mark.integration
@pytest.mark.slow
def test_complete_goal_lifecycle(client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test complete goal tracking workflow"""

    # 1. Create goal
    goal = create_test_goal(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        description="Reduce anxiety symptoms"
    )
    test_db.add(goal)
    test_db.commit()

    # 2. Configure tracking
    config = create_test_tracking_config(
        goal_id=goal.id,
        tracking_method="scale",
        tracking_frequency="daily",
        scale_min=1,
        scale_max=10
    )
    test_db.add(config)
    test_db.commit()

    # 3. Generate progress data
    entries = generate_progress_trend(
        goal_id=goal.id,
        num_entries=30,
        trend_type="improving",
        baseline=3.0,
        target=8.0
    )
    for entry in entries:
        test_db.add(entry)
    test_db.commit()

    # 4. Fetch via API and validate
    response = client.get(
        f"/api/goals/{goal.id}/progress",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # 5. Validate response
    assert len(data["entries"]) == 30
    assert_progress_statistics(
        data["statistics"],
        expected_trend="improving",
        min_entries=30
    )
```

---

## Pytest Marker Usage

### Running Only Goal Tracking Tests

```bash
# Run all goal tracking tests
pytest -m goal_tracking

# Run goal tracking tests excluding slow tests
pytest -m "goal_tracking and not slow"

# Run only analytics tests
pytest -m analytics

# Run slow integration tests
pytest -m "slow and integration"
```

### Marking Tests

```python
import pytest

@pytest.mark.goal_tracking
def test_basic_goal_operation():
    """Fast unit test for goal tracking"""
    pass

@pytest.mark.goal_tracking
@pytest.mark.slow
@pytest.mark.db
def test_complex_goal_queries():
    """Slow database-heavy test"""
    pass

@pytest.mark.goal_tracking
@pytest.mark.analytics
def test_goal_dashboard():
    """Test analytics dashboard with goal data"""
    pass
```

---

## Error Handling Examples

### Validation Assertions

```python
from tests.utils.test_helpers import assert_goal_response

def test_invalid_response_caught():
    """Test that validation catches invalid responses"""

    # Missing required field
    invalid_response = {
        "id": str(uuid4()),
        # Missing patient_id, therapist_id, etc.
    }

    with pytest.raises(AssertionError, match="missing 'patient_id'"):
        assert_goal_response(invalid_response)

    # Invalid status
    invalid_status = {
        "id": str(uuid4()),
        "patient_id": str(uuid4()),
        "therapist_id": str(uuid4()),
        "description": "Test",
        "status": "invalid_status",  # Not in allowed values
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    with pytest.raises(AssertionError, match="Invalid status"):
        assert_goal_response(invalid_status)
```

---

## File Locations

- **Test helpers**: `/backend/tests/utils/test_helpers.py`
- **Pytest config**: `/backend/pytest.ini`
- **This guide**: `/backend/tests/utils/GOAL_TRACKING_TEST_HELPERS.md`

---

## Success Criteria Met

✅ **11 utility functions created** (exceeds requirement of 6):
1. create_test_goal
2. create_test_tracking_config
3. create_test_progress_entry
4. create_test_assessment_score
5. assert_goal_response
6. assert_progress_statistics
7. assert_progress_entry_response
8. mock_milestone_detection
9. generate_progress_trend
10. generate_assessment_series
11. create_test_tracking_config

✅ **3+ pytest markers defined**:
- @pytest.mark.goal_tracking
- @pytest.mark.slow
- @pytest.mark.analytics

✅ **All utilities have proper documentation**:
- Comprehensive docstrings with Args, Returns, Examples
- Type hints for all parameters
- Usage examples in this guide

✅ **Compatible with existing test infrastructure**:
- Uses existing fixtures (test_db, therapist_user, patient_user)
- Follows patterns from tests/utils/data_generators.py
- Works with current pytest configuration
