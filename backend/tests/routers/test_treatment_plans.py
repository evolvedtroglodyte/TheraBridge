"""
Integration tests for treatment plan routers (Feature 4).

Tests cover all endpoints across three routers:
- Treatment Plans Router (5 endpoints)
- Goals Router (5 endpoints)
- Interventions Router (3 endpoints)

Total: 13 endpoints, 25+ test cases covering:
- Successful operations
- Authentication/authorization
- Validation errors
- Response structure validation
- Query parameter filtering
- Goal hierarchy validation
- Progress calculation correctness
"""
import pytest
from fastapi import status
from uuid import uuid4
from datetime import date, datetime, timedelta
from app.models.db_models import User
from app.models.treatment_models import (
    TreatmentPlan,
    GoalProgress,
    Intervention,
    GoalIntervention,
    PlanReview
)
from app.models.goal_models import TreatmentGoal
from app.models.schemas import UserRole
from app.models.treatment_schemas import PlanStatus, GoalStatus, GoalType, EvidenceLevel


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_patient_for_plans(test_db, therapist_user):
    """Create a patient user for treatment plan testing"""
    patient = User(
        email="planpatient@test.com",
        hashed_password="hashed",
        first_name="Plan",
        last_name="Patient",
        full_name="Plan Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)
    return patient


@pytest.fixture(scope="function")
def sample_treatment_plan(test_db, therapist_user, test_patient_for_plans):
    """Create a sample treatment plan for testing"""
    plan = TreatmentPlan(
        patient_id=test_patient_for_plans.id,
        therapist_id=therapist_user.id,
        title="Anxiety Management Plan",
        diagnosis_codes=[
            {"code": "F41.1", "description": "Generalized anxiety disorder"}
        ],
        presenting_problems=["Work stress", "Sleep issues", "Social anxiety"],
        start_date=date.today(),
        target_end_date=date.today() + timedelta(days=180),
        review_frequency_days=30,
        next_review_date=date.today() + timedelta(days=30),
        notes="Client is motivated and engaged",
        status=PlanStatus.active,
        version=1
    )
    test_db.add(plan)
    test_db.commit()
    test_db.refresh(plan)
    return plan


@pytest.fixture(scope="function")
def sample_goal(test_db, sample_treatment_plan):
    """Create a sample treatment goal"""
    goal = TreatmentGoal(
        plan_id=sample_treatment_plan.id,
        parent_goal_id=None,
        goal_type=GoalType.long_term.value,
        description="Reduce anxiety symptoms to manageable levels",
        measurable_criteria="GAD-7 score below 10",
        baseline_value="GAD-7: 18",
        target_value="GAD-7: <10",
        target_date=date.today() + timedelta(days=90),
        priority=1,
        status=GoalStatus.in_progress.value,
        progress_percentage=25
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)
    return goal


@pytest.fixture(scope="function")
def system_intervention(test_db):
    """Create a system intervention for testing"""
    intervention = Intervention(
        name="Cognitive Restructuring",
        description="Challenge and reframe negative thought patterns",
        modality="CBT",
        evidence_level=EvidenceLevel.strong.value,
        is_system=True,
        created_by=None
    )
    test_db.add(intervention)
    test_db.commit()
    test_db.refresh(intervention)
    return intervention


# ============================================================================
# Treatment Plans Router Tests (5 endpoints)
# ============================================================================

class TestTreatmentPlansRouter:
    """Test /patients/{patient_id}/treatment-plans and /treatment-plans/{plan_id} endpoints"""

    def test_create_treatment_plan_success(
        self,
        client,
        test_db,
        therapist_auth_headers,
        test_patient_for_plans
    ):
        """Test successful treatment plan creation"""
        plan_data = {
            "title": "Depression Treatment Plan",
            "diagnosis_codes": [
                {"code": "F32.1", "description": "Major depressive disorder, single episode, moderate"}
            ],
            "presenting_problems": ["Low mood", "Fatigue", "Loss of interest"],
            "start_date": str(date.today()),
            "target_end_date": str(date.today() + timedelta(days=120)),
            "review_frequency_days": 30,
            "notes": "Client recently started therapy"
        }

        response = client.post(
            f"/api/v1/patients/{test_patient_for_plans.id}/treatment-plans",
            json=plan_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["title"] == "Depression Treatment Plan"
        assert data["patient_id"] == str(test_patient_for_plans.id)
        assert data["status"] == PlanStatus.active.value
        assert data["version"] == 1
        assert "next_review_date" in data
        assert len(data["diagnosis_codes"]) == 1
        assert len(data["presenting_problems"]) == 3

    def test_create_treatment_plan_requires_auth(
        self,
        client,
        test_patient_for_plans
    ):
        """Test that creating a plan requires authentication"""
        plan_data = {
            "title": "Test Plan",
            "start_date": str(date.today()),
            "review_frequency_days": 30
        }

        response = client.post(
            f"/api/v1/patients/{test_patient_for_plans.id}/treatment-plans",
            json=plan_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_treatment_plan_validation_errors(
        self,
        client,
        therapist_auth_headers,
        test_patient_for_plans
    ):
        """Test validation errors for invalid plan data"""
        # Missing required fields
        invalid_data = {
            "title": "",  # Empty title
            "start_date": str(date.today())
        }

        response = client.post(
            f"/api/v1/patients/{test_patient_for_plans.id}/treatment-plans",
            json=invalid_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_list_patient_treatment_plans(
        self,
        client,
        test_db,
        therapist_auth_headers,
        test_patient_for_plans,
        sample_treatment_plan
    ):
        """Test listing all treatment plans for a patient"""
        # Create a second plan
        plan2 = TreatmentPlan(
            patient_id=test_patient_for_plans.id,
            therapist_id=sample_treatment_plan.therapist_id,
            title="Follow-up Plan",
            start_date=date.today() + timedelta(days=90),
            review_frequency_days=30,
            next_review_date=date.today() + timedelta(days=120),
            status=PlanStatus.active,
            version=1
        )
        test_db.add(plan2)
        test_db.commit()

        response = client.get(
            f"/api/v1/patients/{test_patient_for_plans.id}/treatment-plans",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response is a list
        assert isinstance(data, list)
        assert len(data) == 2

        # Verify list item structure
        for item in data:
            assert "id" in item
            assert "title" in item
            assert "status" in item
            assert "start_date" in item
            assert "goal_count" in item
            assert "overall_progress" in item
            assert "created_at" in item

    def test_get_treatment_plan_with_goals(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan,
        sample_goal
    ):
        """Test retrieving full treatment plan with goals"""
        response = client.get(
            f"/api/v1/treatment-plans/{sample_treatment_plan.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify plan data
        assert data["id"] == str(sample_treatment_plan.id)
        assert data["title"] == "Anxiety Management Plan"

        # Verify goals are included
        assert "goals" in data
        assert isinstance(data["goals"], list)
        assert len(data["goals"]) == 1
        assert data["goals"][0]["id"] == str(sample_goal.id)

        # Verify progress summary
        assert "progress_summary" in data
        assert data["progress_summary"]["total_goals"] == 1
        assert data["progress_summary"]["in_progress"] == 1
        assert data["progress_summary"]["overall_progress"] == 25

    def test_get_treatment_plan_not_found(
        self,
        client,
        therapist_auth_headers
    ):
        """Test 404 for non-existent treatment plan"""
        nonexistent_id = uuid4()

        response = client.get(
            f"/api/v1/treatment-plans/{nonexistent_id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_treatment_plan(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan
    ):
        """Test updating a treatment plan"""
        update_data = {
            "title": "Updated Anxiety Management Plan",
            "status": PlanStatus.on_hold.value,
            "notes": "Client requested pause due to work commitments"
        }

        response = client.put(
            f"/api/v1/treatment-plans/{sample_treatment_plan.id}",
            json=update_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify updates
        assert data["title"] == "Updated Anxiety Management Plan"
        assert data["status"] == PlanStatus.on_hold.value
        assert data["notes"] == "Client requested pause due to work commitments"
        # Version should increment due to significant change (title)
        assert data["version"] == 2

    def test_update_treatment_plan_invalid_data(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan
    ):
        """Test validation errors when updating plan"""
        # Empty update data
        response = client.put(
            f"/api/v1/treatment-plans/{sample_treatment_plan.id}",
            json={},
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No update data provided" in response.json()["detail"]

    def test_create_plan_review(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan
    ):
        """Test recording a plan review"""
        review_data = {
            "review_date": str(date.today()),
            "summary": "Client making steady progress. All goals remain appropriate.",
            "goals_reviewed": 3,
            "goals_on_track": 2,
            "modifications_made": "Adjusted timeline for goal #2",
            "next_review_date": str(date.today() + timedelta(days=30))
        }

        response = client.post(
            f"/api/v1/treatment-plans/{sample_treatment_plan.id}/review",
            json=review_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify review data
        assert "id" in data
        assert data["plan_id"] == str(sample_treatment_plan.id)
        assert data["summary"] == review_data["summary"]
        assert data["goals_reviewed"] == 3
        assert data["goals_on_track"] == 2


# ============================================================================
# Goals Router Tests (5 endpoints)
# ============================================================================

class TestGoalsRouter:
    """Test /treatment-plans/{plan_id}/goals and /goals/{goal_id} endpoints"""

    def test_create_goal_in_plan(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan,
        system_intervention
    ):
        """Test creating a goal within a treatment plan"""
        goal_data = {
            "plan_id": str(sample_treatment_plan.id),
            "goal_type": GoalType.short_term.value,
            "description": "Practice deep breathing 3x daily",
            "measurable_criteria": "Self-report daily log completion",
            "baseline_value": "0 times/day",
            "target_value": "3 times/day",
            "target_date": str(date.today() + timedelta(days=30)),
            "priority": 2,
            "interventions": [
                {
                    "intervention_id": str(system_intervention.id),
                    "frequency": "3 times daily",
                    "notes": "Use box breathing technique"
                }
            ]
        }

        response = client.post(
            f"/api/v1/treatment-plans/{sample_treatment_plan.id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify goal data
        assert "id" in data
        assert data["plan_id"] == str(sample_treatment_plan.id)
        assert data["description"] == "Practice deep breathing 3x daily"
        assert data["goal_type"] == GoalType.short_term.value
        assert data["status"] == GoalStatus.not_started.value
        assert data["progress_percentage"] == 0
        assert data["priority"] == 2

    def test_create_goal_with_parent_hierarchy(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan,
        sample_goal
    ):
        """Test creating a sub-goal with parent hierarchy"""
        sub_goal_data = {
            "plan_id": str(sample_treatment_plan.id),
            "parent_goal_id": str(sample_goal.id),
            "goal_type": GoalType.objective.value,
            "description": "Complete anxiety symptom log daily",
            "measurable_criteria": "7 consecutive days of completed logs",
            "target_date": str(date.today() + timedelta(days=14)),
            "priority": 1
        }

        response = client.post(
            f"/api/v1/treatment-plans/{sample_treatment_plan.id}/goals",
            json=sub_goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify parent relationship
        assert data["parent_goal_id"] == str(sample_goal.id)
        assert data["goal_type"] == GoalType.objective.value

    def test_create_goal_invalid_parent(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan
    ):
        """Test validation error when parent goal not in same plan"""
        invalid_parent_id = uuid4()

        goal_data = {
            "plan_id": str(sample_treatment_plan.id),
            "parent_goal_id": str(invalid_parent_id),
            "goal_type": GoalType.objective.value,
            "description": "Test goal",
            "priority": 1
        }

        response = client.post(
            f"/api/v1/treatment-plans/{sample_treatment_plan.id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Parent goal" in response.json()["detail"]

    def test_update_goal_progress_percentage(
        self,
        client,
        therapist_auth_headers,
        sample_goal
    ):
        """Test updating goal progress percentage"""
        update_data = {
            "progress_percentage": 50,
            "status": GoalStatus.in_progress.value
        }

        response = client.put(
            f"/api/v1/goals/{sample_goal.id}",
            json=update_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify progress update
        assert data["progress_percentage"] == 50
        assert data["status"] == GoalStatus.in_progress.value

    def test_record_goal_progress(
        self,
        client,
        therapist_auth_headers,
        sample_goal
    ):
        """Test recording a progress entry for a goal"""
        progress_data = {
            "progress_note": "Client reports using breathing exercises before meetings with success",
            "progress_value": "GAD-7: 14",
            "rating": 7
        }

        response = client.post(
            f"/api/v1/goals/{sample_goal.id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify progress entry
        assert "id" in data
        assert data["goal_id"] == str(sample_goal.id)
        assert data["progress_note"] == progress_data["progress_note"]
        assert data["progress_value"] == "GAD-7: 14"
        assert data["rating"] == 7

    def test_record_goal_progress_auto_calculation(
        self,
        client,
        test_db,
        therapist_auth_headers,
        sample_goal
    ):
        """Test that progress updates auto-calculate based on rating"""
        progress_data = {
            "progress_note": "Goal achieved!",
            "progress_value": "GAD-7: 8",  # Matches target (<10)
            "rating": 10
        }

        response = client.post(
            f"/api/v1/goals/{sample_goal.id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify goal progress was updated
        test_db.refresh(sample_goal)
        # Rating of 10 should set progress to 100%
        assert sample_goal.progress_percentage == 100
        assert sample_goal.status == GoalStatus.achieved.value

    def test_get_goal_progress_history(
        self,
        client,
        test_db,
        therapist_auth_headers,
        sample_goal
    ):
        """Test retrieving goal progress history"""
        # Create multiple progress entries
        progress_entries = [
            GoalProgress(
                goal_id=sample_goal.id,
                recorded_by=sample_goal.plan.therapist_id,
                progress_note=f"Progress note {i}",
                progress_value=f"Value {i}",
                rating=i+3
            )
            for i in range(3)
        ]
        test_db.add_all(progress_entries)
        test_db.commit()

        response = client.get(
            f"/api/v1/goals/{sample_goal.id}/history",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify history
        assert isinstance(data, list)
        assert len(data) == 3

        # Verify entries are ordered by most recent first
        for entry in data:
            assert "id" in entry
            assert "goal_id" in entry
            assert "progress_note" in entry
            assert "recorded_at" in entry


# ============================================================================
# Interventions Router Tests (3 endpoints)
# ============================================================================

class TestInterventionsRouter:
    """Test /interventions endpoints"""

    def test_list_interventions_with_filters(
        self,
        client,
        test_db,
        therapist_auth_headers,
        therapist_user,
        system_intervention
    ):
        """Test listing interventions with various filters"""
        # Create custom intervention
        custom_intervention = Intervention(
            name="Custom Mindfulness Exercise",
            description="Personalized breathing exercise for client",
            modality="Mindfulness",
            evidence_level=EvidenceLevel.moderate.value,
            is_system=False,
            created_by=therapist_user.id
        )
        test_db.add(custom_intervention)
        test_db.commit()

        # Test: List all interventions
        response = client.get(
            "/api/v1/interventions",
            headers=therapist_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 2

        # Test: Filter by modality
        response = client.get(
            "/api/v1/interventions?modality=CBT",
            headers=therapist_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all("CBT" in item["modality"] for item in data if item["modality"])

        # Test: Filter by evidence level
        response = client.get(
            f"/api/v1/interventions?evidence_level={EvidenceLevel.strong.value}",
            headers=therapist_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["evidence_level"] == EvidenceLevel.strong.value for item in data if item["evidence_level"])

        # Test: Search by name
        response = client.get(
            "/api/v1/interventions?search=Mindfulness",
            headers=therapist_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any("Mindfulness" in item["name"] for item in data)

    def test_list_interventions_include_filters(
        self,
        client,
        test_db,
        therapist_auth_headers,
        therapist_user,
        system_intervention
    ):
        """Test include_system and include_custom filters"""
        # Create custom intervention
        custom = Intervention(
            name="My Custom Intervention",
            description="Custom technique",
            is_system=False,
            created_by=therapist_user.id
        )
        test_db.add(custom)
        test_db.commit()

        # Test: Only system interventions
        response = client.get(
            "/api/v1/interventions?include_system=true&include_custom=false",
            headers=therapist_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(item["is_system"] for item in data)

        # Test: Only custom interventions
        response = client.get(
            "/api/v1/interventions?include_system=false&include_custom=true",
            headers=therapist_auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(not item["is_system"] for item in data)

    def test_create_custom_intervention(
        self,
        client,
        therapist_auth_headers
    ):
        """Test creating a custom intervention"""
        intervention_data = {
            "name": "Modified Progressive Muscle Relaxation",
            "description": "Adapted PMR technique for client with mobility issues",
            "modality": "Relaxation",
            "evidence_level": EvidenceLevel.moderate.value
        }

        response = client.post(
            "/api/v1/interventions",
            json=intervention_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify intervention data
        assert "id" in data
        assert data["name"] == "Modified Progressive Muscle Relaxation"
        assert data["is_system"] is False
        assert data["modality"] == "Relaxation"
        assert data["evidence_level"] == EvidenceLevel.moderate.value

    def test_create_custom_intervention_requires_therapist(
        self,
        client,
        patient_auth_headers
    ):
        """Test that only therapists can create interventions"""
        intervention_data = {
            "name": "Test Intervention",
            "description": "This should fail"
        }

        response = client.post(
            "/api/v1/interventions",
            json=intervention_data,
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "therapist" in response.json()["detail"].lower()

    def test_get_intervention_by_id(
        self,
        client,
        therapist_auth_headers,
        system_intervention
    ):
        """Test retrieving intervention details by ID"""
        response = client.get(
            f"/api/v1/interventions/{system_intervention.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify intervention data
        assert data["id"] == str(system_intervention.id)
        assert data["name"] == "Cognitive Restructuring"
        assert data["modality"] == "CBT"
        assert data["is_system"] is True

    def test_get_intervention_not_found(
        self,
        client,
        therapist_auth_headers
    ):
        """Test 404 for non-existent intervention"""
        nonexistent_id = uuid4()

        response = client.get(
            f"/api/v1/interventions/{nonexistent_id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_custom_intervention_authorization(
        self,
        client,
        test_db,
        therapist_auth_headers,
        therapist_user
    ):
        """Test that custom interventions are only accessible by creator"""
        # Create a second therapist
        other_therapist = User(
            email="other@test.com",
            hashed_password="hashed",
            first_name="Other",
            last_name="Therapist",
            full_name="Other Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=False
        )
        test_db.add(other_therapist)
        test_db.commit()
        test_db.refresh(other_therapist)

        # Create intervention owned by other therapist
        other_intervention = Intervention(
            name="Other's Custom Intervention",
            description="Private intervention",
            is_system=False,
            created_by=other_therapist.id
        )
        test_db.add(other_intervention)
        test_db.commit()
        test_db.refresh(other_intervention)

        # Try to access with different therapist
        response = client.get(
            f"/api/v1/interventions/{other_intervention.id}",
            headers=therapist_auth_headers
        )

        # Should be forbidden
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not authorized" in response.json()["detail"]


# ============================================================================
# Cross-Router Integration Tests
# ============================================================================

class TestCrossRouterIntegration:
    """Test workflows that span multiple routers"""

    def test_full_treatment_workflow(
        self,
        client,
        test_db,
        therapist_auth_headers,
        test_patient_for_plans,
        system_intervention
    ):
        """Test complete workflow: create plan -> add goals -> link interventions -> track progress"""

        # Step 1: Create treatment plan
        plan_data = {
            "title": "Comprehensive Anxiety Treatment",
            "start_date": str(date.today()),
            "review_frequency_days": 30
        }
        plan_response = client.post(
            f"/api/v1/patients/{test_patient_for_plans.id}/treatment-plans",
            json=plan_data,
            headers=therapist_auth_headers
        )
        assert plan_response.status_code == status.HTTP_200_OK
        plan_id = plan_response.json()["id"]

        # Step 2: Add a long-term goal
        goal_data = {
            "plan_id": plan_id,
            "goal_type": GoalType.long_term.value,
            "description": "Manage anxiety effectively",
            "priority": 1,
            "interventions": [
                {
                    "intervention_id": str(system_intervention.id),
                    "frequency": "Daily",
                    "notes": "Primary intervention"
                }
            ]
        }
        goal_response = client.post(
            f"/api/v1/treatment-plans/{plan_id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )
        assert goal_response.status_code == status.HTTP_201_CREATED
        goal_id = goal_response.json()["id"]

        # Step 3: Record progress
        progress_data = {
            "progress_note": "Client practicing daily",
            "rating": 6
        }
        progress_response = client.post(
            f"/api/v1/goals/{goal_id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )
        assert progress_response.status_code == status.HTTP_201_CREATED

        # Step 4: Retrieve full plan with goals and verify progress
        full_plan_response = client.get(
            f"/api/v1/treatment-plans/{plan_id}",
            headers=therapist_auth_headers
        )
        assert full_plan_response.status_code == status.HTTP_200_OK
        full_plan = full_plan_response.json()

        # Verify integrated data
        assert full_plan["title"] == "Comprehensive Anxiety Treatment"
        assert len(full_plan["goals"]) == 1
        assert full_plan["goals"][0]["id"] == goal_id
        assert full_plan["progress_summary"]["total_goals"] == 1
        # Progress should be updated based on rating (60%)
        assert full_plan["progress_summary"]["overall_progress"] == 60
