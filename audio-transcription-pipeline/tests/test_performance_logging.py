#!/usr/bin/env python3
"""
Test script for the enhanced performance logging system
========================================================

This script demonstrates the performance logging capabilities by:
1. Running a sample audio through the pipeline
2. Collecting detailed timing metrics
3. Generating performance reports
4. Comparing CPU vs GPU performance (if available)
"""

import os
import sys
import json
import time
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from performance_logger import PerformanceLogger, get_logger, reset_logger
from pipeline_enhanced import (
    AudioPreprocessor,
    WhisperTranscriber,
    SpeakerDiarizer,
    EnhancedAudioTranscriptionPipeline
)


def test_basic_logging():
    """Test basic performance logging functionality"""
    print("\n" + "="*60)
    print("TEST 1: Basic Performance Logging")
    print("="*60)

    # Create a logger with path relative to script location
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "outputs" / "performance_logs" / "tests"

    logger = PerformanceLogger(
        name="BasicTest",
        output_dir=str(output_dir),
        verbose=True
    )

    logger.start_pipeline()

    # Simulate some operations with timing
    logger.start_stage("Data Loading")

    with logger.subprocess("file_reading", {"file_size": "10MB"}):
        time.sleep(0.1)  # Simulate file reading

    with logger.subprocess("data_parsing"):
        time.sleep(0.05)  # Simulate parsing

    logger.end_stage("Data Loading")

    # Another stage
    logger.start_stage("Processing")

    with logger.timer("computation_1"):
        time.sleep(0.2)

    with logger.timer("computation_2"):
        time.sleep(0.15)

    logger.end_stage("Processing")

    logger.end_pipeline()

    print("\n✅ Basic logging test completed")
    print(f"Reports saved in: outputs/performance_logs/tests/")


def test_subprocess_tracking():
    """Test detailed subprocess tracking"""
    print("\n" + "="*60)
    print("TEST 2: Subprocess Performance Tracking")
    print("="*60)

    # Use path relative to script location
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "outputs" / "performance_logs" / "tests"

    logger = PerformanceLogger(
        name="SubprocessTest",
        output_dir=str(output_dir),
        verbose=True
    )

    logger.start_pipeline()

    # Test nested subprocess tracking
    logger.start_stage("Audio Processing")

    # Simulate audio processing steps
    operations = [
        ("load_audio", 0.08),
        ("detect_silence", 0.12),
        ("trim_silence", 0.05),
        ("normalize_volume", 0.07),
        ("resample_audio", 0.25),
        ("export_audio", 0.10)
    ]

    for op_name, duration in operations:
        with logger.subprocess(op_name):
            time.sleep(duration)
            logger.log(f"  Processing: {op_name}", level="DEBUG")

    logger.end_stage("Audio Processing")

    # Show timing summary
    logger.end_pipeline()

    print("\n✅ Subprocess tracking test completed")


def test_gpu_monitoring():
    """Test GPU monitoring capabilities"""
    print("\n" + "="*60)
    print("TEST 3: GPU Monitoring")
    print("="*60)

    try:
        import torch
        has_gpu = torch.cuda.is_available() or (
            hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
        )
    except ImportError:
        has_gpu = False

    if not has_gpu:
        print("⚠️  No GPU available, skipping GPU monitoring test")
        return

    # Use path relative to script location
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "outputs" / "performance_logs" / "tests"

    logger = PerformanceLogger(
        name="GPUTest",
        output_dir=str(output_dir),
        enable_gpu_monitoring=True,
        verbose=True
    )

    logger.start_pipeline()
    logger.start_stage("GPU Operations")

    # Simulate GPU operations
    if has_gpu:
        import torch

        device = torch.device("cuda" if torch.cuda.is_available() else "mps")
        logger.log(f"Using device: {device}", level="INFO")

        with logger.subprocess("tensor_operations", {"device": str(device)}):
            # Create some tensors on GPU
            a = torch.randn(1000, 1000, device=device)
            b = torch.randn(1000, 1000, device=device)

            # Perform operations
            for i in range(10):
                c = torch.matmul(a, b)
                time.sleep(0.01)

            logger.log(f"Tensor shape: {c.shape}", level="DEBUG")

    logger.end_stage("GPU Operations")
    logger.end_pipeline()

    print("\n✅ GPU monitoring test completed")


def test_real_audio_pipeline():
    """Test with actual audio file if available"""
    print("\n" + "="*60)
    print("TEST 4: Real Audio Pipeline Performance")
    print("="*60)

    # Look for test audio files - use path relative to script location
    script_dir = Path(__file__).parent
    test_files = [
        script_dir / "samples" / "compressed-cbt-session.m4a",
        script_dir / "samples" / "LIVE Cognitive Behavioral Therapy Session (1).mp3",
        script_dir / "samples" / "Person-Centred Therapy Session - Full Example [VLDDUL3HBIg].mp3",
    ]

    audio_file = None
    for file in test_files:
        if file.exists():
            audio_file = str(file)
            break

    if not audio_file:
        print("⚠️  No test audio file found, creating synthetic test...")
        audio_file = create_test_audio()

    print(f"Testing with: {audio_file}")

    # Use path relative to script location
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "outputs" / "performance_logs" / "tests"

    # Run enhanced pipeline
    pipeline = EnhancedAudioTranscriptionPipeline(
        enable_performance_logging=True,
        output_dir=str(output_dir)
    )

    try:
        # Test preprocessing only (doesn't need API keys)
        logger = pipeline.logger
        logger.start_pipeline()

        # Just test preprocessing
        print("\nRunning preprocessing performance test...")
        preprocessor = AudioPreprocessor(logger=logger)
        processed = preprocessor.preprocess(audio_file)

        logger.end_pipeline()

        print(f"\n✅ Pipeline test completed")
        print(f"Processed audio: {processed}")

    except Exception as e:
        print(f"⚠️  Pipeline test failed: {e}")


