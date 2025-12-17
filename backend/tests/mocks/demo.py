#!/usr/bin/env python
"""
Quick demonstration of OpenAI mocking infrastructure.

Run this to verify the mocking system works correctly.

Usage:
    cd backend
    python -m pytest tests/mocks/demo.py
    # Or: python tests/mocks/demo.py (if PYTHONPATH includes backend)
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path if not already there
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from tests.mocks.openai_mock import (
    MockAsyncOpenAI,
    sample_extraction_response,
    create_mock_with_custom_data,
    create_failing_mock,
)
from app.services.note_extraction import NoteExtractionService


async def demo_basic_mock():
    """Demo 1: Basic mock usage"""
    print("\n" + "="*60)
    print("DEMO 1: Basic Mock Usage")
    print("="*60)

    service = NoteExtractionService(api_key="fake-key")
    service.client = MockAsyncOpenAI()

    transcript = "Therapist: How are you? Client: I'm feeling anxious about work."
    notes = await service.extract_notes_from_transcript(transcript)

    print(f"✓ Mock client created")
    print(f"✓ Extraction completed (no real API call)")
    print(f"✓ Topics: {', '.join(notes.key_topics)}")
    print(f"✓ Mood: {notes.session_mood}")
    print(f"✓ Strategies: {len(notes.strategies)}")
    print(f"✓ Action items: {len(notes.action_items)}")


async def demo_custom_data():
    """Demo 2: Custom response data"""
    print("\n" + "="*60)
    print("DEMO 2: Custom Response Data")
    print("="*60)

    service = NoteExtractionService(api_key="fake-key")
    service.client = create_mock_with_custom_data(
        key_topics=["Depression", "Family conflict", "Self-esteem"],
        session_mood="low",
        include_risk_flags=True,
        num_strategies=3,
    )

    notes = await service.extract_notes_from_transcript("test")

    print(f"✓ Custom mock created")
    print(f"✓ Topics: {', '.join(notes.key_topics)}")
    print(f"✓ Mood: {notes.session_mood}")
    print(f"✓ Risk flags: {len(notes.risk_flags)}")
    print(f"✓ Strategies: {len(notes.strategies)}")


async def demo_error_handling():
    """Demo 3: Error simulation"""
    print("\n" + "="*60)
    print("DEMO 3: Error Simulation")
    print("="*60)

    service = NoteExtractionService(api_key="fake-key")

    # Test rate limit error
    service.client = create_failing_mock("rate_limit")
    try:
        await service.extract_notes_from_transcript("test")
    except ValueError as e:
        print(f"✓ Rate limit error caught: {str(e)[:50]}...")

    # Test timeout error
    service.client = create_failing_mock("timeout")
    try:
        await service.extract_notes_from_transcript("test")
    except ValueError as e:
        print(f"✓ Timeout error caught: {str(e)[:50]}...")

    # Test API error
    service.client = create_failing_mock("api_error")
    try:
        await service.extract_notes_from_transcript("test")
    except ValueError as e:
        print(f"✓ API error caught: {str(e)[:50]}...")


async def demo_call_tracking():
    """Demo 4: Call tracking"""
    print("\n" + "="*60)
    print("DEMO 4: Call Tracking")
    print("="*60)

    service = NoteExtractionService(api_key="fake-key")
    mock_client = MockAsyncOpenAI()
    service.client = mock_client

    # Make multiple calls
    await service.extract_notes_from_transcript("test 1")
    await service.extract_notes_from_transcript("test 2")
    await service.extract_notes_from_transcript("test 3")

    print(f"✓ Made 3 API calls")
    print(f"✓ Call count tracked: {mock_client.call_count}")
    print(f"✓ Call history length: {len(mock_client.call_history)}")
    print(f"✓ First call model: {mock_client.call_history[0]['model']}")
    print(f"✓ First call temperature: {mock_client.call_history[0]['temperature']}")


async def main():
    """Run all demos"""
    print("\n" + "🧪 OpenAI Mock Infrastructure Demo")
    print("="*60)

    await demo_basic_mock()
    await demo_custom_data()
    await demo_error_handling()
    await demo_call_tracking()

    print("\n" + "="*60)
    print("✅ All demos completed successfully!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Check tests/mocks/QUICK_START.md for quick reference")
    print("  2. See tests/mocks/README.md for complete documentation")
    print("  3. Run tests/test_openai_mocks.py for 23 working examples")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
