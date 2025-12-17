"""
Pytest fixtures for authentication integration tests.

This module provides test fixtures for:
- Test database setup/teardown (sync and async)
- FastAPI test client (sync and async)
- Test user creation (therapists, patients, admins)
- Sample data (patients, sessions)
- Mock OpenAI client
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import create_engine, event, JSON
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base, get_db
from app.auth.dependencies import get_db as get_sync_db
from app.main import app
from app.models.db_models import User, Patient, Session
from app.auth.models import AuthSession
from app.auth.utils import get_password_hash
from app.models.schemas import UserRole, SessionStatus, ExtractedNotes, MoodLevel
from app.services.note_extraction import NoteExtractionService, get_extraction_service

# Use SQLite database for tests
# NOTE: Using file-based database instead of :memory: to allow sync and async
# engines to share data. Each test gets a fresh database.
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
ASYNC_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Sync engine for auth tests
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    isolation_level="READ UNCOMMITTED"  # Allow reading uncommitted data
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Async engine for async tests
async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    isolation_level="READ UNCOMMITTED"  # Allow reading uncommitted data
)
AsyncTestingSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Convert JSONB to JSON for SQLite compatibility
@event.listens_for(Base.metadata, "before_create")
def _set_json_columns(target, connection, **kw):
    """
    Convert JSONB columns to JSON for SQLite.

    SQLite doesn't support JSONB (PostgreSQL-specific type),
    so we replace it with JSON for tests.
    """
    from app.models.db_models import Session

    # Only convert if using SQLite
    if connection.dialect.name == "sqlite":
        for col in Session.__table__.columns:
            if isinstance(col.type, JSONB):
                col.type = JSON()


@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh database for each test (sync version).

    This fixture:
    1. Creates all tables
    2. Provides a database session
    3. Cleans up after the test

    Yields:
        SQLAlchemy Session for test database
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables to ensure clean state
        Base.metadata.drop_all(bind=engine)


@pytest_asyncio.fixture(scope="function")
async def async_test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh async database session for each test.

    This fixture:
    1. Creates all tables
    2. Provides an async database session with transaction rollback
    3. Ensures test isolation via nested transactions
    4. Cleans up after the test

    Yields:
        AsyncSession for test database

    Usage:
        @pytest.mark.asyncio
        async def test_something(async_test_db: AsyncSession):
            result = await async_test_db.execute(select(User))
            users = result.scalars().all()
    """
    # Create all tables
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session with transaction for rollback
    async with AsyncTestingSessionLocal() as session:
        async with session.begin():
            yield session
            await session.rollback()

    # Drop all tables to ensure clean state
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def client(test_db):
    """
    FastAPI test client with overridden database dependency (sync version).

    This fixture:
    1. Overrides the get_db dependency to use test database
    2. Provides a TestClient for making HTTP requests
    3. Cleans up dependency overrides after test

    Args:
        test_db: Test database session fixture

    Yields:
        TestClient for making API requests

    Usage:
        def test_endpoint(client: TestClient):
            response = client.get("/api/endpoint")
            assert response.status_code == 200
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_sync_db] = override_get_db

    # Create test client
    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_client(async_test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for testing async endpoints.

    This fixture:
    1. Overrides async database dependency to use test database
    2. Provides an AsyncClient for making async HTTP requests
    3. Cleans up dependency overrides after test

    Args:
        async_test_db: Async test database session fixture

    Yields:
        AsyncClient for making async API requests

    Usage:
        @pytest.mark.asyncio
        async def test_async_endpoint(async_client: AsyncClient):
            response = await async_client.get("/api/endpoint")
            assert response.status_code == 200
    """
    async def override_get_db():
        yield async_test_db

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create async client
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(test_db):
    """
    Create a test user in the database.

    This fixture creates a therapist user with known credentials
    for testing authentication flows.

    Args:
        test_db: Test database session fixture

    Returns:
        User object with the following credentials:
        - email: test@example.com
        - password: TestPass123!
        - role: therapist
    """
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        first_name="Test",
        last_name="User",
        full_name="Test User",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_patient_user(test_db):
    """
    Create a test patient user in the database.

    Args:
        test_db: Test database session fixture

    Returns:
        User object with patient role
    """
    user = User(
        email="patient@example.com",
        hashed_password=get_password_hash("PatientPass123!"),
        first_name="Test",
        last_name="Patient",
        full_name="Test Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def inactive_user(test_db):
    """
    Create an inactive test user in the database.

    Used for testing that inactive accounts cannot log in.

    Args:
        test_db: Test database session fixture

    Returns:
        Inactive User object
    """
    user = User(
        email="inactive@example.com",
        hashed_password=get_password_hash("InactivePass123!"),
        first_name="Inactive",
        last_name="User",
        full_name="Inactive User",
        role=UserRole.therapist,
        is_active=False,
        is_verified=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def therapist_user(test_db):
    """
    Create a test therapist user in the database.

    This fixture creates a therapist user with known credentials
    for testing RBAC and authentication flows.

    Args:
        test_db: Test database session fixture

    Returns:
        User object with the following credentials:
        - email: therapist@test.com
        - password: testpass123
        - role: therapist
    """
    user = User(
        email="therapist@test.com",
        hashed_password=get_password_hash("testpass123"),
        first_name="Test",
        last_name="Therapist",
        full_name="Test Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def patient_user(test_db):
    """
    Create a test patient user in the database.

    Args:
        test_db: Test database session fixture

    Returns:
        User object with patient role
        - email: patient@test.com
        - password: patientpass123
        - role: patient
    """
    user = User(
        email="patient@test.com",
        hashed_password=get_password_hash("patientpass123"),
        first_name="Test",
        last_name="Patient User",
        full_name="Test Patient User",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def admin_user(test_db):
    """
    Create a test admin user in the database.

    Args:
        test_db: Test database session fixture

    Returns:
        User object with admin role
        - email: admin@test.com
        - password: adminpass123
        - role: admin
    """
    user = User(
        email="admin@test.com",
        hashed_password=get_password_hash("adminpass123"),
        first_name="Test",
        last_name="Admin",
        full_name="Test Admin",
        role=UserRole.admin,
        is_active=True,
        is_verified=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def therapist_token(therapist_user):
    """
    Generate an access token for the therapist user.

    Args:
        therapist_user: Therapist user fixture

    Returns:
        JWT access token string
    """
    from app.auth.utils import create_access_token
    return create_access_token(therapist_user.id, therapist_user.role.value)


@pytest.fixture(scope="function")
def patient_token(patient_user):
    """
    Generate an access token for the patient user.

    Args:
        patient_user: Patient user fixture

    Returns:
        JWT access token string
    """
    from app.auth.utils import create_access_token
    return create_access_token(patient_user.id, patient_user.role.value)


@pytest.fixture(scope="function")
def admin_token(admin_user):
    """
    Generate an access token for the admin user.

    Args:
        admin_user: Admin user fixture

    Returns:
        JWT access token string
    """
    from app.auth.utils import create_access_token
    return create_access_token(admin_user.id, admin_user.role.value)


@pytest.fixture(scope="function")
def therapist_auth_headers(therapist_token):
    """
    Generate authorization headers for therapist user.

    Args:
        therapist_token: JWT token for therapist

    Returns:
        Dict with Authorization header
    """
    return {"Authorization": f"Bearer {therapist_token}"}


@pytest.fixture(scope="function")
def patient_auth_headers(patient_token):
    """
    Generate authorization headers for patient user.

    Args:
        patient_token: JWT token for patient

    Returns:
        Dict with Authorization header
    """
    return {"Authorization": f"Bearer {patient_token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(admin_token):
    """
    Generate authorization headers for admin user.

    Args:
        admin_token: JWT token for admin

    Returns:
        Dict with Authorization header
    """
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="function")
def db_session(test_db):
    """
    Alias for test_db fixture for compatibility with test files.

    Args:
        test_db: Test database session fixture

    Returns:
        SQLAlchemy Session for test database
    """
    return test_db


# ============================================================================
# Sample Data Fixtures - Patients and Sessions
# ============================================================================

@pytest.fixture(scope="function")
def sample_patient(test_db, therapist_user):
    """
    Create a sample patient for testing.

    Args:
        test_db: Test database session
        therapist_user: Therapist who owns this patient

    Returns:
        Patient object with basic information
    """
    patient = Patient(
        name="John Doe",
        email="john.doe@example.com",
        phone="555-0100",
        therapist_id=therapist_user.id
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)
    return patient


@pytest_asyncio.fixture(scope="function")
async def async_sample_patient(async_test_db: AsyncSession, therapist_user):
    """
    Create a sample patient for async testing.

    Args:
        async_test_db: Async test database session
        therapist_user: Therapist who owns this patient

    Returns:
        Patient object with basic information
    """
    patient = Patient(
        name="Jane Smith",
        email="jane.smith@example.com",
        phone="555-0101",
        therapist_id=therapist_user.id
    )
    async_test_db.add(patient)
    await async_test_db.commit()
    await async_test_db.refresh(patient)
    return patient


@pytest.fixture(scope="function")
def sample_session(test_db, sample_patient, therapist_user):
    """
    Create a sample therapy session for testing.

    Args:
        test_db: Test database session
        sample_patient: Patient for this session
        therapist_user: Therapist conducting the session

    Returns:
        Session object with basic session data
    """
    session = Session(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        duration_seconds=3600,
        audio_filename="test_session.mp3",
        status=SessionStatus.pending.value
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session


@pytest_asyncio.fixture(scope="function")
async def async_sample_session(async_test_db: AsyncSession, async_sample_patient, therapist_user):
    """
    Create a sample therapy session for async testing.

    Args:
        async_test_db: Async test database session
        async_sample_patient: Patient for this session
        therapist_user: Therapist conducting the session

    Returns:
        Session object with basic session data
    """
    session = Session(
        patient_id=async_sample_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        duration_seconds=3600,
        audio_filename="test_session.mp3",
        status=SessionStatus.pending.value
    )
    async_test_db.add(session)
    await async_test_db.commit()
    await async_test_db.refresh(session)
    return session


@pytest.fixture(scope="function")
def sample_session_with_transcript(test_db, sample_patient, therapist_user):
    """
    Create a sample session with transcript for testing note extraction.

    Args:
        test_db: Test database session
        sample_patient: Patient for this session
        therapist_user: Therapist conducting the session

    Returns:
        Session object with transcript data
    """
    transcript = """
    Therapist: Good morning. How have you been feeling since our last session?
    Client: I've been doing okay. I tried the breathing exercises you suggested, and they really helped when I felt anxious at work.
    Therapist: That's wonderful to hear. Can you tell me more about that situation?
    Client: Sure. There was this team meeting, and I usually get really nervous before those. But this time, I did the box breathing for a few minutes beforehand, and I felt much calmer.
    Therapist: Excellent. It sounds like you're making real progress. Were there any other challenging moments this week?
    Client: Well, I had another argument with my partner about finances. That's still a big trigger for me.
    """

    session = Session(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        duration_seconds=3600,
        audio_filename="test_session_with_transcript.mp3",
        transcript_text=transcript.strip(),
        status=SessionStatus.transcribed.value
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session


@pytest_asyncio.fixture(scope="function")
async def async_sample_session_with_transcript(async_test_db: AsyncSession, async_sample_patient, therapist_user):
    """
    Create a sample session with transcript for async testing.

    Args:
        async_test_db: Async test database session
        async_sample_patient: Patient for this session
        therapist_user: Therapist conducting the session

    Returns:
        Session object with transcript data
    """
    transcript = """
    Therapist: Good afternoon. How have things been?
    Client: Better, actually. I've been practicing mindfulness like we discussed.
    Therapist: That's great progress. Tell me more about how that's been going.
    Client: Well, I'm able to notice when I'm getting stressed and take a step back now.
    """

    session = Session(
        patient_id=async_sample_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        duration_seconds=3600,
        audio_filename="test_async_session.mp3",
        transcript_text=transcript.strip(),
        status=SessionStatus.transcribed.value
    )
    async_test_db.add(session)
    await async_test_db.commit()
    await async_test_db.refresh(session)
    return session


# ============================================================================
# Mock OpenAI Client Fixture
# ============================================================================

@pytest.fixture(scope="function")
def mock_openai():
    """
    Create a mock OpenAI client for testing without making real API calls.

    This fixture mocks the AsyncOpenAI client to return predictable responses
    for testing note extraction without consuming API credits.

    Returns:
        MagicMock configured to simulate OpenAI API responses

    Usage:
        def test_extraction(mock_openai):
            service = NoteExtractionService(api_key="fake-key")
            service.client = mock_openai
            # Test extraction logic
    """
    mock_client = MagicMock()
    mock_completion = AsyncMock()

    # Create a mock response object
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """
    {
        "key_topics": ["Anxiety management", "Work stress", "Relationship issues"],
        "topic_summary": "Client discussed progress with breathing exercises and challenges with partner communication.",
        "strategies": [
            {
                "name": "Box breathing",
                "category": "breathing",
                "status": "practiced",
                "context": "Used before team meetings to manage anxiety"
            }
        ],
        "emotional_themes": ["Anxiety", "Progress", "Frustration"],
        "triggers": [
            {
                "trigger": "Team meetings",
                "context": "Causes anticipatory anxiety",
                "severity": "moderate"
            },
            {
                "trigger": "Financial discussions with partner",
                "context": "Leads to arguments and stress",
                "severity": "moderate"
            }
        ],
        "action_items": [
            {
                "task": "Continue daily breathing exercises",
                "category": "homework",
                "details": "Practice box breathing for 5 minutes each morning"
            }
        ],
        "significant_quotes": [
            {
                "quote": "I did the box breathing for a few minutes beforehand, and I felt much calmer",
                "context": "Demonstrates successful application of coping strategy"
            }
        ],
        "session_mood": "positive",
        "mood_trajectory": "improving",
        "follow_up_topics": ["Partner communication strategies", "Workplace anxiety"],
        "unresolved_concerns": ["Financial stress management"],
        "risk_flags": [],
        "therapist_notes": "Client demonstrates good progress with anxiety management techniques. Successfully applied box breathing before stressful work situation with positive results. Continues to struggle with partner communication, particularly around finances. Will explore communication strategies in next session. Overall trajectory is positive with client showing increased self-awareness and willingness to practice skills between sessions.",
        "patient_summary": "You're making great progress with managing your anxiety! The breathing exercises are really working for you, especially before those team meetings. Keep practicing them daily - they're becoming a powerful tool in your toolkit. We'll continue working on communication strategies for those tough conversations with your partner. Remember, progress isn't always linear, but you're definitely moving in the right direction."
    }
    """

    mock_completion.create.return_value = mock_response
    mock_client.chat.completions = mock_completion

    return mock_client


@pytest.fixture(scope="function")
def mock_extraction_service(mock_openai):
    """
    Create a NoteExtractionService with mocked OpenAI client.

    This fixture provides a fully configured extraction service that uses
    the mock OpenAI client, allowing tests to verify extraction logic
    without making real API calls.

    Args:
        mock_openai: Mock OpenAI client fixture

    Returns:
        NoteExtractionService with mocked client

    Usage:
        def test_extraction_endpoint(client, mock_extraction_service):
            # Override the service dependency
            app.dependency_overrides[get_extraction_service] = lambda: mock_extraction_service
            response = client.post("/api/sessions/extract", json={...})
    """
    service = NoteExtractionService(api_key="fake-test-key")
    service.client = mock_openai
    return service


# ============================================================================
# Enhanced OpenAI Mocking Fixtures (from tests/mocks/openai_mock.py)
# ============================================================================

@pytest.fixture
def mock_openai_client():
    """
    Provide a mock OpenAI client with default sample response.

    Returns:
        MockAsyncOpenAI with realistic extraction response

    Usage:
        async def test_extraction(mock_openai_client):
            service = NoteExtractionService()
            service.client = mock_openai_client
            notes = await service.extract_notes_from_transcript(transcript)
            assert notes.session_mood == "neutral"
    """
    from tests.mocks.openai_mock import MockAsyncOpenAI
    return MockAsyncOpenAI()


@pytest.fixture
def mock_openai_with_risk_flags():
    """
    Provide a mock OpenAI client that returns extraction with risk flags.

    Returns:
        MockAsyncOpenAI with risk flags included

    Usage:
        async def test_risk_detection(mock_openai_with_risk_flags):
            service.client = mock_openai_with_risk_flags
            notes = await service.extract_notes_from_transcript(transcript)
            assert len(notes.risk_flags) > 0
    """
    from tests.mocks.openai_mock import MockAsyncOpenAI, sample_extraction_response
    return MockAsyncOpenAI(
        response_data=sample_extraction_response(include_risk_flags=True)
    )


@pytest.fixture
def mock_openai_rate_limit():
    """
    Provide a mock OpenAI client that raises RateLimitError.

    Returns:
        MockAsyncOpenAI configured to raise rate limit error

    Usage:
        async def test_rate_limit_handling(mock_openai_rate_limit):
            service.client = mock_openai_rate_limit
            with pytest.raises(ValueError, match="rate limit"):
                await service.extract_notes_from_transcript(transcript)
    """
    from tests.mocks.openai_mock import MockAsyncOpenAI, mock_rate_limit_error
    return MockAsyncOpenAI(error_to_raise=mock_rate_limit_error())


@pytest.fixture
def mock_openai_timeout():
    """
    Provide a mock OpenAI client that raises APITimeoutError.

    Returns:
        MockAsyncOpenAI configured to raise timeout error

    Usage:
        async def test_timeout_handling(mock_openai_timeout):
            service.client = mock_openai_timeout
            with pytest.raises(ValueError, match="timed out"):
                await service.extract_notes_from_transcript(transcript)
    """
    from tests.mocks.openai_mock import MockAsyncOpenAI, mock_timeout_error
    return MockAsyncOpenAI(error_to_raise=mock_timeout_error())


@pytest.fixture
def mock_openai_api_error():
    """
    Provide a mock OpenAI client that raises APIError.

    Returns:
        MockAsyncOpenAI configured to raise API error

    Usage:
        async def test_api_error_handling(mock_openai_api_error):
            service.client = mock_openai_api_error
            with pytest.raises(ValueError, match="API error"):
                await service.extract_notes_from_transcript(transcript)
    """
    from tests.mocks.openai_mock import MockAsyncOpenAI, mock_api_error
    return MockAsyncOpenAI(error_to_raise=mock_api_error())


# ============================================================================
# Fixtures for Async Router Tests (e.g., patients router)
# ============================================================================

@pytest.fixture(scope="function")
def async_db_client(test_db):
    """
    Sync TestClient for testing async endpoints with SQLite test database.

    This fixture creates a sync TestClient that wraps async endpoints,
    but uses a shared SQLite database that can be accessed both synchronously
    (for test setup) and asynchronously (by the endpoint).

    The trick: We override get_db with an async generator that creates a new
    async session from the same database file used by test_db.

    IMPORTANT: Call test_db.commit() BEFORE making HTTP requests to ensure
    test data is visible to the async session.

    Args:
        test_db: Sync test database session (for test setup/assertions)

    Yields:
        TestClient for making API requests to async endpoints

    Usage:
        def test_patient_endpoint(async_db_client, test_db, therapist_user):
            # therapist_user is auto-committed by its fixture
            response = async_db_client.post("/api/patients/", json={...})
            assert response.status_code == 200
    """
    # Ensure any pending data from test_db is committed to the database file
    # so async sessions can see it
    test_db.commit()

    async def override_get_async_db():
        """Provide async session connected to the test database"""
        async with AsyncTestingSessionLocal() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Override async database dependency
    app.dependency_overrides[get_db] = override_get_async_db
    app.dependency_overrides[get_sync_db] = lambda: test_db

    # Create sync test client (it will internally handle async endpoints)
    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()
