"""
Export endpoints for generating and downloading reports

This module provides REST API endpoints for:
- Creating export jobs for session notes, progress reports, treatment summaries, and full records
- Managing export jobs (list, get status, delete)
- Downloading completed exports with audit logging
- Managing custom export templates (future)
"""
import logging
from pathlib import Path
from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.auth.dependencies import require_role
from app.models.db_models import User
from app.models.export_models import ExportJob, ExportTemplate, ExportAuditLog
from app.schemas.export_schemas import (
    SessionNotesExportRequest,
    ProgressReportExportRequest,
    TreatmentSummaryExportRequest,
    FullRecordExportRequest,
    ExportJobResponse,
    ExportTemplateResponse,
    ExportTemplateCreate
)
from app.services.export_service import ExportService, get_export_service
from app.services.pdf_generator import get_pdf_generator
from app.services.docx_generator import get_docx_generator
from app.middleware.rate_limit import limiter

router = APIRouter(prefix="/export", tags=["export"])
logger = logging.getLogger(__name__)


async def process_export_job(
    job_id: UUID,
    export_type: str,
    request_data: dict,
    db: AsyncSession
):
    """
    Background task to process export job.

    Updates job status from pending → processing → completed/failed.
    Generates export file, saves to exports/output/, and creates audit log.

    Args:
        job_id: UUID of the export job to process
        export_type: Type of export (session_notes, progress_report, timeline, etc.)
        request_data: Dictionary containing export parameters
        db: Database session

    Side effects:
        - Updates ExportJob status in database
        - Saves export file to exports/output/ directory
        - Creates ExportAuditLog entry on completion
    """
    try:
        # Update status: processing
        await db.execute(
            update(ExportJob)
            .where(ExportJob.id == job_id)
            .values(status='processing', started_at=datetime.utcnow())
        )
        await db.commit()

        # Initialize services
        pdf_gen = get_pdf_generator()
        docx_gen = get_docx_generator()
        export_service = get_export_service(pdf_gen, docx_gen)

        # Gather data based on export type
        if export_type == 'session_notes':
            context = await export_service.gather_session_notes_data(
                request_data['session_ids'],
                db
            )
        elif export_type == 'progress_report':
            context = await export_service.gather_progress_report_data(
                request_data['patient_id'],
                request_data['start_date'],
                request_data['end_date'],
                db
            )
        elif export_type == 'timeline':
            context = await export_service.gather_timeline_data(
                request_data['patient_id'],
                request_data.get('start_date'),
                request_data.get('end_date'),
                request_data.get('event_types'),
                request_data.get('include_private', True),
                db
            )
        # Future export types will be added here
        # elif export_type == 'treatment_summary':
        #     context = await export_service.gather_treatment_summary_data(...)
        # elif export_type == 'full_record':
        #     context = await export_service.gather_full_record_data(...)
        else:
            raise ValueError(f"Unsupported export type: {export_type}")

        # Generate export file
        file_bytes = await export_service.generate_export(
            export_type,
            request_data['format'],
            context,
            request_data.get('template_id'),
            db
        )

        # Save file to exports/output/ directory
        file_ext = request_data['format']
        file_path = export_service.export_dir / f"{job_id}.{file_ext}"

        file_path.write_bytes(file_bytes)

        # Update job status: completed
        await db.execute(
            update(ExportJob)
            .where(ExportJob.id == job_id)
            .values(
                status='completed',
                file_path=str(file_path),
                file_size_bytes=len(file_bytes),
                completed_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=7)  # Files auto-delete after 7 days
            )
        )
        await db.commit()

        # Create audit log entry for HIPAA compliance
        job = await db.get(ExportJob, job_id)
        audit_entry = ExportAuditLog(
            export_job_id=job_id,
            user_id=job.user_id,
            patient_id=job.patient_id,
            action='created'
        )
        db.add(audit_entry)
        await db.commit()

        logger.info(f"Export job completed successfully", extra={
            "job_id": str(job_id),
            "export_type": export_type,
            "file_size_bytes": len(file_bytes)
        })

    except Exception as e:
        logger.error(f"Export job failed", extra={
            "job_id": str(job_id),
            "export_type": export_type,
            "error": str(e)
        }, exc_info=True)

        # Update job status: failed
        await db.execute(
            update(ExportJob)
            .where(ExportJob.id == job_id)
            .values(status='failed', error_message=str(e))
        )
        await db.commit()


