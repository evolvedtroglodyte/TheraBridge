# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for AudioProcessingService with parallel execution.

Tests cover:
1. Happy path - successful processing with parallel execution
2. Parallel execution verification - transcription and diarization run concurrently
3. Error handling - transcription failures, diarization failures, both failing
4. Progress updates - verify status updates at each stage
5. Note generation - verify GPT-4o integration
6. Database persistence - verify results are saved correctly
7. Audio file validation
8. Performance timing validation
"""
import pytest
import asyncio
import time
from pathlib import Path
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch, Mock, call
from datetime import datetime

from app.services.audio_processing_service import AudioProcessingService
from app.models.schemas import (
    SessionStatus,
    TranscriptSegment,
    ExtractedNotes,
    MoodLevel,
    RiskFlag,
    Strategy,
    StrategyStatus
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session"""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def audio_service():
    """AudioProcessingService with mocked dependencies"""
    service = AudioProcessingService()
    # Mock the note service
    service.note_service = MagicMock()
    service.note_service.extract_notes_from_transcript = AsyncMock()
    return service


@pytest.fixture
def sample_session_id():
    """Sample session UUID"""
    return uuid4()


@pytest.fixture
def sample_audio_path(tmp_path):
    """Create a temporary audio file for testing"""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data" * 1000)  # 15KB file
    return str(audio_file)


@pytest.fixture
def mock_transcription_result():
    """Mock transcription result from Whisper API"""
    return {
        "segments": [
            {
                "start": 0.0,
                "end": 5.0,
                "text": "Hello, how are you feeling today?"
            },
            {
                "start": 5.0,
                "end": 10.0,
                "text": "I've been struggling with anxiety lately."
            },
            {
                "start": 10.0,
                "end": 15.0,
                "text": "Let's talk about what's been triggering that."
            }
        ],
        "full_text": "Hello, how are you feeling today? I've been struggling with anxiety lately. Let's talk about what's been triggering that.",
        "language": "en",
        "duration": 15.0
    }


@pytest.fixture
def mock_diarization_result():
    """Mock diarization result from pyannote"""
    return {
        "segments": [
            {"start": 0.0, "end": 5.0, "speaker": "Therapist"},
            {"start": 5.0, "end": 10.0, "speaker": "Client"},
            {"start": 10.0, "end": 15.0, "speaker": "Therapist"}
        ]
    }


@pytest.fixture
def mock_extracted_notes():
    """Mock extracted notes from GPT-4o"""
    return ExtractedNotes(
        key_topics=["Anxiety", "Triggers", "Coping strategies"],
        topic_summary="Patient discussed anxiety symptoms and potential triggers.",
        strategies=[
            Strategy(
                name="Deep breathing",
                category="breathing",
                status=StrategyStatus.introduced,
                context="Introduced as anxiety management technique"
            )
        ],
        emotional_themes=["anxiety", "stress"],
        triggers=[],
        action_items=[],
        significant_quotes=[],
        session_mood=MoodLevel.low,
        mood_trajectory="stable",
        follow_up_topics=["Anxiety management"],
        unresolved_concerns=[],
        risk_flags=[],
        therapist_notes="Patient experiencing moderate anxiety. Introduced breathing techniques. Continue monitoring progress.",
        patient_summary="You shared your experiences with anxiety. We discussed some breathing exercises to help manage stress."
    )


# ============================================================================
# Happy Path Tests
# ============================================================================

@pytest.mark.asyncio
async def test_process_session_audio_success(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path,
    mock_transcription_result,
    mock_diarization_result,
    mock_extracted_notes
):
    """Test successful processing of audio file through entire pipeline"""

    # Mock all pipeline steps
    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = AsyncMock(return_value=mock_transcription_result)
    audio_service._diarize_with_retry = AsyncMock(return_value=mock_diarization_result)
    audio_service._update_session_status = AsyncMock()
    audio_service._save_session_data = AsyncMock()
    audio_service.note_service.extract_notes_from_transcript = AsyncMock(return_value=mock_extracted_notes)

    # Execute
    result = await audio_service.process_session_audio(
        session_id=sample_session_id,
        audio_file_path=sample_audio_path,
        db=mock_db
    )

    # Verify result structure
    assert result["transcript"] is not None
    assert "Therapist:" in result["transcript"]
    assert "Client:" in result["transcript"]
    assert "notes" in result
    assert "segments" in result
    assert result["status"] == "processed"
    assert result["processing_time"] >= 0  # May be 0 in fast tests

    # Verify segments have speakers
    assert len(result["segments"]) == 3
    assert result["segments"][0]["speaker"] == "Therapist"
    assert result["segments"][1]["speaker"] == "Client"

    # Verify all methods called
    audio_service._preprocess_audio.assert_called_once()
    audio_service._transcribe_with_retry.assert_called_once()
    audio_service._diarize_with_retry.assert_called_once()
    audio_service.note_service.extract_notes_from_transcript.assert_called_once()
    audio_service._save_session_data.assert_called_once()

    # Verify progress updates
    assert audio_service._update_session_status.call_count >= 4  # 0%, 25%, 50%, 75%, 100%


