# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for timeline service.

Tests cover:
1. get_patient_timeline - Retrieve timeline with filtering, pagination, and search
2. create_timeline_event - Create new timeline events with validation
3. get_timeline_event - Retrieve single event by ID
4. delete_timeline_event - Delete timeline events
5. get_timeline_summary - Calculate timeline summary statistics
6. get_timeline_chart_data - Generate chart visualization data
7. auto_generate_session_event - Automatically create session events

Edge cases tested:
- Empty timelines
- Cursor-based pagination boundaries
- Date range filtering
- Event type filtering
- Importance filtering
- Text search functionality
- Invalid patient validation
- Event not found scenarios
- Milestone detection (every 10th session)
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.timeline import (
    get_patient_timeline,
    create_timeline_event,
    get_timeline_event,
    delete_timeline_event,
    get_timeline_summary,
    get_timeline_chart_data,
    auto_generate_session_event
)
from app.models.schemas import (
    TimelineEventCreate,
    TimelineEventResponse,
    SessionTimelineResponse,
    TimelineImportance,
    TimelineSummaryResponse,
    TimelineChartDataResponse,
    UserRole,
    SessionStatus
)
from app.models.db_models import TimelineEvent, User, TherapySession, Patient
from app.models.analytics_models import SessionMetrics
from app.auth.utils import get_password_hash


# ============================================================================
# Fixtures for Timeline Tests
# ============================================================================

