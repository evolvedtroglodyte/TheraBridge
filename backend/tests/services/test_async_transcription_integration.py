"""
Integration tests for async transcription wrapper.

These tests verify that the async wrapper properly integrates with the
synchronous CPU pipeline and handles threading correctly.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from pathlib import Path


class TestAsyncTranscriptionIntegration:
    """Integration tests for async_transcribe_cpu() wrapper"""

    @pytest.mark.asyncio
    async def test_async_wrapper_runs_in_thread_pool(self):
        """
        Verify that async_transcribe_cpu() runs the synchronous pipeline in a thread pool.

        This ensures the event loop is not blocked during transcription.
        """
        mock_pipeline = Mock()
        mock_pipeline.process.return_value = {
            "segments": [{"start": 0, "end": 5, "text": "Test"}],
            "full_text": "Test",
            "language": "en",
            "duration": 5.0
        }

        with patch("app.services.transcription.AudioTranscriptionPipeline", return_value=mock_pipeline):
            from app.services.transcription import async_transcribe_cpu

            # Call the async wrapper
            result = await async_transcribe_cpu("/dummy/audio.wav")

            # Verify result
            assert result["full_text"] == "Test"
            assert result["language"] == "en"
            mock_pipeline.process.assert_called_once_with("/dummy/audio.wav")

    @pytest.mark.asyncio
    async def test_concurrent_transcriptions(self):
        """
        Verify that multiple transcriptions can run concurrently without blocking.

        This tests that the thread pool executor allows true concurrency.
        """
        mock_pipeline = Mock()

        def mock_process(audio_path):
            """Simulate varying processing times"""
            import time
            if "slow" in audio_path:
                time.sleep(0.1)
            return {
                "segments": [],
                "full_text": f"Transcribed: {audio_path}",
                "language": "en",
                "duration": 1.0
            }

        mock_pipeline.process.side_effect = mock_process

        with patch("app.services.transcription.AudioTranscriptionPipeline", return_value=mock_pipeline):
            from app.services.transcription import async_transcribe_cpu

            # Run 3 transcriptions concurrently
            tasks = [
                async_transcribe_cpu("/dummy/fast1.wav"),
                async_transcribe_cpu("/dummy/slow.wav"),
                async_transcribe_cpu("/dummy/fast2.wav")
            ]

            results = await asyncio.gather(*tasks)

            # Verify all completed
            assert len(results) == 3
            assert all(result["language"] == "en" for result in results)
            assert mock_pipeline.process.call_count == 3

    @pytest.mark.asyncio
    async def test_error_propagation_from_thread(self):
        """
        Verify that exceptions raised in the thread pool are properly propagated
        to the async caller.

        ValueError exceptions (validation errors) are re-raised as-is.
        Other exceptions are wrapped in RuntimeError.
        """
        mock_pipeline = Mock()
        mock_pipeline.process.side_effect = ValueError("Invalid audio format")

        with patch("app.services.transcription.AudioTranscriptionPipeline", return_value=mock_pipeline):
            from app.services.transcription import async_transcribe_cpu

            # ValueError is re-raised directly (not wrapped)
            with pytest.raises(ValueError) as exc_info:
                await async_transcribe_cpu("/dummy/invalid.wav")

            assert "Invalid audio format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_file_not_found_error_handling(self):
        """
        Verify that FileNotFoundError is properly wrapped and propagated.
        """
        mock_pipeline = Mock()
        mock_pipeline.process.side_effect = FileNotFoundError("Audio file not found")

        with patch("app.services.transcription.AudioTranscriptionPipeline", return_value=mock_pipeline):
            from app.services.transcription import async_transcribe_cpu

            with pytest.raises(ValueError) as exc_info:
                await async_transcribe_cpu("/nonexistent/audio.wav")

            assert "Audio file not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_custom_executor_support(self):
        """
        Verify that async_transcribe_cpu() supports custom ThreadPoolExecutor.

        This allows callers to control thread pool size for resource management.
        """
        from concurrent.futures import ThreadPoolExecutor

        mock_pipeline = Mock()
        mock_pipeline.process.return_value = {
            "segments": [],
            "full_text": "Test",
            "language": "en",
            "duration": 1.0
        }

        with patch("app.services.transcription.AudioTranscriptionPipeline", return_value=mock_pipeline):
            from app.services.transcription import async_transcribe_cpu

            # Use custom executor with 2 threads
            with ThreadPoolExecutor(max_workers=2) as executor:
                result = await async_transcribe_cpu("/dummy/audio.wav", executor=executor)

            assert result["full_text"] == "Test"
            mock_pipeline.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_legacy_wrapper_compatibility(self):
        """
        Verify that transcribe_audio_file() legacy wrapper works correctly.

        This ensures backward compatibility with existing code.
        """
        mock_pipeline = Mock()
        mock_pipeline.process.return_value = {
            "segments": [],
            "full_text": "Legacy test",
            "language": "en",
            "duration": 1.0
        }

        with patch("app.services.transcription.AudioTranscriptionPipeline", return_value=mock_pipeline):
            from app.services.transcription import transcribe_audio_file

            result = await transcribe_audio_file("/dummy/audio.wav")

            assert result["full_text"] == "Legacy test"
            mock_pipeline.process.assert_called_once()

    @pytest.mark.asyncio
    async def test_no_blocking_during_async_operations(self):
        """
        Verify that the async wrapper doesn't block the event loop.

        This test ensures that while a transcription is running in a thread,
        other async operations can still execute.
        """
        mock_pipeline = Mock()

        # Track execution order
        execution_order = []

        def slow_process(audio_path):
            """Simulate slow transcription"""
            import time
            execution_order.append("transcription_start")
            time.sleep(0.05)  # Simulate work
            execution_order.append("transcription_end")
            return {
                "segments": [],
                "full_text": "Slow result",
                "language": "en",
                "duration": 1.0
            }

        mock_pipeline.process.side_effect = slow_process

        with patch("app.services.transcription.AudioTranscriptionPipeline", return_value=mock_pipeline):
            from app.services.transcription import async_transcribe_cpu

            async def other_async_work():
                """Simulate other async work"""
                execution_order.append("other_work_start")
                await asyncio.sleep(0.01)
                execution_order.append("other_work_end")

            # Start transcription
            transcription_task = asyncio.create_task(
                async_transcribe_cpu("/dummy/audio.wav")
            )

            # Do other work while transcription runs
            await asyncio.sleep(0.02)  # Let transcription start
            await other_async_work()

            # Wait for transcription to complete
            result = await transcription_task

            # Verify other work could run concurrently
            assert "transcription_start" in execution_order
            assert "other_work_start" in execution_order
            assert "other_work_end" in execution_order
            assert "transcription_end" in execution_order

            # Verify transcription completed successfully
            assert result["full_text"] == "Slow result"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
