"""
Integration tests for note templates router endpoints.

Tests cover:
- Template listing and filtering
- Template retrieval (system, custom, shared)
- Template creation (validation, RBAC)
- Template updates (ownership, versioning)
- Template deletion (soft delete, RBAC)
- Auto-fill from AI extraction
- Authentication and authorization
- Response structure validation
- Error cases
"""
import pytest
from fastapi import status
from uuid import uuid4
from datetime import datetime
from app.models.db_models import User, NoteTemplate, TherapySession as Session, Patient
from app.models.schemas import UserRole, SessionStatus, TemplateType

TEMPLATES_PREFIX = "/api/v1/templates"
NOTES_PREFIX = "/api/v1/sessions"


# ============================================================================
# Test Fixtures - Sample Template Data
# ============================================================================

@pytest.fixture(scope="function")
def test_system_template(test_db):
    """
    Create a system-provided SOAP template for testing.

    System templates:
    - is_system = True
    - created_by = None
    - Cannot be modified or deleted by users
    - Visible to all users

    Returns:
        NoteTemplate object (SOAP system template)
    """
    template = NoteTemplate(
        name="SOAP Note",
        description="Standard SOAP format for medical documentation",
        template_type=TemplateType.soap.value,
        is_system=True,
        created_by=None,
        is_shared=True,
        structure={
            "sections": [
                {
                    "id": "subjective",
                    "name": "Subjective",
                    "description": "Patient's reported symptoms and concerns",
                    "fields": [
                        {
                            "id": "chief_complaint",
                            "label": "Chief Complaint",
                            "type": "textarea",
                            "required": True,
                            "ai_mapping": "presenting_issues"
                        },
                        {
                            "id": "mood",
                            "label": "Reported Mood",
                            "type": "text",
                            "ai_mapping": "session_mood"
                        }
                    ]
                },
                {
                    "id": "objective",
                    "name": "Objective",
                    "description": "Observable findings",
                    "fields": [
                        {
                            "id": "appearance",
                            "label": "Appearance",
                            "type": "text",
                            "required": False
                        },
                        {
                            "id": "affect",
                            "label": "Affect",
                            "type": "select",
                            "options": ["appropriate", "flat", "labile"],
                            "required": True
                        }
                    ]
                },
                {
                    "id": "assessment",
                    "name": "Assessment",
                    "description": "Clinical assessment",
                    "fields": [
                        {
                            "id": "clinical_impression",
                            "label": "Clinical Impression",
                            "type": "textarea",
                            "required": True
                        }
                    ]
                },
                {
                    "id": "plan",
                    "name": "Plan",
                    "description": "Treatment plan",
                    "fields": [
                        {
                            "id": "interventions",
                            "label": "Interventions",
                            "type": "textarea",
                            "ai_mapping": "strategies"
                        },
                        {
                            "id": "homework",
                            "label": "Homework",
                            "type": "textarea",
                            "ai_mapping": "action_items"
                        }
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
def test_user_template(test_db, therapist_user):
    """
    Create a custom user-created template for testing.

    User templates:
    - is_system = False
    - created_by = therapist user ID
    - Can be modified/deleted by owner
    - Private unless is_shared = True

    Args:
        test_db: Test database session
        therapist_user: Therapist who owns this template

    Returns:
        NoteTemplate object (custom therapist template)
    """
    template = NoteTemplate(
        name="My CBT Session Note",
        description="Custom template for CBT sessions",
        template_type=TemplateType.custom.value,
        is_system=False,
        created_by=therapist_user.id,
        is_shared=False,
        structure={
            "sections": [
                {
                    "id": "presenting_problem",
                    "name": "Presenting Problem",
                    "description": "Current issues",
                    "fields": [
                        {
                            "id": "problem",
                            "label": "Problem Description",
                            "type": "textarea",
                            "required": True
                        }
                    ]
                },
                {
                    "id": "interventions",
                    "name": "CBT Interventions",
                    "description": "Techniques used",
                    "fields": [
                        {
                            "id": "technique",
                            "label": "Technique",
                            "type": "select",
                            "options": ["cognitive restructuring", "exposure", "behavioral activation"],
                            "required": True
                        }
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
def test_shared_template(test_db, therapist_user):
    """
    Create a shared template visible to all therapists in the practice.

    Args:
        test_db: Test database session
        therapist_user: Therapist who created and shared this template

    Returns:
        NoteTemplate object (shared custom template)
    """
    template = NoteTemplate(
        name="Practice-Wide Progress Note",
        description="Shared template for all therapists",
        template_type=TemplateType.progress.value,
        is_system=False,
        created_by=therapist_user.id,
        is_shared=True,
        structure={
            "sections": [
                {
                    "id": "progress",
                    "name": "Progress Summary",
                    "fields": [
                        {
                            "id": "summary",
                            "label": "Summary",
                            "type": "textarea",
                            "required": True
                        }
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
def test_session_with_notes(test_db, therapist_user, sample_patient):
    """
    Create a therapy session with extracted notes for auto-fill testing.

    Args:
        test_db: Test database session
        therapist_user: Therapist conducting the session
        sample_patient: Patient for this session

    Returns:
        Session object with complete extracted_notes
    """
    session = Session(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        duration_seconds=3600,
        audio_filename="test_session.mp3",
        transcript_text="Therapist: How are you? Client: Feeling anxious about work.",
        status=SessionStatus.completed.value,
        extracted_notes={
            "key_topics": ["Work stress", "Anxiety"],
            "topic_summary": "Client discussed ongoing anxiety related to work deadlines.",
            "strategies": [
                {
                    "name": "Deep breathing",
                    "category": "relaxation",
                    "status": "taught",
                    "context": "For managing work-related anxiety"
                }
            ],
            "emotional_themes": ["Anxiety", "Stress"],
            "action_items": [
                {
                    "task": "Practice breathing exercises daily",
                    "category": "homework",
                    "details": "5 minutes morning and evening"
                }
            ],
            "session_mood": "anxious",
            "mood_trajectory": "stable",
            "therapist_notes": "Client demonstrated good insight into triggers. Responded well to breathing exercise instruction.",
            "patient_summary": "You're making progress in identifying your anxiety triggers."
        }
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session


@pytest.fixture(scope="function")
def second_therapist_with_template(test_db):
    """
    Create a second therapist with their own private template for authorization testing.

    Returns:
        Dict with:
        - therapist: User object (second therapist)
        - template: NoteTemplate object (private template)
    """
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

    template = NoteTemplate(
        name="Other Therapist Template",
        description="Private template",
        template_type=TemplateType.custom.value,
        is_system=False,
        created_by=therapist2.id,
        is_shared=False,
        structure={
            "sections": [
                {
                    "id": "notes",
                    "name": "Notes",
                    "fields": [
                        {"id": "content", "label": "Content", "type": "textarea", "required": True}
                    ]
                }
            ]
        }
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)

    return {
        "therapist": therapist2,
        "template": template
    }


# ============================================================================
# Test Class 1: TestListTemplates
# ============================================================================

class TestListTemplates:
    """Test GET /templates endpoint"""

    def test_list_returns_system_templates(
        self,
        client,
        therapist_auth_headers,
        test_system_template
    ):
        """Test that all users can see system templates"""
        response = client.get(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "templates" in data
        assert isinstance(data["templates"], list)

        # Verify system template is included
        template_ids = [t["id"] for t in data["templates"]]
        assert str(test_system_template.id) in template_ids

        # Verify system template has correct fields
        system_template = next(t for t in data["templates"] if t["id"] == str(test_system_template.id))
        assert system_template["name"] == "SOAP Note"
        assert system_template["is_system"] is True
        assert system_template["template_type"] == "soap"

    def test_list_returns_own_templates(
        self,
        client,
        therapist_auth_headers,
        test_user_template
    ):
        """Test that user sees their own custom templates"""
        response = client.get(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify user's template is included
        template_ids = [t["id"] for t in data["templates"]]
        assert str(test_user_template.id) in template_ids

        # Verify template details
        user_template = next(t for t in data["templates"] if t["id"] == str(test_user_template.id))
        assert user_template["name"] == "My CBT Session Note"
        assert user_template["is_system"] is False

    def test_list_filters_by_type(
        self,
        client,
        therapist_auth_headers,
        test_system_template,
        test_user_template
    ):
        """Test filtering templates by template_type"""
        response = client.get(
            f"{TEMPLATES_PREFIX}?template_type=soap",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should only include SOAP templates
        for template in data["templates"]:
            assert template["template_type"] == "soap"

        # SOAP template should be included
        template_ids = [t["id"] for t in data["templates"]]
        assert str(test_system_template.id) in template_ids

        # Custom template (not SOAP) should be excluded
        assert str(test_user_template.id) not in template_ids

    def test_list_includes_shared(
        self,
        client,
        therapist_auth_headers,
        test_shared_template,
        second_therapist_with_template
    ):
        """Test that shared templates are visible to all therapists"""
        response = client.get(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        template_ids = [t["id"] for t in data["templates"]]

        # Shared template should be visible
        assert str(test_shared_template.id) in template_ids

        # Other therapist's PRIVATE template should NOT be visible
        assert str(second_therapist_with_template["template"].id) not in template_ids

    def test_list_requires_auth(self, client):
        """Test that listing templates requires authentication"""
        response = client.get(f"{TEMPLATES_PREFIX}")

        assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Test Class 2: TestGetTemplate
# ============================================================================

class TestGetTemplate:
    """Test GET /templates/{template_id} endpoint"""

    def test_get_system_template_success(
        self,
        client,
        therapist_auth_headers,
        test_system_template
    ):
        """Test that any user can retrieve system templates"""
        response = client.get(
            f"{TEMPLATES_PREFIX}/{test_system_template.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert data["id"] == str(test_system_template.id)
        assert data["name"] == "SOAP Note"
        assert data["is_system"] is True
        assert "structure" in data
        assert "sections" in data["structure"]

        # Verify structure details
        sections = data["structure"]["sections"]
        assert len(sections) == 4
        assert sections[0]["id"] == "subjective"

    def test_get_own_template_success(
        self,
        client,
        therapist_auth_headers,
        test_user_template
    ):
        """Test that owner can retrieve their own templates"""
        response = client.get(
            f"{TEMPLATES_PREFIX}/{test_user_template.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == str(test_user_template.id)
        assert data["name"] == "My CBT Session Note"
        assert data["is_system"] is False
        assert "structure" in data

    def test_get_shared_template_success(
        self,
        client,
        patient_auth_headers,
        test_shared_template
    ):
        """Test that shared templates are visible to all users"""
        response = client.get(
            f"{TEMPLATES_PREFIX}/{test_shared_template.id}",
            headers=patient_auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == str(test_shared_template.id)
        assert data["is_shared"] is True

    def test_get_private_template_fails(
        self,
        client,
        therapist_auth_headers,
        second_therapist_with_template
    ):
        """Test that non-owners cannot access private templates"""
        private_template = second_therapist_with_template["template"]

        response = client.get(
            f"{TEMPLATES_PREFIX}/{private_template.id}",
            headers=therapist_auth_headers
        )

        # Should return 403 Forbidden (not authorized to view)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_nonexistent_template(
        self,
        client,
        therapist_auth_headers
    ):
        """Test retrieving non-existent template returns 404"""
        nonexistent_id = uuid4()

        response = client.get(
            f"{TEMPLATES_PREFIX}/{nonexistent_id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# ============================================================================
# Test Class 3: TestCreateTemplate
# ============================================================================

class TestCreateTemplate:
    """Test POST /templates endpoint"""

    def test_create_template_success(
        self,
        client,
        therapist_auth_headers
    ):
        """Test that therapist can successfully create a custom template"""
        template_data = {
            "name": "New Custom Template",
            "description": "Test template creation",
            "template_type": "custom",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "Section 1",
                        "description": "First section",
                        "fields": [
                            {
                                "id": "field1",
                                "label": "Field 1",
                                "type": "textarea",
                                "required": True
                            }
                        ]
                    }
                ]
            }
        }

        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=template_data
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify created template
        assert data["name"] == "New Custom Template"
        assert data["is_system"] is False
        assert "id" in data
        assert "created_by" in data
        assert "created_at" in data

    def test_create_requires_therapist_role(
        self,
        client,
        patient_auth_headers
    ):
        """Test that patients cannot create templates"""
        template_data = {
            "name": "Patient Template",
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "s1",
                        "name": "Section",
                        "fields": [
                            {"id": "f1", "label": "Field", "type": "text", "required": True}
                        ]
                    }
                ]
            }
        }

        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=patient_auth_headers,
            json=template_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "therapist" in response.json()["detail"].lower()

    def test_create_validates_structure(
        self,
        client,
        therapist_auth_headers
    ):
        """Test that invalid template structure returns 400"""
        # Missing required 'sections' field
        invalid_template = {
            "name": "Invalid Template",
            "template_type": "custom",
            "structure": {}
        }

        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_template
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_sets_metadata(
        self,
        client,
        test_db,
        therapist_auth_headers,
        therapist_user
    ):
        """Test that created_by and is_system are set correctly"""
        template_data = {
            "name": "Metadata Test Template",
            "template_type": "custom",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "s1",
                        "name": "Section",
                        "fields": [
                            {"id": "f1", "label": "Field", "type": "text", "required": True}
                        ]
                    }
                ]
            }
        }

        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=template_data
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # Verify metadata
        assert data["is_system"] is False
        assert data["created_by"] == str(therapist_user.id)
        assert "created_at" in data
        assert "updated_at" in data


# ============================================================================
# Test Class 4: TestUpdateTemplate
# ============================================================================

class TestUpdateTemplate:
    """Test PUT/PATCH /templates/{template_id} endpoint"""

    def test_update_own_template(
        self,
        client,
        therapist_auth_headers,
        test_user_template
    ):
        """Test that owner can update their own template"""
        update_data = {
            "name": "Updated Template Name",
            "description": "Updated description"
        }

        response = client.patch(
            f"{TEMPLATES_PREFIX}/{test_user_template.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["name"] == "Updated Template Name"
        assert data["description"] == "Updated description"

    def test_update_non_owner_fails(
        self,
        client,
        therapist_auth_headers,
        second_therapist_with_template
    ):
        """Test that non-owners cannot update templates"""
        other_template = second_therapist_with_template["template"]

        update_data = {
            "name": "Trying to update someone else's template"
        }

        response = client.patch(
            f"{TEMPLATES_PREFIX}/{other_template.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_system_template_fails(
        self,
        client,
        therapist_auth_headers,
        test_system_template
    ):
        """Test that system templates cannot be modified"""
        update_data = {
            "name": "Trying to update system template"
        }

        response = client.patch(
            f"{TEMPLATES_PREFIX}/{test_system_template.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "system" in response.json()["detail"].lower()

    def test_partial_update_works(
        self,
        client,
        therapist_auth_headers,
        test_user_template
    ):
        """Test that PATCH with subset of fields works"""
        # Only update is_shared, leave other fields unchanged
        update_data = {
            "is_shared": True
        }

        response = client.patch(
            f"{TEMPLATES_PREFIX}/{test_user_template.id}",
            headers=therapist_auth_headers,
            json=update_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # is_shared should be updated
        assert data["is_shared"] is True

        # Other fields should remain unchanged
        assert data["name"] == "My CBT Session Note"
        assert data["template_type"] == "custom"


# ============================================================================
# Test Class 5: TestDeleteTemplate
# ============================================================================

class TestDeleteTemplate:
    """Test DELETE /templates/{template_id} endpoint"""

    def test_delete_own_template(
        self,
        client,
        therapist_auth_headers,
        test_user_template
    ):
        """Test that owner can delete their own template"""
        response = client.delete(
            f"{TEMPLATES_PREFIX}/{test_user_template.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify template is no longer accessible
        get_response = client.get(
            f"{TEMPLATES_PREFIX}/{test_user_template.id}",
            headers=therapist_auth_headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_non_owner_fails(
        self,
        client,
        therapist_auth_headers,
        second_therapist_with_template
    ):
        """Test that non-owners cannot delete templates"""
        other_template = second_therapist_with_template["template"]

        response = client.delete(
            f"{TEMPLATES_PREFIX}/{other_template.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_system_template_fails(
        self,
        client,
        therapist_auth_headers,
        test_system_template
    ):
        """Test that system templates cannot be deleted"""
        response = client.delete(
            f"{TEMPLATES_PREFIX}/{test_system_template.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "system" in response.json()["detail"].lower()


# ============================================================================
# Test Class 6: TestAutoFill (for notes router)
# ============================================================================

class TestAutoFill:
    """Test POST /sessions/{session_id}/notes/auto-fill endpoint"""

    def test_autofill_soap_success(
        self,
        client,
        therapist_auth_headers,
        test_system_template,
        test_session_with_notes
    ):
        """Test auto-fill returns filled SOAP template from AI extraction"""
        request_data = {
            "template_id": str(test_system_template.id)
        }

        response = client.post(
            f"{NOTES_PREFIX}/{test_session_with_notes.id}/notes/auto-fill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify response structure
        assert "auto_filled_content" in data
        assert "confidence_scores" in data
        assert "missing_fields" in data

        # Verify auto-filled content has expected sections
        content = data["auto_filled_content"]
        assert "subjective" in content or "assessment" in content or "plan" in content

    def test_autofill_requires_extracted_notes(
        self,
        client,
        therapist_auth_headers,
        test_system_template,
        sample_session
    ):
        """Test auto-fill fails if session hasn't been processed"""
        # sample_session has no extracted_notes
        request_data = {
            "template_id": str(test_system_template.id)
        }

        response = client.post(
            f"{NOTES_PREFIX}/{sample_session.id}/notes/auto-fill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "extracted" in response.json()["detail"].lower() or "processed" in response.json()["detail"].lower()

    def test_autofill_includes_confidence_scores(
        self,
        client,
        therapist_auth_headers,
        test_system_template,
        test_session_with_notes
    ):
        """Test auto-fill response includes confidence scores for each field"""
        request_data = {
            "template_id": str(test_system_template.id)
        }

        response = client.post(
            f"{NOTES_PREFIX}/{test_session_with_notes.id}/notes/auto-fill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify confidence_scores exist
        assert "confidence_scores" in data
        assert isinstance(data["confidence_scores"], dict)

        # Scores should be floats between 0 and 1
        for field_key, score in data["confidence_scores"].items():
            assert isinstance(score, (int, float))
            assert 0.0 <= score <= 1.0

    def test_autofill_identifies_missing_fields(
        self,
        client,
        therapist_auth_headers,
        test_system_template,
        test_session_with_notes
    ):
        """Test auto-fill response lists fields that couldn't be filled"""
        request_data = {
            "template_id": str(test_system_template.id)
        }

        response = client.post(
            f"{NOTES_PREFIX}/{test_session_with_notes.id}/notes/auto-fill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify missing_fields is a list
        assert "missing_fields" in data
        assert isinstance(data["missing_fields"], list)

        # If there are missing fields, they should be strings
        for field_key in data["missing_fields"]:
            assert isinstance(field_key, str)


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================

class TestTemplatesEdgeCases:
    """Test edge cases and error scenarios"""

    def test_invalid_auth_token(self, client):
        """Test all endpoints reject invalid authentication tokens"""
        invalid_headers = {"Authorization": "Bearer invalid-token-12345"}

        endpoints = [
            (f"{TEMPLATES_PREFIX}", "get"),
            (f"{TEMPLATES_PREFIX}/{uuid4()}", "get"),
            (f"{TEMPLATES_PREFIX}", "post"),
            (f"{TEMPLATES_PREFIX}/{uuid4()}", "patch"),
            (f"{TEMPLATES_PREFIX}/{uuid4()}", "delete"),
        ]

        for endpoint, method in endpoints:
            if method == "get":
                response = client.get(endpoint, headers=invalid_headers)
            elif method == "post":
                response = client.post(endpoint, headers=invalid_headers, json={})
            elif method == "patch":
                response = client.patch(endpoint, headers=invalid_headers, json={})
            elif method == "delete":
                response = client.delete(endpoint, headers=invalid_headers)

            assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_malformed_template_id(self, client, therapist_auth_headers):
        """Test get template with malformed UUID"""
        response = client.get(
            f"{TEMPLATES_PREFIX}/not-a-uuid",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_template_missing_required_fields(
        self,
        client,
        therapist_auth_headers
    ):
        """Test creating template without required fields fails"""
        # Missing 'name' field
        incomplete_data = {
            "template_type": "custom",
            "structure": {
                "sections": [
                    {
                        "id": "s1",
                        "name": "Section",
                        "fields": [
                            {"id": "f1", "label": "Field", "type": "text", "required": True}
                        ]
                    }
                ]
            }
        }

        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=incomplete_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_template_empty_sections(
        self,
        client,
        therapist_auth_headers
    ):
        """Test creating template with empty sections array fails"""
        invalid_data = {
            "name": "Empty Template",
            "template_type": "custom",
            "structure": {
                "sections": []
            }
        }

        response = client.post(
            f"{TEMPLATES_PREFIX}",
            headers=therapist_auth_headers,
            json=invalid_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_filter_by_invalid_template_type(
        self,
        client,
        therapist_auth_headers
    ):
        """Test filtering by invalid template_type"""
        response = client.get(
            f"{TEMPLATES_PREFIX}?template_type=invalid_type",
            headers=therapist_auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_autofill_nonexistent_session(
        self,
        client,
        therapist_auth_headers,
        test_system_template
    ):
        """Test auto-fill with non-existent session ID"""
        nonexistent_session_id = uuid4()

        request_data = {
            "template_id": str(test_system_template.id)
        }

        response = client.post(
            f"{NOTES_PREFIX}/{nonexistent_session_id}/notes/auto-fill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_autofill_nonexistent_template(
        self,
        client,
        therapist_auth_headers,
        test_session_with_notes
    ):
        """Test auto-fill with non-existent template ID"""
        nonexistent_template_id = uuid4()

        request_data = {
            "template_id": str(nonexistent_template_id)
        }

        response = client.post(
            f"{NOTES_PREFIX}/{test_session_with_notes.id}/notes/auto-fill",
            headers=therapist_auth_headers,
            json=request_data
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
