from abc import ABC, abstractmethod
from typing import List
import logging
from bs4 import BeautifulSoup
from ..utils.http_client import http_client
from ..utils.rate_limiter import rate_limiter
from ..models.schemas import UphealData
from ..config import settings

logger = logging.getLogger(__name__)

class ScraperBase(ABC):
    """
    Abstract base class for all web scrapers.
    Provides common functionality: HTTP fetching, rate limiting, parsing.
    """

    def __init__(self):
        self.http_client = http_client
        self.rate_limiter = rate_limiter
        self.parser = 'lxml'  # Fast, lenient parser

        logger.info(f"{self.__class__.__name__} initialized")

    @abstractmethod
    def get_urls(self) -> List[str]:
        """
        Return list of URLs to scrape.
        Must be implemented by subclasses.

        Returns:
            List of URLs to scrape
        """
        pass

    @abstractmethod
    async def extract(self, html: str, url: str) -> UphealData:
        """
        Extract data from HTML content.
        Must be implemented by subclasses.

        Args:
            html: HTML content as string
            url: Source URL

        Returns:
            UphealData object with extracted data
        """
        pass

    async def fetch_page(self, url: str) -> str:
        """
        Fetch a single page with rate limiting.

        Args:
            url: URL to fetch

        Returns:
            HTML content as string
        """
        # Rate limit before request
        await self.rate_limiter.async_wait()

        logger.info(f"Fetching: {url}")
        html = await self.http_client.fetch_text(url)

        return html

    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML string into BeautifulSoup object.

        Args:
            html: HTML content

        Returns:
            BeautifulSoup parsed object
        """
        return BeautifulSoup(html, self.parser)

    async def check_compliance(self) -> bool:
        """
        Check robots.txt compliance for target domain.

        Returns:
            True if allowed to scrape, False otherwise
        """
        try:
            robots_txt = await self.http_client.check_robots_txt(str(settings.upheal_base_url))

            # Basic check: warn if "Disallow: /" is present
            if "Disallow: /" in robots_txt:
                logger.warning(
                    "robots.txt contains 'Disallow: /' - scraping may not be allowed. "
                    "Review robots.txt manually before proceeding."
                )
                return False

            logger.info("robots.txt check passed")
            return True
        except Exception as e:
            logger.error(f"Failed to check robots.txt: {e}")
            return False

    async def scrape(self) -> UphealData:
        """
        Main scraping workflow.
        1. Check robots.txt compliance
        2. Get URLs to scrape
        3. Fetch each URL with rate limiting
        4. Extract data from HTML
        5. Return aggregated data

        Returns:
            UphealData object with all scraped data
        """
        # Compliance check
        compliant = await self.check_compliance()
        if not compliant:
            logger.error("Compliance check failed. Aborting scrape.")
            raise ValueError("robots.txt compliance check failed")

        # Get URLs
        urls = self.get_urls()
        logger.info(f"Scraping {len(urls)} URLs")

        # Scrape each URL
        all_data = None
        for url in urls:
            html = await self.fetch_page(url)
            data = await self.extract(html, url)

            # Merge data
            if all_data is None:
                all_data = data
            else:
                all_data.features.extend(data.features)
                all_data.pricing_tiers.extend(data.pricing_tiers)
                all_data.testimonials.extend(data.testimonials)

        logger.info(
            f"Scraping complete: {len(all_data.features)} features, "
            f"{len(all_data.pricing_tiers)} pricing tiers, "
            f"{len(all_data.testimonials)} testimonials"
        )

        return all_data

    def __repr__(self):
        return f"{self.__class__.__name__}(parser={self.parser})"
