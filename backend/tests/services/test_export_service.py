"""
Tests for export service - data gathering and export orchestration.

This module tests:
- Session notes data gathering
- Progress report data gathering
- Export generation (PDF, DOCX, JSON)
- Serialization of ORM models
- Integration tests for full export workflow
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.export_service import ExportService, get_export_service
from app.services.pdf_generator import PDFGeneratorService
from app.services.docx_generator import DOCXGeneratorService
from app.models.db_models import User, TherapySession, TherapistPatient
from app.models.schemas import UserRole, SessionStatus


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_pdf_generator():
    """Mock PDF generator service."""
    generator = MagicMock(spec=PDFGeneratorService)
    generator.generate_from_template = AsyncMock(return_value=b"PDF content")
    return generator


@pytest.fixture
def mock_docx_generator():
    """Mock DOCX generator service."""
    generator = MagicMock(spec=DOCXGeneratorService)
    generator.generate_progress_report = AsyncMock(return_value=b"DOCX content")
    generator.generate_treatment_summary = AsyncMock(return_value=b"DOCX summary")
    return generator


@pytest.fixture
def export_service(mock_pdf_generator, mock_docx_generator):
    """Create export service with mocked generators."""
    return ExportService(
        pdf_generator=mock_pdf_generator,
        docx_generator=mock_docx_generator
    )


@pytest_asyncio.fixture
async def therapist_with_sessions(async_test_db: AsyncSession):
    """
    Create therapist with patient and therapy sessions for testing.

    Returns:
        Dict with therapist, patient, and sessions
    """
    # Create therapist
    therapist = User(
        email="export.therapist@test.com",
        hashed_password="hashed",
        first_name="Export",
        last_name="Therapist",
        full_name="Export Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(therapist)
    await async_test_db.flush()

    # Create patient
    patient = User(
        email="export.patient@test.com",
        hashed_password="hashed",
        first_name="Export",
        last_name="Patient",
        full_name="Export Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(patient)
    await async_test_db.flush()

    # Create therapist-patient relationship
    relationship = TherapistPatient(
        therapist_id=therapist.id,
        patient_id=patient.id,
        relationship_type='primary',
        is_active=True
    )
    async_test_db.add(relationship)
    await async_test_db.flush()

    # Create 3 therapy sessions
    now = datetime.utcnow()
    sessions = []

    for i in range(3):
        session = TherapySession(
            patient_id=patient.id,
            therapist_id=therapist.id,
            session_date=now - timedelta(days=(i * 7)),
            duration_seconds=3600 + (i * 300),  # 60-75 minutes
            transcript_text=f"Session {i+1} transcript",
            extracted_notes={
                "key_topics": [f"topic_{i}_a", f"topic_{i}_b"],
                "session_mood": "neutral" if i == 0 else "positive",
                "mood_trajectory": "improving",
                "treatment_goals": [
                    {
                        "description": f"Goal {i+1}",
                        "baseline": "Low",
                        "current": "Medium",
                        "progress_percentage": 50 + (i * 10)
                    }
                ]
            },
            therapist_summary=f"Summary for session {i+1}",
            patient_summary=f"Patient summary {i+1}",
            status="processed"
        )
        async_test_db.add(session)
        sessions.append(session)

    await async_test_db.commit()

    return {
        "therapist": therapist,
        "patient": patient,
        "sessions": sessions
    }


# ============================================================================
# Session Notes Data Gathering Tests
# ============================================================================

@pytest.mark.asyncio
async def test_gather_session_notes_data_success(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions
):
    """Test successful gathering of session notes data."""
    sessions = therapist_with_sessions["sessions"]
    session_ids = [s.id for s in sessions]

    # Gather data
    context = await export_service.gather_session_notes_data(
        session_ids=session_ids,
        db=async_test_db
    )

    # Verify context structure
    assert "sessions" in context
    assert "therapist" in context
    assert "patients" in context
    assert "session_count" in context

    # Verify session data
    assert len(context["sessions"]) == 3
    assert context["session_count"] == 3

    # Verify therapist data
    assert context["therapist"]["email"] == "export.therapist@test.com"
    assert context["therapist"]["role"] == "therapist"

    # Verify patients dict
    assert len(context["patients"]) == 1
    patient_id = str(therapist_with_sessions["patient"].id)
    assert patient_id in context["patients"]
    assert context["patients"][patient_id]["email"] == "export.patient@test.com"


@pytest.mark.asyncio
async def test_gather_session_notes_multiple_sessions(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions
):
    """Test gathering data for multiple sessions."""
    sessions = therapist_with_sessions["sessions"]
    session_ids = [s.id for s in sessions[:2]]  # Only first 2 sessions

    context = await export_service.gather_session_notes_data(
        session_ids=session_ids,
        db=async_test_db
    )

    # Verify only 2 sessions included
    assert len(context["sessions"]) == 2
    assert context["session_count"] == 2

    # Verify session data integrity
    for session_data in context["sessions"]:
        assert "id" in session_data
        assert "session_date" in session_data
        assert "transcript_text" in session_data
        assert "extracted_notes" in session_data


@pytest.mark.asyncio
async def test_gather_session_notes_no_sessions_raises(
    export_service: ExportService,
    async_test_db: AsyncSession
):
    """Test that ValueError is raised when no sessions found."""
    fake_session_ids = [uuid4(), uuid4()]

    with pytest.raises(ValueError, match="No sessions found"):
        await export_service.gather_session_notes_data(
            session_ids=fake_session_ids,
            db=async_test_db
        )


@pytest.mark.asyncio
async def test_gather_session_notes_empty_list_raises(
    export_service: ExportService,
    async_test_db: AsyncSession
):
    """Test that ValueError is raised when session_ids list is empty."""
    with pytest.raises(ValueError, match="No sessions found"):
        await export_service.gather_session_notes_data(
            session_ids=[],
            db=async_test_db
        )


# ============================================================================
# Progress Report Data Gathering Tests
# ============================================================================

@pytest.mark.asyncio
async def test_gather_progress_report_data_success(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions
):
    """Test successful gathering of progress report data."""
    patient = therapist_with_sessions["patient"]
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()

    context = await export_service.gather_progress_report_data(
        patient_id=patient.id,
        start_date=start_date,
        end_date=end_date,
        db=async_test_db
    )

    # Verify context structure
    assert "patient" in context
    assert "therapist" in context
    assert "sessions" in context
    assert "session_count" in context
    assert "avg_duration_minutes" in context
    assert "goals" in context
    assert "key_topics" in context
    assert "start_date" in context
    assert "end_date" in context

    # Verify patient data
    assert context["patient"]["email"] == "export.patient@test.com"

    # Verify therapist data
    assert context["therapist"]["email"] == "export.therapist@test.com"

    # Verify sessions
    assert context["session_count"] == 3


@pytest.mark.asyncio
async def test_gather_progress_report_calculates_metrics(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions
):
    """Test that progress report calculates avg duration and session count correctly."""
    patient = therapist_with_sessions["patient"]
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()

    context = await export_service.gather_progress_report_data(
        patient_id=patient.id,
        start_date=start_date,
        end_date=end_date,
        db=async_test_db
    )

    # Verify session count
    assert context["session_count"] == 3

    # Verify avg duration calculation
    # Sessions have durations: 3600, 3900, 4200 seconds
    # Average: (3600 + 3900 + 4200) / 3 = 3900 seconds = 65 minutes
    assert context["avg_duration_minutes"] == 65.0


@pytest.mark.asyncio
async def test_gather_progress_report_extracts_topics(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions
):
    """Test that progress report extracts and counts topics correctly."""
    patient = therapist_with_sessions["patient"]
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()

    context = await export_service.gather_progress_report_data(
        patient_id=patient.id,
        start_date=start_date,
        end_date=end_date,
        db=async_test_db
    )

    # Verify topics extracted
    assert "key_topics" in context
    assert isinstance(context["key_topics"], list)

    # Each session has 2 topics, so we should have topics extracted
    assert len(context["key_topics"]) > 0


@pytest.mark.asyncio
async def test_gather_progress_report_patient_not_found_raises(
    export_service: ExportService,
    async_test_db: AsyncSession
):
    """Test that ValueError is raised when patient not found."""
    fake_patient_id = uuid4()
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()

    with pytest.raises(ValueError, match="Patient .* not found"):
        await export_service.gather_progress_report_data(
            patient_id=fake_patient_id,
            start_date=start_date,
            end_date=end_date,
            db=async_test_db
        )


@pytest.mark.asyncio
async def test_gather_progress_report_extracts_goals(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions
):
    """Test that progress report extracts treatment goals from sessions."""
    patient = therapist_with_sessions["patient"]
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()

    context = await export_service.gather_progress_report_data(
        patient_id=patient.id,
        start_date=start_date,
        end_date=end_date,
        db=async_test_db
    )

    # Verify goals extracted
    assert "goals" in context
    assert isinstance(context["goals"], list)

    # Each session has 1 goal, so we should have 3 goals
    assert len(context["goals"]) == 3


# ============================================================================
# Export Generation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_generate_export_pdf_calls_pdf_generator(
    export_service: ExportService,
    mock_pdf_generator
):
    """Test that PDF generation routes to PDF generator."""
    context = {"sessions": [], "therapist": {}, "patients": {}}

    result = await export_service.generate_export(
        export_type="session_notes",
        format="pdf",
        context=context
    )

    # Verify PDF generator called
    mock_pdf_generator.generate_from_template.assert_called_once()

    # Verify template name
    call_args = mock_pdf_generator.generate_from_template.call_args
    assert call_args[0][0] == "session_notes.html"
    assert call_args[0][1] == context

    # Verify result
    assert result == b"PDF content"


@pytest.mark.asyncio
async def test_generate_export_docx_calls_docx_generator(
    export_service: ExportService,
    mock_docx_generator
):
    """Test that DOCX generation routes to DOCX generator for progress report."""
    context = {
        "patient": {"name": "Test Patient"},
        "therapist": {"name": "Test Therapist"},
        "goals": [],
        "sessions": [],
        "start_date": datetime.utcnow(),
        "end_date": datetime.utcnow()
    }

    result = await export_service.generate_export(
        export_type="progress_report",
        format="docx",
        context=context
    )

    # Verify DOCX generator called
    mock_docx_generator.generate_progress_report.assert_called_once()

    # Verify result
    assert result == b"DOCX content"


@pytest.mark.asyncio
async def test_generate_export_docx_treatment_summary(
    export_service: ExportService,
    mock_docx_generator
):
    """Test that DOCX generation routes to DOCX generator for treatment summary."""
    context = {
        "patient": {"name": "Test Patient"},
        "therapist": {"name": "Test Therapist"}
    }

    result = await export_service.generate_export(
        export_type="treatment_summary",
        format="docx",
        context=context
    )

    # Verify DOCX generator called
    mock_docx_generator.generate_treatment_summary.assert_called_once()

    # Verify result
    assert result == b"DOCX summary"


@pytest.mark.asyncio
async def test_generate_export_json_returns_json(
    export_service: ExportService
):
    """Test that JSON export returns serialized JSON bytes."""
    context = {
        "sessions": [{"id": "123"}],
        "therapist": {"name": "Test"}
    }

    result = await export_service.generate_export(
        export_type="session_notes",
        format="json",
        context=context
    )

    # Verify JSON bytes returned
    assert isinstance(result, bytes)

    # Verify can decode JSON
    import json
    decoded = json.loads(result.decode('utf-8'))
    assert decoded["therapist"]["name"] == "Test"
    assert len(decoded["sessions"]) == 1


@pytest.mark.asyncio
async def test_generate_export_unsupported_format_raises(
    export_service: ExportService
):
    """Test that unsupported format raises ValueError."""
    context = {"sessions": []}

    with pytest.raises(ValueError, match="Unsupported format: xml"):
        await export_service.generate_export(
            export_type="session_notes",
            format="xml",
            context=context
        )


@pytest.mark.asyncio
async def test_generate_export_csv_not_implemented_raises(
    export_service: ExportService
):
    """Test that CSV export raises ValueError (not yet implemented)."""
    context = {"sessions": []}

    with pytest.raises(ValueError, match="CSV export format not yet implemented"):
        await export_service.generate_export(
            export_type="session_notes",
            format="csv",
            context=context
        )


@pytest.mark.asyncio
async def test_generate_export_unsupported_docx_type_raises(
    export_service: ExportService
):
    """Test that unsupported DOCX export type raises ValueError."""
    context = {"sessions": []}

    with pytest.raises(ValueError, match="Unsupported DOCX export type"):
        await export_service.generate_export(
            export_type="unknown_type",
            format="docx",
            context=context
        )


# ============================================================================
# Serialization Tests
# ============================================================================

def test_serialize_user_converts_orm_to_dict(export_service: ExportService):
    """Test that _serialize_user converts User ORM to dict."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        first_name="Test",
        last_name="User",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )

    result = export_service._serialize_user(user)

    # Verify structure
    assert result["email"] == "test@example.com"
    assert result["first_name"] == "Test"
    assert result["last_name"] == "User"
    assert result["full_name"] == "Test User"
    assert result["role"] == "therapist"
    assert "id" in result


