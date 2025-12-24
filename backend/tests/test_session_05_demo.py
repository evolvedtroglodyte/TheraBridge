"""
Test speaker labeling on Session 5 (Family Conflict)
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.speaker_labeler import SpeakerLabeler
import os
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

def load_session_05():
    """Load session 5 transcript"""
    mock_data_dir = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions"
    file_path = mock_data_dir / "session_05_family_conflict.json"

    with open(file_path, 'r') as f:
        return json.load(f)

def main():
    print("\n" + "="*100)
    print("SESSION 5 - FAMILY CONFLICT")
    print("Testing Speaker Labeling Algorithm on Real Mock Therapy Transcript")
    print("="*100 + "\n")

    # Load session data
    session_data = load_session_05()
    segments = session_data.get("segments", [])

    print(f"📊 Session Metadata:")
    print(f"   Duration: {session_data.get('metadata', {}).get('duration', 0) / 60:.1f} minutes")
    print(f"   Total Segments: {len(segments)}")
    print(f"   Session Type: Family Conflict\n")

    # Initialize speaker labeler
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return

    labeler = SpeakerLabeler(openai_api_key=api_key)

    # Step 1: Show first few raw segments
    print("="*100)
    print("STEP 1: RAW TRANSCRIPT PREVIEW (First 5 segments)")
    print("="*100 + "\n")

    for i, seg in enumerate(segments[:5]):
        print(f"[{i+1}] {seg['speaker']} ({seg['start']:.1f}s - {seg['end']:.1f}s)")
        print(f"    {seg['text']}\n")

    # Step 2: AI Speaker Detection
    print("="*100)
    print("STEP 2: AI SPEAKER ROLE DETECTION")
    print("="*100 + "\n")

    detection = labeler._detect_speaker_roles(segments)

    print(f"🤖 AI Analysis:")
    print(f"   Therapist Speaker ID: {detection.therapist_speaker_id}")
    print(f"   Patient Speaker ID:   {detection.patient_speaker_id}")
    print(f"   Confidence:           {detection.confidence:.2%}")
    print(f"\n💭 AI Reasoning:")
    print(f"   {detection.reasoning}\n")

    # Step 3: Calculate speaking statistics
    print("="*100)
    print("STEP 3: SPEAKING TIME STATISTICS")
    print("="*100 + "\n")

    stats = labeler._calculate_speaker_stats(segments)

    for speaker_id, data in stats.items():
        role = "Therapist" if speaker_id == detection.therapist_speaker_id else "Patient"
        print(f"{speaker_id} ({role}):")
        print(f"   Total Time:    {data['total_time_seconds']:.1f}s ({data['total_time_seconds']/60:.1f} min)")
        print(f"   Segments:      {data['segment_count']}")
        print(f"   Percentage:    {data['percentage']:.1f}%\n")

    # Step 4: Merge consecutive segments
    print("="*100)
    print("STEP 4: SEGMENT MERGING")
    print("="*100 + "\n")

    merged = labeler._merge_consecutive_segments(segments)

    print(f"Original Segments: {len(segments)}")
    print(f"Merged Segments:   {len(merged)}")
    print(f"Reduction:         {len(segments) - len(merged)} segments ({(1 - len(merged)/len(segments))*100:.1f}%)\n")

    # Step 5: Full labeling pipeline
    print("="*100)
    print("STEP 5: COMPLETE LABELED TRANSCRIPT")
    print("="*100 + "\n")

    result = labeler.label_transcript(
        raw_segments=segments,
        therapist_name="Dr. Emily Chen"
    )

    print(f"✅ Labeling Complete!")
    print(f"   Therapist: {result.therapist_name}")
    print(f"   Patient:   {result.patient_label}")
    print(f"   Confidence: {result.detection.confidence:.2%}")
    print(f"   Final Segments: {len(result.labeled_transcript)}\n")

    # Show full labeled transcript
    print("-"*100)
    print("FULL LABELED TRANSCRIPT (Patient-Facing View)")
    print("-"*100 + "\n")

    for i, seg in enumerate(result.labeled_transcript, 1):
        speaker_display = f"[{seg.speaker}]"
        print(f"{seg.timestamp} {speaker_display:25} {seg.text}")

        # Add spacing after each segment for readability
        if i < len(result.labeled_transcript):
            print()

    print("\n" + "-"*100)

    # Summary statistics
    print("\n" + "="*100)
    print("SUMMARY")
    print("="*100 + "\n")

    therapist_segments = sum(1 for seg in result.labeled_transcript if seg.speaker == result.therapist_name)
    patient_segments = sum(1 for seg in result.labeled_transcript if seg.speaker == result.patient_label)

    print(f"✅ Speaker Detection:     {detection.confidence:.2%} confidence")
    print(f"✅ Segment Reduction:     {len(segments)} → {len(result.labeled_transcript)} ({(1-len(result.labeled_transcript)/len(segments))*100:.1f}% reduction)")
    print(f"✅ Therapist Segments:    {therapist_segments}")
    print(f"✅ Patient Segments:      {patient_segments}")
    print(f"✅ Format:                Patient-facing (therapist name + 'You')")
    print(f"✅ Timestamps:            MM:SS format")

    print("\n🎉 Speaker labeling complete for Session 5!\n")

if __name__ == "__main__":
    main()
