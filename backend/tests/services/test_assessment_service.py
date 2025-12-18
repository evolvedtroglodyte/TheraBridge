"""
Tests for assessment service - assessment tracking and severity classification.

This module tests:
- Assessment recording with severity calculation
- PHQ-9, GAD-7, and BDI-II severity classification formulas
- Assessment history retrieval and filtering
- Date range and assessment type filtering
- Assessment due date calculations
- Latest assessments retrieval
- JSONB subscores handling
- Clinical accuracy of severity classifications
"""
import pytest
import pytest_asyncio
from datetime import date, datetime, timedelta
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.assessment_service import (
    record_assessment,
    calculate_severity,
    get_assessment_history,
    check_assessments_due,
    get_latest_assessments,
    ASSESSMENT_FREQUENCIES
)
from app.models.tracking_models import AssessmentScore
from app.schemas.assessment_schemas import (
    AssessmentScoreCreate,
    AssessmentType,
    Severity
)


# ============================================================================
# Severity Classification Tests - PHQ-9
# ============================================================================

def test_calculate_severity_phq9_minimal():
    """Test PHQ-9 severity classification for minimal range (0-4)"""
    # Boundary values for minimal
    assert calculate_severity("PHQ-9", 0) == Severity.minimal
    assert calculate_severity("PHQ-9", 4) == Severity.minimal


def test_calculate_severity_phq9_mild():
    """Test PHQ-9 severity classification for mild range (5-9)"""
    assert calculate_severity("PHQ-9", 5) == Severity.mild
    assert calculate_severity("PHQ-9", 7) == Severity.mild
    assert calculate_severity("PHQ-9", 9) == Severity.mild


def test_calculate_severity_phq9_moderate():
    """Test PHQ-9 severity classification for moderate range (10-14)"""
    assert calculate_severity("PHQ-9", 10) == Severity.moderate
    assert calculate_severity("PHQ-9", 12) == Severity.moderate
    assert calculate_severity("PHQ-9", 14) == Severity.moderate


def test_calculate_severity_phq9_moderately_severe():
    """Test PHQ-9 severity classification for moderately severe range (15-19)"""
    assert calculate_severity("PHQ-9", 15) == Severity.moderately_severe
    assert calculate_severity("PHQ-9", 17) == Severity.moderately_severe
    assert calculate_severity("PHQ-9", 19) == Severity.moderately_severe


def test_calculate_severity_phq9_severe():
    """Test PHQ-9 severity classification for severe range (20+)"""
    assert calculate_severity("PHQ-9", 20) == Severity.severe
    assert calculate_severity("PHQ-9", 25) == Severity.severe
    assert calculate_severity("PHQ-9", 27) == Severity.severe


# ============================================================================
# Severity Classification Tests - GAD-7
# ============================================================================

def test_calculate_severity_gad7_minimal():
    """Test GAD-7 severity classification for minimal range (0-4)"""
    assert calculate_severity("GAD-7", 0) == Severity.minimal
    assert calculate_severity("GAD-7", 2) == Severity.minimal
    assert calculate_severity("GAD-7", 4) == Severity.minimal


def test_calculate_severity_gad7_mild():
    """Test GAD-7 severity classification for mild range (5-9)"""
    assert calculate_severity("GAD-7", 5) == Severity.mild
    assert calculate_severity("GAD-7", 7) == Severity.mild
    assert calculate_severity("GAD-7", 9) == Severity.mild


def test_calculate_severity_gad7_moderate():
    """Test GAD-7 severity classification for moderate range (10-14)"""
    assert calculate_severity("GAD-7", 10) == Severity.moderate
    assert calculate_severity("GAD-7", 12) == Severity.moderate
    assert calculate_severity("GAD-7", 14) == Severity.moderate


def test_calculate_severity_gad7_severe():
    """Test GAD-7 severity classification for severe range (15+)"""
    assert calculate_severity("GAD-7", 15) == Severity.severe
    assert calculate_severity("GAD-7", 18) == Severity.severe
    assert calculate_severity("GAD-7", 21) == Severity.severe


# ============================================================================
# Severity Classification Tests - BDI-II
# ============================================================================

