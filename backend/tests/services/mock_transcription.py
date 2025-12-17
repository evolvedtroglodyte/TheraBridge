"""
Mock transcription service for testing without calling external APIs
"""
from typing import Dict, List, Optional
import asyncio
import random


async def mock_transcribe_audio_file(audio_path: str) -> Dict:
    """
    Mock transcription function that returns realistic test data.

    Simulates the transcription pipeline without actually processing audio
    or calling external APIs. Returns structured data matching the expected
    format from the real transcription service.

    Args:
        audio_path: Path to audio file (not actually processed)

    Returns:
        Dict with segments, full_text, language, and duration
    """
    # Simulate processing delay
    await asyncio.sleep(0.1)

    # Generate mock transcript segments
    segments = [
        {
            "start": 0.0,
            "end": 5.2,
            "text": "I've been feeling really anxious about work lately.",
            "speaker": "Client"
        },
        {
            "start": 5.5,
            "end": 10.1,
            "text": "Can you tell me more about what's been triggering this anxiety?",
            "speaker": "Therapist"
        },
        {
            "start": 10.5,
            "end": 18.3,
            "text": "It's mainly the team meetings. I feel like everyone is judging my ideas.",
            "speaker": "Client"
        },
        {
            "start": 18.6,
            "end": 25.0,
            "text": "That sounds difficult. Let's explore some strategies to help you manage those feelings.",
            "speaker": "Therapist"
        },
        {
            "start": 25.3,
            "end": 32.1,
            "text": "I've tried breathing exercises before, but I'm not sure if they help.",
            "speaker": "Client"
        },
        {
            "start": 32.5,
            "end": 40.0,
            "text": "Let's practice box breathing together. Breathe in for 4, hold for 4, out for 4, hold for 4.",
            "speaker": "Therapist"
        }
    ]

    # Combine all text
    full_text = " ".join(seg["text"] for seg in segments)

    return {
        "segments": segments,
        "full_text": full_text,
        "language": "en",
        "duration": 40.0
    }


async def mock_transcribe_with_failure(audio_path: str) -> Dict:
    """
    Mock transcription that always fails.

    Used for testing error handling in the upload pipeline.

    Args:
        audio_path: Path to audio file (not processed)

    Raises:
        Exception: Always raises to simulate transcription failure
    """
    await asyncio.sleep(0.1)
    raise Exception("Transcription service unavailable")


async def mock_transcribe_with_timeout(audio_path: str) -> Dict:
    """
    Mock transcription that times out.

    Used for testing timeout handling.

    Args:
        audio_path: Path to audio file (not processed)

    Raises:
        asyncio.TimeoutError: Always raises to simulate timeout
    """
    await asyncio.sleep(10)  # Longer than any reasonable timeout
    raise asyncio.TimeoutError("Transcription timeout")
