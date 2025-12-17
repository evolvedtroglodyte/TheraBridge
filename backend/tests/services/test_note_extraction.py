# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for note extraction service.

Tests cover:
1. AsyncOpenAI client initialization with timeouts
2. Error handling for RateLimitError, APITimeoutError, APIError
3. JSON parsing error handling
4. Pydantic validation error handling
5. Cost estimation function
6. Mock OpenAI API responses
"""
import pytest
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from openai import RateLimitError, APITimeoutError, APIError
from app.services.note_extraction import NoteExtractionService, EXTRACTION_PROMPT
from app.models.schemas import ExtractedNotes, MoodLevel, StrategyStatus
from tests.fixtures.sample_transcripts import SAMPLE_TRANSCRIPT_1


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_response():
    """Create a mock OpenAI API response with valid extracted notes"""
    return {
        "key_topics": ["Work stress", "Sleep issues", "Cognitive distortions"],
        "topic_summary": "Patient discussed work-related stress, sleep disruption, and cognitive patterns.",
        "strategies": [
            {
                "name": "Box breathing",
                "category": "breathing",
                "status": "reviewed",
                "context": "Previously taught, patient tried it with some success"
            },
            {
                "name": "Evidence checking",
                "category": "cognitive",
                "status": "introduced",
                "context": "Identifying mind-reading and checking assumptions"
            }
        ],
        "emotional_themes": ["anxiety", "stress", "hope"],
        "triggers": [
            {
                "trigger": "Work deadlines",
                "context": "Large project with tight deadline",
                "severity": "moderate"
            }
        ],
        "action_items": [
            {
                "task": "Practice evidence-checking",
                "category": "homework",
                "details": "When assuming others' thoughts, ask for evidence"
            }
        ],
        "significant_quotes": [
            {
                "quote": "I'm going to fail. Everyone will see I can't handle this.",
                "context": "Catastrophizing about work performance"
            }
        ],
        "session_mood": "low",
        "mood_trajectory": "improving",
        "follow_up_topics": ["Sleep quality", "Work boundaries"],
        "unresolved_concerns": ["Long-term career stress"],
        "risk_flags": [],
        "therapist_notes": "Patient experiencing significant work-related stress with sleep disruption. Cognitive distortions present, particularly mind-reading. Responded well to CBT interventions. Continue with cognitive restructuring techniques. Monitor sleep patterns.",
        "patient_summary": "You've been dealing with a lot of stress from work lately, and it's been affecting your sleep. We talked about how you sometimes assume you know what others are thinking without evidence. You're going to practice checking those assumptions and try writing down your worries when you wake up at night."
    }


@pytest.fixture
def mock_openai_client():
    """Create a mock AsyncOpenAI client"""
    client = AsyncMock()
    client.chat = AsyncMock()
    client.chat.completions = AsyncMock()
    return client


# ============================================================================
# Initialization Tests
# ============================================================================

def test_service_initialization_with_api_key():
    """Test service initializes correctly with provided API key"""
    service = NoteExtractionService(api_key="test-key-123", timeout=60.0)

    assert service.api_key == "test-key-123"
    assert service.default_timeout == 60.0
    assert service.model == "gpt-4o"
    assert service.client is not None


def test_service_initialization_with_env_api_key(monkeypatch):
    """Test service initializes with API key from environment"""
    monkeypatch.setenv("OPENAI_API_KEY", "env-key-456")

    service = NoteExtractionService()

    assert service.api_key == "env-key-456"


def test_service_initialization_without_api_key(monkeypatch):
    """Test service raises error when no API key is available"""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(ValueError, match="OPENAI_API_KEY not found in environment"):
        NoteExtractionService(api_key=None)


def test_service_initialization_with_custom_timeout(monkeypatch):
    """Test service uses custom timeout from parameter"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    service = NoteExtractionService(timeout=180.0)

    assert service.default_timeout == 180.0


def test_service_initialization_with_env_timeout(monkeypatch):
    """Test service uses timeout from environment variable"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_TIMEOUT", "90.0")

    service = NoteExtractionService()

    assert service.default_timeout == 90.0


# ============================================================================
# Successful Extraction Tests
# ============================================================================

@pytest.mark.asyncio
async def test_extract_notes_success(monkeypatch, mock_openai_response):
    """Test successful note extraction with valid transcript"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Create mock response
    mock_message = MagicMock()
    mock_message.content = json.dumps(mock_openai_response)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    # Patch the AsyncOpenAI client
    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()
        notes = await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)

    # Verify result
    assert isinstance(notes, ExtractedNotes)
    assert len(notes.key_topics) == 3
    assert notes.session_mood == MoodLevel.low
    assert notes.mood_trajectory == "improving"
    assert len(notes.strategies) == 2
    assert len(notes.action_items) == 1
    assert len(notes.triggers) == 1
    assert notes.therapist_notes
    assert notes.patient_summary


