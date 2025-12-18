"""
Comprehensive integration tests for goal_tracking router.

Tests:
- POST /goals/{goal_id}/tracking/config - Configure tracking method
- POST /goals/{goal_id}/progress - Record progress entry
- GET /goals/{goal_id}/progress - Get progress history with aggregation
- GET /patients/{patient_id}/goals/dashboard - Get patient dashboard
- POST /patients/{patient_id}/goals - Create treatment goal
- GET /patients/{patient_id}/goals - List patient goals

Coverage:
- All 6 endpoints tested
- Rate limiting enforcement
- Data isolation (patient vs therapist access)
- Aggregation logic (daily, weekly, monthly)
- Dashboard calculations
- Status filtering
- Trend detection (improving/stable/declining)
"""
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime, date, time, timedelta
from app.models.db_models import User, Patient, TherapistPatient
from app.models.schemas import UserRole
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import GoalTrackingConfig, ProgressEntry
from app.schemas.tracking_schemas import GoalStatus, TrackingMethod, TrackingFrequency, TargetDirection, EntryContext, AggregationPeriod
from app.database import get_db

pytestmark = pytest.mark.goal_tracking

# No prefix needed - endpoints are at /api/v1/goals/ and /api/v1/patients/
API_PREFIX = "/api/v1"


# ============================================================================
# Test Utilities (Wave 1 style)
# ============================================================================

def create_test_goal(
    test_db,
    patient_id,
    therapist_id,
    description="Test goal",
    category="anxiety_management",
    status="assigned",
    baseline_value=2.0,
    target_value=8.0,
    target_date=None
):
    """Create a test treatment goal"""
    if target_date is None:
        target_date = date.today() + timedelta(days=30)

    goal = TreatmentGoal(
        patient_id=patient_id,
        therapist_id=therapist_id,
        description=description,
        category=category,
        status=status,
        baseline_value=baseline_value,
        target_value=target_value,
        target_date=target_date,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)
    return goal


def create_test_tracking_config(
    test_db,
    goal_id,
    tracking_method="scale",
    tracking_frequency="daily",
    scale_min=1,
    scale_max=10,
    target_direction="increase"
):
    """Create a test tracking configuration"""
    config = GoalTrackingConfig(
        goal_id=goal_id,
        tracking_method=tracking_method,
        tracking_frequency=tracking_frequency,
        scale_min=scale_min,
        scale_max=scale_max,
        target_direction=target_direction,
        reminder_enabled=True,
        created_at=datetime.utcnow()
    )
    test_db.add(config)
    test_db.commit()
    test_db.refresh(config)
    return config


def generate_progress_trend(
    test_db,
    goal_id,
    tracking_config_id,
    days=7,
    start_value=3.0,
    trend="improving"
):
    """Generate a series of progress entries with a specific trend"""
    entries = []
    base_date = date.today() - timedelta(days=days)

    for i in range(days):
        if trend == "improving":
            value = start_value + (i * 0.5)  # Increase by 0.5 each day
        elif trend == "declining":
            value = start_value - (i * 0.5)  # Decrease by 0.5 each day
        else:  # stable
            value = start_value + ((-1 if i % 2 == 0 else 1) * 0.2)  # Small fluctuations

        entry = ProgressEntry(
            goal_id=goal_id,
            tracking_config_id=tracking_config_id,
            entry_date=base_date + timedelta(days=i),
            entry_time=time(hour=20, minute=0),
            value=value,
            value_label=f"Value: {value}",
            notes=f"Day {i+1} entry",
            context="self_report",
            recorded_at=datetime.utcnow()
        )
        test_db.add(entry)
        entries.append(entry)

    test_db.commit()
    for entry in entries:
        test_db.refresh(entry)

    return entries


def assert_goal_response(data, expected_status=None):
    """Assert that a goal response has correct structure"""
    assert "id" in data
    assert "patient_id" in data
    assert "therapist_id" in data
    assert "description" in data
    assert "status" in data
    assert "created_at" in data
    assert "updated_at" in data

    if expected_status:
        assert data["status"] == expected_status


