"""
Comprehensive unit tests for ProgressTracker service.

Tests cover:
- Basic progress update and retrieval
- Multiple concurrent sessions
- Thread safety with concurrent updates
- WebSocket subscription/unsubscription
- Broadcast notifications to subscribers
- Edge cases (non-existent sessions, expired entries)
- TTL-based cleanup functionality
"""
import pytest
import pytest_asyncio
import asyncio
from uuid import uuid4, UUID
from datetime import datetime, timedelta
from typing import List
from unittest.mock import AsyncMock, MagicMock
from app.services.progress_tracker import (
    ProgressTracker,
    ProgressUpdate,
    get_progress_tracker
)
from app.models.schemas import SessionStatus


@pytest_asyncio.fixture
async def progress_tracker():
    """Create a fresh ProgressTracker instance for each test."""
    # Create tracker without starting background task
    tracker = ProgressTracker.__new__(ProgressTracker)
    tracker._progress = {}
    tracker._locks = {}
    tracker._subscribers = {}
    tracker._ttl_seconds = 60
    tracker._cleanup_task = None
    tracker._locks_lock = asyncio.Lock()

    yield tracker

    # Cleanup: cancel background task if it exists
    if tracker._cleanup_task and not tracker._cleanup_task.done():
        tracker._cleanup_task.cancel()
        try:
            await tracker._cleanup_task
        except asyncio.CancelledError:
            pass


@pytest.fixture
def sample_session_id() -> UUID:
    """Generate a sample session UUID."""
    return uuid4()


@pytest.fixture
def multiple_session_ids() -> List[UUID]:
    """Generate multiple session UUIDs for concurrent testing."""
    return [uuid4() for _ in range(5)]


# ============================================================================
# Basic Functionality Tests
# ============================================================================

@pytest.mark.asyncio
async def test_update_progress(progress_tracker, sample_session_id):
    """Test updating progress for a session."""
    # Update progress
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.transcribing,
        progress=45,
        message="Transcribing audio...",
    )

    # Retrieve and verify
    progress = await progress_tracker.get_progress(sample_session_id)
    assert progress is not None
    assert progress.session_id == sample_session_id
    assert progress.status == SessionStatus.transcribing
    assert progress.progress == 45
    assert progress.message == "Transcribing audio..."
    assert progress.error is None
    assert progress.estimated_time_remaining is None


@pytest.mark.asyncio
async def test_update_progress_with_error(progress_tracker, sample_session_id):
    """Test updating progress with error message."""
    error_msg = "Transcription failed: audio file corrupted"

    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.failed,
        progress=30,
        message="Processing failed",
        error=error_msg,
    )

    progress = await progress_tracker.get_progress(sample_session_id)
    assert progress.status == SessionStatus.failed
    assert progress.error == error_msg


@pytest.mark.asyncio
async def test_update_progress_with_time_estimate(progress_tracker, sample_session_id):
    """Test updating progress with estimated time remaining."""
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.transcribing,
        progress=25,
        message="Transcribing...",
        estimated_time_remaining=120,  # 2 minutes
    )

    progress = await progress_tracker.get_progress(sample_session_id)
    assert progress.estimated_time_remaining == 120


@pytest.mark.asyncio
async def test_get_progress_nonexistent_session(progress_tracker):
    """Test retrieving progress for non-existent session returns None."""
    non_existent_id = uuid4()
    progress = await progress_tracker.get_progress(non_existent_id)
    assert progress is None


@pytest.mark.asyncio
async def test_has_progress(progress_tracker, sample_session_id):
    """Test checking if progress exists for a session."""
    # Initially should not exist
    assert await progress_tracker.has_progress(sample_session_id) is False

    # After update, should exist
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.pending,
        progress=0,
        message="Starting...",
    )
    assert await progress_tracker.has_progress(sample_session_id) is True

    # After removal, should not exist
    await progress_tracker.remove_progress(sample_session_id)
    assert await progress_tracker.has_progress(sample_session_id) is False


