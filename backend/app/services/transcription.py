"""
Audio transcription service - async wrapper for existing CPU pipeline

This module integrates the synchronous audio-transcription-pipeline with
the async FastAPI backend. The key challenge is that the pipeline is fully
synchronous (uses pydub, OpenAI SDK sync calls), but FastAPI endpoints are async.

Strategy:
- Use asyncio.to_thread() to run the synchronous pipeline in a thread pool
- This prevents blocking the event loop during long-running operations
- Each transcription runs in its own thread, allowing concurrent processing
- Thread pool is managed by asyncio's default executor
"""
import asyncio
import os
import sys
import logging
from pathlib import Path
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logger = logging.getLogger(__name__)


def get_pipeline_directory() -> Path:
    """
    Resolve the audio transcription pipeline directory with validation.

    Checks in order:
    1. AUDIO_PIPELINE_DIR environment variable (absolute path)
    2. Default monorepo location (../audio-transcription-pipeline)

    Returns:
        Path: Validated pipeline directory

    Raises:
        RuntimeError: If pipeline directory cannot be found or is invalid
    """
    # Try environment variable first (production/deployment use case)
    env_path = os.getenv("AUDIO_PIPELINE_DIR")
    if env_path:
        pipeline_dir = Path(env_path).resolve()
        if pipeline_dir.is_dir() and (pipeline_dir / "src" / "pipeline.py").exists():
            logger.info(f"Using pipeline from AUDIO_PIPELINE_DIR: {pipeline_dir}")
            return pipeline_dir
        raise RuntimeError(
            f"AUDIO_PIPELINE_DIR set to '{env_path}' but directory is invalid. "
            f"Expected 'src/pipeline.py' to exist."
        )

    # Fall back to monorepo structure (development use case)
    backend_root = Path(__file__).parent.parent.parent
    pipeline_dir = (backend_root.parent / "audio-transcription-pipeline").resolve()

    if pipeline_dir.is_dir() and (pipeline_dir / "src" / "pipeline.py").exists():
        logger.info(f"Using pipeline from monorepo: {pipeline_dir}")
        return pipeline_dir

    raise RuntimeError(
        f"Audio transcription pipeline not found. Tried:\n"
        f"  1. Environment variable AUDIO_PIPELINE_DIR (not set)\n"
        f"  2. Monorepo location: {pipeline_dir} (not found)\n"
        f"Please set AUDIO_PIPELINE_DIR or ensure monorepo structure is intact."
    )


# Initialize and validate pipeline directory
PIPELINE_DIR = get_pipeline_directory()
sys.path.insert(0, str(PIPELINE_DIR))

from src.pipeline import AudioTranscriptionPipeline


def _sync_transcribe_cpu(audio_path: str) -> Dict:
    """
    Synchronous CPU transcription function (runs in thread pool).

    This function is called by async_transcribe_cpu() via asyncio.to_thread().
    It performs the actual synchronous pipeline processing.

    Args:
        audio_path: Absolute path to audio file

    Returns:
        Dict containing:
            - segments: List[Dict] with start, end, text for each segment
            - full_text: str - Complete transcription
            - language: str - Detected language code
            - duration: float - Audio duration in seconds

    Raises:
        ValueError: If file size exceeds limits or file is invalid
        FileNotFoundError: If audio file doesn't exist
        Exception: Any pipeline processing errors

    Pipeline Steps:
        1. Audio preprocessing (silence trimming, normalization, format conversion)
        2. Whisper transcription via OpenAI API (with retry logic)

    Note:
        File existence validation is delegated to the pipeline itself
        to allow for proper mocking in tests.
    """
    logger.info(f"Starting synchronous CPU transcription for: {audio_path}")

    # Initialize pipeline and process
    # Note: File validation happens inside the pipeline's preprocess() method
    try:
        pipeline = AudioTranscriptionPipeline()
        result = pipeline.process(audio_path)
        logger.info(
            f"Transcription complete: {len(result.get('segments', []))} segments, "
            f"{result.get('duration', 0):.1f}s duration"
        )
        return result
    except FileNotFoundError as e:
        logger.error(f"Audio file not found: {audio_path}")
        raise
    except Exception as e:
        logger.error(
            f"Pipeline processing failed for {audio_path}: {type(e).__name__}: {str(e)}"
        )
        raise


async def async_transcribe_cpu(
    audio_path: str,
    executor: Optional[ThreadPoolExecutor] = None
) -> Dict:
    """
    Async wrapper for synchronous CPU transcription pipeline.

    This function wraps the synchronous AudioTranscriptionPipeline.process()
    call and runs it in a thread pool to avoid blocking the event loop.

    Why asyncio.to_thread()?
    - The pipeline uses synchronous I/O (pydub, OpenAI SDK sync client)
    - Running it directly in an async function would block the event loop
    - asyncio.to_thread() runs it in a thread pool executor
    - This allows FastAPI to handle other requests concurrently

    Args:
        audio_path: Absolute path to audio file to transcribe
        executor: Optional custom ThreadPoolExecutor. If None, uses asyncio's default.

    Returns:
        Dict containing:
            - segments: List[Dict] with start, end, text for each segment
            - full_text: str - Complete transcription
            - language: str - Detected language code
            - duration: float - Audio duration in seconds

    Raises:
        ValueError: If file size exceeds limits or file is invalid
        FileNotFoundError: If audio file doesn't exist
        Exception: Any pipeline processing errors

    Example:
        >>> result = await async_transcribe_cpu("/path/to/audio.mp3")
        >>> print(result["full_text"])
        >>> for segment in result["segments"]:
        ...     print(f"[{segment['start']:.1f}s] {segment['text']}")

    Performance:
        - Typical 1-minute audio: 5-15 seconds (depends on API latency)
        - Preprocessing: 1-3 seconds
        - Whisper API call: 3-10 seconds
        - Thread pool overhead: <100ms
    """
    logger.info(f"Starting async CPU transcription wrapper for: {audio_path}")

    try:
        # Run synchronous pipeline in thread pool
        if executor:
            # Use custom executor if provided
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(executor, _sync_transcribe_cpu, audio_path)
        else:
            # Use asyncio's default thread pool (recommended)
            result = await asyncio.to_thread(_sync_transcribe_cpu, audio_path)

        logger.info(f"Async transcription completed successfully for: {audio_path}")
        return result

    except FileNotFoundError as e:
        logger.error(f"File not found during async transcription: {audio_path}")
        raise ValueError(f"Audio file not found: {audio_path}") from e

    except ValueError as e:
        # Re-raise validation errors from pipeline
        logger.error(f"Validation error during async transcription: {str(e)}")
        raise

    except Exception as e:
        # Catch and log all other errors
        logger.error(
            f"Unexpected error during async transcription: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        raise RuntimeError(
            f"Transcription failed: {type(e).__name__}: {str(e)}"
        ) from e


async def transcribe_audio_file(audio_path: str) -> Dict:
    """
    Legacy wrapper for backward compatibility.

    This function maintains the original API while using the new async wrapper.

    Args:
        audio_path: Path to audio file

    Returns:
        Dict with segments, full_text, language, duration

    Note:
        This is a compatibility shim. New code should use async_transcribe_cpu() directly.
    """
    logger.warning(
        "Using legacy transcribe_audio_file(). Consider using async_transcribe_cpu() directly."
    )
    return await async_transcribe_cpu(audio_path)
