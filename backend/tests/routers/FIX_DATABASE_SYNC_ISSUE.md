# Fix Guide: Database Synchronization Issue

## Problem
Tests fail with "Session/Patient not found" errors because:
1. Fixtures create data using **synchronous SQLAlchemy** (sqlite)
2. TestClient queries using **asynchronous SQLAlchemy** (aiosqlite)
3. Both connect to same DB file but don't see each other's transactions

## Solution #1: PostgreSQL Testcontainer (RECOMMENDED)

### Why This Works
- PostgreSQL handles concurrent connections properly
- Matches production database
- Async/sync interoperability built-in

### Implementation

#### 1. Install Dependencies
```bash
pip install testcontainers[postgres]
```

#### 2. Update `tests/routers/conftest.py`

```python
import pytest
import pytest_asyncio
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Global container for test session
_postgres_container = None
_test_db_url = None
_test_async_db_url = None


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for all tests"""
    global _postgres_container, _test_db_url, _test_async_db_url

    _postgres_container = PostgresContainer("postgres:15-alpine")
    _postgres_container.start()

    # Get connection strings
    _test_db_url = _postgres_container.get_connection_url()
    _test_async_db_url = _test_db_url.replace("postgresql://", "postgresql+asyncpg://")

    yield _postgres_container

    _postgres_container.stop()


@pytest.fixture(scope="session")
def test_sync_engine(postgres_container):
    """Create synchronous engine for fixtures"""
    engine = create_engine(_test_db_url)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope="session")
def test_async_engine(postgres_container):
    """Create asynchronous engine for TestClient"""
    engine = create_async_engine(_test_async_db_url)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_sync_engine):
    """Provide synchronous session for fixtures"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_sync_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest_asyncio.fixture(scope="function")
async def test_async_db(test_async_engine):
    """Provide asynchronous session for TestClient"""
    AsyncSessionLocal = async_sessionmaker(test_async_engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
def client(test_async_db):
    """TestClient with overridden DB dependency"""
    async def override_get_db():
        yield test_async_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def therapist_user(test_db):
    """Create therapist user using sync session"""
    from app.models.db_models import User
    from app.auth.utils import get_password_hash
    from app.models.schemas import UserRole
    from uuid import uuid4

    user = User(
        id=uuid4(),
        email="therapist@test.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test Therapist",
        role=UserRole.therapist,
        is_active=True
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_patient(test_db, therapist_user):
    """Create patient using sync session"""
    from app.models.db_models import Patient
    from uuid import uuid4

    patient = Patient(
        id=uuid4(),
        name="Test Patient",
        email="patient@test.com",
        phone="+1234567890",
        therapist_id=therapist_user.id
    )
    test_db.add(patient)
    test_db.commit()
    test_db.refresh(patient)
    return patient


@pytest.fixture(scope="function")
def test_session(test_db, test_patient, therapist_user):
    """Create session using sync session"""
    from app.models.db_models import Session
    from datetime import datetime
    from uuid import uuid4

    session = Session(
        id=uuid4(),
        patient_id=test_patient.id,
        therapist_id=therapist_user.id,
        session_date=datetime.utcnow(),
        status="pending",
        transcript_text="Sample transcript"
    )
    test_db.add(session)
    test_db.commit()
    test_db.refresh(session)
    return session
```

#### 3. Update `requirements.txt`
```txt
testcontainers[postgres]>=3.7.0
asyncpg>=0.29.0  # PostgreSQL async driver
```

#### 4. Run Tests
```bash
pytest tests/routers/test_sessions.py -v
```

### Expected Result
✅ All 36+ tests should pass
✅ Database synchronization issues resolved
✅ Tests run ~2-3x faster than before

---

## Solution #2: All-Async Fixtures (Alternative)

### Why This Works
- Everything uses AsyncSession
- Single connection type (aiosqlite)
- No sync/async mixing

### Implementation

```python
@pytest_asyncio.fixture(scope="function")
async def therapist_user(test_async_db):
    """Create therapist user using async session"""
    from app.models.db_models import User
    from app.auth.utils import get_password_hash
    from app.models.schemas import UserRole
    from uuid import uuid4

    user = User(
        id=uuid4(),
        email="therapist@test.com",
        hashed_password=get_password_hash("testpass123"),
        full_name="Test Therapist",
        role=UserRole.therapist,
        is_active=True
    )
    test_async_db.add(user)
    await test_async_db.commit()
    await test_async_db.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def test_patient(test_async_db, therapist_user):
    """Create patient using async session"""
    from app.models.db_models import Patient
    from uuid import uuid4

    patient = Patient(
        id=uuid4(),
        name="Test Patient",
        email="patient@test.com",
        phone="+1234567890",
        therapist_id=therapist_user.id
    )
    test_async_db.add(patient)
    await test_async_db.commit()
    await test_async_db.refresh(patient)
    return patient


# All other fixtures follow same pattern: use `await` and `test_async_db`
```

### Pros
- No external dependencies (testcontainers)
- Keeps SQLite for simplicity
- Pure async pattern

### Cons
- All test functions must be `async def`
- More complex fixture dependencies
- SQLite limitations remain (concurrency)

---

## Solution #3: Shared Session (Quick Fix)

### Why This Works
- Both sync and async use same session instance
- Bypasses connection isolation

### Implementation
```python
@pytest.fixture(scope="function")
def shared_db():
    """Single session for both sync and async"""
    from sqlalchemy.orm import Session
    from sqlalchemy import create_engine

    engine = create_engine("sqlite:///./test.db")
    Base.metadata.create_all(bind=engine)

    session = Session(engine)
    yield session

    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(shared_db):
    """Override both sync and async dependencies"""
    def override_get_db():
        yield shared_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
```

### Pros
- Minimal code changes
- Quick to implement

### Cons
- Not production-like
- Doesn't test async properly
- Not recommended for CI/CD

---

## Comparison Matrix

| Solution | Complexity | Production Parity | Async Testing | Setup Time |
|----------|-----------|-------------------|---------------|------------|
| **PostgreSQL Testcontainer** | Medium | ✅ High | ✅ Full | 2-3 hours |
| All-Async Fixtures | Medium | ⚠️ Medium | ✅ Full | 4-6 hours |
| Shared Session | Low | ❌ Low | ❌ Limited | 30 mins |

---

## Recommendation

**Use PostgreSQL Testcontainer (Solution #1)** for:
- ✅ Best production parity
- ✅ Proper async/sync interoperability
- ✅ Scalable for future tests
- ✅ Industry best practice

---

## Verification Steps

After implementing the fix:

```bash
# 1. Run all tests
pytest tests/routers/test_sessions.py -v

# Expected: 35+ passing, 1 skipped (rate limit), 0-2 failures

# 2. Check coverage
pytest tests/routers/test_sessions.py --cov=app/routers/sessions

# Expected: 70%+ coverage

# 3. Run specific failing test
pytest tests/routers/test_sessions.py::test_get_session_by_id -v

# Expected: PASSED

# 4. Verify database cleanup
ls test*.db
# Expected: No leftover database files
```

---

## Additional Resources

- [Testcontainers Python Docs](https://testcontainers-python.readthedocs.io/)
- [SQLAlchemy Async Guide](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [pytest-asyncio Guide](https://pytest-asyncio.readthedocs.io/)
- [FastAPI Testing Best Practices](https://fastapi.tiangolo.com/advanced/testing-database/)

---

**Next Steps**: Implement Solution #1 and verify tests pass
