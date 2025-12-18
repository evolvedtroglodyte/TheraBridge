"""
Type-safe configuration management for Upheal scraper.

This module provides centralized configuration using Pydantic Settings,
with support for environment variables, .env files, and sensible defaults
for ethical web scraping practices.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, HttpUrl
from typing import Optional
from pathlib import Path


class ScraperSettings(BaseSettings):
    """
    Upheal scraper configuration using Pydantic Settings.
    Reads from environment variables and .env file.

    Environment variables can be prefixed with SCRAPER_ or used directly.
    Example: SCRAPER_LOG_LEVEL=DEBUG or LOG_LEVEL=DEBUG
    """

    # Application Info
    app_name: str = "upheal-scraper"
    environment: str = Field(default="development", env="ENV")

    # HTTP Client Settings
    requests_per_second: float = Field(
        default=0.5,
        ge=0.1,
        le=10.0,
        description="Rate limit for HTTP requests (ethical scraping default: 0.5 req/sec)"
    )
    request_timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="HTTP request timeout in seconds"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum number of retry attempts for failed requests"
    )
    user_agent: str = Field(
        default="UphealScraper/1.0 (+https://yourcompany.com/scraping-policy; contact@yourcompany.com)",
        env="USER_AGENT",
        description="User-Agent header for HTTP requests (should identify your scraper)"
    )

    # Target URLs
    upheal_base_url: HttpUrl = Field(
        default="https://www.upheal.io",
        description="Base URL for Upheal website"
    )
    start_urls: list[str] = Field(
        default_factory=lambda: [
            "https://www.upheal.io/features",
            "https://www.upheal.io/pricing"
        ],
        description="Initial URLs to scrape"
    )

    # Storage Paths
    data_dir: Path = Field(
        default=Path("./data"),
        description="Root directory for all data storage"
    )
    raw_data_dir: Path = Field(
        default=Path("./data/raw"),
        description="Directory for raw scraped HTML/JSON"
    )
    processed_data_dir: Path = Field(
        default=Path("./data/processed"),
        description="Directory for processed/cleaned data"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    log_file: Path = Field(
        default=Path("./logs/scraper.log"),
        description="Path to log file"
    )
    enable_json_logs: bool = Field(
        default=True,
        description="Enable structured JSON logging"
    )

    # Pydantic Settings Configuration
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',  # Ignore extra environment variables
        env_prefix='SCRAPER_'  # Optional prefix for environment variables
    )

    def __init__(self, **kwargs):
        """Initialize settings and create necessary directories."""
        super().__init__(**kwargs)

        # Ensure all directories exist on initialization
        self._create_directories()

    def _create_directories(self) -> None:
        """Create all necessary directories if they don't exist."""
        directories = [
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.log_file.parent
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def delay_between_requests(self) -> float:
        """Calculate delay in seconds between requests based on rate limit."""
        return 1.0 / self.requests_per_second

    def get_headers(self) -> dict[str, str]:
        """Get default HTTP headers for requests."""
        return {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }


# Global settings instance - import this in other modules
settings = ScraperSettings()
