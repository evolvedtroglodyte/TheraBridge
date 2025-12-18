# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for analytics service.

Tests cover:
1. calculate_overview_analytics - practice overview metrics
2. calculate_patient_progress - patient progress tracking
3. calculate_session_trends - session trends over time
4. calculate_topic_frequencies - topic analysis and insights

Edge cases tested:
- No patients/sessions
- Date range boundaries
- Unauthorized access (403 errors)
- Empty data sets
- Percentage calculations
- Trend detection
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services.analytics import (
    calculate_overview_analytics,
    calculate_patient_progress,
    calculate_session_trends,
    calculate_topic_frequencies
)
from app.models.schemas import (
    AnalyticsOverviewResponse,
    PatientProgressResponse,
    SessionTrendsResponse,
    TopicsResponse,
    SessionFrequency,
    MoodTrend,
    GoalStatus,
    UserRole,
    SessionStatus,
    MoodLevel
)
from app.models.db_models import User, TherapySession, Patient, TherapistPatient
from app.auth.utils import get_password_hash


# ============================================================================
# Fixtures for Analytics Tests
# ============================================================================

@pytest_asyncio.fixture
async def therapist_with_patients_and_sessions(async_test_db: AsyncSession):
    """
    Create a therapist with multiple patients and sessions for comprehensive testing.

    Structure:
    - 1 therapist
    - 3 patients (2 active, 1 inactive)
    - Multiple sessions across different time periods
    - Sessions with extracted_notes containing topics and moods

    Returns:
        Dict with therapist, patients, and sessions
    """
    # Note: async_test_db fixture manages transaction, so we just add and flush
    # Create therapist user
    therapist = User(
        email="analytics.therapist@test.com",
        hashed_password=get_password_hash("SecurePass123!"),
        first_name="Analytics",
        last_name="Therapist",
        full_name="Analytics Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=True
    )
    async_test_db.add(therapist)
    await async_test_db.flush()

    # Create patient users (for TherapistPatient junction)
    patient1_user = User(
        email="patient1@test.com",
        hashed_password=get_password_hash("PatientPass123!"),
        first_name="Patient",
        last_name="One",
        full_name="Patient One",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(patient1_user)

    patient2_user = User(
        email="patient2@test.com",
        hashed_password=get_password_hash("PatientPass123!"),
        first_name="Patient",
        last_name="Two",
        full_name="Patient Two",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(patient2_user)

    patient3_user = User(
        email="patient3@test.com",
        hashed_password=get_password_hash("PatientPass123!"),
        first_name="Patient",
        last_name="Three",
        full_name="Patient Three",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(patient3_user)
    await async_test_db.flush()

    # Create Patient records (legacy table)
    patient1 = Patient(
        name="Patient One",
        email="patient1@test.com",
        therapist_id=therapist.id
    )
    async_test_db.add(patient1)

    patient2 = Patient(
        name="Patient Two",
        email="patient2@test.com",
        therapist_id=therapist.id
    )
    async_test_db.add(patient2)

    patient3 = Patient(
        name="Patient Three",
        email="patient3@test.com",
        therapist_id=therapist.id
    )
    async_test_db.add(patient3)
    await async_test_db.flush()

    # Create TherapistPatient relationships (2 active, 1 inactive)
    rel1 = TherapistPatient(
        therapist_id=therapist.id,
        patient_id=patient1_user.id,
        is_active=True,
        relationship_type="primary"
    )
    async_test_db.add(rel1)

    rel2 = TherapistPatient(
        therapist_id=therapist.id,
        patient_id=patient2_user.id,
        is_active=True,
        relationship_type="primary"
    )
    async_test_db.add(rel2)

    rel3 = TherapistPatient(
        therapist_id=therapist.id,
        patient_id=patient3_user.id,
        is_active=False,  # Inactive patient
        relationship_type="primary",
        ended_at=datetime.utcnow() - timedelta(days=60)
    )
    async_test_db.add(rel3)
    await async_test_db.flush()

    # Create sessions across different time periods
    # Calculate calendar boundaries to prevent flaky tests
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())  # Monday this week
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)  # 1st of this month

    # Sessions this week (2 sessions) - relative to week_start
    session1 = TherapySession(
        patient_id=patient1.id,
        therapist_id=therapist.id,
        session_date=week_start + timedelta(days=1),  # Tuesday this week
        status=SessionStatus.processed.value,
        extracted_notes={
            "key_topics": ["anxiety", "work stress", "sleep issues"],
            "session_mood": "low",
            "action_items": [
                {"task": "Practice breathing", "category": "homework", "details": "Daily"}
            ]
        }
    )
    async_test_db.add(session1)

    session2 = TherapySession(
        patient_id=patient2.id,
        therapist_id=therapist.id,
        session_date=week_start + timedelta(days=2),  # Wednesday this week
        status=SessionStatus.processed.value,
        extracted_notes={
            "key_topics": ["relationships", "communication"],
            "session_mood": "neutral",
            "action_items": []
        }
    )
    async_test_db.add(session2)

    # Sessions this month (but not this week) - relative to month_start
    session3 = TherapySession(
        patient_id=patient1.id,
        therapist_id=therapist.id,
        session_date=month_start + timedelta(days=10),  # 10th of this month
        status=SessionStatus.processed.value,
        extracted_notes={
            "key_topics": ["anxiety", "relationships"],
            "session_mood": "neutral",
            "action_items": [
                {"task": "Journal daily", "category": "homework", "details": ""}
            ]
        }
    )
    async_test_db.add(session3)

    # Older sessions (within month, but not this week)
    # Ensure session is always in the past by using min of day 14 or (now - 2 days)
    session4_date = min(month_start + timedelta(days=14), now - timedelta(days=2))
    session4 = TherapySession(
        patient_id=patient2.id,
        therapist_id=therapist.id,
        session_date=session4_date,  # Earlier in this month, always in past
        status=SessionStatus.processed.value,
        extracted_notes={
            "key_topics": ["work stress", "boundaries"],
            "session_mood": "positive",
            "action_items": []
        }
    )
    async_test_db.add(session4)

    # Old session (inactive patient, > 30 days ago)
    session5 = TherapySession(
        patient_id=patient3.id,
        therapist_id=therapist.id,
        session_date=month_start - timedelta(days=90),  # 3 months ago
        status=SessionStatus.processed.value,
        extracted_notes={
            "key_topics": ["depression"],
            "session_mood": "very_low",
            "action_items": []
        }
    )
    async_test_db.add(session5)

    # Future session (upcoming)
    session6 = TherapySession(
        patient_id=patient1.id,
        therapist_id=therapist.id,
        session_date=now + timedelta(days=3),  # Keep relative to now for future
        status=SessionStatus.pending.value
    )
    async_test_db.add(session6)

    # Failed session (should be excluded from most metrics)
    session7 = TherapySession(
        patient_id=patient1.id,
        therapist_id=therapist.id,
        session_date=week_start + timedelta(days=3),  # Thursday this week
        status=SessionStatus.failed.value
    )
    async_test_db.add(session7)

    await async_test_db.flush()

    return {
        "therapist": therapist,
        "patients": [patient1, patient2, patient3],
        "patient_users": [patient1_user, patient2_user, patient3_user],
        "sessions": [session1, session2, session3, session4, session5, session6, session7]
    }


@pytest_asyncio.fixture
async def sample_sessions_with_analytics_data(async_test_db: AsyncSession, therapist_with_patients_and_sessions):
    """
    Sessions with comprehensive analytics data including topics, moods, and action items.

    This fixture is provided by therapist_with_patients_and_sessions above.
    """
    return therapist_with_patients_and_sessions


@pytest_asyncio.fixture
async def completed_sessions(async_test_db: AsyncSession):
    """
    Create a therapist with only completed/processed sessions for completion rate tests.

    Returns:
        Dict with therapist and sessions
    """
    therapist = User(
        email="completion.therapist@test.com",
        hashed_password=get_password_hash("SecurePass123!"),
        first_name="Completion",
        last_name="Therapist",
        full_name="Completion Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=True
    )
    async_test_db.add(therapist)
    await async_test_db.flush()

    patient_user = User(
        email="completion.patient@test.com",
        hashed_password=get_password_hash("PatientPass123!"),
        first_name="Test",
        last_name="Patient",
        full_name="Test Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(patient_user)
    await async_test_db.flush()

    patient = Patient(
        name="Test Patient",
        email="completion.patient@test.com",
        therapist_id=therapist.id
    )
    async_test_db.add(patient)
    await async_test_db.flush()

    # Create 8 processed sessions and 2 pending sessions
    now = datetime.utcnow()
    sessions = []

    for i in range(8):
        session = TherapySession(
            patient_id=patient.id,
            therapist_id=therapist.id,
            session_date=now - timedelta(days=i),
            status=SessionStatus.processed.value
        )
        async_test_db.add(session)
        sessions.append(session)

    for i in range(2):
        session = TherapySession(
            patient_id=patient.id,
            therapist_id=therapist.id,
            session_date=now - timedelta(days=i + 8),
            status=SessionStatus.transcribing.value
        )
        async_test_db.add(session)
        sessions.append(session)

    await async_test_db.flush()

    return {
        "therapist": therapist,
        "patient": patient,
        "sessions": sessions
    }


# ============================================================================
# TestCalculateOverviewAnalytics
# ============================================================================

class TestCalculateOverviewAnalytics:
    """Test overview analytics calculation"""

    @pytest.mark.asyncio
    async def test_overview_with_active_patients(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test overview calculation with active patients and sessions"""
        therapist = therapist_with_patients_and_sessions["therapist"]

        result = await calculate_overview_analytics(therapist.id, async_test_db)

        assert isinstance(result, AnalyticsOverviewResponse)
        assert result.total_patients == 2  # 2 active relationships
        assert result.active_patients == 2  # 2 patients with sessions in last 30 days
        assert result.sessions_this_week == 2  # session1 and session2
        assert result.sessions_this_month == 4  # session1, 2, 3, 4
        assert result.upcoming_sessions == 1  # session6
        # 5 processed out of 6 non-failed sessions
        assert result.completion_rate == pytest.approx(5/6, rel=0.01)

    @pytest.mark.asyncio
    async def test_overview_with_no_patients(self, async_test_db: AsyncSession):
        """Test overview calculation with therapist who has no patients"""
        # Create therapist with no patients
        therapist = User(
            email="empty.therapist@test.com",
            hashed_password=get_password_hash("SecurePass123!"),
            first_name="Empty",
            last_name="Therapist",
            full_name="Empty Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=True
        )
        async_test_db.add(therapist)
        await async_test_db.flush()

        result = await calculate_overview_analytics(therapist.id, async_test_db)

        assert isinstance(result, AnalyticsOverviewResponse)
        assert result.total_patients == 0
        assert result.active_patients == 0
        assert result.sessions_this_week == 0
        assert result.sessions_this_month == 0
        assert result.upcoming_sessions == 0
        assert result.completion_rate == 0.0

    @pytest.mark.asyncio
    async def test_overview_with_no_sessions(self, async_test_db: AsyncSession):
        """Test overview with patients but no sessions"""
        therapist = User(
            email="nosessions.therapist@test.com",
            hashed_password=get_password_hash("SecurePass123!"),
            first_name="NoSessions",
            last_name="Therapist",
            full_name="NoSessions Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=True
        )
        async_test_db.add(therapist)
        await async_test_db.flush()

        patient_user = User(
            email="nosessions.patient@test.com",
            hashed_password=get_password_hash("PatientPass123!"),
            first_name="Test",
            last_name="Patient",
            full_name="Test Patient",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(patient_user)
        await async_test_db.flush()

        # Create active relationship
        rel = TherapistPatient(
            therapist_id=therapist.id,
            patient_id=patient_user.id,
            is_active=True
        )
        async_test_db.add(rel)
        await async_test_db.flush()

        result = await calculate_overview_analytics(therapist.id, async_test_db)

        assert result.total_patients == 1  # Has 1 patient relationship
        assert result.active_patients == 0  # But no sessions in last 30 days
        assert result.sessions_this_week == 0
        assert result.sessions_this_month == 0
        assert result.upcoming_sessions == 0
        assert result.completion_rate == 0.0

    @pytest.mark.asyncio
    async def test_overview_completion_rate(
        self,
        async_test_db: AsyncSession,
        completed_sessions
    ):
        """Test completion rate calculation accuracy"""
        therapist = completed_sessions["therapist"]

        result = await calculate_overview_analytics(therapist.id, async_test_db)

        # 8 processed out of 10 non-failed sessions = 0.8
        assert result.completion_rate == pytest.approx(0.8, rel=0.01)

    @pytest.mark.asyncio
    async def test_overview_date_ranges(self, async_test_db: AsyncSession):
        """Test that week and month boundaries are calculated correctly"""
        therapist = User(
            email="dateranges.therapist@test.com",
            hashed_password=get_password_hash("SecurePass123!"),
            first_name="DateRanges",
            last_name="Therapist",
            full_name="DateRanges Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=True
        )
        async_test_db.add(therapist)
        await async_test_db.flush()

        patient_user = User(
            email="dateranges.patient@test.com",
            hashed_password=get_password_hash("PatientPass123!"),
            first_name="Test",
            last_name="Patient",
            full_name="Test Patient",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(patient_user)
        await async_test_db.flush()

        patient = Patient(
            name="Test Patient",
            email="dateranges.patient@test.com",
            therapist_id=therapist.id
        )
        async_test_db.add(patient)
        await async_test_db.flush()

        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())  # Monday of current week
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Session exactly at week start (should be included)
        session1 = TherapySession(
            patient_id=patient.id,
            therapist_id=therapist.id,
            session_date=week_start,
            status=SessionStatus.processed.value
        )
        async_test_db.add(session1)

        # Session exactly at month start (should be included)
        session2 = TherapySession(
            patient_id=patient.id,
            therapist_id=therapist.id,
            session_date=month_start,
            status=SessionStatus.processed.value
        )
        async_test_db.add(session2)

        # Session 1 second before week start (should be excluded from week)
        session3 = TherapySession(
            patient_id=patient.id,
            therapist_id=therapist.id,
            session_date=week_start - timedelta(seconds=1),
            status=SessionStatus.processed.value
        )
        async_test_db.add(session3)

        await async_test_db.flush()

        result = await calculate_overview_analytics(therapist.id, async_test_db)

        # Verify boundary handling
        assert result.sessions_this_week >= 1  # At least session1
        assert result.sessions_this_month >= 2  # At least session1 and session2


# ============================================================================
# TestCalculatePatientProgress
# ============================================================================

class TestCalculatePatientProgress:
    """Test patient progress calculation"""

    @pytest.mark.asyncio
    async def test_patient_progress_success(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test patient progress calculation with valid data"""
        therapist = therapist_with_patients_and_sessions["therapist"]
        patients = therapist_with_patients_and_sessions["patients"]
        patient1 = patients[0]  # Get Patient object from legacy table

        result = await calculate_patient_progress(
            patient1.id,  # Use Patient ID, not User ID
            therapist.id,
            async_test_db
        )

        assert isinstance(result, PatientProgressResponse)
        assert result.patient_id == patient1.id
        assert result.total_sessions > 0
        assert isinstance(result.first_session_date, str)
        assert isinstance(result.last_session_date, str)
        assert isinstance(result.session_frequency, SessionFrequency)
        assert isinstance(result.mood_trend, MoodTrend)
        assert isinstance(result.goals, GoalStatus)

    @pytest.mark.asyncio
    async def test_patient_progress_unauthorized(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test that unauthorized access raises 403 HTTPException"""
        therapist = therapist_with_patients_and_sessions["therapist"]

        # Create a different therapist who doesn't have access
        unauthorized_therapist = User(
            email="unauthorized@test.com",
            hashed_password=get_password_hash("SecurePass123!"),
            first_name="Unauthorized",
            last_name="Therapist",
            full_name="Unauthorized Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=True
        )
        async_test_db.add(unauthorized_therapist)
        await async_test_db.flush()

        patients = therapist_with_patients_and_sessions["patients"]
        patient1 = patients[0]  # Get Patient object from legacy table

        # Should raise 403 HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await calculate_patient_progress(
                patient1.id,  # Use Patient ID, not User ID
                unauthorized_therapist.id,
                async_test_db
            )

        assert exc_info.value.status_code == 403
        assert "not assigned" in exc_info.value.detail.lower()

    @pytest.mark.asyncio
    async def test_patient_progress_no_sessions(self, async_test_db: AsyncSession):
        """Test patient progress with patient who has no sessions"""
        therapist = User(
            email="progress.therapist@test.com",
            hashed_password=get_password_hash("SecurePass123!"),
            first_name="Progress",
            last_name="Therapist",
            full_name="Progress Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=True
        )
        async_test_db.add(therapist)
        await async_test_db.flush()

        patient_user = User(
            email="progress.patient@test.com",
            hashed_password=get_password_hash("PatientPass123!"),
            first_name="Test",
            last_name="Patient",
            full_name="Test Patient",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(patient_user)
        await async_test_db.flush()

        # Create Patient record (legacy table)
        patient = Patient(
            name="Test Patient",
            email="progress.patient@test.com",
            therapist_id=therapist.id
        )
        async_test_db.add(patient)
        await async_test_db.flush()

        # Create active relationship
        rel = TherapistPatient(
            therapist_id=therapist.id,
            patient_id=patient_user.id,
            is_active=True
        )
        async_test_db.add(rel)
        await async_test_db.flush()

        result = await calculate_patient_progress(
            patient.id,  # Use Patient ID from legacy table, not User ID
            therapist.id,
            async_test_db
        )

        assert result.total_sessions == 0
        assert result.first_session_date == "N/A"
        assert result.last_session_date == "N/A"
        assert result.session_frequency.weekly_average == 0.0
        assert result.session_frequency.trend == "stable"
        assert result.mood_trend.trend == "stable"
        assert len(result.mood_trend.data) == 0
        assert result.goals.total == 0

    @pytest.mark.asyncio
    async def test_patient_progress_mood_trend(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test mood trend calculation from session data"""
        therapist = therapist_with_patients_and_sessions["therapist"]
        patients = therapist_with_patients_and_sessions["patients"]
        patient1 = patients[0]  # Get Patient object from legacy table

        result = await calculate_patient_progress(
            patient1.id,  # Use Patient ID, not User ID
            therapist.id,
            async_test_db
        )

        # Should have mood trend data
        assert isinstance(result.mood_trend, MoodTrend)
        assert result.mood_trend.trend in ["improving", "declining", "stable"]
        # Each mood data point should have valid structure
        for data_point in result.mood_trend.data:
            assert hasattr(data_point, "date")
            assert hasattr(data_point, "avg_pre")
            assert hasattr(data_point, "avg_post")
            assert 1.0 <= data_point.avg_pre <= 5.0
            assert 1.0 <= data_point.avg_post <= 5.0

    @pytest.mark.asyncio
    async def test_patient_progress_session_frequency(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test session frequency calculation and trend detection"""
        therapist = therapist_with_patients_and_sessions["therapist"]
        patients = therapist_with_patients_and_sessions["patients"]
        patient1 = patients[0]  # Get Patient object from legacy table

        result = await calculate_patient_progress(
            patient1.id,  # Use Patient ID, not User ID
            therapist.id,
            async_test_db
        )

        assert isinstance(result.session_frequency, SessionFrequency)
        assert result.session_frequency.weekly_average >= 0.0
        assert result.session_frequency.trend in ["stable", "increasing", "decreasing"]


# ============================================================================
# TestCalculateSessionTrends
# ============================================================================

class TestCalculateSessionTrends:
    """Test session trends calculation"""

    @pytest.mark.asyncio
    async def test_session_trends_weekly(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test weekly session trends aggregation"""
        therapist = therapist_with_patients_and_sessions["therapist"]

        result = await calculate_session_trends(
            therapist.id,
            "week",
            None,
            async_test_db
        )

        assert isinstance(result, SessionTrendsResponse)
        assert result.period == "week"
        assert isinstance(result.data, list)
        # Each data point should have proper structure
        for data_point in result.data:
            assert hasattr(data_point, "label")
            assert hasattr(data_point, "sessions")
            assert hasattr(data_point, "unique_patients")
            assert "Week" in data_point.label
            assert data_point.sessions >= 0
            assert data_point.unique_patients >= 0

    @pytest.mark.asyncio
    async def test_session_trends_monthly(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test monthly session trends aggregation"""
        therapist = therapist_with_patients_and_sessions["therapist"]

        result = await calculate_session_trends(
            therapist.id,
            "month",
            None,
            async_test_db
        )

        assert isinstance(result, SessionTrendsResponse)
        assert result.period == "month"
        assert isinstance(result.data, list)
        # Labels should be month names
        for data_point in result.data:
            # Month label format: "Jan", "Feb", etc.
            assert len(data_point.label) == 3 or len(data_point.label) > 3

    @pytest.mark.asyncio
    async def test_session_trends_quarterly(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test quarterly session trends aggregation"""
        therapist = therapist_with_patients_and_sessions["therapist"]

        result = await calculate_session_trends(
            therapist.id,
            "quarter",
            None,
            async_test_db
        )

        assert isinstance(result, SessionTrendsResponse)
        assert result.period == "quarter"
        assert isinstance(result.data, list)
        # Labels should contain Q1, Q2, Q3, or Q4
        for data_point in result.data:
            assert "Q" in data_point.label

    @pytest.mark.asyncio
    async def test_session_trends_yearly(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test yearly session trends aggregation"""
        therapist = therapist_with_patients_and_sessions["therapist"]

        result = await calculate_session_trends(
            therapist.id,
            "year",
            None,
            async_test_db
        )

        assert isinstance(result, SessionTrendsResponse)
        assert result.period == "year"
        assert isinstance(result.data, list)
        # Labels should be years (4 digits)
        for data_point in result.data:
            assert len(data_point.label) == 4
            assert data_point.label.isdigit()

    @pytest.mark.asyncio
    async def test_session_trends_with_patient_filter(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test session trends filtered by specific patient"""
        therapist = therapist_with_patients_and_sessions["therapist"]
        patient_user = therapist_with_patients_and_sessions["patient_users"][0]
        patients = therapist_with_patients_and_sessions["patients"]
        patient1 = patients[0]  # Get the Patient object

        result = await calculate_session_trends(
            therapist.id,
            "month",
            patient1.id,  # Filter by patient1
            async_test_db
        )

        assert isinstance(result, SessionTrendsResponse)
        assert result.period == "month"
        # unique_patients should always be 1 or 0 when filtering by patient
        for data_point in result.data:
            assert data_point.unique_patients <= 1


# ============================================================================
# TestCalculateTopicFrequencies
# ============================================================================

class TestCalculateTopicFrequencies:
    """Test topic frequency analysis"""

    @pytest.mark.asyncio
    async def test_topic_frequencies_success(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test topic frequency calculation with valid data"""
        therapist = therapist_with_patients_and_sessions["therapist"]

        result = await calculate_topic_frequencies(therapist.id, async_test_db)

        assert isinstance(result, TopicsResponse)
        assert isinstance(result.topics, list)
        # Should have topics from sessions
        assert len(result.topics) > 0
        # Each topic should have proper structure
        for topic in result.topics:
            assert hasattr(topic, "name")
            assert hasattr(topic, "count")
            assert hasattr(topic, "percentage")
            assert topic.count > 0
            assert 0.0 < topic.percentage <= 1.0

    @pytest.mark.asyncio
    async def test_topic_frequencies_with_no_topics(self, async_test_db: AsyncSession):
        """Test topic frequencies when no sessions have topics"""
        therapist = User(
            email="notopics.therapist@test.com",
            hashed_password=get_password_hash("SecurePass123!"),
            first_name="NoTopics",
            last_name="Therapist",
            full_name="NoTopics Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=True
        )
        async_test_db.add(therapist)
        await async_test_db.flush()

        patient_user = User(
            email="notopics.patient@test.com",
            hashed_password=get_password_hash("PatientPass123!"),
            first_name="Test",
            last_name="Patient",
            full_name="Test Patient",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(patient_user)
        await async_test_db.flush()

        patient = Patient(
            name="Test Patient",
            email="notopics.patient@test.com",
            therapist_id=therapist.id
        )
        async_test_db.add(patient)
        await async_test_db.flush()

        # Create session without extracted_notes
        session = TherapySession(
            patient_id=patient.id,
            therapist_id=therapist.id,
            session_date=datetime.utcnow(),
            status=SessionStatus.processed.value
        )
        async_test_db.add(session)
        await async_test_db.flush()

        result = await calculate_topic_frequencies(therapist.id, async_test_db)

        assert isinstance(result, TopicsResponse)
        assert len(result.topics) == 0

    @pytest.mark.asyncio
    async def test_topic_frequencies_percentages(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test that topic percentages sum correctly"""
        therapist = therapist_with_patients_and_sessions["therapist"]

        result = await calculate_topic_frequencies(therapist.id, async_test_db)

        # All percentages should sum to approximately 1.0
        total_percentage = sum(topic.percentage for topic in result.topics)
        assert total_percentage == pytest.approx(1.0, rel=0.01)

        # Each percentage should be in valid range
        for topic in result.topics:
            assert 0.0 < topic.percentage <= 1.0

    @pytest.mark.asyncio
    async def test_topic_frequencies_sorting(
        self,
        async_test_db: AsyncSession,
        therapist_with_patients_and_sessions
    ):
        """Test that topics are sorted by count descending"""
        therapist = therapist_with_patients_and_sessions["therapist"]

        result = await calculate_topic_frequencies(therapist.id, async_test_db)

        # Verify descending order by count
        counts = [topic.count for topic in result.topics]
        assert counts == sorted(counts, reverse=True)

        # Verify most frequent topic is first
        if len(result.topics) > 1:
            assert result.topics[0].count >= result.topics[1].count
