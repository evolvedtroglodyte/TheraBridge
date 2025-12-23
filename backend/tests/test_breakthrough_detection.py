"""
Test script for Breakthrough Detection Algorithm

Tests the breakthrough detector against real therapy session transcripts
from the audio-transcription-pipeline outputs.
"""

import sys
import os
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.breakthrough_detector import BreakthroughDetector


def load_transcript(json_path: str) -> dict:
    """Load transcript JSON from audio pipeline output"""
    with open(json_path, 'r') as f:
        return json.load(f)


def test_breakthrough_detection():
    """
    Test breakthrough detection on real therapy session transcript.

    Expected breakthroughs in the sample session:
    1. Patient recognition of eating disorder triggers (insight)
    2. Connection between mom's pressure and body image issues (cognitive insight)
    3. Realization about Bruce potentially causing divorce (relational realization)
    """
    print("=" * 80)
    print("BREAKTHROUGH DETECTION TEST")
    print("=" * 80)

    # Initialize detector
    print("\n1. Initializing BreakthroughDetector...")
    detector = BreakthroughDetector()
    print("   ✓ Detector initialized with OpenAI API")

    # Load real therapy transcript
    print("\n2. Loading therapy session transcript...")
    transcript_path = "../../audio-transcription-pipeline/tests/outputs/cpu_pipeline_file1_20251219_013423.json"

    # Make path absolute
    script_dir = Path(__file__).parent
    full_path = (script_dir / transcript_path).resolve()

    if not full_path.exists():
        print(f"   ✗ Transcript not found at: {full_path}")
        print("\n   Available transcripts:")
        output_dir = script_dir / "../../audio-transcription-pipeline/tests/outputs"
        if output_dir.exists():
            for file in output_dir.glob("*.json"):
                print(f"     - {file.name}")
        return

    data = load_transcript(str(full_path))
    transcript = data.get("segments", [])
    metadata = data.get("metadata", {})

    print(f"   ✓ Loaded transcript: {metadata.get('source_file', 'unknown')}")
    print(f"   ✓ Duration: {metadata.get('duration', 0):.1f} seconds")
    print(f"   ✓ Total segments: {len(transcript)}")

    # Analyze session for breakthroughs
    print("\n3. Analyzing session with AI...")
    print("   (This may take 30-60 seconds...)")

    session_metadata = {
        "session_id": "test_session_1",
        "duration": metadata.get("duration"),
        "file": metadata.get("source_file")
    }

    analysis = detector.analyze_session(transcript, session_metadata)

    # Display results
    print("\n" + "=" * 80)
    print("ANALYSIS RESULTS")
    print("=" * 80)

    print(f"\n✓ Breakthroughs detected: {len(analysis.breakthrough_candidates)}")
    print(f"✓ Has primary breakthrough: {'Yes' if analysis.primary_breakthrough else 'No'}")

    print(f"\n📊 Session Summary:")
    print(f"   {analysis.session_summary}")

    print(f"\n💭 Emotional Trajectory:")
    print(f"   {analysis.emotional_trajectory}")

    # Display each breakthrough
    if analysis.breakthrough_candidates:
        print(f"\n🎯 BREAKTHROUGH MOMENTS ({len(analysis.breakthrough_candidates)}):")
        print("-" * 80)

        for i, breakthrough in enumerate(analysis.breakthrough_candidates, 1):
            print(f"\n   Breakthrough #{i}")
            print(f"   Type: {breakthrough.breakthrough_type}")
            print(f"   Confidence: {breakthrough.confidence_score:.2f}")
            print(f"   Timestamp: {int(breakthrough.timestamp_start // 60):02d}:{int(breakthrough.timestamp_start % 60):02d} - {int(breakthrough.timestamp_end // 60):02d}:{int(breakthrough.timestamp_end % 60):02d}")
            print(f"\n   Description:")
            print(f"   {breakthrough.description}")
            print(f"\n   Evidence:")
            print(f"   {breakthrough.evidence}")

            # Show dialogue excerpt
            if breakthrough.speaker_sequence:
                print(f"\n   Dialogue Excerpt:")
                for turn in breakthrough.speaker_sequence[:4]:  # Show first 4 turns
                    speaker = turn.get("speaker", "Unknown")
                    text = turn.get("text", "")[:150]  # Truncate long texts
                    print(f"   {speaker}: {text}...")

            print("-" * 80)
    else:
        print("\n   No breakthroughs detected in this session.")
        print("   This may indicate:")
        print("   - Early rapport-building phase")
        print("   - Maintenance/check-in session")
        print("   - Algorithm needs adjustment for this therapy style")

    # Export results
    print("\n4. Exporting results...")
    output_path = script_dir / "breakthrough_analysis_output.json"
    detector.export_breakthrough_report(analysis, str(output_path))
    print(f"   ✓ Results saved to: {output_path}")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


