#!/bin/bash
#
# Run this script directly on the Vast.ai instance after SSH'ing in
# Copy-paste this entire script into the terminal
#

set -e

echo "==> Installing dependencies..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git ffmpeg sox > /dev/null 2>&1

echo "==> Setting up Python environment..."
pip install -q torch torchaudio faster-whisper pyannote.audio pydub

echo "==> Cloning repository..."
if [ -d "TheraBridge" ]; then
    cd TheraBridge && git pull -q && cd ..
else
    git clone -q https://github.com/evolvedtroglodyte/TheraBridge.git
fi
cd TheraBridge/audio-transcription-pipeline

# Set HuggingFace token from environment (user must set before running)
# export HF_TOKEN=your_token_here  # Set this in your environment or .env file

echo "==> Checking if audio file exists..."
if [ ! -f "/root/test_audio.mp3" ]; then
    echo "ERROR: Audio file not found at /root/test_audio.mp3"
    echo "Please upload it first using:"
    echo "  scp -P <PORT> 'local/path/to/audio.mp3' root@ssh1.vast.ai:/root/test_audio.mp3"
    exit 1
fi

echo "==> Processing audio with GPU pipeline..."
python3 << 'PYTHON_SCRIPT'
import os
import json
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

print("\n" + "="*60)
print("GPU AUDIO PROCESSING")
print("="*60 + "\n")

# Import and run pipeline
from pipeline_gpu import GPUTranscriptionPipeline

start_time = time.time()

with GPUTranscriptionPipeline(whisper_model="large-v3") as pipeline:
    results = pipeline.process(
        audio_path="/root/test_audio.mp3",
        num_speakers=2,
        language="en",
        enable_diarization=True
    )

total_time = time.time() - start_time

# Add timing
results['total_processing_time'] = total_time

# Save results
with open('/root/results.json', 'w') as f:
    json.dump(results, f, indent=2, default=str)

# Print summary
perf = results.get('performance', {})
transcript = results.get('aligned_transcript', []) or results.get('transcript', [])

print("\n" + "="*60)
print("PROCESSING COMPLETE")
print("="*60)
print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
print(f"Segments: {len(transcript)}")

# Audio duration
audio_duration = 0
if transcript:
    audio_duration = max([seg.get('end', 0) for seg in transcript] or [0])
if audio_duration > 0:
    speedup = audio_duration / max(total_time, 1)
    print(f"Audio duration: {audio_duration:.1f}s ({audio_duration/60:.1f} min)")
    print(f"Speedup: {speedup:.2f}x real-time")

# Count speakers
speakers = {}
for seg in transcript:
    speaker = seg.get('speaker', 'Unknown')
    speakers[speaker] = speakers.get(speaker, 0) + 1

print("\nSpeakers:")
for speaker, count in sorted(speakers.items()):
    print(f"  {speaker}: {count} segments")

# Show first 30 segments
print("\n" + "="*60)
print("DIARIZED TRANSCRIPT (First 30 segments)")
print("="*60 + "\n")

current_speaker = None
for i, seg in enumerate(transcript[:30]):
    speaker = seg.get('speaker', 'Unknown')
    text = seg.get('text', '').strip()
    start = seg.get('start', 0)

    if speaker != current_speaker:
        print(f"\n[{speaker}] ({start:.1f}s)")
        current_speaker = speaker

    print(f"  {text}")

if len(transcript) > 30:
    print(f"\n... ({len(transcript) - 30} more segments)")

print("\n" + "="*60)
print("Results saved to: /root/results.json")
print("Download with: scp -P <PORT> root@ssh1.vast.ai:/root/results.json ./")
print("="*60 + "\n")
PYTHON_SCRIPT

echo "==> Complete!"