def test_serialize_user_handles_none(export_service: ExportService):
    """Test that _serialize_user returns None for None input."""
    result = export_service._serialize_user(None)
    assert result is None


def test_serialize_user_handles_full_name(export_service: ExportService):
    """Test that _serialize_user prioritizes full_name if present."""
    user = User(
        id=uuid4(),
        email="test@example.com",
        hashed_password="hashed",
        first_name="Test",
        last_name="User",
        full_name="Dr. Test User",  # Custom full name
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )

    result = export_service._serialize_user(user)
    assert result["full_name"] == "Dr. Test User"


def test_serialize_session_converts_orm_to_dict(export_service: ExportService):
    """Test that _serialize_session converts TherapySession ORM to dict."""
    session = TherapySession(
        id=uuid4(),
        session_date=datetime(2025, 12, 17, 10, 0, 0),
        duration_seconds=3600,
        transcript_text="Test transcript",
        extracted_notes={"key_topics": ["anxiety"]},
        therapist_summary="Summary",
        patient_summary="Patient summary",
        status="processed"
    )

    result = export_service._serialize_session(session)

    # Verify structure
    assert "id" in result
    assert result["session_date"] == datetime(2025, 12, 17, 10, 0, 0)
    assert result["duration_minutes"] == 60.0
    assert result["transcript_text"] == "Test transcript"
    assert result["extracted_notes"]["key_topics"] == ["anxiety"]
    assert result["status"] == "processed"


