# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for MilestoneDetector service.

Tests cover:
1. check_milestones - Percentage improvement milestone detection (25%, 50%, 75%, 100%)
2. get_or_create_milestone - Milestone persistence and idempotency
3. check_streak_milestones - Consecutive check-in streak detection (7, 14, 30, 60, 90 days)

Edge cases tested:
- No progress (baseline == current)
- Baseline == target (no progress possible)
- Already-achieved milestone handling (idempotency)
- Multiple milestones in single check
- Same-day multiple entries (don't break streak)
- Broken streaks
- Different goal types (increasing vs decreasing targets)
- Negative progress (regressing)
"""
import pytest
import pytest_asyncio
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.milestone_detector import (
    check_milestones,
    get_or_create_milestone,
    check_streak_milestones,
    PERCENTAGE_THRESHOLDS,
    STREAK_THRESHOLDS,
)
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import ProgressEntry, ProgressMilestone
from tests.utils.test_helpers import (
    create_test_goal,
    create_test_progress_entry,
)


# ============================================================================
# Fixtures for Milestone Tests
# ============================================================================

@pytest_asyncio.fixture
async def test_goal_decreasing(async_test_db: AsyncSession, sample_patient, therapist_user, sample_session) -> TreatmentGoal:
    """
    Create a goal where lower values are better (e.g., anxiety reduction).
    Baseline: 8.0, Target: 2.0
    """
    goal = create_test_goal(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_id=sample_session.id,
        description="Reduce anxiety level from 8 to 2",
        category="anxiety_management",
        baseline_value=8.0,
        target_value=2.0,
        status="in_progress"
    )
    async_test_db.add(goal)
    await async_test_db.flush()
    return goal


@pytest_asyncio.fixture
async def test_goal_increasing(async_test_db: AsyncSession, sample_patient, therapist_user, sample_session) -> TreatmentGoal:
    """
    Create a goal where higher values are better (e.g., confidence building).
    Baseline: 3.0, Target: 8.0
    """
    goal = create_test_goal(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_id=sample_session.id,
        description="Increase confidence from 3 to 8",
        category="self_esteem",
        baseline_value=3.0,
        target_value=8.0,
        status="in_progress"
    )
    async_test_db.add(goal)
    await async_test_db.flush()
    return goal


@pytest_asyncio.fixture
async def test_goal_no_baseline(async_test_db: AsyncSession, sample_patient, therapist_user, sample_session) -> TreatmentGoal:
    """
    Create a goal without baseline/target values (qualitative goal).
    """
    goal = create_test_goal(
        patient_id=sample_patient.id,
        therapist_id=therapist_user.id,
        session_id=sample_session.id,
        description="Practice mindfulness daily",
        category="behavioral",
        baseline_value=None,
        target_value=None,
        status="assigned"
    )
    async_test_db.add(goal)
    await async_test_db.flush()
    return goal


# ============================================================================
# TestCheckMilestones - Percentage Improvement Detection
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
class TestCheckMilestones:
    """Test percentage-based milestone detection"""

    async def test_detect_25_percent_milestone_decreasing(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test detecting 25% improvement for decreasing target (anxiety: 8 → 2)"""
        # 25% improvement: 8.0 - (8.0 - 2.0) * 0.25 = 6.5
        entry = create_test_progress_entry(
            goal_id=test_goal_decreasing.id,
            value=6.5,
            entry_date=date.today(),
            context="self_report"
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        milestones = await check_milestones(test_goal_decreasing, entry, async_test_db)

        assert len(milestones) == 1
        assert milestones[0].milestone_type == "percentage"
        assert milestones[0].title == "25% Improvement Achieved"
        assert milestones[0].target_value == Decimal("0.25")
        assert milestones[0].achieved_at is not None

    async def test_detect_50_percent_milestone_increasing(
        self,
        async_test_db: AsyncSession,
        test_goal_increasing: TreatmentGoal
    ):
        """Test detecting 50% improvement for increasing target (confidence: 3 → 8)"""
        # 50% improvement: 3.0 + (8.0 - 3.0) * 0.50 = 5.5
        entry = create_test_progress_entry(
            goal_id=test_goal_increasing.id,
            value=5.5,
            entry_date=date.today(),
            context="self_report"
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        milestones = await check_milestones(test_goal_increasing, entry, async_test_db)

        # Should detect both 25% and 50% milestones
        assert len(milestones) == 2
        milestone_percentages = {int(m.target_value * 100) for m in milestones}
        assert 25 in milestone_percentages
        assert 50 in milestone_percentages

    async def test_detect_75_percent_milestone(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test detecting 75% improvement milestone"""
        # 75% improvement: 8.0 - (8.0 - 2.0) * 0.75 = 3.5
        entry = create_test_progress_entry(
            goal_id=test_goal_decreasing.id,
            value=3.5,
            entry_date=date.today(),
            context="self_report"
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        milestones = await check_milestones(test_goal_decreasing, entry, async_test_db)

        # Should detect 25%, 50%, and 75% milestones
        assert len(milestones) == 3
        milestone_percentages = {int(m.target_value * 100) for m in milestones}
        assert milestone_percentages == {25, 50, 75}

    async def test_detect_100_percent_milestone(
        self,
        async_test_db: AsyncSession,
        test_goal_increasing: TreatmentGoal
    ):
        """Test detecting 100% completion milestone"""
        # 100% improvement: reached target value 8.0
        entry = create_test_progress_entry(
            goal_id=test_goal_increasing.id,
            value=8.0,
            entry_date=date.today(),
            context="self_report"
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        milestones = await check_milestones(test_goal_increasing, entry, async_test_db)

        # Should detect all 4 milestones (25%, 50%, 75%, 100%)
        assert len(milestones) == 4
        milestone_percentages = {int(m.target_value * 100) for m in milestones}
        assert milestone_percentages == {25, 50, 75, 100}

    async def test_no_milestone_below_threshold(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test that no milestones are detected for insufficient progress"""
        # Only 10% improvement: 8.0 - (8.0 - 2.0) * 0.10 = 7.4
        entry = create_test_progress_entry(
            goal_id=test_goal_decreasing.id,
            value=7.4,
            entry_date=date.today(),
            context="self_report"
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        milestones = await check_milestones(test_goal_decreasing, entry, async_test_db)

        assert len(milestones) == 0

    async def test_no_milestone_for_regression(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test that no milestones are detected when progress regresses"""
        # Regression: value increased from baseline
        entry = create_test_progress_entry(
            goal_id=test_goal_decreasing.id,
            value=9.0,  # Worse than baseline of 8.0
            entry_date=date.today(),
            context="self_report"
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        milestones = await check_milestones(test_goal_decreasing, entry, async_test_db)

        assert len(milestones) == 0

    async def test_milestone_idempotency(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test that already-achieved milestones are not re-created"""
        # First entry achieves 50% milestone
        entry1 = create_test_progress_entry(
            goal_id=test_goal_decreasing.id,
            value=5.0,
            entry_date=date.today() - timedelta(days=1),
            context="self_report"
        )
        async_test_db.add(entry1)
        await async_test_db.flush()

        milestones1 = await check_milestones(test_goal_decreasing, entry1, async_test_db)
        assert len(milestones1) == 2  # 25% and 50%

        # Second entry also at 50% improvement (should not re-create)
        entry2 = create_test_progress_entry(
            goal_id=test_goal_decreasing.id,
            value=5.0,
            entry_date=date.today(),
            context="self_report"
        )
        async_test_db.add(entry2)
        await async_test_db.flush()

        milestones2 = await check_milestones(test_goal_decreasing, entry2, async_test_db)
        assert len(milestones2) == 0  # No new milestones

    async def test_no_milestone_without_baseline(
        self,
        async_test_db: AsyncSession,
        test_goal_no_baseline: TreatmentGoal
    ):
        """Test that milestones are not detected for goals without baseline/target"""
        entry = create_test_progress_entry(
            goal_id=test_goal_no_baseline.id,
            value=5.0,
            entry_date=date.today(),
            context="self_report"
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        milestones = await check_milestones(test_goal_no_baseline, entry, async_test_db)

        assert len(milestones) == 0

    async def test_baseline_equals_target(
        self,
        async_test_db: AsyncSession,
        sample_patient,
        therapist_user,
        sample_session
    ):
        """Test edge case where baseline equals target (no progress possible)"""
        goal = create_test_goal(
            patient_id=sample_patient.id,
            therapist_id=therapist_user.id,
            session_id=sample_session.id,
            description="Maintain current level",
            baseline_value=5.0,
            target_value=5.0  # Same as baseline
        )
        async_test_db.add(goal)
        await async_test_db.flush()

        entry = create_test_progress_entry(
            goal_id=goal.id,
            value=5.0,
            entry_date=date.today()
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        milestones = await check_milestones(goal, entry, async_test_db)

        assert len(milestones) == 0

    async def test_entry_without_value(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test that entries without value don't trigger milestones"""
        entry = create_test_progress_entry(
            goal_id=test_goal_decreasing.id,
            value=None,  # No value
            entry_date=date.today(),
            context="self_report"
        )
        async_test_db.add(entry)
        await async_test_db.flush()

        milestones = await check_milestones(test_goal_decreasing, entry, async_test_db)

        assert len(milestones) == 0


# ============================================================================
# TestGetOrCreateMilestone - Milestone Persistence
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
class TestGetOrCreateMilestone:
    """Test milestone creation and retrieval logic"""

    async def test_create_new_milestone(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test creating a new milestone record"""
        milestone = await get_or_create_milestone(
            goal_id=test_goal_decreasing.id,
            threshold=0.50,
            db=async_test_db
        )

        assert milestone is not None
        assert milestone.goal_id == test_goal_decreasing.id
        assert milestone.milestone_type == "percentage"
        assert milestone.title == "50% Improvement Achieved"
        assert milestone.target_value == Decimal("0.50")
        assert milestone.achieved_at is None  # Not achieved yet

    async def test_retrieve_existing_milestone(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test retrieving an existing milestone instead of creating duplicate"""
        # Create milestone first
        milestone1 = await get_or_create_milestone(
            goal_id=test_goal_decreasing.id,
            threshold=0.25,
            db=async_test_db
        )
        milestone1_id = milestone1.id

        # Try to get same milestone again
        milestone2 = await get_or_create_milestone(
            goal_id=test_goal_decreasing.id,
            threshold=0.25,
            db=async_test_db
        )

        # Should return the same milestone, not create a new one
        assert milestone2.id == milestone1_id

    async def test_create_all_percentage_thresholds(
        self,
        async_test_db: AsyncSession,
        test_goal_increasing: TreatmentGoal
    ):
        """Test creating milestones for all percentage thresholds"""
        milestones = []
        for threshold in PERCENTAGE_THRESHOLDS:
            milestone = await get_or_create_milestone(
                goal_id=test_goal_increasing.id,
                threshold=threshold,
                db=async_test_db
            )
            milestones.append(milestone)

        assert len(milestones) == 4
        percentages = {int(m.target_value * 100) for m in milestones}
        assert percentages == {25, 50, 75, 100}

    async def test_milestone_title_formatting(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test that milestone titles are correctly formatted"""
        milestone_75 = await get_or_create_milestone(
            goal_id=test_goal_decreasing.id,
            threshold=0.75,
            db=async_test_db
        )

        assert milestone_75.title == "75% Improvement Achieved"
        assert "75% progress toward goal target" in milestone_75.description

    async def test_milestone_description_includes_details(
        self,
        async_test_db: AsyncSession,
        test_goal_increasing: TreatmentGoal
    ):
        """Test that milestone descriptions include meaningful details"""
        milestone = await get_or_create_milestone(
            goal_id=test_goal_increasing.id,
            threshold=1.0,
            db=async_test_db
        )

        assert "100%" in milestone.title
        assert "progress toward goal target" in milestone.description


# ============================================================================
# TestCheckStreakMilestones - Streak Detection
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.goal_tracking
class TestCheckStreakMilestones:
    """Test consecutive check-in streak detection"""

    async def test_detect_7_day_streak(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test detecting 7-day consecutive streak"""
        entries = []
        base_date = date.today() - timedelta(days=7)

        for i in range(7):
            entry = create_test_progress_entry(
                goal_id=test_goal_decreasing.id,
                value=7.0 - (i * 0.1),
                entry_date=base_date + timedelta(days=i),
                context="self_report"
            )
            async_test_db.add(entry)
            entries.append(entry)

        await async_test_db.flush()

        milestones = await check_streak_milestones(
            goal_id=test_goal_decreasing.id,
            entries=entries,
            db=async_test_db
        )

        assert len(milestones) == 1
        assert milestones[0].milestone_type == "streak"
        assert milestones[0].title == "7-Day Streak Achieved"
        assert milestones[0].target_value == Decimal("7")
        assert milestones[0].achieved_at is not None

    async def test_detect_14_day_streak(
        self,
        async_test_db: AsyncSession,
        test_goal_increasing: TreatmentGoal
    ):
        """Test detecting 14-day consecutive streak"""
        entries = []
        base_date = date.today() - timedelta(days=14)

        for i in range(14):
            entry = create_test_progress_entry(
                goal_id=test_goal_increasing.id,
                value=3.0 + (i * 0.1),
                entry_date=base_date + timedelta(days=i),
                context="self_report"
            )
            async_test_db.add(entry)
            entries.append(entry)

        await async_test_db.flush()

        milestones = await check_streak_milestones(
            goal_id=test_goal_increasing.id,
            entries=entries,
            db=async_test_db
        )

        # Should detect both 7-day and 14-day streaks
        assert len(milestones) == 2
        streak_days = {int(m.target_value) for m in milestones}
        assert 7 in streak_days
        assert 14 in streak_days

    async def test_detect_30_day_streak(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test detecting 30-day consecutive streak"""
        entries = []
        base_date = date.today() - timedelta(days=30)

        for i in range(30):
            entry = create_test_progress_entry(
                goal_id=test_goal_decreasing.id,
                value=8.0 - (i * 0.05),
                entry_date=base_date + timedelta(days=i),
                context="self_report"
            )
            async_test_db.add(entry)
            entries.append(entry)

        await async_test_db.flush()

        milestones = await check_streak_milestones(
            goal_id=test_goal_decreasing.id,
            entries=entries,
            db=async_test_db
        )

        # Should detect 7, 14, and 30-day streaks
        assert len(milestones) == 3
        streak_days = {int(m.target_value) for m in milestones}
        assert streak_days == {7, 14, 30}

    async def test_broken_streak_resets_count(
        self,
        async_test_db: AsyncSession,
        test_goal_increasing: TreatmentGoal
    ):
        """Test that broken streak doesn't count toward milestone"""
        entries = []
        base_date = date.today() - timedelta(days=10)

        # 5 consecutive days
        for i in range(5):
            entry = create_test_progress_entry(
                goal_id=test_goal_increasing.id,
                value=4.0,
                entry_date=base_date + timedelta(days=i),
                context="self_report"
            )
            async_test_db.add(entry)
            entries.append(entry)

        # Skip day 6 (break the streak)

        # Another 3 consecutive days
        for i in range(3):
            entry = create_test_progress_entry(
                goal_id=test_goal_increasing.id,
                value=5.0,
                entry_date=base_date + timedelta(days=7 + i),
                context="self_report"
            )
            async_test_db.add(entry)
            entries.append(entry)

        await async_test_db.flush()

        milestones = await check_streak_milestones(
            goal_id=test_goal_increasing.id,
            entries=entries,
            db=async_test_db
        )

        # Current streak is only 3 days (not enough for 7-day milestone)
        assert len(milestones) == 0

    async def test_same_day_multiple_entries_dont_break_streak(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test that multiple entries on same day don't break streak"""
        entries = []
        base_date = date.today() - timedelta(days=7)

        for i in range(7):
            # Add 2 entries on the same day
            for j in range(2):
                entry = create_test_progress_entry(
                    goal_id=test_goal_decreasing.id,
                    value=7.0 - (i * 0.1),
                    entry_date=base_date + timedelta(days=i),
                    entry_time=time(hour=10 + (j * 6), minute=0),
                    context="self_report"
                )
                async_test_db.add(entry)
                entries.append(entry)

        await async_test_db.flush()

        milestones = await check_streak_milestones(
            goal_id=test_goal_decreasing.id,
            entries=entries,
            db=async_test_db
        )

        # Should still detect 7-day streak
        assert len(milestones) == 1
        assert int(milestones[0].target_value) == 7

    async def test_no_streak_with_insufficient_entries(
        self,
        async_test_db: AsyncSession,
        test_goal_increasing: TreatmentGoal
    ):
        """Test that no streak milestones are detected with < 7 entries"""
        entries = []
        base_date = date.today() - timedelta(days=5)

        for i in range(5):
            entry = create_test_progress_entry(
                goal_id=test_goal_increasing.id,
                value=4.0,
                entry_date=base_date + timedelta(days=i),
                context="self_report"
            )
            async_test_db.add(entry)
            entries.append(entry)

        await async_test_db.flush()

        milestones = await check_streak_milestones(
            goal_id=test_goal_increasing.id,
            entries=entries,
            db=async_test_db
        )

        assert len(milestones) == 0

    async def test_empty_entries_list(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test that empty entries list returns no milestones"""
        milestones = await check_streak_milestones(
            goal_id=test_goal_decreasing.id,
            entries=[],
            db=async_test_db
        )

        assert len(milestones) == 0

    async def test_streak_milestone_idempotency(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test that existing streak milestones are not re-created"""
        entries = []
        base_date = date.today() - timedelta(days=7)

        for i in range(7):
            entry = create_test_progress_entry(
                goal_id=test_goal_decreasing.id,
                value=7.0,
                entry_date=base_date + timedelta(days=i),
                context="self_report"
            )
            async_test_db.add(entry)
            entries.append(entry)

        await async_test_db.flush()

        # First check should create milestone
        milestones1 = await check_streak_milestones(
            goal_id=test_goal_decreasing.id,
            entries=entries,
            db=async_test_db
        )
        assert len(milestones1) == 1

        # Second check should not create duplicate
        milestones2 = await check_streak_milestones(
            goal_id=test_goal_decreasing.id,
            entries=entries,
            db=async_test_db
        )
        assert len(milestones2) == 0

    async def test_unsorted_entries_are_sorted(
        self,
        async_test_db: AsyncSession,
        test_goal_increasing: TreatmentGoal
    ):
        """Test that unsorted entries are correctly sorted for streak calculation"""
        entries = []
        base_date = date.today() - timedelta(days=7)

        # Add entries in random order
        dates = [base_date + timedelta(days=i) for i in range(7)]
        import random
        random.shuffle(dates)

        for entry_date in dates:
            entry = create_test_progress_entry(
                goal_id=test_goal_increasing.id,
                value=5.0,
                entry_date=entry_date,
                context="self_report"
            )
            async_test_db.add(entry)
            entries.append(entry)

        await async_test_db.flush()

        milestones = await check_streak_milestones(
            goal_id=test_goal_increasing.id,
            entries=entries,
            db=async_test_db
        )

        # Should still detect 7-day streak despite unsorted input
        assert len(milestones) == 1
        assert int(milestones[0].target_value) == 7

    async def test_all_streak_thresholds(
        self,
        async_test_db: AsyncSession,
        test_goal_decreasing: TreatmentGoal
    ):
        """Test detecting all streak threshold milestones (7, 14, 30, 60, 90)"""
        entries = []
        base_date = date.today() - timedelta(days=90)

        # Create 90 consecutive days of entries
        for i in range(90):
            entry = create_test_progress_entry(
                goal_id=test_goal_decreasing.id,
                value=8.0 - (i * 0.05),
                entry_date=base_date + timedelta(days=i),
                context="self_report"
            )
            async_test_db.add(entry)
            entries.append(entry)

        await async_test_db.flush()

        milestones = await check_streak_milestones(
            goal_id=test_goal_decreasing.id,
            entries=entries,
            db=async_test_db
        )

        # Should detect all 5 streak thresholds
        assert len(milestones) == 5
        streak_days = {int(m.target_value) for m in milestones}
        assert streak_days == {7, 14, 30, 60, 90}
