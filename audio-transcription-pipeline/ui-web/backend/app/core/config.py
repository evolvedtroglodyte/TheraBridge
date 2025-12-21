"""Configuration management for the API"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = True

    # CORS Settings
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # File Upload
    max_upload_size_mb: int = 100
    upload_dir: Path = Path("./uploads")
    results_dir: Path = Path("./results")

    # Pipeline Configuration
    pipeline_path: Path = Path("../../src/pipeline.py")
    openai_api_key: str = ""
    huggingface_token: str = ""

    # Processing
    max_concurrent_jobs: int = 3
    job_timeout_seconds: int = 3600

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)

# Global settings instance
settings = Settings()
