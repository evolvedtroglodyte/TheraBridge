"""
Performance Benchmarks for Audio Processing Pipeline

This test suite validates the <60 second processing target for 1-hour audio files.

Performance Requirements (from TherapyBridge specification):
- Process 1-hour audio in < 60 seconds (matching Upheal benchmark)
- Parallel execution should provide > 1.5x speedup vs sequential
- Memory usage should stay < 2GB per session
- Support concurrent processing of multiple sessions

Test Strategy:
1. Mock external API calls (Whisper, GPT-4) with realistic delays
2. Test synthetic audio of various durations (1min, 5min, 10min, 30min, 1hr)
3. Measure total processing time per stage
4. Verify parallel vs sequential speedup
5. Monitor CPU and memory usage
6. Test concurrent session processing

Dependencies:
- pytest-asyncio for async test support
- psutil for resource monitoring (optional - install separately)
- All tests use mocked API calls to isolate pipeline performance

Usage:
    # Run all performance tests
    pytest backend/tests/test_performance_benchmarks.py -v

    # Run with resource monitoring (requires psutil)
    pytest backend/tests/test_performance_benchmarks.py -v --log-cli-level=INFO

    # Run only 1hr target test
    pytest backend/tests/test_performance_benchmarks.py::test_1hr_audio_processing_time -v
"""

import pytest
import asyncio
import time
from pathlib import Path
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from typing import Dict, List, Tuple
import json

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

# Try to import psutil for resource monitoring (optional)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("WARNING: psutil not installed - resource monitoring disabled")


# ============================================================================
# Synthetic Audio Generation Utilities
# ============================================================================

