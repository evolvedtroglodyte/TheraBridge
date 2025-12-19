"""
Tests for N+1 query prevention in export service.

This module verifies that eager loading (joinedload) is used correctly
to prevent N+1 queries when fetching sessions with related patient/therapist data.

Background:
-----------
An N+1 query problem occurs when:
1. We fetch N sessions in one query
2. For each session, we access session.patient or session.therapist
3. SQLAlchemy makes a separate query for each relationship access (N additional queries)
4. Total: 1 + N queries instead of 1 or 2 queries

Solution:
---------
Use SQLAlchemy's eager loading with joinedload() or selectinload() to fetch
relationships in the initial query, avoiding the N+1 problem.

Test Strategy:
--------------
We use SQLAlchemy's event listener to count actual database queries executed
during the test, then verify that query count is minimal (no N+1 pattern).
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import event
from sqlalchemy.engine import Engine

from app.services.export_service import ExportService
from app.services.pdf_generator import PDFGeneratorService
from app.services.docx_generator import DOCXGeneratorService
from app.models.db_models import User, Patient, TherapySession, TherapistPatient
from app.models.schemas import UserRole


# ============================================================================
# Query Counter - Tracks SQL queries executed during tests
# ============================================================================

class QueryCounter:
    """
    Context manager that counts SQL queries executed.

    Usage:
        with QueryCounter(db_session) as counter:
            # ... perform database operations ...
            pass

        print(f"Queries executed: {counter.count}")
    """

    def __init__(self):
        self.count = 0
        self.queries = []

    def __enter__(self):
        self.count = 0
        self.queries = []
        event.listen(Engine, "before_cursor_execute", self._before_cursor_execute)
        return self

    def __exit__(self, *args):
        event.remove(Engine, "before_cursor_execute", self._before_cursor_execute)

    def _before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        """Event handler called before each SQL query."""
        self.count += 1
        self.queries.append(statement)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_pdf_generator():
    """Mock PDF generator service."""
    from unittest.mock import AsyncMock
    generator = MagicMock(spec=PDFGeneratorService)
    generator.generate_from_template = AsyncMock(return_value=b"PDF content")
    return generator


@pytest.fixture
def mock_docx_generator():
    """Mock DOCX generator service."""
    from unittest.mock import AsyncMock
    generator = MagicMock(spec=DOCXGeneratorService)
    generator.generate_progress_report = AsyncMock(return_value=b"DOCX content")
    return generator


@pytest.fixture
def export_service(mock_pdf_generator, mock_docx_generator):
    """Create export service with mocked generators."""
    return ExportService(
        pdf_generator=mock_pdf_generator,
        docx_generator=mock_docx_generator
    )


@pytest_asyncio.fixture
async def many_sessions(async_test_db: AsyncSession):
    """
    Create therapist with multiple patients and many sessions.

    This fixture creates:
    - 1 therapist
    - 3 patients
    - 10 sessions total (distributed across patients)

    This allows us to test N+1 query prevention with a realistic dataset.
    """
    # Create therapist
    therapist = User(
        email="therapist.n1@test.com",
        hashed_password="hashed",
        first_name="N1Test",
        last_name="Therapist",
        full_name="N1Test Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(therapist)
    await async_test_db.flush()

    # Create 3 patients (using legacy Patient table that therapy_sessions reference)
    patients = []
    for i in range(3):
        patient = Patient(
            name=f"Patient{i} TestN1",
            email=f"patient.n1.{i}@test.com",
            phone="555-0100",
            therapist_id=therapist.id
        )
        async_test_db.add(patient)
        patients.append(patient)

    await async_test_db.flush()

    # Create 10 sessions distributed across patients
    now = datetime.utcnow()
    sessions = []

    for i in range(10):
        patient = patients[i % 3]  # Distribute sessions across patients
        session = TherapySession(
            patient_id=patient.id,
            therapist_id=therapist.id,
            session_date=now - timedelta(days=i),
            duration_seconds=3600,
            transcript_text=f"Session {i+1} transcript",
            extracted_notes={
                "key_topics": [f"topic_{i}"],
                "treatment_goals": []
            },
            status="processed"
        )
        async_test_db.add(session)
        sessions.append(session)

    await async_test_db.commit()

    return {
        "therapist": therapist,
        "patients": patients,
        "sessions": sessions
    }


# ============================================================================
# N+1 Query Prevention Tests
# ============================================================================

@pytest.mark.asyncio
async def test_gather_session_notes_prevents_n_plus_one(
    export_service: ExportService,
    async_test_db: AsyncSession,
    many_sessions
):
    """
    Test that gather_session_notes_data uses eager loading to prevent N+1 queries.

    Without eager loading:
    - 1 query to fetch 10 sessions
    - 10 queries to fetch patient for each session
    - 10 queries to fetch therapist for each session
    - Total: 21 queries

    With eager loading (joinedload):
    - 1 query to fetch sessions with patients and therapists joined
    - Total: 1 query (or at most 3 if using selectinload)
    """
    sessions = many_sessions["sessions"]
    session_ids = [s.id for s in sessions]

    # Count queries during data gathering
    with QueryCounter() as counter:
        context = await export_service.gather_session_notes_data(
            session_ids=session_ids,
            db=async_test_db
        )

    # Verify data was fetched correctly
    assert len(context["sessions"]) == 10
    assert context["session_count"] == 10
    assert context["therapist"] is not None
    assert len(context["patients"]) == 3

    # Verify query count is minimal (no N+1 problem)
    # With eager loading: should be 1-3 queries max
    # Without eager loading: would be 21+ queries
    print(f"Query count: {counter.count}")
    print(f"Queries executed: {counter.queries}")

    assert counter.count <= 5, (
        f"N+1 query detected! Expected ≤5 queries with eager loading, "
        f"but {counter.count} queries were executed. "
        f"This suggests missing joinedload() or selectinload()."
    )


@pytest.mark.asyncio
async def test_gather_progress_report_prevents_n_plus_one(
    export_service: ExportService,
    async_test_db: AsyncSession,
    many_sessions
):
    """
    Test that gather_progress_report_data uses eager loading to prevent N+1 queries.

    Without eager loading:
    - 1 query to fetch patient
    - 1 query to fetch therapist relationship
    - 1 query to fetch sessions in date range
    - N queries to fetch patient for each session
    - N queries to fetch therapist for each session
    - Total: 3 + 2N queries

    With eager loading:
    - 1 query for patient
    - 1 query for therapist relationship
    - 1 query for sessions with relationships joined
    - Total: 3-5 queries max
    """
    patient = many_sessions["patients"][0]
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()

    # Count queries during data gathering
    with QueryCounter() as counter:
        context = await export_service.gather_progress_report_data(
            patient_id=patient.id,
            start_date=start_date,
            end_date=end_date,
            db=async_test_db
        )

    # Verify data was fetched correctly
    assert context["patient"] is not None
    assert context["therapist"] is not None
    assert context["session_count"] >= 3  # At least 3 sessions for this patient

    # Verify query count is minimal (no N+1 problem)
    print(f"Query count: {counter.count}")
    print(f"Queries executed: {counter.queries}")

    assert counter.count <= 10, (
        f"N+1 query detected! Expected ≤10 queries with eager loading, "
        f"but {counter.count} queries were executed. "
        f"This suggests missing joinedload() or selectinload() in progress report query."
    )


@pytest.mark.asyncio
async def test_timeline_export_worker_prevents_n_plus_one(
    async_test_db: AsyncSession,
    many_sessions
):
    """
    Test that export_worker._fetch_timeline_data uses eager loading.

    This tests the export worker background task that fetches timeline data.
    """
    from app.tasks.export_worker import _fetch_timeline_data

    patient = many_sessions["patients"][0]
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()

    # Count queries during timeline data fetch
    with QueryCounter() as counter:
        timeline_data = await _fetch_timeline_data(
            patient_id=patient.id,
            start_date=start_date,
            end_date=end_date,
            db=async_test_db
        )

    # Verify data was fetched
    assert len(timeline_data) >= 3  # At least 3 sessions for this patient

    # Verify query count is minimal
    print(f"Query count: {counter.count}")
    print(f"Queries executed: {counter.queries}")

    assert counter.count <= 5, (
        f"N+1 query detected in export_worker! Expected ≤5 queries with eager loading, "
        f"but {counter.count} queries were executed. "
        f"This suggests missing joinedload() or selectinload() in _fetch_timeline_data."
    )


# ============================================================================
# Comparison Test - Demonstrates N+1 Problem Without Eager Loading
# ============================================================================

@pytest.mark.asyncio
async def test_demonstrate_n_plus_one_problem_without_eager_loading(
    async_test_db: AsyncSession,
    many_sessions
):
    """
    Demonstration test showing what happens WITHOUT eager loading.

    This test deliberately avoids eager loading to show the N+1 problem.
    It's marked as expected to have many queries (for documentation purposes).

    This test is informational - it shows the problem we're solving.
    """
    from sqlalchemy import select

    sessions = many_sessions["sessions"]
    session_ids = [s.id for s in sessions]

    # Query WITHOUT eager loading (the wrong way)
    with QueryCounter() as counter:
        query = select(TherapySession).where(TherapySession.id.in_(session_ids))
        # NOTE: No .options(joinedload(...)) - this is the bug!

        result = await async_test_db.execute(query)
        sessions_fetched = result.scalars().all()

        # Access relationships - this triggers N+1 queries
        for session in sessions_fetched:
            _ = session.patient  # Lazy load - triggers query
            _ = session.therapist  # Lazy load - triggers query

    print(f"N+1 problem demonstration - Query count: {counter.count}")

    # Without eager loading, we expect 1 + 2N queries (1 for sessions, 2N for relationships)
    # With 10 sessions: 1 + 20 = 21 queries
    assert counter.count >= 15, (
        f"Expected N+1 problem to cause many queries (≥15), "
        f"but only {counter.count} were executed. Test may be invalid."
    )
