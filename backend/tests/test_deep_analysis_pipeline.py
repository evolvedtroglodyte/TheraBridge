"""
Test Deep Analysis Pipeline

This script tests the complete deep analysis pipeline on mock therapy sessions:
1. Wave 1: Mood analysis, topic extraction, breakthrough detection (parallel)
2. Wave 2: Deep clinical analysis (synthesizes Wave 1 + patient history)

Usage:
    python tests/test_deep_analysis_pipeline.py

Output:
    - Terminal display of deep analysis results
    - JSON file with all results
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.analysis_orchestrator import AnalysisOrchestrator
from app.database import get_db
from supabase import Client


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text: str):
    """Print colored header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.END}\n")


def print_section(title: str, content: Any, color=Colors.CYAN):
    """Print formatted section"""
    print(f"{color}{Colors.BOLD}{title}:{Colors.END}")
    if isinstance(content, list):
        for item in content:
            print(f"  • {item}")
    elif isinstance(content, dict):
        for key, value in content.items():
            print(f"  {key}: {value}")
    else:
        print(f"  {content}")
    print()


def print_progress_indicator(progress_indicators: Dict[str, Any]):
    """Pretty print progress indicators"""
    print_header("📊 PROGRESS INDICATORS")

    # Symptom reduction
    if progress_indicators.get("symptom_reduction"):
        sr = progress_indicators["symptom_reduction"]
        if sr.get("detected"):
            print(f"{Colors.GREEN}✓ Symptom Reduction Detected:{Colors.END}")
            print(f"  {sr.get('description', 'N/A')}")
            print(f"  Confidence: {sr.get('confidence', 0):.0%}\n")
        else:
            print(f"{Colors.YELLOW}○ No significant symptom reduction detected{Colors.END}\n")

    # Skill development
    skills = progress_indicators.get("skill_development", [])
    if skills:
        print(f"{Colors.CYAN}{Colors.BOLD}Skills Developed:{Colors.END}")
        for skill in skills:
            proficiency = skill.get("proficiency", "unknown")
            emoji = "🌱" if proficiency == "beginner" else "🌿" if proficiency == "developing" else "🌳"
            print(f"  {emoji} {skill.get('skill', 'Unknown')} ({proficiency})")
            print(f"     Evidence: {skill.get('evidence', 'N/A')}")
        print()

    # Goal progress
    goals = progress_indicators.get("goal_progress", [])
    if goals:
        print(f"{Colors.CYAN}{Colors.BOLD}Goal Progress:{Colors.END}")
        for goal in goals:
            status = goal.get("status", "unknown")
            emoji = "✅" if status == "achieved" else "🔄" if status == "on_track" else "⚠️"
            print(f"  {emoji} {goal.get('goal', 'Unknown')} ({status})")
            print(f"     Evidence: {goal.get('evidence', 'N/A')}")
        print()

    # Behavioral changes
    changes = progress_indicators.get("behavioral_changes", [])
    if changes:
        print(f"{Colors.CYAN}{Colors.BOLD}Behavioral Changes:{Colors.END}")
        for change in changes:
            print(f"  ✓ {change}")
        print()


def print_therapeutic_insights(insights: Dict[str, Any]):
    """Pretty print therapeutic insights"""
    print_header("🧠 THERAPEUTIC INSIGHTS")

    # Key realizations
    realizations = insights.get("key_realizations", [])
    if realizations:
        print(f"{Colors.YELLOW}{Colors.BOLD}Key Realizations:{Colors.END}")
        for realization in realizations:
            print(f"  💡 {realization}")
        print()

    # Patterns
    patterns = insights.get("patterns", [])
    if patterns:
        print(f"{Colors.YELLOW}{Colors.BOLD}Patterns Emerging:{Colors.END}")
        for pattern in patterns:
            print(f"  🔗 {pattern}")
        print()

    # Growth areas
    growth = insights.get("growth_areas", [])
    if growth:
        print(f"{Colors.GREEN}{Colors.BOLD}Growth Areas:{Colors.END}")
        for area in growth:
            print(f"  🌱 {area}")
        print()

    # Strengths
    strengths = insights.get("strengths", [])
    if strengths:
        print(f"{Colors.GREEN}{Colors.BOLD}Strengths Demonstrated:{Colors.END}")
        for strength in strengths:
            print(f"  💪 {strength}")
        print()


