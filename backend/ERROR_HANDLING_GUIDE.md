# Audio Processing Error Handling Guide

## Overview

The backend audio processing service implements comprehensive error handling for parallel processing failures, ensuring the pipeline continues even when individual components fail.

## Architecture

### Parallel Processing Strategy

The service runs **transcription** and **diarization** concurrently using `asyncio.gather(return_exceptions=True)`:

```python
results = await asyncio.gather(
    transcribe_with_retry(audio_path),
    diarize_with_retry(audio_path),
    return_exceptions=True  # Collect exceptions instead of raising
)

transcript_result, diarization_result = results
```

**Key benefit:** If one task fails, the other may still succeed. We handle partial failures gracefully.

---

## Error Handling Strategy

### Decision Matrix

| Transcription | Diarization | Action | Severity |
|--------------|------------|---------|----------|
| ✅ Success   | ✅ Success  | Proceed with diarized transcript | Normal |
| ✅ Success   | ❌ Failed   | **RECOVERABLE**: Use undiarized transcript | Warning |
| ❌ Failed    | ✅ Success  | **FATAL**: Cannot proceed without transcript | Error |
| ❌ Failed    | ❌ Failed   | **FATAL**: Mark session as failed | Critical |

### Fallback Strategy

**Diarization failure is RECOVERABLE:**
- Pipeline continues with undiarized transcript
- All segments labeled as "Unknown Speaker"
- Session marked with `diarization_status: "failed"` metadata
- Warning logged for monitoring

**Transcription failure is FATAL:**
- Pipeline aborts immediately
- Session status set to `"failed"`
- Error message stored in `session.error_message`
- Circuit breaker increments failure count

---

## Exception Classes

All exceptions inherit from `ProcessingError` base class and include:
- `message`: Human-readable error description
- `session_id`: UUID for logging/tracking
- `error_details`: Dict with additional metadata

### 1. TranscriptionError

**Raised when:** Whisper API or transcription service fails

**Common causes:**
- Rate limit exceeded (429)
- Authentication failure (401)
- Network timeout
- Corrupted audio file

**Properties:**
- `is_retryable`: Boolean indicating if error is transient

**Recovery:**
```python
try:
    transcript = await transcribe_audio(audio_path)
except TranscriptionError as e:
    if e.is_retryable:
        # Retry with exponential backoff
        await retry_transcription(audio_path)
    else:
        # Mark session as failed
        await update_session_status(session_id, "failed", e.message)
```

---

### 2. DiarizationError

**Raised when:** Speaker diarization (pyannote) fails

**Common causes:**
- HuggingFace token invalid
- Audio too short (< 1 second)
- Out of memory
- Model download failure

**Properties:**
- `fallback_available`: Boolean indicating if undiarized transcript is acceptable

**Recovery:**
```python
try:
    diarization = await diarize_audio(audio_path)
except DiarizationError as e:
    if e.fallback_available:
        # Proceed with undiarized transcript
        logger.warning(f"Using undiarized transcript: {e.message}")
        diarization = None
    else:
        raise
```

---

### 3. ParallelProcessingError

**Raised when:** Both transcription AND diarization fail

**Properties:**
- `transcription_error`: Exception from transcription task
- `diarization_error`: Exception from diarization task

**Recovery:**
- No recovery possible - mark session as failed
- Log both errors for debugging
- Alert monitoring system

---

### 4. PartialProcessingError

**Raised when:** One task succeeds, one task fails

**Properties:**
- `succeeded_task`: Name of successful task ("transcription" or "diarization")
- `failed_task`: Name of failed task
- `failed_exception`: Exception from failed task

**Recovery:**
- If transcription succeeded: Proceed with available data
- If transcription failed: Escalate to `TranscriptionError`

---

### 5. CircuitBreakerOpenError

**Raised when:** Circuit breaker is OPEN after repeated failures

**Properties:**
- `service_name`: Name of protected service ("transcription" or "diarization")
- `failure_count`: Number of consecutive failures

**Recovery:**
- Return 503 Service Unavailable to client
- Wait for circuit breaker timeout (120s for transcription, 60s for diarization)
- Do NOT retry - indicates systemic issue

---

### 6. RetryExhaustedError

**Raised when:** All retry attempts exhausted for transient error

**Properties:**
- `retry_count`: Number of attempts made
- `last_exception`: Final exception after all retries

**Recovery:**
- Mark session as failed
- Store retry history for debugging
- Alert monitoring system (may indicate service degradation)

---

## Circuit Breaker Pattern

### Purpose
Prevent cascading failures by temporarily blocking requests after repeated failures.

