"""
Authorization and data isolation tests for goal tracking endpoints.

Tests verify that:
- Therapists can only access goals for their assigned patients (active relationship)
- Patients can only access their own goals
- Inactive therapist-patient relationships don't grant access
- Role-based access control (therapist vs patient)
- Goal tracking operations enforce access control
- Proper 403/401 error responses for unauthorized access
"""
import pytest
from fastapi import status
from uuid import uuid4
from datetime import datetime, date, timedelta

from app.models.db_models import User, TherapistPatient
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import GoalTrackingConfig, ProgressEntry
from app.models.schemas import UserRole
from app.auth.utils import get_password_hash


# ============================================================================
# Fixtures for Goal Tracking Authorization Tests
# ============================================================================

@pytest.fixture(scope="function")
def assigned_patient_user(test_db, therapist_user):
    """
    Create a patient user assigned to the therapist via active relationship.

    Args:
        test_db: Test database session
        therapist_user: Therapist user fixture

    Returns:
        User object with patient role assigned to therapist
    """
    patient = User(
        email="assigned_patient@test.com",
        hashed_password=get_password_hash("patientpass123"),
        first_name="Assigned",
        last_name="Patient",
        full_name="Assigned Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient.id,
        is_active=True,
        relationship_type="primary"
    )
    test_db.add(relationship)
    test_db.commit()

    return patient


@pytest.fixture(scope="function")
def assigned_patient_token(assigned_patient_user):
    """
    Generate access token for the assigned patient.

    Args:
        assigned_patient_user: Assigned patient user fixture

    Returns:
        JWT access token string
    """
    from app.auth.utils import create_access_token
    return create_access_token(assigned_patient_user.id, assigned_patient_user.role.value)


@pytest.fixture(scope="function")
def assigned_patient_auth_headers(assigned_patient_token):
    """
    Generate authorization headers for assigned patient.

    Args:
        assigned_patient_token: JWT token for assigned patient

    Returns:
        Dict with Authorization header
    """
    return {"Authorization": f"Bearer {assigned_patient_token}"}


