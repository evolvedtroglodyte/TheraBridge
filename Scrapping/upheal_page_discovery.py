"""
Upheal Page Discovery System - Automatic Link Discovery and Site Mapping

This module provides intelligent page discovery for Upheal.io, automatically
finding ALL feature pages without requiring manual URL lists.

Features:
- Automatic navigation link extraction (sidebar, header, footer)
- Recursive link discovery (configurable depth)
- URL pattern categorization (features, sessions, analytics, etc.)
- Payment page filtering (billing, pricing excluded)
- Complete sitemap generation in JSON format

Requires:
- crawl4ai (for JavaScript rendering and session management)
- pydantic (for data validation)

Usage:
    # Basic discovery
    discovery = UphealPageDiscovery()
    sitemap = await discovery.discover_all_pages()

    # With authentication (requires login session)
    discovery = UphealPageDiscovery(session_id="my_session")
    sitemap = await discovery.discover_from_dashboard()

Author: Discovery Engineer (Instance I3)
Part of: TherapyBridge Competitive Analysis - Wave 1
"""

import asyncio
import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

try:
    from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
    CRAWL4AI_AVAILABLE = True
except ImportError:
    CRAWL4AI_AVAILABLE = False
    print("WARNING: crawl4ai not installed. Install with: pip install crawl4ai")

from pydantic import BaseModel, Field


# =============================================================================
# Page Category Definitions
# =============================================================================

class PageCategory(str, Enum):
    """Categories for discovered Upheal pages."""
    FEATURES = "features"
    SESSIONS = "sessions"
    ANALYTICS = "analytics"
    PATIENTS = "patients"
    SETTINGS = "settings"
    NOTES = "notes"
    TREATMENT = "treatment"
    GOALS = "goals"
    COMPLIANCE = "compliance"
    DASHBOARD = "dashboard"
    HELP = "help"
    OTHER = "other"
    EXCLUDED = "excluded"  # Payment/billing pages


# URL patterns for categorization
# NOTE: Order matters! More specific patterns (patients, sessions) should be
# checked BEFORE generic patterns (analytics/dashboard) to avoid misclassification.
# The categorize_url() method uses an ordered check list.
URL_CATEGORY_PATTERNS: Dict[PageCategory, List[str]] = {
    # Check PATIENTS first (before analytics/dashboard)
    PageCategory.PATIENTS: [
        r"/patient",
        r"/client",
        r"/portal",
        r"/member",
    ],
    # Check SESSIONS before analytics
    PageCategory.SESSIONS: [
        r"/session",
        r"/appointment",
        r"/meeting",
        r"/recording",
        r"/transcript",
    ],
    PageCategory.FEATURES: [
        r"/feature",
        r"/capabilities",
        r"/tools",
        r"/ai-",
        r"/automation",
    ],
    PageCategory.ANALYTICS: [
        r"/analytics",
        r"/insights",
        r"/report",
        r"/statistics",
        r"/metrics",
    ],
    # Dashboard is separate from analytics (more generic)
    PageCategory.DASHBOARD: [
        r"/dashboard",
        r"/home",
        r"/overview",
    ],
    PageCategory.SETTINGS: [
        r"/setting",
        r"/config",
        r"/account",
        r"/profile",
        r"/preference",
    ],
    PageCategory.NOTES: [
        r"/note",
        r"/summary",
        r"/soap",
        r"/dap",
        r"/template",
        r"/clinical",
    ],
    PageCategory.TREATMENT: [
        r"/treatment",
        r"/plan",
        r"/therapy",
        r"/intervention",
    ],
    PageCategory.GOALS: [
        r"/goal",
        r"/progress",
        r"/milestone",
        r"/outcome",
    ],
    PageCategory.COMPLIANCE: [
        r"/hipaa",
        r"/compliance",
        r"/audit",
        r"/security",
        r"/privacy",
        r"/consent",
    ],
    PageCategory.HELP: [
        r"/help",
        r"/support",
        r"/faq",
        r"/guide",
        r"/documentation",
    ],
}

