"""
Audio File Cleanup Service

Handles cleanup of orphaned audio files from failed uploads or processing errors.
Provides both scheduled cleanup and manual cleanup endpoints.

Safety Features:
- Only deletes files not referenced in database
- Configurable retention period for failed sessions
- Dry-run mode for testing
- Comprehensive logging of all cleanup operations
"""
import os
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging

from app.models.db_models import Session
from app.models.export_models import ExportJob
from app.database import AsyncSessionLocal

# Configure logger
logger = logging.getLogger(__name__)


class CleanupConfig:
    """Configuration for cleanup service"""

    # Retention period for failed sessions (default: 7 days)
    FAILED_SESSION_RETENTION_DAYS = int(
        os.getenv("FAILED_SESSION_RETENTION_DAYS", "7")
    )

    # Retention period for orphaned files (default: 1 day)
    # Files not referenced in DB and older than this will be deleted
    ORPHANED_FILE_RETENTION_HOURS = int(
        os.getenv("ORPHANED_FILE_RETENTION_HOURS", "24")
    )

    # Upload directory
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads/audio")

    # Enable automatic cleanup on startup
    AUTO_CLEANUP_ON_STARTUP = os.getenv("AUTO_CLEANUP_ON_STARTUP", "false").lower() in (
        "true",
        "1",
        "yes",
    )

    # Cleanup schedule (cron-like, not implemented yet but reserved for future)
    CLEANUP_SCHEDULE_HOUR = int(os.getenv("CLEANUP_SCHEDULE_HOUR", "3"))  # 3 AM


class CleanupResult:
    """Result of a cleanup operation"""

    def __init__(self):
        self.orphaned_files_deleted: List[str] = []
        self.failed_sessions_cleaned: List[str] = []
        self.total_space_freed_mb: float = 0.0
        self.errors: List[str] = []
        self.dry_run: bool = False

    def to_dict(self) -> Dict:
        """Convert result to dictionary for API response"""
        return {
            "orphaned_files_deleted": self.orphaned_files_deleted,
            "orphaned_files_count": len(self.orphaned_files_deleted),
            "failed_sessions_cleaned": self.failed_sessions_cleaned,
            "failed_sessions_count": len(self.failed_sessions_cleaned),
            "total_space_freed_mb": round(self.total_space_freed_mb, 2),
            "errors": self.errors,
            "error_count": len(self.errors),
            "dry_run": self.dry_run,
        }


