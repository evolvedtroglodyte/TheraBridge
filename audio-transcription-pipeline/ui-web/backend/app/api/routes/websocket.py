"""WebSocket endpoint for real-time job updates"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.services.websocket_manager import ws_manager
from app.services.queue_service import QueueService
from app.services.pipeline_service import PipelineService
from app.api.deps import get_queue_service, get_pipeline_service
from app.models.responses import JobStatus
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/transcription/{job_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    job_id: str,
    queue_service: QueueService = Depends(get_queue_service),
    pipeline_service: PipelineService = Depends(get_pipeline_service)
):
    """
    WebSocket endpoint for real-time transcription progress

    Connect with: ws://host:port/ws/transcription/{job_id}

    Receives messages:
    - {"type": "progress", "job_id": "...", "stage": "...", "progress": 0.5}
    - {"type": "completed", "job_id": "...", "result": {...}}
    - {"type": "error", "job_id": "...", "error": "..."}
    """
    await ws_manager.connect(websocket, job_id)

    # Check if job is already completed (race condition fix)
    job_info = queue_service.get_job(job_id)
    if job_info:
        if job_info.status == JobStatus.COMPLETED:
            # Job finished before WebSocket connected - send result now
            result = pipeline_service.get_result(job_id)
            if result:
                logger.info(f"Sending cached result to late-joining WebSocket for job {job_id}")
                await websocket.send_json({
                    "type": "completed",
                    "job_id": job_id,
                    "result": result
                })
        elif job_info.status == JobStatus.FAILED:
            # Job failed before WebSocket connected - send error now
            logger.info(f"Sending cached error to late-joining WebSocket for job {job_id}")
            await websocket.send_json({
                "type": "error",
                "job_id": job_id,
                "error": job_info.error
            })

    try:
        # Keep connection alive and receive client messages (if any)
        while True:
            # Wait for client messages (e.g., ping/pong)
            data = await websocket.receive_text()

            # Echo back (optional - can handle client commands here)
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job {job_id}")

    finally:
        await ws_manager.disconnect(websocket, job_id)
