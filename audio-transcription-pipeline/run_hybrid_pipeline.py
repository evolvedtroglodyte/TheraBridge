#!/usr/bin/env python3
"""
Hybrid Audio Transcription Pipeline - API + GPU
Uses OpenAI Whisper API for transcription (no cuDNN issues)
Uses GPU for pyannote diarization
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime

def main():
    print("="*70)
    print("HYBRID AUDIO TRANSCRIPTION PIPELINE (API + GPU)")
    print("="*70)

    # Import pipeline
    print("\nImporting pipeline modules...")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
    from pipeline import AudioTranscriptionPipeline
    print("✓ Pipeline imported successfully")

    # Configuration
    AUDIO_FILE = "/root/test_audio.mp3"
    NUM_SPEAKERS = 2
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

    # Initialize pipeline
    print("\n" + "="*70)
    print("INITIALIZING PIPELINE (OpenAI API + GPU Diarization)")
    print("="*70)
    print(f"  Transcription: OpenAI Whisper API (large-v3)")
    print(f"  Diarization: pyannote.audio 3.1 (GPU)")
    print(f"  Number of speakers: {NUM_SPEAKERS}")
    print(f"  Language: {LANGUAGE}")

    pipeline = AudioTranscriptionPipeline()
    print("\n✓ Pipeline ready")

    # Run processing
    print("\n" + "="*70)
    print("PROCESSING AUDIO")
    print("="*70)

    start_time = time.time()

    results = pipeline.process(
        audio_path=AUDIO_FILE,
        num_speakers=NUM_SPEAKERS,
        language=LANGUAGE
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
        print(f"  {stage:35s} {time_taken:8.2f}s")

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
    output_file = f"/root/hybrid_results_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n✓ Results saved to: {output_file}")
    print(f"  File size: {os.path.getsize(output_file) / 1024:.1f} KB")

    print("\n" + "="*70)
    print("PIPELINE EXECUTION COMPLETE")
    print("="*70)

    return 0

if __name__ == "__main__":
    sys.exit(main())
