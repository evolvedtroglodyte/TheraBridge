from typing import List
import logging
from datetime import datetime
from ..scrapers.base import ScraperBase
from ..models.schemas import UphealData, Feature, PricingTier, Testimonial
from ..config import settings

logger = logging.getLogger(__name__)

class UphealScraper(ScraperBase):
    """
    Scraper for Upheal therapy platform website.
    Extracts features, pricing tiers, and testimonials.
    """

    def __init__(self):
        super().__init__()
        logger.info("UphealScraper initialized for competitive analysis")

    def get_urls(self) -> List[str]:
        """
        Return Upheal URLs to scrape.

        Returns:
            List of URLs (features, pricing pages)
        """
        return settings.start_urls

    async def extract(self, html: str, url: str) -> UphealData:
        """
        Extract data from Upheal page HTML.

        Args:
            html: HTML content
            url: Source URL

        Returns:
            UphealData with extracted features, pricing, testimonials
        """
        soup = self.parse_html(html)

        # Determine page type from URL
        if 'features' in url.lower():
            features = self._extract_features(soup)
            testimonials = self._extract_testimonials(soup)
            pricing_tiers = []
        elif 'pricing' in url.lower():
            features = []
            testimonials = []
            pricing_tiers = self._extract_pricing(soup)
        else:
            features = []
            testimonials = []
            pricing_tiers = []

        return UphealData(
            scraped_at=datetime.utcnow(),
            source_url=url,
            features=features,
            pricing_tiers=pricing_tiers,
            testimonials=testimonials
        )

    def _extract_features(self, soup) -> List[Feature]:
        """
        Extract product features from features page.

        TODO: Update CSS selectors after inspecting actual Upheal HTML structure

        Args:
            soup: BeautifulSoup object

        Returns:
            List of Feature objects
        """
        features = []

        # TODO: Replace with actual selectors from Upheal's features page
        # Typical patterns for feature sections:
        # - .feature-card, .feature-item, .product-feature
        # - div[class*="feature"], section[class*="feature"]

        # Placeholder selector (update after inspecting site)
        feature_elements = soup.select('.feature-card, .feature-item, [class*="feature"]')

        for elem in feature_elements:
            try:
                # TODO: Update selectors based on actual HTML structure
                name_elem = elem.select_one('h3, h4, .feature-title, .title')
                desc_elem = elem.select_one('p, .description, .feature-description')
                category_elem = elem.select_one('.category, .feature-category, [data-category]')

                if name_elem:
                    feature = Feature(
                        name=name_elem.get_text(strip=True),
                        description=desc_elem.get_text(strip=True) if desc_elem else None,
                        category=category_elem.get_text(strip=True) if category_elem else None
                    )
                    features.append(feature)
                    logger.debug(f"Extracted feature: {feature.name}")
            except Exception as e:
                logger.warning(f"Failed to extract feature from element: {e}")
                continue

        logger.info(f"Extracted {len(features)} features")
        return features

    def _extract_pricing(self, soup) -> List[PricingTier]:
        """
        Extract pricing tiers from pricing page.

        TODO: Update CSS selectors after inspecting actual Upheal HTML structure

        Args:
            soup: BeautifulSoup object

        Returns:
            List of PricingTier objects
        """
        pricing_tiers = []

        # TODO: Replace with actual selectors from Upheal's pricing page
        # Typical patterns for pricing cards:
        # - .pricing-card, .plan-card, .pricing-tier
        # - div[class*="pricing"], div[class*="plan"]

        # Placeholder selector (update after inspecting site)
        pricing_elements = soup.select('.pricing-card, .plan-card, [class*="pricing-tier"]')

        for elem in pricing_elements:
            try:
                # TODO: Update selectors based on actual HTML structure
                name_elem = elem.select_one('h3, h4, .plan-name, .tier-name')
                price_elem = elem.select_one('.price, .plan-price, [class*="price"]')
                period_elem = elem.select_one('.billing-period, .period, [data-period]')
                popular_elem = elem.select_one('.popular, .recommended, [data-popular]')

                # Extract feature list
                feature_list = []
                feature_items = elem.select('li, .feature-item, [class*="feature"]')
                for item in feature_items:
                    feature_text = item.get_text(strip=True)
                    if feature_text:
                        feature_list.append(feature_text)

                if name_elem:
                    tier = PricingTier(
                        name=name_elem.get_text(strip=True),
                        price=price_elem.get_text(strip=True) if price_elem else None,
                        billing_period=period_elem.get_text(strip=True) if period_elem else None,
                        features=feature_list,
                        is_popular=popular_elem is not None
                    )
                    pricing_tiers.append(tier)
                    logger.debug(f"Extracted pricing tier: {tier.name}")
            except Exception as e:
                logger.warning(f"Failed to extract pricing tier from element: {e}")
                continue

        logger.info(f"Extracted {len(pricing_tiers)} pricing tiers")
        return pricing_tiers

    def _extract_testimonials(self, soup) -> List[Testimonial]:
        """
        Extract anonymized testimonials.

        TODO: Update CSS selectors after inspecting actual Upheal HTML structure

        Args:
            soup: BeautifulSoup object

        Returns:
            List of Testimonial objects (anonymized, no personal names)
        """
        testimonials = []

        # TODO: Replace with actual selectors from Upheal's testimonial section
        # Typical patterns for testimonials:
        # - .testimonial, .review, .quote
        # - div[class*="testimonial"], blockquote

        # Placeholder selector (update after inspecting site)
        testimonial_elements = soup.select('.testimonial, .review, blockquote')

        for elem in testimonial_elements:
            try:
                # TODO: Update selectors based on actual HTML structure
                quote_elem = elem.select_one('p, .quote, .testimonial-text')
                role_elem = elem.select_one('.role, .title, .position')
                org_elem = elem.select_one('.organization, .company')

                if quote_elem:
                    # IMPORTANT: Exclude any personal names for GDPR compliance
                    testimonial = Testimonial(
                        quote=quote_elem.get_text(strip=True),
                        role=role_elem.get_text(strip=True) if role_elem else None,
                        organization=org_elem.get_text(strip=True) if org_elem else None
                    )
                    testimonials.append(testimonial)
                    logger.debug(f"Extracted testimonial from {testimonial.role or 'unknown role'}")
            except Exception as e:
                logger.warning(f"Failed to extract testimonial from element: {e}")
                continue

        logger.info(f"Extracted {len(testimonials)} testimonials")
        return testimonials

# Example usage
if __name__ == "__main__":
    import asyncio
    from ..utils.logger import setup_logging

    # Setup logging
    setup_logging()

    async def main():
        scraper = UphealScraper()

        # Run scraper
        data = await scraper.scrape()

        # Export results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_path = f"data/processed/upheal_{timestamp}.json"
        csv_path = f"data/processed/upheal_{timestamp}.csv"

        data.export_json(json_path)
        data.export_csv(csv_path)

        print(f"\n✅ Scraping complete!")
        print(f"   Features: {len(data.features)}")
        print(f"   Pricing tiers: {len(data.pricing_tiers)}")
        print(f"   Testimonials: {len(data.testimonials)}")
        print(f"\n📁 Data saved:")
        print(f"   JSON: {json_path}")
        print(f"   CSV: {csv_path}")

    asyncio.run(main())
