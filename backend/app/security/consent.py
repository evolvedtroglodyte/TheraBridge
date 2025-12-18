"""
Consent Service for HIPAA Compliance Feature 8

Provides business logic for patient consent management:
- Record patient consent (treatment, HIPAA notice, telehealth, recording, etc.)
- Get patient consent records with filtering
- Check if patient has valid consent for specific type
- Revoke consent
- Get consent status summary for a patient

Implements comprehensive consent tracking with version control, signature capture,
and expiration management for HIPAA compliance.
"""
from uuid import UUID
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from app.models.security_models import ConsentRecord
from app.models.db_models import User
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ConsentType(str, Enum):
    """Types of consent that can be recorded"""
    treatment = "treatment"  # Consent to treatment
    hipaa_notice = "hipaa_notice"  # HIPAA notice acknowledgment
    telehealth = "telehealth"  # Telehealth consent
    recording = "recording"  # Session recording consent
    data_sharing = "data_sharing"  # Data sharing consent
    research = "research"  # Research participation consent


class ConsentService:
    """
    Service for managing patient consent records.

    Consent management is critical for HIPAA compliance. This service tracks all
    patient consents including treatment authorization, HIPAA notices, telehealth
    agreements, and recording permissions. Supports consent versioning, signature
    capture, expiration tracking, and revocation workflows.
    """

    async def record_consent(
        self,
        patient_id: UUID,
        consent_type: str,
        consented: bool,
        consent_text: str,
        signature_data: Optional[str],
        ip_address: str,
        db: AsyncSession,
        version: Optional[str] = "1.0",
        expires_at: Optional[datetime] = None
    ) -> ConsentRecord:
        """
        Create a consent record.

        Records patient consent for a specific purpose (treatment, HIPAA notice,
        telehealth, recording, etc.). Stores the full consent text, signature data
        (if provided), and metadata for audit purposes.

        Args:
            patient_id: UUID of patient providing consent
            consent_type: Type of consent (treatment, hipaa_notice, telehealth, etc.)
            consented: True if patient consents, False if declined
            consent_text: Full text of consent form shown to patient
            signature_data: Optional base64-encoded signature image
            ip_address: IP address where consent was given (for electronic consent)
            db: Async database session
            version: Version of consent form (default "1.0")
            expires_at: Optional expiration date for consent

        Returns:
            ConsentRecord: Created consent record

        Example:
            >>> service = ConsentService()
            >>> consent = await service.record_consent(
            ...     patient_id=patient_uuid,
            ...     consent_type="telehealth",
            ...     consented=True,
            ...     consent_text="I consent to receive telehealth services...",
            ...     signature_data="data:image/png;base64,iVBORw0KGgo...",
            ...     ip_address="192.168.1.100",
            ...     db=db,
            ...     version="2.1"
            ... )
            >>> print(f"Consent recorded: {consent.id}")
        """
        logger.info(
            f"Recording consent: patient={patient_id}, type={consent_type}, "
            f"consented={consented}, version={version}"
        )

        # Create consent record
        consent_record = ConsentRecord(
            patient_id=patient_id,
            consent_type=consent_type,
            version=version,
            consented=consented,
            consent_text=consent_text,
            signature_data=signature_data,
            ip_address=ip_address,
            consented_at=datetime.utcnow() if consented else None,
            expires_at=expires_at,
            revoked_at=None,
            created_at=datetime.utcnow()
        )

        db.add(consent_record)
        await db.commit()
        await db.refresh(consent_record)

        logger.info(f"Consent record created: {consent_record.id}")
        return consent_record

    async def get_patient_consents(
        self,
        patient_id: UUID,
        consent_type: Optional[str],
        db: AsyncSession
    ) -> List[ConsentRecord]:
        """
        Get all consents for patient, optionally filtered by type.

        Retrieves all consent records for a specific patient. Can be filtered to
        show only a specific consent type (e.g., only telehealth consents). Results
        are ordered by creation date (newest first).

        Args:
            patient_id: UUID of patient to get consents for
            consent_type: Optional consent type to filter by (None = all types)
            db: Async database session

        Returns:
            List[ConsentRecord]: List of consent records matching criteria

        Example:
            >>> service = ConsentService()
            >>> # Get all consents for patient
            >>> all_consents = await service.get_patient_consents(
            ...     patient_id=patient_uuid,
            ...     consent_type=None,
            ...     db=db
            ... )
            >>> print(f"Patient has {len(all_consents)} consent records")
            >>>
            >>> # Get only telehealth consents
            >>> telehealth = await service.get_patient_consents(
            ...     patient_id=patient_uuid,
            ...     consent_type="telehealth",
            ...     db=db
            ... )
            >>> for consent in telehealth:
            ...     print(f"  {consent.version} - {consent.created_at}")
        """
        logger.info(f"Fetching consents: patient={patient_id}, type={consent_type}")

        # Build query
        conditions = [ConsentRecord.patient_id == patient_id]
        if consent_type:
            conditions.append(ConsentRecord.consent_type == consent_type)

        stmt = select(ConsentRecord).where(
            and_(*conditions)
        ).order_by(ConsentRecord.created_at.desc())

        result = await db.execute(stmt)
        consents = result.scalars().all()

        logger.info(f"Found {len(consents)} consent records")
        return list(consents)

    async def is_consent_valid(
        self,
        patient_id: UUID,
        consent_type: str,
        db: AsyncSession
    ) -> bool:
        """
        Check if patient has valid consent for specific type.

        Determines if a patient has valid (consented=True, not expired, not revoked)
        consent for a specific purpose. Used by access control and business logic to
        ensure patient authorization before proceeding with certain actions.

        Args:
            patient_id: UUID of patient to check consent for
            consent_type: Type of consent to check (treatment, telehealth, etc.)
            db: Async database session

        Returns:
            bool: True if patient has valid consent, False otherwise

        Example:
            >>> service = ConsentService()
            >>> can_record = await service.is_consent_valid(
            ...     patient_id=patient_uuid,
            ...     consent_type="recording",
            ...     db=db
            ... )
            >>> if can_record:
            ...     print("Patient has consented to recording")
            ... else:
            ...     print("Recording not permitted - no valid consent")
        """
        logger.debug(f"Checking consent validity: patient={patient_id}, type={consent_type}")

        now = datetime.utcnow()

        # Query for valid consent
        stmt = select(ConsentRecord).where(
            and_(
                ConsentRecord.patient_id == patient_id,
                ConsentRecord.consent_type == consent_type,
                ConsentRecord.consented == True,  # Must be consented (not declined)
                ConsentRecord.revoked_at.is_(None),  # Not revoked
                or_(
                    ConsentRecord.expires_at.is_(None),  # No expiration
                    ConsentRecord.expires_at > now  # Or not expired yet
                )
            )
        ).order_by(ConsentRecord.created_at.desc())  # Get most recent

        result = await db.execute(stmt)
        consent = result.scalar_one_or_none()

        is_valid = consent is not None
        logger.debug(f"Consent validity check result: {is_valid}")
        return is_valid

    async def revoke_consent(
        self,
        consent_id: UUID,
        db: AsyncSession
    ) -> ConsentRecord:
        """
        Revoke consent (set revoked_at).

        Revokes a previously granted consent, immediately invalidating it. Used when
        a patient withdraws consent for a specific purpose. The revocation is
        timestamped for audit purposes.

        Args:
            consent_id: UUID of consent record to revoke
            db: Async database session

        Returns:
            ConsentRecord: Updated consent record with revocation timestamp

        Raises:
            ValueError: If consent not found or already revoked

        Example:
            >>> service = ConsentService()
            >>> revoked = await service.revoke_consent(
            ...     consent_id=consent_uuid,
            ...     db=db
            ... )
            >>> print(f"Consent revoked at {revoked.revoked_at}")
        """
        logger.info(f"Revoking consent: {consent_id}")

        # Fetch the consent record
        stmt = select(ConsentRecord).where(ConsentRecord.id == consent_id)
        result = await db.execute(stmt)
        consent = result.scalar_one_or_none()

        if not consent:
            raise ValueError(f"Consent record {consent_id} not found")

        if consent.revoked_at is not None:
            raise ValueError(f"Consent {consent_id} already revoked at {consent.revoked_at}")

        # Revoke the consent
        consent.revoked_at = datetime.utcnow()

        await db.commit()
        await db.refresh(consent)

        logger.info(f"Consent revoked: {consent_id} at {consent.revoked_at}")
        return consent

    async def get_consent_status(
        self,
        patient_id: UUID,
        db: AsyncSession
    ) -> Dict[str, bool]:
        """
        Return dict of consent_type -> is_valid for all consent types.

        Provides a comprehensive overview of a patient's consent status across all
        consent types. Returns a dictionary mapping each consent type to a boolean
        indicating whether the patient has valid consent for that type.

        Args:
            patient_id: UUID of patient to get consent status for
            db: Async database session

        Returns:
            Dict[str, bool]: Dictionary mapping consent type to validity status

        Example:
            >>> service = ConsentService()
            >>> status = await service.get_consent_status(
            ...     patient_id=patient_uuid,
            ...     db=db
            ... )
            >>> print(status)
            {
                "treatment": True,
                "hipaa_notice": True,
                "telehealth": True,
                "recording": False,
                "data_sharing": False,
                "research": False
            }
            >>> if status["recording"]:
            ...     print("Can record sessions")
        """
        logger.info(f"Fetching consent status for patient: {patient_id}")

        # Check each consent type
        status = {}
        for consent_type in ConsentType:
            is_valid = await self.is_consent_valid(
                patient_id=patient_id,
                consent_type=consent_type.value,
                db=db
            )
            status[consent_type.value] = is_valid

        logger.info(f"Consent status for patient {patient_id}: {status}")
        return status


def get_consent_service() -> ConsentService:
    """
    FastAPI dependency for injecting ConsentService.

    Returns:
        ConsentService: Instance of the consent service

    Usage:
        >>> @router.post("/consent")
        >>> async def record_consent(
        ...     request: ConsentRequest,
        ...     service: ConsentService = Depends(get_consent_service),
        ...     db: AsyncSession = Depends(get_db)
        ... ):
        ...     return await service.record_consent(...)
    """
    return ConsentService()
