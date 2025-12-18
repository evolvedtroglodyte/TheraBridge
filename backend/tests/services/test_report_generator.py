"""
Comprehensive unit tests for Report Generator Service (Feature 6 - Goal Tracking).

This module tests:
1. generate_progress_report() - Complete progress report generation
2. calculate_goal_summaries() - Goal progress calculations
3. format_assessment_summary() - Assessment score formatting
4. generate_clinical_observations() - Clinical insights generation

Test coverage:
- Complete report generation with goals and assessments
- Goal summary calculations (baseline, current, change %)
- Assessment summary formatting across multiple types
- Clinical observations with various progress patterns
- Empty data handling and edge cases
- Date range filtering
- Multiple goal types in single report
- Report structure validation
- Calculation accuracy for percentage changes
- Status determination logic

Author: QA Validator #1 (Instance I7) - Wave 3
"""
import pytest
import pytest_asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.report_generator import (
    generate_progress_report,
    calculate_goal_summaries,
    format_assessment_summary,
    generate_clinical_observations
)
from app.schemas.report_schemas import (
    GoalStatus,
    GoalSummaryItem,
    AssessmentChange
)
from app.models.db_models import User, TherapySession, TherapistPatient
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import ProgressEntry, AssessmentScore, GoalTrackingConfig
from app.models.schemas import UserRole


# ============================================================================
# Fixtures for Report Generator Tests
# ============================================================================