def test_serialize_session_handles_none_duration(export_service: ExportService):
    """Test that _serialize_session handles None duration_seconds."""
    session = TherapySession(
        id=uuid4(),
        session_date=datetime(2025, 12, 17, 10, 0, 0),
        duration_seconds=None,
        status="pending"
    )

    result = export_service._serialize_session(session)
    assert result["duration_minutes"] is None


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_end_to_end_session_notes_export(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions,
    mock_pdf_generator
):
    """
    Test complete end-to-end workflow for session notes export.

    This integration test verifies:
    1. Data gathering works correctly
    2. Data is properly serialized
    3. Export generation is called with correct data
    """
    sessions = therapist_with_sessions["sessions"]
    session_ids = [s.id for s in sessions]

    # Step 1: Gather data
    context = await export_service.gather_session_notes_data(
        session_ids=session_ids,
        db=async_test_db
    )

    # Step 2: Generate export
    result = await export_service.generate_export(
        export_type="session_notes",
        format="pdf",
        context=context
    )

    # Verify end-to-end flow
    assert result == b"PDF content"

    # Verify PDF generator was called with correct data
    mock_pdf_generator.generate_from_template.assert_called_once()
    call_args = mock_pdf_generator.generate_from_template.call_args

    # Verify template and context
    assert call_args[0][0] == "session_notes.html"
    passed_context = call_args[0][1]
    assert passed_context["session_count"] == 3
    assert len(passed_context["sessions"]) == 3


