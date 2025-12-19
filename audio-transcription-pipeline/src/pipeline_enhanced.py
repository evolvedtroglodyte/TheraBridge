#!/usr/bin/env python3
"""
Enhanced Audio Transcription Pipeline with Performance Logging
==============================================================

This enhanced version includes comprehensive performance tracking for:
- Individual subprocess timings
- GPU utilization monitoring
- Memory usage tracking
- Detailed stage-by-stage performance metrics
"""

import os
import time
from pathlib import Path
from typing import Dict, Optional, List
from performance_logger import PerformanceLogger, get_logger

class AudioPreprocessor:
    """Audio preprocessing with detailed performance tracking"""

    def __init__(self,
                 target_format: str = "mp3",
                 target_sample_rate: int = 16000,
                 target_bitrate: str = "64k",
                 max_file_size_mb: int = 25,
                 logger: Optional[PerformanceLogger] = None):

        self.target_format = target_format
        self.target_sample_rate = target_sample_rate
        self.target_bitrate = target_bitrate
        self.max_file_size_mb = max_file_size_mb
        self.logger = logger or get_logger()

    def preprocess(self, audio_path: str, output_path: Optional[str] = None) -> str:
        """
        Preprocess audio file with performance tracking for each step

        Tracked operations:
        1. Audio file loading
        2. Silence trimming
        3. Volume normalization
        4. Format conversion
        5. File export
        """
        from pydub import AudioSegment, effects
        from pydub.silence import detect_leading_silence

        self.logger.start_stage("Audio Preprocessing")

        try:
            # Load audio file
            with self.logger.subprocess("audio_loading", {"file": audio_path}):
                self.logger.log(f"[Preprocess] Loading: {audio_path}", level="INFO")
                audio = AudioSegment.from_file(audio_path)
                original_duration = len(audio) / 1000  # seconds
                original_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

                metadata = {
                    "duration_seconds": original_duration,
                    "channels": audio.channels,
                    "sample_rate": audio.frame_rate,
                    "file_size_mb": original_size_mb,
                    "format": audio_path.rsplit('.', 1)[-1].lower()
                }
                self.logger.log(f"[Preprocess] Loaded: {original_duration:.1f}s, "
                              f"{metadata['channels']}ch, {metadata['sample_rate']}Hz", level="INFO")

            # Trim silence
            with self.logger.subprocess("silence_trimming"):
                self.logger.log("[Preprocess] Trimming silence...", level="DEBUG")
                trimmed_audio = self._trim_silence_tracked(audio)
                trimmed_duration = len(trimmed_audio) / 1000
                trim_amount = original_duration - trimmed_duration

                if trim_amount > 0:
                    self.logger.log(f"[Preprocess] Trimmed {trim_amount:.1f}s of silence", level="INFO")

            # Normalize volume
            with self.logger.subprocess("volume_normalization"):
                self.logger.log("[Preprocess] Normalizing volume...", level="DEBUG")
                normalized_audio = self._normalize_tracked(trimmed_audio)

            # Convert format
            with self.logger.subprocess("format_conversion",
                                       {"target_channels": 1, "target_rate": self.target_sample_rate}):
                self.logger.log("[Preprocess] Converting to mono 16kHz...", level="DEBUG")

                # Channel conversion
                start = time.perf_counter()
                audio_mono = normalized_audio.set_channels(1)
                channel_time = time.perf_counter() - start
                self.logger.record_timing("channel_conversion", channel_time)

                # Sample rate conversion (most expensive operation)
                start = time.perf_counter()
                audio_resampled = audio_mono.set_frame_rate(self.target_sample_rate)
                resample_time = time.perf_counter() - start
                self.logger.record_timing("sample_rate_conversion", resample_time)
                self.logger.log(f"[Preprocess] Resampling took {resample_time:.3f}s", level="DEBUG")

            # Export
            if output_path is None:
                output_path = audio_path.rsplit('.', 1)[0] + f'_processed.{self.target_format}'

            with self.logger.subprocess("audio_export", {"output_format": self.target_format}):
                self.logger.log(f"[Preprocess] Exporting to {self.target_format}...", level="DEBUG")
                export_params = {
                    "format": self.target_format,
                    "parameters": ["-ac", "1"]
                }
                if self.target_format == "mp3":
                    export_params["bitrate"] = self.target_bitrate

                audio_resampled.export(output_path, **export_params)

                # Validate size
                file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                self.logger.log(f"[Preprocess] Output: {output_path} ({file_size_mb:.2f} MB)", level="INFO")

                if file_size_mb > self.max_file_size_mb:
                    raise ValueError(f"File size {file_size_mb:.2f}MB exceeds {self.max_file_size_mb}MB limit")

        finally:
            self.logger.end_stage("Audio Preprocessing")

        return output_path

    def _trim_silence_tracked(self, audio: 'AudioSegment',
                             silence_threshold: int = -40,
                             min_silence_len: int = 500) -> 'AudioSegment':
        """Trim silence with detailed subprocess tracking"""
        from pydub.silence import detect_leading_silence

        # Track leading silence detection
        with self.logger.timer("detect_leading_silence"):
            start_trim = detect_leading_silence(audio, silence_threshold=silence_threshold)

        # Track audio reversal for trailing silence
        with self.logger.timer("audio_reverse"):
            reversed_audio = audio.reverse()

        # Track trailing silence detection
        with self.logger.timer("detect_trailing_silence"):
            end_trim = detect_leading_silence(reversed_audio, silence_threshold=silence_threshold)

        # Track trimming operation
        with self.logger.timer("apply_trim"):
            duration = len(audio)
            trimmed = audio[start_trim:duration - end_trim]

        trimmed_amount = (start_trim + end_trim) / 1000
        self.logger.record_timing("total_silence_trimmed", trimmed_amount)

        return trimmed

    def _normalize_tracked(self, audio: 'AudioSegment', target_dBFS: float = -20.0) -> 'AudioSegment':
        """Normalize audio with performance tracking"""
        from pydub import effects

        original_dbfs = audio.dBFS

        # Track peak detection and normalization
        with self.logger.timer("peak_normalization"):
            normalized = effects.normalize(audio, headroom=0.1)

        change = normalized.dBFS - original_dbfs
        if abs(change) > 0.5:
            self.logger.log(f"[Preprocess] Normalized volume: {change:+.1f} dB", level="INFO")

        return normalized

    def validate_audio(self, audio_path: str) -> Dict:
        """Validate audio file with timing"""
        from pydub import AudioSegment

        with self.logger.subprocess("audio_validation", {"file": audio_path}):
            try:
                audio = AudioSegment.from_file(audio_path)
                file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)

                return {
                    "valid": True,
                    "duration_seconds": len(audio) / 1000,
                    "channels": audio.channels,
                    "sample_rate": audio.frame_rate,
                    "file_size_mb": file_size_mb,
                    "format": audio_path.rsplit('.', 1)[-1].lower()
                }
            except Exception as e:
                return {
                    "valid": False,
                    "error": str(e)
                }