@pytest.fixture(scope="function")
def other_therapist_user(test_db):
    """
    Create a different therapist user for testing access isolation.

    Args:
        test_db: Test database session

    Returns:
        User object with therapist role (different from therapist_user)
    """
    therapist = User(
        email="other_therapist@test.com",
        hashed_password=get_password_hash("otherpass123"),
        first_name="Other",
        last_name="Therapist",
        full_name="Other Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    test_db.add(therapist)
    test_db.commit()
    test_db.refresh(therapist)
    return therapist


@pytest.fixture(scope="function")
def other_therapist_token(other_therapist_user):
    """
    Generate access token for the other therapist.

    Args:
        other_therapist_user: Other therapist user fixture

    Returns:
        JWT access token string
    """
    from app.auth.utils import create_access_token
    return create_access_token(other_therapist_user.id, other_therapist_user.role.value)


@pytest.fixture(scope="function")
def other_therapist_auth_headers(other_therapist_token):
    """
    Generate authorization headers for other therapist.

    Args:
        other_therapist_token: JWT token for other therapist

    Returns:
        Dict with Authorization header
    """
    return {"Authorization": f"Bearer {other_therapist_token}"}


@pytest.fixture(scope="function")
def other_patient_user(test_db, other_therapist_user):
    """
    Create a patient assigned to other_therapist (not current therapist).

    Args:
        test_db: Test database session
        other_therapist_user: Other therapist user fixture

    Returns:
        User object with patient role assigned to other therapist
    """
    patient = User(
        email="other_patient@test.com",
        hashed_password=get_password_hash("otherpatient123"),
        first_name="Other",
        last_name="Patient",
        full_name="Other Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)

    # Create active relationship with other therapist
    relationship = TherapistPatient(
        therapist_id=other_therapist_user.id,
        patient_id=patient.id,
        is_active=True,
        relationship_type="primary"
    )
    test_db.add(relationship)
    test_db.commit()

    return patient


@pytest.fixture(scope="function")
def inactive_relationship_patient(test_db, therapist_user):
    """
    Create a patient with INACTIVE relationship to therapist.

    Args:
        test_db: Test database session
        therapist_user: Therapist user fixture

    Returns:
        User object with patient role and inactive relationship
    """
    patient = User(
        email="inactive_rel@test.com",
        hashed_password=get_password_hash("inactivepass123"),
        first_name="Inactive",
        last_name="Relationship",
        full_name="Inactive Relationship",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)

    # Create INACTIVE therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient.id,
        is_active=False,  # Relationship exists but is inactive
        relationship_type="primary",
        ended_at=datetime.utcnow() - timedelta(days=30)
    )
    test_db.add(relationship)
    test_db.commit()

    return patient


@pytest.fixture(scope="function")
def assigned_patient_goal(test_db, therapist_user, assigned_patient_user):
    """
    Create a treatment goal for assigned patient.

    Args:
        test_db: Test database session
        therapist_user: Therapist user fixture
        assigned_patient_user: Patient assigned to therapist

    Returns:
        TreatmentGoal object for assigned patient
    """
    goal = TreatmentGoal(
        patient_id=assigned_patient_user.id,
        therapist_id=therapist_user.id,
        description="Practice deep breathing exercises daily",
        category="anxiety_management",
        status="in_progress",
        baseline_value=2.0,
        target_value=7.0,
        target_date=date.today() + timedelta(days=30)
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)
    return goal


@pytest.fixture(scope="function")
def other_patient_goal(test_db, other_therapist_user, other_patient_user):
    """
    Create a treatment goal for other patient (not assigned to current therapist).

    Args:
        test_db: Test database session
        other_therapist_user: Other therapist user fixture
        other_patient_user: Patient assigned to other therapist

    Returns:
        TreatmentGoal object for other patient
    """
    goal = TreatmentGoal(
        patient_id=other_patient_user.id,
        therapist_id=other_therapist_user.id,
        description="Improve sleep hygiene",
        category="behavioral",
        status="in_progress",
        baseline_value=4.0,
        target_value=8.0,
        target_date=date.today() + timedelta(days=60)
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)
    return goal


@pytest.fixture(scope="function")
def assigned_goal_with_tracking(test_db, assigned_patient_goal):
    """
    Create tracking config for assigned patient's goal.

    Args:
        test_db: Test database session
        assigned_patient_goal: Goal for assigned patient

    Returns:
        GoalTrackingConfig object
    """
    config = GoalTrackingConfig(
        goal_id=assigned_patient_goal.id,
        tracking_method="scale",
        tracking_frequency="daily",
        scale_min=1,
        scale_max=10,
        scale_labels={"1": "Low anxiety", "10": "High anxiety"},
        target_direction="increase"
    )
    test_db.add(config)
    test_db.commit()
    test_db.refresh(config)
    return config


# ============================================================================
# Test: POST /goals/{goal_id}/tracking/config
# ============================================================================

@pytest.mark.goal_tracking
class TestTrackingConfigAuthorization:
    """Test authorization for creating goal tracking configurations"""

    def test_therapist_can_configure_tracking_for_assigned_patient_goal(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_goal
    ):
        """Test therapist can configure tracking for their assigned patient's goal"""
        test_db.commit()

        config_data = {
            "tracking_method": "scale",
            "tracking_frequency": "daily",
            "scale_min": 1,
            "scale_max": 10,
            "target_direction": "decrease"
        }

        response = async_db_client.post(
            f"/api/v1/goals/{assigned_patient_goal.id}/tracking/config",
            headers=therapist_auth_headers,
            json=config_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["goal_id"] == str(assigned_patient_goal.id)
        assert data["tracking_method"] == "scale"


    def test_therapist_cannot_configure_tracking_for_unassigned_patient_goal(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_goal
    ):
        """Test therapist cannot configure tracking for non-assigned patient's goal"""
        test_db.commit()

        config_data = {
            "tracking_method": "scale",
            "tracking_frequency": "daily",
            "scale_min": 1,
            "scale_max": 10,
            "target_direction": "decrease"
        }

        response = async_db_client.post(
            f"/api/v1/goals/{other_patient_goal.id}/tracking/config",
            headers=therapist_auth_headers,
            json=config_data
        )

        # Should return 403 Forbidden (not authorized to access this goal)
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_patient_cannot_configure_tracking(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        assigned_patient_goal
    ):
        """Test patient role cannot configure tracking (therapist only)"""
        test_db.commit()

        config_data = {
            "tracking_method": "scale",
            "tracking_frequency": "daily",
            "scale_min": 1,
            "scale_max": 10,
            "target_direction": "decrease"
        }

        response = async_db_client.post(
            f"/api/v1/goals/{assigned_patient_goal.id}/tracking/config",
            headers=assigned_patient_auth_headers,
            json=config_data
        )

        # Should return 403 Forbidden (therapist role required)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: POST /goals/{goal_id}/progress
# ============================================================================

@pytest.mark.goal_tracking
class TestRecordProgressAuthorization:
    """Test authorization for recording progress entries"""

    def test_therapist_can_record_progress_for_assigned_patient_goal(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_goal,
        assigned_goal_with_tracking
    ):
        """Test therapist can record progress for assigned patient's goal"""
        test_db.commit()

        progress_data = {
            "entry_date": str(date.today()),
            "entry_time": "14:30:00",
            "value": 7.5,
            "value_label": "Better today",
            "notes": "Client reports progress",
            "context": "session"
        }

        response = async_db_client.post(
            f"/api/v1/goals/{assigned_patient_goal.id}/progress",
            headers=therapist_auth_headers,
            json=progress_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["goal_id"] == str(assigned_patient_goal.id)
        assert data["value"] == 7.5


    def test_therapist_cannot_record_progress_for_unassigned_patient_goal(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_goal
    ):
        """Test therapist cannot record progress for non-assigned patient's goal"""
        test_db.commit()

        progress_data = {
            "entry_date": str(date.today()),
            "entry_time": "14:30:00",
            "value": 5.0,
            "notes": "Unauthorized entry"
        }

        response = async_db_client.post(
            f"/api/v1/goals/{other_patient_goal.id}/progress",
            headers=therapist_auth_headers,
            json=progress_data
        )

        # Should return 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_patient_can_record_progress_for_own_goal(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        assigned_patient_goal,
        assigned_goal_with_tracking
    ):
        """Test patient can record progress for their own goal"""
        test_db.commit()

        progress_data = {
            "entry_date": str(date.today()),
            "entry_time": "20:00:00",
            "value": 6.0,
            "value_label": "Daily check-in",
            "notes": "Feeling better",
            "context": "self_report"
        }

        response = async_db_client.post(
            f"/api/v1/goals/{assigned_patient_goal.id}/progress",
            headers=assigned_patient_auth_headers,
            json=progress_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["goal_id"] == str(assigned_patient_goal.id)


    def test_patient_cannot_record_progress_for_other_patient_goal(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        other_patient_goal
    ):
        """Test patient cannot record progress for another patient's goal"""
        test_db.commit()

        progress_data = {
            "entry_date": str(date.today()),
            "value": 5.0
        }

        response = async_db_client.post(
            f"/api/v1/goals/{other_patient_goal.id}/progress",
            headers=assigned_patient_auth_headers,
            json=progress_data
        )

        # Should return 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_therapist_cannot_record_progress_with_inactive_assignment(
        self,
        async_db_client,
        test_db,
        therapist_user,
        therapist_auth_headers,
        inactive_relationship_patient
    ):
        """Test inactive therapist-patient relationship blocks progress recording"""
        # Create goal for patient with inactive relationship
        goal = TreatmentGoal(
            patient_id=inactive_relationship_patient.id,
            therapist_id=therapist_user.id,
            description="Old goal from inactive relationship",
            category="behavioral",
            status="assigned",
            baseline_value=1.0,
            target_value=5.0,
            target_date=date.today() + timedelta(days=30)
        )
        test_db.add(goal)
        test_db.commit()
        test_db.refresh(goal)

        progress_data = {
            "entry_date": str(date.today()),
            "value": 3.0
        }

        response = async_db_client.post(
            f"/api/v1/goals/{goal.id}/progress",
            headers=therapist_auth_headers,
            json=progress_data
        )

        # Should return 403 Forbidden (relationship is inactive)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: GET /goals/{goal_id}/progress
# ============================================================================

@pytest.mark.goal_tracking
class TestGetProgressHistoryAuthorization:
    """Test authorization for viewing progress history"""

    def test_therapist_can_view_progress_for_assigned_patient_goal(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_goal
    ):
        """Test therapist can view progress history for assigned patient's goal"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/goals/{assigned_patient_goal.id}/progress",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "entries" in data
        assert "summary" in data


    def test_therapist_cannot_view_progress_for_unassigned_patient_goal(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_goal
    ):
        """Test therapist cannot view progress for non-assigned patient's goal"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/goals/{other_patient_goal.id}/progress",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_patient_can_view_progress_for_own_goal(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        assigned_patient_goal
    ):
        """Test patient can view progress history for their own goal"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/goals/{assigned_patient_goal.id}/progress",
            headers=assigned_patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK


    def test_patient_cannot_view_progress_for_other_patient_goal(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        other_patient_goal
    ):
        """Test patient cannot view progress for another patient's goal"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/goals/{other_patient_goal.id}/progress",
            headers=assigned_patient_auth_headers
        )

        # Should return 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: GET /patients/{patient_id}/goals/dashboard
