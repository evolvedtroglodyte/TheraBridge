"""
Integration tests for analytics router endpoints.

Tests cover:
- Analytics overview endpoint
- Patient progress endpoint
- Session trends endpoint
- Topics frequency endpoint
- Authentication/authorization
- Response structure validation
- Error cases
"""
import pytest
from fastapi import status
from uuid import uuid4
from datetime import datetime, timedelta
from app.models.db_models import User, Patient, Session
from app.models.schemas import UserRole, SessionStatus

ANALYTICS_PREFIX = "/api/v1/analytics"


# ============================================================================
# Test Fixtures - Sample Data
# ============================================================================

@pytest.fixture(scope="function")
def therapist_with_patients_and_sessions(test_db, therapist_user):
    """
    Create a therapist with multiple patients and completed sessions.

    This fixture creates:
    - 3 patients
    - 10 sessions across different patients
    - Mix of completed and pending sessions
    - Sessions with extracted notes data

    Returns:
        Dict with therapist, patients, and sessions
    """
    # Create patients
    patients = [
        Patient(
            name=f"Patient {i}",
            email=f"patient{i}@example.com",
            phone=f"555010{i}",
            therapist_id=therapist_user.id
        )
        for i in range(1, 4)
    ]
    test_db.add_all(patients)
    test_db.commit()
    for p in patients:
        test_db.refresh(p)

    # Create sessions with varying dates
    sessions = []
    base_date = datetime.utcnow()

    # Sessions for Patient 1 (4 sessions over last month)
    for i in range(4):
        session = Session(
            patient_id=patients[0].id,
            therapist_id=therapist_user.id,
            session_date=base_date - timedelta(days=i*7),
            duration_seconds=3600,
            audio_filename=f"session_p1_{i}.mp3",
            transcript_text="Therapist: How are you? Client: Good.",
            status=SessionStatus.processed.value,
            extracted_notes={
                "key_topics": ["Anxiety", "Work stress"],
                "session_mood": "neutral",
                "mood_trajectory": "stable",
                "action_items": [{"task": "Practice breathing", "category": "homework"}]
            }
        )
        sessions.append(session)

    # Sessions for Patient 2 (3 sessions)
    for i in range(3):
        session = Session(
            patient_id=patients[1].id,
            therapist_id=therapist_user.id,
            session_date=base_date - timedelta(days=i*10),
            duration_seconds=3000,
            audio_filename=f"session_p2_{i}.mp3",
            transcript_text="Therapist: Let's talk. Client: Okay.",
            status=SessionStatus.processed.value,
            extracted_notes={
                "key_topics": ["Depression", "Family issues"],
                "session_mood": "positive",
                "mood_trajectory": "improving"
            }
        )
        sessions.append(session)

    # Sessions for Patient 3 (2 completed, 1 pending)
    for i in range(2):
        session = Session(
            patient_id=patients[2].id,
            therapist_id=therapist_user.id,
            session_date=base_date - timedelta(days=i*14),
            duration_seconds=4200,
            audio_filename=f"session_p3_{i}.mp3",
            transcript_text="Therapist: Welcome. Client: Thanks.",
            status=SessionStatus.processed.value,
            extracted_notes={
                "key_topics": ["Relationships", "Self-esteem"],
                "session_mood": "neutral"
            }
        )
        sessions.append(session)

    # Add one pending session
    pending_session = Session(
        patient_id=patients[2].id,
        therapist_id=therapist_user.id,
        session_date=base_date + timedelta(days=3),
        duration_seconds=0,
        audio_filename="session_pending.mp3",
        status=SessionStatus.pending.value
    )
    sessions.append(pending_session)

    test_db.add_all(sessions)
    test_db.commit()
    for s in sessions:
        test_db.refresh(s)

    return {
        "therapist": therapist_user,
        "patients": patients,
        "sessions": sessions
    }


