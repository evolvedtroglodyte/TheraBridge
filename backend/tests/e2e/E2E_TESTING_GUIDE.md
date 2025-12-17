# E2E Testing Guide for Session Upload Pipeline

## Overview

This directory contains end-to-end tests for the complete session upload and processing workflow:
- File upload validation
- Audio transcription
- Note extraction with AI
- Database persistence
- Error handling

## Test Architecture

### Test Strategy

We use **mocked services** for transcription and note extraction to:
1. **Speed**: Tests run in milliseconds instead of minutes
2. **Reliability**: No dependency on external APIs (OpenAI, audio processing)
3. **Cost**: No API charges during testing
4. **Determinism**: Predictable, repeatable results

### Mocked Components

Located in `tests/services/`:
- `mock_transcription.py` - Simulates audio transcription pipeline
- `mock_extraction.py` - Simulates OpenAI note extraction

### Real Components

These are tested with actual implementation:
- File upload and validation
- Database operations
- Status transitions
- Error handling
- Data schema validation

## Test Coverage

### ✅ Success Paths

1. **test_upload_mp3_complete_pipeline**
   - Upload MP3 file
   - Process through full pipeline
   - Verify all data stored correctly

2. **test_upload_wav_complete_pipeline**
   - Upload WAV file
   - Verify different audio format handled

3. **test_verify_transcript_segments_stored**
   - Check segment array populated
   - Verify speaker labels
   - Confirm chronological order

4. **test_verify_extracted_notes_schema**
   - Validate all required fields
   - Check data types
   - Verify nested objects

5. **test_verify_status_transitions**
   - uploading → transcribing → transcribed → extracting_notes → processed

6. **test_multiple_concurrent_uploads**
   - Simultaneous file uploads
   - No race conditions
   - All complete successfully

7. **test_risk_flags_detected**
   - Risk flags identified
   - Stored in database
   - Correct structure

### ❌ Error Paths

8. **test_upload_invalid_file_type**
   - Text files rejected
   - Invalid MIME types caught
   - Proper error messages

9. **test_upload_file_too_large**
   - 500MB+ files rejected
   - HTTP 413 status
   - Descriptive error

10. **test_upload_file_too_small**
    - Files < 1KB rejected
    - Prevents empty uploads

11. **test_transcription_failure**
    - Transcription errors caught
    - Status set to "failed"
    - error_message populated

12. **test_extraction_failure**
    - Extraction errors caught
    - Transcript still saved
    - Graceful degradation

13. **test_invalid_patient_id**
    - Non-existent patient rejected
    - HTTP 404 response

## Known Limitations

### Async Background Tasks

**Issue**: FastAPI's `BackgroundTasks` run after response is sent, making them hard to test with synchronous TestClient.

**Solutions Used**:
1. `asyncio.sleep()` to wait for tasks
2. Direct database queries to verify results
3. Polling pattern for status checks

**Future Improvement**: Use async test client (httpx.AsyncClient) for better async support.

### Rate Limiting

**Issue**: Rate limiting can interfere with rapid test execution.

**Solution**: Tests should mock rate limiting or use test-specific limits.

### Database State

**Issue**: Background tasks modify database after test assertions.

**Solution**: Each test gets fresh database via `test_db` fixture.

## Running Tests

### Run All E2E Tests
```bash
cd backend
source venv/bin/activate
pytest tests/e2e/ -v
```

### Run Specific Test
```bash
pytest tests/e2e/test_session_upload.py::test_upload_mp3_complete_pipeline -v
```

### Run with Coverage
```bash
pytest tests/e2e/ --cov=app --cov-report=html
```

### Run Real Audio Test (Optional)
```bash
# Requires actual audio file
pytest tests/e2e/ -k test_with_real_audio_file -v
```

## Test Data

### Sample Audio Files

Located in `tests/fixtures/audio/`:
- `test_session.mp3` - Minimal valid MP3
- `test_session.wav` - Minimal valid WAV
- `invalid.txt` - Non-audio file for error testing

These are **generated programmatically** in `tests/utils/audio_generators.py`:
- `generate_wav_file()` - Creates valid WAV with sine wave
- `generate_mp3_header()` - Creates minimal valid MP3
- `generate_invalid_audio_file()` - Creates corrupted file

### Mock Transcript Data

From `tests/services/mock_transcription.py`:
```python
{
    "segments": [
        {
            "start": 0.0,
            "end": 5.2,
            "text": "I've been feeling really anxious about work lately.",
            "speaker": "Client"
        },
        ...
    ],
    "full_text": "...",
    "language": "en",
    "duration": 40.0
}
```

