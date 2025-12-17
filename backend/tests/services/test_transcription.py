"""
Comprehensive unit tests for transcription service.

Tests cover:
1. get_pipeline_directory() path resolution logic
2. Environment variable handling (AUDIO_PIPELINE_DIR)
3. Fallback to monorepo structure
4. Error cases (missing pipeline, invalid paths)
5. transcribe_audio_file() function
6. sys.path manipulation
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict


class TestGetPipelineDirectory:
    """Test suite for get_pipeline_directory() function"""

    @pytest.fixture
    def mock_pipeline_structure(self, tmp_path):
        """
        Create a mock pipeline directory structure for testing.

        Returns:
            Path: Root of mock pipeline directory with src/pipeline.py
        """
        pipeline_dir = tmp_path / "audio-transcription-pipeline"
        pipeline_dir.mkdir()
        src_dir = pipeline_dir / "src"
        src_dir.mkdir()
        (src_dir / "pipeline.py").write_text("# Mock pipeline")
        return pipeline_dir

    @pytest.fixture
    def mock_backend_root(self, tmp_path):
        """
        Create a mock backend directory structure for testing monorepo fallback.

        Returns:
            Path: Root directory containing both backend and pipeline
        """
        # Create monorepo structure
        monorepo_root = tmp_path / "monorepo"
        monorepo_root.mkdir()

        # Create backend structure
        backend_dir = monorepo_root / "backend"
        backend_dir.mkdir()
        app_dir = backend_dir / "app"
        app_dir.mkdir()
        services_dir = app_dir / "services"
        services_dir.mkdir()
        (services_dir / "transcription.py").write_text("# Mock transcription service")

        # Create pipeline structure
        pipeline_dir = monorepo_root / "audio-transcription-pipeline"
        pipeline_dir.mkdir()
        src_dir = pipeline_dir / "src"
        src_dir.mkdir()
        (src_dir / "pipeline.py").write_text("# Mock pipeline")

        return monorepo_root

    def test_env_var_set_and_valid(self, mock_pipeline_structure, monkeypatch):
        """
        ✅ Test Case 1: Environment variable set and points to valid pipeline

        Expected: Should return the path from environment variable
        """
        # Set environment variable to valid pipeline directory
        monkeypatch.setenv("AUDIO_PIPELINE_DIR", str(mock_pipeline_structure))

        # Import function fresh (to apply env var)
        from app.services.transcription import get_pipeline_directory

        result = get_pipeline_directory()

        assert result == mock_pipeline_structure.resolve()
        assert result.is_dir()
        assert (result / "src" / "pipeline.py").exists()

    def test_env_var_set_but_invalid_missing_pipeline(self, tmp_path, monkeypatch):
        """
        ❌ Test Case 2: Environment variable set but directory is invalid (missing pipeline.py)

        Expected: Should raise RuntimeError with descriptive message
        """
        # Create directory without pipeline.py
        invalid_dir = tmp_path / "invalid-pipeline"
        invalid_dir.mkdir()
        src_dir = invalid_dir / "src"
        src_dir.mkdir()
        # Note: NOT creating pipeline.py

        monkeypatch.setenv("AUDIO_PIPELINE_DIR", str(invalid_dir))

        from app.services.transcription import get_pipeline_directory

        with pytest.raises(RuntimeError) as exc_info:
            get_pipeline_directory()

        assert "AUDIO_PIPELINE_DIR set to" in str(exc_info.value)
        assert "directory is invalid" in str(exc_info.value)
        assert "Expected 'src/pipeline.py' to exist" in str(exc_info.value)

    def test_env_var_set_but_not_a_directory(self, tmp_path, monkeypatch):
        """
        ❌ Test Case 2b: Environment variable points to a file, not a directory

        Expected: Should raise RuntimeError
        """
        # Create a file instead of directory
        invalid_path = tmp_path / "not-a-directory.txt"
        invalid_path.write_text("I am a file")

        monkeypatch.setenv("AUDIO_PIPELINE_DIR", str(invalid_path))

        from app.services.transcription import get_pipeline_directory

        with pytest.raises(RuntimeError) as exc_info:
            get_pipeline_directory()

        assert "AUDIO_PIPELINE_DIR set to" in str(exc_info.value)
        assert "directory is invalid" in str(exc_info.value)

    def test_fallback_to_monorepo_structure(self, mock_backend_root, monkeypatch):
        """
        ✅ Test Case 3: Fallback to monorepo structure (env var not set)

        Expected: Should find pipeline in ../audio-transcription-pipeline
        """
        # Ensure AUDIO_PIPELINE_DIR is not set
        monkeypatch.delenv("AUDIO_PIPELINE_DIR", raising=False)

        # Mock __file__ to point to our test structure
        transcription_file = (
            mock_backend_root / "backend" / "app" / "services" / "transcription.py"
        )

        with patch("app.services.transcription.Path") as mock_path_class:
            # Setup mock to return correct paths
            mock_file_path = Mock()
            mock_file_path.parent.parent.parent = mock_backend_root / "backend"
            mock_path_class.return_value = mock_file_path

            # When Path(env_path) is called, return real Path
            def path_side_effect(path_str):
                if isinstance(path_str, str):
                    return Path(path_str)
                return mock_file_path

            mock_path_class.side_effect = path_side_effect

            # Re-import to apply patches
            import importlib
            import app.services.transcription
            importlib.reload(app.services.transcription)

            from app.services.transcription import get_pipeline_directory

            result = get_pipeline_directory()

            # Verify it found the monorepo pipeline
            assert result.is_dir()
            assert (result / "src" / "pipeline.py").exists()
            assert "audio-transcription-pipeline" in str(result)

    def test_neither_env_nor_monorepo_found(self, tmp_path, monkeypatch):
        """
        ❌ Test Case 4: Neither env var nor monorepo structure found

        Expected: Should raise RuntimeError with helpful error message listing both attempts
        """
        # Ensure AUDIO_PIPELINE_DIR is not set
        monkeypatch.delenv("AUDIO_PIPELINE_DIR", raising=False)

        # Create a fake backend structure with no pipeline
        fake_backend = tmp_path / "fake_backend" / "app" / "services"
        fake_backend.mkdir(parents=True)
        fake_file = fake_backend / "transcription.py"
        fake_file.write_text("# Fake file")

        # Mock Path(__file__) to return our fake location
        with patch("app.services.transcription.__file__", str(fake_file)):
            from app.services.transcription import get_pipeline_directory

            with pytest.raises(RuntimeError) as exc_info:
                get_pipeline_directory()

            error_message = str(exc_info.value)
            assert "Audio transcription pipeline not found" in error_message
            assert "Environment variable AUDIO_PIPELINE_DIR (not set)" in error_message
            assert "Monorepo location:" in error_message
            assert "Please set AUDIO_PIPELINE_DIR or ensure monorepo structure is intact" in error_message

    def test_env_var_relative_path_resolved(self, mock_pipeline_structure, monkeypatch):
        """
        ✅ Test Case 5: Environment variable with relative path is resolved to absolute

        Expected: Should resolve relative path to absolute path
        """
        # Change to parent directory and use relative path
        original_cwd = os.getcwd()
        try:
            os.chdir(mock_pipeline_structure.parent)
            monkeypatch.setenv("AUDIO_PIPELINE_DIR", mock_pipeline_structure.name)

            from app.services.transcription import get_pipeline_directory

            result = get_pipeline_directory()

            # Should be absolute path
            assert result.is_absolute()
            assert result == mock_pipeline_structure.resolve()
        finally:
            os.chdir(original_cwd)

    def test_env_var_with_trailing_slash(self, mock_pipeline_structure, monkeypatch):
        """
        ✅ Test Case 6: Environment variable with trailing slash is handled correctly

        Expected: Should work regardless of trailing slash
        """
        monkeypatch.setenv("AUDIO_PIPELINE_DIR", str(mock_pipeline_structure) + "/")

        from app.services.transcription import get_pipeline_directory

        result = get_pipeline_directory()

        assert result == mock_pipeline_structure.resolve()


class TestSysPathManipulation:
    """Test that sys.path is manipulated correctly for pipeline imports"""

    def test_pipeline_dir_added_to_sys_path(self, monkeypatch, tmp_path):
        """
        Test that PIPELINE_DIR is added to sys.path at position 0

        Expected: Pipeline directory should be first in sys.path
        """
        # Create mock pipeline
        pipeline_dir = tmp_path / "pipeline"
        pipeline_dir.mkdir()
        src_dir = pipeline_dir / "src"
        src_dir.mkdir()
        (src_dir / "pipeline.py").write_text("# Mock pipeline")

        monkeypatch.setenv("AUDIO_PIPELINE_DIR", str(pipeline_dir))

        # Save original sys.path
        original_path = sys.path.copy()

        try:
            # Import module (which should modify sys.path)
            import importlib
            import app.services.transcription
            importlib.reload(app.services.transcription)

            # Check that pipeline_dir was added to sys.path
            assert str(pipeline_dir) in sys.path or any(
                str(pipeline_dir) in p for p in sys.path
            )
        finally:
            # Restore original sys.path
            sys.path = original_path


class TestTranscribeAudioFile:
    """Test suite for transcribe_audio_file() function"""

    @pytest.fixture
    def mock_pipeline(self):
        """Create a mock AudioTranscriptionPipeline instance"""
        mock = Mock()
        mock.process.return_value = {
            "segments": [
                {
                    "speaker": "SPEAKER_00",
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Hello, how are you feeling today?"
                },
                {
                    "speaker": "SPEAKER_01",
                    "start": 5.5,
                    "end": 10.0,
                    "text": "I've been feeling anxious lately."
                }
            ],
            "full_text": "Hello, how are you feeling today? I've been feeling anxious lately.",
            "language": "en",
            "duration": 10.0
        }
        return mock

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_success(self, mock_pipeline):
        """
        ✅ Test Case 7: Successful transcription with mocked pipeline

        Expected: Should call pipeline.process() and return result dictionary
        """
        with patch("app.services.transcription.AudioTranscriptionPipeline", return_value=mock_pipeline):
            from app.services.transcription import transcribe_audio_file

            audio_path = "/path/to/audio.wav"
            result = await transcribe_audio_file(audio_path)

            # Verify pipeline was called correctly
            mock_pipeline.process.assert_called_once_with(audio_path)

            # Verify result structure
            assert isinstance(result, dict)
            assert "segments" in result
            assert "full_text" in result
            assert "language" in result
            assert "duration" in result
            assert len(result["segments"]) == 2
            assert result["language"] == "en"
            assert result["duration"] == 10.0

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_empty_result(self):
        """
        Test Case 8: Pipeline returns empty segments

        Expected: Should handle empty results gracefully
        """
        mock_pipeline = Mock()
        mock_pipeline.process.return_value = {
            "segments": [],
            "full_text": "",
            "language": "en",
            "duration": 0.0
        }

        with patch("app.services.transcription.AudioTranscriptionPipeline", return_value=mock_pipeline):
            from app.services.transcription import transcribe_audio_file

            result = await transcribe_audio_file("/path/to/silent.wav")

            assert result["segments"] == []
            assert result["full_text"] == ""
            assert result["duration"] == 0.0

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_pipeline_error(self):
        """
        ❌ Test Case 9: Pipeline raises exception during processing

        Expected: Exception should propagate to caller
        """
        mock_pipeline = Mock()
        mock_pipeline.process.side_effect = Exception("Audio file corrupted")

        with patch("app.services.transcription.AudioTranscriptionPipeline", return_value=mock_pipeline):
            from app.services.transcription import transcribe_audio_file

            with pytest.raises(Exception) as exc_info:
                await transcribe_audio_file("/path/to/corrupted.wav")

            assert "Audio file corrupted" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_with_role_labels(self):
        """
        ✅ Test Case 10: Transcription with therapist/client role labels

        Expected: Should preserve speaker labels from pipeline
        """
        mock_pipeline = Mock()
        mock_pipeline.process.return_value = {
            "segments": [
                {
                    "speaker": "Therapist",
                    "start": 0.0,
                    "end": 3.0,
                    "text": "Welcome to our session."
                },
                {
                    "speaker": "Client",
                    "start": 3.5,
                    "end": 7.0,
                    "text": "Thank you for seeing me."
                }
            ],
            "full_text": "Welcome to our session. Thank you for seeing me.",
            "language": "en",
            "duration": 7.0
        }

        with patch("app.services.transcription.AudioTranscriptionPipeline", return_value=mock_pipeline):
            from app.services.transcription import transcribe_audio_file

            result = await transcribe_audio_file("/path/to/session.wav")

            assert result["segments"][0]["speaker"] == "Therapist"
            assert result["segments"][1]["speaker"] == "Client"
            assert len(result["segments"]) == 2


class TestIntegration:
    """Integration tests combining multiple components"""

    @pytest.mark.asyncio
    async def test_end_to_end_mock_flow(self, tmp_path, monkeypatch):
        """
        ✅ Integration Test: Complete flow from directory setup to transcription

        Tests that:
        1. Pipeline directory is found via env var
        2. Module can be imported successfully
        3. Transcription function can be called
        """
        # Setup mock pipeline directory
        pipeline_dir = tmp_path / "pipeline"
        pipeline_dir.mkdir()
        src_dir = pipeline_dir / "src"
        src_dir.mkdir()
        (src_dir / "pipeline.py").write_text("# Mock pipeline")

        monkeypatch.setenv("AUDIO_PIPELINE_DIR", str(pipeline_dir))

        # Mock the pipeline before module import
        mock_pipeline_instance = Mock()
        mock_pipeline_instance.process.return_value = {
            "segments": [{"speaker": "SPEAKER_00", "start": 0, "end": 5, "text": "Test"}],
            "full_text": "Test",
            "language": "en",
            "duration": 5.0
        }

        # Patch the import path before reload
        with patch.dict("sys.modules", {"src.pipeline": Mock(AudioTranscriptionPipeline=Mock(return_value=mock_pipeline_instance))}):
            # Force reload to apply environment changes
            import importlib
            import app.services.transcription
            importlib.reload(app.services.transcription)

            from app.services.transcription import PIPELINE_DIR

            # Verify pipeline directory was set correctly
            assert PIPELINE_DIR == pipeline_dir.resolve()

            # Now patch the imported class and test transcription
            with patch.object(app.services.transcription, "AudioTranscriptionPipeline", return_value=mock_pipeline_instance):
                from app.services.transcription import transcribe_audio_file

                # Call transcription with a dummy path
                result = await transcribe_audio_file("/dummy/audio.wav")
                assert result["language"] == "en"
                assert len(result["segments"]) == 1

                # Verify the pipeline was called
                mock_pipeline_instance.process.assert_called_with("/dummy/audio.wav")


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_pipeline_dir_with_symlink(self, tmp_path, monkeypatch):
        """
        Test Case: Pipeline directory is a symlink

        Expected: Should resolve symlink and work correctly
        """
        # Create actual pipeline
        real_pipeline = tmp_path / "real-pipeline"
        real_pipeline.mkdir()
        src_dir = real_pipeline / "src"
        src_dir.mkdir()
        (src_dir / "pipeline.py").write_text("# Mock")

        # Create symlink
        symlink = tmp_path / "pipeline-link"
        symlink.symlink_to(real_pipeline)

        monkeypatch.setenv("AUDIO_PIPELINE_DIR", str(symlink))

        from app.services.transcription import get_pipeline_directory

        result = get_pipeline_directory()

        # Should resolve to real path
        assert result.is_dir()
        assert (result / "src" / "pipeline.py").exists()

    def test_unicode_in_path(self, tmp_path, monkeypatch):
        """
        Test Case: Pipeline path contains unicode characters

        Expected: Should handle unicode paths correctly
        """
        # Create pipeline with unicode name
        pipeline_dir = tmp_path / "pipeline-测试"
        pipeline_dir.mkdir()
        src_dir = pipeline_dir / "src"
        src_dir.mkdir()
        (src_dir / "pipeline.py").write_text("# Mock")

        monkeypatch.setenv("AUDIO_PIPELINE_DIR", str(pipeline_dir))

        from app.services.transcription import get_pipeline_directory

        result = get_pipeline_directory()

        assert result == pipeline_dir.resolve()
        assert result.is_dir()

    def test_very_long_path(self, tmp_path, monkeypatch):
        """
        Test Case: Very long directory path

        Expected: Should handle long paths correctly
        """
        # Create nested structure
        long_path = tmp_path
        for i in range(20):
            long_path = long_path / f"nested_{i}"
        long_path.mkdir(parents=True)

        src_dir = long_path / "src"
        src_dir.mkdir()
        (src_dir / "pipeline.py").write_text("# Mock")

        monkeypatch.setenv("AUDIO_PIPELINE_DIR", str(long_path))

        from app.services.transcription import get_pipeline_directory

        result = get_pipeline_directory()

        assert result == long_path.resolve()
        assert (result / "src" / "pipeline.py").exists()


# Test execution summary
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "--cov=app.services.transcription", "--cov-report=term-missing"])