### States

1. **CLOSED** (Normal operation)
   - All requests allowed
   - Failure count tracked
   - Transitions to OPEN after `failure_threshold` failures

2. **OPEN** (Service degraded)
   - All requests blocked with `CircuitBreakerOpenError`
   - Waits `timeout` seconds before testing recovery
   - Transitions to HALF_OPEN after timeout

3. **HALF_OPEN** (Testing recovery)
   - Limited requests allowed
   - Tracks success count
   - Transitions to CLOSED after `success_threshold` successes
   - Transitions back to OPEN on any failure

### Configuration

```python
transcription_circuit_breaker = CircuitBreaker(
    service_name="transcription",
    failure_threshold=5,    # Open after 5 consecutive failures
    timeout=120,            # Wait 120s before testing recovery
    success_threshold=2     # Close after 2 successes in HALF_OPEN
)

diarization_circuit_breaker = CircuitBreaker(
    service_name="diarization",
    failure_threshold=5,
    timeout=60,             # Shorter timeout (diarization less critical)
    success_threshold=2
)
```

### Usage

```python
# Check circuit before processing
transcription_circuit_breaker.can_attempt()  # Raises CircuitBreakerOpenError if OPEN

# Record result
if success:
    transcription_circuit_breaker.call_succeeded()
else:
    transcription_circuit_breaker.call_failed()
```

---

## Retry Logic

### Exponential Backoff

Automatically retries transient errors with increasing delays:

```python
result = await exponential_backoff_retry(
    transcribe_audio_file,
    audio_path,
    max_attempts=3,
    initial_backoff=2.0  # seconds
)
```

**Backoff schedule:**
- Attempt 1: Immediate
- Attempt 2: Wait 2.0s
- Attempt 3: Wait 4.0s
- Attempt 4: Wait 8.0s (max 60s)

### Retryable Errors

Errors are considered retryable if they match these patterns:
- `"rate limit"` (API quota)
- `"429"` (HTTP too many requests)
- `"503"` (Service unavailable)
- `"timeout"` (Network timeout)
- `"temporarily unavailable"` (Transient failure)
- `"connection reset"` (Network issue)

**Non-retryable errors** (fail immediately):
- `"400"` (Bad request - malformed input)
- `"401"` (Authentication failure)
- `"invalid audio format"` (Corrupted file)
- `ValueError`, `FileNotFoundError`

---

## Logging Strategy

### Structured Logging

All errors include structured metadata for monitoring:

```python
logger.error(
    "Transcription failed for session",
    extra={
        "session_id": str(session_id),
        "error_type": "TranscriptionError",
        "is_retryable": True,
        "retry_count": 2,
        "circuit_breaker_state": "CLOSED"
    },
    exc_info=True
)
```

### Log Levels

- **INFO**: Normal operation, progress updates
- **WARNING**: Diarization failure (recoverable), retry attempts
- **ERROR**: Transcription failure, session failed
- **CRITICAL**: Both tasks failed, circuit breaker opened

---

## Testing

### Unit Tests

Run error handling tests:

```bash
cd backend
source venv/bin/activate
pytest tests/test_audio_processing_error_handling.py -v
```

**Test coverage:**
- ✅ Retry logic (success after retries, exhaustion)
- ✅ Circuit breaker (CLOSED → OPEN → HALF_OPEN → CLOSED)
- ✅ Parallel processing (all 4 failure combinations)
- ✅ Exception properties and error messages

### Integration Tests

Test with real audio files:

```python
from app.services.audio_processing_service import AudioProcessingService

service = AudioProcessingService()

# Test with valid audio
result = await service.process_session_audio(
    session_id=uuid4(),
    audio_file_path="tests/samples/valid.mp3",
    db=db
)

# Test with corrupted audio (should fail)
with pytest.raises(TranscriptionError):
    await service.process_session_audio(
        session_id=uuid4(),
        audio_file_path="tests/samples/corrupted.mp3",
        db=db
    )
```

---

## Monitoring & Alerts

### Key Metrics to Track

1. **Transcription failure rate**
   - Alert if > 5% in 15 minutes
   - Indicates API issues or quota exhaustion

2. **Diarization failure rate**
   - Alert if > 10% in 15 minutes
   - May indicate model availability issues

3. **Circuit breaker state**
   - Alert when OPEN (service degraded)
   - Alert if OPEN > 5 minutes (sustained outage)

4. **Retry exhaustion rate**
   - Alert if > 2% sessions exhausting retries
   - Indicates persistent service issues

5. **Average processing time**
   - Alert if > 90 seconds for 1-hour audio
   - May indicate API degradation

