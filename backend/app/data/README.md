# System Data Directory

## Purpose

This directory contains data files used for seeding the database with system defaults. These files ensure that essential data (like clinical note templates) is available in the database when the application starts.

## Files

### default_templates.json

Contains the four system-provided clinical note templates:

1. **SOAP** - Subjective, Objective, Assessment, Plan
2. **DAP** - Data, Assessment, Plan
3. **BIRP** - Behavior, Intervention, Response, Plan
4. **Progress Note** - General progress documentation

These templates are automatically loaded into the database on application startup if they don't already exist.

## Usage

Templates are loaded by the application startup logic in `app/main.py` via the `services/template_service.py` initialization code. The system checks if templates exist before inserting to prevent duplicates.

## Important Warnings

### Do NOT Modify Template IDs

The template IDs in `default_templates.json` are used as primary keys in the database. Changing these IDs will break references and cause data integrity issues.

**Example - DO NOT CHANGE:**
```json
{
  "id": "soap-template-v1",  // ← NEVER MODIFY THIS
  "name": "SOAP Note"
}
```

### System Templates Cannot Be Edited

Templates with `is_system: true` are read-only in the application. Users cannot edit or delete these templates through the API. This ensures consistent documentation standards across all therapists.

### Database Re-seeding Required

If you modify the template content (names, descriptions, sections) in this file, you must re-seed the database for changes to take effect:

1. **Development:** Delete existing templates from database and restart app
2. **Production:** Run migration script to update existing system templates

Changes to this file do NOT automatically update existing database records.

## Developer Notes

- This directory is committed to git (not ignored)
- The __init__.py file makes this a Python package
- Templates can be imported programmatically if needed
- Additional system data files can be added here following the same pattern
