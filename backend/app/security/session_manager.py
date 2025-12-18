"""
Session management service for HIPAA-compliant session lifecycle management.

Implements:
- Session creation with secure token generation and hashing
- Session validation with timeout and expiry checks
- Device fingerprinting and tracking
- Session limit enforcement (max 5 concurrent sessions per user)
- Idle timeout (30 minutes) and absolute expiration (8 hours)
- Session revocation with audit trail

Security features:
- Tokens hashed with SHA-256 before storage (only hash is stored)
- Automatic cleanup of expired/idle sessions
- Device and IP tracking for security monitoring
- Concurrent session limits to prevent session hijacking
"""
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
import secrets
import hashlib
import logging
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc
from user_agents import parse as parse_user_agent

from app.models.security_models import UserSession

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages user session lifecycle including creation, validation, timeout, and limits.

    Constants:
        SESSION_TIMEOUT_MINUTES: Idle timeout after which sessions are invalidated (30 minutes)
        MAX_SESSIONS_PER_USER: Maximum concurrent sessions per user (5 sessions)
        SESSION_EXPIRY_HOURS: Absolute expiration time for sessions (8 hours)
    """

    # Session configuration constants
    SESSION_TIMEOUT_MINUTES = 30  # Idle timeout
    MAX_SESSIONS_PER_USER = 5  # Concurrent session limit
    SESSION_EXPIRY_HOURS = 8  # Absolute expiration

    @staticmethod
    def _hash_token(token: str) -> str:
        """
        Hash a session token using SHA-256.

        Args:
            token: The raw session token

        Returns:
            Hexadecimal string representation of the SHA-256 hash
        """
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    @staticmethod
    def _extract_device_info(request: Request) -> dict:
        """
        Extract and parse device information from request headers.

        Args:
            request: FastAPI Request object

        Returns:
            Dictionary containing device_type, os, browser, and is_mobile
        """
        user_agent_string = request.headers.get("user-agent", "")

        if not user_agent_string:
            return {
                "device_type": "unknown",
                "os": "unknown",
                "browser": "unknown",
                "is_mobile": False
            }

        try:
            ua = parse_user_agent(user_agent_string)

            # Determine device type
            if ua.is_mobile:
                device_type = "mobile"
            elif ua.is_tablet:
                device_type = "tablet"
            elif ua.is_pc:
                device_type = "desktop"
            elif ua.is_bot:
                device_type = "bot"
            else:
                device_type = "unknown"

            return {
                "device_type": device_type,
                "os": f"{ua.os.family} {ua.os.version_string}",
                "browser": f"{ua.browser.family} {ua.browser.version_string}",
                "is_mobile": ua.is_mobile
            }
        except Exception as e:
            logger.warning(f"Failed to parse user agent: {e}")
            return {
                "device_type": "unknown",
                "os": "unknown",
                "browser": "unknown",
                "is_mobile": False,
                "parse_error": str(e)
            }

    @staticmethod
    def is_session_idle(session: UserSession) -> bool:
        """
        Check if a session has exceeded the idle timeout.

        Args:
            session: UserSession object to check

        Returns:
            True if session is idle (last activity > SESSION_TIMEOUT_MINUTES), False otherwise
        """
        idle_threshold = datetime.utcnow() - timedelta(minutes=SessionManager.SESSION_TIMEOUT_MINUTES)
        return session.last_activity_at < idle_threshold

    async def create_session(
        self,
        user_id: UUID,
        request: Request,
        db: AsyncSession
    ) -> tuple[UserSession, str]:
        """
        Create a new user session with secure token generation and device tracking.

        Enforces session limit by revoking oldest sessions if MAX_SESSIONS_PER_USER is exceeded.

        Args:
            user_id: UUID of the user
            request: FastAPI Request object for extracting IP and device info
            db: Async database session

        Returns:
            Tuple of (UserSession object, raw session token)
            Note: Raw token is only returned once and never stored
        """
        # Generate secure random token (256 bits of entropy)
        raw_token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(raw_token)

        # Extract request metadata
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        device_info = self._extract_device_info(request)

        # Calculate expiration times
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.SESSION_EXPIRY_HOURS)

        # Enforce session limit before creating new session
        await self.enforce_session_limit(user_id, db)

        # Create new session
        session = UserSession(
            user_id=user_id,
            session_token_hash=token_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            device_info=device_info,
            is_active=True,
            last_activity_at=now,
            expires_at=expires_at,
            created_at=now
        )

        db.add(session)
        await db.flush()  # Flush to get session ID without committing

        logger.info(
            f"Created session {session.id} for user {user_id} "
            f"from {ip_address} (device: {device_info.get('device_type')})"
        )

        return session, raw_token

    async def validate_session(
        self,
        token: str,
        db: AsyncSession
    ) -> Optional[UserSession]:
        """
        Validate a session token and update last activity if valid.

        Checks:
        - Token exists and is active
        - Session has not expired (absolute expiration)
        - Session has not exceeded idle timeout

        Args:
            token: Raw session token
            db: Async database session

        Returns:
            UserSession object if valid, None if invalid/expired/idle
        """
        token_hash = self._hash_token(token)

        # Look up session by hashed token
        result = await db.execute(
            select(UserSession).where(
                and_(
                    UserSession.session_token_hash == token_hash,
                    UserSession.is_active == True
                )
            )
        )
        session = result.scalar_one_or_none()

        if not session:
            logger.debug("Session not found or inactive")
            return None

        now = datetime.utcnow()

        # Check absolute expiration
        if now > session.expires_at:
            logger.info(f"Session {session.id} expired (absolute expiration)")
            await self.revoke_session(session.id, "expired", db)
            return None

        # Check idle timeout
        if self.is_session_idle(session):
            logger.info(f"Session {session.id} idle timeout")
            await self.revoke_session(session.id, "idle_timeout", db)
            return None

        # Session is valid - update last activity
        session.last_activity_at = now
        await db.flush()

        logger.debug(f"Session {session.id} validated and activity updated")
        return session

    async def revoke_session(
        self,
        session_id: UUID,
        reason: str,
        db: AsyncSession
    ) -> None:
        """
        Revoke a session by marking it as inactive.

        Args:
            session_id: UUID of the session to revoke
            reason: Reason for revocation (e.g., "expired", "idle_timeout", "user_logout", "admin_revoke")
            db: Async database session
        """
        result = await db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        session = result.scalar_one_or_none()

        if session:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            session.revoke_reason = reason
            await db.flush()

            logger.info(f"Revoked session {session_id} for user {session.user_id} (reason: {reason})")
        else:
            logger.warning(f"Attempted to revoke non-existent session {session_id}")

    async def revoke_all_sessions(
        self,
        user_id: UUID,
        except_token: Optional[str],
        db: AsyncSession
    ) -> int:
        """
        Revoke all sessions for a user except the current session (if provided).

        Useful for:
        - Password changes (revoke all sessions)
        - Security incidents (revoke all sessions)
        - User-initiated "sign out everywhere" action

        Args:
            user_id: UUID of the user
            except_token: Raw token of the current session to preserve (optional)
            db: Async database session

        Returns:
            Number of sessions revoked
        """
        # Build query to get all active sessions
        query = select(UserSession).where(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True
            )
        )

        # If except_token is provided, exclude that session
        if except_token:
            except_token_hash = self._hash_token(except_token)
            query = query.where(UserSession.session_token_hash != except_token_hash)

        result = await db.execute(query)
        sessions = result.scalars().all()

        # Revoke each session
        count = 0
        for session in sessions:
            session.is_active = False
            session.revoked_at = datetime.utcnow()
            session.revoke_reason = "revoke_all_sessions"
            count += 1

        if count > 0:
            await db.flush()
            logger.info(f"Revoked {count} sessions for user {user_id}")

        return count

    async def get_active_sessions(
        self,
        user_id: UUID,
        db: AsyncSession
    ) -> List[UserSession]:
        """
        Get all active sessions for a user, ordered by last activity (most recent first).

        Args:
            user_id: UUID of the user
            db: Async database session

        Returns:
            List of active UserSession objects
        """
        result = await db.execute(
            select(UserSession)
            .where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
            .order_by(desc(UserSession.last_activity_at))
        )
        return list(result.scalars().all())

    async def enforce_session_limit(
        self,
        user_id: UUID,
        db: AsyncSession
    ) -> None:
        """
        Enforce the maximum session limit per user.

        If the user has MAX_SESSIONS_PER_USER or more active sessions,
        revokes the oldest sessions (by creation date) to make room for new session.

        Args:
            user_id: UUID of the user
            db: Async database session
        """
        # Get count of active sessions
        result = await db.execute(
            select(func.count(UserSession.id))
            .where(
                and_(
                    UserSession.user_id == user_id,
                    UserSession.is_active == True
                )
            )
        )
        session_count = result.scalar()

        if session_count >= self.MAX_SESSIONS_PER_USER:
            # Get oldest sessions that need to be revoked
            sessions_to_revoke = session_count - self.MAX_SESSIONS_PER_USER + 1

            result = await db.execute(
                select(UserSession)
                .where(
                    and_(
                        UserSession.user_id == user_id,
                        UserSession.is_active == True
                    )
                )
                .order_by(UserSession.created_at.asc())
                .limit(sessions_to_revoke)
            )
            oldest_sessions = result.scalars().all()

            # Revoke oldest sessions
            for session in oldest_sessions:
                await self.revoke_session(session.id, "session_limit_exceeded", db)

            logger.info(
                f"Enforced session limit for user {user_id}: "
                f"revoked {sessions_to_revoke} oldest sessions"
            )

    async def cleanup_expired_sessions(
        self,
        db: AsyncSession
    ) -> int:
        """
        Clean up expired and idle sessions across all users.

        This should be run periodically (e.g., via scheduled task) to:
        - Revoke sessions past absolute expiration
        - Revoke sessions past idle timeout

        Args:
            db: Async database session

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        idle_threshold = now - timedelta(minutes=self.SESSION_TIMEOUT_MINUTES)

        # Find sessions that are expired or idle
        result = await db.execute(
            select(UserSession)
            .where(
                and_(
                    UserSession.is_active == True,
                    (
                        (UserSession.expires_at < now) |  # Expired
                        (UserSession.last_activity_at < idle_threshold)  # Idle
                    )
                )
            )
        )
        expired_sessions = result.scalars().all()

        # Revoke each expired session
        count = 0
        for session in expired_sessions:
            if session.expires_at < now:
                reason = "expired"
            else:
                reason = "idle_timeout"

            await self.revoke_session(session.id, reason, db)
            count += 1

        if count > 0:
            logger.info(f"Cleaned up {count} expired/idle sessions")

        return count


# FastAPI dependency for dependency injection
def get_session_manager() -> SessionManager:
    """
    FastAPI dependency that provides a SessionManager instance.

    Usage:
        @app.post("/login")
        async def login(
            db: AsyncSession = Depends(get_db),
            session_mgr: SessionManager = Depends(get_session_manager)
        ):
            session, token = await session_mgr.create_session(user_id, request, db)
            return {"session_token": token}
    """
    return SessionManager()
