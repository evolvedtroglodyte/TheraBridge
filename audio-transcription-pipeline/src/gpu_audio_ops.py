#!/usr/bin/env python3
"""
GPU-Accelerated Audio Operations for Colab L4
==============================================

Replaces CPU-based pydub operations with GPU-accelerated PyTorch equivalents.
"""

import os
import torch
import torchaudio
from typing import Tuple, Optional
import julius


class GPUAudioProcessor:
    """
    GPU-accelerated audio processing operations

    Recommended usage with context manager (guarantees cleanup):
        with GPUAudioProcessor() as processor:
            waveform, sr = processor.load_audio("audio.mp3")
    """

    def __init__(self, device: Optional[torch.device] = None):
        """Initialize with CUDA device (L4 GPU)"""
        if device is None:
            if not torch.cuda.is_available():
                raise RuntimeError("CUDA not available. This module requires GPU.")
            self.device = torch.device("cuda")
        else:
            self.device = device

        print(f"[GPUAudio] Using device: {self.device}")
        if self.device.type == "cuda":
            print(f"[GPUAudio] GPU: {torch.cuda.get_device_name(0)}")
            print(f"[GPUAudio] VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    def __enter__(self) -> "GPUAudioProcessor":
        """Context manager entry - returns self for use in with block"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit - guarantees GPU cleanup even on exception"""
        self.cleanup_gpu_memory()
        return False  # Don't suppress exceptions

    def __del__(self) -> None:
        """Fallback cleanup for backward compatibility (not guaranteed to execute)"""
        self.cleanup_gpu_memory()

    def cleanup_gpu_memory(self) -> None:
        """
        Cleanup GPU memory and clear cache

        Clears PyTorch GPU cache to free up VRAM
        """
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print(f"[GPUAudio] GPU cache cleared")
        except Exception as e:
            print(f"[GPUAudio] Warning: Failed to cleanup GPU memory: {str(e)}")

    def load_audio(self, audio_path: str) -> Tuple[torch.Tensor, int]:
        """
        Load audio file to GPU memory

        Args:
            audio_path: Path to audio file

        Returns:
            (waveform, sample_rate) tuple with waveform on GPU

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If loading fails
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        try:
            # Load with torchaudio
            waveform, sample_rate = torchaudio.load(audio_path)

            # Move immediately to GPU
            waveform = waveform.to(self.device)

            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)

            return waveform, sample_rate

        except Exception as e:
            raise RuntimeError(f"Failed to load audio: {str(e)}")

    def resample_gpu(self, waveform: torch.Tensor, orig_sr: int, target_sr: int = 16000) -> torch.Tensor:
        """GPU-accelerated resampling using julius (high quality)"""
        if orig_sr == target_sr:
            return waveform

        # Use julius for high-quality resampling on GPU
        # Julius uses sinc interpolation which is superior to linear
        resampled = julius.resample_frac(waveform, orig_sr, target_sr)

        return resampled

    def detect_silence_gpu(self, waveform: torch.Tensor,
                          threshold_db: float = -40.0,
                          min_silence_duration: float = 0.5,
                          sample_rate: int = 16000) -> Tuple[torch.Tensor, torch.Tensor]:
        """GPU-accelerated silence detection"""
        # Calculate dB levels using GPU
        # Add small epsilon to avoid log(0)
        db_levels = 20 * torch.log10(torch.abs(waveform) + 1e-10)

        # Create silence mask
        silence_mask = db_levels < threshold_db

        # Find silence regions using morphological operations
        min_silence_samples = int(min_silence_duration * sample_rate)

        # Use 1D convolution for efficient region detection
        kernel = torch.ones(1, 1, min_silence_samples).to(self.device) / min_silence_samples
        silence_regions = torch.nn.functional.conv1d(
            silence_mask.float().unsqueeze(0),
            kernel,
            padding=min_silence_samples//2
        ).squeeze(0) > 0.99

        return silence_mask, silence_regions

    def trim_silence_gpu(self, waveform: torch.Tensor,
                        threshold_db: float = -40.0,
                        min_silence_duration: float = 0.5,
                        sample_rate: int = 16000) -> torch.Tensor:
        """Remove leading and trailing silence using GPU"""
        silence_mask, silence_regions = self.detect_silence_gpu(
            waveform, threshold_db, min_silence_duration, sample_rate
        )

        # Find first and last non-silent samples
        non_silent = ~silence_regions.squeeze()
        if non_silent.any():
            indices = torch.where(non_silent)[0]
            start_idx = indices[0].item()
            end_idx = indices[-1].item() + 1

            # Trim the waveform
            trimmed = waveform[:, start_idx:end_idx]
        else:
            # All silent, return as-is
            trimmed = waveform

        return trimmed

    def normalize_gpu(self, waveform: torch.Tensor,
                     target_db: float = -20.0,
                     headroom: float = 0.1) -> torch.Tensor:
        """GPU-accelerated peak normalization"""
        # Calculate current peak amplitude
        peak = torch.abs(waveform).max()

        # Calculate target peak with headroom
        target_peak = 10 ** (target_db / 20) * (1 - headroom)

        # Scale to target
        if peak > 0:
            scale_factor = target_peak / peak
            normalized = waveform * scale_factor
        else:
            normalized = waveform

        # Ensure no clipping
        normalized = torch.clamp(normalized, -1.0, 1.0)

        return normalized

    def save_audio_gpu(self, waveform: torch.Tensor,
                      sample_rate: int,
                      output_path: str,
                      format: str = "mp3",
                      bitrate: str = "64k") -> None:
        """
        Save GPU tensor as audio file

        Moves waveform to CPU, saves it, and cleans up GPU memory
        """
        try:
            # Move to CPU for saving
            waveform_cpu = waveform.cpu()

            # Save using torchaudio with specific encoding
            if format == "mp3":
                # For MP3, we need to use a specific backend
                torchaudio.save(
                    output_path,
                    waveform_cpu,
                    sample_rate,
                    format="mp3",
                    encoding="PCM_S",
                    bits_per_sample=16
                )
            else:
                torchaudio.save(output_path, waveform_cpu, sample_rate)
        finally:
            # Cleanup GPU memory after saving
            del waveform
            if torch.cuda.is_available():
                torch.cuda.empty_cache()