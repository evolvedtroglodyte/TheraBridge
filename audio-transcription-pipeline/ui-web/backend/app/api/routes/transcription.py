"""Transcription endpoints for retrieving results"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from app.models.responses import TranscriptionResult, JobListResponse, JobStatus
from app.services.queue_service import QueueService
from app.services.pipeline_service import PipelineService
from app.services.file_service import FileService
from app.api.deps import get_queue_service, get_pipeline_service, get_file_service

router = APIRouter()

@router.get("/transcriptions/{job_id}", response_model=TranscriptionResult)
async def get_transcription(
    job_id: str,
    queue_service: QueueService = Depends(get_queue_service),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    Get transcription result by job ID

    - **job_id**: Unique job identifier returned from upload

    Returns complete transcription result including segments and metadata
    """
    # Check queue for job status
    job_info = queue_service.get_job(job_id)

    if not job_info:
        # Try loading from disk
        result = pipeline_service.get_result(job_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        return result

    # Job is in queue - check status
    if job_info.status == JobStatus.COMPLETED:
        result = pipeline_service.get_result(job_id)
        if not result:
            raise HTTPException(status_code=500, detail="Result file not found")
        return result

    elif job_info.status == JobStatus.FAILED:
        raise HTTPException(status_code=500, detail=f"Job failed: {job_info.error}")

    else:
        # Job is still processing or pending
        return TranscriptionResult(
            id=job_id,
            status=job_info.status,
            filename=job_info.filename,
            created_at=job_info.created_at,
            metadata=None,
            performance=None,
            speakers=[],
            segments=[]
        )

@router.get("/transcriptions", response_model=JobListResponse)
async def list_transcriptions(
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    List all transcription jobs

    Returns list of all completed transcriptions
    """
    results = pipeline_service.list_results()

    return JobListResponse(
        jobs=[TranscriptionResult(**result) for result in results],
        total=len(results)
    )

@router.delete("/transcriptions/{job_id}")
async def delete_transcription(
    job_id: str,
    queue_service: QueueService = Depends(get_queue_service),
    pipeline_service: PipelineService = Depends(get_pipeline_service),
    file_service: FileService = Depends(get_file_service)
):
    """
    Delete a transcription job and its associated files

    - **job_id**: Unique job identifier

    Returns success message
    """
    # Cancel if running
    await queue_service.cancel_job(job_id)

    # Remove from queue
    await queue_service.remove_job(job_id)

    # Delete result file
    pipeline_service.delete_result(job_id)

    # Delete uploaded files
    try:
        file_service.delete_job_files(job_id)
    except:
        pass  # Ignore if files don't exist

    return {"message": f"Job {job_id} deleted successfully"}

@router.get("/transcriptions/{job_id}/status")
async def get_job_status(
    job_id: str,
    queue_service: QueueService = Depends(get_queue_service),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    Get current status of a job

    - **job_id**: Unique job identifier

    Returns status, progress, and stage information
    """
    job_info = queue_service.get_job(job_id)

    if not job_info:
        # Check if completed job exists on disk
        result = pipeline_service.get_result(job_id)
        if result:
            return {
                "job_id": job_id,
                "status": "completed",
                "progress": 1.0,
                "stage": "completed"
            }

        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return {
        "job_id": job_id,
        "status": job_info.status.value,
        "progress": job_info.progress,
        "stage": job_info.stage,
        "error": job_info.error
    }