@pytest_asyncio.fixture
async def test_patient(async_test_db: AsyncSession):
    """
    Create a test patient user for timeline tests.

    Returns:
        User object with patient role
    """
    patient = User(
        email="timeline.patient@test.com",
        hashed_password=get_password_hash("PatientPass123!"),
        first_name="Timeline",
        last_name="Patient",
        full_name="Timeline Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(patient)
    await async_test_db.flush()
    await async_test_db.refresh(patient)
    return patient


@pytest_asyncio.fixture
async def test_therapist(async_test_db: AsyncSession):
    """
    Create a test therapist user for timeline tests.

    Returns:
        User object with therapist role
    """
    therapist = User(
        email="timeline.therapist@test.com",
        hashed_password=get_password_hash("TherapistPass123!"),
        first_name="Timeline",
        last_name="Therapist",
        full_name="Timeline Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=True
    )
    async_test_db.add(therapist)
    await async_test_db.flush()
    await async_test_db.refresh(therapist)
    return therapist


@pytest_asyncio.fixture
async def legacy_patient(async_test_db: AsyncSession, test_patient, test_therapist):
    """
    Create a legacy Patient record for TherapySession FK compatibility.

    Returns:
        Patient object linked to therapist
    """
    patient = Patient(
        name=test_patient.full_name,
        email=test_patient.email,
        therapist_id=test_therapist.id
    )
    async_test_db.add(patient)
    await async_test_db.flush()
    await async_test_db.refresh(patient)
    return patient


@pytest_asyncio.fixture
async def sample_timeline_events(async_test_db: AsyncSession, test_patient, test_therapist):
    """
    Create sample timeline events for testing.

    Creates 10 events with various types, dates, and importance levels:
    - 5 session events (2 milestones)
    - 2 clinical events
    - 2 goal events
    - 1 note event

    Returns:
        List of TimelineEvent objects
    """
    now = datetime.utcnow()
    events = []

    # Event 1: Session event (oldest, 60 days ago)
    event1 = TimelineEvent(
        patient_id=test_patient.id,
        therapist_id=test_therapist.id,
        event_type="session",
        event_date=now - timedelta(days=60),
        title="Session #1",
        description="Initial consultation and assessment",
        importance="normal",
        is_private=False,
        metadata={"session_number": 1, "topics": ["anxiety", "work stress"]}
    )
    events.append(event1)

    # Event 2: Clinical event (diagnosis)
    event2 = TimelineEvent(
        patient_id=test_patient.id,
        therapist_id=test_therapist.id,
        event_type="clinical",
        event_subtype="diagnosis",
        event_date=now - timedelta(days=55),
        title="Diagnosis: Generalized Anxiety Disorder",
        description="Initial diagnosis established after assessment",
        importance="high",
        is_private=True
    )
    events.append(event2)

    # Event 3: Goal event
    event3 = TimelineEvent(
        patient_id=test_patient.id,
        therapist_id=test_therapist.id,
        event_type="goal",
        event_subtype="created",
        event_date=now - timedelta(days=50),
        title="Goal: Reduce anxiety symptoms",
        description="Patient goal to manage work-related anxiety",
        importance="normal",
        is_private=False
    )
    events.append(event3)

    # Event 4: Session event (milestone - 10th session)
    event4 = TimelineEvent(
        patient_id=test_patient.id,
        therapist_id=test_therapist.id,
        event_type="session",
        event_date=now - timedelta(days=30),
        title="Session #10",
        description="Milestone: 10th session completed. Significant progress with coping strategies.",
        importance="milestone",
        is_private=False,
        metadata={"session_number": 10, "topics": ["progress review", "coping strategies"]}
    )
    events.append(event4)

    # Event 5: Clinical event (treatment plan update)
    event5 = TimelineEvent(
        patient_id=test_patient.id,
        therapist_id=test_therapist.id,
        event_type="clinical",
        event_subtype="treatment_plan",
        event_date=now - timedelta(days=25),
        title="Updated treatment plan",
        description="Incorporated mindfulness techniques",
        importance="high",
        is_private=True
    )
    events.append(event5)

    # Event 6: Session event
    event6 = TimelineEvent(
        patient_id=test_patient.id,
        therapist_id=test_therapist.id,
        event_type="session",
        event_date=now - timedelta(days=20),
        title="Session #15",
        description="Discussed work boundaries",
        importance="normal",
        is_private=False,
        metadata={"session_number": 15, "topics": ["boundaries", "work-life balance"]}
    )
    events.append(event6)

    # Event 7: Goal event (achieved)
    event7 = TimelineEvent(
        patient_id=test_patient.id,
        therapist_id=test_therapist.id,
        event_type="goal",
        event_subtype="achieved",
        event_date=now - timedelta(days=15),
        title="Goal achieved: Consistent sleep schedule",
        description="Patient successfully maintained sleep routine for 3 weeks",
        importance="high",
        is_private=False
    )
    events.append(event7)

    # Event 8: Session event (milestone - 20th session)
    event8 = TimelineEvent(
        patient_id=test_patient.id,
        therapist_id=test_therapist.id,
        event_type="session",
        event_date=now - timedelta(days=10),
        title="Session #20",
        description="Milestone: 20th session. Major improvements in anxiety management.",
        importance="milestone",
        is_private=False,
        metadata={"session_number": 20, "topics": ["milestone review", "future goals"]}
    )
    events.append(event8)

    # Event 9: Note event
    event9 = TimelineEvent(
        patient_id=test_patient.id,
        therapist_id=test_therapist.id,
        event_type="note",
        event_date=now - timedelta(days=5),
        title="Clinical note: Family involvement",
        description="Patient discussed family support system",
        importance="normal",
        is_private=True
    )
    events.append(event9)

    # Event 10: Session event (most recent)
    event10 = TimelineEvent(
        patient_id=test_patient.id,
        therapist_id=test_therapist.id,
        event_type="session",
        event_date=now - timedelta(days=1),
        title="Session #22",
        description="Recent session focusing on communication skills",
        importance="normal",
        is_private=False,
        metadata={"session_number": 22, "topics": ["communication", "assertiveness"]}
    )
    events.append(event10)

    # Add all events to database
    for event in events:
        async_test_db.add(event)

    await async_test_db.flush()

    # Refresh all events
    for event in events:
        await async_test_db.refresh(event)

    return events


@pytest_asyncio.fixture
async def sample_therapy_sessions(async_test_db: AsyncSession, legacy_patient, test_therapist):
    """
    Create sample therapy sessions for summary and chart data tests.

    Returns:
        List of TherapySession objects
    """
    now = datetime.utcnow()
    sessions = []

    # Create 5 sessions over last 3 months
    for i in range(5):
        session = TherapySession(
            patient_id=legacy_patient.id,
            therapist_id=test_therapist.id,
            session_date=now - timedelta(days=60 - (i * 12)),
            duration_seconds=3600,
            status=SessionStatus.processed.value,
            patient_summary=f"Session {i+1} summary: Patient discussed progress and challenges.",
            extracted_notes={
                "key_topics": ["anxiety", "progress"],
                "session_mood": "neutral"
            }
        )
        async_test_db.add(session)
        sessions.append(session)

    await async_test_db.flush()

    for session in sessions:
        await async_test_db.refresh(session)

    return sessions


@pytest_asyncio.fixture
async def sample_session_metrics(async_test_db: AsyncSession, legacy_patient):
    """
    Create sample session metrics for chart data tests.

    Returns:
        List of SessionMetrics objects
    """
    now = datetime.utcnow()
    metrics = []

    # Create metrics for last 3 months (monthly data points)
    for i in range(3):
        metric = SessionMetrics(
            session_id=uuid4(),  # Dummy session ID
            patient_id=legacy_patient.id,
            session_date=now - timedelta(days=60 - (i * 30)),
            mood_pre=3.0 + i * 0.5,
            mood_post=4.0 + i * 0.5
        )
        async_test_db.add(metric)
        metrics.append(metric)

    await async_test_db.flush()

    for metric in metrics:
        await async_test_db.refresh(metric)

    return metrics


# ============================================================================
# TestGetPatientTimeline
# ============================================================================

class TestGetPatientTimeline:
    """Test get_patient_timeline function with various filters and pagination"""

    @pytest.mark.asyncio
    async def test_get_patient_timeline_basic(
        self,
        async_test_db: AsyncSession,
        test_patient,
        sample_timeline_events
    ):
        """Test basic timeline retrieval without filters"""
        result = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            limit=20
        )

        assert isinstance(result, SessionTimelineResponse)
        assert len(result.events) == 10
        assert result.total_count == 10
        assert result.has_more is False
        assert result.next_cursor is None

        # Verify events are ordered by date DESC (newest first)
        for i in range(len(result.events) - 1):
            assert result.events[i].event_date >= result.events[i + 1].event_date

    @pytest.mark.asyncio
    async def test_get_patient_timeline_with_filters(
        self,
        async_test_db: AsyncSession,
        test_patient,
        sample_timeline_events
    ):
        """Test timeline with event_types, date range, and importance filtering"""
        # Filter by event_types (only sessions)
        result = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            event_types=["session"]
        )
        assert len(result.events) == 5
        assert all(e.event_type == "session" for e in result.events)

        # Filter by importance (only milestones)
        result = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            importance=TimelineImportance.milestone
        )
        assert len(result.events) == 2
        assert all(e.importance == TimelineImportance.milestone for e in result.events)

        # Filter by date range (last 30 days)
        now = datetime.utcnow()
        result = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            start_date=now - timedelta(days=30),
            end_date=now
        )
        assert len(result.events) == 6  # Events from last 30 days

        # Combined filters: session events in last 30 days
        result = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            event_types=["session"],
            start_date=now - timedelta(days=30)
        )
        assert len(result.events) == 3
        assert all(e.event_type == "session" for e in result.events)

    @pytest.mark.asyncio
    async def test_get_patient_timeline_pagination(
        self,
        async_test_db: AsyncSession,
        test_patient,
        sample_timeline_events
    ):
        """Test cursor-based pagination"""
        # Get first page (limit 3)
        page1 = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            limit=3
        )

        assert len(page1.events) == 3
        assert page1.has_more is True
        assert page1.next_cursor is not None
        assert page1.total_count == 10

        # Get second page using cursor
        page2 = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            limit=3,
            cursor=page1.next_cursor
        )

        assert len(page2.events) == 3
        assert page2.has_more is True
        assert page2.next_cursor is not None

        # Verify no overlap between pages
        page1_ids = {e.id for e in page1.events}
        page2_ids = {e.id for e in page2.events}
        assert page1_ids.isdisjoint(page2_ids)

        # Get last page
        page3 = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            limit=3,
            cursor=page2.next_cursor
        )

        assert len(page3.events) == 3
        assert page3.has_more is True

        page4 = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            limit=3,
            cursor=page3.next_cursor
        )

        assert len(page4.events) == 1  # Last event
        assert page4.has_more is False
        assert page4.next_cursor is None

    @pytest.mark.asyncio
    async def test_get_patient_timeline_search(
        self,
        async_test_db: AsyncSession,
        test_patient,
        sample_timeline_events
    ):
        """Test text search functionality"""
        # Search in title
        result = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            search="milestone"
        )
        assert len(result.events) == 2  # Two milestone sessions
        assert all("milestone" in e.title.lower() or "milestone" in (e.description or "").lower()
                   for e in result.events)

        # Search in description
        result = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            search="anxiety"
        )
        assert len(result.events) >= 2  # At least events mentioning anxiety

        # Search with no results
        result = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db,
            search="nonexistent term xyz123"
        )
        assert len(result.events) == 0
        assert result.total_count == 0

    @pytest.mark.asyncio
    async def test_get_patient_timeline_empty(self, async_test_db: AsyncSession, test_patient):
        """Test timeline retrieval for patient with no events"""
        result = await get_patient_timeline(
            patient_id=test_patient.id,
            db=async_test_db
        )

        assert isinstance(result, SessionTimelineResponse)
        assert len(result.events) == 0
        assert result.total_count == 0
        assert result.has_more is False
        assert result.next_cursor is None


