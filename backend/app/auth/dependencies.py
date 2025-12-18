"""
FastAPI dependencies for authentication
"""
from typing import Generator
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import SessionLocal
from app.auth.utils import decode_access_token
from app.models.db_models import User, TherapistPatient
import logging

logger = logging.getLogger(__name__)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Yields:
        SQLAlchemy Session object

    Note:
        Session is automatically closed after request completes (finally block)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Security scheme for JWT Bearer tokens
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate user from JWT access token.

    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session

    Returns:
        User object from database

    Raises:
        HTTPException 401: If token invalid or user not found
        HTTPException 403: If user account is inactive
    """
    # Decode and verify token
    payload = decode_access_token(credentials.credentials)
    user_id = UUID(payload["user_id"])

    # Load user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    return user


def require_role(allowed_roles: list[str]):
    """
    Create a dependency that requires specific user roles.

    Args:
        allowed_roles: List of role names (e.g., ["therapist", "admin"])

    Returns:
        Dependency function that checks user role

    Usage:
        @router.get("/analytics")
        def get_analytics(user: User = Depends(require_role(["therapist"]))):
            # Only therapists can access this endpoint
            ...
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.value not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}"
            )
        return current_user

    return role_checker


async def verify_treatment_plan_access(
    plan_id: UUID,
    therapist_id: UUID,
    db: AsyncSession
):
    """
    Verify therapist has access to treatment plan via active patient relationship.

    This helper ensures that the therapist attempting to access a treatment plan
    has an active relationship with the patient who owns the plan. It loads the
    plan with its patient relationship and verifies ownership through the
    therapist_patients junction table.

    Args:
        plan_id: UUID of the treatment plan to verify access for
        therapist_id: UUID of the therapist requesting access
        db: AsyncSession database connection

    Returns:
        TreatmentPlan: The treatment plan object if access is authorized

    Raises:
        HTTPException 404: If treatment plan not found
        HTTPException 403: If therapist does not have active relationship with patient

    Usage:
        @router.get("/treatment-plans/{plan_id}")
        async def get_plan(
            plan_id: UUID,
            current_user: User = Depends(require_role(["therapist"])),
            db: AsyncSession = Depends(get_db)
        ):
            # Verify access and get plan in one operation
            plan = await verify_treatment_plan_access(plan_id, current_user.id, db)
            return plan

    Example:
        # In a router endpoint
        plan = await verify_treatment_plan_access(
            plan_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            therapist_id=current_user.id,
            db=db
        )
        # If we get here, access is authorized and plan is loaded
    """
    # Import here to avoid circular dependency
    from app.models.treatment_models import TreatmentPlan

    # Load treatment plan with patient relationship
    query = select(TreatmentPlan).where(
        TreatmentPlan.id == plan_id
    ).options(
        selectinload(TreatmentPlan.patient)
    )

    result = await db.execute(query)
    plan = result.scalar_one_or_none()

    if not plan:
        logger.warning(f"Treatment plan {plan_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Treatment plan not found"
        )

    # Verify therapist has active relationship with patient
    patient_id = plan.patient_id

    access_query = select(TherapistPatient).where(
        TherapistPatient.therapist_id == therapist_id,
        TherapistPatient.patient_id == patient_id,
        TherapistPatient.is_active == True
    )

    access_result = await db.execute(access_query)
    relationship = access_result.scalar_one_or_none()

    if not relationship:
        logger.warning(
            f"Access denied: Therapist {therapist_id} does not have active "
            f"relationship with patient {patient_id} for plan {plan_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Plan not assigned to this therapist"
        )

    return plan


async def verify_timeline_event_access(
    event_id: UUID,
    therapist_id: UUID,
    db: AsyncSession
):
    """
    Verify therapist has access to timeline event via active patient relationship.

    This helper ensures that the therapist attempting to access a timeline event
    has an active relationship with the patient who owns the event. It loads the
    event with its patient relationship and verifies ownership through the
    therapist_patients junction table.

    Args:
        event_id: UUID of the timeline event to verify access for
        therapist_id: UUID of the therapist requesting access
        db: AsyncSession database connection

    Returns:
        TimelineEvent: The timeline event object if access is authorized

    Raises:
        HTTPException 404: If timeline event not found
        HTTPException 403: If therapist does not have active relationship with patient

    Usage:
        @router.patch("/timeline-events/{event_id}")
        async def update_event(
            event_id: UUID,
            event_data: TimelineEventUpdate,
            current_user: User = Depends(require_role(["therapist"])),
            db: AsyncSession = Depends(get_db)
        ):
            # Verify access and get event in one operation
            event = await verify_timeline_event_access(event_id, current_user.id, db)
            # Proceed with update...
            return updated_event

    Example:
        # In a router endpoint
        event = await verify_timeline_event_access(
            event_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
            therapist_id=current_user.id,
            db=db
        )
        # If we get here, access is authorized and event is loaded
    """
    # Import here to avoid circular dependency
    from app.models.db_models import TimelineEvent

    # Load timeline event
    result = await db.execute(
        select(TimelineEvent).where(TimelineEvent.id == event_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        logger.warning(f"Timeline event {event_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline event not found"
        )

    # Verify therapist has active relationship with patient
    access_query = select(TherapistPatient).where(
        TherapistPatient.therapist_id == therapist_id,
        TherapistPatient.patient_id == event.patient_id,
        TherapistPatient.is_active == True
    )

    access_result = await db.execute(access_query)
    relationship = access_result.scalar_one_or_none()

    if not relationship:
        logger.warning(
            f"Access denied: Therapist {therapist_id} does not have active "
            f"relationship with patient {event.patient_id} for event {event_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: Event not assigned to this therapist's patients"
        )

    return event