@pytest.mark.asyncio
async def test_end_to_end_progress_report_export(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions,
    mock_pdf_generator
):
    """
    Test complete end-to-end workflow for progress report export.

    This integration test verifies:
    1. Progress report data gathering
    2. Metrics calculation
    3. PDF generation with correct template
    """
    patient = therapist_with_sessions["patient"]
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()

    # Step 1: Gather data
    context = await export_service.gather_progress_report_data(
        patient_id=patient.id,
        start_date=start_date,
        end_date=end_date,
        db=async_test_db
    )

    # Step 2: Generate export
    result = await export_service.generate_export(
        export_type="progress_report",
        format="pdf",
        context=context
    )

    # Verify end-to-end flow
    assert result == b"PDF content"

    # Verify PDF generator was called with progress report template
    mock_pdf_generator.generate_from_template.assert_called_once()
    call_args = mock_pdf_generator.generate_from_template.call_args
    assert call_args[0][0] == "progress_report.html"


@pytest.mark.asyncio
async def test_end_to_end_json_export(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions
):
    """Test end-to-end JSON export workflow."""
    sessions = therapist_with_sessions["sessions"]
    session_ids = [s.id for s in sessions]

    # Gather data
    context = await export_service.gather_session_notes_data(
        session_ids=session_ids,
        db=async_test_db
    )

    # Generate JSON export
    result = await export_service.generate_export(
        export_type="session_notes",
        format="json",
        context=context
    )

    # Verify JSON structure
    import json
    decoded = json.loads(result.decode('utf-8'))

    assert decoded["session_count"] == 3
    assert len(decoded["sessions"]) == 3
    assert "therapist" in decoded
    assert "patients" in decoded


