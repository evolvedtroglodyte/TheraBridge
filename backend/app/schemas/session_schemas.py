"""
Pydantic schemas for Session Management API (Authentication Sessions)
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class SessionStatus(str, Enum):
    """Authentication session status"""
    active = "active"
    expired = "expired"
    revoked = "revoked"


class SessionTerminationReason(str, Enum):
    """Reasons for session termination"""
    user_logout = "user_logout"
    user_revoked = "user_revoked"
    admin_revoked = "admin_revoked"
    timeout = "timeout"
    security_event = "security_event"
    password_changed = "password_changed"
    mfa_enabled = "mfa_enabled"


# ============================================================================
# Session Response Schemas
# ============================================================================

class AuthSessionResponse(BaseModel):
    """Information about an authentication session"""
    id: UUID = Field(..., description="Unique session identifier")
    user_id: UUID = Field(..., description="User who owns this session")
    status: SessionStatus = Field(..., description="Current session status")
    created_at: datetime = Field(..., description="When session was created")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    expires_at: datetime = Field(..., description="When session expires")
    ip_address: Optional[str] = Field(None, description="IP address of session")
    user_agent: Optional[str] = Field(None, description="Browser/app user agent")
    device_name: Optional[str] = Field(None, description="Device name/description")
    is_current: bool = Field(default=False, description="Whether this is the current session")
    is_mfa_verified: bool = Field(default=False, description="Whether MFA was completed for this session")

    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    """List of all active sessions for a user"""
    sessions: List[AuthSessionResponse] = Field(..., description="List of authentication sessions")
    total_count: int = Field(..., description="Total number of sessions")
    active_count: int = Field(..., description="Number of active sessions")


# ============================================================================
# Session Management Schemas
# ============================================================================

class SessionRevokeRequest(BaseModel):
    """Request to revoke a specific session"""
    session_id: UUID = Field(..., description="Session ID to revoke")
    reason: SessionTerminationReason = Field(
        default=SessionTerminationReason.user_revoked,
        description="Reason for revocation"
    )


class SessionRevokeResponse(BaseModel):
    """Response after revoking a session"""
    success: bool = Field(..., description="Whether revocation succeeded")
    session_id: UUID = Field(..., description="Revoked session ID")
    message: str = Field(..., description="Success or error message")


class SessionRevokeAllRequest(BaseModel):
    """Request to revoke all other sessions (keep current)"""
    exclude_current: bool = Field(
        default=True,
        description="Whether to exclude current session from revocation"
    )
    reason: SessionTerminationReason = Field(
        default=SessionTerminationReason.user_revoked,
        description="Reason for revocation"
    )
    password: str = Field(..., description="User password for confirmation")


class SessionRevokeAllResponse(BaseModel):
    """Response after revoking all sessions"""
    success: bool = Field(..., description="Whether revocation succeeded")
    sessions_revoked: int = Field(..., description="Number of sessions revoked")
    sessions_remaining: int = Field(..., description="Number of sessions still active")
    message: str = Field(..., description="Success or error message")


# ============================================================================
# Session Activity Schemas
# ============================================================================

class SessionActivityEvent(BaseModel):
    """A single session activity event"""
    event_type: str = Field(..., description="Type of activity (login, api_call, page_view, etc.)")
    timestamp: datetime = Field(..., description="When the event occurred")
    ip_address: Optional[str] = Field(None, description="IP address of the request")
    user_agent: Optional[str] = Field(None, description="User agent of the request")
    endpoint: Optional[str] = Field(None, description="API endpoint accessed")
    status_code: Optional[int] = Field(None, description="HTTP status code")
    metadata: Optional[dict] = Field(None, description="Additional event metadata")

    model_config = ConfigDict(from_attributes=True)


class SessionActivityResponse(BaseModel):
    """Activity log for a specific session"""
    session_id: UUID = Field(..., description="Session identifier")
    events: List[SessionActivityEvent] = Field(..., description="List of activity events")
    total_events: int = Field(..., description="Total number of events")
    first_activity: datetime = Field(..., description="Timestamp of first activity")
    last_activity: datetime = Field(..., description="Timestamp of last activity")


# ============================================================================
# Session Security Schemas
# ============================================================================

class SessionSecurityAlert(BaseModel):
    """Security alert related to a session"""
    alert_type: str = Field(..., description="Type of alert (suspicious_location, unusual_device, etc.)")
    severity: str = Field(..., description="Alert severity (low, medium, high, critical)")
    message: str = Field(..., description="Human-readable alert message")
    detected_at: datetime = Field(..., description="When the alert was detected")
    resolved: bool = Field(default=False, description="Whether the alert has been resolved")


class SessionSecurityResponse(BaseModel):
    """Security information for a session"""
    session_id: UUID = Field(..., description="Session identifier")
    security_score: float = Field(..., ge=0.0, le=1.0, description="Security score (0.0-1.0)")
    risk_level: str = Field(..., description="Risk level (low, medium, high)")
    alerts: List[SessionSecurityAlert] = Field(default_factory=list, description="Active security alerts")
    ip_matches_previous: bool = Field(..., description="Whether IP matches previous sessions")
    location_matches_previous: bool = Field(..., description="Whether location matches previous sessions")
    device_matches_previous: bool = Field(..., description="Whether device matches previous sessions")


# ============================================================================
# Session Refresh Schemas
# ============================================================================

class SessionRefreshRequest(BaseModel):
    """Request to refresh session/extend expiration"""
    refresh_token: str = Field(..., description="Valid refresh token")


class SessionRefreshResponse(BaseModel):
    """Response after refreshing session"""
    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Seconds until access token expires")
    session_id: UUID = Field(..., description="Session identifier")
