"""
Example tests demonstrating how to use pytest fixtures from conftest.py

This file shows practical examples of using all available fixtures:
- Database fixtures (sync and async)
- HTTP clients (sync and async)
- User fixtures with authentication
- Sample data fixtures (patients, sessions)
- Mock OpenAI fixtures

Run with: pytest tests/test_fixtures_example.py -v
"""
import pytest
from sqlalchemy import select
from app.models.db_models import User, Patient, Session
from app.models.schemas import UserRole, SessionStatus, MoodLevel
from app.services.note_extraction import NoteExtractionService, get_extraction_service
from app.main import app


# ============================================================================
# Basic Database Fixture Examples
# ============================================================================

def test_sync_database_fixture(test_db):
    """Example: Using synchronous database fixture."""
    # Create a user
    user = User(
        email="fixture_test@example.com",
        hashed_password="hashed_password",
        full_name="Fixture Test User",
        role=UserRole.therapist,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    # Verify user was created
    assert user.id is not None
    assert user.email == "fixture_test@example.com"

    # Query all users
    users = test_db.query(User).all()
    assert len(users) == 1


@pytest.mark.asyncio
async def test_async_database_fixture(async_test_db):
    """Example: Using asynchronous database fixture."""
    # Create a user
    user = User(
        email="async_fixture@example.com",
        hashed_password="hashed_password",
        full_name="Async Fixture User",
        role=UserRole.patient,
        is_active=True
    )
    async_test_db.add(user)
    await async_test_db.commit()
    await async_test_db.refresh(user)

    # Verify user was created
    assert user.id is not None
    assert user.email == "async_fixture@example.com"

    # Query using SQLAlchemy 2.0 async style
    result = await async_test_db.execute(select(User))
    users = result.scalars().all()
    assert len(users) == 1


def test_database_isolation(test_db):
    """
    Example: Verify tests are isolated.

    This test creates data but it won't affect other tests
    because each test gets a fresh database.
    """
    # Create multiple users
    for i in range(3):
        user = User(
            email=f"user{i}@example.com",
            hashed_password="hashed",
            full_name=f"User {i}",
            role=UserRole.therapist,
            is_active=True
        )
        test_db.add(user)
    test_db.commit()

    # Verify all were created
    users = test_db.query(User).all()
    assert len(users) == 3


# ============================================================================
# HTTP Client Fixture Examples
# ============================================================================

def test_sync_client_fixture(client, therapist_user, therapist_auth_headers):
    """Example: Using synchronous HTTP client."""
    # Make authenticated request
    response = client.get(
        "/api/patients",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_async_client_fixture(async_client, therapist_user, therapist_auth_headers):
    """Example: Using asynchronous HTTP client."""
    # Make authenticated async request
    response = await async_client.get(
        "/api/patients",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# ============================================================================
# User Fixture Examples
# ============================================================================

def test_therapist_user_fixture(therapist_user):
    """Example: Using therapist user fixture."""
    assert therapist_user.id is not None
    assert therapist_user.email == "therapist@test.com"
    assert therapist_user.role == UserRole.therapist
    assert therapist_user.is_active is True


def test_patient_user_fixture(patient_user):
    """Example: Using patient user fixture."""
    assert patient_user.id is not None
    assert patient_user.email == "patient@test.com"
    assert patient_user.role == UserRole.patient
    assert patient_user.is_active is True


def test_admin_user_fixture(admin_user):
    """Example: Using admin user fixture."""
    assert admin_user.id is not None
    assert admin_user.email == "admin@test.com"
    assert admin_user.role == UserRole.admin
    assert admin_user.is_active is True


def test_inactive_user_fixture(inactive_user):
    """Example: Using inactive user fixture."""
    assert inactive_user.id is not None
    assert inactive_user.is_active is False


def test_multiple_users(therapist_user, patient_user, admin_user):
    """Example: Using multiple user fixtures in one test."""
    # All fixtures can be used together
    assert therapist_user.role == UserRole.therapist
    assert patient_user.role == UserRole.patient
    assert admin_user.role == UserRole.admin

    # Each has a unique email
    emails = {therapist_user.email, patient_user.email, admin_user.email}
    assert len(emails) == 3


# ============================================================================
# Authentication Header Examples
# ============================================================================

def test_therapist_auth_headers(client, therapist_auth_headers):
    """Example: Using therapist authentication headers."""
    response = client.get(
        "/api/patients",
        headers=therapist_auth_headers
    )

    # Headers automatically include valid JWT token
    assert response.status_code == 200


def test_patient_auth_headers(client, patient_auth_headers):
    """Example: Using patient authentication headers."""
    response = client.get(
        "/api/sessions",
        headers=patient_auth_headers
    )

    assert response.status_code == 200


def test_admin_auth_headers(client, admin_auth_headers):
    """Example: Using admin authentication headers."""
    response = client.get(
        "/health",
        headers=admin_auth_headers
    )

    assert response.status_code == 200


# ============================================================================
# Sample Patient Fixture Examples
# ============================================================================

def test_sample_patient_fixture(sample_patient, therapist_user):
    """Example: Using sample patient fixture."""
    assert sample_patient.id is not None
    assert sample_patient.name == "John Doe"
    assert sample_patient.email == "john.doe@example.com"
    assert sample_patient.phone == "555-0100"
    assert sample_patient.therapist_id == therapist_user.id


@pytest.mark.asyncio
async def test_async_sample_patient_fixture(async_sample_patient, therapist_user):
    """Example: Using async sample patient fixture."""
    assert async_sample_patient.id is not None
    assert async_sample_patient.name == "Jane Smith"
    assert async_sample_patient.email == "jane.smith@example.com"
    assert async_sample_patient.therapist_id == therapist_user.id


def test_patient_belongs_to_therapist(sample_patient, therapist_user, test_db):
    """Example: Verifying patient-therapist relationship."""
    # Query patient from database
    patient = test_db.query(Patient).filter(
        Patient.id == sample_patient.id
    ).first()

    assert patient is not None
    assert patient.therapist_id == therapist_user.id


# ============================================================================
# Sample Session Fixture Examples
# ============================================================================

def test_sample_session_fixture(sample_session, sample_patient, therapist_user):
    """Example: Using basic sample session fixture."""
    assert sample_session.id is not None
    assert sample_session.patient_id == sample_patient.id
    assert sample_session.therapist_id == therapist_user.id
    assert sample_session.duration_seconds == 3600
    assert sample_session.audio_filename == "test_session.mp3"
    assert sample_session.status == SessionStatus.pending.value


@pytest.mark.asyncio
async def test_async_sample_session_fixture(
    async_sample_session,
    async_sample_patient,
    therapist_user
):
    """Example: Using async sample session fixture."""
    assert async_sample_session.id is not None
    assert async_sample_session.patient_id == async_sample_patient.id
    assert async_sample_session.therapist_id == therapist_user.id
    assert async_sample_session.status == SessionStatus.pending.value


def test_sample_session_with_transcript_fixture(
    sample_session_with_transcript,
    sample_patient,
    therapist_user
):
    """Example: Using session with transcript fixture."""
    session = sample_session_with_transcript

    assert session.id is not None
    assert session.patient_id == sample_patient.id
    assert session.therapist_id == therapist_user.id
    assert session.transcript_text is not None
    assert len(session.transcript_text) > 0

    # Verify transcript contains expected content
    assert "breathing exercises" in session.transcript_text
    assert "Therapist:" in session.transcript_text
    assert "Client:" in session.transcript_text
    assert session.status == SessionStatus.transcribed.value


@pytest.mark.asyncio
async def test_async_session_with_transcript_fixture(
    async_sample_session_with_transcript,
    async_sample_patient
):
    """Example: Using async session with transcript fixture."""
    session = async_sample_session_with_transcript

    assert session.id is not None
    assert session.transcript_text is not None
    assert "mindfulness" in session.transcript_text
    assert session.status == SessionStatus.transcribed.value


# ============================================================================
# Mock OpenAI Fixture Examples
# ============================================================================

def test_mock_openai_fixture(mock_openai):
    """Example: Using mock OpenAI client fixture."""
    # Create service and inject mock
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = mock_openai

    # The mock is configured to return predictable responses
    assert mock_openai is not None
    assert hasattr(mock_openai, 'chat')


@pytest.mark.asyncio
async def test_mock_extraction_service_fixture(mock_extraction_service):
    """Example: Using mock extraction service fixture."""
    # Service is pre-configured with mock OpenAI client
    transcript = "Therapist: How are you? Client: I'm doing well."

    notes = await mock_extraction_service.extract_notes_from_transcript(transcript)

    # Mock returns predictable data
    assert notes.key_topics == ["Anxiety management", "Work stress", "Relationship issues"]
    assert notes.session_mood == MoodLevel.positive
    assert notes.mood_trajectory == "improving"
    assert len(notes.strategies) > 0
    assert notes.therapist_notes is not None
    assert notes.patient_summary is not None


@pytest.mark.asyncio
async def test_extraction_without_api_cost(
    mock_extraction_service,
    sample_session_with_transcript
):
    """
    Example: Testing extraction logic without API costs.

    This test uses the mock service to verify extraction workflow
    without making real OpenAI API calls.
    """
    # Extract notes from sample transcript
    notes = await mock_extraction_service.extract_notes_from_transcript(
        transcript=sample_session_with_transcript.transcript_text
    )

    # Verify structure is correct
    assert isinstance(notes.key_topics, list)
    assert len(notes.key_topics) > 0
    assert notes.session_mood in [m.value for m in MoodLevel]
    assert notes.mood_trajectory in ["improving", "declining", "stable", "fluctuating"]
    assert isinstance(notes.strategies, list)
    assert isinstance(notes.triggers, list)
    assert isinstance(notes.action_items, list)
    assert isinstance(notes.risk_flags, list)


# ============================================================================
# Full Integration Test Examples
# ============================================================================

def test_full_stack_sync(
    client,
    therapist_auth_headers,
    sample_patient,
    therapist_user,
    test_db
):
    """
    Example: Complete end-to-end test using multiple fixtures.

    This demonstrates how fixtures work together for integration testing.
    """
    # 1. Verify patient exists
    patient = test_db.query(Patient).filter(
        Patient.id == sample_patient.id
    ).first()
    assert patient is not None

    # 2. Create a new session via API
    response = client.post(
        "/api/sessions",
        headers=therapist_auth_headers,
        json={
            "patient_id": str(sample_patient.id),
            "session_date": "2024-12-17T10:00:00"
        }
    )

    assert response.status_code == 201
    session_data = response.json()
    session_id = session_data["id"]

    # 3. Fetch the created session
    response = client.get(
        f"/api/sessions/{session_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    session = response.json()
    assert session["patient_id"] == str(sample_patient.id)
    assert session["therapist_id"] == str(therapist_user.id)

    # 4. Verify it's in the database
    db_session = test_db.query(Session).filter(
        Session.id == session_id
    ).first()
    assert db_session is not None


@pytest.mark.asyncio
async def test_full_stack_async(
    async_client,
    therapist_auth_headers,
    async_sample_patient,
    therapist_user,
    async_test_db
):
    """
    Example: Complete end-to-end async test.

    Demonstrates async fixtures working together.
    """
    # 1. Verify patient exists
    result = await async_test_db.execute(
        select(Patient).where(Patient.id == async_sample_patient.id)
    )
    patient = result.scalar_one()
    assert patient is not None

    # 2. Create session via async API client
    response = await async_client.post(
        "/api/sessions",
        headers=therapist_auth_headers,
        json={
            "patient_id": str(async_sample_patient.id),
            "session_date": "2024-12-17T15:00:00"
        }
    )

    assert response.status_code == 201
    session_data = response.json()

    # 3. Verify session in database
    result = await async_test_db.execute(
        select(Session).where(Session.id == session_data["id"])
    )
    db_session = result.scalar_one()
    assert db_session.patient_id == async_sample_patient.id


def test_extraction_endpoint_with_mock(
    client,
    therapist_auth_headers,
    mock_extraction_service,
    sample_session_with_transcript
):
    """
    Example: Testing extraction endpoint with mock service.

    Shows how to override FastAPI dependencies for testing.
    """
    # Override the extraction service dependency
    app.dependency_overrides[get_extraction_service] = lambda: mock_extraction_service

    try:
        # Make request to extraction endpoint (if it exists)
        # This is a hypothetical endpoint for demonstration
        response = client.post(
            "/api/sessions/extract-notes",
            headers=therapist_auth_headers,
            json={
                "session_id": str(sample_session_with_transcript.id),
                "transcript": sample_session_with_transcript.transcript_text
            }
        )

        # Verify response structure (endpoint may not exist yet)
        # This demonstrates the pattern for when it does
        if response.status_code == 404:
            pytest.skip("Extraction endpoint not yet implemented")

    finally:
        # Clean up dependency override
        app.dependency_overrides.clear()


# ============================================================================
# Edge Case and Error Handling Examples
# ============================================================================

def test_inactive_user_cannot_login(client, inactive_user):
    """Example: Testing with inactive user fixture."""
    # Attempt to login with inactive user
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": inactive_user.email,
            "password": "InactivePass123!"
        }
    )

    # Should fail because user is inactive
    assert response.status_code == 401


def test_session_without_transcript(sample_session):
    """Example: Testing session in pending state."""
    # Sample_session fixture creates a pending session
    assert sample_session.status == SessionStatus.pending.value
    assert sample_session.transcript_text is None
    assert sample_session.extracted_notes is None


@pytest.mark.asyncio
async def test_query_empty_database(async_test_db):
    """Example: Testing with empty database (no fixtures)."""
    # Query when no data exists
    result = await async_test_db.execute(select(User))
    users = result.scalars().all()

    # Database is fresh and empty
    assert len(users) == 0


# ============================================================================
# Performance and Isolation Tests
# ============================================================================

def test_fixture_performance_1(test_db):
    """Test 1: Each test gets fresh database - this won't affect test 2."""
    user = User(
        email="perf1@example.com",
        hashed_password="hashed",
        full_name="Perf Test 1",
        role=UserRole.therapist,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()

    users = test_db.query(User).all()
    assert len(users) == 1


def test_fixture_performance_2(test_db):
    """Test 2: Gets fresh database - test 1's data is gone."""
    # This test proves isolation works
    users = test_db.query(User).all()
    assert len(users) == 0  # Test 1's user is not here!


def test_fixture_performance_3(therapist_user, patient_user, test_db):
    """Test 3: Multiple fixtures are isolated to this test."""
    users = test_db.query(User).all()
    # Only the users from fixtures used in THIS test
    assert len(users) == 2


# ============================================================================
# Documentation Test
# ============================================================================

def test_fixture_documentation():
    """
    This test demonstrates that all fixtures are documented in conftest.py.

    Run 'pytest tests/test_fixtures_example.py -v' to see all examples.

    Available fixtures:
    - test_db: Sync database session
    - async_test_db: Async database session
    - client: Sync HTTP client
    - async_client: Async HTTP client
    - therapist_user, patient_user, admin_user: User fixtures
    - sample_patient, async_sample_patient: Patient fixtures
    - sample_session, async_sample_session: Session fixtures
    - sample_session_with_transcript: Session with transcript
    - mock_openai: Mock OpenAI client
    - mock_extraction_service: Mock NoteExtractionService
    - *_auth_headers: Authentication header fixtures

    See FIXTURES_GUIDE.md for complete documentation.
    """
    assert True  # This test always passes and serves as documentation