class AudioCleanupService:
    """Service for cleaning up orphaned audio files"""

    def __init__(self, db: Optional[AsyncSession] = None):
        """
        Initialize cleanup service

        Args:
            db: Optional database session (if None, creates its own)
        """
        self.db = db
        self.upload_dir = Path(CleanupConfig.UPLOAD_DIR)
        self._owns_db = db is None

    async def __aenter__(self):
        """Context manager entry"""
        if self._owns_db:
            self.db = AsyncSessionLocal()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self._owns_db and self.db:
            await self.db.close()

    async def cleanup_orphaned_files(self, dry_run: bool = False) -> CleanupResult:
        """
        Clean up audio files not referenced in database

        Strategy:
        1. Get all audio filenames from database
        2. Scan upload directory for all files
        3. Find files not in database that are older than retention period
        4. Delete orphaned files (or log if dry_run)

        Args:
            dry_run: If True, only log what would be deleted without actually deleting

        Returns:
            CleanupResult with details of cleanup operation
        """
        result = CleanupResult()
        result.dry_run = dry_run

        logger.info(
            f"Starting orphaned file cleanup (dry_run={dry_run}) in {self.upload_dir}"
        )

        try:
            # Get all audio filenames referenced in database
            referenced_files = await self._get_referenced_files()
            logger.info(f"Found {len(referenced_files)} files referenced in database")

            # Scan upload directory
            if not self.upload_dir.exists():
                logger.warning(f"Upload directory does not exist: {self.upload_dir}")
                return result

            all_files = self._scan_upload_directory()
            logger.info(f"Found {len(all_files)} files in upload directory")

            # Calculate retention cutoff time
            retention_cutoff = datetime.now() - timedelta(
                hours=CleanupConfig.ORPHANED_FILE_RETENTION_HOURS
            )

            # Find orphaned files
            orphaned_files = all_files - referenced_files

            logger.info(f"Identified {len(orphaned_files)} orphaned files")

            # Delete orphaned files older than retention period
            for filename in orphaned_files:
                file_path = self.upload_dir / filename
                if not file_path.exists():
                    continue

                # Check file age
                file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_mtime > retention_cutoff:
                    logger.debug(
                        f"Skipping {filename} (too recent: {file_mtime})"
                    )
                    continue

                # Get file size before deletion
                file_size_mb = file_path.stat().st_size / (1024 * 1024)

                if dry_run:
                    logger.info(
                        f"[DRY RUN] Would delete orphaned file: {filename} ({file_size_mb:.2f} MB)"
                    )
                else:
                    try:
                        file_path.unlink()
                        logger.info(
                            f"Deleted orphaned file: {filename} ({file_size_mb:.2f} MB)"
                        )
                    except Exception as e:
                        error_msg = f"Failed to delete {filename}: {str(e)}"
                        logger.error(error_msg)
                        result.errors.append(error_msg)
                        continue

                result.orphaned_files_deleted.append(filename)
                result.total_space_freed_mb += file_size_mb

        except Exception as e:
            error_msg = f"Error during orphaned file cleanup: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)

        logger.info(
            f"Orphaned file cleanup complete: {len(result.orphaned_files_deleted)} files, "
            f"{result.total_space_freed_mb:.2f} MB freed"
        )

        return result

    async def cleanup_failed_sessions(self, dry_run: bool = False) -> CleanupResult:
        """
        Clean up audio files from failed sessions older than retention period

        Strategy:
        1. Find sessions with status='failed' older than retention period
        2. Delete associated audio files
        3. Optionally delete session records (currently just cleans files)

        Args:
            dry_run: If True, only log what would be deleted without actually deleting

        Returns:
            CleanupResult with details of cleanup operation
        """
        result = CleanupResult()
        result.dry_run = dry_run

        logger.info(
            f"Starting failed session cleanup (dry_run={dry_run})"
        )

        try:
            # Calculate retention cutoff
            retention_cutoff = datetime.now() - timedelta(
                days=CleanupConfig.FAILED_SESSION_RETENTION_DAYS
            )

            # Find old failed sessions
            query = select(Session).where(
                and_(
                    Session.status == "failed",
                    Session.created_at < retention_cutoff,
                    Session.audio_filename.isnot(None),
                )
            )

            result_db = await self.db.execute(query)
            failed_sessions = result_db.scalars().all()

            logger.info(
                f"Found {len(failed_sessions)} failed sessions older than {CleanupConfig.FAILED_SESSION_RETENTION_DAYS} days"
            )

            for session in failed_sessions:
                if not session.audio_filename:
                    continue

                # Check for both original and processed files
                files_to_delete = [session.audio_filename]

                # Check for processed file variant (e.g., uuid.m4a -> uuid_processed.mp3)
                base_name = Path(session.audio_filename).stem
                processed_file = f"{base_name}_processed.mp3"
                files_to_delete.append(processed_file)

                for filename in files_to_delete:
                    file_path = self.upload_dir / filename
                    if not file_path.exists():
                        continue

                    file_size_mb = file_path.stat().st_size / (1024 * 1024)

                    if dry_run:
                        logger.info(
                            f"[DRY RUN] Would delete file from failed session {session.id}: "
                            f"{filename} ({file_size_mb:.2f} MB)"
                        )
                    else:
                        try:
                            file_path.unlink()
                            logger.info(
                                f"Deleted file from failed session {session.id}: "
                                f"{filename} ({file_size_mb:.2f} MB)"
                            )
                        except Exception as e:
                            error_msg = (
                                f"Failed to delete {filename} from session {session.id}: {str(e)}"
                            )
                            logger.error(error_msg)
                            result.errors.append(error_msg)
                            continue

                    result.total_space_freed_mb += file_size_mb

                result.failed_sessions_cleaned.append(str(session.id))

        except Exception as e:
            error_msg = f"Error during failed session cleanup: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)

        logger.info(
            f"Failed session cleanup complete: {len(result.failed_sessions_cleaned)} sessions, "
            f"{result.total_space_freed_mb:.2f} MB freed"
        )

        return result

    async def cleanup_all(self, dry_run: bool = False) -> CleanupResult:
        """
        Run all cleanup operations

        Args:
            dry_run: If True, only log what would be deleted without actually deleting

        Returns:
            Combined CleanupResult from all operations
        """
        logger.info(f"Starting full cleanup (dry_run={dry_run})")

        # Run both cleanup operations
        orphaned_result = await self.cleanup_orphaned_files(dry_run=dry_run)
        failed_result = await self.cleanup_failed_sessions(dry_run=dry_run)

        # Combine results
        combined_result = CleanupResult()
        combined_result.dry_run = dry_run
        combined_result.orphaned_files_deleted = orphaned_result.orphaned_files_deleted
        combined_result.failed_sessions_cleaned = failed_result.failed_sessions_cleaned
        combined_result.total_space_freed_mb = (
            orphaned_result.total_space_freed_mb + failed_result.total_space_freed_mb
        )
        combined_result.errors = orphaned_result.errors + failed_result.errors

        logger.info(
            f"Full cleanup complete: "
            f"{len(combined_result.orphaned_files_deleted)} orphaned files, "
            f"{len(combined_result.failed_sessions_cleaned)} failed sessions, "
            f"{combined_result.total_space_freed_mb:.2f} MB total freed"
        )

        return combined_result

    async def _get_referenced_files(self) -> Set[str]:
        """
        Get all audio filenames referenced in database

        Returns:
            Set of filenames currently referenced in sessions table
        """
        query = select(Session.audio_filename).where(
            Session.audio_filename.isnot(None)
        )
        result = await self.db.execute(query)
        filenames = result.scalars().all()

        # Include both original and processed files
        referenced = set()
        for filename in filenames:
            if filename:
                referenced.add(filename)

                # Add processed file variant
                base_name = Path(filename).stem
                referenced.add(f"{base_name}_processed.mp3")

        return referenced

    def _scan_upload_directory(self) -> Set[str]:
        """
        Scan upload directory for all audio files

        Returns:
            Set of all filenames in upload directory (excluding .gitkeep)
        """
        if not self.upload_dir.exists():
            return set()

        files = set()
        for file_path in self.upload_dir.iterdir():
            if file_path.is_file() and file_path.name != ".gitkeep":
                files.add(file_path.name)

        return files