@pytest.mark.asyncio
async def test_extract_notes_with_custom_timeout(monkeypatch, mock_openai_response):
    """Test note extraction with custom timeout parameter"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Create mock response
    mock_message = MagicMock()
    mock_message.content = json.dumps(mock_openai_response)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_create = AsyncMock(return_value=mock_response)
        mock_client.chat.completions.create = mock_create
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()
        notes = await service.extract_notes_from_transcript(
            SAMPLE_TRANSCRIPT_1,
            timeout=30.0
        )

        # Verify custom timeout was used
        call_args = mock_create.call_args
        assert call_args.kwargs['timeout'] == 30.0

    assert isinstance(notes, ExtractedNotes)


@pytest.mark.asyncio
async def test_extract_notes_strips_markdown_code_blocks(monkeypatch):
    """Test that markdown code blocks are stripped from response"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    valid_json = {
        "key_topics": ["Topic 1"],
        "topic_summary": "Summary here",
        "strategies": [],
        "emotional_themes": [],
        "triggers": [],
        "action_items": [],
        "significant_quotes": [],
        "session_mood": "neutral",
        "mood_trajectory": "stable",
        "follow_up_topics": [],
        "unresolved_concerns": [],
        "risk_flags": [],
        "therapist_notes": "Notes here",
        "patient_summary": "Summary here"
    }

    # Response wrapped in markdown code block
    mock_message = MagicMock()
    mock_message.content = f"```json\n{json.dumps(valid_json)}\n```"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()
        notes = await service.extract_notes_from_transcript("Test transcript")

    assert isinstance(notes, ExtractedNotes)
    assert notes.key_topics == ["Topic 1"]


# ============================================================================
# Error Handling Tests - OpenAI API Errors
# ============================================================================

@pytest.mark.asyncio
async def test_extract_notes_rate_limit_error(monkeypatch):
    """Test handling of OpenAI rate limit error"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Create mock response and body for RateLimitError
    mock_response = MagicMock()
    mock_response.status_code = 429
    mock_body = {"error": {"message": "Rate limit exceeded"}}

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError("Rate limit exceeded", response=mock_response, body=mock_body)
        )
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()

        with pytest.raises(ValueError, match="OpenAI rate limit exceeded"):
            await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)


@pytest.mark.asyncio
async def test_extract_notes_api_timeout_error(monkeypatch):
    """Test handling of OpenAI API timeout error"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError("Request timed out")
        )
        mock_client_class.return_value = mock_client

        service = NoteExtractionService(timeout=60.0)

        with pytest.raises(ValueError, match="OpenAI API request timed out after 60.0s"):
            await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)


@pytest.mark.asyncio
async def test_extract_notes_api_error(monkeypatch):
    """Test handling of general OpenAI API error"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Create mock request, body, and APIError
    mock_request = MagicMock()
    mock_request.method = "POST"
    mock_request.url = "https://api.openai.com/v1/chat/completions"
    mock_body = {"error": {"message": "Service unavailable"}}

    mock_error = APIError("Service unavailable", request=mock_request, body=mock_body)
    mock_error.status_code = 503

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(side_effect=mock_error)
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()

        with pytest.raises(ValueError, match="OpenAI API error"):
            await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)


@pytest.mark.asyncio
async def test_extract_notes_unexpected_error(monkeypatch):
    """Test handling of unexpected errors during API call"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=RuntimeError("Unexpected error")
        )
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()

        with pytest.raises(ValueError, match="Unexpected error during note extraction"):
            await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)


# ============================================================================
# Error Handling Tests - JSON Parsing
# ============================================================================

@pytest.mark.asyncio
async def test_extract_notes_invalid_json(monkeypatch):
    """Test handling of invalid JSON response from OpenAI"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Create mock response with invalid JSON
    mock_message = MagicMock()
    mock_message.content = "This is not valid JSON { incomplete"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()

        with pytest.raises(ValueError, match="Failed to parse OpenAI response as JSON"):
            await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)


@pytest.mark.asyncio
async def test_extract_notes_json_decode_error_with_position(monkeypatch):
    """Test that JSON decode error includes position information"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Create mock response with malformed JSON
    mock_message = MagicMock()
    mock_message.content = '{"key": invalid}'

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()

        with pytest.raises(ValueError) as exc_info:
            await service.extract_notes_from_transcript("Test transcript")

        error_msg = str(exc_info.value)
        assert "Failed to parse OpenAI response as JSON" in error_msg
        assert "line" in error_msg
        assert "column" in error_msg


