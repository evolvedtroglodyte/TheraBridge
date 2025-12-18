"""
Test to verify goal tracking fixtures work correctly.
This file validates that all fixtures import and can be instantiated.
"""
import pytest
from datetime import datetime, date


class TestGoalFixtures:
    """Validate goal tracking test fixtures"""

    def test_sample_goal_fixture(self, sample_goal):
        """Test that sample_goal fixture creates valid TreatmentGoal"""
        assert sample_goal.id is not None
        assert sample_goal.description == "Practice deep breathing exercises daily"
        assert sample_goal.category == "anxiety_management"
        assert sample_goal.status == "assigned"
        assert sample_goal.baseline_value == 2.0
        assert sample_goal.target_value == 7.0
        assert sample_goal.target_date is not None
        assert sample_goal.patient_id is not None
        assert sample_goal.therapist_id is not None

    def test_sample_goal_with_tracking_fixture(self, sample_goal_with_tracking):
        """Test that sample_goal_with_tracking creates goal and config"""
        goal, tracking_config = sample_goal_with_tracking

        # Verify goal
        assert goal.id is not None
        assert goal.description == "Rate anxiety level on scale of 1-10"
        assert goal.status == "in_progress"

        # Verify tracking config
        assert tracking_config.id is not None
        assert tracking_config.goal_id == goal.id
        assert tracking_config.tracking_method == "scale"
        assert tracking_config.tracking_frequency == "daily"
        assert tracking_config.scale_min == 1
        assert tracking_config.scale_max == 10
        assert tracking_config.target_direction == "decrease"

    def test_sample_progress_entries_fixture(self, sample_progress_entries):
        """Test that sample_progress_entries creates multiple entries"""
        assert len(sample_progress_entries) == 5

        # Verify entries are in order
        values = [entry.value for entry in sample_progress_entries]
        assert values == [8.0, 7.5, 7.0, 6.5, 6.0]  # Improving trend

        # Verify each entry has required fields
        for entry in sample_progress_entries:
            assert entry.id is not None
            assert entry.goal_id is not None
            assert entry.entry_date is not None
            assert entry.value is not None
            assert entry.context == "self_report"

    def test_sample_assessment_fixture(self, sample_assessment):
        """Test that sample_assessment creates valid AssessmentScore"""
        assert sample_assessment.id is not None
        assert sample_assessment.assessment_type == "GAD-7"
        assert sample_assessment.score == 14
        assert sample_assessment.severity == "moderate"
        assert sample_assessment.subscores is not None
        assert len(sample_assessment.subscores) == 7
        assert sample_assessment.patient_id is not None
        assert sample_assessment.administered_by is not None

    def test_sample_milestone_fixture(self, sample_milestone):
        """Test that sample_milestone creates valid ProgressMilestone"""
        assert sample_milestone.id is not None
        assert sample_milestone.milestone_type == "percentage"
        assert sample_milestone.title == "50% Progress Achieved"
        assert sample_milestone.target_value == 4.5
        assert sample_milestone.achieved_at is None  # Not yet achieved
        assert sample_milestone.goal_id is not None

    def test_goal_with_progress_history_fixture(self, goal_with_progress_history):
        """Test that goal_with_progress_history creates complete history"""
        goal, tracking_config, entries = goal_with_progress_history

        # Verify goal
        assert goal.id is not None
        assert goal.description == "Exercise for 30 minutes, 5 times per week"
        assert goal.category == "physical_activity"

        # Verify tracking config
        assert tracking_config.tracking_method == "frequency"
        assert tracking_config.frequency_unit == "times_per_week"

        # Verify 12 weeks of entries
        assert len(entries) == 12

        # Verify improvement trend
        values = [entry.value for entry in entries]
        assert values[0] == 1.0  # Start at 1
        assert values[-1] == 5.0  # End at 5 (target reached)
        assert values == sorted(values, key=lambda x: (x, 0))  # Non-decreasing

    def test_multiple_goals_for_patient_fixture(self, multiple_goals_for_patient):
        """Test that multiple_goals_for_patient creates 3 goals"""
        goals = multiple_goals_for_patient
        assert len(goals) == 3

        # Verify different statuses
        statuses = [goal.status for goal in goals]
        assert "in_progress" in statuses
        assert "completed" in statuses
        assert "assigned" in statuses

        # Verify different categories
        categories = [goal.category for goal in goals]
        assert "anxiety_management" in categories
        assert "behavioral" in categories
        assert "depression_management" in categories

        # Verify completed goal has completed_at timestamp
        completed_goal = next(g for g in goals if g.status == "completed")
        assert completed_goal.completed_at is not None

    def test_fixtures_use_same_patient(
        self,
        sample_goal,
        sample_goal_with_tracking,
        sample_patient
    ):
        """Test that fixtures share the same patient"""
        goal, _ = sample_goal_with_tracking

        # All goals should belong to the same patient
        assert sample_goal.patient_id == sample_patient.id
        assert goal.patient_id == sample_patient.id

    def test_fixtures_use_same_therapist(
        self,
        sample_goal,
        sample_goal_with_tracking,
        therapist_user
    ):
        """Test that fixtures share the same therapist"""
        goal, _ = sample_goal_with_tracking

        # All goals should be created by the same therapist
        assert sample_goal.therapist_id == therapist_user.id
        assert goal.therapist_id == therapist_user.id
