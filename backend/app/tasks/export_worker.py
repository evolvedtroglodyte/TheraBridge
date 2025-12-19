"""
Export background worker for processing timeline export jobs

Handles background processing of export jobs created via the timeline export endpoint.
Generates PDF, DOCX, or JSON files from patient timeline data.
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.export_models import ExportJob, ExportAuditLog
from app.models.db_models import User, TherapySession
from app.services.pdf_generator import PDFGeneratorService
from app.services.docx_generator import DOCXGeneratorService

logger = logging.getLogger(__name__)

# Export output directory
EXPORT_OUTPUT_DIR = Path("exports/output")
EXPORT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def process_timeline_export(
    job_id: UUID,
    patient_id: UUID,
    format: str,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    db: AsyncSession
):
    """
    Background task to process timeline export job.

    Args:
        job_id: ExportJob ID
        patient_id: Patient UUID
        format: Export format (pdf, docx, json)
        start_date: Optional start date filter
        end_date: Optional end date filter
        db: Database session

    Process:
        1. Fetch export job from database
        2. Fetch timeline data (therapy sessions) for patient
        3. Generate export file in requested format
        4. Save file to disk
        5. Update job status and file_path
        6. Create audit log entry
        7. Set expiration timestamp (7 days)
    """
    try:
        logger.info(
            f"Starting timeline export processing",
            extra={
                "job_id": str(job_id),
                "patient_id": str(patient_id),
                "format": format
            }
        )

        # Step 1: Fetch export job
        job_query = select(ExportJob).where(ExportJob.id == job_id)
        job_result = await db.execute(job_query)
        job = job_result.scalar_one_or_none()

        if not job:
            logger.error(f"Export job not found: {job_id}")
            return

        # Update status to processing
        job.status = "processing"
        job.started_at = datetime.utcnow()
        await db.commit()

        # Step 2: Fetch patient data
        patient_query = select(User).where(User.id == patient_id)
        patient_result = await db.execute(patient_query)
        patient = patient_result.scalar_one_or_none()

        if not patient:
            await _mark_job_failed(
                job,
                f"Patient not found: {patient_id}",
                db
            )
            return

        # Step 3: Fetch timeline data (therapy sessions)
        timeline_data = await _fetch_timeline_data(
            patient_id,
            start_date,
            end_date,
            db
        )

        if not timeline_data:
            logger.warning(f"No timeline data found for patient {patient_id}")

        # Step 4: Generate export file
        file_path, file_size = await _generate_export_file(
            patient=patient,
            timeline_data=timeline_data,
            format=format,
            job_id=job_id,
            start_date=start_date,
            end_date=end_date
        )

        # Step 5: Update job status
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.file_path = str(file_path)
        job.file_size = file_size
        job.expires_at = datetime.utcnow() + timedelta(days=7)
        await db.commit()

        # Step 6: Create audit log
        audit_log = ExportAuditLog(
            export_job_id=job.id,
            user_id=job.user_id,
            action="export_completed",
            details={
                "patient_id": str(patient_id),
                "format": format,
                "file_size": file_size,
                "session_count": len(timeline_data)
            }
        )
        db.add(audit_log)
        await db.commit()

        logger.info(
            f"Timeline export completed successfully",
            extra={
                "job_id": str(job_id),
                "file_path": str(file_path),
                "file_size_kb": round(file_size / 1024, 2),
                "session_count": len(timeline_data)
            }
        )

    except Exception as e:
        logger.error(
            f"Timeline export failed: {str(e)}",
            extra={"job_id": str(job_id)},
            exc_info=True
        )

        # Mark job as failed
        if 'job' in locals():
            await _mark_job_failed(job, str(e), db)


async def _fetch_timeline_data(
    patient_id: UUID,
    start_date: Optional[datetime],
    end_date: Optional[datetime],
    db: AsyncSession
) -> list:
    """
    Fetch therapy sessions for patient within date range.
    Uses eager loading to prevent N+1 queries when accessing patient/therapist relationships.

    Returns:
        List of session dictionaries with timeline data
    """
    from sqlalchemy.orm import joinedload

    query = select(TherapySession).where(
        TherapySession.patient_id == patient_id
    )

    if start_date:
        query = query.where(TherapySession.session_date >= start_date)
    if end_date:
        query = query.where(TherapySession.session_date <= end_date)

    # Add eager loading to prevent N+1 queries
    query = query.options(joinedload(TherapySession.patient))
    query = query.options(joinedload(TherapySession.therapist))
    query = query.order_by(TherapySession.session_date.desc())

    result = await db.execute(query)
    sessions = result.scalars().unique().all()

    # Convert to dictionaries
    timeline_data = []
    for session in sessions:
        timeline_data.append({
            "id": str(session.id),
            "date": session.session_date,
            "title": f"Session {session.session_number}" if hasattr(session, 'session_number') else f"Session on {session.session_date.strftime('%Y-%m-%d')}",
            "therapist_notes": session.therapist_notes if hasattr(session, 'therapist_notes') else "",
            "patient_summary": session.patient_summary if hasattr(session, 'patient_summary') else "",
            "session_type": session.session_type if hasattr(session, 'session_type') else "standard",
            "duration_minutes": session.duration_minutes if hasattr(session, 'duration_minutes') else None
        })

    return timeline_data


async def _generate_export_file(
    patient: User,
    timeline_data: list,
    format: str,
    job_id: UUID,
    start_date: Optional[datetime],
    end_date: Optional[datetime]
) -> tuple[Path, int]:
    """
    Generate export file in requested format.

    Returns:
        Tuple of (file_path, file_size_bytes)
    """
    filename = f"timeline_export_{patient.id}_{job_id}.{format}"
    file_path = EXPORT_OUTPUT_DIR / filename

    if format == "json":
        # JSON export
        export_data = {
            "patient": {
                "id": str(patient.id),
                "name": f"{patient.first_name} {patient.last_name}",
                "email": patient.email
            },
            "export_date": datetime.utcnow().isoformat(),
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            },
            "timeline": timeline_data
        }

        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)

        file_size = file_path.stat().st_size
        return file_path, file_size

    elif format == "pdf":
        # PDF export
        pdf_generator = PDFGeneratorService()

        context = {
            "patient": {
                "name": f"{patient.first_name} {patient.last_name}",
                "id": str(patient.id)
            },
            "date_range": {
                "start": start_date.strftime("%B %d, %Y") if start_date else "Beginning",
                "end": end_date.strftime("%B %d, %Y") if end_date else "Present"
            },
            "timeline": timeline_data,
            "generated_at": datetime.utcnow()
        }

        pdf_bytes = await pdf_generator.generate_from_template(
            "timeline_export.html",
            context
        )

        with open(file_path, 'wb') as f:
            f.write(pdf_bytes)

        file_size = len(pdf_bytes)
        return file_path, file_size

    elif format == "docx":
        # DOCX export
        docx_generator = DOCXGeneratorService()

        # Convert timeline data to format expected by DOCX generator
        sessions = []
        for item in timeline_data:
            sessions.append({
                "date": item["date"],
                "type": item.get("session_type", "standard"),
                "summary": item.get("therapist_notes", ""),
                "duration": item.get("duration_minutes")
            })

        docx_bytes = await docx_generator.generate_progress_report(
            patient={
                "name": f"{patient.first_name} {patient.last_name}",
                "id": str(patient.id)
            },
            therapist={"name": "Therapist"},  # TODO: Fetch actual therapist
            goals=[],  # Timeline export doesn't include goals
            sessions=sessions,
            date_range={
                "start_date": start_date or datetime.min,
                "end_date": end_date or datetime.utcnow()
            },
            include_sections={
                "sessions": True,
                "goals": False
            }
        )

        with open(file_path, 'wb') as f:
            f.write(docx_bytes)

        file_size = len(docx_bytes)
        return file_path, file_size

    else:
        raise ValueError(f"Unsupported export format: {format}")


async def _mark_job_failed(
    job: ExportJob,
    error_message: str,
    db: AsyncSession
):
    """Mark export job as failed with error message"""
    job.status = "failed"
    job.completed_at = datetime.utcnow()
    job.error_message = error_message
    await db.commit()

    logger.error(
        f"Export job marked as failed",
        extra={
            "job_id": str(job.id),
            "error": error_message
        }
    )


async def cleanup_expired_exports(db: AsyncSession) -> int:
    """
    Clean up expired export files (older than 7 days).

    Returns:
        Number of files deleted
    """
    now = datetime.utcnow()

    # Find expired jobs
    query = select(ExportJob).where(
        ExportJob.expires_at <= now,
        ExportJob.status == "completed"
    )

    result = await db.execute(query)
    expired_jobs = result.scalars().all()

    deleted_count = 0

    for job in expired_jobs:
        try:
            # Delete file from disk
            if job.file_path:
                file_path = Path(job.file_path)
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted expired export file: {file_path}")
                    deleted_count += 1

            # Update job record
            job.status = "expired"
            job.file_path = None

        except Exception as e:
            logger.error(
                f"Failed to delete expired export: {e}",
                extra={"job_id": str(job.id)}
            )

    await db.commit()

    logger.info(f"Cleaned up {deleted_count} expired export files")
    return deleted_count
