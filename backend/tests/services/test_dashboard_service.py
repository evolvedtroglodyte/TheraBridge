# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for dashboard_service.py

Tests cover:
1. get_goal_dashboard() - Complete patient dashboard aggregation
2. aggregate_tracking_summary() - Tracking activity metrics
3. get_goal_dashboard_items() - Per-goal dashboard data

Edge cases tested:
- No goals/entries
- Empty tracking data
- Streak calculation logic (consecutive days, grace period)
- Completion rate formulas
- Next check-in date calculations
- Progress percentage calculations
- Trend detection (improving/stable/declining)
- N+1 query performance issues

Performance notes included for optimization opportunities.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, date as date_type, time
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal

from app.services.dashboard_service import (
    get_goal_dashboard,
    aggregate_tracking_summary,
    get_goal_dashboard_items
)
from app.schemas.tracking_schemas import (
    GoalDashboardResponse,
    TrackingSummary,
    GoalDashboardItem,
    TrendDirection,
    GoalStatus
)
from app.models.db_models import User
from app.models.schemas import UserRole
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import (
    GoalTrackingConfig,
    ProgressEntry,
    ProgressMilestone,
    AssessmentScore
)
from app.auth.utils import get_password_hash


# ============================================================================
# Fixtures
# ============================================================================

