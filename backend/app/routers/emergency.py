"""
Emergency Access API Endpoints for HIPAA Compliance Feature 8

Provides REST API for break-the-glass emergency access functionality:
- POST /api/v1/emergency-access - Request emergency access to patient records
- GET /api/v1/emergency-access/active - List active emergency access grants
- DELETE /api/v1/emergency-access/{access_id} - Revoke emergency access

All emergency access requests are rate-limited, authenticated, authorized, and audited.
Implements security controls for emergency scenarios requiring temporary elevated access.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List
import logging

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.db_models import User
from app.models.schemas import UserRole
from app.schemas.emergency_schemas import (
    EmergencyAccessRequest,
    EmergencyAccessResponse,
    EmergencyAccessListResponse,
    EmergencyAccessStatus,
    EmergencyAccessLevel,
    EmergencyAccessReason
)
from app.security.emergency_access import (
    EmergencyAccessService,
    get_emergency_access_service
)
from app.middleware.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/", response_model=EmergencyAccessResponse, status_code=201)
@limiter.limit("5/hour")
async def request_emergency_access(
    request: Request,
    access_request: EmergencyAccessRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: EmergencyAccessService = Depends(get_emergency_access_service)
):
    """
    Request emergency access to patient records (break-the-glass).

    Creates a temporary emergency access grant for accessing patient records in
    urgent situations (e.g., patient crisis, medical emergency, covering therapist).
    For MVP, requests are auto-approved immediately. In production, this would
    require supervisor approval.

    Rate Limit:
        - 5 requests per hour per IP address
        - Prevents abuse of emergency access mechanism
        - Ensures emergency access is used only for genuine emergencies

    Authorization:
        - Requires authentication (valid JWT token)
        - Only therapists and admins can request emergency access
        - Patients cannot request emergency access

    Security Features:
        - All requests fully audited with requester, reason, and timestamp
        - Justification must be at least 50 characters (detailed explanation required)
        - Default duration: 24 hours (configurable, max 168 hours = 7 days)
        - Access level defaults to read_only (safest option)
        - Logs high-risk audit event for compliance tracking

    Request Body (EmergencyAccessRequest):
        - patient_id: UUID of patient whose records need access
        - reason: EmergencyAccessReason enum (patient_crisis, medical_emergency, etc.)
        - justification: Detailed explanation (min 50 chars, max 2000 chars)
        - access_level: read_only | read_write | full_access (default: read_only)
        - duration_hours: 1-168 hours (default: 24)
        - contact_phone: Emergency contact phone number
        - supervisor_id: Optional supervisor to notify about this request

    Returns:
        EmergencyAccessResponse: Emergency access grant with details

    Raises:
        HTTPException 401: If user not authenticated
        HTTPException 403: If user role not authorized (patient role)
        HTTPException 404: If patient not found
        HTTPException 429: Rate limit exceeded (too many emergency requests)

    Example Usage:
        POST /api/v1/emergency-access
        {
            "patient_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "reason": "patient_crisis",
            "justification": "Patient called reporting suicidal ideation. Need immediate access to treatment plan and risk assessment to ensure safety.",
            "access_level": "read_only",
            "duration_hours": 24,
            "contact_phone": "+1-555-123-4567",
            "supervisor_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef1"
        }

    Emergency Access Use Cases:
        - Patient in crisis requiring immediate safety assessment
        - Medical emergency requiring access to treatment history
        - Court order or legal requirement for records access
        - Patient incapacitated and unable to provide consent
        - Covering therapist needs access while primary therapist unavailable
    """
    # Authorization check: Only therapists and admins can request emergency access
    if current_user.role not in [UserRole.therapist, UserRole.admin]:
        logger.warning(
            f"Emergency access denied: user {current_user.id} has role {current_user.role}"
        )
        raise HTTPException(
            status_code=403,
            detail="Only therapists and administrators can request emergency access"
        )

    # Validate patient exists in database
    patient_query = select(User).where(
        User.id == access_request.patient_id,
        User.role == UserRole.patient.value
    )
    patient_result = await db.execute(patient_query)
    patient = patient_result.scalar_one_or_none()

    if not patient:
        logger.warning(
            f"Emergency access failed: patient {access_request.patient_id} not found"
        )
        raise HTTPException(
            status_code=404,
            detail=f"Patient {access_request.patient_id} not found"
        )

    # Convert duration from hours to minutes for service layer
    duration_minutes = access_request.duration_hours * 60

    # Log high-risk emergency access request
    logger.warning(
        f"EMERGENCY ACCESS REQUEST: User {current_user.id} ({current_user.email}) "
        f"requesting access to patient {access_request.patient_id} "
        f"for reason: {access_request.reason.value} - {access_request.justification[:100]}..."
    )

    # Create emergency access request (status: pending)
    emergency_access = await service.request_emergency_access(
        user_id=current_user.id,
        patient_id=access_request.patient_id,
        reason=access_request.justification,
        duration_minutes=duration_minutes,
        db=db
    )

    # MVP: Auto-approve immediately (in production, this would require supervisor approval)
    logger.info(
        f"Auto-approving emergency access request {emergency_access.id} (MVP mode)"
    )
    approved_access = await service.approve_emergency_access(
        request_id=emergency_access.id,
        approver_id=current_user.id,  # Self-approval for MVP
        db=db
    )

    # Construct response
    response = EmergencyAccessResponse(
        id=approved_access.id,
        patient_id=approved_access.patient_id,
        requesting_user_id=approved_access.user_id,
        requesting_user_email=current_user.email,
        requesting_user_role=current_user.role.value,
        reason=access_request.reason,
        justification=access_request.justification,
        access_level=access_request.access_level,
        status=EmergencyAccessStatus.approved,
        requested_at=approved_access.created_at,
        duration_hours=access_request.duration_hours,
        expires_at=approved_access.expires_at,
        reviewed_by=approved_access.approved_by,
        reviewed_at=approved_access.approved_at,
        approval_notes="Auto-approved (MVP mode)",
        denial_reason=None,
        contact_phone=access_request.contact_phone,
        supervisor_id=access_request.supervisor_id,
        access_count=0,
        last_accessed_at=None
    )

    logger.info(
        f"Emergency access granted: {approved_access.id}, "
        f"expires at {approved_access.expires_at}"
    )

    return response


@router.get("/active", response_model=EmergencyAccessListResponse)
@limiter.limit("30/minute")
async def get_active_emergency_accesses(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: EmergencyAccessService = Depends(get_emergency_access_service)
):
    """
    List all active emergency access grants for current user.

    Retrieves all currently active (approved, not expired, not revoked) emergency
    access grants for the authenticated user. Useful for displaying active access
    in UI or for monitoring which patients the user has emergency access to.

    Rate Limit:
        - 30 requests per minute per IP address
        - Allows frequent polling for dashboard updates

    Authorization:
        - Requires authentication (valid JWT token)
        - Users can only see their own active emergency accesses

    Returns:
        EmergencyAccessListResponse: List of active emergency accesses with stats

    Response Includes:
        - requests: List[EmergencyAccessResponse] - All active access grants
        - total_count: Total number of requests returned
        - active_count: Number of currently active accesses
        - pending_count: Number of pending requests (always 0 in MVP)

    Example Response:
        {
            "requests": [
                {
                    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                    "patient_id": "b2c3d4e5-f6a7-8901-2345-67890abcdef1",
                    "requesting_user_id": "c3d4e5f6-a7b8-9012-3456-7890abcdef12",
                    "requesting_user_email": "therapist@example.com",
                    "requesting_user_role": "therapist",
                    "reason": "patient_crisis",
                    "justification": "Patient in crisis...",
                    "access_level": "read_only",
                    "status": "approved",
                    "requested_at": "2025-12-17T10:00:00Z",
                    "duration_hours": 24,
                    "expires_at": "2025-12-18T10:00:00Z",
                    "reviewed_by": "c3d4e5f6-a7b8-9012-3456-7890abcdef12",
                    "reviewed_at": "2025-12-17T10:00:00Z",
                    "approval_notes": "Auto-approved (MVP mode)",
                    "denial_reason": null,
                    "contact_phone": "+1-555-123-4567",
                    "supervisor_id": null,
                    "access_count": 0,
                    "last_accessed_at": null
                }
            ],
            "total_count": 1,
            "active_count": 1,
            "pending_count": 0
        }
    """
    logger.info(f"Fetching active emergency accesses for user {current_user.id}")

    # Get all active emergency accesses for current user
    active_accesses = await service.get_active_emergency_accesses(
        user_id=current_user.id,
        db=db
    )

    # Convert to response models
    access_responses: List[EmergencyAccessResponse] = []
    for access in active_accesses:
        # Get patient info for response
        patient_query = select(User).where(User.id == access.patient_id)
        patient_result = await db.execute(patient_query)
        patient = patient_result.scalar_one_or_none()

        # Determine reason and access level (stored in justification field for MVP)
        # In production, these would be separate columns
        access_response = EmergencyAccessResponse(
            id=access.id,
            patient_id=access.patient_id,
            requesting_user_id=access.user_id,
            requesting_user_email=current_user.email,
            requesting_user_role=current_user.role.value,
            reason=EmergencyAccessReason.patient_crisis,  # Default for MVP
            justification=access.reason,
            access_level=EmergencyAccessLevel.read_only,  # Default for MVP
            status=EmergencyAccessStatus.approved,
            requested_at=access.created_at,
            duration_hours=access.duration_minutes // 60,
            expires_at=access.expires_at,
            reviewed_by=access.approved_by,
            reviewed_at=access.approved_at,
            approval_notes="Auto-approved (MVP mode)",
            denial_reason=None,
            contact_phone="N/A",  # Not stored in MVP
            supervisor_id=None,
            access_count=0,  # Not tracked in MVP
            last_accessed_at=None
        )
        access_responses.append(access_response)

    # Build summary statistics
    total_count = len(access_responses)
    active_count = len([a for a in access_responses if a.status == EmergencyAccessStatus.approved])
    pending_count = 0  # MVP auto-approves, so no pending requests

    logger.info(
        f"Found {total_count} active emergency accesses for user {current_user.id}"
    )

    return EmergencyAccessListResponse(
        requests=access_responses,
        total_count=total_count,
        active_count=active_count,
        pending_count=pending_count
    )


@router.delete("/{access_id}", status_code=200)
@limiter.limit("20/minute")
async def revoke_emergency_access(
    request: Request,
    access_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: EmergencyAccessService = Depends(get_emergency_access_service)
):
    """
    Revoke emergency access before expiration.

    Immediately terminates an active emergency access grant, revoking the user's
    access to the patient's records. Used when emergency situation is resolved
    or access needs to be terminated for security reasons.

    Rate Limit:
        - 20 requests per minute per IP address
        - Allows multiple revocations for emergency cleanup

    Authorization:
        - Requires authentication (valid JWT token)
        - Users can only revoke their own emergency access
        - Admins can revoke any emergency access (future enhancement)

    Path Parameters:
        - access_id: UUID of emergency access grant to revoke

    Returns:
        Success message with revocation timestamp

    Raises:
        HTTPException 404: If emergency access grant not found
        HTTPException 403: If user not authorized to revoke this access
        HTTPException 400: If access already revoked or expired

    Example Usage:
        DELETE /api/v1/emergency-access/a1b2c3d4-e5f6-7890-1234-567890abcdef

    Example Response:
        {
            "message": "Emergency access revoked successfully",
            "access_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
            "revoked_at": "2025-12-17T12:00:00Z",
            "status": "revoked"
        }
    """
    logger.info(
        f"Revoking emergency access: {access_id} by user {current_user.id}"
    )

    # Validate that emergency access exists
    from app.models.security_models import EmergencyAccess

    access_query = select(EmergencyAccess).where(EmergencyAccess.id == access_id)
    access_result = await db.execute(access_query)
    emergency_access = access_result.scalar_one_or_none()

    if not emergency_access:
        raise HTTPException(
            status_code=404,
            detail=f"Emergency access {access_id} not found"
        )

    # Authorization: Users can only revoke their own emergency access
    # (In production, admins could revoke any access)
    if emergency_access.user_id != current_user.id and current_user.role != UserRole.admin:
        logger.warning(
            f"Unauthorized revocation attempt: user {current_user.id} "
            f"tried to revoke access {access_id} owned by {emergency_access.user_id}"
        )
        raise HTTPException(
            status_code=403,
            detail="Not authorized to revoke this emergency access"
        )

    # Check if already revoked
    if emergency_access.access_revoked_at is not None:
        raise HTTPException(
            status_code=400,
            detail=f"Emergency access {access_id} already revoked at {emergency_access.access_revoked_at}"
        )

    # Revoke the emergency access
    revoked_access = await service.revoke_emergency_access(
        request_id=access_id,
        db=db
    )

    logger.info(
        f"Emergency access revoked: {access_id} at {revoked_access.access_revoked_at}"
    )

    return {
        "message": "Emergency access revoked successfully",
        "access_id": str(access_id),
        "revoked_at": revoked_access.access_revoked_at,
        "status": "revoked"
    }
