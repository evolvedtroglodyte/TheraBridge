"""In-memory job queue service for managing transcription jobs"""
import asyncio
import logging
from typing import Dict, Optional, Callable
from datetime import datetime
from enum import Enum

from app.models.responses import JobStatus
from app.services.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

class JobInfo:
    """Information about a running job"""

    def __init__(self, job_id: str, filename: str):
        self.job_id = job_id
        self.filename = filename
        self.status = JobStatus.PENDING
        self.progress = 0.0
        self.stage = "queued"
        self.error: Optional[str] = None
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "job_id": self.job_id,
            "filename": self.filename,
            "status": self.status.value,
            "progress": self.progress,
            "stage": self.stage,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

class QueueService:
    """Manages in-memory job queue with concurrency control"""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.jobs: Dict[str, JobInfo] = {}
        self.active_count = 0
        self._lock = asyncio.Lock()

    async def add_job(
        self,
        job_id: str,
        filename: str,
        task_func: Callable,
        *args,
        **kwargs
    ) -> JobInfo:
        """
        Add a job to the queue and start processing if slots available

        Args:
            job_id: Unique job identifier
            filename: Original filename
            task_func: Async function to execute (pipeline.run_transcription)
            *args, **kwargs: Arguments to pass to task_func

        Returns:
            JobInfo object
        """
        async with self._lock:
            # Create job info
            job_info = JobInfo(job_id, filename)
            self.jobs[job_id] = job_info

            # Create and start task
            job_info.task = asyncio.create_task(
                self._run_job(job_info, task_func, *args, **kwargs)
            )

            logger.info(f"Job {job_id} added to queue")
            return job_info

    async def _run_job(
        self,
        job_info: JobInfo,
        task_func: Callable,
        *args,
        **kwargs
    ):
        """Run a job with concurrency control"""
        result = None
        try:
            # Wait for available slot
            while self.active_count >= self.max_concurrent:
                await asyncio.sleep(0.5)

            # Mark as active
            async with self._lock:
                self.active_count += 1
                job_info.status = JobStatus.PROCESSING
                job_info.started_at = datetime.now()
                logger.info(f"Job {job_info.job_id} started (active: {self.active_count}/{self.max_concurrent})")

            # Run the task and capture result
            result = await task_func(*args, **kwargs)

            # Mark as completed
            async with self._lock:
                job_info.status = JobStatus.COMPLETED
                job_info.completed_at = datetime.now()
                job_info.progress = 1.0
                logger.info(f"Job {job_info.job_id} completed")

            # Send completion event via WebSocket
            await ws_manager.send_completed(job_info.job_id, result)

        except Exception as e:
            # Mark as failed
            async with self._lock:
                job_info.status = JobStatus.FAILED
                job_info.error = str(e)
                job_info.completed_at = datetime.now()
                logger.error(f"Job {job_info.job_id} failed: {e}", exc_info=True)

            # Send error event via WebSocket
            await ws_manager.send_error(job_info.job_id, str(e))

        finally:
            # Release slot
            async with self._lock:
                self.active_count -= 1
                logger.info(f"Job {job_info.job_id} released slot (active: {self.active_count}/{self.max_concurrent})")

    async def update_progress(self, job_id: str, stage: str, progress: float):
        """Update job progress"""
        async with self._lock:
            if job_id in self.jobs:
                self.jobs[job_id].stage = stage
                self.jobs[job_id].progress = progress

    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get job information"""
        return self.jobs.get(job_id)

    def get_all_jobs(self) -> list:
        """Get all jobs"""
        return [job.to_dict() for job in self.jobs.values()]

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        async with self._lock:
            if job_id not in self.jobs:
                return False

            job_info = self.jobs[job_id]

            if job_info.task and not job_info.task.done():
                job_info.task.cancel()
                job_info.status = JobStatus.FAILED
                job_info.error = "Cancelled by user"
                job_info.completed_at = datetime.now()
                logger.info(f"Job {job_id} cancelled")
                return True

            return False

    async def remove_job(self, job_id: str) -> bool:
        """Remove job from queue"""
        async with self._lock:
            if job_id in self.jobs:
                del self.jobs[job_id]
                return True
            return False
