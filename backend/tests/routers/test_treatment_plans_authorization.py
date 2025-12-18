"""
Authorization and data isolation tests for treatment plan endpoints.

Tests verify that:
- Therapists can only access treatment plans for their assigned patients
- Active therapist-patient relationships are enforced
- Inactive relationships don't grant access
- Role-based access control (therapist vs patient)
- Treatment plan operations (create, read, update, goals, progress) enforce access control
- Proper 403/401 error responses for unauthorized access
"""
import pytest
from fastapi import status
from uuid import uuid4
from datetime import datetime, date, timedelta

# Note: TreatmentPlan/TreatmentPlanGoal are in treatment_models.py (Feature 4)
# There's a separate TreatmentGoal in goal_models.py (Feature 6) that uses a different table
# We renamed TreatmentGoal to TreatmentPlanGoal in treatment_models to avoid naming conflicts
from app.models.db_models import User, TherapistPatient
from app.models.treatment_models import TreatmentPlan, TreatmentPlanGoal, GoalProgress
from app.models.schemas import UserRole
from app.auth.utils import get_password_hash


# ============================================================================
# Fixtures for Treatment Plan Authorization Tests
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
def assigned_patient_plan(test_db, therapist_user, assigned_patient_user):
    """
    Create a treatment plan for assigned patient.

    Args:
        test_db: Test database session
        therapist_user: Therapist user fixture
        assigned_patient_user: Patient assigned to therapist

    Returns:
        TreatmentPlan object for assigned patient
    """
    plan = TreatmentPlan(
        patient_id=assigned_patient_user.id,
        therapist_id=therapist_user.id,
        title="Anxiety Treatment Plan",
        diagnosis_codes=[{"code": "F41.1", "description": "Generalized anxiety disorder"}],
        presenting_problems=["Work-related anxiety", "Social anxiety"],
        start_date=date.today(),
        target_end_date=date.today() + timedelta(days=90),
        review_frequency_days=30,
        next_review_date=date.today() + timedelta(days=30),
        status="active",
        version=1,
        notes="Initial treatment plan for anxiety management"
    )
    test_db.add(plan)
    test_db.commit()
    test_db.refresh(plan)
    return plan


@pytest.fixture(scope="function")
def other_therapist_plan(test_db, other_therapist_user, other_patient_user):
    """
    Create a treatment plan owned by other therapist.

    Args:
        test_db: Test database session
        other_therapist_user: Other therapist user fixture
        other_patient_user: Patient assigned to other therapist

    Returns:
        TreatmentPlan object for other therapist's patient
    """
    plan = TreatmentPlan(
        patient_id=other_patient_user.id,
        therapist_id=other_therapist_user.id,
        title="Depression Treatment Plan",
        diagnosis_codes=[{"code": "F33.1", "description": "Major depressive disorder"}],
        presenting_problems=["Persistent low mood", "Sleep disturbance"],
        start_date=date.today(),
        target_end_date=date.today() + timedelta(days=120),
        review_frequency_days=30,
        next_review_date=date.today() + timedelta(days=30),
        status="active",
        version=1,
        notes="Other therapist's treatment plan"
    )
    test_db.add(plan)
    test_db.commit()
    test_db.refresh(plan)
    return plan


@pytest.fixture(scope="function")
def assigned_plan_goal(test_db, assigned_patient_plan):
    """
    Create a goal for assigned patient's treatment plan.

    Args:
        test_db: Test database session
        assigned_patient_plan: Treatment plan for assigned patient

    Returns:
        TreatmentGoal object for assigned patient's plan
    """
    goal = TreatmentPlanGoal(
        plan_id=assigned_patient_plan.id,
        goal_type="short_term",
        description="Practice relaxation techniques daily",
        measurable_criteria="Frequency of practice sessions per week",
        baseline_value="0",
        target_value="7",
        target_date=date.today() + timedelta(days=30),
        status="not_started",
        progress_percentage=0,
        priority=1
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)
    return goal