# Ordered list for categorization priority
# More specific categories first, then generic ones
CATEGORY_CHECK_ORDER: List[PageCategory] = [
    PageCategory.PATIENTS,      # Check before dashboard (member dashboard)
    PageCategory.SESSIONS,      # Check before analytics
    PageCategory.FEATURES,
    PageCategory.NOTES,
    PageCategory.TREATMENT,
    PageCategory.GOALS,
    PageCategory.COMPLIANCE,
    PageCategory.SETTINGS,
    PageCategory.HELP,
    PageCategory.ANALYTICS,     # Generic - check late
    PageCategory.DASHBOARD,     # Most generic - check last
]

# URLs to EXCLUDE (payment/billing)
EXCLUDED_URL_PATTERNS: List[str] = [
    r"/billing",
    r"/pricing",
    r"/price",
    r"/payment",
    r"/checkout",
    r"/subscribe",
    r"/subscription",
    r"/plan",  # Careful - exclude pricing plans but not treatment plans
    r"/upgrade",
    r"/purchase",
    r"/cart",
    r"/order",
]


# =============================================================================
# Data Models
# =============================================================================

class DiscoveredPage(BaseModel):
    """Individual discovered page with metadata."""

    url: str = Field(..., description="Full URL of the page")
    title: Optional[str] = Field(None, description="Page title if extracted")
    category: PageCategory = Field(PageCategory.OTHER, description="Page category")
    depth: int = Field(0, description="Discovery depth from start page")
    discovered_from: Optional[str] = Field(None, description="Parent URL that linked here")
    link_text: Optional[str] = Field(None, description="Anchor text of the link")
    discovered_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"use_enum_values": True}