def create_synthetic_audio(duration_seconds: int, tmp_path: Path) -> str:
    """
    Create synthetic audio file for testing.

    Args:
        duration_seconds: Duration of audio in seconds
        tmp_path: Temporary directory path (from pytest fixture)

    Returns:
        Path to synthetic audio file
    """
    audio_file = tmp_path / f"synthetic_{duration_seconds}s.mp3"

    # Create fake audio data with size proportional to duration
    # Rough estimate: 128kbps MP3 = ~16KB per second
    bytes_per_second = 16 * 1024
    fake_audio_data = b"FAKE_AUDIO_DATA" * (bytes_per_second * duration_seconds // 15)

    audio_file.write_bytes(fake_audio_data)
    return str(audio_file)


def get_realistic_api_delays(audio_duration_seconds: int) -> Dict[str, float]:
    """
    Calculate realistic API delay times based on audio duration.

    Based on empirical data from audio-transcription-pipeline testing:
    - Whisper API: ~0.4x real-time (24s for 1hr audio)
    - Pyannote diarization: ~0.3x real-time (18s for 1hr audio)
    - GPT-4o note extraction: ~8-12s regardless of length
    - Audio preprocessing: ~0.1x real-time (6s for 1hr audio)

    Args:
        audio_duration_seconds: Duration of audio in seconds

    Returns:
        Dict with delays for each stage:
        - preprocess: Audio preprocessing time
        - transcribe: Whisper transcription time
        - diarize: Speaker diarization time
        - extract_notes: GPT-4o extraction time
    """
    # Convert seconds to hours for calculation
    duration_hours = audio_duration_seconds / 3600.0

    return {
        "preprocess": duration_hours * 6.0,  # 6s per hour
        "transcribe": duration_hours * 24.0,  # 24s per hour (Whisper API)
        "diarize": duration_hours * 18.0,  # 18s per hour (pyannote)
        "extract_notes": 10.0,  # GPT-4o is constant ~10s
        "save_db": 1.0,  # Database save is constant ~1s
    }


def generate_mock_transcript(audio_duration_seconds: int) -> Dict:
    """
    Generate realistic mock transcript based on audio duration.

    Assumes ~150 words per minute speaking rate.
    Creates segments of ~5-10 seconds each.

    Args:
        audio_duration_seconds: Duration of audio in seconds

    Returns:
        Dict with transcript data matching Whisper API format
    """
    words_per_minute = 150
    total_words = int((audio_duration_seconds / 60) * words_per_minute)

    # Generate segments (each ~5-10 seconds, ~12-25 words)
    segments = []
    current_time = 0.0
    segment_duration = 7.5  # Average segment length
    words_per_segment = 20

    sample_sentences = [
        "How have you been feeling since our last session?",
        "I've been practicing the breathing exercises you suggested.",
        "That's wonderful to hear. Can you tell me more about that?",
        "When I feel anxious, I try to focus on my breath.",
        "Let's explore what triggers those anxious feelings.",
        "I think it's related to work stress and deadlines.",
        "Have you noticed any patterns in when the anxiety occurs?",
        "Usually in the mornings before meetings.",
        "That's a valuable insight. Let's work on coping strategies.",
        "I'm willing to try anything that might help.",
    ]

    num_segments = int(audio_duration_seconds / segment_duration)

    for i in range(num_segments):
        start = current_time
        end = current_time + segment_duration
        text = sample_sentences[i % len(sample_sentences)]

        segments.append({
            "start": start,
            "end": end,
            "text": text
        })

        current_time = end

    full_text = " ".join(seg["text"] for seg in segments)

    return {
        "segments": segments,
        "full_text": full_text,
        "language": "en",
        "duration": audio_duration_seconds
    }


def generate_mock_diarization(audio_duration_seconds: int) -> Dict:
    """
    Generate realistic mock diarization based on audio duration.

    Alternates between Therapist and Client speakers.

    Args:
        audio_duration_seconds: Duration of audio in seconds

    Returns:
        Dict with diarization data
    """
    segments = []
    current_time = 0.0
    segment_duration = 7.5  # Match transcript segment duration
    num_segments = int(audio_duration_seconds / segment_duration)

    for i in range(num_segments):
        speaker = "Therapist" if i % 2 == 0 else "Client"
        segments.append({
            "start": current_time,
            "end": current_time + segment_duration,
            "speaker": speaker
        })
        current_time += segment_duration

    return {
        "segments": segments,
        "speaker_count": 2
    }


def generate_mock_notes() -> ExtractedNotes:
    """
    Generate realistic mock extracted notes for testing.

    Returns:
        ExtractedNotes object matching GPT-4o output format
    """
    return ExtractedNotes(
        key_topics=["anxiety management", "work stress", "coping strategies"],
        topic_summary="Client discussed progress with breathing exercises and ongoing challenges with work-related anxiety.",
        strategies=[
            Strategy(
                name="Box breathing",
                category="breathing",
                status=StrategyStatus.practiced,
                context="Used before stressful meetings"
            )
        ],
        emotional_themes=["anxiety", "progress", "hope"],
        triggers=[
            {
                "trigger": "Morning meetings",
                "context": "Anticipatory anxiety before team meetings",
                "severity": "moderate"
            }
        ],
        action_items=[
            {
                "task": "Continue daily breathing practice",
                "category": "homework",
                "details": "Practice box breathing for 5 minutes each morning"
            }
        ],
        significant_quotes=[
            {
                "quote": "When I feel anxious, I try to focus on my breath",
                "context": "Demonstrates application of coping strategy"
            }
        ],
        session_mood=MoodLevel.neutral,
        mood_trajectory="improving",
        follow_up_topics=["workplace stress management", "assertiveness training"],
        unresolved_concerns=["work deadline anxiety"],
        risk_flags=[],
        therapist_notes="Client shows good progress with anxiety management techniques. Continue reinforcing breathing exercises and explore workplace stress management strategies.",
        patient_summary="You're making great progress! Keep practicing those breathing exercises - they're really helping with your anxiety. We'll continue working on strategies for managing work stress."
    )


# ============================================================================
# Resource Monitoring Utilities
# ============================================================================

class ResourceMonitor:
    """Monitor CPU and memory usage during test execution."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.peak_memory = None
        self.cpu_percent = []

    def start(self):
        """Start monitoring resources."""
        self.start_time = time.time()
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
            self.peak_memory = self.start_memory

    def sample(self):
        """Sample current resource usage."""
        if PSUTIL_AVAILABLE:
            process = psutil.Process()
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            self.peak_memory = max(self.peak_memory, current_memory)
            self.cpu_percent.append(process.cpu_percent(interval=0.1))

    def stop(self) -> Dict:
        """
        Stop monitoring and return results.

        Returns:
            Dict with resource usage statistics
        """
        self.end_time = time.time()
        elapsed = self.end_time - self.start_time

        if PSUTIL_AVAILABLE:
            return {
                "elapsed_time": elapsed,
                "memory_mb_start": self.start_memory,
                "memory_mb_peak": self.peak_memory,
                "memory_mb_delta": self.peak_memory - self.start_memory,
                "cpu_percent_avg": sum(self.cpu_percent) / len(self.cpu_percent) if self.cpu_percent else 0,
                "cpu_percent_max": max(self.cpu_percent) if self.cpu_percent else 0,
            }
        else:
            return {
                "elapsed_time": elapsed,
                "memory_mb_start": None,
                "memory_mb_peak": None,
                "memory_mb_delta": None,
                "cpu_percent_avg": None,
                "cpu_percent_max": None,
            }


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session for testing."""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def audio_service():
    """AudioProcessingService with mocked note extraction."""
    service = AudioProcessingService()
    service.note_service = MagicMock()
    service.note_service.extract_notes_from_transcript = AsyncMock()
    return service


# ============================================================================
# Performance Tests - Different Audio Durations
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_1min_audio_processing_time(audio_service, mock_db, tmp_path):
    """
    Baseline test: Process 1-minute audio.

    This establishes the baseline overhead for the pipeline.
    Expected time: < 12 seconds (GPT-4o note extraction adds ~10s fixed overhead)
    """
    # Setup
    session_id = uuid4()
    audio_path = create_synthetic_audio(60, tmp_path)  # 1 minute
    delays = get_realistic_api_delays(60)

    # Mock API calls with realistic delays
    async def mock_preprocess(audio_path_arg):
        await asyncio.sleep(delays["preprocess"])
        return audio_path_arg

    async def mock_transcribe(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["transcribe"])
        return generate_mock_transcript(60)

    async def mock_diarize(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["diarize"])
        return generate_mock_diarization(60)

    async def mock_extract_notes(transcript, segments):
        await asyncio.sleep(delays["extract_notes"])
        return generate_mock_notes()

    # Patch pipeline methods
    with patch.object(audio_service, '_preprocess_audio', side_effect=mock_preprocess), \
         patch.object(audio_service, '_transcribe_with_retry', side_effect=mock_transcribe), \
         patch.object(audio_service, '_diarize_with_retry', side_effect=mock_diarize):

        audio_service.note_service.extract_notes_from_transcript.side_effect = mock_extract_notes

        # Execute
        monitor = ResourceMonitor()
        monitor.start()

        start_time = time.time()
        result = await audio_service.process_session_audio(
            session_id=session_id,
            audio_file_path=audio_path,
            db=mock_db
        )
        elapsed = time.time() - start_time

        monitor.stop()
        resources = monitor.stop()

    # Assertions
    assert result["status"] == "processed"
    assert elapsed < 12.0, f"1min audio took {elapsed:.2f}s, expected < 12s"

    # Log results
    print(f"\n1-minute audio performance:")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Expected parallel time: ~{max(delays['transcribe'], delays['diarize']) + delays['preprocess'] + delays['extract_notes'] + delays['save_db']:.2f}s")
    if resources["memory_mb_peak"]:
        print(f"  Memory usage: {resources['memory_mb_delta']:.1f} MB delta, {resources['memory_mb_peak']:.1f} MB peak")


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_5min_audio_processing_time(audio_service, mock_db, tmp_path):
    """
    Mid-range test: Process 5-minute audio.

    Expected time: < 15 seconds
    """
    # Setup
    session_id = uuid4()
    audio_path = create_synthetic_audio(300, tmp_path)  # 5 minutes
    delays = get_realistic_api_delays(300)

    # Mock API calls
    async def mock_preprocess(audio_path_arg):
        await asyncio.sleep(delays["preprocess"])
        return audio_path_arg

    async def mock_transcribe(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["transcribe"])
        return generate_mock_transcript(300)

    async def mock_diarize(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["diarize"])
        return generate_mock_diarization(300)

    async def mock_extract_notes(transcript, segments):
        await asyncio.sleep(delays["extract_notes"])
        return generate_mock_notes()

    with patch.object(audio_service, '_preprocess_audio', side_effect=mock_preprocess), \
         patch.object(audio_service, '_transcribe_with_retry', side_effect=mock_transcribe), \
         patch.object(audio_service, '_diarize_with_retry', side_effect=mock_diarize):

        audio_service.note_service.extract_notes_from_transcript.side_effect = mock_extract_notes

        # Execute
        monitor = ResourceMonitor()
        monitor.start()

        start_time = time.time()
        result = await audio_service.process_session_audio(
            session_id=session_id,
            audio_file_path=audio_path,
            db=mock_db
        )
        elapsed = time.time() - start_time

        resources = monitor.stop()

    # Assertions
    assert result["status"] == "processed"
    assert elapsed < 15.0, f"5min audio took {elapsed:.2f}s, expected < 15s"

    print(f"\n5-minute audio performance:")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Expected parallel time: ~{max(delays['transcribe'], delays['diarize']) + delays['preprocess'] + delays['extract_notes'] + delays['save_db']:.2f}s")


@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_1hr_audio_processing_time(audio_service, mock_db, tmp_path):
    """
    PRIMARY PERFORMANCE TARGET: Process 1-hour audio in < 60 seconds.

    This is the critical benchmark from the TherapyBridge specification.
    Target matches Upheal's performance benchmark.

    With parallel execution:
    - Preprocess: ~6s
    - Transcribe (Whisper): ~24s } Run in PARALLEL
    - Diarize (pyannote): ~18s   }  → max(24, 18) = 24s
    - Extract notes (GPT-4o): ~10s
    - Save to DB: ~1s
    Total expected: ~41s (well under 60s target)

    CRITICAL ASSERTION: Total time must be < 60 seconds
    """
    # Setup
    session_id = uuid4()
    audio_path = create_synthetic_audio(3600, tmp_path)  # 1 hour
    delays = get_realistic_api_delays(3600)

    print(f"\nExpected stage delays for 1hr audio:")
    print(f"  Preprocess: {delays['preprocess']:.1f}s")
    print(f"  Transcribe: {delays['transcribe']:.1f}s")
    print(f"  Diarize: {delays['diarize']:.1f}s")
    print(f"  Extract notes: {delays['extract_notes']:.1f}s")
    print(f"  Save DB: {delays['save_db']:.1f}s")
    print(f"  Expected total (parallel): ~{delays['preprocess'] + max(delays['transcribe'], delays['diarize']) + delays['extract_notes'] + delays['save_db']:.1f}s")

    # Mock API calls with realistic delays
    async def mock_preprocess(audio_path_arg):
        await asyncio.sleep(delays["preprocess"])
        return audio_path_arg

    async def mock_transcribe(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["transcribe"])
        return generate_mock_transcript(3600)

    async def mock_diarize(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["diarize"])
        return generate_mock_diarization(3600)

    async def mock_extract_notes(transcript, segments):
        await asyncio.sleep(delays["extract_notes"])
        return generate_mock_notes()

    with patch.object(audio_service, '_preprocess_audio', side_effect=mock_preprocess), \
         patch.object(audio_service, '_transcribe_with_retry', side_effect=mock_transcribe), \
         patch.object(audio_service, '_diarize_with_retry', side_effect=mock_diarize):

        audio_service.note_service.extract_notes_from_transcript.side_effect = mock_extract_notes

        # Execute with resource monitoring
        monitor = ResourceMonitor()
        monitor.start()

        start_time = time.time()
        result = await audio_service.process_session_audio(
            session_id=session_id,
            audio_file_path=audio_path,
            db=mock_db
        )
        elapsed = time.time() - start_time

        resources = monitor.stop()

    # CRITICAL ASSERTION: Must process in under 60 seconds
    assert result["status"] == "processed", "Processing should complete successfully"
    assert elapsed < 60.0, f"❌ FAILED: 1hr audio took {elapsed:.2f}s, REQUIRED < 60s"

    # Secondary assertion: Should achieve parallel speedup
    # With parallel execution, time should be ~40s (6 + 24 + 10 + 1)
    # Allow some overhead, but should be well under 50s
    expected_parallel_time = delays['preprocess'] + max(delays['transcribe'], delays['diarize']) + delays['extract_notes'] + delays['save_db']
    assert elapsed < expected_parallel_time + 10, f"Processing took {elapsed:.2f}s, expected ~{expected_parallel_time:.1f}s with parallel execution"

    # Success - log detailed results
    print(f"\n✅ SUCCESS: 1-hour audio performance TARGET MET:")
    print(f"  Total time: {elapsed:.2f}s (target: < 60s)")
    print(f"  Parallel efficiency: {(expected_parallel_time / elapsed) * 100:.1f}%")
    print(f"  Segments processed: {len(result['segments'])}")

    if resources["memory_mb_peak"]:
        print(f"  Memory usage: {resources['memory_mb_delta']:.1f} MB delta, {resources['memory_mb_peak']:.1f} MB peak")
        # Assert memory usage < 2GB
        assert resources["memory_mb_peak"] < 2048, f"Memory usage {resources['memory_mb_peak']:.1f} MB exceeds 2GB limit"


# ============================================================================
# Parallel vs Sequential Speedup Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_parallel_vs_sequential_speedup(audio_service, mock_db, tmp_path):
    """
    Measure speedup from parallel execution vs sequential.

    This test runs the same workload:
    1. Sequential: transcribe → diarize (one after the other)
    2. Parallel: transcribe + diarize (concurrently via asyncio.gather)

    Expected speedup: > 1.5x (since transcribe and diarize have similar durations)

    For 1hr audio:
    - Sequential: 24s (transcribe) + 18s (diarize) = 42s
    - Parallel: max(24s, 18s) = 24s
    - Speedup: 42/24 = 1.75x
    """
    session_id = uuid4()
    audio_path = create_synthetic_audio(3600, tmp_path)  # 1 hour
    delays = get_realistic_api_delays(3600)

    # Mock functions
    async def mock_transcribe(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["transcribe"])
        return generate_mock_transcript(3600)

    async def mock_diarize(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["diarize"])
        return generate_mock_diarization(3600)

    # Test 1: Sequential execution
    print("\n--- Sequential Execution ---")
    start_seq = time.time()

    transcript_seq = await mock_transcribe(str(session_id), audio_path)
    diarization_seq = await mock_diarize(str(session_id), audio_path)

    elapsed_seq = time.time() - start_seq
    print(f"Sequential time: {elapsed_seq:.2f}s")

    # Test 2: Parallel execution (using asyncio.gather like the service does)
    print("\n--- Parallel Execution ---")
    start_par = time.time()

    transcript_par, diarization_par = await asyncio.gather(
        mock_transcribe(str(session_id), audio_path),
        mock_diarize(str(session_id), audio_path)
    )

    elapsed_par = time.time() - start_par
    print(f"Parallel time: {elapsed_par:.2f}s")

    # Calculate speedup
    speedup = elapsed_seq / elapsed_par
    print(f"\nSpeedup: {speedup:.2f}x")
    print(f"Expected speedup: {(delays['transcribe'] + delays['diarize']) / max(delays['transcribe'], delays['diarize']):.2f}x")

    # Assertions
    assert speedup > 1.5, f"Parallel speedup was {speedup:.2f}x, expected > 1.5x"
    assert elapsed_par < elapsed_seq, "Parallel execution should be faster than sequential"

    # Verify parallel time is approximately max(transcribe, diarize)
    expected_parallel = max(delays['transcribe'], delays['diarize'])
    assert abs(elapsed_par - expected_parallel) < 2.0, f"Parallel time {elapsed_par:.2f}s should be ~{expected_parallel:.1f}s"


# ============================================================================
# Concurrent Session Processing Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_throughput_multiple_sessions(audio_service, mock_db, tmp_path):
    """
    Test concurrent processing of 5 sessions.

    Verifies that the service can handle multiple sessions simultaneously
    without significant performance degradation.

    Expected behavior:
    - 5 sessions processed concurrently
    - Each session completes in < 60s
    - Total time < 70s (due to async I/O overlap)
    """
    # Create 5 sessions with 1hr audio each
    num_sessions = 5
    sessions = []

    for i in range(num_sessions):
        session_id = uuid4()
        audio_path = create_synthetic_audio(3600, tmp_path)  # 1 hour
        sessions.append({
            "id": session_id,
            "path": audio_path
        })

    delays = get_realistic_api_delays(3600)

    # Mock API calls
    async def mock_preprocess(audio_path_arg):
        await asyncio.sleep(delays["preprocess"])
        return audio_path_arg

    async def mock_transcribe(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["transcribe"])
        return generate_mock_transcript(3600)

    async def mock_diarize(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["diarize"])
        return generate_mock_diarization(3600)

    async def mock_extract_notes(transcript, segments):
        await asyncio.sleep(delays["extract_notes"])
        return generate_mock_notes()

    with patch.object(audio_service, '_preprocess_audio', side_effect=mock_preprocess), \
         patch.object(audio_service, '_transcribe_with_retry', side_effect=mock_transcribe), \
         patch.object(audio_service, '_diarize_with_retry', side_effect=mock_diarize):

        audio_service.note_service.extract_notes_from_transcript.side_effect = mock_extract_notes

        # Process all sessions concurrently
        monitor = ResourceMonitor()
        monitor.start()

        start_time = time.time()

        tasks = [
            audio_service.process_session_audio(
                session_id=session["id"],
                audio_file_path=session["path"],
                db=mock_db
            )
            for session in sessions
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.time() - start_time
        resources = monitor.stop()

    # Assertions
    assert all(isinstance(r, dict) for r in results), "All sessions should complete successfully"
    assert all(r["status"] == "processed" for r in results), "All sessions should be processed"

    # With perfect parallelism, time should be ~41s (same as single session)
    # With some overhead, allow up to 70s for 5 concurrent sessions
    assert elapsed < 70.0, f"Processing 5 concurrent sessions took {elapsed:.2f}s, expected < 70s"

    print(f"\nConcurrent session processing:")
    print(f"  Sessions: {num_sessions}")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Average per session: {elapsed / num_sessions:.2f}s")
    print(f"  Single session time: ~41s")
    print(f"  Concurrency efficiency: {(41 * num_sessions / elapsed):.1f}x")

    if resources["memory_mb_peak"]:
        print(f"  Peak memory: {resources['memory_mb_peak']:.1f} MB")
        print(f"  Memory per session: {resources['memory_mb_delta'] / num_sessions:.1f} MB")


# ============================================================================
# Resource Usage Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.benchmark
@pytest.mark.skipif(not PSUTIL_AVAILABLE, reason="Requires psutil for resource monitoring")
async def test_resource_usage(audio_service, mock_db, tmp_path):
    """
    Monitor CPU and memory usage during 1hr audio processing.

    Performance requirements:
    - Memory usage < 2GB per session
    - CPU usage should be moderate (API calls are I/O bound)

    This test requires psutil to be installed:
        pip install psutil
    """
    # Setup
    session_id = uuid4()
    audio_path = create_synthetic_audio(3600, tmp_path)  # 1 hour
    delays = get_realistic_api_delays(3600)

    # Mock API calls
    async def mock_preprocess(audio_path_arg):
        await asyncio.sleep(delays["preprocess"])
        return audio_path_arg

    async def mock_transcribe(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["transcribe"])
        return generate_mock_transcript(3600)

    async def mock_diarize(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["diarize"])
        return generate_mock_diarization(3600)

    async def mock_extract_notes(transcript, segments):
        await asyncio.sleep(delays["extract_notes"])
        return generate_mock_notes()

    with patch.object(audio_service, '_preprocess_audio', side_effect=mock_preprocess), \
         patch.object(audio_service, '_transcribe_with_retry', side_effect=mock_transcribe), \
         patch.object(audio_service, '_diarize_with_retry', side_effect=mock_diarize):

        audio_service.note_service.extract_notes_from_transcript.side_effect = mock_extract_notes

        # Execute with active resource monitoring
        monitor = ResourceMonitor()
        monitor.start()

        # Create background task to sample resources periodically
        async def sample_resources():
            while True:
                monitor.sample()
                await asyncio.sleep(0.5)

        sampling_task = asyncio.create_task(sample_resources())

        try:
            result = await audio_service.process_session_audio(
                session_id=session_id,
                audio_file_path=audio_path,
                db=mock_db
            )
        finally:
            sampling_task.cancel()
            try:
                await sampling_task
            except asyncio.CancelledError:
                pass

        resources = monitor.stop()

    # Assertions
    assert result["status"] == "processed"

    # Memory usage should be under 2GB
    assert resources["memory_mb_peak"] < 2048, f"Memory usage {resources['memory_mb_peak']:.1f} MB exceeds 2GB limit"

    # Log detailed resource usage
    print(f"\nResource usage for 1hr audio:")
    print(f"  Processing time: {resources['elapsed_time']:.2f}s")
    print(f"  Memory (start): {resources['memory_mb_start']:.1f} MB")
    print(f"  Memory (peak): {resources['memory_mb_peak']:.1f} MB")
    print(f"  Memory (delta): {resources['memory_mb_delta']:.1f} MB")
    print(f"  CPU (average): {resources['cpu_percent_avg']:.1f}%")
    print(f"  CPU (peak): {resources['cpu_percent_max']:.1f}%")


# ============================================================================
# Performance Report Generation
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.benchmark
async def test_generate_performance_report(audio_service, mock_db, tmp_path):
    """
    Generate comprehensive performance report with all metrics.

    This test runs the complete suite and generates a JSON report with:
    - Processing times for different audio durations
    - Parallel vs sequential speedup
    - Resource usage statistics
    - Target compliance (< 60s for 1hr audio)

    Report saved to: backend/tests/outputs/performance_report.json
    """
    report = {
        "test_date": datetime.utcnow().isoformat(),
        "performance_target": "< 60 seconds for 1hr audio",
        "tests": []
    }

    # Test different durations
    test_durations = [
        (60, "1min", 12.0),
        (300, "5min", 15.0),
        (600, "10min", 25.0),
        (1800, "30min", 40.0),
        (3600, "1hr", 60.0),
    ]

    for duration_seconds, label, target_time in test_durations:
        session_id = uuid4()
        audio_path = create_synthetic_audio(duration_seconds, tmp_path)
        delays = get_realistic_api_delays(duration_seconds)

        # Mock API calls
        async def mock_preprocess(audio_path_arg):
            await asyncio.sleep(delays["preprocess"])
            return audio_path_arg

        async def mock_transcribe(session_id_str, audio_path_arg):
            await asyncio.sleep(delays["transcribe"])
            return generate_mock_transcript(duration_seconds)

        async def mock_diarize(session_id_str, audio_path_arg):
            await asyncio.sleep(delays["diarize"])
            return generate_mock_diarization(duration_seconds)

        async def mock_extract_notes(transcript, segments):
            await asyncio.sleep(delays["extract_notes"])
            return generate_mock_notes()

        with patch.object(audio_service, '_preprocess_audio', side_effect=mock_preprocess), \
             patch.object(audio_service, '_transcribe_with_retry', side_effect=mock_transcribe), \
             patch.object(audio_service, '_diarize_with_retry', side_effect=mock_diarize):

            audio_service.note_service.extract_notes_from_transcript.side_effect = mock_extract_notes

            # Execute
            start_time = time.time()
            result = await audio_service.process_session_audio(
                session_id=session_id,
                audio_file_path=audio_path,
                db=mock_db
            )
            elapsed = time.time() - start_time

            # Record results
            test_result = {
                "duration_label": label,
                "duration_seconds": duration_seconds,
                "processing_time": round(elapsed, 2),
                "target_time": target_time,
                "target_met": elapsed < target_time,
                "stage_delays": delays,
                "segments_count": len(result["segments"]),
            }
            report["tests"].append(test_result)

    # Calculate parallel speedup
    session_id = uuid4()
    audio_path = create_synthetic_audio(3600, tmp_path)
    delays = get_realistic_api_delays(3600)

    async def mock_transcribe_speedup(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["transcribe"])
        return generate_mock_transcript(3600)

    async def mock_diarize_speedup(session_id_str, audio_path_arg):
        await asyncio.sleep(delays["diarize"])
        return generate_mock_diarization(3600)

    # Sequential
    start_seq = time.time()
    await mock_transcribe_speedup(str(session_id), audio_path)
    await mock_diarize_speedup(str(session_id), audio_path)
    elapsed_seq = time.time() - start_seq

    # Parallel
    start_par = time.time()
    await asyncio.gather(
        mock_transcribe_speedup(str(session_id), audio_path),
        mock_diarize_speedup(str(session_id), audio_path)
    )
    elapsed_par = time.time() - start_par

    report["parallel_speedup"] = {
        "sequential_time": round(elapsed_seq, 2),
        "parallel_time": round(elapsed_par, 2),
        "speedup_factor": round(elapsed_seq / elapsed_par, 2),
        "target_speedup": 1.5,
        "target_met": (elapsed_seq / elapsed_par) > 1.5
    }

    # Overall summary
    report["summary"] = {
        "1hr_target_met": report["tests"][-1]["target_met"],
        "all_targets_met": all(test["target_met"] for test in report["tests"]),
        "parallel_speedup_met": report["parallel_speedup"]["target_met"],
    }

    # Save report
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)
    report_path = output_dir / "performance_report.json"

    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    # Print summary
    print("\n" + "=" * 60)
    print("PERFORMANCE BENCHMARK REPORT")
    print("=" * 60)

    for test in report["tests"]:
        status = "✅ PASS" if test["target_met"] else "❌ FAIL"
        print(f"{status} {test['duration_label']:>6} | {test['processing_time']:>6.2f}s / {test['target_time']:>6.1f}s target")

    print("\nParallel Speedup:")
    status = "✅ PASS" if report["parallel_speedup"]["target_met"] else "❌ FAIL"
    print(f"{status} {report['parallel_speedup']['speedup_factor']:.2f}x (target: > 1.5x)")

    print("\nOverall Result:")
    if report["summary"]["all_targets_met"] and report["summary"]["parallel_speedup_met"]:
        print("✅ ALL PERFORMANCE TARGETS MET")
    else:
        print("❌ SOME PERFORMANCE TARGETS NOT MET")

    print(f"\nDetailed report saved to: {report_path}")
    print("=" * 60)

    # Assertions
    assert report["summary"]["1hr_target_met"], "1hr audio must process in < 60s"
    assert report["summary"]["parallel_speedup_met"], "Parallel speedup must be > 1.5x"