def create_test_audio():
    """Create a simple test audio file"""
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine

        # Generate 5 second sine wave
        tone = Sine(440).to_audio_segment(duration=5000)
        test_file = "test_audio_generated.mp3"
        tone.export(test_file, format="mp3")

        print(f"Generated test audio: {test_file}")
        return test_file

    except ImportError:
        print("pydub not installed, cannot generate test audio")
        return None


def test_performance_comparison():
    """Compare performance with and without enhancements"""
    print("\n" + "="*60)
    print("TEST 5: Performance Comparison")
    print("="*60)

    # Create test data
    test_segments = [{"start": i, "end": i+1, "text": f"Segment {i}"} for i in range(100)]
    test_turns = [{"start": i*0.5, "end": i*0.5+2, "speaker": f"SPEAKER_{i%2:02d}"} for i in range(50)]

    # Test CPU alignment
    logger = PerformanceLogger(name="ComparisonTest", verbose=False)
    pipeline = EnhancedAudioTranscriptionPipeline(enable_performance_logging=False)
    pipeline.logger = logger

    # CPU version
    start = time.perf_counter()
    aligned_cpu = pipeline._align_speakers_cpu(test_segments, test_turns)
    cpu_time = time.perf_counter() - start

    print(f"CPU Alignment: {cpu_time*1000:.2f}ms for {len(test_segments)} segments")

    # GPU version (if available)
    try:
        import torch
        if torch.cuda.is_available() or (hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()):
            start = time.perf_counter()
            aligned_gpu = pipeline._align_speakers_gpu(test_segments, test_turns)
            gpu_time = time.perf_counter() - start

            print(f"GPU Alignment: {gpu_time*1000:.2f}ms for {len(test_segments)} segments")
            print(f"Speedup: {cpu_time/gpu_time:.1f}x")

            # Verify results match
            matches = sum(1 for c, g in zip(aligned_cpu, aligned_gpu) if c["speaker"] == g["speaker"])
            print(f"Accuracy: {matches}/{len(test_segments)} matches")
        else:
            print("No GPU available for comparison")

    except ImportError:
        print("PyTorch not available for GPU comparison")

    print("\n✅ Performance comparison completed")


def analyze_performance_logs():
    """Analyze and summarize all performance logs"""
    print("\n" + "="*60)
    print("PERFORMANCE LOG ANALYSIS")
    print("="*60)

    # Use path relative to script location
    script_dir = Path(__file__).parent
    log_dir = script_dir.parent / "outputs" / "performance_logs" / "tests"

    if not log_dir.exists():
        print(f"No performance logs found at: {log_dir.absolute()}")
        return

    # Find all JSON logs
    json_files = list(log_dir.glob("performance_*.json"))

    if not json_files:
        print("No performance logs found")
        return

    print(f"Found {len(json_files)} performance logs\n")

    # Analyze each log
    total_times = []
    stage_times = {}

    for json_file in json_files:
        with open(json_file) as f:
            data = json.load(f)

        pipeline_name = data.get("pipeline_name", "Unknown")
        metrics = data.get("metrics", {})

        if metrics.get("total_duration"):
            total_times.append(metrics["total_duration"])

        print(f"Pipeline: {pipeline_name}")
        print(f"  Session: {data.get('session_id', 'N/A')}")
        print(f"  Total Time: {metrics.get('total_duration', 0):.2f}s")

        # Stage breakdown
        if metrics.get("stages"):
            print("  Stages:")
            for stage_name, stage_data in metrics["stages"].items():
                duration = stage_data.get("duration", 0)
                print(f"    - {stage_name}: {duration:.3f}s")

                if stage_name not in stage_times:
                    stage_times[stage_name] = []
                stage_times[stage_name].append(duration)

        print()

    # Summary statistics
    if total_times:
        print("SUMMARY STATISTICS")
        print("-" * 40)
        print(f"Average Total Time: {sum(total_times)/len(total_times):.2f}s")
        print(f"Min Total Time: {min(total_times):.2f}s")
        print(f"Max Total Time: {max(total_times):.2f}s")

    if stage_times:
        print("\nAverage Stage Times:")
        for stage, times in stage_times.items():
            avg_time = sum(times) / len(times)
            print(f"  {stage}: {avg_time:.3f}s")


def main():
    """Run all performance tests"""
    print("="*60)
    print("PERFORMANCE LOGGING TEST SUITE")
    print("="*60)

    # Create output directory - use path relative to script location
    script_dir = Path(__file__).parent
    output_dir = script_dir.parent / "outputs" / "performance_logs" / "tests"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Run tests
    test_basic_logging()
    test_subprocess_tracking()
    test_gpu_monitoring()
    test_real_audio_pipeline()
    test_performance_comparison()

    # Analyze results
    analyze_performance_logs()

    print("\n" + "="*60)
    print("ALL TESTS COMPLETED")
    print(f"Performance reports available in: {output_dir.absolute()}/")
    print("="*60)


if __name__ == "__main__":
    main()