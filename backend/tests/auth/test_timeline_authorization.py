"""
Comprehensive tests for Sub-feature 7: Timeline Event Authorization Helper.

Tests verify_timeline_event_access() function which checks if therapist has
active relationship with patient before allowing access to timeline events.

Test coverage:
1. Success case - therapist has active relationship
2. Event not found - invalid event_id
3. No relationship - therapist not assigned to patient
4. Inactive relationship - relationship exists but is_active=False
"""
import pytest
import uuid
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import verify_timeline_event_access
from app.models.db_models import User, TherapistPatient, TimelineEvent
from app.models.schemas import UserRole


@pytest.mark.asyncio
async def test_verify_timeline_event_access_success(async_test_db: AsyncSession):
    """
    Test successful timeline event access verification.

    Verifies that verify_timeline_event_access() returns the TimelineEvent
    when therapist has an active relationship with the patient.
    """
    # Create therapist user
    therapist = User(
        email="therapist@test.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="Therapist",
        full_name="Test Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(therapist)
    await async_test_db.commit()
    await async_test_db.refresh(therapist)

    # Create patient user
    patient = User(
        email="patient@test.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="Patient",
        full_name="Test Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(patient)
    await async_test_db.commit()
    await async_test_db.refresh(patient)

    # Create active therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist.id,
        patient_id=patient.id,
        relationship_type="primary",
        is_active=True
    )
    async_test_db.add(relationship)
    await async_test_db.commit()
    await async_test_db.refresh(relationship)

    # Create timeline event for patient
    event = TimelineEvent(
        patient_id=patient.id,
        therapist_id=therapist.id,
        event_type="session",
        title="Therapy Session",
        description="First therapy session",
        event_date=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    async_test_db.add(event)
    await async_test_db.commit()
    await async_test_db.refresh(event)

    # Call verify_timeline_event_access
    result_event = await verify_timeline_event_access(
        event_id=event.id,
        therapist_id=therapist.id,
        db=async_test_db
    )

    # Assert: Returns TimelineEvent object (not exception)
    assert result_event is not None
    assert isinstance(result_event, TimelineEvent)

    # Assert: Returned event matches created event
    assert result_event.id == event.id
    assert result_event.patient_id == patient.id
    assert result_event.therapist_id == therapist.id
    assert result_event.title == "Therapy Session"


@pytest.mark.asyncio
async def test_verify_timeline_event_access_event_not_found(async_test_db: AsyncSession):
    """
    Test timeline event access with non-existent event_id.

    Verifies that verify_timeline_event_access() raises HTTPException with
    status_code=404 when event_id does not exist.
    """
    # Create therapist user (needed for function signature)
    therapist = User(
        email="therapist2@test.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="Therapist",
        full_name="Test Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(therapist)
    await async_test_db.commit()
    await async_test_db.refresh(therapist)

    # Use non-existent event_id (random UUID)
    non_existent_event_id = uuid.uuid4()

    # Call verify_timeline_event_access and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await verify_timeline_event_access(
            event_id=non_existent_event_id,
            therapist_id=therapist.id,
            db=async_test_db
        )

    # Assert: Raises HTTPException with status_code=404
    assert exc_info.value.status_code == 404

    # Assert: Detail message contains "not found"
    assert "not found" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_verify_timeline_event_access_no_relationship(async_test_db: AsyncSession):
    """
    Test timeline event access without therapist-patient relationship.

    Verifies that verify_timeline_event_access() raises HTTPException with
    status_code=403 when therapist is not assigned to patient.
    """
    # Create therapist user
    therapist = User(
        email="therapist3@test.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="Therapist",
        full_name="Test Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(therapist)
    await async_test_db.commit()
    await async_test_db.refresh(therapist)

    # Create patient user
    patient = User(
        email="patient3@test.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="Patient",
        full_name="Test Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(patient)
    await async_test_db.commit()
    await async_test_db.refresh(patient)

    # Do NOT create TherapistPatient relationship

    # Create timeline event for patient
    event = TimelineEvent(
        patient_id=patient.id,
        therapist_id=None,  # No therapist assigned
        event_type="clinical_note",
        title="Clinical Note",
        description="Patient note without therapist",
        event_date=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    async_test_db.add(event)
    await async_test_db.commit()
    await async_test_db.refresh(event)

    # Call verify_timeline_event_access and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await verify_timeline_event_access(
            event_id=event.id,
            therapist_id=therapist.id,
            db=async_test_db
        )

    # Assert: Raises HTTPException with status_code=403
    assert exc_info.value.status_code == 403

    # Assert: Detail message contains "Access denied"
    assert "access denied" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_verify_timeline_event_access_inactive_relationship(async_test_db: AsyncSession):
    """
    Test timeline event access with inactive therapist-patient relationship.

    Verifies that verify_timeline_event_access() raises HTTPException with
    status_code=403 when relationship exists but is_active=False.
    """
    # Create therapist user
    therapist = User(
        email="therapist4@test.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="Therapist",
        full_name="Test Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(therapist)
    await async_test_db.commit()
    await async_test_db.refresh(therapist)

    # Create patient user
    patient = User(
        email="patient4@test.com",
        hashed_password="hashed_password",
        first_name="Test",
        last_name="Patient",
        full_name="Test Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(patient)
    await async_test_db.commit()
    await async_test_db.refresh(patient)

    # Create INACTIVE therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist.id,
        patient_id=patient.id,
        relationship_type="primary",
        is_active=False  # Inactive relationship
    )
    async_test_db.add(relationship)
    await async_test_db.commit()
    await async_test_db.refresh(relationship)

    # Create timeline event for patient
    event = TimelineEvent(
        patient_id=patient.id,
        therapist_id=therapist.id,
        event_type="milestone",
        title="Treatment Milestone",
        description="Completed CBT module",
        event_date=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    async_test_db.add(event)
    await async_test_db.commit()
    await async_test_db.refresh(event)

    # Call verify_timeline_event_access and expect HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await verify_timeline_event_access(
            event_id=event.id,
            therapist_id=therapist.id,
            db=async_test_db
        )

    # Assert: Raises HTTPException with status_code=403
    assert exc_info.value.status_code == 403

    # Assert: Detail message contains "Access denied" or "active relationship"
    detail_lower = exc_info.value.detail.lower()
    assert "access denied" in detail_lower or "active" in detail_lower
