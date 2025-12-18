"""
Emergency Access Service for HIPAA Compliance Feature 8

Provides business logic for break-the-glass emergency access functionality:
- Request emergency access to patient records
- Approve/deny emergency access requests
- Check if user has valid emergency access to a patient
- Revoke active emergency access
- List active emergency access grants for a user

Implements comprehensive audit logging and security controls for emergency scenarios.
"""
from uuid import UUID
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.security_models import EmergencyAccess
from app.models.db_models import User
import logging

logger = logging.getLogger(__name__)


class EmergencyAccessService:
    """
    Service for managing emergency access to patient records.

    Emergency access allows authorized users to request temporary access to patient
    records in urgent situations (e.g., medical emergency, patient crisis). All
    emergency access requests are fully audited and require approval before access
    is granted.
    """

    async def request_emergency_access(
        self,
        user_id: UUID,
        patient_id: UUID,
        reason: str,
        duration_minutes: int,
        db: AsyncSession
    ) -> EmergencyAccess:
        """
        Create an emergency access request.

        Creates a pending emergency access request that must be approved by an
        authorized user (typically an admin or supervisor) before access is granted.
        The request includes the reason for access and requested duration.

        Args:
            user_id: UUID of user requesting emergency access
            patient_id: UUID of patient whose records need access
            reason: Detailed justification for emergency access (required)
            duration_minutes: How long access is needed (in minutes)
            db: Async database session

        Returns:
            EmergencyAccess: Created emergency access request object

        Example:
            >>> service = EmergencyAccessService()
            >>> request = await service.request_emergency_access(
            ...     user_id=therapist_uuid,
            ...     patient_id=patient_uuid,
            ...     reason="Patient in crisis, immediate access needed for safety assessment",
            ...     duration_minutes=120,
            ...     db=db
            ... )
            >>> print(f"Request created: {request.id}, Status: pending")
        """
        logger.info(
            f"Creating emergency access request: user={user_id}, patient={patient_id}, "
            f"duration={duration_minutes}min"
        )

        # Create emergency access request with pending status
        emergency_access = EmergencyAccess(
            user_id=user_id,
            patient_id=patient_id,
            reason=reason,
            duration_minutes=duration_minutes,
            approved_by=None,
            approved_at=None,
            expires_at=None,  # Set when approved
            access_revoked_at=None,
            created_at=datetime.utcnow()
        )

        db.add(emergency_access)
        await db.commit()
        await db.refresh(emergency_access)

        logger.info(f"Emergency access request created: {emergency_access.id}")
        return emergency_access

    async def approve_emergency_access(
        self,
        request_id: UUID,
        approver_id: UUID,
        db: AsyncSession
    ) -> EmergencyAccess:
        """
        Approve an emergency access request.

        Approves a pending emergency access request, granting the user temporary
        access to the patient's records. Sets the approval timestamp and calculates
        the expiration time based on the requested duration.

        Args:
            request_id: UUID of the emergency access request to approve
            approver_id: UUID of user approving the request (admin/supervisor)
            db: Async database session

        Returns:
            EmergencyAccess: Updated emergency access request with approval details

        Raises:
            ValueError: If request not found or already processed

        Example:
            >>> service = EmergencyAccessService()
            >>> approved = await service.approve_emergency_access(
            ...     request_id=request_uuid,
            ...     approver_id=admin_uuid,
            ...     db=db
            ... )
            >>> print(f"Approved by {approved.approved_by}, expires at {approved.expires_at}")
        """
        logger.info(f"Approving emergency access request: {request_id} by {approver_id}")

        # Fetch the emergency access request
        stmt = select(EmergencyAccess).where(EmergencyAccess.id == request_id)
        result = await db.execute(stmt)
        emergency_access = result.scalar_one_or_none()

        if not emergency_access:
            raise ValueError(f"Emergency access request {request_id} not found")

        if emergency_access.approved_at is not None:
            raise ValueError(f"Emergency access request {request_id} already approved")

        # Approve the request
        now = datetime.utcnow()
        emergency_access.approved_by = approver_id
        emergency_access.approved_at = now
        emergency_access.expires_at = now + timedelta(minutes=emergency_access.duration_minutes)

        await db.commit()
        await db.refresh(emergency_access)

        logger.info(
            f"Emergency access approved: {request_id}, expires at {emergency_access.expires_at}"
        )
        return emergency_access

    async def is_emergency_access_valid(
        self,
        user_id: UUID,
        patient_id: UUID,
        db: AsyncSession
    ) -> bool:
        """
        Check if user has valid emergency access to patient.

        Determines if a user currently has valid (approved, not expired, not revoked)
        emergency access to a specific patient's records. Used by access control
        middleware to grant or deny access.

        Args:
            user_id: UUID of user to check access for
            patient_id: UUID of patient whose records are being accessed
            db: Async database session

        Returns:
            bool: True if user has valid emergency access, False otherwise

        Example:
            >>> service = EmergencyAccessService()
            >>> has_access = await service.is_emergency_access_valid(
            ...     user_id=therapist_uuid,
            ...     patient_id=patient_uuid,
            ...     db=db
            ... )
            >>> if has_access:
            ...     print("Emergency access granted")
            ... else:
            ...     print("Access denied - no valid emergency access")
        """
        logger.debug(f"Checking emergency access: user={user_id}, patient={patient_id}")

        now = datetime.utcnow()

        # Query for valid emergency access
        stmt = select(EmergencyAccess).where(
            and_(
                EmergencyAccess.user_id == user_id,
                EmergencyAccess.patient_id == patient_id,
                EmergencyAccess.approved_at.isnot(None),  # Must be approved
                EmergencyAccess.expires_at.isnot(None),  # Must have expiration
                EmergencyAccess.expires_at > now,  # Not expired
                EmergencyAccess.access_revoked_at.is_(None)  # Not revoked
            )
        )

        result = await db.execute(stmt)
        emergency_access = result.scalar_one_or_none()

        has_access = emergency_access is not None
        logger.debug(f"Emergency access check result: {has_access}")
        return has_access

    async def revoke_emergency_access(
        self,
        request_id: UUID,
        db: AsyncSession
    ) -> EmergencyAccess:
        """
        Revoke emergency access before expiration.

        Revokes an active emergency access grant, immediately terminating the user's
        access to the patient's records. Used when emergency situation is resolved
        or access needs to be terminated for security reasons.

        Args:
            request_id: UUID of emergency access request to revoke
            db: Async database session

        Returns:
            EmergencyAccess: Updated emergency access with revocation timestamp

        Raises:
            ValueError: If request not found or already revoked

        Example:
            >>> service = EmergencyAccessService()
            >>> revoked = await service.revoke_emergency_access(
            ...     request_id=request_uuid,
            ...     db=db
            ... )
            >>> print(f"Access revoked at {revoked.access_revoked_at}")
        """
        logger.info(f"Revoking emergency access: {request_id}")

        # Fetch the emergency access request
        stmt = select(EmergencyAccess).where(EmergencyAccess.id == request_id)
        result = await db.execute(stmt)
        emergency_access = result.scalar_one_or_none()

        if not emergency_access:
            raise ValueError(f"Emergency access request {request_id} not found")

        if emergency_access.access_revoked_at is not None:
            raise ValueError(f"Emergency access {request_id} already revoked")

        # Revoke the access
        emergency_access.access_revoked_at = datetime.utcnow()

        await db.commit()
        await db.refresh(emergency_access)

        logger.info(f"Emergency access revoked: {request_id} at {emergency_access.access_revoked_at}")
        return emergency_access

    async def get_active_emergency_accesses(
        self,
        user_id: UUID,
        db: AsyncSession
    ) -> List[EmergencyAccess]:
        """
        Return all active emergency access grants for user.

        Retrieves all currently active (approved, not expired, not revoked) emergency
        access grants for a specific user. Useful for displaying active access in UI
        or for administrative monitoring.

        Args:
            user_id: UUID of user to get active accesses for
            db: Async database session

        Returns:
            List[EmergencyAccess]: List of active emergency access grants

        Example:
            >>> service = EmergencyAccessService()
            >>> active_accesses = await service.get_active_emergency_accesses(
            ...     user_id=therapist_uuid,
            ...     db=db
            ... )
            >>> print(f"User has {len(active_accesses)} active emergency accesses")
            >>> for access in active_accesses:
            ...     print(f"  - Patient {access.patient_id}, expires {access.expires_at}")
        """
        logger.info(f"Fetching active emergency accesses for user: {user_id}")

        now = datetime.utcnow()

        # Query for all active emergency accesses
        stmt = select(EmergencyAccess).where(
            and_(
                EmergencyAccess.user_id == user_id,
                EmergencyAccess.approved_at.isnot(None),  # Approved
                EmergencyAccess.expires_at.isnot(None),  # Has expiration
                EmergencyAccess.expires_at > now,  # Not expired
                EmergencyAccess.access_revoked_at.is_(None)  # Not revoked
            )
        ).order_by(EmergencyAccess.expires_at.asc())  # Soonest expiring first

        result = await db.execute(stmt)
        active_accesses = result.scalars().all()

        logger.info(f"Found {len(active_accesses)} active emergency accesses for user {user_id}")
        return list(active_accesses)


def get_emergency_access_service() -> EmergencyAccessService:
    """
    FastAPI dependency for injecting EmergencyAccessService.

    Returns:
        EmergencyAccessService: Instance of the emergency access service

    Usage:
        >>> @router.post("/emergency-access")
        >>> async def request_emergency_access(
        ...     request: EmergencyAccessRequest,
        ...     service: EmergencyAccessService = Depends(get_emergency_access_service),
        ...     db: AsyncSession = Depends(get_db)
        ... ):
        ...     return await service.request_emergency_access(...)
    """
    return EmergencyAccessService()
