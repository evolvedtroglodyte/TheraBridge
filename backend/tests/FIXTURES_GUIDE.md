# Database Pytest Fixtures Guide

Complete guide to using the test infrastructure fixtures in `conftest.py`.

## Overview

The test infrastructure provides:
- **Sync and async database fixtures** with automatic cleanup
- **Test clients** for making HTTP requests (sync and async)
- **Sample data fixtures** (users, patients, sessions)
- **Mock OpenAI client** for testing without API costs
- **Full test isolation** - no cross-test contamination

## Installation

Ensure you have the required dependencies:

```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

Required packages for testing:
- `pytest>=7.4.4`
- `pytest-asyncio>=0.23.3`
- `httpx>=0.26.0` (async HTTP client)
- `aiosqlite>=0.19.0` (async SQLite driver)

## Core Database Fixtures

### Synchronous Database Session

```python
def test_create_user(test_db):
    """Test with synchronous database session."""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        role=UserRole.therapist,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)

    assert user.id is not None
```

**Features:**
- Fresh database for each test
- Automatic table creation/cleanup
- Uses SQLite in-memory for speed
- Full transaction support

### Asynchronous Database Session

```python
import pytest
from sqlalchemy import select

@pytest.mark.asyncio
async def test_create_user_async(async_test_db):
    """Test with async database session."""
    user = User(
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        role=UserRole.therapist,
        is_active=True
    )
    async_test_db.add(user)
    await async_test_db.commit()
    await async_test_db.refresh(user)

    # Query with SQLAlchemy 2.0 style
    result = await async_test_db.execute(select(User))
    users = result.scalars().all()

    assert len(users) == 1
```

**Features:**
- Async/await support
- Transaction rollback for isolation
- Compatible with AsyncSession
- Uses aiosqlite driver

## HTTP Client Fixtures

### Synchronous Test Client

```python
def test_endpoint(client):
    """Test with synchronous HTTP client."""
    response = client.get("/api/sessions")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

**Features:**
- FastAPI TestClient
- Database dependency automatically overridden
- Synchronous request/response
- Fast for simple tests

### Asynchronous Test Client