def print_coping_skills(skills: Dict[str, Any]):
    """Pretty print coping skills"""
    print_header("🛠️ COPING SKILLS DEVELOPMENT")

    # Skills learned
    learned = skills.get("learned", [])
    if learned:
        print(f"{Colors.CYAN}{Colors.BOLD}Skills Learned:{Colors.END}")
        for skill in learned:
            print(f"  📚 {skill}")
        print()

    # Proficiency levels
    proficiency = skills.get("proficiency", {})
    if proficiency:
        print(f"{Colors.CYAN}{Colors.BOLD}Proficiency Levels:{Colors.END}")
        for skill_name, level in proficiency.items():
            emoji = "🌱" if level == "beginner" else "🌿" if level == "developing" else "🌳"
            print(f"  {emoji} {skill_name}: {level}")
        print()

    # Practice recommendations
    recommendations = skills.get("practice_recommendations", [])
    if recommendations:
        print(f"{Colors.YELLOW}{Colors.BOLD}Practice Recommendations:{Colors.END}")
        for rec in recommendations:
            print(f"  → {rec}")
        print()


def print_therapeutic_relationship(relationship: Dict[str, Any]):
    """Pretty print therapeutic relationship assessment"""
    print_header("🤝 THERAPEUTIC RELATIONSHIP")

    # Engagement
    engagement = relationship.get("engagement_level", "moderate")
    emoji = "🔥" if engagement == "high" else "⚡" if engagement == "moderate" else "💤"
    print(f"{Colors.BLUE}{Colors.BOLD}Engagement:{Colors.END} {emoji} {engagement.upper()}")
    print(f"  Evidence: {relationship.get('engagement_evidence', 'N/A')}\n")

    # Openness
    openness = relationship.get("openness", "somewhat_open")
    emoji = "🌊" if openness == "very_open" else "🌤️" if openness == "somewhat_open" else "🛡️"
    print(f"{Colors.BLUE}{Colors.BOLD}Openness:{Colors.END} {emoji} {openness.replace('_', ' ').upper()}")
    print(f"  Evidence: {relationship.get('openness_evidence', 'N/A')}\n")

    # Alliance strength
    alliance = relationship.get("alliance_strength", "developing")
    emoji = "💎" if alliance == "strong" else "🌿" if alliance == "developing" else "🌱"
    print(f"{Colors.BLUE}{Colors.BOLD}Alliance Strength:{Colors.END} {emoji} {alliance.upper()}")
    print(f"  Evidence: {relationship.get('alliance_evidence', 'N/A')}\n")


def print_recommendations(recommendations: Dict[str, Any]):
    """Pretty print recommendations"""
    print_header("📝 RECOMMENDATIONS")

    # Practices
    practices = recommendations.get("practices", [])
    if practices:
        print(f"{Colors.YELLOW}{Colors.BOLD}Practices to Try:{Colors.END}")
        for practice in practices:
            print(f"  ✓ {practice}")
        print()

    # Resources
    resources = recommendations.get("resources", [])
    if resources:
        print(f"{Colors.CYAN}{Colors.BOLD}Resources:{Colors.END}")
        for resource in resources:
            print(f"  📖 {resource}")
        print()

    # Reflection prompts
    prompts = recommendations.get("reflection_prompts", [])
    if prompts:
        print(f"{Colors.CYAN}{Colors.BOLD}Reflection Prompts:{Colors.END}")
        for prompt in prompts:
            print(f"  💭 {prompt}")
        print()


async def load_mock_session_to_db(
    db: Client,
    session_file: Path,
    patient_id: str,
    therapist_id: str
) -> str:
    """
    Load mock session data into database for testing

    Args:
        db: Supabase client
        session_file: Path to mock session JSON file
        patient_id: Patient UUID
        therapist_id: Therapist UUID

    Returns:
        Session ID
    """
    # Load session data
    with open(session_file, 'r') as f:
        session_data = json.load(f)

    # Extract session date from filename (e.g., session_01_2025-01-10.mp3)
    filename = session_data.get("filename", "session_2025-01-01.mp3")
    date_str = filename.split("_")[-1].replace(".mp3", "")
    try:
        session_date = datetime.strptime(date_str, "%Y-%m-%d")
    except:
        session_date = datetime.now()

    # Create session record
    session_record = {
        "patient_id": patient_id,
        "therapist_id": therapist_id,
        "session_date": session_date.isoformat(),
        "duration_minutes": int(session_data.get("metadata", {}).get("duration", 3600) / 60),
        "transcript": session_data.get("segments", []),
        "processing_status": "completed",
        "analysis_status": "pending",
    }

    response = db.table("therapy_sessions").insert(session_record).execute()

    if not response.data:
        raise Exception("Failed to create session record")

    session_id = response.data[0]["id"]
    print(f"{Colors.GREEN}✓ Loaded session: {session_file.name} → {session_id}{Colors.END}")

    return session_id


