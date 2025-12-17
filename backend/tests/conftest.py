"""
Pytest fixtures for authentication integration tests.

This module provides test fixtures for:
- Test database setup/teardown
- FastAPI test client
- Test user creation
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, JSON
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base
from app.auth.dependencies import get_db
from app.main import app
from app.models.db_models import User
from app.auth.models import AuthSession
from app.auth.utils import get_password_hash
from app.models.schemas import UserRole

# Use SQLite in-memory database for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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
    Create a fresh database for each test.

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


@pytest.fixture(scope="function")
def client(test_db):
    """
    FastAPI test client with overridden database dependency.

    This fixture:
    1. Overrides the get_db dependency to use test database
    2. Provides a TestClient for making HTTP requests
    3. Cleans up dependency overrides after test

    Args:
        test_db: Test database session fixture

    Yields:
        TestClient for making API requests
    """
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db

    # Create test client
    with TestClient(app) as test_client:
        yield test_client

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
        full_name="Test User",
        role=UserRole.therapist,
        is_active=True
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
        full_name="Test Patient",
        role=UserRole.patient,
        is_active=True
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
        full_name="Inactive User",
        role=UserRole.therapist,
        is_active=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user
