"""
Pydantic schemas for Emergency Access API
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class EmergencyAccessStatus(str, Enum):
    """Status of an emergency access request"""
    requested = "requested"
    approved = "approved"
    denied = "denied"
    expired = "expired"
    revoked = "revoked"


class EmergencyAccessReason(str, Enum):
    """Valid reasons for emergency access"""
    patient_crisis = "patient_crisis"  # Patient in crisis/danger
    medical_emergency = "medical_emergency"  # Medical emergency
    legal_request = "legal_request"  # Court order or legal requirement
    patient_incapacitated = "patient_incapacitated"  # Patient unable to provide consent
    covering_therapist = "covering_therapist"  # Covering for another therapist
    other = "other"  # Other emergency (requires detailed justification)


class EmergencyAccessLevel(str, Enum):
    """Level of access granted in emergency"""
    read_only = "read_only"  # Can only view records
    read_write = "read_write"  # Can view and update records
    full_access = "full_access"  # Full access including deletion (rarely granted)


# ============================================================================
# Emergency Access Request Schemas
# ============================================================================

class EmergencyAccessRequest(BaseModel):
    """Request emergency access to patient records"""
    patient_id: UUID = Field(..., description="Patient whose records need access")
    reason: EmergencyAccessReason = Field(..., description="Reason for emergency access")
    justification: str = Field(
        ...,
        min_length=50,
        max_length=2000,
        description="Detailed justification for emergency access (minimum 50 characters)"
    )
    access_level: EmergencyAccessLevel = Field(
        default=EmergencyAccessLevel.read_only,
        description="Level of access requested"
    )
    duration_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="How long access is needed (1-168 hours, default 24)"
    )
    contact_phone: str = Field(..., description="Emergency contact phone number")
    supervisor_id: Optional[UUID] = Field(None, description="Supervisor to notify about this request")

    @field_validator('justification')
    @classmethod
    def validate_justification_for_other(cls, v: str, info) -> str:
        """Require detailed justification for 'other' reason"""
        reason = info.data.get('reason')
        if reason == EmergencyAccessReason.other and len(v.strip()) < 100:
            raise ValueError('Justification for "other" reason must be at least 100 characters')
        return v


class EmergencyAccessResponse(BaseModel):
    """Emergency access request data"""
    id: UUID = Field(..., description="Unique request identifier")
    patient_id: UUID = Field(..., description="Patient whose records are accessed")
    requesting_user_id: UUID = Field(..., description="User requesting access")
    requesting_user_email: str = Field(..., description="Email of requesting user")
    requesting_user_role: str = Field(..., description="Role of requesting user")

    reason: EmergencyAccessReason = Field(..., description="Reason for request")
    justification: str = Field(..., description="Detailed justification")
    access_level: EmergencyAccessLevel = Field(..., description="Level of access")

    status: EmergencyAccessStatus = Field(..., description="Current request status")

    # Timing
    requested_at: datetime = Field(..., description="When request was made")
    duration_hours: int = Field(..., description="Requested duration")
    expires_at: Optional[datetime] = Field(None, description="When access expires (if approved)")

    # Review details
    reviewed_by: Optional[UUID] = Field(None, description="Admin who reviewed (if reviewed)")
    reviewed_at: Optional[datetime] = Field(None, description="When request was reviewed")
    approval_notes: Optional[str] = Field(None, description="Notes from reviewer")
    denial_reason: Optional[str] = Field(None, description="Reason for denial (if denied)")

    # Contact info
    contact_phone: str = Field(..., description="Emergency contact number")
    supervisor_id: Optional[UUID] = Field(None, description="Notified supervisor")

    # Activity tracking
    access_count: int = Field(default=0, description="Number of times records were accessed")
    last_accessed_at: Optional[datetime] = Field(None, description="When records were last accessed")

    model_config = ConfigDict(from_attributes=True)


class EmergencyAccessListResponse(BaseModel):
    """List of emergency access requests"""
    requests: List[EmergencyAccessResponse] = Field(..., description="List of requests")
    total_count: int = Field(..., description="Total number of requests")
    active_count: int = Field(..., description="Number of currently active accesses")
    pending_count: int = Field(..., description="Number of pending requests")


# ============================================================================
# Emergency Access Review Schemas (Admin Actions)
# ============================================================================

class EmergencyAccessReview(BaseModel):
    """Admin review of emergency access request"""
    status: EmergencyAccessStatus = Field(
        ...,
        description="Approved or denied (only valid values for review)"
    )
    approval_notes: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Notes explaining the decision"
    )
    denial_reason: Optional[str] = Field(
        None,
        description="Required if denying the request"
    )
    adjusted_duration_hours: Optional[int] = Field(
        None,
        ge=1,
        le=168,
        description="Override requested duration (if approving)"
    )
    adjusted_access_level: Optional[EmergencyAccessLevel] = Field(
        None,
        description="Override requested access level (if approving)"
    )

    @field_validator('status')
    @classmethod
    def validate_review_status(cls, v: EmergencyAccessStatus) -> EmergencyAccessStatus:
        """Only approved or denied are valid for review"""
        if v not in [EmergencyAccessStatus.approved, EmergencyAccessStatus.denied]:
            raise ValueError('Review status must be approved or denied')
        return v

    @field_validator('denial_reason')
    @classmethod
    def validate_denial_reason(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure denial reason is provided when denying"""
        status = info.data.get('status')
        if status == EmergencyAccessStatus.denied and not v:
            raise ValueError('denial_reason is required when denying a request')
        return v