@pytest.fixture(scope="function")
def second_therapist_with_data(test_db):
    """Create a second therapist with their own patients for authorization testing"""
    therapist2 = User(
        email="therapist2@test.com",
        hashed_password="hashed",
        first_name="Second",
        last_name="Therapist",
        full_name="Second Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    test_db.add(therapist2)
    test_db.commit()
    test_db.refresh(therapist2)

    # Create a patient for this therapist
    patient = Patient(
        name="Other Patient",
        email="other@example.com",
        therapist_id=therapist2.id
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)

    return {
        "therapist": therapist2,
        "patient": patient
    }


# ============================================================================
# Test Analytics Overview Endpoint
# ============================================================================

class TestAnalyticsOverview:
    """Test GET /analytics/overview endpoint"""

    def test_get_overview_success(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test successful overview retrieval"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/overview",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "total_patients" in data
        assert "active_patients" in data
        assert "sessions_this_week" in data
        assert "sessions_this_month" in data
        assert "upcoming_sessions" in data
        assert "completion_rate" in data

        # Verify types
        assert isinstance(data["total_patients"], int)
        assert isinstance(data["active_patients"], int)
        assert isinstance(data["sessions_this_week"], int)
        assert isinstance(data["sessions_this_month"], int)
        assert isinstance(data["upcoming_sessions"], int)
        assert isinstance(data["completion_rate"], float)

        # Verify values match test data
        assert data["total_patients"] == 3
        assert data["upcoming_sessions"] >= 1  # At least one pending session

    def test_get_overview_response_structure(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test overview response has correct structure and value ranges"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/overview",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify completion_rate is between 0 and 1
        assert 0.0 <= data["completion_rate"] <= 1.0

        # Verify non-negative counts
        assert data["total_patients"] >= 0
        assert data["active_patients"] >= 0
        assert data["sessions_this_week"] >= 0
        assert data["sessions_this_month"] >= 0
        assert data["upcoming_sessions"] >= 0

    def test_get_overview_requires_auth(self, client):
        """Test overview endpoint requires authentication"""
        response = client.get(f"{ANALYTICS_PREFIX}/overview")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_overview_requires_therapist_role(
        self,
        client,
        patient_auth_headers
    ):
        """Test overview endpoint requires therapist role (patient should fail)"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/overview",
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "therapist" in response.json()["detail"].lower()

    def test_get_overview_empty_data(
        self,
        client,
        therapist_auth_headers
    ):
        """Test overview with therapist that has no patients"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/overview",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return zeros for empty data
        assert data["total_patients"] == 0
        assert data["sessions_this_week"] == 0
        assert data["sessions_this_month"] == 0


# ============================================================================
# Test Patient Progress Endpoint
# ============================================================================

class TestPatientProgress:
    """Test GET /analytics/patients/{patient_id}/progress endpoint"""

    def test_get_patient_progress_success(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test successful patient progress retrieval"""
        patient = therapist_with_patients_and_sessions["patients"][0]

        response = client.get(
            f"{ANALYTICS_PREFIX}/patients/{patient.id}/progress",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "patient_id" in data
        assert "total_sessions" in data
        assert "first_session_date" in data
        assert "last_session_date" in data
        assert "session_frequency" in data
        assert "mood_trend" in data
        assert "goals" in data

        # Verify patient_id matches
        assert data["patient_id"] == str(patient.id)
        assert data["total_sessions"] == 4  # Patient 1 has 4 sessions

    def test_get_patient_progress_response_structure(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test patient progress response has correct nested structure"""
        patient = therapist_with_patients_and_sessions["patients"][0]

        response = client.get(
            f"{ANALYTICS_PREFIX}/patients/{patient.id}/progress",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify session_frequency structure
        assert "sessions_per_week" in data["session_frequency"]
        assert "sessions_per_month" in data["session_frequency"]
        assert isinstance(data["session_frequency"]["sessions_per_week"], (int, float))

        # Verify mood_trend structure
        assert "current" in data["mood_trend"]
        assert "trend" in data["mood_trend"]

        # Verify goals structure
        assert "achieved" in data["goals"]
        assert "in_progress" in data["goals"]
        assert "total" in data["goals"]

    def test_get_patient_progress_invalid_patient_id(
        self,
        client,
        therapist_auth_headers
    ):
        """Test get patient progress fails with non-existent patient_id"""
        nonexistent_id = uuid4()

        response = client.get(
            f"{ANALYTICS_PREFIX}/patients/{nonexistent_id}/progress",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "patient" in response.json()["detail"].lower()

    def test_get_patient_progress_unauthorized_therapist(
        self,
        client,
        test_db,
        therapist_auth_headers,
        second_therapist_with_data
    ):
        """Test patient progress fails when requesting different therapist's patient"""
        other_patient = second_therapist_with_data["patient"]

        response = client.get(
            f"{ANALYTICS_PREFIX}/patients/{other_patient.id}/progress",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden or 404 Not Found (therapist can't access)
        assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]

    def test_get_patient_progress_requires_auth(
        self,
        client,
        therapist_with_patients_and_sessions
    ):
        """Test patient progress endpoint requires authentication"""
        patient = therapist_with_patients_and_sessions["patients"][0]

        response = client.get(
            f"{ANALYTICS_PREFIX}/patients/{patient.id}/progress"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_patient_progress_invalid_uuid(self, client, therapist_auth_headers):
        """Test get patient progress fails with invalid UUID format"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/patients/not-a-uuid/progress",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Test Session Trends Endpoint
# ============================================================================

class TestSessionTrends:
    """Test GET /analytics/sessions/trends endpoint"""

    def test_get_trends_default_period(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test session trends with default period (month)"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/sessions/trends",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "period" in data
        assert "data" in data

        # Verify period is default (month)
        assert data["period"] == "month"

        # Verify data is a list
        assert isinstance(data["data"], list)

    def test_get_trends_weekly_period(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test session trends with weekly period"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/sessions/trends?period=week",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["period"] == "week"
        assert isinstance(data["data"], list)

    def test_get_trends_all_periods(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test session trends with all valid period values"""
        valid_periods = ["week", "month", "quarter", "year"]

        for period in valid_periods:
            response = client.get(
                f"{ANALYTICS_PREFIX}/sessions/trends?period={period}",
                headers=therapist_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["period"] == period

    def test_get_trends_invalid_period(
        self,
        client,
        therapist_auth_headers
    ):
        """Test session trends fails with invalid period"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/sessions/trends?period=invalid",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_get_trends_with_patient_filter(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test session trends filtered by specific patient"""
        patient = therapist_with_patients_and_sessions["patients"][0]

        response = client.get(
            f"{ANALYTICS_PREFIX}/sessions/trends?patient_id={patient.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return trends data (structure same as without filter)
        assert "period" in data
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_get_trends_response_structure(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test session trends response has correct data point structure"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/sessions/trends",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify period and data fields exist
        assert data["period"] == "month"
        assert isinstance(data["data"], list)

        # If data points exist, verify their structure
        if len(data["data"]) > 0:
            data_point = data["data"][0]
            assert "date" in data_point
            assert "session_count" in data_point
            assert isinstance(data_point["session_count"], int)

    def test_get_trends_requires_auth(self, client):
        """Test session trends endpoint requires authentication"""
        response = client.get(f"{ANALYTICS_PREFIX}/sessions/trends")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_trends_invalid_patient_uuid(
        self,
        client,
        therapist_auth_headers
    ):
        """Test trends fails with invalid patient UUID format"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/sessions/trends?patient_id=not-a-uuid",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Test Topics Endpoint
# ============================================================================

class TestTopics:
    """Test GET /analytics/topics endpoint"""

    def test_get_topics_success(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test successful topic frequencies retrieval"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/topics",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "topics" in data
        assert isinstance(data["topics"], list)

        # Should have topics since we have sessions with extracted_notes
        assert len(data["topics"]) > 0

    def test_get_topics_response_structure(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test topics response has correct structure for each topic"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/topics",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify each topic has correct fields
        for topic in data["topics"]:
            assert "name" in topic
            assert "count" in topic
            assert "percentage" in topic

            # Verify types
            assert isinstance(topic["name"], str)
            assert isinstance(topic["count"], int)
            assert isinstance(topic["percentage"], float)

            # Verify value ranges
            assert topic["count"] > 0
            assert 0.0 <= topic["percentage"] <= 1.0

    def test_get_topics_empty_data(
        self,
        client,
        therapist_auth_headers
    ):
        """Test topics endpoint with therapist that has no sessions"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/topics",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should return empty topics list
        assert "topics" in data
        assert isinstance(data["topics"], list)
        assert len(data["topics"]) == 0

    def test_get_topics_requires_auth(self, client):
        """Test topics endpoint requires authentication"""
        response = client.get(f"{ANALYTICS_PREFIX}/topics")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_topics_requires_therapist_role(
        self,
        client,
        patient_auth_headers
    ):
        """Test topics endpoint requires therapist role"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/topics",
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "therapist" in response.json()["detail"].lower()

    def test_get_topics_sorted_by_frequency(
        self,
        client,
        therapist_auth_headers,
        therapist_with_patients_and_sessions
    ):
        """Test that topics are returned sorted by frequency (descending)"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/topics",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify topics are sorted by count (descending)
        if len(data["topics"]) > 1:
            counts = [topic["count"] for topic in data["topics"]]
            assert counts == sorted(counts, reverse=True)


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================

class TestAnalyticsEdgeCases:
    """Test edge cases and error scenarios"""

    def test_invalid_auth_token(self, client):
        """Test all endpoints reject invalid authentication tokens"""
        invalid_headers = {"Authorization": "Bearer invalid-token-12345"}

        endpoints = [
            f"{ANALYTICS_PREFIX}/overview",
            f"{ANALYTICS_PREFIX}/patients/{uuid4()}/progress",
            f"{ANALYTICS_PREFIX}/sessions/trends",
            f"{ANALYTICS_PREFIX}/topics"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=invalid_headers)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_malformed_patient_id(self, client, therapist_auth_headers):
        """Test patient progress with malformed UUID"""
        response = client.get(
            f"{ANALYTICS_PREFIX}/patients/12345/progress",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_patient_with_no_sessions(
        self,
        client,
        test_db,
        therapist_auth_headers,
        therapist_user
    ):
        """Test patient progress for patient with no sessions"""
        # Create a patient with no sessions
        patient = Patient(
            name="No Sessions Patient",
            therapist_id=therapist_user.id
        )
        test_db.add(patient)
        test_db.commit()
        test_db.refresh(patient)

        response = client.get(
            f"{ANALYTICS_PREFIX}/patients/{patient.id}/progress",
            headers=therapist_auth_headers
        )

        # Should still return 200 with empty/zero values
        # Or return 404 if no sessions exist - depends on service implementation
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]