# ============================================================================

@pytest.mark.goal_tracking
class TestGoalDashboardAuthorization:
    """Test authorization for viewing patient goal dashboards"""

    def test_therapist_can_view_assigned_patient_dashboard(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_user
    ):
        """Test therapist can view goal dashboard for assigned patient"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/patients/{assigned_patient_user.id}/goals/dashboard",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["patient_id"] == str(assigned_patient_user.id)
        assert "active_goals" in data


    def test_therapist_cannot_view_unassigned_patient_dashboard(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_user
    ):
        """Test therapist cannot view goal dashboard for non-assigned patient"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/patients/{other_patient_user.id}/goals/dashboard",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_patient_can_view_own_dashboard(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        assigned_patient_user
    ):
        """Test patient can view their own goal dashboard"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/patients/{assigned_patient_user.id}/goals/dashboard",
            headers=assigned_patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["patient_id"] == str(assigned_patient_user.id)


    def test_patient_cannot_view_other_patient_dashboard(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        other_patient_user
    ):
        """Test patient cannot view another patient's goal dashboard"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/patients/{other_patient_user.id}/goals/dashboard",
            headers=assigned_patient_auth_headers
        )

        # Should return 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_therapist_cannot_view_dashboard_with_inactive_assignment(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        inactive_relationship_patient
    ):
        """Test inactive relationship blocks dashboard access"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/patients/{inactive_relationship_patient.id}/goals/dashboard",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden (relationship is inactive)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: POST /patients/{patient_id}/goals
# ============================================================================

@pytest.mark.goal_tracking
class TestCreateGoalAuthorization:
    """Test authorization for creating treatment goals"""

    def test_therapist_can_create_goal_for_assigned_patient(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_user
    ):
        """Test therapist can create goal for assigned patient"""
        test_db.commit()

        goal_data = {
            "description": "Practice mindfulness meditation daily",
            "category": "anxiety_management",
            "baseline_value": 2.0,
            "target_value": 8.0,
            "target_date": str(date.today() + timedelta(days=30))
        }

        response = async_db_client.post(
            f"/api/v1/patients/{assigned_patient_user.id}/goals",
            headers=therapist_auth_headers,
            json=goal_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["patient_id"] == str(assigned_patient_user.id)
        assert data["description"] == goal_data["description"]


    def test_therapist_cannot_create_goal_for_unassigned_patient(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_user
    ):
        """Test therapist cannot create goal for non-assigned patient"""
        test_db.commit()

        goal_data = {
            "description": "Unauthorized goal",
            "category": "behavioral",
            "target_date": str(date.today() + timedelta(days=30))
        }

        response = async_db_client.post(
            f"/api/v1/patients/{other_patient_user.id}/goals",
            headers=therapist_auth_headers,
            json=goal_data
        )

        # Should return 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_patient_cannot_create_goal(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        assigned_patient_user
    ):
        """Test patient role cannot create goals (therapist only)"""
        test_db.commit()

        goal_data = {
            "description": "Self-assigned goal (should fail)",
            "category": "behavioral",
            "target_date": str(date.today() + timedelta(days=30))
        }

        response = async_db_client.post(
            f"/api/v1/patients/{assigned_patient_user.id}/goals",
            headers=assigned_patient_auth_headers,
            json=goal_data
        )

        # Should return 403 Forbidden (therapist role required)
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: GET /patients/{patient_id}/goals
# ============================================================================

@pytest.mark.goal_tracking
class TestListGoalsAuthorization:
    """Test authorization for listing patient goals"""

    def test_therapist_can_list_assigned_patient_goals(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_user,
        assigned_patient_goal
    ):
        """Test therapist can list goals for assigned patient"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/patients/{assigned_patient_user.id}/goals",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert any(goal["id"] == str(assigned_patient_goal.id) for goal in data)


    def test_therapist_cannot_list_unassigned_patient_goals(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_user
    ):
        """Test therapist cannot list goals for non-assigned patient"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/patients/{other_patient_user.id}/goals",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


    def test_patient_can_list_own_goals(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        assigned_patient_user,
        assigned_patient_goal
    ):
        """Test patient can list their own goals"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/patients/{assigned_patient_user.id}/goals",
            headers=assigned_patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


    def test_patient_cannot_list_other_patient_goals(
        self,
        async_db_client,
        test_db,
        assigned_patient_auth_headers,
        other_patient_user
    ):
        """Test patient cannot list another patient's goals"""
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/patients/{other_patient_user.id}/goals",
            headers=assigned_patient_auth_headers
        )

        # Should return 403 Forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test: Unauthenticated Access