# ============================================================================
# Error Handling Tests - Pydantic Validation
# ============================================================================

@pytest.mark.asyncio
async def test_extract_notes_missing_required_fields(monkeypatch):
    """Test handling of Pydantic validation error for missing required fields"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Response missing required fields
    incomplete_data = {
        "key_topics": ["Topic 1"],
        # Missing topic_summary, mood fields, etc.
    }

    mock_message = MagicMock()
    mock_message.content = json.dumps(incomplete_data)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()

        with pytest.raises(ValueError, match="Extracted data failed validation"):
            await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)


@pytest.mark.asyncio
async def test_extract_notes_invalid_enum_values(monkeypatch):
    """Test handling of invalid enum values in response"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Response with invalid mood enum value
    invalid_data = {
        "key_topics": ["Topic 1"],
        "topic_summary": "Summary here",
        "strategies": [],
        "emotional_themes": [],
        "triggers": [],
        "action_items": [],
        "significant_quotes": [],
        "session_mood": "super_happy",  # Invalid enum value
        "mood_trajectory": "stable",
        "follow_up_topics": [],
        "unresolved_concerns": [],
        "risk_flags": [],
        "therapist_notes": "Notes",
        "patient_summary": "Summary"
    }

    mock_message = MagicMock()
    mock_message.content = json.dumps(invalid_data)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()

        with pytest.raises(ValueError, match="Extracted data failed validation"):
            await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)


@pytest.mark.asyncio
async def test_extract_notes_invalid_nested_object(monkeypatch):
    """Test handling of validation errors in nested objects"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Response with invalid strategy status
    invalid_data = {
        "key_topics": ["Topic 1"],
        "topic_summary": "Summary here",
        "strategies": [
            {
                "name": "Deep breathing",
                "category": "breathing",
                "status": "completed",  # Invalid status (not in enum)
                "context": "Practiced in session"
            }
        ],
        "emotional_themes": [],
        "triggers": [],
        "action_items": [],
        "significant_quotes": [],
        "session_mood": "neutral",
        "mood_trajectory": "stable",
        "follow_up_topics": [],
        "unresolved_concerns": [],
        "risk_flags": [],
        "therapist_notes": "Notes",
        "patient_summary": "Summary"
    }

    mock_message = MagicMock()
    mock_message.content = json.dumps(invalid_data)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()

        with pytest.raises(ValueError, match="Extracted data failed validation"):
            await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)


# ============================================================================
# Cost Estimation Tests
# ============================================================================

def test_estimate_cost_short_transcript(monkeypatch):
    """Test cost estimation for short transcript"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    service = NoteExtractionService()

    short_transcript = "Patient discussed anxiety. Therapist provided coping strategies."
    cost = service.estimate_cost(short_transcript)

    assert "estimated_input_tokens" in cost
    assert "estimated_output_tokens" in cost
    assert "estimated_cost_usd" in cost
    assert cost["estimated_input_tokens"] > 0
    assert cost["estimated_output_tokens"] == 1500
    assert cost["estimated_cost_usd"] > 0
    assert cost["estimated_cost_usd"] < 0.05  # Should be very cheap


def test_estimate_cost_medium_transcript(monkeypatch):
    """Test cost estimation for medium-length transcript"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    service = NoteExtractionService()

    cost = service.estimate_cost(SAMPLE_TRANSCRIPT_1)

    assert cost["estimated_input_tokens"] > 0
    assert cost["estimated_output_tokens"] == 1500
    assert cost["estimated_cost_usd"] > 0
    assert cost["estimated_cost_usd"] < 0.50  # Should be pennies


def test_estimate_cost_long_transcript(monkeypatch):
    """Test cost estimation for long transcript"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    service = NoteExtractionService()

    # Create a long transcript (10x the sample)
    long_transcript = SAMPLE_TRANSCRIPT_1 * 10
    cost = service.estimate_cost(long_transcript)

    assert cost["estimated_input_tokens"] > 5000  # Should be significantly larger
    assert cost["estimated_output_tokens"] == 1500
    assert cost["estimated_cost_usd"] > 0.02  # More expensive but still cheap


