#!/usr/bin/env python3
"""
Pyannote Version Compatibility Layer
====================================

Handles version-specific differences between pyannote.audio 3.x and 4.x.

Key differences:
- pyannote 3.x: Pipeline returns Annotation object directly
- pyannote 4.x: Pipeline returns DiarizeOutput dataclass with attributes:
  - speaker_diarization: full diarization with overlapping speech
  - exclusive_speaker_diarization: cleaner version without overlaps (preferred)

Supported versions: pyannote.audio 3.1.0 - 4.x
"""

from typing import Any
import importlib.metadata


def get_pyannote_version() -> tuple:
    """
    Get installed pyannote.audio version

    Returns:
        Tuple of (major, minor, patch) version numbers

    Example:
        >>> get_pyannote_version()
        (3, 1, 0)
    """
    try:
        version_string = importlib.metadata.version("pyannote.audio")
        # Parse version like "3.1.0" or "4.0.0"
        parts = version_string.split(".")
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2].split("-")[0]) if len(parts) > 2 else 0  # Handle "4.0.0-dev"
        return (major, minor, patch)
    except Exception as e:
        raise ImportError(f"Failed to detect pyannote.audio version: {e}")


def extract_annotation(diarization_result: Any) -> Any:
    """
    Extract Annotation object from pyannote pipeline output

    Handles both pyannote 3.x and 4.x return types transparently.

    Args:
        diarization_result: Output from pyannote.audio.Pipeline

    Returns:
        Annotation object with speaker turns

    Raises:
        AttributeError: If the result doesn't match any known pyannote version format
    """
    version = get_pyannote_version()
    major_version = version[0]

    if major_version >= 4:
        # pyannote 4.x: Returns DiarizeOutput dataclass
        # Prefer exclusive_speaker_diarization (no overlapping speech) for cleaner alignment
        if hasattr(diarization_result, 'exclusive_speaker_diarization'):
            return diarization_result.exclusive_speaker_diarization
        elif hasattr(diarization_result, 'speaker_diarization'):
            return diarization_result.speaker_diarization
        else:
            raise AttributeError(
                f"Unexpected pyannote 4.x output format. "
                f"Expected DiarizeOutput with 'speaker_diarization' or 'exclusive_speaker_diarization', "
                f"got {type(diarization_result)} with attributes: {dir(diarization_result)}"
            )

    elif major_version == 3:
        # pyannote 3.x: Returns Annotation directly
        # Check if it's already an Annotation object (has itertracks method)
        if hasattr(diarization_result, 'itertracks'):
            return diarization_result
        else:
            raise AttributeError(
                f"Unexpected pyannote 3.x output format. "
                f"Expected Annotation object with 'itertracks' method, "
                f"got {type(diarization_result)}"
            )

    else:
        raise NotImplementedError(
            f"Unsupported pyannote.audio version {version}. "
            f"Supported versions: 3.1.0 - 4.x"
        )


def get_supported_versions() -> str:
    """
    Return human-readable string of supported pyannote versions

    Returns:
        String describing supported version range
    """
    return "pyannote.audio 3.1.0 - 4.x"


def log_version_info(logger_func=print):
    """
    Log pyannote version information

    Args:
        logger_func: Function to call for logging (default: print)
    """
    try:
        version = get_pyannote_version()
        version_string = ".".join(map(str, version))
        logger_func(f"[Pyannote] Detected pyannote.audio version: {version_string}")
        logger_func(f"[Pyannote] Supported versions: {get_supported_versions()}")
    except Exception as e:
        logger_func(f"[Pyannote] Warning: Could not detect version: {e}")
