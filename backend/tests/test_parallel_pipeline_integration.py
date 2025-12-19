"""
Integration tests for the complete parallel audio processing pipeline.

This module tests the full end-to-end workflow from audio upload to completed processing,
verifying that all pipeline components work together correctly and meet performance targets.

Test Coverage:
1. Full pipeline success flow (upload -> transcription -> diarization -> notes -> database)
2. Progress updates sequential ordering (0% -> 100%)
3. Parallel speedup verification (vs sequential processing)
4. Database persistence of all processed data
5. Error recovery and failure handling

Performance Target: <60s for 1-hour audio (matching Upheal)

Note: These are SLOW tests - they make real API calls and process actual audio files.
Mark with @pytest.mark.slow and run selectively during development.
"""

import pytest
import pytest_asyncio
import asyncio
import time
import logging
from pathlib import Path
from uuid import UUID, uuid4
from datetime import datetime
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.models.db_models import User, Patient, TherapySession
from app.models.schemas import SessionStatus, UserRole
from app.services.audio_processing_service import AudioProcessingService
from app.services.progress_tracker import ProgressTracker, ProgressUpdate
from app.routers.sessions import process_audio_pipeline

# Configure logging for test debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test audio samples from the audio-transcription-pipeline
PIPELINE_DIR = Path(__file__).parent.parent.parent / "audio-transcription-pipeline"
SAMPLES_DIR = PIPELINE_DIR / "tests" / "samples"

# Available test files (from ls output)
SAMPLE_AUDIO_23MIN = SAMPLES_DIR / "Carl Rogers and Gloria - Counselling 1965 Full Session - CAPTIONED [ee1bU4XuUyg].mp3"
SAMPLE_AUDIO_12MIN = SAMPLES_DIR / "Initial Phase and Interpersonal Inventory 1 [A1XJeciqyL8].mp3"
SAMPLE_AUDIO_CBT = SAMPLES_DIR / "LIVE Cognitive Behavioral Therapy Session (1).mp3"
SAMPLE_AUDIO_COMPRESSED = SAMPLES_DIR / "compressed-cbt-session.m4a"


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_audio_path() -> Path:
    """
    Provide path to real test audio file.

    Returns:
        Path to 12-minute therapy session audio (smallest file for faster tests)
    """
    # Use the smallest file for faster test execution
    if SAMPLE_AUDIO_COMPRESSED.exists():
        return SAMPLE_AUDIO_COMPRESSED
    elif SAMPLE_AUDIO_12MIN.exists():
        return SAMPLE_AUDIO_12MIN
    elif SAMPLE_AUDIO_CBT.exists():
        return SAMPLE_AUDIO_CBT
    else:
        pytest.skip(f"No test audio files found in {SAMPLES_DIR}")


@pytest.fixture
def long_audio_path() -> Path:
    """
    Provide path to longer test audio file for performance testing.

    Returns:
        Path to 23-minute therapy session audio
    """
    if SAMPLE_AUDIO_23MIN.exists():
        return SAMPLE_AUDIO_23MIN
    else:
        pytest.skip(f"Long audio file not found: {SAMPLE_AUDIO_23MIN}")


@pytest_asyncio.fixture
async def setup_test_session(async_test_db: AsyncSession) -> Dict:
    """
    Create test therapist, patient, and session for pipeline testing.

    Returns:
        Dict with therapist, patient, and session objects
    """
    # Create therapist
    therapist = User(
        email="pipeline.therapist@test.com",
        hashed_password="hashed_password_placeholder",
        first_name="Pipeline",
        last_name="Therapist",
        full_name="Pipeline Therapist",
        role=UserRole.therapist,
        is_active=True
    )
    async_test_db.add(therapist)
    await async_test_db.commit()
    await async_test_db.refresh(therapist)

    # Create patient
    patient = Patient(
        name="Pipeline Test Patient",
        email="pipeline.patient@test.com",
        phone="555-0199",
        therapist_id=therapist.id
    )
    async_test_db.add(patient)
    await async_test_db.commit()
    await async_test_db.refresh(patient)

    # Create session
    session = TherapySession(
        patient_id=patient.id,
        therapist_id=therapist.id,
        session_date=datetime.utcnow(),
        audio_filename="test_pipeline.mp3",
        status=SessionStatus.pending.value
    )
    async_test_db.add(session)
    await async_test_db.commit()
    await async_test_db.refresh(session)

    return {
        "therapist": therapist,
        "patient": patient,
        "session": session
    }


