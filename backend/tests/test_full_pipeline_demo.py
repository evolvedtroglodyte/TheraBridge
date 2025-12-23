"""
Full Pipeline Demo - Run complete AI analysis on Sessions 10, 11, 12

Demonstrates:
- Wave 1: Mood analysis, topic extraction, breakthrough detection (parallel)
- Wave 2: Deep clinical analysis (uses previous sessions as context)

Outputs:
- Detailed terminal output
- Comprehensive JSON report (auto-opened)
"""

import os
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import subprocess
import platform
import asyncio

# Load environment variables
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.mood_analyzer import MoodAnalyzer
from app.services.topic_extractor import TopicExtractor
from app.services.breakthrough_detector import BreakthroughDetector
from app.services.deep_analyzer import DeepAnalyzer


def load_session(session_number: int) -> Dict[str, Any]:
    """Load a session JSON file"""
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


def open_file_automatically(filepath: str):
    """Open file using system default application"""
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", filepath], check=True)
        elif system == "Windows":
            os.startfile(filepath)
        elif system == "Linux":
            subprocess.run(["xdg-open", filepath], check=True)
        else:
            print(f"⚠️  Cannot auto-open on {system}. File saved to: {filepath}")
    except Exception as e:
        print(f"⚠️  Could not auto-open file: {e}")
        print(f"📄 File saved to: {filepath}")


