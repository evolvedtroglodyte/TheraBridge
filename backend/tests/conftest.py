"""
Pytest configuration and fixtures for backend tests
"""

import pytest
import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


@pytest.fixture
def openai_api_key():
    """OpenAI API key from environment"""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY not set")
    return key


@pytest.fixture
def db():
    """Supabase database client"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        pytest.skip("SUPABASE_URL and SUPABASE_KEY must be set")

    return create_client(supabase_url, supabase_key)


@pytest.fixture
def demo_session_id(db):
    """Get ID of a demo session with transcript"""
    response = (
        db.table("therapy_sessions")
        .select("id")
        .not_.is_("transcript", "null")
        .limit(1)
        .execute()
    )

    if not response.data:
        pytest.skip("No demo sessions with transcripts")

    return response.data[0]["id"]


@pytest.fixture
def session_without_transcript_id(db):
    """Get ID of a session without transcript (for testing error handling)"""
    # First, try to find an existing session without transcript
    response = (
        db.table("therapy_sessions")
        .select("id")
        .is_("transcript", "null")
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]["id"]

    # If no sessions without transcript exist, skip this test
    pytest.skip("No sessions without transcripts found for testing")