def test_calculate_severity_bdi_minimal():
    """Test BDI-II severity classification for minimal range (0-13)"""
    assert calculate_severity("BDI-II", 0) == Severity.minimal
    assert calculate_severity("BDI-II", 7) == Severity.minimal
    assert calculate_severity("BDI-II", 13) == Severity.minimal


def test_calculate_severity_bdi_mild():
    """Test BDI-II severity classification for mild range (14-19)"""
    assert calculate_severity("BDI-II", 14) == Severity.mild
    assert calculate_severity("BDI-II", 16) == Severity.mild
    assert calculate_severity("BDI-II", 19) == Severity.mild


def test_calculate_severity_bdi_moderate():
    """Test BDI-II severity classification for moderate range (20-28)"""
    assert calculate_severity("BDI-II", 20) == Severity.moderate
    assert calculate_severity("BDI-II", 24) == Severity.moderate
    assert calculate_severity("BDI-II", 28) == Severity.moderate


def test_calculate_severity_bdi_severe():
    """Test BDI-II severity classification for severe range (29+)"""
    assert calculate_severity("BDI-II", 29) == Severity.severe
    assert calculate_severity("BDI-II", 35) == Severity.severe
    assert calculate_severity("BDI-II", 63) == Severity.severe


# ============================================================================
# Severity Classification Tests - Unsupported Types
# ============================================================================

def test_calculate_severity_bai_returns_none():
    """Test that BAI returns None (no standardized severity ranges)"""
    assert calculate_severity("BAI", 10) is None
    assert calculate_severity("BAI", 30) is None


def test_calculate_severity_pcl5_returns_none():
    """Test that PCL-5 returns None (no standardized severity ranges)"""
    assert calculate_severity("PCL-5", 20) is None
    assert calculate_severity("PCL-5", 50) is None


def test_calculate_severity_audit_returns_none():
    """Test that AUDIT returns None (no standardized severity ranges)"""
    assert calculate_severity("AUDIT", 5) is None
    assert calculate_severity("AUDIT", 15) is None


def test_calculate_severity_unknown_type_returns_none():
    """Test that unknown assessment types return None"""
    assert calculate_severity("UNKNOWN", 10) is None


# ============================================================================
# Assessment Recording Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_record_assessment_basic(async_test_db: AsyncSession, therapist_user, sample_patient):
    """Test basic assessment recording with automatic severity calculation"""
    # Create assessment data (GAD-7 with score of 8 = mild)
    assessment_data = AssessmentScoreCreate(
        assessment_type=AssessmentType.GAD7,
        score=8,
        administered_date=date(2024, 3, 10)
    )

    # Record assessment
    result = await record_assessment(
        patient_id=sample_patient.id,
        assessment_data=assessment_data,
        db=async_test_db,
        administered_by=therapist_user.id
    )

    # Verify response
    assert result.id is not None
    assert result.patient_id == sample_patient.id
    assert result.assessment_type == AssessmentType.GAD7
    assert result.score == 8
    assert result.severity == Severity.mild  # Automatically calculated
    assert result.administered_date == date(2024, 3, 10)
    assert result.administered_by == therapist_user.id


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_record_assessment_with_subscores(async_test_db: AsyncSession, therapist_user, sample_patient):
    """Test assessment recording with JSONB subscores"""
    subscores_data = {
        "feeling_nervous": 2,
        "cant_stop_worrying": 1,
        "worrying_too_much": 2,
        "trouble_relaxing": 2,
        "restless": 1,
        "easily_annoyed": 0,
        "feeling_afraid": 0
    }

    assessment_data = AssessmentScoreCreate(
        assessment_type=AssessmentType.GAD7,
        score=8,
        subscores=subscores_data,
        administered_date=date.today()
    )

    result = await record_assessment(
        patient_id=sample_patient.id,
        assessment_data=assessment_data,
        db=async_test_db
    )

    # Verify subscores stored correctly
    assert result.subscores == subscores_data
    assert result.subscores["feeling_nervous"] == 2
    assert result.subscores["easily_annoyed"] == 0


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_record_assessment_with_manual_severity(async_test_db: AsyncSession, sample_patient):
    """Test that manually provided severity overrides automatic calculation"""
    # Score of 8 would normally be "mild", but we'll override with "moderate"
    assessment_data = AssessmentScoreCreate(
        assessment_type=AssessmentType.GAD7,
        score=8,
        severity=Severity.moderate,  # Manual override
        administered_date=date.today()
    )

    result = await record_assessment(
        patient_id=sample_patient.id,
        assessment_data=assessment_data,
        db=async_test_db
    )

    # Verify manual severity is preserved
    assert result.severity == Severity.moderate


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_record_assessment_with_goal_link(
    async_test_db: AsyncSession,
    sample_patient,
    sample_goal,
    therapist_user
):
    """Test assessment recording linked to a treatment goal"""
    assessment_data = AssessmentScoreCreate(
        assessment_type=AssessmentType.GAD7,
        score=14,
        goal_id=sample_goal.id,
        administered_date=date.today(),
        notes="Baseline assessment for anxiety goal"
    )

    result = await record_assessment(
        patient_id=sample_patient.id,
        assessment_data=assessment_data,
        db=async_test_db,
        administered_by=therapist_user.id
    )

    # Verify goal linkage
    assert result.goal_id == sample_goal.id
    assert result.notes == "Baseline assessment for anxiety goal"


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_record_assessment_without_severity_for_bai(
    async_test_db: AsyncSession,
    sample_patient
):
    """Test that assessment types without severity ranges (BAI) don't get severity"""
    assessment_data = AssessmentScoreCreate(
        assessment_type=AssessmentType.BAI,
        score=20,
        administered_date=date.today()
    )

    result = await record_assessment(
        patient_id=sample_patient.id,
        assessment_data=assessment_data,
        db=async_test_db
    )

    # Verify no severity assigned for BAI
    assert result.severity is None