def assert_progress_statistics(stats, has_entries=True):
    """Assert that progress statistics have correct structure"""
    assert "baseline" in stats
    assert "current" in stats
    assert "target" in stats
    assert "average" in stats
    assert "min" in stats
    assert "max" in stats
    assert "trend_slope" in stats
    assert "trend_direction" in stats

    if has_entries:
        assert stats["current"] is not None
        assert stats["average"] is not None


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def async_db_client(test_async_db):
    """
    Async TestClient for testing async endpoints (goal_tracking uses async).

    Uses the router-specific conftest pattern for async database access.
    """
    async def override_get_db():
        yield test_async_db

    # Override database dependency
    from app.main import app
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture
def test_patient_with_assignment(therapist_user, patient_user):
    """Create a therapist-patient assignment for testing"""
    # Use sync session for fixture setup
    from tests.routers.conftest import TestingSyncSessionLocal
    db = TestingSyncSessionLocal()
    try:
        assignment = TherapistPatient(
            therapist_id=therapist_user.id,
            patient_id=patient_user.id,
            relationship_type="primary",
            is_active=True,
            started_at=datetime.utcnow()
        )
        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return {"therapist": therapist_user, "patient": patient_user, "assignment": assignment}
    finally:
        db.close()


@pytest.fixture
def test_goal_with_tracking(test_patient_with_assignment):
    """Create a goal with tracking configuration"""
    patient = test_patient_with_assignment["patient"]
    therapist = test_patient_with_assignment["therapist"]

    # Use sync session for fixture setup
    from tests.routers.conftest import TestingSyncSessionLocal
    db = TestingSyncSessionLocal()
    try:
        goal = create_test_goal(
            db,
            patient_id=patient.id,
            therapist_id=therapist.id,
            description="Track anxiety levels daily",
            status="in_progress"
        )

        config = create_test_tracking_config(
            db,
            goal_id=goal.id,
            tracking_method="scale",
            scale_min=1,
            scale_max=10,
            target_direction="decrease"
        )

        return {"goal": goal, "config": config, "patient": patient, "therapist": therapist}
    finally:
        db.close()


@pytest.fixture
def test_goal_with_progress(test_goal_with_tracking):
    """Create a goal with progress entries"""
    goal = test_goal_with_tracking["goal"]
    config = test_goal_with_tracking["config"]

    # Use sync session for fixture setup
    from tests.routers.conftest import TestingSyncSessionLocal
    db = TestingSyncSessionLocal()
    try:
        entries = generate_progress_trend(
            db,
            goal_id=goal.id,
            tracking_config_id=config.id,
            days=7,
            start_value=8.0,
            trend="improving"
        )

        return {**test_goal_with_tracking, "entries": entries}
    finally:
        db.close()


# ============================================================================
# Test POST /goals/{goal_id}/tracking/config - Configure tracking
# ============================================================================

