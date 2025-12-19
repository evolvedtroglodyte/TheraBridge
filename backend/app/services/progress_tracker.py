"""
Progress tracking service for real-time session processing updates.

Provides in-memory storage and retrieval of session processing progress
for real-time updates via Server-Sent Events (SSE) or WebSocket.

Enhanced with:
- TTL-based automatic cleanup of expired entries
- Per-session locking for better concurrency
- Extended status support (preprocessing, diarizing, generating_notes, completed)
- Broadcast method for explicit WebSocket notifications
"""
from typing import Dict, Optional, Set, Callable, Awaitable
from datetime import datetime, timedelta
from uuid import UUID
from pydantic import BaseModel, Field
from app.models.schemas import SessionStatus
import asyncio
import logging

logger = logging.getLogger(__name__)


class ProgressUpdate(BaseModel):
    """Real-time progress update for session processing."""
    session_id: UUID
    status: SessionStatus
    progress: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    message: str = Field(..., description="Human-readable status message")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When progress was first created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When progress was last updated")
    error: Optional[str] = Field(None, description="Error message if status is 'failed'")
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated seconds remaining")

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }


class ProgressTracker:
    """
    In-memory progress tracking for session processing.

    Thread-safe storage for real-time progress updates that can be consumed
    by SSE endpoints or WebSocket connections. Supports callback-based
    subscriptions for push notifications to WebSocket clients.

    Features:
    - Per-session locking for better concurrency
    - TTL-based automatic cleanup of expired entries (default: 1 hour)
    - WebSocket subscriber management with callback-based notifications
    - HTTP polling support via get_progress()
    - Broadcast method for explicit WebSocket notifications

    Note: This is an in-memory implementation suitable for single-instance deployments.
    For multi-instance production deployments, consider using Redis or similar
    distributed cache for shared state across instances.
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize progress tracker.

        Args:
            ttl_seconds: Time-to-live for progress entries (default: 3600 = 1 hour)
        """
        self._progress: Dict[UUID, ProgressUpdate] = {}
        # Per-session locks for better concurrency (instead of single global lock)
        self._locks: Dict[UUID, asyncio.Lock] = {}
        # WebSocket subscribers: session_id -> set of async callbacks
        self._subscribers: Dict[UUID, Set[Callable[[ProgressUpdate], Awaitable[None]]]] = {}
        # TTL configuration
        self._ttl_seconds = ttl_seconds
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        # Lock for managing locks dict itself
        self._locks_lock = asyncio.Lock()

        # Start background cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_entries())

        logger.info(f"ProgressTracker initialized with TTL={ttl_seconds}s")

    async def _get_session_lock(self, session_id: UUID) -> asyncio.Lock:
        """
        Get or create a lock for a specific session (thread-safe).

        Args:
            session_id: UUID of the session

        Returns:
            asyncio.Lock for the session
        """
        async with self._locks_lock:
            if session_id not in self._locks:
                self._locks[session_id] = asyncio.Lock()
            return self._locks[session_id]

    async def update_progress(
        self,
        session_id: UUID,
        status: SessionStatus,
        progress: int,
        message: str,
        error: Optional[str] = None,
        estimated_time_remaining: Optional[int] = None
    ) -> ProgressUpdate:
        """
        Update progress for a session and notify all WebSocket subscribers.

        Args:
            session_id: UUID of the session being processed
            status: Current SessionStatus
            progress: Progress percentage (0-100)
            message: Human-readable status message
            error: Optional error message if status is 'failed'
            estimated_time_remaining: Optional estimated seconds remaining

        Returns:
            ProgressUpdate: The updated progress object

        Example:
            await tracker.update_progress(
                session_id=session_uuid,
                status=SessionStatus.transcribing,
                progress=45,
                message="Transcribing audio with Whisper...",
                estimated_time_remaining=120
            )
        """
        # Get per-session lock for better concurrency
        lock = await self._get_session_lock(session_id)

        async with lock:
            # Check if entry exists to preserve created_at timestamp
            existing = self._progress.get(session_id)

            update = ProgressUpdate(
                session_id=session_id,
                status=status,
                progress=progress,
                message=message,
                error=error,
                estimated_time_remaining=estimated_time_remaining,
                created_at=existing.created_at if existing else datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            self._progress[session_id] = update

            logger.debug(
                f"Progress updated: session={session_id}, status={status}, progress={progress}%"
            )

            # Get copy of subscribers to notify (to release lock quickly)
            subscribers = self._subscribers.get(session_id, set()).copy()

        # Notify subscribers outside the lock to avoid blocking
        if subscribers:
            logger.debug(f"Notifying {len(subscribers)} WebSocket subscribers for session {session_id}")
            await self._notify_subscribers(session_id, update, subscribers)

        return update

    async def _notify_subscribers(
        self,
        session_id: UUID,
        update: ProgressUpdate,
        subscribers: Set[Callable[[ProgressUpdate], Awaitable[None]]]
    ) -> None:
        """
        Notify all subscribers for a session (internal method).

        Args:
            session_id: UUID of the session
            update: Progress update to send
            subscribers: Set of callback functions to notify
        """
        failed_callbacks = []

        for callback in subscribers:
            try:
                await callback(update)
            except Exception as e:
                logger.error(f"Error notifying WebSocket subscriber: {e}", exc_info=True)
                failed_callbacks.append(callback)

        # Remove failed callbacks
        if failed_callbacks:
            lock = await self._get_session_lock(session_id)
            async with lock:
                for callback in failed_callbacks:
                    self._subscribers.get(session_id, set()).discard(callback)
                logger.warning(f"Removed {len(failed_callbacks)} failed subscribers for session {session_id}")

    async def get_progress(self, session_id: UUID) -> Optional[ProgressUpdate]:
        """
        Retrieve current progress for a session (for HTTP polling).

        Args:
            session_id: UUID of the session

        Returns:
            ProgressUpdate if found, None otherwise

        Example:
            progress = await tracker.get_progress(session_uuid)
            if progress:
                print(f"Status: {progress.status}, {progress.progress}%")
        """
        # Fast path: check if session exists before acquiring lock
        if session_id not in self._progress:
            return None

        lock = await self._get_session_lock(session_id)
        async with lock:
            return self._progress.get(session_id)

    async def broadcast(self, session_id: UUID, update: ProgressUpdate) -> None:
        """
        Explicitly broadcast a progress update to all WebSocket subscribers.

        This is useful when you want to send a custom update without
        modifying the stored progress state.

        Args:
            session_id: UUID of the session
            update: Progress update to broadcast

        Example:
            custom_update = ProgressUpdate(
                session_id=session_uuid,
                status=SessionStatus.transcribing,
                progress=50,
                message="Custom message..."
            )
            await tracker.broadcast(session_uuid, custom_update)
        """
        lock = await self._get_session_lock(session_id)
        async with lock:
            subscribers = self._subscribers.get(session_id, set()).copy()

        if subscribers:
            logger.debug(f"Broadcasting to {len(subscribers)} WebSocket subscribers for session {session_id}")
            await self._notify_subscribers(session_id, update, subscribers)

    async def remove_progress(self, session_id: UUID) -> None:
        """
        Remove progress tracking for a completed/failed session.

        Args:
            session_id: UUID of the session to remove
        """
        lock = await self._get_session_lock(session_id)
        async with lock:
            self._progress.pop(session_id, None)
            # Clean up subscribers
            self._subscribers.pop(session_id, None)
            logger.debug(f"Progress tracking removed for session={session_id}")

        # Clean up the lock itself
        async with self._locks_lock:
            self._locks.pop(session_id, None)

    async def has_progress(self, session_id: UUID) -> bool:
        """
        Check if progress tracking exists for a session.

        Args:
            session_id: UUID of the session

        Returns:
            True if progress exists, False otherwise
        """
        return session_id in self._progress

    async def _cleanup_expired_entries(self) -> None:
        """
        Background task to clean up expired progress entries.

        Runs every 5 minutes and removes entries older than TTL.
        This prevents memory leaks from abandoned sessions.
        """
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                now = datetime.utcnow()
                expired_sessions = []

                # Find expired sessions
                for session_id, progress in list(self._progress.items()):
                    age = (now - progress.updated_at).total_seconds()
                    if age > self._ttl_seconds:
                        expired_sessions.append(session_id)

                # Remove expired entries
                for session_id in expired_sessions:
                    lock = await self._get_session_lock(session_id)
                    async with lock:
                        self._progress.pop(session_id, None)
                        self._subscribers.pop(session_id, None)

                    # Clean up the lock itself
                    async with self._locks_lock:
                        self._locks.pop(session_id, None)

                    logger.info(f"Cleaned up expired progress: session={session_id}")

                if expired_sessions:
                    logger.info(f"Cleaned up {len(expired_sessions)} expired progress entries")

            except asyncio.CancelledError:
                logger.info("Progress cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}", exc_info=True)

    async def get_all_active_sessions(self) -> Dict[UUID, ProgressUpdate]:
        """
        Get all active progress entries (useful for monitoring/debugging).

        Returns:
            Dict mapping session_id to ProgressUpdate

        Example:
            active = await tracker.get_all_active_sessions()
            print(f"Active sessions: {len(active)}")
        """
        return dict(self._progress)

    async def subscribe(
        self,
        session_id: UUID,
        callback: Callable[[ProgressUpdate], Awaitable[None]]
    ) -> None:
        """
        Subscribe to progress updates for a session via WebSocket.

        The callback will be called whenever progress is updated for this session.

        Args:
            session_id: UUID of the session to subscribe to
            callback: Async function to call with ProgressUpdate when updates occur

        Example:
            async def send_to_websocket(update: ProgressUpdate):
                await websocket.send_json(update.dict())

            await tracker.subscribe(session_uuid, send_to_websocket)
        """
        lock = await self._get_session_lock(session_id)
        async with lock:
            if session_id not in self._subscribers:
                self._subscribers[session_id] = set()
            self._subscribers[session_id].add(callback)
            logger.info(f"WebSocket client subscribed to session {session_id}")

            # Send current progress immediately if available
            current_progress = self._progress.get(session_id)

        # Send initial progress outside the lock
        if current_progress:
            try:
                await callback(current_progress)
                logger.debug(f"Sent initial progress to new subscriber for session {session_id}")
            except Exception as e:
                logger.error(f"Error sending initial progress: {e}", exc_info=True)

    async def unsubscribe(
        self,
        session_id: UUID,
        callback: Callable[[ProgressUpdate], Awaitable[None]]
    ) -> None:
        """
        Unsubscribe from progress updates for a session.

        Args:
            session_id: UUID of the session
            callback: The callback function to remove
        """
        lock = await self._get_session_lock(session_id)
        async with lock:
            if session_id in self._subscribers:
                self._subscribers[session_id].discard(callback)
                if not self._subscribers[session_id]:
                    # Clean up empty subscriber sets
                    del self._subscribers[session_id]
                logger.info(f"WebSocket client unsubscribed from session {session_id}")

    def shutdown(self) -> None:
        """
        Shutdown the progress tracker and cancel cleanup task.

        Call this when shutting down the application.

        Example:
            @app.on_event("shutdown")
            async def shutdown_event():
                tracker = get_progress_tracker()
                tracker.shutdown()
        """
        if self._cleanup_task:
            self._cleanup_task.cancel()
            logger.info("ProgressTracker cleanup task cancelled")


# Global singleton instance
_progress_tracker: Optional[ProgressTracker] = None


def get_progress_tracker(ttl_seconds: int = 3600) -> ProgressTracker:
    """
    Get or create global ProgressTracker instance (singleton pattern).

    Args:
        ttl_seconds: Time-to-live for progress entries (default: 3600 = 1 hour)

    Returns:
        ProgressTracker: Global progress tracker instance

    Usage:
        # In FastAPI dependency
        tracker = get_progress_tracker()

        # In route handler
        @app.post("/api/sessions/{session_id}/process")
        async def process_session(session_id: UUID):
            tracker = get_progress_tracker()
            await tracker.update_progress(
                session_id=session_id,
                status=SessionStatus.preprocessing,
                progress=10,
                message="Starting preprocessing..."
            )
    """
    global _progress_tracker

    if _progress_tracker is None:
        _progress_tracker = ProgressTracker(ttl_seconds=ttl_seconds)

    return _progress_tracker