@pytest.mark.asyncio
async def test_remove_progress(progress_tracker, sample_session_id):
    """Test removing progress tracking for a session."""
    # Add progress
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.processed,
        progress=100,
        message="Completed",
    )
    assert await progress_tracker.get_progress(sample_session_id) is not None

    # Remove progress
    await progress_tracker.remove_progress(sample_session_id)
    assert await progress_tracker.get_progress(sample_session_id) is None


# ============================================================================
# Multiple Sessions Tests
# ============================================================================

@pytest.mark.asyncio
async def test_multiple_sessions_concurrent(progress_tracker, multiple_session_ids):
    """Test tracking multiple sessions concurrently."""
    # Update progress for multiple sessions in parallel
    async def update_session(session_id: UUID, progress_value: int):
        await progress_tracker.update_progress(
            session_id=session_id,
            status=SessionStatus.transcribing,
            progress=progress_value,
            message=f"Processing session {progress_value}",
        )

    # Create tasks for all sessions
    tasks = [
        update_session(session_id, idx * 20)
        for idx, session_id in enumerate(multiple_session_ids)
    ]
    await asyncio.gather(*tasks)

    # Verify all sessions have correct progress
    for idx, session_id in enumerate(multiple_session_ids):
        progress = await progress_tracker.get_progress(session_id)
        assert progress is not None
        assert progress.progress == idx * 20
        assert progress.session_id == session_id


@pytest.mark.asyncio
async def test_multiple_sessions_isolation(progress_tracker, multiple_session_ids):
    """Test that updates to one session don't affect others."""
    # Initialize all sessions
    for session_id in multiple_session_ids:
        await progress_tracker.update_progress(
            session_id=session_id,
            status=SessionStatus.pending,
            progress=0,
            message="Initialized",
        )

    # Update only the first session
    target_session = multiple_session_ids[0]
    await progress_tracker.update_progress(
        session_id=target_session,
        status=SessionStatus.processed,
        progress=100,
        message="Completed",
    )

    # Verify target session updated
    progress = await progress_tracker.get_progress(target_session)
    assert progress.progress == 100
    assert progress.status == SessionStatus.processed

    # Verify other sessions unchanged
    for session_id in multiple_session_ids[1:]:
        progress = await progress_tracker.get_progress(session_id)
        assert progress.progress == 0
        assert progress.status == SessionStatus.pending


# ============================================================================
# Concurrency and Thread Safety Tests
# ============================================================================

@pytest.mark.asyncio
async def test_concurrent_updates_same_session(progress_tracker, sample_session_id):
    """
    Test thread safety with concurrent updates to the same session.
    Verifies no race conditions or data corruption.
    """
    update_count = 50

    async def update_task(progress_value: int):
        await progress_tracker.update_progress(
            session_id=sample_session_id,
            status=SessionStatus.transcribing,
            progress=progress_value % 101,  # Keep in 0-100 range
            message=f"Update {progress_value}",
        )

    # Launch concurrent updates
    tasks = [update_task(i) for i in range(update_count)]
    await asyncio.gather(*tasks)

    # Verify final state is consistent (no corruption)
    progress = await progress_tracker.get_progress(sample_session_id)
    assert progress is not None
    assert 0 <= progress.progress <= 100
    assert progress.status == SessionStatus.transcribing
    # Message should be from one of the updates
    assert "Update" in progress.message


