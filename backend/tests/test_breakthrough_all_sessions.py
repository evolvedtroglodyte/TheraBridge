"""
Test breakthrough detection on all 12 mock therapy sessions.

This script analyzes each session to identify breakthrough moments and saves
a comprehensive report to understand the current behavior of the algorithm.

Expected behavior (desired):
- Only 2-3 sessions should have breakthroughs
- Each session should have at most 1 breakthrough
- Breakthroughs should be genuine insights (like ADHD discovery)
- Not every session should be marked as a breakthrough

Current behavior (to be determined):
- This test will reveal if the algorithm is detecting too many breakthroughs
"""

import os
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.breakthrough_detector import BreakthroughDetector


def load_session(session_number: int) -> dict:
    """Load a session JSON file"""
    # Map session numbers to file names
    session_files = {
        1: "session_01_crisis_intake.json",
        2: "session_02_emotional_regulation.json",
        3: "session_03_adhd_discovery.json",
        4: "session_04_medication_start.json",
        5: "session_05_family_conflict.json",
        6: "session_06_spring_break_hope.json",
        7: "session_07_dating_anxiety.json",
        8: "session_08_relationship_boundaries.json",
        9: "session_09_coming_out_preparation.json",
        10: "session_10_coming_out_aftermath.json",
        11: "session_11_rebuilding.json",
        12: "session_12_thriving.json",
    }

    data_dir = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions"
    filepath = data_dir / session_files[session_number]

    with open(filepath, 'r') as f:
        return json.load(f)


def main():
    """Test breakthrough detection on all 12 mock sessions"""

    print("=" * 80)
    print("BREAKTHROUGH DETECTION - ALL SESSIONS TEST")
    print("=" * 80)
    print()

    # Initialize detector
    detector = BreakthroughDetector()

    # Store results
    all_results = []
    breakthrough_count = 0

    # Test each session
    for session_num in range(1, 13):
        print(f"\n{'=' * 80}")
        print(f"SESSION {session_num}")
        print(f"{'=' * 80}")

        # Load session
        session_data = load_session(session_num)
        transcript = session_data.get("segments", [])

        print(f"Session ID: {session_data.get('id', 'Unknown')}")
        print(f"Transcript segments: {len(transcript)}")

        # Run breakthrough detection
        try:
            analysis = detector.analyze_session(
                transcript=transcript,
                session_metadata={"session_id": f"session_{session_num:02d}"}
            )

            # Display results
            print(f"\n📊 RESULTS:")
            print(f"Has breakthrough: {analysis.has_breakthrough}")
            print(f"Number of breakthrough candidates: {len(analysis.breakthrough_candidates)}")

            if analysis.primary_breakthrough:
                breakthrough_count += 1
                print(f"\n⭐ PRIMARY BREAKTHROUGH:")
                print(f"  Label: {analysis.primary_breakthrough.label}")  # NEW
                print(f"  Type: {analysis.primary_breakthrough.breakthrough_type}")
                print(f"  Description: {analysis.primary_breakthrough.description}")
                print(f"  Confidence: {analysis.primary_breakthrough.confidence_score:.2f}")
                print(f"  Evidence: {analysis.primary_breakthrough.evidence}")

                # Show timestamp
                minutes = int(analysis.primary_breakthrough.timestamp_start // 60)
                seconds = int(analysis.primary_breakthrough.timestamp_start % 60)
                print(f"  Timestamp: {minutes:02d}:{seconds:02d}")

            # Show all breakthrough candidates
            if len(analysis.breakthrough_candidates) > 1:
                print(f"\n📝 ALL BREAKTHROUGH CANDIDATES ({len(analysis.breakthrough_candidates)}):")
                for i, bt in enumerate(analysis.breakthrough_candidates, 1):
                    print(f"\n  {i}. {bt.breakthrough_type} (confidence: {bt.confidence_score:.2f})")
                    print(f"     {bt.description}")

            # Store for report
            all_results.append({
                "session_num": session_num,
                "session_id": session_data.get("id", "Unknown"),
                "has_breakthrough": analysis.has_breakthrough,
                "breakthrough_count": len(analysis.breakthrough_candidates),
                "primary_breakthrough": {
                    "type": analysis.primary_breakthrough.breakthrough_type,
                    "label": analysis.primary_breakthrough.label,  # NEW
                    "description": analysis.primary_breakthrough.description,
                    "confidence": float(analysis.primary_breakthrough.confidence_score),
                    "evidence": analysis.primary_breakthrough.evidence,
                } if analysis.primary_breakthrough else None,
                "all_breakthroughs": [
                    {
                        "type": bt.breakthrough_type,
                        "label": bt.label,  # NEW
                        "description": bt.description,
                        "confidence": float(bt.confidence_score),
                        "evidence": bt.evidence,
                    }
                    for bt in analysis.breakthrough_candidates
                ],
                "session_summary": analysis.session_summary,
                "emotional_trajectory": analysis.emotional_trajectory,
            })

        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            all_results.append({
                "session_num": session_num,
                "session_id": session_data.get("id", "Unknown"),
                "error": str(e),
            })

    # Final summary
    print(f"\n\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total sessions analyzed: 12")
    print(f"Sessions with breakthroughs: {breakthrough_count}")
    print(f"Breakthrough rate: {breakthrough_count / 12 * 100:.1f}%")
    print()

    # Determine if behavior matches expectation
    if breakthrough_count <= 3:
        print("✅ GOOD: Breakthrough count is within desired range (2-3 sessions)")
    elif breakthrough_count <= 6:
        print("⚠️ MODERATE: Breakthrough count is higher than desired (4-6 sessions)")
    else:
        print("❌ TOO HIGH: Breakthrough count is significantly higher than desired (7+ sessions)")

    print()
    print("Sessions with breakthroughs:")
    for result in all_results:
        if result.get("has_breakthrough"):
            bt = result.get("primary_breakthrough", {})
            print(f"  - Session {result['session_num']}: {result['session_id']}")
            print(f"    Type: {bt.get('type', 'N/A')}")
            print(f"    Label: {bt.get('label', 'N/A')}")  # NEW
            print(f"    Description: {bt.get('description', 'N/A')}")

    # Save results to file
    output_file = Path(__file__).parent.parent.parent / "mock-therapy-data" / "breakthrough_analysis_all_sessions.json"
    with open(output_file, 'w') as f:
        json.dump({
            "summary": {
                "total_sessions": 12,
                "breakthrough_count": breakthrough_count,
                "breakthrough_rate": f"{breakthrough_count / 12 * 100:.1f}%",
            },
            "results": all_results,
        }, f, indent=2)

    print(f"\n📄 Full results saved to: {output_file}")
    print()


if __name__ == "__main__":
    main()