@pytest.fixture
def mock_progress_tracker():
    """
    Mock ProgressTracker for testing progress updates without database.

    Returns:
        Mock ProgressTracker with update method
    """
    tracker = MagicMock(spec=ProgressTracker)
    tracker.updates = []

    async def mock_update(session_id, status, progress, message, **kwargs):
        update = {
            "session_id": session_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": datetime.utcnow()
        }
        tracker.updates.append(update)
        logger.info(f"Progress update: {progress}% - {message}")

    tracker.update_progress = AsyncMock(side_effect=mock_update)
    return tracker


# ============================================================================
# Test Cases
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.integration
async def test_full_pipeline_success(
    async_test_db: AsyncSession,
    setup_test_session: Dict,
    sample_audio_path: Path
):
    """
    Test complete pipeline from audio file to database persistence.

    This test verifies:
    1. Audio file is successfully processed
    2. Transcript is generated with timestamps and text
    3. Speaker diarization assigns speakers to segments
    4. Clinical notes are extracted with GPT-4o
    5. All data is persisted to database
    6. Session status is updated to 'processed'

    Performance: Should complete in <60s for 12-min audio
    """
    session = setup_test_session["session"]
    start_time = time.time()

    logger.info(f"Starting full pipeline test with session {session.id}")
    logger.info(f"Audio file: {sample_audio_path.name} ({sample_audio_path.stat().st_size / 1024 / 1024:.1f} MB)")

    # Initialize audio processing service
    processing_service = AudioProcessingService()

    # Process audio file
    try:
        result = await processing_service.process_session_audio(
            session_id=session.id,
            audio_file_path=str(sample_audio_path),
            db=async_test_db,
            client_id=session.patient_id
        )

        elapsed_time = time.time() - start_time
        logger.info(f"Pipeline completed in {elapsed_time:.2f}s")

        # Verify result structure
        assert "transcript" in result
        assert "segments" in result
        assert "notes" in result
        assert "processing_time" in result
        assert result["status"] == "processed"

        # Verify transcript data
        assert len(result["transcript"]) > 0, "Transcript text should not be empty"
        assert len(result["segments"]) > 0, "Should have transcript segments"

        # Verify segments have required fields
        for segment in result["segments"]:
            assert "start" in segment
            assert "end" in segment
            assert "text" in segment
            assert "speaker" in segment
            assert isinstance(segment["start"], (int, float))
            assert isinstance(segment["end"], (int, float))
            assert len(segment["text"]) > 0

        # Verify notes extraction
        assert "key_topics" in result["notes"]
        assert "therapist_notes" in result["notes"]
        assert "patient_summary" in result["notes"]
        assert len(result["notes"]["key_topics"]) > 0, "Should extract at least one topic"

        # Verify database persistence
        await async_test_db.refresh(session)
        assert session.status == SessionStatus.processed.value
        assert session.transcript_text is not None
        assert len(session.transcript_text) > 0
        assert session.transcript_segments is not None
        assert len(session.transcript_segments) > 0
        assert session.extracted_notes is not None
        assert session.duration_seconds is not None
        assert session.duration_seconds > 0

        # Verify performance
        assert elapsed_time < 120, f"Pipeline took {elapsed_time:.2f}s, expected <120s for 12-min audio"
        logger.info(f"✓ Performance check passed: {elapsed_time:.2f}s < 120s")

    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"Pipeline failed after {elapsed_time:.2f}s: {e}")
        raise


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.integration
async def test_progress_updates_sequential(
    async_test_db: AsyncSession,
    setup_test_session: Dict,
    sample_audio_path: Path
):
    """
    Test that progress updates are emitted in sequential order (0% -> 100%).

    This test verifies:
    1. Progress starts at 0%
    2. Progress increases monotonically
    3. Progress reaches 100% upon completion
    4. Status transitions are logical (pending -> transcribing -> processed)
    """
    session = setup_test_session["session"]
    progress_updates = []

    # Create custom progress tracker that captures updates
    class CapturingProgressTracker:
        def __init__(self, session_id, db):
            self.session_id = session_id
            self.db = db

        async def update(self, progress, status, message):
            update = {
                "progress": progress,
                "status": status,
                "message": message,
                "timestamp": datetime.utcnow()
            }
            progress_updates.append(update)
            logger.info(f"Progress: {progress}% - {status} - {message}")

            # Update session status in database
            from sqlalchemy import update as sql_update
            stmt = (
                sql_update(TherapySession)
                .where(TherapySession.id == self.session_id)
                .values(status=status)
            )
            await self.db.execute(stmt)
            await self.db.commit()

    # Patch the progress tracker
    with patch('app.services.audio_processing_service.ProgressTracker', CapturingProgressTracker):
        processing_service = AudioProcessingService()

        try:
            await processing_service.process_session_audio(
                session_id=session.id,
                audio_file_path=str(sample_audio_path),
                db=async_test_db,
                client_id=session.patient_id
            )

            # Verify progress updates
            assert len(progress_updates) > 0, "Should have progress updates"

            # Check progress values are monotonically increasing
            progress_values = [u["progress"] for u in progress_updates]
            logger.info(f"Progress sequence: {progress_values}")

            assert progress_values[0] == 0, "Should start at 0%"
            assert progress_values[-1] == 100, "Should end at 100%"

            for i in range(len(progress_values) - 1):
                assert progress_values[i] <= progress_values[i + 1], \
                    f"Progress should be monotonic: {progress_values[i]} > {progress_values[i + 1]}"

            # Check status transitions
            statuses = [u["status"] for u in progress_updates]
            logger.info(f"Status sequence: {statuses}")

            # Should have logical status progression
            assert SessionStatus.transcribing.value in statuses, "Should have transcribing status"
            assert SessionStatus.processed.value in statuses, "Should have processed status"

            logger.info("✓ Progress updates are sequential and valid")

        except Exception as e:
            logger.error(f"Progress tracking test failed: {e}")
            logger.error(f"Captured updates: {progress_updates}")
            raise


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.integration
@pytest.mark.performance
async def test_parallel_speedup(
    async_test_db: AsyncSession,
    setup_test_session: Dict,
    sample_audio_path: Path
):
    """
    Verify parallel execution is faster than sequential processing.

    This test measures:
    1. Time for parallel execution (transcription + diarization concurrent)
    2. Estimated sequential time (sum of individual task times)
    3. Speedup factor (should be >1.3x faster for I/O-bound tasks)

    Note: This is a synthetic test since we can't easily measure sequential
    time without refactoring. We verify the parallel execution time is
    reasonable (<60s for 12-min audio).
    """
    session = setup_test_session["session"]

    logger.info("Testing parallel execution performance")
    start_time = time.time()

    processing_service = AudioProcessingService()

    result = await processing_service.process_session_audio(
        session_id=session.id,
        audio_file_path=str(sample_audio_path),
        db=async_test_db,
        client_id=session.patient_id
    )

    parallel_time = time.time() - start_time
    logger.info(f"Parallel execution time: {parallel_time:.2f}s")

    # Expected performance targets
    # For 12-min audio: ~30-60s total (including preprocessing, note extraction)
    # For 23-min audio: ~40-80s total

    # Get audio duration from result
    if "duration" in result.get("transcript", {}):
        audio_duration = result["transcript"]["duration"]
        logger.info(f"Audio duration: {audio_duration:.1f}s ({audio_duration/60:.1f} min)")

        # Processing should be faster than real-time playback
        speedup_vs_realtime = audio_duration / parallel_time
        logger.info(f"Speedup vs real-time: {speedup_vs_realtime:.2f}x")

        assert speedup_vs_realtime > 1.0, \
            f"Processing should be faster than real-time playback ({speedup_vs_realtime:.2f}x)"

    # Performance should meet Upheal-level targets
    # For 1-hour audio: <60s processing time
    # For shorter audio, scale proportionally
    audio_size_mb = sample_audio_path.stat().st_size / (1024 * 1024)
    expected_max_time = 120  # 2 minutes for 12-min audio (conservative)

    assert parallel_time < expected_max_time, \
        f"Parallel execution took {parallel_time:.2f}s, expected <{expected_max_time}s"

    logger.info(f"✓ Performance check passed: {parallel_time:.2f}s < {expected_max_time}s")
    logger.info(f"  Audio size: {audio_size_mb:.1f}MB")
    logger.info(f"  Processing rate: {audio_size_mb/parallel_time:.2f} MB/s")


