"""
Pytest fixtures for authentication integration tests.

This module provides test fixtures for:
- Test database setup/teardown (sync and async)
- FastAPI test client (sync and async)
- Test user creation (therapists, patients, admins)
- Sample data (patients, sessions)
- Mock OpenAI client
"""
import os
import pytest
import pytest_asyncio


@pytest.fixture(scope="session", autouse=True)
def set_test_secret_key():
    """Set consistent SECRET_KEY for all test JWT operations"""
    os.environ["SECRET_KEY"] = "test-secret-key-must-be-32-characters-long-for-hs256-algorithm-security"
    yield
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
import app.models  # Import models package to register all tables with Base.metadata
from app.main import app
from app.models.db_models import User, Patient, Session, TherapistPatient
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
    echo=False,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Enable WAL mode for sync SQLite connections
@event.listens_for(engine, "connect")
def set_sqlite_pragma_sync(dbapi_conn, connection_record):
    """Enable WAL mode for SQLite to support concurrent reads/writes"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

# Async engine for async tests
async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
    echo=False,
    future=True,
)
AsyncTestingSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Enable WAL mode for async SQLite connections to allow concurrent reads/writes
@event.listens_for(async_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable WAL mode for SQLite to support async writes"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()


# Convert JSONB to JSON for SQLite compatibility
@event.listens_for(Base.metadata, "before_create")
def _set_json_columns(target, connection, **kw):
    """
    Convert JSONB columns to JSON for SQLite.
    SQLite doesn't support JSONB (PostgreSQL-specific type),
    so we replace it with JSON for tests.
    """
    # Only convert if using SQLite
    if connection.dialect.name == "sqlite":
        for table in Base.metadata.tables.values():
            for col in table.columns:
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

    # Create session and commit fixture data
    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Commit fixture data
        except Exception:
            await session.rollback()  # Only rollback on error
            raise

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
        - password: TestPass123!@
        - role: therapist
    """
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("TestPass123!@"),
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
# Analytics Test Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def sample_sessions_with_analytics_data(test_db, therapist_user):
    """
    Create 10 therapy sessions with varied analytics data for testing.

    This fixture provides sessions distributed across the last 60 days with:
    - Mixed dates (distributed across weeks/months)
    - Varied session durations (30-90 minutes)
    - Complete extracted_notes JSONB with key_topics, action_items, session_mood
    - Different statuses (processed, failed, pending)
    - Multiple patients (2-3 different patients)

    Args:
        test_db: Test database session
        therapist_user: Therapist who owns these sessions

    Returns:
        List of 10 Session objects with analytics-ready data
    """
    # Create 3 patients
    patients = []
    for i in range(3):
        patient = Patient(
            name=f"Analytics Patient {i+1}",
            email=f"analytics.patient{i+1}@example.com",
            phone=f"555-010{i}",
            therapist_id=therapist_user.id
        )
        test_db.add(patient)
        patients.append(patient)
    test_db.commit()

    # Refresh patients
    for patient in patients:
        test_db.refresh(patient)

    # Date distribution across last 60 days
    now = datetime.utcnow()
    dates = [
        now - timedelta(days=60),  # 2 months ago
        now - timedelta(days=52),
        now - timedelta(days=45),
        now - timedelta(days=30),  # 1 month ago
        now - timedelta(days=21),
        now - timedelta(days=14),  # 2 weeks ago
        now - timedelta(days=10),
        now - timedelta(days=7),   # 1 week ago
        now - timedelta(days=3),
        now - timedelta(days=1),   # Yesterday
    ]

    # Session configurations
    session_configs = [
        {
            "duration": 1800,  # 30 minutes
            "status": SessionStatus.processed.value,
            "mood": "anxious",
            "topics": ["anxiety", "work stress"],
            "trajectory": "stable",
        },
        {
            "duration": 3600,  # 60 minutes
            "status": SessionStatus.processed.value,
            "mood": "neutral",
            "topics": ["coping strategies", "relationships"],
            "trajectory": "improving",
        },
        {
            "duration": 5400,  # 90 minutes
            "status": SessionStatus.processed.value,
            "mood": "positive",
            "topics": ["progress", "goals"],
            "trajectory": "improving",
        },
        {
            "duration": 2700,  # 45 minutes
            "status": SessionStatus.failed.value,
            "mood": "neutral",
            "topics": ["family issues"],
            "trajectory": "stable",
        },
        {
            "duration": 3600,  # 60 minutes
            "status": SessionStatus.processed.value,
            "mood": "neutral",
            "topics": ["stress management", "sleep"],
            "trajectory": "stable",
        },
        {
            "duration": 4500,  # 75 minutes
            "status": SessionStatus.pending.value,
            "mood": "anxious",
            "topics": ["anxiety", "panic attacks"],
            "trajectory": "declining",
        },
        {
            "duration": 3600,  # 60 minutes
            "status": SessionStatus.processed.value,
            "mood": "hopeful",
            "topics": ["mindfulness", "meditation"],
            "trajectory": "improving",
        },
        {
            "duration": 3000,  # 50 minutes
            "status": SessionStatus.processed.value,
            "mood": "positive",
            "topics": ["achievements", "self-esteem"],
            "trajectory": "improving",
        },
        {
            "duration": 3600,  # 60 minutes
            "status": SessionStatus.processed.value,
            "mood": "neutral",
            "topics": ["work-life balance", "boundaries"],
            "trajectory": "stable",
        },
        {
            "duration": 4200,  # 70 minutes
            "status": SessionStatus.processed.value,
            "mood": "calm",
            "topics": ["reflection", "gratitude"],
            "trajectory": "improving",
        },
    ]

    sessions = []
    for i, (date, config) in enumerate(zip(dates, session_configs)):
        # Rotate through patients
        patient = patients[i % len(patients)]

        # Build extracted_notes
        extracted_notes = {
            "key_topics": config["topics"],
            "session_mood": config["mood"],
            "mood_trajectory": config["trajectory"],
            "action_items": [
                {
                    "task": f"Practice breathing exercises",
                    "status": "completed" if i % 3 == 0 else "in_progress",
                    "category": "homework"
                },
                {
                    "task": f"Journal daily about emotions",
                    "status": "in_progress" if i % 2 == 0 else "completed",
                    "category": "reflection"
                }
            ],
            "emotional_themes": config["topics"][:2] if len(config["topics"]) >= 2 else config["topics"],
        }

        session = Session(
            patient_id=patient.id,
            therapist_id=therapist_user.id,
            session_date=date,
            duration_seconds=config["duration"],
            audio_filename=f"analytics_session_{i+1}.mp3",
            status=config["status"],
            extracted_notes=extracted_notes if config["status"] == SessionStatus.processed.value else None
        )
        test_db.add(session)
        sessions.append(session)

    test_db.commit()

    # Refresh all sessions
    for session in sessions:
        test_db.refresh(session)

    return sessions