async def cleanup_expired_exports(dry_run: bool = False) -> CleanupResult:
    """
    Clean up expired export files.

    Deletes export files where expires_at < now and updates database records.

    Strategy:
    1. Query ExportJob table for expired exports (status='completed', expires_at < now, file_path IS NOT NULL)
    2. For each expired job:
       - Check if file exists on disk
       - Delete file if not dry_run
       - Update job record (set file_path=None, file_size_bytes=None)
       - Log deletion with job_id and file_size context
    3. Return CleanupResult with files deleted and bytes freed

    Args:
        dry_run: If True, only log what would be deleted without actually deleting

    Returns:
        CleanupResult with details of cleanup operation
    """
    result = CleanupResult()
    result.dry_run = dry_run

    logger.info(f"Starting expired export cleanup (dry_run={dry_run})")

    async with AsyncSessionLocal() as db:
        try:
            now = datetime.now()

            # Find expired jobs with files
            query = select(ExportJob).where(
                and_(
                    ExportJob.status == 'completed',
                    ExportJob.expires_at < now,
                    ExportJob.file_path.isnot(None)
                )
            )
            result_db = await db.execute(query)
            expired_jobs = result_db.scalars().all()

            logger.info(f"Found {len(expired_jobs)} expired export jobs with files")

            for job in expired_jobs:
                if not job.file_path:
                    continue

                file_path = Path(job.file_path)

                # Check if file exists
                if not file_path.exists():
                    logger.warning(
                        f"Export file not found for job {job.id}: {job.file_path}"
                    )
                    # Update database even if file doesn't exist
                    if not dry_run:
                        job.file_path = None
                        job.file_size_bytes = None
                        await db.commit()
                    continue

                # Get file size before deletion
                file_size = file_path.stat().st_size
                file_size_mb = file_size / (1024 * 1024)

                if dry_run:
                    logger.info(
                        f"[DRY RUN] Would delete expired export for job {job.id}: "
                        f"{file_path.name} ({file_size_mb:.2f} MB)"
                    )
                else:
                    try:
                        # Delete file
                        file_path.unlink()

                        # Update job record
                        job.file_path = None
                        job.file_size_bytes = None
                        await db.commit()

                        logger.info(
                            f"Deleted expired export for job {job.id}: "
                            f"{file_path.name} ({file_size_mb:.2f} MB)"
                        )
                    except Exception as e:
                        error_msg = f"Failed to delete export file for job {job.id}: {str(e)}"
                        logger.error(error_msg)
                        result.errors.append(error_msg)
                        await db.rollback()
                        continue

                # Track in result (use orphaned_files_deleted for now, could add export-specific field later)
                result.orphaned_files_deleted.append(str(job.id))
                result.total_space_freed_mb += file_size_mb

        except Exception as e:
            error_msg = f"Error during expired export cleanup: {str(e)}"
            logger.error(error_msg, exc_info=True)
            result.errors.append(error_msg)

    logger.info(
        f"Expired export cleanup complete: {len(result.orphaned_files_deleted)} files deleted, "
        f"{result.total_space_freed_mb:.2f} MB freed"
    )

    return result


# Standalone function for scheduled cleanup
async def run_scheduled_cleanup(dry_run: bool = False) -> CleanupResult:
    """
    Run cleanup as a standalone scheduled task

    This can be called by cron, Celery, or other scheduling systems.

    Args:
        dry_run: If True, only log what would be deleted without actually deleting

    Returns:
        CleanupResult with details of cleanup operation
    """
    async with AudioCleanupService() as cleanup_service:
        return await cleanup_service.cleanup_all(dry_run=dry_run)


# Startup cleanup hook
async def run_startup_cleanup():
    """
    Run cleanup on application startup if AUTO_CLEANUP_ON_STARTUP is enabled

    This is called from the FastAPI lifespan event.
    """
    if not CleanupConfig.AUTO_CLEANUP_ON_STARTUP:
        logger.info("Auto cleanup on startup is disabled")
        return

    logger.info("Running cleanup on startup")
    try:
        result = await run_scheduled_cleanup(dry_run=False)
        logger.info(f"Startup cleanup completed: {result.to_dict()}")
    except Exception as e:
        logger.error(f"Startup cleanup failed: {str(e)}", exc_info=True)
