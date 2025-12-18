"""
Async HTTP client with automatic retry logic and exponential backoff.

This module provides a robust HTTP client built on HTTPX with:
- Async/await support for high performance
- Automatic retry logic with exponential backoff
- Realistic browser headers for ethical scraping
- HTTP/2 support
- Comprehensive error handling and logging
"""

import httpx
import asyncio
from typing import Optional, Dict, Any
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging
from ..config import settings

logger = logging.getLogger(__name__)


class HTTPClient:
    """
    Async HTTP client with automatic retry logic and exponential backoff.
    Uses HTTPX for HTTP/2 support and async operations.
    """

    def __init__(self):
        self.timeout = httpx.Timeout(settings.request_timeout)
        self.headers = {
            'User-Agent': settings.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }

    @retry(
        stop=stop_after_attempt(settings.max_retries),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((
            httpx.TimeoutException,
            httpx.ConnectError,
            httpx.ReadTimeout
        )),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def fetch(
        self,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> httpx.Response:
        """
        Fetch URL with automatic retry on network errors.

        Args:
            url: Target URL
            method: HTTP method (GET, POST, etc.)
            headers: Additional headers (merged with defaults)
            **kwargs: Additional httpx.request arguments

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPStatusError: On 4xx/5xx responses after retries
            httpx.TimeoutException: On timeout after retries
        """
        request_headers = self.headers.copy()
        if headers:
            request_headers.update(headers)

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=request_headers,
                **kwargs
            )

            # Log response
            logger.info(
                f"{method} {url} -> {response.status_code} ({len(response.content)} bytes)"
            )

            # Raise on 4xx/5xx errors
            response.raise_for_status()

            return response

    async def fetch_text(self, url: str, **kwargs) -> str:
        """Convenience method to fetch URL and return text content."""
        response = await self.fetch(url, **kwargs)
        return response.text

    async def fetch_json(self, url: str, **kwargs) -> Dict[str, Any]:
        """Convenience method to fetch URL and return JSON."""
        response = await self.fetch(url, **kwargs)
        return response.json()

    async def check_robots_txt(self, base_url: str) -> str:
        """
        Check robots.txt for the given domain.

        Args:
            base_url: Base URL (e.g., 'https://www.upheal.io')

        Returns:
            robots.txt content as string
        """
        robots_url = f"{base_url.rstrip('/')}/robots.txt"
        try:
            response = await self.fetch(robots_url)
            logger.info(f"Retrieved robots.txt from {robots_url}")
            return response.text
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"No robots.txt found at {robots_url}")
                return ""
            raise


# Global client instance
http_client = HTTPClient()