# ============================================================================
# Dependency Injection Test
# ============================================================================

def test_get_export_service_creates_instance(
    mock_pdf_generator,
    mock_docx_generator
):
    """Test that get_export_service factory creates ExportService instance."""
    service = get_export_service(
        pdf_generator=mock_pdf_generator,
        docx_generator=mock_docx_generator
    )

    assert isinstance(service, ExportService)
    assert service.pdf_generator == mock_pdf_generator
    assert service.docx_generator == mock_docx_generator


# ============================================================================
# Timeline Data Gathering Tests (Sub-feature 4: Export Processor)
# ============================================================================

@pytest.mark.asyncio
async def test_gather_timeline_data_success(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions
):
    """Test successful gathering of timeline data with 5 events."""
    from app.models.schemas import TimelineEventResponse, SessionTimelineResponse, TimelineSummaryResponse
    from unittest.mock import patch, MagicMock

    patient = therapist_with_sessions["patient"]
    therapist = therapist_with_sessions["therapist"]

    # Create 5 mock timeline events
    now = datetime.utcnow()
    mock_events = []
    for i in range(5):
        event = MagicMock(spec=TimelineEventResponse)
        event.id = uuid4()
        event.event_type = "milestone" if i % 2 == 0 else "note"
        event.event_subtype = None
        event.event_date = now - timedelta(days=i)
        event.title = f"Event {i+1}"
        event.description = f"Description for event {i+1}"
        event.importance = "milestone" if i == 0 else "normal"
        event.is_private = (i == 4)  # Make last event private
        event.metadata = {}
        mock_events.append(event)

    # Mock timeline service response
    mock_timeline_response = MagicMock(spec=SessionTimelineResponse)
    mock_timeline_response.events = mock_events

    # Mock summary response
    mock_summary = MagicMock(spec=TimelineSummaryResponse)
    mock_summary.total_sessions = 3
    mock_summary.first_session = now.date()
    mock_summary.last_session = now.date()
    mock_summary.milestones_achieved = 1
    mock_summary.events_by_type = {"milestone": 3, "note": 2}

    # Patch timeline service functions at their import location
    with patch('app.services.timeline.get_patient_timeline', new=AsyncMock(return_value=mock_timeline_response)):
        with patch('app.services.timeline.get_timeline_summary', new=AsyncMock(return_value=mock_summary)):
            # Gather timeline data
            result = await export_service.gather_timeline_data(
                patient_id=patient.id,
                start_date=None,
                end_date=None,
                event_types=None,
                include_private=True,
                db=async_test_db
            )

    # Assert: Returns dict with required keys
    assert "patient" in result
    assert "therapist" in result
    assert "events" in result
    assert "total_events" in result
    assert "summary" in result

    # Assert: events list contains 5 items
    assert len(result["events"]) == 5
    assert result["total_events"] == 5

    # Assert: Each event has required fields
    for event_data in result["events"]:
        assert "id" in event_data
        assert "event_type" in event_data
        assert "title" in event_data
        assert "description" in event_data
        assert "is_private" in event_data
        assert "event_date" in event_data
        assert "importance" in event_data

    # Verify patient and therapist data
    assert result["patient"]["email"] == "export.patient@test.com"
    assert result["therapist"]["email"] == "export.therapist@test.com"

    # Verify summary structure
    assert "total_sessions" in result["summary"]
    assert "first_session" in result["summary"]
    assert "last_session" in result["summary"]
    assert "milestones_achieved" in result["summary"]
    assert "events_by_type" in result["summary"]


