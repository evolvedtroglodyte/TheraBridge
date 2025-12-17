"""
Tests demonstrating OpenAI mock infrastructure usage.

This test suite shows how to use the OpenAI mocking infrastructure
for testing without making real API calls or consuming credits.

Run with: pytest tests/test_openai_mocks.py -v
"""

import pytest
from app.services.note_extraction import NoteExtractionService
from app.models.schemas import ExtractedNotes, MoodLevel
from tests.mocks.openai_mock import (
    MockAsyncOpenAI,
    sample_extraction_response,
    mock_rate_limit_error,
    mock_timeout_error,
    mock_api_error,
    create_mock_with_custom_data,
    create_failing_mock,
)


# ============================================================================
# Basic Mock Usage Tests
# ============================================================================

@pytest.mark.asyncio
async def test_basic_mock_extraction():
    """Test basic note extraction with default mock response."""
    # Create service and replace client with mock
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = MockAsyncOpenAI()

    # Extract notes from sample transcript
    transcript = "Therapist: How are you? Client: I'm feeling anxious about work."
    notes = await service.extract_notes_from_transcript(transcript)

    # Verify response structure
    assert isinstance(notes, ExtractedNotes)
    assert len(notes.key_topics) >= 3
    assert notes.session_mood in [m.value for m in MoodLevel]
    assert notes.therapist_notes
    assert notes.patient_summary

    # Verify mock was called
    assert service.client.call_count == 1


@pytest.mark.asyncio
async def test_mock_with_custom_response():
    """Test mock with custom extraction response data."""
    # Create custom response
    custom_data = sample_extraction_response(
        key_topics=["Depression", "Family conflict", "Self-esteem"],
        session_mood="low",
        mood_trajectory="declining",
        include_risk_flags=True,
        num_strategies=3,
        num_action_items=3,
    )

    # Create mock with custom data
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = MockAsyncOpenAI(response_data=custom_data)

    # Extract notes
    transcript = "Test transcript content"
    notes = await service.extract_notes_from_transcript(transcript)

    # Verify custom data was used
    assert "Depression" in notes.key_topics
    assert "Family conflict" in notes.key_topics
    assert notes.session_mood == MoodLevel.low
    assert notes.mood_trajectory == "declining"
    assert len(notes.risk_flags) > 0
    assert len(notes.strategies) == 3
    assert len(notes.action_items) == 3


@pytest.mark.asyncio
async def test_mock_tracks_calls():
    """Test that mock tracks all API calls."""
    service = NoteExtractionService(api_key="fake-test-key")
    mock_client = MockAsyncOpenAI()
    service.client = mock_client

    # Make multiple calls
    transcript = "Test transcript"
    await service.extract_notes_from_transcript(transcript)
    await service.extract_notes_from_transcript(transcript)
    await service.extract_notes_from_transcript(transcript)

    # Verify call tracking
    assert mock_client.call_count == 3
    assert len(mock_client.call_history) == 3

    # Check call history contains expected parameters
    for call in mock_client.call_history:
        assert "model" in call
        assert "messages" in call
        assert call["model"] == "gpt-4o"
        assert call["temperature"] == 0.3


# ============================================================================
# Error Scenario Tests
# ============================================================================

@pytest.mark.asyncio
async def test_rate_limit_error():
    """Test handling of rate limit errors."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = MockAsyncOpenAI(
        error_to_raise=mock_rate_limit_error(retry_after=120)
    )

    # Verify rate limit error is raised and caught
    transcript = "Test transcript"
    with pytest.raises(ValueError, match="rate limit"):
        await service.extract_notes_from_transcript(transcript)


@pytest.mark.asyncio
async def test_timeout_error():
    """Test handling of API timeout errors."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = MockAsyncOpenAI(
        error_to_raise=mock_timeout_error()
    )

    # Verify timeout error is raised and caught
    transcript = "Test transcript"
    with pytest.raises(ValueError, match="timed out"):
        await service.extract_notes_from_transcript(transcript)