@pytest.mark.asyncio
async def test_concurrent_reads_and_writes(progress_tracker, sample_session_id):
    """Test concurrent read and write operations don't cause issues."""
    write_count = 20
    read_count = 30

    # Initialize session
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.transcribing,
        progress=0,
        message="Starting",
    )

    async def write_task(value: int):
        await progress_tracker.update_progress(
            session_id=sample_session_id,
            status=SessionStatus.transcribing,
            progress=min(value * 5, 100),
            message=f"Writing {value}",
        )

    async def read_task():
        progress = await progress_tracker.get_progress(sample_session_id)
        assert progress is not None
        assert 0 <= progress.progress <= 100

    # Mix reads and writes
    tasks = []
    tasks.extend([write_task(i) for i in range(write_count)])
    tasks.extend([read_task() for _ in range(read_count)])

    # Shuffle to intermix operations
    import random
    random.shuffle(tasks)

    # Execute all tasks concurrently
    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_concurrent_session_operations(progress_tracker, multiple_session_ids):
    """Test concurrent add, update, and remove operations across multiple sessions."""
    async def session_lifecycle(session_id: UUID, delay: float):
        # Add
        await progress_tracker.update_progress(
            session_id=session_id,
            status=SessionStatus.pending,
            progress=0,
            message="Starting",
        )
        await asyncio.sleep(delay)

        # Update
        await progress_tracker.update_progress(
            session_id=session_id,
            status=SessionStatus.transcribing,
            progress=50,
            message="Processing",
        )
        await asyncio.sleep(delay)

        # Complete and remove
        await progress_tracker.update_progress(
            session_id=session_id,
            status=SessionStatus.processed,
            progress=100,
            message="Done",
        )
        await progress_tracker.remove_progress(session_id)

    # Run lifecycle for multiple sessions with varying delays
    tasks = [
        session_lifecycle(session_id, idx * 0.01)
        for idx, session_id in enumerate(multiple_session_ids)
    ]
    await asyncio.gather(*tasks)

    # All sessions should be removed
    for session_id in multiple_session_ids:
        assert await progress_tracker.has_progress(session_id) is False


# ============================================================================
# WebSocket Subscription Tests
# ============================================================================

@pytest.mark.asyncio
async def test_subscribe_and_notify(progress_tracker, sample_session_id):
    """Test subscribing to progress updates and receiving notifications."""
    received_updates = []

    async def callback(update: ProgressUpdate):
        received_updates.append(update)

    # Subscribe
    await progress_tracker.subscribe(sample_session_id, callback)

    # Update progress (should trigger callback)
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.transcribing,
        progress=50,
        message="Processing",
    )

    # Give callback time to execute
    await asyncio.sleep(0.1)

    # Verify callback was called
    assert len(received_updates) == 1
    assert received_updates[0].progress == 50
    assert received_updates[0].status == SessionStatus.transcribing


@pytest.mark.asyncio
async def test_subscribe_receives_current_progress(progress_tracker, sample_session_id):
    """Test that new subscribers immediately receive current progress."""
    received_updates = []

    # Set initial progress
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.transcribing,
        progress=30,
        message="Already processing",
    )

    async def callback(update: ProgressUpdate):
        received_updates.append(update)

    # Subscribe (should immediately receive current progress)
    await progress_tracker.subscribe(sample_session_id, callback)

    # Give callback time to execute
    await asyncio.sleep(0.1)

    # Verify received initial progress
    assert len(received_updates) == 1
    assert received_updates[0].progress == 30


@pytest.mark.asyncio
async def test_multiple_subscribers(progress_tracker, sample_session_id):
    """Test multiple subscribers receive updates."""
    received_updates_1 = []
    received_updates_2 = []
    received_updates_3 = []

    async def callback_1(update: ProgressUpdate):
        received_updates_1.append(update)

    async def callback_2(update: ProgressUpdate):
        received_updates_2.append(update)

    async def callback_3(update: ProgressUpdate):
        received_updates_3.append(update)

    # Subscribe all three
    await progress_tracker.subscribe(sample_session_id, callback_1)
    await progress_tracker.subscribe(sample_session_id, callback_2)
    await progress_tracker.subscribe(sample_session_id, callback_3)

    # Update progress
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.transcribing,
        progress=75,
        message="Almost done",
    )

    await asyncio.sleep(0.1)

    # All subscribers should receive update
    assert len(received_updates_1) == 1
    assert len(received_updates_2) == 1
    assert len(received_updates_3) == 1

    # All should have same data
    assert received_updates_1[0].progress == 75
    assert received_updates_2[0].progress == 75
    assert received_updates_3[0].progress == 75


