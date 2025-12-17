# Pytest Fixtures Quick Reference

Quick reference card for test fixtures in `/backend/tests/conftest.py`

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/test_fixtures_example.py -v

# Run with specific fixtures
pytest tests/ -k "auth" -v
```

## Most Common Fixtures

### Database
```python
def test_something(test_db):              # Sync database
@pytest.mark.asyncio
async def test_async(async_test_db):      # Async database
```

### HTTP Clients
```python
def test_endpoint(client):                # Sync client
@pytest.mark.asyncio
async def test_async_endpoint(async_client):  # Async client
```

### Users & Auth
```python
def test_therapist(therapist_user, therapist_auth_headers):  # Therapist
def test_patient(patient_user, patient_auth_headers):        # Patient
def test_admin(admin_user, admin_auth_headers):              # Admin
```

### Sample Data
```python
def test_patient(sample_patient):         # Patient owned by therapist
def test_session(sample_session):         # Basic session
def test_transcript(sample_session_with_transcript):  # Session + transcript
```

### Mock OpenAI
```python
@pytest.mark.asyncio
async def test_extraction(mock_extraction_service):
    notes = await mock_extraction_service.extract_notes_from_transcript(text)
```

## All Available Fixtures

### Database Fixtures
| Fixture | Type | Description |
|---------|------|-------------|
| `test_db` | Sync | Sync database session |
| `async_test_db` | Async | Async database session |
| `db_session` | Sync | Alias for test_db |

### HTTP Client Fixtures
| Fixture | Type | Description |
|---------|------|-------------|
| `client` | Sync | FastAPI TestClient |
| `async_client` | Async | AsyncClient for async endpoints |

### User Fixtures
| Fixture | Role | Email | Password |
|---------|------|-------|----------|
| `therapist_user` | therapist | therapist@test.com | testpass123 |
| `patient_user` | patient | patient@test.com | patientpass123 |
| `admin_user` | admin | admin@test.com | adminpass123 |
| `test_user` | therapist | test@example.com | TestPass123! |
| `test_patient_user` | patient | patient@example.com | PatientPass123! |
| `inactive_user` | therapist | inactive@example.com | InactivePass123! |

### Auth Token Fixtures
| Fixture | Returns |
|---------|---------|
| `therapist_token` | JWT token string |
| `patient_token` | JWT token string |
| `admin_token` | JWT token string |

### Auth Header Fixtures
| Fixture | Returns |
|---------|---------|
| `therapist_auth_headers` | {"Authorization": "Bearer <token>"} |
| `patient_auth_headers` | {"Authorization": "Bearer <token>"} |
| `admin_auth_headers` | {"Authorization": "Bearer <token>"} |

### Sample Data Fixtures (Sync)
| Fixture | Description |
|---------|-------------|
| `sample_patient` | Patient: "John Doe", email: john.doe@example.com |
| `sample_session` | Session in "pending" status, 3600s duration |
| `sample_session_with_transcript` | Session with realistic therapy transcript |

### Sample Data Fixtures (Async)
| Fixture | Description |
|---------|-------------|
| `async_sample_patient` | Async patient: "Jane Smith" |
| `async_sample_session` | Async session in "pending" status |
| `async_sample_session_with_transcript` | Async session with transcript |

### Mock OpenAI Fixtures
| Fixture | Description |
|---------|-------------|
| `mock_openai` | Mocked AsyncOpenAI client |
| `mock_extraction_service` | NoteExtractionService with mocked client |
| `mock_openai_client` | Enhanced mock with default response |
| `mock_openai_with_risk_flags` | Mock returning risk flags |
| `mock_openai_rate_limit` | Mock that raises RateLimitError |
| `mock_openai_timeout` | Mock that raises APITimeoutError |
| `mock_openai_api_error` | Mock that raises APIError |

## Common Patterns

### Create User Test
```python
def test_create_user(test_db):
    user = User(email="new@test.com", ...)
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    assert user.id is not None
```

### Async Query Test
```python
@pytest.mark.asyncio
async def test_query_users(async_test_db):
    from sqlalchemy import select
    result = await async_test_db.execute(select(User))
    users = result.scalars().all()
    assert len(users) == 0
```

### Authenticated API Test
```python
def test_get_patients(client, therapist_auth_headers):
    response = client.get("/api/patients", headers=therapist_auth_headers)
    assert response.status_code == 200
```

### Async API Test
```python
@pytest.mark.asyncio
async def test_async_endpoint(async_client, therapist_auth_headers):
    response = await async_client.get("/api/patients", headers=therapist_auth_headers)
    assert response.status_code == 200
```

### Test with Sample Data
```python
def test_session_belongs_to_patient(sample_session, sample_patient):
    assert sample_session.patient_id == sample_patient.id
    assert sample_session.status == "pending"