async def test_single_session(
    orchestrator: AnalysisOrchestrator,
    session_id: str,
    session_name: str
):
    """
    Test full pipeline on a single session

    Args:
        orchestrator: AnalysisOrchestrator instance
        session_id: Session UUID
        session_name: Human-readable session name
    """
    print_header(f"TESTING SESSION: {session_name}")

    try:
        # Run full pipeline
        print(f"{Colors.CYAN}Running full analysis pipeline...{Colors.END}")
        status = await orchestrator.process_session_full_pipeline(session_id, force=True)

        # Get session with deep analysis
        session = await orchestrator._get_session(session_id)

        # Display results
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ Analysis Complete{Colors.END}")
        print(f"Status: {status.analysis_status}")
        print(f"Confidence: {session.get('analysis_confidence', 0):.0%}")

        # Extract deep analysis
        deep_analysis = session.get("deep_analysis")

        if not deep_analysis:
            print(f"{Colors.RED}❌ No deep analysis data found{Colors.END}")
            return None

        # Pretty print each section
        print_progress_indicator(deep_analysis.get("progress_indicators", {}))
        print_therapeutic_insights(deep_analysis.get("therapeutic_insights", {}))
        print_coping_skills(deep_analysis.get("coping_skills", {}))
        print_therapeutic_relationship(deep_analysis.get("therapeutic_relationship", {}))
        print_recommendations(deep_analysis.get("recommendations", {}))

        return {
            "session_id": session_id,
            "session_name": session_name,
            "status": status.analysis_status,
            "confidence": session.get("analysis_confidence"),
            "mood_score": session.get("mood_score"),
            "topics": session.get("topics"),
            "technique": session.get("technique"),
            "deep_analysis": deep_analysis,
        }

    except Exception as e:
        print(f"{Colors.RED}❌ Failed: {e}{Colors.END}")
        return None


async def main():
    """Main test function"""
    print_header("DEEP ANALYSIS PIPELINE TEST")

    # Initialize database connection
    db = next(get_db())
    orchestrator = AnalysisOrchestrator(db=db)

    # Test patient and therapist IDs (you may need to create these first)
    PATIENT_ID = "11111111-1111-1111-1111-111111111111"  # Replace with actual patient ID
    THERAPIST_ID = "22222222-2222-2222-2222-222222222222"  # Replace with actual therapist ID

    # Find all mock session files
    mock_sessions_dir = Path(__file__).parent.parent.parent / "mock-therapy-data" / "sessions"

    if not mock_sessions_dir.exists():
        print(f"{Colors.RED}❌ Mock sessions directory not found: {mock_sessions_dir}{Colors.END}")
        return

    session_files = sorted(mock_sessions_dir.glob("session_*.json"))

    if not session_files:
        print(f"{Colors.RED}❌ No mock session files found{Colors.END}")
        return

    print(f"{Colors.CYAN}Found {len(session_files)} mock sessions{Colors.END}\n")

    # Test configuration
    TEST_ALL = False  # Set to True to test all sessions, False to test just one
    TEST_SESSION_INDEX = 0  # Which session to test if TEST_ALL is False

    results = []

    if TEST_ALL:
        # Test all sessions
        for session_file in session_files:
            try:
                # Load session to database
                session_id = await load_mock_session_to_db(
                    db, session_file, PATIENT_ID, THERAPIST_ID
                )

                # Test pipeline
                result = await test_single_session(
                    orchestrator,
                    session_id,
                    session_file.stem
                )

                if result:
                    results.append(result)

            except Exception as e:
                print(f"{Colors.RED}❌ Failed to process {session_file.name}: {e}{Colors.END}")

    else:
        # Test single session
        if TEST_SESSION_INDEX >= len(session_files):
            print(f"{Colors.RED}❌ Invalid session index: {TEST_SESSION_INDEX}{Colors.END}")
            return

        session_file = session_files[TEST_SESSION_INDEX]

        try:
            # Load session to database
            session_id = await load_mock_session_to_db(
                db, session_file, PATIENT_ID, THERAPIST_ID
            )

            # Test pipeline
            result = await test_single_session(
                orchestrator,
                session_id,
                session_file.stem
            )

            if result:
                results.append(result)

        except Exception as e:
            print(f"{Colors.RED}❌ Failed to process {session_file.name}: {e}{Colors.END}")

    # Save results to file
    output_file = Path(__file__).parent.parent.parent / "deep_analysis_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)

    print_header("TEST COMPLETE")
    print(f"{Colors.GREEN}✓ Tested {len(results)} session(s){Colors.END}")
    print(f"{Colors.CYAN}Results saved to: {output_file}{Colors.END}")

    # Summary statistics
    if results:
        avg_confidence = sum(r.get("confidence", 0) for r in results) / len(results)
        print(f"\n{Colors.BOLD}Summary:{Colors.END}")
        print(f"  Average Confidence: {avg_confidence:.0%}")
        print(f"  Success Rate: {len(results)}/{len(session_files) if TEST_ALL else 1}")


if __name__ == "__main__":
    asyncio.run(main())