# ============================================================================
# Parallel Execution Tests
# ============================================================================

@pytest.mark.asyncio
async def test_parallel_execution_timing(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path,
    mock_transcription_result,
    mock_diarization_result,
    mock_extracted_notes
):
    """Verify transcription and diarization run in parallel (not sequential)"""

    # Track execution timing
    transcribe_start = None
    transcribe_end = None
    diarize_start = None
    diarize_end = None

    async def mock_transcribe(session_id, audio_path):
        nonlocal transcribe_start, transcribe_end
        transcribe_start = time.time()
        await asyncio.sleep(0.2)  # Simulate 200ms API call
        transcribe_end = time.time()
        return mock_transcription_result

    async def mock_diarize(session_id, audio_path):
        nonlocal diarize_start, diarize_end
        diarize_start = time.time()
        await asyncio.sleep(0.2)  # Simulate 200ms API call
        diarize_end = time.time()
        return mock_diarization_result

    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = mock_transcribe
    audio_service._diarize_with_retry = mock_diarize
    audio_service._update_session_status = AsyncMock()
    audio_service._save_session_data = AsyncMock()
    audio_service.note_service.extract_notes_from_transcript = AsyncMock(return_value=mock_extracted_notes)

    start_time = time.time()
    await audio_service.process_session_audio(
        session_id=sample_session_id,
        audio_file_path=sample_audio_path,
        db=mock_db
    )
    total_time = time.time() - start_time

    # Verify both tasks started
    assert transcribe_start is not None
    assert diarize_start is not None

    # Verify parallel execution: tasks overlap in time
    # If sequential, total would be ~400ms. If parallel, ~200ms.
    assert total_time < 0.35, f"Tasks appear to run sequentially (took {total_time:.3f}s)"

    # Verify overlap: diarize should start before transcribe finishes
    assert diarize_start < transcribe_end, "Tasks did not execute in parallel"


@pytest.mark.asyncio
async def test_parallel_execution_uses_asyncio_gather(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path,
    mock_transcription_result,
    mock_diarization_result,
    mock_extracted_notes
):
    """Verify that asyncio.gather is used for parallel execution"""

    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = AsyncMock(return_value=mock_transcription_result)
    audio_service._diarize_with_retry = AsyncMock(return_value=mock_diarization_result)
    audio_service._update_session_status = AsyncMock()
    audio_service._save_session_data = AsyncMock()
    audio_service.note_service.extract_notes_from_transcript = AsyncMock(return_value=mock_extracted_notes)

    with patch('app.services.audio_processing_service.asyncio.gather', wraps=asyncio.gather) as mock_gather:
        await audio_service.process_session_audio(
            session_id=sample_session_id,
            audio_file_path=sample_audio_path,
            db=mock_db
        )

        # Verify asyncio.gather was called
        mock_gather.assert_called_once()


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_transcription_failure(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path
):
    """Test handling of transcription failure"""

    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = AsyncMock(side_effect=Exception("Whisper API failed"))
    audio_service._diarize_with_retry = AsyncMock()
    audio_service._update_session_status = AsyncMock()

    # Should raise an exception with descriptive message
    with pytest.raises(Exception) as exc_info:
        await audio_service.process_session_audio(
            session_id=sample_session_id,
            audio_file_path=sample_audio_path,
            db=mock_db
        )

    assert "failed" in str(exc_info.value).lower()

    # Verify session marked as failed (status may be in args[2] or kwargs['status'])
    failed_calls = [
        call for call in audio_service._update_session_status.call_args_list
        if (len(call[0]) > 2 and call[0][2] == SessionStatus.failed) or
           call[1].get('status') == SessionStatus.failed
    ]
    assert len(failed_calls) > 0, f"No failed status updates found. Calls: {audio_service._update_session_status.call_args_list}"