@pytest_asyncio.fixture
async def patient_with_goals_and_assessments(async_test_db: AsyncSession):
    """
    Create patient with multiple goals, progress entries, and assessments.

    This comprehensive fixture provides:
    - 1 therapist
    - 1 patient
    - 3 treatment goals with different progress patterns
    - Progress entries spanning 30 days
    - 2 assessment types (GAD-7 and PHQ-9) with baseline and current scores
    - 3 therapy sessions (completed and missed)

    Returns:
        Dict with therapist, patient, goals, progress_entries, assessments, sessions
    """
    # Create therapist first
    therapist = User(
        email="report.therapist@test.com",
        hashed_password="hashed",
        first_name="Report",
        last_name="Therapist",
        full_name="Report Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(therapist)
    await async_test_db.flush()

    # Create patient
    patient = User(
        email="report.patient@test.com",
        hashed_password="hashed",
        first_name="Report",
        last_name="Patient",
        full_name="Report Patient",
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

    # Create 3 goals with different progress patterns
    now = datetime.utcnow()

    # Goal 1: Significant improvement (anxiety reduction)
    goal1 = TreatmentGoal(
        patient_id=patient.id,
        therapist_id=therapist.id,
        description="Reduce anxiety symptoms",
        category="anxiety_management",
        status="in_progress",
        baseline_value=Decimal("8.0"),
        target_value=Decimal("3.0"),
        target_date=date.today() + timedelta(days=30),
        created_at=now - timedelta(days=40)
    )
    async_test_db.add(goal1)
    await async_test_db.flush()

    # Goal 2: Moderate improvement (sleep)
    goal2 = TreatmentGoal(
        patient_id=patient.id,
        therapist_id=therapist.id,
        description="Improve sleep quality",
        category="sleep",
        status="in_progress",
        baseline_value=Decimal("5.0"),
        target_value=Decimal("8.0"),
        target_date=date.today() + timedelta(days=30),
        created_at=now - timedelta(days=40)
    )
    async_test_db.add(goal2)
    await async_test_db.flush()

    # Goal 3: Stable/slight decline (exercise)
    goal3 = TreatmentGoal(
        patient_id=patient.id,
        therapist_id=therapist.id,
        description="Exercise 5 times per week",
        category="physical_activity",
        status="in_progress",
        baseline_value=Decimal("3.0"),
        target_value=Decimal("5.0"),
        target_date=date.today() + timedelta(days=30),
        created_at=now - timedelta(days=40)
    )
    async_test_db.add(goal3)
    await async_test_db.flush()

    # Create tracking configs
    tracking_config1 = GoalTrackingConfig(
        goal_id=goal1.id,
        tracking_method="scale",
        tracking_frequency="daily",
        scale_min=1,
        scale_max=10,
        target_direction="decrease"
    )
    tracking_config2 = GoalTrackingConfig(
        goal_id=goal2.id,
        tracking_method="scale",
        tracking_frequency="daily",
        scale_min=1,
        scale_max=10,
        target_direction="increase"
    )
    tracking_config3 = GoalTrackingConfig(
        goal_id=goal3.id,
        tracking_method="frequency",
        tracking_frequency="weekly",
        frequency_unit="times_per_week",
        target_direction="increase"
    )
    async_test_db.add_all([tracking_config1, tracking_config2, tracking_config3])
    await async_test_db.flush()

    # Create progress entries
    progress_entries = []

    # Goal 1: Baseline 8.0 → Current 5.0 (37.5% improvement = significant)
    start_date = date.today() - timedelta(days=35)
    entry1_baseline = ProgressEntry(
        goal_id=goal1.id,
        tracking_config_id=tracking_config1.id,
        entry_date=start_date,
        value=Decimal("8.0"),
        context="therapist_assessment"
    )
    entry1_current = ProgressEntry(
        goal_id=goal1.id,
        tracking_config_id=tracking_config1.id,
        entry_date=date.today() - timedelta(days=1),
        value=Decimal("5.0"),
        context="self_report"
    )
    progress_entries.extend([entry1_baseline, entry1_current])

    # Goal 2: Baseline 5.0 → Current 5.5 (10% improvement = moderate)
    entry2_baseline = ProgressEntry(
        goal_id=goal2.id,
        tracking_config_id=tracking_config2.id,
        entry_date=start_date,
        value=Decimal("5.0"),
        context="therapist_assessment"
    )
    entry2_current = ProgressEntry(
        goal_id=goal2.id,
        tracking_config_id=tracking_config2.id,
        entry_date=date.today() - timedelta(days=1),
        value=Decimal("5.5"),
        context="self_report"
    )
    progress_entries.extend([entry2_baseline, entry2_current])

    # Goal 3: Baseline 3.0 → Current 2.8 (6.7% decline = stable)
    entry3_baseline = ProgressEntry(
        goal_id=goal3.id,
        tracking_config_id=tracking_config3.id,
        entry_date=start_date,
        value=Decimal("3.0"),
        context="therapist_assessment"
    )
    entry3_current = ProgressEntry(
        goal_id=goal3.id,
        tracking_config_id=tracking_config3.id,
        entry_date=date.today() - timedelta(days=1),
        value=Decimal("2.8"),
        context="self_report"
    )
    progress_entries.extend([entry3_baseline, entry3_current])

    async_test_db.add_all(progress_entries)
    await async_test_db.flush()

    # Create assessments (GAD-7 and PHQ-9)
    assessments = []

    # GAD-7: Baseline 14 (moderate) → Current 8 (mild) - improvement
    gad7_baseline = AssessmentScore(
        patient_id=patient.id,
        goal_id=goal1.id,
        administered_by=therapist.id,
        assessment_type="GAD-7",
        score=14,
        severity="moderate",
        subscores={"total": 14},
        administered_date=start_date,
        notes="Baseline anxiety assessment"
    )
    gad7_current = AssessmentScore(
        patient_id=patient.id,
        goal_id=goal1.id,
        administered_by=therapist.id,
        assessment_type="GAD-7",
        score=8,
        severity="mild",
        subscores={"total": 8},
        administered_date=date.today() - timedelta(days=2),
        notes="Follow-up anxiety assessment"
    )
    assessments.extend([gad7_baseline, gad7_current])

    # PHQ-9: Baseline 12 (moderate) → Current 16 (moderately severe) - worsening
    phq9_baseline = AssessmentScore(
        patient_id=patient.id,
        administered_by=therapist.id,
        assessment_type="PHQ-9",
        score=12,
        severity="moderate",
        subscores={"total": 12},
        administered_date=start_date,
        notes="Baseline depression assessment"
    )
    phq9_current = AssessmentScore(
        patient_id=patient.id,
        administered_by=therapist.id,
        assessment_type="PHQ-9",
        score=16,
        severity="moderately severe",
        subscores={"total": 16},
        administered_date=date.today() - timedelta(days=2),
        notes="Follow-up depression assessment"
    )
    assessments.extend([phq9_baseline, phq9_current])

    async_test_db.add_all(assessments)
    await async_test_db.flush()

    # Create therapy sessions
    sessions = []

    # 2 completed sessions
    for i in range(2):
        session = TherapySession(
            patient_id=patient.id,
            therapist_id=therapist.id,
            session_date=date.today() - timedelta(days=(i * 14 + 7)),
            duration_seconds=3600,
            status='completed'
        )
        sessions.append(session)
        async_test_db.add(session)

    # 1 missed session
    missed_session = TherapySession(
        patient_id=patient.id,
        therapist_id=therapist.id,
        session_date=date.today() - timedelta(days=3),
        status='missed'
    )
    sessions.append(missed_session)
    async_test_db.add(missed_session)

    await async_test_db.commit()

    return {
        "therapist": therapist,
        "patient": patient,
        "goals": [goal1, goal2, goal3],
        "progress_entries": progress_entries,
        "assessments": assessments,
        "sessions": sessions
    }


# ============================================================================
# Test generate_progress_report()
# ============================================================================

@pytest.mark.goal_tracking
@pytest.mark.asyncio
class TestGenerateProgressReport:
    """Test complete progress report generation"""

    async def test_generate_complete_report(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test generating complete progress report with all data"""
        patient = patient_with_goals_and_assessments["patient"]
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        report = await generate_progress_report(
            patient_id=patient.id,
            start_date=start_date,
            end_date=end_date,
            db=async_test_db
        )

        # Verify report structure
        assert report.report_period.start == start_date
        assert report.report_period.end == end_date
        assert report.patient_summary.name == "Report Patient"
        assert report.patient_summary.sessions_attended == 2
        assert report.patient_summary.sessions_missed == 1

        # Verify goals summary
        assert len(report.goals_summary) == 3

        # Verify assessment summary
        assert len(report.assessment_summary) == 2
        assert "GAD-7" in report.assessment_summary
        assert "PHQ-9" in report.assessment_summary

        # Verify clinical observations exist
        assert report.clinical_observations is not None
        assert len(report.clinical_observations) > 0

        # Verify recommendations exist
        assert report.recommendations is not None
        assert len(report.recommendations) > 0

    async def test_generate_report_patient_not_found(
        self,
        async_test_db: AsyncSession
    ):
        """Test that ValueError is raised when patient doesn't exist"""
        fake_patient_id = uuid4()

        with pytest.raises(ValueError, match="Patient .* not found"):
            await generate_progress_report(
                patient_id=fake_patient_id,
                start_date=date.today() - timedelta(days=30),
                end_date=date.today(),
                db=async_test_db
            )

    async def test_generate_report_treatment_start_date(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test that treatment start date is calculated correctly"""
        patient = patient_with_goals_and_assessments["patient"]

        report = await generate_progress_report(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            db=async_test_db
        )

        # Treatment start should be earliest goal or session date
        assert report.patient_summary.treatment_start is not None
        assert report.patient_summary.treatment_start <= date.today() - timedelta(days=30)

    async def test_generate_report_empty_date_range(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test report generation with date range containing no data"""
        patient = patient_with_goals_and_assessments["patient"]

        # Use future date range with no data
        future_start = date.today() + timedelta(days=100)
        future_end = date.today() + timedelta(days=130)

        report = await generate_progress_report(
            patient_id=patient.id,
            start_date=future_start,
            end_date=future_end,
            db=async_test_db
        )

        # Report should generate but with empty data
        assert report.patient_summary.sessions_attended == 0
        assert report.patient_summary.sessions_missed == 0
        assert len(report.goals_summary) == 0
        assert len(report.assessment_summary) == 0


# ============================================================================
# Test calculate_goal_summaries()
# ============================================================================

@pytest.mark.goal_tracking
@pytest.mark.asyncio
class TestCalculateGoalSummaries:
    """Test goal summary calculations and status determination"""

    async def test_calculate_goal_summaries_all_goals(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test calculating summaries for all patient goals"""
        patient = patient_with_goals_and_assessments["patient"]

        summaries = await calculate_goal_summaries(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=35),
            end_date=date.today(),
            db=async_test_db
        )

        assert len(summaries) == 3

        # Verify all required fields present
        for summary in summaries:
            assert summary.goal is not None
            assert summary.baseline is not None
            assert summary.current is not None
            assert summary.change is not None
            assert summary.change_percentage is not None
            assert summary.status is not None

    async def test_significant_improvement_status(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test that >= 30% improvement is classified as significant_improvement"""
        patient = patient_with_goals_and_assessments["patient"]

        summaries = await calculate_goal_summaries(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=35),
            end_date=date.today(),
            db=async_test_db
        )

        # Goal 1: 8.0 → 5.0 = -37.5% (significant improvement for decrease goal)
        anxiety_goal = next(s for s in summaries if "anxiety" in s.goal.lower())
        assert anxiety_goal.baseline == 8.0
        assert anxiety_goal.current == 5.0
        assert anxiety_goal.change == -3.0
        assert anxiety_goal.change_percentage == -37.5
        assert anxiety_goal.status == GoalStatus.significant_improvement

    async def test_moderate_improvement_status(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test that 10-29% improvement is classified as improvement"""
        patient = patient_with_goals_and_assessments["patient"]

        summaries = await calculate_goal_summaries(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=35),
            end_date=date.today(),
            db=async_test_db
        )

        # Goal 2: 5.0 → 5.5 = +10% (improvement for increase goal)
        sleep_goal = next(s for s in summaries if "sleep" in s.goal.lower())
        assert sleep_goal.baseline == 5.0
        assert sleep_goal.current == 5.5
        assert sleep_goal.change == 0.5
        assert sleep_goal.change_percentage == 10.0
        assert sleep_goal.status == GoalStatus.improvement

    async def test_stable_status(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test that < 10% change is classified as stable"""
        patient = patient_with_goals_and_assessments["patient"]

        summaries = await calculate_goal_summaries(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=35),
            end_date=date.today(),
            db=async_test_db
        )

        # Goal 3: 3.0 → 2.8 = -6.7% (stable)
        exercise_goal = next(s for s in summaries if "exercise" in s.goal.lower())
        assert exercise_goal.baseline == 3.0
        assert exercise_goal.current == 2.8
        assert abs(exercise_goal.change_percentage) < 10
        assert exercise_goal.status == GoalStatus.stable

    async def test_change_percentage_calculation(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test that change percentage is calculated correctly"""
        patient = patient_with_goals_and_assessments["patient"]

        summaries = await calculate_goal_summaries(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=35),
            end_date=date.today(),
            db=async_test_db
        )

        for summary in summaries:
            # Verify: change_percentage = (change / baseline) * 100
            expected_pct = (summary.change / summary.baseline) * 100
            assert abs(summary.change_percentage - expected_pct) < 0.01

    async def test_goals_without_baseline_or_current_skipped(
        self,
        async_test_db: AsyncSession
    ):
        """Test that goals without both baseline and current values are skipped"""
        # Create therapist
        therapist = User(
            email="test.therapist@test.com",
            hashed_password="hashed",
            first_name="Test",
            last_name="Therapist",
            full_name="Test Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(therapist)
        await async_test_db.flush()

        # Create patient
        patient = User(
            email="test.incomplete@test.com",
            hashed_password="hashed",
            first_name="Test",
            last_name="Incomplete",
            full_name="Test Incomplete",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(patient)
        await async_test_db.flush()

        # Create goal without progress entries
        goal = TreatmentGoal(
            patient_id=patient.id,
            therapist_id=therapist.id,
            description="Goal with no progress",
            category="test",
            status="assigned",
            baseline_value=None,
            target_value=Decimal("10.0"),
            target_date=date.today() + timedelta(days=30)
        )
        async_test_db.add(goal)
        await async_test_db.commit()

        summaries = await calculate_goal_summaries(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            db=async_test_db
        )

        # Should return empty list (no goals with both baseline and current)
        assert len(summaries) == 0

    async def test_date_range_filtering(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test that date range correctly filters progress entries"""
        patient = patient_with_goals_and_assessments["patient"]

        # Use narrow date range that excludes baseline entries
        summaries = await calculate_goal_summaries(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=5),
            end_date=date.today(),
            db=async_test_db
        )

        # Should still find entries (uses <= start_date for baseline)
        assert len(summaries) == 3


# ============================================================================
# Test format_assessment_summary()
# ============================================================================

@pytest.mark.goal_tracking
@pytest.mark.asyncio
class TestFormatAssessmentSummary:
    """Test assessment summary formatting and interpretation"""

    async def test_format_multiple_assessment_types(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test formatting assessments with multiple types (GAD-7, PHQ-9)"""
        patient = patient_with_goals_and_assessments["patient"]

        summary = await format_assessment_summary(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=35),
            end_date=date.today(),
            db=async_test_db
        )

        assert len(summary) == 2
        assert "GAD-7" in summary
        assert "PHQ-9" in summary

    async def test_assessment_improvement_interpretation(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test interpretation text for improved assessment scores"""
        patient = patient_with_goals_and_assessments["patient"]

        summary = await format_assessment_summary(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=35),
            end_date=date.today(),
            db=async_test_db
        )

        # GAD-7: 14 → 8 (improved)
        gad7 = summary["GAD-7"]
        assert gad7.baseline == 14
        assert gad7.current == 8
        assert gad7.change == -6
        assert "Improved" in gad7.interpretation
        assert "moderate" in gad7.interpretation.lower()
        assert "mild" in gad7.interpretation.lower()

    async def test_assessment_worsening_interpretation(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test interpretation text for worsened assessment scores"""
        patient = patient_with_goals_and_assessments["patient"]

        summary = await format_assessment_summary(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=35),
            end_date=date.today(),
            db=async_test_db
        )

        # PHQ-9: 12 → 16 (worsened)
        phq9 = summary["PHQ-9"]
        assert phq9.baseline == 12
        assert phq9.current == 16
        assert phq9.change == 4
        assert "Worsened" in phq9.interpretation
        assert "moderate" in phq9.interpretation.lower()
        assert "moderately severe" in phq9.interpretation.lower()

    async def test_assessment_stable_interpretation(
        self,
        async_test_db: AsyncSession
    ):
        """Test interpretation text for stable assessment scores"""
        # Create therapist
        therapist = User(
            email="stable.therapist@test.com",
            hashed_password="hashed",
            first_name="Stable",
            last_name="Therapist",
            full_name="Stable Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(therapist)
        await async_test_db.flush()

        # Create patient
        patient = User(
            email="stable.assessment@test.com",
            hashed_password="hashed",
            first_name="Stable",
            last_name="Patient",
            full_name="Stable Patient",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(patient)
        await async_test_db.flush()

        # Create identical baseline and current assessments
        baseline = AssessmentScore(
            patient_id=patient.id,
            administered_by=therapist.id,
            assessment_type="GAD-7",
            score=10,
            severity="moderate",
            subscores={"total": 10},
            administered_date=date.today() - timedelta(days=30)
        )
        current = AssessmentScore(
            patient_id=patient.id,
            administered_by=therapist.id,
            assessment_type="GAD-7",
            score=10,
            severity="moderate",
            subscores={"total": 10},
            administered_date=date.today() - timedelta(days=1)
        )
        async_test_db.add_all([baseline, current])
        await async_test_db.commit()

        summary = await format_assessment_summary(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=35),
            end_date=date.today(),
            db=async_test_db
        )

        gad7 = summary["GAD-7"]
        assert gad7.baseline == 10
        assert gad7.current == 10
        assert gad7.change == 0
        assert "Remained stable" in gad7.interpretation

    async def test_empty_assessment_summary(
        self,
        async_test_db: AsyncSession
    ):
        """Test that empty dict is returned when no assessments found"""
        # Create patient with no assessments
        patient = User(
            email="no.assessments@test.com",
            hashed_password="hashed",
            first_name="No",
            last_name="Assessments",
            full_name="No Assessments",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(patient)
        await async_test_db.commit()

        summary = await format_assessment_summary(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today(),
            db=async_test_db
        )

        assert len(summary) == 0
        assert summary == {}


# ============================================================================
# Test generate_clinical_observations()
# ============================================================================

@pytest.mark.goal_tracking
@pytest.mark.asyncio
class TestGenerateClinicalObservations:
    """Test clinical observations generation from progress data"""

    async def test_observations_with_significant_improvements(self):
        """Test observations highlight significant improvements"""
        goals_summary = [
            GoalSummaryItem(
                goal="Reduce anxiety",
                baseline=8.0,
                current=4.0,
                change=-4.0,
                change_percentage=-50.0,
                status=GoalStatus.significant_improvement
            ),
            GoalSummaryItem(
                goal="Improve sleep",
                baseline=5.0,
                current=3.0,
                change=-2.0,
                change_percentage=-40.0,
                status=GoalStatus.significant_improvement
            )
        ]

        observations = await generate_clinical_observations(
            goals_summary=goals_summary,
            assessment_summary={}
        )

        assert "significant improvement" in observations.lower()
        assert "2 goal" in observations

    async def test_observations_with_moderate_improvements(self):
        """Test observations note moderate progress"""
        goals_summary = [
            GoalSummaryItem(
                goal="Exercise regularly",
                baseline=2.0,
                current=2.5,
                change=0.5,
                change_percentage=25.0,
                status=GoalStatus.improvement
            )
        ]

        observations = await generate_clinical_observations(
            goals_summary=goals_summary,
            assessment_summary={}
        )

        assert "moderate progress" in observations.lower() or "progress observed" in observations.lower()
        assert "1 goal" in observations

    async def test_observations_with_stable_goals(self):
        """Test observations mention stable goals"""
        goals_summary = [
            GoalSummaryItem(
                goal="Maintain mood",
                baseline=6.0,
                current=6.2,
                change=0.2,
                change_percentage=3.3,
                status=GoalStatus.stable
            )
        ]

        observations = await generate_clinical_observations(
            goals_summary=goals_summary,
            assessment_summary={}
        )

        assert "stable" in observations.lower()
        assert "1 goal" in observations

    async def test_observations_with_declining_goals(self):
        """Test observations flag goals showing decline"""
        goals_summary = [
            GoalSummaryItem(
                goal="Exercise frequency",
                baseline=5.0,
                current=3.5,
                change=-1.5,
                change_percentage=-30.0,
                status=GoalStatus.decline
            )
        ]

        observations = await generate_clinical_observations(
            goals_summary=goals_summary,
            assessment_summary={}
        )

        assert "decline" in observations.lower()
        assert "1 goal" in observations
        assert "review" in observations.lower() or "barrier" in observations.lower()

    async def test_observations_with_improved_assessments(self):
        """Test observations mention improved standardized assessments"""
        goals_summary = []
        assessment_summary = {
            "GAD-7": AssessmentChange(
                baseline=14,
                current=8,
                change=-6,
                interpretation="Improved from moderate to mild"
            ),
            "PHQ-9": AssessmentChange(
                baseline=16,
                current=10,
                change=-6,
                interpretation="Improved from moderately severe to moderate"
            )
        }

        observations = await generate_clinical_observations(
            goals_summary=goals_summary,
            assessment_summary=assessment_summary
        )

        assert "GAD-7" in observations
        assert "PHQ-9" in observations
        assert "improvement" in observations.lower()

    async def test_observations_with_no_data(self):
        """Test default observations when no goals or assessments"""
        observations = await generate_clinical_observations(
            goals_summary=[],
            assessment_summary={}
        )

        # Should return default message
        assert len(observations) > 0
        assert "engagement" in observations.lower() or "continue monitoring" in observations.lower()

    async def test_observations_mixed_progress_patterns(self):
        """Test observations with combination of improvement and decline"""
        goals_summary = [
            GoalSummaryItem(
                goal="Anxiety reduction",
                baseline=8.0,
                current=5.0,
                change=-3.0,
                change_percentage=-37.5,
                status=GoalStatus.significant_improvement
            ),
            GoalSummaryItem(
                goal="Sleep quality",
                baseline=6.0,
                current=6.5,
                change=0.5,
                change_percentage=8.3,
                status=GoalStatus.stable
            ),
            GoalSummaryItem(
                goal="Exercise",
                baseline=4.0,
                current=3.0,
                change=-1.0,
                change_percentage=-25.0,
                status=GoalStatus.decline
            )
        ]

        observations = await generate_clinical_observations(
            goals_summary=goals_summary,
            assessment_summary={}
        )

        # Should mention all status types
        assert "significant improvement" in observations.lower()
        assert "stable" in observations.lower()
        assert "decline" in observations.lower()


# ============================================================================
# Edge Cases and Integration Tests
# ============================================================================

@pytest.mark.goal_tracking
@pytest.mark.asyncio
class TestReportGeneratorEdgeCases:
    """Test edge cases and integration scenarios"""

    async def test_report_with_zero_baseline_value(
        self,
        async_test_db: AsyncSession
    ):
        """Test handling of goals with zero baseline (division by zero)"""
        # Create therapist
        therapist = User(
            email="zero.therapist@test.com",
            hashed_password="hashed",
            first_name="Zero",
            last_name="Therapist",
            full_name="Zero Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(therapist)
        await async_test_db.flush()

        # Create patient
        patient = User(
            email="zero.baseline@test.com",
            hashed_password="hashed",
            first_name="Zero",
            last_name="Baseline",
            full_name="Zero Baseline",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(patient)
        await async_test_db.flush()

        # Create goal with zero baseline
        goal = TreatmentGoal(
            patient_id=patient.id,
            therapist_id=therapist.id,
            description="Start exercising",
            category="physical_activity",
            status="in_progress",
            baseline_value=Decimal("0.0"),
            target_value=Decimal("5.0"),
            target_date=date.today() + timedelta(days=30)
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        # Create tracking config
        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="frequency",
            tracking_frequency="weekly"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create progress entry
        entry = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=config.id,
            entry_date=date.today() - timedelta(days=1),
            value=Decimal("2.0"),
            context="self_report"
        )
        async_test_db.add(entry)
        await async_test_db.commit()

        # Should handle division by zero gracefully
        summaries = await calculate_goal_summaries(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=7),
            end_date=date.today(),
            db=async_test_db
        )

        # Should return percentage as 0 (handled in code)
        assert len(summaries) == 1
        assert summaries[0].change_percentage == 0

    async def test_report_with_very_large_percentage_changes(
        self,
        async_test_db: AsyncSession
    ):
        """Test handling of extreme percentage changes"""
        # Create therapist
        therapist = User(
            email="extreme.therapist@test.com",
            hashed_password="hashed",
            first_name="Extreme",
            last_name="Therapist",
            full_name="Extreme Therapist",
            role=UserRole.therapist,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(therapist)
        await async_test_db.flush()

        # Create patient
        patient = User(
            email="extreme.change@test.com",
            hashed_password="hashed",
            first_name="Extreme",
            last_name="Change",
            full_name="Extreme Change",
            role=UserRole.patient,
            is_active=True,
            is_verified=False
        )
        async_test_db.add(patient)
        await async_test_db.flush()

        # Create goal with small baseline
        goal = TreatmentGoal(
            patient_id=patient.id,
            therapist_id=therapist.id,
            description="Reduce severe symptoms",
            category="symptom_management",
            status="in_progress",
            baseline_value=Decimal("0.5"),
            target_value=Decimal("0.1"),
            target_date=date.today() + timedelta(days=30)
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create entries showing large change
        baseline_entry = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=config.id,
            entry_date=date.today() - timedelta(days=10),
            value=Decimal("0.5"),
            context="therapist_assessment"
        )
        current_entry = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=config.id,
            entry_date=date.today() - timedelta(days=1),
            value=Decimal("5.0"),  # 900% increase
            context="self_report"
        )
        async_test_db.add_all([baseline_entry, current_entry])
        await async_test_db.commit()

        summaries = await calculate_goal_summaries(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=15),
            end_date=date.today(),
            db=async_test_db
        )

        assert len(summaries) == 1
        # Large negative change (worsening) should be flagged
        assert abs(summaries[0].change_percentage) >= 30
        # Status should reflect significant change
        assert summaries[0].status in [GoalStatus.significant_improvement, GoalStatus.decline]

    async def test_multiple_goals_same_category(
        self,
        async_test_db: AsyncSession,
        patient_with_goals_and_assessments
    ):
        """Test report handles multiple goals in same category"""
        patient = patient_with_goals_and_assessments["patient"]

        # Add another anxiety goal
        therapist = patient_with_goals_and_assessments["therapist"]
        goal4 = TreatmentGoal(
            patient_id=patient.id,
            therapist_id=therapist.id,
            description="Reduce panic attacks frequency",
            category="anxiety_management",
            status="in_progress",
            baseline_value=Decimal("10.0"),
            target_value=Decimal("3.0"),
            target_date=date.today() + timedelta(days=30)
        )
        async_test_db.add(goal4)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal4.id,
            tracking_method="frequency",
            tracking_frequency="weekly"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Add progress entries
        baseline = ProgressEntry(
            goal_id=goal4.id,
            tracking_config_id=config.id,
            entry_date=date.today() - timedelta(days=20),
            value=Decimal("10.0")
        )
        current = ProgressEntry(
            goal_id=goal4.id,
            tracking_config_id=config.id,
            entry_date=date.today() - timedelta(days=1),
            value=Decimal("7.0")
        )
        async_test_db.add_all([baseline, current])
        await async_test_db.commit()

        summaries = await calculate_goal_summaries(
            patient_id=patient.id,
            start_date=date.today() - timedelta(days=35),
            end_date=date.today(),
            db=async_test_db
        )

        # Should have 4 goals total (3 original + 1 new)
        assert len(summaries) == 4

        # Should have 2 anxiety-related goals
        anxiety_goals = [s for s in summaries if "anxiety" in s.goal.lower() or "panic" in s.goal.lower()]
        assert len(anxiety_goals) == 2
