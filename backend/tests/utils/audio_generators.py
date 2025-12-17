"""
Audio file generators for testing
Creates minimal valid audio files for upload testing
"""
import io
import wave
import struct
from pathlib import Path
from typing import BinaryIO


def generate_wav_file(
    duration_seconds: float = 1.0,
    sample_rate: int = 16000,
    channels: int = 1
) -> bytes:
    """
    Generate a minimal valid WAV file in memory.

    Creates a simple sine wave audio file that is valid for upload testing.
    The file will have a proper WAV header and audio data.

    Args:
        duration_seconds: Length of audio in seconds
        sample_rate: Sample rate in Hz (16kHz is common for speech)
        channels: Number of audio channels (1=mono, 2=stereo)

    Returns:
        bytes: Complete WAV file as bytes
    """
    import math

    num_samples = int(duration_seconds * sample_rate)

    # Generate simple sine wave at 440Hz (A4 note)
    frequency = 440.0
    audio_data = []

    for i in range(num_samples):
        # Generate sine wave sample
        sample = math.sin(2.0 * math.pi * frequency * i / sample_rate)
        # Convert to 16-bit PCM
        sample_int = int(sample * 32767)
        audio_data.append(sample_int)

    # Create WAV file in memory
    buffer = io.BytesIO()
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Pack samples as 16-bit signed integers
        packed_data = struct.pack('<' + 'h' * len(audio_data), *audio_data)
        wav_file.writeframes(packed_data)

    return buffer.getvalue()


def generate_mp3_header() -> bytes:
    """
    Generate a minimal valid MP3 file header.

    This creates the smallest possible valid MP3 file with proper headers.
    Useful for testing file type validation.

    Returns:
        bytes: Minimal MP3 file (just header + minimal frame)
    """
    # MP3 frame header for MPEG-1 Layer 3, 128kbps, 44.1kHz, mono
    # This is a valid MP3 sync frame header
    mp3_header = bytes([
        0xFF, 0xFB,  # Sync word + MPEG-1 Layer 3
        0x90, 0x00,  # Bitrate 128kbps, Sample rate 44.1kHz, no padding
    ])

    # Add minimal frame data (all zeros is valid for silence)
    frame_data = bytes([0x00] * 417)  # 417 bytes = standard frame size for 128kbps

    return mp3_header + frame_data


def generate_invalid_audio_file() -> bytes:
    """
    Generate a file that looks like audio but has invalid headers.

    Creates a file with a .mp3 extension but invalid content.
    Useful for testing file validation.

    Returns:
        bytes: Invalid audio file content
    """
    # Create a file that starts with invalid magic bytes
    return b"This is not a valid audio file\n" + b"\x00" * 1000


def create_test_audio_file(
    file_path: Path,
    file_type: str = "wav",
    duration: float = 1.0,
    invalid: bool = False
) -> Path:
    """
    Create a test audio file on disk.

    Args:
        file_path: Where to save the file
        file_type: Type of audio file ("wav" or "mp3")
        duration: Duration in seconds (for WAV files)
        invalid: If True, create an invalid file

    Returns:
        Path: Path to created file
    """
    if invalid:
        content = generate_invalid_audio_file()
    elif file_type == "wav":
        content = generate_wav_file(duration_seconds=duration)
    elif file_type == "mp3":
        content = generate_mp3_header()
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)

    return file_path


def create_large_file(file_path: Path, size_mb: int) -> Path:
    """
    Create a large file for size limit testing.

    Args:
        file_path: Where to save the file
        size_mb: Size in megabytes

    Returns:
        Path: Path to created file
    """
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write in chunks to avoid memory issues
    chunk_size = 1024 * 1024  # 1MB chunks
    with open(file_path, 'wb') as f:
        for _ in range(size_mb):
            f.write(b'\x00' * chunk_size)

    return file_path
