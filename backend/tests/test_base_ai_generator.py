"""
Test suite for BaseAIGenerator

Tests the abstract base class and sync/async variants.
Run with: python -m pytest backend/tests/test_base_ai_generator.py -v
Or directly: python backend/tests/test_base_ai_generator.py
"""

import os
import sys
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.base_ai_generator import (
    BaseAIGenerator,
    SyncAIGenerator,
    AsyncAIGenerator,
    GenerationResult,
)
from app.config.model_config import ModelTier, set_tier, get_current_tier


# =============================================================================
# Test Implementations
# =============================================================================

class MockSyncGenerator(SyncAIGenerator):
    """Test implementation of SyncAIGenerator."""

    def get_task_name(self) -> str:
        return "mood_analysis"

    def build_messages(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": "You are a mood analyzer."},
            {"role": "user", "content": f"Analyze: {context.get('text', '')}"}
        ]


class MockAsyncGenerator(AsyncAIGenerator):
    """Test implementation of AsyncAIGenerator."""

    def get_task_name(self) -> str:
        return "deep_analysis"

    def build_messages(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": "You are a deep analyzer."},
            {"role": "user", "content": f"Analyze: {context.get('transcript', '')}"}
        ]


# =============================================================================
# Tests
# =============================================================================

def test_sync_generator_initialization():
    """Test SyncAIGenerator initializes correctly."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        gen = MockSyncGenerator(api_key="test-key")

        assert gen.api_key == "test-key"
        assert gen.get_task_name() == "mood_analysis"
        assert gen._client is not None

    print("✓ SyncAIGenerator initialization works")


def test_async_generator_initialization():
    """Test AsyncAIGenerator initializes correctly."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        gen = MockAsyncGenerator(api_key="test-key")

        assert gen.api_key == "test-key"
        assert gen.get_task_name() == "deep_analysis"
        assert gen._client is not None

    print("✓ AsyncAIGenerator initialization works")


def test_build_messages():
    """Test message building."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        gen = MockSyncGenerator(api_key="test-key")
        messages = gen.build_messages({"text": "I feel great today"})

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "I feel great today" in messages[1]["content"]

    print("✓ build_messages() works correctly")


def test_model_tier_integration():
    """Test that MODEL_TIER affects model selection."""
    original_tier = get_current_tier()

    try:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            # Test precision tier
            set_tier(ModelTier.PRECISION)
            gen1 = MockSyncGenerator(api_key="test-key")
            assert gen1.model == "gpt-5-nano"  # mood_analysis uses nano

            # Test rapid tier
            set_tier(ModelTier.RAPID)
            gen2 = MockAsyncGenerator(api_key="test-key")
            assert gen2.model == "gpt-5-mini"  # deep_analysis rapid uses mini

        print("✓ MODEL_TIER integration works correctly")
    finally:
        set_tier(original_tier)


def test_override_model():
    """Test model override parameter."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        gen = MockSyncGenerator(api_key="test-key", override_model="gpt-5.2")

        assert gen.model == "gpt-5.2"

    print("✓ Model override works correctly")


def test_api_kwargs():
    """Test default API kwargs."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        gen = MockSyncGenerator(api_key="test-key")
        kwargs = gen.get_api_kwargs()

        assert "response_format" in kwargs
        assert kwargs["response_format"]["type"] == "json_object"

    print("✓ Default API kwargs are correct")


def test_generation_result_structure():
    """Test GenerationResult dataclass."""
    result = GenerationResult(
        content={"mood_score": 7.5},
        cost_info=None,
        raw_response=None
    )

    assert result.content["mood_score"] == 7.5
    assert result.cost_info is None

    print("✓ GenerationResult structure is correct")


def test_sync_generate_with_mock():
    """Test sync generate() with mocked API."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        gen = MockSyncGenerator(api_key="test-key")

        # Mock the client's create method
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"mood_score": 7.5}'))]
        mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50)

        gen._client.chat.completions.create = Mock(return_value=mock_response)

        # Mock cost tracking to avoid database writes
        with patch("app.services.base_ai_generator.track_generation_cost") as mock_track:
            mock_track.return_value = Mock(cost=0.001)

            result = gen.generate({"text": "test"}, session_id="test-session")

            assert result.content["mood_score"] == 7.5
            assert mock_track.called

    print("✓ Sync generate() works with mocked API")


async def test_async_generate_with_mock():
    """Test async generate() with mocked API."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        gen = MockAsyncGenerator(api_key="test-key")

        # Mock the client's create method
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content='{"confidence": 0.85}'))]
        mock_response.usage = Mock(prompt_tokens=200, completion_tokens=100)

        gen._client.chat.completions.create = AsyncMock(return_value=mock_response)

        # Mock cost tracking to avoid database writes
        with patch("app.services.base_ai_generator.track_generation_cost") as mock_track:
            mock_track.return_value = Mock(cost=0.002)

            result = await gen.generate({"transcript": "test transcript"})

            assert result.content["confidence"] == 0.85
            assert mock_track.called

    print("✓ Async generate() works with mocked API")


def test_parse_response():
    """Test response parsing."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
        gen = MockSyncGenerator(api_key="test-key")

        parsed = gen.parse_response('{"key": "value", "number": 42}')

        assert parsed["key"] == "value"
        assert parsed["number"] == 42

    print("✓ parse_response() works correctly")


def test_get_current_model():
    """Test get_current_model() method."""
    original_tier = get_current_tier()

    try:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            set_tier(ModelTier.BALANCED)
            gen = MockAsyncGenerator(api_key="test-key")

            # deep_analysis in balanced tier uses gpt-5
            assert gen.get_current_model() == "gpt-5"

        print("✓ get_current_model() returns correct model")
    finally:
        set_tier(original_tier)


def test_missing_api_key_raises():
    """Test that missing API key raises ValueError."""
    # Clear environment
    with patch.dict(os.environ, {}, clear=True):
        # Remove any cached settings
        with patch("app.services.base_ai_generator.settings") as mock_settings:
            mock_settings.openai_api_key = None

            try:
                gen = MockSyncGenerator()
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "API key required" in str(e)

    print("✓ Missing API key raises ValueError")


def run_all_tests():
    """Run all tests."""
    import asyncio

    print("\n" + "=" * 60)
    print("BaseAIGenerator Tests")
    print("=" * 60 + "\n")

    tests = [
        test_sync_generator_initialization,
        test_async_generator_initialization,
        test_build_messages,
        test_model_tier_integration,
        test_override_model,
        test_api_kwargs,
        test_generation_result_structure,
        test_sync_generate_with_mock,
        test_parse_response,
        test_get_current_model,
        test_missing_api_key_raises,
    ]

    async_tests = [
        test_async_generate_with_mock,
    ]

    passed = 0
    failed = 0

    # Run sync tests
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: ERROR - {e}")
            failed += 1

    # Run async tests
    for test in async_tests:
        try:
            asyncio.run(test())
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: ERROR - {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