@pytest.mark.asyncio
async def test_gather_timeline_data_with_date_filtering(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions
):
    """Test timeline data gathering with date range filtering."""
    from app.models.schemas import TimelineEventResponse, SessionTimelineResponse, TimelineSummaryResponse
    from unittest.mock import patch, MagicMock

    patient = therapist_with_sessions["patient"]

    # Set date range: day 10 to day 20
    base_date = datetime.utcnow()
    start_date = base_date - timedelta(days=20)
    end_date = base_date - timedelta(days=10)

    # Create 3 mock events within date range (days 12, 15, 18)
    mock_events = []
    for day_offset in [12, 15, 18]:
        event = MagicMock(spec=TimelineEventResponse)
        event.id = uuid4()
        event.event_type = "note"
        event.event_date = base_date - timedelta(days=day_offset)
        event.title = f"Event day {day_offset}"
        event.description = f"Event at day {day_offset}"
        event.importance = "normal"
        event.is_private = False
        event.event_subtype = None
        event.metadata = {}
        mock_events.append(event)

    # Mock timeline service response
    mock_timeline_response = MagicMock(spec=SessionTimelineResponse)
    mock_timeline_response.events = mock_events

    # Mock summary response
    mock_summary = MagicMock(spec=TimelineSummaryResponse)
    mock_summary.total_sessions = 0
    mock_summary.first_session = None
    mock_summary.last_session = None
    mock_summary.milestones_achieved = 0
    mock_summary.events_by_type = {"note": 3}

    # Patch timeline service functions at their import location
    with patch('app.services.timeline.get_patient_timeline', new=AsyncMock(return_value=mock_timeline_response)):
        with patch('app.services.timeline.get_timeline_summary', new=AsyncMock(return_value=mock_summary)):
            # Gather timeline data with date filtering
            result = await export_service.gather_timeline_data(
                patient_id=patient.id,
                start_date=start_date,
                end_date=end_date,
                event_types=None,
                include_private=True,
                db=async_test_db
            )

    # Assert: Returns only events within date range
    assert result["total_events"] == 3

    # Verify all returned events are within date range
    for event_data in result["events"]:
        event_date = event_data["event_date"]
        assert event_date >= start_date
        assert event_date <= end_date

    # Verify date filters are stored in result
    assert result["start_date"] == start_date
    assert result["end_date"] == end_date


