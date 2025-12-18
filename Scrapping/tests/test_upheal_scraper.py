"""
Comprehensive unit tests for UphealScraper.

Tests feature extraction, pricing extraction, testimonial extraction,
edge cases, and error handling using mocked HTML responses.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch, Mock
from decimal import Decimal

# Import scraper components
from src.scraper.scrapers.upheal_scraper import UphealScraper
from src.scraper.models.schemas import Feature, PricingTier, Testimonial, UphealData


# ==================== Fixtures ====================

@pytest.fixture
def mock_html():
    """Load sample HTML from mocks directory."""
    mock_file = Path(__file__).parent / 'mocks' / 'sample_upheal.html'
    return mock_file.read_text()


@pytest.fixture
def scraper():
    """Create scraper instance for testing."""
    return UphealScraper()


# ==================== Initialization Tests ====================

class TestScraperInitialization:
    """Test scraper initialization and configuration."""

    def test_initialization(self, scraper):
        """Test scraper initializes correctly with all dependencies."""
        assert scraper is not None
        assert scraper.parser == 'lxml'
        assert hasattr(scraper, 'http_client')
        assert hasattr(scraper, 'rate_limiter')
        assert scraper.__class__.__name__ == 'UphealScraper'

    def test_get_urls(self, scraper):
        """Test URL generation returns valid Upheal URLs."""
        urls = scraper.get_urls()

        assert isinstance(urls, list)
        assert len(urls) > 0
        # All URLs should contain 'upheal'
        assert all('upheal' in url.lower() for url in urls)

    def test_parser_type(self, scraper):
        """Test scraper uses lxml parser for performance."""
        assert scraper.parser == 'lxml'


# ==================== Feature Extraction Tests ====================

class TestFeatureExtraction:
    """Test feature extraction from HTML."""

    @pytest.mark.asyncio
    async def test_extract_features_from_features_page(self, scraper, mock_html):
        """Test feature extraction from features page URL."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/features")

        # Should extract at least 4 complete features
        assert len(data.features) >= 4

        # Check first feature
        feature = data.features[0]
        assert isinstance(feature, Feature)
        assert feature.name == "AI Session Notes"
        assert "clinical notes" in feature.description.lower()
        assert feature.category == "AI Features"

    @pytest.mark.asyncio
    async def test_extract_multiple_features(self, scraper, mock_html):
        """Test extraction of multiple features with different categories."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/features")

        # Check we have features from different categories
        categories = [f.category for f in data.features if f.category]
        assert "AI Features" in categories
        assert "Clinical Tools" in categories
        assert "Practice Management" in categories

    @pytest.mark.asyncio
    async def test_feature_data_structure(self, scraper, mock_html):
        """Test extracted features have correct Pydantic structure."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/features")

        for feature in data.features:
            # All features must have a name
            assert isinstance(feature.name, str)
            assert len(feature.name) > 0

            # Description can be None or string
            assert feature.description is None or isinstance(feature.description, str)

            # Category can be None or string
            assert feature.category is None or isinstance(feature.category, str)

    @pytest.mark.asyncio
    async def test_features_not_extracted_from_pricing_page(self, scraper, mock_html):
        """Test features are not extracted from pricing page URL."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/pricing")

        # Pricing page should not extract features
        assert len(data.features) == 0


# ==================== Pricing Extraction Tests ====================

class TestPricingExtraction:
    """Test pricing tier extraction from HTML."""

    @pytest.mark.asyncio
    async def test_extract_pricing_tiers(self, scraper, mock_html):
        """Test pricing extraction from pricing page URL."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/pricing")

        # Should extract at least 4 pricing tiers
        assert len(data.pricing_tiers) >= 4

    @pytest.mark.asyncio
    async def test_pricing_tier_structure(self, scraper, mock_html):
        """Test extracted pricing tiers have correct structure."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/pricing")

        # Check Professional tier
        professional = next((t for t in data.pricing_tiers if t.name == "Professional"), None)
        assert professional is not None
        assert isinstance(professional, PricingTier)
        assert professional.price == Decimal("99")
        assert professional.billing_period == "monthly"
        assert len(professional.features) >= 4
        assert "Unlimited sessions" in professional.features
        assert "AI-powered notes" in professional.features

    @pytest.mark.asyncio
    async def test_popular_tier_detection(self, scraper, mock_html):
        """Test detection of popular/recommended pricing tier."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/pricing")

        # Premium tier should be marked as popular
        premium = next((t for t in data.pricing_tiers if t.name == "Premium"), None)
        assert premium is not None
        assert premium.is_popular is True

        # Professional tier should not be marked as popular
        professional = next((t for t in data.pricing_tiers if t.name == "Professional"), None)
        assert professional is not None
        assert professional.is_popular is False

    @pytest.mark.asyncio
    async def test_free_tier_price_handling(self, scraper, mock_html):
        """Test free tier price is parsed as None."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/pricing")

        # Starter tier is free
        starter = next((t for t in data.pricing_tiers if t.name == "Starter"), None)
        assert starter is not None
        assert starter.price is None or starter.price == Decimal("0")

    @pytest.mark.asyncio
    async def test_custom_price_handling(self, scraper, mock_html):
        """Test custom/enterprise pricing is parsed as None."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/pricing")

        # Enterprise tier has custom pricing
        enterprise = next((t for t in data.pricing_tiers if t.name == "Enterprise"), None)
        assert enterprise is not None
        assert enterprise.price is None  # "Custom" should parse to None

    @pytest.mark.asyncio
    async def test_pricing_not_extracted_from_features_page(self, scraper, mock_html):
        """Test pricing is not extracted from features page URL."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/features")

        # Features page should not extract pricing
        assert len(data.pricing_tiers) == 0


# ==================== Testimonial Extraction Tests ====================

class TestTestimonialExtraction:
    """Test testimonial extraction from HTML."""

    @pytest.mark.asyncio
    async def test_extract_testimonials(self, scraper, mock_html):
        """Test testimonial extraction from features page."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/features")

        # Should extract at least 3 testimonials
        assert len(data.testimonials) >= 3

    @pytest.mark.asyncio
    async def test_testimonial_structure(self, scraper, mock_html):
        """Test extracted testimonials have correct structure."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/features")

        # Check first testimonial
        testimonial = data.testimonials[0]
        assert isinstance(testimonial, Testimonial)
        assert "transformed" in testimonial.quote.lower()
        assert testimonial.role == "Licensed Therapist"

    @pytest.mark.asyncio
    async def test_testimonial_with_organization(self, scraper, mock_html):
        """Test testimonial extraction includes organization when present."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/features")

        # Find testimonial with organization
        with_org = next((t for t in data.testimonials if t.organization), None)
        assert with_org is not None
        assert with_org.organization == "Private Practice"
        assert with_org.role == "Clinical Psychologist"

    @pytest.mark.asyncio
    async def test_testimonial_without_organization(self, scraper, mock_html):
        """Test testimonial extraction works without organization field."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/features")

        # Find testimonial without organization
        without_org = next((t for t in data.testimonials if not t.organization), None)
        assert without_org is not None
        assert without_org.quote is not None
        assert without_org.role is not None


# ==================== Edge Case Tests ====================

class TestEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_extract_handles_empty_page(self, scraper):
        """Test extraction handles empty/invalid HTML gracefully."""
        empty_html = "<html><body></body></html>"
        data = await scraper.extract(empty_html, "https://www.upheal.io/test")

        # Should return empty lists, not crash
        assert data.features == []
        assert data.pricing_tiers == []
        assert data.testimonials == []

    @pytest.mark.asyncio
    async def test_missing_feature_description(self, scraper, mock_html):
        """Test extraction handles features missing description."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/features")

        # Should extract "Upcoming Feature" which has no description
        upcoming = next((f for f in data.features if "Upcoming" in f.name), None)
        assert upcoming is not None
        assert upcoming.name == "Upcoming Feature"
        assert upcoming.description is None

    @pytest.mark.asyncio
    async def test_missing_pricing_features(self, scraper, mock_html):
        """Test pricing extraction handles missing feature list."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/pricing")

        # Beta Plan has no features list
        beta = next((t for t in data.pricing_tiers if "Beta" in t.name), None)
        assert beta is not None
        assert isinstance(beta.features, list)
        # Should be empty list, not None
        assert len(beta.features) == 0

    @pytest.mark.asyncio
    async def test_malformed_price_contact_us(self, scraper, mock_html):
        """Test pricing extraction handles 'Contact us' price format."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/pricing")

        # Beta Plan has "Contact us" as price
        beta = next((t for t in data.pricing_tiers if "Beta" in t.name), None)
        assert beta is not None
        # "Contact us" should parse to None
        assert beta.price is None

    @pytest.mark.asyncio
    async def test_unknown_url_pattern(self, scraper, mock_html):
        """Test extraction with unknown URL pattern returns empty data."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/about")

        # Unknown URL type should return empty data
        assert len(data.features) == 0
        assert len(data.pricing_tiers) == 0
        assert len(data.testimonials) == 0

    @pytest.mark.asyncio
    async def test_malformed_html(self, scraper):
        """Test scraper handles malformed HTML without crashing."""
        malformed_html = "<html><div class='feature-card'><h3>Test</div></html>"

        # Should not crash
        data = await scraper.extract(malformed_html, "https://www.upheal.io/features")
        assert data is not None


# ==================== Integration Tests ====================

class TestScraperWorkflow:
    """Test full scraping workflow with mocked HTTP."""

    @pytest.mark.asyncio
    async def test_scrape_workflow_with_mock(self, scraper, mock_html):
        """Test full scraping workflow with mocked HTTP responses."""
        # Mock HTTP client
        with patch.object(scraper.http_client, 'fetch_text', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_html

            # Mock compliance check
            with patch.object(scraper, 'check_compliance', new_callable=AsyncMock) as mock_compliance:
                mock_compliance.return_value = True

                # Run scraper
                data = await scraper.scrape()

                # Verify results
                assert data is not None
                assert isinstance(data, UphealData)
                assert len(data.features) > 0

                # Verify methods called
                mock_compliance.assert_called_once()
                assert mock_fetch.call_count > 0

    @pytest.mark.asyncio
    async def test_scrape_compliance_failure(self, scraper):
        """Test scraper stops if compliance check fails."""
        # Mock compliance check to fail
        with patch.object(scraper, 'check_compliance', new_callable=AsyncMock) as mock_compliance:
            mock_compliance.return_value = False

            # Should raise ValueError
            with pytest.raises(ValueError, match="robots.txt compliance check failed"):
                await scraper.scrape()

    @pytest.mark.asyncio
    async def test_fetch_page_calls_rate_limiter(self, scraper):
        """Test that fetch_page respects rate limiting."""
        with patch.object(scraper.rate_limiter, 'async_wait', new_callable=AsyncMock) as mock_wait:
            with patch.object(scraper.http_client, 'fetch_text', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = "<html></html>"

                await scraper.fetch_page("https://test.com")

                # Verify rate limiter was called before fetch
                mock_wait.assert_called_once()
                mock_fetch.assert_called_once_with("https://test.com")

    @pytest.mark.asyncio
    async def test_data_aggregation_across_pages(self, scraper, mock_html):
        """Test scraper aggregates data from multiple pages."""
        with patch.object(scraper.http_client, 'fetch_text', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_html

            with patch.object(scraper, 'check_compliance', new_callable=AsyncMock) as mock_compliance:
                mock_compliance.return_value = True

                # Mock multiple URLs
                with patch.object(scraper, 'get_urls') as mock_urls:
                    mock_urls.return_value = [
                        "https://www.upheal.io/features",
                        "https://www.upheal.io/pricing"
                    ]

                    data = await scraper.scrape()

                    # Should have data from both pages
                    assert len(data.features) > 0  # from features page
                    assert len(data.pricing_tiers) > 0  # from pricing page


# ==================== Data Model Tests ====================

class TestDataModels:
    """Test Pydantic data models."""

    @pytest.mark.asyncio
    async def test_upheal_data_timestamp(self, scraper, mock_html):
        """Test UphealData includes timestamp."""
        data = await scraper.extract(mock_html, "https://www.upheal.io/features")

        assert data.scraped_at is not None
        assert data.source_url is not None

    @pytest.mark.asyncio
    async def test_feature_validation(self, scraper):
        """Test Feature model validation."""
        # Valid feature
        feature = Feature(
            name="Test Feature",
            description="Test description",
            category="Test Category"
        )
        assert feature.name == "Test Feature"

        # Feature with no description is valid
        feature_no_desc = Feature(name="Test")
        assert feature_no_desc.description is None

    @pytest.mark.asyncio
    async def test_pricing_tier_validation(self, scraper):
        """Test PricingTier model validation."""
        # Valid tier with price
        tier = PricingTier(
            name="Test Plan",
            price=Decimal("99.99"),
            billing_period="monthly",
            features=["Feature 1", "Feature 2"]
        )
        assert tier.price == Decimal("99.99")

        # Valid tier with no price (free)
        free_tier = PricingTier(name="Free Plan")
        assert free_tier.price is None


# ==================== Rate Limiting Tests ====================

@pytest.mark.asyncio
async def test_rate_limiting_respected(scraper):
    """Test that rate limiter is called during each fetch."""
    with patch.object(scraper.rate_limiter, 'async_wait', new_callable=AsyncMock) as mock_wait:
        with patch.object(scraper.http_client, 'fetch_text', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = "<html></html>"

            # Fetch multiple pages
            await scraper.fetch_page("https://test.com/page1")
            await scraper.fetch_page("https://test.com/page2")

            # Verify rate limiter called for each fetch
            assert mock_wait.call_count == 2


# ==================== HTML Parsing Tests ====================

class TestHTMLParsing:
    """Test HTML parsing functionality."""

    def test_parse_html_returns_beautifulsoup(self, scraper, mock_html):
        """Test parse_html returns BeautifulSoup object."""
        soup = scraper.parse_html(mock_html)

        # Should be BeautifulSoup object
        assert soup is not None
        assert hasattr(soup, 'select')
        assert hasattr(soup, 'find')

    def test_parse_html_with_lxml(self, scraper):
        """Test HTML parsing uses lxml parser."""
        html = "<html><body><p>Test</p></body></html>"
        soup = scraper.parse_html(html)

        # Should successfully parse with lxml
        p_tag = soup.find('p')
        assert p_tag is not None
        assert p_tag.text == "Test"
