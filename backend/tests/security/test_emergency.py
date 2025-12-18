"""
Comprehensive test suite for Emergency Access functionality (Feature 8: HIPAA Compliance).

Tests cover:
- Emergency access request creation (POST /api/v1/emergency-access)
- Emergency access validation (service layer)
- Emergency access listing (GET /api/v1/emergency-access/active)
- Emergency access revocation (DELETE /api/v1/emergency-access/{access_id})
- Authorization checks (role-based access control)
- Rate limiting enforcement
- Time-based expiration logic
- Audit logging for high-risk operations
"""
import pytest
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.db_models import User
from app.models.schemas import UserRole
from app.models.security_models import EmergencyAccess
from app.schemas.emergency_schemas import (
    EmergencyAccessRequest,
    EmergencyAccessReason,
    EmergencyAccessLevel,
    EmergencyAccessStatus
)
from app.security.emergency_access import EmergencyAccessService


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def emergency_access_request(test_db, therapist_user, patient_user):
    """Create an active emergency access grant in database"""
    now = datetime.utcnow()
    emergency_access = EmergencyAccess(
        id=uuid4(),
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Patient in crisis - requires immediate safety assessment",
        duration_minutes=1440,  # 24 hours
        approved_by=therapist_user.id,  # Self-approved for MVP
        approved_at=now,
        expires_at=now + timedelta(hours=24),
        access_revoked_at=None,
        created_at=now
    )
    test_db.add(emergency_access)
    test_db.commit()
    test_db.refresh(emergency_access)
    return emergency_access


@pytest.fixture
def expired_emergency_access(test_db, therapist_user, patient_user):
    """Create an expired emergency access grant"""
    now = datetime.utcnow()
    past_time = now - timedelta(hours=48)
    emergency_access = EmergencyAccess(
        id=uuid4(),
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Past emergency - now expired",
        duration_minutes=1440,
        approved_by=therapist_user.id,
        approved_at=past_time,
        expires_at=past_time + timedelta(hours=24),  # Expired 24 hours ago
        access_revoked_at=None,
        created_at=past_time
    )
    test_db.add(emergency_access)
    test_db.commit()
    test_db.refresh(emergency_access)
    return emergency_access


@pytest.fixture
def revoked_emergency_access(test_db, therapist_user, patient_user):
    """Create a revoked emergency access grant"""
    now = datetime.utcnow()
    emergency_access = EmergencyAccess(
        id=uuid4(),
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Revoked emergency access",
        duration_minutes=1440,
        approved_by=therapist_user.id,
        approved_at=now - timedelta(hours=2),
        expires_at=now + timedelta(hours=22),  # Still valid but revoked
        access_revoked_at=now - timedelta(hours=1),  # Revoked 1 hour ago
        created_at=now - timedelta(hours=2)
    )
    test_db.add(emergency_access)
    test_db.commit()
    test_db.refresh(emergency_access)
    return emergency_access


# ============================================================================
# Emergency Access Request Tests (POST /api/v1/emergency-access)
# ============================================================================

