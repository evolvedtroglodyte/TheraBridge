# OpenAI API Mocking Infrastructure

Complete mocking infrastructure for testing OpenAI API calls without consuming credits or making real API requests.

## Overview

This package provides:
- **MockAsyncOpenAI**: Drop-in replacement for OpenAI's AsyncOpenAI client
- **Sample Responses**: Realistic extraction data matching `ExtractedNotes` schema
- **Error Simulation**: Rate limits, timeouts, and API errors
- **Call Tracking**: Monitor and verify API call behavior
- **Pytest Fixtures**: Ready-to-use fixtures in `conftest.py`

## Quick Start

### Basic Usage

```python
from tests.mocks.openai_mock import MockAsyncOpenAI
from app.services.note_extraction import NoteExtractionService

@pytest.mark.asyncio
async def test_extraction():
    # Create service
    service = NoteExtractionService(api_key="fake-key")

    # Replace client with mock
    service.client = MockAsyncOpenAI()

    # Use normally - no real API calls!
    notes = await service.extract_notes_from_transcript(transcript)

    assert notes.session_mood == "neutral"
```

### Using Pytest Fixtures

```python
@pytest.mark.asyncio
async def test_with_fixture(mock_openai_client):
    service = NoteExtractionService(api_key="fake-key")
    service.client = mock_openai_client

    notes = await service.extract_notes_from_transcript("test")
    assert isinstance(notes, ExtractedNotes)
```

## Available Fixtures

All fixtures are defined in `tests/conftest.py`:

| Fixture | Description |
|---------|-------------|
| `mock_openai_client` | Default mock with realistic response |
| `mock_openai_with_risk_flags` | Response includes risk flags |
| `mock_openai_rate_limit` | Raises `RateLimitError` |
| `mock_openai_timeout` | Raises `APITimeoutError` |
| `mock_openai_api_error` | Raises `APIError` (500) |

### Fixture Examples

```python
@pytest.mark.asyncio
async def test_rate_limit(mock_openai_rate_limit):
    """Test rate limit error handling."""
    service.client = mock_openai_rate_limit

    with pytest.raises(ValueError, match="rate limit"):
        await service.extract_notes_from_transcript("test")

@pytest.mark.asyncio
async def test_risk_detection(mock_openai_with_risk_flags):
    """Test that risk flags are detected."""
    service.client = mock_openai_with_risk_flags

    notes = await service.extract_notes_from_transcript("test")
    assert len(notes.risk_flags) > 0
```

## Custom Responses

### Using `sample_extraction_response()`

Generate custom extraction data:

```python
from tests.mocks.openai_mock import sample_extraction_response, MockAsyncOpenAI

# Customize the response
custom_data = sample_extraction_response(
    key_topics=["Depression", "Family conflict"],
    session_mood="low",
    mood_trajectory="declining",
    include_risk_flags=True,
    num_strategies=3,
    num_action_items=2,
)

# Create mock with custom data
service.client = MockAsyncOpenAI(response_data=custom_data)

notes = await service.extract_notes_from_transcript("test")
assert "Depression" in notes.key_topics
assert notes.session_mood == "low"
```

### Parameters

```python
sample_extraction_response(
    key_topics: Optional[list[str]] = None,  # Default: ["Work stress", "Anxiety management", "Sleep issues"]
    session_mood: str = "neutral",           # very_low, low, neutral, positive, very_positive
    mood_trajectory: str = "stable",         # improving, declining, stable, fluctuating
    include_risk_flags: bool = False,        # Include self-harm risk flag
    num_strategies: int = 2,                 # Number of strategies (0-3)
    num_action_items: int = 2,               # Number of action items (0-3)
)
```

## Error Scenarios

### Rate Limit Error

```python
from tests.mocks.openai_mock import mock_rate_limit_error, MockAsyncOpenAI

service.client = MockAsyncOpenAI(
    error_to_raise=mock_rate_limit_error(retry_after=120)
)

with pytest.raises(ValueError, match="rate limit"):
    await service.extract_notes_from_transcript("test")
```

### Timeout Error

```python
from tests.mocks.openai_mock import mock_timeout_error, MockAsyncOpenAI

service.client = MockAsyncOpenAI(
    error_to_raise=mock_timeout_error()
)

with pytest.raises(ValueError, match="timed out"):
    await service.extract_notes_from_transcript("test")
```

### API Error (500, 502, 503, etc.)

```python
from tests.mocks.openai_mock import mock_api_error, MockAsyncOpenAI

service.client = MockAsyncOpenAI(
    error_to_raise=mock_api_error(
        status_code=503,
        message="Service unavailable"
    )
)

with pytest.raises(ValueError, match="API error"):
    await service.extract_notes_from_transcript("test")
```

## Advanced Usage

### Custom Response Function

Generate responses dynamically based on input:

```python
def custom_response_fn(messages, **kwargs):
    """Generate response based on transcript content."""
    user_message = messages[1]["content"]

    if "anxiety" in user_message.lower():
        return sample_extraction_response(
            key_topics=["Anxiety", "Panic"],
            session_mood="low"
        )
    else:
        return sample_extraction_response(
            session_mood="positive"
        )

service.client = MockAsyncOpenAI(response_fn=custom_response_fn)

# Different inputs produce different outputs
notes1 = await service.extract_notes_from_transcript("I have anxiety")
assert notes1.session_mood == "low"

notes2 = await service.extract_notes_from_transcript("I feel great")
assert notes2.session_mood == "positive"
```

### Call Tracking

Monitor all API calls:

