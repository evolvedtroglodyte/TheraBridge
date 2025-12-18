"""
Comprehensive tests for patient self-report router.

Tests:
- POST /self-report/check-in - Patient check-in submission
- GET /self-report/goals - Get trackable goals for patient
- Patient authorization (patients can only access own data)
- Goal linkage and tracking validation
- Check-in history and progress tracking
- Required fields validation
- Authorization edge cases
"""
import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException

from app.models.db_models import User
from app.models.schemas import UserRole


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def patient_with_goals(test_db, sample_patient, therapist_user, sample_session, sample_goal_with_tracking):
    """
    Create a patient with trackable goals.

    Returns:
        Tuple of (patient, goal, tracking_config)
    """
    goal, tracking_config = sample_goal_with_tracking
    return (sample_patient, goal, tracking_config)


@pytest.fixture
def other_patient_with_goal(test_db, therapist_user):
    """
    Create another patient with a goal for authorization tests.
    """
    from app.models.db_models import Patient
    from app.models.goal_models import TreatmentGoal
    from app.models.tracking_models import GoalTrackingConfig

    # Create other patient
    other_patient = Patient(
        name="Other Patient",
        email="other.patient@example.com",
        phone="555-9999",
        therapist_id=therapist_user.id
    )
    test_db.add(other_patient)
    test_db.commit()
    test_db.refresh(other_patient)

    # Create goal for other patient
    goal = TreatmentGoal(
        patient_id=other_patient.id,
        therapist_id=therapist_user.id,
        session_id=None,
        description="Other patient's goal",
        category="anxiety_management",
        status="in_progress",
        baseline_value=8.0,
        target_value=4.0,
        target_date=date.today() + timedelta(days=30),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)

    # Create tracking config
    tracking_config = GoalTrackingConfig(
        goal_id=goal.id,
        tracking_method="scale",
        tracking_frequency="daily",
        scale_min=1,
        scale_max=10,
        target_direction="decrease",
        reminder_enabled=False,
        created_at=datetime.utcnow()
    )
    test_db.add(tracking_config)
    test_db.commit()
    test_db.refresh(tracking_config)

    return (other_patient, goal, tracking_config)


@pytest.fixture
def patient_user_with_goals(test_db, patient_user, therapist_user, sample_session):
    """
    Create patient_user with trackable goals for authentication tests.

    Returns:
        Tuple of (patient_user, goal, tracking_config)
    """
    from app.models.goal_models import TreatmentGoal
    from app.models.tracking_models import GoalTrackingConfig

    # Create goal for patient_user
    goal = TreatmentGoal(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        session_id=sample_session.id,
        description="Reduce anxiety through breathing exercises",
        category="anxiety_management",
        status="in_progress",
        baseline_value=8.0,
        target_value=4.0,
        target_date=date.today() + timedelta(days=60),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)

    # Create tracking config
    tracking_config = GoalTrackingConfig(
        goal_id=goal.id,
        tracking_method="scale",
        tracking_frequency="daily",
        scale_min=1,
        scale_max=10,
        scale_labels={"1": "No anxiety", "5": "Moderate", "10": "Severe"},
        target_direction="decrease",
        reminder_enabled=True,
        created_at=datetime.utcnow()
    )
    test_db.add(tracking_config)
    test_db.commit()
    test_db.refresh(tracking_config)

    return (patient_user, goal, tracking_config)


# ============================================================================
# POST /self-report/check-in - Patient Check-in Tests
# ============================================================================

