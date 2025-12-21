"""WebSocket connection manager for real-time updates"""
import asyncio
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for job updates"""

    def __init__(self):
        # Map of job_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, job_id: str):
        """Accept and register a WebSocket connection"""
        await websocket.accept()

        async with self._lock:
            if job_id not in self.active_connections:
                self.active_connections[job_id] = set()

            self.active_connections[job_id].add(websocket)
            logger.info(f"WebSocket connected for job {job_id} (total: {len(self.active_connections[job_id])})")

    async def disconnect(self, websocket: WebSocket, job_id: str):
        """Remove a WebSocket connection"""
        async with self._lock:
            if job_id in self.active_connections:
                self.active_connections[job_id].discard(websocket)

                # Clean up empty sets
                if not self.active_connections[job_id]:
                    del self.active_connections[job_id]

                logger.info(f"WebSocket disconnected for job {job_id}")

    async def send_progress(self, job_id: str, stage: str, progress: float):
        """Send progress update to all connections for a job"""
        message = {
            "type": "progress",
            "job_id": job_id,
            "stage": stage,
            "progress": progress
        }

        await self._broadcast(job_id, message)

    async def send_completed(self, job_id: str, result: dict):
        """Send completion notification"""
        message = {
            "type": "completed",
            "job_id": job_id,
            "result": result
        }

        await self._broadcast(job_id, message)

    async def send_error(self, job_id: str, error: str):
        """Send error notification"""
        message = {
            "type": "error",
            "job_id": job_id,
            "error": error
        }

        await self._broadcast(job_id, message)

    async def _broadcast(self, job_id: str, message: dict):
        """Broadcast message to all connections for a job"""
        if job_id not in self.active_connections:
            return

        # Create a copy to avoid modification during iteration
        connections = list(self.active_connections[job_id])

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                # Remove broken connection
                await self.disconnect(websocket, job_id)

# Global connection manager instance
ws_manager = ConnectionManager()
