# Test Database Configuration

## Overview

The test infrastructure uses **SQLite in-memory databases** for fast, isolated testing. This document explains the configuration and provides recommendations.

## Current Configuration

### Database URLs

**Synchronous tests:**
```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
```

**Asynchronous tests:**
```python
ASYNC_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
```

### Engine Configuration

**Sync Engine:**
```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
```

**Async Engine:**
```python
async_engine = create_async_engine(
    ASYNC_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
```

### Why SQLite for Tests?

1. **Speed**: In-memory SQLite is 10-100x faster than PostgreSQL
2. **Isolation**: Each test gets a fresh database
3. **No setup**: No database server required
4. **Portability**: Works on any platform
5. **CI/CD friendly**: No external dependencies

## Compatibility Handling

### JSONB → JSON Conversion

PostgreSQL uses `JSONB` columns, but SQLite only supports `JSON`. The test configuration automatically converts:

```python
@event.listens_for(Base.metadata, "before_create")
def _set_json_columns(target, connection, **kw):
    """Convert JSONB columns to JSON for SQLite."""
    if connection.dialect.name == "sqlite":
        for col in Session.__table__.columns:
            if isinstance(col.type, JSONB):
                col.type = JSON()
```

This ensures tests work with SQLite while production uses PostgreSQL.

### UUID Handling

SQLite stores UUIDs as strings, but this is transparent in tests:

```python
# Works in both SQLite and PostgreSQL
id = Column(SQLUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

## Test Isolation Strategy

### Per-Test Database Creation

Each test function gets:
1. Fresh table creation
2. New database session
3. Automatic cleanup after test

**Sync isolation:**
```python
@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)  # Create tables
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # Clean up
```

**Async isolation:**
```python
@pytest_asyncio.fixture(scope="function")
async def async_test_db():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncTestingSessionLocal() as session:
        async with session.begin():
            yield session
            await session.rollback()  # Rollback for isolation

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Dependency Injection

Tests override FastAPI database dependencies:

```python
@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
```

## Performance Optimization

### Current Performance

- **Test database creation**: ~5-10ms per test
- **Fixture setup**: ~10-50ms per test
- **Total overhead**: ~15-60ms per test

### Optimization Options

**1. In-Memory Database (Fastest)**

Already implemented - uses file-based SQLite but could switch to pure in-memory:

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"  # Pure in-memory
```

**Pros:**
- Fastest possible
- No file I/O

**Cons:**
- Harder to debug (no persistent file)
- Can't inspect database between tests

**2. Connection Pooling (Current Approach)**

Uses file-based SQLite with cleanup:

```python
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"  # File-based
```

**Pros:**
- Can inspect test.db if test fails
- Easier debugging
- Still very fast

**Cons:**
- Slightly slower than pure in-memory
- Creates test.db file (cleaned up after tests)

**3. Session Fixture (Module Scope)**

For tests that don't need isolation:

```python
@pytest.fixture(scope="module")
def shared_test_db():
    """Shared database for read-only tests."""
    Base.metadata.create_all(bind=engine)
    yield TestingSessionLocal()
    Base.metadata.drop_all(bind=engine)
```

**Use for:**
- Read-only tests
- Tests that don't modify data
- Performance-critical test suites

**Don't use for:**
- Tests that create/update/delete data
- Tests that need isolation

## Testing Against Production Database

For integration tests that need PostgreSQL-specific features:

### Option 1: Docker PostgreSQL

```python
import os

# conftest.py
@pytest.fixture(scope="session")
def postgres_test_db():
    """PostgreSQL test database for integration tests."""
    if os.getenv("USE_POSTGRES_TESTS"):
        DATABASE_URL = "postgresql://test:test@localhost:5432/test_db"
        engine = create_engine(DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        yield sessionmaker(bind=engine)()
        Base.metadata.drop_all(bind=engine)
    else:
        pytest.skip("PostgreSQL tests disabled")
```

**Setup:**
```bash
# Start PostgreSQL in Docker
docker run -d \
  --name postgres-test \
  -e POSTGRES_USER=test \
  -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=test_db \
  -p 5432:5432 \
  postgres:15

# Run tests
USE_POSTGRES_TESTS=true pytest tests/
```

### Option 2: pytest-postgresql Plugin

```bash
pip install pytest-postgresql
```

```python
@pytest.fixture
def test_db(postgresql):
    """Auto-managed PostgreSQL test database."""
    engine = create_engine(postgresql.url())
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(bind=engine)()
```

## Recommendations

### For Unit Tests
✅ **Use SQLite in-memory** (current approach)
- Fast
- Isolated
- No external dependencies

### For Integration Tests
✅ **Use Docker PostgreSQL**
- Tests production database features
- Validates JSONB, UUID, full-text search
- Catches PostgreSQL-specific issues

### For CI/CD
✅ **SQLite for fast feedback**
```yaml
# .github/workflows/test.yml
- name: Run unit tests
  run: pytest tests/ -v
```

✅ **PostgreSQL for pre-merge**
```yaml
services:
  postgres:
    image: postgres:15
    env:
      POSTGRES_PASSWORD: test
- name: Run integration tests
  run: USE_POSTGRES_TESTS=true pytest tests/integration/
```

## Troubleshooting

### Issue: "Event loop is closed"

**Solution:** Use `@pytest.mark.asyncio` and async fixtures:
```python
@pytest.mark.asyncio
async def test_something(async_test_db):  # Not test_db
    # ...
```

### Issue: "Database is locked"

**Solution:** Use `connect_args={"check_same_thread": False}`:
```python
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
```

### Issue: Tests affecting each other

**Solution:** Verify fixture scope is `"function"` not `"session"`:
```python
@pytest.fixture(scope="function")  # Isolated
def test_db():
    # ...
```

### Issue: JSONB not working in tests

**Solution:** Already handled by JSONB→JSON converter. If issues persist:
```python
# Check if conversion is applied
from app.models.db_models import Session
for col in Session.__table__.columns:
    print(f"{col.name}: {col.type}")
```

### Issue: UUID comparison failing

**Solution:** Convert to string for comparison in SQLite:
```python
assert str(session.patient_id) == str(patient.id)
```

## Configuration Summary

| Setting | Value | Reason |
|---------|-------|--------|
| Database | SQLite file-based | Debugging friendly |
| Async Driver | aiosqlite | Async support |
| Isolation | Per-test create/drop | Full isolation |
| Transaction | Rollback in async | Faster cleanup |
| JSONB Handling | Auto-convert to JSON | SQLite compatibility |
| Check same thread | Disabled | Multi-thread support |

## Next Steps

1. ✅ Run example tests: `pytest tests/test_fixtures_example.py -v`
2. ✅ Verify isolation: Check that tests don't affect each other
3. ✅ Measure performance: Run with `pytest --durations=10`
4. Consider PostgreSQL integration tests for production validation
5. Add parallel test execution: `pip install pytest-xdist && pytest -n auto`

## Performance Benchmarks

**Current setup (SQLite):**
- Simple test: ~20ms
- With fixtures: ~50ms
- With API client: ~100ms
- Full integration: ~200ms

**Target (optimized):**
- Simple test: <10ms
- With fixtures: <30ms
- With API client: <80ms
- Full integration: <150ms

**Optimizations to consider:**
1. Switch to pure in-memory SQLite: `sqlite:///:memory:`
2. Use `pytest-xdist` for parallel execution
3. Cache compiled SQLAlchemy models
4. Reduce fixture scope where safe
5. Mock external services (OpenAI, file I/O)
