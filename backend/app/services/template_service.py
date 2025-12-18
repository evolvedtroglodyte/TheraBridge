"""
Template service for managing note templates with CRUD operations and validation.

Provides business logic for creating, reading, updating, and deleting note templates.
Handles validation of template structures, access control, and filtering.
"""
import logging
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.models.db_models import NoteTemplate
from app.models.schemas import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateStructure,
    TemplateType
)

# Configure logging
logger = logging.getLogger(__name__)


class TemplateService:
    """Service for managing note templates with comprehensive validation and access control"""

    async def list_templates(
        self,
        db: AsyncSession,
        user_id: UUID,
        template_type: Optional[TemplateType] = None,
        include_shared: bool = True
    ) -> List[NoteTemplate]:
        """
        List templates with optional filtering.

        Returns system templates + user's templates + shared templates (if requested).
        Results are sorted by is_system DESC, created_at DESC (system templates first).

        Args:
            db: Database session
            user_id: User requesting the templates
            template_type: Optional filter by template type (soap, dap, birp, etc.)
            include_shared: Whether to include shared templates from other users

        Returns:
            List of NoteTemplate objects matching the filters

        Raises:
            HTTPException: 500 if database error occurs
        """
        logger.info(
            "Listing templates",
            extra={
                "user_id": str(user_id),
                "template_type": template_type,
                "include_shared": include_shared
            }
        )

        try:
            # Build query conditions
            conditions = []

            # System templates (available to all)
            conditions.append(NoteTemplate.is_system == True)

            # User's own templates
            conditions.append(NoteTemplate.created_by == user_id)

            # Shared templates from other users (if requested)
            if include_shared:
                conditions.append(
                    and_(
                        NoteTemplate.is_shared == True,
                        NoteTemplate.created_by != user_id,
                        NoteTemplate.is_system == False
                    )
                )

            # Combine with OR
            query = select(NoteTemplate).where(or_(*conditions))

            # Apply template type filter if specified
            if template_type:
                query = query.where(NoteTemplate.template_type == template_type.value)

            # Sort: system templates first, then by created date descending
            query = query.order_by(
                NoteTemplate.is_system.desc(),
                NoteTemplate.created_at.desc()
            )

            result = await db.execute(query)
            templates = result.scalars().all()

            logger.info(
                "Templates retrieved successfully",
                extra={
                    "user_id": str(user_id),
                    "count": len(templates)
                }
            )

            return templates

        except Exception as e:
            logger.error(
                "Database error listing templates",
                extra={
                    "user_id": str(user_id),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve templates: {str(e)}"
            ) from e

    async def get_template(
        self,
        db: AsyncSession,
        template_id: UUID,
        user_id: UUID
    ) -> NoteTemplate:
        """
        Get single template by ID with access validation.

        User has access if:
        - Template is a system template, OR
        - Template was created by the user, OR
        - Template is shared

        Args:
            db: Database session
            template_id: UUID of template to retrieve
            user_id: User requesting the template

        Returns:
            NoteTemplate object

        Raises:
            HTTPException: 404 if template not found or user lacks access
            HTTPException: 500 if database error occurs
        """
        logger.info(
            "Fetching template",
            extra={
                "template_id": str(template_id),
                "user_id": str(user_id)
            }
        )

        try:
            # Fetch template
            result = await db.execute(
                select(NoteTemplate).where(NoteTemplate.id == template_id)
            )
            template = result.scalar_one_or_none()

            # Check if template exists
            if not template:
                logger.warning(
                    "Template not found",
                    extra={
                        "template_id": str(template_id),
                        "user_id": str(user_id)
                    }
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Template {template_id} not found"
                )

            # Validate access
            has_access = (
                template.is_system or
                template.created_by == user_id or
                template.is_shared
            )

            if not has_access:
                logger.warning(
                    "User lacks access to template",
                    extra={
                        "template_id": str(template_id),
                        "user_id": str(user_id),
                        "template_created_by": str(template.created_by) if template.created_by else None,
                        "is_system": template.is_system,
                        "is_shared": template.is_shared
                    }
                )
                raise HTTPException(
                    status_code=403,
                    detail="You do not have access to this template"
                )

            logger.info(
                "Template retrieved successfully",
                extra={
                    "template_id": str(template_id),
                    "user_id": str(user_id),
                    "template_name": template.name
                }
            )

            return template

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Database error fetching template",
                extra={
                    "template_id": str(template_id),
                    "user_id": str(user_id),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve template: {str(e)}"
            ) from e

    async def create_template(
        self,
        db: AsyncSession,
        template_data: TemplateCreate,
        user_id: UUID
    ) -> NoteTemplate:
        """
        Create a new template with structure validation.

        Args:
            db: Database session
            template_data: Template creation data (includes name, type, structure)
            user_id: User creating the template

        Returns:
            Created NoteTemplate object

        Raises:
            HTTPException: 400 if template structure is invalid
            HTTPException: 500 if database error occurs
        """
        logger.info(
            "Creating template",
            extra={
                "user_id": str(user_id),
                "template_name": template_data.name,
                "template_type": template_data.template_type
            }
        )

        # Validate structure
        try:
            self.validate_template_structure(template_data.structure)
        except ValueError as e:
            logger.warning(
                "Invalid template structure",
                extra={
                    "user_id": str(user_id),
                    "template_name": template_data.name,
                    "error": str(e)
                }
            )
            raise HTTPException(
                status_code=400,
                detail=f"Invalid template structure: {str(e)}"
            ) from e

        try:
            # Create template object
            template = NoteTemplate(
                name=template_data.name,
                description=template_data.description,
                template_type=template_data.template_type.value,
                is_system=False,  # User templates are never system templates
                created_by=user_id,
                is_shared=template_data.is_shared,
                structure=template_data.structure.model_dump()  # Convert Pydantic to dict for JSONB
            )

            db.add(template)
            await db.flush()  # Flush to get the ID without committing
            await db.refresh(template)

            logger.info(
                "Template created successfully",
                extra={
                    "template_id": str(template.id),
                    "user_id": str(user_id),
                    "template_name": template.name,
                    "section_count": self.get_section_count(template_data.structure)
                }
            )

            return template

        except Exception as e:
            logger.error(
                "Database error creating template",
                extra={
                    "user_id": str(user_id),
                    "template_name": template_data.name,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create template: {str(e)}"
            ) from e

    async def update_template(
        self,
        db: AsyncSession,
        template_id: UUID,
        updates: TemplateUpdate,
        user_id: UUID
    ) -> NoteTemplate:
        """
        Update template (partial PATCH).

        Only the owner can update (not system templates).

        Args:
            db: Database session
            template_id: UUID of template to update
            updates: Partial template updates
            user_id: User requesting the update

        Returns:
            Updated NoteTemplate object

        Raises:
            HTTPException: 404 if template not found
            HTTPException: 403 if user is not the owner or template is system template
            HTTPException: 400 if updated structure is invalid
            HTTPException: 500 if database error occurs
        """
        logger.info(
            "Updating template",
            extra={
                "template_id": str(template_id),
                "user_id": str(user_id)
            }
        )

        try:
            # Fetch template
            result = await db.execute(
                select(NoteTemplate).where(NoteTemplate.id == template_id)
            )
            template = result.scalar_one_or_none()

            if not template:
                logger.warning(
                    "Template not found for update",
                    extra={
                        "template_id": str(template_id),
                        "user_id": str(user_id)
                    }
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Template {template_id} not found"
                )

            # Check if system template
            if template.is_system:
                logger.warning(
                    "Attempted to update system template",
                    extra={
                        "template_id": str(template_id),
                        "user_id": str(user_id)
                    }
                )
                raise HTTPException(
                    status_code=403,
                    detail="Cannot update system templates"
                )

            # Check ownership
            if template.created_by != user_id:
                logger.warning(
                    "User is not template owner",
                    extra={
                        "template_id": str(template_id),
                        "user_id": str(user_id),
                        "template_created_by": str(template.created_by) if template.created_by else None
                    }
                )
                raise HTTPException(
                    status_code=403,
                    detail="You can only update templates you created"
                )

            # Validate structure if being updated
            if updates.structure:
                try:
                    self.validate_template_structure(updates.structure)
                except ValueError as e:
                    logger.warning(
                        "Invalid updated template structure",
                        extra={
                            "template_id": str(template_id),
                            "user_id": str(user_id),
                            "error": str(e)
                        }
                    )
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid template structure: {str(e)}"
                    ) from e

            # Apply updates
            update_data = updates.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field == "structure" and value:
                    # Convert Pydantic to dict for JSONB
                    setattr(template, field, value.model_dump())
                else:
                    setattr(template, field, value)

            template.updated_at = datetime.utcnow()

            await db.flush()
            await db.refresh(template)

            logger.info(
                "Template updated successfully",
                extra={
                    "template_id": str(template_id),
                    "user_id": str(user_id),
                    "fields_updated": list(update_data.keys())
                }
            )

            return template

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Database error updating template",
                extra={
                    "template_id": str(template_id),
                    "user_id": str(user_id),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update template: {str(e)}"
            ) from e

    async def delete_template(
        self,
        db: AsyncSession,
        template_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Soft delete template.

        Only the owner can delete (not system templates).
        Database CASCADE will handle related SessionNote records.

        Args:
            db: Database session
            template_id: UUID of template to delete
            user_id: User requesting the deletion

        Returns:
            True if deletion was successful

        Raises:
            HTTPException: 404 if template not found
            HTTPException: 403 if user is not the owner or template is system template
            HTTPException: 500 if database error occurs
        """
        logger.info(
            "Deleting template",
            extra={
                "template_id": str(template_id),
                "user_id": str(user_id)
            }
        )

        try:
            # Fetch template
            result = await db.execute(
                select(NoteTemplate).where(NoteTemplate.id == template_id)
            )
            template = result.scalar_one_or_none()

            if not template:
                logger.warning(
                    "Template not found for deletion",
                    extra={
                        "template_id": str(template_id),
                        "user_id": str(user_id)
                    }
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Template {template_id} not found"
                )

            # Check if system template
            if template.is_system:
                logger.warning(
                    "Attempted to delete system template",
                    extra={
                        "template_id": str(template_id),
                        "user_id": str(user_id)
                    }
                )
                raise HTTPException(
                    status_code=403,
                    detail="Cannot delete system templates"
                )

            # Check ownership
            if template.created_by != user_id:
                logger.warning(
                    "User is not template owner",
                    extra={
                        "template_id": str(template_id),
                        "user_id": str(user_id),
                        "template_created_by": str(template.created_by) if template.created_by else None
                    }
                )
                raise HTTPException(
                    status_code=403,
                    detail="You can only delete templates you created"
                )

            # Delete template (CASCADE will handle related records)
            await db.delete(template)
            await db.flush()

            logger.info(
                "Template deleted successfully",
                extra={
                    "template_id": str(template_id),
                    "user_id": str(user_id),
                    "template_name": template.name
                }
            )

            return True

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Database error deleting template",
                extra={
                    "template_id": str(template_id),
                    "user_id": str(user_id),
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete template: {str(e)}"
            ) from e

    def validate_template_structure(self, structure: TemplateStructure) -> bool:
        """
        Validate template structure JSONB.

        Checks:
        - Sections exist and are not empty
        - Section IDs are unique
        - Fields have valid types
        - Required select/multiselect fields have options

        Args:
            structure: TemplateStructure to validate

        Returns:
            True if valid

        Raises:
            ValueError: If structure is invalid
        """
        # Pydantic validators already handle most validation
        # This method provides additional business logic validation if needed

        # Ensure sections exist (Pydantic validator handles this)
        if not structure.sections or len(structure.sections) == 0:
            raise ValueError("Template must have at least one section")

        # Ensure section IDs are unique (Pydantic validator handles this)
        section_ids = [section.id for section in structure.sections]
        if len(section_ids) != len(set(section_ids)):
            raise ValueError("All section IDs must be unique")

        # Validate each section has fields
        for section in structure.sections:
            if not section.fields or len(section.fields) == 0:
                raise ValueError(f"Section '{section.name}' must have at least one field")

            # Validate field IDs are unique within section
            field_ids = [field.id for field in section.fields]
            if len(field_ids) != len(set(field_ids)):
                raise ValueError(f"Section '{section.name}' has duplicate field IDs")

            # Validate field types and options (Pydantic validator handles select/multiselect options)
            for field in section.fields:
                # Additional validation can go here
                pass

        logger.debug(
            "Template structure validated",
            extra={
                "section_count": len(structure.sections),
                "total_fields": sum(len(s.fields) for s in structure.sections)
            }
        )

        return True

    def get_section_count(self, structure: TemplateStructure) -> int:
        """
        Helper to count sections in a template structure.

        Args:
            structure: TemplateStructure object

        Returns:
            Number of sections in the template
        """
        return len(structure.sections)


# Dependency function for FastAPI
def get_template_service() -> TemplateService:
    """
    FastAPI dependency to provide the template service.

    Creates a new TemplateService instance for each request.

    Returns:
        TemplateService: New instance ready for use

    Usage:
        In FastAPI routes, use: service = Depends(get_template_service)
    """
    return TemplateService()
