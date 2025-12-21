"""Dependency injection for API routes"""
from app.core.config import settings
from app.services.file_service import FileService
from app.services.queue_service import QueueService
from app.services.pipeline_service import PipelineService

# Global service instances (singletons)
_file_service = None
_queue_service = None
_pipeline_service = None

def get_file_service() -> FileService:
    """Get or create FileService instance"""
    global _file_service
    if _file_service is None:
        _file_service = FileService(
            upload_dir=settings.upload_dir,
            max_size_mb=settings.max_upload_size_mb
        )
    return _file_service

def get_queue_service() -> QueueService:
    """Get or create QueueService instance"""
    global _queue_service
    if _queue_service is None:
        _queue_service = QueueService(
            max_concurrent=settings.max_concurrent_jobs
        )
    return _queue_service

def get_pipeline_service() -> PipelineService:
    """Get or create PipelineService instance"""
    global _pipeline_service
    if _pipeline_service is None:
        _pipeline_service = PipelineService(
            pipeline_path=settings.pipeline_path,
            results_dir=settings.results_dir
        )
    return _pipeline_service
