"""
Application Configuration
Loads settings from environment variables
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Supabase Configuration
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_service_key: str = ""

    # OpenAI Configuration
    openai_api_key: str = ""

    # JWT Configuration
    jwt_secret: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Application Settings
    environment: str = "development"
    debug: bool = True

    # CORS Settings (will be parsed from comma-separated string)
    cors_origins: str = "http://localhost:3000,http://localhost:3001,https://therabridge.up.railway.app"

    # Breakthrough Detection Settings
    breakthrough_min_confidence: float = 0.6
    breakthrough_auto_analyze: bool = True

    # Background Jobs (optional)
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# Global settings instance
settings = Settings()


# Validation checks
def validate_config():
    """Validate required configuration"""
    errors = []

    if not settings.supabase_url:
        errors.append("SUPABASE_URL is required")

    if not settings.supabase_key:
        errors.append("SUPABASE_KEY is required")

    if not settings.openai_api_key:
        errors.append("OPENAI_API_KEY is required for breakthrough detection")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")


# Run validation on import
if settings.environment != "test":
    try:
        validate_config()
    except ValueError as e:
        print(f"⚠️  Configuration Warning: {e}")
        print("   Set environment variables in .env file")