@pytest.mark.asyncio
async def test_unsubscribe(progress_tracker, sample_session_id):
    """Test unsubscribing from progress updates."""
    received_updates = []

    async def callback(update: ProgressUpdate):
        received_updates.append(update)

    # Subscribe
    await progress_tracker.subscribe(sample_session_id, callback)

    # First update (should receive)
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.transcribing,
        progress=25,
        message="First update",
    )
    await asyncio.sleep(0.1)
    assert len(received_updates) == 1

    # Unsubscribe
    await progress_tracker.unsubscribe(sample_session_id, callback)

    # Second update (should NOT receive)
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.transcribing,
        progress=75,
        message="Second update",
    )
    await asyncio.sleep(0.1)

    # Should still only have 1 update
    assert len(received_updates) == 1
    assert received_updates[0].progress == 25


@pytest.mark.asyncio
async def test_unsubscribe_cleans_up_empty_sets(progress_tracker, sample_session_id):
    """Test that unsubscribing removes empty subscriber sets."""
    async def callback(update: ProgressUpdate):
        pass

    # Subscribe and verify subscribers dict has entry
    await progress_tracker.subscribe(sample_session_id, callback)
    assert sample_session_id in progress_tracker._subscribers

    # Unsubscribe and verify entry is removed (not just empty set)
    await progress_tracker.unsubscribe(sample_session_id, callback)
    assert sample_session_id not in progress_tracker._subscribers


@pytest.mark.asyncio
async def test_subscriber_error_handling(progress_tracker, sample_session_id):
    """Test that errors in subscriber callbacks don't crash the tracker."""
    received_updates_good = []

    async def failing_callback(update: ProgressUpdate):
        raise Exception("Subscriber error!")

    async def good_callback(update: ProgressUpdate):
        received_updates_good.append(update)

    # Subscribe both (one fails, one succeeds)
    await progress_tracker.subscribe(sample_session_id, failing_callback)
    await progress_tracker.subscribe(sample_session_id, good_callback)

    # Update progress (failing callback should be logged, not crash)
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.transcribing,
        progress=50,
        message="Test error handling",
    )

    await asyncio.sleep(0.1)

    # Good callback should still receive update
    assert len(received_updates_good) == 1
    assert received_updates_good[0].progress == 50


@pytest.mark.asyncio
async def test_subscriber_initial_progress_error(progress_tracker, sample_session_id):
    """Test error handling when sending initial progress to new subscriber fails."""
    async def failing_callback(update: ProgressUpdate):
        raise RuntimeError("Cannot send initial progress!")

    # Set initial progress
    await progress_tracker.update_progress(
        session_id=sample_session_id,
        status=SessionStatus.transcribing,
        progress=30,
        message="Initial progress",
    )

    # Subscribe with failing callback (should log error, not crash)
    # This tests line 368-369 (error handling for initial progress send)
    await progress_tracker.subscribe(sample_session_id, failing_callback)
    await asyncio.sleep(0.05)

    # Tracker should still be functional
    assert await progress_tracker.has_progress(sample_session_id)


@pytest.mark.asyncio
async def test_unsubscribe_nonexistent_session(progress_tracker):
    """Test unsubscribing from a session that doesn't exist."""
    async def dummy_callback(update: ProgressUpdate):
        pass

    non_existent_id = uuid4()

    # Should not raise an error (tests lines 385->390)
    await progress_tracker.unsubscribe(non_existent_id, dummy_callback)


