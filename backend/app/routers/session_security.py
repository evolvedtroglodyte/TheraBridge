"""
Session security router for managing active authentication sessions.

Provides endpoints for users to:
- View all active sessions across devices
- Revoke individual sessions
- Sign out everywhere (revoke all sessions)

HIPAA Compliance:
- Session management for access control
- Audit trail for session revocation
- Device tracking for security monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.db_models import User
from app.schemas.session_schemas import (
    SessionListResponse,
    SessionRevokeResponse,
    SessionRevokeAllRequest,
    SessionRevokeAllResponse,
    AuthSessionResponse
)
from app.security.session_manager import SessionManager, get_session_manager
from app.middleware.rate_limit import limiter

router = APIRouter()
security = HTTPBearer()


async def get_current_session_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract the current session token from Authorization header.

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        Raw session token string
    """
    return credentials.credentials


@router.get("/sessions", response_model=SessionListResponse)
@limiter.limit("30/minute")
async def get_active_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    current_token: str = Depends(get_current_session_token),
    session_mgr: SessionManager = Depends(get_session_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active sessions for the current user.

    Returns a list of all active authentication sessions across all devices,
    including session metadata like device info, IP address, and last activity.
    The current session (matching the request token) is marked with is_current=True.

    Auth:
        Requires valid authentication token

    Rate Limit:
        30 requests per minute per IP address

    Args:
        request: FastAPI request object (for rate limiting)
        current_user: Authenticated user (injected by get_current_user dependency)
        current_token: Current session token from Authorization header
        session_mgr: SessionManager instance
        db: AsyncSession database dependency

    Returns:
        SessionListResponse: List of active sessions with metadata

    Response includes:
        - sessions: List of AuthSessionResponse objects
        - total_count: Total number of sessions
        - active_count: Number of active sessions
        - Each session includes: id, status, created_at, last_activity, expires_at,
          ip_address, user_agent, device_name, is_current, is_mfa_verified

    Raises:
        HTTPException 401: If authentication token is invalid
        HTTPException 429: Rate limit exceeded

    Example:
        GET /api/v1/auth/sessions
        Authorization: Bearer <token>

        Response:
        {
            "sessions": [
                {
                    "id": "uuid",
                    "user_id": "uuid",
                    "status": "active",
                    "created_at": "2025-01-15T10:00:00Z",
                    "last_activity": "2025-01-15T14:30:00Z",
                    "expires_at": "2025-01-15T18:00:00Z",
                    "ip_address": "192.168.1.1",
                    "user_agent": "Mozilla/5.0...",
                    "device_name": "Chrome on macOS",
                    "is_current": true,
                    "is_mfa_verified": true
                }
            ],
            "total_count": 3,
            "active_count": 3
        }
    """
    # Get all active sessions for the user
    sessions = await session_mgr.get_active_sessions(current_user.id, db)

    # Hash the current token to match against stored sessions
    current_token_hash = session_mgr._hash_token(current_token)

    # Convert to response schema and mark current session
    session_responses: List[AuthSessionResponse] = []
    for session in sessions:
        # Determine if this is the current session
        is_current = (session.session_token_hash == current_token_hash)

        # Extract device name from device_info JSON
        device_name = None
        if session.device_info:
            browser = session.device_info.get('browser', 'Unknown Browser')
            os = session.device_info.get('os', 'Unknown OS')
            device_name = f"{browser} on {os}"

        session_response = AuthSessionResponse(
            id=session.id,
            user_id=session.user_id,
            status="active" if session.is_active else "revoked",
            created_at=session.created_at,
            last_activity=session.last_activity_at,
            expires_at=session.expires_at,
            ip_address=session.ip_address,
            user_agent=session.user_agent,
            device_name=device_name,
            is_current=is_current,
            is_mfa_verified=False  # TODO: Implement MFA verification tracking
        )
        session_responses.append(session_response)

    return SessionListResponse(
        sessions=session_responses,
        total_count=len(session_responses),
        active_count=len([s for s in session_responses if s.status == "active"])
    )


@router.delete("/sessions/{session_id}", response_model=SessionRevokeResponse)
@limiter.limit("20/minute")
async def revoke_session(
    request: Request,
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    session_mgr: SessionManager = Depends(get_session_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke a specific session by ID.

    Allows users to remotely sign out from a specific device or session.
    Validates that the session belongs to the current user before revoking.

    Auth:
        Requires valid authentication token
        Session must belong to the authenticated user

    Rate Limit:
        20 requests per minute per IP address

    Args:
        request: FastAPI request object (for rate limiting)
        session_id: UUID of the session to revoke
        current_user: Authenticated user (injected by get_current_user dependency)
        session_mgr: SessionManager instance
        db: AsyncSession database dependency

    Returns:
        SessionRevokeResponse: Result of revocation operation

    Response includes:
        - success: Whether revocation succeeded
        - session_id: UUID of the revoked session
        - message: Success or error message

    Raises:
        HTTPException 401: If authentication token is invalid
        HTTPException 403: If session does not belong to current user
        HTTPException 404: If session not found
        HTTPException 429: Rate limit exceeded

    Example:
        DELETE /api/v1/auth/sessions/{session_id}
        Authorization: Bearer <token>

        Response:
        {
            "success": true,
            "session_id": "uuid",
            "message": "Session revoked successfully"
        }
    """
    # Fetch the session to verify ownership
    all_sessions = await session_mgr.get_active_sessions(current_user.id, db)

    # Find the target session
    target_session = None
    for session in all_sessions:
        if session.id == session_id:
            target_session = session
            break

    if not target_session:
        # Check if session exists but belongs to another user
        from app.models.security_models import UserSession
        from sqlalchemy import select

        result = await db.execute(
            select(UserSession).where(UserSession.id == session_id)
        )
        exists = result.scalar_one_or_none()

        if exists:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Session does not belong to current user"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )

    # Revoke the session
    await session_mgr.revoke_session(session_id, "user_revoked", db)
    await db.commit()

    return SessionRevokeResponse(
        success=True,
        session_id=session_id,
        message="Session revoked successfully"
    )


@router.post("/sessions/revoke-all", response_model=SessionRevokeAllResponse)
@limiter.limit("10/minute")
async def revoke_all_sessions(
    request: Request,
    revoke_request: SessionRevokeAllRequest,
    current_user: User = Depends(get_current_user),
    current_token: str = Depends(get_current_session_token),
    session_mgr: SessionManager = Depends(get_session_manager),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke all sessions for the current user (sign out everywhere).

    Allows users to invalidate all active sessions across all devices,
    optionally excluding the current session. Useful for security purposes
    when a user suspects unauthorized access or wants to force re-authentication
    on all devices.

    Requires password confirmation for security.

    Auth:
        Requires valid authentication token
        Requires correct password in request body

    Rate Limit:
        10 requests per minute per IP address

    Args:
        request: FastAPI request object (for rate limiting)
        revoke_request: Request body containing exclude_current flag, reason, and password
        current_user: Authenticated user (injected by get_current_user dependency)
        current_token: Current session token from Authorization header
        session_mgr: SessionManager instance
        db: AsyncSession database dependency

    Returns:
        SessionRevokeAllResponse: Result of revocation operation

    Response includes:
        - success: Whether revocation succeeded
        - sessions_revoked: Number of sessions that were revoked
        - sessions_remaining: Number of sessions still active (0 or 1)
        - message: Success or error message

    Raises:
        HTTPException 401: If authentication token is invalid or password incorrect
        HTTPException 429: Rate limit exceeded

    Request body:
        {
            "exclude_current": true,
            "reason": "user_revoked",
            "password": "user_password"
        }

    Example:
        POST /api/v1/auth/sessions/revoke-all
        Authorization: Bearer <token>
        {
            "exclude_current": true,
            "reason": "user_revoked",
            "password": "mypassword123"
        }

        Response:
        {
            "success": true,
            "sessions_revoked": 4,
            "sessions_remaining": 1,
            "message": "Successfully revoked 4 sessions. Current session preserved."
        }
    """
    # Verify password for security
    from app.auth.utils import verify_password

    if not verify_password(revoke_request.password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    # Get count of sessions before revocation
    sessions_before = await session_mgr.get_active_sessions(current_user.id, db)
    total_before = len(sessions_before)

    # Revoke all sessions (optionally excluding current)
    except_token = current_token if revoke_request.exclude_current else None
    revoked_count = await session_mgr.revoke_all_sessions(
        current_user.id,
        except_token,
        db
    )
    await db.commit()

    # Calculate remaining sessions
    sessions_remaining = total_before - revoked_count

    # Generate success message
    if revoke_request.exclude_current and sessions_remaining > 0:
        message = f"Successfully revoked {revoked_count} sessions. Current session preserved."
    else:
        message = f"Successfully revoked all {revoked_count} sessions."

    return SessionRevokeAllResponse(
        success=True,
        sessions_revoked=revoked_count,
        sessions_remaining=sessions_remaining,
        message=message
    )
