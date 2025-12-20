"""
Pytest configuration and fixtures for audio-transcription-pipeline tests.

This module provides:
- Sample audio file fixtures with automatic skip on missing files
- Temporary directory fixtures for test outputs
- Environment variable validation
- Reusable test utilities
"""

import pytest
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Test directory paths
TESTS_DIR = Path(__file__).parent
SAMPLES_DIR = TESTS_DIR / "samples"
OUTPUTS_DIR = TESTS_DIR / "outputs"
PROCESSED_DIR = TESTS_DIR / "processed"


# ============================================================================
# Sample Audio File Fixtures
# ============================================================================

def _get_sample_path(filename: str) -> Optional[Path]:
    """Get path to sample audio file, return None if doesn't exist"""
    path = SAMPLES_DIR / filename
    return path if path.exists() else None


@pytest.fixture
def sample_cbt_session() -> Path:
    """
    Fixture for CBT therapy session sample audio.

    Skips test if file doesn't exist.

    Returns:
        Path to "LIVE Cognitive Behavioral Therapy Session (1).mp3"
    """
    path = _get_sample_path("LIVE Cognitive Behavioral Therapy Session (1).mp3")
    if path is None:
        pytest.skip("Sample audio file not found: LIVE Cognitive Behavioral Therapy Session (1).mp3")
    return path


@pytest.fixture
def sample_person_centered() -> Path:
    """
    Fixture for Person-Centered therapy session sample audio.

    Skips test if file doesn't exist.

    Returns:
        Path to "Person-Centred Therapy Session - Full Example [VLDDUL3HBIg].mp3"
    """
    path = _get_sample_path("Person-Centred Therapy Session - Full Example [VLDDUL3HBIg].mp3")
    if path is None:
        pytest.skip("Sample audio file not found: Person-Centred Therapy Session - Full Example [VLDDUL3HBIg].mp3")
    return path


@pytest.fixture
def sample_compressed_cbt() -> Path:
    """
    Fixture for compressed CBT session sample audio.

    Skips test if file doesn't exist.

    Returns:
        Path to "compressed-cbt-session.m4a"
    """
    path = _get_sample_path("compressed-cbt-session.m4a")
    if path is None:
        pytest.skip("Sample audio file not found: compressed-cbt-session.m4a")
    return path


@pytest.fixture
def any_sample_audio() -> Path:
    """
    Fixture that returns any available sample audio file.

    Tries to find any sample audio file in order of preference.
    Skips test if no sample files are available.

    Returns:
        Path to first available sample audio file
    """
    candidates = [
        "compressed-cbt-session.m4a",  # Smallest file first
        "LIVE Cognitive Behavioral Therapy Session (1).mp3",
        "Person-Centred Therapy Session - Full Example [VLDDUL3HBIg].mp3",
    ]

    for filename in candidates:
        path = _get_sample_path(filename)
        if path is not None:
            return path

    pytest.skip("No sample audio files found in tests/samples/. See tests/README.md for setup instructions.")


# ============================================================================
# Environment Variable Fixtures
# ============================================================================