def test_with_known_breakthrough():
    """
    Test with a manually created example that SHOULD contain a breakthrough.
    This validates that the algorithm can detect obvious breakthrough moments.
    """
    print("\n\n" + "=" * 80)
    print("VALIDATION TEST: Known Breakthrough Example")
    print("=" * 80)

    # Create a sample transcript with an obvious breakthrough
    sample_transcript = [
        {"start": 0.0, "end": 3.5, "speaker": "Therapist", "text": "You mentioned feeling really anxious about your mother's criticism. Tell me more about that."},
        {"start": 3.5, "end": 8.2, "speaker": "Patient", "text": "Yeah, whenever she comments on my weight, I just shut down. I feel like nothing I do is ever good enough."},
        {"start": 8.2, "end": 12.0, "speaker": "Therapist", "text": "That sounds painful. When did you first start feeling that you weren't good enough?"},
        {"start": 12.0, "end": 18.5, "speaker": "Patient", "text": "I... I think it started when I was really young. Maybe 8 or 9? She would compare me to my cousin who was thinner."},
        {"start": 18.5, "end": 22.0, "speaker": "Therapist", "text": "So you've carried this belief for a very long time. How does it affect you today?"},
        {"start": 22.0, "end": 30.0, "speaker": "Patient", "text": "Oh my god. I just realized... I do the same thing to myself that she did to me. I'm constantly comparing myself to others and never feeling good enough."},
        {"start": 30.0, "end": 33.5, "speaker": "Therapist", "text": "That's a really important insight. You've internalized her critical voice."},
        {"start": 33.5, "end": 40.0, "speaker": "Patient", "text": "Yes! And I don't have to keep doing that. I can choose to be kinder to myself. This is... wow, this is big."},
    ]

    detector = BreakthroughDetector()
    analysis = detector.analyze_session(
        sample_transcript,
        {"session_id": "validation_test", "duration": 40.0}
    )

    print(f"\n✓ Expected: 1 breakthrough (cognitive insight)")
    print(f"✓ Detected: {len(analysis.breakthrough_candidates)} breakthrough(s)")

    if analysis.primary_breakthrough:
        print(f"\n✓ Primary breakthrough type: {analysis.primary_breakthrough.breakthrough_type}")
        print(f"✓ Confidence: {analysis.primary_breakthrough.confidence_score:.2f}")
        print(f"✓ Description: {analysis.primary_breakthrough.description}")

        if analysis.primary_breakthrough.confidence_score >= 0.7:
            print("\n✅ VALIDATION PASSED - Algorithm correctly identified breakthrough")
        else:
            print("\n⚠️  VALIDATION WARNING - Low confidence score")
    else:
        print("\n❌ VALIDATION FAILED - No breakthrough detected")


if __name__ == "__main__":
    # Run main test
    test_breakthrough_detection()

    # Run validation test
    test_with_known_breakthrough()

    print("\n\nTo run this test, execute:")
    print("  cd backend")
    print("  python tests/test_breakthrough_detection.py")