@pytest.fixture(scope="function")
def completed_sessions(test_db, therapist_user):
    """
    Create 5 completed sessions with status='processed' for testing.

    All sessions:
    - Have status='processed'
    - Include complete extracted_notes
    - Are from the last 14 days
    - Have analytics-ready data

    Args:
        test_db: Test database session
        therapist_user: Therapist who owns these sessions

    Returns:
        List of 5 Session objects with complete data
    """
    # Create 2 patients
    patients = []
    for i in range(2):
        patient = Patient(
            name=f"Completed Session Patient {i+1}",
            email=f"completed.patient{i+1}@example.com",
            phone=f"555-020{i}",
            therapist_id=therapist_user.id
        )
        test_db.add(patient)
        patients.append(patient)
    test_db.commit()

    # Refresh patients
    for patient in patients:
        test_db.refresh(patient)

    # Recent dates (last 14 days)
    now = datetime.utcnow()
    dates = [
        now - timedelta(days=14),
        now - timedelta(days=10),
        now - timedelta(days=7),
        now - timedelta(days=3),
        now - timedelta(days=1),
    ]

    sessions = []
    topics_list = [
        ["anxiety", "work stress", "coping strategies"],
        ["relationships", "communication", "boundaries"],
        ["depression", "medication", "sleep"],
        ["trauma", "healing", "resilience"],
        ["goals", "progress", "self-compassion"],
    ]

    moods = ["anxious", "neutral", "hopeful", "calm", "positive"]

    for i, (date, topics, mood) in enumerate(zip(dates, topics_list, moods)):
        patient = patients[i % len(patients)]

        extracted_notes = {
            "key_topics": topics,
            "session_mood": mood,
            "mood_trajectory": "improving" if i >= 3 else "stable",
            "action_items": [
                {
                    "task": "Practice mindfulness meditation",
                    "status": "completed",
                    "category": "homework"
                },
                {
                    "task": "Complete mood tracking log",
                    "status": "in_progress",
                    "category": "reflection"
                }
            ],
            "emotional_themes": [topics[0], "hope"] if i >= 2 else [topics[0], "anxiety"],
        }

        session = Session(
            patient_id=patient.id,
            therapist_id=therapist_user.id,
            session_date=date,
            duration_seconds=3600,  # 60 minutes
            audio_filename=f"completed_session_{i+1}.mp3",
            status=SessionStatus.processed.value,
            extracted_notes=extracted_notes
        )
        test_db.add(session)
        sessions.append(session)

    test_db.commit()

    # Refresh all sessions
    for session in sessions:
        test_db.refresh(session)

    return sessions