# ============================================================================
# TestCreateTimelineEvent
# ============================================================================

class TestCreateTimelineEvent:
    """Test create_timeline_event function"""

    @pytest.mark.asyncio
    async def test_create_timeline_event(
        self,
        async_test_db: AsyncSession,
        test_patient,
        test_therapist
    ):
        """Test successful timeline event creation"""
        event_data = TimelineEventCreate(
            event_type="milestone",
            event_date=datetime.utcnow(),
            title="50th session completed",
            description="Patient has shown consistent progress over 50 sessions",
            importance=TimelineImportance.milestone,
            metadata={"session_number": 50}
        )

        result = await create_timeline_event(
            patient_id=test_patient.id,
            event_data=event_data,
            therapist_id=test_therapist.id,
            db=async_test_db
        )

        assert isinstance(result, TimelineEventResponse)
        assert result.patient_id == test_patient.id
        assert result.therapist_id == test_therapist.id
        assert result.event_type == "milestone"
        assert result.title == "50th session completed"
        assert result.importance == TimelineImportance.milestone
        assert result.metadata == {"session_number": 50}
        assert result.id is not None
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_create_timeline_event_invalid_patient(
        self,
        async_test_db: AsyncSession,
        test_therapist
    ):
        """Test event creation fails with invalid patient_id"""
        invalid_patient_id = uuid4()

        event_data = TimelineEventCreate(
            event_type="note",
            event_date=datetime.utcnow(),
            title="Test note",
            description="This should fail"
        )

        with pytest.raises(ValueError, match="does not exist"):
            await create_timeline_event(
                patient_id=invalid_patient_id,
                event_data=event_data,
                therapist_id=test_therapist.id,
                db=async_test_db
            )

    @pytest.mark.asyncio
    async def test_create_timeline_event_minimal(
        self,
        async_test_db: AsyncSession,
        test_patient
    ):
        """Test event creation with minimal required fields"""
        event_data = TimelineEventCreate(
            event_type="note",
            event_date=datetime.utcnow(),
            title="Quick note"
        )

        result = await create_timeline_event(
            patient_id=test_patient.id,
            event_data=event_data,
            therapist_id=None,  # Optional therapist
            db=async_test_db
        )

        assert result.patient_id == test_patient.id
        assert result.therapist_id is None
        assert result.event_type == "note"
        assert result.title == "Quick note"
        assert result.description is None
        assert result.importance == TimelineImportance.normal  # Default


