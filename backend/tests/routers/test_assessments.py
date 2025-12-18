"""
Comprehensive integration tests for assessments router (Feature 6).

Tests standardized clinical assessment endpoints including:
- POST /patients/{patient_id}/assessments - Record new assessment
- GET /patients/{patient_id}/assessments - Get assessment history
- GET /patients/{patient_id}/assessments/due - Check assessments due

Coverage includes:
- All assessment types (PHQ-9, GAD-7, BDI-II, BAI, PCL-5, AUDIT)
- Severity classification validation
- Score calculation and validation
- History filtering (by type, date range)
- Subscores JSONB field
- Authorization (therapist/patient access)
- Invalid score rejection
"""

import pytest
from datetime import date, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient

from app.models.db_models import User, TherapistPatient, Patient
from app.models.schemas import UserRole
from tests.utils.test_helpers import create_test_assessment_score, generate_assessment_series

# Ensure all tables are registered
import app.models


# ============================================================================
# Fixtures
# ============================================================================

# Note: Using patient_user from conftest.py which is already configured

def create_therapist_patient_relationship(test_db, therapist_user, patient_user):
    """Helper to create therapist-patient relationship for testing assessments"""
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()
    return relationship


# ============================================================================
# POST /patients/{patient_id}/assessments - Create Assessment Tests
# ============================================================================

