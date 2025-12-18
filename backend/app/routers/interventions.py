"""
Interventions router for Feature 4: Treatment Plans
Provides evidence-based intervention library access and custom intervention creation.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.db_models import User
from app.models.treatment_models import Intervention
from app.models.treatment_schemas import (
    InterventionCreate,
    InterventionResponse,
    InterventionListItem,
    EvidenceLevel
)
from app.models.schemas import UserRole

router = APIRouter()


@router.get("/interventions", response_model=List[InterventionListItem])
async def list_interventions(
    modality: Optional[str] = None,
    search: Optional[str] = None,
    evidence_level: Optional[EvidenceLevel] = None,
    include_system: bool = True,
    include_custom: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List available interventions from the system library and user's custom interventions.

    Returns a filtered list of interventions based on query parameters. System interventions
    (built-in library) and custom user-created interventions can be included or excluded.

    Authorization:
        - Requires therapist role

    Query Parameters:
        - modality: Filter by therapy modality (e.g., "CBT", "DBT", "psychodynamic")
          - Case-insensitive partial match
        - search: Search by name or description (case-insensitive)
        - evidence_level: Filter by evidence level (strong, moderate, emerging)
        - include_system: Include system interventions (default: True)
        - include_custom: Include user's custom interventions (default: True)

    Returns:
        List[InterventionListItem]: Minimal intervention data for list views
        - Ordered by: is_system DESC (system first), name ASC

    Raises:
        HTTPException 403: If user is not a therapist

    Examples:
        GET /interventions?modality=CBT
        GET /interventions?search=relaxation&evidence_level=strong
        GET /interventions?include_system=true&include_custom=false
    """
    # Authorization: Only therapists can access interventions
    if current_user.role != UserRole.therapist:
        raise HTTPException(
            status_code=403,
            detail="Only therapists can access interventions"
        )

    # Build base query
    query = select(Intervention)

    # Filter by system vs custom interventions
    if not include_system and not include_custom:
        # If both excluded, return empty list
        return []

    if not include_system:
        # Only custom interventions by current user
        query = query.where(
            Intervention.is_system == False,
            Intervention.created_by == current_user.id
        )
    elif not include_custom:
        # Only system interventions
        query = query.where(Intervention.is_system == True)
    else:
        # Both system and custom: system interventions OR custom by current user
        query = query.where(
            or_(
                Intervention.is_system == True,
                Intervention.created_by == current_user.id
            )
        )

    # Filter by modality (case-insensitive partial match)
    if modality:
        query = query.where(
            Intervention.modality.ilike(f"%{modality}%")
        )

    # Filter by search term (name or description, case-insensitive)
    if search:
        query = query.where(
            or_(
                Intervention.name.ilike(f"%{search}%"),
                Intervention.description.ilike(f"%{search}%")
            )
        )

    # Filter by evidence level (exact match)
    if evidence_level:
        query = query.where(
            Intervention.evidence_level == evidence_level.value
        )

    # Order by: system interventions first, then alphabetically by name
    query = query.order_by(
        Intervention.is_system.desc(),
        Intervention.name.asc()
    )

    # Execute query
    result = await db.execute(query)
    interventions = result.scalars().all()

    # Return list items (minimal data)
    return [InterventionListItem.model_validate(i) for i in interventions]


@router.post("/interventions", response_model=InterventionResponse, status_code=201)
async def create_custom_intervention(
    intervention_data: InterventionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a custom intervention for the current therapist.

    Allows therapists to create their own interventions beyond the system library.
    Custom interventions are only visible to the therapist who created them.

    Authorization:
        - Requires therapist role
        - Intervention is automatically linked to current_user.id as created_by

    Request Body:
        - name: Intervention name (1-200 characters, required)
        - description: Detailed description (optional)
        - modality: Therapy modality, e.g., "CBT", "DBT" (optional)
        - evidence_level: Evidence strength (strong, moderate, emerging) (optional)

    Returns:
        InterventionResponse: Full intervention data including ID and timestamps
        - is_system: Always False for custom interventions
        - created_by: Set to current user's ID

    Raises:
        HTTPException 403: If user is not a therapist
        HTTPException 400: If validation fails (e.g., name too short/long)

    Example:
        POST /interventions
        {
            "name": "Modified Mindful Breathing Exercise",
            "description": "3-minute breathing exercise with body scan",
            "modality": "Mindfulness",
            "evidence_level": "moderate"
        }
    """
    # Authorization: Only therapists can create interventions
    if current_user.role != UserRole.therapist:
        raise HTTPException(
            status_code=403,
            detail="Only therapists can create interventions"
        )

    # Create new intervention
    new_intervention = Intervention(
        name=intervention_data.name.strip(),
        description=intervention_data.description.strip() if intervention_data.description else None,
        modality=intervention_data.modality.strip() if intervention_data.modality else None,
        evidence_level=intervention_data.evidence_level.value if intervention_data.evidence_level else None,
        is_system=False,  # Custom interventions are never system interventions
        created_by=current_user.id
    )

    db.add(new_intervention)
    await db.commit()
    await db.refresh(new_intervention)

    return InterventionResponse.model_validate(new_intervention)


@router.get("/interventions/{intervention_id}", response_model=InterventionResponse)
async def get_intervention_details(
    intervention_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full details for a specific intervention.

    Returns complete intervention data including all fields.

    Authorization:
        - Requires therapist role
        - System interventions: accessible by all therapists
        - Custom interventions: only accessible by creator

    Args:
        intervention_id: UUID of the intervention to retrieve

    Returns:
        InterventionResponse: Complete intervention data

    Raises:
        HTTPException 403: If user is not a therapist or not authorized to view
        HTTPException 404: If intervention not found

    Example:
        GET /interventions/a1b2c3d4-e5f6-7890-abcd-ef1234567890
    """
    # Authorization: Only therapists can access interventions
    if current_user.role != UserRole.therapist:
        raise HTTPException(
            status_code=403,
            detail="Only therapists can access interventions"
        )

    # Load intervention by ID
    result = await db.execute(
        select(Intervention).where(
            Intervention.id == intervention_id
        )
    )
    intervention = result.scalar_one_or_none()

    if not intervention:
        raise HTTPException(
            status_code=404,
            detail=f"Intervention {intervention_id} not found"
        )

    # Authorization check: custom interventions only accessible by creator
    if not intervention.is_system and intervention.created_by != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this custom intervention"
        )

    return InterventionResponse.model_validate(intervention)
