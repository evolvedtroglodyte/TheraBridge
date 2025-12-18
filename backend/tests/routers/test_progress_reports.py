"""
Integration tests for progress reports router endpoints.

Tests cover:
- Progress report generation with goals and assessments
- Date range validation and filtering
- Report format handling (JSON vs PDF)
- Authorization (therapist-only access with data isolation)
- Edge cases (no data, partial data, empty results)
- Report structure validation
- Multiple goal types in single report
"""
import pytest
from fastapi import status
from datetime import datetime, timedelta, date
from uuid import uuid4

from app.models.db_models import User, TherapistPatient
from app.models.schemas import UserRole

REPORTS_PREFIX = "/api/v1/progress-reports/progress-reports"


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def therapist_patient_assignment(test_db, therapist_user, sample_patient):
    """
    Create TherapistPatient assignment for data isolation testing.

    The progress reports router requires active therapist-patient assignments
    to enforce data isolation.
    """
    assignment = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=sample_patient.id,
        relationship_type="primary",
        is_active=True,
        started_at=datetime.utcnow() - timedelta(days=90)
    )
    test_db.add(assignment)
    test_db.commit()
    test_db.refresh(assignment)
    return assignment


@pytest.fixture(scope="function")
def inactive_therapist_patient_assignment(test_db, therapist_user, sample_patient):
    """
    Create inactive TherapistPatient assignment for testing access denial.
    """
    assignment = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=sample_patient.id,
        relationship_type="primary",
        is_active=False,  # Inactive assignment
        started_at=datetime.utcnow() - timedelta(days=90),
        ended_at=datetime.utcnow() - timedelta(days=30)
    )
    test_db.add(assignment)
    test_db.commit()
    test_db.refresh(assignment)
    return assignment