@pytest.fixture(scope="function")
def other_plan_goal(test_db, other_therapist_plan):
    """
    Create a goal for other therapist's treatment plan.

    Args:
        test_db: Test database session
        other_therapist_plan: Treatment plan for other therapist's patient

    Returns:
        TreatmentGoal object for other therapist's plan
    """
    goal = TreatmentPlanGoal(
        plan_id=other_therapist_plan.id,
        goal_type="short_term",
        description="Improve sleep hygiene",
        measurable_criteria="Hours of sleep per night",
        baseline_value="4",
        target_value="7",
        target_date=date.today() + timedelta(days=30),
        status="in_progress",
        progress_percentage=20,
        priority=1
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)
    return goal


# ============================================================================
# Therapist-Patient Relationship Access Tests
# ============================================================================

class TestTherapistPatientRelationshipAccess:
    """Test therapist can only access plans for assigned patients"""

    def test_therapist_can_access_assigned_patient_plan(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_plan
    ):
        """Test therapist can access treatment plan for assigned patient"""
        # Ensure data is committed
        test_db.commit()

        # Access plan details
        response = async_db_client.get(
            f"/api/v1/treatment-plans/{assigned_patient_plan.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(assigned_patient_plan.id)
        assert data["title"] == "Anxiety Treatment Plan"


    def test_therapist_cannot_access_unassigned_patient_plan(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_therapist_plan
    ):
        """Test therapist cannot access treatment plan for unassigned patient"""
        # Ensure data is committed
        test_db.commit()

        # Try to access other therapist's plan
        response = async_db_client.get(
            f"/api/v1/treatment-plans/{other_therapist_plan.id}",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden (patient not assigned to current therapist)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "access denied" in error_msg.lower() or "not assigned" in error_msg.lower()


    def test_therapist_cannot_access_inactive_relationship_plan(
        self,
        async_db_client,
        test_db,
        therapist_user,
        therapist_auth_headers,
        inactive_relationship_patient
    ):
        """Test inactive therapist-patient relationship blocks plan access"""
        # Create plan for patient with inactive relationship
        plan = TreatmentPlan(
            patient_id=inactive_relationship_patient.id,
            therapist_id=therapist_user.id,
            title="Old Treatment Plan",
            start_date=date.today() - timedelta(days=60),
            review_frequency_days=30,
            next_review_date=date.today() - timedelta(days=30),
            status="discontinued",
            version=1
        )
        test_db.add(plan)
        test_db.commit()
        test_db.refresh(plan)

        # Try to access plan with inactive relationship
        response = async_db_client.get(
            f"/api/v1/treatment-plans/{plan.id}",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden (relationship is inactive)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "access denied" in error_msg.lower() or "not assigned" in error_msg.lower()


# ============================================================================
# Treatment Plan CRUD Authorization Tests
# ============================================================================

class TestTreatmentPlanCRUDAuthorization:
    """Test authorization for create, read, update operations on treatment plans"""

    def test_therapist_can_create_plan_for_assigned_patient(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_user
    ):
        """Test therapist can create treatment plan for assigned patient"""
        # Ensure data is committed
        test_db.commit()

        plan_data = {
            "title": "New Anxiety Treatment Plan",
            "diagnosis_codes": [{"code": "F41.1", "description": "GAD"}],
            "presenting_problems": ["Anxiety", "Stress"],
            "start_date": str(date.today()),
            "target_end_date": str(date.today() + timedelta(days=90)),
            "review_frequency_days": 30,
            "notes": "Initial plan"
        }

        response = async_db_client.post(
            f"/api/v1/patients/{assigned_patient_user.id}/treatment-plans",
            headers=therapist_auth_headers,
            json=plan_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "New Anxiety Treatment Plan"
        assert data["patient_id"] == str(assigned_patient_user.id)


    def test_therapist_cannot_create_plan_for_unassigned_patient(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_user
    ):
        """Test therapist cannot create treatment plan for unassigned patient"""
        # Ensure data is committed
        test_db.commit()

        plan_data = {
            "title": "Unauthorized Plan",
            "start_date": str(date.today()),
            "review_frequency_days": 30
        }

        response = async_db_client.post(
            f"/api/v1/patients/{other_patient_user.id}/treatment-plans",
            headers=therapist_auth_headers,
            json=plan_data
        )

        # Should return 403 Forbidden (patient not assigned)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "access denied" in error_msg.lower() or "not have access" in error_msg.lower()


    def test_therapist_can_update_own_plan(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_plan
    ):
        """Test therapist can update their own treatment plan"""
        # Ensure data is committed
        test_db.commit()

        update_data = {
            "title": "Updated Anxiety Treatment Plan",
            "notes": "Updated treatment notes"
        }

        response = async_db_client.put(
            f"/api/v1/treatment-plans/{assigned_patient_plan.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "Updated Anxiety Treatment Plan"
        assert data["notes"] == "Updated treatment notes"


    def test_therapist_cannot_update_other_therapist_plan(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_therapist_plan
    ):
        """Test therapist cannot update another therapist's treatment plan"""
        # Ensure data is committed
        test_db.commit()

        update_data = {
            "title": "Unauthorized Update",
            "notes": "Should fail"
        }

        response = async_db_client.put(
            f"/api/v1/treatment-plans/{other_therapist_plan.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        # Should return 403 Forbidden (not authorized)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "access denied" in error_msg.lower() or "not assigned" in error_msg.lower()


    def test_therapist_can_list_assigned_patient_plans(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_user,
        assigned_patient_plan
    ):
        """Test therapist can list treatment plans for assigned patient"""
        # Ensure data is committed
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/patients/{assigned_patient_user.id}/treatment-plans",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert any(plan["id"] == str(assigned_patient_plan.id) for plan in data)


    def test_therapist_cannot_list_unassigned_patient_plans(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_patient_user,
        other_therapist_plan
    ):
        """Test therapist cannot list treatment plans for unassigned patient"""
        # Ensure data is committed
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/patients/{other_patient_user.id}/treatment-plans",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden (patient not assigned)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "access denied" in error_msg.lower() or "not have access" in error_msg.lower()


# ============================================================================
# Goal Operations Authorization Tests
# ============================================================================

class TestGoalOperationsAuthorization:
    """Test authorization for goal-related operations"""

    def test_therapist_can_add_goal_to_own_plan(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_patient_plan
    ):
        """Test therapist can add goal to their own treatment plan"""
        # Ensure data is committed
        test_db.commit()

        goal_data = {
            "goal_type": "short_term",
            "description": "Reduce anxiety symptoms",
            "measurable_criteria": "Anxiety scale rating",
            "baseline_value": "8",
            "target_value": "4",
            "target_date": str(date.today() + timedelta(days=30)),
            "priority": 1
        }

        response = async_db_client.post(
            f"/api/v1/treatment-plans/{assigned_patient_plan.id}/goals",
            headers=therapist_auth_headers,
            json=goal_data
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["description"] == "Reduce anxiety symptoms"
        assert data["plan_id"] == str(assigned_patient_plan.id)


    def test_therapist_cannot_add_goal_to_other_plan(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_therapist_plan
    ):
        """Test therapist cannot add goal to another therapist's treatment plan"""
        # Ensure data is committed
        test_db.commit()

        goal_data = {
            "goal_type": "short_term",
            "description": "Unauthorized goal",
            "priority": 1
        }

        response = async_db_client.post(
            f"/api/v1/treatment-plans/{other_therapist_plan.id}/goals",
            headers=therapist_auth_headers,
            json=goal_data
        )

        # Should return 403 Forbidden (not authorized)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "not authorized" in error_msg.lower() or "access" in error_msg.lower()


    def test_therapist_can_update_own_goal(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_plan_goal
    ):
        """Test therapist can update goal on their own treatment plan"""
        # Ensure data is committed
        test_db.commit()

        update_data = {
            "status": "in_progress",
            "progress_percentage": 25,
            "current_value": "2"
        }

        response = async_db_client.put(
            f"/api/v1/goals/{assigned_plan_goal.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["progress_percentage"] == 25


    def test_therapist_cannot_update_other_goal(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_plan_goal
    ):
        """Test therapist cannot update goal on another therapist's plan"""
        # Ensure data is committed
        test_db.commit()

        update_data = {
            "status": "achieved",
            "progress_percentage": 100
        }

        response = async_db_client.put(
            f"/api/v1/goals/{other_plan_goal.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        # Should return 403 Forbidden (not authorized)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "not authorized" in error_msg.lower() or "access" in error_msg.lower()


    def test_therapist_can_record_progress_on_own_goal(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        assigned_plan_goal
    ):
        """Test therapist can record progress on goal in their own plan"""
        # Ensure data is committed
        test_db.commit()

        progress_data = {
            "progress_note": "Client practicing techniques daily",
            "progress_value": "3",
            "rating": 7
        }

        response = async_db_client.post(
            f"/api/v1/goals/{assigned_plan_goal.id}/progress",
            headers=therapist_auth_headers,
            json=progress_data
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["progress_note"] == "Client practicing techniques daily"
        assert data["rating"] == 7


    def test_therapist_cannot_record_progress_on_other_goal(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        other_plan_goal
    ):
        """Test therapist cannot record progress on another therapist's goal"""
        # Ensure data is committed
        test_db.commit()

        progress_data = {
            "progress_note": "Unauthorized progress entry",
            "rating": 5
        }

        response = async_db_client.post(
            f"/api/v1/goals/{other_plan_goal.id}/progress",
            headers=therapist_auth_headers,
            json=progress_data
        )

        # Should return 403 Forbidden (not authorized)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "not authorized" in error_msg.lower() or "access" in error_msg.lower()


# ============================================================================
# Role-Based Access Control Tests
# ============================================================================

class TestRoleBasedAccessControl:
    """Test that RBAC is properly enforced for treatment plan endpoints"""

    def test_patient_cannot_create_treatment_plan(
        self,
        async_db_client,
        test_db,
        patient_auth_headers,
        patient_user
    ):
        """Patient role cannot create treatment plans"""
        # Ensure data is committed
        test_db.commit()

        plan_data = {
            "title": "Patient-created plan (should fail)",
            "start_date": str(date.today()),
            "review_frequency_days": 30
        }

        response = async_db_client.post(
            f"/api/v1/patients/{patient_user.id}/treatment-plans",
            headers=patient_auth_headers,
            json=plan_data
        )

        # Should return 403 Forbidden (therapist role required)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "role" in error_msg.lower() or "forbidden" in error_msg.lower() or "access denied" in error_msg.lower()


    def test_patient_cannot_access_treatment_plan(
        self,
        async_db_client,
        test_db,
        patient_auth_headers,
        assigned_patient_plan
    ):
        """Patient role cannot access treatment plan details"""
        # Ensure data is committed
        test_db.commit()

        response = async_db_client.get(
            f"/api/v1/treatment-plans/{assigned_patient_plan.id}",
            headers=patient_auth_headers
        )

        # Should return 403 Forbidden (therapist role required)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "role" in error_msg.lower() or "forbidden" in error_msg.lower() or "access denied" in error_msg.lower()


    def test_patient_cannot_update_treatment_plan(
        self,
        async_db_client,
        test_db,
        patient_auth_headers,
        assigned_patient_plan
    ):
        """Patient role cannot update treatment plans"""
        # Ensure data is committed
        test_db.commit()

        update_data = {
            "title": "Unauthorized update",
            "notes": "Should fail"
        }

        response = async_db_client.put(
            f"/api/v1/treatment-plans/{assigned_patient_plan.id}",
            headers=patient_auth_headers,
            json=update_data
        )

        # Should return 403 Forbidden (therapist role required)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "role" in error_msg.lower() or "forbidden" in error_msg.lower() or "access denied" in error_msg.lower()


    def test_patient_cannot_add_goals(
        self,
        async_db_client,
        test_db,
        patient_auth_headers,
        assigned_patient_plan
    ):
        """Patient role cannot add goals to treatment plans"""
        # Ensure data is committed
        test_db.commit()

        goal_data = {
            "goal_type": "short_term",
            "description": "Unauthorized goal",
            "priority": 1
        }

        response = async_db_client.post(
            f"/api/v1/treatment-plans/{assigned_patient_plan.id}/goals",
            headers=patient_auth_headers,
            json=goal_data
        )

        # Should return 403 Forbidden (therapist role required)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        error_msg = response.json().get("detail", "")
        assert "role" in error_msg.lower() or "forbidden" in error_msg.lower() or "access denied" in error_msg.lower()


    def test_unauthenticated_request_fails(
        self,
        async_db_client,
        test_db,
        assigned_patient_plan
    ):
        """Unauthenticated requests to treatment plan endpoints fail"""
        # Ensure data is committed
        test_db.commit()

        endpoints = [
            f"/api/v1/treatment-plans/{assigned_patient_plan.id}",
            f"/api/v1/treatment-plans/{assigned_patient_plan.id}/goals",
        ]

        for endpoint in endpoints:
            response = async_db_client.get(endpoint)

            # Should return 401 Unauthorized or 403 Forbidden
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ], f"Endpoint {endpoint} should reject unauthenticated request"


# ============================================================================
# Cross-Therapist Data Isolation Tests
# ============================================================================

class TestCrossTherapistDataIsolation:
    """Test that therapists cannot access each other's data"""

    def test_therapist_cannot_see_other_therapist_plan_in_list(
        self,
        async_db_client,
        test_db,
        therapist_user,
        therapist_auth_headers,
        assigned_patient_user,
        assigned_patient_plan,
        other_therapist_user,
        other_patient_user,
        other_therapist_plan
    ):
        """Test therapist only sees their own plans when listing patient plans"""
        # Ensure data is committed
        test_db.commit()

        # Request plans for assigned patient
        response = async_db_client.get(
            f"/api/v1/patients/{assigned_patient_user.id}/treatment-plans",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should only see assigned patient's plans
        plan_ids = [plan["id"] for plan in data]
        assert str(assigned_patient_plan.id) in plan_ids
        assert str(other_therapist_plan.id) not in plan_ids


    def test_shared_patient_respects_therapist_filter(
        self,
        async_db_client,
        test_db,
        therapist_user,
        therapist_auth_headers,
        other_therapist_user,
        other_therapist_auth_headers
    ):
        """Test shared patients: each therapist only sees their own plans"""
        # Create shared patient
        shared_patient = User(
            email="shared@patient.com",
            hashed_password=get_password_hash("sharedpass123"),
            first_name="Shared",
            last_name="Patient",
            full_name="Shared Patient",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        test_db.add(shared_patient)
        test_db.commit()
        test_db.refresh(shared_patient)

        # Create relationships for BOTH therapists
        rel1 = TherapistPatient(
            therapist_id=therapist_user.id,
            patient_id=shared_patient.id,
            is_active=True,
            relationship_type="primary"
        )
        rel2 = TherapistPatient(
            therapist_id=other_therapist_user.id,
            patient_id=shared_patient.id,
            is_active=True,
            relationship_type="secondary"
        )
        test_db.add_all([rel1, rel2])
        test_db.commit()

        # Create plan for therapist_user
        plan1 = TreatmentPlan(
            patient_id=shared_patient.id,
            therapist_id=therapist_user.id,
            title="Therapist 1 Plan",
            start_date=date.today(),
            review_frequency_days=30,
            next_review_date=date.today() + timedelta(days=30),
            status="active",
            version=1
        )
        # Create plan for other_therapist_user
        plan2 = TreatmentPlan(
            patient_id=shared_patient.id,
            therapist_id=other_therapist_user.id,
            title="Therapist 2 Plan",
            start_date=date.today(),
            review_frequency_days=30,
            next_review_date=date.today() + timedelta(days=30),
            status="active",
            version=1
        )
        test_db.add_all([plan1, plan2])
        test_db.commit()
        test_db.refresh(plan1)
        test_db.refresh(plan2)

        # Therapist 1 should only access their own plan
        response1 = async_db_client.get(
            f"/api/v1/treatment-plans/{plan1.id}",
            headers=therapist_auth_headers
        )
        assert response1.status_code == status.HTTP_200_OK

        # Therapist 1 should NOT access therapist 2's plan
        response2 = async_db_client.get(
            f"/api/v1/treatment-plans/{plan2.id}",
            headers=therapist_auth_headers
        )
        assert response2.status_code == status.HTTP_403_FORBIDDEN

        # Therapist 2 should only access their own plan
        response3 = async_db_client.get(
            f"/api/v1/treatment-plans/{plan2.id}",
            headers=other_therapist_auth_headers
        )
        assert response3.status_code == status.HTTP_200_OK

        # Therapist 2 should NOT access therapist 1's plan
        response4 = async_db_client.get(
            f"/api/v1/treatment-plans/{plan1.id}",
            headers=other_therapist_auth_headers
        )
        assert response4.status_code == status.HTTP_403_FORBIDDEN
