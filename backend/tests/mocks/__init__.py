"""
OpenAI API mocking infrastructure for testing.

This package provides reusable mocks for OpenAI API calls, including:
- AsyncOpenAI client mocking
- Error scenario simulation (rate limits, timeouts, API errors)
- Sample responses for note extraction
- Pytest fixtures for easy integration
"""

from tests.mocks.openai_mock import (
    MockAsyncOpenAI,
    MockChatCompletion,
    MockChoice,
    MockMessage,
    sample_extraction_response,
    mock_rate_limit_error,
    mock_timeout_error,
    mock_api_error,
)

__all__ = [
    "MockAsyncOpenAI",
    "MockChatCompletion",
    "MockChoice",
    "MockMessage",
    "sample_extraction_response",
    "mock_rate_limit_error",
    "mock_timeout_error",
    "mock_api_error",
]
