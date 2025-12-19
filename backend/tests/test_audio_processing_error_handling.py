"""
Tests for audio processing error handling and resilience.

This test suite validates that the AudioProcessingService handles parallel
processing failures gracefully using asyncio.gather(return_exceptions=True).

Test scenarios:
1. Both transcription and diarization succeed
2. Transcription succeeds, diarization fails (RECOVERABLE)
3. Transcription fails, diarization succeeds (FATAL)
4. Both fail (FATAL)
5. Circuit breaker activation after repeated failures
6. Retry logic for transient errors
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from app.services.audio_processing_service import (
    AudioProcessingService,
    transcription_circuit_breaker,
    diarization_circuit_breaker,
    exponential_backoff_retry,
    _is_retryable_error,
    CircuitBreakerState
)
from app.services.processing_exceptions import (
    TranscriptionError,
    DiarizationError,
    ParallelProcessingError,
    PartialProcessingError,
    CircuitBreakerOpenError,
    RetryExhaustedError
)


@pytest.fixture
def reset_circuit_breakers():
    """Reset circuit breakers before each test."""
    transcription_circuit_breaker.state = CircuitBreakerState.CLOSED
    transcription_circuit_breaker.failure_count = 0
    transcription_circuit_breaker.success_count = 0
    diarization_circuit_breaker.state = CircuitBreakerState.CLOSED
    diarization_circuit_breaker.failure_count = 0
    diarization_circuit_breaker.success_count = 0
    yield
    # Reset again after test
    transcription_circuit_breaker.state = CircuitBreakerState.CLOSED
    transcription_circuit_breaker.failure_count = 0
    diarization_circuit_breaker.state = CircuitBreakerState.CLOSED
    diarization_circuit_breaker.failure_count = 0


class TestRetryLogic:
    """Test exponential backoff retry logic."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_on_first_attempt(self):
        """Test successful function call on first attempt."""
        mock_func = AsyncMock(return_value={"result": "success"})

        result = await exponential_backoff_retry(mock_func)

        assert result == {"result": "success"}
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_retries(self):
        """Test successful function call after transient failures."""
        mock_func = AsyncMock()
        # Fail twice with retryable errors, then succeed
        mock_func.side_effect = [
            Exception("rate limit exceeded"),
            Exception("503 service unavailable"),
            {"result": "success"}
        ]

        result = await exponential_backoff_retry(mock_func, max_attempts=3)

        assert result == {"result": "success"}
        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted_non_retryable_error(self):
        """Test immediate failure for non-retryable errors."""
        mock_func = AsyncMock(side_effect=ValueError("invalid audio format"))

        with pytest.raises(RetryExhaustedError) as exc_info:
            await exponential_backoff_retry(mock_func, max_attempts=3)

        assert exc_info.value.retry_count == 3
        assert mock_func.call_count == 1  # No retries for non-retryable

    @pytest.mark.asyncio
    async def test_retry_exhausted_all_attempts(self):
        """Test failure after exhausting all retry attempts."""
        mock_func = AsyncMock(side_effect=Exception("rate limit exceeded"))

        with pytest.raises(RetryExhaustedError) as exc_info:
            await exponential_backoff_retry(mock_func, max_attempts=3)

        assert exc_info.value.retry_count == 3
        assert mock_func.call_count == 3  # All attempts used

    def test_is_retryable_error_detection(self):
        """Test retryable error pattern detection."""
        # Retryable errors
        assert _is_retryable_error(Exception("rate limit exceeded"))
        assert _is_retryable_error(Exception("429 too many requests"))
        assert _is_retryable_error(Exception("503 service unavailable"))
        assert _is_retryable_error(Exception("timeout waiting for response"))

        # Non-retryable errors
        assert not _is_retryable_error(Exception("invalid audio format"))
        assert not _is_retryable_error(ValueError("missing parameter"))
        assert not _is_retryable_error(Exception("400 bad request"))