@pytest.mark.asyncio
async def test_shutdown_method():
    """Test shutdown method cancels cleanup task."""
    # Create tracker with background task
    import app.services.progress_tracker as pt_module
    original_singleton = pt_module._progress_tracker
    pt_module._progress_tracker = None

    try:
        tracker = pt_module.get_progress_tracker()

        # Verify cleanup task is running
        assert tracker._cleanup_task is not None
        assert not tracker._cleanup_task.done()

        # Shutdown
        tracker.shutdown()

        # Give the task a moment to process cancellation
        await asyncio.sleep(0.01)

        # Task should be cancelled or done
        assert tracker._cleanup_task.cancelled() or tracker._cleanup_task.done()

        # Cleanup: wait for task to complete
        try:
            await tracker._cleanup_task
        except asyncio.CancelledError:
            pass
    finally:
        # Cleanup original singleton if it exists
        if original_singleton and original_singleton._cleanup_task:
            original_singleton._cleanup_task.cancel()
            try:
                await original_singleton._cleanup_task
            except asyncio.CancelledError:
                pass
        pt_module._progress_tracker = original_singleton


# ============================================================================
# Broadcast Tests
# ============================================================================

@pytest.mark.asyncio
async def test_broadcast_to_subscribers(progress_tracker, sample_session_id):
    """Test explicit broadcast without modifying stored progress."""
    received_updates = []

    async def callback(update: ProgressUpdate):
        received_updates.append(update)

    # Subscribe
    await progress_tracker.subscribe(sample_session_id, callback)
    await asyncio.sleep(0.05)  # Let initial subscribe complete

    # Create custom update (different from stored state)
    custom_update = ProgressUpdate(
        session_id=sample_session_id,
        status=SessionStatus.transcribing,
        progress=75,
        message="Custom broadcast message",
    )

    # Broadcast custom update
    await progress_tracker.broadcast(sample_session_id, custom_update)
    await asyncio.sleep(0.1)

    # Verify subscriber received the broadcast
    assert len(received_updates) >= 1
    # Last update should be the custom broadcast
    assert received_updates[-1].message == "Custom broadcast message"
    assert received_updates[-1].progress == 75


@pytest.mark.asyncio
async def test_broadcast_no_subscribers(progress_tracker, sample_session_id):
    """Test broadcast with no subscribers doesn't error."""
    custom_update = ProgressUpdate(
        session_id=sample_session_id,
        status=SessionStatus.pending,
        progress=0,
        message="No subscribers",
    )

    # Should not raise an error
    await progress_tracker.broadcast(sample_session_id, custom_update)


@pytest.mark.asyncio
async def test_broadcast_multiple_subscribers(progress_tracker, sample_session_id):
    """Test broadcast reaches all subscribers."""
    received_1 = []
    received_2 = []
    received_3 = []

    async def callback_1(update: ProgressUpdate):
        received_1.append(update)

    async def callback_2(update: ProgressUpdate):
        received_2.append(update)

    async def callback_3(update: ProgressUpdate):
        received_3.append(update)

    # Subscribe all
    await progress_tracker.subscribe(sample_session_id, callback_1)
    await progress_tracker.subscribe(sample_session_id, callback_2)
    await progress_tracker.subscribe(sample_session_id, callback_3)

    # Broadcast
    custom_update = ProgressUpdate(
        session_id=sample_session_id,
        status=SessionStatus.processed,
        progress=100,
        message="Broadcast to all",
    )
    await progress_tracker.broadcast(sample_session_id, custom_update)
    await asyncio.sleep(0.1)

    # All should have received it
    assert len(received_1) >= 1
    assert len(received_2) >= 1
    assert len(received_3) >= 1


# ============================================================================
# TTL and Cleanup Tests
# ============================================================================

