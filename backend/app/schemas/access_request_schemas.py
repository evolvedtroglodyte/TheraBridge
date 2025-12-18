"""
Pydantic schemas for Patient Access Request API
"""
from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class AccessRequestType(str, Enum):
    """Types of access requests patients can make"""
    view_records = "view_records"  # Request to view their own records
    download_data = "download_data"  # Request data export
    correct_data = "correct_data"  # Request data correction
    delete_data = "delete_data"  # Request data deletion (right to be forgotten)
    restrict_processing = "restrict_processing"  # Request to restrict data processing
    data_portability = "data_portability"  # Request data in portable format


class AccessRequestStatus(str, Enum):
    """Status of an access request"""
    pending = "pending"
    under_review = "under_review"
    approved = "approved"
    denied = "denied"
    completed = "completed"
    cancelled = "cancelled"


class AccessRequestPriority(str, Enum):
    """Priority levels for access requests"""
    low = "low"
    normal = "normal"
    high = "high"
    urgent = "urgent"


# ============================================================================
# Access Request Creation Schemas
# ============================================================================

class AccessRequestCreate(BaseModel):
    """Request to create a patient access request"""
    request_type: AccessRequestType = Field(..., description="Type of access request")
    description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Detailed description of the request"
    )
    priority: AccessRequestPriority = Field(
        default=AccessRequestPriority.normal,
        description="Request priority"
    )
    specific_records: Optional[List[UUID]] = Field(
        None,
        description="Specific record IDs if requesting access to particular sessions/notes"
    )
    preferred_format: Optional[str] = Field(
        None,
        description="Preferred format for data export (pdf, csv, json)"
    )
    correction_details: Optional[str] = Field(
        None,
        description="Details about data to be corrected (for correct_data requests)"
    )

    @field_validator('preferred_format')
    @classmethod
    def validate_format_for_download(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure format is specified for download/portability requests"""
        request_type = info.data.get('request_type')
        if request_type in [AccessRequestType.download_data, AccessRequestType.data_portability]:
            if not v:
                raise ValueError(f'preferred_format is required for {request_type.value} requests')
            if v not in ['pdf', 'csv', 'json']:
                raise ValueError('preferred_format must be one of: pdf, csv, json')
        return v


class AccessRequestUpdate(BaseModel):
    """Update an existing access request (patient can add details)"""
    description: Optional[str] = Field(None, min_length=10, max_length=1000)
    priority: Optional[AccessRequestPriority] = Field(None)
    correction_details: Optional[str] = Field(None)


# ============================================================================
# Access Request Response Schemas
# ============================================================================

class AccessRequestResponse(BaseModel):
    """Complete access request data"""
    id: UUID = Field(..., description="Unique request identifier")
    patient_id: UUID = Field(..., description="Patient who made the request")
    therapist_id: Optional[UUID] = Field(None, description="Assigned therapist")

    request_type: AccessRequestType = Field(..., description="Type of access request")
    status: AccessRequestStatus = Field(..., description="Current request status")
    priority: AccessRequestPriority = Field(..., description="Request priority")

    description: str = Field(..., description="Detailed request description")
    specific_records: Optional[List[UUID]] = Field(None, description="Specific record IDs")
    preferred_format: Optional[str] = Field(None, description="Preferred data format")
    correction_details: Optional[str] = Field(None, description="Correction details")

    # Response from therapist/admin
    response_notes: Optional[str] = Field(None, description="Response from reviewer")
    denial_reason: Optional[str] = Field(None, description="Reason for denial (if denied)")

    # Fulfillment details
    download_url: Optional[str] = Field(None, description="Download URL for completed requests")
    download_expires_at: Optional[datetime] = Field(None, description="When download link expires")

    # Timestamps
    created_at: datetime = Field(..., description="When request was created")
    updated_at: datetime = Field(..., description="When request was last updated")
    reviewed_at: Optional[datetime] = Field(None, description="When request was reviewed")
    completed_at: Optional[datetime] = Field(None, description="When request was completed")

    # Reviewer information
    reviewed_by: Optional[UUID] = Field(None, description="User ID who reviewed the request")

    model_config = ConfigDict(from_attributes=True)


class AccessRequestListResponse(BaseModel):
    """List of access requests with pagination"""
    requests: List[AccessRequestResponse] = Field(..., description="List of access requests")
    total_count: int = Field(..., description="Total number of requests")
    pending_count: int = Field(..., description="Number of pending requests")
    completed_count: int = Field(..., description="Number of completed requests")


# ============================================================================
# Access Request Review Schemas (Therapist/Admin Actions)
# ============================================================================

class AccessRequestReview(BaseModel):
    """Therapist/admin review of an access request"""
    status: AccessRequestStatus = Field(..., description="New status (approved, denied, under_review)")
    response_notes: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Notes explaining the decision"
    )
    denial_reason: Optional[str] = Field(
        None,
        description="Required if status is denied"
    )

    @field_validator('denial_reason')
    @classmethod
    def validate_denial_reason(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure denial reason is provided when denying"""
        status = info.data.get('status')
        if status == AccessRequestStatus.denied and not v:
            raise ValueError('denial_reason is required when denying a request')
        return v


class AccessRequestApprovalResponse(BaseModel):
    """Response after approving an access request"""
    request_id: UUID = Field(..., description="Request identifier")
    status: AccessRequestStatus = Field(..., description="Updated status")
    message: str = Field(..., description="Success message")
    download_url: Optional[str] = Field(None, description="Download URL if data was prepared")
    download_expires_at: Optional[datetime] = Field(None, description="Download link expiration")


# ============================================================================
# Access Request Statistics
# ============================================================================

class AccessRequestStatistics(BaseModel):
    """Statistics about access requests"""
    total_requests: int = Field(..., description="Total number of requests")
    pending_requests: int = Field(..., description="Number of pending requests")
    approved_requests: int = Field(..., description="Number of approved requests")
    denied_requests: int = Field(..., description="Number of denied requests")
    completed_requests: int = Field(..., description="Number of completed requests")

    requests_by_type: dict = Field(..., description="Breakdown by request type")
    average_resolution_time_hours: Optional[float] = Field(None, description="Average time to resolve")
    oldest_pending_request_age_hours: Optional[float] = Field(None, description="Age of oldest pending request")


# ============================================================================
# Cancel Request Schema
# ============================================================================

class AccessRequestCancel(BaseModel):
    """Patient cancellation of their own request"""
    cancellation_reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional reason for cancellation"
    )
