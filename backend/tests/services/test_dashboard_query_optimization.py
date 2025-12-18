"""
Query Performance Tests for Dashboard Service N+1 Optimizations

This test suite validates query count reductions achieved through N+1 optimization fixes:
- Latest progress entry optimization (I3's work)
- Trend entries optimization (I4's work)
- Assessment loop optimization (I5's work)

Uses SQLAlchemy event listeners to count actual database queries executed.
"""
import pytest
import pytest_asyncio
from sqlalchemy import event
from datetime import datetime, date, timedelta
from uuid import uuid4

from app.services.dashboard_service import (
    get_goal_dashboard,
    get_goal_dashboard_items
)
from app.models.goal_models import TreatmentGoal
from app.models.tracking_models import (
    GoalTrackingConfig,
    ProgressEntry,
    AssessmentScore
)


# ============================================================================
# Query Counter Utilities
# ============================================================================

class QueryCounter:
    """
    Thread-safe query counter using SQLAlchemy event listeners.
    Tracks all SQL queries executed during a test.
    """
    def __init__(self, engine):
        self.engine = engine
        self.count = 0
        self.queries = []

    def __enter__(self):
        """Start counting queries"""
        self.count = 0
        self.queries = []
        event.listen(
            self.engine.sync_engine,
            "before_cursor_execute",
            self._count_query
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop counting queries"""
        event.remove(
            self.engine.sync_engine,
            "before_cursor_execute",
            self._count_query
        )

    def _count_query(self, conn, cursor, statement, params, context, executemany):
        """Callback to increment query count"""
        self.count += 1
        self.queries.append({
            'statement': statement,
            'params': params
        })


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest_asyncio.fixture(scope="function")
async def async_engine():
    """Provide the async engine for query counting"""
    from tests.conftest import async_engine as test_async_engine
    return test_async_engine


@pytest_asyncio.fixture(scope="function")
async def patient_with_goals(async_test_db, therapist_user, sample_patient, sample_session):
    """
    Create a patient with 10 treatment goals for testing dashboard queries.

    This fixture creates realistic test data:
    - 10 treatment goals with different categories and statuses
    - Each goal has a tracking config
    - Mix of assigned, in_progress, and completed goals
    """
    goals = []
    configs = []

    # Goal categories and configurations
    goal_data = [
        {"desc": "Reduce anxiety symptoms", "category": "anxiety_management", "status": "in_progress", "baseline": 8.0, "target": 3.0},
        {"desc": "Practice mindfulness daily", "category": "behavioral", "status": "in_progress", "baseline": 2.0, "target": 7.0},
        {"desc": "Improve sleep quality", "category": "sleep_hygiene", "status": "in_progress", "baseline": 4.0, "target": 8.0},
        {"desc": "Exercise 3x per week", "category": "physical_activity", "status": "assigned", "baseline": 0.0, "target": 3.0},
        {"desc": "Journal daily emotions", "category": "reflection", "status": "in_progress", "baseline": 1.0, "target": 7.0},
        {"desc": "Reduce caffeine intake", "category": "behavioral", "status": "in_progress", "baseline": 5.0, "target": 1.0},
        {"desc": "Social connection weekly", "category": "social", "status": "assigned", "baseline": 0.0, "target": 1.0},
        {"desc": "Deep breathing practice", "category": "anxiety_management", "status": "in_progress", "baseline": 2.0, "target": 7.0},
        {"desc": "Gratitude practice", "category": "reflection", "status": "completed", "baseline": 0.0, "target": 5.0},
        {"desc": "Set healthy boundaries", "category": "relationships", "status": "in_progress", "baseline": 3.0, "target": 8.0},
    ]

    for i, data in enumerate(goal_data):
        # Create goal
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=therapist_user.id,
            session_id=sample_session.id,
            description=data["desc"],
            category=data["category"],
            status=data["status"],
            baseline_value=data["baseline"],
            target_value=data["target"],
            target_date=date.today() + timedelta(days=60),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        async_test_db.add(goal)
        goals.append(goal)

    # Flush to get goal IDs
    await async_test_db.flush()

    # Create tracking configs for each goal
    for goal in goals:
        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily",
            scale_min=1,
            scale_max=10,
            target_direction="decrease" if goal.baseline_value > goal.target_value else "increase",
            reminder_enabled=True,
            created_at=datetime.utcnow()
        )
        async_test_db.add(config)
        configs.append(config)

    await async_test_db.commit()

    # Refresh all objects
    for goal in goals:
        await async_test_db.refresh(goal)
    for config in configs:
        await async_test_db.refresh(config)

    return {
        "patient": sample_patient,
        "goals": goals,
        "configs": configs
    }


@pytest_asyncio.fixture(scope="function")
async def goals_with_progress_entries(async_test_db, patient_with_goals):
    """
    Add progress entries to all goals for trend analysis testing.

    Creates:
    - 5 progress entries per goal (last 10 days)
    - Realistic trending data (improving, stable, declining)
    - Both latest entry and historical entries for trend calculation
    """
    goals = patient_with_goals["goals"]
    configs = patient_with_goals["configs"]

    all_entries = []

    for goal, config in zip(goals, configs):
        # Skip completed goals
        if goal.status == "completed":
            continue

        # Create 5 progress entries over last 10 days
        base_date = date.today() - timedelta(days=10)

        # Generate trend: improving for anxiety goals, stable for others
        if "anxiety" in goal.category:
            # Decreasing trend (improving for anxiety)
            values = [7.0, 6.5, 6.0, 5.5, 5.0]
        elif goal.status == "assigned":
            # No entries for newly assigned goals
            continue
        else:
            # Stable trend
            values = [5.0, 5.2, 4.8, 5.1, 5.0]

        for i, value in enumerate(values):
            entry = ProgressEntry(
                goal_id=goal.id,
                tracking_config_id=config.id,
                entry_date=base_date + timedelta(days=i*2),
                value=value,
                value_label=f"Rating: {value}",
                notes=f"Progress entry {i+1}",
                context="self_report",
                recorded_at=datetime.utcnow()
            )
            async_test_db.add(entry)
            all_entries.append(entry)

    await async_test_db.commit()

    # Refresh all entries
    for entry in all_entries:
        await async_test_db.refresh(entry)

    return {
        **patient_with_goals,
        "entries": all_entries
    }


@pytest_asyncio.fixture(scope="function")
async def patient_with_assessments(async_test_db, patient_with_goals):
    """
    Add GAD-7 and PHQ-9 assessments for testing assessment query optimization.

    Creates:
    - GAD-7 assessment from 5 weeks ago (overdue for re-administration)
    - PHQ-9 assessment from 2 weeks ago (not yet due)
    """
    patient = patient_with_goals["patient"]
    goals = patient_with_goals["goals"]

    # Create GAD-7 assessment (35 days ago - should be due)
    gad7 = AssessmentScore(
        patient_id=patient.id,
        goal_id=goals[0].id if goals else None,
        administered_by=patient.therapist_id,
        assessment_type="GAD-7",
        score=14,
        severity="moderate",
        subscores={
            "feeling_nervous": 2,
            "not_stop_worrying": 2,
            "worrying_too_much": 2,
            "trouble_relaxing": 2,
            "restless": 2,
            "easily_annoyed": 2,
            "feeling_afraid": 2
        },
        administered_date=date.today() - timedelta(days=35),
        notes="Baseline GAD-7 assessment",
        created_at=datetime.utcnow()
    )
    async_test_db.add(gad7)

    # Create PHQ-9 assessment (14 days ago - not yet due)
    phq9 = AssessmentScore(
        patient_id=patient.id,
        goal_id=goals[1].id if len(goals) > 1 else None,
        administered_by=patient.therapist_id,
        assessment_type="PHQ-9",
        score=10,
        severity="moderate",
        subscores={
            "little_interest": 1,
            "feeling_down": 2,
            "sleep_trouble": 2,
            "tired": 2,
            "appetite": 1,
            "feeling_bad": 1,
            "concentration": 1,
            "moving_slowly": 0,
            "suicide_thoughts": 0
        },
        administered_date=date.today() - timedelta(days=14),
        notes="Recent PHQ-9 assessment",
        created_at=datetime.utcnow()
    )
    async_test_db.add(phq9)

    await async_test_db.commit()

    await async_test_db.refresh(gad7)
    await async_test_db.refresh(phq9)

    return {
        **patient_with_goals,
        "assessments": [gad7, phq9]
    }


# ============================================================================
# N+1 Optimization Tests
# ============================================================================

@pytest.mark.asyncio
async def test_latest_progress_entry_optimization(async_test_db, goals_with_progress_entries, async_engine):
    """
    Test I3's fix: Latest progress entry should be fetched with eager loading.

    BEFORE: 1 query for goals + N queries for latest entry per goal = 11 queries
    AFTER: Should use joinedload/subquery to fetch all latest entries in 2-3 queries

    Expected query count: <= 3 (vs 11 before optimization)
    Reduction: ~73%
    """
    patient = goals_with_progress_entries["patient"]

    # Count queries during dashboard item retrieval
    with QueryCounter(async_engine) as counter:
        dashboard_items = await get_goal_dashboard_items(
            patient_id=patient.id,
            db=async_test_db
        )

    # Validate results
    assert len(dashboard_items) == 10, "Should return all 10 goals"

    # Count goals with current values (those with progress entries)
    goals_with_values = [item for item in dashboard_items if item.current_value is not None]
    assert len(goals_with_values) >= 7, "At least 7 goals should have progress entries"

    # CRITICAL ASSERTION: Query count should be dramatically reduced
    print(f"\n[I3 FIX] Latest Entry Queries: {counter.count}")
    print(f"Expected: <= 3, Actual: {counter.count}")

    # BEFORE optimization: 1 (goals query) + 10 (latest entry per goal) = 11 queries
    # AFTER optimization: Should be 3 or fewer with proper eager loading
    assert counter.count <= 3, (
        f"N+1 issue detected! Expected <= 3 queries, got {counter.count}. "
        f"Latest progress entry should be eagerly loaded with joinedload/subqueryload."
    )

    # Calculate improvement
    before_count = 11
    reduction_pct = ((before_count - counter.count) / before_count) * 100
    print(f"Improvement: {before_count} → {counter.count} queries ({reduction_pct:.1f}% reduction)")


@pytest.mark.asyncio
async def test_trend_entries_optimization(async_test_db, goals_with_progress_entries, async_engine):
    """
    Test I4's fix: Trend entries (last 30 days) should be fetched efficiently.

    BEFORE: 1 query for goals + N queries for trend entries per goal = 11 queries
    AFTER: Should use subquery or batch loading to fetch all trend data together

    Expected query count: <= 3 (vs 11 before optimization)
    Reduction: ~73%
    """
    patient = goals_with_progress_entries["patient"]

    # Count queries during dashboard item retrieval
    with QueryCounter(async_engine) as counter:
        dashboard_items = await get_goal_dashboard_items(
            patient_id=patient.id,
            db=async_test_db
        )

    # Validate trend data is present
    items_with_trends = [item for item in dashboard_items if len(item.trend_data) > 0]
    assert len(items_with_trends) >= 7, "At least 7 goals should have trend data"

    # Verify trend calculations are correct
    for item in items_with_trends:
        assert len(item.trend_data) >= 3, f"Goal {item.id} should have at least 3 trend points"
        # Verify trend direction is calculated
        assert item.trend is not None, f"Goal {item.id} should have trend direction"

    # CRITICAL ASSERTION: Query count should be dramatically reduced
    print(f"\n[I4 FIX] Trend Entries Queries: {counter.count}")
    print(f"Expected: <= 3, Actual: {counter.count}")

    # BEFORE optimization: 1 (goals) + 10 (latest entry) + 10 (trend entries) = 21 queries
    # AFTER optimization: Should be 3 or fewer with proper eager loading
    assert counter.count <= 3, (
        f"N+1 issue detected! Expected <= 3 queries, got {counter.count}. "
        f"Trend entries should be eagerly loaded or batched."
    )

    # Calculate improvement
    before_count = 21  # Includes both latest entry and trend entry queries
    reduction_pct = ((before_count - counter.count) / before_count) * 100
    print(f"Improvement: {before_count} → {counter.count} queries ({reduction_pct:.1f}% reduction)")


@pytest.mark.asyncio
async def test_assessment_loop_optimization(async_test_db, patient_with_assessments, async_engine):
    """
    Test I5's fix: Assessment queries should be batched, not looped.

    BEFORE: 2 separate queries (one per assessment type: GAD-7, PHQ-9)
    AFTER: 1 query with IN clause to fetch all assessment types at once

    Expected query count for assessment section: 1 (vs 2 before)
    Reduction: 50%
    """
    patient = patient_with_assessments["patient"]

    # Count queries during full dashboard retrieval
    with QueryCounter(async_engine) as counter:
        dashboard = await get_goal_dashboard(
            patient_id=patient.id,
            db=async_test_db
        )

    # Validate assessment data
    assert len(dashboard.assessments_due) >= 1, "Should have at least 1 assessment due"

    # Check that GAD-7 is marked as due (35 days since last administration)
    gad7_due = any(a["type"] == "GAD-7" for a in dashboard.assessments_due)
    assert gad7_due, "GAD-7 should be due (35 days since last)"

    # CRITICAL ASSERTION: Assessment queries should be batched
    print(f"\n[I5 FIX] Total Dashboard Queries: {counter.count}")

    # Count how many queries were for assessments (check query statements)
    assessment_queries = [
        q for q in counter.queries
        if "assessment_scores" in q["statement"].lower()
    ]
    assessment_query_count = len(assessment_queries)

    print(f"Assessment queries: {assessment_query_count}")
    print(f"Expected: 1, Actual: {assessment_query_count}")

    # BEFORE optimization: 2 queries (one per assessment type in loop)
    # AFTER optimization: 1 query with IN clause for both types
    assert assessment_query_count == 1, (
        f"Assessment N+1 issue detected! Expected 1 query, got {assessment_query_count}. "
        f"Assessment types should be fetched in a single query with IN clause."
    )

    # Calculate improvement
    before_count = 2
    reduction_pct = ((before_count - assessment_query_count) / before_count) * 100
    print(f"Improvement: {before_count} → {assessment_query_count} queries ({reduction_pct:.1f}% reduction)")


@pytest.mark.asyncio
async def test_combined_dashboard_query_efficiency(async_test_db, patient_with_assessments, goals_with_progress_entries, async_engine):
    """
    Integration test: Verify all N+1 fixes work together.

    Tests the complete dashboard with:
    - 10 goals with tracking configs
    - Progress entries for trend analysis
    - Multiple assessments (GAD-7, PHQ-9)

    BEFORE all optimizations:
    - 1 (goals) + 10 (latest entry) + 10 (trend entries) + 2 (assessments) + misc = ~30 queries

    AFTER all optimizations:
    - Goals + eager loads: 3 queries
    - Assessments: 1 query
    - Milestones: 1 query
    - Activity summary: ~2 queries
    - Total: ~7 queries

    Expected: <= 10 queries (vs ~30 before)
    Overall improvement: ~67%
    """
    # Merge fixtures: Add assessments to goals_with_progress_entries data
    patient = goals_with_progress_entries["patient"]

    # Add assessments to this patient
    gad7 = AssessmentScore(
        patient_id=patient.id,
        goal_id=goals_with_progress_entries["goals"][0].id,
        administered_by=patient.therapist_id,
        assessment_type="GAD-7",
        score=14,
        severity="moderate",
        subscores={},
        administered_date=date.today() - timedelta(days=35),
        notes="Test assessment"
    )
    phq9 = AssessmentScore(
        patient_id=patient.id,
        goal_id=goals_with_progress_entries["goals"][1].id,
        administered_by=patient.therapist_id,
        assessment_type="PHQ-9",
        score=10,
        severity="moderate",
        subscores={},
        administered_date=date.today() - timedelta(days=14),
        notes="Test assessment"
    )
    async_test_db.add(gad7)
    async_test_db.add(phq9)
    await async_test_db.commit()

    # Count queries for complete dashboard
    with QueryCounter(async_engine) as counter:
        dashboard = await get_goal_dashboard(
            patient_id=patient.id,
            db=async_test_db
        )

    # Validate complete dashboard data
    assert dashboard.active_goals == 9, "Should have 9 active goals (10 total - 1 completed)"
    assert len(dashboard.goals) == 10, "Should return all 10 goals"
    assert dashboard.tracking_summary.entries_this_week >= 0, "Should have tracking summary"
    assert len(dashboard.assessments_due) >= 1, "Should have assessments due"

    # CRITICAL ASSERTION: Total query count should be dramatically reduced
    print(f"\n[COMBINED] Full Dashboard Queries: {counter.count}")
    print(f"Expected: <= 10, Actual: {counter.count}")

    # BEFORE all optimizations: ~30 queries
    # AFTER all optimizations: ~7-10 queries
    assert counter.count <= 10, (
        f"Dashboard has excessive queries! Expected <= 10, got {counter.count}. "
        f"All N+1 issues should be fixed with proper eager loading and batching."
    )

    # Calculate improvement
    before_count = 30
    reduction_pct = ((before_count - counter.count) / before_count) * 100
    print(f"Overall Improvement: {before_count} → {counter.count} queries ({reduction_pct:.1f}% reduction)")

    # Performance estimate: Database round-trip time savings
    # Assume 10ms per query average latency
    time_saved_ms = (before_count - counter.count) * 10
    print(f"Estimated time saved: ~{time_saved_ms}ms per dashboard load")


@pytest.mark.asyncio
async def test_query_optimization_with_large_dataset(async_test_db, therapist_user, sample_patient, sample_session, async_engine):
    """
    Stress test: Verify optimizations scale well with larger datasets.

    Creates:
    - 50 goals
    - 10 progress entries per goal (500 total entries)
    - Multiple assessments

    This test ensures N+1 fixes don't regress as data volume increases.
    Query count should remain constant regardless of number of goals.
    """
    # Create 50 goals
    goals = []
    for i in range(50):
        goal = TreatmentGoal(
            patient_id=sample_patient.id,
            therapist_id=therapist_user.id,
            session_id=sample_session.id,
            description=f"Goal {i+1}: Test goal for performance testing",
            category="test_category",
            status="in_progress",
            baseline_value=1.0,
            target_value=10.0,
            target_date=date.today() + timedelta(days=60)
        )
        async_test_db.add(goal)
        goals.append(goal)

    await async_test_db.flush()

    # Create tracking configs and progress entries
    for goal in goals:
        config = GoalTrackingConfig(
            goal_id=goal.id,
            tracking_method="scale",
            tracking_frequency="daily",
            scale_min=1,
            scale_max=10,
            target_direction="increase"
        )
        async_test_db.add(config)

        # 10 progress entries per goal
        for j in range(10):
            entry = ProgressEntry(
                goal_id=goal.id,
                tracking_config_id=config.id,
                entry_date=date.today() - timedelta(days=j),
                value=float(j + 1),
                context="self_report"
            )
            async_test_db.add(entry)

    await async_test_db.commit()

    # Test query efficiency with large dataset
    with QueryCounter(async_engine) as counter:
        dashboard_items = await get_goal_dashboard_items(
            patient_id=sample_patient.id,
            db=async_test_db
        )

    # Validate results
    assert len(dashboard_items) == 50, "Should return all 50 goals"

    # CRITICAL: Query count should NOT scale with number of goals
    print(f"\n[SCALE TEST] 50 goals with 500 entries: {counter.count} queries")
    print(f"Expected: <= 5, Actual: {counter.count}")

    # Even with 50 goals and 500 entries, query count should remain low
    # If we had N+1 issues: 1 + 50 + 50 = 101 queries
    # With optimizations: Should be ~3-5 queries
    assert counter.count <= 5, (
        f"Optimizations don't scale! With 50 goals, expected <= 5 queries, got {counter.count}. "
        f"N+1 fixes should prevent query count from scaling with data volume."
    )

    # Calculate what query count WOULD be without optimizations
    unoptimized_count = 1 + 50 + 50  # goals + latest entries + trend entries
    improvement = ((unoptimized_count - counter.count) / unoptimized_count) * 100
    print(f"At scale: {unoptimized_count} → {counter.count} queries ({improvement:.1f}% reduction)")


# ============================================================================
# Summary Report Test
# ============================================================================

@pytest.mark.asyncio
async def test_optimization_summary_report(async_test_db, goals_with_progress_entries, async_engine):
    """
    Generate summary report of all query optimizations.

    This test documents the measured improvements for each N+1 fix:
    - I3: Latest progress entry
    - I4: Trend entries
    - I5: Assessment loop

    Outputs a formatted report with before/after metrics.
    """
    patient = goals_with_progress_entries["patient"]

    # Test each optimization individually
    results = {}

    # I3: Latest entry optimization
    with QueryCounter(async_engine) as counter:
        await get_goal_dashboard_items(patient_id=patient.id, db=async_test_db)
    results["latest_entry"] = {
        "before": 11,
        "after": counter.count,
        "reduction_pct": ((11 - counter.count) / 11) * 100
    }

    # I4: Trend entries optimization (same function, different aspect)
    with QueryCounter(async_engine) as counter:
        await get_goal_dashboard_items(patient_id=patient.id, db=async_test_db)
    results["trend_entries"] = {
        "before": 21,
        "after": counter.count,
        "reduction_pct": ((21 - counter.count) / 21) * 100
    }

    # I5: Assessment optimization (requires full dashboard)
    # Add assessments
    gad7 = AssessmentScore(
        patient_id=patient.id,
        assessment_type="GAD-7",
        score=14,
        severity="moderate",
        administered_date=date.today() - timedelta(days=35)
    )
    phq9 = AssessmentScore(
        patient_id=patient.id,
        assessment_type="PHQ-9",
        score=10,
        severity="moderate",
        administered_date=date.today() - timedelta(days=14)
    )
    async_test_db.add(gad7)
    async_test_db.add(phq9)
    await async_test_db.commit()

    with QueryCounter(async_engine) as counter:
        await get_goal_dashboard(patient_id=patient.id, db=async_test_db)

    assessment_queries = [q for q in counter.queries if "assessment_scores" in q["statement"].lower()]
    results["assessments"] = {
        "before": 2,
        "after": len(assessment_queries),
        "reduction_pct": ((2 - len(assessment_queries)) / 2) * 100 if assessment_queries else 0
    }

    # Print summary report
    print("\n" + "="*80)
    print("DASHBOARD SERVICE QUERY OPTIMIZATION SUMMARY")
    print("="*80)
    print(f"\n{'Optimization':<30} {'Before':<10} {'After':<10} {'Reduction':<15}")
    print("-"*80)

    print(f"{'I3: Latest Progress Entry':<30} {results['latest_entry']['before']:<10} {results['latest_entry']['after']:<10} {results['latest_entry']['reduction_pct']:.1f}%")
    print(f"{'I4: Trend Entries':<30} {results['trend_entries']['before']:<10} {results['trend_entries']['after']:<10} {results['trend_entries']['reduction_pct']:.1f}%")
    print(f"{'I5: Assessment Loop':<30} {results['assessments']['before']:<10} {results['assessments']['after']:<10} {results['assessments']['reduction_pct']:.1f}%")

    print("-"*80)

    # Calculate overall improvement
    total_before = 30  # Approximate total before all optimizations
    total_after = results['trend_entries']['after']  # Use trend entries as it includes both I3 and I4
    overall_reduction = ((total_before - total_after) / total_before) * 100

    print(f"{'Overall Dashboard':<30} {total_before:<10} {total_after:<10} {overall_reduction:.1f}%")
    print("="*80)
    print(f"\nEstimated performance improvement: ~{overall_reduction:.0f}% faster dashboard loads")
    print(f"Average latency savings: ~{(total_before - total_after) * 10}ms per request (@ 10ms/query)")
    print("="*80 + "\n")

    # Assertions to ensure report is accurate
    assert results['latest_entry']['after'] <= 3, "Latest entry optimization failed"
    assert results['trend_entries']['after'] <= 3, "Trend entries optimization failed"
    assert results['assessments']['after'] == 1, "Assessment optimization failed"