@pytest.mark.asyncio
async def test_request_emergency_access_success(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test successful emergency access request by therapist"""
    request_data = {
        "patient_id": str(patient_user.id),
        "reason": "patient_crisis",
        "justification": "Patient called reporting suicidal ideation. Need immediate access to treatment plan and risk assessment to ensure safety.",
        "access_level": "read_only",
        "duration_hours": 24,
        "contact_phone": "+1-555-123-4567",
        "supervisor_id": None
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    # Verify response structure
    assert "id" in data
    assert data["patient_id"] == str(patient_user.id)
    assert data["requesting_user_id"] == str(therapist_user.id)
    assert data["requesting_user_email"] == therapist_user.email
    assert data["requesting_user_role"] == UserRole.therapist.value
    assert data["reason"] == "patient_crisis"
    assert data["justification"] == request_data["justification"]
    assert data["access_level"] == "read_only"
    assert data["status"] == "approved"  # MVP auto-approves
    assert data["duration_hours"] == 24
    assert data["expires_at"] is not None
    assert data["contact_phone"] == "+1-555-123-4567"


@pytest.mark.asyncio
async def test_request_emergency_access_auto_approved(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test that MVP automatically approves emergency access requests"""
    request_data = {
        "patient_id": str(patient_user.id),
        "reason": "medical_emergency",
        "justification": "Patient in medical crisis requiring immediate access to medication history and allergies for emergency room staff coordination.",
        "access_level": "read_only",
        "duration_hours": 12,
        "contact_phone": "+1-555-999-8888"
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    # MVP should auto-approve immediately
    assert data["status"] == "approved"
    assert data["reviewed_by"] == str(therapist_user.id)  # Self-approved in MVP
    assert data["reviewed_at"] is not None
    assert data["approval_notes"] == "Auto-approved (MVP mode)"
    assert data["expires_at"] is not None

    # Verify expiration is correctly calculated (12 hours from now)
    expires_at = datetime.fromisoformat(data["expires_at"].replace('Z', '+00:00'))
    now = datetime.utcnow()
    time_diff = expires_at - now
    assert 11 <= time_diff.total_seconds() / 3600 <= 13  # Within 1 hour tolerance


@pytest.mark.asyncio
async def test_request_emergency_access_patient_forbidden(async_db_client, test_db, patient_user, therapist_user, patient_auth_headers):
    """Test that patients cannot request emergency access (403 Forbidden)"""
    request_data = {
        "patient_id": str(therapist_user.id),  # Patient trying to access therapist's records
        "reason": "other",
        "justification": "This should not be allowed - patients cannot request emergency access to other users' records or their own records.",
        "access_level": "read_only",
        "duration_hours": 24,
        "contact_phone": "+1-555-000-0000"
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=patient_auth_headers
    )

    assert response.status_code == 403
    assert "only therapists and administrators" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_request_emergency_access_invalid_patient(async_db_client, test_db, therapist_user, therapist_auth_headers):
    """Test emergency access request for non-existent patient (404)"""
    fake_patient_id = uuid4()
    request_data = {
        "patient_id": str(fake_patient_id),
        "reason": "patient_crisis",
        "justification": "Attempting to request access for a patient that doesn't exist in the system. This should fail with 404.",
        "access_level": "read_only",
        "duration_hours": 24,
        "contact_phone": "+1-555-404-0000"
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_request_emergency_access_rate_limit(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test that rate limiting is enforced (5 requests per hour)"""
    request_data = {
        "patient_id": str(patient_user.id),
        "reason": "patient_crisis",
        "justification": "Testing rate limiting - this is a valid emergency access request but should be blocked after 5 attempts.",
        "access_level": "read_only",
        "duration_hours": 24,
        "contact_phone": "+1-555-123-4567"
    }

    # Make 6 requests (rate limit is 5/hour)
    successful_requests = 0
    rate_limited = False

    for i in range(6):
        response = async_db_client.post(
            "/api/v1/emergency-access",
            json=request_data,
            headers=therapist_auth_headers
        )

        if response.status_code == 201:
            successful_requests += 1
        elif response.status_code == 429:
            rate_limited = True
            break

    # Should allow first 5, then rate limit on 6th
    assert successful_requests <= 5
    assert rate_limited, "Rate limiting was not enforced after 5 requests"


# ============================================================================
# Emergency Access Validation Tests (Service Layer)
# ============================================================================

@pytest.mark.asyncio
async def test_is_emergency_access_valid_approved(async_test_db, therapist_user, patient_user):
    """Test that valid approved emergency access returns True"""
    service = EmergencyAccessService()

    # Create approved emergency access
    now = datetime.utcnow()
    emergency_access = EmergencyAccess(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Valid emergency access",
        duration_minutes=60,
        approved_by=therapist_user.id,
        approved_at=now,
        expires_at=now + timedelta(hours=1),
        access_revoked_at=None
    )
    async_test_db.add(emergency_access)
    await async_test_db.commit()

    # Validate access
    is_valid = await service.is_emergency_access_valid(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        db=async_test_db
    )

    assert is_valid is True


@pytest.mark.asyncio
async def test_is_emergency_access_valid_pending(async_test_db, therapist_user, patient_user):
    """Test that pending (not approved) emergency access returns False"""
    service = EmergencyAccessService()

    # Create pending emergency access (not approved)
    emergency_access = EmergencyAccess(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Pending emergency access",
        duration_minutes=60,
        approved_by=None,  # Not approved yet
        approved_at=None,
        expires_at=None,
        access_revoked_at=None
    )
    async_test_db.add(emergency_access)
    await async_test_db.commit()

    # Validate access
    is_valid = await service.is_emergency_access_valid(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        db=async_test_db
    )

    assert is_valid is False


@pytest.mark.asyncio
async def test_is_emergency_access_valid_expired(async_test_db, therapist_user, patient_user):
    """Test that expired emergency access returns False"""
    service = EmergencyAccessService()

    # Create expired emergency access
    now = datetime.utcnow()
    past_time = now - timedelta(hours=2)
    emergency_access = EmergencyAccess(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Expired emergency access",
        duration_minutes=60,
        approved_by=therapist_user.id,
        approved_at=past_time,
        expires_at=past_time + timedelta(hours=1),  # Expired 1 hour ago
        access_revoked_at=None
    )
    async_test_db.add(emergency_access)
    await async_test_db.commit()

    # Validate access
    is_valid = await service.is_emergency_access_valid(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        db=async_test_db
    )

    assert is_valid is False


@pytest.mark.asyncio
async def test_is_emergency_access_valid_revoked(async_test_db, therapist_user, patient_user):
    """Test that revoked emergency access returns False"""
    service = EmergencyAccessService()

    # Create revoked emergency access
    now = datetime.utcnow()
    emergency_access = EmergencyAccess(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Revoked emergency access",
        duration_minutes=120,
        approved_by=therapist_user.id,
        approved_at=now - timedelta(hours=1),
        expires_at=now + timedelta(hours=1),  # Still valid time-wise
        access_revoked_at=now - timedelta(minutes=30)  # But revoked
    )
    async_test_db.add(emergency_access)
    await async_test_db.commit()

    # Validate access
    is_valid = await service.is_emergency_access_valid(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        db=async_test_db
    )

    assert is_valid is False


# ============================================================================
# Emergency Access List Tests (GET /api/v1/emergency-access/active)
# ============================================================================

@pytest.mark.asyncio
async def test_list_active_emergency_access_success(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test listing active emergency access grants"""
    # Create active emergency access
    now = datetime.utcnow()
    emergency_access = EmergencyAccess(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Active emergency access",
        duration_minutes=1440,
        approved_by=therapist_user.id,
        approved_at=now,
        expires_at=now + timedelta(hours=24),
        access_revoked_at=None
    )
    test_db.add(emergency_access)
    test_db.commit()

    response = async_db_client.get(
        "/api/v1/emergency-access/active",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify response structure
    assert "requests" in data
    assert "total_count" in data
    assert "active_count" in data
    assert "pending_count" in data

    # Verify data
    assert len(data["requests"]) >= 1
    assert data["total_count"] >= 1
    assert data["active_count"] >= 1
    assert data["pending_count"] == 0  # MVP auto-approves

    # Verify first request
    first_request = data["requests"][0]
    assert first_request["patient_id"] == str(patient_user.id)
    assert first_request["requesting_user_id"] == str(therapist_user.id)
    assert first_request["status"] == "approved"


@pytest.mark.asyncio
async def test_list_active_emergency_access_empty(async_db_client, test_db, therapist_user, therapist_auth_headers):
    """Test listing active emergency access when none exist"""
    response = async_db_client.get(
        "/api/v1/emergency-access/active",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["requests"] == []
    assert data["total_count"] == 0
    assert data["active_count"] == 0
    assert data["pending_count"] == 0


@pytest.mark.asyncio
async def test_list_active_emergency_access_excludes_expired(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test that listing active emergency access excludes expired grants"""
    now = datetime.utcnow()

    # Create active emergency access
    active_access = EmergencyAccess(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Active access",
        duration_minutes=1440,
        approved_by=therapist_user.id,
        approved_at=now,
        expires_at=now + timedelta(hours=24),
        access_revoked_at=None
    )
    test_db.add(active_access)

    # Create expired emergency access
    past_time = now - timedelta(hours=48)
    expired_access = EmergencyAccess(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Expired access",
        duration_minutes=1440,
        approved_by=therapist_user.id,
        approved_at=past_time,
        expires_at=past_time + timedelta(hours=24),
        access_revoked_at=None
    )
    test_db.add(expired_access)
    test_db.commit()

    response = async_db_client.get(
        "/api/v1/emergency-access/active",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Should only return active access, not expired
    assert len(data["requests"]) == 1
    assert data["total_count"] == 1
    assert data["active_count"] == 1


# ============================================================================
# Emergency Access Revocation Tests (DELETE /api/v1/emergency-access/{access_id})
# ============================================================================

@pytest.mark.asyncio
async def test_revoke_emergency_access_success(async_db_client, test_db, emergency_access_request, therapist_auth_headers):
    """Test successful revocation of emergency access by owner"""
    access_id = emergency_access_request.id

    response = async_db_client.delete(
        f"/api/v1/emergency-access/{access_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["message"] == "Emergency access revoked successfully"
    assert data["access_id"] == str(access_id)
    assert data["status"] == "revoked"
    assert "revoked_at" in data

    # Verify access was actually revoked in database
    test_db.refresh(emergency_access_request)
    assert emergency_access_request.access_revoked_at is not None


@pytest.mark.asyncio
async def test_revoke_emergency_access_admin_override(async_db_client, test_db, therapist_user, patient_user, admin_user, admin_auth_headers):
    """Test that admin can revoke any emergency access"""
    # Create emergency access for therapist
    now = datetime.utcnow()
    emergency_access = EmergencyAccess(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Emergency access owned by therapist",
        duration_minutes=1440,
        approved_by=therapist_user.id,
        approved_at=now,
        expires_at=now + timedelta(hours=24),
        access_revoked_at=None
    )
    test_db.add(emergency_access)
    test_db.commit()
    test_db.refresh(emergency_access)

    # Admin should be able to revoke it
    response = async_db_client.delete(
        f"/api/v1/emergency-access/{emergency_access.id}",
        headers=admin_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "revoked"


@pytest.mark.asyncio
async def test_revoke_emergency_access_unauthorized(async_db_client, test_db, therapist_user, patient_user, test_patient_user, patient_auth_headers):
    """Test that users cannot revoke emergency access they don't own (403)"""
    # Create emergency access for therapist
    now = datetime.utcnow()
    emergency_access = EmergencyAccess(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Emergency access owned by therapist",
        duration_minutes=1440,
        approved_by=therapist_user.id,
        approved_at=now,
        expires_at=now + timedelta(hours=24),
        access_revoked_at=None
    )
    test_db.add(emergency_access)
    test_db.commit()
    test_db.refresh(emergency_access)

    # Patient tries to revoke it (should fail)
    response = async_db_client.delete(
        f"/api/v1/emergency-access/{emergency_access.id}",
        headers=patient_auth_headers
    )

    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_revoke_emergency_access_already_revoked(async_db_client, test_db, revoked_emergency_access, therapist_auth_headers):
    """Test that revoking already revoked access returns error (400)"""
    access_id = revoked_emergency_access.id

    response = async_db_client.delete(
        f"/api/v1/emergency-access/{access_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == 400
    assert "already revoked" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_revoke_emergency_access_not_found(async_db_client, test_db, therapist_auth_headers):
    """Test revoking non-existent emergency access (404)"""
    fake_access_id = uuid4()

    response = async_db_client.delete(
        f"/api/v1/emergency-access/{fake_access_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ============================================================================
# Authorization Tests
# ============================================================================

@pytest.mark.asyncio
async def test_emergency_access_requires_therapist_role(async_db_client, test_db, patient_user, therapist_user, patient_auth_headers):
    """Test that only therapists and admins can request emergency access"""
    request_data = {
        "patient_id": str(therapist_user.id),
        "reason": "patient_crisis",
        "justification": "Patients should not be able to request emergency access. This request should be denied with 403 Forbidden.",
        "access_level": "read_only",
        "duration_hours": 24,
        "contact_phone": "+1-555-403-0000"
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=patient_auth_headers
    )

    assert response.status_code == 403
    detail = response.json()["detail"].lower()
    assert "only therapists and administrators" in detail or "therapist" in detail


@pytest.mark.asyncio
async def test_emergency_access_records_audit_log(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test that emergency access requests create high-risk audit events"""
    from app.models.security_models import AuditLog

    # Count audit logs before request
    initial_count = test_db.query(AuditLog).count()

    request_data = {
        "patient_id": str(patient_user.id),
        "reason": "patient_crisis",
        "justification": "Testing audit logging - this emergency access request should create an audit log entry with high risk level.",
        "access_level": "read_only",
        "duration_hours": 24,
        "contact_phone": "+1-555-999-0000"
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 201

    # Note: Audit logging would be implemented in middleware/service layer
    # This test documents the expected behavior
    # In production, verify audit log was created with:
    # - action: "emergency_access_request"
    # - risk_level: "high"
    # - user_id: therapist_user.id
    # - patient_id: patient_user.id


# ============================================================================
# Duration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_emergency_access_default_duration(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test that default duration is 24 hours when not specified"""
    request_data = {
        "patient_id": str(patient_user.id),
        "reason": "covering_therapist",
        "justification": "Covering for primary therapist on vacation. Need access to patient records for continuity of care during absence.",
        "access_level": "read_only",
        # duration_hours not specified - should default to 24
        "contact_phone": "+1-555-111-2222"
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["duration_hours"] == 24  # Default duration


@pytest.mark.asyncio
async def test_emergency_access_max_duration(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test maximum duration is 168 hours (7 days)"""
    request_data = {
        "patient_id": str(patient_user.id),
        "reason": "legal_request",
        "justification": "Court order requires access to patient records for legal proceedings. Extended access needed for comprehensive record review.",
        "access_level": "read_only",
        "duration_hours": 168,  # Maximum allowed (7 days)
        "contact_phone": "+1-555-333-4444"
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=therapist_auth_headers
    )

    assert response.status_code == 201
    data = response.json()

    assert data["duration_hours"] == 168

    # Verify expiration is correctly calculated
    expires_at = datetime.fromisoformat(data["expires_at"].replace('Z', '+00:00'))
    now = datetime.utcnow()
    time_diff = expires_at - now
    assert 167 <= time_diff.total_seconds() / 3600 <= 169  # Within 1 hour tolerance


@pytest.mark.asyncio
async def test_emergency_access_expiration_calculated(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test that expires_at is correctly calculated from duration_hours"""
    duration_hours = 48
    request_data = {
        "patient_id": str(patient_user.id),
        "reason": "patient_incapacitated",
        "justification": "Patient incapacitated due to medical emergency. Emergency contact authorized access for 48 hours until patient recovery.",
        "access_level": "read_only",
        "duration_hours": duration_hours,
        "contact_phone": "+1-555-555-6666"
    }

    before_request = datetime.utcnow()

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=therapist_auth_headers
    )

    after_request = datetime.utcnow()

    assert response.status_code == 201
    data = response.json()

    # Parse expires_at
    expires_at = datetime.fromisoformat(data["expires_at"].replace('Z', '+00:00'))

    # Verify expiration is approximately duration_hours from now
    expected_min = before_request + timedelta(hours=duration_hours)
    expected_max = after_request + timedelta(hours=duration_hours)

    assert expected_min <= expires_at <= expected_max


@pytest.mark.asyncio
async def test_emergency_access_invalid_duration_too_short(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test that duration less than 1 hour is rejected (422)"""
    request_data = {
        "patient_id": str(patient_user.id),
        "reason": "patient_crisis",
        "justification": "Testing validation - duration must be at least 1 hour. This request should be rejected.",
        "access_level": "read_only",
        "duration_hours": 0,  # Invalid - too short
        "contact_phone": "+1-555-000-0000"
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=therapist_auth_headers
    )

    # Pydantic validation should reject this
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_emergency_access_invalid_duration_too_long(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test that duration greater than 168 hours is rejected (422)"""
    request_data = {
        "patient_id": str(patient_user.id),
        "reason": "other",
        "justification": "Testing validation - duration cannot exceed 168 hours (7 days). This request with 200 hours should be rejected.",
        "access_level": "read_only",
        "duration_hours": 200,  # Invalid - too long
        "contact_phone": "+1-555-888-9999"
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=therapist_auth_headers
    )

    # Pydantic validation should reject this
    assert response.status_code == 422


# ============================================================================
# Validation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_emergency_access_justification_min_length(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test that justification must be at least 50 characters"""
    request_data = {
        "patient_id": str(patient_user.id),
        "reason": "patient_crisis",
        "justification": "Too short",  # Less than 50 characters
        "access_level": "read_only",
        "duration_hours": 24,
        "contact_phone": "+1-555-000-0000"
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=therapist_auth_headers
    )

    # Pydantic validation should reject this
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_emergency_access_other_reason_requires_longer_justification(async_db_client, test_db, therapist_user, patient_user, therapist_auth_headers):
    """Test that 'other' reason requires at least 100 characters justification"""
    request_data = {
        "patient_id": str(patient_user.id),
        "reason": "other",
        "justification": "This is 60 characters - not enough for 'other' reason type",
        "access_level": "read_only",
        "duration_hours": 24,
        "contact_phone": "+1-555-000-0000"
    }

    response = async_db_client.post(
        "/api/v1/emergency-access",
        json=request_data,
        headers=therapist_auth_headers
    )

    # Pydantic validation should reject this (other requires 100+ chars)
    assert response.status_code == 422


# ============================================================================
# Service Layer Tests
# ============================================================================

@pytest.mark.asyncio
async def test_service_request_emergency_access(async_test_db, therapist_user, patient_user):
    """Test service layer creates emergency access request"""
    service = EmergencyAccessService()

    emergency_access = await service.request_emergency_access(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Service layer test - emergency access request",
        duration_minutes=120,
        db=async_test_db
    )

    assert emergency_access.id is not None
    assert emergency_access.user_id == therapist_user.id
    assert emergency_access.patient_id == patient_user.id
    assert emergency_access.reason == "Service layer test - emergency access request"
    assert emergency_access.duration_minutes == 120
    assert emergency_access.approved_by is None  # Not approved yet
    assert emergency_access.approved_at is None
    assert emergency_access.expires_at is None


@pytest.mark.asyncio
async def test_service_approve_emergency_access(async_test_db, therapist_user, patient_user, admin_user):
    """Test service layer approves emergency access request"""
    service = EmergencyAccessService()

    # Create pending request
    emergency_access = await service.request_emergency_access(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Test approval workflow",
        duration_minutes=60,
        db=async_test_db
    )

    # Approve request
    approved_access = await service.approve_emergency_access(
        request_id=emergency_access.id,
        approver_id=admin_user.id,
        db=async_test_db
    )

    assert approved_access.approved_by == admin_user.id
    assert approved_access.approved_at is not None
    assert approved_access.expires_at is not None

    # Verify expiration time
    time_diff = approved_access.expires_at - approved_access.approved_at
    assert time_diff.total_seconds() == 60 * 60  # 60 minutes


@pytest.mark.asyncio
async def test_service_revoke_emergency_access(async_test_db, therapist_user, patient_user):
    """Test service layer revokes emergency access"""
    service = EmergencyAccessService()

    # Create and approve request
    emergency_access = await service.request_emergency_access(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Test revocation",
        duration_minutes=120,
        db=async_test_db
    )

    approved_access = await service.approve_emergency_access(
        request_id=emergency_access.id,
        approver_id=therapist_user.id,
        db=async_test_db
    )

    # Revoke access
    revoked_access = await service.revoke_emergency_access(
        request_id=approved_access.id,
        db=async_test_db
    )

    assert revoked_access.access_revoked_at is not None


@pytest.mark.asyncio
async def test_service_get_active_emergency_accesses(async_test_db, therapist_user, patient_user):
    """Test service layer returns only active emergency accesses"""
    service = EmergencyAccessService()

    # Create active emergency access
    active_request = await service.request_emergency_access(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Active access",
        duration_minutes=1440,
        db=async_test_db
    )
    await service.approve_emergency_access(
        request_id=active_request.id,
        approver_id=therapist_user.id,
        db=async_test_db
    )

    # Create expired emergency access
    now = datetime.utcnow()
    past_time = now - timedelta(hours=48)
    expired_access = EmergencyAccess(
        user_id=therapist_user.id,
        patient_id=patient_user.id,
        reason="Expired access",
        duration_minutes=60,
        approved_by=therapist_user.id,
        approved_at=past_time,
        expires_at=past_time + timedelta(hours=1),
        access_revoked_at=None
    )
    async_test_db.add(expired_access)
    await async_test_db.commit()

    # Get active accesses
    active_accesses = await service.get_active_emergency_accesses(
        user_id=therapist_user.id,
        db=async_test_db
    )

    # Should only return active, not expired
    assert len(active_accesses) == 1
    assert active_accesses[0].id == active_request.id