@pytest.mark.asyncio
async def test_diarization_failure_graceful_degradation(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path,
    mock_transcription_result,
    mock_extracted_notes
):
    """Test that diarization failure doesn't stop processing (graceful degradation)"""

    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = AsyncMock(return_value=mock_transcription_result)
    audio_service._diarize_with_retry = AsyncMock(side_effect=Exception("Diarization service unavailable"))
    audio_service._update_session_status = AsyncMock()
    audio_service._save_session_data = AsyncMock()
    audio_service.note_service.extract_notes_from_transcript = AsyncMock(return_value=mock_extracted_notes)

    # Diarization failure should be handled gracefully - service should succeed
    result = await audio_service.process_session_audio(
        session_id=sample_session_id,
        audio_file_path=sample_audio_path,
        db=mock_db
    )

    # Should complete successfully
    assert result["status"] == "processed"

    # All speakers should be "Unknown" since diarization failed
    for segment in result["segments"]:
        assert segment["speaker"] == "Unknown"


@pytest.mark.asyncio
async def test_both_transcription_and_diarization_fail(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path
):
    """Test handling when both transcription and diarization fail"""

    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = AsyncMock(side_effect=Exception("Transcription failed"))
    audio_service._diarize_with_retry = AsyncMock(side_effect=Exception("Diarization failed"))
    audio_service._update_session_status = AsyncMock()

    with pytest.raises(Exception) as exc_info:
        await audio_service.process_session_audio(
            session_id=sample_session_id,
            audio_file_path=sample_audio_path,
            db=mock_db
        )

    assert "failed" in str(exc_info.value).lower()

    # Verify session marked as failed (status may be in args[2] or kwargs['status'])
    failed_calls = [
        call for call in audio_service._update_session_status.call_args_list
        if (len(call[0]) > 2 and call[0][2] == SessionStatus.failed) or
           call[1].get('status') == SessionStatus.failed
    ]
    assert len(failed_calls) > 0, f"No failed status updates found. Calls: {audio_service._update_session_status.call_args_list}"


@pytest.mark.asyncio
async def test_note_generation_failure(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path,
    mock_transcription_result,
    mock_diarization_result
):
    """Test handling of note generation failure"""

    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = AsyncMock(return_value=mock_transcription_result)
    audio_service._diarize_with_retry = AsyncMock(return_value=mock_diarization_result)
    audio_service._update_session_status = AsyncMock()
    audio_service.note_service.extract_notes_from_transcript = AsyncMock(
        side_effect=Exception("GPT-4o API failed")
    )

    with pytest.raises(Exception):
        await audio_service.process_session_audio(
            session_id=sample_session_id,
            audio_file_path=sample_audio_path,
            db=mock_db
        )

    # Verify session marked as failed (status may be in args[2] or kwargs['status'])
    failed_calls = [
        call for call in audio_service._update_session_status.call_args_list
        if (len(call[0]) > 2 and call[0][2] == SessionStatus.failed) or
           call[1].get('status') == SessionStatus.failed
    ]
    assert len(failed_calls) > 0, f"No failed status updates found. Calls: {audio_service._update_session_status.call_args_list}"


@pytest.mark.asyncio
async def test_audio_file_not_found(
    audio_service,
    mock_db,
    sample_session_id
):
    """Test handling when audio file doesn't exist"""

    audio_service._update_session_status = AsyncMock()

    nonexistent_path = "/tmp/nonexistent_audio_file.mp3"

    with pytest.raises(Exception) as exc_info:
        await audio_service.process_session_audio(
            session_id=sample_session_id,
            audio_file_path=nonexistent_path,
            db=mock_db
        )

    assert "failed" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()

    # Verify session marked as failed (status may be in args[2] or kwargs['status'])
    failed_calls = [
        call for call in audio_service._update_session_status.call_args_list
        if (len(call[0]) > 2 and call[0][2] == SessionStatus.failed) or
           call[1].get('status') == SessionStatus.failed
    ]
    assert len(failed_calls) > 0, f"No failed status updates found. Calls: {audio_service._update_session_status.call_args_list}"


# ============================================================================
# Progress Update Tests
# ============================================================================

