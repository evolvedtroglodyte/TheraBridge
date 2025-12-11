#!/usr/bin/env python3
"""
GPU Provider Detection and Configuration
Automatically detects GPU provider and optimizes settings
"""

import os
import platform
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict
import torch


class GPUProvider(Enum):
    """Supported GPU providers"""
    COLAB = "google_colab"
    VASTAI = "vast_ai"
    RUNPOD = "runpod"
    LAMBDA = "lambda_labs"
    PAPERSPACE = "paperspace"
    LOCAL = "local"
    UNKNOWN = "unknown"


@dataclass
class GPUConfig:
    """GPU configuration for optimal performance"""
    provider: GPUProvider
    device_name: str
    vram_gb: float
    compute_type: str  # "float16", "int8", "float32"
    batch_size: int
    num_workers: int
    enable_tf32: bool
    model_cache_dir: str


def detect_provider() -> GPUProvider:
    """
    Auto-detect GPU provider from environment

    Returns:
        GPUProvider enum indicating platform
    """
    # Check Colab
    if os.path.exists('/content') and 'COLAB_GPU' in os.environ:
        return GPUProvider.COLAB

    # Check for provider-specific environment variables
    # Vast.ai - check env vars first (hostname is usually a container ID)
    if 'VAST_CONTAINERLABEL' in os.environ or 'VAST_CONTAINER_USER' in os.environ:
        return GPUProvider.VASTAI

    if 'RUNPOD_POD_ID' in os.environ:
        return GPUProvider.RUNPOD

    if 'PAPERSPACE_METRIC_URL' in os.environ or os.path.exists('/storage'):
        return GPUProvider.PAPERSPACE

    # Check hostname patterns (fallback)
    hostname = platform.node().lower()
    if 'vast' in hostname or 'vps' in hostname:
        return GPUProvider.VASTAI

    if 'lambda' in hostname or 'lambdalabs' in hostname:
        return GPUProvider.LAMBDA

    # Check if running in container
    if os.path.exists('/.dockerenv'):
        return GPUProvider.LOCAL  # Assume local Docker

    return GPUProvider.UNKNOWN


def get_optimal_config() -> GPUConfig:
    """
    Get optimal GPU configuration based on detected hardware

    Returns:
        GPUConfig with optimized settings
    """
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA not available. GPU pipeline requires NVIDIA GPU.")

    provider = detect_provider()
    device_name = torch.cuda.get_device_name(0)
    vram_gb = torch.cuda.get_device_properties(0).total_memory / 1024**3

    # Determine optimal compute type based on GPU
    if "A100" in device_name or "H100" in device_name:
        compute_type = "float16"
        enable_tf32 = True
        batch_size = 16
    elif any(gpu in device_name for gpu in ["RTX 3090", "RTX 4090", "A6000"]):
        compute_type = "int8"
        enable_tf32 = False
        batch_size = 8
    else:
        # Safe defaults for other GPUs
        compute_type = "int8"
        enable_tf32 = False
        batch_size = 4

    # Determine model cache directory
    if provider == GPUProvider.COLAB:
        model_cache_dir = "/content/models"
    elif provider in [GPUProvider.VASTAI, GPUProvider.RUNPOD]:
        model_cache_dir = "/workspace/models"
    elif provider == GPUProvider.PAPERSPACE:
        model_cache_dir = "/storage/models"
    else:
        model_cache_dir = os.path.expanduser("~/.cache/huggingface")

    # Set environment variables for model caching
    os.environ['TRANSFORMERS_CACHE'] = model_cache_dir
    os.environ['HF_HOME'] = model_cache_dir

    return GPUConfig(
        provider=provider,
        device_name=device_name,
        vram_gb=vram_gb,
        compute_type=compute_type,
        batch_size=batch_size,
        num_workers=4,
        enable_tf32=enable_tf32,
        model_cache_dir=model_cache_dir
    )


def print_gpu_info():
    """Print detailed GPU information for debugging"""
    config = get_optimal_config()

    print("=" * 60)
    print("GPU Configuration")
    print("=" * 60)
    print(f"Provider: {config.provider.value}")
    print(f"Device: {config.device_name}")
    print(f"VRAM: {config.vram_gb:.1f} GB")
    print(f"Compute Type: {config.compute_type}")
    print(f"Batch Size: {config.batch_size}")
    print(f"TF32 Enabled: {config.enable_tf32}")
    print(f"Model Cache: {config.model_cache_dir}")
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"PyTorch Version: {torch.__version__}")
    print("=" * 60)


if __name__ == "__main__":
    print_gpu_info()