@pytest.mark.analytics
class TestConfigureTracking:
    """Test POST /goals/{goal_id}/tracking/config endpoint"""

    def test_create_tracking_config_success(
        self,
        async_db_client,
        test_db,
        test_patient_with_assignment,
        therapist_auth_headers
    ):
        """Test successful tracking configuration creation"""
        patient = test_patient_with_assignment["patient"]
        therapist = test_patient_with_assignment["therapist"]

        goal = create_test_goal(
            test_db,
            patient_id=patient.id,
            therapist_id=therapist.id
        )

        config_data = {
            "tracking_method": "scale",
            "tracking_frequency": "daily",
            "scale_min": 1,
            "scale_max": 10,
            "target_direction": "decrease",
            "reminder_enabled": True
        }

        response = async_db_client.post(
            f"{API_PREFIX}/goals/{goal.id}/tracking/config",
            json=config_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["goal_id"] == str(goal.id)
        assert data["tracking_method"] == "scale"
        assert data["scale_min"] == 1
        assert data["scale_max"] == 10
        assert data["target_direction"] == "decrease"

    def test_create_tracking_config_requires_therapist(
        self,
        async_db_client,
        test_db,
        test_patient_with_assignment,
        patient_auth_headers
    ):
        """Test that only therapists can configure tracking"""
        patient = test_patient_with_assignment["patient"]
        therapist = test_patient_with_assignment["therapist"]

        goal = create_test_goal(
            test_db,
            patient_id=patient.id,
            therapist_id=therapist.id
        )

        config_data = {
            "tracking_method": "scale",
            "tracking_frequency": "daily",
            "scale_min": 1,
            "scale_max": 10,
            "target_direction": "increase",
            "reminder_enabled": False
        }

        response = async_db_client.post(
            f"{API_PREFIX}/goals/{goal.id}/tracking/config",
            json=config_data,
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_tracking_config_invalid_goal(
        self,
        async_db_client,
        therapist_auth_headers
    ):
        """Test configuration fails with non-existent goal"""
        fake_goal_id = uuid4()

        config_data = {
            "tracking_method": "binary",
            "tracking_frequency": "weekly",
            "target_direction": "increase",
            "reminder_enabled": True
        }

        response = async_db_client.post(
            f"{API_PREFIX}/goals/{fake_goal_id}/tracking/config",
            json=config_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_frequency_tracking_config(
        self,
        async_db_client,
        test_db,
        test_patient_with_assignment,
        therapist_auth_headers
    ):
        """Test creating frequency-based tracking config"""
        patient = test_patient_with_assignment["patient"]
        therapist = test_patient_with_assignment["therapist"]

        goal = create_test_goal(
            test_db,
            patient_id=patient.id,
            therapist_id=therapist.id,
            description="Exercise 5 times per week"
        )

        config_data = {
            "tracking_method": "frequency",
            "tracking_frequency": "weekly",
            "frequency_unit": "times_per_week",
            "target_direction": "increase",
            "reminder_enabled": True
        }

        response = async_db_client.post(
            f"{API_PREFIX}/goals/{goal.id}/tracking/config",
            json=config_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["tracking_method"] == "frequency"
        assert data["frequency_unit"] == "times_per_week"


# ============================================================================
# Test POST /goals/{goal_id}/progress - Record progress
# ============================================================================

class TestRecordProgress:
    """Test POST /goals/{goal_id}/progress endpoint"""

    def test_record_progress_as_patient(
        self,
        async_db_client,
        test_db,
        test_goal_with_tracking,
        patient_auth_headers
    ):
        """Test patient can record their own progress"""
        goal = test_goal_with_tracking["goal"]

        entry_data = {
            "entry_date": str(date.today()),
            "entry_time": "14:30:00",
            "value": 7.5,
            "value_label": "Feeling better",
            "notes": "Anxiety reduced after breathing exercises",
            "context": "self_report"
        }

        response = async_db_client.post(
            f"{API_PREFIX}/goals/{goal.id}/progress",
            json=entry_data,
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["goal_id"] == str(goal.id)
        assert data["value"] == 7.5
        assert data["context"] == "self_report"

    def test_record_progress_as_therapist(
        self,
        async_db_client,
        test_db,
        test_goal_with_tracking,
        therapist_auth_headers
    ):
        """Test therapist can record progress for assigned patient"""
        goal = test_goal_with_tracking["goal"]

        entry_data = {
            "entry_date": str(date.today()),
            "entry_time": "10:00:00",
            "value": 6.0,
            "value_label": "Session observation",
            "notes": "Patient showed reduced anxiety during session",
            "context": "session"
        }

        response = async_db_client.post(
            f"{API_PREFIX}/goals/{goal.id}/progress",
            json=entry_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["context"] == "session"

    def test_record_progress_data_isolation(
        self,
        async_db_client,
        therapist_user,
        patient_user,
        patient_auth_headers
    ):
        """Test patient cannot record progress for another patient's goal"""
        # Create another patient
        from tests.routers.conftest import TestingSyncSessionLocal
        db = TestingSyncSessionLocal()
        try:
            other_patient = User(
                email="other.goal.patient@test.com",
                hashed_password="hashed",
                first_name="Other",
                last_name="Patient",
                role=UserRole.patient,
                is_active=True,
                is_verified=False
            )
            db.add(other_patient)
            db.commit()
            db.refresh(other_patient)

            # Create goal for other patient
            goal = create_test_goal(
                db,
                patient_id=other_patient.id,
                therapist_id=therapist_user.id
            )

            entry_data = {
                "entry_date": str(date.today()),
                "value": 5.0,
                "context": "self_report"
            }

            response = async_db_client.post(
                f"{API_PREFIX}/goals/{goal.id}/progress",
                json=entry_data,
                headers=patient_auth_headers
            )

            assert response.status_code == status.HTTP_403_FORBIDDEN
        finally:
            db.close()

    def test_record_progress_future_date_rejected(
        self,
        async_db_client,
        test_goal_with_tracking,
        patient_auth_headers
    ):
        """Test that future dates are rejected"""
        goal = test_goal_with_tracking["goal"]
        future_date = date.today() + timedelta(days=5)

        entry_data = {
            "entry_date": str(future_date),
            "value": 5.0,
            "context": "self_report"
        }

        response = async_db_client.post(
            f"{API_PREFIX}/goals/{goal.id}/progress",
            json=entry_data,
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# Test GET /goals/{goal_id}/progress - Get progress history
# ============================================================================

@pytest.mark.analytics
class TestGetProgressHistory:
    """Test GET /goals/{goal_id}/progress endpoint"""

    def test_get_progress_history_success(
        self,
        async_db_client,
        test_goal_with_progress,
        patient_auth_headers
    ):
        """Test successful progress history retrieval"""
        goal = test_goal_with_progress["goal"]

        response = async_db_client.get(
            f"{API_PREFIX}/goals/{goal.id}/progress",
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["goal_id"] == str(goal.id)
        assert len(data["entries"]) == 7  # 7 days of entries
        assert_progress_statistics(data["statistics"], has_entries=True)

    def test_get_progress_history_with_date_filter(
        self,
        async_db_client,
        test_goal_with_progress,
        therapist_auth_headers
    ):
        """Test progress history with date range filtering"""
        goal = test_goal_with_progress["goal"]
        start_date = date.today() - timedelta(days=4)
        end_date = date.today()

        response = async_db_client.get(
            f"{API_PREFIX}/goals/{goal.id}/progress?start_date={start_date}&end_date={end_date}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["entries"]) <= 5  # Max 5 days in range

    def test_get_progress_history_daily_aggregation(
        self,
        async_db_client,
        test_goal_with_progress,
        patient_auth_headers
    ):
        """Test progress history with daily aggregation"""
        goal = test_goal_with_progress["goal"]

        response = async_db_client.get(
            f"{API_PREFIX}/goals/{goal.id}/progress?aggregation=daily",
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "entries" in data
        assert "statistics" in data

    def test_get_progress_history_weekly_aggregation(
        self,
        async_db_client,
        test_db,
        test_goal_with_tracking,
        therapist_auth_headers
    ):
        """Test progress history with weekly aggregation"""
        goal = test_goal_with_tracking["goal"]
        config = test_goal_with_tracking["config"]

        # Create 3 weeks of data
        generate_progress_trend(
            test_db,
            goal_id=goal.id,
            tracking_config_id=config.id,
            days=21,
            start_value=5.0,
            trend="improving"
        )

        response = async_db_client.get(
            f"{API_PREFIX}/goals/{goal.id}/progress?aggregation=weekly",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should aggregate into ~3 weekly groups
        assert "entries" in data

    def test_get_progress_history_monthly_aggregation(
        self,
        async_db_client,
        test_db,
        test_goal_with_tracking,
        patient_auth_headers
    ):
        """Test progress history with monthly aggregation"""
        goal = test_goal_with_tracking["goal"]
        config = test_goal_with_tracking["config"]

        # Create 2 months of data
        generate_progress_trend(
            test_db,
            goal_id=goal.id,
            tracking_config_id=config.id,
            days=60,
            start_value=3.0,
            trend="improving"
        )

        response = async_db_client.get(
            f"{API_PREFIX}/goals/{goal.id}/progress?aggregation=monthly",
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should aggregate into ~2 monthly groups
        assert "entries" in data

    def test_get_progress_history_trend_detection(
        self,
        async_db_client,
        test_goal_with_progress,
        therapist_auth_headers
    ):
        """Test that trend direction is correctly calculated"""
        goal = test_goal_with_progress["goal"]

        response = async_db_client.get(
            f"{API_PREFIX}/goals/{goal.id}/progress",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # We created an improving trend
        assert data["statistics"]["trend_direction"] in ["improving", "stable"]
        assert data["statistics"]["trend_slope"] is not None


# ============================================================================
# Test GET /patients/{patient_id}/goals/dashboard - Get dashboard
# ============================================================================

@pytest.mark.analytics
class TestGetDashboard:
    """Test GET /patients/{patient_id}/goals/dashboard endpoint"""

    def test_get_dashboard_as_patient(
        self,
        async_db_client,
        test_db,
        test_goal_with_progress,
        patient_auth_headers
    ):
        """Test patient can view their own dashboard"""
        patient = test_goal_with_progress["patient"]

        response = async_db_client.get(
            f"{API_PREFIX}/patients/{patient.id}/goals/dashboard",
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["patient_id"] == str(patient.id)
        assert data["active_goals"] >= 1
        assert "tracking_summary" in data
        assert "goals" in data

    def test_get_dashboard_as_therapist(
        self,
        async_db_client,
        test_goal_with_progress,
        therapist_auth_headers
    ):
        """Test therapist can view assigned patient's dashboard"""
        patient = test_goal_with_progress["patient"]

        response = async_db_client.get(
            f"{API_PREFIX}/patients/{patient.id}/goals/dashboard",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["patient_id"] == str(patient.id)

    def test_get_dashboard_data_isolation(
        self,
        async_db_client,
        therapist_user,
        patient_user,
        patient_auth_headers
    ):
        """Test patient cannot view another patient's dashboard"""
        # Create another patient
        from tests.routers.conftest import TestingSyncSessionLocal
        db = TestingSyncSessionLocal()
        try:
            other_patient = User(
                email="dashboard.other@test.com",
                hashed_password="hashed",
                first_name="Other",
                last_name="Patient",
                role=UserRole.patient,
                is_active=True,
                is_verified=False
            )
            db.add(other_patient)
            db.commit()
            db.refresh(other_patient)

            response = async_db_client.get(
                f"{API_PREFIX}/patients/{other_patient.id}/goals/dashboard",
                headers=patient_auth_headers
            )

            assert response.status_code == status.HTTP_403_FORBIDDEN
        finally:
            db.close()

    def test_get_dashboard_tracking_summary(
        self,
        async_db_client,
        test_goal_with_progress,
        therapist_auth_headers
    ):
        """Test dashboard tracking summary calculations"""
        patient = test_goal_with_progress["patient"]

        response = async_db_client.get(
            f"{API_PREFIX}/patients/{patient.id}/goals/dashboard",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        summary = data["tracking_summary"]
        assert "entries_this_week" in summary
        assert "streak_days" in summary
        assert "completion_rate" in summary
        assert isinstance(summary["completion_rate"], (int, float))

    def test_get_dashboard_goal_items(
        self,
        async_db_client,
        test_goal_with_progress,
        therapist_auth_headers
    ):
        """Test dashboard goal items structure"""
        patient = test_goal_with_progress["patient"]

        response = async_db_client.get(
            f"{API_PREFIX}/patients/{patient.id}/goals/dashboard",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["goals"]) >= 1

        goal_item = data["goals"][0]
        assert "id" in goal_item
        assert "description" in goal_item
        assert "status" in goal_item
        assert "current_value" in goal_item
        assert "progress_percentage" in goal_item
        assert "trend" in goal_item
        assert "trend_data" in goal_item


# ============================================================================
# Test POST /patients/{patient_id}/goals - Create goal
# ============================================================================

class TestCreateGoal:
    """Test POST /patients/{patient_id}/goals endpoint"""

    def test_create_goal_success(
        self,
        async_db_client,
        test_patient_with_assignment,
        therapist_auth_headers
    ):
        """Test successful goal creation"""
        patient = test_patient_with_assignment["patient"]

        goal_data = {
            "description": "Reduce anxiety symptoms to manageable levels",
            "category": "Anxiety management",
            "baseline_value": 8.5,
            "target_value": 3.0,
            "target_date": str(date.today() + timedelta(days=90))
        }

        response = async_db_client.post(
            f"{API_PREFIX}/patients/{patient.id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert_goal_response(data, expected_status="assigned")
        assert data["description"] == goal_data["description"]
        assert data["patient_id"] == str(patient.id)

    def test_create_goal_requires_therapist(
        self,
        async_db_client,
        test_patient_with_assignment,
        patient_auth_headers
    ):
        """Test that only therapists can create goals"""
        patient = test_patient_with_assignment["patient"]

        goal_data = {
            "description": "Test goal",
            "category": "Test",
            "baseline_value": 5.0,
            "target_value": 10.0
        }

        response = async_db_client.post(
            f"{API_PREFIX}/patients/{patient.id}/goals",
            json=goal_data,
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_goal_invalid_patient(
        self,
        async_db_client,
        therapist_auth_headers
    ):
        """Test goal creation fails with non-existent patient"""
        fake_patient_id = uuid4()

        goal_data = {
            "description": "Test goal",
            "baseline_value": 5.0,
            "target_value": 10.0
        }

        response = async_db_client.post(
            f"{API_PREFIX}/patients/{fake_patient_id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_goal_minimal_data(
        self,
        async_db_client,
        test_patient_with_assignment,
        therapist_auth_headers
    ):
        """Test goal creation with minimal required data"""
        patient = test_patient_with_assignment["patient"]

        goal_data = {
            "description": "Simple goal with minimal data"
        }

        response = async_db_client.post(
            f"{API_PREFIX}/patients/{patient.id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["description"] == goal_data["description"]
        assert data["status"] == "assigned"


# ============================================================================
# Test GET /patients/{patient_id}/goals - List goals
# ============================================================================

class TestListGoals:
    """Test GET /patients/{patient_id}/goals endpoint"""

    def test_list_goals_success(
        self,
        async_db_client,
        test_db,
        test_patient_with_assignment,
        patient_auth_headers
    ):
        """Test successful goal listing"""
        patient = test_patient_with_assignment["patient"]
        therapist = test_patient_with_assignment["therapist"]

        # Create multiple goals
        for i in range(3):
            create_test_goal(
                test_db,
                patient_id=patient.id,
                therapist_id=therapist.id,
                description=f"Goal {i+1}"
            )

        response = async_db_client.get(
            f"{API_PREFIX}/patients/{patient.id}/goals",
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, list)
        assert len(data) == 3

    def test_list_goals_filter_by_status(
        self,
        async_db_client,
        test_db,
        test_patient_with_assignment,
        therapist_auth_headers
    ):
        """Test goal listing with status filter"""
        patient = test_patient_with_assignment["patient"]
        therapist = test_patient_with_assignment["therapist"]

        # Create goals with different statuses
        create_test_goal(test_db, patient.id, therapist.id, status="assigned")
        create_test_goal(test_db, patient.id, therapist.id, status="in_progress")
        create_test_goal(test_db, patient.id, therapist.id, status="completed")

        response = async_db_client.get(
            f"{API_PREFIX}/patients/{patient.id}/goals?status=in_progress",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert all(goal["status"] == "in_progress" for goal in data)

    def test_list_goals_ordered_by_date(
        self,
        async_db_client,
        test_db,
        test_patient_with_assignment,
        therapist_auth_headers
    ):
        """Test that goals are ordered by creation date (newest first)"""
        patient = test_patient_with_assignment["patient"]
        therapist = test_patient_with_assignment["therapist"]

        # Create goals with staggered timestamps
        for i in range(3):
            goal = create_test_goal(
                test_db,
                patient_id=patient.id,
                therapist_id=therapist.id,
                description=f"Goal {i+1}"
            )
            goal.created_at = datetime.utcnow() - timedelta(hours=i)
            test_db.commit()

        response = async_db_client.get(
            f"{API_PREFIX}/patients/{patient.id}/goals",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify descending order (newest first)
        timestamps = [datetime.fromisoformat(goal["created_at"].replace('Z', '+00:00')) for goal in data]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_list_goals_data_isolation(
        self,
        async_db_client,
        therapist_user,
        patient_user,
        patient_auth_headers
    ):
        """Test that patients can only see their own goals"""
        # Create another patient
        from tests.routers.conftest import TestingSyncSessionLocal
        db = TestingSyncSessionLocal()
        try:
            other_patient = User(
                email="list.other@test.com",
                hashed_password="hashed",
                first_name="Other",
                last_name="Patient",
                role=UserRole.patient,
                is_active=True,
                is_verified=False
            )
            db.add(other_patient)
            db.commit()
            db.refresh(other_patient)

            response = async_db_client.get(
                f"{API_PREFIX}/patients/{other_patient.id}/goals",
                headers=patient_auth_headers
            )

            assert response.status_code == status.HTTP_403_FORBIDDEN
        finally:
            db.close()


# ============================================================================
# Test Rate Limiting
# ============================================================================

class TestRateLimiting:
    """Test rate limiting on goal tracking endpoints"""

    @pytest.mark.skip(reason="Rate limiting tests require Redis or in-memory storage cleanup")
    def test_config_endpoint_rate_limit(
        self,
        async_db_client,
        test_goal_with_tracking,
        therapist_auth_headers
    ):
        """Test rate limit on config endpoint (20/minute)"""
        goal = test_goal_with_tracking["goal"]

        config_data = {
            "tracking_method": "scale",
            "tracking_frequency": "daily",
            "scale_min": 1,
            "scale_max": 10,
            "target_direction": "increase",
            "reminder_enabled": True
        }

        # Try to exceed rate limit
        for i in range(22):
            response = async_db_client.post(
                f"{API_PREFIX}/goals/{goal.id}/tracking/config",
                json=config_data,
                headers=therapist_auth_headers
            )

            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break

        # Should have hit rate limit
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @pytest.mark.skip(reason="Rate limiting tests require Redis or in-memory storage cleanup")
    def test_progress_endpoint_rate_limit(
        self,
        async_db_client,
        test_goal_with_tracking,
        patient_auth_headers
    ):
        """Test rate limit on progress endpoint (50/minute)"""
        goal = test_goal_with_tracking["goal"]

        entry_data = {
            "entry_date": str(date.today()),
            "value": 5.0,
            "context": "self_report"
        }

        # Try to exceed rate limit
        for i in range(52):
            response = async_db_client.post(
                f"{API_PREFIX}/goals/{goal.id}/progress",
                json=entry_data,
                headers=patient_auth_headers
            )

            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                break

        # Should have hit rate limit
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_get_progress_history_no_entries(
        self,
        async_db_client,
        test_goal_with_tracking,
        therapist_auth_headers
    ):
        """Test progress history with no entries returns empty data"""
        goal = test_goal_with_tracking["goal"]

        response = async_db_client.get(
            f"{API_PREFIX}/goals/{goal.id}/progress",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["entries"]) == 0
        assert data["statistics"]["trend_direction"] == "insufficient_data"

    def test_get_dashboard_no_goals(
        self,
        async_db_client,
        test_patient_with_assignment,
        patient_auth_headers
    ):
        """Test dashboard with no goals returns empty data"""
        patient = test_patient_with_assignment["patient"]

        response = async_db_client.get(
            f"{API_PREFIX}/patients/{patient.id}/goals/dashboard",
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["active_goals"] == 0
        assert len(data["goals"]) == 0

    def test_create_goal_with_past_target_date(
        self,
        async_db_client,
        test_patient_with_assignment,
        therapist_auth_headers
    ):
        """Test goal creation fails with past target date"""
        patient = test_patient_with_assignment["patient"]
        past_date = date.today() - timedelta(days=10)

        goal_data = {
            "description": "Test goal",
            "target_date": str(past_date)
        }

        response = async_db_client.post(
            f"{API_PREFIX}/patients/{patient.id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