class WhisperTranscriber:
    """Whisper transcription with API call timing"""

    def __init__(self, api_key: Optional[str] = None, logger: Optional[PerformanceLogger] = None):
        from openai import OpenAI
        from dotenv import load_dotenv

        load_dotenv()

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.client = OpenAI(api_key=self.api_key)
        self.logger = logger or get_logger()

    def transcribe(self,
                   audio_path: str,
                   language: Optional[str] = "en",
                   response_format: str = "verbose_json") -> Dict:
        """
        Transcribe audio with detailed timing metrics

        Tracked operations:
        - File preparation
        - API upload time
        - API processing time
        - Response parsing
        """
        self.logger.start_stage("Whisper Transcription")

        try:
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            self.logger.log(f"[Whisper] Transcribing: {audio_path} ({file_size_mb:.2f} MB)", level="INFO")

            # Track file reading
            with self.logger.subprocess("whisper_file_preparation"):
                audio_file = open(audio_path, "rb")

            # Track API call
            with self.logger.subprocess("whisper_api_call",
                                       {"file_size_mb": file_size_mb, "language": language}):
                self.logger.log("[Whisper] Sending to OpenAI API...", level="DEBUG")

                start_api = time.perf_counter()

                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format=response_format,
                    timestamp_granularities=["segment"] if response_format == "verbose_json" else None
                )

                api_time = time.perf_counter() - start_api
                self.logger.log(f"[Whisper] API responded in {api_time:.2f}s", level="INFO")

            # Close file
            audio_file.close()

            # Parse response with timing
            with self.logger.subprocess("whisper_response_parsing"):
                if response_format == "verbose_json":
                    result = {
                        "segments": [
                            {
                                "start": seg.start,
                                "end": seg.end,
                                "text": seg.text.strip()
                            }
                            for seg in response.segments
                        ],
                        "full_text": response.text,
                        "language": response.language,
                        "duration": response.duration
                    }
                elif response_format == "json":
                    result = {
                        "segments": [],
                        "full_text": response.text,
                        "language": language,
                        "duration": None
                    }
                else:
                    result = {
                        "segments": [],
                        "full_text": response,
                        "language": language,
                        "duration": None
                    }

            self.logger.log(f"[Whisper] Transcribed {len(result['segments'])} segments", level="INFO")
            self.logger.record_timing("segments_count", len(result['segments']))

        finally:
            self.logger.end_stage("Whisper Transcription")

        return result