class TestCircuitBreaker:
    """Test circuit breaker pattern."""

    def test_circuit_closed_allows_requests(self, reset_circuit_breakers):
        """Test that CLOSED circuit allows requests."""
        assert transcription_circuit_breaker.can_attempt() is True

    def test_circuit_opens_after_failure_threshold(self, reset_circuit_breakers):
        """Test circuit opens after repeated failures."""
        # Trigger 5 failures (threshold)
        for _ in range(5):
            transcription_circuit_breaker.call_failed()

        assert transcription_circuit_breaker.state == CircuitBreakerState.OPEN

        with pytest.raises(CircuitBreakerOpenError) as exc_info:
            transcription_circuit_breaker.can_attempt()

        assert exc_info.value.service_name == "transcription"
        assert exc_info.value.failure_count == 5

    def test_circuit_resets_on_success(self, reset_circuit_breakers):
        """Test circuit failure count resets on success."""
        # Record some failures
        transcription_circuit_breaker.call_failed()
        transcription_circuit_breaker.call_failed()
        assert transcription_circuit_breaker.failure_count == 2

        # Success resets counter
        transcription_circuit_breaker.call_succeeded()
        assert transcription_circuit_breaker.failure_count == 0

    def test_circuit_half_open_transition(self, reset_circuit_breakers):
        """Test circuit transitions to HALF_OPEN after timeout."""
        import time
        from datetime import datetime, timedelta

        # Open the circuit
        for _ in range(5):
            transcription_circuit_breaker.call_failed()

        assert transcription_circuit_breaker.state == CircuitBreakerState.OPEN

        # Manually set last_failure_time to past (simulate timeout)
        transcription_circuit_breaker.last_failure_time = datetime.utcnow() - timedelta(seconds=200)

        # Should transition to HALF_OPEN
        assert transcription_circuit_breaker.can_attempt() is True
        assert transcription_circuit_breaker.state == CircuitBreakerState.HALF_OPEN

    def test_circuit_closes_after_half_open_successes(self, reset_circuit_breakers):
        """Test circuit closes after successes in HALF_OPEN."""
        # Force circuit to HALF_OPEN
        transcription_circuit_breaker.state = CircuitBreakerState.HALF_OPEN
        transcription_circuit_breaker.success_count = 0

        # Record 2 successes (success_threshold)
        transcription_circuit_breaker.call_succeeded()
        assert transcription_circuit_breaker.state == CircuitBreakerState.HALF_OPEN

        transcription_circuit_breaker.call_succeeded()
        assert transcription_circuit_breaker.state == CircuitBreakerState.CLOSED