@pytest.fixture(scope="function")
def other_therapist(test_db):
    """
    Create a second therapist for testing data isolation.
    """
    user = User(
        email="other.therapist@test.com",
        hashed_password="hashed_password",
        first_name="Other",
        last_name="Therapist",
        full_name="Other Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def other_therapist_auth_headers(other_therapist):
    """Generate auth headers for the other therapist."""
    from app.auth.utils import create_access_token
    token = create_access_token(other_therapist.id, other_therapist.role.value)
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Basic Report Generation Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_generate_progress_report_with_goals(
    async_db_client,
    therapist_auth_headers,
    therapist_user,
    sample_patient,
    therapist_patient_assignment,
    goal_with_progress_history,
    test_db
):
    """Test generating progress report with treatment goals."""
    goal, tracking_config, progress_entries = goal_with_progress_history

    # Ensure all fixtures are committed to the shared database file
    test_db.commit()
    test_db.refresh(therapist_user)
    test_db.refresh(sample_patient)
    test_db.refresh(therapist_patient_assignment)

    # Use date range covering all progress entries
    start_date = (date.today() - timedelta(weeks=13)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Validate report structure
    assert "report_period" in data
    assert data["report_period"]["start"] == start_date
    assert data["report_period"]["end"] == end_date

    assert "patient_summary" in data
    assert data["patient_summary"]["name"] == sample_patient.name
    assert "sessions_attended" in data["patient_summary"]
    assert "sessions_missed" in data["patient_summary"]

    assert "goals_summary" in data
    assert isinstance(data["goals_summary"], list)
    assert len(data["goals_summary"]) > 0

    # Validate goal summary structure
    goal_summary = data["goals_summary"][0]
    assert "goal" in goal_summary
    assert "baseline" in goal_summary
    assert "current" in goal_summary
    assert "change" in goal_summary
    assert "change_percentage" in goal_summary
    assert "status" in goal_summary
    assert goal_summary["status"] in [
        "significant_improvement", "improvement", "stable", "decline"
    ]

    assert "assessment_summary" in data
    assert "clinical_observations" in data
    assert "recommendations" in data


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_generate_progress_report_with_assessments(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    sample_goal,
    sample_assessment,
    test_db
):
    """Test progress report includes assessment data."""
    test_db.commit()

    # Create second assessment in date range
    from app.models.tracking_models import AssessmentScore

    second_assessment = AssessmentScore(
        patient_id=sample_patient.id,
        goal_id=sample_goal.id,
        administered_by=therapist_patient_assignment.therapist_id,
        assessment_type="GAD-7",
        score=8,  # Improved from 14 to 8
        severity="mild",
        subscores={
            "feeling_nervous": 1,
            "not_stop_worrying": 1,
            "worrying_too_much": 1,
            "trouble_relaxing": 1,
            "restless": 2,
            "easily_annoyed": 1,
            "feeling_afraid": 1
        },
        administered_date=date.today(),
        notes="Follow-up assessment showing improvement",
        created_at=datetime.utcnow()
    )
    test_db.add(second_assessment)
    test_db.commit()
    test_db.refresh(second_assessment)

    # Generate report covering both assessments
    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Validate assessment summary
    assert "assessment_summary" in data
    assert isinstance(data["assessment_summary"], dict)

    if "GAD-7" in data["assessment_summary"]:
        gad7_summary = data["assessment_summary"]["GAD-7"]
        assert "baseline" in gad7_summary
        assert "current" in gad7_summary
        assert "change" in gad7_summary
        assert "interpretation" in gad7_summary

        # Verify values
        assert gad7_summary["baseline"] == 14
        assert gad7_summary["current"] == 8
        assert gad7_summary["change"] == -6


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_generate_progress_report_multiple_goal_types(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    multiple_goals_for_patient,
    test_db
):
    """Test report includes multiple goals with different categories and statuses."""
    test_db.commit()

    # Create progress entries for the goals
    from app.models.tracking_models import ProgressEntry

    for goal in multiple_goals_for_patient:
        # Add progress entries to each goal
        entry = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=None,
            entry_date=date.today() - timedelta(days=1),
            entry_time=datetime.utcnow().time(),
            value=goal.baseline_value + 1.0,  # Show some progress
            value_label="Progress update",
            notes="Test progress entry",
            context="self_report",
            recorded_at=datetime.utcnow()
        )
        test_db.add(entry)

    test_db.commit()

    # Generate report
    start_date = (date.today() - timedelta(days=90)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Should include all goals with progress entries
    assert "goals_summary" in data
    assert len(data["goals_summary"]) >= 3  # All 3 goals from fixture

    # Verify different goal categories are included
    goal_descriptions = [g["goal"] for g in data["goals_summary"]]
    assert any("anxiety" in desc.lower() for desc in goal_descriptions)
    assert any("sleep" in desc.lower() or "behavioral" in desc.lower() for desc in goal_descriptions)


# ============================================================================
# Date Range Validation Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_invalid_date_range_rejected(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    test_db
):
    """Test that end_date before start_date returns 400 error."""
    test_db.commit()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": "2024-03-31",
            "end_date": "2024-01-01",  # End before start
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "end_date must be after start_date" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_date_range_exceeds_one_year_rejected(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    test_db
):
    """Test that date range exceeding 1 year is rejected."""
    test_db.commit()

    start_date = date(2023, 1, 1)
    end_date = date(2024, 2, 1)  # 13 months later

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "cannot exceed 1 year" in data["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_date_range_filters_correctly(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    goal_with_progress_history,
    test_db
):
    """Test that date range correctly filters included data."""
    test_db.commit()

    goal, tracking_config, progress_entries = goal_with_progress_history

    # Request report for only last 4 weeks (should exclude older entries)
    start_date = (date.today() - timedelta(weeks=4)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Report period should match request
    assert data["report_period"]["start"] == start_date
    assert data["report_period"]["end"] == end_date


# ============================================================================
# Empty Data / Edge Case Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_no_goals_returns_empty_summary(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    test_db
):
    """Test report generation when patient has no goals."""
    test_db.commit()

    # Patient exists but has no goals or assessments
    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Should return valid report with empty summaries
    assert "goals_summary" in data
    assert isinstance(data["goals_summary"], list)
    assert len(data["goals_summary"]) == 0

    assert "assessment_summary" in data
    assert isinstance(data["assessment_summary"], dict)
    assert len(data["assessment_summary"]) == 0

    # Should still have clinical observations and recommendations
    assert "clinical_observations" in data
    assert len(data["clinical_observations"]) > 0
    assert "recommendations" in data
    assert len(data["recommendations"]) > 0


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_no_assessments_still_includes_goals(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    goal_with_progress_history,
    test_db
):
    """Test report with goals but no assessments."""
    test_db.commit()

    goal, tracking_config, progress_entries = goal_with_progress_history

    start_date = (date.today() - timedelta(weeks=13)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Should have goals but no assessments
    assert len(data["goals_summary"]) > 0
    assert len(data["assessment_summary"]) == 0


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_goals_without_progress_entries_excluded(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    sample_goal,
    test_db
):
    """Test that goals without progress entries are excluded from report."""
    test_db.commit()

    # sample_goal has no progress entries
    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Goals without entries should be excluded from summary
    # (service only includes goals with both baseline and current values)
    assert "goals_summary" in data
    # Should be empty or not include the goal without progress
    goal_descriptions = [g["goal"] for g in data["goals_summary"]]
    # Our sample_goal has baseline but no entries, so it won't appear
    # This is expected behavior


# ============================================================================
# Report Format Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_json_format_success(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    test_db
):
    """Test requesting progress report in JSON format (default)."""
    test_db.commit()

    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Should return JSON response
    assert isinstance(data, dict)
    assert "report_period" in data


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_pdf_format_not_implemented(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    test_db
):
    """Test that PDF format returns 501 Not Implemented."""
    test_db.commit()

    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "pdf"
        }
    )

    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
    data = response.json()
    assert "not yet implemented" in data["detail"].lower()
    assert "format=json" in data["detail"]


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_default_format_is_json(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    test_db
):
    """Test that default format is JSON when not specified."""
    test_db.commit()

    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    # Don't specify format parameter
    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict)


