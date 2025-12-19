"""
Test GPU Pipeline Integration

Tests the async GPU wrapper and fallback behavior.
"""
import os
import sys
import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add backend to path
backend_root = Path(__file__).parent.parent
sys.path.insert(0, str(backend_root))

from app.services import gpu_pipeline_wrapper


class TestGPUPipelineWrapper:
    """Test suite for GPU pipeline integration"""

    def test_get_pipeline_directory_monorepo(self):
        """Test pipeline directory resolution in monorepo structure"""
        # Clear environment variable
        if "AUDIO_PIPELINE_DIR" in os.environ:
            del os.environ["AUDIO_PIPELINE_DIR"]

        # Should resolve to monorepo location
        pipeline_dir = gpu_pipeline_wrapper._get_pipeline_directory()
        assert pipeline_dir.exists()
        assert (pipeline_dir / "src").exists()
        assert "audio-transcription-pipeline" in str(pipeline_dir)

    def test_get_pipeline_directory_env_var(self, tmp_path):
        """Test pipeline directory resolution from environment variable"""
        # Create temporary pipeline structure
        fake_pipeline = tmp_path / "fake-pipeline"
        fake_pipeline.mkdir()
        (fake_pipeline / "src").mkdir()

        # Set environment variable
        os.environ["AUDIO_PIPELINE_DIR"] = str(fake_pipeline)

        try:
            pipeline_dir = gpu_pipeline_wrapper._get_pipeline_directory()
            assert pipeline_dir == fake_pipeline.resolve()
        finally:
            # Cleanup
            del os.environ["AUDIO_PIPELINE_DIR"]

    def test_get_pipeline_directory_invalid_env(self):
        """Test error handling for invalid AUDIO_PIPELINE_DIR"""
        os.environ["AUDIO_PIPELINE_DIR"] = "/nonexistent/path"

        try:
            with pytest.raises(RuntimeError, match="directory is invalid"):
                gpu_pipeline_wrapper._get_pipeline_directory()
        finally:
            del os.environ["AUDIO_PIPELINE_DIR"]

    def test_is_gpu_available_disabled(self):
        """Test GPU availability check when GPU disabled"""
        # Mock environment
        with patch.dict(os.environ, {"USE_GPU_PIPELINE": "false"}):
            # Reload module to pick up new env var
            import importlib
            importlib.reload(gpu_pipeline_wrapper)

            assert gpu_pipeline_wrapper.is_gpu_available() is False

    @pytest.mark.asyncio
    async def test_transcribe_force_cpu(self):
        """Test forced CPU transcription"""
        # Mock CPU transcription
        mock_result = {
            "full_text": "Test transcription",
            "segments": [],
            "language": "en",
            "duration": 10.0
        }

        # Mock the transcription module import
        with patch("app.services.transcription.transcribe_audio_file", return_value=mock_result) as mock_cpu:
            result = await gpu_pipeline_wrapper.transcribe_audio_file(
                "test.mp3",
                force_cpu=True
            )

            # Should use CPU
            mock_cpu.assert_called_once_with("test.mp3")
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_transcribe_gpu_disabled(self):
        """Test transcription when GPU disabled"""
        # Mock CPU transcription
        mock_result = {
            "full_text": "Test transcription",
            "segments": [],
            "language": "en",
            "duration": 10.0
        }

        with patch.dict(os.environ, {"USE_GPU_PIPELINE": "false"}):
            with patch("app.services.transcription.transcribe_audio_file", return_value=mock_result) as mock_cpu:
                result = await gpu_pipeline_wrapper.transcribe_audio_file("test.mp3")

                # Should use CPU
                mock_cpu.assert_called_once_with("test.mp3")
                assert result == mock_result

    @pytest.mark.asyncio
    async def test_transcribe_gpu_fallback_on_error(self):
        """Test GPU fallback to CPU on error"""
        mock_cpu_result = {
            "full_text": "CPU transcription",
            "segments": [],
            "language": "en",
            "duration": 10.0
        }

        with patch.dict(os.environ, {"USE_GPU_PIPELINE": "true"}):
            with patch("app.services.gpu_pipeline_wrapper.async_transcribe_gpu", side_effect=RuntimeError("CUDA error")):
                with patch("app.services.transcription.transcribe_audio_file", return_value=mock_cpu_result) as mock_cpu:
                    result = await gpu_pipeline_wrapper.transcribe_audio_file("test.mp3")

                    # Should fall back to CPU
                    mock_cpu.assert_called_once_with("test.mp3")
                    assert result == mock_cpu_result

    @pytest.mark.asyncio
    async def test_shutdown_gpu_executor(self):
        """Test GPU executor shutdown"""
        # Create executor
        gpu_pipeline_wrapper._get_gpu_executor()
        assert gpu_pipeline_wrapper._gpu_executor is not None

        # Shutdown
        await gpu_pipeline_wrapper.shutdown_gpu_executor()
        assert gpu_pipeline_wrapper._gpu_executor is None


class TestGPUWrapperErrorHandling:
    """Test error handling in GPU wrapper"""

    def test_sync_transcribe_gpu_import_error(self):
        """Test handling of missing GPU dependencies"""
        with patch("app.services.gpu_pipeline_wrapper._setup_pipeline_path"):
            with patch.dict("sys.modules", {"pipeline_gpu": None}):
                with pytest.raises(RuntimeError, match="dependencies not installed"):
                    gpu_pipeline_wrapper._sync_transcribe_gpu("test.mp3")

    def test_sync_transcribe_gpu_cuda_error(self):
        """Test handling of CUDA errors"""
        # Mock GPU pipeline that raises RuntimeError
        mock_pipeline_class = MagicMock()
        mock_pipeline_class.return_value.__enter__.return_value.process.side_effect = RuntimeError("CUDA out of memory")

        with patch("app.services.gpu_pipeline_wrapper._setup_pipeline_path"):
            with patch.dict("sys.modules", {"pipeline_gpu": MagicMock(GPUTranscriptionPipeline=mock_pipeline_class)}):
                with pytest.raises(RuntimeError, match="GPU transcription failed"):
                    gpu_pipeline_wrapper._sync_transcribe_gpu("test.mp3")


class TestGPUWrapperIntegration:
    """Integration tests for GPU wrapper (requires GPU)"""

    @pytest.mark.skipif(
        not gpu_pipeline_wrapper.is_gpu_available(),
        reason="GPU not available"
    )
    @pytest.mark.asyncio
    async def test_gpu_transcription_real(self):
        """Test real GPU transcription (only if GPU available)"""
        # This test requires a real audio file and GPU
        # Skip if sample file doesn't exist
        sample_file = Path(__file__).parent.parent.parent / "audio-transcription-pipeline" / "tests" / "samples" / "sample_session.mp3"

        if not sample_file.exists():
            pytest.skip("Sample audio file not found")

        # Enable GPU
        with patch.dict(os.environ, {"USE_GPU_PIPELINE": "true"}):
            result = await gpu_pipeline_wrapper.transcribe_audio_file(str(sample_file))

            # Verify result structure
            assert "full_text" in result
            assert "segments" in result
            assert "language" in result
            assert "duration" in result
            assert "provider" in result  # GPU-specific field
            assert len(result["segments"]) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
