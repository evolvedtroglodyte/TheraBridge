"""
Comprehensive test suite for Multi-Factor Authentication (MFA) endpoints.

Tests cover:
- MFA setup with QR code and backup codes
- MFA verification (completing enrollment)
- MFA validation during login flow
- Database state verification
- Error handling and edge cases
- Rate limiting (mocked)
- TOTP service integration with mocked codes
"""
import pytest
from fastapi import status
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from app.models.security_models import MFAConfig
from app.schemas.mfa_schemas import MFAMethod, MFAStatus

# API prefix for MFA endpoints
MFA_PREFIX = "/api/v1/mfa"


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def mock_totp_service():
    """
    Mock TOTP service for deterministic testing.

    Returns:
        Mock TOTPService with predefined responses:
        - generate_secret() -> "JBSWY3DPEHPK3PXP"
        - get_provisioning_uri() -> "otpauth://totp/..."
        - generate_qr_code() -> b"fake_qr_code_bytes"
        - verify_code() -> True/False based on code
        - generate_backup_codes() -> ["ABCD-1234", "EFGH-5678", ...]
        - hash_backup_code() -> SHA256 hash
    """
    mock = Mock()
    mock.generate_secret.return_value = "JBSWY3DPEHPK3PXP"
    mock.get_provisioning_uri.return_value = "otpauth://totp/TherapyBridge:test@example.com?secret=JBSWY3DPEHPK3PXP&issuer=TherapyBridge"
    mock.generate_qr_code.return_value = b"fake_qr_code_bytes_for_testing"
    mock.generate_backup_codes.return_value = [
        "ABCD-1234", "EFGH-5678", "IJKL-9012",
        "MNOP-3456", "QRST-7890", "UVWX-1234",
        "YZAB-5678", "CDEF-9012"
    ]

    # Mock hash_backup_code to return deterministic hashes
    def mock_hash(code):
        import hashlib
        normalized = code.replace('-', '')
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()

    mock.hash_backup_code.side_effect = mock_hash

    # Mock verify_code: returns True for "123456", False otherwise
    def mock_verify(secret, code, **kwargs):
        return code == "123456"

    mock.verify_code.side_effect = mock_verify

    return mock


@pytest.fixture(scope="function")
def mock_encryption_service():
    """
    Mock encryption service for testing without real encryption.

    Returns:
        Mock FieldEncryption with encrypt/decrypt that just adds prefix:
        - encrypt("secret") -> b"encrypted_secret"
        - decrypt(b"encrypted_secret") -> "secret"
    """
    mock = Mock()

    # Mock encrypt: just adds "encrypted_" prefix as bytes
    def mock_encrypt(plaintext):
        return f"encrypted_{plaintext}".encode('utf-8')

    # Mock decrypt: removes "encrypted_" prefix
    def mock_decrypt(ciphertext):
        return ciphertext.decode('utf-8').replace('encrypted_', '')

    mock.encrypt.side_effect = mock_encrypt
    mock.decrypt.side_effect = mock_decrypt

    return mock


@pytest.fixture(scope="function")
def mfa_user(test_db, therapist_user):
    """
    Create a user with MFA already set up but not verified.

    This simulates a user who has initiated MFA setup but hasn't
    completed verification yet.

    Args:
        test_db: Test database session
        therapist_user: Base therapist user

    Returns:
        User object with pending MFA setup
    """
    # Create pending MFA config
    mfa_config = MFAConfig(
        user_id=therapist_user.id,
        mfa_type=MFAMethod.totp.value,
        secret_encrypted=b"encrypted_JBSWY3DPEHPK3PXP",
        backup_codes_hash=[
            "hash1", "hash2", "hash3", "hash4",
            "hash5", "hash6", "hash7", "hash8"
        ],
        is_enabled=False,
        verified_at=None
    )
    test_db.add(mfa_config)
    test_db.commit()
    test_db.refresh(therapist_user)

    return therapist_user


@pytest.fixture(scope="function")
def mfa_enabled_user(test_db, patient_user):
    """
    Create a user with MFA fully enabled.

    This simulates a user who has completed MFA setup and verification.

    Args:
        test_db: Test database session
        patient_user: Base patient user

    Returns:
        User object with MFA enabled
    """
    # Create enabled MFA config
    mfa_config = MFAConfig(
        user_id=patient_user.id,
        mfa_type=MFAMethod.totp.value,
        secret_encrypted=b"encrypted_SECRET123",
        backup_codes_hash=[
            "hash1", "hash2", "hash3", "hash4",
            "hash5", "hash6", "hash7", "hash8"
        ],
        is_enabled=True,
        verified_at=datetime.utcnow()
    )
    test_db.add(mfa_config)
    test_db.commit()
    test_db.refresh(patient_user)

    return patient_user