@pytest.fixture(scope="function")
def therapist_with_patients_and_sessions(test_db):
    """
    Create a therapist with 3 patients and 8 sessions for comprehensive testing.

    Creates:
    - 1 therapist (User with role=therapist)
    - 3 patient User objects (with role=patient) for authorization/analytics
    - 3 TherapistPatient junction records (linking therapist to patient users)
    - 3 Patient records (legacy table for session compatibility)
    - 8 sessions total: Patient A (3), Patient B (3), Patient C (2)
    - All sessions have analytics-ready data

    Args:
        test_db: Test database session

    Returns:
        Dict with:
        - therapist: User object (therapist)
        - patients: List of 3 Patient objects (legacy table)
        - patient_users: List of 3 User objects with role=patient
        - sessions: List of 8 Session objects
    """
    # Create therapist
    therapist = User(
        email="analytics.therapist@test.com",
        hashed_password=get_password_hash("testpass123"),
        first_name="Analytics",
        last_name="Therapist",
        full_name="Analytics Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    test_db.add(therapist)
    test_db.commit()
    test_db.refresh(therapist)

    # Create 3 patient User objects (for therapist_patients junction table)
    patient_users = []
    for i in range(3):
        patient_user = User(
            email=f"patient{chr(97+i)}@example.com",
            hashed_password=get_password_hash("testpass123"),
            first_name=f"Patient{chr(65+i)}",
            last_name="TestUser",
            full_name=f"Patient {chr(65+i)} TestUser",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        test_db.add(patient_user)
        patient_users.append(patient_user)
    test_db.commit()

    # Refresh patient users
    for patient_user in patient_users:
        test_db.refresh(patient_user)

    # Create TherapistPatient junction records (for authorization/analytics)
    for patient_user in patient_users:
        therapist_patient = TherapistPatient(
            therapist_id=therapist.id,
            patient_id=patient_user.id,
            relationship_type="primary",
            is_active=True
        )
        test_db.add(therapist_patient)
    test_db.commit()

    # Create 3 Patient records (for session compatibility - sessions reference patients table)
    patients = []
    for i in range(3):
        patient = Patient(
            name=f"Patient {chr(65+i)}",  # Patient A, B, C
            email=f"patient{chr(97+i)}@example.com",
            phone=f"555-030{i}",
            therapist_id=therapist.id
        )
        test_db.add(patient)
        patients.append(patient)
    test_db.commit()

    # Refresh patients
    for patient in patients:
        test_db.refresh(patient)

    # Create 2-3 sessions per patient
    sessions = []
    now = datetime.utcnow()

    session_data = [
        # Patient A - 3 sessions
        {"patient_idx": 0, "days_ago": 21, "topics": ["anxiety", "work"], "mood": "anxious", "trajectory": "stable"},
        {"patient_idx": 0, "days_ago": 14, "topics": ["coping", "stress"], "mood": "neutral", "trajectory": "improving"},
        {"patient_idx": 0, "days_ago": 7, "topics": ["progress", "goals"], "mood": "hopeful", "trajectory": "improving"},
        # Patient B - 3 sessions
        {"patient_idx": 1, "days_ago": 20, "topics": ["depression", "sleep"], "mood": "low", "trajectory": "stable"},
        {"patient_idx": 1, "days_ago": 13, "topics": ["medication", "energy"], "mood": "neutral", "trajectory": "improving"},
        {"patient_idx": 1, "days_ago": 6, "topics": ["activities", "motivation"], "mood": "positive", "trajectory": "improving"},
        # Patient C - 2 sessions
        {"patient_idx": 2, "days_ago": 15, "topics": ["relationships", "boundaries"], "mood": "neutral", "trajectory": "stable"},
        {"patient_idx": 2, "days_ago": 8, "topics": ["communication", "assertiveness"], "mood": "hopeful", "trajectory": "improving"},
    ]

    for i, data in enumerate(session_data):
        patient = patients[data["patient_idx"]]
        session_date = now - timedelta(days=data["days_ago"])

        extracted_notes = {
            "key_topics": data["topics"],
            "session_mood": data["mood"],
            "mood_trajectory": data["trajectory"],
            "action_items": [
                {
                    "task": f"Practice {data['topics'][0]} management",
                    "status": "completed" if i % 2 == 0 else "in_progress",
                    "category": "homework"
                }
            ],
            "emotional_themes": data["topics"],
        }

        session = Session(
            patient_id=patient.id,
            therapist_id=therapist.id,
            session_date=session_date,
            duration_seconds=3600,
            audio_filename=f"session_{i+1}.mp3",
            status=SessionStatus.processed.value,
            extracted_notes=extracted_notes
        )
        test_db.add(session)
        sessions.append(session)

    test_db.commit()

    # Refresh all sessions
    for session in sessions:
        test_db.refresh(session)

    return {
        "therapist": therapist,
        "patients": patients,
        "patient_users": patient_users,  # User objects with role=patient (for analytics/authorization)
        "sessions": sessions
    }


@pytest.fixture(scope="function")
def mock_analytics_date_range():
    """
    Provide consistent date ranges for analytics testing.

    Returns:
        Dict with:
        - start_date: datetime (30 days ago)
        - end_date: datetime (now)
        - middle_date: datetime (15 days ago)

    Usage:
        def test_analytics(mock_analytics_date_range):
            start = mock_analytics_date_range["start_date"]
            end = mock_analytics_date_range["end_date"]
            # Use for consistent date filtering
    """
    now = datetime.utcnow()
    return {
        "start_date": now - timedelta(days=30),
        "end_date": now,
        "middle_date": now - timedelta(days=15),
    }


# ============================================================================
# Goal Tracking Test Fixtures (Feature 6)
# ============================================================================

@pytest.fixture(scope="function")
def sample_goal(test_db, sample_patient, therapist_user, sample_session):
    """
    Create a basic TreatmentGoal for testing.

    Args:
        test_db: Test database session
        sample_patient: Patient who owns this goal
        therapist_user: Therapist who created this goal
        sample_session: Session where goal was assigned

    Returns:
        TreatmentGoal object with basic goal data
    """
    from app.models.goal_models import TreatmentGoal
    from datetime import date

    goal = TreatmentGoal(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_id=sample_session.id,
        description="Practice deep breathing exercises daily",
        category="anxiety_management",
        status="assigned",
        baseline_value=2.0,
        target_value=7.0,
        target_date=date.today() + timedelta(days=30),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)
    return goal


@pytest.fixture(scope="function")
def sample_goal_with_tracking(test_db, sample_patient, therapist_user, sample_session):
    """
    Create a TreatmentGoal with associated GoalTrackingConfig.

    Args:
        test_db: Test database session
        sample_patient: Patient who owns this goal
        therapist_user: Therapist who created this goal
        sample_session: Session where goal was assigned

    Returns:
        Tuple of (TreatmentGoal, GoalTrackingConfig)
    """
    from app.models.goal_models import TreatmentGoal
    from app.models.tracking_models import GoalTrackingConfig
    from datetime import date

    # Create goal
    goal = TreatmentGoal(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_id=sample_session.id,
        description="Rate anxiety level on scale of 1-10",
        category="anxiety_tracking",
        status="in_progress",
        baseline_value=8.0,
        target_value=4.0,
        target_date=date.today() + timedelta(days=60),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)

    # Create tracking config
    tracking_config = GoalTrackingConfig(
        goal_id=goal.id,
        tracking_method="scale",
        tracking_frequency="daily",
        scale_min=1,
        scale_max=10,
        scale_labels={"1": "No anxiety", "5": "Moderate", "10": "Severe"},
        target_direction="decrease",
        reminder_enabled=True,
        created_at=datetime.utcnow()
    )
    test_db.add(tracking_config)
    test_db.commit()
    test_db.refresh(tracking_config)

    return (goal, tracking_config)


@pytest.fixture(scope="function")
def sample_progress_entries(test_db, sample_goal_with_tracking):
    """
    Create a list of ProgressEntry objects for testing.

    Args:
        test_db: Test database session
        sample_goal_with_tracking: Tuple of (goal, tracking_config)

    Returns:
        List of 5 ProgressEntry objects spanning 5 days
    """
    from app.models.tracking_models import ProgressEntry
    from datetime import date, time

    goal, tracking_config = sample_goal_with_tracking

    entries = []
    base_date = date.today() - timedelta(days=5)
    values = [8.0, 7.5, 7.0, 6.5, 6.0]  # Improving trend

    for i, value in enumerate(values):
        entry = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=tracking_config.id,
            entry_date=base_date + timedelta(days=i),
            entry_time=time(hour=20, minute=0),
            value=value,
            value_label=f"Anxiety level: {value}",
            notes=f"Daily check-in day {i+1}",
            context="self_report",
            recorded_at=datetime.utcnow()
        )
        test_db.add(entry)
        entries.append(entry)

    test_db.commit()

    # Refresh all entries
    for entry in entries:
        test_db.refresh(entry)

    return entries


@pytest.fixture(scope="function")
def sample_assessment(test_db, sample_patient, therapist_user, sample_goal):
    """
    Create an AssessmentScore fixture for testing.

    Args:
        test_db: Test database session
        sample_patient: Patient who took the assessment
        therapist_user: Therapist who administered the assessment
        sample_goal: Related treatment goal

    Returns:
        AssessmentScore object (e.g., GAD-7 assessment)
    """
    from app.models.tracking_models import AssessmentScore
    from datetime import date

    assessment = AssessmentScore(
        patient_id=sample_patient.id,
        goal_id=sample_goal.id,
        administered_by=therapist_user.id,
        assessment_type="GAD-7",
        score=14,
        severity="moderate",
        subscores={
            "feeling_nervous": 2,
            "not_stop_worrying": 2,
            "worrying_too_much": 2,
            "trouble_relaxing": 2,
            "restless": 2,
            "easily_annoyed": 2,
            "feeling_afraid": 2
        },
        administered_date=date.today() - timedelta(days=7),
        notes="Baseline assessment - moderate anxiety symptoms present",
        created_at=datetime.utcnow()
    )
    test_db.add(assessment)
    test_db.commit()
    test_db.refresh(assessment)
    return assessment


@pytest.fixture(scope="function")
def sample_milestone(test_db, sample_goal):
    """
    Create a ProgressMilestone fixture for testing.

    Args:
        test_db: Test database session
        sample_goal: Goal associated with this milestone

    Returns:
        ProgressMilestone object
    """
    from app.models.tracking_models import ProgressMilestone

    milestone = ProgressMilestone(
        goal_id=sample_goal.id,
        milestone_type="percentage",
        title="50% Progress Achieved",
        description="Halfway to target value",
        target_value=4.5,  # Midpoint between baseline (2.0) and target (7.0)
        achieved_at=None,  # Not yet achieved
        created_at=datetime.utcnow()
    )
    test_db.add(milestone)
    test_db.commit()
    test_db.refresh(milestone)
    return milestone


@pytest.fixture(scope="function")
def goal_with_progress_history(test_db, sample_patient, therapist_user, sample_session):
    """
    Create a goal with 10+ progress entries for testing trend analysis.

    This fixture provides a complete goal tracking history suitable for:
    - Trend calculation tests
    - Progress statistics tests
    - Dashboard visualization tests

    Args:
        test_db: Test database session
        sample_patient: Patient who owns this goal
        therapist_user: Therapist who created this goal
        sample_session: Session where goal was assigned

    Returns:
        Tuple of (TreatmentGoal, GoalTrackingConfig, List[ProgressEntry])
    """
    from app.models.goal_models import TreatmentGoal
    from app.models.tracking_models import GoalTrackingConfig, ProgressEntry
    from datetime import date, time

    # Create goal
    goal = TreatmentGoal(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_id=sample_session.id,
        description="Exercise for 30 minutes, 5 times per week",
        category="physical_activity",
        status="in_progress",
        baseline_value=1.0,  # 1 time per week
        target_value=5.0,    # 5 times per week
        target_date=date.today() + timedelta(days=90),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(goal)
    test_db.commit()
    test_db.refresh(goal)

    # Create tracking config
    tracking_config = GoalTrackingConfig(
        goal_id=goal.id,
        tracking_method="frequency",
        tracking_frequency="weekly",
        frequency_unit="times_per_week",
        target_direction="increase",
        reminder_enabled=True,
        created_at=datetime.utcnow()
    )
    test_db.add(tracking_config)
    test_db.commit()
    test_db.refresh(tracking_config)

    # Create 12 weeks of progress entries showing improvement
    entries = []
    base_date = date.today() - timedelta(weeks=12)

    # Realistic improvement pattern: slow start, then steady progress
    weekly_values = [1.0, 1.5, 2.0, 2.0, 2.5, 3.0, 3.5, 3.5, 4.0, 4.5, 4.5, 5.0]

    for week_num, value in enumerate(weekly_values):
        entry = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=tracking_config.id,
            entry_date=base_date + timedelta(weeks=week_num),
            entry_time=time(hour=9, minute=0),
            value=value,
            value_label=f"{int(value)} times this week",
            notes=f"Week {week_num + 1} summary",
            context="self_report",
            recorded_at=datetime.utcnow()
        )
        test_db.add(entry)
        entries.append(entry)

    test_db.commit()

    # Refresh all entries
    for entry in entries:
        test_db.refresh(entry)

    return (goal, tracking_config, entries)


@pytest.fixture(scope="function")
def multiple_goals_for_patient(test_db, sample_patient, therapist_user, sample_session):
    """
    Create multiple treatment goals for comprehensive testing.

    Creates 3 goals with different:
    - Categories (anxiety, depression, behavioral)
    - Statuses (assigned, in_progress, completed)
    - Target dates

    Args:
        test_db: Test database session
        sample_patient: Patient who owns these goals
        therapist_user: Therapist who created these goals
        sample_session: Session where goals were assigned

    Returns:
        List of 3 TreatmentGoal objects
    """
    from app.models.goal_models import TreatmentGoal
    from datetime import date

    goals = []

    # Goal 1: Active anxiety goal
    goal1 = TreatmentGoal(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_id=sample_session.id,
        description="Reduce anxiety symptoms to mild level",
        category="anxiety_management",
        status="in_progress",
        baseline_value=15.0,
        target_value=7.0,
        target_date=date.today() + timedelta(days=60),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(goal1)
    goals.append(goal1)

    # Goal 2: Completed behavioral goal
    goal2 = TreatmentGoal(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_id=sample_session.id,
        description="Establish consistent sleep schedule",
        category="behavioral",
        status="completed",
        baseline_value=5.0,  # 5 hours average
        target_value=8.0,    # 8 hours average
        target_date=date.today() - timedelta(days=10),
        created_at=datetime.utcnow() - timedelta(days=60),
        updated_at=datetime.utcnow() - timedelta(days=10),
        completed_at=datetime.utcnow() - timedelta(days=10)
    )
    test_db.add(goal2)
    goals.append(goal2)

    # Goal 3: Newly assigned depression goal
    goal3 = TreatmentGoal(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_id=sample_session.id,
        description="Engage in at least one social activity per week",
        category="depression_management",
        status="assigned",
        baseline_value=0.0,
        target_value=1.0,
        target_date=date.today() + timedelta(days=30),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    test_db.add(goal3)
    goals.append(goal3)

    test_db.commit()

    # Refresh all goals
    for goal in goals:
        test_db.refresh(goal)

    return goals


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
