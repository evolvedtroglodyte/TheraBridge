"""
Consent Management Endpoints for HIPAA Compliance Feature 8

Provides API endpoints for recording and querying patient consent:
- POST /api/v1/consent - Record new consent
- GET /api/v1/patients/{patient_id}/consents - Get patient consent history
- GET /api/v1/patients/{patient_id}/consent/status - Get consent status summary

All endpoints require authentication and enforce proper authorization.
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from typing import Optional
import logging

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.db_models import User, TherapistPatient
from app.models.schemas import UserRole
from app.schemas.consent_schemas import (
    ConsentRecordCreate,
    ConsentRecordResponse,
    ConsentRecordListResponse,
    ConsentType
)
from app.security.consent import ConsentService, get_consent_service
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/consent", tags=["consent"])


async def verify_patient_access(
    patient_id: UUID,
    current_user: User,
    db: AsyncSession
) -> None:
    """
    Verify that current user has access to patient's consent data.

    Authorization rules:
    - Admin: Can access any patient
    - Therapist: Can access assigned patients only
    - Patient: Can access own data only

    Args:
        patient_id: UUID of patient to access
        current_user: Current authenticated user
        db: Database session

    Raises:
        HTTPException 403: If user doesn't have access to this patient
        HTTPException 404: If patient not found
    """
    # Verify patient exists
    patient_query = select(User).where(
        and_(
            User.id == patient_id,
            User.role == UserRole.patient.value
        )
    )
    patient_result = await db.execute(patient_query)
    patient = patient_result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Patient {patient_id} not found"
        )

    # Authorization checks
    if current_user.role == UserRole.admin:
        # Admins can access any patient
        return

    elif current_user.role == UserRole.patient:
        # Patients can only access their own data
        if current_user.id != patient_id:
            logger.warning(
                f"Patient {current_user.id} attempted to access consent data "
                f"for patient {patient_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this patient's consent data"
            )

    elif current_user.role == UserRole.therapist:
        # Therapists can only access assigned patients
        assignment_query = select(TherapistPatient).where(
            and_(
                TherapistPatient.therapist_id == current_user.id,
                TherapistPatient.patient_id == patient_id,
                TherapistPatient.is_active == True
            )
        )
        assignment_result = await db.execute(assignment_query)
        assignment = assignment_result.scalar_one_or_none()

        if not assignment:
            logger.warning(
                f"Therapist {current_user.id} attempted to access consent data "
                f"for unassigned patient {patient_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to access this patient's consent data"
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role"
        )


@router.post("", response_model=ConsentRecordResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
async def record_consent(
    request: Request,
    consent_data: ConsentRecordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    consent_service: ConsentService = Depends(get_consent_service)
) -> ConsentRecordResponse:
    """
    Record a new patient consent.

    Creates a consent record for treatment, HIPAA notice, telehealth, recording,
    data sharing, or research. Supports electronic signature capture and tracks
    IP address for audit purposes.

    Rate Limit:
        - 20 consents per minute per IP address
        - Prevents abuse while allowing legitimate consent workflows

    Authorization:
        - Admin/Therapist: Can record consent for any patient
        - Patient: Can only record consent for themselves

    Consent Types:
        - treatment: Consent to treatment
        - hipaa_notice: HIPAA notice acknowledgment
        - telehealth: Telehealth service consent
        - recording: Session recording consent
        - data_sharing: Data sharing consent
        - research: Research participation consent

    Args:
        request: FastAPI request (for IP address extraction)
        consent_data: ConsentRecordCreate schema with consent details
        db: AsyncSession database dependency
        current_user: Authenticated user from JWT token
        consent_service: ConsentService dependency

    Returns:
        ConsentRecordResponse: Created consent record

    Raises:
        HTTPException 400: Invalid consent data
        HTTPException 403: Not authorized to record consent for this patient
        HTTPException 404: Patient not found
        HTTPException 429: Rate limit exceeded

    Example:
        POST /api/v1/consent
        {
            "patient_id": "123e4567-e89b-12d3-a456-426614174000",
            "consent_type": "telehealth",
            "consented": true,
            "consent_text": "I consent to receive telehealth services...",
            "signature_data": "data:image/png;base64,iVBORw0KGgo...",
            "version": "2.1"
        }
    """
    logger.info(
        f"Recording consent: user={current_user.id}, patient={consent_data.patient_id}, "
        f"type={consent_data.consent_type}"
    )

    # Authorization check: Patient can only record own consent
    # Therapist/Admin can record consent for any patient
    if current_user.role == UserRole.patient:
        if current_user.id != consent_data.patient_id:
            logger.warning(
                f"Patient {current_user.id} attempted to record consent "
                f"for patient {consent_data.patient_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Patients can only record their own consent"
            )

    # Verify patient exists (for therapist/admin creating consent)
    await verify_patient_access(consent_data.patient_id, current_user, db)

    # Extract IP address from request
    ip_address = request.client.host if request.client else "unknown"

    # Record consent using service
    consent_record = await consent_service.record_consent(
        patient_id=consent_data.patient_id,
        consent_type=consent_data.consent_type.value,
        consented=consent_data.consent_status.value == "granted",
        consent_text=consent_data.consent_text,
        signature_data=consent_data.signature_data,
        ip_address=ip_address,
        version=consent_data.version,
        expires_at=consent_data.expires_at,
        db=db
    )

    logger.info(f"Consent recorded successfully: {consent_record.id}")

    # Convert to response schema
    return ConsentRecordResponse(
        id=consent_record.id,
        patient_id=consent_record.patient_id,
        consent_type=ConsentType(consent_record.consent_type),
        consent_status=consent_data.consent_status,
        consent_method=consent_data.consent_method,
        consent_text=consent_record.consent_text,
        version=consent_record.version,
        signature_data=consent_record.signature_data,
        signed_at=consent_data.signed_at or consent_record.consented_at,
        ip_address=consent_record.ip_address,
        created_at=consent_record.created_at,
        updated_at=consent_record.created_at,
        expires_at=consent_record.expires_at,
        revoked_at=consent_record.revoked_at,
        revocation_reason=None,
        witness_name=consent_data.witness_name,
        witness_signature=consent_data.witness_signature,
        notes=consent_data.notes,
        metadata=consent_data.metadata,
        created_by=current_user.id
    )


@router.get("/patients/{patient_id}/consents", response_model=ConsentRecordListResponse)
@limiter.limit("30/minute")
async def get_patient_consents(
    request: Request,
    patient_id: UUID,
    consent_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    consent_service: ConsentService = Depends(get_consent_service)
) -> ConsentRecordListResponse:
    """
    Get all consent records for a patient.

    Retrieves complete consent history for a patient, optionally filtered by
    consent type. Results are ordered by creation date (newest first).

    Rate Limit:
        - 30 requests per minute per IP address
        - Allows reasonable consent verification frequency

    Authorization:
        - Admin: Can access any patient's consents
        - Therapist: Can access assigned patients only
        - Patient: Can access own consents only

    Query Parameters:
        - consent_type: Optional filter (treatment, hipaa_notice, telehealth, etc.)

    Args:
        request: FastAPI request (for rate limiting)
        patient_id: UUID of patient to get consents for
        consent_type: Optional consent type filter
        db: AsyncSession database dependency
        current_user: Authenticated user from JWT token
        consent_service: ConsentService dependency

    Returns:
        ConsentRecordListResponse: List of consent records with summary stats

    Raises:
        HTTPException 403: Not authorized to access this patient's consents
        HTTPException 404: Patient not found
        HTTPException 429: Rate limit exceeded

    Example:
        GET /api/v1/consent/patients/{patient_id}/consents?consent_type=telehealth
    """
    logger.info(
        f"Fetching consents: user={current_user.id}, patient={patient_id}, "
        f"type={consent_type}"
    )

    # Authorization check
    await verify_patient_access(patient_id, current_user, db)

    # Validate consent_type if provided
    if consent_type:
        try:
            ConsentType(consent_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid consent_type: {consent_type}. Must be one of: "
                       f"{', '.join([ct.value for ct in ConsentType])}"
            )

    # Fetch consents from service
    consents = await consent_service.get_patient_consents(
        patient_id=patient_id,
        consent_type=consent_type,
        db=db
    )

    # Calculate summary statistics
    total_count = len(consents)
    active_count = sum(
        1 for c in consents
        if c.consented and not c.revoked_at and (not c.expires_at or c.expires_at > c.created_at)
    )
    expired_count = sum(
        1 for c in consents
        if c.expires_at and c.expires_at <= c.created_at and not c.revoked_at
    )
    revoked_count = sum(1 for c in consents if c.revoked_at)

    logger.info(
        f"Consent summary: total={total_count}, active={active_count}, "
        f"expired={expired_count}, revoked={revoked_count}"
    )

    # Convert to response schemas
    consent_responses = [
        ConsentRecordResponse(
            id=c.id,
            patient_id=c.patient_id,
            consent_type=ConsentType(c.consent_type),
            consent_status="granted" if c.consented and not c.revoked_at else "revoked",
            consent_method="electronic",  # Default for now
            consent_text=c.consent_text,
            version=c.version,
            signature_data=c.signature_data,
            signed_at=c.consented_at,
            ip_address=c.ip_address,
            created_at=c.created_at,
            updated_at=c.created_at,
            expires_at=c.expires_at,
            revoked_at=c.revoked_at,
            revocation_reason=None,
            witness_name=None,
            witness_signature=None,
            notes=None,
            metadata=None,
            created_by=current_user.id  # Simplified for now
        )
        for c in consents
    ]

    return ConsentRecordListResponse(
        consents=consent_responses,
        total_count=total_count,
        active_count=active_count,
        expired_count=expired_count,
        revoked_count=revoked_count
    )


@router.get("/patients/{patient_id}/consent/status", response_model=dict)
@limiter.limit("50/minute")
async def get_consent_status(
    request: Request,
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    consent_service: ConsentService = Depends(get_consent_service)
) -> dict:
    """
    Get consent status summary for a patient.

    Returns a quick overview of valid consent status for all consent types.
    Useful for UI consent checkboxes and validation before operations.

    Rate Limit:
        - 50 requests per minute per IP address
        - Higher limit for frequent UI status checks

    Authorization:
        - Admin: Can access any patient's status
        - Therapist: Can access assigned patients only
        - Patient: Can access own status only

    Args:
        request: FastAPI request (for rate limiting)
        patient_id: UUID of patient to check consent status for
        db: AsyncSession database dependency
        current_user: Authenticated user from JWT token
        consent_service: ConsentService dependency

    Returns:
        Dict[str, bool]: Mapping of consent type to validity status

    Raises:
        HTTPException 403: Not authorized to access this patient's consent status
        HTTPException 404: Patient not found
        HTTPException 429: Rate limit exceeded

    Example Response:
        {
            "treatment": true,
            "hipaa_notice": true,
            "telehealth": true,
            "recording": false,
            "data_sharing": false,
            "research": false
        }

    Example:
        GET /api/v1/consent/patients/{patient_id}/consent/status
    """
    logger.info(
        f"Fetching consent status: user={current_user.id}, patient={patient_id}"
    )

    # Authorization check
    await verify_patient_access(patient_id, current_user, db)

    # Get consent status from service
    status = await consent_service.get_consent_status(
        patient_id=patient_id,
        db=db
    )

    logger.info(f"Consent status for patient {patient_id}: {status}")

    return status
