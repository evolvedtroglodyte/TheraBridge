"""
Pytest configuration and fixtures for Scrapping tests.

Provides global fixtures and setup for all test files.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_dir():
    """
    Return project root directory.

    Useful for accessing files relative to project root.

    Returns:
        Path: Project root directory
    """
    return project_root


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Reset global singleton instances between tests.

    This ensures test isolation by resetting:
    - Rate limiter state
    - HTTP client connections
    - Any other stateful singletons

    Runs automatically before each test.
    """
    # Reset rate limiter
    try:
        from src.scraper.utils.rate_limiter import rate_limiter
        if hasattr(rate_limiter, 'reset'):
            rate_limiter.reset()
    except ImportError:
        pass  # Rate limiter may not have reset method

    yield

    # Cleanup after test (if needed)


@pytest.fixture
def sample_html_path():
    """
    Return path to sample HTML mock file.

    Returns:
        Path: Path to sample_upheal.html
    """
    return Path(__file__).parent / 'mocks' / 'sample_upheal.html'


# Configure pytest settings
def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.
    """
    config.addinivalue_line(
        "markers",
        "asyncio: mark test as async (using pytest-asyncio)"
    )
    config.addinivalue_line(
        "markers",
        "slow: mark test as slow-running"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires network)"
    )


# Add custom pytest options (if needed)
def pytest_addoption(parser):
    """
    Add custom command-line options to pytest.
    """
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests (requires network)"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection based on command-line options.

    Skip slow/integration tests unless explicitly requested.
    """
    if not config.getoption("--run-slow"):
        skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

    if not config.getoption("--run-integration"):
        skip_integration = pytest.mark.skip(reason="need --run-integration option to run")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)
