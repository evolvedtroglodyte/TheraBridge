#!/usr/bin/env python3
"""
Example test file demonstrating proper use of pytest fixtures.

This file shows how to write tests that:
- Automatically skip when sample files are missing
- Use environment variables safely
- Handle temporary directories
- Are properly marked with requirements
"""

import pytest
from pathlib import Path


# ============================================================================
# Sample Audio Fixture Tests
# ============================================================================

@pytest.mark.requires_sample_audio
def test_with_cbt_sample(sample_cbt_session):
    """
    Test using specific CBT therapy session sample.

    This test will automatically skip if the sample file is not available.
    """
    assert sample_cbt_session.exists()
    assert sample_cbt_session.suffix == ".mp3"
    assert sample_cbt_session.stat().st_size > 0
    print(f"✅ Using CBT sample: {sample_cbt_session}")


@pytest.mark.requires_sample_audio
def test_with_any_sample(any_sample_audio):
    """
    Test using any available sample audio file.

    This is the recommended approach for most tests - it will use
    whichever sample file is available, making tests more resilient.
    """
    assert any_sample_audio.exists()
    assert any_sample_audio.suffix in [".mp3", ".m4a", ".wav"]
    assert any_sample_audio.stat().st_size > 0
    print(f"✅ Using sample: {any_sample_audio}")


@pytest.mark.requires_sample_audio
def test_with_person_centered_sample(sample_person_centered):
    """
    Test using specific person-centered therapy session sample.

    Skips if this specific file is not available.
    """
    assert sample_person_centered.exists()
    print(f"✅ Using person-centered sample: {sample_person_centered}")


# ============================================================================
# Environment Variable Tests
# ============================================================================

@pytest.mark.requires_openai
def test_with_openai_key(openai_api_key):
    """
    Test that requires OpenAI API key.

    Skips if OPENAI_API_KEY is not set in environment.
    """
    assert openai_api_key
    assert openai_api_key.startswith("sk-")
    print(f"✅ OpenAI API key available")


@pytest.mark.requires_hf
def test_with_hf_token(hf_token):
    """
    Test that requires HuggingFace token.

    Skips if HF_TOKEN is not set in environment.
    """
    assert hf_token
    assert hf_token.startswith("hf_")
    print(f"✅ HuggingFace token available")


# ============================================================================
# Directory Fixture Tests
# ============================================================================

def test_outputs_directory(outputs_dir):
    """
    Test using temporary outputs directory.

    The directory is automatically cleaned up after the test.
    """
    assert outputs_dir.exists()
    assert outputs_dir.is_dir()

    # Create a test file
    test_file = outputs_dir / "test_output.txt"
    test_file.write_text("Test data")

    assert test_file.exists()
    print(f"✅ Created output in: {outputs_dir}")


def test_processed_directory(processed_dir):
    """
    Test using temporary processed audio directory.
    """
    assert processed_dir.exists()
    assert processed_dir.is_dir()

    # Simulate processed audio file
    test_audio = processed_dir / "processed_audio.mp3"
    test_audio.write_bytes(b"fake audio data")

    assert test_audio.exists()
    print(f"✅ Created processed file in: {processed_dir}")


# ============================================================================
# Integration Test Examples
# ============================================================================

@pytest.mark.integration
def test_preprocessing_pipeline(any_sample_audio, processed_dir):
    """
    Integration test for audio preprocessing.

    Requires:
    - Sample audio file
    - OpenAI API key
    - HuggingFace token

    Automatically skips if any requirement is missing.
    """
    from pydub import AudioSegment

    # Load audio
    audio = AudioSegment.from_file(str(any_sample_audio))
    assert len(audio) > 0

    # Process audio (simplified example)
    mono_audio = audio.set_channels(1)
    mono_audio = mono_audio.set_frame_rate(16000)

    # Save to processed directory
    output_path = processed_dir / "processed_test.mp3"
    mono_audio.export(str(output_path), format="mp3")

    assert output_path.exists()
    print(f"✅ Processed audio saved to: {output_path}")


@pytest.mark.integration
def test_full_pipeline_simulation(any_sample_audio, outputs_dir, openai_api_key, hf_token):
    """
    Simulated full pipeline test.

    This test demonstrates how to use multiple fixtures together
    for integration testing.
    """
    import json

    # Verify all resources available
    assert any_sample_audio.exists()
    assert outputs_dir.exists()
    assert openai_api_key
    assert hf_token

    # Simulate pipeline results
    result = {
        "input_file": str(any_sample_audio),
        "file_size_mb": any_sample_audio.stat().st_size / (1024 * 1024),
        "status": "simulated",
        "segments": [
            {"start": 0.0, "end": 2.5, "text": "Hello, this is a test", "speaker": "SPEAKER_00"},
            {"start": 2.5, "end": 5.0, "text": "This is the response", "speaker": "SPEAKER_01"},
        ]
    }

    # Save results
    output_file = outputs_dir / "pipeline_result.json"
    output_file.write_text(json.dumps(result, indent=2))

    assert output_file.exists()
    print(f"✅ Pipeline simulation complete: {output_file}")


# ============================================================================
# Skip Condition Examples
# ============================================================================

def test_always_runs():
    """
    This test always runs - no special requirements.
    """
    assert 1 + 1 == 2
    print("✅ Basic test always runs")


@pytest.mark.skip(reason="Example of manually skipped test")
def test_manually_skipped():
    """
    Example of a test that is always skipped.
    """
    assert False  # Never runs


@pytest.mark.skipif(Path("tests/samples/specific_file.mp3").exists(), reason="Only runs if specific file missing")
def test_conditional_skip():
    """
    Example of conditional skip based on file existence.
    """
    print("✅ This runs only if specific_file.mp3 is missing")


# ============================================================================
# Parametrized Tests
# ============================================================================

@pytest.mark.parametrize("duration,expected_size", [
    (1.0, 15000),   # 1 second should be ~15KB at 16kHz mono
    (5.0, 75000),   # 5 seconds should be ~75KB
])
def test_audio_size_estimation(duration, expected_size):
    """
    Example of parametrized test.

    Tests run multiple times with different parameters.
    """
    # Simple estimation: 16kHz * 2 bytes/sample * 1 channel
    estimated_size = int(duration * 16000 * 2)
    assert abs(estimated_size - expected_size) < expected_size * 0.1  # Within 10%
    print(f"✅ Duration {duration}s estimated at {estimated_size} bytes")
