"""
Authentication configuration for JWT tokens.

This module centralizes all auth-related settings (secret key, token expiration times).
Using environment variables allows different settings for dev/staging/prod.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class AuthConfig(BaseSettings):
    """Configuration for JWT authentication."""

    # Secret key for JWT signing (should be 32+ random bytes)
    # In production, this MUST be set via environment variable
    # If key changes, all existing tokens become invalid
    SECRET_KEY: str = secrets.token_urlsafe(32)

    # JWT algorithm
    ALGORITHM: str = "HS256"

    # Access token expiration (in minutes)
    # Short-lived to minimize damage if token is stolen
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Refresh token expiration (in days)
    # Long-lived to reduce login frequency
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Allow other env vars to exist (DATABASE_URL, etc.)


# Singleton instance
auth_config = AuthConfig()
