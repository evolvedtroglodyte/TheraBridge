"""
Pydantic schemas for Multi-Factor Authentication (MFA) API
"""
from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class MFAMethod(str, Enum):
    """Multi-factor authentication methods"""
    totp = "totp"  # Time-based One-Time Password (Google Authenticator, Authy)
    sms = "sms"    # SMS-based verification
    email = "email"  # Email-based verification


class MFAStatus(str, Enum):
    """MFA setup status for a user"""
    disabled = "disabled"
    pending = "pending"  # Setup initiated but not verified
    enabled = "enabled"


# ============================================================================
# MFA Setup Schemas
# ============================================================================

class MFASetupRequest(BaseModel):
    """Request to initiate MFA setup"""
    method: MFAMethod = Field(..., description="MFA method to set up (totp, sms, email)")
    phone_number: Optional[str] = Field(None, description="Required for SMS method")

    @field_validator('phone_number')
    @classmethod
    def validate_phone_for_sms(cls, v: Optional[str], info) -> Optional[str]:
        """Ensure phone number is provided for SMS method"""
        if info.data.get('method') == MFAMethod.sms and not v:
            raise ValueError('Phone number is required for SMS method')
        return v


class MFASetupResponse(BaseModel):
    """Response after initiating MFA setup"""
    method: MFAMethod = Field(..., description="MFA method being set up")
    status: MFAStatus = Field(..., description="Current MFA status")
    qr_code_url: Optional[str] = Field(None, description="QR code data URL for TOTP setup (base64)")
    secret: Optional[str] = Field(None, description="TOTP secret key (for manual entry)")
    backup_codes: List[str] = Field(default_factory=list, description="One-time backup codes (8 codes)")
    expires_at: datetime = Field(..., description="When the setup session expires if not verified")

    @field_validator('backup_codes')
    @classmethod
    def validate_backup_codes_count(cls, v: List[str]) -> List[str]:
        """Ensure exactly 8 backup codes are generated"""
        if len(v) != 8:
            raise ValueError('Must generate exactly 8 backup codes')
        return v


# ============================================================================
# MFA Verification Schemas
# ============================================================================

class MFAVerifyRequest(BaseModel):
    """Request to verify MFA setup (complete enrollment)"""
    method: MFAMethod = Field(..., description="MFA method being verified")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")

    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Ensure code is 6 digits"""
        if not v.isdigit():
            raise ValueError('Verification code must be 6 digits')
        return v


class MFAVerifyResponse(BaseModel):
    """Response after verifying MFA setup"""
    success: bool = Field(..., description="Whether verification succeeded")
    status: MFAStatus = Field(..., description="Updated MFA status")
    message: str = Field(..., description="Success or error message")


# ============================================================================
# MFA Login Validation Schemas
# ============================================================================

class MFAValidateRequest(BaseModel):
    """Request to validate MFA code during login"""
    session_token: str = Field(..., description="Temporary session token from initial login")
    code: str = Field(..., min_length=6, max_length=6, description="6-digit MFA code")
    remember_device: bool = Field(default=False, description="Remember this device for 30 days")
    is_backup_code: bool = Field(default=False, description="Whether this is a backup code")

    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Ensure code is 6 digits or 8 characters for backup codes"""
        if not v.isalnum():
            raise ValueError('Code must contain only letters and numbers')
        return v


class MFAValidateResponse(BaseModel):
    """Response after validating MFA code during login"""
    success: bool = Field(..., description="Whether MFA validation succeeded")
    access_token: Optional[str] = Field(None, description="JWT access token if successful")
    refresh_token: Optional[str] = Field(None, description="JWT refresh token if successful")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Seconds until access token expires")
    backup_codes_remaining: Optional[int] = Field(None, description="Number of unused backup codes")
    message: str = Field(..., description="Success or error message")


# ============================================================================
# MFA Status and Management Schemas
# ============================================================================

class MFAStatusResponse(BaseModel):
    """Current MFA configuration for a user"""
    enabled: bool = Field(..., description="Whether MFA is currently enabled")
    method: Optional[MFAMethod] = Field(None, description="Active MFA method (null if disabled)")
    backup_codes_remaining: int = Field(..., description="Number of unused backup codes")
    trusted_devices: int = Field(..., description="Number of trusted devices")
    enrolled_at: Optional[datetime] = Field(None, description="When MFA was first enabled")

    model_config = ConfigDict(from_attributes=True)


class MFADisableRequest(BaseModel):
    """Request to disable MFA"""
    password: str = Field(..., description="User password for confirmation")
    code: Optional[str] = Field(None, description="Current MFA code (if MFA is enabled)")


class MFARegenerateBackupCodesRequest(BaseModel):
    """Request to regenerate backup codes"""
    password: str = Field(..., description="User password for confirmation")


class MFARegenerateBackupCodesResponse(BaseModel):
    """Response with new backup codes"""
    backup_codes: List[str] = Field(..., description="New one-time backup codes (8 codes)")
    previous_codes_invalidated: bool = Field(True, description="Whether old codes were invalidated")

    @field_validator('backup_codes')
    @classmethod
    def validate_backup_codes_count(cls, v: List[str]) -> List[str]:
        """Ensure exactly 8 backup codes are generated"""
        if len(v) != 8:
            raise ValueError('Must generate exactly 8 backup codes')
        return v


# ============================================================================
# Trusted Device Management
# ============================================================================

class TrustedDeviceResponse(BaseModel):
    """Information about a trusted device"""
    id: UUID = Field(..., description="Unique device identifier")
    device_name: str = Field(..., description="Device name/description")
    device_fingerprint: str = Field(..., description="Hashed device fingerprint")
    last_used: datetime = Field(..., description="When device was last used")
    created_at: datetime = Field(..., description="When device was first trusted")
    ip_address: Optional[str] = Field(None, description="Last known IP address")
    user_agent: Optional[str] = Field(None, description="Browser/app user agent")

    model_config = ConfigDict(from_attributes=True)


class TrustedDeviceRevokeRequest(BaseModel):
    """Request to revoke a trusted device"""
    device_id: UUID = Field(..., description="Device ID to revoke")
    password: str = Field(..., description="User password for confirmation")
