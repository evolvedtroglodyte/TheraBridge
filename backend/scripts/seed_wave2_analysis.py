#!/usr/bin/env python3
"""
Wave 2 Analysis Script - Demo Seeding with Cumulative Context
==============================================================
Runs Wave 2 deep clinical analysis on demo sessions WITH cumulative context:
- Each session analysis includes ALL previous sessions as context
- Builds nested context structure (Session N references Sessions 1...N-1)
- Creates "therapeutic journey" tracking progress over time

Usage:
    python scripts/seed_wave2_analysis.py <patient_id>

Cumulative Context Structure:
    Session 1: No context
    Session 2: {session_01_wave1, session_01_wave2}
    Session 3: {previous_context: {...}, session_02_wave1, session_02_wave2}
    Session 4: {previous_context: {previous_context: {...}}, session_03_wave1, session_03_wave2}

This script:
- Fetches all sessions for patient (chronologically)
- Processes sequentially (must maintain cumulative context)
- Each session gets context from all prior sessions
- Updates database with Wave 2 deep_analysis JSONB
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import get_supabase_admin
from app.services.deep_analyzer import DeepAnalyzer
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def fetch_patient_sessions_chronological(patient_id: str) -> List[Dict[str, Any]]:
    """Fetch all sessions for a patient in chronological order"""
    db = get_supabase_admin()

    try:
        response = (
            db.table("therapy_sessions")
            .select("*")
            .eq("patient_id", patient_id)
            .order("session_date", desc=False)  # Chronological order
            .execute()
        )

        sessions = response.data
        logger.info(f"✓ Fetched {len(sessions)} sessions for patient {patient_id} (chronological)")
        return sessions

    except Exception as e:
        logger.error(f"Failed to fetch sessions: {e}")
        raise


def extract_wave1_data(session: Dict[str, Any]) -> Dict[str, Any]:
    """Extract Wave 1 analysis fields from session"""
    return {
        "session_id": session["id"],
        "session_date": session.get("session_date"),
        "mood_score": session.get("mood_score"),
        "mood_confidence": session.get("mood_confidence"),
        "mood_rationale": session.get("mood_rationale"),
        "emotional_tone": session.get("emotional_tone"),
        "topics": session.get("topics"),
        "action_items": session.get("action_items"),
        "technique": session.get("technique"),
        "summary": session.get("summary"),
        "has_breakthrough": session.get("has_breakthrough"),
        "breakthrough_data": session.get("breakthrough_data")
    }


def extract_wave2_data(session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract Wave 2 deep_analysis from session"""
    deep_analysis = session.get("deep_analysis")

    if not deep_analysis:
        return None

    return {
        "session_id": session["id"],
        "session_date": session.get("session_date"),
        "deep_analysis": deep_analysis
    }


