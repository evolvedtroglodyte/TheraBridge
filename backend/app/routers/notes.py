"""
Session notes router for clinical note creation and auto-fill
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from typing import List
import logging

from app.database import get_db
from app.auth.dependencies import require_role
from app.models import db_models
from app.models.schemas import (
    NoteCreate,
    NoteUpdate,
    NoteResponse,
    AutoFillRequest,
    AutoFillResponse,
    ExtractedNotes,
    TemplateType
)
from app.services.template_autofill import get_autofill_service, TemplateAutoFillService
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


async def verify_session_access(
    session_id: UUID,
    therapist_id: UUID,
    db: AsyncSession
) -> db_models.TherapySession:
    """
    Verify therapist has access to session via active patient relationship.

    Checks that:
    1. Session exists
    2. Therapist has active relationship with patient via therapist_patients table

    Args:
        session_id: UUID of therapy session
        therapist_id: UUID of therapist requesting access
        db: Database session

    Returns:
        TherapySession: Session object if access authorized

    Raises:
        HTTPException 404: If session not found
        HTTPException 403: If therapist doesn't have access to this patient
    """
    # Load session
    result = await db.execute(
        select(db_models.TherapySession).where(db_models.TherapySession.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        logger.warning(f"Session {session_id} not found")
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify therapist has active relationship with patient
    access_query = select(db_models.TherapistPatient).where(
        and_(
            db_models.TherapistPatient.therapist_id == therapist_id,
            db_models.TherapistPatient.patient_id == session.patient_id,
            db_models.TherapistPatient.is_active == True
        )
    )

    access_result = await db.execute(access_query)
    relationship = access_result.scalar_one_or_none()

    if not relationship:
        logger.warning(
            f"Access denied: Therapist {therapist_id} does not have active "
            f"relationship with patient {session.patient_id} for session {session_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="Access denied: Session not assigned to this therapist"
        )

    return session


@router.post("/api/v1/sessions/{session_id}/notes", response_model=NoteResponse, status_code=201)
@limiter.limit("50/hour")
async def create_session_note(
    request: Request,
    session_id: UUID,
    note_data: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(require_role(["therapist"]))
):
    """
    Create a new session note for a therapy session.

    Creates a SessionNote record linked to a specific therapy session using
    a note template. The note content is stored as JSONB for flexible structure.

    Authorization:
        - Only therapists can create notes
        - Therapist must have active relationship with patient

    Rate Limit:
        - 50 notes per hour per therapist
        - Prevents excessive note creation

    Args:
        session_id: UUID of therapy session
        note_data: NoteCreate schema with template_id and content
        db: Database session
        current_user: Authenticated therapist user

    Returns:
        NoteResponse: Created note with all metadata

    Raises:
        HTTPException 404: Session not found
        HTTPException 403: Unauthorized access to session
        HTTPException 400: Invalid template_id or content
        HTTPException 429: Rate limit exceeded
    """
    # Verify session exists and therapist has access
    session = await verify_session_access(session_id, current_user.id, db)

    # Verify template exists if provided
    if note_data.template_id:
        template_result = await db.execute(
            select(db_models.NoteTemplate).where(db_models.NoteTemplate.id == note_data.template_id)
        )
        template = template_result.scalar_one_or_none()

        if not template:
            raise HTTPException(status_code=400, detail="Template not found")

    # Create note
    new_note = db_models.SessionNote(
        session_id=session_id,
        template_id=note_data.template_id,
        content=note_data.content,
        status='draft'
    )

    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)

    logger.info(
        f"Created session note {new_note.id} for session {session_id}",
        extra={
            "note_id": str(new_note.id),
            "session_id": str(session_id),
            "therapist_id": str(current_user.id),
            "template_id": str(note_data.template_id) if note_data.template_id else None
        }
    )

    return NoteResponse.model_validate(new_note)


@router.post("/api/v1/sessions/{session_id}/notes/autofill", response_model=AutoFillResponse)
@limiter.limit("30/hour")
async def autofill_template_from_session(
    request: Request,
    session_id: UUID,
    autofill_request: AutoFillRequest,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(require_role(["therapist"])),
    autofill_service: TemplateAutoFillService = Depends(get_autofill_service)
):
    """
    Auto-fill a note template from AI-extracted session data.

    Takes AI-extracted notes from a processed session and intelligently maps
    them to a clinical note template format (SOAP, DAP, BIRP, or Progress Note).
    Returns filled sections with confidence scores and identifies fields needing
    manual review.

    Authorization:
        - Only therapists can auto-fill templates
        - Therapist must have active relationship with patient

    Rate Limit:
        - 30 auto-fills per hour per therapist
        - Stricter limit due to AI processing overhead

    Workflow:
        1. Verify session exists and has extracted_notes
        2. Reconstruct ExtractedNotes from JSONB
        3. Call auto-fill service to map data to template
        4. Return filled sections with confidence scores

    Args:
        session_id: UUID of processed therapy session
        autofill_request: Request with template_type to auto-fill
        db: Database session
        current_user: Authenticated therapist user
        autofill_service: Template auto-fill service instance

    Returns:
        AutoFillResponse: Filled template sections with confidence scores and missing fields

    Raises:
        HTTPException 404: Session not found
        HTTPException 403: Unauthorized access to session
        HTTPException 400: Session not yet processed (no extracted_notes)
        HTTPException 429: Rate limit exceeded

    Example Response:
        {
            "template_type": "soap",
            "auto_filled_content": {
                "subjective": {"chief_complaint": "...", "mood": "neutral"},
                "objective": {"presentation": "...", "mood_affect": "neutral"},
                "assessment": {"clinical_impression": "..."},
                "plan": {"interventions": "...", "homework": "..."}
            },
            "confidence_scores": {
                "subjective": 0.95,
                "objective": 0.88,
                "assessment": 0.92,
                "plan": 0.85
            },
            "missing_fields": {
                "plan": ["next_session_focus"]
            },
            "metadata": {
                "template_type": "soap",
                "extraction_source": "ai_extraction",
                "overall_confidence": 0.90
            }
        }
    """
    # Verify session exists and therapist has access
    session = await verify_session_access(session_id, current_user.id, db)

    # Verify session has extracted notes
    if not session.extracted_notes:
        logger.warning(f"Auto-fill attempted on unprocessed session {session_id}")
        raise HTTPException(
            status_code=400,
            detail="Session not yet processed. AI extraction must complete before auto-fill."
        )

    # Reconstruct ExtractedNotes from JSONB
    try:
        extracted_notes = ExtractedNotes(**session.extracted_notes)
    except Exception as e:
        logger.error(
            f"Failed to parse extracted_notes for session {session_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Invalid extracted notes format: {str(e)}"
        )

    # Call auto-fill service
    try:
        result = await autofill_service.fill_template(
            notes=extracted_notes,
            template_type=autofill_request.template_type
        )
    except ValueError as e:
        logger.warning(f"Auto-fill validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Auto-fill service failed for session {session_id}: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Auto-fill processing failed: {str(e)}"
        )

    logger.info(
        f"Auto-filled {autofill_request.template_type.value} template for session {session_id}",
        extra={
            "session_id": str(session_id),
            "therapist_id": str(current_user.id),
            "template_type": autofill_request.template_type.value,
            "overall_confidence": result['metadata']['overall_confidence'],
            "missing_fields_count": sum(len(fields) for fields in result['missing_fields'].values())
        }
    )

    # Return AutoFillResponse
    return AutoFillResponse(
        template_type=autofill_request.template_type,
        auto_filled_content=result['sections'],
        confidence_scores=result['confidence_scores'],
        missing_fields=result['missing_fields'],
        metadata=result['metadata']
    )


@router.get("/api/v1/sessions/{session_id}/notes", response_model=List[NoteResponse])
async def list_session_notes(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(require_role(["therapist"]))
):
    """
    List all notes for a specific therapy session.

    Returns all SessionNote records associated with a therapy session,
    ordered by creation date (newest first).

    Authorization:
        - Only therapists can view notes
        - Therapist must have active relationship with patient

    Args:
        session_id: UUID of therapy session
        db: Database session
        current_user: Authenticated therapist user

    Returns:
        List[NoteResponse]: All notes for this session

    Raises:
        HTTPException 404: Session not found
        HTTPException 403: Unauthorized access to session
    """
    # Verify session exists and therapist has access
    session = await verify_session_access(session_id, current_user.id, db)

    # Query all notes for this session
    result = await db.execute(
        select(db_models.SessionNote)
        .where(db_models.SessionNote.session_id == session_id)
        .order_by(db_models.SessionNote.created_at.desc())
    )
    notes = result.scalars().all()

    return [NoteResponse.model_validate(note) for note in notes]


@router.patch("/api/v1/notes/{note_id}", response_model=NoteResponse)
@limiter.limit("100/hour")
async def update_session_note(
    request: Request,
    note_id: UUID,
    note_update: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(require_role(["therapist"]))
):
    """
    Update an existing session note.

    Allows partial updates to note content and status. Therapist must have
    access to the session's patient to update notes.

    Authorization:
        - Only therapists can update notes
        - Therapist must have active relationship with patient

    Rate Limit:
        - 100 updates per hour per therapist
        - Allows frequent edits during documentation

    Args:
        note_id: UUID of note to update
        note_update: NoteUpdate schema with optional content/status
        db: Database session
        current_user: Authenticated therapist user

    Returns:
        NoteResponse: Updated note

    Raises:
        HTTPException 404: Note not found
        HTTPException 403: Unauthorized access to note
        HTTPException 400: Invalid update data
        HTTPException 429: Rate limit exceeded
    """
    # Load note with session relationship
    result = await db.execute(
        select(db_models.SessionNote)
        .where(db_models.SessionNote.id == note_id)
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Verify therapist has access to the session
    await verify_session_access(note.session_id, current_user.id, db)

    # Apply updates
    update_data = note_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(note, field, value)

    await db.commit()
    await db.refresh(note)

    logger.info(
        f"Updated session note {note_id}",
        extra={
            "note_id": str(note_id),
            "therapist_id": str(current_user.id),
            "updated_fields": list(update_data.keys())
        }
    )

    return NoteResponse.model_validate(note)
