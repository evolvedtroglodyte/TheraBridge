"""
OpenAI API mocking infrastructure for testing.

This module provides comprehensive mocking for OpenAI AsyncOpenAI client,
including realistic response data and error scenarios.

Usage:
    from tests.mocks.openai_mock import MockAsyncOpenAI, sample_extraction_response

    # In your test
    service.client = MockAsyncOpenAI()
    notes = await service.extract_notes_from_transcript(transcript)

    # Or use pytest fixtures (see conftest.py)
    async def test_extraction(mock_openai_client):
        service.client = mock_openai_client
        # ... test code
"""

import json
from typing import Optional, Dict, Any, Callable
from unittest.mock import AsyncMock, MagicMock
from openai import RateLimitError, APIError, APITimeoutError
import httpx


# ============================================================================
# Sample Response Data
# ============================================================================

def sample_extraction_response(
    key_topics: Optional[list[str]] = None,
    session_mood: str = "neutral",
    mood_trajectory: str = "stable",
    include_risk_flags: bool = False,
    num_strategies: int = 2,
    num_action_items: int = 2,
) -> Dict[str, Any]:
    """
    Generate a sample extraction response matching ExtractedNotes schema.

    This provides realistic sample data for testing without calling the actual API.
    All fields match the expected structure from the ExtractedNotes Pydantic model.

    Args:
        key_topics: List of topics to include (default: ["Work stress", "Anxiety", "Sleep"])
        session_mood: One of: very_low, low, neutral, positive, very_positive
        mood_trajectory: One of: improving, declining, stable, fluctuating
        include_risk_flags: Whether to include risk flags in the response
        num_strategies: Number of strategies to include (default: 2)
        num_action_items: Number of action items to include (default: 2)

    Returns:
        Dict matching ExtractedNotes schema that can be parsed by Pydantic

    Example:
        >>> response = sample_extraction_response(
        ...     key_topics=["Depression", "Family"],
        ...     session_mood="low",
        ...     include_risk_flags=True
        ... )
        >>> notes = ExtractedNotes(**response)
    """
    if key_topics is None:
        key_topics = ["Work stress", "Anxiety management", "Sleep issues"]

    strategies = []
    if num_strategies >= 1:
        strategies.append({
            "name": "Box breathing",
            "category": "breathing",
            "status": "introduced",
            "context": "Introduced as a grounding technique for acute anxiety"
        })
    if num_strategies >= 2:
        strategies.append({
            "name": "Thought journaling",
            "category": "cognitive",
            "status": "assigned",
            "context": "Homework to identify cognitive distortions"
        })
    if num_strategies >= 3:
        strategies.append({
            "name": "Progressive muscle relaxation",
            "category": "mindfulness",
            "status": "practiced",
            "context": "Practiced together during session for sleep preparation"
        })

    action_items = []
    if num_action_items >= 1:
        action_items.append({
            "task": "Practice box breathing twice daily",
            "category": "homework",
            "details": "Morning and evening, 5 minutes each"
        })
    if num_action_items >= 2:
        action_items.append({
            "task": "Journal about work situations that trigger anxiety",
            "category": "reflection",
            "details": "Identify patterns in thoughts and physical sensations"
        })
    if num_action_items >= 3:
        action_items.append({
            "task": "Schedule sleep routine",
            "category": "behavioral",
            "details": "Same bedtime each night, no screens 1 hour before"
        })

    risk_flags = []
    if include_risk_flags:
        risk_flags.append({
            "type": "self_harm",
            "evidence": "Patient mentioned 'sometimes I think about hurting myself'",
            "severity": "medium"
        })

    return {
        "key_topics": key_topics,
        "topic_summary": f"Session focused on {', '.join(key_topics[:2])}. Patient expressed feeling overwhelmed but engaged well with therapeutic interventions.",

        "strategies": strategies,
        "emotional_themes": ["Anxiety", "Stress", "Hope"],
        "triggers": [
            {
                "trigger": "Work deadlines",
                "context": "Patient reports increased anxiety before project due dates",
                "severity": "moderate"
            },
            {
                "trigger": "Team meetings",
                "context": "Social anxiety surfaces in group settings",
                "severity": "mild"
            }
        ],
        "action_items": action_items,

        "significant_quotes": [
            {
                "quote": "I realize I'm not just anxious, I'm exhausted from fighting it",
                "context": "Breakthrough moment recognizing the impact of resistance"
            },
            {
                "quote": "Maybe I don't have to have all the answers right now",
                "context": "Shift toward self-compassion"
            }
        ],

        "session_mood": session_mood,
        "mood_trajectory": mood_trajectory,

        "follow_up_topics": ["Sleep routine effectiveness", "Work boundaries"],
        "unresolved_concerns": ["Family relationship tension"],

        "risk_flags": risk_flags,

        "therapist_notes": "Patient presented with moderate anxiety symptoms related to work stress. Showed good insight and engagement with CBT techniques. Introduced box breathing as an immediate coping tool and assigned thought journaling to track cognitive patterns. Patient demonstrated willingness to practice new strategies. Sleep issues appear to be exacerbating anxiety symptoms. Monitor work stress levels and consider discussing boundaries in next session.",

        "patient_summary": "In today's session, we explored the connection between your work stress and anxiety symptoms. You showed great insight in recognizing how exhausting it's been to fight against anxious feelings. We practiced box breathing together as a tool you can use anytime anxiety spikes. Your homework is to practice this technique twice daily and journal about situations that trigger anxiety. Remember, progress isn't about having all the answers immediately - it's about learning to respond differently."
    }


