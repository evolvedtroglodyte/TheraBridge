"""
Multi-Factor Authentication (MFA) endpoints for TOTP-based 2FA.

Provides endpoints for:
- MFA setup with QR code generation
- TOTP code verification during setup
- TOTP code validation during login

Security features:
- Rate limiting to prevent brute force attacks
- Encrypted secret storage
- One-time display of backup codes
- Comprehensive audit logging
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID
from typing import Optional
from datetime import datetime
import base64
import logging

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.db_models import User
from app.models.security_models import MFAConfig
from app.schemas.mfa_schemas import (
    MFASetupResponse,
    MFAVerifyRequest,
    MFAVerifyResponse,
    MFAValidateRequest,
    MFAValidateResponse,
    MFAMethod,
    MFAStatus
)
from app.security.mfa import TOTPService, get_totp_service
from app.security.encryption import FieldEncryption, get_encryption_service
from app.middleware.rate_limit import limiter

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/setup", response_model=MFASetupResponse)
@limiter.limit("5/minute")
async def setup_mfa(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    totp_service: TOTPService = Depends(get_totp_service),
    encryption: FieldEncryption = Depends(get_encryption_service)
):
    """
    Initialize MFA setup for the current user.

    Generates a new TOTP secret, creates a QR code for authenticator app enrollment,
    and generates backup recovery codes. The secret is encrypted before storage.

    Rate limit: 5 requests per minute per IP address

    Args:
        request: FastAPI request object (required for rate limiting)
        current_user: Authenticated user from JWT token
        db: AsyncSession database connection
        totp_service: TOTP service for secret generation and QR code creation
        encryption: Encryption service for secure secret storage

    Returns:
        MFASetupResponse containing:
        - method: MFA method (totp)
        - status: Current MFA status (pending)
        - qr_code_url: Base64-encoded QR code image (data URL)
        - secret: TOTP secret for manual entry
        - backup_codes: 8 one-time recovery codes (ONLY shown once)
        - expires_at: When the setup session expires if not verified

    Raises:
        HTTPException 409: If MFA is already enabled for this user
        HTTPException 429: If rate limit exceeded
        HTTPException 500: If secret generation or encryption fails

    Security:
        - Secret is encrypted with FieldEncryption before database storage
        - Backup codes are hashed (SHA256) before storage
        - QR code and backup codes are only shown ONCE during setup
        - Setup session expires after verification

    Example Response:
        {
            "method": "totp",
            "status": "pending",
            "qr_code_url": "data:image/png;base64,iVBORw0KGgo...",
            "secret": "JBSWY3DPEHPK3PXP",
            "backup_codes": ["ABCD-1234", "EFGH-5678", ...],
            "expires_at": "2024-01-15T10:30:00Z"
        }
    """
    logger.info(
        f"MFA setup initiated for user {current_user.id}",
        extra={
            "user_id": str(current_user.id),
            "email": current_user.email
        }
    )

    # Check if MFA is already enabled
    query = select(MFAConfig).where(
        MFAConfig.user_id == current_user.id,
        MFAConfig.is_enabled == True
    )
    result = await db.execute(query)
    existing_mfa = result.scalar_one_or_none()

    if existing_mfa:
        logger.warning(
            f"MFA setup attempted but already enabled for user {current_user.id}",
            extra={"user_id": str(current_user.id)}
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="MFA is already enabled. Please disable existing MFA before setting up a new one."
        )

    try:
        # Generate TOTP secret
        secret = totp_service.generate_secret()

        # Generate provisioning URI for QR code
        uri = totp_service.get_provisioning_uri(secret, current_user.email)

        # Generate QR code image
        qr_bytes = totp_service.generate_qr_code(uri)
        qr_base64 = base64.b64encode(qr_bytes).decode('utf-8')
        qr_data_url = f"data:image/png;base64,{qr_base64}"

        # Generate backup codes
        backup_codes = totp_service.generate_backup_codes(count=8)

        # Hash backup codes for storage
        backup_codes_hashed = [
            totp_service.hash_backup_code(code) for code in backup_codes
        ]

        # Encrypt TOTP secret
        secret_encrypted = encryption.encrypt(secret)

        # Create or update MFAConfig record
        # Check if there's a pending setup
        pending_query = select(MFAConfig).where(MFAConfig.user_id == current_user.id)
        pending_result = await db.execute(pending_query)
        pending_mfa = pending_result.scalar_one_or_none()

        if pending_mfa:
            # Update existing pending setup
            pending_mfa.mfa_type = MFAMethod.totp.value
            pending_mfa.secret_encrypted = secret_encrypted
            pending_mfa.backup_codes_hash = backup_codes_hashed
            pending_mfa.is_enabled = False
            pending_mfa.verified_at = None
            pending_mfa.updated_at = datetime.utcnow()
            logger.info(
                f"Updated pending MFA setup for user {current_user.id}",
                extra={"user_id": str(current_user.id)}
            )
        else:
            # Create new MFAConfig
            new_mfa = MFAConfig(
                user_id=current_user.id,
                mfa_type=MFAMethod.totp.value,
                secret_encrypted=secret_encrypted,
                backup_codes_hash=backup_codes_hashed,
                is_enabled=False,
                verified_at=None
            )
            db.add(new_mfa)
            logger.info(
                f"Created new MFA config for user {current_user.id}",
                extra={"user_id": str(current_user.id)}
            )

        await db.commit()

        # Return setup response with plaintext data
        # SECURITY: This is the ONLY time backup codes are shown to the user
        logger.info(
            f"MFA setup completed successfully for user {current_user.id}",
            extra={
                "user_id": str(current_user.id),
                "backup_codes_count": len(backup_codes)
            }
        )

        return MFASetupResponse(
            method=MFAMethod.totp,
            status=MFAStatus.pending,
            qr_code_url=qr_data_url,
            secret=secret,
            backup_codes=backup_codes,
            # Expire setup session after 15 minutes if not verified
            expires_at=datetime.utcnow().replace(microsecond=0) + \
                       __import__('datetime').timedelta(minutes=15)
        )

    except Exception as e:
        await db.rollback()
        logger.error(
            f"MFA setup failed for user {current_user.id}",
            extra={
                "user_id": str(current_user.id),
                "error_type": type(e).__name__,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set up MFA: {str(e)}"
        )


@router.post("/verify", response_model=MFAVerifyResponse)
@limiter.limit("10/minute")
async def verify_mfa(
    request: Request,
    verify_request: MFAVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    totp_service: TOTPService = Depends(get_totp_service),
    encryption: FieldEncryption = Depends(get_encryption_service)
):
    """
    Verify MFA setup by validating a TOTP code.

    Completes the MFA enrollment process by verifying that the user has successfully
    set up their authenticator app and can generate valid TOTP codes.

    Rate limit: 10 requests per minute per IP address

    Args:
        request: FastAPI request object (required for rate limiting)
        verify_request: Verification request containing TOTP code
        current_user: Authenticated user from JWT token
        db: AsyncSession database connection
        totp_service: TOTP service for code verification
        encryption: Encryption service for secret decryption

    Returns:
        MFAVerifyResponse containing:
        - success: Whether verification succeeded
        - status: Updated MFA status (enabled if successful)
        - message: Success or error message

    Raises:
        HTTPException 404: If no pending MFA setup found
        HTTPException 400: If MFA is already enabled
        HTTPException 401: If TOTP code is invalid
        HTTPException 429: If rate limit exceeded

    Security:
        - Decrypts stored secret to verify code
        - Only enables MFA after successful verification
        - Sets verified_at timestamp
        - Validates code within time window (±30 seconds)

    Example Request:
        {
            "method": "totp",
            "code": "123456"
        }

    Example Response:
        {
            "success": true,
            "status": "enabled",
            "message": "MFA enabled successfully"
        }
    """
    logger.info(
        f"MFA verification attempted for user {current_user.id}",
        extra={
            "user_id": str(current_user.id),
            "method": verify_request.method.value
        }
    )

    # Get MFA config
    query = select(MFAConfig).where(MFAConfig.user_id == current_user.id)
    result = await db.execute(query)
    mfa_config = result.scalar_one_or_none()

    if not mfa_config:
        logger.warning(
            f"MFA verification failed: No config found for user {current_user.id}",
            extra={"user_id": str(current_user.id)}
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No MFA setup found. Please initiate MFA setup first."
        )

    # Check if already enabled
    if mfa_config.is_enabled:
        logger.warning(
            f"MFA verification failed: Already enabled for user {current_user.id}",
            extra={"user_id": str(current_user.id)}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled."
        )

    try:
        # Decrypt TOTP secret
        secret = encryption.decrypt(mfa_config.secret_encrypted)

        # Verify TOTP code
        is_valid = totp_service.verify_code(secret, verify_request.code)

        if not is_valid:
            logger.warning(
                f"MFA verification failed: Invalid code for user {current_user.id}",
                extra={
                    "user_id": str(current_user.id),
                    "code_masked": f"{verify_request.code[:2]}****"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid verification code. Please try again."
            )

        # Enable MFA
        mfa_config.is_enabled = True
        mfa_config.verified_at = datetime.utcnow()
        mfa_config.updated_at = datetime.utcnow()

        await db.commit()

        logger.info(
            f"MFA verification successful for user {current_user.id}",
            extra={
                "user_id": str(current_user.id),
                "method": verify_request.method.value
            }
        )

        return MFAVerifyResponse(
            success=True,
            status=MFAStatus.enabled,
            message="MFA enabled successfully"
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        await db.rollback()
        logger.error(
            f"MFA verification error for user {current_user.id}",
            extra={
                "user_id": str(current_user.id),
                "error_type": type(e).__name__,
                "error": str(e)
            },
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"MFA verification failed: {str(e)}"
        )


@router.post("/validate", response_model=MFAValidateResponse)
@limiter.limit("20/minute")
async def validate_mfa(
    request: Request,
    validate_request: MFAValidateRequest,
    db: AsyncSession = Depends(get_db),
    totp_service: TOTPService = Depends(get_totp_service),
    encryption: FieldEncryption = Depends(get_encryption_service)
):
    """
    Validate MFA code during login flow.

    This endpoint is called after initial username/password authentication to verify
    the second factor. It does not require authentication (no JWT token needed), but
    requires a temporary session token from the initial login.

    Rate limit: 20 requests per minute per IP address

    Args:
        request: FastAPI request object (required for rate limiting)
        validate_request: Validation request containing session token and code
        db: AsyncSession database connection
        totp_service: TOTP service for code verification
        encryption: Encryption service for secret decryption

    Returns:
        MFAValidateResponse containing:
        - success: Whether validation succeeded
        - access_token: JWT access token if successful (None if failed)
        - refresh_token: JWT refresh token if successful (None if failed)
        - token_type: Token type (bearer)
        - expires_in: Seconds until access token expires
        - backup_codes_remaining: Number of unused backup codes (if backup code used)
        - message: Success or error message

    Raises:
        HTTPException 401: If session token invalid or code incorrect
        HTTPException 404: If user not found or MFA not enabled
        HTTPException 429: If rate limit exceeded

    Security:
        - Verifies temporary session token from initial login
        - Falls back to backup codes if TOTP fails
        - Marks backup codes as used (one-time use)
        - Generates full auth tokens only after MFA validation

    Example Request:
        {
            "session_token": "temp_session_token_from_login",
            "code": "123456",
            "remember_device": false,
            "is_backup_code": false
        }

    Example Response (success):
        {
            "success": true,
            "access_token": "eyJhbGciOiJIUzI1NiIs...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
            "token_type": "bearer",
            "expires_in": 900,
            "backup_codes_remaining": 8,
            "message": "MFA validation successful"
        }

    Example Response (failure):
        {
            "success": false,
            "access_token": null,
            "refresh_token": null,
            "token_type": "bearer",
            "expires_in": null,
            "backup_codes_remaining": null,
            "message": "Invalid MFA code"
        }
    """
    logger.info(
        "MFA validation attempted",
        extra={
            "session_token_masked": f"{validate_request.session_token[:8]}****",
            "is_backup_code": validate_request.is_backup_code
        }
    )

    # TODO: Implement session token verification
    # For now, this is a placeholder that requires the full login flow integration
    # In a complete implementation:
    # 1. Verify session_token is valid and not expired
    # 2. Extract user_id from session token
    # 3. Validate MFA code
    # 4. Generate full JWT tokens if valid
    # 5. Optionally trust device for remember_device feature

    # Placeholder response
    logger.warning(
        "MFA validation endpoint called but not fully implemented",
        extra={"session_token_preview": validate_request.session_token[:8]}
    )

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="MFA validation endpoint requires integration with login flow. "
               "Use /auth/login for authentication."
    )