```

### Mock OpenAI Test
```python
@pytest.mark.asyncio
async def test_note_extraction(mock_extraction_service):
    transcript = "Therapist: Hello. Client: Hi, I'm feeling better."
    notes = await mock_extraction_service.extract_notes_from_transcript(transcript)

    assert notes.key_topics is not None
    assert notes.session_mood == MoodLevel.positive
    assert notes.therapist_notes is not None
```

### Override Dependency
```python
def test_with_mock_service(client, mock_extraction_service):
    from app.main import app
    from app.services.note_extraction import get_extraction_service

    app.dependency_overrides[get_extraction_service] = lambda: mock_extraction_service

    try:
        response = client.post("/api/extract", json={...})
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()
```

## Common Mistakes

### ❌ Wrong: Using sync fixture for async code
```python
def test_async_code(test_db):  # Wrong fixture!
    result = await test_db.execute(...)  # Won't work
```

### ✅ Right: Using async fixture
```python
@pytest.mark.asyncio
async def test_async_code(async_test_db):  # Correct!
    result = await async_test_db.execute(...)
```

### ❌ Wrong: Manual user creation when fixture exists
```python
def test_endpoint(client, test_db):
    user = User(email="test@test.com", ...)  # Manual setup
    test_db.add(user)
    test_db.commit()
    # ... lots of boilerplate
```

### ✅ Right: Using fixture
```python
def test_endpoint(client, therapist_user, therapist_auth_headers):
    # User already created, ready to use
    response = client.get("/api/patients", headers=therapist_auth_headers)
```

### ❌ Wrong: Hitting real OpenAI API in tests
```python
def test_extraction():
    service = NoteExtractionService()  # Real API call!
    notes = await service.extract_notes_from_transcript(...)
```

### ✅ Right: Using mock
```python
def test_extraction(mock_extraction_service):
    # No API call, no cost
    notes = await mock_extraction_service.extract_notes_from_transcript(...)
```

## Test Isolation

**Every test gets fresh database:**
```python
def test_1(test_db):
    user = User(...)
    test_db.add(user)
    test_db.commit()
    # User exists in this test

def test_2(test_db):
    users = test_db.query(User).all()
    assert len(users) == 0  # ✅ test_1's user is gone!
```

## Running Tests

```bash
# All tests
pytest

# Specific file
pytest tests/test_fixtures_example.py

# Specific test
pytest tests/test_fixtures_example.py::test_sync_database_fixture

# Tests matching pattern
pytest -k "auth"
pytest -k "async"
pytest -k "mock"

# Verbose output
pytest -v

# With coverage
pytest --cov=app

# Parallel execution
pytest -n auto

# Stop on first failure
pytest -x

# Show print statements
pytest -s
```

## Pytest Markers

```python
@pytest.mark.asyncio           # For async tests
@pytest.mark.skip              # Skip test
@pytest.mark.skipif(condition) # Conditional skip
@pytest.mark.parametrize       # Parameterized tests
```

## Need More Help?

- **Full documentation:** `FIXTURES_GUIDE.md`
- **38 examples:** `test_fixtures_example.py`
- **Database config:** `TEST_DATABASE_CONFIG.md`
- **Summary:** `FIXTURES_SUMMARY.md`

## Example Test File Template

```python
"""
Tests for [feature name]
"""
import pytest
from sqlalchemy import select
from app.models.db_models import User, Patient, Session


def test_sync_feature(test_db, therapist_user):
    """Test synchronous database operations."""
    # Your test code here
    pass


@pytest.mark.asyncio
async def test_async_feature(async_test_db, therapist_user):
    """Test asynchronous database operations."""
    # Your async test code here
    pass


def test_api_endpoint(client, therapist_auth_headers):
    """Test API endpoint with authentication."""
    response = client.get("/api/endpoint", headers=therapist_auth_headers)
    assert response.status_code == 200


def test_with_sample_data(sample_patient, sample_session):
    """Test using sample fixtures."""
    assert sample_session.patient_id == sample_patient.id


@pytest.mark.asyncio
async def test_extraction(mock_extraction_service):
    """Test note extraction without API costs."""
    notes = await mock_extraction_service.extract_notes_from_transcript("...")
    assert notes is not None
```

## Tips

1. **Use fixtures** - Don't create data manually
2. **Async for async** - Use async fixtures for async code
3. **Mock external services** - Don't hit real APIs in tests
4. **Test isolation works** - Each test is independent
5. **Read examples** - Check `test_fixtures_example.py` for patterns

## Performance

- Simple test: ~20-50ms
- With fixtures: ~50-100ms
- Full integration: ~200-300ms

Optimize with:
- `pytest -n auto` (parallel)
- Mock external services
- Use sync fixtures when possible
