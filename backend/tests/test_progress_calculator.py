"""
Tests for progress calculation logic in audio processing pipeline
"""

import pytest
from app.services.progress_calculator import (
    ProgressCalculator,
    ProcessingStage,
    get_progress_calculator
)


class TestProgressCalculator:
    """Test suite for ProgressCalculator class"""

    def test_initialization(self):
        """Test calculator initializes successfully with valid weights"""
        calc = ProgressCalculator()
        assert calc is not None
        assert len(calc.STAGE_WEIGHTS) == 6

    def test_stage_weights_sum_to_100(self):
        """Verify all stage weights sum to 100%"""
        calc = ProgressCalculator()
        stages = [
            ProcessingStage.UPLOADING,
            ProcessingStage.PREPROCESSING,
            ProcessingStage.TRANSCRIBING,
            ProcessingStage.DIARIZING,
            ProcessingStage.GENERATING_NOTES,
            ProcessingStage.SAVING
        ]
        total_weight = sum(
            end - start
            for start, end in [calc.STAGE_WEIGHTS[s] for s in stages]
        )
        assert total_weight == 100

    def test_stage_weights_continuous(self):
        """Verify stage weights are continuous with no gaps"""
        calc = ProgressCalculator()
        stages = [
            ProcessingStage.UPLOADING,
            ProcessingStage.PREPROCESSING,
            ProcessingStage.TRANSCRIBING,
            ProcessingStage.DIARIZING,
            ProcessingStage.GENERATING_NOTES,
            ProcessingStage.SAVING
        ]

        for i in range(len(stages) - 1):
            current_end = calc.STAGE_WEIGHTS[stages[i]][1]
            next_start = calc.STAGE_WEIGHTS[stages[i + 1]][0]
            assert current_end == next_start, (
                f"Gap detected: {stages[i]} ends at {current_end}%, "
                f"but {stages[i + 1]} starts at {next_start}%"
            )

    def test_calculate_progress_stage_start(self):
        """Test progress at start of each stage (sub_progress=0.0)"""
        calc = ProgressCalculator()
        expected = {
            ProcessingStage.UPLOADING: 0,
            ProcessingStage.PREPROCESSING: 5,
            ProcessingStage.TRANSCRIBING: 15,
            ProcessingStage.DIARIZING: 55,
            ProcessingStage.GENERATING_NOTES: 85,
            ProcessingStage.SAVING: 95
        }

        for stage, expected_progress in expected.items():
            progress = calc.calculate_progress(stage, sub_progress=0.0)
            assert progress == expected_progress, (
                f"{stage} with sub_progress=0.0 should be {expected_progress}%, got {progress}%"
            )

    def test_calculate_progress_stage_end(self):
        """Test progress at end of each stage (sub_progress=1.0)"""
        calc = ProgressCalculator()
        expected = {
            ProcessingStage.UPLOADING: 5,
            ProcessingStage.PREPROCESSING: 15,
            ProcessingStage.TRANSCRIBING: 55,
            ProcessingStage.DIARIZING: 85,
            ProcessingStage.GENERATING_NOTES: 95,
            ProcessingStage.SAVING: 100
        }

        for stage, expected_progress in expected.items():
            progress = calc.calculate_progress(stage, sub_progress=1.0)
            assert progress == expected_progress, (
                f"{stage} with sub_progress=1.0 should be {expected_progress}%, got {progress}%"
            )

    def test_calculate_progress_midpoint(self):
        """Test progress at midpoint of each stage (sub_progress=0.5)"""
        calc = ProgressCalculator()

        # Uploading: 0-5% (weight 5%) → 50% = 2.5%
        assert calc.calculate_progress(ProcessingStage.UPLOADING, 0.5) == 2

        # Preprocessing: 5-15% (weight 10%) → 50% = 10%
        assert calc.calculate_progress(ProcessingStage.PREPROCESSING, 0.5) == 10

        # Transcribing: 15-55% (weight 40%) → 50% = 35%
        assert calc.calculate_progress(ProcessingStage.TRANSCRIBING, 0.5) == 35

        # Diarizing: 55-85% (weight 30%) → 50% = 70%
        assert calc.calculate_progress(ProcessingStage.DIARIZING, 0.5) == 70

        # Generating notes: 85-95% (weight 10%) → 50% = 90%
        assert calc.calculate_progress(ProcessingStage.GENERATING_NOTES, 0.5) == 90

        # Saving: 95-100% (weight 5%) → 50% = 97.5%
        assert calc.calculate_progress(ProcessingStage.SAVING, 0.5) == 97

    def test_calculate_progress_invalid_stage(self):
        """Test error handling for invalid stage"""
        calc = ProgressCalculator()
        with pytest.raises(ValueError, match="Invalid stage"):
            calc.calculate_progress("invalid_stage", 0.5)

    def test_calculate_progress_invalid_sub_progress_high(self):
        """Test error handling for sub_progress > 1.0"""
        calc = ProgressCalculator()
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            calc.calculate_progress(ProcessingStage.TRANSCRIBING, 1.5)

    def test_calculate_progress_invalid_sub_progress_low(self):
        """Test error handling for sub_progress < 0.0"""
        calc = ProgressCalculator()
        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            calc.calculate_progress(ProcessingStage.TRANSCRIBING, -0.1)

    def test_calculate_progress_boundary_values(self):
        """Test edge cases with boundary sub_progress values"""
        calc = ProgressCalculator()

        # Test with 0.0 (minimum)
        assert calc.calculate_progress(ProcessingStage.TRANSCRIBING, 0.0) == 15

        # Test with 1.0 (maximum)
        assert calc.calculate_progress(ProcessingStage.TRANSCRIBING, 1.0) == 55

        # Test with very small value
        assert calc.calculate_progress(ProcessingStage.TRANSCRIBING, 0.01) == 15

        # Test with value close to 1.0
        assert calc.calculate_progress(ProcessingStage.TRANSCRIBING, 0.99) == 54

    def test_estimate_time_remaining_linear(self):
        """Test time estimation with linear progression"""
        calc = ProgressCalculator()

        # 50% done in 100 seconds → should take ~100 more seconds
        remaining = calc.estimate_time_remaining(50, 100)
        assert remaining == 100

        # 75% done in 150 seconds → should take ~50 more seconds
        remaining = calc.estimate_time_remaining(75, 150)
        assert remaining == 50

        # 25% done in 50 seconds → should take ~150 more seconds
        remaining = calc.estimate_time_remaining(25, 50)
        assert remaining == 150

    def test_estimate_time_remaining_insufficient_progress(self):
        """Test time estimation returns None for insufficient progress"""
        calc = ProgressCalculator()

        # Less than MIN_PROGRESS_FOR_ESTIMATION (10%)
        assert calc.estimate_time_remaining(5, 10) is None
        assert calc.estimate_time_remaining(9, 20) is None

        # Exactly at threshold should work
        result = calc.estimate_time_remaining(10, 20)
        assert result is not None

    def test_estimate_time_remaining_edge_cases(self):
        """Test time estimation edge cases"""
        calc = ProgressCalculator()

        # Zero elapsed time
        assert calc.estimate_time_remaining(50, 0) is None

        # Negative elapsed time (invalid)
        assert calc.estimate_time_remaining(50, -10) is None

        # Zero progress
        assert calc.estimate_time_remaining(0, 100) is None

        # Negative progress (invalid)
        assert calc.estimate_time_remaining(-5, 100) is None

        # 100% complete
        assert calc.estimate_time_remaining(100, 100) == 0

        # Over 100% (edge case)
        assert calc.estimate_time_remaining(105, 100) == 0

    def test_estimate_time_remaining_realistic_scenario(self):
        """Test time estimation with realistic pipeline scenario"""
        calc = ProgressCalculator()

        # Scenario: 60-minute therapy session processing
        # User is at 35% (middle of transcription stage)
        # 120 seconds elapsed (2 minutes)

        progress = calc.calculate_progress(ProcessingStage.TRANSCRIBING, 0.5)
        assert progress == 35

        remaining = calc.estimate_time_remaining(progress, 120)
        # 35% done in 120s → rate = 0.2917% per second
        # 65% remaining → ~223 seconds (~3.7 minutes)
        assert 220 <= remaining <= 225

    def test_get_stage_info(self):
        """Test getting detailed information about a stage"""
        calc = ProgressCalculator()

        info = calc.get_stage_info(ProcessingStage.TRANSCRIBING)

        assert info['stage'] == 'transcribing'
        assert info['start_percent'] == 15
        assert info['end_percent'] == 55
        assert info['weight_percent'] == 40
        assert 'Whisper' in info['description']

    def test_get_stage_info_all_stages(self):
        """Test getting info for all stages"""
        calc = ProgressCalculator()

        stages = [
            ProcessingStage.UPLOADING,
            ProcessingStage.PREPROCESSING,
            ProcessingStage.TRANSCRIBING,
            ProcessingStage.DIARIZING,
            ProcessingStage.GENERATING_NOTES,
            ProcessingStage.SAVING
        ]

        for stage in stages:
            info = calc.get_stage_info(stage)
            assert 'stage' in info
            assert 'start_percent' in info
            assert 'end_percent' in info
            assert 'weight_percent' in info
            assert 'description' in info
            assert info['weight_percent'] > 0

    def test_get_all_stages_info(self):
        """Test getting information about all stages at once"""
        calc = ProgressCalculator()

        all_info = calc.get_all_stages_info()

        assert len(all_info) == 6
        assert all_info[0]['stage'] == 'uploading'
        assert all_info[-1]['stage'] == 'saving'

        # Verify total weight is 100%
        total_weight = sum(s['weight_percent'] for s in all_info)
        assert total_weight == 100

    def test_handle_stage_transition_forward(self):
        """Test normal forward stage transition"""
        calc = ProgressCalculator()

        # Normal transition: uploading → preprocessing
        adjusted = calc.handle_stage_transition(
            ProcessingStage.UPLOADING,
            ProcessingStage.PREPROCESSING,
            5
        )
        assert adjusted == 5

        # Normal transition with progress increase
        adjusted = calc.handle_stage_transition(
            ProcessingStage.PREPROCESSING,
            ProcessingStage.TRANSCRIBING,
            15
        )
        assert adjusted == 15

    def test_handle_stage_transition_backward(self):
        """Test handling out-of-order status updates (backward transition)"""
        calc = ProgressCalculator()

        # Backward transition (out of order status update)
        # Already at 35% (transcribing), but receive update for preprocessing
        adjusted = calc.handle_stage_transition(
            ProcessingStage.TRANSCRIBING,
            ProcessingStage.PREPROCESSING,
            35
        )
        # Should not go backward
        assert adjusted >= 35

    def test_handle_stage_transition_same_stage(self):
        """Test transition to same stage (no change)"""
        calc = ProgressCalculator()

        adjusted = calc.handle_stage_transition(
            ProcessingStage.TRANSCRIBING,
            ProcessingStage.TRANSCRIBING,
            30
        )
        assert adjusted == 30

    def test_singleton_instance(self):
        """Test that get_progress_calculator returns singleton instance"""
        calc1 = get_progress_calculator()
        calc2 = get_progress_calculator()

        assert calc1 is calc2  # Same instance
        assert id(calc1) == id(calc2)

    def test_progress_never_exceeds_100(self):
        """Test that calculated progress never exceeds 100%"""
        calc = ProgressCalculator()

        # Even with sub_progress=1.0 at final stage
        progress = calc.calculate_progress(ProcessingStage.SAVING, 1.0)
        assert progress == 100

        # Even if we somehow get invalid data
        progress = calc.calculate_progress(ProcessingStage.SAVING, 0.99)
        assert progress <= 100

    def test_transcribing_has_highest_weight(self):
        """Verify transcribing stage has highest weight (slowest)"""
        calc = ProgressCalculator()

        weights = {
            stage: end - start
            for stage, (start, end) in calc.STAGE_WEIGHTS.items()
        }

        max_weight = max(weights.values())
        assert weights[ProcessingStage.TRANSCRIBING] == max_weight
        assert weights[ProcessingStage.TRANSCRIBING] == 40

    def test_diarizing_has_second_highest_weight(self):
        """Verify diarizing stage has second highest weight"""
        calc = ProgressCalculator()

        weights = {
            stage: end - start
            for stage, (start, end) in calc.STAGE_WEIGHTS.items()
        }

        sorted_weights = sorted(weights.values(), reverse=True)
        assert weights[ProcessingStage.DIARIZING] == sorted_weights[1]
        assert weights[ProcessingStage.DIARIZING] == 30

    def test_realistic_full_pipeline_progression(self):
        """Test realistic progression through entire pipeline"""
        calc = ProgressCalculator()

        # Simulate full pipeline progression
        timeline = [
            (ProcessingStage.UPLOADING, 0.0, 0),
            (ProcessingStage.UPLOADING, 0.5, 2),
            (ProcessingStage.UPLOADING, 1.0, 5),
            (ProcessingStage.PREPROCESSING, 0.0, 5),
            (ProcessingStage.PREPROCESSING, 0.5, 10),
            (ProcessingStage.PREPROCESSING, 1.0, 15),
            (ProcessingStage.TRANSCRIBING, 0.0, 15),
            (ProcessingStage.TRANSCRIBING, 0.25, 25),
            (ProcessingStage.TRANSCRIBING, 0.5, 35),
            (ProcessingStage.TRANSCRIBING, 0.75, 45),
            (ProcessingStage.TRANSCRIBING, 1.0, 55),
            (ProcessingStage.DIARIZING, 0.0, 55),
            (ProcessingStage.DIARIZING, 0.5, 70),
            (ProcessingStage.DIARIZING, 1.0, 85),
            (ProcessingStage.GENERATING_NOTES, 0.0, 85),
            (ProcessingStage.GENERATING_NOTES, 0.5, 90),
            (ProcessingStage.GENERATING_NOTES, 1.0, 95),
            (ProcessingStage.SAVING, 0.0, 95),
            (ProcessingStage.SAVING, 1.0, 100),
        ]

        for stage, sub_progress, expected_progress in timeline:
            actual = calc.calculate_progress(stage, sub_progress)
            assert actual == expected_progress, (
                f"{stage} with sub_progress={sub_progress} should be {expected_progress}%, "
                f"got {actual}%"
            )

    def test_progress_monotonically_increases(self):
        """Test that progress only increases, never decreases"""
        calc = ProgressCalculator()

        # Simulate progression with previous progress tracking
        stages_progression = [
            (ProcessingStage.UPLOADING, 0.5),
            (ProcessingStage.UPLOADING, 1.0),
            (ProcessingStage.PREPROCESSING, 0.3),
            (ProcessingStage.PREPROCESSING, 0.8),
            (ProcessingStage.TRANSCRIBING, 0.1),
            (ProcessingStage.TRANSCRIBING, 0.5),
            (ProcessingStage.TRANSCRIBING, 0.9),
            (ProcessingStage.DIARIZING, 0.2),
            (ProcessingStage.DIARIZING, 0.7),
            (ProcessingStage.GENERATING_NOTES, 0.4),
            (ProcessingStage.SAVING, 0.5),
            (ProcessingStage.SAVING, 1.0),
        ]

        previous_progress = -1
        for stage, sub_progress in stages_progression:
            current_progress = calc.calculate_progress(stage, sub_progress)
            assert current_progress >= previous_progress, (
                f"Progress decreased from {previous_progress}% to {current_progress}% "
                f"at {stage} with sub_progress={sub_progress}"
            )
            previous_progress = current_progress


class TestProcessingStage:
    """Test suite for ProcessingStage enum"""

    def test_all_stages_defined(self):
        """Verify all expected stages are defined"""
        expected_stages = [
            "uploading",
            "preprocessing",
            "transcribing",
            "diarizing",
            "generating_notes",
            "saving",
            "completed",
            "failed"
        ]

        for stage_name in expected_stages:
            assert hasattr(ProcessingStage, stage_name.upper())

    def test_stage_values_are_lowercase(self):
        """Verify stage values use lowercase with underscores"""
        for stage in ProcessingStage:
            assert stage.value == stage.value.lower()
            assert ' ' not in stage.value


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