def build_cumulative_context(
    previous_sessions: List[Dict[str, Any]],
    previous_cumulative_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Build cumulative context for current session analysis.

    Args:
        previous_sessions: All sessions before current one (chronological)
        previous_cumulative_context: Context from N-2 session (nested)

    Returns:
        Nested context structure with Wave 1 + Wave 2 from all previous sessions
    """
    if not previous_sessions:
        return None

    # Get most recent previous session
    latest_previous = previous_sessions[-1]

    # Build context
    context = {}

    # Add nested previous context (from N-2, N-3, etc.)
    if previous_cumulative_context:
        context["previous_context"] = previous_cumulative_context

    # Add latest previous session (N-1)
    session_num = len(previous_sessions)
    wave1_key = f"session_{session_num:02d}_wave1"
    wave2_key = f"session_{session_num:02d}_wave2"

    context[wave1_key] = extract_wave1_data(latest_previous)

    wave2 = extract_wave2_data(latest_previous)
    if wave2:
        context[wave2_key] = wave2

    return context


async def run_deep_analysis(
    session: Dict[str, Any],
    cumulative_context: Optional[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Run deep analysis on a session with cumulative context"""
    try:
        analyzer = DeepAnalyzer()

        # Run analysis
        result = await analyzer.analyze_session(
            session_id=session["id"],
            session=session,
            cumulative_context=cumulative_context
        )

        logger.info(f"  ✓ Deep analysis complete (confidence: {result.confidence_score:.2f})")

        return result.to_dict()

    except Exception as e:
        logger.error(f"  ✗ Deep analysis failed: {e}")
        return None


async def update_session_wave2(session_id: str, deep_analysis: Dict[str, Any]) -> bool:
    """Update session with Wave 2 deep analysis"""
    db = get_supabase_admin()

    try:
        response = (
            db.table("therapy_sessions")
            .update({
                "deep_analysis": deep_analysis,
                "deep_analyzed_at": datetime.utcnow().isoformat()
            })
            .eq("id", session_id)
            .execute()
        )

        logger.info(f"  ✓ Database updated with deep analysis")
        return True

    except Exception as e:
        logger.error(f"  ✗ Database update failed: {e}")
        return False


async def process_session_wave2(
    session: Dict[str, Any],
    index: int,
    total: int,
    previous_sessions: List[Dict[str, Any]],
    previous_cumulative_context: Optional[Dict[str, Any]]
):
    """Process a single session with Wave 2 analysis"""
    session_id = session["id"]
    session_date = session.get("session_date", "unknown")

    logger.info(f"\n[{index + 1}/{total}] Processing session {session_date} ({session_id})")

    # Build cumulative context
    cumulative_context = build_cumulative_context(previous_sessions, previous_cumulative_context)

    if cumulative_context:
        context_depth = str(cumulative_context).count("previous_context") + 1
        logger.info(f"  📚 Context depth: {context_depth} previous session(s)")
    else:
        logger.info(f"  📚 No previous context (first session)")

    # Run deep analysis
    deep_analysis = await run_deep_analysis(session, cumulative_context)

    # Update database
    if deep_analysis:
        await update_session_wave2(session_id, deep_analysis)
        logger.info(f"[{index + 1}/{total}] ✅ Session complete")
        return deep_analysis, cumulative_context
    else:
        logger.warning(f"[{index + 1}/{total}] ⚠️  No results to update")
        return None, cumulative_context


async def main(patient_id: str):
    """Main execution flow"""
    logger.info("=" * 80)
    logger.info("Wave 2 Analysis - Demo Seeding with Cumulative Context")
    logger.info("=" * 80)
    logger.info(f"Patient ID: {patient_id}")
    logger.info(f"Started: {datetime.utcnow().isoformat()}")

    # Fetch sessions in chronological order
    sessions = await fetch_patient_sessions_chronological(patient_id)

    if not sessions:
        logger.error("No sessions found for patient")
        return

    # Process each session sequentially (must maintain cumulative context)
    start_time = datetime.utcnow()
    previous_sessions = []
    previous_cumulative_context = None

    for i, session in enumerate(sessions):
        # Process current session
        deep_analysis, cumulative_context = await process_session_wave2(
            session,
            i,
            len(sessions),
            previous_sessions,
            previous_cumulative_context
        )

        # Update for next iteration
        previous_sessions.append(session)
        if deep_analysis:
            # Update session with deep_analysis for next iteration
            session["deep_analysis"] = deep_analysis
            previous_cumulative_context = cumulative_context

    # Summary
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "=" * 80)
    logger.info("✅ Wave 2 Analysis Complete")
    logger.info("=" * 80)
    logger.info(f"Sessions processed: {len(sessions)}")
    logger.info(f"Total time: {duration:.1f} seconds ({duration / 60:.1f} minutes)")
    logger.info(f"Average per session: {duration / len(sessions):.1f} seconds")
    logger.info(f"Finished: {end_time.isoformat()}")
    logger.info("\n💡 Cumulative context depth: Session 1 (none) → Session 10 (9 sessions)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/seed_wave2_analysis.py <patient_id>")
        sys.exit(1)

    patient_id = sys.argv[1]

    # Validate UUID format
    try:
        UUID(patient_id)
    except ValueError:
        print(f"Error: Invalid UUID format: {patient_id}")
        sys.exit(1)

    # Run async main
    asyncio.run(main(patient_id))
