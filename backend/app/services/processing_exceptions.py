"""
Custom exception classes for audio processing pipeline.

This module defines exceptions for handling failures in the parallel processing
pipeline where transcription and diarization run concurrently using asyncio.gather().

Exception Hierarchy:
    ProcessingError (base)
    ├── TranscriptionError - Whisper API or transcription service failed
    ├── DiarizationError - Speaker diarization (pyannote) failed
    ├── ParallelProcessingError - Both tasks failed or fatal error occurred
    └── PartialProcessingError - One task succeeded, one failed

Error Recovery Strategy:
    - TranscriptionError: FATAL - cannot proceed without transcript
    - DiarizationError: RECOVERABLE - can use undiarized transcript
    - ParallelProcessingError: FATAL - critical failure, abort pipeline
    - PartialProcessingError: RECOVERABLE - proceed with available data
"""

from typing import Optional, Dict, Any


class ProcessingError(Exception):
    """
    Base exception for all audio processing errors.

    Provides common error context (session_id, error_details) for all processing exceptions.
    """

    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize processing error with context.

        Args:
            message: Human-readable error description
            session_id: UUID of the session being processed (for logging)
            error_details: Additional error metadata (e.g., API response, traceback)
        """
        super().__init__(message)
        self.message = message
        self.session_id = session_id
        self.error_details = error_details or {}

    def __str__(self) -> str:
        if self.session_id:
            return f"[Session {self.session_id}] {self.message}"
        return self.message


class TranscriptionError(ProcessingError):
    """
    Raised when audio transcription fails (Whisper API or local model).

    This is a FATAL error - the pipeline cannot proceed without a transcript.

    Common causes:
        - Whisper API rate limit exceeded (429)
        - Whisper API authentication failure (401)
        - Audio file corrupted or unsupported format
        - Network timeout during API call
        - OpenAI service outage

    Recovery strategy:
        - Retry with exponential backoff for transient errors (429, 503, network)
        - Mark session as 'failed' for permanent errors (400, 401, corrupted audio)
        - Store error details for debugging
    """

    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        is_retryable: bool = False
    ):
        """
        Initialize transcription error.

        Args:
            message: Human-readable error description
            session_id: UUID of the session being processed
            error_details: API response, status code, or exception details
            is_retryable: True if error is transient and can be retried
        """
        super().__init__(message, session_id, error_details)
        self.is_retryable = is_retryable


class DiarizationError(ProcessingError):
    """
    Raised when speaker diarization fails (pyannote.audio).

    This is a RECOVERABLE error - the pipeline can proceed with undiarized transcript.

    Common causes:
        - HuggingFace token invalid or expired
        - Audio file too short for diarization (< 1 second)
        - Pyannote model download failure
        - Out of memory (GPU/CPU)
        - Audio quality too poor for speaker detection

    Recovery strategy:
        - Log warning and proceed with undiarized transcript
        - Mark diarization as 'skipped' in session metadata
        - Use fallback labeling (e.g., all segments as "Unknown Speaker")
        - Retry with different model settings if appropriate
    """

    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
        fallback_available: bool = True
    ):
        """
        Initialize diarization error.

        Args:
            message: Human-readable error description
            session_id: UUID of the session being processed
            error_details: Model error, stack trace, or audio metadata
            fallback_available: True if undiarized transcript can be used
        """
        super().__init__(message, session_id, error_details)
        self.fallback_available = fallback_available


class ParallelProcessingError(ProcessingError):
    """
    Raised when BOTH transcription AND diarization fail, or a fatal error occurs.

    This is a FATAL error - the pipeline must abort completely.

    Common causes:
        - Audio file corrupted beyond repair
        - Both Whisper and pyannote services unavailable
        - Critical infrastructure failure (database, storage)
        - asyncio.gather() raised unhandled exception

    Recovery strategy:
        - Mark session as 'failed' with detailed error message
        - Send alert to monitoring system (if configured)
        - Do NOT retry - indicates systemic issue
        - Clean up any partial processing artifacts
    """

    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        transcription_error: Optional[Exception] = None,
        diarization_error: Optional[Exception] = None,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize parallel processing error.

        Args:
            message: Human-readable error description
            session_id: UUID of the session being processed
            transcription_error: Exception from transcription task
            diarization_error: Exception from diarization task
            error_details: Additional context about the failure
        """
        super().__init__(message, session_id, error_details)
        self.transcription_error = transcription_error
        self.diarization_error = diarization_error