@pytest.fixture
def openai_api_key() -> str:
    """
    Fixture for OpenAI API key.

    Skips test if OPENAI_API_KEY is not set.

    Returns:
        OpenAI API key from environment
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set in .env file. Required for Whisper transcription tests.")
    return api_key


@pytest.fixture
def hf_token() -> str:
    """
    Fixture for HuggingFace token.

    Skips test if HF_TOKEN is not set.

    Returns:
        HuggingFace token from environment
    """
    token = os.getenv("HF_TOKEN")
    if not token:
        pytest.skip("HF_TOKEN not set in .env file. Required for pyannote diarization tests.")
    return token


# ============================================================================
# Directory Fixtures
# ============================================================================

@pytest.fixture
def outputs_dir(tmp_path: Path) -> Path:
    """
    Fixture for test outputs directory.

    Creates a temporary directory for test outputs.

    Returns:
        Path to temporary outputs directory
    """
    output_dir = tmp_path / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


@pytest.fixture
def processed_dir(tmp_path: Path) -> Path:
    """
    Fixture for processed audio directory.

    Creates a temporary directory for processed audio files.

    Returns:
        Path to temporary processed directory
    """
    proc_dir = tmp_path / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)
    return proc_dir


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """
    Pytest configuration hook.

    Registers custom markers for test organization.
    """
    config.addinivalue_line(
        "markers",
        "requires_sample_audio: mark test as requiring sample audio files"
    )
    config.addinivalue_line(
        "markers",
        "requires_openai: mark test as requiring OpenAI API key"
    )
    config.addinivalue_line(
        "markers",
        "requires_hf: mark test as requiring HuggingFace token"
    )
    config.addinivalue_line(
        "markers",
        "integration: mark test as integration test (requires API keys and sample files)"
    )


def pytest_collection_modifyitems(config, items):
    """
    Pytest hook to modify test collection.

    Automatically adds skip markers to tests that require missing resources.
    """
    # Check for sample files
    has_samples = any((SAMPLES_DIR / f).exists() for f in [
        "compressed-cbt-session.m4a",
        "LIVE Cognitive Behavioral Therapy Session (1).mp3",
        "Person-Centred Therapy Session - Full Example [VLDDUL3HBIg].mp3",
    ])

    # Check for API keys
    has_openai = os.getenv("OPENAI_API_KEY") is not None
    has_hf = os.getenv("HF_TOKEN") is not None

    for item in items:
        # Skip tests requiring sample audio if no samples available
        if "requires_sample_audio" in item.keywords and not has_samples:
            item.add_marker(pytest.mark.skip(reason="No sample audio files available"))

        # Skip tests requiring OpenAI API key
        if "requires_openai" in item.keywords and not has_openai:
            item.add_marker(pytest.mark.skip(reason="OPENAI_API_KEY not set"))

        # Skip tests requiring HuggingFace token
        if "requires_hf" in item.keywords and not has_hf:
            item.add_marker(pytest.mark.skip(reason="HF_TOKEN not set"))

        # Skip integration tests if any requirements missing
        if "integration" in item.keywords:
            if not has_samples:
                item.add_marker(pytest.mark.skip(reason="Integration test requires sample audio files"))
            elif not has_openai:
                item.add_marker(pytest.mark.skip(reason="Integration test requires OPENAI_API_KEY"))
            elif not has_hf:
                item.add_marker(pytest.mark.skip(reason="Integration test requires HF_TOKEN"))


# ============================================================================
# Mock Fixtures for GPU Pipeline Testing
# ============================================================================

@pytest.fixture
def mock_gpu_available(monkeypatch):
    """Mock torch.cuda.is_available to return True"""
    import torch
    monkeypatch.setattr(torch.cuda, "is_available", lambda: True)


@pytest.fixture
def mock_cudnn_error():
    """
    Fixture to create a mock cuDNN error for testing fallback behavior.

    Returns a RuntimeError with cuDNN error message.
    """
    return RuntimeError("cuDNN error: CUDNN_STATUS_NOT_SUPPORTED")


@pytest.fixture
def mock_whisper_model_with_cudnn_error(monkeypatch, mock_cudnn_error):
    """
    Mock WhisperModel to raise cuDNN error on GPU, succeed on CPU.

    This simulates the real-world scenario where cuDNN has compatibility
    issues on certain systems, requiring CPU fallback.
    """
    original_whisper_model = None

    class MockWhisperModel:
        def __init__(self, model_name, device, compute_type, **kwargs):
            # First call (GPU) raises cuDNN error, second call (CPU) succeeds
            if device == "cuda":
                raise mock_cudnn_error
            # CPU call succeeds - create minimal mock
            self.device = device
            self.model_name = model_name

        def transcribe(self, audio_path, **kwargs):
            # Return minimal mock response
            class MockInfo:
                language = "en"
                duration = 60.0

            class MockSegment:
                def __init__(self, text, start, end):
                    self.text = text
                    self.start = start
                    self.end = end

            segments = [MockSegment("Test transcription", 0.0, 60.0)]
            return segments, MockInfo()

    try:
        from faster_whisper import WhisperModel
        original_whisper_model = WhisperModel
        monkeypatch.setattr("faster_whisper.WhisperModel", MockWhisperModel)
    except ImportError:
        pass  # faster_whisper not installed, skip mocking

    yield MockWhisperModel

    # Restore original if it was saved
    if original_whisper_model is not None:
        monkeypatch.setattr("faster_whisper.WhisperModel", original_whisper_model)
