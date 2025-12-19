#!/usr/bin/env python3
"""
Quick test of speaker diarization on short audio
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

print("="*60)
print("Speaker Diarization Test")
print("="*60)
print()

# Test with the CBT session audio - use relative path from test file location
script_dir = Path(__file__).parent

# Try to find any available sample audio file
candidates = [
    script_dir / "samples" / "compressed-cbt-session.m4a",
    script_dir / "samples" / "LIVE Cognitive Behavioral Therapy Session (1).mp3",
    script_dir / "samples" / "Person-Centred Therapy Session - Full Example [VLDDUL3HBIg].mp3",
]

audio_file = None
for candidate in candidates:
    if candidate.exists():
        audio_file = candidate
        break

if audio_file is None:
    print(f"❌ No sample audio files found in tests/samples/")
    print(f"")
    print(f"Please add sample audio files to run this test.")
    print(f"See tests/README.md for setup instructions.")
    exit(1)

print(f"Testing diarization on: {audio_file}")
print("(Using first minute only for quick test)")
print()

# Create a 1-minute clip for testing
from pydub import AudioSegment

print("Creating 1-minute test clip...")
full_audio = AudioSegment.from_file(str(audio_file))
one_minute = full_audio[:60000]  # First 60 seconds
test_file = script_dir / "test_1min.mp3"
one_minute.export(str(test_file), format="mp3")
print(f"✅ Created {test_file}")
print()

try:
    # Initialize diarization pipeline
    from pyannote.audio import Pipeline

    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("❌ HF_TOKEN not found in .env")
        exit(1)

    print("Loading speaker diarization model...")
    print("(This downloads ~1GB model on first run - be patient!)")
    start = time.time()

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=hf_token
    )

    load_time = time.time() - start
    print(f"✅ Model loaded in {load_time:.1f}s")
    print()

    # Run diarization
    # Load audio as waveform (pyannote needs it pre-loaded due to torchcodec issue)
    print("Loading audio as waveform...")
    import torch
    import torchaudio

    waveform, sample_rate = torchaudio.load(str(test_file))

    # Prepare audio dict for pyannote
    audio_dict = {
        "waveform": waveform,
        "sample_rate": sample_rate
    }

    print("Running diarization on 1-minute clip...")
    start = time.time()

    diarization = pipeline(audio_dict)

    process_time = time.time() - start
    print(f"✅ Diarization complete in {process_time:.1f}s")
    print()

    # Show results - use speaker_diarization attribute
    annotation = diarization.speaker_diarization

    print("Speaker turns detected:")
    print("-" * 60)

    turn_count = 0
    for turn, _, speaker in annotation.itertracks(yield_label=True):
        turn_count += 1
        print(f"[{turn.start:5.1f}s - {turn.end:5.1f}s] {speaker}")

    print("-" * 60)
    print(f"\n✅ SUCCESS! Detected {turn_count} speaker turns in 1 minute")
    print()
    print("Your diarization setup is working correctly!")

finally:
    # Cleanup - always run even if test fails
    if test_file.exists():
        test_file.unlink()
        print(f"Cleaned up {test_file}")

print("="*60)