class PartialProcessingError(ProcessingError):
    """
    Raised when ONE task succeeds and ONE task fails during parallel processing.

    This is a RECOVERABLE error - the pipeline can proceed with partial results.

    Common scenarios:
        - Transcription succeeds, diarization fails → Use undiarized transcript
        - Diarization succeeds, transcription fails → FATAL (need transcript)

    Recovery strategy:
        - If transcription succeeded: Proceed with undiarized transcript
        - If transcription failed: Escalate to TranscriptionError (FATAL)
        - Log which task failed for analytics
        - Mark session with 'partial_processing' flag
    """

    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        succeeded_task: Optional[str] = None,
        failed_task: Optional[str] = None,
        failed_exception: Optional[Exception] = None,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize partial processing error.

        Args:
            message: Human-readable error description
            session_id: UUID of the session being processed
            succeeded_task: Name of task that succeeded ('transcription' or 'diarization')
            failed_task: Name of task that failed ('transcription' or 'diarization')
            failed_exception: Exception from the failed task
            error_details: Additional context about the partial failure
        """
        super().__init__(message, session_id, error_details)
        self.succeeded_task = succeeded_task
        self.failed_task = failed_task
        self.failed_exception = failed_exception


class CircuitBreakerOpenError(ProcessingError):
    """
    Raised when circuit breaker is OPEN, preventing new processing attempts.

    This indicates repeated failures have triggered the circuit breaker pattern,
    and the system is temporarily rejecting new requests to prevent cascading failures.

    Common causes:
        - Multiple consecutive API failures (rate limits, outages)
        - Service degradation detected by health checks
        - Too many retries exhausted

    Recovery strategy:
        - Return 503 Service Unavailable to client
        - Wait for circuit breaker to transition to HALF_OPEN (after timeout)
        - Monitor service health and reset when recovered
        - Queue requests for retry when circuit closes
    """

    def __init__(
        self,
        message: str = "Circuit breaker is OPEN - processing temporarily unavailable",
        service_name: Optional[str] = None,
        failure_count: Optional[int] = None,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize circuit breaker error.

        Args:
            message: Human-readable error description
            service_name: Name of the service with open circuit ('transcription' or 'diarization')
            failure_count: Number of consecutive failures that triggered circuit
            error_details: Additional context (last error, timeout duration)
        """
        super().__init__(message, error_details=error_details)
        self.service_name = service_name
        self.failure_count = failure_count


class RetryExhaustedError(ProcessingError):
    """
    Raised when all retry attempts have been exhausted for a transient error.

    This indicates that a retryable error (e.g., rate limit, network timeout)
    has persisted beyond the maximum retry count.

    Common causes:
        - Extended API outage
        - Persistent rate limiting (quota exhausted)
        - Network connectivity issues

    Recovery strategy:
        - Mark session as 'failed' with retry exhaustion details
        - Alert monitoring system (indicates potential service degradation)
        - Store error for manual review/reprocessing
        - Consider increasing retry limits or backoff duration
    """

    def __init__(
        self,
        message: str,
        session_id: Optional[str] = None,
        retry_count: int = 0,
        last_exception: Optional[Exception] = None,
        error_details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize retry exhausted error.

        Args:
            message: Human-readable error description
            session_id: UUID of the session being processed
            retry_count: Number of retry attempts made
            last_exception: The final exception after all retries
            error_details: Additional context (retry history, backoff times)
        """
        super().__init__(message, session_id, error_details)
        self.retry_count = retry_count
        self.last_exception = last_exception
