"""
GPU Pipeline Integration Wrapper
=================================

Async wrapper for GPU-accelerated audio transcription pipeline.

This module provides async integration between the FastAPI backend and the
GPU transcription pipeline, with graceful fallback to CPU when GPU is unavailable.

Environment Variables:
    USE_GPU_PIPELINE: Enable GPU transcription (default: false)
    AUDIO_PIPELINE_DIR: Path to audio-transcription-pipeline directory

GPU Requirements:
    - NVIDIA GPU with CUDA support
    - CUDA Toolkit 11.8 or higher
    - PyTorch with CUDA support
    - Minimum 8GB VRAM (16GB recommended for large models)

Fallback Strategy:
    GPU → CPU automatic fallback on:
    - CUDA not available
    - GPU out of memory (OOM)
    - GPU model loading failures
    - Any GPU-specific runtime errors
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor

# Configure logger
logger = logging.getLogger(__name__)

# GPU toggle from environment
USE_GPU = os.getenv("USE_GPU_PIPELINE", "false").lower() in ("true", "1", "yes")

# Thread pool for GPU operations (1 thread to prevent GPU contention)
_gpu_executor: Optional[ThreadPoolExecutor] = None


def _get_gpu_executor() -> ThreadPoolExecutor:
    """
    Get or create thread pool executor for GPU operations.

    Uses single thread to prevent GPU memory contention.
    """
    global _gpu_executor
    if _gpu_executor is None:
        _gpu_executor = ThreadPoolExecutor(
            max_workers=1,
            thread_name_prefix="gpu_transcription"
        )
    return _gpu_executor


def _get_pipeline_directory() -> Path:
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
        if pipeline_dir.is_dir() and (pipeline_dir / "src").exists():
            return pipeline_dir
        raise RuntimeError(
            f"AUDIO_PIPELINE_DIR set to '{env_path}' but directory is invalid. "
            f"Expected 'src/' directory to exist."
        )

    # Fall back to monorepo structure (development use case)
    backend_root = Path(__file__).parent.parent.parent
    pipeline_dir = (backend_root.parent / "audio-transcription-pipeline").resolve()

    if pipeline_dir.is_dir() and (pipeline_dir / "src").exists():
        return pipeline_dir

    raise RuntimeError(
        f"Audio transcription pipeline not found. Tried:\n"
        f"  1. Environment variable AUDIO_PIPELINE_DIR (not set)\n"
        f"  2. Monorepo location: {pipeline_dir} (not found)\n"
        f"Please set AUDIO_PIPELINE_DIR or ensure monorepo structure is intact."
    )


def _setup_pipeline_path() -> None:
    """Add pipeline directory to Python path for imports."""
    pipeline_dir = _get_pipeline_directory()
    pipeline_src = str(pipeline_dir / "src")

    if pipeline_src not in sys.path:
        sys.path.insert(0, pipeline_src)
        logger.info(f"Added pipeline directory to path: {pipeline_src}")


def _sync_transcribe_gpu(audio_path: str) -> Dict:
    """
    Synchronous GPU transcription (runs in thread pool).

    This function runs in a background thread to avoid blocking the event loop.

    Args:
        audio_path: Path to audio file

    Returns:
        Dict with transcription results:
            - full_text: Complete transcription text
            - segments: List of timestamped segments
            - aligned_segments: Speaker-labeled segments (if diarization enabled)
            - language: Detected language
            - duration: Audio duration in seconds
            - speaker_turns: List of speaker turns (if diarization enabled)
            - provider: GPU provider name (e.g., "vast_ai", "local")
            - performance_metrics: Processing performance stats

    Raises:
        RuntimeError: If GPU transcription fails
        ImportError: If GPU dependencies not installed
    """
    try:
        # Import GPU pipeline (lazy import to avoid errors when GPU not used)
        from pipeline_gpu import GPUTranscriptionPipeline

        logger.info(f"Starting GPU transcription for: {audio_path}")

        # Use context manager for automatic GPU cleanup
        with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
            result = pipeline.process(
                audio_path,
                num_speakers=2,
                language="en",
                enable_diarization=True
            )

        logger.info(
            f"GPU transcription complete. Duration: {result.get('duration', 0):.1f}s, "
            f"Segments: {len(result.get('segments', []))}, "
            f"Provider: {result.get('provider', 'unknown')}"
        )

        return result

    except ImportError as e:
        error_msg = (
            f"GPU pipeline dependencies not installed: {str(e)}. "
            f"Install GPU requirements or set USE_GPU_PIPELINE=false"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    except RuntimeError as e:
        # GPU-specific errors (CUDA not available, OOM, etc.)
        error_msg = f"GPU transcription failed: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg) from e

    except Exception as e:
        error_msg = f"Unexpected error in GPU transcription: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e


async def async_transcribe_gpu(audio_path: str) -> Dict:
    """
    Async wrapper for GPU transcription pipeline.

    Runs GPU transcription in a background thread pool to avoid blocking
    the async event loop. GPU operations are inherently synchronous and
    blocking, so we must use thread pool execution.

    Args:
        audio_path: Path to audio file

    Returns:
        Dict with transcription results (same format as _sync_transcribe_gpu)

    Raises:
        RuntimeError: If GPU transcription fails

    Example:
        >>> result = await async_transcribe_gpu("session_audio.mp3")
        >>> print(result['full_text'])
        >>> print(f"Processed in {result['performance_metrics']['total_duration']:.1f}s")
    """
    loop = asyncio.get_event_loop()
    executor = _get_gpu_executor()

    try:
        # Run GPU transcription in thread pool
        result = await loop.run_in_executor(
            executor,
            _sync_transcribe_gpu,
            audio_path
        )
        return result

    except Exception as e:
        # Re-raise with additional context
        raise RuntimeError(f"GPU transcription failed: {str(e)}") from e


async def transcribe_audio_file(
    audio_path: str,
    force_cpu: bool = False
) -> Dict:
    """
    Transcribe audio file with automatic GPU/CPU selection.

    Selection logic:
    1. If force_cpu=True → Always use CPU
    2. If USE_GPU_PIPELINE=true → Try GPU, fallback to CPU on error
    3. If USE_GPU_PIPELINE=false → Use CPU only

    Args:
        audio_path: Path to audio file
        force_cpu: Force CPU transcription (bypass GPU)

    Returns:
        Dict with transcription results

    Raises:
        RuntimeError: If both GPU and CPU transcription fail

    Example:
        >>> # Automatic selection (respects USE_GPU_PIPELINE env var)
        >>> result = await transcribe_audio_file("audio.mp3")

        >>> # Force CPU (useful for testing or fallback)
        >>> result = await transcribe_audio_file("audio.mp3", force_cpu=True)
    """
    # Import CPU pipeline (lazy import)
    from app.services.transcription import transcribe_audio_file as cpu_transcribe

    # Force CPU if requested
    if force_cpu:
        logger.info("CPU transcription forced (force_cpu=True)")
        return await cpu_transcribe(audio_path)

    # Try GPU if enabled
    if USE_GPU:
        try:
            logger.info("GPU transcription enabled (USE_GPU_PIPELINE=true)")
            _setup_pipeline_path()
            result = await async_transcribe_gpu(audio_path)

            # Log GPU performance metrics
            metrics = result.get('performance_metrics', {})
            total_time = metrics.get('total_duration', 0)
            audio_duration = result.get('duration', 0)
            speed_factor = audio_duration / total_time if total_time > 0 else 0

            logger.info(
                f"GPU transcription successful. "
                f"Speed: {speed_factor:.1f}x real-time, "
                f"Provider: {result.get('provider', 'unknown')}"
            )

            return result

        except Exception as e:
            logger.warning(
                f"GPU transcription failed, falling back to CPU: {str(e)}",
                exc_info=True
            )
            # Fall through to CPU fallback

    # CPU fallback (either USE_GPU=false or GPU failed)
    logger.info("Using CPU transcription")
    return await cpu_transcribe(audio_path)


async def shutdown_gpu_executor() -> None:
    """
    Shutdown GPU thread pool executor.

    Should be called on application shutdown to clean up resources.

    Usage:
        # In main.py shutdown event
        @app.on_event("shutdown")
        async def shutdown_event():
            await shutdown_gpu_executor()
    """
    global _gpu_executor
    if _gpu_executor is not None:
        logger.info("Shutting down GPU executor")
        _gpu_executor.shutdown(wait=True)
        _gpu_executor = None


# GPU availability check
def is_gpu_available() -> bool:
    """
    Check if GPU is available for transcription.

    Returns:
        bool: True if GPU is available and configured, False otherwise

    Example:
        >>> if is_gpu_available():
        ...     print("GPU acceleration enabled")
        ... else:
        ...     print("Using CPU transcription")
    """
    if not USE_GPU:
        return False

    try:
        _setup_pipeline_path()
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False
    except Exception as e:
        logger.warning(f"GPU availability check failed: {str(e)}")
        return False


# Log GPU configuration on module import
if USE_GPU:
    logger.info("GPU transcription enabled (USE_GPU_PIPELINE=true)")
    if is_gpu_available():
        logger.info("GPU hardware detected and available")
    else:
        logger.warning(
            "GPU transcription enabled but GPU not available. "
            "Will fall back to CPU transcription."
        )
else:
    logger.info("GPU transcription disabled (USE_GPU_PIPELINE=false)")
