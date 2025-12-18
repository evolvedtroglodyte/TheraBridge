# Test Helpers Quick Reference

Quick reference for goal tracking test utilities.

## Import Statement

```python
from tests.utils.test_helpers import (
    # Goal creation
    create_test_goal,
    create_test_tracking_config,
    create_test_progress_entry,
    create_test_assessment_score,
    # Validation
    assert_goal_response,
    assert_progress_statistics,
    assert_progress_entry_response,
    # Mocking & generation
    mock_milestone_detection,
    generate_progress_trend,
    generate_assessment_series,
)
```

## Function Signatures

### Goal Creation
```python
create_test_goal(patient_id, therapist_id, description=..., category=..., status="assigned", ...)
create_test_tracking_config(goal_id, tracking_method="scale", tracking_frequency="daily", ...)
create_test_progress_entry(goal_id, value, entry_date=None, context="self_report", ...)
create_test_assessment_score(patient_id, assessment_type="PHQ-9", score=12, ...)
```

### Validation
```python
assert_goal_response(response_data, expected_patient_id=None, expected_status=None, ...)
assert_progress_statistics(stats, expected_trend=None, min_entries=0)
assert_progress_entry_response(entry_data, expected_goal_id=None, expected_value=None, ...)
```

### Mocking & Generation
```python
mock_milestone_detection(goal, entries) -> List[Dict]
generate_progress_trend(goal_id, num_entries=10, trend_type="improving", ...)
generate_assessment_series(patient_id, assessment_type="PHQ-9", trend="improving", ...)
```

## Pytest Markers

```python
@pytest.mark.goal_tracking      # Goal tracking tests
@pytest.mark.slow               # Slow/integration tests
@pytest.mark.analytics          # Analytics tests
```

## Common Patterns

### Create Goal + Entries
```python
goal = create_test_goal(patient_id=p.id, therapist_id=t.id)
db.add(goal)
db.commit()

entries = generate_progress_trend(goal.id, num_entries=10, trend_type="improving")
for entry in entries:
    db.add(entry)
db.commit()
```

### Validate API Response
```python
response = client.get(f"/api/goals/{goal_id}")
assert_goal_response(response.json(), expected_status="in_progress")
```

### Mock Milestones
```python
milestones = mock_milestone_detection(goal, progress_entries)
assert len(milestones) >= 1
```

## File Locations

- **Utilities**: `backend/tests/utils/test_helpers.py` (763 lines)
- **Full Guide**: `backend/tests/utils/GOAL_TRACKING_TEST_HELPERS.md` (457 lines)
- **This Card**: `backend/tests/utils/TEST_HELPERS_QUICK_REF.md`
- **Pytest Config**: `backend/pytest.ini` (markers: lines 38-56)
