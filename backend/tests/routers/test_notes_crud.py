"""
Comprehensive integration tests for session note CRUD operations.

Tests:
- POST /api/v1/sessions/{session_id}/notes (create note)
- GET /api/v1/sessions/{session_id}/notes (list notes)
- PATCH /api/v1/notes/{note_id} (update note)

Coverage areas:
- Note creation with templates
- Authorization via therapist-patient relationships
- Content validation
- Status workflow (draft → completed → signed)
- Template linking
- JSONB content handling
"""
import pytest
from uuid import uuid4
from datetime import datetime
from app.models.db_models import Patient, User, TherapySession, TherapistPatient, NoteTemplate, SessionNote
from app.models.schemas import UserRole, NoteStatus, TemplateType


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_patient(test_db, therapist_user):
    """Create a test patient in the database"""
    patient = Patient(
        id=uuid4(),
        name="Test Patient",
        email="patient@test.com",
        phone="+1234567890",
        therapist_id=therapist_user.id
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)
    return patient


@pytest.fixture(scope="function")
def patient_user_for_relationship(test_db):
    """Create a patient user for therapist-patient relationship testing"""
    from app.auth.utils import get_password_hash
    patient_user = User(
        id=uuid4(),
        email="patientuser@test.com",
        hashed_password=get_password_hash("password12345"),
        first_name="Patient",
        last_name="User",
        full_name="Patient User",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(patient_user)
    test_db.commit()
    test_db.refresh(patient_user)
    return patient_user


@pytest.fixture(scope="function")
def test_patient_linked_to_user(test_db, therapist_user, patient_user_for_relationship):
    """Create a Patient record linked to the patient user (for sessions)"""
    patient = Patient(
        id=patient_user_for_relationship.id,  # Use same ID as user
        name="Patient User",
        email="patientuser@test.com",
        phone="+1234567890",
        therapist_id=therapist_user.id
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)
    return patient


@pytest.fixture(scope="function")
def active_therapist_patient_relationship(test_db, therapist_user, patient_user_for_relationship, test_patient_linked_to_user):
    """Create an active therapist-patient relationship"""
    relationship = TherapistPatient(
        id=uuid4(),
        therapist_id=therapist_user.id,
        patient_id=patient_user_for_relationship.id,  # This must match session.patient_id
        relationship_type="primary",
        is_active=True,
        started_at=datetime.utcnow()
    )
    test_db.add(relationship)
    test_db.commit()
    test_db.refresh(relationship)
    return relationship


@pytest.fixture(scope="function")
def sample_note_template(test_db, therapist_user):
    """Create a sample SOAP note template for testing"""
    template = NoteTemplate(
        id=uuid4(),
        name="SOAP Note",
        description="Standard SOAP clinical note format",
        template_type="soap",
        is_system=True,
        created_by=therapist_user.id,
        is_shared=True,
        structure={
            "sections": [
                {
                    "id": "subjective",
                    "label": "Subjective",
                    "fields": [
                        {"id": "chief_complaint", "label": "Chief Complaint", "type": "textarea", "required": True},
                        {"id": "mood", "label": "Mood", "type": "text", "required": False}
                    ]
                },
                {
                    "id": "objective",
                    "label": "Objective",
                    "fields": [
                        {"id": "presentation", "label": "Presentation", "type": "textarea", "required": True},
                        {"id": "mood_affect", "label": "Mood/Affect", "type": "text", "required": False}
                    ]
                },
                {
                    "id": "assessment",
                    "label": "Assessment",
                    "fields": [
                        {"id": "clinical_impression", "label": "Clinical Impression", "type": "textarea", "required": True}
                    ]
                },
                {
                    "id": "plan",
                    "label": "Plan",
                    "fields": [
                        {"id": "interventions", "label": "Interventions", "type": "textarea", "required": True},
                        {"id": "homework", "label": "Homework", "type": "textarea", "required": False}
                    ]
                }
            ]
        }
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)
    return template


@pytest.fixture(scope="function")
def sample_session_with_extracted_notes(test_db, test_patient_linked_to_user, therapist_user):
    """Create a test session with AI-extracted notes (JSONB)"""
    session = TherapySession(
        id=uuid4(),
        patient_id=test_patient_linked_to_user.id,  # Links to Patient with same ID as User
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        status="processed",
        transcript_text="This is a sample therapy session transcript discussing anxiety and coping strategies.",
        extracted_notes={
            "key_topics": ["Work anxiety", "Breathing techniques", "Sleep patterns"],
            "topic_summary": "Patient discussed work-related stress and learned breathing exercises.",
            "strategies": [
                {
                    "name": "Box breathing",
                    "category": "Breathing technique",
                    "status": "practiced",
                    "context": "Practiced in session to manage acute anxiety"
                }
            ],
            "emotional_themes": ["anxiety", "stress", "hope"],
            "triggers": [
                {
                    "trigger": "Team meetings",
                    "context": "Patient feels anxious before presenting",
                    "severity": "moderate"
                }
            ],
            "action_items": [
                {
                    "task": "Practice box breathing twice daily",
                    "category": "homework",
                    "details": "Morning and before bed"
                }
            ],
            "significant_quotes": [],
            "session_mood": "neutral",
            "mood_trajectory": "improving",
            "follow_up_topics": ["Review breathing practice effectiveness"],
            "unresolved_concerns": [],
            "risk_flags": [],
            "therapist_notes": "Patient is showing progress with anxiety management techniques. Continue with CBT approach.",
            "patient_summary": "You discussed your work anxiety and learned some new breathing techniques to help manage stress."
        }
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session


@pytest.fixture(scope="function")
def sample_note(test_db, sample_session_with_extracted_notes, sample_note_template):
    """Create a pre-existing note for update/get tests"""
    note = SessionNote(
        id=uuid4(),
        session_id=sample_session_with_extracted_notes.id,
        template_id=sample_note_template.id,
        content={
            "subjective": {
                "chief_complaint": "Work-related anxiety and stress",
                "mood": "Anxious but hopeful"
            },
            "objective": {
                "presentation": "Patient appeared engaged and motivated",
                "mood_affect": "Anxious affect, appropriate to discussion"
            },
            "assessment": {
                "clinical_impression": "GAD symptoms with good insight and motivation for change"
            },
            "plan": {
                "interventions": "Taught box breathing technique, practiced in session",
                "homework": "Practice box breathing twice daily"
            }
        },
        status="draft"
    )
    test_db.add(note)
    test_db.commit()
    test_db.refresh(note)
    return note


# ============================================================================
# Create Note Tests (POST /api/v1/sessions/{session_id}/notes)
# ============================================================================

def test_create_note_with_valid_template_succeeds(
    async_db_client,
    therapist_auth_headers,
    sample_session_with_extracted_notes,
    sample_note_template,
    active_therapist_patient_relationship
):
    """Test creating a note with valid template_id and content succeeds"""
    note_data = {
        "template_id": str(sample_note_template.id),
        "content": {
            "subjective": {"chief_complaint": "Patient reports increased anxiety at work"},
            "objective": {"presentation": "Patient appeared calm and engaged"},
            "assessment": {"clinical_impression": "Moderate anxiety, good coping skills"},
            "plan": {"interventions": "Continue CBT techniques"}
        }
    }

    response = async_db_client.post(
        f"/api/v1/sessions/{sample_session_with_extracted_notes.id}/notes",
        json=note_data,
        headers=therapist_auth_headers
    )

    print(f"\n=== DEBUG ===")
    print(f"Response status: {response.status_code}")
    print(f"Response body: {response.json()}")
    print(f"=============\n")

    assert response.status_code == 201
    data = response.json()
    assert data["session_id"] == str(sample_session_with_extracted_notes.id)
    assert data["template_id"] == str(sample_note_template.id)
    assert data["content"] == note_data["content"]
    assert data["status"] == "draft"  # Default status
    assert "id" in data
    assert "created_at" in data


def test_create_note_links_to_session_and_template(
    async_db_client,
    test_db,
    therapist_auth_headers,
    sample_session_with_extracted_notes,
    sample_note_template,
    active_therapist_patient_relationship
):
    """Test created note correctly links to session and template"""
    note_data = {
        "template_id": str(sample_note_template.id),
        "content": {"subjective": {"chief_complaint": "Test complaint"}}
    }

    response = async_db_client.post(
        f"/api/v1/sessions/{sample_session_with_extracted_notes.id}/notes",
        json=note_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 201
    note_id = response.json()["id"]

    # Verify in database
    note = test_db.query(SessionNote).filter(SessionNote.id == note_id).first()
    assert note is not None
    assert note.session_id == sample_session_with_extracted_notes.id
    assert note.template_id == sample_note_template.id


def test_create_note_defaults_to_draft_status(
    async_db_client,
    therapist_auth_headers,
    sample_session_with_extracted_notes,
    sample_note_template,
    active_therapist_patient_relationship
):
    """Test created note defaults to 'draft' status"""
    note_data = {
        "template_id": str(sample_note_template.id),
        "content": {"subjective": {"chief_complaint": "Test"}}
    }

    response = async_db_client.post(
        f"/api/v1/sessions/{sample_session_with_extracted_notes.id}/notes",
        json=note_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 201
    assert response.json()["status"] == "draft"


def test_create_note_requires_therapist_role(
    async_db_client,
    patient_auth_headers,
    sample_session_with_extracted_notes,
    sample_note_template
):
    """Test creating note requires therapist role (patient role rejected)"""
    note_data = {
        "template_id": str(sample_note_template.id),
        "content": {"subjective": {"chief_complaint": "Test"}}
    }

    response = async_db_client.post(
        f"/api/v1/sessions/{sample_session_with_extracted_notes.id}/notes",
        json=note_data,
        headers=patient_auth_headers
    )

    # Should fail due to @require_role(["therapist"]) decorator
    assert response.status_code == 403


def test_create_note_requires_active_patient_relationship(
    async_db_client,
    test_db,
    therapist_auth_headers,
    therapist_user,
    patient_user_for_relationship,
    sample_note_template
):
    """Test creating note requires active therapist-patient relationship"""
    # Create a session for a patient WITHOUT an active relationship
    other_patient = Patient(
        id=uuid4(),
        name="Unrelated Patient",
        email="unrelated@test.com",
        phone="+1111111111",
        therapist_id=uuid4()  # Different therapist
    )
    test_db.add(other_patient)
    test_db.commit()

    session = TherapySession(
        id=uuid4(),
        patient_id=other_patient.id,
        therapist_id=uuid4(),  # Different therapist
        session_date=datetime.utcnow(),
        status="processed"
    )
    test_db.add(session)
    test_db.commit()

    note_data = {
        "template_id": str(sample_note_template.id),
        "content": {"subjective": {"chief_complaint": "Test"}}
    }

    response = async_db_client.post(
        f"/api/v1/sessions/{session.id}/notes",
        json=note_data,
        headers=therapist_auth_headers
    )

    # Should fail due to verify_session_access check
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


def test_create_note_with_invalid_template_returns_400(
    async_db_client,
    therapist_auth_headers,
    sample_session_with_extracted_notes,
    active_therapist_patient_relationship
):
    """Test creating note with non-existent template_id returns 400"""
    note_data = {
        "template_id": str(uuid4()),  # Non-existent template
        "content": {"subjective": {"chief_complaint": "Test"}}
    }

    response = async_db_client.post(
        f"/api/v1/sessions/{sample_session_with_extracted_notes.id}/notes",
        json=note_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 400
    assert "Template not found" in response.json()["detail"]


def test_create_note_with_empty_content_returns_400(
    async_db_client,
    therapist_auth_headers,
    sample_session_with_extracted_notes,
    sample_note_template,
    active_therapist_patient_relationship
):
    """Test creating note with empty content returns 400 (Pydantic validation)"""
    note_data = {
        "template_id": str(sample_note_template.id),
        "content": {}  # Empty content
    }

    response = async_db_client.post(
        f"/api/v1/sessions/{sample_session_with_extracted_notes.id}/notes",
        json=note_data,
        headers=therapist_auth_headers
    )

    # Pydantic validation should reject empty content
    assert response.status_code == 422  # Validation error


# ============================================================================
# List Notes Tests (GET /api/v1/sessions/{session_id}/notes)
# ============================================================================

def test_list_notes_returns_all_notes_for_session(
    async_db_client,
    test_db,
    therapist_auth_headers,
    sample_session_with_extracted_notes,
    sample_note_template,
    active_therapist_patient_relationship
):
    """Test listing notes returns all notes for session"""
    # Create multiple notes
    note1 = SessionNote(
        id=uuid4(),
        session_id=sample_session_with_extracted_notes.id,
        template_id=sample_note_template.id,
        content={"section1": "content1"},
        status="draft"
    )
    note2 = SessionNote(
        id=uuid4(),
        session_id=sample_session_with_extracted_notes.id,
        template_id=sample_note_template.id,
        content={"section2": "content2"},
        status="completed"
    )
    test_db.add_all([note1, note2])
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/sessions/{sample_session_with_extracted_notes.id}/notes",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    note_ids = [note["id"] for note in data]
    assert str(note1.id) in note_ids
    assert str(note2.id) in note_ids


def test_list_notes_ordered_by_created_at_desc(
    async_db_client,
    test_db,
    therapist_auth_headers,
    sample_session_with_extracted_notes,
    sample_note_template,
    active_therapist_patient_relationship
):
    """Test notes are returned ordered by created_at DESC (newest first)"""
    from time import sleep

    # Create notes with slight time delay
    note1 = SessionNote(
        id=uuid4(),
        session_id=sample_session_with_extracted_notes.id,
        template_id=sample_note_template.id,
        content={"older": "note"},
        status="draft",
        created_at=datetime(2024, 1, 1, 10, 0, 0)
    )
    test_db.add(note1)
    test_db.commit()

    note2 = SessionNote(
        id=uuid4(),
        session_id=sample_session_with_extracted_notes.id,
        template_id=sample_note_template.id,
        content={"newer": "note"},
        status="draft",
        created_at=datetime(2024, 1, 1, 12, 0, 0)
    )
    test_db.add(note2)
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/sessions/{sample_session_with_extracted_notes.id}/notes",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Newest first
    assert data[0]["id"] == str(note2.id)
    assert data[1]["id"] == str(note1.id)


def test_list_notes_requires_session_access(
    async_db_client,
    test_db,
    therapist_auth_headers,
    sample_note_template
):
    """Test listing notes requires session access authorization"""
    # Create session for different therapist
    other_patient = Patient(
        id=uuid4(),
        name="Other Patient",
        email="other@test.com",
        therapist_id=uuid4()
    )
    test_db.add(other_patient)
    test_db.commit()

    other_session = TherapySession(
        id=uuid4(),
        patient_id=other_patient.id,
        therapist_id=uuid4(),
        session_date=datetime.utcnow(),
        status="processed"
    )
    test_db.add(other_session)
    test_db.commit()

    response = async_db_client.get(
        f"/api/v1/sessions/{other_session.id}/notes",
        headers=therapist_auth_headers
    )

    # Should fail authorization
    assert response.status_code == 403


# ============================================================================
# Update Note Tests (PATCH /api/v1/notes/{note_id})
# ============================================================================

def test_update_note_allows_partial_content_update(
    async_db_client,
    therapist_auth_headers,
    sample_note,
    active_therapist_patient_relationship
):
    """Test updating note content with partial updates"""
    update_data = {
        "content": {
            "subjective": {
                "chief_complaint": "Updated complaint - severe anxiety",
                "mood": "Very anxious"
            }
        }
    }

    response = async_db_client.patch(
        f"/api/v1/notes/{sample_note.id}",
        json=update_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"]["subjective"]["chief_complaint"] == "Updated complaint - severe anxiety"
    assert data["id"] == str(sample_note.id)


def test_update_note_can_change_status_draft_to_completed(
    async_db_client,
    test_db,
    therapist_auth_headers,
    sample_note,
    active_therapist_patient_relationship
):
    """Test updating note status from draft to completed"""
    assert sample_note.status == "draft"

    update_data = {"status": "completed"}

    response = async_db_client.patch(
        f"/api/v1/notes/{sample_note.id}",
        json=update_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"

    # Verify in database
    test_db.refresh(sample_note)
    assert sample_note.status == "completed"


def test_update_note_can_change_status_completed_to_signed(
    async_db_client,
    test_db,
    therapist_auth_headers,
    sample_note,
    active_therapist_patient_relationship
):
    """Test updating note status from completed to signed"""
    # First set to completed
    sample_note.status = "completed"
    test_db.commit()

    update_data = {"status": "signed"}

    response = async_db_client.patch(
        f"/api/v1/notes/{sample_note.id}",
        json=update_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "signed"


def test_update_note_requires_session_access(
    async_db_client,
    test_db,
    therapist_auth_headers,
    sample_note_template
):
    """Test updating note requires session access (different therapist rejected)"""
    # Create note for different therapist's session
    other_patient = Patient(
        id=uuid4(),
        name="Other Patient",
        email="other@test.com",
        therapist_id=uuid4()
    )
    test_db.add(other_patient)
    test_db.commit()

    other_session = TherapySession(
        id=uuid4(),
        patient_id=other_patient.id,
        therapist_id=uuid4(),
        session_date=datetime.utcnow(),
        status="processed"
    )
    test_db.add(other_session)
    test_db.commit()

    other_note = SessionNote(
        id=uuid4(),
        session_id=other_session.id,
        template_id=sample_note_template.id,
        content={"test": "data"},
        status="draft"
    )
    test_db.add(other_note)
    test_db.commit()

    update_data = {"status": "completed"}

    response = async_db_client.patch(
        f"/api/v1/notes/{other_note.id}",
        json=update_data,
        headers=therapist_auth_headers
    )

    # Should fail authorization
    assert response.status_code == 403


def test_update_note_with_empty_content_returns_400(
    async_db_client,
    therapist_auth_headers,
    sample_note,
    active_therapist_patient_relationship
):
    """Test updating note with empty content returns 400 (Pydantic validation)"""
    update_data = {"content": {}}  # Empty content

    response = async_db_client.patch(
        f"/api/v1/notes/{sample_note.id}",
        json=update_data,
        headers=therapist_auth_headers
    )

    # Pydantic validation should reject empty content
    assert response.status_code == 422  # Validation error


def test_update_note_with_nonexistent_note_id_returns_404(
    async_db_client,
    therapist_auth_headers
):
    """Test updating non-existent note returns 404"""
    update_data = {"status": "completed"}

    response = async_db_client.patch(
        f"/api/v1/notes/{uuid4()}",
        json=update_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 404
    assert "Note not found" in response.json()["detail"]


# ============================================================================
# Authorization Tests
# ============================================================================

def test_create_note_without_auth_returns_401(
    async_db_client,
    sample_session_with_extracted_notes,
    sample_note_template
):
    """Test creating note without authentication returns 401"""
    note_data = {
        "template_id": str(sample_note_template.id),
        "content": {"test": "data"}
    }

    response = async_db_client.post(
        f"/api/v1/sessions/{sample_session_with_extracted_notes.id}/notes",
        json=note_data
    )

    assert response.status_code == 401


def test_list_notes_without_auth_returns_401(
    async_db_client,
    sample_session_with_extracted_notes
):
    """Test listing notes without authentication returns 401"""
    response = async_db_client.get(
        f"/api/v1/sessions/{sample_session_with_extracted_notes.id}/notes"
    )

    assert response.status_code == 401


def test_update_note_without_auth_returns_401(
    async_db_client,
    sample_note
):
    """Test updating note without authentication returns 401"""
    update_data = {"status": "completed"}

    response = async_db_client.patch(
        f"/api/v1/notes/{sample_note.id}",
        json=update_data
    )

    assert response.status_code == 401
