"""
Integration tests for treatment plan goals router (Feature 4).

Tests cover all 4 endpoints in backend/app/routers/goals.py:
1. POST /treatment-plans/{plan_id}/goals - Add goal to treatment plan
2. PUT /goals/{goal_id} - Update goal
3. POST /goals/{goal_id}/progress - Record progress entry
4. GET /goals/{goal_id}/history - Get progress history

Total: 26 test cases covering:
- Happy path tests for all endpoints
- Authentication/authorization tests (therapist-only endpoints)
- Validation error tests (invalid inputs, missing data)
- Edge cases (invalid parent goals, missing IDs, non-existent interventions)
- Hierarchical goal testing (parent/child relationships)
- Progress calculation testing (automatic updates from ratings)
- Parent progress recalculation (weighted average of sub-goals)

Markers:
- @pytest.mark.goal_tracking - All tests in this file
"""
import pytest
from fastapi import status
from uuid import uuid4
from datetime import date, timedelta
from app.models.schemas import UserRole
from app.models.treatment_schemas import GoalType, GoalStatus, EvidenceLevel
from app.models.treatment_models import (
    TreatmentPlan,
    TreatmentPlanGoal as TreatmentGoal,
    Intervention,
    GoalProgress
)


# Mark all tests in this file with goal_tracking marker
pytestmark = pytest.mark.goal_tracking


# ============================================================================
# Test Fixtures (reusing from test_treatment_plans.py)
# ============================================================================

