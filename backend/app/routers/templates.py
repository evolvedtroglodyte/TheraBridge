"""
Templates router for Feature 3: Note Templates
Provides CRUD operations for therapy note templates (SOAP, DAP, BIRP, etc.).
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.auth.dependencies import get_current_user, require_role
from app.models import db_models
from app.models.schemas import (
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListItem,
    TemplateType
)
from app.services.template_service import get_template_service, TemplateService
from app.middleware.rate_limit import limiter

router = APIRouter()


@router.get("/", response_model=List[TemplateListItem])
@limiter.limit("100/minute")
async def list_templates(
    request: Request,
    template_type: Optional[TemplateType] = Query(None, description="Filter by template type (soap, dap, birp, custom)"),
    include_shared: bool = Query(True, description="Include shared templates from other users"),
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    List all available templates for the current user.

    Returns system templates + user's custom templates + shared templates (if requested).
    Templates are sorted with system templates first, then by creation date (newest first).

    Authorization:
        - Requires authentication (any role)

    Rate Limit:
        - 100 requests per minute per IP address

    Query Parameters:
        - template_type: Optional filter by template type (soap, dap, birp, custom)
        - include_shared: Include shared templates from other users (default: True)

    Returns:
        List[TemplateListItem]: List of templates with basic info and section count

    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Database error

    Example:
        GET /api/v1/templates - All templates (system + user's + shared)
        GET /api/v1/templates?template_type=soap - Only SOAP templates
        GET /api/v1/templates?include_shared=false - Only system + user's templates
    """
    templates = await service.list_templates(
        db=db,
        user_id=current_user.id,
        template_type=template_type,
        include_shared=include_shared
    )

    # Transform to list items with section count
    list_items = []
    for template in templates:
        # Parse structure JSONB to TemplateStructure to get section count
        section_count = len(template.structure.get("sections", []))

        list_items.append(
            TemplateListItem(
                id=template.id,
                name=template.name,
                description=template.description,
                template_type=TemplateType(template.template_type),
                is_system=template.is_system,
                is_shared=template.is_shared,
                section_count=section_count,
                created_at=template.created_at
            )
        )

    return list_items


@router.get("/{template_id}", response_model=TemplateResponse)
@limiter.limit("100/minute")
async def get_template(
    request: Request,
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    Get a single template by ID with full details.

    Returns complete template including structure. Access is granted if:
    - Template is a system template (available to all), OR
    - Template was created by the current user, OR
    - Template is shared by another user

    Authorization:
        - Requires authentication (any role)

    Rate Limit:
        - 100 requests per minute per IP address

    Path Parameters:
        - template_id: UUID of the template to retrieve

    Returns:
        TemplateResponse: Complete template with structure and metadata

    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 403: If user does not have access to the template
        HTTPException 404: If template not found
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Database error

    Example:
        GET /api/v1/templates/123e4567-e89b-12d3-a456-426614174000
    """
    template = await service.get_template(
        db=db,
        template_id=template_id,
        user_id=current_user.id
    )

    return TemplateResponse.model_validate(template)


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")
async def create_template(
    request: Request,
    template_data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(require_role(["therapist"])),
    service: TemplateService = Depends(get_template_service)
):
    """
    Create a new custom therapy note template.

    Only therapists can create templates. Templates are validated to ensure:
    - At least one section exists
    - All section IDs are unique
    - All sections have at least one field
    - Field IDs are unique within each section
    - Select/multiselect fields have options defined

    Authorization:
        - Requires therapist role

    Rate Limit:
        - 20 requests per hour per IP address (prevent template spam)

    Request Body:
        TemplateCreate: Template data including name, type, structure, and sharing settings

    Returns:
        TemplateResponse: Created template with generated ID and timestamps (201 status)

    Raises:
        HTTPException 400: If template structure is invalid
        HTTPException 401: If user is not authenticated
        HTTPException 403: If user is not a therapist
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Database error

    Example Request Body:
        {
            "name": "My Custom SOAP Note",
            "description": "Customized SOAP template for anxiety treatment",
            "template_type": "soap",
            "is_shared": false,
            "structure": {
                "sections": [
                    {
                        "id": "subjective",
                        "name": "Subjective",
                        "description": "Patient's reported experience",
                        "order": 1,
                        "fields": [
                            {
                                "id": "mood",
                                "label": "Current Mood",
                                "type": "text",
                                "required": true,
                                "order": 1
                            }
                        ]
                    }
                ]
            }
        }
    """
    template = await service.create_template(
        db=db,
        template_data=template_data,
        user_id=current_user.id
    )

    return TemplateResponse.model_validate(template)


@router.patch("/{template_id}", response_model=TemplateResponse)
@limiter.limit("50/hour")
async def update_template(
    request: Request,
    template_id: UUID,
    updates: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    Update an existing custom template (partial updates allowed).

    Only the template owner can update their templates. System templates cannot be updated.
    All fields are optional - only provided fields will be updated.

    Authorization:
        - Requires authentication
        - User must be the template owner

    Rate Limit:
        - 50 requests per hour per IP address

    Path Parameters:
        - template_id: UUID of the template to update

    Request Body:
        TemplateUpdate: Partial template updates (all fields optional)

    Returns:
        TemplateResponse: Updated template with new data

    Raises:
        HTTPException 400: If updated structure is invalid
        HTTPException 401: If user is not authenticated
        HTTPException 403: If user is not the owner or template is a system template
        HTTPException 404: If template not found
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Database error

    Example Request Body (partial update):
        {
            "name": "Updated Template Name",
            "is_shared": true
        }
    """
    template = await service.update_template(
        db=db,
        template_id=template_id,
        updates=updates,
        user_id=current_user.id
    )

    return TemplateResponse.model_validate(template)


@router.delete("/{template_id}")
@limiter.limit("20/hour")
async def delete_template(
    request: Request,
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user),
    service: TemplateService = Depends(get_template_service)
):
    """
    Delete a custom template.

    Only the template owner can delete their templates. System templates cannot be deleted.
    Deletion will cascade to any SessionNote records using this template.

    Authorization:
        - Requires authentication
        - User must be the template owner

    Rate Limit:
        - 20 requests per hour per IP address

    Path Parameters:
        - template_id: UUID of the template to delete

    Returns:
        dict: Success message {"message": "Template deleted successfully"}

    Raises:
        HTTPException 401: If user is not authenticated
        HTTPException 403: If user is not the owner or template is a system template
        HTTPException 404: If template not found
        HTTPException 429: Rate limit exceeded
        HTTPException 500: Database error

    Example:
        DELETE /api/v1/templates/123e4567-e89b-12d3-a456-426614174000
    """
    await service.delete_template(
        db=db,
        template_id=template_id,
        user_id=current_user.id
    )

    return {"message": "Template deleted successfully"}
