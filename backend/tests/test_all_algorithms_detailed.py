"""
Detailed Algorithm Output Test - Saves Full JSON Output

This script runs all algorithms and saves detailed JSON output showing
the complete data structures returned by each component.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / ".env")

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.mood_analyzer import MoodAnalyzer
from app.services.topic_extractor import TopicExtractor
from app.services.breakthrough_detector import BreakthroughDetector
from app.services.technique_library import get_technique_library


def load_session(session_file: Path) -> dict:
    """Load session data from JSON file"""
    with open(session_file, 'r') as f:
        return json.load(f)


def serialize_datetime(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def main():
    """Run all algorithms and save detailed JSON output"""
    print("Running detailed algorithm analysis...")

    # Load session
    session_file = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions" / "session_03_adhd_discovery.json"
    session = load_session(session_file)
    segments = session['segments']
    session_id = session['id']

    results = {
        "test_metadata": {
            "session_id": session_id,
            "session_file": "session_03_adhd_discovery.json",
            "test_run_at": datetime.utcnow().isoformat(),
            "algorithms_tested": [
                "mood_analysis",
                "topic_extraction",
                "breakthrough_detection",
                "technique_validation"
            ]
        },
        "session_info": {
            "id": session['id'],
            "filename": session['filename'],
            "duration_seconds": session['metadata']['duration'],
            "duration_minutes": session['metadata']['duration'] / 60,
            "total_segments": session['quality']['total_segments'],
            "therapist_segments": session['quality']['speaker_segment_distribution']['SPEAKER_00'],
            "client_segments": session['quality']['speaker_segment_distribution']['SPEAKER_01'],
            "timestamp": session['metadata']['timestamp']
        },
        "algorithms": {}
    }

    # Algorithm 1: Mood Analysis
    print("  Running Mood Analysis...")
    try:
        analyzer = MoodAnalyzer()
        mood_result = analyzer.analyze_session_mood(session_id, segments, "SPEAKER_01")
        results["algorithms"]["mood_analysis"] = {
            "success": True,
            "output": {
                "session_id": mood_result.session_id,
                "mood_score": mood_result.mood_score,
                "confidence": mood_result.confidence,
                "emotional_tone": mood_result.emotional_tone,
                "rationale": mood_result.rationale,
                "key_indicators": mood_result.key_indicators,
                "analyzed_at": mood_result.analyzed_at.isoformat()
            }
        }
        print(f"    ✓ Mood Score: {mood_result.mood_score}/10.0")
    except Exception as e:
        results["algorithms"]["mood_analysis"] = {
            "success": False,
            "error": str(e)
        }
        print(f"    ✗ Error: {e}")

    # Algorithm 2: Topic Extraction
    print("  Running Topic Extraction...")
    try:
        extractor = TopicExtractor()
        topic_result = extractor.extract_metadata(
            session_id,
            segments,
            {"SPEAKER_00": "Therapist", "SPEAKER_01": "Client"}
        )
        results["algorithms"]["topic_extraction"] = {
            "success": True,
            "output": {
                "session_id": topic_result.session_id,
                "topics": topic_result.topics,
                "action_items": topic_result.action_items,
                "technique": topic_result.technique,
                "summary": topic_result.summary,
                "summary_length": len(topic_result.summary),
                "confidence": topic_result.confidence,
                "extracted_at": topic_result.extracted_at.isoformat(),
                "raw_meta_summary": topic_result.raw_meta_summary
            }
        }
        print(f"    ✓ Topics: {len(topic_result.topics)}, Technique: {topic_result.technique}")
    except Exception as e:
        results["algorithms"]["topic_extraction"] = {
            "success": False,
            "error": str(e)
        }
        print(f"    ✗ Error: {e}")

    # Algorithm 3: Breakthrough Detection
    print("  Running Breakthrough Detection...")
    try:
        detector = BreakthroughDetector()
        bt_result = detector.analyze_session(segments, {"session_id": session_id})

        breakthroughs = []
        for bt in bt_result.breakthrough_candidates:
            breakthroughs.append({
                "type": bt.breakthrough_type,
                "confidence_score": bt.confidence_score,
                "description": bt.description,
                "evidence": bt.evidence,
                "timestamp_start": bt.timestamp_start,
                "timestamp_end": bt.timestamp_end,
                "speaker_sequence": bt.speaker_sequence[:3]  # First 3 turns only
            })

        results["algorithms"]["breakthrough_detection"] = {
            "success": True,
            "output": {
                "session_id": bt_result.session_id,
                "has_breakthrough": bt_result.has_breakthrough,
                "breakthrough_count": len(bt_result.breakthrough_candidates),
                "primary_breakthrough": {
                    "type": bt_result.primary_breakthrough.breakthrough_type,
                    "confidence": bt_result.primary_breakthrough.confidence_score,
                    "description": bt_result.primary_breakthrough.description,
                    "evidence": bt_result.primary_breakthrough.evidence
                } if bt_result.primary_breakthrough else None,
                "all_breakthroughs": breakthroughs,
                "session_summary": bt_result.session_summary,
                "emotional_trajectory": bt_result.emotional_trajectory
            }
        }
        print(f"    ✓ Breakthroughs Found: {len(bt_result.breakthrough_candidates)}")
    except Exception as e:
        results["algorithms"]["breakthrough_detection"] = {
            "success": False,
            "error": str(e)
        }
        print(f"    ✗ Error: {e}")

    # Algorithm 4: Technique Validation
    print("  Running Technique Validation...")
    try:
        library = get_technique_library()
        raw_technique = results["algorithms"]["topic_extraction"]["output"]["technique"]

        standardized, confidence, match_type = library.validate_and_standardize(raw_technique)
        definition = library.get_technique_definition(standardized) if standardized else None

        results["algorithms"]["technique_validation"] = {
            "success": True,
            "output": {
                "raw_technique": raw_technique,
                "standardized_technique": standardized,
                "confidence": confidence,
                "match_type": match_type,
                "definition": definition,
                "library_stats": {
                    "total_techniques": len(library.get_all_techniques()),
                    "modalities": list(library.modalities.keys())
                }
            }
        }
        print(f"    ✓ Validated: {standardized}")
    except Exception as e:
        results["algorithms"]["technique_validation"] = {
            "success": False,
            "error": str(e)
        }
        print(f"    ✗ Error: {e}")

    # Save results
    output_file = Path(__file__).parent.parent.parent / "mock-therapy-data" / "session_03_all_algorithms_output.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=serialize_datetime)

    print(f"\n✓ Complete output saved to: {output_file.name}")
    print(f"\nSummary:")
    print(f"  - Mood Analysis: {'✓' if results['algorithms']['mood_analysis']['success'] else '✗'}")
    print(f"  - Topic Extraction: {'✓' if results['algorithms']['topic_extraction']['success'] else '✗'}")
    print(f"  - Breakthrough Detection: {'✓' if results['algorithms']['breakthrough_detection']['success'] else '✗'}")
    print(f"  - Technique Validation: {'✓' if results['algorithms']['technique_validation']['success'] else '✗'}")


if __name__ == "__main__":
    main()