@pytest.mark.asyncio
async def test_progress_ttl_expiration():
    """Test that progress expires after TTL and is cleaned up."""
    # Create tracker with very short TTL (1 second)
    tracker = ProgressTracker.__new__(ProgressTracker)
    tracker._progress = {}
    tracker._locks = {}
    tracker._subscribers = {}
    tracker._ttl_seconds = 1  # 1 second TTL
    tracker._cleanup_task = None
    tracker._locks_lock = asyncio.Lock()

    session_id = uuid4()

    # Create progress with old timestamp
    old_update = ProgressUpdate(
        session_id=session_id,
        status=SessionStatus.transcribing,
        progress=50,
        message="Old entry",
        created_at=datetime.utcnow() - timedelta(seconds=10),
        updated_at=datetime.utcnow() - timedelta(seconds=10),
    )
    tracker._progress[session_id] = old_update

    # Verify it exists
    assert await tracker.has_progress(session_id)

    # Manually trigger cleanup logic (without background task)
    now = datetime.utcnow()
    expired_sessions = []
    for sid, progress in list(tracker._progress.items()):
        age = (now - progress.updated_at).total_seconds()
        if age > tracker._ttl_seconds:
            expired_sessions.append(sid)

    # Should be marked as expired
    assert session_id in expired_sessions

    # Remove expired entries
    for sid in expired_sessions:
        await tracker.remove_progress(sid)

    # Should be gone
    assert not await tracker.has_progress(session_id)


@pytest.mark.asyncio
async def test_ttl_doesnt_remove_fresh_entries():
    """Test that fresh entries are not removed by TTL cleanup."""
    tracker = ProgressTracker.__new__(ProgressTracker)
    tracker._progress = {}
    tracker._locks = {}
    tracker._subscribers = {}
    tracker._ttl_seconds = 3600  # 1 hour TTL
    tracker._cleanup_task = None
    tracker._locks_lock = asyncio.Lock()

    session_id = uuid4()

    # Create fresh progress
    await tracker.update_progress(
        session_id=session_id,
        status=SessionStatus.transcribing,
        progress=50,
        message="Fresh entry",
    )

    # Check for expired entries
    now = datetime.utcnow()
    expired_sessions = []
    for sid, progress in list(tracker._progress.items()):
        age = (now - progress.updated_at).total_seconds()
        if age > tracker._ttl_seconds:
            expired_sessions.append(sid)

    # Should NOT be expired
    assert session_id not in expired_sessions
    assert await tracker.has_progress(session_id)


@pytest.mark.asyncio
async def test_get_all_active_sessions(progress_tracker, multiple_session_ids):
    """Test retrieving all active progress sessions."""
    # Add multiple sessions
    for idx, session_id in enumerate(multiple_session_ids):
        await progress_tracker.update_progress(
            session_id=session_id,
            status=SessionStatus.transcribing,
            progress=idx * 20,
            message=f"Session {idx}",
        )

    # Get all active sessions
    active = await progress_tracker.get_all_active_sessions()

    # Should have all sessions
    assert len(active) == len(multiple_session_ids)
    for session_id in multiple_session_ids:
        assert session_id in active
        assert isinstance(active[session_id], ProgressUpdate)


# ============================================================================
# Progress Update Model Tests
# ============================================================================

def test_progress_update_validation():
    """Test ProgressUpdate Pydantic model validation."""
    session_id = uuid4()

    # Valid update
    update = ProgressUpdate(
        session_id=session_id,
        status=SessionStatus.transcribing,
        progress=50,
        message="Processing...",
    )
    assert update.progress == 50
    assert update.error is None

    # Progress below 0 should fail
    with pytest.raises(Exception):  # Pydantic ValidationError
        ProgressUpdate(
            session_id=session_id,
            status=SessionStatus.transcribing,
            progress=-1,
            message="Invalid",
        )

    # Progress above 100 should fail
    with pytest.raises(Exception):  # Pydantic ValidationError
        ProgressUpdate(
            session_id=session_id,
            status=SessionStatus.transcribing,
            progress=101,
            message="Invalid",
        )


def test_progress_update_timestamps():
    """Test that ProgressUpdate automatically sets timestamps."""
    session_id = uuid4()
    before = datetime.utcnow()

    update = ProgressUpdate(
        session_id=session_id,
        status=SessionStatus.pending,
        progress=0,
        message="Starting",
    )

    after = datetime.utcnow()

    # Timestamps should be set automatically
    assert update.created_at is not None
    assert update.updated_at is not None

    # Should be within test execution time
    assert before <= update.created_at <= after
    assert before <= update.updated_at <= after


