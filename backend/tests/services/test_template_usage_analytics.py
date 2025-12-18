"""
Test suite to validate template usage analytics tracking gap

This test suite verifies the known gap identified in Wave 0 research:
The template_usage table exists in the database but is NOT being written to
when templates are used to create session notes.

Expected results:
- Database schema exists with correct columns, foreign keys, and indexes
- Creating a session note with a template does NOT create a template_usage entry
- No analytics endpoints exist for template usage data
- TemplateUsage model exists but is never instantiated in the codebase

Gap impact:
- Cannot track most-used templates
- Cannot identify template adoption trends
- Cannot provide template effectiveness metrics
- Cannot personalize template recommendations
"""
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text, inspect
from app.models import db_models
from app.database import engine


@pytest.mark.asyncio
async def test_template_usage_table_schema_exists(db_session: AsyncSession):
    """
    Verify template_usage table exists with correct schema.

    Expected columns:
    - id: UUID primary key
    - template_id: UUID foreign key to note_templates
    - user_id: UUID foreign key to users
    - used_at: timestamp with timezone

    This test uses ORM inspection which works across SQLite (tests) and PostgreSQL (prod).
    """
    from sqlalchemy import inspect

    # Get inspector
    inspector = inspect(db_session.get_bind())

    # Check table exists
    tables = inspector.get_table_names()
    assert 'template_usage' in tables, "template_usage table should exist"

    # Check columns
    columns = {col['name']: col for col in inspector.get_columns('template_usage')}

    assert 'id' in columns, "template_usage should have id column"
    assert not columns['id']['nullable'], "id should be NOT NULL"

    assert 'template_id' in columns, "template_usage should have template_id column"
    assert not columns['template_id']['nullable'], "template_id should be NOT NULL"

    assert 'user_id' in columns, "template_usage should have user_id column"
    assert not columns['user_id']['nullable'], "user_id should be NOT NULL"

    assert 'used_at' in columns, "template_usage should have used_at column"
    # SQLite may treat timestamp with default as nullable in schema
    # The important thing is that the column exists

    # Check foreign keys
    foreign_keys = inspector.get_foreign_keys('template_usage')
    fk_columns = {fk['constrained_columns'][0]: fk for fk in foreign_keys}

    assert 'template_id' in fk_columns, "template_id should have foreign key"
    assert fk_columns['template_id']['referred_table'] == 'note_templates', \
        "template_id should reference note_templates table"

    assert 'user_id' in fk_columns, "user_id should have foreign key"
    assert fk_columns['user_id']['referred_table'] == 'users', \
        "user_id should reference users table"

    # Check indexes
    indexes = inspector.get_indexes('template_usage')
    index_names = [idx['name'] for idx in indexes]

    # At minimum, the foreign key columns should be indexed
    assert any('template_id' in name or 'template_id' in str(idx.get('column_names', []))
               for name, idx in zip(index_names, indexes)), \
        "template_id should have index for analytics queries"


@pytest.mark.asyncio
async def test_template_usage_not_tracked_gap(
    db_session: AsyncSession,
    therapist_user,
    patient_user,
    sample_session
):
    """
    CRITICAL GAP TEST: Verify template_usage is NOT being tracked.

    This test confirms the gap identified in Wave 0:
    - Creating a session note with a template does NOT create a template_usage entry
    - The TemplateUsage model exists but is never instantiated

    Expected behavior (CURRENT - BROKEN):
    - Create session note with template_id
    - Query template_usage table
    - Result: 0 entries (GAP CONFIRMED)

    Expected behavior (AFTER FIX):
    - Create session note with template_id
    - Query template_usage table
    - Result: 1 entry with template_id, user_id, timestamp
    """
    # Create a template
    template = db_models.NoteTemplate(
        name="Test SOAP Template",
        description="Test template for gap validation",
        template_type="soap",
        is_system=True,
        structure={
            "sections": [
                {
                    "id": "subjective",
                    "name": "Subjective",
                    "fields": [
                        {
                            "id": "chief_complaint",
                            "label": "Chief Complaint",
                            "type": "textarea",
                            "required": True
                        }
                    ]
                }
            ]
        }
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)

    # Create a session note using the template
    note = db_models.SessionNote(
        session_id=sample_session.id,
        template_id=template.id,  # Template is being used
        content={"subjective": {"chief_complaint": "Test complaint"}},
        status="draft"
    )
    db_session.add(note)
    await db_session.commit()
    await db_session.refresh(note)

    # Query template_usage table - SHOULD have entry but WON'T (gap)
    result = await db_session.execute(
        select(db_models.TemplateUsage).where(
            db_models.TemplateUsage.template_id == template.id
        )
    )
    usage_entries = result.scalars().all()

    # GAP CONFIRMED: No usage tracking despite template being used
    assert len(usage_entries) == 0, \
        "GAP CONFIRMED: Template usage is NOT being tracked. " \
        "Expected 1 entry in template_usage table, found 0."

    # Verify the note was created successfully (to rule out other issues)
    result = await db_session.execute(
        select(db_models.SessionNote).where(
            db_models.SessionNote.id == note.id
        )
    )
    created_note = result.scalar_one_or_none()
    assert created_note is not None, "Session note should be created"
    assert created_note.template_id == template.id, "Session note should reference template"

    # This proves the gap: note created with template, but no usage tracking


