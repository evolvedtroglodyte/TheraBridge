"""Upload endpoint for audio files"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.models.responses import JobResponse, JobStatus
from app.services.file_service import FileService
from app.services.queue_service import QueueService
from app.services.pipeline_service import PipelineService
from app.services.websocket_manager import ws_manager
from app.api.deps import get_file_service, get_queue_service, get_pipeline_service

router = APIRouter()

@router.post("/upload", response_model=JobResponse)
async def upload_audio(
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service),
    queue_service: QueueService = Depends(get_queue_service),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    Upload an audio file for transcription

    - **file**: Audio file (mp3, wav, m4a, ogg, flac, aac)

    Returns job_id to track processing status
    """
    # Save uploaded file
    job_id, file_path = await file_service.save_upload(file)

    # Define progress callback
    async def progress_callback(stage: str, progress: float):
        await queue_service.update_progress(job_id, stage, progress)
        await ws_manager.send_progress(job_id, stage, progress)

    # Add to processing queue
    # Note: Parameters after task_func are passed to run_transcription
    await queue_service.add_job(
        job_id,  # Queue tracking
        file.filename,  # Queue tracking
        pipeline_service.run_transcription,  # The async function to run
        job_id,  # First arg to run_transcription
        file_path,  # Second arg (audio_file_path)
        "en",  # Third arg (language) - ISO-639-1 format required by OpenAI
        progress_callback  # Fourth arg (progress_callback)
    )

    return JobResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        message=f"File '{file.filename}' uploaded successfully. Processing started."
    )