```python
import pytest

@pytest.mark.asyncio
async def test_endpoint_async(async_client):
    """Test with async HTTP client."""
    response = await async_client.get("/api/sessions")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

**Features:**
- Uses httpx.AsyncClient
- Supports async endpoints
- Database dependency overridden
- Ideal for testing async operations

## User Fixtures

### Therapist User

```python
def test_therapist_access(client, therapist_user, therapist_auth_headers):
    """Test therapist can access their data."""
    response = client.get(
        f"/api/patients",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
```

**Available user fixtures:**
- `therapist_user` - Active therapist (email: therapist@test.com)
- `patient_user` - Active patient (email: patient@test.com)
- `admin_user` - Active admin (email: admin@test.com)
- `inactive_user` - Inactive user
- `test_user` - Generic test user

### Authentication Headers

```python
def test_protected_endpoint(client, therapist_auth_headers):
    """Test endpoint requiring authentication."""
    response = client.get(
        "/api/sessions",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
```

**Available auth header fixtures:**
- `therapist_auth_headers` - {"Authorization": "Bearer <token>"}
- `patient_auth_headers`
- `admin_auth_headers`

## Sample Data Fixtures

### Patient Fixtures

```python
def test_patient_data(sample_patient, therapist_user):
    """Test with sample patient."""
    assert sample_patient.name == "John Doe"
    assert sample_patient.therapist_id == therapist_user.id
    assert sample_patient.email == "john.doe@example.com"
```

**Available:**
- `sample_patient` (sync) - Patient owned by therapist_user
- `async_sample_patient` (async) - Async version

### Session Fixtures

```python
def test_session(sample_session, sample_patient):
    """Test with basic session."""
    assert sample_session.patient_id == sample_patient.id
    assert sample_session.status == SessionStatus.pending.value
    assert sample_session.duration_seconds == 3600
```

**Available:**
- `sample_session` (sync) - Basic session
- `sample_session_with_transcript` (sync) - Session with transcript text
- `async_sample_session` (async) - Async basic session
- `async_sample_session_with_transcript` (async) - Async with transcript

### Using Session with Transcript

```python
def test_extraction(sample_session_with_transcript):
    """Test note extraction with transcript."""
    session = sample_session_with_transcript

    assert session.transcript_text is not None
    assert len(session.transcript_text) > 0
    assert "breathing exercises" in session.transcript_text
```

## Mock OpenAI Client

### Basic Mock Usage

```python
def test_extraction_service(mock_openai):
    """Test extraction service with mock OpenAI."""
    service = NoteExtractionService(api_key="fake-key")
    service.client = mock_openai

    # Make extraction call (won't hit real API)
    notes = await service.extract_notes_from_transcript(
        transcript="Therapist: Hello. Client: Hi."
    )

    assert notes.key_topics == ["Anxiety management", "Work stress", "Relationship issues"]
    assert notes.session_mood == MoodLevel.positive
```

### Mock Extraction Service

```python
def test_extraction_endpoint(client, mock_extraction_service):
    """Test endpoint with mocked extraction service."""
    from app.services.note_extraction import get_extraction_service

    # Override dependency
    app.dependency_overrides[get_extraction_service] = lambda: mock_extraction_service

    response = client.post(
        "/api/sessions/extract",
        json={
            "transcript": "Therapist: How are you? Client: Good."
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "extracted_notes" in data
```

**Features:**
- No API costs
- Predictable responses
- Fast test execution
- Pre-configured realistic output

## Complete Test Examples

### Sync Test with Full Stack

```python
def test_create_and_fetch_session(
    client,
    therapist_auth_headers,
    sample_patient,
    therapist_user
):
    """Complete test using multiple fixtures."""
    # Create session
    response = client.post(
        "/api/sessions",
        headers=therapist_auth_headers,
        json={
            "patient_id": str(sample_patient.id),
            "session_date": "2024-12-17T10:00:00"
        }
    )

    assert response.status_code == 201
    session_id = response.json()["id"]

    # Fetch session
    response = client.get(
        f"/api/sessions/{session_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == 200
    session = response.json()
    assert session["patient_id"] == str(sample_patient.id)
```

### Async Test with Full Stack

```python
import pytest

@pytest.mark.asyncio
async def test_async_session_creation(
    async_client,
    therapist_auth_headers,
    async_sample_patient,
    therapist_user
):
    """Async test using async fixtures."""
    response = await async_client.post(
        "/api/sessions",
        headers=therapist_auth_headers,
        json={
            "patient_id": str(async_sample_patient.id),
            "session_date": "2024-12-17T10:00:00"
        }
    )

    assert response.status_code == 201
```

### Testing Note Extraction

```python
import pytest

@pytest.mark.asyncio
async def test_note_extraction_with_mock(
    mock_extraction_service,
    sample_session_with_transcript
):
    """Test note extraction without hitting OpenAI API."""
    notes = await mock_extraction_service.extract_notes_from_transcript(
        transcript=sample_session_with_transcript.transcript_text
    )

    assert notes.key_topics is not None
    assert len(notes.key_topics) > 0
    assert notes.session_mood in [m.value for m in MoodLevel]
    assert notes.therapist_notes is not None
    assert notes.patient_summary is not None
```

## Test Isolation

All fixtures ensure complete test isolation:

1. **Database cleanup**: Tables dropped after each test
2. **Transaction rollback**: Async fixtures use nested transactions
3. **Dependency overrides**: Cleared after each test
4. **Fresh sessions**: New database session for each test

## Best Practices

### 1. Use Async for Async Code

```python
# ✅ Good - async fixture for async code
@pytest.mark.asyncio
async def test_async_operation(async_test_db):
    result = await async_test_db.execute(select(User))

# ❌ Bad - sync fixture for async code
def test_async_operation(test_db):
    result = await test_db.execute(select(User))  # Won't work!
```

### 2. Minimize Database Setup

```python
# ✅ Good - use existing fixtures
def test_session(sample_session):
    assert sample_session.id is not None

# ❌ Bad - manual setup when fixture exists
def test_session(test_db, therapist_user):
    patient = Patient(...)
    test_db.add(patient)
    test_db.commit()
    # ... lots of boilerplate
```

### 3. Mock External Services

```python
# ✅ Good - mock OpenAI for unit tests
def test_extraction(mock_extraction_service):
    notes = await mock_extraction_service.extract_notes_from_transcript("...")

# ❌ Bad - real API calls in unit tests
def test_extraction():
    service = NoteExtractionService()  # Hits real API!
    notes = await service.extract_notes_from_transcript("...")
```

### 4. Use Appropriate Scope

Most fixtures use `scope="function"` for isolation:

```python
@pytest.fixture(scope="function")  # New instance per test
def sample_patient(test_db, therapist_user):
    # ...
```

Only use `scope="session"` for expensive setup that doesn't change state.

## Troubleshooting

### "Event loop is closed" error

Ensure you're using `@pytest.mark.asyncio` and async fixtures:

```python
import pytest

@pytest.mark.asyncio
async def test_something(async_test_db):  # Use async_test_db, not test_db
    # ...
```

### Fixture not found

Check imports and fixture names:

```python
# Make sure conftest.py is in tests/ directory
# Pytest auto-discovers fixtures in conftest.py
```

### Database isolation issues

Fixtures automatically clean up, but if you see cross-test contamination:

1. Check you're not using `scope="session"`
2. Ensure tests don't modify shared state
3. Verify each test uses fresh fixtures

### Mock not working

Ensure dependency override is set:

```python
from app.main import app
from app.services.note_extraction import get_extraction_service

def test_with_mock(client, mock_extraction_service):
    app.dependency_overrides[get_extraction_service] = lambda: mock_extraction_service
    # ... test code
```

## Configuration

### pytest.ini

Recommended configuration:

```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_sessions.py

# Run specific test
pytest tests/test_sessions.py::test_create_session

# Run with verbose output
pytest -v

# Run async tests only
pytest -k "async"

# Run with coverage
pytest --cov=app --cov-report=html
```

## Summary

| Fixture | Type | Purpose |
|---------|------|---------|
| `test_db` | Sync | Database session for sync tests |
| `async_test_db` | Async | Database session for async tests |
| `client` | Sync | HTTP client for sync endpoints |
| `async_client` | Async | HTTP client for async endpoints |
| `therapist_user` | Sync | Sample therapist user |
| `patient_user` | Sync | Sample patient user |
| `admin_user` | Sync | Sample admin user |
| `sample_patient` | Sync | Sample patient with therapist |
| `sample_session` | Sync | Basic therapy session |
| `sample_session_with_transcript` | Sync | Session with transcript text |
| `mock_openai` | Sync | Mocked OpenAI client |
| `mock_extraction_service` | Sync | NoteExtractionService with mock |
| `therapist_auth_headers` | Sync | Auth headers for therapist |

All async equivalents follow naming pattern: `async_<name>`

## Next Steps

1. See `test_fixtures_example.py` for working examples
2. Check existing tests for patterns: `test_auth_integration.py`
3. Refer to FastAPI testing docs: https://fastapi.tiangolo.com/tutorial/testing/
4. SQLAlchemy async docs: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