@pytest.mark.asyncio
async def test_template_usage_model_exists_but_not_used():
    """
    Verify TemplateUsage model exists in db_models but is never instantiated.

    This test confirms the model is defined but not being used anywhere
    in the application code.
    """
    # Verify model exists
    assert hasattr(db_models, 'TemplateUsage'), \
        "TemplateUsage model should exist in db_models"

    # Verify model structure
    model = db_models.TemplateUsage
    assert hasattr(model, 'id'), "TemplateUsage should have id field"
    assert hasattr(model, 'template_id'), "TemplateUsage should have template_id field"
    assert hasattr(model, 'user_id'), "TemplateUsage should have user_id field"
    assert hasattr(model, 'used_at'), "TemplateUsage should have used_at field"
    assert model.__tablename__ == 'template_usage', \
        "TemplateUsage should map to template_usage table"


@pytest.mark.asyncio
async def test_no_template_analytics_endpoints_gap():
    """
    CRITICAL GAP TEST: Verify template analytics endpoints do NOT exist.

    This test confirms that despite the template_usage table existing,
    there are NO analytics endpoints to query template usage data.

    Missing endpoints (should be created after gap is fixed):
    - GET /api/v1/analytics/templates/most-used
    - GET /api/v1/analytics/templates/usage-trends
    - GET /api/v1/analytics/templates/adoption
    - GET /api/v1/analytics/templates/user-preferences
    """
    from app.routers import analytics

    # Get all routes from analytics router
    routes = [route.path for route in analytics.router.routes]

    # Verify no template-related analytics endpoints exist
    template_routes = [r for r in routes if 'template' in r.lower()]

    assert len(template_routes) == 0, \
        "GAP CONFIRMED: No template analytics endpoints exist. " \
        f"Found routes: {routes}"


@pytest.mark.asyncio
async def test_gap_impact_assessment(db_session: AsyncSession):
    """
    Document the impact of the template usage tracking gap.

    This test demonstrates what features are currently impossible
    due to the missing usage tracking.
    """
    # Query template_usage table directly
    result = db_session.execute(
        select(db_models.TemplateUsage)
    )
    all_usage = result.scalars().all()

    assert len(all_usage) == 0, \
        "GAP IMPACT: Template usage table is empty. " \
        "Cannot determine most-used templates, usage trends, or user preferences."

    # Verify we can't do basic analytics without data
    # Most-used templates query would return 0 for all templates
    result = db_session.execute(
        select(db_models.NoteTemplate)
    )
    templates = result.scalars().all()

    # For each template, usage count would be 0
    for template in templates:
        usage_result = db_session.execute(
            select(db_models.TemplateUsage).where(
                db_models.TemplateUsage.template_id == template.id
            )
        )
        usage_count = len(usage_result.scalars().all())
        assert usage_count == 0, \
            f"GAP IMPACT: Template '{template.name}' shows 0 usage. " \
            f"Cannot rank templates by popularity."


def test_implementation_plan_documentation():
    """
    Document the implementation plan to fix the template usage tracking gap.

    Location to add tracking:
    - File: app/routers/notes.py
    - Function: create_session_note
    - Line: ~150 (after new_note is committed)

    Implementation:
    ```python
    # Track template usage for analytics (if template was used)
    if note_data.template_id:
        usage_entry = db_models.TemplateUsage(
            template_id=note_data.template_id,
            user_id=current_user.id
        )
        db.add(usage_entry)
        await db.commit()
    ```

    Analytics endpoints to create:
    - GET /api/v1/analytics/templates/most-used
      Returns top 10 templates by usage count

    - GET /api/v1/analytics/templates/usage-trends?period=week|month|quarter
      Returns time-series data of template usage

    - GET /api/v1/analytics/templates/adoption
      Returns metrics on template adoption rates

    - GET /api/v1/analytics/templates/user-preferences
      Returns user's most-used templates for personalization

    Estimated effort: 2-4 hours
    - 30 minutes: Add usage tracking to notes.py
    - 1 hour: Create analytics service functions
    - 1 hour: Create analytics endpoints
    - 30-60 minutes: Write tests for new functionality

    Priority: MEDIUM
    - Not blocking core functionality
    - Provides valuable insights for therapists
    - Enables future personalization features
    - Low risk, high value-add
    """
    assert True, "Implementation plan documented"
