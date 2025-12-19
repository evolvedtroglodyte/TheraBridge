#!/usr/bin/env python3
"""
Simple test of the performance logging system
"""

import sys
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from performance_logger import PerformanceLogger

def main():
    print("\n" + "="*60)
    print("PERFORMANCE LOGGING SYSTEM TEST")
    print("="*60)

    # Use path relative to script location
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "outputs" / "performance_logs"

    # Create a performance logger
    logger = PerformanceLogger(
        name="TestPipeline",
        output_dir=str(output_dir),
        enable_gpu_monitoring=True,
        verbose=True
    )

    # Start the pipeline
    logger.start_pipeline()
    print("\nSimulating audio processing pipeline...")

    # Stage 1: Audio Preprocessing
    logger.start_stage("Audio Preprocessing")

    with logger.subprocess("load_audio", {"file": "test.mp3", "size_mb": 5.2}):
        print("  Loading audio file...")
        time.sleep(0.1)

    with logger.subprocess("silence_detection"):
        print("  Detecting silence regions...")
        time.sleep(0.08)

    with logger.subprocess("silence_trimming"):
        print("  Trimming silence...")
        time.sleep(0.05)

    with logger.subprocess("volume_normalization"):
        print("  Normalizing volume...")
        time.sleep(0.06)

    with logger.subprocess("sample_rate_conversion", {"from": 44100, "to": 16000}):
        print("  Converting sample rate...")
        time.sleep(0.2)  # This is typically the slowest preprocessing operation

    with logger.subprocess("audio_export", {"format": "mp3"}):
        print("  Exporting processed audio...")
        time.sleep(0.09)

    logger.end_stage("Audio Preprocessing")

    # Stage 2: Whisper Transcription
    logger.start_stage("Whisper Transcription")

    with logger.subprocess("api_upload", {"size_mb": 4.8}):
        print("  Uploading to Whisper API...")
        time.sleep(0.3)

    with logger.subprocess("api_processing"):
        print("  Waiting for API response...")
        time.sleep(1.5)  # Simulate API processing time

    with logger.subprocess("response_parsing", {"segments": 45}):
        print("  Parsing transcription segments...")
        time.sleep(0.05)

    logger.end_stage("Whisper Transcription")

    # Stage 3: Speaker Diarization
    logger.start_stage("Speaker Diarization")

    with logger.subprocess("model_loading"):
        print("  Loading diarization model...")
        time.sleep(0.8)

    with logger.subprocess("audio_tensor_conversion"):
        print("  Converting audio to tensor...")
        time.sleep(0.1)

    with logger.subprocess("diarization_inference", {"device": "cpu", "num_speakers": 2}):
        print("  Running diarization model...")
        time.sleep(0.6)

    with logger.subprocess("speaker_alignment", {"segments": 45, "turns": 23}):
        print("  Aligning speakers with text...")
        time.sleep(0.08)

    logger.end_stage("Speaker Diarization")

    # End pipeline
    logger.end_pipeline()

    # Display results
    print("\n" + "="*60)
    print("PERFORMANCE RESULTS")
    print("="*60)

    if logger.metrics.get("total_duration"):
        print(f"\nTotal Pipeline Time: {logger.metrics['total_duration']:.2f}s")

        print("\nStage Breakdown:")
        for stage_name, stage_data in logger.metrics["stages"].items():
            duration = stage_data["duration"]
            percentage = (duration / logger.metrics['total_duration'] * 100)
            print(f"  {stage_name:25s} {duration:.2f}s ({percentage:.1f}%)")

        print("\nTop 5 Slowest Subprocesses:")
        # Collect all subprocesses
        all_subs = []
        for stage_data in logger.metrics["stages"].values():
            for sub_name, sub_data in stage_data["subprocesses"].items():
                all_subs.append((sub_name, sub_data["duration"]))

        # Sort by duration
        all_subs.sort(key=lambda x: x[1], reverse=True)

        for name, duration in all_subs[:5]:
            print(f"  {name:25s} {duration:.3f}s")

    print("\n" + "="*60)
    print(f"Full reports saved in: {logger.output_dir}")
    print("  - performance_*.json (machine-readable)")
    print("  - performance_*.txt (human-readable)")
    print("="*60)

if __name__ == "__main__":
    main()