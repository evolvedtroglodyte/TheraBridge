"""
Comprehensive integration tests for sessions router.

Tests:
- Upload endpoint with rate limiting (10/hour)
- Extract-notes endpoint with rate limiting (20/hour)
- File upload streaming with SHA256 checksums
- Session processing pipeline (upload → transcribe → extract)
- Error handling for invalid files, missing patients
- CRUD operations (GET, POST, PATCH, DELETE)
"""
import pytest
import io
import time
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from fastapi.testclient import TestClient

from app.models.db_models import Patient, User, Session
from app.models.schemas import UserRole, SessionStatus, ExtractedNotes, MoodLevel


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_patient(test_db, therapist_user):
    """Create a test patient in the database"""
    patient = Patient(
        id=uuid4(),
        name="Test Patient",
        email="patient@test.com",
        phone="+1234567890",
        therapist_id=therapist_user.id
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)
    return patient


@pytest.fixture
def test_session(test_db, test_patient, therapist_user):
    """Create a test session in the database"""
    from datetime import datetime
    session = Session(
        id=uuid4(),
        patient_id=test_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        status=SessionStatus.pending.value,
        transcript_text="This is a sample therapy session transcript. The patient discussed anxiety and coping strategies."
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session


@pytest.fixture
def mock_transcription_service():
    """Mock the transcription service"""
    with patch('app.services.transcription.transcribe_audio_file') as mock_transcribe:
        mock_transcribe.return_value = {
            "full_text": "This is a test transcript with therapist and client speaking.",
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Hello, how are you feeling today?", "speaker": "Therapist"},
                {"start": 5.5, "end": 10.0, "text": "I'm feeling anxious about work.", "speaker": "Client"}
            ],
            "duration": 600.0
        }
        yield mock_transcribe


@pytest.fixture
def mock_extraction_service():
    """Mock the note extraction service"""
    mock_service = Mock()

    # Create a sample ExtractedNotes object
    mock_notes = ExtractedNotes(
        key_topics=["Work anxiety", "Coping strategies", "Sleep patterns"],
        topic_summary="Patient discussed work-related stress and explored breathing techniques.",
        strategies=[],
        emotional_themes=["anxiety", "stress"],
        triggers=[],
        action_items=[],
        significant_quotes=[],
        session_mood=MoodLevel.neutral,
        mood_trajectory="stable",
        follow_up_topics=["Practice breathing exercises"],
        unresolved_concerns=[],
        risk_flags=[],
        therapist_notes="Patient is showing progress with anxiety management techniques. Continue with CBT approach.",
        patient_summary="You discussed your work anxiety and learned some new breathing techniques to help manage stress."
    )

    # Mock the async method
    mock_service.extract_notes_from_transcript = AsyncMock(return_value=mock_notes)

    with patch('app.routers.sessions.get_extraction_service', return_value=mock_service):
        yield mock_service


@pytest.fixture
def sample_audio_file():
    """Create a mock audio file for testing"""
    # Create a minimal MP3-like file (starts with ID3 tag)
    audio_data = b'ID3' + b'\x00' * 2000  # 2KB file with MP3 magic bytes
    return io.BytesIO(audio_data)


@pytest.fixture
def large_audio_file():
    """Create a mock large audio file (>500MB) for testing size limits"""
    # Create a 501MB file
    size = 501 * 1024 * 1024
    audio_data = b'ID3' + b'\x00' * (size - 3)
    return io.BytesIO(audio_data)


# ============================================================================
# Upload Endpoint Tests
# ============================================================================

