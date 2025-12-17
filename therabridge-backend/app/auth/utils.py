"""
Password hashing and verification utilities using bcrypt.

Security Notes:
- Bcrypt automatically includes a random salt (prevents rainbow tables)
- Bcrypt is intentionally slow (prevents brute-force attacks)
- Hash output is always 60 characters
- Same password hashed twice produces different hashes (due to random salt)
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Dict
import secrets

# Create password context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: Plain text password from user input

    Returns:
        Bcrypt hash (60 characters)

    Example:
        >>> hashed = get_password_hash("my_secure_password")
        >>> len(hashed)
        60
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.

    Args:
        plain_password: Password from login attempt
        hashed_password: Stored bcrypt hash from database

    Returns:
        True if password matches, False otherwise

    Example:
        >>> hashed = get_password_hash("correct_password")
        >>> verify_password("correct_password", hashed)
        True
        >>> verify_password("wrong_password", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_refresh_token() -> str:
    """
    Create a secure random refresh token.

    Unlike access tokens (JWTs), refresh tokens are random strings
    stored in the database. This allows server-side revocation.

    Returns:
        URL-safe random string (43 characters)

    Example:
        >>> token1 = create_refresh_token()
        >>> token2 = create_refresh_token()
        >>> len(token1)
        43
        >>> token1 != token2  # Each call produces unique token
        True
    """
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """
    Hash a refresh token before storing in database.

    We store hashed tokens so if the database is compromised,
    attackers can't use the refresh tokens.

    Args:
        token: Plain refresh token

    Returns:
        Bcrypt hash of token (60 characters)

    Security Design:
        - Protects against database breaches
        - Client keeps plain token in httpOnly cookie
        - Server stores only the hash
        - To validate: hash incoming token and compare with stored hash

    Example:
        >>> token = create_refresh_token()
        >>> hashed = hash_refresh_token(token)
        >>> len(hashed)
        60
        >>> verify_password(token, hashed)  # Validate using verify_password
        True
    """
    return get_password_hash(token)