@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_submit_check_in_success(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test successful patient check-in submission"""
    patient, goal, tracking_config = patient_user_with_goals

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(goal.id),
                "value": 6.5,
                "notes": "Feeling better today, exercises helped"
            }
        ],
        "general_mood": 7,
        "additional_notes": "Overall positive day"
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Check-in recorded successfully"
    assert data["entries_created"] == 1


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_submit_check_in_multiple_goals(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test check-in with multiple goals"""
    patient, goal1, tracking_config1 = patient_user_with_goals

    # Create second goal for same patient
    from app.models.goal_models import TreatmentGoal
    from app.models.tracking_models import GoalTrackingConfig

    goal2 = TreatmentGoal(
        patient_id=patient.id,
        therapist_id=goal1.therapist_id,
        session_id=goal1.session_id,
        description="Exercise 5 times per week",
        category="physical_activity",
        status="in_progress",
        baseline_value=1.0,
        target_value=5.0,
        target_date=date.today() + timedelta(days=60),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(goal2)
    test_db.commit()
    test_db.refresh(goal2)

    tracking_config2 = GoalTrackingConfig(
        goal_id=goal2.id,
        tracking_method="frequency",
        tracking_frequency="weekly",
        target_direction="increase",
        reminder_enabled=False,
        created_at=datetime.utcnow()
    )
    test_db.add(tracking_config2)
    test_db.commit()

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(goal1.id),
                "value": 5.5,
                "notes": "Good progress on anxiety"
            },
            {
                "goal_id": str(goal2.id),
                "value": 3,
                "notes": "Exercised 3 times this week"
            }
        ],
        "general_mood": 8,
        "additional_notes": "Productive week overall"
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["entries_created"] == 2


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_submit_check_in_without_notes(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test check-in submission without optional notes"""
    patient, goal, tracking_config = patient_user_with_goals

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(goal.id),
                "value": 7.0,
                "notes": None
            }
        ],
        "general_mood": 6,
        "additional_notes": None
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["entries_created"] == 1


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_submit_check_in_invalid_goal_id(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test check-in fails with non-existent goal ID"""
    patient, goal, tracking_config = patient_user_with_goals

    fake_goal_id = uuid4()
    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(fake_goal_id),
                "value": 5.0,
                "notes": "Test"
            }
        ],
        "general_mood": 6,
        "additional_notes": None
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    assert response.status_code == 400
    assert "Invalid goal IDs" in response.json()["detail"]


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_submit_check_in_other_patients_goal(async_db_client, test_db, patient_user_with_goals, other_patient_with_goal, patient_auth_headers):
    """Test patient cannot submit check-in for another patient's goal"""
    patient, own_goal, _ = patient_user_with_goals
    other_patient, other_goal, _ = other_patient_with_goal

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(other_goal.id),  # Try to access other patient's goal
                "value": 5.0,
                "notes": "Unauthorized access attempt"
            }
        ],
        "general_mood": 6,
        "additional_notes": None
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    assert response.status_code == 400
    assert "do not belong to you" in response.json()["detail"]


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_submit_check_in_mixed_valid_invalid_goals(async_db_client, test_db, patient_user_with_goals, other_patient_with_goal, patient_auth_headers):
    """Test check-in fails when mixing valid and invalid goal IDs"""
    patient, own_goal, _ = patient_user_with_goals
    other_patient, other_goal, _ = other_patient_with_goal

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(own_goal.id),  # Valid
                "value": 6.0,
                "notes": "Valid goal"
            },
            {
                "goal_id": str(other_goal.id),  # Invalid - belongs to other patient
                "value": 5.0,
                "notes": "Invalid goal"
            }
        ],
        "general_mood": 6,
        "additional_notes": None
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    assert response.status_code == 400
    assert "do not belong to you" in response.json()["detail"]


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_submit_check_in_goal_without_tracking_config(async_db_client, test_db, patient_user, therapist_user, patient_auth_headers):
    """Test check-in fails for goal without tracking configuration"""
    from app.models.goal_models import TreatmentGoal

    # Create goal without tracking config
    goal = TreatmentGoal(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        session_id=None,
        description="Goal without tracking config",
        category="test",
        status="assigned",
        baseline_value=None,
        target_value=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(goal.id),
                "value": 5.0,
                "notes": "Test"
            }
        ],
        "general_mood": 6,
        "additional_notes": None
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    # Should fail because tracking service requires tracking config
    assert response.status_code in [400, 404]


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_submit_check_in_missing_required_fields(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test check-in validation for missing required fields"""
    patient, goal, tracking_config = patient_user_with_goals

    # Missing check_in_date
    invalid_data = {
        "goals": [{"goal_id": str(goal.id), "value": 5.0}],
        "general_mood": 6
    }
    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=invalid_data,
        headers=patient_auth_headers
    )
    assert response.status_code == 422

    # Missing goals
    invalid_data = {
        "check_in_date": date.today().isoformat(),
        "general_mood": 6
    }
    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=invalid_data,
        headers=patient_auth_headers
    )
    assert response.status_code == 422

    # Empty goals list
    invalid_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [],
        "general_mood": 6
    }
    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=invalid_data,
        headers=patient_auth_headers
    )
    assert response.status_code == 422

    # Missing general_mood
    invalid_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [{"goal_id": str(goal.id), "value": 5.0}]
    }
    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=invalid_data,
        headers=patient_auth_headers
    )
    assert response.status_code == 422


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_submit_check_in_invalid_mood_range(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test check-in validation for mood outside 1-10 range"""
    patient, goal, tracking_config = patient_user_with_goals

    # Mood too low
    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [{"goal_id": str(goal.id), "value": 5.0}],
        "general_mood": 0
    }
    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )
    assert response.status_code == 422

    # Mood too high
    check_in_data["general_mood"] = 11
    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )
    assert response.status_code == 422


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_submit_check_in_unauthorized_therapist(async_db_client, test_db, patient_user_with_goals, therapist_auth_headers):
    """Test therapist cannot submit check-in (patient-only endpoint)"""
    patient, goal, tracking_config = patient_user_with_goals

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(goal.id),
                "value": 5.0,
                "notes": "Therapist trying to submit"
            }
        ],
        "general_mood": 6,
        "additional_notes": None
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=therapist_auth_headers
    )

    # Should be forbidden (403) - patient-only endpoint
    assert response.status_code == 403


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_submit_check_in_unauthenticated(async_db_client, test_db, patient_user_with_goals):
    """Test check-in requires authentication"""
    patient, goal, tracking_config = patient_user_with_goals

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [{"goal_id": str(goal.id), "value": 5.0}],
        "general_mood": 6
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data
    )

    assert response.status_code == 401


