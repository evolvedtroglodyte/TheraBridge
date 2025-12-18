"""
Session management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from typing import List, Optional
from datetime import datetime
import os
import shutil
from pathlib import Path
import asyncio
import hashlib
import logging

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.schemas import (
    SessionCreate, SessionResponse, SessionStatus,
    ExtractedNotes, ExtractNotesResponse, SessionTimelineResponse,
    TimelineEventCreate, TimelineEventResponse, TimelineSummaryResponse,
    TimelineChartDataResponse, UserRole
)
from app.models import db_models
from app.services.note_extraction import get_extraction_service, NoteExtractionService
from app.services.transcription import transcribe_audio_file
from app.validators import (
    sanitize_filename,
    validate_audio_file_header,
    validate_patient_exists,
    validate_session_exists,
    validate_positive_int
)
from app.middleware.rate_limit import limiter

# Configure logger for upload operations
logger = logging.getLogger(__name__)

router = APIRouter()

# File upload configuration
UPLOAD_DIR = Path("uploads/audio")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
ALLOWED_AUDIO_MIME_TYPES = {
    "audio/mpeg",      # .mp3
    "audio/wav",       # .wav
    "audio/x-wav",     # .wav (alternative)
    "audio/mp4",       # .m4a
    "audio/mpeg4",     # .m4a (alternative)
    "video/mp4",       # .mp4
    "audio/mpg",       # .mpeg
    "audio/mpeg3",     # .mpeg (alternative)
    "audio/x-mpeg",    # .mpeg (alternative)
    "audio/webm",      # .webm
    "video/webm"       # .webm (alternative)
}
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".mpga", ".webm"}


async def validate_audio_upload(file: UploadFile) -> None:
    """
    Validate audio file for upload.

    Checks:
    - File size does not exceed MAX_FILE_SIZE
    - File extension is in ALLOWED_EXTENSIONS
    - MIME type is audio/* or video/* (for container formats)

    Raises HTTPException with descriptive error message if validation fails.
    """
    # Validate filename exists
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file_ext}' not supported. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    # Validate MIME type
    if file.content_type:
        if not (file.content_type.startswith("audio/") or file.content_type.startswith("video/")):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid MIME type: {file.content_type}. Only audio files are accepted."
            )
        if file.content_type not in ALLOWED_AUDIO_MIME_TYPES:
            raise HTTPException(
                status_code=415,  # 415 Unsupported Media Type
                detail=f"MIME type '{file.content_type}' not supported. Allowed: audio/mpeg, audio/wav, audio/mp4, audio/webm, etc."
            )

    # Validate file size
    # Note: file.size is set for in-memory files; for streamed files, we validate during write
    if file.size and file.size > MAX_FILE_SIZE:
        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
        file_size_mb = file.size / (1024 * 1024)
        raise HTTPException(
            status_code=413,  # 413 Payload Too Large
            detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb:.0f}MB)"
        )


async def process_audio_pipeline(
    session_id: UUID,
    audio_path: str,
    db: AsyncSession
):
    """
    Background task to orchestrate audio processing pipeline.

    Executes the complete workflow: transcription -> note extraction -> database update.
    Updates session status at each stage and handles errors gracefully.

    Args:
        session_id: UUID of the session being processed
        audio_path: Absolute file system path to the audio file
        db: AsyncSession database connection for updates

    Processing Stages:
        1. Transcribing: Convert audio to text with timestamps
        2. Transcribed: Save transcript and segments to database
        3. Extracting Notes: Generate structured clinical notes from transcript
        4. Processed: Save extracted notes and update final status
        5. Failed: Capture error message if any stage fails

    Returns:
        None (updates database and status only)
    """
    try:
        # Update status: transcribing
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(status=SessionStatus.transcribing.value)
        )
        await db.commit()

        # Step 1: Transcribe audio
        logger.info("Starting transcription", extra={"session_id": str(session_id)})
        transcript_result = await transcribe_audio_file(audio_path)

        # Save transcript to database
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                transcript_text=transcript_result["full_text"],
                transcript_segments=transcript_result["segments"],
                duration_seconds=int(transcript_result.get("duration", 0)),
                status=SessionStatus.transcribed.value
            )
        )
        await db.commit()

        # Step 2: Extract notes
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(status=SessionStatus.extracting_notes.value)
        )
        await db.commit()

        logger.info("Starting note extraction", extra={"session_id": str(session_id)})
        extraction_service = get_extraction_service()
        notes = await extraction_service.extract_notes_from_transcript(
            transcript=transcript_result["full_text"],
            segments=transcript_result.get("segments")
        )

        # Save extracted notes
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                extracted_notes=notes.model_dump(),
                therapist_summary=notes.therapist_notes,
                patient_summary=notes.patient_summary,
                risk_flags=[flag.model_dump() for flag in notes.risk_flags],
                status=SessionStatus.processed.value
            )
        )
        await db.commit()

        logger.info("Session processing completed", extra={"session_id": str(session_id)})

        # Cleanup audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
            logger.debug("Audio file cleaned up", extra={"audio_path": audio_path})

    except Exception as e:
        logger.error("Pipeline processing failed", extra={"session_id": str(session_id), "error": str(e)}, exc_info=True)

        # Update status to failed
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                status=SessionStatus.failed.value,
                error_message=str(e)
            )
        )
        await db.commit()


@router.post("/upload", response_model=SessionResponse)
@limiter.limit("10/hour")
async def upload_audio_session(
    request: Request,
    patient_id: UUID,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an audio file and create a new therapy session record.

    Creates a session in the database and begins background processing (transcription
    and note extraction). Returns immediately with status="uploading"; client can poll
    the session endpoint to track progress.

    Rate Limit:
        - 10 uploads per hour per IP address
        - Prevents API quota exhaustion from excessive processing

    Validation:
        - Patient ID must exist in database
        - File size must not exceed 500MB
        - File extension must be in ALLOWED_EXTENSIONS
        - MIME type must be audio/* or video/* (for container formats)
        - File header (magic bytes) must match expected audio format
        - File must be at least 1KB in size

    Args:
        patient_id: UUID of the patient associated with this session
        file: Audio file upload (UploadFile from form-data)
        background_tasks: FastAPI BackgroundTasks for async processing
        db: AsyncSession database dependency

    Returns:
        SessionResponse: Newly created session with status="uploading"

    Raises:
        HTTPException 400: Invalid filename, unsupported extension, invalid MIME type, or file too small
        HTTPException 404: Patient ID not found
        HTTPException 413: File size exceeds 500MB
        HTTPException 415: Unsupported MIME type or file header doesn't match audio format
        HTTPException 429: Rate limit exceeded (too many uploads)
        HTTPException 500: No therapist found or file save failed
    """
    # Validate file early before database operations
    await validate_audio_upload(file)

    # Validate patient exists in database (prevents orphaned sessions)
    patient = await validate_patient_exists(patient_id, db)
    logger.info(f"[Upload] Validated patient: {patient.name} (ID: {patient_id})")

    # Get therapist (for MVP, use the seeded therapist)
    therapist_result = await db.execute(
        select(db_models.User).where(db_models.User.role == "therapist").limit(1)
    )
    therapist = therapist_result.scalar_one_or_none()
    if not therapist:
        raise HTTPException(500, "No therapist found in database")

    # Create session in database
    from datetime import datetime

    new_session = db_models.Session(
        patient_id=patient.id,
        therapist_id=therapist.id,
        session_date=datetime.utcnow(),
        audio_filename=file.filename,
        status=SessionStatus.uploading.value
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    # Save audio file with enhanced streaming, progress tracking, and checksum verification
    file_path = UPLOAD_DIR / f"{new_session.id}{Path(file.filename).suffix.lower()}"
    temp_path = file_path.with_suffix(file_path.suffix + ".tmp")

    try:
        # Write file with streaming size validation, progress tracking, and checksum
        bytes_written = 0
        chunk_count = 0
        sha256_hash = hashlib.sha256()
        chunk_size = 1024 * 1024  # 1MB chunks

        logger.info(f"[Upload] Starting upload for session {new_session.id}: {file.filename}")

        with open(temp_path, "wb") as buffer:
            while True:
                try:
                    chunk = await file.read(chunk_size)
                    if not chunk:
                        break

                    chunk_count += 1
                    bytes_written += len(chunk)

                    # Check file size during write (runtime validation for streamed uploads)
                    if bytes_written > MAX_FILE_SIZE:
                        buffer.close()
                        temp_path.unlink(missing_ok=True)
                        max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
                        file_size_mb = bytes_written / (1024 * 1024)
                        logger.warning(
                            f"[Upload] File size exceeded: {file_size_mb:.1f}MB > {max_size_mb:.0f}MB"
                        )
                        raise HTTPException(
                            status_code=413,
                            detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb:.0f}MB)"
                        )

                    # Write chunk and update checksum
                    buffer.write(chunk)
                    sha256_hash.update(chunk)

                    # Log progress every 50MB
                    if bytes_written % (50 * 1024 * 1024) < chunk_size:
                        progress_mb = bytes_written / (1024 * 1024)
                        logger.info(f"[Upload] Progress: {progress_mb:.1f}MB uploaded")

                except asyncio.TimeoutError:
                    buffer.close()
                    temp_path.unlink(missing_ok=True)
                    logger.error(f"[Upload] Timeout reading chunk {chunk_count}")
                    raise HTTPException(
                        status_code=408,
                        detail="Upload timeout - connection lost during file transfer"
                    )
                except Exception as chunk_error:
                    buffer.close()
                    temp_path.unlink(missing_ok=True)
                    logger.error(f"[Upload] Error reading chunk {chunk_count}: {str(chunk_error)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Upload failed during chunk {chunk_count}: {str(chunk_error)}"
                    )

        # Verify minimum file size (at least 1KB to ensure valid audio)
        if bytes_written < 1024:
            temp_path.unlink(missing_ok=True)
            logger.warning(f"[Upload] File too small: {bytes_written} bytes")
            raise HTTPException(
                status_code=400,
                detail=f"File too small ({bytes_written} bytes). Audio file must be at least 1KB."
            )

        # Move temp file to final location (atomic operation)
        temp_path.rename(file_path)

        # Validate file header (magic bytes) to ensure it's actually an audio file
        # This prevents attacks where malicious files are renamed with audio extensions
        try:
            detected_mime_type = validate_audio_file_header(file_path)
            logger.info(f"[Upload] File header validated: {detected_mime_type}")
        except HTTPException as header_error:
            # File header validation failed - delete the file and fail the upload
            file_path.unlink(missing_ok=True)
            logger.error(f"[Upload] File header validation failed: {header_error.detail}")
            raise

        file_checksum = sha256_hash.hexdigest()
        file_size_mb = bytes_written / (1024 * 1024)

        logger.info(
            "Audio file saved and validated",
            extra={
                "session_id": str(new_session.id),
                "file_size_mb": round(file_size_mb, 1),
                "file_path": str(file_path),
                "file_checksum": file_checksum,
                "chunk_count": chunk_count,
                "mime_type": detected_mime_type
            }
        )

        # Update session with file path
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == new_session.id)
            .values(audio_url=str(file_path))
        )
        await db.commit()

        # Start background processing
        background_tasks.add_task(
            process_audio_pipeline,
            session_id=new_session.id,
            audio_path=str(file_path),
            db=db
        )

        return SessionResponse.model_validate(new_session)

    except HTTPException:
        # Re-raise HTTP exceptions (validation errors, size limits, etc.)
        # Clean up any partial uploads
        temp_path.unlink(missing_ok=True)
        file_path.unlink(missing_ok=True)

        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == new_session.id)
            .values(
                status=SessionStatus.failed.value,
                error_message="Upload validation failed"
            )
        )
        await db.commit()
        raise

    except Exception as e:
        # Clean up on unexpected error
        logger.error(f"[Upload] Unexpected error for session {new_session.id}: {str(e)}")
        temp_path.unlink(missing_ok=True)
        file_path.unlink(missing_ok=True)

        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == new_session.id)
            .values(
                status=SessionStatus.failed.value,
                error_message=f"Upload failed: {str(e)}"
            )
        )
        await db.commit()

        raise HTTPException(500, f"Failed to save audio file: {str(e)}")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve a complete session record by ID.

    Fetches the full session data including transcript, extracted notes,
    and processing status from the database.

    Args:
        session_id: UUID of the session to retrieve
        db: AsyncSession database dependency

    Returns:
        SessionResponse: Complete session object with all data

    Raises:
        HTTPException 404: If session with given ID not found
    """
    result = await db.execute(
        select(db_models.Session).where(db_models.Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    return SessionResponse.model_validate(session)


@router.get("/{session_id}/notes", response_model=ExtractedNotes)
async def get_session_notes(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve extracted clinical notes for a specific session.

    Returns only the structured note extraction (without raw transcript).
    Useful for reading notes without the full session data.

    Args:
        session_id: UUID of the session
        db: AsyncSession database dependency

    Returns:
        ExtractedNotes: Structured clinical notes object

    Raises:
        HTTPException 404: If session not found or notes not yet extracted
    """
    result = await db.execute(
        select(db_models.Session).where(db_models.Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    if not session.extracted_notes:
        raise HTTPException(404, "Notes not yet extracted for this session")

    return ExtractedNotes(**session.extracted_notes)


@router.get("/", response_model=List[SessionResponse])
async def list_sessions(
    patient_id: Optional[UUID] = None,
    status: Optional[SessionStatus] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    List therapy sessions with optional filtering.

    Retrieves sessions ordered by date (newest first) with optional
    filtering by patient and processing status.

    Validation:
        - limit must be between 1 and 1000
        - patient_id must exist if provided

    Args:
        patient_id: Optional UUID to filter sessions by patient
        status: Optional SessionStatus to filter by processing status
        limit: Maximum number of results to return (default 50, max 1000)
        db: AsyncSession database dependency

    Returns:
        List[SessionResponse]: List of session records matching filters

    Raises:
        HTTPException 400: If limit is invalid
        HTTPException 404: If patient_id not found

    Query Examples:
        GET /sessions?patient_id=<uuid> - all sessions for a patient
        GET /sessions?status=processed - only completed sessions
        GET /sessions?patient_id=<uuid>&status=failed - failed sessions for a patient
    """
    # Validate limit parameter
    validated_limit = validate_positive_int(
        limit,
        field_name="limit",
        max_value=1000
    )

    query = select(db_models.Session).order_by(db_models.Session.session_date.desc())

    if patient_id:
        # Validate patient exists when filtering
        await validate_patient_exists(patient_id, db)
        query = query.where(db_models.Session.patient_id == patient_id)

    if status:
        query = query.where(db_models.Session.status == status.value)

    query = query.limit(validated_limit)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return [SessionResponse.model_validate(s) for s in sessions]


@router.get("/patients/{patient_id}/timeline", response_model=SessionTimelineResponse)
async def get_patient_timeline_endpoint(
    patient_id: UUID,
    event_types: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    importance: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20,
    cursor: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    """
    Get patient timeline with pagination and filtering.

    Retrieves timeline events for a specific patient with optional filtering
    by event types, date range, importance level, and text search. Uses
    cursor-based pagination for efficient browsing of large timelines.

    Authorization:
        - Patients: Can only access their own timeline
        - Therapists: Can only access timelines of assigned patients
        - Admins: Can access any patient's timeline

    Query Params:
        - event_types: Comma-separated event types (e.g., "session,milestone,clinical")
        - start_date: Filter from date (ISO 8601 format)
        - end_date: Filter to date (ISO 8601 format)
        - importance: Filter by importance level (low, normal, high, milestone)
        - search: Search in title/description (case-insensitive)
        - limit: Number of events per page (default 20, max 100)
        - cursor: Pagination cursor (last event ID from previous page)

    Returns:
        SessionTimelineResponse: Paginated timeline events with cursor for next page

    Raises:
        HTTPException 403: If user not authorized to access this patient's timeline
        HTTPException 404: If patient not found
    """
    # Import datetime for nested use
    from datetime import datetime as dt
    from sqlalchemy import and_

    # Authorization: Check if user has access to this patient's timeline
    if current_user.role == UserRole.patient:
        # Patients can only access their own timeline
        if current_user.id != patient_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this patient's timeline"
            )
    elif current_user.role == UserRole.therapist:
        # Therapists can only access assigned patients' timelines
        # Query the therapist_patients junction table
        therapist_patient_query = select(db_models.TherapistPatient).where(
            and_(
                db_models.TherapistPatient.therapist_id == current_user.id,
                db_models.TherapistPatient.patient_id == patient_id,
                db_models.TherapistPatient.is_active == True
            )
        )
        result = await db.execute(therapist_patient_query)
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this patient's timeline"
            )
    elif current_user.role == UserRole.admin:
        # Admins can access any patient's timeline
        pass
    else:
        raise HTTPException(
            status_code=403,
            detail="Invalid user role"
        )

    # Validate that patient exists
    patient_query = select(db_models.User).where(
        and_(db_models.User.id == patient_id, db_models.User.role == UserRole.patient.value)
    )
    patient_result = await db.execute(patient_query)
    patient = patient_result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=404,
            detail=f"Patient {patient_id} not found"
        )

    # Parse event_types from comma-separated string to list
    event_types_list = None
    if event_types:
        event_types_list = [t.strip() for t in event_types.split(',') if t.strip()]

    # Import timeline service
    from app.services.timeline import get_patient_timeline

    # Call timeline service with parsed parameters
    return await get_patient_timeline(
        patient_id=patient_id,
        db=db,
        event_types=event_types_list,
        start_date=start_date,
        end_date=end_date,
        importance=importance,
        search=search,
        limit=limit,
        cursor=cursor
    )


@router.post("/{session_id}/extract-notes", response_model=ExtractNotesResponse)
@limiter.limit("20/hour")
async def manually_extract_notes(
    request: Request,
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
    extraction_service: NoteExtractionService = Depends(get_extraction_service)
):
    """
    Manually trigger note extraction for a transcribed session.

    Useful for re-processing a session or if automatic extraction failed.
    Session must have transcript_text before extraction is possible.

    Rate Limit:
        - 20 extractions per hour per IP address
        - Prevents OpenAI API quota exhaustion from excessive re-processing

    Args:
        session_id: UUID of session to extract notes from
        db: AsyncSession database dependency
        extraction_service: NoteExtractionService injected dependency

    Returns:
        ExtractNotesResponse: Extracted notes and processing time

    Raises:
        HTTPException 404: If session not found
        HTTPException 400: If session has no transcript_text yet
        HTTPException 429: Rate limit exceeded (too many extractions)
    """
    result = await db.execute(
        select(db_models.Session).where(db_models.Session.id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(404, f"Session {session_id} not found")

    if not session.transcript_text:
        raise HTTPException(400, "Session must be transcribed before extracting notes")

    # Extract notes
    import time
    start_time = time.time()

    notes = await extraction_service.extract_notes_from_transcript(
        transcript=session.transcript_text,
        segments=session.transcript_segments
    )

    processing_time = time.time() - start_time

    # Save to database
    await db.execute(
        update(db_models.Session)
        .where(db_models.Session.id == session_id)
        .values(
            extracted_notes=notes.model_dump(),
            therapist_summary=notes.therapist_notes,
            patient_summary=notes.patient_summary,
            risk_flags=[flag.model_dump() for flag in notes.risk_flags],
            status=SessionStatus.processed.value
        )
    )
    await db.commit()

    return ExtractNotesResponse(
        extracted_notes=notes,
        processing_time=processing_time
    )


@router.post("/patients/{patient_id}/timeline", response_model=TimelineEventResponse, status_code=201)
async def create_timeline_event(
    patient_id: UUID,
    event_data: TimelineEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    """
    Create a manual timeline event for a patient.

    Allows therapists to add custom events like:
    - Milestones
    - Clinical observations
    - Significant moments
    - Administrative notes

    Request body: TimelineEventCreate schema

    Authorization: Only therapists assigned to the patient.
    """
    # Authorization: Only therapists can create manual events
    if current_user.role != UserRole.therapist:
        raise HTTPException(
            status_code=403,
            detail="Only therapists can create timeline events"
        )

    # Check therapist is assigned to patient
    from sqlalchemy import and_
    from app.models.db_models import TherapistPatient

    assignment_query = select(TherapistPatient).where(
        and_(
            TherapistPatient.therapist_id == current_user.id,
            TherapistPatient.patient_id == patient_id,
            TherapistPatient.is_active == True
        )
    )
    result = await db.execute(assignment_query)
    assignment = result.scalar_one_or_none()

    if not assignment:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to create events for this patient"
        )

    # Call timeline service
    from app.services.timeline import create_timeline_event as create_event

    return await create_event(
        patient_id=patient_id,
        event_data=event_data,
        therapist_id=current_user.id,
        db=db
    )


@router.get("/patients/{patient_id}/timeline/summary", response_model=TimelineSummaryResponse)
async def get_timeline_summary(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    """
    Get timeline summary statistics for a patient.

    Returns summary including:
    - First/last session dates
    - Total sessions and events
    - Events grouped by type
    - Milestones achieved
    - Recent highlights

    Authorization: Therapist assigned to patient or patient themselves.
    """
    # Authorization check: patient can view own data, therapist must be assigned
    if current_user.role == UserRole.patient:
        if current_user.id != patient_id:
            raise HTTPException(
                status_code=403,
                detail="Patients can only view their own timeline"
            )
    elif current_user.role == UserRole.therapist:
        # Check therapist is assigned to patient
        from sqlalchemy import and_
        from app.models.db_models import TherapistPatient

        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == patient_id,
                TherapistPatient.is_active == True
            )
        )
        result = await db.execute(assignment_query)
        assignment = result.scalar_one_or_none()

        if not assignment:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to view this patient's timeline"
            )
    else:
        raise HTTPException(
            status_code=403,
            detail="Invalid role for timeline access"
        )

    # Call timeline service
    from app.services.timeline import get_timeline_summary as fetch_summary

    return await fetch_summary(patient_id=patient_id, db=db)


@router.get("/patients/{patient_id}/timeline/chart-data", response_model=TimelineChartDataResponse)
async def get_timeline_chart_data(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    """
    Get chart visualization data for patient timeline.

    Returns data for:
    - Mood trend over time (monthly averages)
    - Session frequency per month
    - Milestone markers with dates and descriptions

    Authorization: Therapist assigned to patient or patient themselves.
    """
    # Authorization check
    if current_user.role == UserRole.patient:
        if current_user.id != patient_id:
            raise HTTPException(status_code=403, detail="Not authorized")
    elif current_user.role == UserRole.therapist:
        # Check therapist assignment
        from sqlalchemy import select, and_
        from app.models.db_models import TherapistPatient

        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == patient_id,
                TherapistPatient.is_active == True
            )
        )
        result = await db.execute(assignment_query)
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        raise HTTPException(status_code=403, detail="Invalid role")

    # Call timeline service
    from app.services.timeline import get_timeline_chart_data

    return await get_timeline_chart_data(patient_id=patient_id, db=db)