class SpeakerDiarizer:
    """Speaker diarization with GPU tracking"""

    def __init__(self, num_speakers: int = 2, logger: Optional[PerformanceLogger] = None):
        import torch
        from pyannote.audio import Pipeline

        self.num_speakers = num_speakers
        self.logger = logger or get_logger()

        # Device detection with logging
        with self.logger.subprocess("diarization_device_detection"):
            if torch.cuda.is_available():
                self.device = torch.device("cuda")
                device_name = torch.cuda.get_device_name(0)
                self.logger.log(f"[Diarization] Using CUDA device: {device_name}", level="INFO")
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = torch.device("mps")
                self.logger.log("[Diarization] Using Apple Silicon MPS acceleration", level="INFO")
            else:
                self.device = torch.device("cpu")
                self.logger.log("[Diarization] Using CPU (no GPU available)", level="WARNING")

        # Load model with timing
        self.logger.log("[Diarization] Loading pyannote model...", level="INFO")

        with self.logger.subprocess("diarization_model_loading"):
            hf_token = os.getenv("HF_TOKEN")
            if not hf_token:
                raise ValueError("HF_TOKEN not found in environment")

            start_load = time.perf_counter()

            self.pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=hf_token
            )
            self.pipeline.to(self.device)

            load_time = time.perf_counter() - start_load
            self.logger.log(f"[Diarization] Model loaded in {load_time:.2f}s", level="INFO")

    def diarize(self, audio_path: str) -> List[Dict]:
        """Run diarization with performance tracking"""
        import torch
        import torchaudio

        self.logger.start_stage("Speaker Diarization")

        try:
            # Load audio with timing
            with self.logger.subprocess("torchaudio_loading"):
                self.logger.log("[Diarization] Loading audio with torchaudio...", level="DEBUG")
                waveform, sample_rate = torchaudio.load(audio_path)

                # Move to GPU if available
                if self.device.type != "cpu":
                    with self.logger.timer("waveform_to_device"):
                        waveform = waveform.to(self.device)
                        self.logger.log(f"[Diarization] Waveform moved to {self.device}", level="DEBUG")

                # Convert to mono if needed
                if waveform.shape[0] > 1:
                    with self.logger.timer("mono_conversion"):
                        waveform = waveform.mean(dim=0, keepdim=True)
                        self.logger.log("[Diarization] Converted to mono", level="DEBUG")

            # Run diarization model
            with self.logger.subprocess("diarization_inference",
                                       {"device": str(self.device), "num_speakers": self.num_speakers}):
                self.logger.log("[Diarization] Running inference...", level="INFO")

                start_inference = time.perf_counter()

                # Create input dict
                audio_input = {"waveform": waveform, "sample_rate": sample_rate}
                diarization = self.pipeline(audio_input, num_speakers=self.num_speakers)

                inference_time = time.perf_counter() - start_inference
                self.logger.log(f"[Diarization] Inference completed in {inference_time:.2f}s", level="INFO")

            # Parse results with timing
            with self.logger.subprocess("diarization_parsing"):
                # Handle both pyannote 3.x and 4.x
                if hasattr(diarization, 'exclusive_speaker_diarization'):
                    annotation = diarization.exclusive_speaker_diarization
                elif hasattr(diarization, 'speaker_diarization'):
                    annotation = diarization.speaker_diarization
                else:
                    annotation = diarization

                # Convert to list
                turns = []
                for turn, _, speaker in annotation.itertracks(yield_label=True):
                    turns.append({
                        "speaker": speaker,
                        "start": turn.start,
                        "end": turn.end
                    })

                self.logger.log(f"[Diarization] Found {len(turns)} speaker turns", level="INFO")
                self.logger.record_timing("speaker_turns_count", len(turns))

                # Count per speaker
                speaker_counts = {}
                for t in turns:
                    speaker_counts[t["speaker"]] = speaker_counts.get(t["speaker"], 0) + 1
                self.logger.log(f"[Diarization] Speaker distribution: {speaker_counts}", level="DEBUG")

        finally:
            self.logger.end_stage("Speaker Diarization")

        return turns


