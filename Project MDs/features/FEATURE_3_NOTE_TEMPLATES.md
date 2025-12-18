# Feature 3: Note Templates

## Overview
Provide customizable note templates that therapists can use to structure their session documentation, supporting various therapy modalities and documentation standards.

## Requirements

### Template Types
1. **SOAP Notes** (Subjective, Objective, Assessment, Plan)
2. **DAP Notes** (Data, Assessment, Plan)
3. **BIRP Notes** (Behavior, Intervention, Response, Plan)
4. **Progress Notes** (General format)
5. **Custom Templates** (User-defined)

### Features
- Pre-built templates for common formats
- Ability to create custom templates
- Template versioning
- Practice-wide template sharing
- Field validation and required fields
- Auto-population from AI extraction

## Database Schema

```sql
-- Note templates
CREATE TABLE note_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    template_type VARCHAR(50) NOT NULL, -- 'soap', 'dap', 'birp', 'progress', 'custom'
    is_system BOOLEAN DEFAULT false, -- true for built-in templates
    created_by UUID REFERENCES users(id),
    is_shared BOOLEAN DEFAULT false, -- shared within practice
    structure JSONB NOT NULL, -- template structure definition
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Template fields definition (within structure JSONB)
-- Example structure:
-- {
--   "sections": [
--     {
--       "id": "subjective",
--       "name": "Subjective",
--       "description": "Patient's reported symptoms and concerns",
--       "fields": [
--         {
--           "id": "chief_complaint",
--           "label": "Chief Complaint",
--           "type": "textarea",
--           "required": true,
--           "ai_mapping": "presenting_issues"
--         },
--         {
--           "id": "mood",
--           "label": "Mood/Affect",
--           "type": "select",
--           "options": ["euthymic", "anxious", "depressed", "irritable"],
--           "required": true
--         }
--       ]
--     }
--   ]
-- }

-- Session notes using templates
CREATE TABLE session_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    template_id UUID REFERENCES note_templates(id),
    content JSONB NOT NULL, -- filled template data
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'completed', 'signed'
    signed_at TIMESTAMP,
    signed_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Template usage tracking
CREATE TABLE template_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID REFERENCES note_templates(id),
    user_id UUID REFERENCES users(id),
    used_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### GET /api/v1/templates
List available templates.

Query params:
- `type`: Filter by template type
- `include_shared`: Include practice-shared templates

Response:
```json
{
    "templates": [
        {
            "id": "uuid",
            "name": "SOAP Note",
            "description": "Standard SOAP format for medical documentation",
            "template_type": "soap",
            "is_system": true,
            "section_count": 4
        }
    ]
}
```

### GET /api/v1/templates/{template_id}
Get full template structure.

Response:
```json
{
    "id": "uuid",
    "name": "SOAP Note",
    "template_type": "soap",
    "structure": {
        "sections": [
            {
                "id": "subjective",
                "name": "Subjective",
                "fields": [...]
            }
        ]
    }
}
```

### POST /api/v1/templates
Create custom template.

Request:
```json
{
    "name": "My CBT Note",
    "description": "Custom template for CBT sessions",
    "template_type": "custom",
    "is_shared": false,
    "structure": {
        "sections": [...]
    }
}
```

### PUT /api/v1/templates/{template_id}
Update custom template (creates new version).

### DELETE /api/v1/templates/{template_id}
Delete custom template (soft delete).

### POST /api/v1/sessions/{session_id}/notes
Create note from template.

Request:
```json
{
    "template_id": "uuid",
    "content": {
        "subjective": {
            "chief_complaint": "Patient reports increased anxiety...",
            "mood": "anxious"
        },
        "objective": {...},
        "assessment": {...},
        "plan": {...}
    }
}
```

### POST /api/v1/sessions/{session_id}/notes/auto-fill
Auto-fill template from AI extraction.

Request:
```json
{
    "template_id": "uuid"
}
```

Response:
```json
{
    "auto_filled_content": {
        "subjective": {
            "chief_complaint": "Patient discussed ongoing work stress and sleep difficulties",
            "mood": "anxious"
        }
    },
    "confidence_scores": {
        "subjective.chief_complaint": 0.92,
        "subjective.mood": 0.78
    },
    "missing_fields": ["objective.vitals"]
}
```

## Built-in Templates

### SOAP Note Template
```json
{
    "sections": [
        {
            "id": "subjective",
            "name": "Subjective",
            "description": "Patient's reported symptoms, feelings, and concerns",
            "fields": [
                {"id": "chief_complaint", "label": "Chief Complaint", "type": "textarea", "required": true},
                {"id": "history", "label": "History of Present Illness", "type": "textarea"},
                {"id": "mood", "label": "Reported Mood", "type": "text"}
            ]
        },
        {
            "id": "objective",
            "name": "Objective",
            "description": "Observable findings and mental status",
            "fields": [
                {"id": "appearance", "label": "Appearance", "type": "text"},
                {"id": "behavior", "label": "Behavior", "type": "text"},
                {"id": "affect", "label": "Affect", "type": "select", "options": ["appropriate", "flat", "labile", "constricted"]}
            ]
        },
        {
            "id": "assessment",
            "name": "Assessment",
            "description": "Clinical assessment and diagnosis considerations",
            "fields": [
                {"id": "clinical_impression", "label": "Clinical Impression", "type": "textarea", "required": true},
                {"id": "risk_assessment", "label": "Risk Assessment", "type": "textarea"}
            ]
        },
        {
            "id": "plan",
            "name": "Plan",
            "description": "Treatment plan and next steps",
            "fields": [
                {"id": "interventions", "label": "Interventions Used", "type": "textarea"},
                {"id": "homework", "label": "Homework/Tasks", "type": "textarea"},
                {"id": "next_session", "label": "Next Session Plan", "type": "textarea"}
            ]
        }
    ]
}
```

## AI Mapping Configuration

Map AI extraction fields to template fields:
```json
{
    "ai_mappings": {
        "presenting_issues": ["subjective.chief_complaint"],
        "mood_assessment": ["subjective.mood", "objective.affect"],
        "therapeutic_interventions": ["plan.interventions"],
        "homework_assigned": ["plan.homework"],
        "key_insights": ["assessment.clinical_impression"]
    }
}
```

## Implementation Notes

### Field Types Supported
- `text`: Single line text input
- `textarea`: Multi-line text
- `select`: Dropdown selection
- `multiselect`: Multiple selection
- `checkbox`: Boolean
- `number`: Numeric input
- `date`: Date picker
- `scale`: 1-10 scale slider

### Validation Rules
- Required field validation
- Character limits
- Format validation (e.g., dates)
- Custom validation functions

## Testing Checklist
- [ ] List templates returns system and custom templates
- [ ] Create custom template validates structure
- [ ] Update template creates new version
- [ ] Delete template soft deletes
- [ ] Create note from template works
- [ ] Auto-fill from AI extraction maps correctly
- [ ] Validation catches missing required fields
- [ ] Shared templates visible to practice members

## Files to Create/Modify
- `app/routers/templates.py`
- `app/routers/notes.py`
- `app/services/template_service.py`
- `app/services/auto_fill_service.py`
- `app/models/templates.py`
- `app/schemas/templates.py`
- `alembic/versions/xxx_add_template_tables.py`
- `app/data/system_templates.json` (built-in templates)
