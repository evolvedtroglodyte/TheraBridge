"""
Authentication utility functions for JWT token management and password hashing.

This module provides functions for creating and validating JWT tokens,
as well as securely hashing and verifying passwords using bcrypt.
"""

import secrets
from datetime import datetime, timedelta
from typing import Dict
from uuid import UUID
from fastapi import HTTPException, status
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.auth.config import auth_config

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(user_id: UUID, role: str) -> str:
    """
    Create a short-lived JWT access token.

    Args:
        user_id: User's UUID
        role: User's role (therapist/patient/admin)

    Returns:
        JWT token string
    """
    # Calculate expiration time
    expires_delta = timedelta(minutes=auth_config.ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.utcnow() + expires_delta

    # Create token payload
    payload = {
        "sub": str(user_id),  # "sub" is standard JWT claim for user ID
        "role": role,
        "exp": expire,  # "exp" is standard JWT claim for expiration
        "type": "access"
    }

    # Encode and sign token
    token = jwt.encode(
        payload,
        auth_config.SECRET_KEY,
        algorithm=auth_config.ALGORITHM
    )

    return token


def decode_access_token(token: str) -> Dict[str, any]:
    """
    Decode and verify a JWT access token.

    Args:
        token: JWT token from Authorization header

    Returns:
        Decoded payload dict with user_id and role

    Raises:
        HTTPException: If token invalid, expired, or wrong type
    """
    try:
        # Decode and verify signature
        payload = jwt.decode(
            token,
            auth_config.SECRET_KEY,
            algorithms=[auth_config.ALGORITHM]
        )

        # Verify token type
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )

        # Extract user_id and role
        user_id: str = payload.get("sub")
        role: str = payload.get("role")

        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        return {
            "user_id": user_id,
            "role": role
        }

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: Plain text password from user input

    Returns:
        Bcrypt hash (60 characters)
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
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_refresh_token() -> str:
    """
    Create a secure random refresh token.

    Unlike access tokens (JWTs), refresh tokens are random strings
    stored in the database. This allows server-side revocation.

    Returns:
        URL-safe random string (43 characters)
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
        Bcrypt hash of token
    """
    return get_password_hash(token)