# ============================================================================
# Export Endpoints (Create Export Jobs)
# ============================================================================

@router.post("/session-notes", response_model=ExportJobResponse)
@limiter.limit("20/hour")
async def export_session_notes(
    request: Request,
    data: SessionNotesExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Export session notes in PDF, DOCX, JSON, or CSV format.

    Creates an export job that runs in the background. Returns immediately
    with job ID that can be used to check status and download the file.

    **Rate Limit:** 20 exports per hour per user

    **Export Options:**
    - include_transcript: Include full transcript in export
    - include_ai_notes: Include AI-extracted notes
    - include_action_items: Include action items

    **Example Request:**
    ```json
    {
      "session_ids": ["550e8400-e29b-41d4-a716-446655440000"],
      "format": "pdf",
      "template_id": null,
      "options": {
        "include_transcript": true,
        "include_ai_notes": true,
        "include_action_items": true
      }
    }
    ```
    """
    logger.info(f"Session notes export requested", extra={
        "user_id": str(current_user.id),
        "session_count": len(data.session_ids),
        "format": data.format
    })

    # Create export job record
    job = ExportJob(
        user_id=current_user.id,
        template_id=data.template_id,
        export_type='session_notes',
        format=data.format,
        status='pending',
        parameters=data.model_dump()
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Queue background processing
    background_tasks.add_task(
        process_export_job,
        job.id,
        'session_notes',
        data.model_dump(),
        db
    )

    return ExportJobResponse(
        id=job.id,
        export_type=job.export_type,
        format=job.format,
        status=job.status,
        created_at=job.created_at
    )


@router.post("/progress-report", response_model=ExportJobResponse)
@limiter.limit("20/hour")
async def export_progress_report(
    request: Request,
    data: ProgressReportExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Export patient progress report for a specific date range.

    **Rate Limit:** 20 exports per hour per user

    **Report Sections:**
    - patient_info: Demographics and contact information
    - treatment_goals: Current treatment goals
    - goal_progress: Progress tracking for each goal
    - assessments: Clinical assessments during period
    - session_summary: Summary of all sessions in date range
    - clinical_observations: Therapist observations
    - recommendations: Treatment recommendations

    **Example Request:**
    ```json
    {
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "start_date": "2025-01-01",
      "end_date": "2025-03-31",
      "format": "pdf",
      "include_sections": {
        "patient_info": true,
        "treatment_goals": true,
        "goal_progress": true,
        "session_summary": true
      }
    }
    ```
    """
    logger.info(f"Progress report export requested", extra={
        "user_id": str(current_user.id),
        "patient_id": str(data.patient_id),
        "start_date": str(data.start_date),
        "end_date": str(data.end_date),
        "format": data.format
    })

    # Create export job record
    job = ExportJob(
        user_id=current_user.id,
        patient_id=data.patient_id,
        export_type='progress_report',
        format=data.format,
        status='pending',
        parameters=data.model_dump()
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Queue background processing
    background_tasks.add_task(
        process_export_job,
        job.id,
        'progress_report',
        data.model_dump(),
        db
    )

    return ExportJobResponse(
        id=job.id,
        export_type=job.export_type,
        format=job.format,
        status=job.status,
        patient_name=None,  # TODO: Fetch patient name from database
        created_at=job.created_at
    )


@router.post("/treatment-summary", response_model=ExportJobResponse)
@limiter.limit("20/hour")
async def export_treatment_summary(
    request: Request,
    data: TreatmentSummaryExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Export comprehensive treatment summary for insurance, transfer, or records.

    **Status:** STUB - To be implemented in Phase 4

    **Purpose Options:**
    - insurance: Formatted for insurance claims/authorization
    - transfer: Formatted for care transfer to another provider
    - records: Formatted for patient medical records

    **Rate Limit:** 20 exports per hour per user
    """
    # TODO: Implement in Phase 4
    # For now, return a placeholder job that will fail with "Not implemented"
    raise HTTPException(
        status_code=501,
        detail="Treatment summary export not yet implemented. Coming in Phase 4."
    )


@router.post("/full-record", response_model=ExportJobResponse)
@limiter.limit("10/hour")
async def export_full_record(
    request: Request,
    data: FullRecordExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Export complete patient record (all sessions, transcripts, notes, goals, etc.)

    **Status:** STUB - To be implemented in Phase 4

    **Rate Limit:** 10 exports per hour per user (lower due to large data volume)

    **Warning:** This export can be very large and may take several minutes to generate.
    Only use for complete record transfer or legal requests.
    """
    # TODO: Implement in Phase 4
    raise HTTPException(
        status_code=501,
        detail="Full record export not yet implemented. Coming in Phase 4."
    )


# ============================================================================
# Job Management Endpoints
# ============================================================================

@router.get("/jobs", response_model=List[ExportJobResponse])
async def list_export_jobs(
    status: str = None,
    patient_id: UUID = None,
    limit: int = 100,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    List export jobs for current user.

    **Query Parameters:**
    - status: Filter by job status (pending, processing, completed, failed)
    - patient_id: Filter by patient ID
    - limit: Maximum number of jobs to return (default: 100, max: 500)

    **Example Response:**
    ```json
    [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "export_type": "session_notes",
        "format": "pdf",
        "status": "completed",
        "created_at": "2025-12-17T10:30:00Z",
        "completed_at": "2025-12-17T10:30:15Z",
        "file_size_bytes": 245678,
        "expires_at": "2025-12-24T10:30:15Z",
        "download_url": "/api/v1/export/download/550e8400-e29b-41d4-a716-446655440000"
      }
    ]
    ```
    """
    # Build query with filters
    query = (
        select(ExportJob)
        .where(ExportJob.user_id == current_user.id)
        .order_by(ExportJob.created_at.desc())
    )

    if status:
        query = query.where(ExportJob.status == status)

    if patient_id:
        query = query.where(ExportJob.patient_id == patient_id)

    # Apply limit (cap at 500)
    limit = min(limit, 500)
    query = query.limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    # Add download URLs for completed jobs
    responses = []
    for job in jobs:
        response = ExportJobResponse.model_validate(job)
        if job.status == 'completed':
            response.download_url = f"/api/v1/export/download/{job.id}"
        responses.append(response)

    return responses


@router.get("/jobs/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: UUID,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Get export job status and details.

    Use this endpoint to poll for job completion. When status is 'completed',
    the response will include a download_url.

    **Typical Flow:**
    1. POST /export/session-notes → Get job_id
    2. GET /export/jobs/{job_id} → Poll until status is 'completed'
    3. GET /export/download/{job_id} → Download the file

    **Status Values:**
    - pending: Job queued, not yet started
    - processing: Job is currently being generated
    - completed: Job finished successfully, file ready for download
    - failed: Job failed, check error_message
    """
    job = await db.get(ExportJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this export job")

    # Build response
    response = ExportJobResponse.model_validate(job)
    if job.status == 'completed':
        response.download_url = f"/api/v1/export/download/{job_id}"

    return response


@router.delete("/jobs/{job_id}")
async def delete_export_job(
    job_id: UUID,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete export job and associated file.

    This permanently deletes the export file from storage and removes
    the job record. Audit logs are preserved for compliance.

    **Note:** Files are automatically deleted after 7 days. Manual deletion
    is only needed if you want to free up storage immediately or remove
    sensitive data.
    """
    job = await db.get(ExportJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this export job")

    # Delete file from filesystem if exists
    if job.file_path:
        file_path = Path(job.file_path)
        if file_path.exists():
            try:
                file_path.unlink()
                logger.info(f"Deleted export file", extra={
                    "job_id": str(job_id),
                    "file_path": str(file_path)
                })
            except Exception as e:
                logger.error(f"Failed to delete export file", extra={
                    "job_id": str(job_id),
                    "file_path": str(file_path),
                    "error": str(e)
                })

    # Create audit log before deletion (for HIPAA compliance)
    audit_entry = ExportAuditLog(
        export_job_id=job_id,
        user_id=current_user.id,
        patient_id=job.patient_id,
        action='deleted'
    )
    db.add(audit_entry)

    # Delete job record (cascade will delete associated audit logs)
    await db.delete(job)
    await db.commit()

    logger.info(f"Export job deleted", extra={
        "job_id": str(job_id),
        "user_id": str(current_user.id)
    })

    return {"message": "Export job deleted successfully"}


# ============================================================================
# Download Endpoint
# ============================================================================

@router.get("/download/{job_id}")
async def download_export(
    job_id: UUID,
    request: Request,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Download completed export file.

    **HIPAA Compliance:** This endpoint creates an audit log entry recording:
    - Who downloaded the file (user_id)
    - When it was downloaded (timestamp)
    - From where it was downloaded (IP address)
    - What user agent was used (browser/app info)

    **Headers:**
    - Content-Disposition: attachment; filename=export_session_notes_{job_id}.pdf
    - X-Export-Job-ID: {job_id}

    **Returns:** FileResponse with appropriate MIME type for the export format
    """
    job = await db.get(ExportJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to this export file")

    if job.status != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Export not ready. Current status: {job.status}"
        )

    if not job.file_path or not Path(job.file_path).exists():
        raise HTTPException(
            status_code=404,
            detail="Export file not found on disk. It may have been deleted or expired."
        )

    # Create audit log entry for HIPAA compliance
    audit_entry = ExportAuditLog(
        export_job_id=job_id,
        user_id=current_user.id,
        patient_id=job.patient_id,
        action='downloaded',
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get('user-agent')
    )
    db.add(audit_entry)
    await db.commit()

    logger.info(f"Export file downloaded", extra={
        "job_id": str(job_id),
        "user_id": str(current_user.id),
        "ip_address": request.client.host if request.client else None
    })

    # Generate download filename
    filename = f"export_{job.export_type}_{job_id}.{job.format}"

    # Return file for download
    return FileResponse(
        path=job.file_path,
        filename=filename,
        media_type=_get_media_type(job.format),
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Job-ID": str(job_id)
        }
    )


# ============================================================================
# Template Management Endpoints (Stubs for Phase 4)
# ============================================================================

@router.get("/templates", response_model=List[ExportTemplateResponse])
async def list_templates(
    export_type: str = None,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    List available export templates (system + user custom).

    **Status:** STUB - To be implemented in Phase 4

    System templates are provided by default and cannot be modified.
    Users can create custom templates for personalized formatting.

    **Query Parameters:**
    - export_type: Filter by export type (session_notes, progress_report, etc.)
    """
    # TODO: Implement in Phase 4
    # For now, return empty list
    return []


@router.post("/templates", response_model=ExportTemplateResponse)
async def create_template(
    data: ExportTemplateCreate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create custom export template.

    **Status:** STUB - To be implemented in Phase 4

    Custom templates allow therapists to define their own formatting,
    branding, and section organization for exports.

    **Template Format:** HTML with Jinja2 templating syntax
    """
    # TODO: Implement in Phase 4
    raise HTTPException(
        status_code=501,
        detail="Custom templates not yet implemented. Coming in Phase 4."
    )


# ============================================================================
# Helper Functions
# ============================================================================

def _get_media_type(format: str) -> str:
    """
    Get MIME type for export format.

    Args:
        format: Export format (pdf, docx, json, csv)

    Returns:
        MIME type string (e.g., 'application/pdf')
    """
    types = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'json': 'application/json',
        'csv': 'text/csv'
    }
    return types.get(format, 'application/octet-stream')
