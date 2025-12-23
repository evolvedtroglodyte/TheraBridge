"""
Test Mood Analysis on Mock Transcripts

This script:
1. Loads all 12 mock therapy session transcripts
2. Runs AI mood analysis on each session
3. Displays results with mood scores and rationale
4. Validates that mood scores are in correct range (0.0-10.0, 0.5 increments)
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.mood_analyzer import MoodAnalyzer


def load_mock_transcript(session_file: str) -> dict:
    """Load a mock transcript JSON file"""
    mock_data_dir = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions"
    file_path = mock_data_dir / session_file

    with open(file_path, 'r') as f:
        return json.load(f)


def test_single_session(session_file: str):
    """Test mood analysis on a single session"""
    print(f"\n{'='*80}")
    print(f"Analyzing: {session_file}")
    print('='*80)

    # Load transcript
    transcript_data = load_mock_transcript(session_file)
    session_id = transcript_data['id']
    segments = transcript_data['segments']

    print(f"Session ID: {session_id}")
    print(f"Total segments: {len(segments)}")

    # Run mood analysis
    analyzer = MoodAnalyzer()
    try:
        analysis = analyzer.analyze_session_mood(
            session_id=session_id,
            segments=segments,
            patient_speaker_id="SPEAKER_01"
        )

        # Display results
        print(f"\n📊 MOOD ANALYSIS RESULTS:")
        print(f"  Mood Score: {analysis.mood_score}/10.0")
        print(f"  Confidence: {analysis.confidence:.2%}")
        print(f"  Emotional Tone: {analysis.emotional_tone}")
        print(f"\n💭 Rationale:")
        print(f"  {analysis.rationale}")
        print(f"\n🔍 Key Indicators:")
        for indicator in analysis.key_indicators:
            print(f"  • {indicator}")

        # Validate mood score
        assert 0.0 <= analysis.mood_score <= 10.0, "Mood score out of range"
        assert analysis.mood_score * 2 % 1 == 0, "Mood score not in 0.5 increments"
        print(f"\n✓ Validation passed")

        return analysis

    except Exception as e:
        print(f"\n❌ Error: {e}")
        raise


def test_all_sessions():
    """Test mood analysis on all 12 mock sessions"""
    session_files = [
        "session_01_crisis_intake.json",
        "session_02_emotional_regulation.json",
        "session_03_adhd_discovery.json",
        "session_04_medication_start.json",
        "session_05_family_conflict.json",
        "session_06_spring_break_hope.json",
        "session_07_dating_anxiety.json",
        "session_08_relationship_boundaries.json",
        "session_09_coming_out_preparation.json",
        "session_10_coming_out_aftermath.json",
        "session_11_rebuilding.json",
        "session_12_thriving.json",
    ]

    results = []

    print("\n" + "="*80)
    print("MOOD ANALYSIS TEST - ALL 12 SESSIONS")
    print("="*80)

    for session_file in session_files:
        try:
            analysis = test_single_session(session_file)
            results.append({
                'session': session_file.replace('.json', ''),
                'mood_score': analysis.mood_score,
                'emotional_tone': analysis.emotional_tone,
                'confidence': analysis.confidence,
            })
        except Exception as e:
            print(f"\n❌ Failed to analyze {session_file}: {e}")
            continue

    # Display summary
    print("\n" + "="*80)
    print("SUMMARY - MOOD PROGRESSION")
    print("="*80)
    print(f"\n{'Session':<40} {'Mood Score':<12} {'Emotional Tone':<20} {'Confidence'}")
    print("-" * 80)

    for result in results:
        session_name = result['session'].replace('session_', 'Session ').replace('_', ' ').title()
        mood_bar = '█' * int(result['mood_score']) + '░' * (10 - int(result['mood_score']))
        print(f"{session_name:<40} {result['mood_score']}/10 {mood_bar:<12} {result['emotional_tone']:<20} {result['confidence']:.0%}")

    # Calculate statistics
    if results:
        mood_scores = [r['mood_score'] for r in results]
        avg_mood = sum(mood_scores) / len(mood_scores)
        min_mood = min(mood_scores)
        max_mood = max(mood_scores)
        improvement = mood_scores[-1] - mood_scores[0] if len(mood_scores) > 1 else 0

        print("\n" + "="*80)
        print("STATISTICS")
        print("="*80)
        print(f"  Average Mood: {avg_mood:.1f}/10.0")
        print(f"  Range: {min_mood:.1f} - {max_mood:.1f}")
        print(f"  Overall Change: {improvement:+.1f} ({(improvement/mood_scores[0]*100):+.0f}%)")
        print(f"  Total Sessions Analyzed: {len(results)}/12")

        if improvement > 0:
            print(f"\n  📈 Trend: IMPROVING ({improvement:+.1f} points)")
        elif improvement < 0:
            print(f"\n  📉 Trend: DECLINING ({improvement:+.1f} points)")
        else:
            print(f"\n  ➡️  Trend: STABLE")

    print("\n" + "="*80)
    print("✓ ALL TESTS COMPLETED")
    print("="*80)


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key:")
        print("  export OPENAI_API_KEY='your-api-key-here'")
        sys.exit(1)

    # Run tests
    import argparse

    parser = argparse.ArgumentParser(description="Test mood analysis on mock transcripts")
    parser.add_argument(
        "--session",
        type=str,
        help="Specific session file to test (e.g., session_01_crisis_intake.json)",
    )

    args = parser.parse_args()

    if args.session:
        # Test single session
        test_single_session(args.session)
    else:
        # Test all sessions
        test_all_sessions()