@pytest.mark.asyncio
async def test_gather_timeline_data_include_private_false(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions
):
    """Test timeline data gathering excludes private events when include_private=False."""
    from app.models.schemas import TimelineEventResponse, SessionTimelineResponse, TimelineSummaryResponse
    from unittest.mock import patch, MagicMock

    patient = therapist_with_sessions["patient"]

    # Create 5 mock events: 3 non-private, 2 private
    now = datetime.utcnow()
    mock_events = []
    for i in range(5):
        is_private = (i in [1, 3])  # Events at index 1 and 3 are private
        event = MagicMock(spec=TimelineEventResponse)
        event.id = uuid4()
        event.event_type = "note"
        event.event_date = now - timedelta(days=i)
        event.title = f"Event {i+1}"
        event.description = f"Description {i+1}"
        event.importance = "normal"
        event.is_private = is_private
        event.event_subtype = None
        event.metadata = {}
        mock_events.append(event)

    # Mock timeline service response (returns all 5 events)
    mock_timeline_response = MagicMock(spec=SessionTimelineResponse)
    mock_timeline_response.events = mock_events

    # Mock summary response
    mock_summary = MagicMock(spec=TimelineSummaryResponse)
    mock_summary.total_sessions = 0
    mock_summary.first_session = None
    mock_summary.last_session = None
    mock_summary.milestones_achieved = 0
    mock_summary.events_by_type = {"note": 5}

    # Patch timeline service functions at their import location
    with patch('app.services.timeline.get_patient_timeline', new=AsyncMock(return_value=mock_timeline_response)):
        with patch('app.services.timeline.get_timeline_summary', new=AsyncMock(return_value=mock_summary)):
            # Gather timeline data with include_private=False
            result = await export_service.gather_timeline_data(
                patient_id=patient.id,
                start_date=None,
                end_date=None,
                event_types=None,
                include_private=False,
                db=async_test_db
            )

    # Assert: Returns only 3 events (non-private ones)
    assert result["total_events"] == 3
    assert len(result["events"]) == 3

    # Assert: All returned events have is_private=False
    for event_data in result["events"]:
        assert event_data["is_private"] == False

    # Verify event titles (should be events 1, 3, 5 - indices 0, 2, 4)
    titles = {event["title"] for event in result["events"]}
    assert "Event 1" in titles
    assert "Event 3" in titles
    assert "Event 5" in titles

    # Private events should not be present (Event 2 and Event 4)
    assert "Event 2" not in titles
    assert "Event 4" not in titles


@pytest.mark.asyncio
async def test_gather_timeline_data_patient_not_found(
    export_service: ExportService,
    async_test_db: AsyncSession
):
    """Test that ValueError is raised when patient not found."""
    fake_patient_id = uuid4()

    # Attempt to gather timeline data for non-existent patient
    with pytest.raises(ValueError, match="Patient .* not found"):
        await export_service.gather_timeline_data(
            patient_id=fake_patient_id,
            start_date=None,
            end_date=None,
            event_types=None,
            include_private=True,
            db=async_test_db
        )


@pytest.mark.asyncio
async def test_gather_timeline_data_empty_result(
    export_service: ExportService,
    async_test_db: AsyncSession,
    therapist_with_sessions
):
    """Test gathering timeline data when patient has zero events."""
    from app.models.schemas import SessionTimelineResponse, TimelineSummaryResponse
    from unittest.mock import patch, MagicMock

    patient = therapist_with_sessions["patient"]

    # Mock timeline service response with empty events list
    mock_timeline_response = MagicMock(spec=SessionTimelineResponse)
    mock_timeline_response.events = []  # No events

    # Mock summary response with zeros
    mock_summary = MagicMock(spec=TimelineSummaryResponse)
    mock_summary.total_sessions = 0
    mock_summary.first_session = None
    mock_summary.last_session = None
    mock_summary.milestones_achieved = 0
    mock_summary.events_by_type = {}

    # Patch timeline service functions at their import location
    with patch('app.services.timeline.get_patient_timeline', new=AsyncMock(return_value=mock_timeline_response)):
        with patch('app.services.timeline.get_timeline_summary', new=AsyncMock(return_value=mock_summary)):
            # Gather timeline data
            result = await export_service.gather_timeline_data(
                patient_id=patient.id,
                start_date=None,
                end_date=None,
                event_types=None,
                include_private=True,
                db=async_test_db
            )

    # Assert: Returns empty events list (not error)
    assert result["events"] == []
    assert result["total_events"] == 0

    # Assert: summary contains zeros for all counts
    assert result["summary"]["milestones_achieved"] == 0

    # Patient and therapist data should still be present
    assert result["patient"]["email"] == "export.patient@test.com"
    assert result["therapist"]["email"] == "export.therapist@test.com"
