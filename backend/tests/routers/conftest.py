"""
Pytest fixtures for router integration tests with async database support.
"""
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, JSON
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from uuid import uuid4

# CRITICAL: Import app.models BEFORE Base to register all model tables with Base.metadata
import app.models  # This triggers all model registrations
from app.database import Base, get_db
from app.main import app
from app.models.db_models import User, Patient, Session, TherapistPatient, TherapySession, TimelineEvent, NoteTemplate, SessionNote, TemplateUsage
from app.auth.utils import get_password_hash
from app.models.schemas import UserRole

# Use SQLite shared cache for tests (allows both sync and async access)
import os
import tempfile

# Create a database file in current working directory (more reliable than tempdir)
_test_db_dir = os.path.join(os.getcwd(), ".test_tmp")
os.makedirs(_test_db_dir, exist_ok=True)
_test_db_path = os.path.join(_test_db_dir, "test_routers_sessions.db")

SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{_test_db_path}"
SQLALCHEMY_SYNC_DATABASE_URL = f"sqlite:///{_test_db_path}"

# Create async engine for tests
test_async_engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    poolclass=None  # Disable pooling for tests
)

# Create async session factory
TestingAsyncSessionLocal = async_sessionmaker(
    test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create sync engine for synchronous operations (shares same file)
test_sync_engine = create_engine(
    SQLALCHEMY_SYNC_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=None  # Disable pooling for tests
)
TestingSyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_sync_engine
)


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


@pytest_asyncio.fixture(scope="function", autouse=True)
async def setup_database():
    """
    Setup and teardown database for each test.
    Creates tables before test and drops them after.
    Uses local .test_tmp directory to avoid permission issues.
    """
    # Create all tables using sync engine
    Base.metadata.create_all(bind=test_sync_engine)
    yield
    # Drop all tables
    Base.metadata.drop_all(bind=test_sync_engine)


@pytest_asyncio.fixture(scope="function")
async def test_async_db():
    """
    Provide an async database session for each test.

    Yields:
        AsyncSession for test database
    """
    # Create session
    async with TestingAsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
def client(test_async_db):
    """
    FastAPI test client with overridden async database dependency.

    This fixture:
    1. Overrides the get_db dependency to use test database
    2. Provides a TestClient for making HTTP requests
    3. Cleans up dependency overrides after test

    Args:
        test_async_db: Async test database session fixture

    Yields:
        TestClient for making API requests
    """
    async def override_get_db():
        yield test_async_db

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def therapist_user(test_async_db):
    """
    Create a test therapist user in the database (synchronous).

    Returns:
        User object with therapist role
    """
    # Use sync session for fixture setup
    db = TestingSyncSessionLocal()
    try:
        user = User(
            id=uuid4(),
            email="therapist@test.com",
            hashed_password=get_password_hash("testpass123"),
            first_name="Test",
            last_name="Therapist",
            full_name="Test Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_patient(therapist_user):
    """
    Create a test patient in the database (synchronous).

    Returns:
        Patient object
    """
    # Use sync session for fixture setup
    db = TestingSyncSessionLocal()
    try:
        patient = Patient(
            id=uuid4(),
            name="Test Patient",
            email="patient@test.com",
            phone="+1234567890",
            therapist_id=therapist_user.id
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        return patient
    finally:
        db.close()


@pytest.fixture(scope="function")
def test_session(test_patient, therapist_user):
    """
    Create a test session in the database (synchronous).

    Returns:
        Session object
    """
    from datetime import datetime

    # Use sync session for fixture setup
    db = TestingSyncSessionLocal()
    try:
        session = Session(
            id=uuid4(),
            patient_id=test_patient.id,
            therapist_id=therapist_user.id,
            session_date=datetime.utcnow(),
            status="pending",
            transcript_text="This is a sample therapy session transcript. The patient discussed anxiety and coping strategies."
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    finally:
        db.close()


@pytest.fixture(scope="function")
def patient_user(test_async_db):
    """
    Create a test patient user in the database (synchronous).

    Returns:
        User object with patient role
    """
    # Use sync session for fixture setup
    db = TestingSyncSessionLocal()
    try:
        user = User(
            id=uuid4(),
            email="patient@test.com",
            hashed_password=get_password_hash("patientpass123"),
            first_name="Test",
            last_name="Patient User",
            full_name="Test Patient User",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


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
def test_db():
    """
    Provide a sync database session for tests that need to create test data.

    Returns:
        Sync database session
    """
    db = TestingSyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def async_db_client(test_db):
    """
    Sync TestClient for testing async endpoints with SQLite test database.

    This fixture creates a sync TestClient that wraps async endpoints,
    but uses a shared SQLite database that can be accessed both synchronously
    (for test setup) and asynchronously (by the endpoint).

    This overrides the root conftest's async_db_client which uses PostgreSQL.

    Args:
        test_db: Sync test database session (for test setup/assertions)

    Yields:
        TestClient for making API requests to async endpoints
    """
    async def override_get_db():
        async with TestingAsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()
