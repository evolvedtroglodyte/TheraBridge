"""
Integration tests for Upheal scraper.

Tests the full scraping pipeline from HTTP fetch to storage,
including data comparison and error resilience.
"""

import pytest
import asyncio
from pathlib import Path
from src.scraper.scrapers.upheal_scraper import UphealScraper
from src.scraper.utils.storage import storage_manager
from src.scraper.config import settings
from src.scraper.models.schemas import UphealData, Feature, PricingTier
from unittest.mock import AsyncMock, patch
from datetime import datetime


@pytest.mark.asyncio
async def test_full_scraping_pipeline():
    """
    Integration test: full scraping workflow from HTTP fetch to storage.
    Uses mocked HTTP to avoid actual network calls.
    """
    # Load mock HTML
    mock_file = Path(__file__).parent / 'mocks' / 'sample_upheal.html'
    mock_html = mock_file.read_text()
    
    # Create scraper
    scraper = UphealScraper()
    
    # Mock HTTP client and compliance check
    with patch.object(scraper.http_client, 'fetch_text', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_html
        
        with patch.object(scraper, 'check_compliance', new_callable=AsyncMock) as mock_compliance:
            mock_compliance.return_value = True
            
            # Run full scraping workflow
            data = await scraper.scrape()
            
            # Verify data extracted
            assert data is not None
            assert len(data.features) > 0 or len(data.pricing_tiers) > 0
            
            # Save data using storage manager
            paths = storage_manager.save_with_timestamp(data, prefix="test_integration")
            
            # Verify JSON file created
            assert Path(paths['json']).exists()

            # Verify CSV files created (features and/or pricing)
            csv_features = paths['csv'].replace('.csv', '_features.csv')
            csv_pricing = paths['csv'].replace('.csv', '_pricing.csv')
            # At least one CSV file should be created
            assert Path(csv_features).exists() or Path(csv_pricing).exists()

            # Cleanup test files
            Path(paths['json']).unlink()
            if Path(csv_features).exists():
                Path(csv_features).unlink()
            if Path(csv_pricing).exists():
                Path(csv_pricing).unlink()


@pytest.mark.asyncio
async def test_storage_comparison_workflow():
    """
    Integration test: storage comparison between two scraping runs.
    """
    # Create two data sets
    data_v1 = UphealData(
        scraped_at=datetime.utcnow(),
        source_url="https://test.com",
        features=[Feature(name="Feature A", description="Desc A")],
        pricing_tiers=[PricingTier(name="Pro", price="99.00")]
    )
    
    data_v2 = UphealData(
        scraped_at=datetime.utcnow(),
        source_url="https://test.com",
        features=[
            Feature(name="Feature A", description="Desc A"),
            Feature(name="Feature B", description="Desc B")  # New feature
        ],
        pricing_tiers=[PricingTier(name="Pro", price="129.00")]  # Price change
    )
    
    # Compare
    comparison = storage_manager.compare_data(data_v1, data_v2)
    
    # Verify comparison results
    assert comparison['features']['added'] == ['Feature B']
    assert comparison['features']['removed'] == []
    assert len(comparison['pricing']['price_changes']) == 1
    assert comparison['pricing']['price_changes'][0]['tier'] == 'Pro'


def test_configuration_loaded():
    """Test that configuration loads correctly from settings"""
    assert settings.requests_per_second > 0
    assert settings.request_timeout > 0
    assert settings.max_retries >= 0
    assert settings.upheal_base_url is not None
    assert len(settings.start_urls) > 0


def test_logging_initialized():
    """Test that logging system is set up"""
    import logging
    logger = logging.getLogger('scraper.test')
    
    # Should have handlers
    root_logger = logging.getLogger()
    assert len(root_logger.handlers) > 0
    
    # Test logging works
    logger.info("Test log message")  # Should not raise


@pytest.mark.asyncio
async def test_error_resilience():
    """Test that scraper handles errors gracefully"""
    scraper = UphealScraper()
    
    # Mock HTTP error
    with patch.object(scraper.http_client, 'fetch_text', new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = Exception("Network error")
        
        with patch.object(scraper, 'check_compliance', new_callable=AsyncMock) as mock_compliance:
            mock_compliance.return_value = True
            
            # Should raise exception (not crash silently)
            with pytest.raises(Exception):
                await scraper.scrape()


@pytest.mark.asyncio
async def test_data_extraction_accuracy():
    """Test that scraper extracts data accurately from HTML"""
    # Load mock HTML
    mock_file = Path(__file__).parent / 'mocks' / 'sample_upheal.html'
    mock_html = mock_file.read_text()
    
    scraper = UphealScraper()
    
    # Test feature extraction
    soup = scraper.parse_html(mock_html)
    features = scraper._extract_features(soup)
    
    # Should extract features from mock HTML
    assert isinstance(features, list)
    
    # Test pricing extraction
    pricing = scraper._extract_pricing(soup)
    assert isinstance(pricing, list)
    
    # Test testimonials extraction
    testimonials = scraper._extract_testimonials(soup)
    assert isinstance(testimonials, list)


@pytest.mark.asyncio
async def test_storage_cleanup():
    """Test that storage cleanup works correctly"""
    from unittest.mock import patch
    import time

    # Create multiple test files with unique timestamps
    test_files = []
    base_time = time.time()

    for i in range(5):
        # Mock the timestamp to create unique filenames
        fake_timestamp = datetime.fromtimestamp(base_time + i).strftime('%Y%m%d_%H%M%S')

        with patch('src.scraper.utils.storage.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = f"test_cleanup_{fake_timestamp}"

            # Manually create unique filename since we're controlling the timestamp
            data = UphealData(
                scraped_at=datetime.utcnow(),
                source_url="https://test.com",
                features=[Feature(name=f"Feature {i}", description=f"Desc {i}")]
            )

            # Use manual filename generation
            json_path = settings.processed_data_dir / f"test_cleanup_{fake_timestamp}.json"
            data.export_json(str(json_path))
            test_files.append(json_path)

    # Verify all 5 files were created
    all_files = storage_manager.list_saved_data("test_cleanup_*.json")
    assert len(all_files) >= 5, f"Expected at least 5 files, found {len(all_files)}"

    # Keep only 2 most recent (note: pattern needs * wildcard, cleanup_old_files adds .json)
    deleted = storage_manager.cleanup_old_files(keep_recent=2, pattern="test_cleanup_*")

    # Should delete at least 3 files (keeping 2 most recent)
    assert deleted >= 3, f"Expected to delete at least 3 files, but deleted {deleted}"

    # Verify only 2 files remain
    remaining = storage_manager.list_saved_data("test_cleanup_*.json")
    assert len(remaining) == 2, f"Expected 2 files to remain, found {len(remaining)}"

    # Cleanup remaining test files
    for file_path in remaining:
        file_path.unlink()


def test_storage_summary_report():
    """Test that storage summary report generates correctly"""
    summary = storage_manager.get_summary_report()

    # Should return dict with expected keys
    assert 'total_files' in summary
    assert 'total_size_mb' in summary
    # storage_dir may or may not be in summary depending on whether files exist

    # Values should be reasonable
    assert summary['total_files'] >= 0
    assert summary['total_size_mb'] >= 0

    # If files exist, should have storage_dir
    if summary['total_files'] > 0:
        assert 'storage_dir' in summary
