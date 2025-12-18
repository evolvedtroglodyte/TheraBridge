"""
Pydantic schemas for Consent Management API
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class ConsentType(str, Enum):
    """Types of consent that can be recorded"""
    treatment = "treatment"  # Consent to treatment
    data_processing = "data_processing"  # Consent to process data
    data_sharing = "data_sharing"  # Consent to share data with third parties
    communication = "communication"  # Consent to communicate via email/SMS
    recording = "recording"  # Consent to record sessions
    research = "research"  # Consent to use anonymized data for research
    telehealth = "telehealth"  # Consent to telehealth services
    billing = "billing"  # Consent for billing/insurance


class ConsentStatus(str, Enum):
    """Current status of consent"""
    granted = "granted"
    revoked = "revoked"
    expired = "expired"
    pending = "pending"  # Requested but not yet given


class ConsentMethod(str, Enum):
    """Method by which consent was obtained"""
    electronic = "electronic"  # E-signature
    written = "written"  # Physical signature
    verbal = "verbal"  # Verbal consent (documented)
    implied = "implied"  # Implied consent (documented)


# ============================================================================
# Consent Record Creation Schemas
# ============================================================================

class ConsentRecordCreate(BaseModel):
    """Create a new consent record"""
    patient_id: UUID = Field(..., description="Patient providing consent")
    consent_type: ConsentType = Field(..., description="Type of consent")
    consent_status: ConsentStatus = Field(
        default=ConsentStatus.granted,
        description="Status of consent (default: granted)"
    )
    consent_method: ConsentMethod = Field(..., description="How consent was obtained")

    # Consent details
    consent_text: str = Field(
        ...,
        min_length=50,
        description="Full text of consent agreement shown to patient"
    )
    version: str = Field(
        default="1.0",
        description="Version of consent form (e.g., '1.0', '2.0')"
    )

    # Signature details (for electronic/written consent)
    signature_data: Optional[str] = Field(
        None,
        description="Base64 encoded signature image or e-signature token"
    )
    signed_at: Optional[datetime] = Field(
        None,
        description="When consent was signed (defaults to now)"
    )
    ip_address: Optional[str] = Field(
        None,
        description="IP address for electronic consent"
    )

    # Expiration
    expires_at: Optional[datetime] = Field(
        None,
        description="When consent expires (null for no expiration)"
    )

    # Witness information (for certain consent types)
    witness_name: Optional[str] = Field(None, description="Name of witness (if applicable)")
    witness_signature: Optional[str] = Field(None, description="Witness signature data")

    # Additional context
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Additional notes about consent"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata (e.g., form_id, document_url)"
    )

    @field_validator('signature_data')
    @classmethod
    def validate_signature_for_electronic(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure signature is provided for electronic/written consent"""
        method = info.data.get('consent_method')
        if method in [ConsentMethod.electronic, ConsentMethod.written] and not v:
            raise ValueError(f'signature_data is required for {method.value} consent')
        return v


