"""
Audio processing module - convenience re-exports.

This module re-exports the main audio processing components to match
the import pattern expected by the routers and other services.

Import Pattern:
    from app.services.audio_processing import (
        AudioProcessingService,
        ProcessingError,
        ProgressTracker
    )

Instead of:
    from app.services.audio_processing_service import AudioProcessingService
    from app.services.processing_exceptions import ProcessingError
    from app.services.progress_tracker import ProgressTracker
"""

# Re-export main service
from app.services.audio_processing_service import (
    AudioProcessingService,
    get_audio_processing_service
)

# Re-export exceptions
from app.services.processing_exceptions import (
    ProcessingError,
    TranscriptionError,
    DiarizationError,
    ParallelProcessingError,
    PartialProcessingError,
    CircuitBreakerOpenError,
    RetryExhaustedError
)

# Re-export progress tracker
from app.services.progress_tracker import (
    ProgressTracker,
    ProgressUpdate,
    get_progress_tracker
)

__all__ = [
    # Main service
    "AudioProcessingService",
    "get_audio_processing_service",
    # Exceptions
    "ProcessingError",
    "TranscriptionError",
    "DiarizationError",
    "ParallelProcessingError",
    "PartialProcessingError",
    "CircuitBreakerOpenError",
    "RetryExhaustedError",
    # Progress tracking
    "ProgressTracker",
    "ProgressUpdate",
    "get_progress_tracker",
]
