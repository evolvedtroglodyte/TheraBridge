"""
Server-Sent Events Router
Real-time pipeline event streaming
"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.utils.pipeline_logger import PipelineLogger
import asyncio
import json

router = APIRouter(prefix="/api/sse", tags=["sse"])

async def event_generator(patient_id: str, request: Request):
    """
    SSE event generator - streams pipeline events to client

    Yields events in SSE format:
    data: {"event": "wave1_complete", "session_id": "...", ...}

    """
    last_event_index = 0

    try:
        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            # Get all events for this patient
            events = PipelineLogger.get_events(patient_id)

            # Send new events since last check
            if len(events) > last_event_index:
                new_events = events[last_event_index:]

                for event in new_events:
                    # Format as SSE event
                    yield f"data: {json.dumps(event)}\n\n"

                last_event_index = len(events)

            # Sleep briefly to avoid tight loop
            await asyncio.sleep(0.5)  # 500ms interval

    finally:
        # Client disconnected, optionally clear old events
        # PipelineLogger.clear_events(patient_id)  # Uncomment to clear on disconnect
        pass


@router.get("/events/{patient_id}")
async def stream_events(patient_id: str, request: Request):
    """
    SSE endpoint - connect to receive real-time pipeline events

    Usage:
        const eventSource = new EventSource('/api/sse/events/{patient_id}');
        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log('Pipeline event:', data);
        };

    Returns:
        StreamingResponse with text/event-stream content type
    """
    # Get origin from request for CORS (use request origin or fallback to production frontend)
    origin = request.headers.get("origin", "https://therabridge.up.railway.app")

    return StreamingResponse(
        event_generator(patient_id, request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Access-Control-Allow-Origin": origin,  # Allow SSE from frontend
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS"
        }
    )