class EmergencyAccessApprovalResponse(BaseModel):
    """Response after approving/denying emergency access"""
    request_id: UUID = Field(..., description="Request identifier")
    status: EmergencyAccessStatus = Field(..., description="Updated status")
    message: str = Field(..., description="Success message")
    expires_at: Optional[datetime] = Field(None, description="When access expires (if approved)")
    access_level: Optional[EmergencyAccessLevel] = Field(None, description="Granted access level")


# ============================================================================
# Emergency Access Revocation Schemas
# ============================================================================

class EmergencyAccessRevoke(BaseModel):
    """Revoke active emergency access"""
    revocation_reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for revoking access"
    )
    notify_user: bool = Field(
        default=True,
        description="Whether to notify the user about revocation"
    )


class EmergencyAccessRevokeResponse(BaseModel):
    """Response after revoking emergency access"""
    request_id: UUID = Field(..., description="Request identifier")
    status: EmergencyAccessStatus = Field(..., description="Updated status (revoked)")
    message: str = Field(..., description="Success message")
    revoked_at: datetime = Field(..., description="When access was revoked")


# ============================================================================
# Emergency Access Activity Log
# ============================================================================

class EmergencyAccessActivity(BaseModel):
    """Activity log entry for emergency access usage"""
    id: UUID = Field(..., description="Unique activity entry ID")
    emergency_access_id: UUID = Field(..., description="Emergency access request ID")
    activity_type: str = Field(..., description="Type of activity (view, update, export, etc.)")
    resource_type: str = Field(..., description="Type of resource accessed")
    resource_id: UUID = Field(..., description="ID of resource accessed")
    timestamp: datetime = Field(..., description="When activity occurred")
    ip_address: Optional[str] = Field(None, description="IP address of access")
    details: Optional[str] = Field(None, description="Additional activity details")

    model_config = ConfigDict(from_attributes=True)


class EmergencyAccessActivityResponse(BaseModel):
    """Activity log for a specific emergency access"""
    emergency_access_id: UUID = Field(..., description="Emergency access request ID")
    activities: List[EmergencyAccessActivity] = Field(..., description="List of activities")
    total_activities: int = Field(..., description="Total number of activities")
    first_access: Optional[datetime] = Field(None, description="First access timestamp")
    last_access: Optional[datetime] = Field(None, description="Last access timestamp")


# ============================================================================
# Emergency Access Statistics
# ============================================================================

class EmergencyAccessStatistics(BaseModel):
    """Statistics about emergency access usage"""
    total_requests: int = Field(..., description="Total number of requests")
    approved_requests: int = Field(..., description="Number of approved requests")
    denied_requests: int = Field(..., description="Number of denied requests")
    active_accesses: int = Field(..., description="Currently active emergency accesses")
    expired_accesses: int = Field(..., description="Number of expired accesses")

    requests_by_reason: dict = Field(..., description="Breakdown by reason")
    average_duration_hours: Optional[float] = Field(None, description="Average access duration")
    average_approval_time_minutes: Optional[float] = Field(None, description="Average time to approve")
