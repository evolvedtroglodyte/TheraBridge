"""
Test All Algorithms on a Single Session

This script runs ALL AI extraction algorithms on a single mock therapy session
and displays comprehensive output for each component:

1. Mood Analysis (mood_analyzer.py)
2. Topic Extraction (topic_extractor.py)
3. Breakthrough Detection (breakthrough_detector.py)
4. Technique Validation (technique_library.py)
5. Deep Analysis (deep_analyzer.py) - Note: Requires database

Usage:
    python test_all_algorithms.py
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.mood_analyzer import MoodAnalyzer
from app.services.topic_extractor import TopicExtractor
from app.services.breakthrough_detector import BreakthroughDetector
from app.services.technique_library import get_technique_library


def load_session(session_file: Path) -> dict:
    """Load session data from JSON file"""
    with open(session_file, 'r') as f:
        return json.load(f)


def print_section(title: str, char: str = "="):
    """Print a formatted section header"""
    print(f"\n{char * 80}")
    print(f"{title.center(80)}")
    print(f"{char * 80}\n")


def print_subsection(title: str):
    """Print a formatted subsection header"""
    print(f"\n{title}")
    print("-" * len(title))


def run_mood_analysis(session_id: str, segments: list):
    """Run mood analysis algorithm"""
    print_section("ALGORITHM 1: MOOD ANALYSIS", "=")

    try:
        analyzer = MoodAnalyzer()
        result = analyzer.analyze_session_mood(
            session_id=session_id,
            segments=segments,
            patient_speaker_id="SPEAKER_01"
        )

        print(f"Session ID: {result.session_id}")
        print(f"Mood Score: {result.mood_score}/10.0")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Emotional Tone: {result.emotional_tone}")

        print_subsection("Rationale")
        print(result.rationale)

        print_subsection("Key Indicators")
        for i, indicator in enumerate(result.key_indicators, 1):
            print(f"  {i}. {indicator}")

        print_subsection("Analysis Metadata")
        print(f"Analyzed At: {result.analyzed_at}")

        return result

    except Exception as e:
        print(f"❌ Mood Analysis Failed: {e}")
        return None


def run_topic_extraction(session_id: str, segments: list):
    """Run topic extraction algorithm"""
    print_section("ALGORITHM 2: TOPIC EXTRACTION", "=")

    try:
        extractor = TopicExtractor()
        result = extractor.extract_metadata(
            session_id=session_id,
            segments=segments,
            speaker_roles={"SPEAKER_00": "Therapist", "SPEAKER_01": "Client"}
        )

        print(f"Session ID: {result.session_id}")

        print_subsection("Topics")
        for i, topic in enumerate(result.topics, 1):
            print(f"  {i}. {topic}")

        print_subsection("Action Items")
        for i, item in enumerate(result.action_items, 1):
            print(f"  {i}. {item}")

        print_subsection("Therapeutic Technique")
        print(f"  {result.technique}")

        print_subsection("Session Summary")
        print(f"  {result.summary}")
        print(f"  (Length: {len(result.summary)} characters)")

        print_subsection("Extraction Metadata")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Extracted At: {result.extracted_at}")

        return result

    except Exception as e:
        print(f"❌ Topic Extraction Failed: {e}")
        return None


def run_breakthrough_detection(session_id: str, segments: list):
    """Run breakthrough detection algorithm"""
    print_section("ALGORITHM 3: BREAKTHROUGH DETECTION", "=")

    try:
        detector = BreakthroughDetector()
        result = detector.analyze_session(
            transcript=segments,
            session_metadata={"session_id": session_id}
        )

        print(f"Session ID: {result.session_id}")
        print(f"Has Breakthrough: {result.has_breakthrough}")
        print(f"Breakthrough Count: {len(result.breakthrough_candidates)}")

        if result.primary_breakthrough:
            print_subsection("Primary Breakthrough")
            bt = result.primary_breakthrough
            print(f"Type: {bt.breakthrough_type}")
            print(f"Confidence: {bt.confidence_score:.2f}")
            print(f"Timestamp: {bt.timestamp_start:.1f}s - {bt.timestamp_end:.1f}s")
            print(f"\nDescription:")
            print(f"  {bt.description}")
            print(f"\nEvidence:")
            print(f"  {bt.evidence}")

            if bt.speaker_sequence:
                print(f"\nDialogue Excerpt:")
                for turn in bt.speaker_sequence[:5]:  # Show first 5 turns
                    print(f"  {turn['speaker']}: {turn['text'][:100]}...")

        if len(result.breakthrough_candidates) > 1:
            print_subsection(f"Additional Breakthroughs ({len(result.breakthrough_candidates) - 1})")
            for i, bt in enumerate(result.breakthrough_candidates[1:], 2):
                print(f"\n  {i}. {bt.breakthrough_type} (confidence: {bt.confidence_score:.2f})")
                print(f"     {bt.description}")

        print_subsection("Session Analysis")
        print(f"Summary: {result.session_summary}")
        print(f"Emotional Trajectory: {result.emotional_trajectory}")

        return result

    except Exception as e:
        print(f"❌ Breakthrough Detection Failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def run_technique_validation(technique_str: str):
    """Run technique validation/standardization"""
    print_section("ALGORITHM 4: TECHNIQUE VALIDATION", "=")

    try:
        library = get_technique_library()

        print(f"Raw Technique: '{technique_str}'")

        standardized, confidence, match_type = library.validate_and_standardize(technique_str)

        print_subsection("Validation Result")
        print(f"Standardized: {standardized or 'No match found'}")
        print(f"Confidence: {confidence:.2f}")
        print(f"Match Type: {match_type}")

        if standardized:
            definition = library.get_technique_definition(standardized)
            if definition:
                print_subsection("Technique Definition")
                print(f"  {definition}")

        # Show similar techniques if no exact match
        if match_type == "none" or match_type == "fuzzy":
            print_subsection("Technique Library Stats")
            all_techniques = library.get_all_formatted_names()
            print(f"Total techniques in library: {len(all_techniques)}")

            modalities = ["CBT", "DBT", "ACT", "Mindfulness-Based", "EMDR", "Psychodynamic"]
            for modality in modalities:
                techniques = library.get_techniques_by_modality(modality)
                if techniques:
                    print(f"  {modality}: {len(techniques)} techniques")

        return standardized

    except Exception as e:
        print(f"❌ Technique Validation Failed: {e}")
        return None


def display_comprehensive_summary(session: dict, mood_result, topic_result, breakthrough_result, technique_result):
    """Display a comprehensive summary of all algorithm outputs"""
    print_section("COMPREHENSIVE ANALYSIS SUMMARY", "█")

    print_subsection("Session Information")
    print(f"Session ID: {session['id']}")
    print(f"Filename: {session['filename']}")
    print(f"Duration: {session['metadata']['duration']/60:.1f} minutes")
    print(f"Date: {session['metadata']['timestamp']}")

    print_subsection("Quick Stats")
    print(f"Total Segments: {session['quality']['total_segments']}")
    print(f"Therapist Segments: {session['quality']['speaker_segment_distribution']['SPEAKER_00']}")
    print(f"Client Segments: {session['quality']['speaker_segment_distribution']['SPEAKER_01']}")

    if mood_result:
        print_subsection("Mood Summary")
        print(f"Score: {mood_result.mood_score}/10.0 ({mood_result.emotional_tone})")
        print(f"Top Indicator: {mood_result.key_indicators[0] if mood_result.key_indicators else 'N/A'}")

    if topic_result:
        print_subsection("Session Focus")
        print(f"Main Topic: {topic_result.topics[0] if topic_result.topics else 'N/A'}")
        print(f"Technique: {topic_result.technique}")
        print(f"Summary: {topic_result.summary}")

    if breakthrough_result and breakthrough_result.has_breakthrough:
        print_subsection("Key Breakthrough")
        if breakthrough_result.primary_breakthrough:
            bt = breakthrough_result.primary_breakthrough
            print(f"Type: {bt.breakthrough_type}")
            print(f"Description: {bt.description}")

    print("\n" + "█" * 80 + "\n")


def main():
    """Main execution function"""
    print_section("COMPREHENSIVE ALGORITHM TESTING SUITE", "█")
    print("Testing all AI extraction algorithms on a single therapy session")
    print("Session: session_03_adhd_discovery.json (Alex Chen)")

    # Load session data
    session_file = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions" / "session_03_adhd_discovery.json"

    if not session_file.exists():
        print(f"❌ Session file not found: {session_file}")
        return

    print(f"\n✓ Loading session from: {session_file.name}")
    session = load_session(session_file)
    segments = session['segments']
    session_id = session['id']

    print(f"✓ Loaded {len(segments)} segments")
    print(f"✓ Session duration: {session['metadata']['duration']/60:.1f} minutes")

    # Run all algorithms
    mood_result = run_mood_analysis(session_id, segments)
    topic_result = run_topic_extraction(session_id, segments)
    breakthrough_result = run_breakthrough_detection(session_id, segments)

    # Technique validation (using result from topic extraction)
    if topic_result:
        technique_result = run_technique_validation(topic_result.technique)
    else:
        technique_result = None

    # Display comprehensive summary
    display_comprehensive_summary(session, mood_result, topic_result, breakthrough_result, technique_result)

    # Note about Deep Analysis
    print_section("NOTE: DEEP ANALYSIS (Algorithm 5)", "=")
    print("Deep Analysis requires database access and patient history.")
    print("It synthesizes outputs from Algorithms 1-4 plus historical data.")
    print("\nTo run Deep Analysis:")
    print("  1. Ensure backend database is running")
    print("  2. Session data must be stored in database")
    print("  3. Use: python tests/test_deep_analysis.py")
    print("\nDeep Analysis outputs:")
    print("  - Progress indicators (symptom reduction, skill development)")
    print("  - Therapeutic insights (realizations, patterns, strengths)")
    print("  - Coping skill proficiency")
    print("  - Therapeutic relationship quality")
    print("  - Actionable recommendations")
    print("=" * 80)


if __name__ == "__main__":
    main()
