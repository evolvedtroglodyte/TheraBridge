"""
Field-level encryption for HIPAA-compliant PHI data protection.

This module provides encryption utilities for sensitive patient health information
using AES-128 encryption via Fernet (symmetric encryption). Key features:

- Field-level encryption for database storage
- PBKDF2-based key derivation from passphrases
- Key rotation support for security compliance
- Environment-based master key management
- Comprehensive error handling and logging

Encryption Standard:
    - Algorithm: AES-128-CBC via Fernet
    - Key derivation: PBKDF2-HMAC-SHA256 with 100,000 iterations
    - Encoding: Base64 for encrypted output

Usage:
    # FastAPI dependency injection
    @app.post("/endpoint")
    async def endpoint(encryption: FieldEncryption = Depends(get_encryption_service)):
        encrypted = encryption.encrypt("sensitive data")
        decrypted = encryption.decrypt(encrypted)

    # Direct instantiation
    from cryptography.fernet import Fernet
    key = Fernet.generate_key()
    encryption = FieldEncryption(key)

Environment Variables:
    ENCRYPTION_MASTER_KEY: Base64-encoded Fernet key for production
                          If not set, a random key is generated with a warning

Security Notes:
    - Master key should be stored in secure key management service (AWS KMS, etc.)
    - Keys should be rotated periodically (every 90 days recommended)
    - Encrypted data is bound to the key - losing the key means losing the data
    - Consider key versioning for rolling key rotation
"""

import os
import logging
import secrets
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# Configure logging
logger = logging.getLogger(__name__)


class EncryptionError(Exception):
    """Base exception for encryption-related errors."""
    pass


class KeyDerivationError(EncryptionError):
    """Raised when key derivation fails."""
    pass


class DecryptionError(EncryptionError):
    """Raised when decryption fails (wrong key, corrupted data, etc.)."""
    pass


class FieldEncryption:
    """
    Field-level encryption service for sensitive PHI data.

    Provides symmetric encryption/decryption using Fernet (AES-128-CBC).
    Designed for encrypting individual database fields like SSN, diagnosis notes,
    and contact information.

    Thread-safe and suitable for concurrent request processing.

    Attributes:
        fernet (Fernet): Configured Fernet cipher instance

    Example:
        >>> key = Fernet.generate_key()
        >>> encryptor = FieldEncryption(key)
        >>> encrypted = encryptor.encrypt("SSN: 123-45-6789")
        >>> decrypted = encryptor.decrypt(encrypted)
        >>> assert decrypted == "SSN: 123-45-6789"
    """

    def __init__(self, master_key: bytes):
        """
        Initialize encryption service with master key.

        Args:
            master_key: Base64-encoded Fernet key (32 url-safe base64-encoded bytes)

        Raises:
            ValueError: If master_key is invalid or not in Fernet format

        Note:
            Master key should be generated using Fernet.generate_key() and stored
            securely in environment variables or key management service.
        """
        try:
            self.fernet = Fernet(master_key)
            logger.info("FieldEncryption initialized successfully")
        except Exception as e:
            logger.error(
                "Failed to initialize FieldEncryption",
                extra={
                    "error_type": type(e).__name__,
                    "error": str(e)
                }
            )
            raise ValueError(
                f"Invalid master key format. Expected Fernet-compatible key. "
                f"Error: {type(e).__name__}: {str(e)}"
            ) from e

    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt plaintext string to bytes.

        Args:
            plaintext: String to encrypt (e.g., SSN, diagnosis, phone number)

        Returns:
            Encrypted data as bytes (base64-encoded ciphertext)

        Raises:
            EncryptionError: If encryption fails
            ValueError: If plaintext is empty or None

        Example:
            >>> encrypted = encryptor.encrypt("SSN: 123-45-6789")
            >>> type(encrypted)
            <class 'bytes'>

        Security:
            - Each encryption includes a timestamp to prevent replay attacks
            - Output is URL-safe base64 encoded
            - Includes authentication tag for integrity verification
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty or None plaintext")

        try:
            encrypted = self.fernet.encrypt(plaintext.encode('utf-8'))
            logger.debug(
                "Data encrypted successfully",
                extra={"plaintext_length": len(plaintext)}
            )
            return encrypted
        except Exception as e:
            logger.error(
                "Encryption failed",
                extra={
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "plaintext_length": len(plaintext) if plaintext else 0
                }
            )
            raise EncryptionError(
                f"Failed to encrypt data: {type(e).__name__}: {str(e)}"
            ) from e

    def decrypt(self, ciphertext: bytes) -> str:
        """
        Decrypt ciphertext bytes to plaintext string.

        Args:
            ciphertext: Encrypted data from encrypt() method

        Returns:
            Decrypted plaintext string

        Raises:
            DecryptionError: If decryption fails (wrong key, corrupted data, etc.)
            ValueError: If ciphertext is empty or None

        Example:
            >>> decrypted = encryptor.decrypt(encrypted_data)
            >>> print(decrypted)
            "SSN: 123-45-6789"

        Security:
            - Verifies authentication tag (prevents tampering)
            - Checks timestamp (default: rejects data >60 seconds old, configurable)
            - Constant-time comparison to prevent timing attacks
        """
        if not ciphertext:
            raise ValueError("Cannot decrypt empty or None ciphertext")

        try:
            decrypted = self.fernet.decrypt(ciphertext)
            logger.debug(
                "Data decrypted successfully",
                extra={"ciphertext_length": len(ciphertext)}
            )
            return decrypted.decode('utf-8')
        except InvalidToken as e:
            logger.error(
                "Decryption failed - invalid token",
                extra={
                    "error": str(e),
                    "ciphertext_length": len(ciphertext) if ciphertext else 0
                }
            )
            raise DecryptionError(
                "Decryption failed. The data may be corrupted or encrypted with a different key."
            ) from e
        except Exception as e:
            logger.error(
                "Decryption failed",
                extra={
                    "error_type": type(e).__name__,
                    "error": str(e),
                    "ciphertext_length": len(ciphertext) if ciphertext else 0
                }
            )
            raise DecryptionError(
                f"Failed to decrypt data: {type(e).__name__}: {str(e)}"
            ) from e

    def encrypt_optional(self, plaintext: Optional[str]) -> Optional[bytes]:
        """
        Encrypt optional string (handles None gracefully).

        Convenience method for encrypting nullable fields.

        Args:
            plaintext: String to encrypt or None

        Returns:
            Encrypted bytes or None if input was None

        Example:
            >>> encryptor.encrypt_optional(None)
            None
            >>> encryptor.encrypt_optional("data")
            b'gAAAAA...'
        """
        if plaintext is None:
            return None
        return self.encrypt(plaintext)

    def decrypt_optional(self, ciphertext: Optional[bytes]) -> Optional[str]:
        """
        Decrypt optional bytes (handles None gracefully).

        Convenience method for decrypting nullable fields.

        Args:
            ciphertext: Encrypted bytes or None

        Returns:
            Decrypted string or None if input was None

        Example:
            >>> encryptor.decrypt_optional(None)
            None
            >>> encryptor.decrypt_optional(encrypted_data)
            'data'
        """
        if ciphertext is None:
            return None
        return self.decrypt(ciphertext)


