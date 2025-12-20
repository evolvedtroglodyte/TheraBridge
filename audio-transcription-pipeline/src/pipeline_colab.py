#!/usr/bin/env python3
"""
Colab L4 GPU-Optimized Audio Transcription Pipeline
===================================================

Full GPU acceleration with faster-whisper large-v3
"""

import os
import time
import torch
from pathlib import Path
from typing import Dict, List, Optional
from gpu_audio_ops import GPUAudioProcessor
from performance_logger import PerformanceLogger


class ColabTranscriptionPipeline:
    """Colab L4 optimized pipeline with full GPU acceleration"""

    def __init__(self,
                 whisper_model: str = "large-v3",
                 device: str = "cuda",
                 compute_type: str = "float16",
                 enable_silence_trimming: bool = False):
        """
        Initialize pipeline for Colab L4 GPU

        Args:
            whisper_model: faster-whisper model size
            device: Must be "cuda" for L4
            compute_type: "float16" for optimal L4 performance
            enable_silence_trimming: Enable silence trimming (default: False for performance)
        """
        self.enable_silence_trimming = enable_silence_trimming
        # Verify CUDA availability
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA not available. This pipeline requires GPU.")

        self.device = torch.device(device)
        self.compute_type = compute_type

        # Initialize performance logger
        self.logger = PerformanceLogger(
            name="ColabL4Pipeline",
            output_dir="/content/performance_logs",
            enable_gpu_monitoring=True,
            verbose=True
        )

        # Initialize GPU audio processor
        self.audio_processor = GPUAudioProcessor(self.device)

        # Initialize faster-whisper (lazy load)
        self.whisper_model = whisper_model
        self.transcriber = None

        # Initialize pyannote diarizer (lazy load)
        self.diarizer = None

        print(f"[Pipeline] Initialized for Colab L4 GPU")
        print(f"[Pipeline] Device: {torch.cuda.get_device_name(0)}")
        print(f"[Pipeline] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    def process(self, audio_path: str,
                num_speakers: int = 2,
                language: str = "en") -> Dict:
        """
        Process audio file with full GPU acceleration

        Args:
            audio_path: Path to audio file
            num_speakers: Number of speakers for diarization
            language: Language code for transcription

        Returns:
            Dict with transcription, diarization, and aligned segments
        """
        self.logger.start_pipeline()

        try:
            print(f"\n{'='*50}")
            print(f"Colab L4 GPU Transcription Pipeline")
            print(f"{'='*50}\n")

            # Step 1: GPU Audio Preprocessing
            self.logger.start_stage("GPU Audio Preprocessing")
            preprocessed_audio = self._preprocess_gpu(audio_path)
            self.logger.end_stage("GPU Audio Preprocessing")

            # Step 2: GPU Transcription with faster-whisper
            self.logger.start_stage("GPU Transcription (faster-whisper)")
            transcription = self._transcribe_gpu(preprocessed_audio, language)
            self.logger.end_stage("GPU Transcription (faster-whisper)")

            # Step 3: GPU Speaker Diarization
            self.logger.start_stage("GPU Speaker Diarization")
            speaker_turns = self._diarize_gpu(preprocessed_audio, num_speakers)
            self.logger.end_stage("GPU Speaker Diarization")

            # Step 4: GPU Speaker Alignment
            self.logger.start_stage("GPU Speaker Alignment")
            aligned_segments = self._align_speakers_gpu(
                transcription['segments'],
                speaker_turns
            )
            self.logger.end_stage("GPU Speaker Alignment")

            # Compile results
            result = {
                'segments': transcription['segments'],
                'aligned_segments': aligned_segments,
                'full_text': transcription['text'],
                'language': transcription['language'],
                'duration': transcription['duration'],
                'speaker_turns': speaker_turns,
                'performance_metrics': self.logger.get_summary()
            }

            self.logger.end_pipeline()

            print(f"\n{'='*50}")
            print(f"Pipeline Complete!")
            print(f"Total time: {self.logger.metrics.get('total_duration', 0):.2f}s")
            print(f"GPU utilization: {self._get_gpu_utilization():.1f}%")
            print(f"{'='*50}\n")

            return result

        except Exception as e:
            self.logger.log(f"Pipeline error: {str(e)}", level="ERROR")
            self.logger.end_pipeline()
            raise

    def _preprocess_gpu(self, audio_path: str) -> str:
        """GPU-accelerated audio preprocessing"""
        with self.logger.subprocess("gpu_audio_loading"):
            # Load directly to GPU
            waveform, sample_rate = self.audio_processor.load_audio(audio_path)
            self.logger.log(f"[Preprocess] Loaded to GPU: shape={waveform.shape}, sr={sample_rate}")

        with self.logger.subprocess("gpu_silence_trimming"):
            # Trim silence on GPU (disabled by default for performance)
            waveform = self.audio_processor.trim_silence_gpu(
                waveform,
                sample_rate=sample_rate,
                enable=self.enable_silence_trimming
            )
            if self.enable_silence_trimming:
                self.logger.log(f"[Preprocess] Trimmed: shape={waveform.shape}")
            else:
                self.logger.log(f"[Preprocess] Silence trimming disabled (performance optimization)")

        with self.logger.subprocess("gpu_normalization"):
            # Normalize on GPU
            waveform = self.audio_processor.normalize_gpu(waveform)
            self.logger.log("[Preprocess] Normalized volume")

        with self.logger.subprocess("gpu_resampling"):
            # Resample to 16kHz on GPU
            if sample_rate != 16000:
                waveform = self.audio_processor.resample_gpu(waveform, sample_rate, 16000)
                sample_rate = 16000
                self.logger.log("[Preprocess] Resampled to 16kHz")

        # Save processed audio
        output_path = "/content/processed_audio.wav"
        with self.logger.subprocess("gpu_audio_saving"):
            self.audio_processor.save_audio_gpu(waveform, sample_rate, output_path, format="wav")
            self.logger.log(f"[Preprocess] Saved: {output_path}")

        return output_path

    def _transcribe_gpu(self, audio_path: str, language: str) -> Dict:
        """Transcribe using faster-whisper on GPU"""
        # Lazy load faster-whisper
        if self.transcriber is None:
            with self.logger.subprocess("whisper_model_loading"):
                from faster_whisper import WhisperModel
                self.logger.log(f"[Whisper] Loading {self.whisper_model} model...")
                start_load = time.perf_counter()

                self.transcriber = WhisperModel(
                    self.whisper_model,
                    device="cuda",
                    compute_type=self.compute_type,
                    num_workers=4,
                    download_root="/content/whisper_models"
                )

                load_time = time.perf_counter() - start_load
                self.logger.log(f"[Whisper] Model loaded in {load_time:.2f}s")

        # Transcribe
        with self.logger.subprocess("whisper_inference"):
            self.logger.log("[Whisper] Starting transcription...")
            start_transcribe = time.perf_counter()

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

            # Convert generator to list
            segment_list = []
            for segment in segments:
                segment_list.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text.strip()
                })

            transcribe_time = time.perf_counter() - start_transcribe
            self.logger.log(f"[Whisper] Transcribed {len(segment_list)} segments in {transcribe_time:.2f}s")

        return {
            'segments': segment_list,
            'text': ' '.join([s['text'] for s in segment_list]),
            'language': info.language,
            'duration': info.duration
        }

    def _diarize_gpu(self, audio_path: str, num_speakers: int) -> List[Dict]:
        """GPU-accelerated speaker diarization"""
        # Lazy load pyannote
        if self.diarizer is None:
            with self.logger.subprocess("diarization_model_loading"):
                from pyannote.audio import Pipeline

                hf_token = os.getenv("HF_TOKEN")
                if not hf_token:
                    raise ValueError("HF_TOKEN not found. Required for pyannote.")

                self.logger.log("[Diarization] Loading pyannote model...")
                start_load = time.perf_counter()

                self.diarizer = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    token=hf_token
                )
                self.diarizer.to(self.device)

                load_time = time.perf_counter() - start_load
                self.logger.log(f"[Diarization] Model loaded in {load_time:.2f}s")

        # Run diarization
        with self.logger.subprocess("diarization_inference"):
            self.logger.log("[Diarization] Running inference...")
            start_diarize = time.perf_counter()

            # Load audio with torchaudio for pyannote
            import torchaudio
            waveform, sample_rate = torchaudio.load(audio_path)
            waveform = waveform.to(self.device)

            # Run diarization
            audio_input = {"waveform": waveform, "sample_rate": sample_rate}
            diarization = self.diarizer(audio_input, num_speakers=num_speakers)

            # Parse results
            turns = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                turns.append({
                    "speaker": speaker,
                    "start": turn.start,
                    "end": turn.end
                })

            diarize_time = time.perf_counter() - start_diarize
            self.logger.log(f"[Diarization] Found {len(turns)} turns in {diarize_time:.2f}s")

        return turns

    def _align_speakers_gpu(self, segments: List[Dict], turns: List[Dict]) -> List[Dict]:
        """GPU-accelerated speaker alignment"""
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

            self.logger.log(f"[Alignment] Aligned {len(aligned)} segments")

        return aligned

    def _get_gpu_utilization(self) -> float:
        """Get current GPU utilization percentage"""
        if torch.cuda.is_available():
            return torch.cuda.utilization()
        return 0.0