class EnhancedAudioTranscriptionPipeline:
    """Main pipeline with comprehensive performance tracking"""

    def __init__(self, enable_performance_logging: bool = True, output_dir: str = None):
        # Initialize performance logger
        if enable_performance_logging:
            self.logger = PerformanceLogger(
                name="AudioTranscriptionPipeline",
                output_dir=output_dir,
                enable_gpu_monitoring=True,
                verbose=True
            )
        else:
            self.logger = get_logger()

        # Initialize components with shared logger
        self.preprocessor = AudioPreprocessor(logger=self.logger)
        self.transcriber = WhisperTranscriber(logger=self.logger)
        self.diarizer = None  # Lazy load when needed

    def process(self, audio_path: str, enable_diarization: bool = False) -> Dict:
        """
        Run complete pipeline with performance tracking

        Args:
            audio_path: Path to audio file
            enable_diarization: Whether to run speaker diarization

        Returns:
            Dict with transcription data and performance metrics
        """
        self.logger.start_pipeline()

        try:
            print(f"\n{'='*50}")
            print(f"Enhanced Audio Transcription Pipeline")
            print(f"Performance logging enabled")
            print(f"{'='*50}\n")

            # Validate input
            validation = self.preprocessor.validate_audio(audio_path)
            if not validation["valid"]:
                raise ValueError(f"Invalid audio file: {validation.get('error')}")

            self.logger.log(f"Processing: {audio_path}", level="INFO")
            self.logger.log(f"Duration: {validation['duration_seconds']:.1f}s, "
                          f"Size: {validation['file_size_mb']:.1f}MB", level="INFO")

            # Step 1: Preprocess audio
            print("\nStep 1: Preprocessing audio...")
            processed_audio = self.preprocessor.preprocess(audio_path)

            # Step 2: Transcribe with Whisper
            print("\nStep 2: Transcribing with Whisper...")
            transcription = self.transcriber.transcribe(processed_audio)

            # Step 3: Speaker diarization (optional)
            speaker_turns = []
            if enable_diarization:
                print("\nStep 3: Running speaker diarization...")
                if self.diarizer is None:
                    self.diarizer = SpeakerDiarizer(logger=self.logger)
                speaker_turns = self.diarizer.diarize(processed_audio)

                # Align speakers with segments
                with self.logger.subprocess("speaker_alignment"):
                    self.logger.log("[Alignment] Matching speakers to text segments...", level="INFO")
                    aligned_segments = self._align_speakers_with_segments(
                        transcription['segments'], speaker_turns
                    )
                    transcription['aligned_segments'] = aligned_segments

            # Finalize
            self.logger.end_pipeline()

            # Add performance metrics to result
            transcription['performance_metrics'] = {
                "total_duration": self.logger.metrics.get("total_duration"),
                "stages": self.logger.metrics.get("stages", {}),
                "session_id": self.logger.session_id
            }

            print(f"\n{'='*50}")
            print(f"Pipeline Complete!")
            print(f"Total time: {self.logger.metrics.get('total_duration', 0):.2f}s")
            print(f"Performance report: outputs/performance_logs/")
            print(f"{'='*50}\n")

            return transcription

        except Exception as e:
            self.logger.log(f"Pipeline error: {str(e)}", level="ERROR")
            self.logger.end_pipeline()
            raise

    def _align_speakers_with_segments(self, segments: List[Dict], turns: List[Dict]) -> List[Dict]:
        """Align speakers with segments using vectorized operations if possible"""
        import torch

        # Check if we can use GPU acceleration
        use_gpu = torch.cuda.is_available() or (
            hasattr(torch.backends, 'mps') and torch.backends.mps.is_available()
        )

        if use_gpu and len(segments) > 50 and len(turns) > 50:
            # Use vectorized GPU operations for large datasets
            with self.logger.timer("gpu_alignment"):
                return self._align_speakers_gpu(segments, turns)
        else:
            # Use CPU for small datasets
            with self.logger.timer("cpu_alignment"):
                return self._align_speakers_cpu(segments, turns)

    def _align_speakers_cpu(self, segments: List[Dict], turns: List[Dict]) -> List[Dict]:
        """CPU-based speaker alignment"""
        aligned = []

        for seg in segments:
            seg_start, seg_end = seg["start"], seg["end"]
            seg_duration = seg_end - seg_start

            best_speaker = "UNKNOWN"
            max_overlap = 0

            for turn in turns:
                overlap_start = max(seg_start, turn["start"])
                overlap_end = min(seg_end, turn["end"])
                overlap = max(0, overlap_end - overlap_start)

                if overlap > max_overlap:
                    max_overlap = overlap
                    best_speaker = turn["speaker"]

            # 50% overlap threshold
            if seg_duration > 0 and (max_overlap / seg_duration) < 0.5:
                best_speaker = "UNKNOWN"

            aligned.append({
                "start": seg_start,
                "end": seg_end,
                "text": seg["text"],
                "speaker": best_speaker
            })

        return aligned

    def _align_speakers_gpu(self, segments: List[Dict], turns: List[Dict]) -> List[Dict]:
        """GPU-accelerated speaker alignment using vectorized operations"""
        import torch

        device = torch.device("cuda" if torch.cuda.is_available() else "mps")

        # Convert to tensors
        seg_starts = torch.tensor([s["start"] for s in segments], device=device)
        seg_ends = torch.tensor([s["end"] for s in segments], device=device)
        turn_starts = torch.tensor([t["start"] for t in turns], device=device)
        turn_ends = torch.tensor([t["end"] for t in turns], device=device)

        # Compute overlaps using broadcasting
        # Shape: [num_segments, num_turns]
        overlap_starts = torch.maximum(seg_starts.unsqueeze(1), turn_starts)
        overlap_ends = torch.minimum(seg_ends.unsqueeze(1), turn_ends)
        overlaps = torch.clamp(overlap_ends - overlap_starts, min=0)

        # Find best speaker per segment
        max_overlaps, best_turn_indices = torch.max(overlaps, dim=1)

        # Calculate segment durations
        seg_durations = seg_ends - seg_starts

        # Apply 50% threshold
        threshold_mask = (max_overlaps / seg_durations) >= 0.5

        # Convert back to CPU for output
        best_turn_indices = best_turn_indices.cpu().numpy()
        threshold_mask = threshold_mask.cpu().numpy()

        # Build aligned segments
        aligned = []
        speaker_labels = [t["speaker"] for t in turns]

        for i, seg in enumerate(segments):
            if threshold_mask[i]:
                speaker = speaker_labels[best_turn_indices[i]]
            else:
                speaker = "UNKNOWN"

            aligned.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": seg["text"],
                "speaker": speaker
            })

        return aligned


