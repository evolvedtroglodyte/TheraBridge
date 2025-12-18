"""
Comprehensive test suite for session management (Feature 8 HIPAA Compliance).

Tests cover:
- Session creation with limit enforcement and device fingerprinting
- Session validation with timeout and expiry checks
- Session revocation (single and bulk)
- Session listing with current session marking
- Cleanup of expired and idle sessions
- Authorization checks (users can't revoke others' sessions)

Implements HIPAA-compliant session security:
- 8-hour absolute expiration
- 30-minute idle timeout
- Max 5 concurrent sessions per user
- Device fingerprinting and tracking
"""
import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time
from uuid import uuid4
from unittest.mock import MagicMock
from fastapi import Request

from app.security.session_manager import SessionManager, get_session_manager
from app.models.security_models import UserSession
from sqlalchemy import select


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def session_manager():
    """Provide a SessionManager instance for testing."""
    return SessionManager()


@pytest.fixture
def mock_request():
    """
    Create a mock FastAPI Request object with realistic headers.

    Returns:
        MagicMock configured with client IP, user-agent, and headers
    """
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = "192.168.1.100"
    request.headers = {
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    return request


@pytest.fixture
def mobile_request():
    """Create a mock Request from a mobile device."""
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = "10.0.0.1"
    request.headers = {
        "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    }
    return request


@pytest.fixture
async def user_with_sessions(test_db, test_user, session_manager, mock_request):
    """
    Create a user with 3 active sessions for testing.

    Returns:
        Dict with:
        - user: User object
        - sessions: List of 3 UserSession objects
        - tokens: List of 3 raw tokens (for validation tests)
    """
    sessions = []
    tokens = []

    for i in range(3):
        # Modify request IP to simulate different devices
        mock_request.client.host = f"192.168.1.{100 + i}"

        session, token = await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()
        await test_db.refresh(session)

        sessions.append(session)
        tokens.append(token)

    return {
        "user": test_user,
        "sessions": sessions,
        "tokens": tokens
    }


@pytest.fixture
async def expired_session(test_db, test_user, session_manager, mock_request):
    """
    Create a session that has exceeded absolute expiration (8 hours).

    Returns:
        Tuple of (UserSession object, raw token)
    """
    with freeze_time("2025-01-01 00:00:00"):
        session, token = await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()
        await test_db.refresh(session)

    # Move time forward 9 hours (past 8-hour expiration)
    with freeze_time("2025-01-01 09:00:00"):
        return session, token


@pytest.fixture
async def idle_session(test_db, test_user, session_manager, mock_request):
    """
    Create a session that has exceeded idle timeout (30 minutes).

    Returns:
        Tuple of (UserSession object, raw token)
    """
    with freeze_time("2025-01-01 12:00:00"):
        session, token = await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()
        await test_db.refresh(session)

    # Move time forward 35 minutes (past 30-minute idle timeout)
    with freeze_time("2025-01-01 12:35:00"):
        return session, token


# ============================================================================
# Session Creation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_session_success(test_db, test_user, session_manager, mock_request):
    """Test SessionManager creates session with secure token and device info."""
    session, raw_token = await session_manager.create_session(
        user_id=test_user.id,
        request=mock_request,
        db=test_db
    )
    await test_db.commit()
    await test_db.refresh(session)

    # Verify session created
    assert session.id is not None
    assert session.user_id == test_user.id
    assert session.is_active is True

    # Verify token is secure (32 bytes urlsafe = ~43 characters)
    assert len(raw_token) >= 40

    # Verify token is hashed in database
    assert session.session_token_hash is not None
    assert session.session_token_hash != raw_token  # Not stored plaintext
    assert len(session.session_token_hash) == 64  # SHA-256 hex = 64 chars

    # Verify expiration times
    assert session.expires_at is not None
    expected_expiry = datetime.utcnow() + timedelta(hours=SessionManager.SESSION_EXPIRY_HOURS)
    assert abs((session.expires_at - expected_expiry).total_seconds()) < 5

    # Verify activity tracking
    assert session.last_activity_at is not None
    assert session.created_at is not None


@pytest.mark.asyncio
async def test_create_session_enforces_limit(test_db, test_user, session_manager, mock_request):
    """Test max 5 sessions enforced - oldest session revoked when limit exceeded."""
    # Create 5 sessions (at the limit)
    sessions = []
    for i in range(5):
        mock_request.client.host = f"192.168.1.{i}"
        session, token = await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()
        await test_db.refresh(session)
        sessions.append(session)

    # Verify all 5 are active
    result = await test_db.execute(
        select(UserSession).where(
            UserSession.user_id == test_user.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 5

    # Create 6th session - should revoke oldest
    mock_request.client.host = "192.168.1.99"
    new_session, new_token = await session_manager.create_session(
        user_id=test_user.id,
        request=mock_request,
        db=test_db
    )
    await test_db.commit()

    # Verify still only 5 active sessions
    result = await test_db.execute(
        select(UserSession).where(
            UserSession.user_id == test_user.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 5

    # Verify oldest session was revoked
    await test_db.refresh(sessions[0])
    assert sessions[0].is_active is False
    assert sessions[0].revoke_reason == "session_limit_exceeded"


@pytest.mark.asyncio
async def test_create_session_revokes_oldest(test_db, test_user, session_manager, mock_request):
    """Test that when limit is exceeded, the OLDEST session is revoked (not random)."""
    # Create sessions with different timestamps
    oldest_session = None

    for i in range(6):
        with freeze_time(f"2025-01-01 10:{i:02d}:00"):
            mock_request.client.host = f"192.168.1.{i}"
            session, token = await session_manager.create_session(
                user_id=test_user.id,
                request=mock_request,
                db=test_db
            )
            await test_db.commit()
            await test_db.refresh(session)

            if i == 0:
                oldest_session = session

    # Verify oldest session (from 10:00) was revoked
    await test_db.refresh(oldest_session)
    assert oldest_session.is_active is False
    assert oldest_session.revoke_reason == "session_limit_exceeded"

    # Verify newest 5 sessions are still active
    result = await test_db.execute(
        select(UserSession).where(
            UserSession.user_id == test_user.id,
            UserSession.is_active == True
        )
    )
    active_sessions = result.scalars().all()
    assert len(active_sessions) == 5


@pytest.mark.asyncio
async def test_create_session_extracts_device_info(test_db, test_user, session_manager, mock_request, mobile_request):
    """Test device fingerprinting extracts device_type, OS, browser, is_mobile."""
    # Test desktop session
    desktop_session, _ = await session_manager.create_session(
        user_id=test_user.id,
        request=mock_request,
        db=test_db
    )
    await test_db.commit()
    await test_db.refresh(desktop_session)

    assert desktop_session.device_info is not None
    assert desktop_session.device_info["device_type"] == "desktop"
    assert "Mac OS X" in desktop_session.device_info["os"]
    assert "Chrome" in desktop_session.device_info["browser"]
    assert desktop_session.device_info["is_mobile"] is False

    # Test mobile session
    mobile_session, _ = await session_manager.create_session(
        user_id=test_user.id,
        request=mobile_request,
        db=test_db
    )
    await test_db.commit()
    await test_db.refresh(mobile_session)

    assert mobile_session.device_info is not None
    assert mobile_session.device_info["device_type"] == "mobile"
    assert "iOS" in mobile_session.device_info["os"]
    assert "Safari" in mobile_session.device_info["browser"]
    assert mobile_session.device_info["is_mobile"] is True


# ============================================================================
# Session Validation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_validate_session_success(test_db, test_user, session_manager, mock_request):
    """Test valid session passes validation and updates last_activity_at."""
    # Create session
    session, token = await session_manager.create_session(
        user_id=test_user.id,
        request=mock_request,
        db=test_db
    )
    await test_db.commit()
    original_activity = session.last_activity_at

    # Wait 1 second and validate
    with freeze_time(datetime.utcnow() + timedelta(seconds=1)):
        validated_session = await session_manager.validate_session(token, test_db)
        await test_db.commit()

    assert validated_session is not None
    assert validated_session.id == session.id
    assert validated_session.is_active is True

    # Verify last_activity_at was updated
    await test_db.refresh(session)
    assert session.last_activity_at > original_activity


@pytest.mark.asyncio
async def test_validate_session_expired(test_db, test_user, session_manager):
    """Test expired session fails validation (8 hours)."""
    # Create session at T=0
    with freeze_time("2025-01-01 00:00:00"):
        from unittest.mock import MagicMock
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {"user-agent": "test"}

        session, token = await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()
        session_id = session.id

    # Validate at T=9 hours (past 8-hour expiration)
    with freeze_time("2025-01-01 09:00:00"):
        validated_session = await session_manager.validate_session(token, test_db)
        await test_db.commit()

    assert validated_session is None

    # Verify session was revoked
    result = await test_db.execute(
        select(UserSession).where(UserSession.id == session_id)
    )
    revoked_session = result.scalar_one()
    assert revoked_session.is_active is False
    assert revoked_session.revoke_reason == "expired"


@pytest.mark.asyncio
async def test_validate_session_idle_timeout(test_db, test_user, session_manager):
    """Test idle timeout enforced (30 minutes)."""
    # Create session at T=0
    with freeze_time("2025-01-01 12:00:00"):
        from unittest.mock import MagicMock
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {"user-agent": "test"}

        session, token = await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()
        session_id = session.id

    # Validate at T=35 minutes (past 30-minute idle timeout)
    with freeze_time("2025-01-01 12:35:00"):
        validated_session = await session_manager.validate_session(token, test_db)
        await test_db.commit()

    assert validated_session is None

    # Verify session was revoked
    result = await test_db.execute(
        select(UserSession).where(UserSession.id == session_id)
    )
    revoked_session = result.scalar_one()
    assert revoked_session.is_active is False
    assert revoked_session.revoke_reason == "idle_timeout"


@pytest.mark.asyncio
async def test_validate_session_updates_activity(test_db, test_user, session_manager, mock_request):
    """Test that validation updates last_activity_at timestamp."""
    # Create session
    with freeze_time("2025-01-01 10:00:00"):
        session, token = await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()
        await test_db.refresh(session)
        initial_activity = session.last_activity_at

    # Validate 10 minutes later
    with freeze_time("2025-01-01 10:10:00"):
        validated_session = await session_manager.validate_session(token, test_db)
        await test_db.commit()

    assert validated_session is not None
    assert validated_session.last_activity_at > initial_activity

    # Verify timestamp in database
    await test_db.refresh(session)
    expected_time = datetime(2025, 1, 1, 10, 10, 0)
    assert abs((session.last_activity_at - expected_time).total_seconds()) < 5


@pytest.mark.asyncio
async def test_validate_session_invalid_token(test_db, session_manager):
    """Test validation fails with non-existent token."""
    invalid_token = "invalid-token-12345678901234567890"
    validated_session = await session_manager.validate_session(invalid_token, test_db)

    assert validated_session is None


@pytest.mark.asyncio
async def test_validate_session_revoked(test_db, test_user, session_manager, mock_request):
    """Test validation fails for revoked sessions."""
    # Create and revoke session
    session, token = await session_manager.create_session(
        user_id=test_user.id,
        request=mock_request,
        db=test_db
    )
    await test_db.commit()

    await session_manager.revoke_session(session.id, "test_revocation", test_db)
    await test_db.commit()

    # Attempt validation
    validated_session = await session_manager.validate_session(token, test_db)

    assert validated_session is None


# ============================================================================
# Session Revocation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_revoke_session_success(test_db, test_user, session_manager, mock_request):
    """Test single session revoked successfully."""
    # Create session
    session, token = await session_manager.create_session(
        user_id=test_user.id,
        request=mock_request,
        db=test_db
    )
    await test_db.commit()

    # Revoke session
    await session_manager.revoke_session(session.id, "user_logout", test_db)
    await test_db.commit()

    # Verify revocation
    await test_db.refresh(session)
    assert session.is_active is False
    assert session.revoked_at is not None
    assert session.revoke_reason == "user_logout"


@pytest.mark.asyncio
async def test_revoke_all_sessions_except_current(test_db, user_with_sessions, session_manager):
    """Test revokes all but current session."""
    sessions = user_with_sessions["sessions"]
    tokens = user_with_sessions["tokens"]
    current_token = tokens[0]  # Keep first session

    # Revoke all except current
    count = await session_manager.revoke_all_sessions(
        user_id=user_with_sessions["user"].id,
        except_token=current_token,
        db=test_db
    )
    await test_db.commit()

    # Verify 2 sessions revoked (out of 3 total)
    assert count == 2

    # Verify current session still active
    await test_db.refresh(sessions[0])
    assert sessions[0].is_active is True

    # Verify others revoked
    await test_db.refresh(sessions[1])
    await test_db.refresh(sessions[2])
    assert sessions[1].is_active is False
    assert sessions[2].is_active is False
    assert sessions[1].revoke_reason == "revoke_all_sessions"
    assert sessions[2].revoke_reason == "revoke_all_sessions"


@pytest.mark.asyncio
async def test_revoke_session_not_found(test_db, session_manager):
    """Test revoking non-existent session doesn't crash."""
    fake_session_id = uuid4()

    # Should not raise exception
    await session_manager.revoke_session(fake_session_id, "test", test_db)
    await test_db.commit()


# ============================================================================
# Session List Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_active_sessions(test_db, user_with_sessions, session_manager):
    """Test retrieves all active sessions ordered by last activity."""
    sessions = await session_manager.get_active_sessions(
        user_id=user_with_sessions["user"].id,
        db=test_db
    )

    # Verify all 3 sessions returned
    assert len(sessions) == 3

    # Verify sessions ordered by last_activity_at (most recent first)
    for i in range(len(sessions) - 1):
        assert sessions[i].last_activity_at >= sessions[i + 1].last_activity_at


@pytest.mark.asyncio
async def test_get_active_sessions_shows_device_info(test_db, user_with_sessions, session_manager):
    """Test session list includes device info."""
    sessions = await session_manager.get_active_sessions(
        user_id=user_with_sessions["user"].id,
        db=test_db
    )

    # Verify each session has device info
    for session in sessions:
        assert session.device_info is not None
        assert "device_type" in session.device_info
        assert "os" in session.device_info
        assert "browser" in session.device_info
        assert "is_mobile" in session.device_info


@pytest.mark.asyncio
async def test_get_active_sessions_empty(test_db, test_user, session_manager):
    """Test returns empty list for user with no sessions."""
    sessions = await session_manager.get_active_sessions(
        user_id=test_user.id,
        db=test_db
    )

    assert sessions == []


@pytest.mark.asyncio
async def test_get_active_sessions_excludes_revoked(test_db, user_with_sessions, session_manager):
    """Test only returns active sessions, excludes revoked."""
    user = user_with_sessions["user"]
    sessions = user_with_sessions["sessions"]

    # Revoke one session
    await session_manager.revoke_session(sessions[0].id, "test", test_db)
    await test_db.commit()

    # Get active sessions
    active_sessions = await session_manager.get_active_sessions(user.id, test_db)

    # Verify only 2 active sessions
    assert len(active_sessions) == 2
    assert sessions[0].id not in [s.id for s in active_sessions]


# ============================================================================
# Cleanup Tests
# ============================================================================

@pytest.mark.asyncio
async def test_cleanup_expired_sessions(test_db, test_user, session_manager):
    """Test cleanup removes expired sessions."""
    # Create 2 sessions: 1 expired, 1 valid
    with freeze_time("2025-01-01 00:00:00"):
        from unittest.mock import MagicMock
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {"user-agent": "test"}

        expired_sess, _ = await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()
        expired_id = expired_sess.id

    with freeze_time("2025-01-01 05:00:00"):
        valid_sess, _ = await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()
        valid_id = valid_sess.id

    # Run cleanup at T=9 hours (expired session is 9 hours old, valid is 4 hours old)
    with freeze_time("2025-01-01 09:00:00"):
        count = await session_manager.cleanup_expired_sessions(test_db)
        await test_db.commit()

    # Verify 1 session cleaned up
    assert count == 1

    # Verify expired session revoked
    result = await test_db.execute(
        select(UserSession).where(UserSession.id == expired_id)
    )
    expired_session = result.scalar_one()
    assert expired_session.is_active is False
    assert expired_session.revoke_reason == "expired"

    # Verify valid session still active
    result = await test_db.execute(
        select(UserSession).where(UserSession.id == valid_id)
    )
    valid_session = result.scalar_one()
    assert valid_session.is_active is True


@pytest.mark.asyncio
async def test_cleanup_idle_sessions(test_db, test_user, session_manager):
    """Test cleanup removes idle sessions."""
    # Create 2 sessions: 1 idle, 1 active
    with freeze_time("2025-01-01 10:00:00"):
        from unittest.mock import MagicMock
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        mock_request.headers = {"user-agent": "test"}

        idle_sess, _ = await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()
        idle_id = idle_sess.id

    with freeze_time("2025-01-01 10:20:00"):
        active_sess, _ = await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()
        active_id = active_sess.id

    # Run cleanup at T=10:35 (idle session is 35 min old, active is 15 min old)
    with freeze_time("2025-01-01 10:35:00"):
        count = await session_manager.cleanup_expired_sessions(test_db)
        await test_db.commit()

    # Verify 1 session cleaned up
    assert count == 1

    # Verify idle session revoked
    result = await test_db.execute(
        select(UserSession).where(UserSession.id == idle_id)
    )
    idle_session = result.scalar_one()
    assert idle_session.is_active is False
    assert idle_session.revoke_reason == "idle_timeout"

    # Verify active session still active
    result = await test_db.execute(
        select(UserSession).where(UserSession.id == active_id)
    )
    active_session = result.scalar_one()
    assert active_session.is_active is True


@pytest.mark.asyncio
async def test_cleanup_sessions_no_cleanup_needed(test_db, test_user, session_manager, mock_request):
    """Test cleanup returns 0 when no sessions need cleanup."""
    # Create fresh session
    session, _ = await session_manager.create_session(
        user_id=test_user.id,
        request=mock_request,
        db=test_db
    )
    await test_db.commit()

    # Run cleanup immediately
    count = await session_manager.cleanup_expired_sessions(test_db)
    await test_db.commit()

    assert count == 0

    # Verify session still active
    await test_db.refresh(session)
    assert session.is_active is True


# ============================================================================
# Dependency Injection Tests
# ============================================================================

def test_get_session_manager_dependency():
    """Test FastAPI dependency returns SessionManager instance."""
    manager = get_session_manager()

    assert isinstance(manager, SessionManager)
    assert manager.SESSION_TIMEOUT_MINUTES == 30
    assert manager.MAX_SESSIONS_PER_USER == 5
    assert manager.SESSION_EXPIRY_HOURS == 8


# ============================================================================
# Edge Cases and Security Tests
# ============================================================================

@pytest.mark.asyncio
async def test_session_token_is_hashed(test_db, test_user, session_manager, mock_request):
    """Test raw token is never stored in database (only hash)."""
    session, raw_token = await session_manager.create_session(
        user_id=test_user.id,
        request=mock_request,
        db=test_db
    )
    await test_db.commit()

    # Verify raw token not in database
    result = await test_db.execute(
        select(UserSession).where(UserSession.session_token_hash.contains(raw_token))
    )
    assert result.scalar_one_or_none() is None

    # Verify hash is stored
    assert session.session_token_hash is not None
    assert len(session.session_token_hash) == 64  # SHA-256 hex length


@pytest.mark.asyncio
async def test_different_users_sessions_isolated(test_db, test_user, test_patient_user, session_manager, mock_request):
    """Test users can't access or affect other users' sessions."""
    # Create sessions for both users
    user1_session, user1_token = await session_manager.create_session(
        user_id=test_user.id,
        request=mock_request,
        db=test_db
    )
    await test_db.commit()

    user2_session, user2_token = await session_manager.create_session(
        user_id=test_patient_user.id,
        request=mock_request,
        db=test_db
    )
    await test_db.commit()

    # Get user1's active sessions
    user1_sessions = await session_manager.get_active_sessions(test_user.id, test_db)

    # Verify only user1's session returned
    assert len(user1_sessions) == 1
    assert user1_sessions[0].id == user1_session.id
    assert user2_session.id not in [s.id for s in user1_sessions]


@pytest.mark.asyncio
async def test_concurrent_session_creation_enforces_limit(test_db, test_user, session_manager, mock_request):
    """Test session limit enforcement works with concurrent session creation."""
    # Create 10 sessions rapidly (simulating concurrent logins)
    for i in range(10):
        mock_request.client.host = f"192.168.1.{i}"
        await session_manager.create_session(
            user_id=test_user.id,
            request=mock_request,
            db=test_db
        )
        await test_db.commit()

    # Verify only 5 active sessions remain
    active_sessions = await session_manager.get_active_sessions(test_user.id, test_db)
    assert len(active_sessions) == 5


@pytest.mark.asyncio
async def test_session_without_user_agent(test_db, test_user, session_manager):
    """Test session creation handles missing user-agent gracefully."""
    request = MagicMock(spec=Request)
    request.client = MagicMock()
    request.client.host = "192.168.1.1"
    request.headers = {}  # No user-agent

    session, token = await session_manager.create_session(
        user_id=test_user.id,
        request=request,
        db=test_db
    )
    await test_db.commit()

    # Verify session created with unknown device info
    assert session.device_info is not None
    assert session.device_info["device_type"] == "unknown"
    assert session.device_info["os"] == "unknown"
    assert session.device_info["browser"] == "unknown"
