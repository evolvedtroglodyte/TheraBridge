"""
Template Seeding Service

Handles initialization and seeding of system note templates on application startup.
Loads default clinical templates (SOAP, DAP, BIRP, etc.) from JSON files and
inserts them into the database.

Safety Features:
- Idempotent seeding (safe to run multiple times)
- Validates JSON structure before insertion
- Comprehensive error handling and logging
- Only seeds if templates don't already exist
"""
import json
import logging
from pathlib import Path
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.db_models import NoteTemplate

# Configure logger
logger = logging.getLogger(__name__)

# Path to default templates JSON file
DEFAULT_TEMPLATES_PATH = Path(__file__).parent.parent / "data" / "default_templates.json"


def load_system_templates() -> List[Dict]:
    """
    Load system templates from JSON file

    Returns:
        List[Dict]: List of template data dictionaries

    Raises:
        ValueError: If file not found or invalid JSON
    """
    try:
        if not DEFAULT_TEMPLATES_PATH.exists():
            raise ValueError(f"Templates file not found: {DEFAULT_TEMPLATES_PATH}")

        logger.info(f"Loading system templates from {DEFAULT_TEMPLATES_PATH}")

        with open(DEFAULT_TEMPLATES_PATH, 'r', encoding='utf-8') as f:
            templates = json.load(f)

        if not isinstance(templates, list):
            raise ValueError("Templates JSON must be a list of template objects")

        logger.info(f"Successfully loaded {len(templates)} template definitions")
        return templates

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in templates file: {str(e)}")
    except Exception as e:
        raise ValueError(f"Failed to load templates: {str(e)}")


async def seed_templates(db: AsyncSession) -> int:
    """
    Insert system templates into database

    Loads templates from JSON and creates NoteTemplate records for any templates
    that don't already exist in the database. Templates are identified by their
    UUID from the JSON file, ensuring idempotent seeding.

    Args:
        db: AsyncSession database session

    Returns:
        int: Number of templates seeded (newly inserted)

    Raises:
        ValueError: If templates file is invalid
        Exception: If database operation fails
    """
    try:
        # Load templates from JSON
        template_data = load_system_templates()

        if not template_data:
            logger.warning("No templates found in JSON file")
            return 0

        templates_seeded = 0

        # Process each template
        for template_dict in template_data:
            # Validate required fields
            required_fields = ['id', 'name', 'template_type', 'structure']
            missing_fields = [field for field in required_fields if field not in template_dict]

            if missing_fields:
                logger.warning(
                    f"Skipping template '{template_dict.get('name', 'unknown')}' - "
                    f"missing required fields: {missing_fields}"
                )
                continue

            template_id = template_dict['id']

            # Check if template already exists
            query = select(NoteTemplate).where(NoteTemplate.id == template_id)
            result = await db.execute(query)
            existing_template = result.scalar_one_or_none()

            if existing_template:
                logger.debug(f"Template '{template_dict['name']}' already exists, skipping")
                continue

            # Create new template record
            new_template = NoteTemplate(
                id=template_id,
                name=template_dict['name'],
                description=template_dict.get('description'),
                template_type=template_dict['template_type'],
                is_system=True,  # Mark as system template
                created_by=None,  # System templates have no creator
                is_shared=template_dict.get('is_shared', True),  # System templates are shared by default
                structure=template_dict['structure']
            )

            db.add(new_template)
            templates_seeded += 1
            logger.info(f"Seeded template: {template_dict['name']} ({template_dict['template_type']})")

        # Commit all templates at once
        if templates_seeded > 0:
            await db.commit()
            logger.info(f"Successfully seeded {templates_seeded} new templates")
        else:
            logger.info("No new templates to seed")

        return templates_seeded

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to seed templates: {str(e)}", exc_info=True)
        raise


async def get_seeding_status(db: AsyncSession) -> Dict:
    """
    Check seeding status and determine if seeding is needed

    Args:
        db: AsyncSession database session

    Returns:
        Dict with status information:
        - total_system_templates: Number of system templates in database
        - needs_seeding: True if seeding should be run
    """
    try:
        # Count existing system templates
        query = select(func.count()).select_from(NoteTemplate).where(
            NoteTemplate.is_system == True
        )
        result = await db.execute(query)
        total_system_templates = result.scalar_one()

        # Load expected templates from JSON to determine if seeding is needed
        try:
            expected_templates = load_system_templates()
            expected_count = len(expected_templates)
        except Exception as e:
            logger.warning(f"Could not load templates file for comparison: {str(e)}")
            expected_count = 0

        needs_seeding = total_system_templates < expected_count

        return {
            "total_system_templates": total_system_templates,
            "expected_templates": expected_count,
            "needs_seeding": needs_seeding
        }

    except Exception as e:
        logger.error(f"Failed to check seeding status: {str(e)}", exc_info=True)
        return {
            "total_system_templates": 0,
            "expected_templates": 0,
            "needs_seeding": True,
            "error": str(e)
        }


async def seed_on_startup(db: AsyncSession) -> None:
    """
    Main entry point for template seeding on application startup

    Checks if seeding is needed and runs the seeding process.
    Safe to call on every startup - will only seed templates that don't exist.

    Args:
        db: AsyncSession database session

    Returns:
        None

    Raises:
        Exception: Logs errors but does not raise (non-critical for startup)
    """
    try:
        logger.info("Checking template seeding status...")

        # Check if seeding is needed
        status = await get_seeding_status(db)

        if "error" in status:
            logger.error(f"Error checking seeding status: {status['error']}")
            return

        logger.info(
            f"Template status: {status['total_system_templates']} system templates in database, "
            f"{status['expected_templates']} expected"
        )

        if not status['needs_seeding']:
            logger.info("Templates already seeded - no action needed")
            return

        # Run seeding
        logger.info("Seeding system templates...")
        templates_seeded = await seed_templates(db)

        if templates_seeded > 0:
            logger.info(f"✅ Successfully seeded {templates_seeded} system templates")
        else:
            logger.info("✅ Template seeding complete - all templates up to date")

    except Exception as e:
        # Log error but don't raise - template seeding is not critical for startup
        logger.error(f"Failed to seed templates on startup: {str(e)}", exc_info=True)
        logger.warning("Application will continue without system templates. Manual seeding may be required.")
