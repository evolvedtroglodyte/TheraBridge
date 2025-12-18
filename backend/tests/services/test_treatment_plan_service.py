# -*- coding: utf-8 -*-
"""
Comprehensive unit tests for treatment plan service.

Tests cover:
1. calculate_goal_progress - goal progress calculation with sub-goals and progress entries
2. check_review_due - review due date checking and status determination
3. generate_progress_report - comprehensive progress report generation
4. recalculate_plan_progress - plan-level progress recalculation
5. get_goals_by_status - goal filtering by status with ordering
6. Edge cases: no data, empty lists, missing dates, error handling

Edge cases tested:
- Goals with no sub-goals or progress entries
- Empty treatment plans
- Missing review dates
- Progress calculation with weighted averages
- Percentage calculations
- Date boundary conditions
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, date
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.treatment_plan_service import (
    calculate_goal_progress,
    check_review_due,
    generate_progress_report,
    recalculate_plan_progress,
    get_goals_by_status
)
from app.models.treatment_models import (
    TreatmentPlan,
    TreatmentPlanGoal as TreatmentGoal,  # Aliased for convenience
    GoalProgress,
    Intervention,
    GoalIntervention
)
from app.models.db_models import User
from app.models.schemas import UserRole
from app.auth.utils import get_password_hash


# ============================================================================
# Fixtures for Treatment Plan Service Tests
# ============================================================================

@pytest_asyncio.fixture
async def therapist_and_patient(async_test_db: AsyncSession):
    """
    Create a therapist and patient for treatment plan tests.

    Returns:
        Dict with therapist and patient User objects
    """
    # Create therapist
    therapist = User(
        email="treatment.therapist@test.com",
        hashed_password=get_password_hash("SecurePass123!"),
        first_name="Treatment",
        last_name="Therapist",
        full_name="Treatment Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=True
    )
    async_test_db.add(therapist)

    # Create patient
    patient = User(
        email="treatment.patient@test.com",
        hashed_password=get_password_hash("PatientPass123!"),
        first_name="Treatment",
        last_name="Patient",
        full_name="Treatment Patient",
        role=UserRole.patient,
        is_active=True,
        is_verified=False
    )
    async_test_db.add(patient)
    await async_test_db.flush()

    return {
        "therapist": therapist,
        "patient": patient
    }


@pytest_asyncio.fixture
async def treatment_plan_with_goals(async_test_db: AsyncSession, therapist_and_patient):
    """
    Create a treatment plan with goals at various progress levels.

    Structure:
    - 1 treatment plan
    - 5 goals with different statuses and progress levels
    - Sub-goals for hierarchical testing
    - Progress entries for rating-based calculation

    Returns:
        Dict with plan, goals, and progress entries
    """
    therapist = therapist_and_patient["therapist"]
    patient = therapist_and_patient["patient"]

    # Create treatment plan
    plan = TreatmentPlan(
        patient_id=patient.id,
        therapist_id=therapist.id,
        title="Anxiety and Depression Treatment Plan",
        diagnosis_codes=[{"code": "F41.1", "description": "Generalized Anxiety Disorder"}],
        presenting_problems=["anxiety", "depression", "sleep issues"],
        start_date=date.today() - timedelta(days=30),
        target_end_date=date.today() + timedelta(days=90),
        status='active',
        review_frequency_days=90,
        next_review_date=date.today() + timedelta(days=10)
    )
    async_test_db.add(plan)
    await async_test_db.flush()

    # Goal 1: Long-term goal with sub-goals (for weighted average testing)
    goal1 = TreatmentGoal(
        plan_id=plan.id,
        goal_type='long_term',
        description='Reduce anxiety symptoms to manageable levels',
        status='in_progress',
        progress_percentage=0,  # Will be calculated from sub-goals
        priority=1
    )
    async_test_db.add(goal1)
    await async_test_db.flush()

    # Sub-goals for goal1 (weighted average calculation)
    subgoal1a = TreatmentGoal(
        plan_id=plan.id,
        parent_goal_id=goal1.id,
        goal_type='short_term',
        description='Practice breathing exercises daily',
        status='in_progress',
        progress_percentage=80,
        priority=1  # Highest priority = highest weight
    )
    async_test_db.add(subgoal1a)

    subgoal1b = TreatmentGoal(
        plan_id=plan.id,
        parent_goal_id=goal1.id,
        goal_type='short_term',
        description='Identify anxiety triggers',
        status='in_progress',
        progress_percentage=60,
        priority=2  # Medium priority
    )
    async_test_db.add(subgoal1b)

    subgoal1c = TreatmentGoal(
        plan_id=plan.id,
        parent_goal_id=goal1.id,
        goal_type='short_term',
        description='Reduce avoidance behaviors',
        status='in_progress',
        progress_percentage=40,
        priority=3  # Lower priority = lower weight
    )
    async_test_db.add(subgoal1c)
    await async_test_db.flush()

    # Goal 2: Goal with progress entries (rating-based calculation)
    goal2 = TreatmentGoal(
        plan_id=plan.id,
        goal_type='short_term',
        description='Improve sleep quality',
        status='in_progress',
        progress_percentage=0,  # Will be calculated from progress entries
        priority=1
    )
    async_test_db.add(goal2)
    await async_test_db.flush()

    # Progress entries for goal2 (latest should be used)
    progress1 = GoalProgress(
        goal_id=goal2.id,
        progress_note='Started sleep hygiene routine',
        rating=5,  # 50% progress
        recorded_at=datetime.utcnow() - timedelta(days=10)
    )
    async_test_db.add(progress1)

    progress2 = GoalProgress(
        goal_id=goal2.id,
        progress_note='Sleeping better, fewer interruptions',
        rating=7,  # 70% progress (latest - should be used)
        recorded_at=datetime.utcnow() - timedelta(days=2)
    )
    async_test_db.add(progress2)

    # Goal 3: Goal with no sub-goals or progress (uses stored percentage)
    goal3 = TreatmentGoal(
        plan_id=plan.id,
        goal_type='objective',
        description='Attend all therapy sessions',
        status='achieved',
        progress_percentage=100,
        priority=2
    )
    async_test_db.add(goal3)

    # Goal 4: Not started goal
    goal4 = TreatmentGoal(
        plan_id=plan.id,
        goal_type='short_term',
        description='Build social support network',
        status='not_started',
        progress_percentage=0,
        priority=3
    )
    async_test_db.add(goal4)

    # Goal 5: In progress goal with low progress
    goal5 = TreatmentGoal(
        plan_id=plan.id,
        goal_type='short_term',
        description='Develop coping strategies for stress',
        status='in_progress',
        progress_percentage=25,
        priority=1
    )
    async_test_db.add(goal5)

    await async_test_db.flush()

    # Load sub_goals relationship for goal1
    await async_test_db.refresh(goal1, ['sub_goals'])

    # Load progress_entries relationship for goal2
    await async_test_db.refresh(goal2, ['progress_entries'])

    return {
        "plan": plan,
        "therapist": therapist,
        "patient": patient,
        "goals": [goal1, goal2, goal3, goal4, goal5],
        "sub_goals": [subgoal1a, subgoal1b, subgoal1c],
        "progress_entries": [progress1, progress2]
    }


@pytest_asyncio.fixture
async def empty_treatment_plan(async_test_db: AsyncSession, therapist_and_patient):
    """
    Create a treatment plan with no goals for edge case testing.

    Returns:
        Dict with plan (no goals)
    """
    therapist = therapist_and_patient["therapist"]
    patient = therapist_and_patient["patient"]

    plan = TreatmentPlan(
        patient_id=patient.id,
        therapist_id=therapist.id,
        title="Empty Treatment Plan",
        start_date=date.today(),
        status='active',
        review_frequency_days=90
    )
    async_test_db.add(plan)
    await async_test_db.flush()

    return {
        "plan": plan,
        "therapist": therapist,
        "patient": patient
    }


# ============================================================================
# TestCalculateGoalProgress
# ============================================================================

class TestCalculateGoalProgress:
    """Test goal progress calculation with sub-goals and progress entries"""

    @pytest.mark.asyncio
    async def test_calculate_progress_with_subgoals(
        self,
        async_test_db: AsyncSession,
        treatment_plan_with_goals
    ):
        """Test weighted average calculation from sub-goals"""
        goal1 = treatment_plan_with_goals["goals"][0]  # Goal with 3 sub-goals

        # Expected calculation:
        # max_priority = 3
        # weight_a = 3 - 1 + 1 = 3 (priority 1)
        # weight_b = 3 - 2 + 1 = 2 (priority 2)
        # weight_c = 3 - 3 + 1 = 1 (priority 3)
        # progress = (80*3 + 60*2 + 40*1) / (3+2+1) = (240+120+40) / 6 = 400/6 = 66.67 = 66 (int)

        progress = await calculate_goal_progress(goal1, async_test_db)

        assert isinstance(progress, int)
        assert progress == 66  # Weighted average

    @pytest.mark.asyncio
    async def test_calculate_progress_with_progress_entries(
        self,
        async_test_db: AsyncSession,
        treatment_plan_with_goals
    ):
        """Test latest rating logic for progress entries"""
        goal2 = treatment_plan_with_goals["goals"][1]  # Goal with 2 progress entries

        # Latest entry has rating=7, which converts to 70%
        progress = await calculate_goal_progress(goal2, async_test_db)

        assert isinstance(progress, int)
        assert progress == 70  # (7/10) * 100 = 70

    @pytest.mark.asyncio
    async def test_calculate_progress_no_data(
        self,
        async_test_db: AsyncSession,
        treatment_plan_with_goals
    ):
        """Test returns stored percentage when no sub-goals or progress entries"""
        goal3 = treatment_plan_with_goals["goals"][2]  # No sub-goals or progress

        progress = await calculate_goal_progress(goal3, async_test_db)

        assert isinstance(progress, int)
        assert progress == 100  # Uses stored progress_percentage

    @pytest.mark.asyncio
    async def test_calculate_progress_empty_subgoals(
        self,
        async_test_db: AsyncSession,
        treatment_plan_with_goals
    ):
        """Test handles empty sub-goals list gracefully"""
        goal4 = treatment_plan_with_goals["goals"][3]  # Not started, no sub-goals

        progress = await calculate_goal_progress(goal4, async_test_db)

        assert isinstance(progress, int)
        assert progress == 0  # Uses stored progress_percentage


# ============================================================================
# TestCheckReviewDue
# ============================================================================

class TestCheckReviewDue:
    """Test review due date checking and status determination"""

    @pytest.mark.asyncio
    async def test_review_overdue(
        self,
        async_test_db: AsyncSession,
        therapist_and_patient
    ):
        """Test overdue review detection (past next_review_date)"""
        therapist = therapist_and_patient["therapist"]
        patient = therapist_and_patient["patient"]

        plan = TreatmentPlan(
            patient_id=patient.id,
            therapist_id=therapist.id,
            title="Overdue Review Plan",
            start_date=date.today() - timedelta(days=100),
            status='active',
            review_frequency_days=90,
            next_review_date=date.today() - timedelta(days=10)  # 10 days overdue
        )
        async_test_db.add(plan)
        await async_test_db.flush()

        result = await check_review_due(plan, async_test_db)

        assert isinstance(result, dict)
        assert result['is_due'] is True
        assert result['status'] == 'overdue'
        assert result['days_overdue'] == 10  # Positive for overdue
        assert isinstance(result['next_review_date'], str)

    @pytest.mark.asyncio
    async def test_review_due_soon(
        self,
        async_test_db: AsyncSession,
        therapist_and_patient
    ):
        """Test due soon detection (within 7 days)"""
        therapist = therapist_and_patient["therapist"]
        patient = therapist_and_patient["patient"]

        plan = TreatmentPlan(
            patient_id=patient.id,
            therapist_id=therapist.id,
            title="Due Soon Plan",
            start_date=date.today() - timedelta(days=30),
            status='active',
            review_frequency_days=90,
            next_review_date=date.today() + timedelta(days=5)  # 5 days away
        )
        async_test_db.add(plan)
        await async_test_db.flush()

        result = await check_review_due(plan, async_test_db)

        assert isinstance(result, dict)
        assert result['is_due'] is True
        assert result['status'] == 'due_soon'
        assert result['days_overdue'] == -5  # Negative for upcoming
        assert isinstance(result['next_review_date'], str)

    @pytest.mark.asyncio
    async def test_review_current(
        self,
        async_test_db: AsyncSession,
        therapist_and_patient
    ):
        """Test current status (more than 7 days away)"""
        therapist = therapist_and_patient["therapist"]
        patient = therapist_and_patient["patient"]

        plan = TreatmentPlan(
            patient_id=patient.id,
            therapist_id=therapist.id,
            title="Current Plan",
            start_date=date.today(),
            status='active',
            review_frequency_days=90,
            next_review_date=date.today() + timedelta(days=30)  # 30 days away
        )
        async_test_db.add(plan)
        await async_test_db.flush()

        result = await check_review_due(plan, async_test_db)

        assert isinstance(result, dict)
        assert result['is_due'] is False
        assert result['status'] == 'current'
        assert result['days_overdue'] == -30  # Negative for upcoming
        assert isinstance(result['next_review_date'], str)

    @pytest.mark.asyncio
    async def test_review_no_date(
        self,
        async_test_db: AsyncSession,
        therapist_and_patient
    ):
        """Test handles missing next_review_date gracefully"""
        therapist = therapist_and_patient["therapist"]
        patient = therapist_and_patient["patient"]

        plan = TreatmentPlan(
            patient_id=patient.id,
            therapist_id=therapist.id,
            title="No Review Date Plan",
            start_date=date.today(),
            status='active',
            review_frequency_days=90,
            next_review_date=None  # No review date set
        )
        async_test_db.add(plan)
        await async_test_db.flush()

        result = await check_review_due(plan, async_test_db)

        assert isinstance(result, dict)
        assert result['is_due'] is False
        assert result['status'] == 'current'
        assert result['days_overdue'] == 0
        assert result['next_review_date'] is None


# ============================================================================
# TestGenerateProgressReport
# ============================================================================

class TestGenerateProgressReport:
    """Test comprehensive progress report generation"""

    @pytest.mark.asyncio
    async def test_progress_report_full_plan(
        self,
        async_test_db: AsyncSession,
        treatment_plan_with_goals
    ):
        """Test comprehensive statistics for plan with goals"""
        plan = treatment_plan_with_goals["plan"]

        report = await generate_progress_report(plan.id, async_test_db)

        # Verify structure
        assert isinstance(report, dict)
        assert report['plan_id'] == str(plan.id)

        # Goal status counts (5 goals total: 1 achieved, 3 in_progress, 1 not_started)
        # Note: sub-goals are counted separately
        assert report['total_goals'] == 8  # 5 main goals + 3 sub-goals
        assert report['achieved_goals'] == 1
        assert report['in_progress_goals'] == 5  # goal1 + 3 sub-goals + goal2 + goal5
        assert report['not_started_goals'] == 1

        # Overall progress (average of all 8 goals)
        assert isinstance(report['overall_progress_percentage'], int)
        assert 0 <= report['overall_progress_percentage'] <= 100

        # On track vs behind
        assert isinstance(report['goals_on_track'], int)
        assert isinstance(report['goals_behind'], int)

        # Recent progress entries
        assert isinstance(report['recent_progress_entries'], list)
        assert len(report['recent_progress_entries']) <= 5  # Limit 5

        # Top performing and needs attention goals
        assert isinstance(report['top_performing_goals'], list)
        assert len(report['top_performing_goals']) <= 3
        assert isinstance(report['needs_attention_goals'], list)
        assert len(report['needs_attention_goals']) <= 3

    @pytest.mark.asyncio
    async def test_progress_report_no_goals(
        self,
        async_test_db: AsyncSession,
        empty_treatment_plan
    ):
        """Test empty plan handling (no goals)"""
        plan = empty_treatment_plan["plan"]

        report = await generate_progress_report(plan.id, async_test_db)

        # Verify empty report structure
        assert isinstance(report, dict)
        assert report['plan_id'] == str(plan.id)
        assert report['total_goals'] == 0
        assert report['achieved_goals'] == 0
        assert report['in_progress_goals'] == 0
        assert report['not_started_goals'] == 0
        assert report['overall_progress_percentage'] == 0
        assert report['goals_on_track'] == 0
        assert report['goals_behind'] == 0
        assert len(report['recent_progress_entries']) == 0
        assert len(report['top_performing_goals']) == 0
        assert len(report['needs_attention_goals']) == 0

    @pytest.mark.asyncio
    async def test_progress_report_no_progress_entries(
        self,
        async_test_db: AsyncSession,
        empty_treatment_plan
    ):
        """Test goals without progress entries"""
        plan = empty_treatment_plan["plan"]

        # Add goals without progress entries
        goal1 = TreatmentGoal(
            plan_id=plan.id,
            goal_type='short_term',
            description='Test goal 1',
            status='in_progress',
            progress_percentage=75,
            priority=1
        )
        async_test_db.add(goal1)

        goal2 = TreatmentGoal(
            plan_id=plan.id,
            goal_type='short_term',
            description='Test goal 2',
            status='in_progress',
            progress_percentage=25,
            priority=2
        )
        async_test_db.add(goal2)
        await async_test_db.flush()

        report = await generate_progress_report(plan.id, async_test_db)

        # Verify report
        assert report['total_goals'] == 2
        assert report['in_progress_goals'] == 2
        assert len(report['recent_progress_entries']) == 0  # No progress entries
        assert report['overall_progress_percentage'] == 50  # (75+25)/2 = 50

        # Top performer should be goal1 (75%), needs attention should be goal2 (25%)
        assert len(report['top_performing_goals']) > 0
        assert report['top_performing_goals'][0]['progress'] == 75
        assert len(report['needs_attention_goals']) > 0
        assert report['needs_attention_goals'][0]['progress'] == 25


# ============================================================================
# TestRecalculatePlanProgress
# ============================================================================

class TestRecalculatePlanProgress:
    """Test plan-level progress recalculation"""

    @pytest.mark.asyncio
    async def test_recalculate_with_multiple_goals(
        self,
        async_test_db: AsyncSession,
        treatment_plan_with_goals
    ):
        """Test average calculation across multiple goals"""
        plan = treatment_plan_with_goals["plan"]

        progress = await recalculate_plan_progress(plan.id, async_test_db)

        # Should calculate progress for each goal and return average
        assert isinstance(progress, int)
        assert 0 <= progress <= 100

    @pytest.mark.asyncio
    async def test_recalculate_empty_plan(
        self,
        async_test_db: AsyncSession,
        empty_treatment_plan
    ):
        """Test empty plan edge case (no goals)"""
        plan = empty_treatment_plan["plan"]

        progress = await recalculate_plan_progress(plan.id, async_test_db)

        assert isinstance(progress, int)
        assert progress == 0  # No goals = 0% progress


# ============================================================================
# TestGetGoalsByStatus
# ============================================================================

class TestGetGoalsByStatus:
    """Test goal filtering by status with ordering"""

    @pytest.mark.asyncio
    async def test_get_goals_by_status_filters_correctly(
        self,
        async_test_db: AsyncSession,
        treatment_plan_with_goals
    ):
        """Test status filtering works correctly"""
        plan = treatment_plan_with_goals["plan"]

        # Get in_progress goals
        in_progress_goals = await get_goals_by_status(
            plan.id,
            'in_progress',
            async_test_db
        )

        assert isinstance(in_progress_goals, list)
        # Should have multiple in_progress goals
        assert len(in_progress_goals) > 0
        # All returned goals should have in_progress status
        for goal in in_progress_goals:
            assert goal.status == 'in_progress'

        # Get achieved goals
        achieved_goals = await get_goals_by_status(
            plan.id,
            'achieved',
            async_test_db
        )

        assert isinstance(achieved_goals, list)
        assert len(achieved_goals) == 1  # Only goal3 is achieved
        assert achieved_goals[0].status == 'achieved'

        # Get not_started goals
        not_started_goals = await get_goals_by_status(
            plan.id,
            'not_started',
            async_test_db
        )

        assert isinstance(not_started_goals, list)
        assert len(not_started_goals) == 1  # Only goal4 is not_started
        assert not_started_goals[0].status == 'not_started'

    @pytest.mark.asyncio
    async def test_get_goals_ordering(
        self,
        async_test_db: AsyncSession,
        treatment_plan_with_goals
    ):
        """Test priority then created_at ordering"""
        plan = treatment_plan_with_goals["plan"]

        # Get in_progress goals (should be ordered by priority asc, then created_at asc)
        in_progress_goals = await get_goals_by_status(
            plan.id,
            'in_progress',
            async_test_db
        )

        assert len(in_progress_goals) > 0

        # Verify priority ordering (ascending - priority 1 first)
        priorities = [goal.priority for goal in in_progress_goals]
        assert priorities == sorted(priorities)  # Should be in ascending order