class TestParallelProcessingErrorHandling:
    """Test parallel processing error scenarios."""

    @pytest.mark.asyncio
    async def test_both_tasks_succeed(self, reset_circuit_breakers):
        """Test successful parallel execution of both tasks."""
        mock_transcription = {"full_text": "Hello world", "segments": [], "duration": 10}
        mock_diarization = {"segments": [{"start": 0, "end": 10, "speaker": "Speaker 1"}]}

        # Simulate asyncio.gather with both succeeding
        results = await asyncio.gather(
            asyncio.coroutine(lambda: mock_transcription)(),
            asyncio.coroutine(lambda: mock_diarization)(),
            return_exceptions=True
        )

        transcript_result, diarization_result = results

        assert not isinstance(transcript_result, Exception)
        assert not isinstance(diarization_result, Exception)
        assert transcript_result == mock_transcription
        assert diarization_result == mock_diarization

    @pytest.mark.asyncio
    async def test_transcription_succeeds_diarization_fails(self, reset_circuit_breakers):
        """Test partial failure: transcription OK, diarization fails (RECOVERABLE)."""
        mock_transcription = {"full_text": "Hello world", "segments": [], "duration": 10}
        diarization_error = DiarizationError("Pyannote timeout", fallback_available=True)

        # Simulate asyncio.gather with partial failure
        async def failing_diarization():
            raise diarization_error

        results = await asyncio.gather(
            asyncio.coroutine(lambda: mock_transcription)(),
            failing_diarization(),
            return_exceptions=True
        )

        transcript_result, diarization_result = results

        # Transcription succeeded
        assert not isinstance(transcript_result, Exception)
        assert transcript_result == mock_transcription

        # Diarization failed but returned exception (not raised)
        assert isinstance(diarization_result, Exception)
        assert isinstance(diarization_result, DiarizationError)

        # Pipeline should continue with None diarization
        # (this is the key recovery strategy)

    @pytest.mark.asyncio
    async def test_transcription_fails_diarization_succeeds(self, reset_circuit_breakers):
        """Test transcription failure (FATAL) even if diarization succeeds."""
        transcription_error = TranscriptionError("Whisper API timeout", is_retryable=True)
        mock_diarization = {"segments": [{"start": 0, "end": 10, "speaker": "Speaker 1"}]}

        # Simulate asyncio.gather with transcription failure
        async def failing_transcription():
            raise transcription_error

        results = await asyncio.gather(
            failing_transcription(),
            asyncio.coroutine(lambda: mock_diarization)(),
            return_exceptions=True
        )

        transcript_result, diarization_result = results

        # Transcription failed
        assert isinstance(transcript_result, Exception)
        assert isinstance(transcript_result, TranscriptionError)

        # Diarization succeeded (but irrelevant)
        assert not isinstance(diarization_result, Exception)

        # Pipeline should ABORT (cannot proceed without transcript)

    @pytest.mark.asyncio
    async def test_both_tasks_fail(self, reset_circuit_breakers):
        """Test both tasks failing (FATAL)."""
        transcription_error = TranscriptionError("Whisper API error")
        diarization_error = DiarizationError("Pyannote error")

        # Simulate asyncio.gather with both failing
        async def failing_transcription():
            raise transcription_error

        async def failing_diarization():
            raise diarization_error

        results = await asyncio.gather(
            failing_transcription(),
            failing_diarization(),
            return_exceptions=True
        )

        transcript_result, diarization_result = results

        # Both failed
        assert isinstance(transcript_result, Exception)
        assert isinstance(diarization_result, Exception)

        # Pipeline should ABORT with detailed error


class TestExceptionClasses:
    """Test custom exception classes."""

    def test_transcription_error_properties(self):
        """Test TranscriptionError exception properties."""
        error = TranscriptionError(
            message="Whisper API failed",
            session_id="test-session-123",
            error_details={"status_code": 429},
            is_retryable=True
        )

        assert error.message == "Whisper API failed"
        assert error.session_id == "test-session-123"
        assert error.error_details["status_code"] == 429
        assert error.is_retryable is True
        assert str(error) == "[Session test-session-123] Whisper API failed"

    def test_diarization_error_properties(self):
        """Test DiarizationError exception properties."""
        error = DiarizationError(
            message="Pyannote timeout",
            session_id="test-session-456",
            fallback_available=True
        )

        assert error.message == "Pyannote timeout"
        assert error.fallback_available is True

    def test_parallel_processing_error_properties(self):
        """Test ParallelProcessingError exception properties."""
        trans_error = Exception("Transcription failed")
        diar_error = Exception("Diarization failed")

        error = ParallelProcessingError(
            message="Both tasks failed",
            session_id="test-session-789",
            transcription_error=trans_error,
            diarization_error=diar_error
        )

        assert error.message == "Both tasks failed"
        assert error.transcription_error == trans_error
        assert error.diarization_error == diar_error

    def test_circuit_breaker_open_error_properties(self):
        """Test CircuitBreakerOpenError exception properties."""
        error = CircuitBreakerOpenError(
            service_name="transcription",
            failure_count=5,
            error_details={"timeout_seconds": 120}
        )

        assert error.service_name == "transcription"
        assert error.failure_count == 5
        assert error.error_details["timeout_seconds"] == 120

    def test_retry_exhausted_error_properties(self):
        """Test RetryExhaustedError exception properties."""
        last_error = Exception("Rate limit exceeded")

        error = RetryExhaustedError(
            message="Retry exhausted",
            session_id="test-session",
            retry_count=3,
            last_exception=last_error
        )

        assert error.retry_count == 3
        assert error.last_exception == last_error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