class SitemapResult(BaseModel):
    """Complete sitemap with all discovered pages."""

    base_url: str = Field(..., description="Base URL of the crawled site")
    total_pages: int = Field(0, description="Total pages discovered")
    max_depth_reached: int = Field(0, description="Maximum depth explored")
    discovery_started: datetime = Field(default_factory=datetime.utcnow)
    discovery_completed: Optional[datetime] = None

    # Pages by category
    pages_by_category: Dict[str, List[DiscoveredPage]] = Field(
        default_factory=dict,
        description="Pages organized by category"
    )

    # Statistics
    category_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of pages per category"
    )

    # Excluded pages (billing/pricing)
    excluded_pages: List[DiscoveredPage] = Field(
        default_factory=list,
        description="Pages excluded from analysis (billing, pricing)"
    )

    model_config = {"use_enum_values": True}

    def add_page(self, page: DiscoveredPage):
        """Add a page to the appropriate category."""
        category = page.category

        if category == PageCategory.EXCLUDED:
            self.excluded_pages.append(page)
        else:
            if category not in self.pages_by_category:
                self.pages_by_category[category] = []
            self.pages_by_category[category].append(page)

        # Update counts
        self.category_counts[category] = self.category_counts.get(category, 0) + 1
        self.total_pages += 1

        if page.depth > self.max_depth_reached:
            self.max_depth_reached = page.depth

    def export_json(self, filepath: str) -> None:
        """Export sitemap to JSON file."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(
                self.model_dump(mode='json'),
                f,
                indent=2,
                default=str
            )

    def get_summary(self) -> str:
        """Get human-readable summary of discovery results."""
        lines = [
            "=" * 60,
            "UPHEAL PAGE DISCOVERY RESULTS",
            "=" * 60,
            f"Base URL: {self.base_url}",
            f"Total Pages Discovered: {self.total_pages}",
            f"Max Depth Reached: {self.max_depth_reached}",
            f"Discovery Time: {self.discovery_started} - {self.discovery_completed}",
            "",
            "BREAKDOWN BY CATEGORY:",
            "-" * 40,
        ]

        # Sort categories by count
        sorted_counts = sorted(
            self.category_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        for category, count in sorted_counts:
            if category != PageCategory.EXCLUDED:
                lines.append(f"  {category}: {count} pages")

        lines.append("")
        lines.append(f"EXCLUDED (billing/pricing): {len(self.excluded_pages)} pages")
        lines.append("=" * 60)

        return "\n".join(lines)


# =============================================================================
# Page Discovery Engine
# =============================================================================

class UphealPageDiscovery:
    """
    Intelligent page discovery system for Upheal.io.

    Automatically discovers all feature pages using recursive link crawling
    with intelligent categorization and filtering.
    """

    BASE_URL = "https://www.upheal.io"
    APP_URL = "https://app.upheal.io"  # Authenticated app domain

    def __init__(
        self,
        max_depth: int = 3,
        session_id: Optional[str] = None,
        rate_limit_delay: float = 2.0,
        headless: bool = True
    ):
        """
        Initialize the page discovery engine.

        Args:
            max_depth: Maximum recursion depth for link discovery (default: 3)
            session_id: Crawl4AI session ID for authenticated crawling
            rate_limit_delay: Seconds between requests (default: 2.0)
            headless: Run browser in headless mode (default: True)
        """
        self.max_depth = max_depth
        self.session_id = session_id or "upheal_discovery_session"
        self.rate_limit_delay = rate_limit_delay
        self.headless = headless

        # Tracking
        self.visited_urls: Set[str] = set()
        self.discovered_urls: Set[str] = set()
        self.sitemap = SitemapResult(base_url=self.BASE_URL)

        # Browser configuration
        self.browser_config = BrowserConfig(
            headless=headless,
            viewport_width=1920,
            viewport_height=1080,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        ) if CRAWL4AI_AVAILABLE else None

    def categorize_url(self, url: str) -> PageCategory:
        """
        Categorize a URL based on its path patterns.

        Args:
            url: URL to categorize

        Returns:
            PageCategory enum value
        """
        url_lower = url.lower()

        # First check if it should be excluded
        for pattern in EXCLUDED_URL_PATTERNS:
            # Special handling: /plan/ for pricing vs /treatment-plan/
            if pattern == r"/plan" and "/treatment" in url_lower:
                continue  # Don't exclude treatment plans
            if re.search(pattern, url_lower):
                return PageCategory.EXCLUDED

        # Check categories in priority order
        # (more specific patterns first, generic patterns last)
        for category in CATEGORY_CHECK_ORDER:
            if category in URL_CATEGORY_PATTERNS:
                for pattern in URL_CATEGORY_PATTERNS[category]:
                    if re.search(pattern, url_lower):
                        return category

        return PageCategory.OTHER

    def is_valid_internal_link(self, url: str, base_domain: str) -> bool:
        """
        Check if a URL is a valid internal link to crawl.

        Args:
            url: URL to check
            base_domain: Base domain to match against

        Returns:
            True if URL should be crawled
        """
        if not url:
            return False

        parsed = urlparse(url)

        # Must be HTTP(S)
        if parsed.scheme not in ('http', 'https', ''):
            return False

        # Check domain
        if parsed.netloc:
            if base_domain not in parsed.netloc and "upheal" not in parsed.netloc:
                return False

        # Skip anchors, mailto, tel
        if url.startswith(('#', 'mailto:', 'tel:', 'javascript:')):
            return False

        # Skip file downloads
        skip_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.png', '.jpg', '.gif']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False

        return True

    def normalize_url(self, url: str, base_url: str) -> str:
        """
        Normalize a URL by resolving relative paths and removing fragments.

        Args:
            url: URL to normalize
            base_url: Base URL for resolving relative paths

        Returns:
            Normalized absolute URL
        """
        # Make absolute
        full_url = urljoin(base_url, url)

        # Parse and reconstruct without fragment
        parsed = urlparse(full_url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

        # Preserve query string if present
        if parsed.query:
            normalized += f"?{parsed.query}"

        # Remove trailing slash for consistency
        normalized = normalized.rstrip('/')

        return normalized

    async def extract_links_from_page(
        self,
        crawler: 'AsyncWebCrawler',
        url: str
    ) -> List[Dict[str, str]]:
        """
        Extract all internal links from a page.

        Args:
            crawler: AsyncWebCrawler instance
            url: URL to extract links from

        Returns:
            List of dicts with 'url' and 'text' keys
        """
        if not CRAWL4AI_AVAILABLE:
            raise ImportError(
                "crawl4ai is required for link extraction. "
                "Install with: pip install crawl4ai"
            )

        config = CrawlerRunConfig(
            session_id=self.session_id,
            page_timeout=30000,
            remove_overlay_elements=True,
            # Wait for navigation to load
            wait_for="css:nav, css:.sidebar, css:header, css:footer",
        )

        try:
            result = await crawler.arun(url, config=config)

            if not result.success:
                print(f"  WARNING: Failed to crawl {url}")
                return []

            # Extract internal links
            internal_links = result.links.get("internal", [])

            links = []
            base_domain = urlparse(url).netloc

            for link in internal_links:
                # Handle both dict and string formats
                if isinstance(link, dict):
                    link_url = link.get("href", "")
                    link_text = link.get("text", "")
                else:
                    link_url = str(link)
                    link_text = ""

                if self.is_valid_internal_link(link_url, base_domain):
                    normalized = self.normalize_url(link_url, url)
                    links.append({
                        "url": normalized,
                        "text": link_text.strip() if link_text else None
                    })

            return links

        except Exception as e:
            print(f"  ERROR extracting links from {url}: {e}")
            return []

    async def discover_page(
        self,
        crawler: 'AsyncWebCrawler',
        url: str,
        depth: int,
        parent_url: Optional[str] = None,
        link_text: Optional[str] = None
    ) -> List[str]:
        """
        Discover a single page and extract its links.

        Args:
            crawler: AsyncWebCrawler instance
            url: URL to discover
            depth: Current recursion depth
            parent_url: URL that linked to this page
            link_text: Anchor text of the link

        Returns:
            List of newly discovered URLs to crawl
        """
        # Skip if already visited
        if url in self.visited_urls:
            return []

        self.visited_urls.add(url)

        # Rate limiting
        await asyncio.sleep(self.rate_limit_delay)

        print(f"  [Depth {depth}] Discovering: {url}")

        # Categorize the URL
        category = self.categorize_url(url)

        # Create page entry
        page = DiscoveredPage(
            url=url,
            category=category,
            depth=depth,
            discovered_from=parent_url,
            link_text=link_text
        )

        # Add to sitemap
        self.sitemap.add_page(page)

        # Don't recurse into excluded pages
        if category == PageCategory.EXCLUDED:
            print(f"    -> EXCLUDED (billing/pricing)")
            return []

        # Don't recurse past max depth
        if depth >= self.max_depth:
            return []

        # Extract links from this page
        links = await self.extract_links_from_page(crawler, url)

        # Filter new links
        new_urls = []
        for link in links:
            link_url = link["url"]
            if link_url not in self.visited_urls and link_url not in self.discovered_urls:
                self.discovered_urls.add(link_url)
                new_urls.append(link)

        print(f"    -> Found {len(links)} links, {len(new_urls)} new")

        return new_urls

    async def discover_all_pages(
        self,
        start_urls: Optional[List[str]] = None
    ) -> SitemapResult:
        """
        Discover all pages starting from given URLs.

        Args:
            start_urls: Initial URLs to crawl (default: Upheal.io main pages)

        Returns:
            SitemapResult with all discovered pages
        """
        if not CRAWL4AI_AVAILABLE:
            raise ImportError(
                "crawl4ai is required for page discovery. "
                "Install with: pip install crawl4ai"
            )

        # Default start URLs for public site
        if start_urls is None:
            start_urls = [
                f"{self.BASE_URL}",
                f"{self.BASE_URL}/features",
                f"{self.BASE_URL}/product",
            ]

        print("\n" + "=" * 60)
        print("UPHEAL PAGE DISCOVERY STARTING")
        print("=" * 60)
        print(f"Start URLs: {len(start_urls)}")
        print(f"Max Depth: {self.max_depth}")
        print(f"Rate Limit: {self.rate_limit_delay}s between requests")
        print("=" * 60 + "\n")

        self.sitemap.discovery_started = datetime.utcnow()

        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            # Queue: (url, depth, parent_url, link_text)
            queue = [(url, 0, None, None) for url in start_urls]

            while queue:
                current_url, depth, parent, text = queue.pop(0)

                # Discover page and get new links
                new_links = await self.discover_page(
                    crawler, current_url, depth, parent, text
                )

                # Add new links to queue for next depth
                for link in new_links:
                    queue.append((
                        link["url"],
                        depth + 1,
                        current_url,
                        link.get("text")
                    ))

        self.sitemap.discovery_completed = datetime.utcnow()

        print("\n" + self.sitemap.get_summary())

        return self.sitemap

    async def discover_from_dashboard(
        self,
        dashboard_url: Optional[str] = None
    ) -> SitemapResult:
        """
        Discover pages starting from authenticated dashboard.

        This method assumes a login session has already been established
        using the session_id.

        Args:
            dashboard_url: Dashboard URL (default: app.upheal.io)

        Returns:
            SitemapResult with all discovered pages
        """
        if dashboard_url is None:
            dashboard_url = f"{self.APP_URL}/dashboard"

        start_urls = [
            dashboard_url,
            f"{self.APP_URL}/sessions",
            f"{self.APP_URL}/patients",
            f"{self.APP_URL}/analytics",
        ]

        return await self.discover_all_pages(start_urls)


# =============================================================================
# Navigation Extractor (Specialized for SPA navigation menus)
# =============================================================================

class NavigationExtractor:
    """
    Specialized extractor for SPA navigation elements.

    Targets:
    - Sidebar menus
    - Header navigation
    - Footer links
    - Dropdown menus
    """

    # Common navigation selectors
    NAV_SELECTORS = [
        "nav",
        ".sidebar",
        ".navigation",
        ".nav-menu",
        "[role='navigation']",
        "header nav",
        "footer nav",
        ".main-nav",
        ".side-nav",
        ".app-sidebar",
    ]

    @classmethod
    async def extract_navigation_links(
        cls,
        crawler: 'AsyncWebCrawler',
        url: str,
        session_id: str
    ) -> List[Dict[str, str]]:
        """
        Extract links specifically from navigation elements.

        Args:
            crawler: AsyncWebCrawler instance
            url: URL to extract from
            session_id: Session ID for authentication

        Returns:
            List of navigation link dicts
        """
        # JavaScript to extract navigation links
        nav_js = """
        (function() {
            const navSelectors = [
                'nav', '.sidebar', '.navigation', '.nav-menu',
                '[role="navigation"]', 'header', 'footer',
                '.main-nav', '.side-nav', '.app-sidebar'
            ];

            const links = [];
            const seen = new Set();

            navSelectors.forEach(selector => {
                document.querySelectorAll(selector + ' a').forEach(a => {
                    const href = a.href;
                    if (href && !seen.has(href)) {
                        seen.add(href);
                        links.push({
                            url: href,
                            text: a.textContent.trim(),
                            section: selector
                        });
                    }
                });
            });

            return links;
        })();
        """

        config = CrawlerRunConfig(
            session_id=session_id,
            page_timeout=30000,
            js_code=nav_js,
            wait_for="css:nav, css:.sidebar, css:header",
        )

        try:
            result = await crawler.arun(url, config=config)

            if not result.success:
                return []

            # The JS code should return in result.extracted_content or similar
            # For now, use internal links from result.links
            internal_links = result.links.get("internal", [])

            return [
                {"url": link.get("href", str(link)), "text": link.get("text", "")}
                for link in internal_links
                if isinstance(link, dict) or isinstance(link, str)
            ]

        except Exception as e:
            print(f"Error extracting navigation: {e}")
            return []


# =============================================================================
# Main Entry Point
# =============================================================================

async def main():
    """
    Main entry point for page discovery.

    Run with: python upheal_page_discovery.py
    """
    # Create discovery engine
    discovery = UphealPageDiscovery(
        max_depth=2,  # Start conservative
        rate_limit_delay=2.5,  # Be respectful
        headless=True
    )

    # Run discovery
    sitemap = await discovery.discover_all_pages()

    # Save results
    output_path = Path(__file__).parent / "data" / "upheal_sitemap.json"
    sitemap.export_json(str(output_path))

    print(f"\nSitemap saved to: {output_path}")

    return sitemap


if __name__ == "__main__":
    asyncio.run(main())
