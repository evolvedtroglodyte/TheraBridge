"""Pipeline service - wraps existing audio transcription pipeline"""
import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

class PipelineService:
    """Wraps the existing pipeline.py to run transcriptions"""

    def __init__(self, pipeline_path: Path, results_dir: Path):
        """
        Initialize pipeline service

        Args:
            pipeline_path: Path to the existing pipeline.py (../../src/pipeline.py)
            results_dir: Directory to store results JSON files
        """
        self.pipeline_path = pipeline_path.resolve()
        self.results_dir = results_dir
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # Thread pool for CPU-intensive operations (prevents blocking event loop)
        self.executor = ThreadPoolExecutor(max_workers=3)

        # Add pipeline directory to Python path
        pipeline_dir = self.pipeline_path.parent
        if str(pipeline_dir) not in sys.path:
            sys.path.insert(0, str(pipeline_dir))

    def shutdown(self):
        """Cleanup thread pool executor"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

    async def run_transcription(
        self,
        job_id: str,
        audio_file_path: str,
        language: str = "english",
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> Dict[str, Any]:
        """
        Run transcription pipeline on an audio file

        Args:
            job_id: Unique job identifier
            audio_file_path: Path to the audio file
            language: Language code for transcription
            progress_callback: Optional callback for progress updates (stage, percent)

        Returns:
            Dict containing the complete transcription result
        """
        import time
        start_time = time.time()

        try:
            # Fix torchaudio compatibility issue with speechbrain
            # speechbrain expects list_audio_backends() which was removed in torchaudio 2.1+
            import torchaudio
            if not hasattr(torchaudio, 'list_audio_backends'):
                torchaudio.list_audio_backends = lambda: ['soundfile']
                logger.info("Applied torchaudio compatibility patch for speechbrain")

            # Fix PyTorch 2.9 weights_only security restriction
            # Pyannote models need several classes to be allowlisted
            import torch
            if hasattr(torch, 'serialization') and hasattr(torch.serialization, 'add_safe_globals'):
                try:
                    # Import all pyannote classes that need to be allowlisted
                    from pyannote.audio.core.task import Specifications, Problem, Resolution
                    from pyannote.core import SlidingWindowFeature, Segment, Timeline, Annotation

                    torch.serialization.add_safe_globals([
                        torch.torch_version.TorchVersion,
                        Specifications,
                        Problem,
                        Resolution,
                        SlidingWindowFeature,
                        Segment,
                        Timeline,
                        Annotation
                    ])
                    logger.info("Applied PyTorch 2.9 weights_only compatibility patch (8 classes)")
                except Exception as e:
                    logger.warning(f"Failed to apply PyTorch weights_only patch: {e}")

            # Import transcriber and diarizer (skip preprocessing due to Python 3.14 audioop issue)
            from pipeline import WhisperTranscriber
            from pipeline_enhanced import SpeakerDiarizer
            from performance_logger import PerformanceLogger

            # Initialize logger for diarization
            perf_logger = PerformanceLogger()

            # Step 1: Preprocessing (file validation and loading)
            if progress_callback:
                await progress_callback("preprocessing", 0.0)

            logger.info(f"[Job {job_id}] Starting preprocessing")
            # Simulate preprocessing progress
            if progress_callback:
                await progress_callback("preprocessing", 0.05)

            # Validate audio file exists
            import os
            if not os.path.exists(audio_file_path):
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

            if progress_callback:
                await progress_callback("preprocessing", 0.10)

            logger.info(f"[Job {job_id}] Preprocessing complete")

            # Step 2: Transcription
            if progress_callback:
                await progress_callback("transcription", 0.10)

            logger.info(f"[Job {job_id}] Starting transcription")
            transcription_start = time.time()
            transcriber = WhisperTranscriber()

            # Progress update during transcription initialization
            if progress_callback:
                await progress_callback("transcription", 0.15)

            # Run transcription in thread pool (API calls may block)
            loop = asyncio.get_event_loop()
            transcription = await loop.run_in_executor(
                self.executor,
                transcriber.transcribe,
                audio_file_path,
                language
            )

            # Transcription complete
            if progress_callback:
                await progress_callback("transcription", 0.40)

            transcription_time = time.time() - transcription_start
            logger.info(f"[Job {job_id}] Transcription completed in {transcription_time:.2f}s")

            # Step 3: Speaker Diarization (optional - skip if incompatible)
            diarization_time = 0
            alignment_time = 0
            diarization_turns = []

            try:
                if progress_callback:
                    await progress_callback("diarization", 0.40)

                logger.info(f"[Job {job_id}] Starting speaker diarization")
                diarization_start = time.time()

                # Ensure HF_TOKEN is set (SpeakerDiarizer expects HF_TOKEN)
                import os
                if "HF_TOKEN" not in os.environ and "HUGGINGFACE_TOKEN" in os.environ:
                    os.environ["HF_TOKEN"] = os.environ["HUGGINGFACE_TOKEN"]

                # Progress update - loading model
                if progress_callback:
                    await progress_callback("diarization", 0.50)

                diarizer = SpeakerDiarizer(num_speakers=2, logger=perf_logger)

                # Progress update - running inference
                if progress_callback:
                    await progress_callback("diarization", 0.60)

                # Run CPU-intensive diarization in thread pool to avoid blocking event loop
                loop = asyncio.get_event_loop()
                diarization_turns = await loop.run_in_executor(
                    self.executor,
                    diarizer.diarize,
                    audio_file_path
                )

                # Diarization complete
                if progress_callback:
                    await progress_callback("diarization", 0.80)

                diarization_time = time.time() - diarization_start
                logger.info(f"[Job {job_id}] Diarization completed in {diarization_time:.2f}s - {len(diarization_turns)} turns")

                # Step 4: Align speakers with transcript segments
                if progress_callback:
                    await progress_callback("alignment", 0.80)

                logger.info(f"[Job {job_id}] Aligning speakers with transcript")
                alignment_start = time.time()

                # Progress update - aligning
                if progress_callback:
                    await progress_callback("alignment", 0.85)

                aligned_segments = self._align_speakers_cpu(
                    transcription.get("segments", []),
                    diarization_turns
                )

                # Progress update - alignment complete
                if progress_callback:
                    await progress_callback("alignment", 0.90)

                alignment_time = time.time() - alignment_start
                logger.info(f"[Job {job_id}] Alignment completed in {alignment_time:.2f}s")

                # Step 5: Combine consecutive segments from same speaker
                if progress_callback:
                    await progress_callback("combining", 0.95)

                combined_segments = self._combine_consecutive_speakers(aligned_segments)

                # Update transcription with aligned and combined segments
                transcription["segments"] = combined_segments

                # Combining complete
                if progress_callback:
                    await progress_callback("combining", 0.98)

            except Exception as diarization_error:
                logger.warning(f"[Job {job_id}] Diarization failed (skipping): {str(diarization_error)}")
                logger.info(f"[Job {job_id}] Continuing without speaker diarization")
                # Keep original segments without speaker labels
                diarization_time = 0
                alignment_time = 0

            if progress_callback:
                await progress_callback("completed", 1.0)

            # Calculate total processing time
            total_time = time.time() - start_time

            # Build result structure
            result = self._build_result(
                job_id=job_id,
                audio_file_path=audio_file_path,
                transcription=transcription,
                language=language,
                processing_time=total_time,
                transcription_time=transcription_time,
                diarization_time=diarization_time,
                alignment_time=alignment_time,
                diarization_turns=diarization_turns
            )

            # Save result to file
            result_path = self.results_dir / f"{job_id}.json"
            with open(result_path, "w") as f:
                json.dump(result, f, indent=2, default=str)

            logger.info(f"[Job {job_id}] Completed successfully")
            return result

        except Exception as e:
            logger.error(f"[Job {job_id}] Pipeline error: {str(e)}", exc_info=True)
            raise

    def _build_result(
        self,
        job_id: str,
        audio_file_path: str,
        transcription: Dict,
        language: str,
        processing_time: float = 0,
        transcription_time: float = 0,
        diarization_time: float = 0,
        alignment_time: float = 0,
        diarization_turns: list = None
    ) -> Dict[str, Any]:
        """Build standardized result structure"""
        import os

        file_size_mb = os.path.getsize(audio_file_path) / (1024 * 1024)

        # Extract metadata from existing results
        metadata = {
            "source_file": audio_file_path,
            "file_size_mb": file_size_mb,
            "duration": transcription.get("duration", 0),
            "language": language,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "pipeline_type": "CPU_API"
        }

        # Extract segments from transcription
        segments = transcription.get("segments", [])

        # Calculate speaker stats from aligned segments
        speakers = self._calculate_speaker_stats(segments)

        # Performance metrics with actual timing data
        performance = {
            "total_processing_time_seconds": processing_time,
            "preprocessing_time_seconds": 0,  # Skipped due to Python 3.14
            "transcription_time_seconds": transcription_time,
            "diarization_time_seconds": diarization_time,
            "alignment_time_seconds": alignment_time
        }

        # Quality metrics - calculate speaker distribution
        speaker_distribution = {}
        unknown_count = 0
        for segment in segments:
            speaker = segment.get("speaker", "UNKNOWN")
            speaker_distribution[speaker] = speaker_distribution.get(speaker, 0) + 1
            if speaker == "UNKNOWN":
                unknown_count += 1

        unknown_percent = (unknown_count / len(segments) * 100) if len(segments) > 0 else 0

        quality = {
            "total_segments": len(segments),
            "speaker_segment_distribution": speaker_distribution,
            "unknown_segments_count": unknown_count,
            "unknown_segments_percent": unknown_percent
        }

        return {
            "id": job_id,
            "status": "completed",
            "filename": Path(audio_file_path).name,
            "metadata": metadata,
            "performance": performance,
            "speakers": speakers,
            "segments": segments,
            "quality": quality,
            "created_at": datetime.now().isoformat(),
            "completed_at": datetime.now().isoformat()
        }

    def _align_speakers_cpu(self, segments: list, turns: list) -> list:
        """
        Improved speaker alignment algorithm with lower threshold and fallback strategies.
        Reduces "Unknown" speaker labels from 8.4% to <2%.

        Based on improved_alignment.py - uses 30% threshold + nearest neighbor fallback
        """
        aligned = []
        overlap_threshold = 0.3  # 30% instead of 50%
        fallback_assignments = 0

        for seg in segments:
            seg_start, seg_end = seg["start"], seg["end"]
            seg_duration = seg_end - seg_start

            # Find speaker with maximum overlap
            best_speaker = "UNKNOWN"
            best_overlap = 0
            best_overlap_ratio = 0

            for turn in turns:
                overlap_start = max(seg_start, turn["start"])
                overlap_end = min(seg_end, turn["end"])
                overlap = max(0, overlap_end - overlap_start)

                if overlap > best_overlap:
                    best_overlap = overlap
                    best_overlap_ratio = overlap / seg_duration if seg_duration > 0 else 0
                    best_speaker = turn["speaker"]

            # Check if best overlap meets threshold
            if seg_duration > 0 and best_overlap_ratio < overlap_threshold:
                # Fallback: Find nearest speaker turn
                min_distance = float('inf')
                nearest_speaker = None

                for turn in turns:
                    # Distance to nearest edge of turn
                    dist_to_start = abs(seg_start - turn["end"])
                    dist_to_end = abs(seg_end - turn["start"])
                    distance = min(dist_to_start, dist_to_end)

                    # Check if segment is in a gap before/after turn
                    if seg_end <= turn["start"]:
                        distance = turn["start"] - seg_end
                    elif seg_start >= turn["end"]:
                        distance = seg_start - turn["end"]

                    if distance < min_distance:
                        min_distance = distance
                        nearest_speaker = turn["speaker"]

                # Use nearest speaker if within 5 seconds
                if nearest_speaker and min_distance < 5.0:
                    best_speaker = nearest_speaker
                    fallback_assignments += 1
                else:
                    best_speaker = "UNKNOWN"

            aligned.append({
                "start": seg_start,
                "end": seg_end,
                "text": seg["text"],
                "speaker": best_speaker,
                "speaker_id": best_speaker  # Frontend expects speaker_id
            })

        logger.info(f"Alignment: {fallback_assignments} segments assigned via nearest-neighbor fallback")
        return aligned

    def _combine_consecutive_speakers(self, segments: list) -> list:
        """
        Combine consecutive segments from the same speaker into single entries.
        Changes speaker only when speakers change.
        """
        if not segments:
            return []

        combined = []
        current_speaker = None
        current_start = None
        current_end = None
        current_texts = []

        for seg in segments:
            speaker = seg.get("speaker", "UNKNOWN")

            # If same speaker, accumulate text and update end time
            if speaker == current_speaker:
                current_texts.append(seg["text"])
                current_end = seg["end"]  # Update to latest end time
            else:
                # Save previous speaker's combined segment
                if current_speaker is not None:
                    combined.append({
                        "start": current_start,
                        "end": current_end,
                        "text": " ".join(current_texts),
                        "speaker": current_speaker,
                        "speaker_id": current_speaker
                    })

                # Start new speaker segment
                current_speaker = speaker
                current_start = seg["start"]
                current_end = seg["end"]
                current_texts = [seg["text"]]

        # Add final segment
        if current_speaker is not None:
            combined.append({
                "start": current_start,
                "end": current_end,
                "text": " ".join(current_texts),
                "speaker": current_speaker,
                "speaker_id": current_speaker
            })

        logger.info(f"Combined {len(segments)} segments into {len(combined)} speaker turns")
        return combined

    def _calculate_speaker_stats(self, segments: list) -> list:
        """Calculate speaker statistics from segments"""
        speaker_map = {}

        for segment in segments:
            speaker_id = segment.get("speaker", "UNKNOWN")

            if speaker_id not in speaker_map:
                speaker_map[speaker_id] = {
                    "id": speaker_id,
                    "label": speaker_id,
                    "total_duration": 0.0,
                    "segment_count": 0
                }

            duration = segment.get("end", 0) - segment.get("start", 0)
            speaker_map[speaker_id]["total_duration"] += duration
            speaker_map[speaker_id]["segment_count"] += 1

        return list(speaker_map.values())

    def _calculate_quality_metrics(self, segments: list, diarization: Dict) -> Dict[str, Any]:
        """Calculate quality metrics"""
        total_segments = len(segments)
        speaker_distribution = {}

        for segment in segments:
            speaker = segment.get("speaker", "UNKNOWN")
            speaker_distribution[speaker] = speaker_distribution.get(speaker, 0) + 1

        unknown_count = speaker_distribution.get("UNKNOWN", 0)
        unknown_percent = (unknown_count / total_segments * 100) if total_segments > 0 else 0

        return {
            "total_segments": total_segments,
            "speaker_segment_distribution": speaker_distribution,
            "unknown_segments_count": unknown_count,
            "unknown_segments_percent": unknown_percent
        }

    def get_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Load result from file"""
        result_path = self.results_dir / f"{job_id}.json"

        if not result_path.exists():
            return None

        with open(result_path, "r") as f:
            return json.load(f)

    def delete_result(self, job_id: str) -> bool:
        """Delete result file"""
        result_path = self.results_dir / f"{job_id}.json"

        if result_path.exists():
            result_path.unlink()
            return True

        return False

    def list_results(self) -> list:
        """List all available results"""
        results = []
        for result_file in self.results_dir.glob("*.json"):
            try:
                with open(result_file, "r") as f:
                    result = json.load(f)
                    results.append(result)
            except Exception as e:
                logger.error(f"Error loading result {result_file}: {e}")

        # Sort by created_at descending
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results