class MockSessionDatabase:
    """
    In-memory mock database for session history.
    Simulates the database queries that deep_analyzer.py makes.
    """

    def __init__(self):
        self.sessions = {}  # session_id -> session data
        self.patient_id = "patient_alex_chen_demo"

    def add_session(self, session_num: int, session_data: Dict[str, Any], wave1_results: Dict[str, Any]):
        """Add a session with its Wave 1 analysis results"""
        session_id = f"session_{session_num:02d}"

        # Simulate database schema
        self.sessions[session_id] = {
            "id": session_id,
            "patient_id": self.patient_id,
            "session_date": (datetime(2025, 1, 10) + timedelta(weeks=session_num-1)).isoformat(),
            "transcript": session_data.get("segments", []),

            # Wave 1 results
            "mood_score": wave1_results.get("mood_score"),
            "mood_confidence": wave1_results.get("mood_confidence"),
            "mood_rationale": wave1_results.get("mood_rationale"),
            "mood_indicators": wave1_results.get("mood_indicators", []),
            "emotional_tone": wave1_results.get("emotional_tone"),

            "topics": wave1_results.get("topics", []),
            "action_items": wave1_results.get("action_items", []),
            "technique": wave1_results.get("technique"),
            "summary": wave1_results.get("summary"),
            "extraction_confidence": wave1_results.get("extraction_confidence"),

            "has_breakthrough": wave1_results.get("has_breakthrough", False),
            "breakthrough_data": wave1_results.get("breakthrough_data"),

            # Timestamps
            "mood_analyzed_at": datetime.utcnow().isoformat(),
            "topics_extracted_at": datetime.utcnow().isoformat(),
            "breakthrough_analyzed_at": datetime.utcnow().isoformat(),
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        return self.sessions.get(session_id)

    def get_previous_sessions(self, current_session_num: int, limit: int = 2) -> List[Dict[str, Any]]:
        """Get previous sessions for context"""
        previous = []
        for i in range(max(1, current_session_num - limit), current_session_num):
            session_id = f"session_{i:02d}"
            if session_id in self.sessions:
                previous.append(self.sessions[session_id])
        return previous


def run_wave1_analysis(session_num: int, session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run Wave 1 analyses: mood, topics, breakthrough (parallel simulation)

    Args:
        session_num: Session number (1-12)
        session_data: Loaded session JSON

    Returns:
        Dictionary with all Wave 1 results
    """
    print(f"\n{'=' * 80}")
    print(f"WAVE 1 ANALYSIS - SESSION {session_num}")
    print(f"{'=' * 80}")

    session_id = f"session_{session_num:02d}"
    segments = session_data.get("segments", [])

    results = {
        "session_id": session_id,
        "session_num": session_num,
    }

    # 1. Mood Analysis
    print(f"\n📊 Running Mood Analysis...")
    try:
        mood_analyzer = MoodAnalyzer()
        mood_analysis = mood_analyzer.analyze_session_mood(
            session_id=session_id,
            segments=segments,
            patient_speaker_id="SPEAKER_01"
        )

        results["mood_score"] = mood_analysis.mood_score
        results["mood_confidence"] = mood_analysis.confidence
        results["mood_rationale"] = mood_analysis.rationale
        results["mood_indicators"] = mood_analysis.key_indicators
        results["emotional_tone"] = mood_analysis.emotional_tone

        print(f"   ✓ Mood Score: {mood_analysis.mood_score}/10.0")
        print(f"   ✓ Confidence: {mood_analysis.confidence:.2f}")
        print(f"   ✓ Emotional Tone: {mood_analysis.emotional_tone}")
        print(f"   ✓ Key Indicators: {', '.join(mood_analysis.key_indicators[:3])}")

    except Exception as e:
        print(f"   ❌ Mood Analysis Failed: {e}")
        results["mood_error"] = str(e)

    # 2. Topic Extraction
    print(f"\n📝 Running Topic Extraction...")
    try:
        topic_extractor = TopicExtractor()
        metadata = topic_extractor.extract_metadata(
            session_id=session_id,
            segments=segments
        )

        results["topics"] = metadata.topics
        results["action_items"] = metadata.action_items
        results["technique"] = metadata.technique
        results["summary"] = metadata.summary
        results["extraction_confidence"] = metadata.confidence

        print(f"   ✓ Topics: {', '.join(metadata.topics)}")
        print(f"   ✓ Technique: {metadata.technique}")
        print(f"   ✓ Action Items: {', '.join(metadata.action_items)}")
        print(f"   ✓ Summary: {metadata.summary[:100]}...")

    except Exception as e:
        print(f"   ❌ Topic Extraction Failed: {e}")
        results["topics_error"] = str(e)

    # 3. Breakthrough Detection
    print(f"\n⭐ Running Breakthrough Detection...")
    try:
        breakthrough_detector = BreakthroughDetector()
        bt_analysis = breakthrough_detector.analyze_session(
            transcript=segments,
            session_metadata={"session_id": session_id}
        )

        results["has_breakthrough"] = bt_analysis.has_breakthrough
        results["breakthrough_data"] = None

        if bt_analysis.primary_breakthrough:
            bt = bt_analysis.primary_breakthrough
            results["breakthrough_data"] = {
                "type": bt.breakthrough_type,
                "label": bt.label,
                "description": bt.description,
                "evidence": bt.evidence,
                "confidence": float(bt.confidence_score),
                "timestamp_start": float(bt.timestamp_start),
                "timestamp_end": float(bt.timestamp_end),
            }

            print(f"   ✓ Breakthrough Detected: {bt.label}")
            print(f"   ✓ Type: {bt.breakthrough_type}")
            print(f"   ✓ Confidence: {bt.confidence_score:.2f}")
            print(f"   ✓ Description: {bt.description[:100]}...")
        else:
            print(f"   ✓ No breakthrough detected (as expected for most sessions)")

    except Exception as e:
        print(f"   ❌ Breakthrough Detection Failed: {e}")
        results["breakthrough_error"] = str(e)

    print(f"\n{'=' * 80}")
    print(f"WAVE 1 COMPLETE - SESSION {session_num}")
    print(f"{'=' * 80}")

    return results


def run_wave1_analysis_silent(session_num: int, session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run Wave 1 analysis without terminal output (for context building)
    """
    session_id = f"session_{session_num:02d}"
    segments = session_data.get("segments", [])

    results = {"session_id": session_id, "session_num": session_num}

    try:
        mood_analyzer = MoodAnalyzer()
        mood_analysis = mood_analyzer.analyze_session_mood(
            session_id=session_id,
            segments=segments,
            patient_speaker_id="SPEAKER_01"
        )
        results.update({
            "mood_score": mood_analysis.mood_score,
            "mood_confidence": mood_analysis.confidence,
            "mood_rationale": mood_analysis.rationale,
            "mood_indicators": mood_analysis.key_indicators,
            "emotional_tone": mood_analysis.emotional_tone,
        })
    except Exception as e:
        results["mood_error"] = str(e)

    try:
        topic_extractor = TopicExtractor()
        metadata = topic_extractor.extract_metadata(session_id=session_id, segments=segments)
        results.update({
            "topics": metadata.topics,
            "action_items": metadata.action_items,
            "technique": metadata.technique,
            "summary": metadata.summary,
            "extraction_confidence": metadata.confidence,
        })
    except Exception as e:
        results["topics_error"] = str(e)

    try:
        breakthrough_detector = BreakthroughDetector()
        bt_analysis = breakthrough_detector.analyze_session(
            transcript=segments,
            session_metadata={"session_id": session_id}
        )
        results["has_breakthrough"] = bt_analysis.has_breakthrough
        results["breakthrough_data"] = None
        if bt_analysis.primary_breakthrough:
            bt = bt_analysis.primary_breakthrough
            results["breakthrough_data"] = {
                "type": bt.breakthrough_type,
                "label": bt.label,
                "description": bt.description,
                "evidence": bt.evidence,
                "confidence": float(bt.confidence_score),
                "timestamp_start": float(bt.timestamp_start),
                "timestamp_end": float(bt.timestamp_end),
            }
    except Exception as e:
        results["breakthrough_error"] = str(e)

    return results


async def run_wave2_analysis(
    session_num: int,
    session_data: Dict[str, Any],
    wave1_results: Dict[str, Any],
    mock_db: MockSessionDatabase
) -> Dict[str, Any]:
    """
    Run Wave 2 deep analysis with session history context

    Args:
        session_num: Current session number
        session_data: Raw session JSON
        wave1_results: Wave 1 analysis results
        mock_db: Mock database with previous sessions

    Returns:
        Deep analysis results
    """
    print(f"\n{'=' * 80}")
    print(f"WAVE 2 ANALYSIS - SESSION {session_num}")
    print(f"{'=' * 80}")

    session_id = f"session_{session_num:02d}"

    # Get previous sessions for context
    previous_sessions = mock_db.get_previous_sessions(session_num, limit=2)

    print(f"\n🧠 Running Deep Clinical Analysis...")
    print(f"   Context: Using {len(previous_sessions)} previous session(s) as history")

    if previous_sessions:
        for i, prev in enumerate(previous_sessions, 1):
            print(f"      - Session {prev['id']}: Mood {prev.get('mood_score', 'N/A')}/10, Topics: {', '.join(prev.get('topics', []))}")

    try:
        # Build session context for deep analyzer
        session_context = {
            "session_id": session_id,
            "patient_id": mock_db.patient_id,
            "session_date": mock_db.sessions[session_id]["session_date"],
            "transcript": session_data.get("segments", []),

            # Wave 1 results
            "mood_score": wave1_results.get("mood_score"),
            "mood_indicators": wave1_results.get("mood_indicators", []),
            "emotional_tone": wave1_results.get("emotional_tone"),
            "topics": wave1_results.get("topics", []),
            "action_items": wave1_results.get("action_items", []),
            "technique": wave1_results.get("technique"),
            "summary": wave1_results.get("summary"),
            "breakthrough_data": wave1_results.get("breakthrough_data"),
        }

        # Create deep analyzer with None for DB (we'll mock it)
        deep_analyzer = DeepAnalyzer(db=None)

        # Mock the database methods to return our previous sessions
        from unittest.mock import MagicMock

        mock_db_client = MagicMock()

        # Mock _get_previous_sessions
        async def mock_get_previous_sessions(patient_id, current_session_id, limit=5):
            return previous_sessions

        # Mock _get_mood_trend
        async def mock_get_mood_trend(patient_id, days=90):
            if not previous_sessions:
                return {}
            recent_moods = [s.get("mood_score") for s in previous_sessions if s.get("mood_score")]
            if recent_moods:
                return {
                    "trend": "improving" if len(recent_moods) > 1 and recent_moods[-1] > recent_moods[0] else "stable",
                    "recent_avg": sum(recent_moods) / len(recent_moods),
                    "historical_avg": sum(recent_moods) / len(recent_moods),
                }
            return {}

        # Mock _get_recurring_topics
        async def mock_get_recurring_topics(patient_id):
            topic_counts = {}
            for s in previous_sessions:
                for topic in s.get("topics", []):
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            return [{"topic": t, "frequency": c} for t, c in topic_counts.items()]

        # Mock _get_technique_history
        async def mock_get_technique_history(patient_id):
            technique_counts = {}
            for s in previous_sessions:
                tech = s.get("technique")
                if tech:
                    technique_counts[tech] = technique_counts.get(tech, 0) + 1
            return [{"technique": t, "usage_count": c} for t, c in technique_counts.items()]

        # Mock _get_breakthrough_history
        async def mock_get_breakthrough_history(patient_id):
            return []

        # Replace the methods
        deep_analyzer._get_previous_sessions = mock_get_previous_sessions
        deep_analyzer._get_mood_trend = mock_get_mood_trend
        deep_analyzer._get_recurring_topics = mock_get_recurring_topics
        deep_analyzer._get_technique_history = mock_get_technique_history
        deep_analyzer._get_breakthrough_history = mock_get_breakthrough_history

        # Run analysis
        analysis = await deep_analyzer.analyze_session(session_id, session_context)

        # Display results
        print(f"\n   ✓ Deep Analysis Complete")
        print(f"   ✓ Confidence: {analysis.confidence_score:.2f}")

        # Progress Indicators
        print(f"\n   📈 Progress Indicators:")
        if analysis.progress_indicators.symptom_reduction:
            print(f"      - Symptom Reduction: {analysis.progress_indicators.symptom_reduction.get('description', 'N/A')[:80]}...")
        print(f"      - Skills Developed: {len(analysis.progress_indicators.skill_development)}")
        print(f"      - Goals Tracked: {len(analysis.progress_indicators.goal_progress)}")

        # Key Insights
        print(f"\n   💡 Therapeutic Insights:")
        for insight in analysis.therapeutic_insights.key_realizations[:2]:
            print(f"      - {insight[:80]}...")

        # Coping Skills
        print(f"\n   🛠️  Coping Skills:")
        for skill in analysis.coping_skills.learned[:3]:
            proficiency = analysis.coping_skills.proficiency.get(skill, "N/A")
            print(f"      - {skill}: {proficiency}")

        # Therapeutic Relationship
        print(f"\n   🤝 Therapeutic Relationship:")
        print(f"      - Engagement: {analysis.therapeutic_relationship.engagement_level}")
        print(f"      - Openness: {analysis.therapeutic_relationship.openness}")
        print(f"      - Alliance: {analysis.therapeutic_relationship.alliance_strength}")

        # Recommendations
        print(f"\n   ✅ Recommendations:")
        for rec in analysis.recommendations.practices[:2]:
            print(f"      - {rec[:80]}...")

        return {
            "session_id": session_id,
            "deep_analysis": analysis.to_dict(),
            "confidence_score": analysis.confidence_score,
        }

    except Exception as e:
        print(f"   ❌ Deep Analysis Failed: {e}")
        import traceback
        traceback.print_exc()
        return {
            "session_id": session_id,
            "deep_error": str(e)
        }


async def main():
    """
    Main execution: Run full pipeline on Sessions 10, 11, 12
    """
    print("=" * 80)
    print("FULL AI ANALYSIS PIPELINE DEMO")
    print("Sessions 10, 11, 12 (Coming Out Aftermath → Rebuilding → Thriving)")
    print("=" * 80)
    print()

    # Initialize mock database
    mock_db = MockSessionDatabase()

    # Store all results
    all_results = {
        "demo_info": {
            "timestamp": datetime.utcnow().isoformat(),
            "sessions_analyzed": [10, 11, 12],
            "pipeline_version": "Wave 1 + Wave 2 (Full Orchestration)",
        },
        "sessions": []
    }

    # Process Sessions 8-9 only (for immediate context, skip 1-7 for speed)
    print("📚 Loading context sessions (8-9) for history...")
    for session_num in [8, 9]:
        session_data = load_session(session_num)

        # Run Wave 1 only (no output)
        print(f"   Processing Session {session_num}...")
        wave1_results = run_wave1_analysis_silent(session_num, session_data)

        # Add to mock database
        mock_db.add_session(session_num, session_data, wave1_results)

        print(f"   ✓ Session {session_num} loaded")

    print(f"\n✅ Context built: 2 previous sessions loaded\n")

    # Process Sessions 10, 11, 12 (full analysis with output)
    target_sessions = [10, 11, 12]

    for session_num in target_sessions:
        print(f"\n{'#' * 80}")
        print(f"SESSION {session_num} - FULL PIPELINE")
        print(f"{'#' * 80}")

        # Load session
        session_data = load_session(session_num)
        print(f"\n📄 Loaded: {session_data.get('id', 'Unknown')}")
        print(f"   Segments: {len(session_data.get('segments', []))}")

        # Wave 1
        wave1_results = run_wave1_analysis(session_num, session_data)

        # Add to mock database
        mock_db.add_session(session_num, session_data, wave1_results)

        # Wave 2
        wave2_results = await run_wave2_analysis(
            session_num,
            session_data,
            wave1_results,
            mock_db
        )

        # Combine results
        session_result = {
            "session_num": session_num,
            "session_id": session_data.get("id"),
            "wave1": wave1_results,
            "wave2": wave2_results,
        }

        all_results["sessions"].append(session_result)

    # Save to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent.parent.parent / "mock-therapy-data"
    output_file = output_dir / f"full_pipeline_demo_{timestamp}.json"

    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2)

    print(f"\n{'=' * 80}")
    print("DEMO COMPLETE")
    print(f"{'=' * 80}")
    print(f"\n✅ All sessions analyzed successfully")
    print(f"📄 Results saved to: {output_file}")
    print(f"\n🚀 Auto-opening results file...\n")

    # Auto-open the JSON file
    open_file_automatically(str(output_file))

    return all_results


if __name__ == "__main__":
    asyncio.run(main())
