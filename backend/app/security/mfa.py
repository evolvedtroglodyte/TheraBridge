"""
Multi-Factor Authentication (MFA) service using Time-based One-Time Passwords (TOTP).

This module provides comprehensive MFA functionality including:
- TOTP secret generation and verification
- QR code generation for authenticator app setup
- Backup/recovery code generation and validation
- HIPAA-compliant security practices

Dependencies:
    - pyotp: TOTP implementation
    - qrcode: QR code generation
    - secrets: Cryptographically secure random generation
    - hashlib: SHA256 hashing for backup codes
"""

import logging
import secrets
import hashlib
import io
from typing import Optional
import pyotp
import qrcode
import os
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

load_dotenv()


class TOTPService:
    """
    Service for managing Time-based One-Time Password (TOTP) authentication.

    Provides functionality for:
    - Generating secure TOTP secrets
    - Creating QR codes for authenticator app enrollment
    - Verifying TOTP codes with configurable time windows
    - Generating and hashing backup recovery codes

    TOTP Configuration:
        - Algorithm: SHA1 (standard for TOTP)
        - Interval: 30 seconds
        - Digits: 6
        - Valid window: ±1 interval (60 seconds total)

    Security Features:
        - Cryptographically secure random generation
        - SHA256 hashing for backup codes
        - Configurable issuer name
        - Time-based code expiration
    """

    def __init__(self, issuer: Optional[str] = None):
        """
        Initialize TOTP service with configuration.

        Args:
            issuer: Optional issuer name for TOTP URIs.
                   Defaults to "TherapyBridge" from environment or hardcoded.
        """
        self.issuer = issuer or os.getenv("MFA_ISSUER", "TherapyBridge")
        self.totp_interval = 30  # 30 second intervals (standard)
        self.totp_digits = 6     # 6-digit codes (standard)
        self.valid_window = 1    # ±1 interval = 60 seconds total validity

        logger.info(
            "TOTPService initialized",
            extra={
                "issuer": self.issuer,
                "interval": self.totp_interval,
                "digits": self.totp_digits,
                "valid_window_seconds": self.valid_window * self.totp_interval * 2
            }
        )

    def generate_secret(self) -> str:
        """
        Generate a cryptographically secure random TOTP secret.

        Creates a base32-encoded random secret suitable for TOTP authentication.
        The secret is 32 characters (160 bits of entropy when decoded).

        Returns:
            str: Base32-encoded TOTP secret (32 characters)

        Example:
            >>> service = TOTPService()
            >>> secret = service.generate_secret()
            >>> len(secret)
            32
            >>> secret.isalnum() and secret.isupper()
            True
        """
        secret = pyotp.random_base32()

        logger.info(
            "Generated new TOTP secret",
            extra={
                "secret_length": len(secret),
                "entropy_bits": 160  # 32 base32 chars = 160 bits
            }
        )

        return secret

    def get_provisioning_uri(
        self,
        secret: str,
        email: str,
        issuer: Optional[str] = None
    ) -> str:
        """
        Generate a provisioning URI for authenticator app enrollment.

        Creates an otpauth:// URI that can be encoded in a QR code for easy
        enrollment in authenticator apps (Google Authenticator, Authy, etc.).

        Args:
            secret: Base32-encoded TOTP secret
            email: User's email address (used as account identifier)
            issuer: Optional issuer name override (defaults to service issuer)

        Returns:
            str: otpauth:// URI for QR code generation

        URI Format:
            otpauth://totp/TherapyBridge:user@example.com?secret=...&issuer=TherapyBridge

        Example:
            >>> service = TOTPService()
            >>> secret = "JBSWY3DPEHPK3PXP"
            >>> uri = service.get_provisioning_uri(secret, "user@example.com")
            >>> "otpauth://totp" in uri
            True
            >>> "TherapyBridge" in uri
            True
        """
        issuer_name = issuer or self.issuer
        totp = pyotp.TOTP(secret, interval=self.totp_interval, digits=self.totp_digits)

        uri = totp.provisioning_uri(name=email, issuer_name=issuer_name)

        logger.info(
            "Generated provisioning URI",
            extra={
                "email": email,
                "issuer": issuer_name,
                "uri_length": len(uri)
            }
        )

        return uri

    def generate_qr_code(self, uri: str) -> bytes:
        """
        Generate a QR code image from a provisioning URI.

        Creates a PNG image of a QR code that users can scan with their
        authenticator app to enroll in MFA.

        Args:
            uri: otpauth:// provisioning URI

        Returns:
            bytes: PNG image data of QR code

        QR Code Configuration:
            - Version: Auto (scales to fit data)
            - Error correction: HIGH (30% of data can be corrupted)
            - Box size: 10 pixels per box
            - Border: 4 boxes (standard)
            - Fill color: Black
            - Background: White

        Example:
            >>> service = TOTPService()
            >>> uri = "otpauth://totp/TherapyBridge:user@example.com?secret=TEST&issuer=TherapyBridge"
            >>> qr_bytes = service.generate_qr_code(uri)
            >>> len(qr_bytes) > 0
            True
            >>> qr_bytes[:4] == b'\\x89PNG'  # PNG header
            True
        """
        # Create QR code with high error correction
        qr = qrcode.QRCode(
            version=None,  # Auto-size to fit data
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Highest error correction
            box_size=10,   # Size of each box in pixels
            border=4,      # Border size in boxes (standard is 4)
        )

        qr.add_data(uri)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_bytes = buffer.getvalue()

        logger.info(
            "Generated QR code",
            extra={
                "uri_length": len(uri),
                "qr_bytes_size": len(qr_bytes),
                "format": "PNG"
            }
        )

        return qr_bytes

    def verify_code(
        self,
        secret: str,
        code: str,
        valid_window: Optional[int] = None
    ) -> bool:
        """
        Verify a TOTP code against a secret.

        Validates a 6-digit TOTP code with a configurable time window to account
        for clock drift and user input delays.

        Args:
            secret: Base32-encoded TOTP secret
            code: 6-digit TOTP code to verify (string or int)
            valid_window: Optional window override in intervals (default: 1)
                         Window of 1 = ±30 seconds = 60 seconds total

        Returns:
            bool: True if code is valid within the time window, False otherwise

        Time Window:
            - Default window: ±1 interval (±30 seconds)
            - Current time + past interval + future interval
            - Total validity: 60 seconds for default window

        Security Notes:
            - Codes are single-use within their validity period
            - Apps should track used codes to prevent replay attacks
            - Window should be kept minimal for security

        Example:
            >>> service = TOTPService()
            >>> secret = service.generate_secret()
            >>> totp = pyotp.TOTP(secret)
            >>> code = totp.now()  # Current valid code
            >>> service.verify_code(secret, code)
            True
            >>> service.verify_code(secret, "000000")  # Invalid code
            False
        """
        window = valid_window if valid_window is not None else self.valid_window
        totp = pyotp.TOTP(secret, interval=self.totp_interval, digits=self.totp_digits)

        # Verify with time window
        is_valid = totp.verify(code, valid_window=window)

        logger.info(
            "TOTP code verification attempt",
            extra={
                "is_valid": is_valid,
                "valid_window": window,
                "window_seconds": window * self.totp_interval * 2,
                "code_masked": f"{code[:2]}****" if len(str(code)) >= 4 else "****"
            }
        )

        return is_valid

    def generate_backup_codes(self, count: int = 10) -> list[str]:
        """
        Generate cryptographically secure backup/recovery codes.

        Creates a list of one-time-use backup codes for account recovery when
        the primary MFA device is unavailable. Each code is 8 characters of
        uppercase alphanumeric characters (excluding ambiguous characters).

        Args:
            count: Number of backup codes to generate (default: 10)

        Returns:
            list[str]: List of backup codes in plaintext (for user display)

        Code Format:
            - Length: 8 characters
            - Character set: A-Z, 0-9 (excluding I, O, 0, 1 for clarity)
            - Format: XXXX-XXXX (with hyphen for readability)
            - Entropy: ~38 bits per code

        Storage:
            - NEVER store plaintext codes in database
            - Always hash codes before storage using hash_backup_code()
            - Present codes to user ONCE during generation

        Example:
            >>> service = TOTPService()
            >>> codes = service.generate_backup_codes(count=5)
            >>> len(codes)
            5
            >>> all(len(code.replace('-', '')) == 8 for code in codes)
            True
        """
        # Character set excluding ambiguous characters (I, O, 0, 1)
        # This improves readability and reduces user errors
        charset = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

        codes = []
        for _ in range(count):
            # Generate 8 random characters
            code = ''.join(secrets.choice(charset) for _ in range(8))
            # Format as XXXX-XXXX for readability
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)

        logger.info(
            "Generated backup codes",
            extra={
                "count": count,
                "code_length": 8,
                "charset_size": len(charset),
                "entropy_bits_per_code": 38  # log2(32^8) ≈ 38 bits
            }
        )

        return codes

    def hash_backup_code(self, code: str) -> str:
        """
        Hash a backup code for secure storage using SHA256.

        Creates a SHA256 hash of a backup code for database storage. The hash
        is deterministic (same code always produces same hash) to allow
        verification, but computationally infeasible to reverse.

        Args:
            code: Plaintext backup code (with or without hyphen)

        Returns:
            str: Hexadecimal SHA256 hash (64 characters)

        Security Properties:
            - One-way function (cannot reverse hash to get code)
            - Deterministic (same input = same output)
            - Collision-resistant (different inputs = different hashes)
            - Fast to compute for verification

        Usage:
            1. Generate backup codes with generate_backup_codes()
            2. Show plaintext codes to user ONCE
            3. Hash each code with this method
            4. Store ONLY hashes in database
            5. Verify by hashing user input and comparing hashes

        Example:
            >>> service = TOTPService()
            >>> code = "ABCD-1234"
            >>> hash1 = service.hash_backup_code(code)
            >>> hash2 = service.hash_backup_code(code)
            >>> hash1 == hash2  # Deterministic
            True
            >>> len(hash1)  # SHA256 hex length
            64
        """
        # Remove hyphen if present (normalize input)
        normalized_code = code.replace('-', '')

        # SHA256 hash
        hash_object = hashlib.sha256(normalized_code.encode('utf-8'))
        code_hash = hash_object.hexdigest()

        logger.debug(
            "Hashed backup code",
            extra={
                "code_length": len(normalized_code),
                "hash_length": len(code_hash),
                "algorithm": "SHA256"
            }
        )

        return code_hash


def get_totp_service() -> TOTPService:
    """
    FastAPI dependency to provide the TOTP service.

    Creates a new TOTPService instance for each request. The service is
    lightweight and stateless, so creating new instances is efficient.

    Returns:
        TOTPService: New instance configured with environment settings

    Configuration:
        - MFA_ISSUER: Environment variable for issuer name (default: "TherapyBridge")

    Usage:
        In FastAPI routes, use: service = Depends(get_totp_service)

    Example:
        >>> @router.post("/mfa/setup")
        >>> async def setup_mfa(
        >>>     user_id: int,
        >>>     totp_service: TOTPService = Depends(get_totp_service)
        >>> ):
        >>>     secret = totp_service.generate_secret()
        >>>     uri = totp_service.get_provisioning_uri(secret, user.email)
        >>>     qr_code = totp_service.generate_qr_code(uri)
        >>>     return {"secret": secret, "qr_code": qr_code}
    """
    return TOTPService()