```python
mock_client = MockAsyncOpenAI()
service.client = mock_client

await service.extract_notes_from_transcript("test1")
await service.extract_notes_from_transcript("test2")

# Check call count
assert mock_client.call_count == 2

# Inspect call history
for call in mock_client.call_history:
    print(f"Model: {call['model']}")
    print(f"Temperature: {call['temperature']}")
    print(f"Messages: {call['messages']}")

# Reset tracking
mock_client.reset()
assert mock_client.call_count == 0
```

### Simulated Delay

Test timeout handling with controlled delay:

```python
import time

service.client = MockAsyncOpenAI(delay_seconds=0.5)

start = time.time()
await service.extract_notes_from_transcript("test")
elapsed = time.time() - start

assert elapsed >= 0.5  # Took at least 500ms
```

## Convenience Functions

### `create_mock_with_custom_data()`

Quick custom mock creation:

```python
from tests.mocks.openai_mock import create_mock_with_custom_data

service.client = create_mock_with_custom_data(
    key_topics=["PTSD", "Trauma"],
    session_mood="very_low",
    include_risk_flags=True
)
```

### `create_failing_mock()`

Quick error mock creation:

```python
from tests.mocks.openai_mock import create_failing_mock

# Create mock that raises rate limit error
service.client = create_failing_mock("rate_limit")

# Create mock that raises timeout
service.client = create_failing_mock("timeout")

# Create mock that raises API error
service.client = create_failing_mock("api_error")
```

## Complete Example

```python
import pytest
from app.services.note_extraction import NoteExtractionService
from tests.mocks.openai_mock import (
    MockAsyncOpenAI,
    sample_extraction_response,
    create_failing_mock,
)

class TestNoteExtraction:
    """Complete test suite using mocks."""

    @pytest.mark.asyncio
    async def test_successful_extraction(self):
        """Test successful note extraction."""
        service = NoteExtractionService(api_key="fake")
        service.client = MockAsyncOpenAI()

        transcript = "Therapist: How are you? Client: Better."
        notes = await service.extract_notes_from_transcript(transcript)

        assert len(notes.key_topics) >= 3
        assert notes.session_mood in ["very_low", "low", "neutral", "positive", "very_positive"]

    @pytest.mark.asyncio
    async def test_risk_flag_detection(self):
        """Test detection of risk flags."""
        service = NoteExtractionService(api_key="fake")
        service.client = MockAsyncOpenAI(
            response_data=sample_extraction_response(include_risk_flags=True)
        )

        notes = await service.extract_notes_from_transcript("test")
        assert len(notes.risk_flags) > 0
        assert notes.risk_flags[0].type == "self_harm"

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self):
        """Test graceful handling of rate limits."""
        service = NoteExtractionService(api_key="fake")
        service.client = create_failing_mock("rate_limit")

        with pytest.raises(ValueError, match="rate limit"):
            await service.extract_notes_from_transcript("test")

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test graceful handling of timeouts."""
        service = NoteExtractionService(api_key="fake")
        service.client = create_failing_mock("timeout")

        with pytest.raises(ValueError, match="timed out"):
            await service.extract_notes_from_transcript("test")
```

## Mock API Structure

The `MockAsyncOpenAI` class mimics the real OpenAI client structure:

```python
mock_client = MockAsyncOpenAI()

# Matches real client interface
response = await mock_client.chat.completions.create(
    model="gpt-4o",
    messages=[...],
    temperature=0.3,
    response_format={"type": "json_object"}
)

# Returns MockChatCompletion with:
response.choices[0].message.content  # JSON string
response.id                          # "chatcmpl-mock123"
response.model                       # "gpt-4o"
response.usage.total_tokens          # 2000
```

## Testing Best Practices

1. **Use fixtures for common scenarios** - Don't recreate mocks repeatedly
2. **Test error handling** - Use error fixtures to verify resilience
3. **Verify call parameters** - Check that service calls API correctly
4. **Test edge cases** - Use custom responses for unusual scenarios
5. **Reset between tests** - Use `mock_client.reset()` if needed

## Running Tests

```bash
# Run all mock tests
pytest tests/test_openai_mocks.py -v

# Run specific test
pytest tests/test_openai_mocks.py::test_basic_mock_extraction -v

# Run with coverage
pytest tests/test_openai_mocks.py --cov=tests.mocks --cov-report=html
```

## Files

- `tests/mocks/__init__.py` - Package exports
- `tests/mocks/openai_mock.py` - Mock implementation (700+ lines)
- `tests/conftest.py` - Pytest fixtures (lines 755-849)
- `tests/test_openai_mocks.py` - Example tests demonstrating usage

## Schema Reference

All mock responses match the `ExtractedNotes` Pydantic model:

```python
class ExtractedNotes(BaseModel):
    key_topics: List[str]                    # 3-7 items
    topic_summary: str                       # 2-3 sentences
    strategies: List[Strategy]               # Coping techniques
    emotional_themes: List[str]              # Emotions expressed
    triggers: List[Trigger]                  # Distress triggers
    action_items: List[ActionItem]           # Homework
    significant_quotes: List[SignificantQuote]  # Key quotes
    session_mood: MoodLevel                  # Overall mood
    mood_trajectory: str                     # improving/declining/stable/fluctuating
    follow_up_topics: List[str]              # For next session
    unresolved_concerns: List[str]           # Incomplete topics
    risk_flags: List[RiskFlag]               # Safety concerns
    therapist_notes: str                     # Clinical summary (150-200 words)
    patient_summary: str                     # Patient-facing summary (100-150 words)
```

## Support

For issues or questions:
1. Check `tests/test_openai_mocks.py` for examples
2. Review `tests/mocks/openai_mock.py` source code
3. See existing tests in `tests/` directory