# ============================================================================
# Mock Response Classes
# ============================================================================

class MockMessage:
    """Mock OpenAI message object"""
    def __init__(self, content: str):
        self.content = content
        self.role = "assistant"


class MockChoice:
    """Mock OpenAI choice object"""
    def __init__(self, content: str):
        self.message = MockMessage(content)
        self.finish_reason = "stop"
        self.index = 0


class MockChatCompletion:
    """Mock OpenAI chat completion response"""
    def __init__(self, content: str):
        self.choices = [MockChoice(content)]
        self.id = "chatcmpl-mock123"
        self.model = "gpt-4o"
        self.object = "chat.completion"
        self.created = 1234567890
        self.usage = MagicMock(
            prompt_tokens=500,
            completion_tokens=1500,
            total_tokens=2000
        )


# ============================================================================
# Mock AsyncOpenAI Client
# ============================================================================

class MockAsyncOpenAI:
    """
    Drop-in replacement for AsyncOpenAI client for testing.

    This mock client allows you to:
    1. Return custom response data
    2. Simulate various error scenarios
    3. Track call history
    4. Control timing/behavior

    Usage:
        # Basic usage with default response
        mock_client = MockAsyncOpenAI()
        service.client = mock_client

        # Custom response
        mock_client = MockAsyncOpenAI(
            response_data=sample_extraction_response(session_mood="positive")
        )

        # Simulate error
        mock_client = MockAsyncOpenAI(error_to_raise=RateLimitError(...))

        # Custom response function
        def custom_response(messages, **kwargs):
            return {"key_topics": ["Custom topic"]}

        mock_client = MockAsyncOpenAI(response_fn=custom_response)
    """

    def __init__(
        self,
        response_data: Optional[Dict[str, Any]] = None,
        response_fn: Optional[Callable] = None,
        error_to_raise: Optional[Exception] = None,
        delay_seconds: float = 0.0,
    ):
        """
        Initialize mock OpenAI client.

        Args:
            response_data: Dict to return as JSON response (default: sample_extraction_response())
            response_fn: Function to call to generate response dynamically
            error_to_raise: Exception to raise instead of returning response
            delay_seconds: Simulated delay before responding (for timeout testing)
        """
        self.response_data = response_data or sample_extraction_response()
        self.response_fn = response_fn
        self.error_to_raise = error_to_raise
        self.delay_seconds = delay_seconds

        # Call tracking
        self.call_count = 0
        self.call_history = []

        # Create nested mock structure matching AsyncOpenAI
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        self.chat.completions.create = self._create_completion

    async def _create_completion(self, **kwargs):
        """
        Mock implementation of chat.completions.create().

        Tracks calls and returns mock response or raises error.
        """
        import asyncio

        # Track the call
        self.call_count += 1
        self.call_history.append(kwargs)

        # Simulate delay if specified
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        # Raise error if configured
        if self.error_to_raise:
            raise self.error_to_raise

        # Generate response
        if self.response_fn:
            # Call response function with all kwargs (not duplicating messages)
            response_data = self.response_fn(**kwargs)
        else:
            response_data = self.response_data

        # Return as mock completion
        response_json = json.dumps(response_data)
        return MockChatCompletion(response_json)

    def reset(self):
        """Reset call tracking"""
        self.call_count = 0
        self.call_history = []


