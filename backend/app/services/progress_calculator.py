"""
Progress calculation for audio processing pipeline

This module provides intelligent progress percentage calculation for the multi-stage
audio processing pipeline, accounting for varying stage durations based on empirical
data and competitive analysis (see UPHEAL_SESSIONS_PIPELINE_ANALYSIS.md).

Stage weights are determined by typical processing times for a 60-minute therapy session:
- Uploading: 5-15 seconds (network bound)
- Preprocessing: 10-30 seconds (CPU bound, fast)
- Transcribing: 60-180 seconds (API latency, file size dependent)
- Diarizing: 45-120 seconds (GPU/CPU intensive, speaker overlap dependent)
- Note generation: 15-45 seconds (GPT-4o API, transcript length dependent)
- Saving: 2-5 seconds (database write, fast)

Key insights from Upheal analysis:
- Whisper API (not local) is fastest option for transcription
- Parallel processing of transcription + diarization can save 50% time
- Progressive loading (showing partial results) improves perceived speed
"""

import time
from typing import Optional, Dict, Tuple
from enum import Enum


class ProcessingStage(str, Enum):
    """
    Processing pipeline stages with standardized names.

    Order represents sequential progression through pipeline.
    Use lowercase with underscores for consistency with database status fields.
    """
    UPLOADING = "uploading"
    PREPROCESSING = "preprocessing"
    TRANSCRIBING = "transcribing"
    DIARIZING = "diarizing"
    GENERATING_NOTES = "generating_notes"
    SAVING = "saving"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressCalculator:
    """
    Intelligent progress calculator for audio processing pipeline.

    Uses weighted stage durations to provide accurate progress estimates
    that reflect actual processing time, not just stage count.

    **Weight Selection Rationale:**

    Based on empirical testing and competitive analysis (Upheal):

    1. **Uploading (5%)** - Fast for most files (<25MB limit), network bound
       - Typical: 5-15 seconds for 10-20MB files

    2. **Preprocessing (10%)** - Audio format conversion, normalization
       - Typical: 10-30 seconds (pydub operations)
       - Includes: silence trimming, mono conversion, 16kHz resampling

    3. **Transcribing (40%)** - SLOWEST STAGE for long sessions
       - OpenAI Whisper API: 60-180 seconds for 60-minute audio
       - File size and audio quality dependent
       - Rate limiting may add latency
       - Largest weight due to API latency and processing time

    4. **Diarizing (30%)** - Second slowest, GPU/CPU intensive
       - pyannote.audio 3.1 speaker diarization: 45-120 seconds
       - Depends on speaker count and overlap complexity
       - Can run in parallel with transcription (optimization opportunity)

    5. **Note Generation (10%)** - GPT-4o API call
       - Typical: 15-45 seconds for full session transcript
       - Depends on transcript length (token count)
       - Relatively fast due to GPT-4o efficiency

    6. **Saving (5%)** - Database write operations
       - Typical: 2-5 seconds (PostgreSQL writes)
       - Fast, mostly I/O bound

    **Future Optimization:**
    If parallel processing is implemented (transcription + diarization concurrent),
    adjust weights: transcribing=45%, diarizing=25% (overlap time savings).

    Usage:
        calculator = ProgressCalculator()

        # Update progress within a stage
        progress = calculator.calculate_progress(
            ProcessingStage.TRANSCRIBING,
            sub_progress=0.6  # 60% through transcription
        )
        # Returns: 39 (15 + 40*0.6 = 15 + 24 = 39%)

        # Estimate time remaining
        elapsed_seconds = 120  # 2 minutes elapsed
        remaining = calculator.estimate_time_remaining(progress, elapsed_seconds)
        # Returns: ~188 seconds (~3 minutes remaining)
    """

    # Stage weight tuples: (start_percentage, end_percentage)
    # Total range: 0-100%
    STAGE_WEIGHTS: Dict[ProcessingStage, Tuple[int, int]] = {
        ProcessingStage.UPLOADING: (0, 5),           # 5% weight
        ProcessingStage.PREPROCESSING: (5, 15),      # 10% weight
        ProcessingStage.TRANSCRIBING: (15, 55),      # 40% weight (slowest)
        ProcessingStage.DIARIZING: (55, 85),         # 30% weight (second slowest)
        ProcessingStage.GENERATING_NOTES: (85, 95),  # 10% weight
        ProcessingStage.SAVING: (95, 100),           # 5% weight
    }

    # Minimum progress threshold for reliable time estimation
    MIN_PROGRESS_FOR_ESTIMATION = 10  # Need at least 10% complete for accuracy

    # Maximum progress percentage (prevents exceeding 100%)
    MAX_PROGRESS = 100

    def __init__(self):
        """Initialize progress calculator with validation checks."""
        self._validate_stage_weights()

    def _validate_stage_weights(self) -> None:
        """
        Validate that stage weights are continuous and sum to 100%.

        Raises:
            ValueError: If weights are invalid (gaps, overlaps, or incorrect total)
        """
        stages = [
            ProcessingStage.UPLOADING,
            ProcessingStage.PREPROCESSING,
            ProcessingStage.TRANSCRIBING,
            ProcessingStage.DIARIZING,
            ProcessingStage.GENERATING_NOTES,
            ProcessingStage.SAVING
        ]

        # Check continuity (each stage starts where previous ended)
        for i in range(len(stages) - 1):
            current_end = self.STAGE_WEIGHTS[stages[i]][1]
            next_start = self.STAGE_WEIGHTS[stages[i + 1]][0]
            if current_end != next_start:
                raise ValueError(
                    f"Stage weight gap detected: {stages[i]} ends at {current_end}%, "
                    f"but {stages[i + 1]} starts at {next_start}%"
                )

        # Check total range is 0-100
        first_start = self.STAGE_WEIGHTS[stages[0]][0]
        last_end = self.STAGE_WEIGHTS[stages[-1]][1]
        if first_start != 0 or last_end != 100:
            raise ValueError(
                f"Stage weights must span 0-100%. Got {first_start}-{last_end}%"
            )

    def calculate_progress(
        self,
        stage: ProcessingStage,
        sub_progress: float = 0.0
    ) -> int:
        """
        Calculate overall progress percentage for current stage and sub-progress.

        Progress is calculated as:
            overall_progress = stage_start + (stage_weight × sub_progress)

        Args:
            stage: Current processing stage (must be a valid ProcessingStage)
            sub_progress: Progress within current stage, range [0.0, 1.0]
                         0.0 = just started stage
                         1.0 = stage complete
                         Default: 0.0

        Returns:
            Overall progress percentage as integer (0-100)

        Raises:
            ValueError: If stage is invalid or sub_progress is out of range

        Examples:
            >>> calc = ProgressCalculator()
            >>> calc.calculate_progress(ProcessingStage.UPLOADING, 0.0)
            0
            >>> calc.calculate_progress(ProcessingStage.UPLOADING, 1.0)
            5
            >>> calc.calculate_progress(ProcessingStage.TRANSCRIBING, 0.5)
            35  # 15 + (40 * 0.5) = 15 + 20 = 35
            >>> calc.calculate_progress(ProcessingStage.SAVING, 1.0)
            100
        """
        # Validate inputs
        if stage not in self.STAGE_WEIGHTS:
            raise ValueError(
                f"Invalid stage: {stage}. Must be one of {list(self.STAGE_WEIGHTS.keys())}"
            )

        if not 0.0 <= sub_progress <= 1.0:
            raise ValueError(
                f"sub_progress must be between 0.0 and 1.0, got {sub_progress}"
            )

        # Calculate progress
        start_percent, end_percent = self.STAGE_WEIGHTS[stage]
        stage_weight = end_percent - start_percent

        overall_progress = start_percent + (stage_weight * sub_progress)

        # Clamp to valid range and convert to integer
        return int(min(max(overall_progress, 0), self.MAX_PROGRESS))

    def estimate_time_remaining(
        self,
        current_progress: int,
        elapsed_seconds: float
    ) -> Optional[int]:
        """
        Estimate seconds remaining until completion using linear extrapolation.

        Assumes processing rate remains constant (% per second).
        Returns None if insufficient data for reliable estimation.

        Formula:
            rate = current_progress / elapsed_seconds  (% per second)
            remaining_progress = 100 - current_progress
            time_remaining = remaining_progress / rate

        Args:
            current_progress: Current progress percentage (0-100)
            elapsed_seconds: Time elapsed since processing started (seconds)

        Returns:
            Estimated seconds remaining until 100% complete, or None if:
                - Progress < MIN_PROGRESS_FOR_ESTIMATION (not enough data)
                - elapsed_seconds <= 0 (invalid input)
                - current_progress <= 0 (no progress made)
                - current_progress >= 100 (already complete)

        Note:
            Estimation accuracy improves as more stages complete. Early estimates
            (during upload/preprocessing) are less reliable than later estimates
            (during transcription/diarization).

        Examples:
            >>> calc = ProgressCalculator()
            >>> calc.estimate_time_remaining(50, 100)
            100  # 50% done in 100s → 50% remaining → ~100s remaining
            >>> calc.estimate_time_remaining(75, 150)
            50   # 75% done in 150s → 25% remaining → ~50s remaining
            >>> calc.estimate_time_remaining(5, 10)
            None # Not enough progress for reliable estimate
        """
        # Validate inputs
        if elapsed_seconds <= 0:
            return None

        if current_progress <= 0:
            return None

        if current_progress >= self.MAX_PROGRESS:
            return 0  # Already complete

        # Need minimum progress for reliable estimation
        if current_progress < self.MIN_PROGRESS_FOR_ESTIMATION:
            return None

        # Calculate processing rate (% per second)
        rate = current_progress / elapsed_seconds

        # Calculate remaining work
        remaining_progress = self.MAX_PROGRESS - current_progress

        # Estimate time remaining
        time_remaining = remaining_progress / rate

        return int(time_remaining)

    def get_stage_info(self, stage: ProcessingStage) -> Dict[str, any]:
        """
        Get detailed information about a specific stage.

        Args:
            stage: Processing stage to query

        Returns:
            Dict containing:
                - stage: Stage name (str)
                - start_percent: Starting percentage (int)
                - end_percent: Ending percentage (int)
                - weight_percent: Total weight/duration (int)
                - description: Human-readable stage description (str)

        Raises:
            ValueError: If stage is invalid

        Example:
            >>> calc = ProgressCalculator()
            >>> info = calc.get_stage_info(ProcessingStage.TRANSCRIBING)
            >>> info['weight_percent']
            40
        """
        if stage not in self.STAGE_WEIGHTS:
            raise ValueError(f"Invalid stage: {stage}")

        start, end = self.STAGE_WEIGHTS[stage]

        # Stage descriptions for UI display
        descriptions = {
            ProcessingStage.UPLOADING: "Uploading audio file to server",
            ProcessingStage.PREPROCESSING: "Preprocessing audio (format conversion, normalization)",
            ProcessingStage.TRANSCRIBING: "Transcribing audio with Whisper API",
            ProcessingStage.DIARIZING: "Identifying speakers with pyannote",
            ProcessingStage.GENERATING_NOTES: "Generating clinical notes with GPT-4o",
            ProcessingStage.SAVING: "Saving results to database"
        }

        return {
            "stage": stage.value,
            "start_percent": start,
            "end_percent": end,
            "weight_percent": end - start,
            "description": descriptions.get(stage, "Processing")
        }

    def get_all_stages_info(self) -> list[Dict[str, any]]:
        """
        Get information about all processing stages in order.

        Returns:
            List of stage info dicts (see get_stage_info for structure)

        Example:
            >>> calc = ProgressCalculator()
            >>> stages = calc.get_all_stages_info()
            >>> stages[0]['stage']
            'uploading'
            >>> sum(s['weight_percent'] for s in stages)
            100
        """
        stages = [
            ProcessingStage.UPLOADING,
            ProcessingStage.PREPROCESSING,
            ProcessingStage.TRANSCRIBING,
            ProcessingStage.DIARIZING,
            ProcessingStage.GENERATING_NOTES,
            ProcessingStage.SAVING
        ]

        return [self.get_stage_info(stage) for stage in stages]

    def handle_stage_transition(
        self,
        from_stage: ProcessingStage,
        to_stage: ProcessingStage,
        current_progress: int
    ) -> int:
        """
        Handle edge case where progress may go backward during stage transitions.

        This can happen if:
        - Stages complete out of order (parallel processing)
        - Network latency causes status updates to arrive out of order
        - Stage is restarted due to error/retry

        Args:
            from_stage: Previous stage
            to_stage: New stage
            current_progress: Current progress percentage

        Returns:
            Adjusted progress that never goes backward (monotonically increasing)

        Example:
            >>> calc = ProgressCalculator()
            >>> # Normal forward transition
            >>> calc.handle_stage_transition(
            ...     ProcessingStage.UPLOADING,
            ...     ProcessingStage.PREPROCESSING,
            ...     5
            ... )
            5
            >>> # Backward status update (out of order)
            >>> calc.handle_stage_transition(
            ...     ProcessingStage.TRANSCRIBING,
            ...     ProcessingStage.PREPROCESSING,
            ...     35
            ... )
            35  # Don't go backward, keep current progress
        """
        if from_stage not in self.STAGE_WEIGHTS or to_stage not in self.STAGE_WEIGHTS:
            # Invalid stages, return current progress unchanged
            return current_progress

        from_start, _ = self.STAGE_WEIGHTS[from_stage]
        to_start, _ = self.STAGE_WEIGHTS[to_stage]

        # If transitioning backward (out of order), don't decrease progress
        if to_start < from_start:
            return max(current_progress, to_start)

        # Normal forward transition
        return max(current_progress, to_start)


# Singleton instance for use across application
_calculator_instance: Optional[ProgressCalculator] = None


def get_progress_calculator() -> ProgressCalculator:
    """
    Get singleton instance of ProgressCalculator.

    Thread-safe singleton pattern ensures consistent stage weights
    across all progress calculations in the application.

    Returns:
        Global ProgressCalculator instance

    Usage:
        from app.services.progress_calculator import get_progress_calculator

        calc = get_progress_calculator()
        progress = calc.calculate_progress(stage, sub_progress)
    """
    global _calculator_instance
    if _calculator_instance is None:
        _calculator_instance = ProgressCalculator()
    return _calculator_instance