### Mock Extracted Notes

From `tests/services/mock_extraction.py`:
```python
ExtractedNotes(
    key_topics=["Work-related anxiety", "Team meeting stress", ...],
    strategies=[Strategy(name="Box breathing", ...)],
    session_mood=MoodLevel.low,
    risk_flags=[],  # Or populated for risk tests
    ...
)
```

## Debugging Failed Tests

### Check Test Logs
```bash
pytest tests/e2e/ -v -s  # -s shows print statements
```

### Inspect Database After Test
```python
# Add at end of test
import pdb; pdb.set_trace()
# Then query test_db to inspect state
```

### Review Mock Responses
```python
# In test, print mock return values
print(response.json())
print(session.extracted_notes)
```

### Check Background Task Execution
```python
# Increase sleep time if tasks not completing
await asyncio.sleep(2.0)  # Instead of 1.0
```

## Adding New Tests

### Template for Success Path
```python
@pytest.mark.asyncio
async def test_new_feature(client: TestClient, test_db: Session, test_patient_e2e: Patient):
    """Test description"""
    # 1. Prepare test data
    audio_file = BytesIO(generate_wav_file())

    # 2. Mock external services
    with patch("app.services.transcription.transcribe_audio_file", new=mock_transcribe_audio_file), \
         patch("app.services.note_extraction.get_extraction_service", return_value=MockNoteExtractionService()):

        # 3. Make request
        response = client.post(
            "/api/sessions/upload",
            params={"patient_id": str(test_patient_e2e.id)},
            files={"file": ("test.wav", audio_file, "audio/wav")}
        )

        # 4. Assert response
        assert response.status_code == 200
        session_id = UUID(response.json()["id"])

        # 5. Wait for background tasks
        await asyncio.sleep(1.0)

        # 6. Verify database state
        session = test_db.query(SessionModel).filter(SessionModel.id == session_id).first()
        assert session.status == SessionStatus.processed.value
```

### Template for Error Path
```python
def test_new_error(client: TestClient, test_patient_e2e: Patient):
    """Test error description"""
    # 1. Prepare invalid data
    invalid_file = BytesIO(b"corrupted")

    # 2. Make request
    response = client.post(
        "/api/sessions/upload",
        params={"patient_id": str(test_patient_e2e.id)},
        files={"file": ("bad.wav", invalid_file, "audio/wav")}
    )

    # 3. Assert error response
    assert response.status_code == 400
    assert "error message" in response.text.lower()
```

## Integration with Real Services (Optional)

To test with real transcription and extraction:

1. Set environment variables:
```bash
export OPENAI_API_KEY="your_key"
export AUDIO_PIPELINE_DIR="../audio-transcription-pipeline"
```

2. Remove mocking from test:
```python
# Remove these lines
with patch("app.services.transcription...", ...):
    ...
```

3. Use real audio file:
```python
with open("path/to/real_audio.mp3", "rb") as f:
    audio_file = BytesIO(f.read())
```

4. Increase timeout:
```python
await asyncio.sleep(30.0)  # Real processing takes longer
```

## Best Practices

1. **Keep tests fast** - Use mocks for external services
2. **Test one thing** - Each test should verify specific behavior
3. **Clean up** - Use fixtures for setup/teardown
4. **Descriptive names** - test_what_when_expected
5. **Good assertions** - Check specific values, not just truthy
6. **Handle async** - Await background tasks before assertions
7. **Isolate tests** - No dependencies between tests

## Troubleshooting

### Tests Hanging
- Background tasks not completing
- **Fix**: Increase sleep timeout or check for infinite loops

### Flaky Tests
- Race conditions in async code
- **Fix**: Add explicit waits, check task completion

### Import Errors
- Missing dependencies
- **Fix**: `pip install -r requirements.txt`

### Database Errors
- Tables not created
- **Fix**: Ensure `test_db` fixture is used and creates tables

## Future Improvements

1. **Async test client** - Better support for background tasks
2. **Real integration tests** - Optional tests with actual services
3. **Performance tests** - Load testing with many concurrent uploads
4. **File size tests** - Test with actual large files (100MB+)
5. **Timeout tests** - Verify pipeline handles slow operations
6. **Retry logic** - Test automatic retry on transient failures

## Resources

- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest fixtures](https://docs.pytest.org/en/stable/fixture.html)
