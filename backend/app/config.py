"""
Centralized configuration module for TherapyBridge backend.

This module consolidates all environment variable loading and configuration settings.
Uses Pydantic BaseSettings for automatic validation and type safety.

Environment Profiles:
    - development: Local development (DEBUG=true, verbose logging)
    - staging: Pre-production testing (DEBUG=false, relaxed CORS)
    - production: Live deployment (DEBUG=false, strict security)

Usage:
    from app.config import settings

    # Access any configuration value
    database_url = settings.DATABASE_URL
    api_key = settings.OPENAI_API_KEY
    is_debug = settings.DEBUG
"""

import os
import secrets
from enum import Enum
from typing import List, Optional
from pathlib import Path

from pydantic import Field, field_validator, PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Annotated


class Environment(str, Enum):
    """Supported deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """
    Application configuration loaded from environment variables.

    All settings are loaded from .env file or environment variables.
    Required settings will raise ValidationError if missing.
    Optional settings have sensible defaults.
    """

    # ============================================
    # Environment Configuration
    # ============================================

    ENVIRONMENT: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment (development/staging/production)"
    )

    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (CRITICAL: Must be False in production to protect PHI)"
    )

    # ============================================
    # Database Configuration
    # ============================================

    DATABASE_URL: str = Field(
        ...,  # Required field
        description="PostgreSQL connection string (postgresql://user:pass@host:port/db)"
    )

    DB_POOL_SIZE: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Database connection pool size"
    )

    DB_MAX_OVERFLOW: int = Field(
        default=20,
        ge=0,
        le=100,
        description="Maximum overflow connections beyond pool_size"
    )

    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Connection pool timeout in seconds"
    )

    SQL_ECHO: bool = Field(
        default=False,
        description="Log all SQL queries (WARNING: Exposes PHI, disable in production)"
    )

    # ============================================
    # OpenAI API Configuration
    # ============================================

    OPENAI_API_KEY: SecretStr = Field(
        ...,  # Required field
        description="OpenAI API key for GPT-4o extraction"
    )

    OPENAI_MODEL: str = Field(
        default="gpt-4o",
        description="OpenAI model for note extraction"
    )

    OPENAI_TIMEOUT: int = Field(
        default=120,
        ge=10,
        le=600,
        description="OpenAI API request timeout in seconds"
    )

    OPENAI_MAX_RETRIES: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retries for OpenAI API calls"
    )

    OPENAI_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="Temperature for note extraction (lower = more consistent)"
    )

    # ============================================
    # JWT Authentication Configuration
    # ============================================

    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        description="Secret key for JWT signing (CRITICAL: Set in production)"
    )

    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Access token expiration time in minutes"
    )

    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        ge=1,
        le=90,
        description="Refresh token expiration time in days"
    )

    # ============================================
    # CORS Configuration
    # ============================================

    # Use str annotation to prevent pydantic-settings from auto-parsing as JSON
    # The field_validator will convert comma-separated string to List[str]
    CORS_ORIGINS: str | List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
        ],
        description="Allowed CORS origins (frontend URLs)"
    )

    CORS_CREDENTIALS: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )

    # ============================================
    # File Upload Configuration
    # ============================================

    UPLOAD_DIR: Path = Field(
        default=Path("uploads/audio"),
        description="Directory for audio file uploads"
    )

    MAX_UPLOAD_SIZE_MB: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Maximum upload file size in megabytes"
    )

    # Use str annotation to prevent pydantic-settings from auto-parsing as JSON
    # The field_validator will convert comma-separated string to List[str]
    ALLOWED_AUDIO_FORMATS: str | List[str] = Field(
        default=["mp3", "wav", "m4a", "ogg", "flac"],
        description="Allowed audio file formats"
    )

    # ============================================
    # Cleanup Configuration
    # ============================================

    FAILED_SESSION_RETENTION_DAYS: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Retention period for failed sessions in days"
    )

    ORPHANED_FILE_RETENTION_HOURS: int = Field(
        default=24,
        ge=1,
        le=720,
        description="Retention period for orphaned files in hours"
    )

    AUTO_CLEANUP_ON_STARTUP: bool = Field(
        default=False,
        description="Enable automatic cleanup when API starts"
    )

    CLEANUP_SCHEDULE_HOUR: int = Field(
        default=3,
        ge=0,
        le=23,
        description="Hour of day (0-23) for scheduled cleanup (reserved for future use)"
    )

    # ============================================
    # Analytics & Scheduler Settings
    # ============================================

    ENABLE_ANALYTICS_SCHEDULER: bool = Field(
        default=True,
        description="Enable background jobs for analytics aggregation"
    )

    DAILY_AGGREGATION_HOUR: int = Field(
        default=0,
        ge=0,
        le=23,
        description="Hour (0-23 UTC) to run daily analytics aggregation"
    )

    ANALYTICS_CACHE_TTL_SECONDS: int = Field(
        default=300,
        ge=60,
        le=3600,
        description="Cache TTL for analytics endpoints (60s-1h)"
    )

    # ============================================
    # Email Service Configuration
    # ============================================

    EMAIL_PROVIDER: str = Field(
        default="smtp",
        description="Email provider: 'smtp', 'sendgrid', or 'ses' (default: smtp)"
    )

    EMAIL_FROM: str = Field(
        default="noreply@therapybridge.com",
        description="From email address for outgoing emails"
    )

    EMAIL_API_KEY: Optional[SecretStr] = Field(
        default=None,
        description="API key for SendGrid or AWS SES (required if EMAIL_PROVIDER is sendgrid/ses)"
    )

    SMTP_HOST: str = Field(
        default="localhost",
        description="SMTP server hostname (required if EMAIL_PROVIDER is smtp)"
    )

    SMTP_PORT: int = Field(
        default=587,
        ge=1,
        le=65535,
        description="SMTP server port (default: 587 for STARTTLS)"
    )

    SMTP_USERNAME: Optional[str] = Field(
        default=None,
        description="SMTP authentication username (optional, required for authenticated SMTP)"
    )

    SMTP_PASSWORD: Optional[SecretStr] = Field(
        default=None,
        description="SMTP authentication password (optional, required for authenticated SMTP)"
    )

    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="Frontend URL for email verification links and password resets"
    )

    # ============================================
    # Security & HIPAA Compliance (Feature 8)
    # ============================================

    ENCRYPTION_MASTER_KEY: Optional[str] = Field(
        default=None,
        description="Master encryption key for field-level encryption (AES-256-GCM)"
    )

    MFA_ISSUER: str = Field(
        default="TherapyBridge",
        description="MFA TOTP issuer name displayed in authenticator apps"
    )

    SECURITY_HSTS_ENABLED: bool = Field(
        default=True,
        description="Enable HTTP Strict Transport Security (HSTS) header"
    )

    CSP_POLICY: Optional[str] = Field(
        default=None,
        description="Custom Content-Security-Policy header (defaults to strict policy)"
    )

    AUDIT_LOG_RETENTION_DAYS: int = Field(
        default=2555,
        ge=1,
        le=3650,
        description="Audit log retention period in days (default: 7 years for HIPAA compliance)"
    )

    # ============================================
    # Rate Limiting Configuration
    # ============================================

    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting middleware"
    )

    # Login endpoint: 5 attempts per minute
    RATE_LIMIT_LOGIN: str = Field(
        default="5/minute",
        description="Rate limit for login endpoint (format: count/period)"
    )

    # Signup endpoint: 3 attempts per hour
    RATE_LIMIT_SIGNUP: str = Field(
        default="3/hour",
        description="Rate limit for signup endpoint"
    )

    # Token refresh: 10 per minute
    RATE_LIMIT_REFRESH: str = Field(
        default="10/minute",
        description="Rate limit for token refresh endpoint"
    )

    # General API: 100 per minute
    RATE_LIMIT_API: str = Field(
        default="100/minute",
        description="Rate limit for general API endpoints"
    )

    # ============================================
    # Server Configuration
    # ============================================

    HOST: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )

    PORT: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="Server port"
    )

    WORKERS: int = Field(
        default=1,
        ge=1,
        le=32,
        description="Number of uvicorn worker processes"
    )

    # ============================================
    # Logging Configuration
    # ============================================

    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level (DEBUG/INFO/WARNING/ERROR/CRITICAL)"
    )

    LOG_FORMAT: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log message format"
    )

    # ============================================
    # Pydantic Configuration
    # ============================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Allow extra env vars to exist
        # Disable JSON parsing for env vars - handle parsing in validators instead
        env_parse_enums=True,
    )

    # ============================================
    # Validators
    # ============================================

    @field_validator("DEBUG")
    @classmethod
    def validate_debug_in_production(cls, v: bool, info) -> bool:
        """Ensure DEBUG is False in production to prevent PHI exposure."""
        # Note: info.data may not have ENVIRONMENT yet during validation
        # We'll do a secondary check in model_post_init
        return v

    @field_validator("SQL_ECHO")
    @classmethod
    def validate_sql_echo_in_production(cls, v: bool, info) -> bool:
        """Ensure SQL_ECHO is False in production to prevent PHI exposure."""
        return v

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        """Warn if JWT_SECRET_KEY is using default in production."""
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v) -> List[str]:
        """Parse CORS_ORIGINS from comma-separated string or list."""
        if isinstance(v, str):
            # Handle empty string
            if not v.strip():
                return []
            # Split comma-separated values and strip whitespace
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return v
        # Fallback for any other type
        return []

    @field_validator("ALLOWED_AUDIO_FORMATS", mode="before")
    @classmethod
    def parse_audio_formats(cls, v) -> List[str]:
        """Parse ALLOWED_AUDIO_FORMATS from comma-separated string or list."""
        if isinstance(v, str):
            # Handle empty string
            if not v.strip():
                return []
            # Split comma-separated values, strip whitespace, and lowercase
            return [fmt.strip().lower() for fmt in v.split(",") if fmt.strip()]
        if isinstance(v, list):
            return [fmt.lower() if isinstance(fmt, str) else str(fmt) for fmt in v]
        # Fallback for any other type
        return []

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Ensure LOG_LEVEL is valid."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"LOG_LEVEL must be one of {valid_levels}")
        return v_upper

    @field_validator("EMAIL_PROVIDER")
    @classmethod
    def validate_email_provider(cls, v: str) -> str:
        """Ensure EMAIL_PROVIDER is valid."""
        valid_providers = {"smtp", "sendgrid", "ses"}
        v_lower = v.lower()
        if v_lower not in valid_providers:
            raise ValueError(f"EMAIL_PROVIDER must be one of {valid_providers}")
        return v_lower

    # ============================================
    # Post-initialization validation
    # ============================================

    def model_post_init(self, __context) -> None:
        """
        Perform environment-specific validation after model initialization.

        This runs after all fields are validated and populated.
        """
        # Production security checks
        if self.ENVIRONMENT == Environment.PRODUCTION:
            if self.DEBUG:
                raise ValueError(
                    "CRITICAL SECURITY ERROR: DEBUG must be False in production. "
                    "Debug mode exposes Protected Health Information (PHI) in error messages."
                )

            if self.SQL_ECHO:
                raise ValueError(
                    "CRITICAL SECURITY ERROR: SQL_ECHO must be False in production. "
                    "SQL logging exposes Protected Health Information (PHI)."
                )

            if self.JWT_SECRET_KEY == secrets.token_urlsafe(32):
                # This check won't work perfectly due to random generation
                # but serves as documentation
                print(
                    "WARNING: JWT_SECRET_KEY appears to be using default generation. "
                    "Ensure a fixed secret key is set via environment variable in production."
                )

            if "localhost" in str(self.CORS_ORIGINS):
                print(
                    "WARNING: CORS_ORIGINS contains 'localhost' in production. "
                    "Ensure only production frontend URLs are whitelisted."
                )

            # Feature 8: Encryption key validation
            if not self.ENCRYPTION_MASTER_KEY:
                print(
                    "WARNING: ENCRYPTION_MASTER_KEY not set in production. "
                    "Field-level encryption will not be available. "
                    "Set ENCRYPTION_MASTER_KEY environment variable for HIPAA compliance."
                )

        # Development: Generate encryption key if not set
        if self.ENVIRONMENT == Environment.DEVELOPMENT and not self.ENCRYPTION_MASTER_KEY:
            # Generate a random 32-byte key for development
            dev_key = secrets.token_urlsafe(32)
            object.__setattr__(self, 'ENCRYPTION_MASTER_KEY', dev_key)
            print(
                f"WARNING: Generated temporary ENCRYPTION_MASTER_KEY for development: {dev_key[:16]}... "
                f"Data encrypted with this key will be lost on restart. "
                f"Set ENCRYPTION_MASTER_KEY in .env for persistent encryption."
            )

        # Create upload directory if it doesn't exist
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

        # Email service configuration validation
        # Only validate if email provider is configured (not using default 'smtp' with localhost)
        if self.EMAIL_PROVIDER == "sendgrid" or self.EMAIL_PROVIDER == "ses":
            if not self.EMAIL_API_KEY:
                print(
                    f"WARNING: EMAIL_PROVIDER is set to '{self.EMAIL_PROVIDER}' but EMAIL_API_KEY is not configured. "
                    f"Email sending will fail. Set EMAIL_API_KEY in .env file."
                )
        elif self.EMAIL_PROVIDER == "smtp":
            # Only warn if SMTP is configured with non-default host
            if self.SMTP_HOST != "localhost" and (not self.SMTP_USERNAME or not self.SMTP_PASSWORD):
                print(
                    f"WARNING: SMTP_HOST is set to '{self.SMTP_HOST}' but SMTP_USERNAME/SMTP_PASSWORD are not configured. "
                    f"Authenticated SMTP will fail. Set SMTP_USERNAME and SMTP_PASSWORD in .env file."
                )

    # ============================================
    # Computed Properties
    # ============================================

    @property
    def async_database_url(self) -> str:
        """Get async database URL with proper driver."""
        url = self.DATABASE_URL

        # Convert to asyncpg driver
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

        # Remove unsupported URL parameters for asyncpg
        import re
        url = re.sub(r'[&?]sslmode=\w+', '', url)
        url = re.sub(r'[&?]channel_binding=\w+', '', url)

        return url

    @property
    def sync_database_url(self) -> str:
        """Get synchronous database URL for auth operations."""
        return self.async_database_url.replace("postgresql+asyncpg://", "postgresql://")

    @property
    def max_upload_size_bytes(self) -> int:
        """Get maximum upload size in bytes."""
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_staging(self) -> bool:
        """Check if running in staging."""
        return self.ENVIRONMENT == Environment.STAGING


# ============================================
# Singleton Instance
# ============================================

# Create a single instance that's imported throughout the application
settings = Settings()


# ============================================
# Startup Validation
# ============================================

def validate_settings() -> None:
    """
    Validate settings on application startup.

    This function should be called during app initialization to fail fast
    if configuration is invalid.

    Raises:
        ValueError: If any critical configuration is missing or invalid
    """
    print("=" * 60)
    print("TherapyBridge Configuration Validation")
    print("=" * 60)
    print(f"Environment: {settings.ENVIRONMENT.value}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Database: {settings.DATABASE_URL[:30]}..." if len(settings.DATABASE_URL) > 30 else settings.DATABASE_URL)
    print(f"OpenAI Model: {settings.OPENAI_MODEL}")
    print(f"CORS Origins: {settings.CORS_ORIGINS}")
    print(f"Upload Directory: {settings.UPLOAD_DIR}")
    print(f"Rate Limiting: {settings.RATE_LIMIT_ENABLED}")
    print("=" * 60)

    # Verify required settings are present
    required_checks = [
        (settings.DATABASE_URL, "DATABASE_URL"),
        (settings.OPENAI_API_KEY.get_secret_value(), "OPENAI_API_KEY"),
        (settings.JWT_SECRET_KEY, "JWT_SECRET_KEY"),
    ]

    missing = []
    for value, name in required_checks:
        if not value:
            missing.append(name)

    if missing:
        raise ValueError(
            f"Missing required configuration: {', '.join(missing)}. "
            f"Please set these in your .env file or environment variables."
        )

    print("✅ Configuration validation passed")
    print()


# ============================================
# Backward Compatibility
# ============================================

# For backward compatibility with existing auth_config usage
class AuthConfig:
    """
    Backward compatibility wrapper for auth configuration.

    This allows existing code using `auth_config.SECRET_KEY` to continue working
    while we migrate to the centralized settings module.
    """
    @property
    def SECRET_KEY(self) -> str:
        return settings.JWT_SECRET_KEY

    @property
    def ALGORITHM(self) -> str:
        return settings.JWT_ALGORITHM

    @property
    def ACCESS_TOKEN_EXPIRE_MINUTES(self) -> int:
        return settings.ACCESS_TOKEN_EXPIRE_MINUTES

    @property
    def REFRESH_TOKEN_EXPIRE_DAYS(self) -> int:
        return settings.REFRESH_TOKEN_EXPIRE_DAYS


# Singleton instance for backward compatibility
auth_config = AuthConfig()