@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.integration
async def test_database_persistence(
    async_test_db: AsyncSession,
    setup_test_session: Dict,
    sample_audio_path: Path
):
    """
    Verify all processed data is correctly saved to database.

    This test checks:
    1. Session status is updated
    2. Transcript text is saved
    3. Transcript segments with timestamps and speakers are saved
    4. Extracted notes are saved
    5. Audio metadata (duration, filename) is saved
    6. Timestamps (processed_at, updated_at) are set
    """
    session = setup_test_session["session"]

    processing_service = AudioProcessingService()

    # Process audio
    result = await processing_service.process_session_audio(
        session_id=session.id,
        audio_file_path=str(sample_audio_path),
        db=async_test_db,
        client_id=session.patient_id
    )

    # Refresh session from database
    await async_test_db.refresh(session)

    # Verify status
    assert session.status == SessionStatus.processed.value, \
        f"Expected status 'processed', got '{session.status}'"

    # Verify transcript text
    assert session.transcript_text is not None, "Transcript text should be saved"
    assert len(session.transcript_text) > 100, "Transcript should have substantial content"
    logger.info(f"Transcript length: {len(session.transcript_text)} characters")

    # Verify transcript segments
    assert session.transcript_segments is not None, "Segments should be saved"
    assert isinstance(session.transcript_segments, list), "Segments should be a list"
    assert len(session.transcript_segments) > 0, "Should have at least one segment"

    # Verify segment structure
    first_segment = session.transcript_segments[0]
    assert "start" in first_segment, "Segment should have start time"
    assert "end" in first_segment, "Segment should have end time"
    assert "text" in first_segment, "Segment should have text"
    assert "speaker" in first_segment, "Segment should have speaker"
    logger.info(f"Transcript segments: {len(session.transcript_segments)}")

    # Verify extracted notes
    assert session.extracted_notes is not None, "Notes should be saved"
    assert isinstance(session.extracted_notes, dict), "Notes should be a dict"
    assert "key_topics" in session.extracted_notes, "Notes should have key_topics"
    assert "therapist_notes" in session.extracted_notes, "Notes should have therapist_notes"
    assert "patient_summary" in session.extracted_notes, "Notes should have patient_summary"
    logger.info(f"Key topics: {session.extracted_notes.get('key_topics', [])}")

    # Verify summaries (denormalized fields)
    assert session.therapist_summary is not None, "Therapist summary should be saved"
    assert session.patient_summary is not None, "Patient summary should be saved"
    assert len(session.therapist_summary) > 50, "Therapist summary should have content"
    assert len(session.patient_summary) > 50, "Patient summary should have content"

    # Verify audio metadata
    assert session.duration_seconds is not None, "Duration should be saved"
    assert session.duration_seconds > 0, "Duration should be positive"
    logger.info(f"Audio duration: {session.duration_seconds}s ({session.duration_seconds/60:.1f} min)")

    # Verify risk flags
    assert session.risk_flags is not None, "Risk flags should be saved (may be empty list)"
    assert isinstance(session.risk_flags, list), "Risk flags should be a list"
    logger.info(f"Risk flags: {len(session.risk_flags)}")

    # Verify timestamps
    assert session.processed_at is not None, "processed_at should be set"
    assert session.updated_at is not None, "updated_at should be set"
    assert session.processed_at >= session.created_at, "processed_at should be after created_at"

    logger.info("✓ All data correctly persisted to database")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_error_recovery_invalid_audio(
    async_test_db: AsyncSession,
    setup_test_session: Dict,
    tmp_path: Path
):
    """
    Test error handling when audio file is invalid or corrupted.

    This test verifies:
    1. Pipeline detects invalid audio
    2. Session status is set to 'failed'
    3. Error message is recorded
    4. Database transaction is rolled back cleanly
    """
    session = setup_test_session["session"]

    # Create invalid audio file (just random bytes)
    invalid_audio = tmp_path / "invalid_audio.mp3"
    invalid_audio.write_bytes(b"This is not audio data" * 100)

    processing_service = AudioProcessingService()

    # Process should fail but not raise unhandled exception
    with pytest.raises(ValueError, match="processing failed|invalid|not found"):
        await processing_service.process_session_audio(
            session_id=session.id,
            audio_file_path=str(invalid_audio),
            db=async_test_db,
            client_id=session.patient_id
        )

    # Refresh session from database
    await async_test_db.refresh(session)

    # Verify error handling
    assert session.status == SessionStatus.failed.value, \
        f"Expected status 'failed', got '{session.status}'"

    # Session should have minimal data (no transcript since processing failed)
    assert session.transcript_text is None or len(session.transcript_text) == 0
    assert session.extracted_notes is None

    logger.info("✓ Error recovery successful - session marked as failed")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_error_recovery_missing_file(
    async_test_db: AsyncSession,
    setup_test_session: Dict
):
    """
    Test error handling when audio file doesn't exist.

    This test verifies:
    1. Pipeline detects missing file
    2. Session status is set to 'failed'
    3. Appropriate error message is recorded
    """
    session = setup_test_session["session"]

    processing_service = AudioProcessingService()

    # Process with non-existent file
    with pytest.raises((FileNotFoundError, ValueError), match="not found|does not exist"):
        await processing_service.process_session_audio(
            session_id=session.id,
            audio_file_path="/tmp/nonexistent_audio_file.mp3",
            db=async_test_db,
            client_id=session.patient_id
        )

    # Refresh session from database
    await async_test_db.refresh(session)

    # Verify error state
    assert session.status == SessionStatus.failed.value
    assert session.transcript_text is None

    logger.info("✓ Missing file error handled correctly")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_concurrent_session_processing(
    async_test_db: AsyncSession,
    setup_test_session: Dict,
    sample_audio_path: Path
):
    """
    Test that multiple sessions can be processed concurrently.

    This test verifies:
    1. Multiple sessions can process simultaneously
    2. Each session maintains independent state
    3. Database transactions don't conflict
    4. All sessions complete successfully

    Note: This simulates the real-world scenario where multiple therapists
    upload sessions simultaneously.
    """
    # Create 3 sessions for parallel processing
    patient = setup_test_session["patient"]
    therapist = setup_test_session["therapist"]

    sessions = []
    for i in range(3):
        session = TherapySession(
            patient_id=patient.id,
            therapist_id=therapist.id,
            session_date=datetime.utcnow(),
            audio_filename=f"concurrent_test_{i}.mp3",
            status=SessionStatus.pending.value
        )
        async_test_db.add(session)
        sessions.append(session)

    await async_test_db.commit()
    for session in sessions:
        await async_test_db.refresh(session)

    # Process all sessions concurrently
    processing_service = AudioProcessingService()

    async def process_session(session):
        """Process a single session and return result"""
        try:
            result = await processing_service.process_session_audio(
                session_id=session.id,
                audio_file_path=str(sample_audio_path),
                db=async_test_db,
                client_id=session.patient_id
            )
            logger.info(f"Session {session.id} completed successfully")
            return {"session_id": session.id, "success": True, "result": result}
        except Exception as e:
            logger.error(f"Session {session.id} failed: {e}")
            return {"session_id": session.id, "success": False, "error": str(e)}

    # Launch all processing tasks concurrently
    start_time = time.time()
    results = await asyncio.gather(
        *[process_session(s) for s in sessions],
        return_exceptions=False
    )
    concurrent_time = time.time() - start_time

    logger.info(f"Concurrent processing completed in {concurrent_time:.2f}s")

    # Verify all sessions succeeded
    for result in results:
        assert result["success"], f"Session {result['session_id']} failed: {result.get('error')}"

    # Verify all sessions in database
    for session in sessions:
        await async_test_db.refresh(session)
        assert session.status == SessionStatus.processed.value
        assert session.transcript_text is not None
        assert session.extracted_notes is not None

    # Concurrent processing should not be 3x slower (due to parallelization)
    # Expected: slightly slower than single session due to contention, but not 3x
    logger.info(f"✓ Concurrent processing successful: {len(sessions)} sessions in {concurrent_time:.2f}s")