# ============================================================================

@pytest.mark.goal_tracking
class TestUnauthenticatedAccess:
    """Test that unauthenticated requests are properly rejected"""

    def test_unauthenticated_requests_fail(
        self,
        async_db_client,
        test_db,
        assigned_patient_goal,
        assigned_patient_user
    ):
        """Test all endpoints reject unauthenticated requests"""
        test_db.commit()

        endpoints = [
            ("POST", f"/api/v1/goals/{assigned_patient_goal.id}/tracking/config", {"tracking_method": "scale"}),
            ("POST", f"/api/v1/goals/{assigned_patient_goal.id}/progress", {"entry_date": str(date.today()), "value": 5}),
            ("GET", f"/api/v1/goals/{assigned_patient_goal.id}/progress", None),
            ("GET", f"/api/v1/patients/{assigned_patient_user.id}/goals/dashboard", None),
            ("POST", f"/api/v1/patients/{assigned_patient_user.id}/goals", {"description": "test"}),
            ("GET", f"/api/v1/patients/{assigned_patient_user.id}/goals", None),
        ]

        for method, endpoint, payload in endpoints:
            if method == "POST":
                response = async_db_client.post(endpoint, json=payload)
            else:
                response = async_db_client.get(endpoint)

            # Should return 401 Unauthorized or 403 Forbidden
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ], f"Endpoint {method} {endpoint} should reject unauthenticated request"
