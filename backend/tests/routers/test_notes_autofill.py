"""
Integration tests for template autofill functionality.

Tests cover:
- Auto-fill endpoint for all 4 template types (SOAP, DAP, BIRP, Progress)
- Confidence score calculation and validation
- Missing fields identification
- Response structure validation
- Authorization (therapist role, active patient relationship)
- Error handling (no extracted_notes, invalid template_type, etc.)
- Edge cases (partial notes, sparse data, empty fields)
"""
import pytest
from fastapi import status
from uuid import uuid4
from datetime import datetime

from app.models.db_models import User, Patient, TherapySession as Session, TherapistPatient
from app.models.schemas import UserRole, SessionStatus, TemplateType, MoodLevel


# ============================================================================
# Test Fixtures - Sessions with Various Extracted Notes
# ============================================================================

@pytest.fixture(scope="function")
def sample_session_rich_notes(therapist_user, sample_patient, active_relationship):
    """
    Create a session with comprehensive extracted_notes for high-confidence autofill.

    This fixture creates a session with complete AI extraction data including:
    - Multiple key topics and strategies
    - Detailed therapist notes and summaries
    - Action items and follow-up topics
    - Significant quotes and emotional themes
    - Complete mood trajectory data

    Args:
        therapist_user: Therapist conducting the session
        sample_patient: Patient for this session
        active_relationship: Active therapist-patient relationship

    Returns:
        Session object with rich extracted_notes (high confidence scores)
    """
    from tests.routers.conftest import TestingSyncSessionLocal

    db = TestingSyncSessionLocal()
    try:
        session = Session(
            patient_id=sample_patient.id,
            therapist_id=therapist_user.id,
            session_date=datetime.utcnow(),
            duration_seconds=3600,
            audio_filename="comprehensive_session.mp3",
            transcript_text="Detailed transcript of a comprehensive therapy session discussing work anxiety, family dynamics, and coping strategies.",
            status=SessionStatus.processed.value,
        extracted_notes={
            "key_topics": [
                "Work-related stress and deadline pressure",
                "Family communication challenges",
                "Sleep disturbances and anxiety",
                "Coping strategies review",
                "Progress on previous goals"
            ],
            "topic_summary": "Patient discussed ongoing work stress related to upcoming project deadlines and how this is affecting sleep patterns. We explored family communication dynamics and reviewed previously learned coping strategies. Patient demonstrated good insight into anxiety triggers and expressed motivation to practice relaxation techniques.",
            "strategies": [
                {
                    "name": "Progressive muscle relaxation",
                    "category": "relaxation",
                    "status": "practiced",
                    "context": "Practiced during session to address physical tension from work stress"
                },
                {
                    "name": "Cognitive restructuring",
                    "category": "cognitive-behavioral",
                    "status": "reviewed",
                    "context": "Reviewed thought records from previous week with good application"
                },
                {
                    "name": "Sleep hygiene protocol",
                    "category": "behavioral",
                    "status": "assigned",
                    "context": "Assigned as homework to address insomnia symptoms"
                }
            ],
            "emotional_themes": [
                "Anxiety",
                "Stress",
                "Frustration",
                "Determination",
                "Hope"
            ],
            "triggers": [
                {
                    "trigger": "Upcoming project deadline",
                    "context": "Major work deadline in two weeks causing anticipatory anxiety",
                    "severity": "moderate"
                },
                {
                    "trigger": "Family dinner conversations",
                    "context": "Tense interactions with parents during weekly dinners",
                    "severity": "mild"
                }
            ],
            "action_items": [
                {
                    "task": "Practice progressive muscle relaxation daily before bed",
                    "category": "homework",
                    "details": "Use guided audio, 15 minutes minimum, track in wellness journal"
                },
                {
                    "task": "Complete thought record for work-related anxious thoughts",
                    "category": "homework",
                    "details": "Document at least 3 situations this week using CBT framework"
                },
                {
                    "task": "Implement sleep hygiene changes",
                    "category": "behavioral",
                    "details": "No screens 1 hour before bed, consistent sleep schedule"
                }
            ],
            "significant_quotes": [
                {
                    "quote": "I noticed this week that my anxiety spikes the most right after checking my work email in the evening",
                    "context": "Patient demonstrating improved self-awareness of anxiety triggers",
                    "timestamp_start": 450.5
                },
                {
                    "quote": "When I used the breathing technique we practiced, I actually felt calmer within a few minutes",
                    "context": "Evidence of strategy effectiveness and patient engagement",
                    "timestamp_start": 1250.0
                }
            ],
            "session_mood": "neutral",
            "mood_trajectory": "improving",
            "follow_up_topics": [
                "Review sleep hygiene implementation results",
                "Explore workplace boundary setting",
                "Continue family communication skill building"
            ],
            "unresolved_concerns": [
                "Difficulty setting boundaries with manager",
                "Ongoing tension with parents about career choices"
            ],
            "risk_flags": [],
            "therapist_notes": "Patient continues to demonstrate strong engagement and insight. Notable progress in identifying anxiety triggers and applying cognitive restructuring techniques. Sleep disturbances remain a concern but patient is motivated to address through behavioral interventions. Family dynamics appear to be a secondary stressor that warrants continued attention. Overall trajectory is positive with good prognosis for continued improvement.",
            "patient_summary": "You're making excellent progress in understanding your anxiety triggers, especially around work deadlines. This week, we practiced relaxation techniques and discussed ways to improve your sleep. Your homework includes daily relaxation practice and tracking anxious thoughts. You're developing good skills for managing stress and anxiety."
        }
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    finally:
        db.close()


@pytest.fixture(scope="function")
def sample_session_sparse_notes(therapist_user, sample_patient, active_relationship):
    """
    Create a session with minimal extracted_notes for low-confidence autofill testing.

    This fixture creates a session with sparse AI extraction data to test:
    - Low confidence score calculation
    - Missing fields identification
    - Handling of incomplete data

    Args:
        therapist_user: Therapist conducting the session
        sample_patient: Patient for this session
        active_relationship: Active therapist-patient relationship

    Returns:
        Session object with sparse extracted_notes (low confidence scores)
    """
    from tests.routers.conftest import TestingSyncSessionLocal

    db = TestingSyncSessionLocal()
    try:
        session = Session(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        duration_seconds=1800,
        audio_filename="brief_session.mp3",
        transcript_text="Brief session.",
        status=SessionStatus.processed.value,
        extracted_notes={
            "key_topics": ["Anxiety"],
            "topic_summary": "Brief check-in.",
            "strategies": [],
            "emotional_themes": ["Stress"],
            "triggers": [],
            "action_items": [],
            "significant_quotes": [],
            "session_mood": "neutral",
            "mood_trajectory": "stable",
            "follow_up_topics": [],
            "unresolved_concerns": [],
            "risk_flags": [],
            "therapist_notes": "Short session.",
            "patient_summary": "Brief update."
        }
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    finally:
        db.close()


@pytest.fixture(scope="function")
def sample_session_no_notes(therapist_user, sample_patient, active_relationship):
    """
    Create a session without extracted_notes for error testing.

    This session has not been processed by AI extraction yet,
    so autofill should fail with a 400 error.

    Args:
        therapist_user: Therapist conducting the session
        sample_patient: Patient for this session
        active_relationship: Active therapist-patient relationship

    Returns:
        Session object with no extracted_notes (status=transcribed)
    """
    from tests.routers.conftest import TestingSyncSessionLocal

    db = TestingSyncSessionLocal()
    try:
        session = Session(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        duration_seconds=3600,
        audio_filename="unprocessed_session.mp3",
        transcript_text="This session has not been processed by AI extraction yet.",
        status=SessionStatus.transcribed.value,
        extracted_notes=None  # Not yet processed
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    finally:
        db.close()


@pytest.fixture(scope="function")
def active_relationship(therapist_user, sample_patient):
    """
    Create an active therapist-patient relationship.

    The notes autofill endpoint requires an active relationship
    via the therapist_patients junction table.

    Args:
        therapist_user: Therapist user
        sample_patient: Patient

    Returns:
        TherapistPatient relationship object
    """
    from tests.routers.conftest import TestingSyncSessionLocal

    db = TestingSyncSessionLocal()
    try:
        relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=sample_patient.id,
        relationship_type="primary",
        is_active=True,
        started_at=datetime.utcnow()
        )
        db.add(relationship)
        db.commit()
        db.refresh(relationship)
        return relationship
    finally:
        db.close()


@pytest.fixture(scope="function")
def second_therapist_user():
    """
    Create a second therapist user for authorization testing.

    This therapist does NOT have a relationship with sample_patient,
    so autofill should fail with 403.

    Returns:
        User object with therapist role (no patient access)
    """
    from app.auth.utils import get_password_hash
    from tests.routers.conftest import TestingSyncSessionLocal

    db = TestingSyncSessionLocal()
    try:
        user = User(
        email="therapist2@test.com",
        hashed_password=get_password_hash("testpass123456"),
        first_name="Second",
        last_name="Therapist",
        full_name="Second Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture(scope="function")
def second_therapist_token(second_therapist_user):
    """
    Generate an access token for the second therapist user.

    Args:
        second_therapist_user: Second therapist user fixture

    Returns:
        JWT access token string
    """
    from app.auth.utils import create_access_token
    return create_access_token(second_therapist_user.id, second_therapist_user.role.value)


@pytest.fixture(scope="function")
def second_therapist_auth_headers(second_therapist_token):
    """
    Generate authorization headers for second therapist user.

    Args:
        second_therapist_token: JWT token for second therapist

    Returns:
        Dict with Authorization header
    """
    return {"Authorization": f"Bearer {second_therapist_token}"}


# ============================================================================
# Test Class 1: TestAutofillSOAP
# ============================================================================

class TestAutofillSOAP:
    """Test autofill for SOAP template type"""

    def test_autofill_soap_success(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test auto-fill returns properly structured SOAP template"""
        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "template_type" in data
        assert data["template_type"] == "soap"
        assert "auto_filled_content" in data
        assert "confidence_scores" in data
        assert "missing_fields" in data
        assert "metadata" in data

        # Verify SOAP sections present
        content = data["auto_filled_content"]
        assert "subjective" in content
        assert "objective" in content
        assert "assessment" in content
        assert "plan" in content

        # Verify sections have expected structure (dicts with fields)
        assert isinstance(content["subjective"], dict)
        assert isinstance(content["objective"], dict)
        assert isinstance(content["assessment"], dict)
        assert isinstance(content["plan"], dict)

        # Verify SOAP sections contain expected fields
        assert "chief_complaint" in content["subjective"]
        assert "mood" in content["subjective"]
        assert "presentation" in content["objective"]
        assert "clinical_impression" in content["assessment"]
        assert "interventions" in content["plan"]

    def test_autofill_soap_confidence_scores(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test SOAP auto-fill includes valid confidence scores for each section"""
        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify confidence_scores structure
        scores = data["confidence_scores"]
        assert isinstance(scores, dict)

        # All SOAP sections should have confidence scores
        assert "subjective" in scores
        assert "objective" in scores
        assert "assessment" in scores
        assert "plan" in scores

        # All scores should be floats between 0.0 and 1.0
        for section_name, score in scores.items():
            assert isinstance(score, (int, float))
            assert 0.0 <= score <= 1.0, f"Confidence score for {section_name} is out of range: {score}"

        # Rich notes should have high confidence scores (>= 0.5)
        for section_name, score in scores.items():
            assert score >= 0.5, f"Expected high confidence for {section_name} with rich notes, got {score}"


# ============================================================================
# Test Class 2: TestAutofillDAP
# ============================================================================

class TestAutofillDAP:
    """Test autofill for DAP template type"""

    def test_autofill_dap_success(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test auto-fill returns properly structured DAP template"""
        request_data = {
            "template_type": "dap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify DAP structure
        assert data["template_type"] == "dap"
        content = data["auto_filled_content"]

        assert "data" in content
        assert "assessment" in content
        assert "plan" in content

        # Verify sections are dicts
        assert isinstance(content["data"], dict)
        assert isinstance(content["assessment"], dict)
        assert isinstance(content["plan"], dict)

        # Verify DAP sections contain expected fields
        assert "observations" in content["data"]
        assert "clinical_impression" in content["assessment"]
        assert "next_session_focus" in content["plan"]

    def test_autofill_dap_confidence_scores(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test DAP auto-fill includes confidence scores"""
        request_data = {
            "template_type": "dap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        scores = data["confidence_scores"]

        # DAP sections should all have scores
        assert "data" in scores
        assert "assessment" in scores
        assert "plan" in scores

        # All scores valid range
        for score in scores.values():
            assert 0.0 <= score <= 1.0


# ============================================================================
# Test Class 3: TestAutofillBIRP
# ============================================================================

class TestAutofillBIRP:
    """Test autofill for BIRP template type"""

    def test_autofill_birp_success(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test auto-fill returns properly structured BIRP template"""
        request_data = {
            "template_type": "birp"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify BIRP structure
        assert data["template_type"] == "birp"
        content = data["auto_filled_content"]

        assert "behavior" in content
        assert "intervention" in content
        assert "response" in content
        assert "plan" in content

        # Verify sections are dicts
        assert isinstance(content["behavior"], dict)
        assert isinstance(content["intervention"], dict)
        assert isinstance(content["response"], dict)
        assert isinstance(content["plan"], dict)

        # Verify BIRP sections contain expected fields
        assert "presentation" in content["behavior"]
        assert "techniques" in content["intervention"]
        assert "patient_response" in content["response"]
        assert "next_steps" in content["plan"]

    def test_autofill_birp_confidence_scores(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test BIRP auto-fill includes confidence scores"""
        request_data = {
            "template_type": "birp"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        scores = data["confidence_scores"]

        # BIRP sections should all have scores
        assert "behavior" in scores
        assert "intervention" in scores
        assert "response" in scores
        assert "plan" in scores

        # All scores valid range
        for score in scores.values():
            assert 0.0 <= score <= 1.0


# ============================================================================
# Test Class 4: TestAutofillProgress
# ============================================================================

class TestAutofillProgress:
    """Test autofill for Progress Note template type"""

    def test_autofill_progress_success(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test auto-fill returns properly structured Progress Note template"""
        request_data = {
            "template_type": "progress"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify Progress Note structure
        assert data["template_type"] == "progress"
        content = data["auto_filled_content"]

        # Progress notes have more sections
        assert "session_summary" in content
        assert "clinical_presentation" in content
        assert "progress" in content
        assert "interventions" in content
        assert "plan" in content

        # Verify sections are dicts
        for section in content.values():
            assert isinstance(section, dict)

        # Verify Progress sections contain expected fields
        assert "overview" in content["session_summary"]
        assert "mood_affect" in content["clinical_presentation"]
        assert "changes" in content["progress"]
        assert "techniques" in content["interventions"]
        assert "next_steps" in content["plan"]

    def test_autofill_progress_confidence_scores(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test Progress Note auto-fill includes confidence scores"""
        request_data = {
            "template_type": "progress"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        scores = data["confidence_scores"]

        # Progress sections should all have scores
        assert "session_summary" in scores
        assert "clinical_presentation" in scores
        assert "progress" in scores
        assert "interventions" in scores
        assert "plan" in scores

        # All scores valid range
        for score in scores.values():
            assert 0.0 <= score <= 1.0


# ============================================================================
# Test Class 5: TestConfidenceScoring
# ============================================================================

class TestConfidenceScoring:
    """Test confidence score calculation and missing fields detection"""

    def test_sparse_notes_lower_confidence(
        self,
        client,
        therapist_auth_headers,
        sample_session_sparse_notes
    ):
        """Test that sparse notes result in lower confidence scores"""
        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_sparse_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        scores = data["confidence_scores"]

        # Sparse notes should have lower confidence (< 0.8)
        # At least some sections should have low confidence
        low_confidence_sections = [s for s, score in scores.items() if score < 0.8]
        assert len(low_confidence_sections) > 0, "Expected at least one section with low confidence for sparse notes"

    def test_missing_fields_identified(
        self,
        client,
        therapist_auth_headers,
        sample_session_sparse_notes
    ):
        """Test that missing or weak fields are properly identified"""
        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_sparse_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        missing = data["missing_fields"]

        # Verify structure: dict mapping section names to lists of field names
        assert isinstance(missing, dict)

        # For sparse notes, we expect some missing fields
        # (empty lists, short strings should be flagged)
        total_missing_fields = sum(len(fields) for fields in missing.values())
        assert total_missing_fields > 0, "Expected some missing fields for sparse notes"

    def test_metadata_includes_overall_confidence(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test that metadata includes overall_confidence score"""
        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        metadata = data["metadata"]

        # Verify metadata structure
        assert "template_type" in metadata
        assert metadata["template_type"] == "soap"
        assert "overall_confidence" in metadata

        # Overall confidence should be average of section scores
        overall = metadata["overall_confidence"]
        assert isinstance(overall, (int, float))
        assert 0.0 <= overall <= 1.0

    def test_rich_notes_high_confidence(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test that comprehensive notes result in high confidence scores"""
        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Overall confidence should be high (>= 0.7) for rich notes
        overall_confidence = data["metadata"]["overall_confidence"]
        assert overall_confidence >= 0.7, f"Expected high overall confidence for rich notes, got {overall_confidence}"


# ============================================================================
# Test Class 6: TestAutofillAuthorization
# ============================================================================

class TestAutofillAuthorization:
    """Test authorization requirements for autofill endpoint"""

    def test_autofill_requires_therapist_role(
        self,
        client,
        patient_auth_headers,
        sample_session_rich_notes
    ):
        """Test that patients cannot access autofill endpoint"""
        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=patient_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "therapist" in response.json()["detail"].lower()

    def test_autofill_requires_active_relationship(
        self,
        client,
        second_therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test that therapist must have active relationship with patient"""
        # second_therapist has NO relationship with sample_patient
        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=second_therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "access" in response.json()["detail"].lower() or "denied" in response.json()["detail"].lower()

    def test_autofill_requires_authentication(
        self,
        client,
        sample_session_rich_notes
    ):
        """Test that autofill requires authentication"""
        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            json=request_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test Class 7: TestAutofillErrors
# ============================================================================

class TestAutofillErrors:
    """Test error handling for autofill endpoint"""

    def test_autofill_fails_without_extracted_notes(
        self,
        client,
        therapist_auth_headers,
        sample_session_no_notes
    ):
        """Test autofill returns 400 if session has no extracted_notes"""
        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_no_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        error_detail = response.json()["detail"].lower()
        assert "processed" in error_detail or "extraction" in error_detail or "extracted" in error_detail

    def test_autofill_invalid_template_type(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test autofill returns 400 for invalid template_type"""
        request_data = {
            "template_type": "invalid_type"
        }

        response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        # Should fail validation at Pydantic level
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_autofill_nonexistent_session(
        self,
        client,
        therapist_auth_headers
    ):
        """Test autofill returns 404 for non-existent session"""
        nonexistent_id = uuid4()

        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{nonexistent_id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_autofill_malformed_session_id(
        self,
        client,
        therapist_auth_headers
    ):
        """Test autofill returns 422 for malformed session UUID"""
        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/not-a-uuid/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Test Class 8: TestAutofillEdgeCases
# ============================================================================

class TestAutofillEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_autofill_handles_partial_extracted_notes(
        self,
        client,
        therapist_auth_headers,
        therapist_user,
        sample_patient,
        active_relationship
    ):
        """Test autofill handles sessions with some fields missing from extracted_notes"""
        from tests.routers.conftest import TestingSyncSessionLocal

        # Create session with only required fields, optional fields missing
        db = TestingSyncSessionLocal()
        session = Session(
            patient_id=sample_patient.id,
            therapist_id=therapist_user.id,
            session_date=datetime.utcnow(),
            status=SessionStatus.processed.value,
            extracted_notes={
                "key_topics": ["Anxiety"],
                "topic_summary": "Patient discussed anxiety.",
                "strategies": [],  # Empty list
                "emotional_themes": ["Anxiety"],
                "triggers": [],  # Empty list
                "action_items": [],  # Empty list
                "significant_quotes": [],  # Empty list
                "session_mood": "neutral",
                "mood_trajectory": "stable",
                "follow_up_topics": [],  # Empty list
                "unresolved_concerns": [],  # Empty list
                "risk_flags": [],  # Empty list
                "therapist_notes": "Standard session notes.",
                "patient_summary": "Brief summary."
            }
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        db.close()

        request_data = {
            "template_type": "soap"
        }

        response = client.post(
            f"/api/v1/sessions/{session.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )

        # Should succeed but with lower confidence
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify autofill completed despite empty fields
        assert "auto_filled_content" in data
        assert "confidence_scores" in data

        # Confidence should be lower due to missing data
        overall_confidence = data["metadata"]["overall_confidence"]
        assert overall_confidence < 0.8, "Expected low confidence for partial notes"

    def test_autofill_all_template_types_same_session(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes
    ):
        """Test that all 4 template types can be auto-filled from the same session"""
        template_types = ["soap", "dap", "birp", "progress"]

        for template_type in template_types:
            request_data = {
                "template_type": template_type
            }

            response = client.post(
                f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
                headers=therapist_auth_headers,
                json=request_data
            )

            assert response.status_code == status.HTTP_200_OK, f"Failed to autofill {template_type}"
            data = response.json()

            # Verify correct template type in response
            assert data["template_type"] == template_type

            # Verify all responses have required structure
            assert "auto_filled_content" in data
            assert "confidence_scores" in data
            assert "missing_fields" in data
            assert "metadata" in data

    def test_autofill_confidence_reflects_data_quality(
        self,
        client,
        therapist_auth_headers,
        sample_session_rich_notes,
        sample_session_sparse_notes
    ):
        """Test that confidence scores accurately reflect data quality differences"""
        request_data = {
            "template_type": "soap"
        }

        # Get confidence for rich notes
        rich_response = client.post(
            f"/api/v1/sessions/{sample_session_rich_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )
        rich_confidence = rich_response.json()["metadata"]["overall_confidence"]

        # Get confidence for sparse notes
        sparse_response = client.post(
            f"/api/v1/sessions/{sample_session_sparse_notes.id}/notes/autofill",
            headers=therapist_auth_headers,
            json=request_data
        )
        sparse_confidence = sparse_response.json()["metadata"]["overall_confidence"]

        # Rich notes should have significantly higher confidence
        assert rich_confidence > sparse_confidence, (
            f"Rich notes confidence ({rich_confidence}) should be higher than "
            f"sparse notes confidence ({sparse_confidence})"
        )

        # Difference should be meaningful (at least 0.2)
        assert rich_confidence - sparse_confidence >= 0.2, (
            f"Expected significant confidence difference, got {rich_confidence - sparse_confidence}"
        )