# ============================================================================
# Global Singleton Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_progress_tracker_singleton():
    """Test that get_progress_tracker returns singleton instance."""
    # Import the module to reset singleton
    import app.services.progress_tracker as pt_module

    # Reset singleton for test
    original_singleton = pt_module._progress_tracker
    pt_module._progress_tracker = None

    try:
        # Create tracker in async context (so background task can start)
        tracker1 = pt_module.get_progress_tracker()
        tracker2 = pt_module.get_progress_tracker()

        # Should be same instance
        assert tracker1 is tracker2

        # Cleanup
        if tracker1._cleanup_task and not tracker1._cleanup_task.done():
            tracker1._cleanup_task.cancel()
            try:
                await tracker1._cleanup_task
            except asyncio.CancelledError:
                pass
    finally:
        # Restore original singleton
        pt_module._progress_tracker = original_singleton


@pytest.mark.asyncio
async def test_singleton_preserves_state():
    """Test that singleton instance preserves state across calls."""
    import app.services.progress_tracker as pt_module

    # Reset singleton for test
    original_singleton = pt_module._progress_tracker
    pt_module._progress_tracker = None

    try:
        tracker = pt_module.get_progress_tracker()
        session_id = uuid4()

        # Add progress
        await tracker.update_progress(
            session_id=session_id,
            status=SessionStatus.transcribing,
            progress=33,
            message="Test singleton",
        )

        # Get tracker again
        tracker2 = pt_module.get_progress_tracker()

        # Should have same progress
        progress = await tracker2.get_progress(session_id)
        assert progress is not None
        assert progress.progress == 33

        # Cleanup
        await tracker.remove_progress(session_id)

        # Cancel background task
        if tracker._cleanup_task and not tracker._cleanup_task.done():
            tracker._cleanup_task.cancel()
            try:
                await tracker._cleanup_task
            except asyncio.CancelledError:
                pass
    finally:
        # Restore original singleton
        pt_module._progress_tracker = original_singleton


# ============================================================================
# Performance Tests
# ============================================================================

@pytest.mark.asyncio
async def test_high_volume_updates(progress_tracker):
    """Test handling high volume of concurrent updates across many sessions."""
    session_count = 100
    updates_per_session = 10

    session_ids = [uuid4() for _ in range(session_count)]

    async def update_session_multiple_times(session_id: UUID):
        for i in range(updates_per_session):
            await progress_tracker.update_progress(
                session_id=session_id,
                status=SessionStatus.transcribing,
                progress=min(i * 10, 100),
                message=f"Update {i}",
            )

    # Launch all tasks
    import time
    start = time.time()

    tasks = [update_session_multiple_times(sid) for sid in session_ids]
    await asyncio.gather(*tasks)

    elapsed = time.time() - start

    # Verify all sessions exist with final state
    for session_id in session_ids:
        progress = await progress_tracker.get_progress(session_id)
        assert progress is not None
        assert progress.progress == min((updates_per_session - 1) * 10, 100)

    # Performance check: should complete in reasonable time
    # 1000 total updates should finish in < 5 seconds
    assert elapsed < 5.0, f"High volume test took {elapsed:.2f}s (expected < 5s)"


@pytest.mark.asyncio
async def test_rapid_subscribe_unsubscribe(progress_tracker, sample_session_id):
    """Test rapid subscribe/unsubscribe cycles don't cause issues."""
    async def dummy_callback(update: ProgressUpdate):
        pass

    # Rapidly subscribe and unsubscribe
    for _ in range(100):
        await progress_tracker.subscribe(sample_session_id, dummy_callback)
        await progress_tracker.unsubscribe(sample_session_id, dummy_callback)

    # Should have no subscribers left
    assert sample_session_id not in progress_tracker._subscribers
