"""
Quick Pipeline Test - Verify setup works on just Session 10
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Check if OpenAI API key is set
api_key = os.getenv("OPENAI_API_KEY")
print(f"OpenAI API Key present: {'Yes' if api_key else 'No'}")
print(f"API Key length: {len(api_key) if api_key else 0}")

# Try loading a session
data_dir = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions"
session_file = data_dir / "session_10_coming_out_aftermath.json"

print(f"\nLoading session file: {session_file}")
print(f"File exists: {session_file.exists()}")

if session_file.exists():
    with open(session_file, 'r') as f:
        session_data = json.load(f)

    print(f"Session ID: {session_data.get('id')}")
    print(f"Segments: {len(session_data.get('segments', []))}")

    # Try importing services
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))

    try:
        from app.services.mood_analyzer import MoodAnalyzer
        print("\n✓ MoodAnalyzer imported successfully")
    except Exception as e:
        print(f"\n❌ Failed to import MoodAnalyzer: {e}")

    try:
        from app.services.topic_extractor import TopicExtractor
        print("✓ TopicExtractor imported successfully")
    except Exception as e:
        print(f"❌ Failed to import TopicExtractor: {e}")

    try:
        from app.services.breakthrough_detector import BreakthroughDetector
        print("✓ BreakthroughDetector imported successfully")
    except Exception as e:
        print(f"❌ Failed to import BreakthroughDetector: {e}")

    # Try running mood analysis
    print("\n" + "=" * 80)
    print("Testing Mood Analysis on Session 10...")
    print("=" * 80)

    try:
        mood_analyzer = MoodAnalyzer()
        print("✓ MoodAnalyzer initialized")

        mood_analysis = mood_analyzer.analyze_session_mood(
            session_id="session_10",
            segments=session_data.get("segments", []),
            patient_speaker_id="SPEAKER_01"
        )

        print(f"\n✓ Mood Analysis Complete!")
        print(f"   Mood Score: {mood_analysis.mood_score}/10.0")
        print(f"   Confidence: {mood_analysis.confidence:.2f}")
        print(f"   Emotional Tone: {mood_analysis.emotional_tone}")
        print(f"   Rationale: {mood_analysis.rationale[:150]}...")

    except Exception as e:
        print(f"\n❌ Mood Analysis Failed: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 80)
print("Quick test complete!")
print("=" * 80)