# ============================================================================
# TestGetTimelineEvent
# ============================================================================

class TestGetTimelineEvent:
    """Test get_timeline_event function"""

    @pytest.mark.asyncio
    async def test_get_timeline_event(
        self,
        async_test_db: AsyncSession,
        sample_timeline_events
    ):
        """Test successful single event retrieval"""
        event = sample_timeline_events[0]

        result = await get_timeline_event(event.id, async_test_db)

        assert result is not None
        assert isinstance(result, TimelineEventResponse)
        assert result.id == event.id
        assert result.title == event.title
        assert result.event_type == event.event_type

    @pytest.mark.asyncio
    async def test_get_timeline_event_not_found(self, async_test_db: AsyncSession):
        """Test retrieval of non-existent event returns None"""
        nonexistent_id = uuid4()

        result = await get_timeline_event(nonexistent_id, async_test_db)

        assert result is None


# ============================================================================
# TestDeleteTimelineEvent
# ============================================================================

class TestDeleteTimelineEvent:
    """Test delete_timeline_event function"""

    @pytest.mark.asyncio
    async def test_delete_timeline_event(
        self,
        async_test_db: AsyncSession,
        test_patient,
        test_therapist
    ):
        """Test successful event deletion"""
        # Create an event to delete
        event = TimelineEvent(
            patient_id=test_patient.id,
            therapist_id=test_therapist.id,
            event_type="note",
            event_date=datetime.utcnow(),
            title="Temporary note",
            description="This will be deleted",
            importance="normal"
        )
        async_test_db.add(event)
        await async_test_db.flush()
        await async_test_db.refresh(event)

        event_id = event.id

        # Delete the event
        deleted = await delete_timeline_event(event_id, async_test_db)

        assert deleted is True

        # Verify event is deleted
        result = await get_timeline_event(event_id, async_test_db)
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_timeline_event_not_found(self, async_test_db: AsyncSession):
        """Test deletion of non-existent event returns False"""
        nonexistent_id = uuid4()

        deleted = await delete_timeline_event(nonexistent_id, async_test_db)

        assert deleted is False


