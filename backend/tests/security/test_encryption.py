# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for field-level encryption service.

Tests cover:
1. Basic encrypt/decrypt roundtrip operations
2. Cryptographic properties (different ciphertexts, bytes output)
3. Optional field handling (None values)
4. Key derivation from passphrases (PBKDF2)
5. Key rotation workflows
6. Error handling (invalid keys, corrupted data, wrong keys)
7. Integration with FastAPI dependency system
8. PHI data encryption scenarios
"""
import pytest
import os
from cryptography.fernet import Fernet, InvalidToken
from app.security.encryption import (
    FieldEncryption,
    EncryptionError,
    DecryptionError,
    KeyDerivationError,
    derive_key_from_passphrase,
    rotate_key,
    get_encryption_service,
    generate_new_master_key
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def test_key():
    """Generate a test Fernet key for encryption tests"""
    return Fernet.generate_key()


@pytest.fixture
def encryption_service(test_key):
    """Create FieldEncryption instance with test key"""
    return FieldEncryption(test_key)


@pytest.fixture
def sample_phi_data():
    """Sample PHI data for realistic encryption tests"""
    return {
        "ssn": "123-45-6789",
        "diagnosis": "Major Depressive Disorder, recurrent, moderate severity. Patient shows improvement with CBT interventions.",
        "phone": "+1-555-123-4567",
        "email": "patient@example.com",
        "address": "123 Main St, Apt 4B, Springfield, IL 62701",
        "medications": "Sertraline 50mg daily, Lorazepam 0.5mg PRN for anxiety",
        "emergency_contact": "Jane Doe (spouse) - 555-987-6543"
    }


@pytest.fixture
def test_salt():
    """Generate test salt for key derivation tests"""
    return os.urandom(16)


# ============================================================================
# Basic Encryption Tests
# ============================================================================

def test_encrypt_decrypt_roundtrip(encryption_service):
    """Test that encrypt then decrypt returns original plaintext"""
    plaintext = "Sensitive patient information"

    encrypted = encryption_service.encrypt(plaintext)
    decrypted = encryption_service.decrypt(encrypted)

    assert decrypted == plaintext


def test_encrypt_produces_bytes(encryption_service):
    """Test that encrypt returns bytes, not string"""
    plaintext = "Test data"

    encrypted = encryption_service.encrypt(plaintext)

    assert isinstance(encrypted, bytes)
    assert not isinstance(encrypted, str)


def test_encrypt_different_ciphertexts(encryption_service):
    """Test that same plaintext produces different ciphertexts each time (due to timestamp/nonce)"""
    plaintext = "Same plaintext"

    encrypted1 = encryption_service.encrypt(plaintext)
    encrypted2 = encryption_service.encrypt(plaintext)

    # Ciphertexts should be different (includes timestamp)
    assert encrypted1 != encrypted2

    # But both should decrypt to same plaintext
    assert encryption_service.decrypt(encrypted1) == plaintext
    assert encryption_service.decrypt(encrypted2) == plaintext


def test_decrypt_requires_correct_key(test_key):
    """Test that wrong key fails decryption"""
    encryptor1 = FieldEncryption(test_key)
    plaintext = "Secret data"
    encrypted = encryptor1.encrypt(plaintext)

    # Try to decrypt with different key
    different_key = Fernet.generate_key()
    encryptor2 = FieldEncryption(different_key)

    with pytest.raises(DecryptionError, match="corrupted or encrypted with a different key"):
        encryptor2.decrypt(encrypted)


def test_encrypt_empty_string(encryption_service):
    """Test that empty string raises ValueError"""
    with pytest.raises(ValueError, match="Cannot encrypt empty or None plaintext"):
        encryption_service.encrypt("")


def test_encrypt_none_value(encryption_service):
    """Test that None value raises ValueError"""
    with pytest.raises(ValueError, match="Cannot encrypt empty or None plaintext"):
        encryption_service.encrypt(None)


def test_decrypt_empty_bytes(encryption_service):
    """Test that empty bytes raises ValueError"""
    with pytest.raises(ValueError, match="Cannot decrypt empty or None ciphertext"):
        encryption_service.decrypt(b"")


def test_decrypt_none_value(encryption_service):
    """Test that None ciphertext raises ValueError"""
    with pytest.raises(ValueError, match="Cannot decrypt empty or None ciphertext"):
        encryption_service.decrypt(None)


# ============================================================================
# Optional Field Tests
# ============================================================================

def test_encrypt_optional_none(encryption_service):
    """Test that encrypt_optional(None) returns None"""
    result = encryption_service.encrypt_optional(None)

    assert result is None


def test_decrypt_optional_none(encryption_service):
    """Test that decrypt_optional(None) returns None"""
    result = encryption_service.decrypt_optional(None)

    assert result is None


def test_encrypt_optional_value(encryption_service):
    """Test that encrypt_optional encrypts non-None values"""
    plaintext = "Optional field value"

    encrypted = encryption_service.encrypt_optional(plaintext)

    assert encrypted is not None
    assert isinstance(encrypted, bytes)

    # Should be able to decrypt it
    decrypted = encryption_service.decrypt_optional(encrypted)
    assert decrypted == plaintext


def test_encrypt_decrypt_optional_roundtrip(encryption_service):
    """Test full roundtrip with optional methods"""
    plaintext = "Nullable field"

    encrypted = encryption_service.encrypt_optional(plaintext)
    decrypted = encryption_service.decrypt_optional(encrypted)

    assert decrypted == plaintext


# ============================================================================
# Key Derivation Tests
# ============================================================================

def test_derive_key_from_passphrase(test_salt):
    """Test that key derivation produces valid Fernet key"""
    passphrase = "my_secure_passphrase_123"

    key = derive_key_from_passphrase(passphrase, test_salt)

    # Key should be bytes
    assert isinstance(key, bytes)

    # Should be able to create FieldEncryption with it
    encryptor = FieldEncryption(key)

    # Should be able to encrypt/decrypt
    plaintext = "Test data"
    encrypted = encryptor.encrypt(plaintext)
    decrypted = encryptor.decrypt(encrypted)
    assert decrypted == plaintext


def test_derive_key_requires_salt():
    """Test that derive_key_from_passphrase fails without valid salt"""
    passphrase = "my_passphrase"

    # Empty salt
    with pytest.raises(ValueError, match="Salt must be at least 16 bytes"):
        derive_key_from_passphrase(passphrase, b"")

    # Salt too short
    with pytest.raises(ValueError, match="Salt must be at least 16 bytes"):
        derive_key_from_passphrase(passphrase, b"short")


def test_derive_key_deterministic(test_salt):
    """Test that same passphrase + salt produces same key"""
    passphrase = "consistent_passphrase"

    key1 = derive_key_from_passphrase(passphrase, test_salt)
    key2 = derive_key_from_passphrase(passphrase, test_salt)

    assert key1 == key2


def test_derive_key_different_salts():
    """Test that different salts produce different keys"""
    passphrase = "same_passphrase"
    salt1 = os.urandom(16)
    salt2 = os.urandom(16)

    key1 = derive_key_from_passphrase(passphrase, salt1)
    key2 = derive_key_from_passphrase(passphrase, salt2)

    assert key1 != key2


def test_derive_key_empty_passphrase(test_salt):
    """Test that empty passphrase raises ValueError"""
    with pytest.raises(ValueError, match="Passphrase cannot be empty"):
        derive_key_from_passphrase("", test_salt)


def test_derive_key_custom_iterations(test_salt):
    """Test key derivation with custom iteration count"""
    passphrase = "test_passphrase"

    # Should work with custom iterations
    key = derive_key_from_passphrase(passphrase, test_salt, iterations=50_000)

    assert isinstance(key, bytes)

    # Should be valid Fernet key
    encryptor = FieldEncryption(key)
    encrypted = encryptor.encrypt("test")
    assert encryptor.decrypt(encrypted) == "test"


# ============================================================================
# Key Rotation Tests
# ============================================================================

def test_rotate_key_success():
    """Test that key rotation works successfully"""
    old_key = Fernet.generate_key()
    new_key = Fernet.generate_key()

    # Encrypt with old key
    old_encryptor = FieldEncryption(old_key)
    plaintext = "Data to rotate"
    encrypted_old = old_encryptor.encrypt(plaintext)

    # Rotate to new key
    encrypted_new = rotate_key(old_key, new_key, encrypted_old)

    # Should be able to decrypt with new key
    new_encryptor = FieldEncryption(new_key)
    decrypted = new_encryptor.decrypt(encrypted_new)

    assert decrypted == plaintext


def test_rotate_key_decrypts_with_new_key():
    """Test that rotated data decrypts with new key"""
    old_key = Fernet.generate_key()
    new_key = Fernet.generate_key()

    old_encryptor = FieldEncryption(old_key)
    plaintext = "Sensitive PHI data"
    encrypted_old = old_encryptor.encrypt(plaintext)

    # Rotate
    encrypted_new = rotate_key(old_key, new_key, encrypted_old)

    # Decrypt with new key
    new_encryptor = FieldEncryption(new_key)
    result = new_encryptor.decrypt(encrypted_new)

    assert result == plaintext


def test_rotate_key_old_key_fails():
    """Test that old key fails to decrypt after rotation"""
    old_key = Fernet.generate_key()
    new_key = Fernet.generate_key()

    old_encryptor = FieldEncryption(old_key)
    plaintext = "Data before rotation"
    encrypted_old = old_encryptor.encrypt(plaintext)

    # Rotate
    encrypted_new = rotate_key(old_key, new_key, encrypted_old)

    # Old key should not work on rotated data
    with pytest.raises(DecryptionError):
        old_encryptor.decrypt(encrypted_new)


def test_rotate_key_preserves_data():
    """Test that plaintext is unchanged after rotation"""
    old_key = Fernet.generate_key()
    new_key = Fernet.generate_key()

    old_encryptor = FieldEncryption(old_key)
    original_plaintext = "Important patient data that must not be corrupted"
    encrypted_old = old_encryptor.encrypt(original_plaintext)

    # Rotate
    encrypted_new = rotate_key(old_key, new_key, encrypted_old)

    # Decrypt and verify data integrity
    new_encryptor = FieldEncryption(new_key)
    decrypted_plaintext = new_encryptor.decrypt(encrypted_new)

    assert decrypted_plaintext == original_plaintext


def test_rotate_key_with_wrong_old_key():
    """Test that rotation fails if old key is incorrect"""
    old_key = Fernet.generate_key()
    wrong_key = Fernet.generate_key()
    new_key = Fernet.generate_key()

    # Encrypt with old key
    old_encryptor = FieldEncryption(old_key)
    encrypted = old_encryptor.encrypt("data")

    # Try to rotate with wrong old key
    with pytest.raises(DecryptionError):
        rotate_key(wrong_key, new_key, encrypted)


# ============================================================================
# Error Handling Tests
# ============================================================================

def test_decrypt_invalid_ciphertext(encryption_service):
    """Test that invalid ciphertext raises DecryptionError"""
    invalid_ciphertext = b"this_is_not_valid_encrypted_data"

    with pytest.raises(DecryptionError, match="corrupted or encrypted with a different key"):
        encryption_service.decrypt(invalid_ciphertext)


def test_decrypt_corrupted_data(encryption_service):
    """Test that corrupted ciphertext is detected"""
    plaintext = "Valid data"
    encrypted = encryption_service.encrypt(plaintext)

    # Corrupt the encrypted data
    corrupted = encrypted[:-10] + b"corrupted!"

    with pytest.raises(DecryptionError):
        encryption_service.decrypt(corrupted)


def test_invalid_master_key():
    """Test that invalid master key raises ValueError"""
    invalid_key = b"not_a_valid_fernet_key"

    with pytest.raises(ValueError, match="Invalid master key format"):
        FieldEncryption(invalid_key)


def test_encryption_service_requires_key(monkeypatch):
    """Test that get_encryption_service works when ENCRYPTION_MASTER_KEY is not set"""
    # Remove env var
    monkeypatch.delenv("ENCRYPTION_MASTER_KEY", raising=False)

    # Should generate random key with warning (for development)
    service = get_encryption_service()

    assert isinstance(service, FieldEncryption)

    # Should be functional
    encrypted = service.encrypt("test")
    decrypted = service.decrypt(encrypted)
    assert decrypted == "test"


def test_encryption_service_with_env_key(monkeypatch):
    """Test that get_encryption_service uses ENCRYPTION_MASTER_KEY from environment"""
    test_key = Fernet.generate_key().decode('utf-8')
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", test_key)

    service = get_encryption_service()

    assert isinstance(service, FieldEncryption)

    # Should work correctly
    encrypted = service.encrypt("test data")
    decrypted = service.decrypt(encrypted)
    assert decrypted == "test data"


def test_encryption_service_with_invalid_env_key(monkeypatch):
    """Test that invalid ENCRYPTION_MASTER_KEY raises error"""
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", "invalid_key_format")

    with pytest.raises(ValueError, match="Invalid ENCRYPTION_MASTER_KEY"):
        get_encryption_service()


# ============================================================================
# Integration Tests
# ============================================================================

def test_encryption_service_dependency(monkeypatch):
    """Test that FastAPI dependency injection works correctly"""
    # Set valid key in environment
    test_key = Fernet.generate_key().decode('utf-8')
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", test_key)

    # Get service via dependency
    service = get_encryption_service()

    assert isinstance(service, FieldEncryption)
    assert service.fernet is not None


def test_encrypt_phi_data(encryption_service, sample_phi_data):
    """Test encryption of realistic PHI data"""
    # Encrypt all PHI fields
    encrypted_phi = {}
    for field, value in sample_phi_data.items():
        encrypted_phi[field] = encryption_service.encrypt(value)

    # All encrypted values should be bytes
    for field, encrypted_value in encrypted_phi.items():
        assert isinstance(encrypted_value, bytes)

    # Decrypt and verify all fields
    decrypted_phi = {}
    for field, encrypted_value in encrypted_phi.items():
        decrypted_phi[field] = encryption_service.decrypt(encrypted_value)

    # Should match original
    assert decrypted_phi == sample_phi_data


def test_encrypt_long_phi_text(encryption_service):
    """Test encryption of long clinical notes"""
    long_note = """
    Patient presents with persistent symptoms of major depressive disorder.
    Current treatment includes weekly CBT sessions and pharmacological intervention
    with Sertraline 50mg daily. Patient reports moderate improvement in mood and
    decreased frequency of negative thought patterns. Sleep quality remains poor,
    averaging 5-6 hours per night with frequent awakenings.

    Treatment goals for next session:
    1. Review sleep hygiene practices
    2. Practice cognitive restructuring techniques
    3. Assess medication efficacy
    4. Discuss work-related stressors

    Risk assessment: Low acute risk. No suicidal ideation reported. Patient has
    strong social support system and engaged in treatment.
    """ * 10  # Make it even longer

    encrypted = encryption_service.encrypt(long_note)
    decrypted = encryption_service.decrypt(encrypted)

    assert decrypted == long_note


def test_encrypt_unicode_phi_data(encryption_service):
    """Test encryption of PHI data with unicode characters"""
    unicode_data = {
        "name": "José García-Martínez",
        "notes": "Patient reports: 'J'ai peur' (anxiety in French)",
        "diagnosis": "焦虑症 (Anxiety disorder in Chinese)"
    }

    for value in unicode_data.values():
        encrypted = encryption_service.encrypt(value)
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == value


def test_generate_new_master_key():
    """Test that generate_new_master_key creates valid key"""
    key_str = generate_new_master_key()

    # Should be a string
    assert isinstance(key_str, str)

    # Should be valid Fernet key
    key_bytes = key_str.encode('utf-8')
    encryptor = FieldEncryption(key_bytes)

    # Should work for encryption
    encrypted = encryptor.encrypt("test")
    decrypted = encryptor.decrypt(encrypted)
    assert decrypted == "test"


# ============================================================================
# Security Property Tests
# ============================================================================

def test_encryption_includes_timestamp(encryption_service):
    """Test that Fernet includes timestamp (prevents replay attacks)"""
    import time

    plaintext = "Time-sensitive data"

    encrypted1 = encryption_service.encrypt(plaintext)
    time.sleep(0.1)  # Small delay
    encrypted2 = encryption_service.encrypt(plaintext)

    # Timestamps should make ciphertexts different
    assert encrypted1 != encrypted2


def test_encryption_is_authenticated(encryption_service):
    """Test that tampering is detected (authenticated encryption)"""
    plaintext = "Protected data"
    encrypted = encryption_service.encrypt(plaintext)

    # Tamper with ciphertext
    tampered = encrypted[:-5] + b"XXXXX"

    # Should raise DecryptionError (authentication failure)
    with pytest.raises(DecryptionError):
        encryption_service.decrypt(tampered)


def test_key_rotation_batch_operation():
    """Test rotating multiple encrypted fields in batch"""
    old_key = Fernet.generate_key()
    new_key = Fernet.generate_key()

    old_encryptor = FieldEncryption(old_key)

    # Simulate database records
    records = [
        {"id": 1, "ssn": "123-45-6789", "diagnosis": "MDD"},
        {"id": 2, "ssn": "987-65-4321", "diagnosis": "GAD"},
        {"id": 3, "ssn": "555-12-3456", "diagnosis": "PTSD"},
    ]

    # Encrypt all records with old key
    encrypted_records = []
    for record in records:
        encrypted_records.append({
            "id": record["id"],
            "ssn": old_encryptor.encrypt(record["ssn"]),
            "diagnosis": old_encryptor.encrypt(record["diagnosis"])
        })

    # Rotate all fields
    rotated_records = []
    for enc_record in encrypted_records:
        rotated_records.append({
            "id": enc_record["id"],
            "ssn": rotate_key(old_key, new_key, enc_record["ssn"]),
            "diagnosis": rotate_key(old_key, new_key, enc_record["diagnosis"])
        })

    # Decrypt with new key and verify
    new_encryptor = FieldEncryption(new_key)
    for i, rotated in enumerate(rotated_records):
        decrypted_ssn = new_encryptor.decrypt(rotated["ssn"])
        decrypted_diagnosis = new_encryptor.decrypt(rotated["diagnosis"])

        assert decrypted_ssn == records[i]["ssn"]
        assert decrypted_diagnosis == records[i]["diagnosis"]


def test_encryption_with_special_characters(encryption_service):
    """Test encryption of data with special characters"""
    special_data = [
        "Patient's diagnosis: anxiety & depression",
        "Notes: <important> [URGENT] {confidential}",
        "Email: patient+test@example.com",
        "Phone: (555) 123-4567 ext. #999",
        "Medication: 50mg/day @ bedtime",
        'Quote: "I\'m feeling better" - patient'
    ]

    for data in special_data:
        encrypted = encryption_service.encrypt(data)
        decrypted = encryption_service.decrypt(encrypted)
        assert decrypted == data