# ============================================================================
# Assessment History Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_get_assessment_history_basic(async_test_db: AsyncSession, sample_patient):
    """Test basic assessment history retrieval"""
    # Create 3 GAD-7 assessments over time
    dates = [
        date(2024, 1, 10),
        date(2024, 2, 10),
        date(2024, 3, 10)
    ]
    scores = [14, 10, 8]

    for test_date, score in zip(dates, scores):
        assessment = AssessmentScore(
            patient_id=sample_patient.id,
            assessment_type="GAD-7",
            score=score,
            severity=calculate_severity("GAD-7", score).value,
            administered_date=test_date
        )
        async_test_db.add(assessment)

    await async_test_db.commit()

    # Retrieve history
    history = await get_assessment_history(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify results
    assert AssessmentType.GAD7 in history.assessments
    gad7_history = history.assessments[AssessmentType.GAD7]
    assert len(gad7_history) == 3

    # Verify chronological order (oldest first)
    assert gad7_history[0].date == date(2024, 1, 10)
    assert gad7_history[0].score == 14
    assert gad7_history[0].severity == Severity.moderate

    assert gad7_history[2].date == date(2024, 3, 10)
    assert gad7_history[2].score == 8
    assert gad7_history[2].severity == Severity.mild


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_get_assessment_history_multiple_types(async_test_db: AsyncSession, sample_patient):
    """Test history retrieval with multiple assessment types"""
    # Create assessments of different types
    assessments_data = [
        ("GAD-7", 10, date(2024, 2, 1)),
        ("PHQ-9", 12, date(2024, 2, 1)),
        ("GAD-7", 8, date(2024, 3, 1)),
        ("PHQ-9", 7, date(2024, 3, 1)),
    ]

    for assessment_type, score, test_date in assessments_data:
        severity = calculate_severity(assessment_type, score)
        assessment = AssessmentScore(
            patient_id=sample_patient.id,
            assessment_type=assessment_type,
            score=score,
            severity=severity.value if severity else None,
            administered_date=test_date
        )
        async_test_db.add(assessment)

    await async_test_db.commit()

    # Retrieve history
    history = await get_assessment_history(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify both types present
    assert AssessmentType.GAD7 in history.assessments
    assert AssessmentType.PHQ9 in history.assessments
    assert len(history.assessments[AssessmentType.GAD7]) == 2
    assert len(history.assessments[AssessmentType.PHQ9]) == 2


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_get_assessment_history_filtered_by_type(async_test_db: AsyncSession, sample_patient):
    """Test history retrieval filtered by assessment type"""
    # Create multiple assessment types
    gad7 = AssessmentScore(
        patient_id=sample_patient.id,
        assessment_type="GAD-7",
        score=10,
        severity="moderate",
        administered_date=date.today()
    )
    phq9 = AssessmentScore(
        patient_id=sample_patient.id,
        assessment_type="PHQ-9",
        score=12,
        severity="moderate",
        administered_date=date.today()
    )
    async_test_db.add_all([gad7, phq9])
    await async_test_db.commit()

    # Filter by GAD-7 only
    history = await get_assessment_history(
        patient_id=sample_patient.id,
        db=async_test_db,
        assessment_type="GAD-7"
    )

    # Verify only GAD-7 returned
    assert AssessmentType.GAD7 in history.assessments
    assert AssessmentType.PHQ9 not in history.assessments
    assert len(history.assessments[AssessmentType.GAD7]) == 1


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_get_assessment_history_date_range_filter(async_test_db: AsyncSession, sample_patient):
    """Test history retrieval with date range filtering"""
    # Create assessments across 3 months
    dates = [
        date(2024, 1, 15),  # Outside range
        date(2024, 2, 10),  # In range
        date(2024, 2, 25),  # In range
        date(2024, 3, 15)   # Outside range
    ]

    for test_date in dates:
        assessment = AssessmentScore(
            patient_id=sample_patient.id,
            assessment_type="GAD-7",
            score=10,
            severity="moderate",
            administered_date=test_date
        )
        async_test_db.add(assessment)

    await async_test_db.commit()

    # Filter by February only
    history = await get_assessment_history(
        patient_id=sample_patient.id,
        db=async_test_db,
        start_date=date(2024, 2, 1),
        end_date=date(2024, 2, 28)
    )

    # Verify only February assessments returned
    gad7_history = history.assessments[AssessmentType.GAD7]
    assert len(gad7_history) == 2
    assert all(date(2024, 2, 1) <= item.date <= date(2024, 2, 28) for item in gad7_history)


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_get_assessment_history_empty_result(async_test_db: AsyncSession, sample_patient):
    """Test history retrieval when no assessments exist"""
    history = await get_assessment_history(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify empty result
    assert history.assessments == {}


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_get_assessment_history_filters_unknown_types(async_test_db: AsyncSession, sample_patient):
    """Test that history filters out assessments with invalid types"""
    # Create valid and invalid assessment types
    valid = AssessmentScore(
        patient_id=sample_patient.id,
        assessment_type="GAD-7",
        score=10,
        severity="moderate",
        administered_date=date.today()
    )
    invalid = AssessmentScore(
        patient_id=sample_patient.id,
        assessment_type="UNKNOWN-TYPE",
        score=10,
        severity=None,
        administered_date=date.today()
    )
    async_test_db.add_all([valid, invalid])
    await async_test_db.commit()

    # Retrieve history
    history = await get_assessment_history(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify only valid type included
    assert AssessmentType.GAD7 in history.assessments
    assert len(history.assessments) == 1


# ============================================================================
# Assessment Due Date Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_check_assessments_due_no_prior_assessments(async_test_db: AsyncSession, sample_patient):
    """Test that all assessments are due when patient has no prior assessments"""
    due_items = await check_assessments_due(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify all assessment types with frequencies are due
    expected_types = [atype for atype, freq in ASSESSMENT_FREQUENCIES.items() if freq is not None]
    assert len(due_items) == len(expected_types)

    # Verify all due dates are today
    today = date.today()
    for item in due_items:
        assert item.type in expected_types
        assert item.last_administered is None
        assert item.due_date == today


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_check_assessments_due_with_recent_assessment(async_test_db: AsyncSession, sample_patient):
    """Test that recently administered assessments are not due"""
    # Create GAD-7 assessment from 7 days ago (frequency: 28 days)
    last_date = date.today() - timedelta(days=7)
    assessment = AssessmentScore(
        patient_id=sample_patient.id,
        assessment_type="GAD-7",
        score=10,
        severity="moderate",
        administered_date=last_date
    )
    async_test_db.add(assessment)
    await async_test_db.commit()

    due_items = await check_assessments_due(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify GAD-7 is NOT due (only 7 days passed, needs 28)
    gad7_items = [item for item in due_items if item.type == "GAD-7"]
    assert len(gad7_items) == 0


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_check_assessments_due_with_overdue_assessment(async_test_db: AsyncSession, sample_patient):
    """Test that overdue assessments are correctly identified"""
    # Create GAD-7 assessment from 35 days ago (frequency: 28 days)
    last_date = date.today() - timedelta(days=35)
    assessment = AssessmentScore(
        patient_id=sample_patient.id,
        assessment_type="GAD-7",
        score=10,
        severity="moderate",
        administered_date=last_date
    )
    async_test_db.add(assessment)
    await async_test_db.commit()

    due_items = await check_assessments_due(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify GAD-7 IS due (35 days passed, needs 28)
    gad7_items = [item for item in due_items if item.type == "GAD-7"]
    assert len(gad7_items) == 1
    assert gad7_items[0].last_administered == last_date
    assert gad7_items[0].due_date == last_date + timedelta(days=28)


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_check_assessments_due_exactly_on_due_date(async_test_db: AsyncSession, sample_patient):
    """Test that assessments due today are correctly identified"""
    # Create GAD-7 assessment from exactly 28 days ago
    last_date = date.today() - timedelta(days=28)
    assessment = AssessmentScore(
        patient_id=sample_patient.id,
        assessment_type="GAD-7",
        score=10,
        severity="moderate",
        administered_date=last_date
    )
    async_test_db.add(assessment)
    await async_test_db.commit()

    due_items = await check_assessments_due(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify GAD-7 IS due (exactly 28 days = due today)
    gad7_items = [item for item in due_items if item.type == "GAD-7"]
    assert len(gad7_items) == 1
    assert gad7_items[0].due_date == date.today()


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_check_assessments_due_skips_pcl5(async_test_db: AsyncSession, sample_patient):
    """Test that PCL-5 (as-needed) is not included in due checks"""
    due_items = await check_assessments_due(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify PCL-5 is not in the list (frequency is None)
    pcl5_items = [item for item in due_items if item.type == "PCL-5"]
    assert len(pcl5_items) == 0


# ============================================================================
# Latest Assessments Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_get_latest_assessments_basic(async_test_db: AsyncSession, sample_patient):
    """Test retrieving latest assessments for each type"""
    # Create multiple assessments over time
    assessments_data = [
        ("GAD-7", 14, date(2024, 1, 10)),
        ("GAD-7", 10, date(2024, 2, 10)),
        ("GAD-7", 8, date(2024, 3, 10)),  # Latest GAD-7
        ("PHQ-9", 15, date(2024, 1, 15)),
        ("PHQ-9", 9, date(2024, 3, 5)),   # Latest PHQ-9
    ]

    for assessment_type, score, test_date in assessments_data:
        severity = calculate_severity(assessment_type, score)
        assessment = AssessmentScore(
            patient_id=sample_patient.id,
            assessment_type=assessment_type,
            score=score,
            severity=severity.value if severity else None,
            administered_date=test_date
        )
        async_test_db.add(assessment)

    await async_test_db.commit()

    # Get latest assessments
    latest = await get_latest_assessments(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify only latest for each type
    assert "GAD-7" in latest
    assert "PHQ-9" in latest
    assert len(latest) == 2

    # Verify GAD-7 latest
    assert latest["GAD-7"].score == 8
    assert latest["GAD-7"].administered_date == date(2024, 3, 10)
    assert latest["GAD-7"].severity == Severity.mild

    # Verify PHQ-9 latest
    assert latest["PHQ-9"].score == 9
    assert latest["PHQ-9"].administered_date == date(2024, 3, 5)
    assert latest["PHQ-9"].severity == Severity.mild


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_get_latest_assessments_single_type(async_test_db: AsyncSession, sample_patient):
    """Test latest assessments when only one type exists"""
    assessment = AssessmentScore(
        patient_id=sample_patient.id,
        assessment_type="GAD-7",
        score=10,
        severity="moderate",
        administered_date=date.today()
    )
    async_test_db.add(assessment)
    await async_test_db.commit()

    latest = await get_latest_assessments(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify only GAD-7 returned
    assert len(latest) == 1
    assert "GAD-7" in latest
    assert latest["GAD-7"].score == 10


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_get_latest_assessments_empty(async_test_db: AsyncSession, sample_patient):
    """Test latest assessments when no assessments exist"""
    latest = await get_latest_assessments(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify empty result
    assert latest == {}


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_get_latest_assessments_all_types(async_test_db: AsyncSession, sample_patient):
    """Test latest assessments retrieval with all supported types"""
    today = date.today()

    # Create one of each assessment type
    assessment_types = ["PHQ-9", "GAD-7", "BDI-II", "BAI", "PCL-5", "AUDIT"]
    scores = [12, 10, 20, 15, 40, 8]

    for assessment_type, score in zip(assessment_types, scores):
        severity = calculate_severity(assessment_type, score)
        assessment = AssessmentScore(
            patient_id=sample_patient.id,
            assessment_type=assessment_type,
            score=score,
            severity=severity.value if severity else None,
            administered_date=today
        )
        async_test_db.add(assessment)

    await async_test_db.commit()

    # Retrieve latest
    latest = await get_latest_assessments(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify all types present
    assert len(latest) == 6
    for assessment_type in assessment_types:
        assert assessment_type in latest


# ============================================================================
# Integration Tests
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_assessment_workflow_record_and_retrieve(
    async_test_db: AsyncSession,
    sample_patient,
    therapist_user
):
    """Test complete workflow: record assessment and retrieve in history"""
    # Record assessment
    assessment_data = AssessmentScoreCreate(
        assessment_type=AssessmentType.PHQ9,
        score=16,
        administered_date=date.today(),
        subscores={
            "little_interest": 2,
            "feeling_down": 2,
            "sleep_problems": 2,
            "tired": 2,
            "appetite": 2,
            "feeling_bad": 2,
            "concentration": 2,
            "moving_slowly": 1,
            "suicidal_thoughts": 1
        }
    )

    recorded = await record_assessment(
        patient_id=sample_patient.id,
        assessment_data=assessment_data,
        db=async_test_db,
        administered_by=therapist_user.id
    )

    # Retrieve history
    history = await get_assessment_history(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify assessment appears in history
    assert AssessmentType.PHQ9 in history.assessments
    phq9_history = history.assessments[AssessmentType.PHQ9]
    assert len(phq9_history) == 1
    assert phq9_history[0].score == 16
    assert phq9_history[0].severity == Severity.moderately_severe


@pytest.mark.asyncio
@pytest.mark.goal_tracking
async def test_assessment_trend_over_time(async_test_db: AsyncSession, sample_patient):
    """Test tracking assessment scores improving over time"""
    # Create declining GAD-7 scores (improvement)
    dates_and_scores = [
        (date(2024, 1, 1), 18),   # Severe
        (date(2024, 2, 1), 12),   # Moderate
        (date(2024, 3, 1), 8),    # Mild
        (date(2024, 4, 1), 3),    # Minimal
    ]

    for test_date, score in dates_and_scores:
        severity = calculate_severity("GAD-7", score)
        assessment = AssessmentScore(
            patient_id=sample_patient.id,
            assessment_type="GAD-7",
            score=score,
            severity=severity.value,
            administered_date=test_date
        )
        async_test_db.add(assessment)

    await async_test_db.commit()

    # Retrieve history
    history = await get_assessment_history(
        patient_id=sample_patient.id,
        db=async_test_db
    )

    # Verify trend shows improvement
    gad7_history = history.assessments[AssessmentType.GAD7]
    assert len(gad7_history) == 4

    # Verify severity progression
    assert gad7_history[0].severity == Severity.severe
    assert gad7_history[1].severity == Severity.moderate
    assert gad7_history[2].severity == Severity.mild
    assert gad7_history[3].severity == Severity.minimal

    # Verify score progression
    scores = [item.score for item in gad7_history]
    assert scores == [18, 12, 8, 3]
