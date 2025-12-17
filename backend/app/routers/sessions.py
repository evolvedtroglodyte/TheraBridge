"""
Session management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from typing import List, Optional
import os
import shutil
from pathlib import Path
import asyncio

from app.database import get_db
from app.models.schemas import (
    SessionCreate, SessionResponse, SessionStatus,
    ExtractedNotes, ExtractNotesResponse
)
from app.models import db_models
from app.services.note_extraction import get_extraction_service
from app.services.transcription import transcribe_audio_file

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
    Background task to process audio: transcribe → extract notes

    This runs asynchronously after audio upload.
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
        print(f"[Pipeline] Transcribing session {session_id}...")
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

        print(f"[Pipeline] Extracting notes for session {session_id}...")
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

        print(f"[Pipeline] Session {session_id} processed successfully!")

        # Cleanup audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"[Pipeline] Cleaned up audio file: {audio_path}")

    except Exception as e:
        print(f"[Pipeline] Error processing session {session_id}: {str(e)}")

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
async def upload_audio_session(
    patient_id: UUID,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload an audio file to create a new session

    This will:
    1. Validate file size (max 500MB) and type (audio/* MIME types only)
    2. Create session record in database
    3. Save audio file
    4. Start background processing (transcription + extraction)

    Returns immediately with session_id and status="uploading"

    Raises:
    - 400: Invalid filename, extension, or MIME type
    - 413: File size exceeds 500MB
    - 415: Unsupported MIME type
    """
    # Validate file early before database operations
    await validate_audio_upload(file)

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
        patient_id=patient_id,
        therapist_id=therapist.id,
        session_date=datetime.utcnow(),
        audio_filename=file.filename,
        status=SessionStatus.uploading.value
    )

    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    # Save audio file
    file_path = UPLOAD_DIR / f"{new_session.id}{file_ext}"

    try:
        # Write file with streaming size validation
        bytes_written = 0
        with open(file_path, "wb") as buffer:
            chunk_size = 1024 * 1024  # 1MB chunks
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break
                bytes_written += len(chunk)

                # Check file size during write (runtime validation for streamed uploads)
                if bytes_written > MAX_FILE_SIZE:
                    buffer.close()
                    file_path.unlink()
                    max_size_mb = MAX_FILE_SIZE / (1024 * 1024)
                    file_size_mb = bytes_written / (1024 * 1024)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb:.0f}MB)"
                    )

                buffer.write(chunk)

        print(f"[Upload] Saved audio file: {file_path} ({bytes_written / (1024*1024):.1f}MB)")

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

    except Exception as e:
        # Clean up on error
        if file_path.exists():
            file_path.unlink()

        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == new_session.id)
            .values(
                status=SessionStatus.failed.value,
                error_message=str(e)
            )
        )
        await db.commit()

        raise HTTPException(500, f"Failed to save audio file: {str(e)}")


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get complete session data including extracted notes"""
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
    """Get just the extracted notes for a session"""
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
    """List sessions with optional filters"""
    query = select(db_models.Session).order_by(db_models.Session.session_date.desc())

    if patient_id:
        query = query.where(db_models.Session.patient_id == patient_id)

    if status:
        query = query.where(db_models.Session.status == status.value)

    query = query.limit(limit)

    result = await db.execute(query)
    sessions = result.scalars().all()

    return [SessionResponse.model_validate(s) for s in sessions]


@router.post("/{session_id}/extract-notes", response_model=ExtractNotesResponse)
async def manually_extract_notes(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger note extraction for a transcribed session

    Useful for re-processing or if automatic extraction failed
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

    extraction_service = get_extraction_service()
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