@pytest.mark.asyncio
async def test_api_error():
    """Test handling of general API errors."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = MockAsyncOpenAI(
        error_to_raise=mock_api_error(
            status_code=503,
            message="Service temporarily unavailable"
        )
    )

    # Verify API error is raised and caught
    transcript = "Test transcript"
    with pytest.raises(ValueError, match="API error"):
        await service.extract_notes_from_transcript(transcript)


@pytest.mark.asyncio
async def test_different_error_codes():
    """Test handling of different API error codes."""
    service = NoteExtractionService(api_key="fake-test-key")

    # Test 500 error
    service.client = MockAsyncOpenAI(
        error_to_raise=mock_api_error(status_code=500, message="Internal server error")
    )
    with pytest.raises(ValueError, match="API error"):
        await service.extract_notes_from_transcript("test")

    # Test 502 error
    service.client = MockAsyncOpenAI(
        error_to_raise=mock_api_error(status_code=502, message="Bad gateway")
    )
    with pytest.raises(ValueError, match="API error"):
        await service.extract_notes_from_transcript("test")


# ============================================================================
# Fixture Usage Tests
# ============================================================================

@pytest.mark.asyncio
async def test_using_mock_openai_client_fixture(mock_openai_client):
    """Test using the mock_openai_client fixture."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = mock_openai_client

    transcript = "Therapist: How are you feeling? Client: Better, thanks."
    notes = await service.extract_notes_from_transcript(transcript)

    assert isinstance(notes, ExtractedNotes)
    assert notes.session_mood == MoodLevel.neutral  # Default from fixture


@pytest.mark.asyncio
async def test_using_risk_flags_fixture(mock_openai_with_risk_flags):
    """Test using the mock_openai_with_risk_flags fixture."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = mock_openai_with_risk_flags

    transcript = "Client mentioned self-harm thoughts"
    notes = await service.extract_notes_from_transcript(transcript)

    # Verify risk flags are present
    assert len(notes.risk_flags) > 0
    assert notes.risk_flags[0].type == "self_harm"
    assert notes.risk_flags[0].severity in ["low", "medium", "high"]


@pytest.mark.asyncio
async def test_using_rate_limit_fixture(mock_openai_rate_limit):
    """Test using the mock_openai_rate_limit fixture."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = mock_openai_rate_limit

    with pytest.raises(ValueError, match="rate limit"):
        await service.extract_notes_from_transcript("test")


@pytest.mark.asyncio
async def test_using_timeout_fixture(mock_openai_timeout):
    """Test using the mock_openai_timeout fixture."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = mock_openai_timeout

    with pytest.raises(ValueError, match="timed out"):
        await service.extract_notes_from_transcript("test")


@pytest.mark.asyncio
async def test_using_api_error_fixture(mock_openai_api_error):
    """Test using the mock_openai_api_error fixture."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = mock_openai_api_error

    with pytest.raises(ValueError, match="API error"):
        await service.extract_notes_from_transcript("test")


# ============================================================================
# Convenience Function Tests
# ============================================================================

@pytest.mark.asyncio
async def test_create_mock_with_custom_data():
    """Test using create_mock_with_custom_data convenience function."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = create_mock_with_custom_data(
        key_topics=["Trauma", "PTSD"],
        session_mood="very_low",
        include_risk_flags=True,
        num_strategies=1,
        num_action_items=1,
    )

    notes = await service.extract_notes_from_transcript("test")

    assert "Trauma" in notes.key_topics
    assert notes.session_mood == MoodLevel.very_low
    assert len(notes.risk_flags) > 0
    assert len(notes.strategies) == 1
    assert len(notes.action_items) == 1


@pytest.mark.asyncio
async def test_create_failing_mock_rate_limit():
    """Test create_failing_mock with rate_limit error."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = create_failing_mock("rate_limit")

    with pytest.raises(ValueError, match="rate limit"):
        await service.extract_notes_from_transcript("test")