### Example Monitoring Query

```sql
-- Sessions failed in last hour
SELECT
    COUNT(*) as failed_count,
    error_message
FROM therapy_sessions
WHERE status = 'failed'
  AND updated_at > NOW() - INTERVAL '1 hour'
GROUP BY error_message
ORDER BY failed_count DESC;
```

---

## Production Deployment

### Environment Variables

```bash
# Retry configuration
AUDIO_PROCESSING_MAX_RETRIES=3
AUDIO_PROCESSING_INITIAL_BACKOFF=2.0
AUDIO_PROCESSING_MAX_BACKOFF=60.0

# Circuit breaker configuration
TRANSCRIPTION_CIRCUIT_FAILURE_THRESHOLD=5
TRANSCRIPTION_CIRCUIT_TIMEOUT=120
DIARIZATION_CIRCUIT_FAILURE_THRESHOLD=5
DIARIZATION_CIRCUIT_TIMEOUT=60

# API keys (ensure these are set)
OPENAI_API_KEY=sk-...
HUGGINGFACE_TOKEN=hf_...
```

### Health Check Endpoint

```python
@router.get("/health/audio-processing")
async def audio_processing_health():
    """Check audio processing service health."""
    return {
        "transcription_circuit": transcription_circuit_breaker.state,
        "diarization_circuit": diarization_circuit_breaker.state,
        "transcription_failures": transcription_circuit_breaker.failure_count,
        "diarization_failures": diarization_circuit_breaker.failure_count
    }
```

---

## Troubleshooting

### Circuit Breaker Stuck OPEN

**Symptoms:**
- All processing requests fail with `CircuitBreakerOpenError`
- Lasts > 5 minutes

**Diagnosis:**
```bash
# Check circuit breaker state
curl http://localhost:8000/health/audio-processing
```

**Resolution:**
1. Check API service status (OpenAI, HuggingFace)
2. Verify API keys are valid
3. Check network connectivity
4. Manually reset circuit breaker (if needed):
   ```python
   transcription_circuit_breaker._close_circuit()
   ```

---

### High Retry Exhaustion Rate

**Symptoms:**
- Many sessions failing after 3 retry attempts
- Logs show `RetryExhaustedError`

**Diagnosis:**
```sql
SELECT error_message, COUNT(*)
FROM therapy_sessions
WHERE error_message LIKE '%Retry exhausted%'
  AND created_at > NOW() - INTERVAL '1 hour'
GROUP BY error_message;
```

**Resolution:**
1. Check API rate limits (may need quota increase)
2. Increase `max_attempts` if transient issue
3. Investigate root cause (API outage, network issues)

---

### Diarization Always Failing

**Symptoms:**
- All sessions have `diarization_status: "failed"`
- Sessions still complete (using undiarized transcript)

**Diagnosis:**
```python
# Check diarization service directly
from app.services.diarization import diarize_audio_file
result = await diarize_audio_file("test.mp3")
```

**Common causes:**
1. HuggingFace token invalid/expired
2. Pyannote model not downloaded
3. Audio files too short (< 1 second)
4. Out of memory (GPU/CPU)

**Resolution:**
1. Verify `HUGGINGFACE_TOKEN` is valid
2. Pre-download models: `python -m src.download_models`
3. Increase memory allocation
4. Check audio file duration

---

## Future Enhancements

1. **Dead Letter Queue**
   - Store failed sessions for manual reprocessing
   - Retry failed sessions during off-peak hours

2. **Adaptive Retry**
   - Adjust retry count based on error type
   - Use jitter to prevent thundering herd

3. **Health-based Circuit Breaking**
   - Check API health endpoints before processing
   - Preemptively open circuit if degraded

4. **Multi-level Fallbacks**
   - Try Whisper API → Whisper local → AssemblyAI
   - Gracefully degrade to lower-quality models

5. **Metrics Dashboard**
   - Real-time circuit breaker states
   - Processing success/failure rates
   - Average processing times

---

## Files

**Exception classes:**
- `backend/app/services/processing_exceptions.py`

**Audio processing service:**
- `backend/app/services/audio_processing_service.py`

**Tests:**
- `backend/tests/test_audio_processing_error_handling.py`

**Documentation:**
- `backend/ERROR_HANDLING_GUIDE.md` (this file)

---

## Support

For questions or issues:
1. Check logs: `tail -f logs/audio_processing.log`
2. Review circuit breaker state: `GET /health/audio-processing`
3. Run tests: `pytest tests/test_audio_processing_error_handling.py -v`
4. Contact: Backend Team (#backend-support)
