# OpenAI Mock - Quick Start Guide

## 30-Second Setup

```python
# 1. Import the mock
from tests.mocks.openai_mock import MockAsyncOpenAI

# 2. Replace the client
service = NoteExtractionService(api_key="fake")
service.client = MockAsyncOpenAI()

# 3. Use normally - no API calls!
notes = await service.extract_notes_from_transcript(transcript)
```

## Common Scenarios

### Default Response
```python
from tests.mocks.openai_mock import MockAsyncOpenAI

service.client = MockAsyncOpenAI()
# Returns neutral mood, 3 topics, 2 strategies, 2 action items
```

### Custom Response
```python
from tests.mocks.openai_mock import create_mock_with_custom_data

service.client = create_mock_with_custom_data(
    key_topics=["Depression", "Trauma"],
    session_mood="low",
    include_risk_flags=True
)
```

### Test Rate Limit
```python
from tests.mocks.openai_mock import create_failing_mock

service.client = create_failing_mock("rate_limit")

with pytest.raises(ValueError, match="rate limit"):
    await service.extract_notes_from_transcript("test")
```

### Test Timeout
```python
service.client = create_failing_mock("timeout")

with pytest.raises(ValueError, match="timed out"):
    await service.extract_notes_from_transcript("test")
```

### Test API Error
```python
service.client = create_failing_mock("api_error")

with pytest.raises(ValueError, match="API error"):
    await service.extract_notes_from_transcript("test")
```

## Using Pytest Fixtures

```python
# No setup needed - just use the fixture!

@pytest.mark.asyncio
async def test_extraction(mock_openai_client):
    service.client = mock_openai_client
    notes = await service.extract_notes_from_transcript("test")
    assert notes.session_mood == "neutral"

@pytest.mark.asyncio
async def test_risk_flags(mock_openai_with_risk_flags):
    service.client = mock_openai_with_risk_flags
    notes = await service.extract_notes_from_transcript("test")
    assert len(notes.risk_flags) > 0

@pytest.mark.asyncio
async def test_rate_limit(mock_openai_rate_limit):
    service.client = mock_openai_rate_limit
    with pytest.raises(ValueError, match="rate limit"):
        await service.extract_notes_from_transcript("test")
```

## Available Fixtures

| Fixture | What it does |
|---------|--------------|
| `mock_openai_client` | Default mock, neutral mood |
| `mock_openai_with_risk_flags` | Includes risk flags |
| `mock_openai_rate_limit` | Raises rate limit error |
| `mock_openai_timeout` | Raises timeout error |
| `mock_openai_api_error` | Raises API error |

## Verify Calls

```python
mock_client = MockAsyncOpenAI()
service.client = mock_client

await service.extract_notes_from_transcript("test")
await service.extract_notes_from_transcript("test")

# Check how many times API was called
assert mock_client.call_count == 2

# Inspect call parameters
for call in mock_client.call_history:
    print(f"Model: {call['model']}")
    print(f"Temperature: {call['temperature']}")
```

## Customize Everything

```python
from tests.mocks.openai_mock import sample_extraction_response, MockAsyncOpenAI

# Generate custom data
data = sample_extraction_response(
    key_topics=["Work stress", "Burnout", "Career change"],
    session_mood="low",              # very_low, low, neutral, positive, very_positive
    mood_trajectory="declining",     # improving, declining, stable, fluctuating
    include_risk_flags=True,         # Add self-harm risk flag
    num_strategies=3,                # 0-3 strategies
    num_action_items=3,              # 0-3 action items
)

# Create mock with that data
service.client = MockAsyncOpenAI(response_data=data)
```

## Run Examples

```bash
# See all 23 examples in action
cd backend
pytest tests/test_openai_mocks.py -v

# Run specific example
pytest tests/test_openai_mocks.py::test_basic_mock_extraction -v
```

## Full Documentation

- **Complete Guide**: `tests/mocks/README.md` (430 lines)
- **All Examples**: `tests/test_openai_mocks.py` (23 tests)
- **Source Code**: `tests/mocks/openai_mock.py` (418 lines)
- **Implementation Summary**: `tests/mocks/IMPLEMENTATION_SUMMARY.md`

## Need Help?

1. Check `tests/test_openai_mocks.py` for working examples
2. Read `tests/mocks/README.md` for detailed docs
3. Look at existing tests using the mocks