# ============================================================================
# Error Factories
# ============================================================================

def mock_rate_limit_error(
    message: str = "Rate limit exceeded",
    retry_after: int = 60
) -> RateLimitError:
    """
    Create a mock RateLimitError for testing.

    Args:
        message: Error message
        retry_after: Suggested retry delay in seconds

    Returns:
        RateLimitError instance

    Example:
        mock_client = MockAsyncOpenAI(
            error_to_raise=mock_rate_limit_error(retry_after=120)
        )
    """
    response = httpx.Response(
        status_code=429,
        headers={"retry-after": str(retry_after)},
        json={"error": {"message": message, "type": "rate_limit_error"}},
        request=httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    )
    return RateLimitError(
        message=message,
        response=response,
        body={"error": {"message": message, "type": "rate_limit_error"}}
    )


def mock_timeout_error(
    message: str = "Request timed out"
) -> APITimeoutError:
    """
    Create a mock APITimeoutError for testing.

    Args:
        message: Error message

    Returns:
        APITimeoutError instance

    Example:
        mock_client = MockAsyncOpenAI(
            error_to_raise=mock_timeout_error()
        )
    """
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return APITimeoutError(request=request)


def mock_api_error(
    message: str = "Internal server error",
    status_code: int = 500
) -> APIError:
    """
    Create a mock APIError for testing.

    Args:
        message: Error message
        status_code: HTTP status code (500, 502, 503, etc.)

    Returns:
        APIError instance

    Example:
        mock_client = MockAsyncOpenAI(
            error_to_raise=mock_api_error(status_code=503, message="Service unavailable")
        )
    """
    request = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    return APIError(
        message=message,
        request=request,
        body={"error": {"message": message, "type": "server_error"}}
    )


# ============================================================================
# Convenience Functions for Common Scenarios
# ============================================================================

def create_mock_with_custom_data(**kwargs) -> MockAsyncOpenAI:
    """
    Create a mock client with custom extraction data.

    Example:
        mock = create_mock_with_custom_data(
            key_topics=["Depression", "Trauma"],
            session_mood="low",
            include_risk_flags=True
        )
    """
    return MockAsyncOpenAI(
        response_data=sample_extraction_response(**kwargs)
    )


def create_failing_mock(error_type: str = "rate_limit") -> MockAsyncOpenAI:
    """
    Create a mock client that raises an error.

    Args:
        error_type: One of "rate_limit", "timeout", "api_error"

    Example:
        mock = create_failing_mock("timeout")
    """
    errors = {
        "rate_limit": mock_rate_limit_error(),
        "timeout": mock_timeout_error(),
        "api_error": mock_api_error(),
    }

    if error_type not in errors:
        raise ValueError(f"Unknown error type: {error_type}. Choose from: {list(errors.keys())}")

    return MockAsyncOpenAI(error_to_raise=errors[error_type])