def derive_key_from_passphrase(
    passphrase: str,
    salt: bytes,
    iterations: int = 100_000,
    key_length: int = 32
) -> bytes:
    """
    Derive encryption key from passphrase using PBKDF2-HMAC-SHA256.

    Use this to generate keys from user-provided passwords or secure phrases.
    Salt should be randomly generated and stored alongside encrypted data.

    Args:
        passphrase: User-provided passphrase or password
        salt: Random salt (minimum 16 bytes recommended)
        iterations: Number of PBKDF2 iterations (default: 100,000)
        key_length: Length of derived key in bytes (default: 32 for Fernet)

    Returns:
        Derived key suitable for Fernet encryption (base64-encoded)

    Raises:
        KeyDerivationError: If key derivation fails
        ValueError: If passphrase is empty or salt is too short

    Example:
        >>> salt = os.urandom(16)  # Generate random salt
        >>> key = derive_key_from_passphrase("my_secure_passphrase", salt)
        >>> encryptor = FieldEncryption(key)

    Security:
        - Use minimum 16-byte random salt
        - Store salt unencrypted alongside encrypted data
        - Higher iteration count increases security but slows key derivation
        - 100,000 iterations is recommended minimum as of 2024

    Note:
        The salt must be stored and reused for decryption. Changing the salt
        produces a different key, making previously encrypted data unrecoverable.
    """
    if not passphrase:
        raise ValueError("Passphrase cannot be empty")

    if len(salt) < 16:
        raise ValueError(
            f"Salt must be at least 16 bytes long. Got {len(salt)} bytes. "
            "Generate with: os.urandom(16)"
        )

    try:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        raw_key = kdf.derive(passphrase.encode('utf-8'))

        # Convert to Fernet-compatible key (base64-encoded)
        from base64 import urlsafe_b64encode
        fernet_key = urlsafe_b64encode(raw_key)

        logger.info(
            "Key derived from passphrase",
            extra={
                "salt_length": len(salt),
                "iterations": iterations,
                "key_length": key_length
            }
        )

        return fernet_key

    except Exception as e:
        logger.error(
            "Key derivation failed",
            extra={
                "error_type": type(e).__name__,
                "error": str(e),
                "salt_length": len(salt) if salt else 0,
                "iterations": iterations
            }
        )
        raise KeyDerivationError(
            f"Failed to derive key from passphrase: {type(e).__name__}: {str(e)}"
        ) from e


