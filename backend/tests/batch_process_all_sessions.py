"""
Batch Process All Mock Therapy Sessions

Runs all 4 AI extraction algorithms on all 12 mock therapy sessions using GPT-5 models.
Saves individual session outputs and generates comparative summary report.

Usage:
    python backend/tests/batch_process_all_sessions.py
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict, List, Any

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
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def process_single_session(
    session_file: Path,
    session_num: int,
    total_sessions: int
) -> Dict[str, Any]:
    """
    Process a single session through all algorithms.

    Returns:
        Dictionary with results and metadata
    """
    print(f"\n{'='*80}")
    print(f"Processing Session {session_num}/{total_sessions}: {session_file.name}")
    print(f"{'='*80}")

    session = load_session(session_file)
    segments = session['segments']
    session_id = session['id']

    results = {
        "session_id": session_id,
        "session_file": session_file.name,
        "processed_at": datetime.utcnow().isoformat(),
        "success": False,
        "algorithms": {},
        "errors": []
    }

    # Algorithm 1: Mood Analysis (GPT-5-mini)
    print("  [1/4] Running Mood Analysis (gpt-5-mini)...")
    try:
        analyzer = MoodAnalyzer(model="gpt-5-mini")
        mood_result = analyzer.analyze_session_mood(session_id, segments, "SPEAKER_01")
        results["algorithms"]["mood_analysis"] = {
            "success": True,
            "model": "gpt-5-mini",
            "output": {
                "mood_score": mood_result.mood_score,
                "confidence": mood_result.confidence,
                "emotional_tone": mood_result.emotional_tone,
                "rationale": mood_result.rationale,
                "key_indicators": mood_result.key_indicators,
                "analyzed_at": mood_result.analyzed_at.isoformat()
            }
        }
        print(f"        ✓ Mood Score: {mood_result.mood_score}/10.0")
    except Exception as e:
        results["algorithms"]["mood_analysis"] = {"success": False, "error": str(e)}
        results["errors"].append(f"Mood Analysis: {str(e)}")
        print(f"        ✗ Error: {e}")

    # Algorithm 2: Topic Extraction (GPT-5-mini)
    print("  [2/4] Running Topic Extraction (gpt-5-mini)...")
    try:
        extractor = TopicExtractor(model="gpt-5-mini")
        topic_result = extractor.extract_metadata(
            session_id,
            segments,
            {"SPEAKER_00": "Therapist", "SPEAKER_01": "Client"}
        )
        results["algorithms"]["topic_extraction"] = {
            "success": True,
            "model": "gpt-5-mini",
            "output": {
                "topics": topic_result.topics,
                "action_items": topic_result.action_items,
                "technique": topic_result.technique,
                "summary": topic_result.summary,
                "confidence": topic_result.confidence,
                "extracted_at": topic_result.extracted_at.isoformat()
            }
        }
        print(f"        ✓ Topics: {len(topic_result.topics)}, Technique: {topic_result.technique}")
    except Exception as e:
        results["algorithms"]["topic_extraction"] = {"success": False, "error": str(e)}
        results["errors"].append(f"Topic Extraction: {str(e)}")
        print(f"        ✗ Error: {e}")

    # Algorithm 3: Breakthrough Detection (GPT-5)
    print("  [3/4] Running Breakthrough Detection (gpt-5)...")
    try:
        detector = BreakthroughDetector(model="gpt-5")
        bt_result = detector.analyze_session(segments, {"session_id": session_id})

        breakthroughs = []
        for bt in bt_result.breakthrough_candidates:
            breakthroughs.append({
                "type": bt.breakthrough_type,
                "confidence_score": bt.confidence_score,
                "description": bt.description,
                "evidence": bt.evidence,
                "timestamp_start": bt.timestamp_start,
                "timestamp_end": bt.timestamp_end
            })

        results["algorithms"]["breakthrough_detection"] = {
            "success": True,
            "model": "gpt-5",
            "output": {
                "has_breakthrough": bt_result.has_breakthrough,
                "breakthrough_count": len(bt_result.breakthrough_candidates),
                "primary_breakthrough": {
                    "type": bt_result.primary_breakthrough.breakthrough_type,
                    "confidence": bt_result.primary_breakthrough.confidence_score,
                    "description": bt_result.primary_breakthrough.description
                } if bt_result.primary_breakthrough else None,
                "all_breakthroughs": breakthroughs,
                "emotional_trajectory": bt_result.emotional_trajectory
            }
        }
        print(f"        ✓ Breakthroughs: {len(bt_result.breakthrough_candidates)}")
    except Exception as e:
        results["algorithms"]["breakthrough_detection"] = {"success": False, "error": str(e)}
        results["errors"].append(f"Breakthrough Detection: {str(e)}")
        print(f"        ✗ Error: {e}")

    # Algorithm 4: Technique Validation (Local, no AI)
    print("  [4/4] Running Technique Validation (local)...")
    try:
        if results["algorithms"].get("topic_extraction", {}).get("success"):
            library = get_technique_library()
            raw_technique = results["algorithms"]["topic_extraction"]["output"]["technique"]
            standardized, confidence, match_type = library.validate_and_standardize(raw_technique)

            results["algorithms"]["technique_validation"] = {
                "success": True,
                "model": "local",
                "output": {
                    "raw_technique": raw_technique,
                    "standardized_technique": standardized,
                    "confidence": confidence,
                    "match_type": match_type
                }
            }
            print(f"        ✓ Validated: {standardized}")
        else:
            results["algorithms"]["technique_validation"] = {
                "success": False,
                "error": "Topic extraction failed, cannot validate technique"
            }
            print(f"        ✗ Skipped (topic extraction failed)")
    except Exception as e:
        results["algorithms"]["technique_validation"] = {"success": False, "error": str(e)}
        results["errors"].append(f"Technique Validation: {str(e)}")
        print(f"        ✗ Error: {e}")

    # Mark overall success if at least 2 algorithms succeeded
    successful_algos = sum(1 for algo in results["algorithms"].values() if algo.get("success"))
    results["success"] = successful_algos >= 2
    results["successful_algorithms"] = successful_algos

    print(f"\n  Session Result: {'✓ SUCCESS' if results['success'] else '✗ FAILED'} ({successful_algos}/4 algorithms)")

    return results


def generate_summary_report(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate comprehensive summary report with analytics.

    Args:
        all_results: List of individual session results

    Returns:
        Summary report dictionary
    """
    print("\n" + "="*80)
    print("GENERATING SUMMARY REPORT".center(80))
    print("="*80)

    summary = {
        "report_generated_at": datetime.utcnow().isoformat(),
        "total_sessions": len(all_results),
        "successful_sessions": sum(1 for r in all_results if r.get("success")),
        "failed_sessions": sum(1 for r in all_results if not r.get("success")),
        "statistics": {},
        "comparative_analytics": {},
        "cost_breakdown": {},
        "sessions": all_results
    }

    # Extract successful results only
    successful = [r for r in all_results if r.get("success")]

    if not successful:
        summary["error"] = "No successful sessions to analyze"
        return summary

    # === MOOD ANALYSIS STATISTICS ===
    mood_scores = []
    emotional_tones = []

    for result in successful:
        mood_data = result.get("algorithms", {}).get("mood_analysis", {}).get("output", {})
        if mood_data:
            mood_scores.append(mood_data.get("mood_score"))
            emotional_tones.append(mood_data.get("emotional_tone"))

    if mood_scores:
        summary["statistics"]["mood_analysis"] = {
            "average_mood_score": round(sum(mood_scores) / len(mood_scores), 2),
            "min_mood_score": min(mood_scores),
            "max_mood_score": max(mood_scores),
            "mood_trend": "improving" if mood_scores[-1] > mood_scores[0] else "declining" if mood_scores[-1] < mood_scores[0] else "stable",
            "emotional_tone_distribution": {tone: emotional_tones.count(tone) for tone in set(emotional_tones)}
        }

    # === TOPIC EXTRACTION STATISTICS ===
    all_topics = []
    all_techniques = []
    all_action_items = []

    for result in successful:
        topic_data = result.get("algorithms", {}).get("topic_extraction", {}).get("output", {})
        if topic_data:
            all_topics.extend(topic_data.get("topics", []))
            all_techniques.append(topic_data.get("technique"))
            all_action_items.extend(topic_data.get("action_items", []))

    if all_techniques:
        technique_freq = {tech: all_techniques.count(tech) for tech in set(all_techniques)}
        summary["statistics"]["topic_extraction"] = {
            "total_topics": len(all_topics),
            "unique_topics": len(set(all_topics)),
            "total_action_items": len(all_action_items),
            "technique_frequency": dict(sorted(technique_freq.items(), key=lambda x: x[1], reverse=True)),
            "most_common_technique": max(technique_freq.items(), key=lambda x: x[1])[0]
        }

    # === BREAKTHROUGH DETECTION STATISTICS ===
    sessions_with_breakthroughs = 0
    total_breakthroughs = 0
    breakthrough_types = []

    for result in successful:
        bt_data = result.get("algorithms", {}).get("breakthrough_detection", {}).get("output", {})
        if bt_data:
            if bt_data.get("has_breakthrough"):
                sessions_with_breakthroughs += 1
                total_breakthroughs += bt_data.get("breakthrough_count", 0)

                for bt in bt_data.get("all_breakthroughs", []):
                    breakthrough_types.append(bt.get("type"))

    if breakthrough_types:
        bt_type_freq = {bt_type: breakthrough_types.count(bt_type) for bt_type in set(breakthrough_types)}
        summary["statistics"]["breakthrough_detection"] = {
            "sessions_with_breakthroughs": sessions_with_breakthroughs,
            "breakthrough_rate": round(sessions_with_breakthroughs / len(successful) * 100, 1),
            "total_breakthroughs": total_breakthroughs,
            "avg_breakthroughs_per_session": round(total_breakthroughs / len(successful), 2),
            "breakthrough_type_frequency": dict(sorted(bt_type_freq.items(), key=lambda x: x[1], reverse=True))
        }

    # === COST BREAKDOWN ===
    # Estimated costs based on GPT-5 pricing
    # GPT-5-mini: $0.25/1M input, $2/1M output
    # GPT-5: $1.25/1M input, $10/1M output

    # Rough estimates per session:
    mood_cost = 0.01  # ~10k tokens @ gpt-5-mini
    topic_cost = 0.01  # ~10k tokens @ gpt-5-mini
    breakthrough_cost = 0.05  # ~10k tokens @ gpt-5 (more expensive)

    cost_per_session = mood_cost + topic_cost + breakthrough_cost
    total_cost = cost_per_session * len(successful)

    summary["cost_breakdown"] = {
        "model_pricing": {
            "gpt-5-mini": "$0.25/1M input, $2/1M output",
            "gpt-5": "$1.25/1M input, $10/1M output"
        },
        "estimated_cost_per_algorithm": {
            "mood_analysis": f"${mood_cost:.2f}",
            "topic_extraction": f"${topic_cost:.2f}",
            "breakthrough_detection": f"${breakthrough_cost:.2f}"
        },
        "cost_per_session": f"${cost_per_session:.2f}",
        "total_sessions_processed": len(successful),
        "estimated_total_cost": f"${total_cost:.2f}"
    }

    # === COMPARATIVE ANALYTICS ===
    summary["comparative_analytics"] = {
        "session_progression": {
            "mood_scores_timeline": mood_scores,
            "breakthrough_timeline": [
                result.get("algorithms", {}).get("breakthrough_detection", {}).get("output", {}).get("has_breakthrough", False)
                for result in successful
            ]
        },
        "key_insights": [
            f"Average mood score: {summary['statistics']['mood_analysis']['average_mood_score']}/10.0",
            f"Most common technique: {summary['statistics']['topic_extraction']['most_common_technique']}",
            f"Breakthrough rate: {summary['statistics']['breakthrough_detection']['breakthrough_rate']}%",
            f"Total estimated cost: {summary['cost_breakdown']['estimated_total_cost']}"
        ]
    }

    return summary


