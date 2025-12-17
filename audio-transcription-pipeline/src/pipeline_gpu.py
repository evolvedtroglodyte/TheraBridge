#!/usr/bin/env python3
"""
Provider-Agnostic GPU Transcription Pipeline
Works on Vast.ai, RunPod, Lambda Labs, Paperspace, Colab
"""

import os
import time
import torch
from pathlib import Path
from typing import Dict, List, Optional
from gpu_audio_ops import GPUAudioProcessor
from performance_logger import PerformanceLogger
from gpu_config import get_optimal_config, GPUConfig


class GPUTranscriptionPipeline:
    """
    GPU-accelerated audio transcription pipeline
    Auto-detects provider and optimizes settings
    """

    def __init__(self,
                 whisper_model: str = "large-v3",
                 config: Optional[GPUConfig] = None):
        """
        Initialize GPU pipeline with auto-configuration

        Args:
            whisper_model: faster-whisper model size (base, small, medium, large-v3)
            config: Optional GPU config (auto-detected if None)
        """
        # Auto-detect optimal configuration
        self.config = config or get_optimal_config()

        # Configure PyTorch for optimal GPU performance
        if self.config.enable_tf32:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
        torch.backends.cudnn.benchmark = True

        self.device = torch.device("cuda")
        self.whisper_model = whisper_model

        # Initialize performance logger
        log_dir = Path(self.config.model_cache_dir).parent / "logs"
        self.logger = PerformanceLogger(
            name=f"{self.config.provider.value}_pipeline",
            output_dir=str(log_dir),
            enable_gpu_monitoring=True,
            verbose=True
        )

        # Initialize components (lazy loading)
        self.audio_processor = GPUAudioProcessor(self.device)
        self.transcriber = None
        self.diarizer = None

        # Log configuration
        self._log_initialization()

    def __del__(self):
        """Cleanup GPU resources when pipeline is destroyed"""
        self.cleanup_models()

    def _log_initialization(self):
        """Log pipeline initialization details"""
        print(f"\n{'='*60}")
        print(f"GPU Transcription Pipeline")
        print(f"{'='*60}")
        print(f"Provider: {self.config.provider.value}")
        print(f"Device: {self.config.device_name}")
        print(f"VRAM: {self.config.vram_gb:.1f} GB")
        print(f"Compute Type: {self.config.compute_type}")
        print(f"Whisper Model: {self.whisper_model}")
        print(f"TF32: {self.config.enable_tf32}")
        print(f"Model Cache: {self.config.model_cache_dir}")
        print(f"{'='*60}\n")

    def process(self,
                audio_path: str,
                num_speakers: int = 2,
                language: str = "en",
                enable_diarization: bool = True) -> Dict:
        """
        Process audio file with GPU acceleration

        Args:
            audio_path: Path to audio file
            num_speakers: Number of speakers (for diarization)
            language: Language code for transcription
            enable_diarization: Whether to run speaker diarization

        Returns:
            Dict with transcription, diarization, and performance metrics
        """
        self.logger.start_pipeline()

        try:
            # Step 1: GPU Audio Preprocessing
            self.logger.start_stage("GPU Audio Preprocessing")
            preprocessed_audio = self._preprocess_gpu(audio_path)
            self.logger.end_stage("GPU Audio Preprocessing")

            # Step 2: GPU Transcription
            self.logger.start_stage("GPU Transcription")
            transcription = self._transcribe_gpu(preprocessed_audio, language)
            self.logger.end_stage("GPU Transcription")

            # Step 3: GPU Diarization (optional)
            speaker_turns = []
            aligned_segments = []

            if enable_diarization:
                self.logger.start_stage("GPU Speaker Diarization")
                speaker_turns = self._diarize_gpu(preprocessed_audio, num_speakers)
                self.logger.end_stage("GPU Speaker Diarization")

                # Step 4: Speaker Alignment
                self.logger.start_stage("Speaker Alignment")
                aligned_segments = self._align_speakers_gpu(
                    transcription['segments'],
                    speaker_turns
                )
                self.logger.end_stage("Speaker Alignment")

            # Compile results
            result = {
                'segments': transcription['segments'],
                'aligned_segments': aligned_segments if enable_diarization else [],
                'full_text': transcription['text'],
                'language': transcription['language'],
                'duration': transcription['duration'],
                'speaker_turns': speaker_turns,
                'provider': self.config.provider.value,
                'performance_metrics': self.logger.get_summary()
            }

            self.logger.end_pipeline()

            # Print summary
            total_time = self.logger.metrics.get('total_duration', 0)
            speed_factor = transcription['duration'] / total_time if total_time > 0 else 0

            print(f"\n{'='*60}")
            print(f"Processing Complete!")
            print(f"{'='*60}")
            print(f"Audio Duration: {transcription['duration']:.1f}s")
            print(f"Processing Time: {total_time:.1f}s")
            print(f"Speed: {speed_factor:.1f}x real-time")
            print(f"GPU Utilization: {self._get_avg_gpu_util():.1f}%")
            print(f"Segments: {len(transcription['segments'])}")
            if enable_diarization:
                print(f"Speaker Turns: {len(speaker_turns)}")
            print(f"{'='*60}\n")

            return result

        except Exception as e:
            self.logger.log(f"Pipeline error: {str(e)}", level="ERROR")
            self.logger.end_pipeline()
            raise
        finally:
            # Always cleanup GPU memory, even if processing fails
            self.cleanup_models()

    def _preprocess_gpu(self, audio_path: str) -> str:
        """GPU-accelerated audio preprocessing"""
        output_dir = Path(self.config.model_cache_dir).parent / "temp"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / "processed_audio.wav")

        with self.logger.subprocess("gpu_audio_loading"):
            waveform, sample_rate = self.audio_processor.load_audio(audio_path)
            self.logger.log(f"Loaded: shape={waveform.shape}, sr={sample_rate}")

        with self.logger.subprocess("gpu_silence_trimming"):
            waveform = self.audio_processor.trim_silence_gpu(waveform, sample_rate=sample_rate)
            self.logger.log(f"Trimmed: shape={waveform.shape}")

        with self.logger.subprocess("gpu_normalization"):
            waveform = self.audio_processor.normalize_gpu(waveform)

        with self.logger.subprocess("gpu_resampling"):
            if sample_rate != 16000:
                waveform = self.audio_processor.resample_gpu(waveform, sample_rate, 16000)
                sample_rate = 16000

        with self.logger.subprocess("gpu_audio_saving"):
            self.audio_processor.save_audio_gpu(waveform, sample_rate, output_path, format="wav")

        return output_path

    def _transcribe_gpu(self, audio_path: str, language: str) -> Dict:
        """Transcribe using faster-whisper on GPU"""
        if self.transcriber is None:
            with self.logger.subprocess("whisper_model_loading"):
                from faster_whisper import WhisperModel
                self.logger.log(f"Loading {self.whisper_model} model...")
                start_load = time.perf_counter()

                self.transcriber = WhisperModel(
                    self.whisper_model,
                    device="cuda",
                    compute_type=self.config.compute_type,
                    num_workers=self.config.num_workers,
                    download_root=self.config.model_cache_dir
                )

                load_time = time.perf_counter() - start_load
                self.logger.log(f"Model loaded in {load_time:.2f}s")

        with self.logger.subprocess("whisper_inference"):
            start_time = time.perf_counter()

            segments, info = self.transcriber.transcribe(
                audio_path,
                language=language,
                beam_size=5,
                best_of=5,
                temperature=0,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=400
                )
            )

            segment_list = []
            for segment in segments:
                segment_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })

            duration = time.perf_counter() - start_time
            self.logger.log(f"Transcribed {len(segment_list)} segments in {duration:.2f}s")

        return {
            'segments': segment_list,
            'text': ' '.join([s['text'] for s in segment_list]),
            'language': info.language,
            'duration': info.duration
        }

    def _diarize_gpu(self, audio_path: str, num_speakers: int) -> List[Dict]:
        """GPU-accelerated speaker diarization"""
        if self.diarizer is None:
            with self.logger.subprocess("diarization_model_loading"):
                from pyannote.audio import Pipeline

                hf_token = os.getenv("HF_TOKEN")
                if not hf_token:
                    raise ValueError(
                        "HF_TOKEN not found. Required for speaker diarization.\n"
                        "Get token at: https://huggingface.co/settings/tokens"
                    )

                self.logger.log("Loading pyannote model...")
                start_load = time.perf_counter()

                self.diarizer = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    token=hf_token,
                    cache_dir=self.config.model_cache_dir
                )
                self.diarizer.to(self.device)

                load_time = time.perf_counter() - start_load
                self.logger.log(f"Model loaded in {load_time:.2f}s")

        with self.logger.subprocess("diarization_inference"):
            import torchaudio

            waveform, sample_rate = torchaudio.load(audio_path)
            waveform = waveform.to(self.device)

            audio_input = {"waveform": waveform, "sample_rate": sample_rate}
            diarization = self.diarizer(audio_input, num_speakers=num_speakers)

            turns = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                turns.append({
                    "speaker": speaker,
                    "start": turn.start,
                    "end": turn.end
                })

            self.logger.log(f"Found {len(turns)} speaker turns")

        return turns

    def _align_speakers_gpu(self, segments: List[Dict], turns: List[Dict]) -> List[Dict]:
        """GPU-accelerated speaker alignment"""
        if not turns:
            return []

        with self.logger.subprocess("gpu_speaker_alignment"):
            # Convert to GPU tensors
            seg_starts = torch.tensor([s["start"] for s in segments], device=self.device)
            seg_ends = torch.tensor([s["end"] for s in segments], device=self.device)
            turn_starts = torch.tensor([t["start"] for t in turns], device=self.device)
            turn_ends = torch.tensor([t["end"] for t in turns], device=self.device)

            # Vectorized overlap computation
            overlap_starts = torch.maximum(seg_starts.unsqueeze(1), turn_starts)
            overlap_ends = torch.minimum(seg_ends.unsqueeze(1), turn_ends)
            overlaps = torch.clamp(overlap_ends - overlap_starts, min=0)

            # Find best speaker per segment
            max_overlaps, best_turn_indices = torch.max(overlaps, dim=1)
            seg_durations = seg_ends - seg_starts

            # Apply 50% threshold
            threshold_mask = (max_overlaps / seg_durations) >= 0.5

            # Convert to CPU
            best_turn_indices = best_turn_indices.cpu().numpy()
            threshold_mask = threshold_mask.cpu().numpy()

            # Build aligned segments
            aligned = []
            speaker_labels = [t["speaker"] for t in turns]

            for i, seg in enumerate(segments):
                speaker = speaker_labels[best_turn_indices[i]] if threshold_mask[i] else "UNKNOWN"
                aligned.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "text": seg["text"],
                    "speaker": speaker
                })

            self.logger.log(f"Aligned {len(aligned)} segments")

        return aligned

    def _get_avg_gpu_util(self) -> float:
        """Get average GPU utilization from metrics"""
        stages = self.logger.metrics.get('stages', {})
        total_util = 0
        count = 0

        for stage_data in stages.values():
            gpu_stats = stage_data.get('gpu_stats', {})
            if 'avg_utilization' in gpu_stats:
                total_util += gpu_stats['avg_utilization']
                count += 1

        return total_util / count if count > 0 else 0.0

    def cleanup_models(self):
        """
        Cleanup GPU VRAM by unloading models

        This method:
        - Unloads Whisper model from GPU memory
        - Unloads pyannote diarization model from GPU memory
        - Clears GPU cache
        - Logs cleanup status
        """
        cleanup_msg = []

        try:
            # Cleanup Whisper model
            if self.transcriber is not None:
                try:
                    # Delete the transcriber reference
                    del self.transcriber
                    self.transcriber = None
                    cleanup_msg.append("Whisper model unloaded")
                except Exception as e:
                    self.logger.log(f"Warning: Failed to cleanup Whisper model: {str(e)}", level="WARNING")

            # Cleanup pyannote diarization model
            if self.diarizer is not None:
                try:
                    # Delete the diarizer reference
                    del self.diarizer
                    self.diarizer = None
                    cleanup_msg.append("Diarization model unloaded")
                except Exception as e:
                    self.logger.log(f"Warning: Failed to cleanup diarization model: {str(e)}", level="WARNING")

            # Force GPU cache clear
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                cleanup_msg.append("GPU cache cleared")

                # Log remaining GPU memory
                remaining_vram = torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()
                remaining_vram_gb = remaining_vram / (1024 ** 3)
                self.logger.log(f"GPU cleanup complete. Available VRAM: {remaining_vram_gb:.2f} GB")

            if cleanup_msg:
                print(f"\n[GPU Cleanup] {', '.join(cleanup_msg)}")

        except Exception as e:
            self.logger.log(f"Error during GPU cleanup: {str(e)}", level="ERROR")


def main():
    """Example usage"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pipeline_gpu.py <audio_file> [--num-speakers N] [--no-diarization]")
        sys.exit(1)

    audio_file = sys.argv[1]
    num_speakers = 2
    enable_diarization = True

    # Parse arguments
    if "--num-speakers" in sys.argv:
        idx = sys.argv.index("--num-speakers")
        num_speakers = int(sys.argv[idx + 1])

    if "--no-diarization" in sys.argv:
        enable_diarization = False

    # Process
    pipeline = GPUTranscriptionPipeline(whisper_model="large-v3")
    result = pipeline.process(
        audio_file,
        num_speakers=num_speakers,
        enable_diarization=enable_diarization
    )

    # Save output
    import json
    output_file = "transcription_result.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"Results saved to {output_file}")


if __name__ == "__main__":
    main()