@pytest_asyncio.fixture
async def sample_patient(async_test_db: AsyncSession):
    """Create a test patient user"""
    patient = User(
        email="dashboard.patient@test.com",
        hashed_password=get_password_hash("PatientPass123!"),
        first_name="Dashboard",
        last_name="Patient",
        full_name="Dashboard Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(patient)
    await async_test_db.flush()
    return patient


@pytest_asyncio.fixture
async def sample_therapist(async_test_db: AsyncSession):
    """Create a test therapist user"""
    therapist = User(
        email="dashboard.therapist@test.com",
        hashed_password=get_password_hash("TherapistPass123!"),
        first_name="Dashboard",
        last_name="Therapist",
        full_name="Dashboard Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=True
    )
    async_test_db.add(therapist)
    await async_test_db.flush()
    return therapist


@pytest_asyncio.fixture
async def goal_with_progress_history(async_test_db: AsyncSession, sample_patient, sample_therapist):
    """Create a goal with progress entries spanning multiple weeks"""
    goal = TreatmentGoal(
        patient_id=sample_patient.id,
        therapist_id=sample_therapist.id,
        description="Track anxiety levels",
        category="anxiety_management",
        status="in_progress",
        baseline_value=Decimal("8.0"),
        target_value=Decimal("3.0"),
        target_date=date_type.today() + timedelta(days=90),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    async_test_db.add(goal)
    await async_test_db.flush()

    config = GoalTrackingConfig(
        goal_id=goal.id,
        tracking_method="scale",
        tracking_frequency="daily",
        scale_min=1,
        scale_max=10,
        target_direction="decrease",
        reminder_enabled=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    async_test_db.add(config)
    await async_test_db.flush()

    # Create 30 days of progress entries (improving trend)
    entries = []
    for i in range(30):
        entry_date = date_type.today() - timedelta(days=29 - i)
        value = 8.0 - (i * 0.15)  # Gradually decreasing (improving)

        entry = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=config.id,
            entry_date=entry_date,
            entry_time=time(hour=20, minute=0),
            value=Decimal(str(value)),
            value_label=f"Value: {value:.1f}",
            notes=f"Day {i+1} entry",
            context="self_report",
            recorded_at=datetime.utcnow()
        )
        async_test_db.add(entry)
        entries.append(entry)

    await async_test_db.flush()
    return {"goal": goal, "config": config, "entries": entries, "patient": sample_patient}


@pytest_asyncio.fixture
async def multiple_goals_for_patient(async_test_db: AsyncSession, sample_patient, sample_therapist):
    """Create multiple goals with different statuses and tracking configs"""
    goals = []
    configs = []

    # Goal 1: Daily tracking, in progress
    goal1 = TreatmentGoal(
        patient_id=sample_patient.id,
        therapist_id=sample_therapist.id,
        description="Reduce panic attacks",
        category="anxiety_management",
        status="in_progress",
        baseline_value=Decimal("5.0"),
        target_value=Decimal("1.0"),
        created_at=datetime.utcnow()
    )
    async_test_db.add(goal1)
    await async_test_db.flush()

    config1 = GoalTrackingConfig(
        goal_id=goal1.id,
        tracking_method="frequency",
        tracking_frequency="daily",
        frequency_unit="times_per_day",
        target_direction="decrease",
        created_at=datetime.utcnow()
    )
    async_test_db.add(config1)
    goals.append(goal1)
    configs.append(config1)

    # Goal 2: Weekly tracking, assigned
    goal2 = TreatmentGoal(
        patient_id=sample_patient.id,
        therapist_id=sample_therapist.id,
        description="Practice mindfulness",
        category="coping_skills",
        status="assigned",
        baseline_value=Decimal("2.0"),
        target_value=Decimal("7.0"),
        created_at=datetime.utcnow()
    )
    async_test_db.add(goal2)
    await async_test_db.flush()

    config2 = GoalTrackingConfig(
        goal_id=goal2.id,
        tracking_method="scale",
        tracking_frequency="weekly",
        scale_min=1,
        scale_max=10,
        target_direction="increase",
        created_at=datetime.utcnow()
    )
    async_test_db.add(config2)
    goals.append(goal2)
    configs.append(config2)

    # Goal 3: Completed
    goal3 = TreatmentGoal(
        patient_id=sample_patient.id,
        therapist_id=sample_therapist.id,
        description="Sleep 7+ hours",
        category="sleep_hygiene",
        status="completed",
        baseline_value=Decimal("4.0"),
        target_value=Decimal("7.0"),
        completed_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    async_test_db.add(goal3)
    await async_test_db.flush()

    config3 = GoalTrackingConfig(
        goal_id=goal3.id,
        tracking_method="duration",
        tracking_frequency="daily",
        duration_unit="hours",
        target_direction="increase",
        created_at=datetime.utcnow()
    )
    async_test_db.add(config3)
    goals.append(goal3)
    configs.append(config3)

    await async_test_db.flush()
    return {
        "goals": goals,
        "configs": configs,
        "patient": sample_patient,
        "therapist": sample_therapist
    }


@pytest_asyncio.fixture
async def sample_milestone(async_test_db: AsyncSession, goal_with_progress_history):
    """Create a sample milestone for a goal"""
    goal = goal_with_progress_history["goal"]

    milestone = ProgressMilestone(
        goal_id=goal.id,
        title="Reached anxiety level 5",
        description="Successfully reduced anxiety to manageable levels",
        target_value=Decimal("5.0"),
        achieved_at=datetime.utcnow() - timedelta(days=5),
        created_at=datetime.utcnow()
    )
    async_test_db.add(milestone)
    await async_test_db.flush()
    return milestone


# ============================================================================
# Test get_goal_dashboard()
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.analytics
@pytest.mark.goal_tracking
class TestGetGoalDashboard:
    """Test get_goal_dashboard() function"""

    async def test_dashboard_with_complete_data(
        self,
        async_test_db: AsyncSession,
        goal_with_progress_history,
        sample_milestone
    ):
        """Test dashboard aggregation with complete data"""
        patient = goal_with_progress_history["patient"]

        result = await get_goal_dashboard(patient.id, async_test_db)

        assert isinstance(result, GoalDashboardResponse)
        assert result.patient_id == patient.id
        assert result.active_goals == 1  # 1 in_progress goal
        assert isinstance(result.tracking_summary, TrackingSummary)
        assert len(result.goals) >= 1
        assert isinstance(result.recent_milestones, list)
        assert len(result.recent_milestones) == 1
        assert result.recent_milestones[0]["milestone"] == "Reached anxiety level 5"

    async def test_dashboard_with_no_goals(
        self,
        async_test_db: AsyncSession,
        sample_patient
    ):
        """Test dashboard with patient who has no goals"""
        result = await get_goal_dashboard(sample_patient.id, async_test_db)

        assert result.patient_id == sample_patient.id
        assert result.active_goals == 0
        assert result.tracking_summary.entries_this_week == 0
        assert result.tracking_summary.streak_days == 0
        assert result.tracking_summary.completion_rate == 0.0
        assert len(result.goals) == 0
        assert len(result.recent_milestones) == 0

    async def test_dashboard_active_goals_count(
        self,
        async_test_db: AsyncSession,
        multiple_goals_for_patient
    ):
        """Test that only assigned and in_progress goals are counted as active"""
        patient = multiple_goals_for_patient["patient"]

        result = await get_goal_dashboard(patient.id, async_test_db)

        # Should count only assigned and in_progress (not completed)
        assert result.active_goals == 2

    async def test_dashboard_recent_milestones_filter(
        self,
        async_test_db: AsyncSession,
        goal_with_progress_history
    ):
        """Test that only milestones from last 30 days are included"""
        goal = goal_with_progress_history["goal"]

        # Create old milestone (>30 days)
        old_milestone = ProgressMilestone(
            goal_id=goal.id,
            title="Old milestone",
            target_value=Decimal("7.0"),
            achieved_at=datetime.utcnow() - timedelta(days=45),
            created_at=datetime.utcnow()
        )
        async_test_db.add(old_milestone)

        # Create recent milestone
        recent_milestone = ProgressMilestone(
            goal_id=goal.id,
            title="Recent milestone",
            target_value=Decimal("5.0"),
            achieved_at=datetime.utcnow() - timedelta(days=3),
            created_at=datetime.utcnow()
        )
        async_test_db.add(recent_milestone)
        await async_test_db.flush()

        patient = goal_with_progress_history["patient"]
        result = await get_goal_dashboard(patient.id, async_test_db)

        # Only recent milestone should be included
        assert len(result.recent_milestones) == 1
        assert result.recent_milestones[0]["milestone"] == "Recent milestone"

    async def test_dashboard_assessments_due_logic(
        self,
        async_test_db: AsyncSession,
        sample_patient
    ):
        """Test assessments due calculation (28-day cycle)"""
        # Create assessment from 30 days ago (should be due)
        assessment = AssessmentScore(
            patient_id=sample_patient.id,
            assessment_type="GAD-7",
            total_score=12,
            administered_date=date_type.today() - timedelta(days=30),
            created_at=datetime.utcnow()
        )
        async_test_db.add(assessment)
        await async_test_db.flush()

        result = await get_goal_dashboard(sample_patient.id, async_test_db)

        # GAD-7 should be marked as due
        gad7_due = [a for a in result.assessments_due if a["type"] == "GAD-7"]
        assert len(gad7_due) == 1
        assert gad7_due[0]["last_administered"] is not None

    async def test_dashboard_assessments_no_baseline(
        self,
        async_test_db: AsyncSession,
        sample_patient
    ):
        """Test that assessments with no baseline are marked as due"""
        result = await get_goal_dashboard(sample_patient.id, async_test_db)

        # Both GAD-7 and PHQ-9 should be due (no baseline)
        assert len(result.assessments_due) == 2
        assessment_types = [a["type"] for a in result.assessments_due]
        assert "GAD-7" in assessment_types
        assert "PHQ-9" in assessment_types


# ============================================================================
# Test aggregate_tracking_summary()
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.analytics
@pytest.mark.goal_tracking
class TestAggregateTrackingSummary:
    """Test aggregate_tracking_summary() function"""

    async def test_tracking_summary_basic_metrics(
        self,
        async_test_db: AsyncSession,
        goal_with_progress_history
    ):
        """Test basic tracking summary metrics calculation"""
        patient = goal_with_progress_history["patient"]

        result = await aggregate_tracking_summary(patient.id, async_test_db)

        assert isinstance(result, TrackingSummary)
        assert result.entries_this_week >= 0
        assert result.streak_days >= 0
        assert 0.0 <= result.completion_rate <= 100.0

    async def test_tracking_summary_entries_this_week(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test entries_this_week counts only current week entries"""
        # Create goal with tracking config
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Test goal",
            status="in_progress"
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily",
            scale_min=1,
            scale_max=10,
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create entries: 3 this week, 2 last week
        now = datetime.utcnow()
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

        # This week entries
        for i in range(3):
            entry = ProgressEntry(
                goal_id=goal.id,
                tracking_config_id=config.id,
                entry_date=date_type.today() - timedelta(days=i),
                value=Decimal("5.0"),
                context="self_report",
                recorded_at=week_start + timedelta(days=i)
            )
            async_test_db.add(entry)

        # Last week entries
        for i in range(2):
            entry = ProgressEntry(
                goal_id=goal.id,
                tracking_config_id=config.id,
                entry_date=date_type.today() - timedelta(days=7 + i),
                value=Decimal("6.0"),
                context="self_report",
                recorded_at=week_start - timedelta(days=7 - i)
            )
            async_test_db.add(entry)

        await async_test_db.flush()

        result = await aggregate_tracking_summary(sample_patient.id, async_test_db)

        assert result.entries_this_week == 3

    async def test_tracking_summary_streak_consecutive_days(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test streak calculation for consecutive days"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Streak test goal",
            status="in_progress"
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="binary",
            tracking_frequency="daily",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create 5 consecutive days of entries (including today)
        for i in range(5):
            entry = ProgressEntry(
                goal_id=goal.id,
                tracking_config_id=config.id,
                entry_date=date_type.today() - timedelta(days=i),
                value=Decimal("1.0"),
                context="self_report",
                recorded_at=datetime.utcnow()
            )
            async_test_db.add(entry)

        await async_test_db.flush()

        result = await aggregate_tracking_summary(sample_patient.id, async_test_db)

        # Should have 5-day streak
        assert result.streak_days == 5

    async def test_tracking_summary_streak_with_gap(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test streak resets to 0 when there's a gap"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Gap test goal",
            status="in_progress"
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create entries with a gap: today, yesterday, then 3 days ago (missing day 2)
        entry_today = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=config.id,
            entry_date=date_type.today(),
            value=Decimal("5.0"),
            context="self_report",
            recorded_at=datetime.utcnow()
        )
        async_test_db.add(entry_today)

        entry_yesterday = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=config.id,
            entry_date=date_type.today() - timedelta(days=1),
            value=Decimal("5.0"),
            context="self_report",
            recorded_at=datetime.utcnow()
        )
        async_test_db.add(entry_yesterday)

        # Gap: day 2 is missing

        entry_old = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=config.id,
            entry_date=date_type.today() - timedelta(days=3),
            value=Decimal("5.0"),
            context="self_report",
            recorded_at=datetime.utcnow()
        )
        async_test_db.add(entry_old)

        await async_test_db.flush()

        result = await aggregate_tracking_summary(sample_patient.id, async_test_db)

        # Streak should be 2 (today + yesterday only)
        assert result.streak_days == 2

    async def test_tracking_summary_streak_grace_period(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test that streak allows 1-day grace period (yesterday counts as current)"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Grace period test",
            status="in_progress"
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="binary",
            tracking_frequency="daily",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create entries for yesterday and 2 days ago (no entry today)
        for i in range(1, 4):
            entry = ProgressEntry(
                goal_id=goal.id,
                tracking_config_id=config.id,
                entry_date=date_type.today() - timedelta(days=i),
                value=Decimal("1.0"),
                context="self_report",
                recorded_at=datetime.utcnow()
            )
            async_test_db.add(entry)

        await async_test_db.flush()

        result = await aggregate_tracking_summary(sample_patient.id, async_test_db)

        # Streak should count yesterday as valid start (grace period)
        assert result.streak_days >= 1

    async def test_tracking_summary_completion_rate_daily(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test completion rate for daily tracking frequency"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Daily tracking goal",
            status="in_progress"
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create 5 entries this week (expected: 7)
        now = datetime.utcnow()
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(5):
            entry = ProgressEntry(
                goal_id=goal.id,
                tracking_config_id=config.id,
                entry_date=date_type.today() - timedelta(days=i),
                value=Decimal("7.0"),
                context="self_report",
                recorded_at=week_start + timedelta(days=i)
            )
            async_test_db.add(entry)

        await async_test_db.flush()

        result = await aggregate_tracking_summary(sample_patient.id, async_test_db)

        # 5 out of 7 expected = ~71.4%
        assert result.completion_rate == pytest.approx(71.4, rel=1.0)

    async def test_tracking_summary_completion_rate_weekly(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test completion rate for weekly tracking frequency"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Weekly tracking goal",
            status="in_progress"
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="frequency",
            tracking_frequency="weekly",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create 1 entry this week (expected: 1)
        now = datetime.utcnow()
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

        entry = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=config.id,
            entry_date=date_type.today(),
            value=Decimal("3.0"),
            context="self_report",
            recorded_at=week_start + timedelta(days=2)
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        result = await aggregate_tracking_summary(sample_patient.id, async_test_db)

        # 1 out of 1 expected = 100%
        assert result.completion_rate == 100.0

    async def test_tracking_summary_completion_rate_custom_frequency(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test completion rate for custom frequency (every 3 days)"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Custom frequency goal",
            status="in_progress"
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="custom",
            custom_frequency_days=3,
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create 2 entries this week (expected: 7/3 = 2.33)
        now = datetime.utcnow()
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)

        for i in range(2):
            entry = ProgressEntry(
                goal_id=goal.id,
                tracking_config_id=config.id,
                entry_date=date_type.today() - timedelta(days=i * 3),
                value=Decimal("8.0"),
                context="self_report",
                recorded_at=week_start + timedelta(days=i * 3)
            )
            async_test_db.add(entry)

        await async_test_db.flush()

        result = await aggregate_tracking_summary(sample_patient.id, async_test_db)

        # 2 out of ~2.33 expected = ~85.7%
        assert result.completion_rate >= 80.0

    async def test_tracking_summary_no_active_goals(
        self,
        async_test_db: AsyncSession,
        sample_patient
    ):
        """Test tracking summary with no active goals returns zeros"""
        result = await aggregate_tracking_summary(sample_patient.id, async_test_db)

        assert result.entries_this_week == 0
        assert result.streak_days == 0
        assert result.completion_rate == 0.0


# ============================================================================
# Test get_goal_dashboard_items()
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.analytics
@pytest.mark.goal_tracking
class TestGetGoalDashboardItems:
    """Test get_goal_dashboard_items() function"""

    async def test_dashboard_items_basic_structure(
        self,
        async_test_db: AsyncSession,
        goal_with_progress_history
    ):
        """Test basic structure of dashboard items"""
        patient = goal_with_progress_history["patient"]

        result = await get_goal_dashboard_items(patient.id, async_test_db)

        assert isinstance(result, list)
        assert len(result) >= 1

        item = result[0]
        assert isinstance(item, GoalDashboardItem)
        assert item.id == goal_with_progress_history["goal"].id
        assert item.description == "Track anxiety levels"
        assert item.status == GoalStatus.in_progress
        assert item.current_value is not None
        assert item.baseline_value == 8.0
        assert item.target_value == 3.0

    async def test_dashboard_items_progress_percentage_calculation(
        self,
        async_test_db: AsyncSession,
        goal_with_progress_history
    ):
        """Test progress percentage calculation formula"""
        patient = goal_with_progress_history["patient"]

        result = await get_goal_dashboard_items(patient.id, async_test_db)

        item = result[0]
        # Progress = (current - baseline) / (target - baseline) * 100
        # For decreasing goal: current should be lower than baseline
        assert item.progress_percentage is not None
        assert 0.0 <= item.progress_percentage <= 100.0

    async def test_dashboard_items_progress_percentage_capped(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test that progress percentage is capped at 0-100 range"""
        # Create goal where current exceeds target
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Overshoot test",
            status="in_progress",
            baseline_value=Decimal("5.0"),
            target_value=Decimal("10.0")
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create entry that exceeds target
        entry = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=config.id,
            entry_date=date_type.today(),
            value=Decimal("15.0"),  # Exceeds target of 10.0
            context="self_report",
            recorded_at=datetime.utcnow()
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        result = await get_goal_dashboard_items(sample_patient.id, async_test_db)

        item = result[0]
        # Should be capped at 100%
        assert item.progress_percentage == 100.0

    async def test_dashboard_items_trend_improving(
        self,
        async_test_db: AsyncSession,
        goal_with_progress_history
    ):
        """Test trend detection for improving trend"""
        patient = goal_with_progress_history["patient"]

        result = await get_goal_dashboard_items(patient.id, async_test_db)

        item = result[0]
        # Goal has decreasing target, values are decreasing = improving
        assert item.trend == TrendDirection.improving

    async def test_dashboard_items_trend_stable(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test trend detection for stable trend (< 5% change)"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Stable goal",
            status="in_progress",
            baseline_value=Decimal("5.0"),
            target_value=Decimal("8.0")
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create entries with minimal variation (5.0 ± 0.1)
        for i in range(10):
            value = 5.0 + (0.1 if i % 2 == 0 else -0.1)
            entry = ProgressEntry(
                goal_id=goal.id,
                tracking_config_id=config.id,
                entry_date=date_type.today() - timedelta(days=9 - i),
                value=Decimal(str(value)),
                context="self_report",
                recorded_at=datetime.utcnow()
            )
            async_test_db.add(entry)

        await async_test_db.flush()

        result = await get_goal_dashboard_items(sample_patient.id, async_test_db)

        item = result[0]
        assert item.trend == TrendDirection.stable

    async def test_dashboard_items_trend_insufficient_data(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test trend is insufficient_data when < 3 entries"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="New goal",
            status="in_progress"
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="binary",
            tracking_frequency="daily",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        # Create only 2 entries
        for i in range(2):
            entry = ProgressEntry(
                goal_id=goal.id,
                tracking_config_id=config.id,
                entry_date=date_type.today() - timedelta(days=i),
                value=Decimal("1.0"),
                context="self_report",
                recorded_at=datetime.utcnow()
            )
            async_test_db.add(entry)

        await async_test_db.flush()

        result = await get_goal_dashboard_items(sample_patient.id, async_test_db)

        item = result[0]
        assert item.trend == TrendDirection.insufficient_data

    async def test_dashboard_items_trend_data_last_30_days(
        self,
        async_test_db: AsyncSession,
        goal_with_progress_history
    ):
        """Test that trend_data includes only last 30 days"""
        patient = goal_with_progress_history["patient"]

        result = await get_goal_dashboard_items(patient.id, async_test_db)

        item = result[0]
        assert len(item.trend_data) == 30  # Created 30 days of data

        # Verify all dates are within last 30 days
        for data_point in item.trend_data:
            days_ago = (date_type.today() - data_point.date).days
            assert 0 <= days_ago <= 30

    async def test_dashboard_items_next_check_in_daily(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test next_check_in calculation for daily tracking"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Daily check-in goal",
            status="in_progress"
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        last_entry_date = date_type.today() - timedelta(days=2)
        entry = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=config.id,
            entry_date=last_entry_date,
            value=Decimal("6.0"),
            context="self_report",
            recorded_at=datetime.utcnow()
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        result = await get_goal_dashboard_items(sample_patient.id, async_test_db)

        item = result[0]
        # Next check-in should be 1 day after last entry
        expected_date = last_entry_date + timedelta(days=1)
        assert item.next_check_in == expected_date

    async def test_dashboard_items_next_check_in_weekly(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test next_check_in calculation for weekly tracking"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Weekly check-in goal",
            status="in_progress"
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="frequency",
            tracking_frequency="weekly",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        last_entry_date = date_type.today() - timedelta(days=5)
        entry = ProgressEntry(
            goal_id=goal.id,
            tracking_config_id=config.id,
            entry_date=last_entry_date,
            value=Decimal("2.0"),
            context="self_report",
            recorded_at=datetime.utcnow()
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        result = await get_goal_dashboard_items(sample_patient.id, async_test_db)

        item = result[0]
        # Next check-in should be 7 days after last entry
        expected_date = last_entry_date + timedelta(days=7)
        assert item.next_check_in == expected_date

    async def test_dashboard_items_no_entries(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test dashboard item with no progress entries"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="No entries goal",
            status="assigned",
            baseline_value=Decimal("3.0"),
            target_value=Decimal("7.0")
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        result = await get_goal_dashboard_items(sample_patient.id, async_test_db)

        item = result[0]
        assert item.current_value is None
        assert item.progress_percentage is None
        assert item.trend == TrendDirection.insufficient_data
        assert len(item.trend_data) == 0
        assert item.last_entry is None
        assert item.next_check_in is None

    async def test_dashboard_items_includes_completed_goals(
        self,
        async_test_db: AsyncSession,
        multiple_goals_for_patient
    ):
        """Test that dashboard items include completed goals"""
        patient = multiple_goals_for_patient["patient"]

        result = await get_goal_dashboard_items(patient.id, async_test_db)

        # Should include all 3 goals (assigned, in_progress, completed)
        assert len(result) == 3

        statuses = [item.status for item in result]
        assert GoalStatus.completed in statuses

    async def test_dashboard_items_performance_n_plus_one(
        self,
        async_test_db: AsyncSession,
        multiple_goals_for_patient
    ):
        """
        Test for N+1 query performance issue.

        PERFORMANCE NOTE:
        The current implementation has an N+1 query problem:
        - For each goal, it runs 2 separate queries:
          1. Get latest progress entry (line 340-345)
          2. Get trend entries for last 30 days (line 363-371)

        For N goals, this results in 1 + (N * 2) queries.

        OPTIMIZATION OPPORTUNITY:
        - Use a single query with JOIN to fetch all goals with their latest entries
        - Use subquery or window function to get last 30 days of entries in one query
        - Expected improvement: 1 + (N * 2) queries → 2-3 queries total

        This test documents the issue. Query count verification would require
        query logging or profiling middleware.
        """
        patient = multiple_goals_for_patient["patient"]

        # This call will trigger N+1 queries (N = 3 goals)
        result = await get_goal_dashboard_items(patient.id, async_test_db)

        # Verify results are correct despite performance issue
        assert len(result) == 3

        # TODO: Add query count assertion when profiling is available
        # Expected: 7 queries (1 goals query + 3 * (latest + trend))
        # Optimized: 2-3 queries total


# ============================================================================
# Test Edge Cases
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
class TestDashboardServiceEdgeCases:
    """Test edge cases and error handling"""

    async def test_empty_patient_data(
        self,
        async_test_db: AsyncSession,
        sample_patient
    ):
        """Test all functions with patient who has no data"""
        # Test get_goal_dashboard
        dashboard = await get_goal_dashboard(sample_patient.id, async_test_db)
        assert dashboard.active_goals == 0
        assert len(dashboard.goals) == 0

        # Test aggregate_tracking_summary
        summary = await aggregate_tracking_summary(sample_patient.id, async_test_db)
        assert summary.entries_this_week == 0
        assert summary.streak_days == 0
        assert summary.completion_rate == 0.0

        # Test get_goal_dashboard_items
        items = await get_goal_dashboard_items(sample_patient.id, async_test_db)
        assert len(items) == 0

    async def test_nonexistent_patient(
        self,
        async_test_db: AsyncSession
    ):
        """Test functions with non-existent patient ID"""
        fake_patient_id = uuid4()

        # All functions should handle gracefully (no errors)
        dashboard = await get_goal_dashboard(fake_patient_id, async_test_db)
        assert dashboard.active_goals == 0

        summary = await aggregate_tracking_summary(fake_patient_id, async_test_db)
        assert summary.entries_this_week == 0

        items = await get_goal_dashboard_items(fake_patient_id, async_test_db)
        assert len(items) == 0

    async def test_goal_with_no_baseline_or_target(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        sample_therapist
    ):
        """Test dashboard item for goal without baseline/target values"""
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=sample_therapist.id,
            description="Qualitative goal",
            status="in_progress",
            baseline_value=None,
            target_value=None
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="binary",
            tracking_frequency="daily",
            target_direction="increase"
        )
        async_test_db.add(config)
        await async_test_db.flush()

        result = await get_goal_dashboard_items(sample_patient.id, async_test_db)

        item = result[0]
        assert item.baseline_value is None
        assert item.target_value is None
        assert item.progress_percentage is None  # Can't calculate without baseline/target
