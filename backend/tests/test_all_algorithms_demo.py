"""
Demo Script: All Therapy Analysis Algorithms on Session 03

Demonstrates all AI-powered analysis algorithms on a single therapy session:
1. Mood Analysis - Extract patient mood score and emotional tone
2. Topic Extraction - Extract topics, action items, technique, and summary
3. Breakthrough Detection - Identify therapeutic breakthroughs
4. Deep Analysis - Comprehensive clinical insights synthesis

Outputs: Terminal display + JSON file
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.services.mood_analyzer import MoodAnalyzer
from app.services.topic_extractor import TopicExtractor
from app.services.breakthrough_detector import BreakthroughDetector
# Deep analyzer requires async and database connection - skip for this demo


def load_session_data(session_file: str) -> dict:
    """Load session transcript data from JSON file"""
    session_path = backend_dir.parent / "mock-therapy-data" / "sessions" / session_file
    with open(session_path, 'r') as f:
        return json.load(f)


def print_section_header(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_subsection(title: str):
    """Print formatted subsection"""
    print(f"\n--- {title} ---")


def run_mood_analysis(session_data: dict) -> dict:
    """Run mood analysis algorithm"""
    print_section_header("ALGORITHM 1: MOOD ANALYSIS")

    analyzer = MoodAnalyzer(model="gpt-4o-mini")  # Using current default

    result = analyzer.analyze_session_mood(
        session_id=session_data["id"],
        segments=session_data["segments"],
        patient_speaker_id="SPEAKER_01"
    )

    # Display results
    print(f"Session ID: {result.session_id}")
    print(f"Mood Score: {result.mood_score}/10.0")
    print(f"Confidence: {result.confidence:.2%}")
    print(f"Emotional Tone: {result.emotional_tone}")
    print(f"\nRationale:")
    print(f"  {result.rationale}")
    print(f"\nKey Indicators:")
    for indicator in result.key_indicators:
        print(f"  • {indicator}")
    print(f"\nAnalyzed At: {result.analyzed_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # Return as dict for JSON export
    return {
        "session_id": result.session_id,
        "mood_score": result.mood_score,
        "confidence": result.confidence,
        "emotional_tone": result.emotional_tone,
        "rationale": result.rationale,
        "key_indicators": result.key_indicators,
        "analyzed_at": result.analyzed_at.isoformat()
    }


def run_topic_extraction(session_data: dict) -> dict:
    """Run topic extraction algorithm"""
    print_section_header("ALGORITHM 2: TOPIC EXTRACTION")

    extractor = TopicExtractor(model="gpt-4o-mini")  # Using current default

    result = extractor.extract_metadata(
        session_id=session_data["id"],
        segments=session_data["segments"]
    )

    # Display results
    print(f"Session ID: {result.session_id}")
    print(f"Confidence: {result.confidence:.2%}")

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
    print(f"  ({len(result.summary)} characters)")

    print(f"\nExtracted At: {result.extracted_at.strftime('%Y-%m-%d %H:%M:%S')}")

    # Return as dict for JSON export
    return {
        "session_id": result.session_id,
        "topics": result.topics,
        "action_items": result.action_items,
        "technique": result.technique,
        "summary": result.summary,
        "confidence": result.confidence,
        "raw_meta_summary": result.raw_meta_summary,
        "extracted_at": result.extracted_at.isoformat()
    }


def run_breakthrough_detection(session_data: dict) -> dict:
    """Run breakthrough detection algorithm"""
    print_section_header("ALGORITHM 3: BREAKTHROUGH DETECTION")

    detector = BreakthroughDetector(model="gpt-4o")  # Using GPT-4o for complex reasoning

    result = detector.analyze_session(
        transcript=session_data["segments"],
        session_metadata={"session_id": session_data["id"]}
    )

    # Display results
    print(f"Session ID: {result.session_id}")
    print(f"Has Breakthrough: {result.has_breakthrough}")
    print(f"Breakthrough Count: {len(result.breakthrough_candidates)}")

    if result.primary_breakthrough:
        bt = result.primary_breakthrough
        print_subsection("Primary Breakthrough")
        print(f"  Label: {bt.label}")
        print(f"  Type: {bt.breakthrough_type}")
        print(f"  Confidence: {bt.confidence_score:.2%}")
        print(f"  Timestamp: {int(bt.timestamp_start // 60):02d}:{int(bt.timestamp_start % 60):02d} - {int(bt.timestamp_end // 60):02d}:{int(bt.timestamp_end % 60):02d}")
        print(f"\n  Description:")
        print(f"    {bt.description}")
        print(f"\n  Evidence:")
        print(f"    {bt.evidence}")
    else:
        print("  No breakthrough detected in this session.")

    print_subsection("Session Summary")
    print(f"  {result.session_summary}")

    print_subsection("Emotional Trajectory")
    print(f"  {result.emotional_trajectory}")

    # Return as dict for JSON export
    return {
        "session_id": result.session_id,
        "has_breakthrough": result.has_breakthrough,
        "breakthrough_count": len(result.breakthrough_candidates),
        "primary_breakthrough": {
            "label": result.primary_breakthrough.label,
            "type": result.primary_breakthrough.breakthrough_type,
            "confidence": result.primary_breakthrough.confidence_score,
            "timestamp_start": result.primary_breakthrough.timestamp_start,
            "timestamp_end": result.primary_breakthrough.timestamp_end,
            "description": result.primary_breakthrough.description,
            "evidence": result.primary_breakthrough.evidence
        } if result.primary_breakthrough else None,
        "session_summary": result.session_summary,
        "emotional_trajectory": result.emotional_trajectory
    }


def save_results_to_json(all_results: dict, session_id: str):
    """Save all algorithm outputs to JSON file"""
    output_dir = backend_dir.parent / "mock-therapy-data"
    output_file = output_dir / f"{session_id}_all_algorithms_output.json"

    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print_section_header("OUTPUT SAVED")
    print(f"All algorithm outputs saved to:")
    print(f"  {output_file}")
    print(f"\nFile size: {output_file.stat().st_size:,} bytes")


def create_markdown_report(all_results: dict, session_id: str):
    """Create formatted markdown report"""
    output_dir = backend_dir.parent / "mock-therapy-data"
    output_file = output_dir / f"{session_id}_algorithm_report.md"

    with open(output_file, 'w') as f:
        f.write(f"# Therapy Session Analysis Report\n\n")
        f.write(f"**Session ID:** {session_id}\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

        # Mood Analysis
        f.write("## 1. Mood Analysis\n\n")
        mood = all_results["mood_analysis"]
        f.write(f"**Mood Score:** {mood['mood_score']}/10.0 (Confidence: {mood['confidence']:.1%})\n\n")
        f.write(f"**Emotional Tone:** {mood['emotional_tone']}\n\n")
        f.write(f"**Rationale:**\n{mood['rationale']}\n\n")
        f.write("**Key Indicators:**\n")
        for indicator in mood['key_indicators']:
            f.write(f"- {indicator}\n")
        f.write("\n---\n\n")

        # Topic Extraction
        f.write("## 2. Topic Extraction\n\n")
        topics = all_results["topic_extraction"]
        f.write(f"**Confidence:** {topics['confidence']:.1%}\n\n")
        f.write("**Topics:**\n")
        for i, topic in enumerate(topics['topics'], 1):
            f.write(f"{i}. {topic}\n")
        f.write("\n**Action Items:**\n")
        for i, item in enumerate(topics['action_items'], 1):
            f.write(f"{i}. {item}\n")
        f.write(f"\n**Therapeutic Technique:** {topics['technique']}\n\n")
        f.write(f"**Summary:** {topics['summary']}\n\n")
        f.write("---\n\n")

        # Breakthrough Detection
        f.write("## 3. Breakthrough Detection\n\n")
        breakthrough = all_results["breakthrough_detection"]
        f.write(f"**Has Breakthrough:** {breakthrough['has_breakthrough']}\n\n")

        if breakthrough['primary_breakthrough']:
            bt = breakthrough['primary_breakthrough']
            f.write(f"### Primary Breakthrough: {bt['label']}\n\n")
            f.write(f"**Type:** {bt['type']}\n")
            f.write(f"**Confidence:** {bt['confidence']:.1%}\n")
            timestamp_start = f"{int(bt['timestamp_start'] // 60):02d}:{int(bt['timestamp_start'] % 60):02d}"
            timestamp_end = f"{int(bt['timestamp_end'] // 60):02d}:{int(bt['timestamp_end'] % 60):02d}"
            f.write(f"**Timestamp:** {timestamp_start} - {timestamp_end}\n\n")
            f.write(f"**Description:**\n{bt['description']}\n\n")
            f.write(f"**Evidence:**\n{bt['evidence']}\n\n")
        else:
            f.write("*No breakthrough detected in this session.*\n\n")

        f.write(f"**Session Summary:** {breakthrough['session_summary']}\n\n")
        f.write(f"**Emotional Trajectory:** {breakthrough['emotional_trajectory']}\n\n")

    print(f"Markdown report saved to:")
    print(f"  {output_file}")


def main():
    """Main demo execution"""
    print_section_header("THERAPY SESSION ANALYSIS - ALL ALGORITHMS DEMO")
    print("Analyzing Session 03: ADHD Discovery")
    print("Patient: Alex Chen")
    print("Date: 2025-01-31")

    # Load session data
    print("\nLoading session data...")
    session_data = load_session_data("session_03_adhd_discovery.json")
    session_id = session_data["id"]
    print(f"✓ Loaded session: {session_id}")
    print(f"  Duration: {session_data['metadata']['duration']:.0f} seconds ({session_data['metadata']['duration']/60:.1f} minutes)")
    print(f"  Segments: {len(session_data['segments'])}")

    # Initialize results container
    all_results = {
        "session_id": session_id,
        "session_metadata": session_data["metadata"],
        "analyzed_at": datetime.now().isoformat(),
        "mood_analysis": None,
        "topic_extraction": None,
        "breakthrough_detection": None
    }

    try:
        # Run Algorithm 1: Mood Analysis
        all_results["mood_analysis"] = run_mood_analysis(session_data)

        # Run Algorithm 2: Topic Extraction
        all_results["topic_extraction"] = run_topic_extraction(session_data)

        # Run Algorithm 3: Breakthrough Detection
        all_results["breakthrough_detection"] = run_breakthrough_detection(session_data)

        # Save outputs
        save_results_to_json(all_results, session_id)
        create_markdown_report(all_results, session_id)

        print_section_header("DEMO COMPLETE ✓")
        print("All algorithms executed successfully!")
        print("\nNote: Deep Analysis (Algorithm 4) requires database connection")
        print("      and is part of the orchestrated pipeline. See analysis_orchestrator.py")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