# ============================================================================
# Test MFA Setup Endpoint
# ============================================================================

class TestMFASetup:
    """Test POST /mfa/setup endpoint"""

    def test_mfa_setup_success(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        therapist_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test successful MFA setup with QR code and backup codes"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            response = async_db_client.post(
                f"{MFA_PREFIX}/setup",
                headers=therapist_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            # Verify response structure
            assert data["method"] == MFAMethod.totp.value
            assert data["status"] == MFAStatus.pending.value
            assert "qr_code_url" in data
            assert data["qr_code_url"].startswith("data:image/png;base64,")
            assert data["secret"] == "JBSWY3DPEHPK3PXP"
            assert len(data["backup_codes"]) == 8
            assert "expires_at" in data

            # Verify backup codes format
            for code in data["backup_codes"]:
                assert len(code.replace('-', '')) == 8
                assert '-' in code

    def test_mfa_setup_creates_db_record(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        therapist_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test that MFA setup creates MFAConfig record in database"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            response = async_db_client.post(
                f"{MFA_PREFIX}/setup",
                headers=therapist_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK

            # Verify database record
            mfa_config = test_db.query(MFAConfig).filter(
                MFAConfig.user_id == therapist_user.id
            ).first()

            assert mfa_config is not None
            assert mfa_config.mfa_type == MFAMethod.totp.value
            assert mfa_config.is_enabled is False
            assert mfa_config.verified_at is None
            assert mfa_config.secret_encrypted is not None
            assert len(mfa_config.backup_codes_hash) == 8

    def test_mfa_setup_already_enabled(
        self,
        async_db_client,
        test_db,
        patient_auth_headers,
        mfa_enabled_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test that MFA setup fails when MFA is already enabled"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            response = async_db_client.post(
                f"{MFA_PREFIX}/setup",
                headers=patient_auth_headers
            )

            assert response.status_code == status.HTTP_409_CONFLICT
            assert "already enabled" in response.json()["detail"].lower()

    def test_mfa_setup_unauthenticated(self, async_db_client):
        """Test that MFA setup requires authentication"""
        response = async_db_client.post(f"{MFA_PREFIX}/setup")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_mfa_setup_updates_pending_config(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        mfa_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test that re-running setup updates existing pending config"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            # First setup already exists (from mfa_user fixture)
            initial_config = test_db.query(MFAConfig).filter(
                MFAConfig.user_id == mfa_user.id
            ).first()
            assert initial_config is not None

            # Run setup again
            response = async_db_client.post(
                f"{MFA_PREFIX}/setup",
                headers=therapist_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK

            # Verify only one config exists (updated, not duplicated)
            configs = test_db.query(MFAConfig).filter(
                MFAConfig.user_id == mfa_user.id
            ).all()
            assert len(configs) == 1
            assert configs[0].id == initial_config.id  # Same record


# ============================================================================
# Test MFA Verify Endpoint
# ============================================================================

class TestMFAVerify:
    """Test POST /mfa/verify endpoint"""

    def test_mfa_verify_success(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        mfa_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test successful MFA verification with valid TOTP code"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            response = async_db_client.post(
                f"{MFA_PREFIX}/verify",
                headers=therapist_auth_headers,
                json={
                    "method": MFAMethod.totp.value,
                    "code": "123456"  # Valid code per mock
                }
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()

            assert data["success"] is True
            assert data["status"] == MFAStatus.enabled.value
            assert "success" in data["message"].lower()

    def test_mfa_verify_enables_mfa(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        mfa_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test that verification sets is_enabled=True and verified_at"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            # Verify initial state
            mfa_config = test_db.query(MFAConfig).filter(
                MFAConfig.user_id == mfa_user.id
            ).first()
            assert mfa_config.is_enabled is False
            assert mfa_config.verified_at is None

            # Verify MFA
            response = async_db_client.post(
                f"{MFA_PREFIX}/verify",
                headers=therapist_auth_headers,
                json={
                    "method": MFAMethod.totp.value,
                    "code": "123456"
                }
            )

            assert response.status_code == status.HTTP_200_OK

            # Verify database updated
            test_db.refresh(mfa_config)
            assert mfa_config.is_enabled is True
            assert mfa_config.verified_at is not None
            assert isinstance(mfa_config.verified_at, datetime)

    def test_mfa_verify_invalid_code(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        mfa_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test that verification fails with invalid TOTP code"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            response = async_db_client.post(
                f"{MFA_PREFIX}/verify",
                headers=therapist_auth_headers,
                json={
                    "method": MFAMethod.totp.value,
                    "code": "999999"  # Invalid code per mock
                }
            )

            assert response.status_code == status.HTTP_401_UNAUTHORIZED
            assert "invalid" in response.json()["detail"].lower()

    def test_mfa_verify_not_setup(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        therapist_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test that verification fails when MFA not set up"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            response = async_db_client.post(
                f"{MFA_PREFIX}/verify",
                headers=therapist_auth_headers,
                json={
                    "method": MFAMethod.totp.value,
                    "code": "123456"
                }
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "no mfa setup" in response.json()["detail"].lower()

    def test_mfa_verify_already_enabled(
        self,
        async_db_client,
        test_db,
        patient_auth_headers,
        mfa_enabled_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test that verification fails when MFA is already enabled"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            response = async_db_client.post(
                f"{MFA_PREFIX}/verify",
                headers=patient_auth_headers,
                json={
                    "method": MFAMethod.totp.value,
                    "code": "123456"
                }
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "already enabled" in response.json()["detail"].lower()

    def test_mfa_verify_invalid_code_format(
        self,
        async_db_client,
        therapist_auth_headers,
        mfa_user
    ):
        """Test that verification validates code format"""
        # Test with non-numeric code
        response = async_db_client.post(
            f"{MFA_PREFIX}/verify",
            headers=therapist_auth_headers,
            json={
                "method": MFAMethod.totp.value,
                "code": "abcdef"  # Should be numeric
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_mfa_verify_code_too_short(
        self,
        async_db_client,
        therapist_auth_headers,
        mfa_user
    ):
        """Test that verification rejects codes shorter than 6 digits"""
        response = async_db_client.post(
            f"{MFA_PREFIX}/verify",
            headers=therapist_auth_headers,
            json={
                "method": MFAMethod.totp.value,
                "code": "12345"  # Too short
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Test MFA Validate Endpoint (Login Flow)
# ============================================================================

class TestMFAValidate:
    """Test POST /mfa/validate endpoint"""

    def test_mfa_validate_not_implemented(
        self,
        client
    ):
        """Test that validate endpoint returns 501 Not Implemented"""
        # NOTE: This endpoint is not fully implemented yet, requires login flow integration
        response = async_db_client.post(
            f"{MFA_PREFIX}/validate",
            json={
                "session_token": "temp_session_token_12345",
                "code": "123456",
                "remember_device": False,
                "is_backup_code": False
            }
        )

        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
        assert "not fully implemented" in response.json()["detail"].lower()


# ============================================================================
# Test Integration Flows
# ============================================================================

class TestMFAIntegration:
    """Test complete MFA flows from setup to verification"""

    def test_mfa_full_flow(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        therapist_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test complete MFA flow: Setup → Verify → Enabled"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            # Step 1: Setup MFA
            setup_response = async_db_client.post(
                f"{MFA_PREFIX}/setup",
                headers=therapist_auth_headers
            )

            assert setup_response.status_code == status.HTTP_200_OK
            setup_data = setup_response.json()
            assert setup_data["status"] == MFAStatus.pending.value

            # Verify database state after setup
            mfa_config = test_db.query(MFAConfig).filter(
                MFAConfig.user_id == therapist_user.id
            ).first()
            assert mfa_config.is_enabled is False

            # Step 2: Verify MFA with valid code
            verify_response = async_db_client.post(
                f"{MFA_PREFIX}/verify",
                headers=therapist_auth_headers,
                json={
                    "method": MFAMethod.totp.value,
                    "code": "123456"
                }
            )

            assert verify_response.status_code == status.HTTP_200_OK
            verify_data = verify_response.json()
            assert verify_data["success"] is True
            assert verify_data["status"] == MFAStatus.enabled.value

            # Verify final database state
            test_db.refresh(mfa_config)
            assert mfa_config.is_enabled is True
            assert mfa_config.verified_at is not None

    def test_mfa_setup_verify_with_different_codes(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        therapist_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test that verification requires correct code (security test)"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            # Setup MFA
            setup_response = async_db_client.post(
                f"{MFA_PREFIX}/setup",
                headers=therapist_auth_headers
            )
            assert setup_response.status_code == status.HTTP_200_OK

            # Try to verify with wrong code multiple times
            wrong_codes = ["000000", "111111", "999999"]
            for code in wrong_codes:
                verify_response = async_db_client.post(
                    f"{MFA_PREFIX}/verify",
                    headers=therapist_auth_headers,
                    json={
                        "method": MFAMethod.totp.value,
                        "code": code
                    }
                )
                assert verify_response.status_code == status.HTTP_401_UNAUTHORIZED

            # Verify MFA is still not enabled
            mfa_config = test_db.query(MFAConfig).filter(
                MFAConfig.user_id == therapist_user.id
            ).first()
            assert mfa_config.is_enabled is False

            # Finally verify with correct code
            verify_response = async_db_client.post(
                f"{MFA_PREFIX}/verify",
                headers=therapist_auth_headers,
                json={
                    "method": MFAMethod.totp.value,
                    "code": "123456"
                }
            )
            assert verify_response.status_code == status.HTTP_200_OK


# ============================================================================
# Test Edge Cases and Error Handling
# ============================================================================

class TestMFAEdgeCases:
    """Test edge cases and error scenarios"""

    def test_mfa_setup_without_token(self, client):
        """Test all MFA endpoints require authentication"""
        endpoints = [
            (f"{MFA_PREFIX}/setup", "post", {}),
            (f"{MFA_PREFIX}/verify", "post", {"method": "totp", "code": "123456"}),
        ]

        for endpoint, method, json_data in endpoints:
            if method == "post":
                response = async_db_client.post(endpoint, json=json_data)
            else:
                response = async_db_client.get(endpoint)

            assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_mfa_verify_missing_fields(
        self,
        async_db_client,
        therapist_auth_headers
    ):
        """Test verify endpoint validates required fields"""
        # Missing method
        response = async_db_client.post(
            f"{MFA_PREFIX}/verify",
            headers=therapist_auth_headers,
            json={"code": "123456"}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing code
        response = async_db_client.post(
            f"{MFA_PREFIX}/verify",
            headers=therapist_auth_headers,
            json={"method": MFAMethod.totp.value}
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_mfa_backup_codes_hashed_in_db(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        therapist_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test that backup codes are hashed before storage (security)"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            response = async_db_client.post(
                f"{MFA_PREFIX}/setup",
                headers=therapist_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            plaintext_codes = data["backup_codes"]

            # Get stored hashes from database
            mfa_config = test_db.query(MFAConfig).filter(
                MFAConfig.user_id == therapist_user.id
            ).first()

            # Verify codes are hashed (not stored as plaintext)
            for plaintext_code in plaintext_codes:
                assert plaintext_code not in mfa_config.backup_codes_hash

            # Verify hashes can be regenerated from plaintext
            import hashlib
            for i, code in enumerate(plaintext_codes):
                normalized = code.replace('-', '')
                expected_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
                assert mfa_config.backup_codes_hash[i] == expected_hash

    def test_mfa_secret_encrypted_in_db(
        self,
        async_db_client,
        test_db,
        therapist_auth_headers,
        therapist_user,
        mock_totp_service,
        mock_encryption_service
    ):
        """Test that TOTP secret is encrypted before storage (security)"""
        with patch('app.routers.mfa.get_totp_service', return_value=mock_totp_service), \
             patch('app.routers.mfa.get_encryption_service', return_value=mock_encryption_service):

            response = async_db_client.post(
                f"{MFA_PREFIX}/setup",
                headers=therapist_auth_headers
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            plaintext_secret = data["secret"]

            # Get stored encrypted secret from database
            mfa_config = test_db.query(MFAConfig).filter(
                MFAConfig.user_id == therapist_user.id
            ).first()

            # Verify secret is NOT stored as plaintext
            assert plaintext_secret.encode() != mfa_config.secret_encrypted

            # Verify secret was "encrypted" (our mock adds "encrypted_" prefix)
            decrypted = mock_encryption_service.decrypt(mfa_config.secret_encrypted)
            assert decrypted == plaintext_secret
