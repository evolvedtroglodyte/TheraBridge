#!/usr/bin/env python3
"""
GPU Audio Transcription Pipeline - Standalone Execution Script
Runs the complete audio processing pipeline on GPU with real-time progress tracking
"""

import os
import sys
import json
import time
import torch
from pathlib import Path
from datetime import datetime

def main():
    print("="*70)
    print("GPU AUDIO TRANSCRIPTION PIPELINE")
    print("="*70)

    # System info
    print(f"\nPython: {sys.version}")
    print(f"PyTorch: {torch.__version__}")
    print(f"CUDA Available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # Import pipeline
    print("\nImporting pipeline modules...")
    # Add src directory to Python path
    src_dir = os.path.join(os.path.dirname(__file__), 'src')
    sys.path.insert(0, src_dir)
    from pipeline_gpu import GPUTranscriptionPipeline
    print("✓ Pipeline imported successfully")

    # Configuration
    AUDIO_FILE = "/root/test_audio.mp3"
    NUM_SPEAKERS = 2
    WHISPER_MODEL = "large-v3"
    LANGUAGE = "en"

    # Check audio file
    print("\n" + "="*70)
    print("AUDIO FILE CHECK")
    print("="*70)
    if not os.path.exists(AUDIO_FILE):
        print(f"❌ Audio file not found: {AUDIO_FILE}")
        return 1

    file_size_mb = os.path.getsize(AUDIO_FILE) / (1024 * 1024)
    print(f"✓ Audio file: {AUDIO_FILE} ({file_size_mb:.1f} MB)")

    # Check audio duration
    from pydub import AudioSegment
    audio = AudioSegment.from_file(AUDIO_FILE)
    duration_secs = len(audio) / 1000
    duration_mins = duration_secs / 60

    print(f"  Duration: {duration_mins:.1f} minutes ({duration_secs:.0f} seconds)")
    print(f"  Sample Rate: {audio.frame_rate} Hz")
    print(f"  Channels: {audio.channels}")
    print(f"  Estimated processing time: {duration_mins * 0.15:.1f} - {duration_mins * 0.2:.1f} minutes")

    # Initialize pipeline
    print("\n" + "="*70)
    print("INITIALIZING GPU PIPELINE")
    print("="*70)
    print(f"  Whisper model: {WHISPER_MODEL}")
    print(f"  Number of speakers: {NUM_SPEAKERS}")
    print(f"  Language: {LANGUAGE}")

    pipeline = GPUTranscriptionPipeline(
        whisper_model=WHISPER_MODEL
    )
    print("\n✓ Pipeline ready")

    # Run processing
    print("\n" + "="*70)
    print("PROCESSING AUDIO")
    print("="*70)

    start_time = time.time()

    results = pipeline.process(
        audio_path=AUDIO_FILE,
        num_speakers=NUM_SPEAKERS,
        language=LANGUAGE,
        enable_diarization=True
    )

    total_time = time.time() - start_time

    print("\n" + "="*70)
    print("✓ PROCESSING COMPLETE")
    print("="*70)
    print(f"Total time: {total_time:.1f} seconds ({total_time/60:.1f} minutes)")
    print(f"Speedup: {duration_secs / total_time:.2f}x real-time")

    # Display performance metrics
    perf = results.get('performance', {})

    print("\n" + "="*70)
    print("PERFORMANCE METRICS")
    print("="*70)

    stages = perf.get('stages', {})
    for stage, time_taken in stages.items():
        print(f"  {stage:30s} {time_taken:8.2f}s")

    gpu_metrics = perf.get('gpu_metrics', {})
    if gpu_metrics:
        print("\nGPU Metrics:")
        print(f"  Provider: {gpu_metrics.get('provider', 'unknown')}")
        print(f"  Device: {gpu_metrics.get('device', 'unknown')}")
        print(f"  Peak VRAM: {gpu_metrics.get('peak_vram_gb', 0):.1f} GB")
        print(f"  Avg Utilization: {gpu_metrics.get('avg_utilization_pct', 0):.1f}%")

    # Display transcript statistics
    transcript = results.get('aligned_transcript', []) or results.get('transcript', [])

    print("\n" + "="*70)
    print("TRANSCRIPT STATISTICS")
    print("="*70)
    print(f"Total segments: {len(transcript)}")

    # Count by speaker
    speakers = {}
    for seg in transcript:
        speaker = seg.get('speaker', 'Unknown')
        speakers[speaker] = speakers.get(speaker, 0) + 1

    for speaker, count in sorted(speakers.items()):
        print(f"  {speaker}: {count} segments")

    # Display diarized transcript (first 20 segments)
    print("\n" + "="*70)
    print("DIARIZED TRANSCRIPT (First 20 segments)")
    print("="*70 + "\n")

    current_speaker = None
    for i, seg in enumerate(transcript[:20]):
        speaker = seg.get('speaker', 'Unknown')
        text = seg.get('text', '').strip()
        start = seg.get('start', 0)

        # Add speaker label when speaker changes
        if speaker != current_speaker:
            print(f"\n[{speaker}] ({start:.1f}s)")
            current_speaker = speaker

        print(f"  {text}")

    if len(transcript) > 20:
        print(f"\n... ({len(transcript) - 20} more segments)")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"/root/gpu_results_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n✓ Results saved to: {output_file}")
    print(f"  File size: {os.path.getsize(output_file) / 1024:.1f} KB")

    # Cleanup
    pipeline.cleanup_models()
    print("\n✓ GPU memory released")

    print("\n" + "="*70)
    print("PIPELINE EXECUTION COMPLETE")
    print("="*70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
