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

# PyTorch 2.6+ compatibility: Register safe globals for pyannote model loading
# Required for pyannote.audio 3.1+ to deserialize model checkpoints
import torch.serialization
from pyannote.audio.core.task import Specifications, Problem, Resolution

torch.serialization.add_safe_globals([
    torch.torch_version.TorchVersion,
    Specifications,
    Problem,
    Resolution
])


class GPUTranscriptionPipeline:
    """
    GPU-accelerated audio transcription pipeline
    Auto-detects provider and optimizes settings

    Recommended usage with context manager (guarantees cleanup):
        with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
            result = pipeline.process("audio.mp3")
    """

    def __init__(self,
                 whisper_model: str = "large-v3",
                 config: Optional[GPUConfig] = None,
                 enable_silence_trimming: bool = False):
        """
        Initialize GPU pipeline with auto-configuration

        Args:
            whisper_model: faster-whisper model size (base, small, medium, large-v3)
            config: Optional GPU config (auto-detected if None)
            enable_silence_trimming: Enable silence trimming during preprocessing (default: False)
                                    Note: Disabled by default for performance. Adds ~537s overhead
                                    on 45-min audio files. Enable only if absolutely needed.
        """
        self.enable_silence_trimming = enable_silence_trimming
        # Auto-detect optimal configuration
        self.config = config or get_optimal_config()

        # Configure PyTorch for optimal GPU performance
        if self.config.enable_tf32:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True
        torch.backends.cudnn.benchmark = True

        self.device = torch.device("cuda")
        self.whisper_model = whisper_model

        # Track CPU fallback status (set to True if cuDNN errors force CPU mode)
        self.used_cpu_fallback = False

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

    def __enter__(self):
        """Context manager entry - returns self for use in with block"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - guarantees GPU cleanup even on exception"""
        self.cleanup_models()
        return False  # Don't suppress exceptions

    def __del__(self):
        """Fallback cleanup for backward compatibility (not guaranteed to execute)"""
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

        # Log initial GPU memory state
        self._log_gpu_memory("Pipeline Initialization")

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
            self._log_gpu_memory("Before Audio Preprocessing")
            preprocessed_audio = self._preprocess_gpu(audio_path)
            self._log_gpu_memory("After Audio Preprocessing")
            self.logger.end_stage("GPU Audio Preprocessing")

            # Step 2: GPU Transcription
            self.logger.start_stage("GPU Transcription")
            self._log_gpu_memory("Before Transcription")
            transcription = self._transcribe_gpu(preprocessed_audio, language)
            self._log_gpu_memory("After Transcription (post-cleanup)")
            self.logger.end_stage("GPU Transcription")

            # Step 3: GPU Diarization (optional)
            speaker_turns = []
            aligned_segments = []

            if enable_diarization:
                self.logger.start_stage("GPU Speaker Diarization")
                self._log_gpu_memory("Before Diarization")
                speaker_turns = self._diarize_gpu(preprocessed_audio, num_speakers)
                self._log_gpu_memory("After Diarization (post-cleanup)")
                self.logger.end_stage("GPU Speaker Diarization")

                # Step 4: Speaker Alignment
                self.logger.start_stage("Speaker Alignment")
                self._log_gpu_memory("Before Speaker Alignment")
                aligned_segments = self._align_speakers_gpu(
                    transcription['segments'],
                    speaker_turns
                )
                self._log_gpu_memory("After Speaker Alignment (post-cleanup)")
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
                'used_cpu_fallback': self.used_cpu_fallback,
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
            if self.used_cpu_fallback:
                print(f"Device: CPU (fallback due to cuDNN error)")
            else:
                print(f"Device: GPU (CUDA)")
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
            waveform = self.audio_processor.trim_silence_gpu(
                waveform,
                sample_rate=sample_rate,
                enable=self.enable_silence_trimming
            )
            if self.enable_silence_trimming:
                self.logger.log(f"Trimmed: shape={waveform.shape}")
            else:
                self.logger.log(f"Silence trimming disabled (performance optimization)")

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
        """
        Transcribe using faster-whisper on GPU with automatic CPU fallback

        Automatically falls back to CPU mode if cuDNN errors occur during model loading.
        This ensures the pipeline works on any system, even if cuDNN has compatibility issues.
        """
        try:
            if self.transcriber is None:
                with self.logger.subprocess("whisper_model_loading"):
                    from faster_whisper import WhisperModel
                    self.logger.log(f"Loading {self.whisper_model} model...")
                    start_load = time.perf_counter()

                    try:
                        # Attempt GPU-accelerated model loading
                        self.transcriber = WhisperModel(
                            self.whisper_model,
                            device="cuda",
                            compute_type=self.config.compute_type,
                            num_workers=self.config.num_workers,
                            download_root=self.config.model_cache_dir
                        )
                        self.logger.log(f"Successfully loaded on GPU (device=cuda)")

                    except RuntimeError as e:
                        # Check if this is a cuDNN-related error
                        if "cuDNN" in str(e) or "cudnn" in str(e).lower():
                            # Log the cuDNN error and fallback to CPU
                            self.logger.log(
                                f"cuDNN error detected: {str(e)}",
                                level="WARNING"
                            )
                            self.logger.log(
                                "Falling back to CPU mode for transcription (slower but reliable)",
                                level="WARNING"
                            )

                            # Load model on CPU instead
                            self.transcriber = WhisperModel(
                                self.whisper_model,
                                device="cpu",
                                compute_type="int8",  # CPU-compatible compute type
                                num_workers=self.config.num_workers,
                                download_root=self.config.model_cache_dir
                            )

                            # Mark that we used CPU fallback
                            self.used_cpu_fallback = True
                            self.logger.log(
                                "Successfully loaded on CPU (device=cpu)",
                                level="WARNING"
                            )
                        else:
                            # Not a cuDNN error - re-raise the exception
                            raise

                    load_time = time.perf_counter() - start_load
                    device_info = "CPU (fallback)" if self.used_cpu_fallback else "GPU"
                    self.logger.log(f"Model loaded on {device_info} in {load_time:.2f}s")

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
        finally:
            # Free Whisper model from GPU after transcription completes
            if self.transcriber is not None:
                try:
                    self._log_gpu_memory("Before Whisper Cleanup")
                    del self.transcriber
                    self.transcriber = None
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    self._log_gpu_memory("After Whisper Cleanup")
                    self.logger.log("GPU memory freed after transcription")
                except Exception as e:
                    self.logger.log(f"Warning: Failed to free GPU memory after transcription: {str(e)}", level="WARNING")

    def _diarize_gpu(self, audio_path: str, num_speakers: int) -> List[Dict]:
        """GPU-accelerated speaker diarization"""
        waveform = None
        try:
            if self.diarizer is None:
                with self.logger.subprocess("diarization_model_loading"):
                    from pyannote.audio import Pipeline
                    from pyannote_compat import log_version_info

                    hf_token = os.getenv("HF_TOKEN")
                    if not hf_token:
                        raise ValueError(
                            "HF_TOKEN not found. Required for speaker diarization.\n"
                            "Get token at: https://huggingface.co/settings/tokens"
                        )

                    # Log pyannote version information
                    log_version_info(self.logger.log)

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
                from pyannote_compat import extract_annotation

                waveform, sample_rate = torchaudio.load(audio_path)
                waveform = waveform.to(self.device)

                audio_input = {"waveform": waveform, "sample_rate": sample_rate}
                diarization = self.diarizer(audio_input, num_speakers=num_speakers)

                # Use compatibility layer to extract Annotation object
                annotation = extract_annotation(diarization)
                self.logger.log(f"Extracted Annotation from {type(diarization).__name__}")

                turns = []
                for turn, _, speaker in annotation.itertracks(yield_label=True):
                    turns.append({
                        "speaker": speaker,
                        "start": turn.start,
                        "end": turn.end
                    })

                self.logger.log(f"Found {len(turns)} speaker turns")

            return turns
        finally:
            # Free waveform tensor from GPU memory
            if waveform is not None:
                try:
                    self._log_gpu_memory("Before Waveform Cleanup")
                    del waveform
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    self._log_gpu_memory("After Waveform Cleanup")
                    self.logger.log("GPU waveform freed after diarization")
                except Exception as e:
                    self.logger.log(f"Warning: Failed to free waveform memory: {str(e)}", level="WARNING")

            # Free diarization model from GPU after diarization completes
            if self.diarizer is not None:
                try:
                    self._log_gpu_memory("Before Diarization Model Cleanup")
                    del self.diarizer
                    self.diarizer = None
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                    self._log_gpu_memory("After Diarization Model Cleanup")
                    self.logger.log("GPU memory freed after diarization")
                except Exception as e:
                    self.logger.log(f"Warning: Failed to free GPU memory after diarization: {str(e)}", level="WARNING")

    def _align_speakers_gpu(self, segments: List[Dict], turns: List[Dict]) -> List[Dict]:
        """GPU-accelerated speaker alignment"""
        if not turns:
            return []

        # Track all GPU tensors for cleanup
        gpu_tensors = []
        try:
            with self.logger.subprocess("gpu_speaker_alignment"):
                # Convert to GPU tensors
                seg_starts = torch.tensor([s["start"] for s in segments], device=self.device)
                seg_ends = torch.tensor([s["end"] for s in segments], device=self.device)
                turn_starts = torch.tensor([t["start"] for t in turns], device=self.device)
                turn_ends = torch.tensor([t["end"] for t in turns], device=self.device)
                gpu_tensors.extend([seg_starts, seg_ends, turn_starts, turn_ends])

                # Vectorized overlap computation
                overlap_starts = torch.maximum(seg_starts.unsqueeze(1), turn_starts)
                overlap_ends = torch.minimum(seg_ends.unsqueeze(1), turn_ends)
                overlaps = torch.clamp(overlap_ends - overlap_starts, min=0)
                gpu_tensors.extend([overlap_starts, overlap_ends, overlaps])

                # Find best speaker per segment
                max_overlaps, best_turn_indices = torch.max(overlaps, dim=1)
                seg_durations = seg_ends - seg_starts
                gpu_tensors.extend([max_overlaps, best_turn_indices, seg_durations])

                # Apply 50% threshold
                threshold_mask = (max_overlaps / seg_durations) >= 0.5
                gpu_tensors.append(threshold_mask)

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
        finally:
            # Free all GPU tensors from speaker alignment
            try:
                self._log_gpu_memory("Before Alignment Tensors Cleanup")
                for tensor in gpu_tensors:
                    if tensor is not None:
                        del tensor
                gpu_tensors.clear()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                self._log_gpu_memory("After Alignment Tensors Cleanup")
                self.logger.log("GPU tensors freed after speaker alignment")
            except Exception as e:
                self.logger.log(f"Warning: Failed to free alignment tensors: {str(e)}", level="WARNING")

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

    def _log_gpu_memory(self, stage_name: str):
        """
        Log current GPU memory usage for monitoring and debugging.

        This helps track memory consumption at critical pipeline stages
        and identify potential memory leaks or OOM conditions before they occur.

        Args:
            stage_name: Name of the current stage for logging context
        """
        if not torch.cuda.is_available():
            return

        try:
            # Get memory statistics
            allocated = torch.cuda.memory_allocated(0) / (1024 ** 3)  # GB
            reserved = torch.cuda.memory_reserved(0) / (1024 ** 3)    # GB
            total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)  # GB
            free = total - allocated

            # Calculate percentages
            allocated_pct = (allocated / total) * 100
            reserved_pct = (reserved / total) * 100

            # Log memory state
            log_msg = (
                f"[GPU Memory] {stage_name}: "
                f"Allocated: {allocated:.2f}GB ({allocated_pct:.1f}%) | "
                f"Reserved: {reserved:.2f}GB ({reserved_pct:.1f}%) | "
                f"Free: {free:.2f}GB | "
                f"Total: {total:.2f}GB"
            )

            self.logger.log(log_msg, level="INFO")

            # Warning if memory usage is high
            if allocated_pct > 85:
                warning_msg = (
                    f"WARNING: GPU memory usage is critically high ({allocated_pct:.1f}%). "
                    f"Consider reducing batch size or using a smaller model."
                )
                self.logger.log(warning_msg, level="WARNING")
            elif allocated_pct > 70:
                warning_msg = (
                    f"NOTICE: GPU memory usage is elevated ({allocated_pct:.1f}%). "
                    f"Monitor for potential OOM conditions."
                )
                self.logger.log(warning_msg, level="INFO")

        except Exception as e:
            self.logger.log(f"Failed to log GPU memory: {str(e)}", level="WARNING")

    def cleanup_models(self):
        """
        Cleanup GPU VRAM by unloading models

        This method:
        - Unloads Whisper model from GPU memory
        - Unloads pyannote diarization model from GPU memory
        - Clears GPU cache
        - Logs cleanup status and memory recovery

        Best Practice:
        - Always call this method when done processing, or use context manager
        - Monitors memory before/after to verify cleanup effectiveness
        """
        cleanup_msg = []

        try:
            # Log memory state before cleanup
            self._log_gpu_memory("Before Final Cleanup")

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

            # Log memory state after cleanup
            self._log_gpu_memory("After Final Cleanup")

            if cleanup_msg:
                print(f"\n[GPU Cleanup] {', '.join(cleanup_msg)}")

        except Exception as e:
            self.logger.log(f"Error during GPU cleanup: {str(e)}", level="ERROR")


def main():
    """Example usage with context manager"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pipeline_gpu.py <audio_file> [--num-speakers N] [--no-diarization] [--enable-silence-trimming]")
        sys.exit(1)

    audio_file = sys.argv[1]
    num_speakers = 2
    enable_diarization = True
    enable_silence_trimming = False

    # Parse arguments
    if "--num-speakers" in sys.argv:
        idx = sys.argv.index("--num-speakers")
        num_speakers = int(sys.argv[idx + 1])

    if "--no-diarization" in sys.argv:
        enable_diarization = False

    if "--enable-silence-trimming" in sys.argv:
        enable_silence_trimming = True
        print("[Performance] Warning: Silence trimming enabled. This adds ~537s overhead on 45-min files.")

    # Process using context manager (guarantees cleanup)
    with GPUTranscriptionPipeline(
        whisper_model="large-v3",
        enable_silence_trimming=enable_silence_trimming
    ) as pipeline:
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