# ============================================================================
# TestGetTimelineSummary
# ============================================================================

class TestGetTimelineSummary:
    """Test get_timeline_summary function"""

    @pytest.mark.asyncio
    async def test_get_timeline_summary(
        self,
        async_test_db: AsyncSession,
        test_patient,
        sample_timeline_events,
        sample_therapy_sessions
    ):
        """Test timeline summary calculation with events and sessions"""
        result = await get_timeline_summary(test_patient.id, async_test_db)

        assert isinstance(result, TimelineSummaryResponse)
        assert result.patient_id == test_patient.id
        assert result.total_events == 10
        assert result.total_sessions == 5

        # Verify events_by_type breakdown
        assert isinstance(result.events_by_type, dict)
        assert result.events_by_type.get("session", 0) == 5
        assert result.events_by_type.get("clinical", 0) == 2
        assert result.events_by_type.get("goal", 0) == 2
        assert result.events_by_type.get("note", 0) == 1

        # Verify milestones
        assert result.milestones_achieved == 2

        # Verify recent highlights
        assert isinstance(result.recent_highlights, list)
        assert len(result.recent_highlights) <= 3
        for highlight in result.recent_highlights:
            assert "id" in highlight
            assert "title" in highlight
            assert "event_date" in highlight

        # Verify session dates
        assert result.first_session is not None
        assert result.last_session is not None

    @pytest.mark.asyncio
    async def test_get_timeline_summary_no_data(
        self,
        async_test_db: AsyncSession,
        test_patient
    ):
        """Test summary for patient with no events or sessions"""
        result = await get_timeline_summary(test_patient.id, async_test_db)

        assert result.patient_id == test_patient.id
        assert result.total_events == 0
        assert result.total_sessions == 0
        assert result.events_by_type == {}
        assert result.milestones_achieved == 0
        assert result.recent_highlights == []
        assert result.first_session is None
        assert result.last_session is None


# ============================================================================
# TestGetTimelineChartData
# ============================================================================

class TestGetTimelineChartData:
    """Test get_timeline_chart_data function"""

    @pytest.mark.asyncio
    async def test_get_timeline_chart_data(
        self,
        async_test_db: AsyncSession,
        legacy_patient,
        sample_timeline_events,
        sample_therapy_sessions,
        sample_session_metrics
    ):
        """Test chart data generation with mood trends, session frequency, and milestones"""
        result = await get_timeline_chart_data(legacy_patient.id, async_test_db)

        assert isinstance(result, TimelineChartDataResponse)

        # Verify mood_trend data
        assert isinstance(result.mood_trend, list)
        assert len(result.mood_trend) == 3  # 3 months of data
        for data_point in result.mood_trend:
            assert "month" in data_point
            assert "avg_mood" in data_point
            assert isinstance(data_point["avg_mood"], (int, float))

        # Verify session_frequency data
        assert isinstance(result.session_frequency, list)
        for data_point in result.session_frequency:
            assert "month" in data_point
            assert "count" in data_point
            assert data_point["count"] >= 0

        # Verify milestones data
        assert isinstance(result.milestones, list)
        # Note: milestones come from timeline_events, not sessions
        # So we check the sample_timeline_events which have 2 milestones

    @pytest.mark.asyncio
    async def test_get_timeline_chart_data_empty(
        self,
        async_test_db: AsyncSession,
        legacy_patient
    ):
        """Test chart data generation with no data"""
        result = await get_timeline_chart_data(legacy_patient.id, async_test_db)

        assert isinstance(result, TimelineChartDataResponse)
        assert result.mood_trend == []
        assert result.session_frequency == []
        assert result.milestones == []