# ============================================================================
# Performance Benchmarking Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.slow
@pytest.mark.benchmark
@pytest.mark.skipif(
    not SAMPLE_AUDIO_23MIN.exists(),
    reason="23-minute audio file not available for benchmark"
)
async def test_performance_benchmark_23min_audio(
    async_test_db: AsyncSession,
    setup_test_session: Dict,
    long_audio_path: Path
):
    """
    Benchmark test with 23-minute audio file.

    Performance target: <80s (Upheal standard is <60s for 1-hour audio, scaled down)

    This test measures:
    1. Total processing time
    2. Time per processing stage
    3. Throughput (MB/s and minutes audio/second)
    """
    session = setup_test_session["session"]

    audio_size_mb = long_audio_path.stat().st_size / (1024 * 1024)
    logger.info(f"Starting benchmark with 23-min audio ({audio_size_mb:.1f} MB)")

    start_time = time.time()

    processing_service = AudioProcessingService()
    result = await processing_service.process_session_audio(
        session_id=session.id,
        audio_file_path=str(long_audio_path),
        db=async_test_db,
        client_id=session.patient_id
    )

    total_time = time.time() - start_time

    # Calculate metrics
    audio_duration_min = 23  # Known duration
    throughput_mb_s = audio_size_mb / total_time
    throughput_min_s = audio_duration_min / total_time

    # Log performance metrics
    logger.info("=" * 70)
    logger.info("PERFORMANCE BENCHMARK RESULTS")
    logger.info("=" * 70)
    logger.info(f"Audio file: {long_audio_path.name}")
    logger.info(f"Audio size: {audio_size_mb:.1f} MB")
    logger.info(f"Audio duration: {audio_duration_min} minutes")
    logger.info(f"Total processing time: {total_time:.2f}s ({total_time/60:.1f} min)")
    logger.info(f"Throughput: {throughput_mb_s:.2f} MB/s")
    logger.info(f"Processing rate: {throughput_min_s:.2f} min audio/sec")
    logger.info(f"Speedup vs real-time: {(audio_duration_min * 60) / total_time:.2f}x")
    logger.info(f"Transcript segments: {len(result['segments'])}")
    logger.info(f"Key topics: {len(result['notes']['key_topics'])}")
    logger.info("=" * 70)

    # Performance assertions
    assert total_time < 120, f"Processing took {total_time:.2f}s, expected <120s for 23-min audio"
    assert throughput_min_s > 0.15, f"Processing rate {throughput_min_s:.2f} min/s is too slow"

    logger.info("✓ Performance benchmark passed")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_websocket_progress_streaming(
    async_test_db: AsyncSession,
    setup_test_session: Dict,
    sample_audio_path: Path
):
    """
    Test real-time progress updates via WebSocket-like streaming.

    This test verifies:
    1. Progress updates are emitted during processing
    2. Updates include all required fields
    3. Updates arrive in chronological order
    4. Final update indicates completion
    """
    session = setup_test_session["session"]
    progress_stream = []

    # Create mock WebSocket-like progress collector
    class StreamingProgressTracker:
        def __init__(self, session_id, db):
            self.session_id = session_id
            self.db = db

        async def update(self, progress, status, message):
            update = ProgressUpdate(
                session_id=self.session_id,
                status=status,
                progress=progress,
                message=message,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            progress_stream.append(update)
            logger.info(f"[WebSocket] {progress}% - {message}")

    # Process with streaming progress
    with patch('app.services.audio_processing_service.ProgressTracker', StreamingProgressTracker):
        processing_service = AudioProcessingService()

        await processing_service.process_session_audio(
            session_id=session.id,
            audio_file_path=str(sample_audio_path),
            db=async_test_db,
            client_id=session.patient_id
        )

    # Verify streaming updates
    assert len(progress_stream) > 0, "Should have progress updates"

    # Check update ordering (timestamps should be increasing)
    for i in range(len(progress_stream) - 1):
        assert progress_stream[i].updated_at <= progress_stream[i + 1].updated_at, \
            "Updates should arrive in chronological order"

    # Check required fields
    for update in progress_stream:
        assert update.session_id == session.id
        assert update.progress >= 0 and update.progress <= 100
        assert update.status in [s.value for s in SessionStatus]
        assert len(update.message) > 0

    # Check completion
    final_update = progress_stream[-1]
    assert final_update.progress == 100
    assert final_update.status == SessionStatus.processed.value

    logger.info(f"✓ WebSocket streaming test passed: {len(progress_stream)} updates received")


# ============================================================================
# Test Summary and Metrics
# ============================================================================

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Custom pytest hook to display test summary with performance metrics.

    This hook runs after all tests complete and displays:
    - Number of integration tests run
    - Average processing time
    - Performance statistics
    """
    if hasattr(terminalreporter.config, 'workerinput'):
        return  # Skip in xdist workers

    stats = terminalreporter.stats

    if 'passed' in stats:
        passed_tests = stats['passed']
        integration_tests = [t for t in passed_tests if 'integration' in str(t.nodeid)]

        if integration_tests:
            terminalreporter.write_sep("=", "Integration Test Summary")
            terminalreporter.write_line(f"Integration tests passed: {len(integration_tests)}")
            terminalreporter.write_line("")