def main():
    """Main batch processing function"""
    print("="*80)
    print("BATCH PROCESSING ALL MOCK THERAPY SESSIONS".center(80))
    print("="*80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Find all session files
    sessions_dir = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions"
    session_files = sorted(sessions_dir.glob("session_*.json"))

    print(f"\nFound {len(session_files)} sessions to process")
    print(f"Output Directory: {sessions_dir.parent}")

    # Process each session
    all_results = []
    successful_sessions = 0
    failed_sessions = 0

    for i, session_file in enumerate(session_files, 1):
        try:
            result = process_single_session(session_file, i, len(session_files))
            all_results.append(result)

            # Save individual session output
            output_file = sessions_dir.parent / f"{session_file.stem}_all_algorithms_output.json"
            with open(output_file, 'w') as f:
                json.dump(result, f, indent=2, default=serialize_datetime)

            if result["success"]:
                successful_sessions += 1
            else:
                failed_sessions += 1

        except Exception as e:
            print(f"\n  ✗ FATAL ERROR processing {session_file.name}: {e}")
            failed_sessions += 1
            all_results.append({
                "session_file": session_file.name,
                "success": False,
                "error": str(e),
                "processed_at": datetime.utcnow().isoformat()
            })

    # Generate summary report
    summary = generate_summary_report(all_results)

    # Save summary report
    summary_file = sessions_dir.parent / "all_sessions_summary_report.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2, default=serialize_datetime)

    print(f"\n✓ Summary report saved: {summary_file.name}")
    print(f"\nKey Insights:")
    for insight in summary.get("comparative_analytics", {}).get("key_insights", []):
        print(f"  • {insight}")

    # Print final summary
    print("\n" + "="*80)
    print("BATCH PROCESSING COMPLETE".center(80))
    print("="*80)
    print(f"Total Sessions: {len(session_files)}")
    print(f"Successful: {successful_sessions}")
    print(f"Failed: {failed_sessions}")
    print(f"Success Rate: {successful_sessions/len(session_files)*100:.1f}%")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return all_results


if __name__ == "__main__":
    results = main()