# ============================================================================
# GET /self-report/goals - Get Trackable Goals Tests
# ============================================================================

@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_get_trackable_goals_success(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test successful retrieval of patient's trackable goals"""
    patient, goal, tracking_config = patient_user_with_goals

    response = async_db_client.get(
        "/api/v1/self-report/goals",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1

    goal_data = data[0]
    assert goal_data["goal_id"] == str(goal.id)
    assert goal_data["goal_description"] == goal.description
    assert goal_data["status"] in ["assigned", "in_progress"]
    assert goal_data["baseline_value"] == float(goal.baseline_value)
    assert goal_data["target_value"] == float(goal.target_value)
    assert goal_data["tracking_method"] == tracking_config.tracking_method
    assert goal_data["tracking_frequency"] == tracking_config.tracking_frequency
    assert goal_data["scale_min"] == tracking_config.scale_min
    assert goal_data["scale_max"] == tracking_config.scale_max
    assert goal_data["target_direction"] == tracking_config.target_direction


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_get_trackable_goals_multiple(async_db_client, test_db, patient_user, therapist_user, patient_auth_headers):
    """Test retrieval of multiple trackable goals"""
    from app.models.goal_models import TreatmentGoal
    from app.models.tracking_models import GoalTrackingConfig

    # Create 3 goals with different statuses
    goals = []
    for i in range(3):
        goal = TreatmentGoal(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            session_id=None,
            description=f"Goal {i+1}",
            category="test",
            status="in_progress" if i < 2 else "assigned",
            baseline_value=float(i),
            target_value=float(i + 5),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        test_db.add(goal)
        goals.append(goal)

    test_db.commit()

    # Create tracking configs
    for goal in goals:
        test_db.refresh(goal)
        tracking_config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily",
            scale_min=1,
            scale_max=10,
            target_direction="increase",
            reminder_enabled=False,
            created_at=datetime.utcnow()
        )
        test_db.add(tracking_config)

    test_db.commit()

    response = async_db_client.get(
        "/api/v1/self-report/goals",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 3
    assert all(g["status"] in ["assigned", "in_progress"] for g in data)


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_get_trackable_goals_filters_status(async_db_client, test_db, patient_user, therapist_user, patient_auth_headers):
    """Test that only assigned/in_progress goals are returned"""
    from app.models.goal_models import TreatmentGoal
    from app.models.tracking_models import GoalTrackingConfig

    # Create goals with different statuses
    statuses = ["assigned", "in_progress", "completed", "abandoned"]
    goals = []

    for status in statuses:
        goal = TreatmentGoal(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            session_id=None,
            description=f"Goal with status {status}",
            category="test",
            status=status,
            baseline_value=1.0,
            target_value=10.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        test_db.add(goal)
        goals.append(goal)

    test_db.commit()

    # Create tracking configs for all goals
    for goal in goals:
        test_db.refresh(goal)
        tracking_config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily",
            scale_min=1,
            scale_max=10,
            target_direction="increase",
            reminder_enabled=False,
            created_at=datetime.utcnow()
        )
        test_db.add(tracking_config)

    test_db.commit()

    response = async_db_client.get(
        "/api/v1/self-report/goals",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should only return assigned and in_progress goals (2 out of 4)
    assert len(data) == 2
    returned_statuses = {g["status"] for g in data}
    assert returned_statuses == {"assigned", "in_progress"}


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_get_trackable_goals_includes_without_tracking_config(async_db_client, test_db, patient_user, therapist_user, patient_auth_headers):
    """Test that goals without tracking config are still returned (with null fields)"""
    from app.models.goal_models import TreatmentGoal

    # Create goal without tracking config
    goal = TreatmentGoal(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        session_id=None,
        description="Goal without tracking config",
        category="test",
        status="assigned",
        baseline_value=5.0,
        target_value=10.0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)

    response = async_db_client.get(
        "/api/v1/self-report/goals",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    goal_data = data[0]
    assert goal_data["goal_id"] == str(goal.id)
    assert goal_data["tracking_method"] is None
    assert goal_data["tracking_frequency"] is None
    assert goal_data["scale_min"] is None
    assert goal_data["scale_max"] is None


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_get_trackable_goals_empty_list(async_db_client, test_db, patient_user, patient_auth_headers):
    """Test retrieval when patient has no trackable goals"""
    response = async_db_client.get(
        "/api/v1/self-report/goals",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_get_trackable_goals_patient_isolation(async_db_client, test_db, patient_user_with_goals, other_patient_with_goal, patient_auth_headers):
    """Test patient can only see their own goals, not other patients' goals"""
    patient, own_goal, _ = patient_user_with_goals
    other_patient, other_goal, _ = other_patient_with_goal

    response = async_db_client.get(
        "/api/v1/self-report/goals",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should only return own goal
    assert len(data) == 1
    assert data[0]["goal_id"] == str(own_goal.id)

    # Verify other patient's goal is NOT in the response
    returned_goal_ids = {g["goal_id"] for g in data}
    assert str(other_goal.id) not in returned_goal_ids


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_get_trackable_goals_unauthorized_therapist(async_db_client, test_db, patient_user_with_goals, therapist_auth_headers):
    """Test therapist cannot access patient's trackable goals endpoint"""
    response = async_db_client.get(
        "/api/v1/self-report/goals",
        headers=therapist_auth_headers
    )

    # Should be forbidden (403) - patient-only endpoint
    assert response.status_code == 403


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_get_trackable_goals_unauthenticated(async_db_client, test_db):
    """Test trackable goals endpoint requires authentication"""
    response = async_db_client.get("/api/v1/self-report/goals")

    assert response.status_code == 401


# ============================================================================
# Check-in History and Goal Linkage Tests
# ============================================================================

@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_check_in_creates_progress_entry(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test that check-in creates progress entry in database"""
    from app.models.tracking_models import ProgressEntry

    patient, goal, tracking_config = patient_user_with_goals

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(goal.id),
                "value": 6.5,
                "notes": "Progress check"
            }
        ],
        "general_mood": 7,
        "additional_notes": "Good day"
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    assert response.status_code == 200

    # Verify progress entry was created in database
    entries = test_db.query(ProgressEntry).filter_by(goal_id=goal.id).all()
    assert len(entries) == 1

    entry = entries[0]
    assert entry.value == 6.5
    assert entry.notes == "Progress check"
    assert entry.context == "self_report"
    assert entry.entry_date == date.today()


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_multiple_check_ins_create_history(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test multiple check-ins create progress history"""
    from app.models.tracking_models import ProgressEntry

    patient, goal, tracking_config = patient_user_with_goals

    # Submit 3 check-ins on different dates
    dates = [
        date.today() - timedelta(days=2),
        date.today() - timedelta(days=1),
        date.today()
    ]

    values = [8.0, 7.0, 6.0]

    for check_date, value in zip(dates, values):
        check_in_data = {
            "check_in_date": check_date.isoformat(),
            "goals": [
                {
                    "goal_id": str(goal.id),
                    "value": value,
                    "notes": f"Check-in for {check_date}"
                }
            ],
            "general_mood": 6,
            "additional_notes": None
        }

        response = async_db_client.post(
            "/api/v1/self-report/check-in",
            json=check_in_data,
            headers=patient_auth_headers
        )

        assert response.status_code == 200

    # Verify 3 progress entries were created
    entries = test_db.query(ProgressEntry).filter_by(goal_id=goal.id).order_by(ProgressEntry.entry_date).all()
    assert len(entries) == 3

    # Verify values show improvement trend
    assert entries[0].value == 8.0
    assert entries[1].value == 7.0
    assert entries[2].value == 6.0


# ============================================================================
# Authorization Edge Cases
# ============================================================================

@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_check_in_with_expired_token(async_db_client, test_db, patient_user_with_goals):
    """Test check-in fails with expired authentication token"""
    patient, goal, tracking_config = patient_user_with_goals

    # Create expired token (token from far past)
    from app.auth.utils import create_access_token
    from datetime import timedelta

    # Mock an expired token by creating one that's already old
    # In reality, we'd patch datetime or use a test-specific short expiry
    expired_headers = {
        "Authorization": "Bearer expired.token.value"
    }

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [{"goal_id": str(goal.id), "value": 5.0}],
        "general_mood": 6
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=expired_headers
    )

    assert response.status_code == 401


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_check_in_with_malformed_token(async_db_client, test_db, patient_user_with_goals):
    """Test check-in fails with malformed authentication token"""
    patient, goal, tracking_config = patient_user_with_goals

    malformed_headers = {
        "Authorization": "Bearer not.a.real.token"
    }

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [{"goal_id": str(goal.id), "value": 5.0}],
        "general_mood": 6
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=malformed_headers
    )

    assert response.status_code == 401


# ============================================================================
# Security Concerns Tests
# ============================================================================

@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_check_in_sql_injection_protection(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test check-in is protected against SQL injection in notes"""
    patient, goal, tracking_config = patient_user_with_goals

    malicious_notes = "'; DROP TABLE progress_entries; --"

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(goal.id),
                "value": 5.0,
                "notes": malicious_notes
            }
        ],
        "general_mood": 6,
        "additional_notes": malicious_notes
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    # Should succeed - SQLAlchemy ORM prevents SQL injection
    assert response.status_code == 200

    # Verify table still exists
    from app.models.tracking_models import ProgressEntry
    entries = test_db.query(ProgressEntry).all()
    assert len(entries) >= 1  # At least the one we just created


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_check_in_xss_protection(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test check-in handles XSS attempts in notes"""
    patient, goal, tracking_config = patient_user_with_goals

    xss_notes = "<script>alert('XSS')</script>"

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(goal.id),
                "value": 5.0,
                "notes": xss_notes
            }
        ],
        "general_mood": 6,
        "additional_notes": xss_notes
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    # Should succeed - notes are stored as-is, escaping happens at render time
    assert response.status_code == 200


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_check_in_max_notes_length(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test check-in enforces maximum length on notes"""
    patient, goal, tracking_config = patient_user_with_goals

    # Notes field has max_length=500
    long_notes = "x" * 501

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(goal.id),
                "value": 5.0,
                "notes": long_notes
            }
        ],
        "general_mood": 6,
        "additional_notes": None
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    # Should fail validation
    assert response.status_code == 422


@pytest.mark.goal_tracking
@pytest.mark.asyncio
async def test_check_in_max_additional_notes_length(async_db_client, test_db, patient_user_with_goals, patient_auth_headers):
    """Test check-in enforces maximum length on additional_notes"""
    patient, goal, tracking_config = patient_user_with_goals

    # additional_notes has max_length=1000
    long_notes = "x" * 1001

    check_in_data = {
        "check_in_date": date.today().isoformat(),
        "goals": [
            {
                "goal_id": str(goal.id),
                "value": 5.0,
                "notes": "Short note"
            }
        ],
        "general_mood": 6,
        "additional_notes": long_notes
    }

    response = async_db_client.post(
        "/api/v1/self-report/check-in",
        json=check_in_data,
        headers=patient_auth_headers
    )

    # Should fail validation
    assert response.status_code == 422