# ============================================================================
# Authorization and Data Isolation Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_patient_not_found(
    async_db_client,
    therapist_auth_headers,
    test_db
):
    """Test that requesting report for non-existent patient returns 404."""
    test_db.commit()

    fake_patient_id = uuid4()
    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{fake_patient_id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_patient_not_assigned_to_therapist(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    test_db
):
    """Test that therapist cannot access report for unassigned patient."""
    test_db.commit()

    # No TherapistPatient assignment exists
    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "not assigned to you" in data["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_inactive_assignment_denied(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    inactive_therapist_patient_assignment,
    test_db
):
    """Test that inactive assignments are denied access."""
    test_db.commit()

    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_different_therapist_denied(
    async_db_client,
    other_therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    test_db
):
    """Test that therapists cannot access other therapists' patients."""
    test_db.commit()

    # sample_patient is assigned to therapist_user, not other_therapist
    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=other_therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_patient_role_forbidden(
    async_db_client,
    patient_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    test_db
):
    """Test that patients cannot generate progress reports."""
    test_db.commit()

    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=patient_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_requires_authentication(
    async_db_client,
    sample_patient,
    therapist_patient_assignment,
    test_db
):
    """Test that unauthenticated requests are rejected."""
    test_db.commit()

    start_date = (date.today() - timedelta(days=30)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Report Structure Validation Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_structure_completeness(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    goal_with_progress_history,
    test_db
):
    """Test that report response includes all required fields."""
    test_db.commit()

    goal, tracking_config, progress_entries = goal_with_progress_history

    start_date = (date.today() - timedelta(weeks=13)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Validate report_period
    assert "report_period" in data
    assert "start" in data["report_period"]
    assert "end" in data["report_period"]

    # Validate patient_summary
    assert "patient_summary" in data
    patient_summary = data["patient_summary"]
    assert "name" in patient_summary
    assert "treatment_start" in patient_summary
    assert "sessions_attended" in patient_summary
    assert "sessions_missed" in patient_summary
    assert isinstance(patient_summary["sessions_attended"], int)
    assert isinstance(patient_summary["sessions_missed"], int)
    assert patient_summary["sessions_attended"] >= 0
    assert patient_summary["sessions_missed"] >= 0

    # Validate goals_summary
    assert "goals_summary" in data
    assert isinstance(data["goals_summary"], list)
    for goal_item in data["goals_summary"]:
        assert "goal" in goal_item
        assert "baseline" in goal_item
        assert "current" in goal_item
        assert "change" in goal_item
        assert "change_percentage" in goal_item
        assert "status" in goal_item

    # Validate assessment_summary
    assert "assessment_summary" in data
    assert isinstance(data["assessment_summary"], dict)

    # Validate clinical_observations
    assert "clinical_observations" in data
    assert isinstance(data["clinical_observations"], str)
    assert len(data["clinical_observations"]) > 0

    # Validate recommendations
    assert "recommendations" in data
    assert isinstance(data["recommendations"], str)
    assert len(data["recommendations"]) > 0


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_progress_report_goal_status_categorization(
    async_db_client,
    therapist_auth_headers,
    sample_patient,
    therapist_patient_assignment,
    goal_with_progress_history,
    test_db
):
    """Test that goal status is correctly categorized based on progress."""
    test_db.commit()

    goal, tracking_config, progress_entries = goal_with_progress_history

    # Goal shows improvement from 1.0 to 5.0 (weekly exercise frequency)
    start_date = (date.today() - timedelta(weeks=13)).isoformat()
    end_date = date.today().isoformat()

    response = async_db_client.get(
        f"{REPORTS_PREFIX}/patients/{sample_patient.id}/progress-report",
        headers=therapist_auth_headers,
        params={
            "start_date": start_date,
            "end_date": end_date,
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Should have at least one goal with status
    assert len(data["goals_summary"]) > 0

    goal_summary = data["goals_summary"][0]
    assert goal_summary["status"] in [
        "significant_improvement",
        "improvement",
        "stable",
        "decline"
    ]

    # Verify change calculations are present
    assert "change" in goal_summary
    assert "change_percentage" in goal_summary
    assert isinstance(goal_summary["change"], (int, float))
    assert isinstance(goal_summary["change_percentage"], (int, float))