class ConsentRecordUpdate(BaseModel):
    """Update an existing consent record (mainly for revocation)"""
    consent_status: ConsentStatus = Field(..., description="New consent status")
    revocation_reason: Optional[str] = Field(
        None,
        description="Required if status is revoked"
    )
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('revocation_reason')
    @classmethod
    def validate_revocation_reason(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure revocation reason is provided when revoking"""
        status = info.data.get('consent_status')
        if status == ConsentStatus.revoked and not v:
            raise ValueError('revocation_reason is required when revoking consent')
        return v


# ============================================================================
# Consent Record Response Schemas
# ============================================================================

class ConsentRecordResponse(BaseModel):
    """Complete consent record data"""
    id: UUID = Field(..., description="Unique consent record identifier")
    patient_id: UUID = Field(..., description="Patient who provided consent")
    consent_type: ConsentType = Field(..., description="Type of consent")
    consent_status: ConsentStatus = Field(..., description="Current status")
    consent_method: ConsentMethod = Field(..., description="How consent was obtained")

    # Consent details
    consent_text: str = Field(..., description="Full consent agreement text")
    version: str = Field(..., description="Version of consent form")

    # Signature details
    signature_data: Optional[str] = Field(None, description="Signature data")
    signed_at: Optional[datetime] = Field(None, description="When signed")
    ip_address: Optional[str] = Field(None, description="IP address for electronic consent")

    # Timing
    created_at: datetime = Field(..., description="When consent was recorded")
    updated_at: datetime = Field(..., description="Last update time")
    expires_at: Optional[datetime] = Field(None, description="When consent expires")

    # Revocation
    revoked_at: Optional[datetime] = Field(None, description="When consent was revoked")
    revocation_reason: Optional[str] = Field(None, description="Reason for revocation")

    # Witness
    witness_name: Optional[str] = Field(None, description="Name of witness")
    witness_signature: Optional[str] = Field(None, description="Witness signature data")

    # Additional context
    notes: Optional[str] = Field(None, description="Additional notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    # Audit
    created_by: UUID = Field(..., description="User who recorded consent")

    model_config = ConfigDict(from_attributes=True)


class ConsentRecordListResponse(BaseModel):
    """List of consent records for a patient"""
    consents: List[ConsentRecordResponse] = Field(..., description="List of consent records")
    total_count: int = Field(..., description="Total number of consents")
    active_count: int = Field(..., description="Number of active consents")
    expired_count: int = Field(..., description="Number of expired consents")
    revoked_count: int = Field(..., description="Number of revoked consents")


# ============================================================================
# Consent Status Check Schemas
# ============================================================================

class ConsentStatusCheck(BaseModel):
    """Check if patient has valid consent for specific type"""
    consent_type: ConsentType = Field(..., description="Type of consent to check")


class ConsentStatusCheckResponse(BaseModel):
    """Response indicating if consent is valid"""
    consent_type: ConsentType = Field(..., description="Type of consent checked")
    has_valid_consent: bool = Field(..., description="Whether valid consent exists")
    consent_status: Optional[ConsentStatus] = Field(None, description="Status of most recent consent")
    granted_at: Optional[datetime] = Field(None, description="When consent was granted")
    expires_at: Optional[datetime] = Field(None, description="When consent expires")
    days_until_expiration: Optional[int] = Field(None, description="Days until expiration (null if no expiration)")
    latest_consent_id: Optional[UUID] = Field(None, description="ID of most recent consent record")


# ============================================================================
# Consent Template Schemas
# ============================================================================

class ConsentTemplate(BaseModel):
    """Template for consent forms"""
    consent_type: ConsentType = Field(..., description="Type of consent")
    version: str = Field(..., description="Template version")
    title: str = Field(..., description="Consent form title")
    consent_text: str = Field(..., description="Full consent agreement text")
    requires_witness: bool = Field(default=False, description="Whether witness is required")
    default_expiration_days: Optional[int] = Field(None, description="Default expiration period")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional template metadata")


class ConsentTemplateResponse(BaseModel):
    """Consent template data"""
    id: UUID = Field(..., description="Unique template identifier")
    consent_type: ConsentType = Field(..., description="Type of consent")
    version: str = Field(..., description="Template version")
    title: str = Field(..., description="Consent form title")
    consent_text: str = Field(..., description="Full consent agreement text")
    requires_witness: bool = Field(..., description="Whether witness is required")
    default_expiration_days: Optional[int] = Field(None, description="Default expiration period")
    is_active: bool = Field(default=True, description="Whether template is currently active")
    created_at: datetime = Field(..., description="When template was created")
    updated_at: datetime = Field(..., description="Last update time")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Consent Revocation Schemas
# ============================================================================

class ConsentRevoke(BaseModel):
    """Revoke a specific consent"""
    revocation_reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for revoking consent"
    )
    revocation_method: ConsentMethod = Field(
        default=ConsentMethod.electronic,
        description="How revocation was documented"
    )


class ConsentRevokeResponse(BaseModel):
    """Response after revoking consent"""
    consent_id: UUID = Field(..., description="Consent record identifier")
    consent_type: ConsentType = Field(..., description="Type of consent revoked")
    status: ConsentStatus = Field(..., description="Updated status (revoked)")
    revoked_at: datetime = Field(..., description="When consent was revoked")
    message: str = Field(..., description="Success message")


# ============================================================================
# Consent Statistics
# ============================================================================

class ConsentStatistics(BaseModel):
    """Statistics about consent records"""
    total_consents: int = Field(..., description="Total number of consent records")
    active_consents: int = Field(..., description="Number of active consents")
    expired_consents: int = Field(..., description="Number of expired consents")
    revoked_consents: int = Field(..., description="Number of revoked consents")

    consents_by_type: Dict[str, int] = Field(..., description="Breakdown by consent type")
    consents_by_method: Dict[str, int] = Field(..., description="Breakdown by consent method")

    expiring_soon_count: int = Field(..., description="Consents expiring in next 30 days")
    missing_required_consents: List[ConsentType] = Field(
        default_factory=list,
        description="Required consent types not yet obtained"
    )