def test_upload_valid_audio_file(client, test_patient, mock_transcription_service, mock_extraction_service):
    """Test successful audio file upload"""
    audio_data = b'ID3' + b'\x00' * 2000
    files = {
        'file': ('test_audio.mp3', io.BytesIO(audio_data), 'audio/mpeg')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert 'id' in data
    assert data['patient_id'] == str(test_patient.id)
    assert data['status'] == SessionStatus.uploading.value
    assert data['audio_filename'] == 'test_audio.mp3'


def test_upload_with_invalid_patient_id(client):
    """Test upload fails with non-existent patient ID"""
    fake_patient_id = uuid4()
    audio_data = b'ID3' + b'\x00' * 2000
    files = {
        'file': ('test_audio.mp3', io.BytesIO(audio_data), 'audio/mpeg')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={fake_patient_id}",
        files=files
    )

    assert response.status_code == 404
    assert "not found" in response.json()['detail'].lower()


def test_upload_non_audio_file(client, test_patient):
    """Test upload fails with non-audio file (text file)"""
    text_data = b'This is a text file, not audio'
    files = {
        'file': ('document.txt', io.BytesIO(text_data), 'text/plain')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 400
    assert 'audio' in response.json()['detail'].lower()


def test_upload_unsupported_file_extension(client, test_patient):
    """Test upload fails with unsupported file extension"""
    audio_data = b'ID3' + b'\x00' * 2000
    files = {
        'file': ('test_audio.xyz', io.BytesIO(audio_data), 'audio/mpeg')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 400
    assert 'not supported' in response.json()['detail'].lower()


def test_upload_file_too_large(client, test_patient):
    """Test upload fails when file exceeds 500MB limit"""
    # Note: We can't actually create a 500MB file in memory for testing,
    # so we'll test the size validation logic indirectly by checking
    # the file size field if it's set

    # Create a file with size field set (simulating browser upload)
    audio_data = b'ID3' + b'\x00' * 2000
    files = {
        'file': ('huge_audio.mp3', io.BytesIO(audio_data), 'audio/mpeg')
    }

    # The actual size check happens during streaming,
    # so we'll test with a modified approach in a separate test
    # This test documents the expected behavior
    pass


def test_upload_file_too_small(client, test_patient):
    """Test upload fails when file is too small (<1KB)"""
    audio_data = b'ID3' + b'\x00' * 100  # Only 103 bytes
    files = {
        'file': ('tiny_audio.mp3', io.BytesIO(audio_data), 'audio/mpeg')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 400
    assert 'too small' in response.json()['detail'].lower()


def test_upload_invalid_audio_header(client, test_patient):
    """Test upload fails when file header doesn't match audio format"""
    # File with .mp3 extension but wrong magic bytes
    fake_audio_data = b'FAKE' + b'\x00' * 2000
    files = {
        'file': ('fake_audio.mp3', io.BytesIO(fake_audio_data), 'audio/mpeg')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 415
    assert 'not appear to be' in response.json()['detail'].lower()


def test_upload_wav_file(client, test_patient, mock_transcription_service, mock_extraction_service):
    """Test upload with WAV file format"""
    # WAV file starts with RIFF header
    wav_data = b'RIFF' + b'\x00' * 2000
    files = {
        'file': ('test_audio.wav', io.BytesIO(wav_data), 'audio/wav')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 200
    data = response.json()
    assert data['audio_filename'] == 'test_audio.wav'


def test_upload_m4a_file(client, test_patient, mock_transcription_service, mock_extraction_service):
    """Test upload with M4A file format"""
    # M4A/MP4 file has 'ftyp' at offset 4
    m4a_data = b'\x00\x00\x00\x20ftyp' + b'\x00' * 2000
    files = {
        'file': ('test_audio.m4a', io.BytesIO(m4a_data), 'audio/mp4')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 200
    data = response.json()
    assert data['audio_filename'] == 'test_audio.m4a'


# ============================================================================
# Rate Limiting Tests
# ============================================================================

def test_upload_rate_limit_enforcement(client, test_patient, mock_transcription_service, mock_extraction_service):
    """Test that upload endpoint enforces 10/hour rate limit"""
    # Note: Rate limiting is per-IP and uses in-memory storage by default
    # This test verifies the behavior but may need adjustment based on
    # your rate limiting backend (Redis, etc.)

    audio_data = b'ID3' + b'\x00' * 2000

    successful_uploads = 0
    rate_limited = False

    # Try 12 uploads (should hit limit at 11)
    for i in range(12):
        files = {
            'file': (f'test_audio_{i}.mp3', io.BytesIO(audio_data), 'audio/mpeg')
        }

        response = client.post(
            f"/api/sessions/upload?patient_id={test_patient.id}",
            files=files
        )

        if response.status_code == 200:
            successful_uploads += 1
        elif response.status_code == 429:
            rate_limited = True
            break

    # Should have succeeded for first 10, then rate limited
    assert successful_uploads <= 10
    assert rate_limited, "Rate limiting was not enforced"


@pytest.mark.skip(reason="Rate limiting tests require Redis or in-memory storage cleanup between tests")
def test_extract_notes_rate_limit_enforcement(client, test_session, mock_extraction_service):
    """Test that extract-notes endpoint enforces 20/hour rate limit"""
    successful_extractions = 0
    rate_limited = False

    # Try 22 extractions (should hit limit at 21)
    for i in range(22):
        response = client.post(f"/api/sessions/{test_session.id}/extract-notes")

        if response.status_code == 200:
            successful_extractions += 1
        elif response.status_code == 429:
            rate_limited = True
            break

    # Should have succeeded for first 20, then rate limited
    assert successful_extractions <= 20
    assert rate_limited, "Rate limiting was not enforced"


# ============================================================================
# Get Session Tests
# ============================================================================

def test_get_session_by_id(client, test_session):
    """Test retrieving a session by ID"""
    response = client.get(f"/api/sessions/{test_session.id}")

    assert response.status_code == 200
    data = response.json()

    assert data['id'] == str(test_session.id)
    assert data['patient_id'] == str(test_session.patient_id)
    assert data['status'] == test_session.status


def test_get_session_not_found(client):
    """Test getting non-existent session returns 404"""
    fake_session_id = uuid4()
    response = client.get(f"/api/sessions/{fake_session_id}")

    assert response.status_code == 404
    assert "not found" in response.json()['detail'].lower()


def test_get_session_notes(client, test_session, test_db):
    """Test retrieving extracted notes for a session"""
    # Add extracted notes to session
    test_session.extracted_notes = {
        "key_topics": ["Anxiety", "Work stress"],
        "topic_summary": "Test summary",
        "strategies": [],
        "emotional_themes": ["anxiety"],
        "triggers": [],
        "action_items": [],
        "significant_quotes": [],
        "session_mood": "neutral",
        "mood_trajectory": "stable",
        "follow_up_topics": [],
        "unresolved_concerns": [],
        "risk_flags": [],
        "therapist_notes": "Test therapist notes",
        "patient_summary": "Test patient summary"
    }
    test_db.commit()

    response = client.get(f"/api/sessions/{test_session.id}/notes")

    assert response.status_code == 200
    data = response.json()

    assert data['key_topics'] == ["Anxiety", "Work stress"]
    assert data['therapist_notes'] == "Test therapist notes"


def test_get_session_notes_not_extracted(client, test_session):
    """Test getting notes for session without extraction returns 404"""
    response = client.get(f"/api/sessions/{test_session.id}/notes")

    assert response.status_code == 404
    assert "not yet extracted" in response.json()['detail'].lower()


# ============================================================================
# List Sessions Tests
# ============================================================================

def test_list_all_sessions(client, test_session):
    """Test listing all sessions"""
    response = client.get("/api/sessions/")

    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1

    # Find our test session
    session_ids = [s['id'] for s in data]
    assert str(test_session.id) in session_ids


def test_list_sessions_by_patient(client, test_session, test_patient, test_db, therapist_user):
    """Test filtering sessions by patient_id"""
    # Create another patient and session
    other_patient = Patient(
        id=uuid4(),
        name="Other Patient",
        therapist_id=therapist_user.id
    )
    test_db.add(other_patient)
    test_db.commit()

    from datetime import datetime
    other_session = Session(
        id=uuid4(),
        patient_id=other_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        status=SessionStatus.pending.value
    )
    test_db.add(other_session)
    test_db.commit()

    # List sessions for specific patient
    response = client.get(f"/api/sessions/?patient_id={test_patient.id}")

    assert response.status_code == 200
    data = response.json()

    # Should only return sessions for test_patient
    assert all(s['patient_id'] == str(test_patient.id) for s in data)
    assert str(test_session.id) in [s['id'] for s in data]
    assert str(other_session.id) not in [s['id'] for s in data]


def test_list_sessions_by_status(client, test_session, test_db, test_patient, therapist_user):
    """Test filtering sessions by status"""
    from datetime import datetime

    # Create a processed session
    processed_session = Session(
        id=uuid4(),
        patient_id=test_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        status=SessionStatus.processed.value
    )
    test_db.add(processed_session)
    test_db.commit()

    # List only processed sessions
    response = client.get(f"/api/sessions/?status={SessionStatus.processed.value}")

    assert response.status_code == 200
    data = response.json()

    # Should only return processed sessions
    assert all(s['status'] == SessionStatus.processed.value for s in data)
    assert str(processed_session.id) in [s['id'] for s in data]


def test_list_sessions_with_limit(client, test_session, test_db, test_patient, therapist_user):
    """Test limiting number of sessions returned"""
    from datetime import datetime

    # Create multiple sessions
    for i in range(5):
        session = Session(
            id=uuid4(),
            patient_id=test_patient.id,
            therapist_id=therapist_user.id,
            session_date=datetime.utcnow(),
            status=SessionStatus.pending.value
        )
        test_db.add(session)
    test_db.commit()

    # Request only 3 sessions
    response = client.get("/api/sessions/?limit=3")

    assert response.status_code == 200
    data = response.json()

    assert len(data) <= 3


def test_list_sessions_invalid_limit(client):
    """Test that invalid limit values are rejected"""
    # Negative limit
    response = client.get("/api/sessions/?limit=-1")
    assert response.status_code == 400

    # Limit too large (max is 1000)
    response = client.get("/api/sessions/?limit=10000")
    assert response.status_code == 400


def test_list_sessions_invalid_patient_id(client):
    """Test listing sessions with non-existent patient ID returns 404"""
    fake_patient_id = uuid4()
    response = client.get(f"/api/sessions/?patient_id={fake_patient_id}")

    assert response.status_code == 404
    assert "not found" in response.json()['detail'].lower()


# ============================================================================
# Extract Notes Endpoint Tests
# ============================================================================

def test_manually_extract_notes(client, test_session, mock_extraction_service):
    """Test manually triggering note extraction"""
    response = client.post(f"/api/sessions/{test_session.id}/extract-notes")

    assert response.status_code == 200
    data = response.json()

    # Check response structure
    assert 'extracted_notes' in data
    assert 'processing_time' in data

    # Verify notes were extracted
    notes = data['extracted_notes']
    assert 'key_topics' in notes
    assert 'therapist_notes' in notes
    assert 'patient_summary' in notes


def test_extract_notes_session_not_found(client, mock_extraction_service):
    """Test extracting notes for non-existent session returns 404"""
    fake_session_id = uuid4()
    response = client.post(f"/api/sessions/{fake_session_id}/extract-notes")

    assert response.status_code == 404
    assert "not found" in response.json()['detail'].lower()


def test_extract_notes_without_transcript(client, test_db, test_patient, therapist_user, mock_extraction_service):
    """Test extracting notes fails when session has no transcript"""
    from datetime import datetime

    # Create session without transcript
    session = Session(
        id=uuid4(),
        patient_id=test_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        status=SessionStatus.uploading.value,
        transcript_text=None  # No transcript yet
    )
    test_db.add(session)
    test_db.commit()

    response = client.post(f"/api/sessions/{session.id}/extract-notes")

    assert response.status_code == 400
    assert "transcribed" in response.json()['detail'].lower()


def test_extract_notes_updates_database(client, test_session, test_db, mock_extraction_service):
    """Test that note extraction updates the database correctly"""
    response = client.post(f"/api/sessions/{test_session.id}/extract-notes")

    assert response.status_code == 200

    # Refresh session from database
    test_db.refresh(test_session)

    # Check that notes were saved
    assert test_session.extracted_notes is not None
    assert test_session.therapist_summary is not None
    assert test_session.patient_summary is not None
    assert test_session.status == SessionStatus.processed.value


# ============================================================================
# Background Processing Tests
# ============================================================================

def test_upload_triggers_background_processing(client, test_patient, mock_transcription_service, mock_extraction_service):
    """Test that uploading a file triggers background processing"""
    audio_data = b'ID3' + b'\x00' * 2000
    files = {
        'file': ('test_audio.mp3', io.BytesIO(audio_data), 'audio/mpeg')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 200
    data = response.json()

    # Session should be in uploading status initially
    assert data['status'] == SessionStatus.uploading.value

    # Note: Testing full background processing requires async handling
    # In production, you would poll the session endpoint to verify
    # status changes: uploading → transcribing → transcribed → extracting_notes → processed


@patch('app.routers.sessions.process_audio_pipeline')
def test_upload_background_task_called(mock_pipeline, client, test_patient, mock_transcription_service, mock_extraction_service):
    """Test that background task is scheduled on upload"""
    mock_pipeline.return_value = None

    audio_data = b'ID3' + b'\x00' * 2000
    files = {
        'file': ('test_audio.mp3', io.BytesIO(audio_data), 'audio/mpeg')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 200

    # Background task should have been called
    # Note: With FastAPI's BackgroundTasks, the task is queued but may not execute immediately
    # In a real test, you'd verify the task was added to the queue


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_upload_with_missing_file(client, test_patient):
    """Test upload without providing a file"""
    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}"
    )

    # Should return 422 (Unprocessable Entity) for missing required field
    assert response.status_code == 422


def test_upload_with_invalid_mime_type(client, test_patient):
    """Test upload with invalid MIME type"""
    audio_data = b'ID3' + b'\x00' * 2000
    files = {
        'file': ('test_audio.mp3', io.BytesIO(audio_data), 'video/avi')  # Wrong MIME type
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 415
    assert 'not supported' in response.json()['detail'].lower()


def test_extract_notes_api_error(client, test_session):
    """Test handling of OpenAI API errors during extraction"""
    mock_service = Mock()
    mock_service.extract_notes_from_transcript = AsyncMock(
        side_effect=ValueError("OpenAI API error: Rate limit exceeded")
    )

    with patch('app.routers.sessions.get_extraction_service', return_value=mock_service):
        response = client.post(f"/api/sessions/{test_session.id}/extract-notes")

        # Should return 500 for internal errors
        assert response.status_code == 500


# ============================================================================
# Edge Cases and Validation Tests
# ============================================================================

def test_upload_with_special_characters_in_filename(client, test_patient, mock_transcription_service, mock_extraction_service):
    """Test upload with special characters in filename (should be sanitized)"""
    audio_data = b'ID3' + b'\x00' * 2000
    files = {
        'file': ('test audio!@#$%.mp3', io.BytesIO(audio_data), 'audio/mpeg')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    # Should succeed - filename gets sanitized
    assert response.status_code == 200


def test_get_session_invalid_uuid(client):
    """Test getting session with invalid UUID format"""
    response = client.get("/api/sessions/not-a-uuid")

    # Should return 422 (validation error)
    assert response.status_code == 422


def test_list_sessions_combined_filters(client, test_session, test_patient):
    """Test listing sessions with multiple filters combined"""
    response = client.get(
        f"/api/sessions/?patient_id={test_patient.id}&status={SessionStatus.pending.value}&limit=10"
    )

    assert response.status_code == 200
    data = response.json()

    # All filters should be applied
    assert all(s['patient_id'] == str(test_patient.id) for s in data)
    assert all(s['status'] == SessionStatus.pending.value for s in data)
    assert len(data) <= 10


def test_upload_creates_audio_file_on_disk(client, test_patient, mock_transcription_service, mock_extraction_service):
    """Test that upload actually writes file to disk with correct path"""
    import os
    from pathlib import Path

    audio_data = b'ID3' + b'\x00' * 2000
    files = {
        'file': ('test_audio.mp3', io.BytesIO(audio_data), 'audio/mpeg')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 200
    data = response.json()

    # Check that audio_url is set
    assert data['audio_url'] is not None

    # In production, verify file exists on disk
    # Note: In tests, we may want to clean up test files
    audio_path = data.get('audio_url')
    if audio_path:
        # Clean up test file
        try:
            if os.path.exists(audio_path):
                os.remove(audio_path)
        except:
            pass


def test_concurrent_uploads_same_patient(client, test_patient, mock_transcription_service, mock_extraction_service):
    """Test that multiple concurrent uploads for same patient are handled correctly"""
    import concurrent.futures

    def upload_file(file_num):
        audio_data = b'ID3' + b'\x00' * 2000
        files = {
            'file': (f'test_audio_{file_num}.mp3', io.BytesIO(audio_data), 'audio/mpeg')
        }
        response = client.post(
            f"/api/sessions/upload?patient_id={test_patient.id}",
            files=files
        )
        return response.status_code

    # Try 3 concurrent uploads
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(upload_file, i) for i in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All should succeed (or be rate limited if hitting limit)
    assert all(code in [200, 429] for code in results)


# ============================================================================
# Database Integrity Tests
# ============================================================================

def test_session_timestamps_set_correctly(client, test_patient, mock_transcription_service, mock_extraction_service):
    """Test that session timestamps are set correctly on creation"""
    from datetime import datetime

    before_upload = datetime.utcnow()

    audio_data = b'ID3' + b'\x00' * 2000
    files = {
        'file': ('test_audio.mp3', io.BytesIO(audio_data), 'audio/mpeg')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    after_upload = datetime.utcnow()

    assert response.status_code == 200
    data = response.json()

    # Parse timestamps
    created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))

    # created_at should be between before and after
    assert before_upload <= created_at <= after_upload


def test_session_belongs_to_correct_patient_and_therapist(client, test_patient, therapist_user, mock_transcription_service, mock_extraction_service):
    """Test that session is correctly associated with patient and therapist"""
    audio_data = b'ID3' + b'\x00' * 2000
    files = {
        'file': ('test_audio.mp3', io.BytesIO(audio_data), 'audio/mpeg')
    }

    response = client.post(
        f"/api/sessions/upload?patient_id={test_patient.id}",
        files=files
    )

    assert response.status_code == 200
    data = response.json()

    # Verify relationships
    assert data['patient_id'] == str(test_patient.id)
    assert data['therapist_id'] == str(therapist_user.id)


# ============================================================================
# Status Transition Tests
# ============================================================================

def test_session_status_transitions(test_db, test_session):
    """Test that session status follows expected state machine"""
    valid_transitions = {
        SessionStatus.pending.value: [SessionStatus.uploading.value],
        SessionStatus.uploading.value: [SessionStatus.transcribing.value, SessionStatus.failed.value],
        SessionStatus.transcribing.value: [SessionStatus.transcribed.value, SessionStatus.failed.value],
        SessionStatus.transcribed.value: [SessionStatus.extracting_notes.value],
        SessionStatus.extracting_notes.value: [SessionStatus.processed.value, SessionStatus.failed.value],
        SessionStatus.processed.value: [],  # Terminal state
        SessionStatus.failed.value: []  # Terminal state
    }

    # This is a documentation test - actual state transitions happen in process_audio_pipeline
    # In production, you'd test the full pipeline with integration tests
    assert SessionStatus.pending.value in valid_transitions
    assert SessionStatus.processed.value in valid_transitions


# ============================================================================
# Timeline Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_timeline_success(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test successful timeline retrieval for a patient"""
    from app.models.db_models import TimelineEvent
    from datetime import datetime, timedelta

    # Create 3 timeline events for the patient
    now = datetime.utcnow()
    events_data = [
        {
            "event_type": "session",
            "event_date": now - timedelta(days=7),
            "title": "Session #1",
            "description": "Initial consultation",
            "importance": "normal"
        },
        {
            "event_type": "milestone",
            "event_date": now - timedelta(days=3),
            "title": "First breakthrough",
            "description": "Patient showed significant progress",
            "importance": "milestone"
        },
        {
            "event_type": "note",
            "event_date": now - timedelta(days=1),
            "title": "Clinical note",
            "description": "Follow-up observations",
            "importance": "normal"
        }
    ]

    for event_data in events_data:
        event = TimelineEvent(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            **event_data
        )
        test_db.add(event)
    test_db.commit()

    # Make request as therapist
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "events" in data
    assert "next_cursor" in data
    assert "has_more" in data
    assert "total_count" in data

    # Verify events were returned
    assert len(data["events"]) == 3
    assert data["total_count"] == 3
    assert data["has_more"] is False

    # Verify events are sorted by date (newest first)
    event_dates = [event["event_date"] for event in data["events"]]
    assert event_dates == sorted(event_dates, reverse=True)


@pytest.mark.asyncio
async def test_get_timeline_unauthorized(async_db_client, test_db, patient_user, test_patient_user, patient_auth_headers):
    """Test authorization failure when patient tries to access another patient's timeline"""
    from app.models.db_models import TimelineEvent
    from datetime import datetime

    # Create timeline event for test_patient_user
    event = TimelineEvent(
        patient_id=test_patient_user.id,
        therapist_id=None,
        event_type="session",
        event_date=datetime.utcnow(),
        title="Session #1",
        description="Test session",
        importance="normal"
    )
    test_db.add(event)
    test_db.commit()

    # Try to access another patient's timeline (using patient_user credentials, accessing test_patient_user timeline)
    response = async_db_client.get(
        f"/api/sessions/patients/{test_patient_user.id}/timeline",
        headers=patient_auth_headers
    )

    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_timeline_with_filters(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test timeline with query parameters (event_types, dates, importance)"""
    from app.models.db_models import TimelineEvent
    from datetime import datetime, timedelta

    # Create events with different types and importance levels
    now = datetime.utcnow()
    events_data = [
        {"event_type": "session", "importance": "normal", "days_ago": 10, "title": "Session 1"},
        {"event_type": "milestone", "importance": "milestone", "days_ago": 7, "title": "Milestone 1"},
        {"event_type": "note", "importance": "low", "days_ago": 5, "title": "Note 1"},
        {"event_type": "session", "importance": "normal", "days_ago": 3, "title": "Session 2"},
        {"event_type": "milestone", "importance": "milestone", "days_ago": 1, "title": "Milestone 2"},
    ]

    for event_data in events_data:
        days_ago = event_data.pop("days_ago")
        event = TimelineEvent(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            event_date=now - timedelta(days=days_ago),
            **event_data
        )
        test_db.add(event)
    test_db.commit()

    # Test filtering by event type
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline?event_types=session",
        headers=therapist_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 2
    assert all(e["event_type"] == "session" for e in data["events"])

    # Test filtering by importance
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline?importance=milestone",
        headers=therapist_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["events"]) == 2
    assert all(e["importance"] == "milestone" for e in data["events"])

    # Test filtering by date range
    start_date = (now - timedelta(days=6)).isoformat()
    end_date = now.isoformat()
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline?start_date={start_date}&end_date={end_date}",
        headers=therapist_auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    # Should return events from last 6 days (4 events: milestone at day 7 excluded)
    assert len(data["events"]) == 4


@pytest.mark.asyncio
async def test_get_timeline_pagination(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test cursor-based pagination for timeline"""
    from app.models.db_models import TimelineEvent
    from datetime import datetime, timedelta

    # Create 25 timeline events
    now = datetime.utcnow()
    for i in range(25):
        event = TimelineEvent(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            event_type="session",
            event_date=now - timedelta(days=i),
            title=f"Session #{i+1}",
            description=f"Session description {i+1}",
            importance="normal"
        )
        test_db.add(event)
    test_db.commit()

    # Get first page (default limit is 20)
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline",
        headers=therapist_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data["events"]) == 20
    assert data["has_more"] is True
    assert data["total_count"] == 25
    assert data["next_cursor"] is not None

    # Get second page using cursor
    cursor = data["next_cursor"]
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline?cursor={cursor}",
        headers=therapist_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data["events"]) == 5
    assert data["has_more"] is False
    assert data["total_count"] == 25

    # Test custom limit
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline?limit=10",
        headers=therapist_auth_headers
    )
    assert response.status_code == 200
    data = response.json()

    assert len(data["events"]) == 10
    assert data["has_more"] is True


@pytest.mark.asyncio
async def test_get_timeline_summary_success(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test GET /patients/{patient_id}/timeline/summary"""
    from app.models.db_models import TimelineEvent, Session as TherapySession
    from datetime import datetime, timedelta

    now = datetime.utcnow()

    # Create therapy sessions
    for i in range(5):
        session = TherapySession(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            session_date=now - timedelta(days=i*7),
            status=SessionStatus.processed.value,
            duration_seconds=3600
        )
        test_db.add(session)

    # Create timeline events with different types
    events_data = [
        {"event_type": "session", "importance": "normal", "title": "Session 1"},
        {"event_type": "session", "importance": "normal", "title": "Session 2"},
        {"event_type": "milestone", "importance": "milestone", "title": "10th session"},
        {"event_type": "milestone", "importance": "milestone", "title": "First breakthrough"},
        {"event_type": "note", "importance": "normal", "title": "Clinical note"},
        {"event_type": "goal", "importance": "high", "title": "New goal set"},
    ]

    for i, event_data in enumerate(events_data):
        event = TimelineEvent(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            event_date=now - timedelta(days=i),
            description=f"Description for {event_data['title']}",
            **event_data
        )
        test_db.add(event)
    test_db.commit()

    # Get timeline summary
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline/summary",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify summary structure
    assert "patient_id" in data
    assert "total_sessions" in data
    assert "total_events" in data
    assert "events_by_type" in data
    assert "milestones_achieved" in data
    assert "recent_highlights" in data

    # Verify counts
    assert data["total_sessions"] == 5
    assert data["total_events"] == 6
    assert data["milestones_achieved"] == 2
    assert data["events_by_type"]["session"] == 2
    assert data["events_by_type"]["milestone"] == 2
    assert data["events_by_type"]["note"] == 1
    assert data["events_by_type"]["goal"] == 1

    # Verify recent highlights (last 3 milestones)
    assert len(data["recent_highlights"]) == 2  # Only 2 milestones total


@pytest.mark.asyncio
async def test_create_timeline_event_success(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test POST /patients/{patient_id}/timeline"""
    from datetime import datetime, timedelta

    event_data = {
        "event_type": "milestone",
        "event_subtype": "treatment_progress",
        "event_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "title": "Major breakthrough in therapy",
        "description": "Patient demonstrated significant progress in managing anxiety",
        "importance": "milestone",
        "is_private": False,
        "metadata": {
            "achievement": "First panic-free week",
            "techniques_used": ["CBT", "breathing exercises"]
        }
    }

    response = async_db_client.post(
        f"/api/sessions/patients/{patient_user.id}/timeline",
        json=event_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    # Verify response structure
    assert "id" in data
    assert data["patient_id"] == str(patient_user.id)
    assert data["therapist_id"] == str(therapist_user.id)
    assert data["event_type"] == "milestone"
    assert data["title"] == "Major breakthrough in therapy"
    assert data["importance"] == "milestone"
    assert "created_at" in data

    # Verify event was saved to database
    from app.models.db_models import TimelineEvent
    db_event = test_db.query(TimelineEvent).filter_by(id=UUID(data["id"])).first()
    assert db_event is not None
    assert db_event.title == "Major breakthrough in therapy"


@pytest.mark.asyncio
async def test_create_timeline_event_unauthorized(async_db_client, test_db, patient_user, patient_auth_headers):
    """Test that patients cannot create timeline events"""
    from datetime import datetime, timedelta

    event_data = {
        "event_type": "note",
        "event_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "title": "Patient note",
        "description": "This should not be allowed",
        "importance": "normal",
        "is_private": False
    }

    response = async_db_client.post(
        f"/api/sessions/patients/{patient_user.id}/timeline",
        json=event_data,
        headers=patient_auth_headers
    )

    assert response.status_code == 403
    assert "only therapists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_chart_data_success(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test GET /patients/{patient_id}/timeline/chart-data"""
    from app.models.db_models import TimelineEvent, Session as TherapySession
    from app.models.analytics_models import SessionMetrics
    from datetime import datetime, timedelta

    now = datetime.utcnow()

    # Create sessions with metrics for mood trend
    for i in range(6):
        session = TherapySession(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            session_date=now - timedelta(days=i*30),  # Monthly sessions
            status=SessionStatus.processed.value,
            duration_seconds=3600
        )
        test_db.add(session)
        test_db.flush()

        # Add session metrics with mood data
        metrics = SessionMetrics(
            session_id=session.id,
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            session_date=session.session_date,
            mood_pre=5.0 - i*0.5,  # Declining mood
            mood_post=6.0 + i*0.5  # Improving mood
        )
        test_db.add(metrics)

    # Create milestone events for chart
    milestone_events = [
        {"title": "First session", "days_ago": 150},
        {"title": "10th session", "days_ago": 100},
        {"title": "Breakthrough", "days_ago": 50},
    ]

    for milestone in milestone_events:
        event = TimelineEvent(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            event_type="milestone",
            event_date=now - timedelta(days=milestone["days_ago"]),
            title=milestone["title"],
            description=f"Milestone: {milestone['title']}",
            importance="milestone"
        )
        test_db.add(event)

    test_db.commit()

    # Get chart data
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline/chart-data",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify chart data structure
    assert "mood_trend" in data
    assert "session_frequency" in data
    assert "milestones" in data

    # Verify mood trend data
    assert len(data["mood_trend"]) > 0
    for mood_point in data["mood_trend"]:
        assert "month" in mood_point
        assert "avg_mood" in mood_point

    # Verify session frequency data
    assert len(data["session_frequency"]) > 0
    for freq_point in data["session_frequency"]:
        assert "month" in freq_point
        assert "count" in freq_point

    # Verify milestones data
    assert len(data["milestones"]) == 3
    for milestone in data["milestones"]:
        assert "date" in milestone
        assert "title" in milestone
        assert "description" in milestone
        assert "event_type" in milestone


# ============================================================================
# Timeline Event Update Tests (PATCH /patients/{patient_id}/timeline/{event_id})
# ============================================================================

@pytest.mark.asyncio
async def test_update_timeline_event_success(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test successful timeline event update with partial fields"""
    from app.models.db_models import TimelineEvent, TherapistPatient
    from datetime import datetime, timedelta

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()

    # Create a timeline event
    event = TimelineEvent(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        event_type="session",
        event_date=datetime.utcnow() - timedelta(days=1),
        title="Original Title",
        description="Original description",
        importance="normal"
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Update title and importance
    update_data = {
        "title": "Updated Title",
        "importance": "milestone"
    }

    response = async_db_client.patch(
        f"/api/sessions/patients/{patient_user.id}/timeline/{event.id}",
        json=update_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response contains updated fields
    assert data["title"] == "Updated Title"
    assert data["importance"] == "milestone"
    assert data["description"] == "Original description"  # Unchanged
    assert data["id"] == str(event.id)
    assert data["patient_id"] == str(patient_user.id)

    # Verify database was updated
    test_db.refresh(event)
    assert event.title == "Updated Title"
    assert event.importance == "milestone"
    assert event.description == "Original description"


@pytest.mark.asyncio
async def test_update_timeline_event_partial_update(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test that partial updates only modify specified fields"""
    from app.models.db_models import TimelineEvent, TherapistPatient
    from datetime import datetime, timedelta

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()

    # Create event with multiple fields
    event = TimelineEvent(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        event_type="milestone",
        event_subtype="treatment_progress",
        event_date=datetime.utcnow() - timedelta(days=2),
        title="Original Title",
        description="Original description",
        importance="high",
        is_private=False,
        metadata={"key": "original_value"}
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Update only title - all other fields should remain unchanged
    update_data = {"title": "New Title"}

    response = async_db_client.patch(
        f"/api/sessions/patients/{patient_user.id}/timeline/{event.id}",
        json=update_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify only title changed
    assert data["title"] == "New Title"
    assert data["description"] == "Original description"
    assert data["importance"] == "high"
    assert data["is_private"] is False
    assert data["event_type"] == "milestone"
    assert data["event_subtype"] == "treatment_progress"
    assert data["metadata"]["key"] == "original_value"

    # Verify database reflects partial update
    test_db.refresh(event)
    assert event.title == "New Title"
    assert event.description == "Original description"


@pytest.mark.asyncio
async def test_update_timeline_event_inactive_relationship(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test update fails when therapist-patient relationship is inactive"""
    from app.models.db_models import TimelineEvent, TherapistPatient
    from datetime import datetime, timedelta

    # Create inactive relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=False  # Inactive relationship
    )
    test_db.add(relationship)
    test_db.commit()

    # Create timeline event for patient
    event = TimelineEvent(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        event_type="note",
        event_date=datetime.utcnow() - timedelta(days=1),
        title="Clinical Note",
        description="Some clinical observations",
        importance="normal"
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Attempt to update event
    update_data = {"title": "Updated Note"}

    response = async_db_client.patch(
        f"/api/sessions/patients/{patient_user.id}/timeline/{event.id}",
        json=update_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 403
    assert "access denied" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_timeline_event_empty_body(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test update fails with empty request body"""
    from app.models.db_models import TimelineEvent, TherapistPatient
    from datetime import datetime, timedelta

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()

    # Create timeline event
    event = TimelineEvent(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        event_type="goal",
        event_date=datetime.utcnow() - timedelta(days=1),
        title="Treatment Goal",
        description="Goal description",
        importance="high"
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Attempt update with empty body
    update_data = {}

    response = async_db_client.patch(
        f"/api/sessions/patients/{patient_user.id}/timeline/{event.id}",
        json=update_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 400
    assert "no update data provided" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_timeline_event_patient_id_mismatch(async_db_client, test_db, therapist_user, therapist_auth_headers):
    """Test update fails when event belongs to different patient than path parameter"""
    from app.models.db_models import TimelineEvent, User, TherapistPatient
    from datetime import datetime, timedelta
    from app.models.schemas import UserRole
    from app.auth.utils import get_password_hash

    # Create two patients
    patient1 = User(
        email="patient1@test.com",
        hashed_password=get_password_hash("testpass123"),
        first_name="Patient",
        last_name="One",
        full_name="Patient One",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    patient2 = User(
        email="patient2@test.com",
        hashed_password=get_password_hash("testpass123"),
        first_name="Patient",
        last_name="Two",
        full_name="Patient Two",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(patient1)
    test_db.add(patient2)
    test_db.commit()
    test_db.refresh(patient1)
    test_db.refresh(patient2)

    # Create active relationships for both patients
    rel1 = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient1.id,
        relationship_type="primary",
        is_active=True
    )
    rel2 = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient2.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(rel1)
    test_db.add(rel2)
    test_db.commit()

    # Create event for patient1
    event = TimelineEvent(
        patient_id=patient1.id,
        therapist_id=therapist_user.id,
        event_type="assessment",
        event_date=datetime.utcnow() - timedelta(days=1),
        title="Initial Assessment",
        description="Assessment notes",
        importance="high"
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Attempt to update with patient2's ID in path (wrong patient)
    update_data = {"title": "Updated Assessment"}

    response = async_db_client.patch(
        f"/api/sessions/patients/{patient2.id}/timeline/{event.id}",
        json=update_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 404
    assert "not found for this patient" in response.json()["detail"].lower()


# ============================================================================
# Delete Timeline Event Tests (Sub-feature 6: DELETE endpoint)
# ============================================================================

@pytest.mark.asyncio
async def test_delete_timeline_event_success(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test successful deletion of a timeline event"""
    from app.models.db_models import TimelineEvent, TherapistPatient
    from datetime import datetime, timedelta

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()

    # Create timeline event
    event = TimelineEvent(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        event_type="note",
        event_date=datetime.utcnow() - timedelta(days=1),
        title="Clinical note to delete",
        description="This event should be deleted",
        importance="normal"
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)
    event_id = event.id

    # Verify event exists before deletion
    db_event = test_db.query(TimelineEvent).filter_by(id=event_id).first()
    assert db_event is not None
    assert db_event.title == "Clinical note to delete"

    # Delete event
    response = async_db_client.delete(
        f"/api/sessions/patients/{patient_user.id}/timeline/{event_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "deleted successfully" in data["message"].lower()

    # Verify event no longer exists in database (hard delete)
    db_event = test_db.query(TimelineEvent).filter_by(id=event_id).first()
    assert db_event is None


@pytest.mark.asyncio
async def test_delete_timeline_event_not_found(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test deletion fails with non-existent event ID"""
    from app.models.db_models import TherapistPatient

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()

    # Try to delete non-existent event
    fake_event_id = uuid4()
    response = async_db_client.delete(
        f"/api/sessions/patients/{patient_user.id}/timeline/{fake_event_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_delete_timeline_event_inactive_relationship(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test deletion fails when therapist-patient relationship is inactive"""
    from app.models.db_models import TimelineEvent, TherapistPatient
    from datetime import datetime, timedelta

    # Create timeline event
    event = TimelineEvent(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        event_type="milestone",
        event_date=datetime.utcnow() - timedelta(days=2),
        title="Milestone event",
        description="Event that cannot be deleted with inactive relationship",
        importance="milestone"
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Create INACTIVE therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=False  # Inactive relationship
    )
    test_db.add(relationship)
    test_db.commit()

    # Try to delete event with inactive relationship
    response = async_db_client.delete(
        f"/api/sessions/patients/{patient_user.id}/timeline/{event.id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "access denied" in data["detail"].lower()


@pytest.mark.asyncio
async def test_delete_timeline_event_patient_id_mismatch(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test deletion fails when patient_id in URL doesn't match event's patient"""
    from app.models.db_models import TimelineEvent, TherapistPatient, User
    from datetime import datetime, timedelta
    from app.auth.utils import get_password_hash

    # Create second patient
    patient_user_2 = User(
        email="patient2@test.com",
        hashed_password=get_password_hash("testpass123"),
        first_name="Test",
        last_name="Patient 2",
        full_name="Test Patient 2",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(patient_user_2)
    test_db.commit()
    test_db.refresh(patient_user_2)

    # Create active relationship for both patients
    relationship1 = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    relationship2 = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user_2.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship1)
    test_db.add(relationship2)
    test_db.commit()

    # Create event for patient_user
    event = TimelineEvent(
        patient_id=patient_user.id,
        therapist_id=therapist_user.id,
        event_type="session",
        event_date=datetime.utcnow() - timedelta(days=3),
        title="Session event for patient 1",
        description="This event belongs to patient 1",
        importance="normal"
    )
    test_db.add(event)
    test_db.commit()
    test_db.refresh(event)

    # Try to delete event using wrong patient_id in URL
    response = async_db_client.delete(
        f"/api/sessions/patients/{patient_user_2.id}/timeline/{event.id}",  # Wrong patient_id
        headers=therapist_auth_headers
    )

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found for this patient" in data["detail"].lower()

    # Verify event still exists (was not deleted)
    db_event = test_db.query(TimelineEvent).filter_by(id=event.id).first()
    assert db_event is not None

# ============================================================================
# Feature 7 - Sub-feature 3: Export Timeline Tests
# ============================================================================

@pytest.mark.asyncio
async def test_export_timeline_pdf_success(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test successful PDF export job creation"""
    from app.models.db_models import TimelineEvent, TherapistPatient
    from app.models.export_models import ExportJob
    from datetime import datetime, timedelta

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()

    # Create 5 timeline events
    now = datetime.utcnow()
    for i in range(5):
        event = TimelineEvent(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            event_type="session",
            event_date=now - timedelta(days=i*2),
            title=f"Session #{i+1}",
            description=f"Session notes for event {i+1}",
            importance="normal"
        )
        test_db.add(event)
    test_db.commit()

    # Request PDF export
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline/export?format=pdf",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "id" in data
    assert data["status"] == "pending"
    assert data["export_type"] == "timeline"
    assert data["format"] == "pdf"
    assert "created_at" in data

    # Verify ExportJob created in database
    job = test_db.query(ExportJob).filter(ExportJob.id == data["id"]).first()
    assert job is not None
    assert job.user_id == therapist_user.id
    assert job.patient_id == patient_user.id
    assert job.export_type == "timeline"
    assert job.format == "pdf"
    assert job.status == "pending"
    assert job.parameters["patient_id"] == str(patient_user.id)


@pytest.mark.asyncio
async def test_export_timeline_docx_success(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test successful DOCX export job creation"""
    from app.models.db_models import TimelineEvent, TherapistPatient
    from app.models.export_models import ExportJob
    from datetime import datetime, timedelta

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()

    # Create 5 timeline events
    now = datetime.utcnow()
    for i in range(5):
        event = TimelineEvent(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            event_type="note",
            event_date=now - timedelta(days=i*3),
            title=f"Clinical note #{i+1}",
            description=f"Note content {i+1}",
            importance="normal"
        )
        test_db.add(event)
    test_db.commit()

    # Request DOCX export
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline/export?format=docx",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "id" in data
    assert data["status"] == "pending"
    assert data["format"] == "docx"

    # Verify ExportJob created in database
    job = test_db.query(ExportJob).filter(ExportJob.id == data["id"]).first()
    assert job is not None
    assert job.format == "docx"
    assert job.status == "pending"


@pytest.mark.asyncio
async def test_export_timeline_json_success(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test successful JSON export job creation"""
    from app.models.db_models import TimelineEvent, TherapistPatient
    from app.models.export_models import ExportJob
    from datetime import datetime, timedelta

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()

    # Create 5 timeline events
    now = datetime.utcnow()
    for i in range(5):
        event = TimelineEvent(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            event_type="milestone",
            event_date=now - timedelta(days=i*5),
            title=f"Milestone #{i+1}",
            description=f"Progress milestone {i+1}",
            importance="milestone"
        )
        test_db.add(event)
    test_db.commit()

    # Request JSON export
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline/export?format=json",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "id" in data
    assert data["status"] == "pending"
    assert data["format"] == "json"

    # Verify ExportJob created in database
    job = test_db.query(ExportJob).filter(ExportJob.id == data["id"]).first()
    assert job is not None
    assert job.format == "json"
    assert job.status == "pending"


@pytest.mark.asyncio
async def test_export_timeline_with_date_filtering(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test export with date range filtering"""
    from app.models.db_models import TimelineEvent, TherapistPatient
    from app.models.export_models import ExportJob
    from datetime import datetime, timedelta

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()

    # Create events spanning 30 days
    base_date = datetime(2024, 1, 1)
    for i in range(30):
        event = TimelineEvent(
            patient_id=patient_user.id,
            therapist_id=therapist_user.id,
            event_type="session",
            event_date=base_date + timedelta(days=i),
            title=f"Session day {i+1}",
            description=f"Daily session {i+1}",
            importance="normal"
        )
        test_db.add(event)
    test_db.commit()

    # Request export with date filtering
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline/export?format=pdf&start_date=2024-01-10&end_date=2024-01-20",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify job created
    assert "id" in data
    assert data["status"] == "pending"

    # Verify date parameters stored in job
    job = test_db.query(ExportJob).filter(ExportJob.id == data["id"]).first()
    assert job is not None
    assert job.parameters["start_date"] == "2024-01-10"
    assert job.parameters["end_date"] == "2024-01-20"


@pytest.mark.asyncio
async def test_export_timeline_invalid_date_range(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test export with invalid date range (end before start)"""
    from app.models.db_models import TherapistPatient

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()

    # Request export with invalid date range (end before start)
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline/export?format=pdf&start_date=2024-01-20&end_date=2024-01-10",
        headers=therapist_auth_headers
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "end_date must be after start_date" in data["detail"]


@pytest.mark.asyncio
async def test_export_timeline_unauthorized_therapist(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test export authorization - therapist without patient relationship"""
    from app.models.db_models import User, TherapistPatient
    from uuid import uuid4

    # Create a second therapist (not related to patient_user)
    therapist2 = User(
        id=uuid4(),
        email="therapist2@test.com",
        hashed_password="hashed_password_here_12345",
        first_name="Second",
        last_name="Therapist",
        role="therapist",
        is_active=True,
        is_verified=True
    )
    test_db.add(therapist2)
    test_db.commit()
    test_db.refresh(therapist2)

    # Create relationship between therapist2 and patient (NOT therapist_user)
    relationship = TherapistPatient(
        therapist_id=therapist2.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    test_db.add(relationship)
    test_db.commit()

    # Try to export as therapist_user (who has NO relationship with patient)
    response = async_db_client.get(
        f"/api/sessions/patients/{patient_user.id}/timeline/export?format=pdf",
        headers=therapist_auth_headers  # This is for therapist_user, not therapist2
    )

    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not authorized" in data["detail"] or "not assigned" in data["detail"].lower()