@pytest.mark.goal_tracking
def test_create_assessment_phq9_success(async_db_client, test_db, patient_user, therapist_user, therapist_auth_headers):
    """Test creating a PHQ-9 assessment with valid data"""
    # Create therapist-patient relationship
    create_therapist_patient_relationship(test_db, therapist_user, patient_user)
    test_db.commit()  # Ensure fixture data is visible to async session

    assessment_data = {
        "assessment_type": "PHQ-9",
        "score": 12,
        "administered_date": str(date.today()),
        "notes": "Patient reports improved mood",
        "subscores": {
            "little_interest": 2,
            "feeling_down": 2,
            "sleep_problems": 1,
            "tired": 2,
            "appetite": 1,
            "feeling_bad": 1,
            "concentration": 2,
            "moving_slowly": 1,
            "suicidal_thoughts": 0
        }
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert data["assessment_type"] == "PHQ-9"
    assert data["score"] == 12
    assert data["severity"] == "moderate"  # Auto-calculated
    assert data["patient_id"] == str(patient_with_therapist.id)
    assert data["subscores"] == assessment_data["subscores"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.goal_tracking
def test_create_assessment_gad7_success(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test creating a GAD-7 assessment"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "GAD-7",
        "score": 8,
        "administered_date": str(date.today()),
        "subscores": {
            "feeling_nervous": 2,
            "cant_stop_worrying": 1,
            "worrying_too_much": 2,
            "trouble_relaxing": 1,
            "restless": 1,
            "easily_annoyed": 1,
            "feeling_afraid": 0
        }
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["assessment_type"] == "GAD-7"
    assert data["score"] == 8
    assert data["severity"] == "mild"  # GAD-7: 5-9 is mild
    assert data["subscores"] == assessment_data["subscores"]


@pytest.mark.goal_tracking
def test_create_assessment_bdi2_success(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test creating a BDI-II assessment"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "BDI-II",
        "score": 22,
        "administered_date": str(date.today()),
        "notes": "Baseline depression assessment"
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["assessment_type"] == "BDI-II"
    assert data["score"] == 22
    assert data["severity"] == "moderate"  # BDI-II: 20-28 is moderate


@pytest.mark.goal_tracking
def test_create_assessment_bai_success(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test creating a BAI assessment (no automatic severity)"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "BAI",
        "score": 18,
        "severity": "moderate",  # Must be provided manually
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["assessment_type"] == "BAI"
    assert data["score"] == 18
    assert data["severity"] == "moderate"


@pytest.mark.goal_tracking
def test_create_assessment_pcl5_success(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test creating a PCL-5 assessment"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "PCL-5",
        "score": 45,
        "severity": "severe",
        "administered_date": str(date.today()),
        "notes": "PTSD screening"
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["assessment_type"] == "PCL-5"
    assert data["score"] == 45


@pytest.mark.goal_tracking
def test_create_assessment_audit_success(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test creating an AUDIT assessment"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "AUDIT",
        "score": 6,
        "severity": "minimal",
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["assessment_type"] == "AUDIT"
    assert data["score"] == 6


@pytest.mark.goal_tracking
def test_create_assessment_severity_phq9_minimal(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test PHQ-9 severity classification: minimal (0-4)"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "PHQ-9",
        "score": 3,
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["severity"] == "minimal"


@pytest.mark.goal_tracking
def test_create_assessment_severity_phq9_mild(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test PHQ-9 severity classification: mild (5-9)"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "PHQ-9",
        "score": 7,
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["severity"] == "mild"


@pytest.mark.goal_tracking
def test_create_assessment_severity_phq9_moderate(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test PHQ-9 severity classification: moderate (10-14)"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "PHQ-9",
        "score": 12,
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["severity"] == "moderate"


@pytest.mark.goal_tracking
def test_create_assessment_severity_phq9_moderately_severe(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test PHQ-9 severity classification: moderately_severe (15-19)"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "PHQ-9",
        "score": 17,
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["severity"] == "moderately_severe"


@pytest.mark.goal_tracking
def test_create_assessment_severity_phq9_severe(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test PHQ-9 severity classification: severe (20+)"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "PHQ-9",
        "score": 23,
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["severity"] == "severe"


@pytest.mark.goal_tracking
def test_create_assessment_severity_gad7_severe(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test GAD-7 severity classification: severe (15+)"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "GAD-7",
        "score": 18,
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    assert response.json()["severity"] == "severe"


@pytest.mark.goal_tracking
def test_create_assessment_invalid_negative_score(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test that negative scores are rejected"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "PHQ-9",
        "score": -5,
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.goal_tracking
def test_create_assessment_unauthorized_patient_not_assigned(async_db_client, test_db, unassigned_patient, therapist_auth_headers):
    """Test that therapist cannot create assessment for unassigned patient"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "GAD-7",
        "score": 10,
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{unassigned_patient.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.goal_tracking
def test_create_assessment_patient_cannot_create(async_db_client, test_db, patient_with_therapist, patient_auth_headers):
    """Test that patients cannot create assessments (therapist-only)"""
    test_db.commit()

    assessment_data = {
        "assessment_type": "PHQ-9",
        "score": 8,
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=patient_auth_headers
    )

    # Should fail - only therapists can create assessments
    assert response.status_code == 403


@pytest.mark.goal_tracking
def test_create_assessment_invalid_patient_id(async_db_client, test_db, therapist_auth_headers):
    """Test creating assessment for non-existent patient"""
    test_db.commit()

    fake_patient_id = uuid4()
    assessment_data = {
        "assessment_type": "PHQ-9",
        "score": 10,
        "administered_date": str(date.today())
    }

    response = async_db_client.post(
        f"/api/v1/patients/{fake_patient_id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 403  # No access to non-existent patient


# ============================================================================
# GET /patients/{patient_id}/assessments - Get History Tests
# ============================================================================

@pytest.mark.goal_tracking
def test_get_assessment_history_success(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test retrieving assessment history"""
    # Create multiple assessments
    assessments = generate_assessment_series(
        patient_id=patient_with_therapist.id,
        assessment_type="GAD-7",
        num_assessments=3,
        trend="improving"
    )
    for assessment in assessments:
        test_db.add(assessment)
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/patients/{patient_user.id}/assessments",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "assessments" in data
    assert "GAD-7" in data["assessments"]
    assert len(data["assessments"]["GAD-7"]) == 3

    # Verify chronological order (oldest to newest)
    scores = [item["score"] for item in data["assessments"]["GAD-7"]]
    assert scores == sorted(scores, reverse=True)  # Improving trend = decreasing scores


@pytest.mark.goal_tracking
def test_get_assessment_history_multiple_types(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test retrieving history with multiple assessment types"""
    # Create GAD-7 assessments
    gad7_assessments = generate_assessment_series(
        patient_id=patient_with_therapist.id,
        assessment_type="GAD-7",
        num_assessments=2,
        trend="stable"
    )
    for assessment in gad7_assessments:
        test_db.add(assessment)

    # Create PHQ-9 assessments
    phq9_assessments = generate_assessment_series(
        patient_id=patient_with_therapist.id,
        assessment_type="PHQ-9",
        num_assessments=3,
        trend="improving"
    )
    for assessment in phq9_assessments:
        test_db.add(assessment)

    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/patients/{patient_user.id}/assessments",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "GAD-7" in data["assessments"]
    assert "PHQ-9" in data["assessments"]
    assert len(data["assessments"]["GAD-7"]) == 2
    assert len(data["assessments"]["PHQ-9"]) == 3


@pytest.mark.goal_tracking
def test_get_assessment_history_filter_by_type(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test filtering history by assessment type"""
    # Create multiple types
    gad7 = create_test_assessment_score(
        patient_id=patient_with_therapist.id,
        assessment_type="GAD-7",
        score=10
    )
    phq9 = create_test_assessment_score(
        patient_id=patient_with_therapist.id,
        assessment_type="PHQ-9",
        score=12
    )
    test_db.add(gad7)
    test_db.add(phq9)
    test_db.commit()

    # Filter for GAD-7 only
    response = async_db_client.get(
        f"/api/v1/patients/{patient_with_therapist.id}/assessments?assessment_type=GAD-7",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "GAD-7" in data["assessments"]
    assert "PHQ-9" not in data["assessments"]
    assert len(data["assessments"]["GAD-7"]) == 1


@pytest.mark.goal_tracking
def test_get_assessment_history_filter_by_date_range(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test filtering history by date range"""
    # Create assessments across different dates
    today = date.today()
    assessments = [
        create_test_assessment_score(
            patient_id=patient_with_therapist.id,
            assessment_type="GAD-7",
            score=14,
            administered_date=today - timedelta(days=60)
        ),
        create_test_assessment_score(
            patient_id=patient_with_therapist.id,
            assessment_type="GAD-7",
            score=10,
            administered_date=today - timedelta(days=30)
        ),
        create_test_assessment_score(
            patient_id=patient_with_therapist.id,
            assessment_type="GAD-7",
            score=8,
            administered_date=today - timedelta(days=5)
        ),
    ]
    for assessment in assessments:
        test_db.add(assessment)
    test_db.commit()

    # Filter for last 45 days
    start_date = today - timedelta(days=45)
    end_date = today

    response = async_db_client.get(
        f"/api/v1/patients/{patient_with_therapist.id}/assessments"
        f"?start_date={start_date}&end_date={end_date}",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should only include the 2 recent assessments (30 days and 5 days ago)
    assert len(data["assessments"]["GAD-7"]) == 2


@pytest.mark.goal_tracking
def test_get_assessment_history_patient_own_data(async_db_client, test_db, patient_with_therapist):
    """Test that patient can access their own assessment history"""
    from app.auth.utils import create_access_token

    # Create assessments
    assessment = create_test_assessment_score(
        patient_id=patient_with_therapist.id,
        assessment_type="PHQ-9",
        score=10
    )
    test_db.add(assessment)
    test_db.commit()

    # Generate patient auth token
    patient_token = create_access_token(patient_with_therapist.id, "patient")
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    response = async_db_client.get(
        f"/api/v1/patients/{patient_user.id}/assessments",
        headers=patient_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert "PHQ-9" in data["assessments"]
    assert len(data["assessments"]["PHQ-9"]) == 1


@pytest.mark.goal_tracking
def test_get_assessment_history_patient_cannot_access_other_patient(async_db_client, test_db, patient_with_therapist, patient_user):
    """Test that patient cannot access another patient's history"""
    from app.auth.utils import create_access_token

    # Create assessment for patient_with_therapist
    assessment = create_test_assessment_score(
        patient_id=patient_with_therapist.id,
        assessment_type="GAD-7",
        score=8
    )
    test_db.add(assessment)
    test_db.commit()

    # Try to access with patient_user credentials (different patient)
    patient_token = create_access_token(patient_user.id, "patient")
    patient_headers = {"Authorization": f"Bearer {patient_token}"}

    response = async_db_client.get(
        f"/api/v1/patients/{patient_user.id}/assessments",
        headers=patient_headers
    )

    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.goal_tracking
def test_get_assessment_history_empty(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test retrieving history when no assessments exist"""
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/patients/{patient_user.id}/assessments",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["assessments"] == {}


# ============================================================================
# GET /patients/{patient_id}/assessments/due - Check Due Assessments Tests
# ============================================================================

@pytest.mark.goal_tracking
def test_get_assessments_due_all_due_new_patient(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test that all assessments are due for new patient with no history"""
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/patients/{patient_with_therapist.id}/assessments/due",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should return all assessment types with fixed frequencies (excludes PCL-5)
    assert len(data) == 5  # PHQ-9, GAD-7, BDI-II, BAI, AUDIT

    assessment_types = [item["type"] for item in data]
    assert "PHQ-9" in assessment_types
    assert "GAD-7" in assessment_types
    assert "BDI-II" in assessment_types
    assert "BAI" in assessment_types
    assert "AUDIT" in assessment_types

    # All should have no last_administered date
    for item in data:
        assert item["last_administered"] is None
        assert item["due_date"] == str(date.today())


@pytest.mark.goal_tracking
def test_get_assessments_due_phq9_overdue(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test PHQ-9 is due when last administered 28+ days ago"""
    # Create PHQ-9 assessment 30 days ago
    old_assessment = create_test_assessment_score(
        patient_id=patient_with_therapist.id,
        assessment_type="PHQ-9",
        score=12,
        administered_date=date.today() - timedelta(days=30)
    )
    test_db.add(old_assessment)
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/patients/{patient_with_therapist.id}/assessments/due",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # PHQ-9 should be in due list
    phq9_items = [item for item in data if item["type"] == "PHQ-9"]
    assert len(phq9_items) == 1

    phq9_due = phq9_items[0]
    assert phq9_due["last_administered"] == str(date.today() - timedelta(days=30))
    assert phq9_due["due_date"] == str(date.today() - timedelta(days=2))  # 30 days - 28 day frequency


@pytest.mark.goal_tracking
def test_get_assessments_due_gad7_not_due_yet(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test GAD-7 is NOT due when recently administered"""
    # Create GAD-7 assessment 10 days ago
    recent_assessment = create_test_assessment_score(
        patient_id=patient_with_therapist.id,
        assessment_type="GAD-7",
        score=8,
        administered_date=date.today() - timedelta(days=10)
    )
    test_db.add(recent_assessment)
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/patients/{patient_with_therapist.id}/assessments/due",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # GAD-7 should NOT be in due list (needs 28 days)
    gad7_items = [item for item in data if item["type"] == "GAD-7"]
    assert len(gad7_items) == 0


@pytest.mark.goal_tracking
def test_get_assessments_due_audit_quarterly(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test AUDIT is due after 90 days"""
    # Create AUDIT assessment 95 days ago
    old_audit = create_test_assessment_score(
        patient_id=patient_with_therapist.id,
        assessment_type="AUDIT",
        score=6,
        administered_date=date.today() - timedelta(days=95)
    )
    test_db.add(old_audit)
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/patients/{patient_with_therapist.id}/assessments/due",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # AUDIT should be due
    audit_items = [item for item in data if item["type"] == "AUDIT"]
    assert len(audit_items) == 1


@pytest.mark.goal_tracking
def test_get_assessments_due_mixed_statuses(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test mix of due and not-due assessments"""
    today = date.today()

    # PHQ-9: Due (35 days ago)
    test_db.add(create_test_assessment_score(
        patient_id=patient_with_therapist.id,
        assessment_type="PHQ-9",
        score=10,
        administered_date=today - timedelta(days=35)
    ))

    # GAD-7: Not due yet (15 days ago)
    test_db.add(create_test_assessment_score(
        patient_id=patient_with_therapist.id,
        assessment_type="GAD-7",
        score=8,
        administered_date=today - timedelta(days=15)
    ))

    # BDI-II: Never administered (due immediately)
    # (no entry)

    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/patients/{patient_with_therapist.id}/assessments/due",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    due_types = [item["type"] for item in data]

    # PHQ-9 should be due
    assert "PHQ-9" in due_types

    # GAD-7 should NOT be due
    assert "GAD-7" not in due_types

    # BDI-II should be due (never administered)
    assert "BDI-II" in due_types


@pytest.mark.goal_tracking
def test_get_assessments_due_unauthorized_unassigned_patient(async_db_client, test_db, unassigned_patient, therapist_auth_headers):
    """Test therapist cannot check due assessments for unassigned patient"""
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/patients/{unassigned_patient.id}/assessments/due",
        headers=therapist_auth_headers
    )

    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.goal_tracking
def test_get_assessments_due_patient_role_forbidden(async_db_client, test_db, patient_with_therapist, patient_auth_headers):
    """Test that patients cannot check due assessments (therapist-only endpoint)"""
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/patients/{patient_with_therapist.id}/assessments/due",
        headers=patient_auth_headers
    )

    assert response.status_code == 403


# ============================================================================
# Edge Cases and Validation Tests
# ============================================================================

@pytest.mark.goal_tracking
def test_create_assessment_with_goal_id(async_db_client, test_db, patient_with_therapist, therapist_user, therapist_auth_headers):
    """Test linking assessment to a treatment goal"""
    from app.models.goal_models import TreatmentGoal

    # Create a treatment goal
    goal = TreatmentGoal(
        patient_id=patient_with_therapist.id,
        therapist_id=therapist_user.id,
        description="Reduce anxiety symptoms",
        category="anxiety_management",
        status="in_progress"
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)

    assessment_data = {
        "assessment_type": "GAD-7",
        "score": 10,
        "administered_date": str(date.today()),
        "goal_id": str(goal.id)
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["goal_id"] == str(goal.id)


@pytest.mark.goal_tracking
def test_assessment_subscores_jsonb_validation(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test that subscores JSONB field accepts complex data"""
    test_db.commit()

    complex_subscores = {
        "question_1": 3,
        "question_2": 2,
        "nested_data": {
            "subsection_a": 1,
            "subsection_b": 2
        },
        "array_data": [1, 2, 3]
    }

    assessment_data = {
        "assessment_type": "BAI",
        "score": 20,
        "severity": "moderate",
        "administered_date": str(date.today()),
        "subscores": complex_subscores
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["subscores"] == complex_subscores


@pytest.mark.goal_tracking
def test_assessment_notes_max_length(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test that notes field enforces max length"""
    test_db.commit()

    long_notes = "x" * 1001  # Exceeds 1000 character limit

    assessment_data = {
        "assessment_type": "PHQ-9",
        "score": 10,
        "administered_date": str(date.today()),
        "notes": long_notes
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.goal_tracking
def test_assessment_history_chronological_order(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test that history is returned in chronological order (oldest first)"""
    today = date.today()

    # Create assessments in random order
    dates = [today - timedelta(days=30), today - timedelta(days=10), today - timedelta(days=60)]
    scores = [14, 10, 18]

    for assessment_date, score in zip(dates, scores):
        assessment = create_test_assessment_score(
            patient_id=patient_with_therapist.id,
            assessment_type="GAD-7",
            score=score,
            administered_date=assessment_date
        )
        test_db.add(assessment)
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/patients/{patient_user.id}/assessments",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    history = data["assessments"]["GAD-7"]
    dates_returned = [item["date"] for item in history]

    # Should be ordered oldest to newest
    assert dates_returned == sorted(dates_returned)


@pytest.mark.goal_tracking
def test_create_assessment_future_date_allowed(async_db_client, test_db, patient_with_therapist, therapist_auth_headers):
    """Test that future dates are allowed for scheduled assessments"""
    test_db.commit()

    future_date = date.today() + timedelta(days=7)

    assessment_data = {
        "assessment_type": "PHQ-9",
        "score": 10,
        "administered_date": str(future_date)
    }

    response = async_db_client.post(
        f"/api/v1/patients/{patient_user.id}/assessments",
        json=assessment_data,
        headers=therapist_auth_headers
    )

    # Should succeed - future dates are valid
    assert response.status_code == 200
    assert response.json()["administered_date"] == str(future_date)