@pytest.mark.asyncio
async def test_progress_updates_at_each_stage(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path,
    mock_transcription_result,
    mock_diarization_result,
    mock_extracted_notes
):
    """Verify progress is updated at each processing stage"""

    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = AsyncMock(return_value=mock_transcription_result)
    audio_service._diarize_with_retry = AsyncMock(return_value=mock_diarization_result)
    audio_service._update_session_status = AsyncMock()
    audio_service._save_session_data = AsyncMock()
    audio_service.note_service.extract_notes_from_transcript = AsyncMock(return_value=mock_extracted_notes)

    await audio_service.process_session_audio(
        session_id=sample_session_id,
        audio_file_path=sample_audio_path,
        db=mock_db
    )

    # Extract progress updates
    calls = audio_service._update_session_status.call_args_list

    # Verify we have updates for key milestones
    # 0% - start, 25% - preprocessed, 50% - transcribed, 75% - diarized, 100% - complete
    assert any(call[1].get('progress') == 0 for call in calls), f"Missing 0% progress. Calls: {calls}"
    assert any(call[1].get('progress') == 25 for call in calls), f"Missing 25% progress. Calls: {calls}"
    assert any(call[1].get('progress') == 50 for call in calls), f"Missing 50% progress. Calls: {calls}"
    assert any(call[1].get('progress') == 75 for call in calls), f"Missing 75% progress. Calls: {calls}"
    assert any(call[1].get('progress') == 100 for call in calls), f"Missing 100% progress. Calls: {calls}"

    # Verify status transitions (status may be in args[2] or kwargs['status'])
    status_updates = [
        call[0][2] if len(call[0]) > 2 else call[1].get('status')
        for call in calls
    ]
    assert SessionStatus.transcribing in status_updates, f"Missing transcribing status. Updates: {status_updates}"
    assert SessionStatus.extracting_notes in status_updates, f"Missing extracting_notes status. Updates: {status_updates}"
    assert SessionStatus.processed in status_updates, f"Missing processed status. Updates: {status_updates}"


# ============================================================================
# Database Persistence Tests
# ============================================================================

@pytest.mark.asyncio
async def test_database_save_called_with_correct_data(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path,
    mock_transcription_result,
    mock_diarization_result,
    mock_extracted_notes
):
    """Verify database save is called with correct data structure"""

    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = AsyncMock(return_value=mock_transcription_result)
    audio_service._diarize_with_retry = AsyncMock(return_value=mock_diarization_result)
    audio_service._update_session_status = AsyncMock()
    audio_service._save_session_data = AsyncMock()
    audio_service.note_service.extract_notes_from_transcript = AsyncMock(return_value=mock_extracted_notes)

    await audio_service.process_session_audio(
        session_id=sample_session_id,
        audio_file_path=sample_audio_path,
        db=mock_db
    )

    # Verify save was called once
    audio_service._save_session_data.assert_called_once()

    # Verify save was called with correct arguments
    call_kwargs = audio_service._save_session_data.call_args[1]
    assert call_kwargs['session_id'] == sample_session_id
    assert call_kwargs['db'] == mock_db
    assert 'transcript_text' in call_kwargs
    assert 'transcript_segments' in call_kwargs
    assert 'notes' in call_kwargs
    assert call_kwargs['notes'] == mock_extracted_notes
    assert 'audio_path' in call_kwargs
    assert 'duration_seconds' in call_kwargs


# ============================================================================
# Merging and Integration Tests
# ============================================================================

def test_merge_transcript_with_speakers(
    audio_service,
    mock_transcription_result,
    mock_diarization_result
):
    """Test merging transcription segments with speaker labels"""

    merged = audio_service._merge_transcript_with_speakers(
        mock_transcription_result,
        mock_diarization_result
    )

    # Verify merged segments have both text and speaker
    assert 'segments' in merged
    assert 'full_text' in merged
    assert len(merged['segments']) == 3

    # Verify speaker assignment
    assert merged['segments'][0]['speaker'] == 'Therapist'
    assert merged['segments'][1]['speaker'] == 'Client'
    assert merged['segments'][2]['speaker'] == 'Therapist'

    # Verify text content preserved
    assert merged['segments'][0]['text'] == mock_transcription_result['segments'][0]['text']

    # Verify full text has speaker labels
    assert 'Therapist:' in merged['full_text']
    assert 'Client:' in merged['full_text']