def test_estimate_cost_includes_prompt_tokens(monkeypatch):
    """Test that cost estimation includes prompt tokens"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    service = NoteExtractionService()

    # Even empty transcript should have cost from prompt
    cost = service.estimate_cost("")

    # Prompt is about 1500 chars, so ~375 tokens
    assert cost["estimated_input_tokens"] > 300
    assert cost["estimated_cost_usd"] > 0


def test_estimate_cost_returns_rounded_values(monkeypatch):
    """Test that cost estimation returns properly rounded values"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    service = NoteExtractionService()

    cost = service.estimate_cost(SAMPLE_TRANSCRIPT_1)

    # Check that cost is rounded to 4 decimal places
    assert round(cost["estimated_cost_usd"], 4) == cost["estimated_cost_usd"]


# ============================================================================
# Integration-like Tests
# ============================================================================

@pytest.mark.asyncio
async def test_extract_notes_with_empty_lists(monkeypatch):
    """Test extraction with empty optional lists"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    minimal_data = {
        "key_topics": ["Simple topic"],
        "topic_summary": "Brief session summary",
        "strategies": [],  # Empty list
        "emotional_themes": [],  # Empty list
        "triggers": [],  # Empty list
        "action_items": [],  # Empty list
        "significant_quotes": [],  # Empty list
        "session_mood": "neutral",
        "mood_trajectory": "stable",
        "follow_up_topics": [],  # Empty list
        "unresolved_concerns": [],  # Empty list
        "risk_flags": [],  # Empty list
        "therapist_notes": "Brief notes",
        "patient_summary": "Brief summary"
    }

    mock_message = MagicMock()
    mock_message.content = json.dumps(minimal_data)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()
        notes = await service.extract_notes_from_transcript("Short session")

    assert isinstance(notes, ExtractedNotes)
    assert len(notes.strategies) == 0
    assert len(notes.triggers) == 0
    assert len(notes.action_items) == 0
    assert len(notes.risk_flags) == 0


@pytest.mark.asyncio
async def test_extract_notes_api_call_parameters(monkeypatch):
    """Test that API is called with correct parameters"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    valid_response = {
        "key_topics": ["Topic"],
        "topic_summary": "Summary",
        "strategies": [],
        "emotional_themes": [],
        "triggers": [],
        "action_items": [],
        "significant_quotes": [],
        "session_mood": "neutral",
        "mood_trajectory": "stable",
        "follow_up_topics": [],
        "unresolved_concerns": [],
        "risk_flags": [],
        "therapist_notes": "Notes",
        "patient_summary": "Summary"
    }

    mock_message = MagicMock()
    mock_message.content = json.dumps(valid_response)

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_create = AsyncMock(return_value=mock_response)
        mock_client.chat.completions.create = mock_create
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()
        await service.extract_notes_from_transcript(SAMPLE_TRANSCRIPT_1)

        # Verify API call parameters
        call_args = mock_create.call_args
        assert call_args.kwargs['model'] == 'gpt-4o'
        assert call_args.kwargs['temperature'] == 0.3
        assert call_args.kwargs['response_format'] == {"type": "json_object"}
        assert call_args.kwargs['timeout'] == 120.0  # Default timeout

        # Verify messages structure
        messages = call_args.kwargs['messages']
        assert len(messages) == 2
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert SAMPLE_TRANSCRIPT_1 in messages[1]['content']


# ============================================================================
# Edge Cases
# ============================================================================

@pytest.mark.asyncio
def test_estimate_cost_with_zero_length_transcript(monkeypatch):
    """Test cost estimation with empty transcript"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    service = NoteExtractionService()

    cost = service.estimate_cost("")

    # Should still have cost from prompt
    assert cost["estimated_input_tokens"] > 0
    assert cost["estimated_cost_usd"] > 0


@pytest.mark.asyncio
async def test_extract_notes_response_with_generic_code_block(monkeypatch):
    """Test that generic code blocks (without json specifier) are also stripped"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    valid_json = {
        "key_topics": ["Topic 1"],
        "topic_summary": "Summary here",
        "strategies": [],
        "emotional_themes": [],
        "triggers": [],
        "action_items": [],
        "significant_quotes": [],
        "session_mood": "neutral",
        "mood_trajectory": "stable",
        "follow_up_topics": [],
        "unresolved_concerns": [],
        "risk_flags": [],
        "therapist_notes": "Notes here",
        "patient_summary": "Summary here"
    }

    # Response wrapped in generic code block
    mock_message = MagicMock()
    mock_message.content = f"```\n{json.dumps(valid_json)}\n```"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    with patch('app.services.note_extraction.AsyncOpenAI') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_client_class.return_value = mock_client

        service = NoteExtractionService()
        notes = await service.extract_notes_from_transcript("Test transcript")

    assert isinstance(notes, ExtractedNotes)
    assert notes.key_topics == ["Topic 1"]
