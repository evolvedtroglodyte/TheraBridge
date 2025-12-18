"""
Comprehensive test suite for Consent Management endpoints.

Tests consent recording, querying, revocation, and status checking for HIPAA compliance.
Validates authorization rules and consent workflow for all 6 consent types.

Test Coverage:
- Consent recording (patient/therapist/admin)
- Consent queries with filtering
- Consent status summaries
- Consent revocation
- Authorization enforcement
- Signature capture and IP tracking
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import User, TherapistPatient
from app.models.security_models import ConsentRecord
from app.models.schemas import UserRole
from app.schemas.consent_schemas import ConsentType


# ============================================================================
# Consent Recording Tests
# ============================================================================

@pytest.mark.asyncio
async def test_record_consent_success(async_client, patient_user, patient_auth_headers, async_test_db):
    """Patient successfully records own consent"""
    response = await async_client.post(
        "/api/v1/consent",
        json={
            "patient_id": str(patient_user.id),
            "consent_type": "treatment",
            "consent_status": "granted",
            "consent_method": "electronic",
            "consent_text": "I consent to receive treatment from this therapist and understand the risks and benefits.",
            "version": "1.0",
            "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        },
        headers=patient_auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["consent_type"] == "treatment"
    assert data["consent_status"] == "granted"
    assert data["patient_id"] == str(patient_user.id)
    assert data["signature_data"] is not None
    assert data["ip_address"] is not None  # IP address was captured


@pytest.mark.asyncio
async def test_record_consent_therapist_for_patient(
    async_client, therapist_user, patient_user, therapist_auth_headers, async_test_db
):
    """Therapist records consent for assigned patient"""
    # Create therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    async_test_db.add(relationship)
    await async_test_db.commit()

    response = await async_client.post(
        "/api/v1/consent",
        json={
            "patient_id": str(patient_user.id),
            "consent_type": "telehealth",
            "consent_status": "granted",
            "consent_method": "electronic",
            "consent_text": "I consent to receive services via telehealth platform and understand the technology requirements.",
            "version": "2.0",
            "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        },
        headers=therapist_auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["consent_type"] == "telehealth"
    assert data["patient_id"] == str(patient_user.id)


@pytest.mark.asyncio
async def test_record_consent_with_signature(async_client, patient_user, patient_auth_headers):
    """Consent with electronic signature is stored correctly"""
    signature_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    response = await async_client.post(
        "/api/v1/consent",
        json={
            "patient_id": str(patient_user.id),
            "consent_type": "recording",
            "consent_status": "granted",
            "consent_method": "electronic",
            "consent_text": "I consent to have my therapy sessions recorded for quality assurance and training purposes.",
            "version": "1.0",
            "signature_data": signature_base64
        },
        headers=patient_auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["signature_data"] == signature_base64
    assert data["consent_method"] == "electronic"


@pytest.mark.asyncio
async def test_record_consent_ip_address_recorded(async_client, patient_user, patient_auth_headers):
    """IP address is captured when recording electronic consent"""
    response = await async_client.post(
        "/api/v1/consent",
        json={
            "patient_id": str(patient_user.id),
            "consent_type": "data_sharing",
            "consent_status": "granted",
            "consent_method": "electronic",
            "consent_text": "I consent to share my de-identified data with approved third parties for research purposes.",
            "version": "1.0",
            "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        },
        headers=patient_auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["ip_address"] is not None
    assert len(data["ip_address"]) > 0


@pytest.mark.asyncio
async def test_record_consent_invalid_type(async_client, patient_user, patient_auth_headers):
    """Error returned for invalid consent type"""
    response = await async_client.post(
        "/api/v1/consent",
        json={
            "patient_id": str(patient_user.id),
            "consent_type": "invalid_type",
            "consent_status": "granted",
            "consent_method": "electronic",
            "consent_text": "Some consent text that is long enough to pass validation.",
            "version": "1.0",
            "signature_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
        },
        headers=patient_auth_headers
    )

    assert response.status_code == 422  # Validation error


# ============================================================================
# Consent Query Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_patient_consents_own(async_client, patient_user, patient_auth_headers, async_test_db):
    """Patient views own consent history"""
    # Create multiple consent records
    consents = [
        ConsentRecord(
            patient_id=patient_user.id,
            consent_type="treatment",
            version="1.0",
            consented=True,
            consent_text="Treatment consent text",
            ip_address="192.168.1.1",
            consented_at=datetime.utcnow()
        ),
        ConsentRecord(
            patient_id=patient_user.id,
            consent_type="telehealth",
            version="1.0",
            consented=True,
            consent_text="Telehealth consent text",
            ip_address="192.168.1.1",
            consented_at=datetime.utcnow()
        )
    ]
    for consent in consents:
        async_test_db.add(consent)
    await async_test_db.commit()

    response = await async_client.get(
        f"/api/v1/consent/patients/{patient_user.id}/consents",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    assert len(data["consents"]) == 2


@pytest.mark.asyncio
async def test_get_patient_consents_therapist(
    async_client, therapist_user, patient_user, therapist_auth_headers, async_test_db
):
    """Therapist views assigned patient's consents"""
    # Create therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist_user.id,
        patient_id=patient_user.id,
        relationship_type="primary",
        is_active=True
    )
    async_test_db.add(relationship)

    # Create consent
    consent = ConsentRecord(
        patient_id=patient_user.id,
        consent_type="treatment",
        version="1.0",
        consented=True,
        consent_text="Treatment consent text",
        ip_address="192.168.1.1",
        consented_at=datetime.utcnow()
    )
    async_test_db.add(consent)
    await async_test_db.commit()

    response = await async_client.get(
        f"/api/v1/consent/patients/{patient_user.id}/consents",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] >= 1