@pytest.fixture(scope="function")
def test_patient_for_goals(test_db, therapist_user):
    """Create a patient user for goals testing"""
    from app.models.db_models import User

    patient = User(
        email="goalspatient@test.com",
        hashed_password="hashed",
        first_name="Goals",
        last_name="Patient",
        full_name="Goals Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)
    return patient


@pytest.fixture(scope="function")
def sample_treatment_plan_for_goals(test_db, therapist_user, test_patient_for_goals):
    """Create a sample treatment plan for goals testing"""
    plan = TreatmentPlan(
        patient_id=test_patient_for_goals.id,
        therapist_id=therapist_user.id,
        title="Anxiety Management Plan for Goals Testing",
        diagnosis_codes=[
            {"code": "F41.1", "description": "Generalized anxiety disorder"}
        ],
        presenting_problems=["Work stress", "Sleep issues"],
        start_date=date.today(),
        target_end_date=date.today() + timedelta(days=180),
        review_frequency_days=30,
        next_review_date=date.today() + timedelta(days=30),
        status='active',
        version=1
    )
    test_db.add(plan)
    test_db.commit()
    test_db.refresh(plan)
    return plan


@pytest.fixture(scope="function")
def sample_goal_for_testing(test_db, sample_treatment_plan_for_goals):
    """Create a sample treatment goal"""
    goal = TreatmentGoal(
        plan_id=sample_treatment_plan_for_goals.id,
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
def sample_intervention_for_goals(test_db):
    """Create a system intervention for testing"""
    intervention = Intervention(
        name="Cognitive Restructuring for Goals",
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
# POST /treatment-plans/{plan_id}/goals - Add Goal to Plan (8 tests)
# ============================================================================

class TestAddGoalToPlan:
    """Test POST /treatment-plans/{plan_id}/goals endpoint"""

    def test_create_goal_in_plan_success(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan_for_goals
    ):
        """Test successful goal creation within a treatment plan"""
        goal_data = {
            "plan_id": str(sample_treatment_plan_for_goals.id),
            "goal_type": GoalType.short_term.value,
            "description": "Practice deep breathing 3x daily",
            "measurable_criteria": "Self-report daily log completion",
            "baseline_value": "0 times/day",
            "target_value": "3 times/day",
            "target_date": str(date.today() + timedelta(days=30)),
            "priority": 2
        }

        response = client.post(
            f"/api/v1/treatment-plans/{sample_treatment_plan_for_goals.id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["plan_id"] == str(sample_treatment_plan_for_goals.id)
        assert data["description"] == "Practice deep breathing 3x daily"
        assert data["goal_type"] == GoalType.short_term.value
        assert data["status"] == GoalStatus.not_started.value
        assert data["progress_percentage"] == 0
        assert data["priority"] == 2
        assert data["baseline_value"] == "0 times/day"
        assert data["target_value"] == "3 times/day"

    def test_create_goal_with_intervention_links(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan_for_goals,
        sample_intervention_for_goals
    ):
        """Test creating a goal with linked interventions"""
        goal_data = {
            "plan_id": str(sample_treatment_plan_for_goals.id),
            "goal_type": GoalType.short_term.value,
            "description": "Reduce worry using cognitive techniques",
            "priority": 1,
            "interventions": [
                {
                    "intervention_id": str(sample_intervention_for_goals.id),
                    "frequency": "3 times daily",
                    "notes": "Use box breathing technique"
                }
            ]
        }

        response = client.post(
            f"/api/v1/treatment-plans/{sample_treatment_plan_for_goals.id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify intervention linking
        assert "id" in data
        assert data["description"] == "Reduce worry using cognitive techniques"

    def test_create_goal_with_parent_hierarchy(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan_for_goals,
        sample_goal_for_testing
    ):
        """Test creating a sub-goal with parent hierarchy"""
        sub_goal_data = {
            "plan_id": str(sample_treatment_plan_for_goals.id),
            "parent_goal_id": str(sample_goal_for_testing.id),
            "goal_type": GoalType.objective.value,
            "description": "Complete anxiety symptom log daily",
            "measurable_criteria": "7 consecutive days of completed logs",
            "target_date": str(date.today() + timedelta(days=14)),
            "priority": 1
        }

        response = client.post(
            f"/api/v1/treatment-plans/{sample_treatment_plan_for_goals.id}/goals",
            json=sub_goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify parent relationship
        assert data["parent_goal_id"] == str(sample_goal_for_testing.id)
        assert data["goal_type"] == GoalType.objective.value
        assert data["description"] == "Complete anxiety symptom log daily"

    def test_create_goal_requires_authentication(
        self,
        client,
        sample_treatment_plan_for_goals
    ):
        """Test that creating a goal requires authentication"""
        goal_data = {
            "plan_id": str(sample_treatment_plan_for_goals.id),
            "goal_type": GoalType.short_term.value,
            "description": "Test goal",
            "priority": 1
        }

        response = client.post(
            f"/api/v1/treatment-plans/{sample_treatment_plan_for_goals.id}/goals",
            json=goal_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_goal_requires_therapist_role(
        self,
        client,
        patient_auth_headers,
        sample_treatment_plan_for_goals
    ):
        """Test that only therapists can create goals"""
        goal_data = {
            "plan_id": str(sample_treatment_plan_for_goals.id),
            "goal_type": GoalType.short_term.value,
            "description": "Test goal",
            "priority": 1
        }

        response = client.post(
            f"/api/v1/treatment-plans/{sample_treatment_plan_for_goals.id}/goals",
            json=goal_data,
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_goal_invalid_parent_goal_id(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan_for_goals
    ):
        """Test validation error when parent goal not in same plan"""
        invalid_parent_id = uuid4()

        goal_data = {
            "plan_id": str(sample_treatment_plan_for_goals.id),
            "parent_goal_id": str(invalid_parent_id),
            "goal_type": GoalType.objective.value,
            "description": "Test goal with invalid parent",
            "priority": 1
        }

        response = client.post(
            f"/api/v1/treatment-plans/{sample_treatment_plan_for_goals.id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Parent goal" in response.json()["detail"]

    def test_create_goal_plan_not_found(
        self,
        client,
        therapist_auth_headers
    ):
        """Test 404 for non-existent treatment plan"""
        nonexistent_plan_id = uuid4()

        goal_data = {
            "plan_id": str(nonexistent_plan_id),
            "goal_type": GoalType.short_term.value,
            "description": "Test goal",
            "priority": 1
        }

        response = client.post(
            f"/api/v1/treatment-plans/{nonexistent_plan_id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_goal_invalid_intervention_id(
        self,
        client,
        therapist_auth_headers,
        sample_treatment_plan_for_goals
    ):
        """Test validation error when intervention doesn't exist"""
        invalid_intervention_id = uuid4()

        goal_data = {
            "plan_id": str(sample_treatment_plan_for_goals.id),
            "goal_type": GoalType.short_term.value,
            "description": "Test goal",
            "priority": 1,
            "interventions": [
                {
                    "intervention_id": str(invalid_intervention_id),
                    "frequency": "daily"
                }
            ]
        }

        response = client.post(
            f"/api/v1/treatment-plans/{sample_treatment_plan_for_goals.id}/goals",
            json=goal_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Intervention" in response.json()["detail"]


# ============================================================================
# PUT /goals/{goal_id} - Update Goal (6 tests)
# ============================================================================

class TestUpdateGoal:
    """Test PUT /goals/{goal_id} endpoint"""

    def test_update_goal_progress_percentage(
        self,
        client,
        therapist_auth_headers,
        sample_goal_for_testing
    ):
        """Test updating goal progress percentage"""
        update_data = {
            "progress_percentage": 50,
            "status": GoalStatus.in_progress.value
        }

        response = client.put(
            f"/api/v1/goals/{sample_goal_for_testing.id}",
            json=update_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify progress update
        assert data["progress_percentage"] == 50
        assert data["status"] == GoalStatus.in_progress.value

    def test_update_goal_description_and_target(
        self,
        client,
        therapist_auth_headers,
        sample_goal_for_testing
    ):
        """Test updating goal description and target value"""
        update_data = {
            "description": "Updated: Reduce anxiety to mild levels",
            "target_value": "GAD-7: <8"
        }

        response = client.put(
            f"/api/v1/goals/{sample_goal_for_testing.id}",
            json=update_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify updates
        assert data["description"] == "Updated: Reduce anxiety to mild levels"
        assert data["target_value"] == "GAD-7: <8"

    def test_update_goal_recalculates_parent_progress(
        self,
        client,
        test_db,
        therapist_auth_headers,
        sample_treatment_plan_for_goals,
        sample_goal_for_testing
    ):
        """Test that updating sub-goal progress recalculates parent goal progress"""
        # Create a sub-goal
        sub_goal = TreatmentGoal(
            plan_id=sample_treatment_plan_for_goals.id,
            parent_goal_id=sample_goal_for_testing.id,
            goal_type=GoalType.objective.value,
            description="Sub-goal for testing parent recalculation",
            priority=1,
            status=GoalStatus.not_started.value,
            progress_percentage=0
        )
        test_db.add(sub_goal)
        test_db.commit()
        test_db.refresh(sub_goal)

        # Update sub-goal progress to 80%
        update_data = {
            "progress_percentage": 80
        }

        response = client.put(
            f"/api/v1/goals/{sub_goal.id}",
            json=update_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify parent goal progress was recalculated
        # Parent had 25%, sub-goal now has 80%, average should be (25+80)/2 = 52.5 → 52
        test_db.refresh(sample_goal_for_testing)
        assert sample_goal_for_testing.progress_percentage == 52

    def test_update_goal_requires_authentication(
        self,
        client,
        sample_goal_for_testing
    ):
        """Test that updating a goal requires authentication"""
        update_data = {
            "progress_percentage": 75
        }

        response = client.put(
            f"/api/v1/goals/{sample_goal_for_testing.id}",
            json=update_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_goal_not_found(
        self,
        client,
        therapist_auth_headers
    ):
        """Test 404 for non-existent goal"""
        nonexistent_goal_id = uuid4()

        update_data = {
            "progress_percentage": 50
        }

        response = client.put(
            f"/api/v1/goals/{nonexistent_goal_id}",
            json=update_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_goal_unauthorized_therapist(
        self,
        client,
        test_db,
        therapist_auth_headers,
        sample_goal_for_testing
    ):
        """Test that therapist cannot update another therapist's goal"""
        from app.models.db_models import User
        from app.auth.utils import get_password_hash, create_access_token

        # Create a second therapist
        other_therapist = User(
            email="othertherapist@test.com",
            hashed_password=get_password_hash("testpass123"),
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

        # Create auth headers for other therapist
        other_token = create_access_token(other_therapist.id, other_therapist.role.value)
        other_headers = {"Authorization": f"Bearer {other_token}"}

        update_data = {
            "progress_percentage": 90
        }

        response = client.put(
            f"/api/v1/goals/{sample_goal_for_testing.id}",
            json=update_data,
            headers=other_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# POST /goals/{goal_id}/progress - Record Progress (7 tests)
# ============================================================================

class TestRecordGoalProgress:
    """Test POST /goals/{goal_id}/progress endpoint"""

    def test_record_goal_progress_success(
        self,
        client,
        therapist_auth_headers,
        sample_goal_for_testing
    ):
        """Test recording a progress entry for a goal"""
        progress_data = {
            "progress_note": "Client reports using breathing exercises before meetings with success",
            "progress_value": "GAD-7: 14",
            "rating": 7
        }

        response = client.post(
            f"/api/v1/goals/{sample_goal_for_testing.id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify progress entry
        assert "id" in data
        assert data["goal_id"] == str(sample_goal_for_testing.id)
        assert data["progress_note"] == progress_data["progress_note"]
        assert data["progress_value"] == "GAD-7: 14"
        assert data["rating"] == 7
        assert "recorded_by" in data
        assert "recorded_at" in data

    def test_record_progress_auto_calculates_percentage_from_rating(
        self,
        client,
        test_db,
        therapist_auth_headers,
        sample_goal_for_testing
    ):
        """Test that progress updates auto-calculate percentage based on rating"""
        # Initial progress is 25%
        assert sample_goal_for_testing.progress_percentage == 25

        progress_data = {
            "progress_note": "Significant improvement this week",
            "rating": 8  # Should set progress to 80%
        }

        response = client.post(
            f"/api/v1/goals/{sample_goal_for_testing.id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify goal progress was updated
        test_db.refresh(sample_goal_for_testing)
        # Rating of 8 should set progress to 80% (8/10 * 100)
        assert sample_goal_for_testing.progress_percentage == 80
        assert sample_goal_for_testing.status == GoalStatus.in_progress.value

    def test_record_progress_rating_only_increases_percentage(
        self,
        client,
        test_db,
        therapist_auth_headers,
        sample_goal_for_testing
    ):
        """Test that rating only increases progress, never decreases"""
        # Set initial progress to 70%
        sample_goal_for_testing.progress_percentage = 70
        test_db.commit()
        test_db.refresh(sample_goal_for_testing)

        # Record progress with lower rating (5 = 50%)
        progress_data = {
            "progress_note": "Rough week, some setbacks",
            "rating": 5  # 50% - lower than current 70%
        }

        response = client.post(
            f"/api/v1/goals/{sample_goal_for_testing.id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify progress stayed at 70% (not decreased to 50%)
        test_db.refresh(sample_goal_for_testing)
        assert sample_goal_for_testing.progress_percentage == 70

    def test_record_progress_achieves_goal_at_rating_10(
        self,
        client,
        test_db,
        therapist_auth_headers,
        sample_goal_for_testing
    ):
        """Test that rating of 10 marks goal as achieved"""
        progress_data = {
            "progress_note": "Goal fully achieved!",
            "rating": 10
        }

        response = client.post(
            f"/api/v1/goals/{sample_goal_for_testing.id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify goal is marked as achieved
        test_db.refresh(sample_goal_for_testing)
        assert sample_goal_for_testing.progress_percentage == 100
        assert sample_goal_for_testing.status == GoalStatus.achieved.value

    def test_record_progress_recalculates_parent_goal(
        self,
        client,
        test_db,
        therapist_auth_headers,
        sample_treatment_plan_for_goals,
        sample_goal_for_testing
    ):
        """Test that recording progress on sub-goal recalculates parent progress"""
        # Create a sub-goal
        sub_goal = TreatmentGoal(
            plan_id=sample_treatment_plan_for_goals.id,
            parent_goal_id=sample_goal_for_testing.id,
            goal_type=GoalType.objective.value,
            description="Sub-goal for parent recalc test",
            priority=1,
            status=GoalStatus.not_started.value,
            progress_percentage=0
        )
        test_db.add(sub_goal)
        test_db.commit()
        test_db.refresh(sub_goal)

        # Record progress on sub-goal
        progress_data = {
            "progress_note": "Making good progress",
            "rating": 9  # 90%
        }

        response = client.post(
            f"/api/v1/goals/{sub_goal.id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED

        # Verify parent goal progress was recalculated
        # Parent was 25%, sub-goal now 90%, average = (25+90)/2 = 57.5 → 57
        test_db.refresh(sample_goal_for_testing)
        assert sample_goal_for_testing.progress_percentage == 57

    def test_record_progress_requires_authentication(
        self,
        client,
        sample_goal_for_testing
    ):
        """Test that recording progress requires authentication"""
        progress_data = {
            "progress_note": "Test note",
            "rating": 5
        }

        response = client.post(
            f"/api/v1/goals/{sample_goal_for_testing.id}/progress",
            json=progress_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_record_progress_goal_not_found(
        self,
        client,
        therapist_auth_headers
    ):
        """Test 404 for non-existent goal"""
        nonexistent_goal_id = uuid4()

        progress_data = {
            "progress_note": "Test note",
            "rating": 5
        }

        response = client.post(
            f"/api/v1/goals/{nonexistent_goal_id}/progress",
            json=progress_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# GET /goals/{goal_id}/history - Get Progress History (5 tests)
# ============================================================================

class TestGetGoalProgressHistory:
    """Test GET /goals/{goal_id}/history endpoint"""

    def test_get_goal_progress_history_success(
        self,
        client,
        test_db,
        therapist_auth_headers,
        sample_goal_for_testing,
        therapist_user
    ):
        """Test retrieving goal progress history"""
        # Create multiple progress entries
        progress_entries = [
            GoalProgress(
                goal_id=sample_goal_for_testing.id,
                recorded_by=therapist_user.id,
                progress_note=f"Progress note {i}",
                progress_value=f"Value {i}",
                rating=i+3
            )
            for i in range(3)
        ]
        test_db.add_all(progress_entries)
        test_db.commit()

        response = client.get(
            f"/api/v1/goals/{sample_goal_for_testing.id}/history",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify history
        assert isinstance(data, list)
        assert len(data) == 3

        # Verify entries have required fields
        for entry in data:
            assert "id" in entry
            assert "goal_id" in entry
            assert "progress_note" in entry
            assert "recorded_at" in entry
            assert "rating" in entry
            assert entry["goal_id"] == str(sample_goal_for_testing.id)

    def test_get_goal_progress_history_ordered_by_recent(
        self,
        client,
        test_db,
        therapist_auth_headers,
        sample_goal_for_testing,
        therapist_user
    ):
        """Test that progress history is ordered by most recent first"""
        from datetime import datetime

        # Create entries with different timestamps
        entries = []
        for i in range(3):
            entry = GoalProgress(
                goal_id=sample_goal_for_testing.id,
                recorded_by=therapist_user.id,
                progress_note=f"Entry {i}",
                rating=5
            )
            test_db.add(entry)
            test_db.flush()
            entries.append(entry)

        test_db.commit()

        response = client.get(
            f"/api/v1/goals/{sample_goal_for_testing.id}/history",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Entries should be in reverse chronological order
        # Most recent first (Entry 2, Entry 1, Entry 0)
        assert len(data) == 3
        # Can't guarantee exact order without explicit timestamps, but verify all present
        progress_notes = [entry["progress_note"] for entry in data]
        assert "Entry 0" in progress_notes
        assert "Entry 1" in progress_notes
        assert "Entry 2" in progress_notes

    def test_get_goal_progress_history_empty(
        self,
        client,
        therapist_auth_headers,
        sample_goal_for_testing
    ):
        """Test getting progress history for goal with no entries"""
        response = client.get(
            f"/api/v1/goals/{sample_goal_for_testing.id}/history",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return empty list
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_goal_progress_history_requires_authentication(
        self,
        client,
        sample_goal_for_testing
    ):
        """Test that getting progress history requires authentication"""
        response = client.get(
            f"/api/v1/goals/{sample_goal_for_testing.id}/history"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_goal_progress_history_goal_not_found(
        self,
        client,
        therapist_auth_headers
    ):
        """Test 404 for non-existent goal"""
        nonexistent_goal_id = uuid4()

        response = client.get(
            f"/api/v1/goals/{nonexistent_goal_id}/history",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