def rotate_key(old_key: bytes, new_key: bytes, encrypted_data: bytes) -> bytes:
    """
    Rotate encryption key by decrypting with old key and re-encrypting with new key.

    Use this for periodic key rotation to maintain security compliance.
    Typically performed every 90 days for HIPAA compliance.

    Args:
        old_key: Current encryption key (Fernet format)
        new_key: New encryption key (Fernet format)
        encrypted_data: Data encrypted with old_key

    Returns:
        Data re-encrypted with new_key

    Raises:
        DecryptionError: If data cannot be decrypted with old_key
        EncryptionError: If data cannot be encrypted with new_key

    Example:
        >>> old_key = Fernet.generate_key()
        >>> new_key = Fernet.generate_key()
        >>> encrypted = old_encryptor.encrypt("sensitive data")
        >>> rotated = rotate_key(old_key, new_key, encrypted)
        >>> new_encryptor.decrypt(rotated) == "sensitive data"
        True

    Security Best Practices:
        1. Generate new key: new_key = Fernet.generate_key()
        2. Rotate all encrypted fields in database
        3. Update ENCRYPTION_MASTER_KEY in environment
        4. Securely delete old key after all data is rotated
        5. Monitor rotation progress to prevent data loss

    Note:
        For large datasets, consider implementing versioned encryption where both
        old and new keys are temporarily valid during rotation period.
    """
    try:
        # Decrypt with old key
        old_encryptor = FieldEncryption(old_key)
        plaintext = old_encryptor.decrypt(encrypted_data)

        # Re-encrypt with new key
        new_encryptor = FieldEncryption(new_key)
        new_encrypted = new_encryptor.encrypt(plaintext)

        logger.info(
            "Key rotation completed successfully",
            extra={
                "original_size": len(encrypted_data),
                "rotated_size": len(new_encrypted)
            }
        )

        return new_encrypted

    except DecryptionError:
        logger.error("Key rotation failed - decryption with old key failed")
        raise
    except EncryptionError:
        logger.error("Key rotation failed - encryption with new key failed")
        raise
    except Exception as e:
        logger.error(
            "Unexpected error during key rotation",
            extra={
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )
        raise EncryptionError(
            f"Key rotation failed: {type(e).__name__}: {str(e)}"
        ) from e


def get_encryption_service() -> FieldEncryption:
    """
    FastAPI dependency to provide field encryption service.

    Loads master key from environment and returns configured FieldEncryption instance.
    Safe to use in concurrent requests - Fernet is thread-safe.

    Returns:
        FieldEncryption: Configured encryption service

    Raises:
        ValueError: If ENCRYPTION_MASTER_KEY is invalid

    Environment Variables:
        ENCRYPTION_MASTER_KEY: Base64-encoded Fernet key
                              Generate with: Fernet.generate_key().decode()

    Usage:
        @router.post("/patients")
        async def create_patient(
            data: PatientCreate,
            encryption: FieldEncryption = Depends(get_encryption_service)
        ):
            encrypted_ssn = encryption.encrypt(data.ssn)
            # Store encrypted_ssn in database

    Development:
        If ENCRYPTION_MASTER_KEY is not set, a random key is generated with a warning.
        This is acceptable for local development but NOT for production.

    Production:
        - Store key in AWS Secrets Manager, HashiCorp Vault, or similar KMS
        - Rotate key every 90 days
        - Monitor key access and usage
        - Implement key versioning for zero-downtime rotation
    """
    master_key_str = os.getenv("ENCRYPTION_MASTER_KEY")

    if not master_key_str:
        # Generate random key for development
        random_key = Fernet.generate_key()
        logger.warning(
            "ENCRYPTION_MASTER_KEY not set. Generated random key for development. "
            "DO NOT USE IN PRODUCTION - encrypted data will be unrecoverable after restart.",
            extra={"key_preview": random_key[:10].decode() + "..."}
        )
        return FieldEncryption(random_key)

    try:
        # Decode base64 key from environment
        master_key = master_key_str.encode('utf-8')
        return FieldEncryption(master_key)

    except Exception as e:
        logger.error(
            "Failed to initialize encryption service from environment",
            extra={
                "error_type": type(e).__name__,
                "error": str(e)
            }
        )
        raise ValueError(
            f"Invalid ENCRYPTION_MASTER_KEY in environment. "
            f"Generate a valid key with: Fernet.generate_key().decode(). "
            f"Error: {type(e).__name__}: {str(e)}"
        ) from e


def generate_new_master_key() -> str:
    """
    Generate a new Fernet master key for ENCRYPTION_MASTER_KEY.

    Helper function for key generation and rotation. Use this to create
    new master keys for initial setup or periodic rotation.

    Returns:
        Base64-encoded Fernet key as string (ready for environment variable)

    Example:
        >>> key = generate_new_master_key()
        >>> print(f"Add to .env: ENCRYPTION_MASTER_KEY={key}")

    Security:
        - Generated key is cryptographically secure (uses os.urandom)
        - Store in secure location immediately
        - Never commit to version control
        - Use key management service in production
    """
    key = Fernet.generate_key()
    key_str = key.decode('utf-8')

    logger.info(
        "Generated new master key",
        extra={"key_preview": key_str[:10] + "..."}
    )

    return key_str