@pytest.mark.asyncio
async def test_create_failing_mock_timeout():
    """Test create_failing_mock with timeout error."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = create_failing_mock("timeout")

    with pytest.raises(ValueError, match="timed out"):
        await service.extract_notes_from_transcript("test")


@pytest.mark.asyncio
async def test_create_failing_mock_api_error():
    """Test create_failing_mock with api_error."""
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = create_failing_mock("api_error")

    with pytest.raises(ValueError, match="API error"):
        await service.extract_notes_from_transcript("test")


# ============================================================================
# Advanced Usage Tests
# ============================================================================

@pytest.mark.asyncio
async def test_custom_response_function():
    """Test using a custom response function."""
    def custom_response_fn(messages, **kwargs):
        """Generate response based on input."""
        # Extract transcript from messages
        user_message = messages[1]["content"]

        # Customize response based on input
        # Check if "panic" appears (unique keyword not in prompt)
        if "panic" in user_message.lower():
            mood = "low"
            topics = ["Anxiety", "Panic attacks"]
        else:
            mood = "positive"
            topics = ["General wellbeing", "Progress"]

        return sample_extraction_response(
            key_topics=topics,
            session_mood=mood
        )

    service = NoteExtractionService(api_key="fake-test-key")
    service.client = MockAsyncOpenAI(response_fn=custom_response_fn)

    # Test with panic transcript
    notes1 = await service.extract_notes_from_transcript(
        "Client: I'm having terrible panic attacks every day"
    )
    assert notes1.session_mood == MoodLevel.low
    assert "Anxiety" in notes1.key_topics

    # Test with positive transcript (no "panic")
    notes2 = await service.extract_notes_from_transcript(
        "Client: I'm feeling great and making wonderful progress"
    )
    assert notes2.session_mood == MoodLevel.positive
    assert "Progress" in notes2.key_topics


@pytest.mark.asyncio
async def test_mock_reset():
    """Test resetting mock call tracking."""
    service = NoteExtractionService(api_key="fake-test-key")
    mock_client = MockAsyncOpenAI()
    service.client = mock_client

    # Make some calls
    await service.extract_notes_from_transcript("test1")
    await service.extract_notes_from_transcript("test2")
    assert mock_client.call_count == 2

    # Reset and verify
    mock_client.reset()
    assert mock_client.call_count == 0
    assert len(mock_client.call_history) == 0

    # Make new call
    await service.extract_notes_from_transcript("test3")
    assert mock_client.call_count == 1


@pytest.mark.asyncio
async def test_simulated_delay():
    """Test mock with simulated delay (for timeout testing)."""
    import time

    service = NoteExtractionService(api_key="fake-test-key")
    service.client = MockAsyncOpenAI(delay_seconds=0.1)

    start = time.time()
    await service.extract_notes_from_transcript("test")
    elapsed = time.time() - start

    # Should take at least 0.1 seconds
    assert elapsed >= 0.1


# ============================================================================
# Schema Validation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_sample_response_valid_schema():
    """Test that sample_extraction_response produces valid ExtractedNotes."""
    # Test default
    data = sample_extraction_response()
    notes = ExtractedNotes(**data)
    assert notes.session_mood in [m.value for m in MoodLevel]

    # Test with custom parameters
    data = sample_extraction_response(
        key_topics=["Test topic"],
        session_mood="very_positive",
        mood_trajectory="improving",
    )
    notes = ExtractedNotes(**data)
    assert "Test topic" in notes.key_topics
    assert notes.session_mood == MoodLevel.very_positive


def test_all_mood_levels_valid():
    """Test that sample_extraction_response works with all mood levels."""
    mood_levels = ["very_low", "low", "neutral", "positive", "very_positive"]

    for mood in mood_levels:
        data = sample_extraction_response(session_mood=mood)
        notes = ExtractedNotes(**data)
        assert notes.session_mood.value == mood


def test_all_mood_trajectories_valid():
    """Test that sample_extraction_response works with all mood trajectories."""
    trajectories = ["improving", "declining", "stable", "fluctuating"]

    for trajectory in trajectories:
        data = sample_extraction_response(mood_trajectory=trajectory)
        notes = ExtractedNotes(**data)
        assert notes.mood_trajectory == trajectory


# ============================================================================
# Integration-style Tests
# ============================================================================

@pytest.mark.asyncio
async def test_full_extraction_workflow():
    """Test a complete extraction workflow with mocks."""
    # Setup service with mock
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = create_mock_with_custom_data(
        key_topics=["Work stress", "Burnout", "Career change"],
        session_mood="low",
        mood_trajectory="stable",
        num_strategies=2,
        num_action_items=3,
    )

    # Sample transcript
    transcript = """
    Therapist: Tell me about what's been going on at work.
    Client: It's been overwhelming. I'm considering a career change because I'm so burned out.
    Therapist: That sounds really difficult. Let's explore some coping strategies.
    """

    # Extract notes
    notes = await service.extract_notes_from_transcript(transcript)

    # Verify complete structure
    assert len(notes.key_topics) >= 3
    assert "Work stress" in notes.key_topics
    assert notes.session_mood == MoodLevel.low
    assert notes.mood_trajectory == "stable"
    assert len(notes.strategies) == 2
    assert len(notes.action_items) == 3
    assert notes.therapist_notes
    assert notes.patient_summary
    assert len(notes.emotional_themes) > 0
    assert len(notes.triggers) > 0

    # Verify call was made with correct parameters
    assert service.client.call_count == 1
    call = service.client.call_history[0]
    assert call["model"] == "gpt-4o"
    assert call["temperature"] == 0.3
    assert call["response_format"] == {"type": "json_object"}


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
