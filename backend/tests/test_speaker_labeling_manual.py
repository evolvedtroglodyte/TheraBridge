"""
Manual test for speaker labeling - verifies AI detection and full pipeline
Run this to test the complete speaker labeling workflow
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.speaker_labeler import SpeakerLabeler
import os
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Sample transcript from plan
SAMPLE_TRANSCRIPT = [
    {"start": 0.0, "end": 28.4, "speaker": "SPEAKER_00", "text": "Hi Alex, welcome. I'm Dr. Rodriguez. Thanks for coming in today. Before we start, I want to explain a bit about confidentiality..."},
    {"start": 28.4, "end": 45.8, "speaker": "SPEAKER_01", "text": "Yeah, that makes sense. Um, I'm really nervous."},
    {"start": 45.8, "end": 60.2, "speaker": "SPEAKER_01", "text": "I've never done therapy before. My roommate kind of pushed me to make this appointment."},
    {"start": 60.2, "end": 72.3, "speaker": "SPEAKER_00", "text": "It's completely normal to feel nervous. This is a safe space."},
    {"start": 72.3, "end": 90.1, "speaker": "SPEAKER_00", "text": "Can you tell me what brings you here today?"},
    {"start": 90.1, "end": 3600.0, "speaker": "SPEAKER_01", "text": "I've been feeling really overwhelmed lately. Work has been stressful, and I just can't seem to shake this feeling of dread."},
]

def test_speaker_detection():
    """Test AI speaker role detection"""
    print("\n" + "="*80)
    print("TESTING SPEAKER ROLE DETECTION")
    print("="*80 + "\n")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    labeler = SpeakerLabeler(openai_api_key=api_key)

    # Test detection
    detection = labeler._detect_speaker_roles(SAMPLE_TRANSCRIPT)

    print(f"Therapist Speaker ID: {detection.therapist_speaker_id}")
    print(f"Patient Speaker ID: {detection.patient_speaker_id}")
    print(f"Confidence: {detection.confidence:.2f}")
    print(f"Reasoning: {detection.reasoning}\n")

    # Verify
    assert detection.therapist_speaker_id == "SPEAKER_00", "❌ Failed: Expected SPEAKER_00 as therapist"
    assert detection.patient_speaker_id == "SPEAKER_01", "❌ Failed: Expected SPEAKER_01 as patient"
    assert detection.confidence > 0.7, f"❌ Failed: Confidence too low ({detection.confidence:.2f})"

    print("✅ AI correctly identified therapist (SPEAKER_00)")
    print("✅ Confidence score is reasonable (>0.7)")
    return True

def test_segment_merging():
    """Test consecutive segment merging"""
    print("\n" + "="*80)
    print("TESTING SEGMENT MERGING")
    print("="*80 + "\n")

    api_key = os.getenv("OPENAI_API_KEY")
    labeler = SpeakerLabeler(openai_api_key=api_key)

    merged = labeler._merge_consecutive_segments(SAMPLE_TRANSCRIPT)

    print(f"Original segments: {len(SAMPLE_TRANSCRIPT)}")
    print(f"Merged segments: {len(merged)}\n")

    for i, seg in enumerate(merged):
        print(f"[{i+1}] {seg['speaker']} ({seg['start']:.1f}s - {seg['end']:.1f}s)")
        print(f"    Text: {seg['text'][:80]}...\n")

    # Verify
    assert len(merged) < len(SAMPLE_TRANSCRIPT), "❌ Failed: No merging occurred"
    assert merged[1]['speaker'] == 'SPEAKER_01', "❌ Failed: Wrong speaker after merge"
    assert "I've never done therapy before" in merged[1]['text'], "❌ Failed: Text not merged correctly"

    print("✅ Consecutive patient segments merged into single blocks")
    return True

def test_timestamp_formatting():
    """Test timestamp conversion to MM:SS"""
    print("\n" + "="*80)
    print("TESTING TIMESTAMP FORMATTING")
    print("="*80 + "\n")

    api_key = os.getenv("OPENAI_API_KEY")
    labeler = SpeakerLabeler(openai_api_key=api_key)

    test_cases = [
        (0.0, "00:00"),
        (28.4, "00:28"),
        (83.7, "01:23"),
        (3600.0, "60:00"),
    ]

    all_passed = True
    for seconds, expected in test_cases:
        result = labeler._format_timestamp(seconds)
        status = "✅" if result == expected else "❌"
        print(f"{status} {seconds}s → {result} (expected: {expected})")
        if result != expected:
            all_passed = False

    assert all_passed, "❌ Failed: Some timestamps not formatted correctly"
    print("\n✅ Timestamps convert correctly")
    return True

def test_full_pipeline():
    """Test complete labeling pipeline"""
    print("\n" + "="*80)
    print("TESTING FULL LABELING PIPELINE")
    print("="*80 + "\n")

    api_key = os.getenv("OPENAI_API_KEY")
    labeler = SpeakerLabeler(openai_api_key=api_key)

    result = labeler.label_transcript(
        raw_segments=SAMPLE_TRANSCRIPT,
        therapist_name="Dr. Sarah Rodriguez"
    )

    print(f"Therapist Name: {result.therapist_name}")
    print(f"Patient Label: {result.patient_label}")
    print(f"Detection Confidence: {result.detection.confidence:.2f}")
    print(f"Labeled Segments: {len(result.labeled_transcript)}\n")

    print("LABELED TRANSCRIPT:")
    print("-" * 80)
    for seg in result.labeled_transcript:
        speaker_label = f"[{seg.speaker}]"
        print(f"{seg.timestamp} {speaker_label:25} {seg.text[:60]}...")
    print("-" * 80)

    # Verify
    assert result.therapist_name == "Dr. Sarah Rodriguez", "❌ Failed: Wrong therapist name"
    assert result.patient_label == "You", "❌ Failed: Wrong patient label"
    assert result.labeled_transcript[0].speaker == "Dr. Sarah Rodriguez", "❌ Failed: First speaker not therapist"
    assert result.labeled_transcript[0].timestamp == "00:00", "❌ Failed: First timestamp not 00:00"
    assert len(result.labeled_transcript) < len(SAMPLE_TRANSCRIPT), "❌ Failed: No merging in final output"

    print("\n✅ Full pipeline produces correct output format")
    print("✅ Speaker labels applied correctly (therapist name and 'You')")
    print("✅ Timestamps in MM:SS format")
    print("✅ Segments merged")
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("SPEAKER LABELING MANUAL TEST SUITE")
    print("="*80)

    try:
        # Run all tests
        tests = [
            ("Speaker Detection", test_speaker_detection),
            ("Segment Merging", test_segment_merging),
            ("Timestamp Formatting", test_timestamp_formatting),
            ("Full Pipeline", test_full_pipeline),
        ]

        results = []
        for name, test_func in tests:
            try:
                passed = test_func()
                results.append((name, passed))
            except Exception as e:
                print(f"\n❌ {name} FAILED with error: {e}")
                results.append((name, False))

        # Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        for name, passed in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} - {name}")

        total_passed = sum(1 for _, passed in results if passed)
        print(f"\nTotal: {total_passed}/{len(results)} tests passed")

        if total_passed == len(results):
            print("\n🎉 ALL MANUAL VERIFICATION TESTS PASSED!")
            print("\nPhase 1 is complete and ready for production.")
        else:
            print("\n⚠️  Some tests failed. Please review the output above.")

    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
