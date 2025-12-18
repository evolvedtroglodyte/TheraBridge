"""
Comprehensive integration tests for templates router CRUD operations.

Tests all template endpoints:
- GET /api/v1/templates (list with filters)
- GET /api/v1/templates/{id} (single template)
- POST /api/v1/templates (create custom template)
- PATCH /api/v1/templates/{id} (update template)
- DELETE /api/v1/templates/{id} (delete template)

Coverage:
- Success cases for all CRUD operations
- Error cases (404, 403, 400)
- Authorization/ownership validation
- Template structure validation
- Filtering and query parameters
- System template protection
"""
import pytest
from uuid import uuid4, UUID
from datetime import datetime

from app.models.db_models import NoteTemplate, User
from app.models.schemas import TemplateType, UserRole


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def system_soap_template(test_db):
    """Create a system SOAP template"""
    template = NoteTemplate(
        id=uuid4(),
        name="SOAP Note (System)",
        description="Standard SOAP note template",
        template_type=TemplateType.soap.value,
        is_system=True,
        is_shared=False,
        created_by=None,
        structure={
            "sections": [
                {
                    "id": "subjective",
                    "name": "Subjective",
                    "description": "Patient's reported experience",
                    "fields": [
                        {
                            "id": "chief_complaint",
                            "label": "Chief Complaint",
                            "type": "textarea",
                            "required": True,
                            "ai_mapping": "topic_summary"
                        }
                    ]
                },
                {
                    "id": "objective",
                    "name": "Objective",
                    "description": "Clinician observations",
                    "fields": [
                        {
                            "id": "mood",
                            "label": "Observed Mood",
                            "type": "select",
                            "required": True,
                            "options": ["anxious", "neutral", "positive"],
                            "ai_mapping": "session_mood"
                        }
                    ]
                },
                {
                    "id": "assessment",
                    "name": "Assessment",
                    "description": "Clinical assessment",
                    "fields": [
                        {
                            "id": "diagnosis",
                            "label": "Diagnosis",
                            "type": "text",
                            "required": False
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
                            "required": True
                        }
                    ]
                }
            ]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)
    return template


@pytest.fixture
def system_dap_template(test_db):
    """Create a system DAP template"""
    template = NoteTemplate(
        id=uuid4(),
        name="DAP Note (System)",
        description="Data, Assessment, Plan template",
        template_type=TemplateType.dap.value,
        is_system=True,
        is_shared=False,
        created_by=None,
        structure={
            "sections": [
                {
                    "id": "data",
                    "name": "Data",
                    "description": "Objective and subjective data",
                    "fields": [
                        {
                            "id": "observations",
                            "label": "Observations",
                            "type": "textarea",
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
                            "id": "progress",
                            "label": "Progress",
                            "type": "text",
                            "required": True
                        }
                    ]
                },
                {
                    "id": "plan",
                    "name": "Plan",
                    "description": "Next steps",
                    "fields": [
                        {
                            "id": "next_session",
                            "label": "Next Session Plan",
                            "type": "textarea",
                            "required": True
                        }
                    ]
                }
            ]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)
    return template


@pytest.fixture
def therapist_custom_template(test_db, therapist_user):
    """Create a custom template owned by therapist_user"""
    template = NoteTemplate(
        id=uuid4(),
        name="My Custom SOAP",
        description="Customized SOAP for anxiety treatment",
        template_type=TemplateType.custom.value,
        is_system=False,
        is_shared=False,
        created_by=therapist_user.id,
        structure={
            "sections": [
                {
                    "id": "anxiety_check",
                    "name": "Anxiety Assessment",
                    "description": "Anxiety-specific questions",
                    "fields": [
                        {
                            "id": "anxiety_level",
                            "label": "Anxiety Level (1-10)",
                            "type": "scale",
                            "required": True
                        }
                    ]
                }
            ]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)
    return template


@pytest.fixture
def shared_template(test_db, therapist_user):
    """Create a shared template from another therapist"""
    # Create another therapist
    other_therapist = User(
        email="other.therapist@test.com",
        hashed_password="hashedpass",
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

    template = NoteTemplate(
        id=uuid4(),
        name="Shared BIRP Template",
        description="Shared template from another therapist",
        template_type=TemplateType.birp.value,
        is_system=False,
        is_shared=True,
        created_by=other_therapist.id,
        structure={
            "sections": [
                {
                    "id": "behavior",
                    "name": "Behavior",
                    "description": "Observed behaviors",
                    "fields": [
                        {
                            "id": "behaviors",
                            "label": "Behaviors",
                            "type": "textarea",
                            "required": True
                        }
                    ]
                }
            ]
        },
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)
    return template


# ============================================================================
# List Templates Tests
# ============================================================================

class TestListTemplates:
    """Test GET /api/v1/templates"""

    def test_list_templates_returns_system_templates_for_any_user(
        self, async_db_client, test_db, system_soap_template, system_dap_template, therapist_auth_headers
    ):
        """List templates returns all system templates for any authenticated user"""
        response = async_db_client.get("/api/v1/templates", headers=therapist_auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)
        assert len(data) >= 2

        # Verify system templates are present
        template_names = [t["name"] for t in data]
        assert "SOAP Note (System)" in template_names
        assert "DAP Note (System)" in template_names

        # Verify all returned templates have required fields
        for template in data:
            assert "id" in template
            assert "name" in template
            assert "template_type" in template
            assert "is_system" in template
            assert "section_count" in template
            assert "created_at" in template

    def test_list_templates_includes_user_custom_templates(
        self, async_db_client, test_db, therapist_user, therapist_custom_template, system_soap_template, therapist_auth_headers
    ):
        """List templates includes user's custom templates"""
        response = async_db_client.get("/api/v1/templates", headers=therapist_auth_headers)

        assert response.status_code == 200
        data = response.json()

        template_names = [t["name"] for t in data]
        assert "My Custom SOAP" in template_names

        # Find custom template in response
        custom_template = next(t for t in data if t["name"] == "My Custom SOAP")
        assert custom_template["is_system"] is False
        assert custom_template["template_type"] == "custom"

    def test_list_templates_includes_shared_templates_by_default(
        self, async_db_client, test_db, shared_template, system_soap_template, therapist_auth_headers
    ):
        """List templates includes shared templates from other users by default"""
        response = async_db_client.get("/api/v1/templates", headers=therapist_auth_headers)

        assert response.status_code == 200
        data = response.json()

        template_names = [t["name"] for t in data]
        assert "Shared BIRP Template" in template_names

        # Verify shared template properties
        shared = next(t for t in data if t["name"] == "Shared BIRP Template")
        assert shared["is_shared"] is True
        assert shared["is_system"] is False

    def test_list_templates_excludes_shared_when_requested(
        self, async_db_client, test_db, shared_template, system_soap_template, therapist_custom_template, therapist_auth_headers
    ):
        """List templates excludes shared templates when include_shared=false"""
        response = async_db_client.get("/api/v1/templates?include_shared=false", headers=therapist_auth_headers)

        assert response.status_code == 200
        data = response.json()

        template_names = [t["name"] for t in data]
        # Should NOT include shared template
        assert "Shared BIRP Template" not in template_names
        # Should still include system and user's own
        assert "SOAP Note (System)" in template_names
        assert "My Custom SOAP" in template_names

    def test_list_templates_filter_by_type(
        self, async_db_client, test_db, system_soap_template, system_dap_template, therapist_custom_template, therapist_auth_headers
    ):
        """List templates with template_type filter"""
        response = async_db_client.get(f"/api/v1/templates?template_type={TemplateType.soap.value}", headers=therapist_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Should only return SOAP templates
        assert all(t["template_type"] == TemplateType.soap.value for t in data)
        template_names = [t["name"] for t in data]
        assert "SOAP Note (System)" in template_names
        assert "DAP Note (System)" not in template_names

    def test_list_templates_sorted_system_first_then_recent(
        self, async_db_client, test_db, system_soap_template, therapist_custom_template, therapist_auth_headers
    ):
        """Templates are sorted with system templates first, then by creation date"""
        response = async_db_client.get("/api/v1/templates", headers=therapist_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # System templates should come before custom templates
        system_indices = [i for i, t in enumerate(data) if t["is_system"]]
        custom_indices = [i for i, t in enumerate(data) if not t["is_system"]]

        if system_indices and custom_indices:
            assert max(system_indices) < min(custom_indices), \
                "System templates should appear before custom templates"

    def test_list_templates_section_count_calculated_correctly(
        self, async_db_client, test_db, system_soap_template, therapist_auth_headers
    ):
        """section_count is correctly calculated from structure"""
        response = async_db_client.get("/api/v1/templates", headers=therapist_auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Find SOAP template
        soap = next(t for t in data if t["name"] == "SOAP Note (System)")
        assert soap["section_count"] == 4  # Subjective, Objective, Assessment, Plan


# ============================================================================
# Get Single Template Tests
# ============================================================================

class TestGetTemplate:
    """Test GET /api/v1/templates/{template_id}"""

    def test_get_system_template_succeeds_for_any_user(
        self, async_db_client, test_db, system_soap_template, therapist_auth_headers
    ):
        """Any user can access system templates"""
        response = async_db_client.get(f"/api/v1/templates/{system_soap_template.id}", headers=therapist_auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(system_soap_template.id)
        assert data["name"] == "SOAP Note (System)"
        assert data["is_system"] is True
        assert "structure" in data
        assert "sections" in data["structure"]
        assert len(data["structure"]["sections"]) == 4

    def test_get_user_own_template_succeeds(
        self, async_db_client, test_db, therapist_user, therapist_custom_template, therapist_auth_headers
    ):
        """User can access their own custom templates"""
        response = async_db_client.get(f"/api/v1/templates/{therapist_custom_template.id}", headers=therapist_auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(therapist_custom_template.id)
        assert data["name"] == "My Custom SOAP"
        assert data["is_system"] is False
        assert data["created_by"] == str(therapist_user.id)

    def test_get_shared_template_succeeds(
        self, async_db_client, test_db, shared_template, therapist_auth_headers
    ):
        """User can access shared templates from other users"""
        response = async_db_client.get(f"/api/v1/templates/{shared_template.id}", headers=therapist_auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(shared_template.id)
        assert data["is_shared"] is True

    def test_get_template_not_found(self, async_db_client, test_db, therapist_auth_headers):
        """Getting non-existent template returns 404"""
        fake_template_id = uuid4()
        response = async_db_client.get(f"/api/v1/templates/{fake_template_id}", headers=therapist_auth_headers)

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_template_includes_complete_structure(
        self, async_db_client, test_db, system_soap_template, therapist_auth_headers
    ):
        """Template response includes complete structure with all fields"""
        response = async_db_client.get(f"/api/v1/templates/{system_soap_template.id}", headers=therapist_auth_headers)

        assert response.status_code == 200
        data = response.json()

        structure = data["structure"]
        assert "sections" in structure

        # Verify section structure
        for section in structure["sections"]:
            assert "id" in section
            assert "name" in section
            assert "fields" in section

            # Verify field structure
            for field in section["fields"]:
                assert "id" in field
                assert "label" in field
                assert "type" in field
                assert "required" in field

    def test_get_template_invalid_uuid(self, async_db_client, test_db, therapist_auth_headers):
        """Getting template with invalid UUID format returns 422"""
        response = async_db_client.get("/api/v1/templates/not-a-uuid", headers=therapist_auth_headers)

        assert response.status_code == 422


# ============================================================================
# Create Template Tests
# ============================================================================

class TestCreateTemplate:
    """Test POST /api/v1/templates"""

    def test_create_custom_template_requires_therapist_role(
        self, async_db_client, test_db, patient_user, patient_auth_headers
    ):
        """Creating template requires therapist role (403 for patients)"""
        template_data = {
            "name": "Patient Template",
            "description": "This should fail",
            "template_type": "custom",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "Section 1",
                        "fields": [
                            {
                                "id": "field1",
                                "label": "Field 1",
                                "type": "text",
                                "required": False
                            }
                        ]
                    }
                ]
            }
        }

        response = async_db_client.post(
            "/api/v1/templates",
            json=template_data,
            headers=patient_auth_headers
        )

        assert response.status_code == 403

    def test_create_template_success(
        self, async_db_client, test_db, therapist_user, therapist_auth_headers
    ):
        """Successfully create a custom template as therapist"""
        template_data = {
            "name": "My New SOAP Template",
            "description": "Custom SOAP for trauma work",
            "template_type": "soap",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "subjective",
                        "name": "Subjective",
                        "description": "Patient report",
                        "fields": [
                            {
                                "id": "trauma_symptoms",
                                "label": "Trauma Symptoms",
                                "type": "textarea",
                                "required": True,
                                "ai_mapping": "topic_summary"
                            },
                            {
                                "id": "flashbacks",
                                "label": "Flashback Frequency",
                                "type": "select",
                                "required": True,
                                "options": ["None", "Rare", "Frequent", "Daily"]
                            }
                        ]
                    },
                    {
                        "id": "assessment",
                        "name": "Assessment",
                        "fields": [
                            {
                                "id": "ptsd_severity",
                                "label": "PTSD Severity (1-10)",
                                "type": "scale",
                                "required": True
                            }
                        ]
                    }
                ]
            }
        }

        response = async_db_client.post(
            "/api/v1/templates",
            json=template_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["name"] == "My New SOAP Template"
        assert data["template_type"] == "soap"
        assert data["is_system"] is False
        assert data["is_shared"] is False
        assert data["created_by"] == str(therapist_user.id)
        assert "structure" in data
        assert len(data["structure"]["sections"]) == 2

    def test_create_template_validates_empty_sections(
        self, async_db_client, test_db, therapist_auth_headers
    ):
        """Creating template with empty sections returns 400"""
        template_data = {
            "name": "Invalid Template",
            "template_type": "custom",
            "is_shared": False,
            "structure": {
                "sections": []  # Empty sections
            }
        }

        response = async_db_client.post(
            "/api/v1/templates",
            json=template_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == 400
        assert "at least one section" in response.json()["detail"].lower()

    def test_create_template_validates_duplicate_section_ids(
        self, async_db_client, test_db, therapist_auth_headers
    ):
        """Creating template with duplicate section IDs returns 400"""
        template_data = {
            "name": "Invalid Template",
            "template_type": "custom",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "duplicate",
                        "name": "Section 1",
                        "fields": [
                            {"id": "field1", "label": "Field 1", "type": "text", "required": False}
                        ]
                    },
                    {
                        "id": "duplicate",  # Duplicate ID
                        "name": "Section 2",
                        "fields": [
                            {"id": "field2", "label": "Field 2", "type": "text", "required": False}
                        ]
                    }
                ]
            }
        }

        response = async_db_client.post(
            "/api/v1/templates",
            json=template_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == 400
        assert "unique" in response.json()["detail"].lower()

    def test_create_template_validates_section_has_fields(
        self, async_db_client, test_db, therapist_auth_headers
    ):
        """Creating template with section without fields returns 400"""
        template_data = {
            "name": "Invalid Template",
            "template_type": "custom",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "Empty Section",
                        "fields": []  # No fields
                    }
                ]
            }
        }

        response = async_db_client.post(
            "/api/v1/templates",
            json=template_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == 400
        assert "at least one field" in response.json()["detail"].lower()

    def test_create_template_validates_select_field_has_options(
        self, async_db_client, test_db, therapist_auth_headers
    ):
        """Select/multiselect fields must have options"""
        template_data = {
            "name": "Invalid Template",
            "template_type": "custom",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "Section 1",
                        "fields": [
                            {
                                "id": "mood",
                                "label": "Mood",
                                "type": "select",
                                "required": True,
                                "options": []  # Empty options
                            }
                        ]
                    }
                ]
            }
        }

        response = async_db_client.post(
            "/api/v1/templates",
            json=template_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == 400
        assert "option" in response.json()["detail"].lower()

    def test_create_template_multiselect_requires_options(
        self, async_db_client, test_db, therapist_auth_headers
    ):
        """Multiselect fields require options"""
        template_data = {
            "name": "Invalid Template",
            "template_type": "custom",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "section1",
                        "name": "Section 1",
                        "fields": [
                            {
                                "id": "symptoms",
                                "label": "Symptoms",
                                "type": "multiselect",
                                "required": True
                                # Missing options
                            }
                        ]
                    }
                ]
            }
        }

        response = async_db_client.post(
            "/api/v1/templates",
            json=template_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == 400


# ============================================================================
# Update Template Tests
# ============================================================================

class TestUpdateTemplate:
    """Test PATCH /api/v1/templates/{template_id}"""

    def test_update_template_requires_ownership(
        self, async_db_client, test_db, shared_template, therapist_auth_headers
    ):
        """User cannot update templates they don't own"""
        updates = {
            "name": "Trying to Update Someone Else's Template"
        }

        response = async_db_client.patch(
            f"/api/v1/templates/{shared_template.id}",
            json=updates,
            headers=therapist_auth_headers
        )

        assert response.status_code == 403
        assert "not the owner" in response.json()["detail"].lower()

    def test_update_system_template_returns_403(
        self, async_db_client, test_db, system_soap_template, therapist_auth_headers
    ):
        """System templates cannot be updated"""
        updates = {
            "name": "Modified System Template"
        }

        response = async_db_client.patch(
            f"/api/v1/templates/{system_soap_template.id}",
            json=updates,
            headers=therapist_auth_headers
        )

        assert response.status_code == 403
        assert "system template" in response.json()["detail"].lower()

    def test_update_template_name_success(
        self, async_db_client, test_db, therapist_custom_template, therapist_auth_headers
    ):
        """Successfully update template name"""
        updates = {
            "name": "Updated Template Name"
        }

        response = async_db_client.patch(
            f"/api/v1/templates/{therapist_custom_template.id}",
            json=updates,
            headers=therapist_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(therapist_custom_template.id)
        assert data["name"] == "Updated Template Name"
        # Other fields unchanged
        assert data["description"] == therapist_custom_template.description

    def test_update_template_sharing_status(
        self, async_db_client, test_db, therapist_custom_template, therapist_auth_headers
    ):
        """Successfully update template sharing status"""
        updates = {
            "is_shared": True
        }

        response = async_db_client.patch(
            f"/api/v1/templates/{therapist_custom_template.id}",
            json=updates,
            headers=therapist_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_shared"] is True

    def test_update_template_structure(
        self, async_db_client, test_db, therapist_custom_template, therapist_auth_headers
    ):
        """Successfully update template structure"""
        updates = {
            "structure": {
                "sections": [
                    {
                        "id": "new_section",
                        "name": "New Section",
                        "description": "Updated structure",
                        "fields": [
                            {
                                "id": "new_field",
                                "label": "New Field",
                                "type": "text",
                                "required": True
                            }
                        ]
                    }
                ]
            }
        }

        response = async_db_client.patch(
            f"/api/v1/templates/{therapist_custom_template.id}",
            json=updates,
            headers=therapist_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["structure"]["sections"]) == 1
        assert data["structure"]["sections"][0]["id"] == "new_section"

    def test_update_template_partial_updates_allowed(
        self, async_db_client, test_db, therapist_custom_template, therapist_auth_headers
    ):
        """Partial updates work correctly (only provided fields updated)"""
        original_name = therapist_custom_template.name

        updates = {
            "description": "Updated description only"
        }

        response = async_db_client.patch(
            f"/api/v1/templates/{therapist_custom_template.id}",
            json=updates,
            headers=therapist_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Description updated
        assert data["description"] == "Updated description only"
        # Name unchanged
        assert data["name"] == original_name

    def test_update_template_validates_structure(
        self, async_db_client, test_db, therapist_custom_template, therapist_auth_headers
    ):
        """Update validates structure (e.g., empty sections)"""
        updates = {
            "structure": {
                "sections": []  # Invalid
            }
        }

        response = async_db_client.patch(
            f"/api/v1/templates/{therapist_custom_template.id}",
            json=updates,
            headers=therapist_auth_headers
        )

        assert response.status_code == 400

    def test_update_template_not_found(
        self, async_db_client, test_db, therapist_auth_headers
    ):
        """Updating non-existent template returns 404"""
        fake_id = uuid4()
        updates = {
            "name": "Updated Name"
        }

        response = async_db_client.patch(
            f"/api/v1/templates/{fake_id}",
            json=updates,
            headers=therapist_auth_headers
        )

        assert response.status_code == 404


# ============================================================================
# Delete Template Tests
# ============================================================================

class TestDeleteTemplate:
    """Test DELETE /api/v1/templates/{template_id}"""

    def test_delete_template_requires_ownership(
        self, async_db_client, test_db, shared_template, therapist_auth_headers
    ):
        """User cannot delete templates they don't own"""
        response = async_db_client.delete(
            f"/api/v1/templates/{shared_template.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == 403
        assert "not the owner" in response.json()["detail"].lower()

    def test_delete_system_template_returns_403(
        self, async_db_client, test_db, system_soap_template, therapist_auth_headers
    ):
        """System templates cannot be deleted"""
        response = async_db_client.delete(
            f"/api/v1/templates/{system_soap_template.id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == 403
        assert "system template" in response.json()["detail"].lower()

    def test_delete_template_success(
        self, async_db_client, test_db, therapist_custom_template, therapist_auth_headers
    ):
        """Successfully delete custom template"""
        template_id = therapist_custom_template.id

        response = async_db_client.delete(
            f"/api/v1/templates/{template_id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "deleted successfully" in data["message"].lower()

        # Verify template no longer exists
        get_response = async_db_client.get(f"/api/v1/templates/{template_id}")
        assert get_response.status_code == 404

    def test_delete_template_not_found(
        self, async_db_client, test_db, therapist_auth_headers
    ):
        """Deleting non-existent template returns 404"""
        fake_id = uuid4()

        response = async_db_client.delete(
            f"/api/v1/templates/{fake_id}",
            headers=therapist_auth_headers
        )

        assert response.status_code == 404

    def test_delete_template_removes_from_database(
        self, async_db_client, test_db, therapist_custom_template, therapist_auth_headers
    ):
        """Deleted template is removed from database"""
        template_id = therapist_custom_template.id

        # Delete template
        response = async_db_client.delete(
            f"/api/v1/templates/{template_id}",
            headers=therapist_auth_headers
        )
        assert response.status_code == 200

        # Query database directly
        from app.models.db_models import NoteTemplate
        db_template = test_db.query(NoteTemplate).filter_by(id=template_id).first()
        assert db_template is None


# ============================================================================
# Edge Cases and Validation Tests
# ============================================================================

class TestTemplateEdgeCases:
    """Edge cases and additional validation scenarios"""

    def test_create_template_with_all_field_types(
        self, async_db_client, test_db, therapist_auth_headers
    ):
        """Create template using all supported field types"""
        template_data = {
            "name": "All Field Types Template",
            "template_type": "custom",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "all_fields",
                        "name": "All Field Types",
                        "fields": [
                            {
                                "id": "text_field",
                                "label": "Text Field",
                                "type": "text",
                                "required": False
                            },
                            {
                                "id": "textarea_field",
                                "label": "Textarea Field",
                                "type": "textarea",
                                "required": False
                            },
                            {
                                "id": "select_field",
                                "label": "Select Field",
                                "type": "select",
                                "required": False,
                                "options": ["Option 1", "Option 2"]
                            },
                            {
                                "id": "multiselect_field",
                                "label": "Multiselect Field",
                                "type": "multiselect",
                                "required": False,
                                "options": ["A", "B", "C"]
                            },
                            {
                                "id": "checkbox_field",
                                "label": "Checkbox Field",
                                "type": "checkbox",
                                "required": False
                            },
                            {
                                "id": "number_field",
                                "label": "Number Field",
                                "type": "number",
                                "required": False
                            },
                            {
                                "id": "date_field",
                                "label": "Date Field",
                                "type": "date",
                                "required": False
                            },
                            {
                                "id": "scale_field",
                                "label": "Scale Field",
                                "type": "scale",
                                "required": False
                            }
                        ]
                    }
                ]
            }
        }

        response = async_db_client.post(
            "/api/v1/templates",
            json=template_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert len(data["structure"]["sections"][0]["fields"]) == 8

    def test_create_template_with_ai_mappings(
        self, async_db_client, test_db, therapist_auth_headers
    ):
        """Create template with AI auto-fill mappings"""
        template_data = {
            "name": "AI-Enabled Template",
            "template_type": "soap",
            "is_shared": False,
            "structure": {
                "sections": [
                    {
                        "id": "subjective",
                        "name": "Subjective",
                        "fields": [
                            {
                                "id": "summary",
                                "label": "Session Summary",
                                "type": "textarea",
                                "required": True,
                                "ai_mapping": "topic_summary"
                            },
                            {
                                "id": "mood",
                                "label": "Mood",
                                "type": "select",
                                "required": True,
                                "options": ["anxious", "neutral", "positive"],
                                "ai_mapping": "session_mood"
                            }
                        ]
                    }
                ]
            }
        }

        response = async_db_client.post(
            "/api/v1/templates",
            json=template_data,
            headers=therapist_auth_headers
        )

        assert response.status_code == 201
        data = response.json()

        # Verify AI mappings preserved
        fields = data["structure"]["sections"][0]["fields"]
        assert fields[0]["ai_mapping"] == "topic_summary"
        assert fields[1]["ai_mapping"] == "session_mood"

    def test_list_templates_with_multiple_filters(
        self, async_db_client, test_db, system_soap_template, system_dap_template, shared_template, therapist_auth_headers
    ):
        """List templates with combined filters"""
        response = async_db_client.get(
            f"/api/v1/templates?template_type={TemplateType.soap.value}&include_shared=false",
            headers=therapist_auth_headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should only return SOAP type templates, excluding shared
        assert all(t["template_type"] == TemplateType.soap.value for t in data)
        template_names = [t["name"] for t in data]
        assert "Shared BIRP Template" not in template_names