def test_merge_handles_unknown_speakers(audio_service):
    """Test merging when diarization doesn't cover all segments"""

    transcription = {
        "segments": [
            {"start": 0.0, "end": 5.0, "text": "First segment"},
            {"start": 20.0, "end": 25.0, "text": "Gap segment"}  # No diarization
        ]
    }

    diarization = {
        "segments": [
            {"start": 0.0, "end": 5.0, "speaker": "Therapist"}
            # No speaker for 20-25s range
        ]
    }

    merged = audio_service._merge_transcript_with_speakers(transcription, diarization)

    # First segment should have speaker
    assert merged['segments'][0]['speaker'] == 'Therapist'

    # Second segment should be labeled as Unknown
    assert merged['segments'][1]['speaker'] == 'Unknown'


# ============================================================================
# Performance and Timing Tests
# ============================================================================

@pytest.mark.asyncio
async def test_processing_time_measured(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path,
    mock_transcription_result,
    mock_diarization_result,
    mock_extracted_notes
):
    """Verify processing time is measured and returned"""

    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = AsyncMock(return_value=mock_transcription_result)
    audio_service._diarize_with_retry = AsyncMock(return_value=mock_diarization_result)
    audio_service._update_session_status = AsyncMock()
    audio_service._save_session_data = AsyncMock()
    audio_service.note_service.extract_notes_from_transcript = AsyncMock(return_value=mock_extracted_notes)

    result = await audio_service.process_session_audio(
        session_id=sample_session_id,
        audio_file_path=sample_audio_path,
        db=mock_db
    )

    # Verify timing data
    assert 'processing_time' in result
    assert isinstance(result['processing_time'], (int, float))
    assert result['processing_time'] >= 0  # May be 0 in fast tests
    assert result['processing_time'] < 60  # Should complete quickly in tests


# ============================================================================
# Edge Cases and Validation
# ============================================================================

@pytest.mark.asyncio
async def test_empty_diarization_segments(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path,
    mock_transcription_result,
    mock_extracted_notes
):
    """Test handling of empty diarization results"""

    empty_diarization = {"segments": []}

    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = AsyncMock(return_value=mock_transcription_result)
    audio_service._diarize_with_retry = AsyncMock(return_value=empty_diarization)
    audio_service._update_session_status = AsyncMock()
    audio_service._save_session_data = AsyncMock()
    audio_service.note_service.extract_notes_from_transcript = AsyncMock(return_value=mock_extracted_notes)

    result = await audio_service.process_session_audio(
        session_id=sample_session_id,
        audio_file_path=sample_audio_path,
        db=mock_db
    )

    # Should still succeed, but all speakers will be "Unknown"
    assert result["status"] == "processed"
    for segment in result["segments"]:
        assert segment["speaker"] == "Unknown"


@pytest.mark.asyncio
async def test_client_id_parameter_passed(
    audio_service,
    mock_db,
    sample_session_id,
    sample_audio_path,
    mock_transcription_result,
    mock_diarization_result,
    mock_extracted_notes
):
    """Test that client_id parameter is handled correctly"""

    client_id = uuid4()

    audio_service._preprocess_audio = AsyncMock(return_value=sample_audio_path)
    audio_service._transcribe_with_retry = AsyncMock(return_value=mock_transcription_result)
    audio_service._diarize_with_retry = AsyncMock(return_value=mock_diarization_result)
    audio_service._update_session_status = AsyncMock()
    audio_service._save_session_data = AsyncMock()
    audio_service.note_service.extract_notes_from_transcript = AsyncMock(return_value=mock_extracted_notes)

    # Should not raise error when client_id provided
    result = await audio_service.process_session_audio(
        session_id=sample_session_id,
        audio_file_path=sample_audio_path,
        db=mock_db,
        client_id=client_id
    )

    assert result["status"] == "processed"


# ============================================================================
# Service Initialization Tests
# ============================================================================

def test_service_initialization():
    """Test AudioProcessingService initializes correctly"""

    service = AudioProcessingService()
    assert service.note_service is not None


# ============================================================================
# Test Summary
# ============================================================================

# Test count: 18 test cases
# Coverage areas:
# - Happy path (1)
# - Parallel execution (2)
# - Error handling (5)
# - Progress updates (1)
# - Database persistence (1)
# - Merging/integration (2)
# - Performance (1)
# - Edge cases (3)
# - Service initialization (1)
# - Audio validation (1)