# ============================================================================
# TestAutoGenerateSessionEvent
# ============================================================================

class TestAutoGenerateSessionEvent:
    """Test auto_generate_session_event function"""

    @pytest.mark.asyncio
    async def test_auto_generate_session_event(
        self,
        async_test_db: AsyncSession,
        legacy_patient,
        test_therapist
    ):
        """Test automatic session event generation"""
        # Create a therapy session
        session = TherapySession(
            patient_id=legacy_patient.id,
            therapist_id=test_therapist.id,
            session_date=datetime.utcnow(),
            duration_seconds=3600,
            status=SessionStatus.processed.value,
            patient_summary="Patient made significant progress with anxiety management techniques.",
            extracted_notes={
                "key_topics": ["anxiety", "coping strategies"],
                "session_mood": "positive"
            }
        )
        async_test_db.add(session)
        await async_test_db.flush()
        await async_test_db.refresh(session)

        # Auto-generate timeline event
        result = await auto_generate_session_event(session, async_test_db)

        assert isinstance(result, TimelineEventResponse)
        assert result.patient_id == legacy_patient.id
        assert result.therapist_id == test_therapist.id
        assert result.event_type == "session"
        assert result.title == "Session #1"
        assert "anxiety management" in result.description
        assert result.importance == TimelineImportance.normal  # Not a milestone
        assert result.related_entity_type == "session"
        assert result.related_entity_id == session.id

        # Verify metadata
        assert result.metadata is not None
        assert result.metadata["session_id"] == str(session.id)
        assert result.metadata["duration_seconds"] == 3600
        assert "topics" in result.metadata
        assert result.metadata["topics"] == ["anxiety", "coping strategies"]
        assert result.metadata["mood"] == "positive"

    @pytest.mark.asyncio
    async def test_auto_generate_session_event_milestone(
        self,
        async_test_db: AsyncSession,
        legacy_patient,
        test_therapist
    ):
        """Test milestone detection for every 10th session"""
        # Create 10 prior sessions
        for i in range(9):
            session = TherapySession(
                patient_id=legacy_patient.id,
                therapist_id=test_therapist.id,
                session_date=datetime.utcnow() - timedelta(days=90 - (i * 10)),
                duration_seconds=3600,
                status=SessionStatus.processed.value,
                patient_summary=f"Session {i+1} summary"
            )
            async_test_db.add(session)

        await async_test_db.flush()

        # Create 10th session
        session_10 = TherapySession(
            patient_id=legacy_patient.id,
            therapist_id=test_therapist.id,
            session_date=datetime.utcnow(),
            duration_seconds=3600,
            status=SessionStatus.processed.value,
            patient_summary="Tenth session - milestone reached!"
        )
        async_test_db.add(session_10)
        await async_test_db.flush()
        await async_test_db.refresh(session_10)

        # Auto-generate timeline event for 10th session
        result = await auto_generate_session_event(session_10, async_test_db)

        assert result.title == "Session #10"
        assert result.importance == TimelineImportance.milestone  # Should be milestone

    @pytest.mark.asyncio
    async def test_auto_generate_session_event_no_summary(
        self,
        async_test_db: AsyncSession,
        legacy_patient,
        test_therapist
    ):
        """Test event generation for session without patient_summary"""
        session = TherapySession(
            patient_id=legacy_patient.id,
            therapist_id=test_therapist.id,
            session_date=datetime.utcnow(),
            duration_seconds=3600,
            status=SessionStatus.processed.value,
            patient_summary=None  # No summary
        )
        async_test_db.add(session)
        await async_test_db.flush()
        await async_test_db.refresh(session)

        result = await auto_generate_session_event(session, async_test_db)

        assert result.description == "Session completed"  # Default description