def main():
    """Example usage with performance tracking"""
    import json

    # Initialize enhanced pipeline
    pipeline = EnhancedAudioTranscriptionPipeline(
        enable_performance_logging=True,
        output_dir="outputs/performance_logs"
    )

    # Example: Process an audio file
    audio_file = "test-audio.mp3"

    if os.path.exists(audio_file):
        # Run with diarization if available
        try:
            result = pipeline.process(audio_file, enable_diarization=True)
        except ValueError as e:
            if "HF_TOKEN" in str(e):
                print("Running without diarization (HF_TOKEN not set)")
                result = pipeline.process(audio_file, enable_diarization=False)
            else:
                raise

        print("\nTranscription Result:")
        print("-" * 40)
        print(f"Language: {result['language']}")
        print(f"Duration: {result.get('duration', 'N/A')}s")
        print(f"\nFull Text (preview):\n{result['full_text'][:500]}...")
        print("-" * 40)

        # Save results with performance metrics
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)

        with open(output_dir / "enhanced_transcription.json", "w") as f:
            json.dump(result, f, indent=2, default=str)

        print(f"\nResults saved to {output_dir}/")
        print(f"Performance logs in outputs/performance_logs/")

    else:
        print(f"Audio file not found: {audio_file}")
        print("Please provide an audio file to process.")


if __name__ == "__main__":
    main()