@pytest.mark.asyncio
async def test_get_patient_consents_admin(
    async_client, admin_user, patient_user, admin_auth_headers, async_test_db
):
    """Admin can view any patient's consents"""
    # Create consent
    consent = ConsentRecord(
        patient_id=patient_user.id,
        consent_type="treatment",
        version="1.0",
        consented=True,
        consent_text="Treatment consent text",
        ip_address="192.168.1.1",
        consented_at=datetime.utcnow()
    )
    async_test_db.add(consent)
    await async_test_db.commit()

    response = await async_client.get(
        f"/api/v1/consent/patients/{patient_user.id}/consents",
        headers=admin_auth_headers
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_patient_consents_unauthorized(
    async_client, patient_user, therapist_user, therapist_auth_headers, async_test_db
):
    """403 error when therapist tries to access unassigned patient"""
    # No relationship created
    response = await async_client.get(
        f"/api/v1/consent/patients/{patient_user.id}/consents",
        headers=therapist_auth_headers
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_patient_consents_filter_by_type(
    async_client, patient_user, patient_auth_headers, async_test_db
):
    """Filtering consents by type works correctly"""
    # Create multiple consent types
    consents = [
        ConsentRecord(
            patient_id=patient_user.id,
            consent_type="treatment",
            version="1.0",
            consented=True,
            consent_text="Treatment consent text",
            ip_address="192.168.1.1",
            consented_at=datetime.utcnow()
        ),
        ConsentRecord(
            patient_id=patient_user.id,
            consent_type="telehealth",
            version="1.0",
            consented=True,
            consent_text="Telehealth consent text",
            ip_address="192.168.1.1",
            consented_at=datetime.utcnow()
        ),
        ConsentRecord(
            patient_id=patient_user.id,
            consent_type="telehealth",
            version="2.0",
            consented=True,
            consent_text="Updated telehealth consent text",
            ip_address="192.168.1.1",
            consented_at=datetime.utcnow()
        )
    ]
    for consent in consents:
        async_test_db.add(consent)
    await async_test_db.commit()

    # Filter for telehealth only
    response = await async_client.get(
        f"/api/v1/consent/patients/{patient_user.id}/consents?consent_type=telehealth",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    assert all(c["consent_type"] == "telehealth" for c in data["consents"])


# ============================================================================
# Consent Status Tests
# ============================================================================

@pytest.mark.asyncio
async def test_get_consent_status_all_types(
    async_client, patient_user, patient_auth_headers, async_test_db
):
    """Consent status returns all 6 consent types"""
    # Create some consents
    consents = [
        ConsentRecord(
            patient_id=patient_user.id,
            consent_type="treatment",
            version="1.0",
            consented=True,
            consent_text="Treatment consent text",
            ip_address="192.168.1.1",
            consented_at=datetime.utcnow()
        ),
        ConsentRecord(
            patient_id=patient_user.id,
            consent_type="telehealth",
            version="1.0",
            consented=True,
            consent_text="Telehealth consent text",
            ip_address="192.168.1.1",
            consented_at=datetime.utcnow()
        )
    ]
    for consent in consents:
        async_test_db.add(consent)
    await async_test_db.commit()

    response = await async_client.get(
        f"/api/v1/consent/patients/{patient_user.id}/consent/status",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # All 6 consent types present
    expected_types = ["treatment", "hipaa_notice", "telehealth", "recording", "data_sharing", "research"]
    for consent_type in expected_types:
        assert consent_type in data
        assert isinstance(data[consent_type], bool)

    # Verify granted consents are True
    assert data["treatment"] is True
    assert data["telehealth"] is True
    # Verify ungranteed consents are False
    assert data["recording"] is False
    assert data["research"] is False


@pytest.mark.asyncio
async def test_is_consent_valid_true(async_client, patient_user, patient_auth_headers, async_test_db):
    """Consent is valid if consented and not expired/revoked"""
    # Create valid consent
    consent = ConsentRecord(
        patient_id=patient_user.id,
        consent_type="recording",
        version="1.0",
        consented=True,
        consent_text="Recording consent text",
        ip_address="192.168.1.1",
        consented_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=365)  # Expires in 1 year
    )
    async_test_db.add(consent)
    await async_test_db.commit()

    response = await async_client.get(
        f"/api/v1/consent/patients/{patient_user.id}/consent/status",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["recording"] is True


@pytest.mark.asyncio
async def test_is_consent_valid_expired(async_client, patient_user, patient_auth_headers, async_test_db):
    """Consent is invalid if expired"""
    # Create expired consent
    consent = ConsentRecord(
        patient_id=patient_user.id,
        consent_type="data_sharing",
        version="1.0",
        consented=True,
        consent_text="Data sharing consent text",
        ip_address="192.168.1.1",
        consented_at=datetime.utcnow() - timedelta(days=400),
        expires_at=datetime.utcnow() - timedelta(days=1)  # Expired yesterday
    )
    async_test_db.add(consent)
    await async_test_db.commit()

    response = await async_client.get(
        f"/api/v1/consent/patients/{patient_user.id}/consent/status",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["data_sharing"] is False


@pytest.mark.asyncio
async def test_is_consent_valid_revoked(async_client, patient_user, patient_auth_headers, async_test_db):
    """Consent is invalid if revoked"""
    # Create revoked consent
    consent = ConsentRecord(
        patient_id=patient_user.id,
        consent_type="research",
        version="1.0",
        consented=True,
        consent_text="Research consent text",
        ip_address="192.168.1.1",
        consented_at=datetime.utcnow() - timedelta(days=30),
        revoked_at=datetime.utcnow() - timedelta(days=5)  # Revoked 5 days ago
    )
    async_test_db.add(consent)
    await async_test_db.commit()

    response = await async_client.get(
        f"/api/v1/consent/patients/{patient_user.id}/consent/status",
        headers=patient_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert data["research"] is False


# ============================================================================
# Consent Revocation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_revoke_consent_success(async_client, patient_user, patient_auth_headers, async_test_db):
    """Consent can be revoked successfully"""
    # Create consent
    consent = ConsentRecord(
        patient_id=patient_user.id,
        consent_type="recording",
        version="1.0",
        consented=True,
        consent_text="Recording consent text",
        ip_address="192.168.1.1",
        consented_at=datetime.utcnow()
    )
    async_test_db.add(consent)
    await async_test_db.commit()
    await async_test_db.refresh(consent)

    # Note: Actual revocation endpoint would be needed here
    # For this test, we'll verify the service layer directly
    from app.security.consent import ConsentService
    service = ConsentService()

    revoked = await service.revoke_consent(consent.id, async_test_db)

    assert revoked.revoked_at is not None
    assert revoked.id == consent.id


@pytest.mark.asyncio
async def test_revoke_consent_already_revoked(async_client, patient_user, async_test_db):
    """Error when trying to revoke already revoked consent"""
    # Create revoked consent
    consent = ConsentRecord(
        patient_id=patient_user.id,
        consent_type="recording",
        version="1.0",
        consented=True,
        consent_text="Recording consent text",
        ip_address="192.168.1.1",
        consented_at=datetime.utcnow(),
        revoked_at=datetime.utcnow()
    )
    async_test_db.add(consent)
    await async_test_db.commit()
    await async_test_db.refresh(consent)

    # Try to revoke again
    from app.security.consent import ConsentService
    service = ConsentService()

    with pytest.raises(ValueError, match="already revoked"):
        await service.revoke_consent(consent.id, async_test_db)
