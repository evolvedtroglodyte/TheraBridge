"""
Pydantic schemas for Audit Log API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class AuditEventType(str, Enum):
    """Types of auditable events"""
    # Authentication events
    user_login = "user_login"
    user_logout = "user_logout"
    user_signup = "user_signup"
    password_change = "password_change"
    password_reset = "password_reset"
    mfa_enabled = "mfa_enabled"
    mfa_disabled = "mfa_disabled"

    # Data access events
    record_view = "record_view"
    record_create = "record_create"
    record_update = "record_update"
    record_delete = "record_delete"
    export_data = "export_data"

    # Session events
    session_create = "session_create"
    session_update = "session_update"
    session_delete = "session_delete"

    # Security events
    failed_login = "failed_login"
    suspicious_activity = "suspicious_activity"
    access_denied = "access_denied"

    # Administrative events
    user_created = "user_created"
    user_updated = "user_updated"
    user_deleted = "user_deleted"
    role_changed = "role_changed"

    # Consent events
    consent_granted = "consent_granted"
    consent_revoked = "consent_revoked"

    # Emergency access events
    emergency_access_requested = "emergency_access_requested"
    emergency_access_granted = "emergency_access_granted"
    emergency_access_denied = "emergency_access_denied"


class AuditSeverity(str, Enum):
    """Severity levels for audit events"""
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AuditOutcome(str, Enum):
    """Outcome of the audited action"""
    success = "success"
    failure = "failure"
    partial = "partial"


# ============================================================================
# Audit Log Query Schemas
# ============================================================================

class AuditLogQuery(BaseModel):
    """Query parameters for filtering audit logs"""
    user_id: Optional[UUID] = Field(None, description="Filter by user who performed action")
    patient_id: Optional[UUID] = Field(None, description="Filter by affected patient")
    event_type: Optional[AuditEventType] = Field(None, description="Filter by event type")
    severity: Optional[AuditSeverity] = Field(None, description="Filter by severity level")
    outcome: Optional[AuditOutcome] = Field(None, description="Filter by outcome")
    start_date: Optional[datetime] = Field(None, description="Filter events after this date")
    end_date: Optional[datetime] = Field(None, description="Filter events before this date")
    ip_address: Optional[str] = Field(None, description="Filter by IP address")
    resource_type: Optional[str] = Field(None, description="Filter by resource type (session, note, patient, etc.)")
    resource_id: Optional[UUID] = Field(None, description="Filter by specific resource ID")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of records to return")
    offset: int = Field(default=0, ge=0, description="Number of records to skip")
    order_by: str = Field(default="timestamp_desc", description="Sort order: timestamp_asc or timestamp_desc")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Ensure end_date is after start_date"""
        start_date = info.data.get('start_date')
        if v and start_date and v < start_date:
            raise ValueError('end_date must be after start_date')
        return v


# ============================================================================
# Audit Log Response Schemas
# ============================================================================

class AuditLogEntry(BaseModel):
    """A single audit log entry"""
    id: UUID = Field(..., description="Unique audit log entry ID")
    event_type: AuditEventType = Field(..., description="Type of event")
    severity: AuditSeverity = Field(..., description="Event severity")
    outcome: AuditOutcome = Field(..., description="Action outcome")
    timestamp: datetime = Field(..., description="When the event occurred")

    # Actor information
    user_id: Optional[UUID] = Field(None, description="User who performed the action")
    user_email: Optional[str] = Field(None, description="Email of user who performed the action")
    user_role: Optional[str] = Field(None, description="Role of user who performed the action")

    # Target information
    patient_id: Optional[UUID] = Field(None, description="Affected patient (if applicable)")
    resource_type: Optional[str] = Field(None, description="Type of resource accessed")
    resource_id: Optional[UUID] = Field(None, description="ID of resource accessed")

    # Request metadata
    ip_address: Optional[str] = Field(None, description="IP address of request")
    user_agent: Optional[str] = Field(None, description="User agent of request")
    session_id: Optional[UUID] = Field(None, description="Session ID")

    # Event details
    description: str = Field(..., description="Human-readable event description")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional event-specific data")

    # Changes (for update events)
    changes: Optional[Dict[str, Any]] = Field(None, description="What changed (before/after values)")

    model_config = ConfigDict(from_attributes=True)


class AuditLogResponse(BaseModel):
    """Paginated audit log response"""
    entries: List[AuditLogEntry] = Field(..., description="List of audit log entries")
    total_count: int = Field(..., description="Total number of matching entries")
    limit: int = Field(..., description="Number of entries per page")
    offset: int = Field(..., description="Current offset")
    has_more: bool = Field(..., description="Whether more entries are available")


# ============================================================================
# Audit Statistics Schemas
# ============================================================================

class AuditEventCount(BaseModel):
    """Count of events by type"""
    event_type: AuditEventType = Field(..., description="Event type")
    count: int = Field(..., description="Number of occurrences")


class AuditStatisticsResponse(BaseModel):
    """Audit log statistics for a time period"""
    period_start: datetime = Field(..., description="Start of analysis period")
    period_end: datetime = Field(..., description="End of analysis period")
    total_events: int = Field(..., description="Total number of events")

    # Event breakdown
    events_by_type: List[AuditEventCount] = Field(..., description="Events grouped by type")
    events_by_severity: Dict[str, int] = Field(..., description="Events grouped by severity")
    events_by_outcome: Dict[str, int] = Field(..., description="Events grouped by outcome")

    # Top actors
    top_users: List[Dict[str, Any]] = Field(..., description="Most active users in period")

    # Security metrics
    failed_login_count: int = Field(..., description="Number of failed login attempts")
    suspicious_activity_count: int = Field(..., description="Number of suspicious activities")
    access_denied_count: int = Field(..., description="Number of access denials")

    # Data access metrics
    unique_patients_accessed: int = Field(..., description="Number of unique patients accessed")
    records_created: int = Field(..., description="Number of records created")
    records_updated: int = Field(..., description="Number of records updated")
    records_deleted: int = Field(..., description="Number of records deleted")


# ============================================================================
# Export Schemas
# ============================================================================

class AuditExportRequest(BaseModel):
    """Request to export audit logs"""
    query: AuditLogQuery = Field(..., description="Query parameters for export")
    format: str = Field(default="csv", description="Export format: csv, json, or pdf")
    include_metadata: bool = Field(default=True, description="Whether to include metadata fields")


class AuditExportResponse(BaseModel):
    """Response after initiating audit export"""
    export_id: UUID = Field(..., description="Unique export job ID")
    status: str = Field(..., description="Export status: pending, processing, completed, failed")
    download_url: Optional[str] = Field(None, description="Download URL (available when completed)")
    expires_at: Optional[datetime] = Field(None, description="When download link expires")
    total_records: int = Field(..., description="Number of records in export")
    created_at: datetime = Field(..., description="When export was requested")
