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
from app.services.prose_generator import ProseGenerator
from app.config import settings
from app.utils.pipeline_logger import PipelineLogger, LogPhase, LogEvent

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
        print(f"  ✓ Deep analysis complete (confidence: {result.confidence_score:.2f})", flush=True)

        return result.to_dict()

    except Exception as e:
        logger.error(f"  ✗ Deep analysis failed: {e}")
        print(f"  ✗ Deep analysis failed: {e}", flush=True)
        return None


async def run_prose_generation(
    session_id: str,
    deep_analysis_dict: Dict[str, Any],
    confidence: float
) -> Optional[str]:
    """Generate patient-facing prose from deep analysis"""
    try:
        generator = ProseGenerator()

        prose_result = await generator.generate_prose(
            session_id=session_id,
            deep_analysis=deep_analysis_dict,
            confidence_score=confidence
        )

        logger.info(f"  ✓ Prose generated: {prose_result.word_count} words, {prose_result.paragraph_count} paragraphs")
        print(f"  ✓ Prose generated: {prose_result.word_count} words, {prose_result.paragraph_count} paragraphs", flush=True)

        return prose_result.prose_text

    except Exception as e:
        logger.error(f"  ✗ Prose generation failed: {e}")
        print(f"  ✗ Prose generation failed: {e}", flush=True)
        return None


async def update_session_wave2(
    session_id: str,
    deep_analysis_dict: Dict[str, Any],
    prose_text: Optional[str],
    deep_analyzed_at: datetime,
    prose_generated_at: Optional[datetime]
) -> bool:
    """Update session with Wave 2 deep analysis and prose"""
    db = get_supabase_admin()

    try:
        update_data = {
            "deep_analysis": deep_analysis_dict,
            "deep_analyzed_at": deep_analyzed_at.isoformat()
        }

        # Add prose fields if generation succeeded
        if prose_text:
            update_data["prose_analysis"] = prose_text
            update_data["prose_generated_at"] = prose_generated_at.isoformat()

        response = (
            db.table("therapy_sessions")
            .update(update_data)
            .eq("id", session_id)
            .execute()
        )

        logger.info(f"  ✓ Database updated with deep analysis{' and prose' if prose_text else ''}")
        print(f"  ✓ Database updated{' with prose' if prose_text else ''}", flush=True)
        return True

    except Exception as e:
        logger.error(f"  ✗ Database update failed: {e}")
        print(f"  ✗ Database update failed: {e}", flush=True)
        return False


async def process_session_wave2(
    session: Dict[str, Any],
    index: int,
    total: int,
    previous_sessions: List[Dict[str, Any]],
    previous_cumulative_context: Optional[Dict[str, Any]]
):
    """Process a single session with Wave 2 analysis - granular logging"""
    session_id = session["id"]
    session_date = session.get("session_date", "unknown")
    patient_id = session.get("patient_id")

    logger_instance = PipelineLogger(patient_id, LogPhase.WAVE2)

    # START event with context depth
    context_depth = len(previous_sessions)
    logger_instance.log_event(
        LogEvent.START,
        session_id=session_id,
        session_date=session_date,
        details={
            "index": index + 1,
            "total": total,
            "context_depth": context_depth
        }
    )

    print(f"[{index + 1}/{total}] Processing Wave 2 for session {session_date}", flush=True)
    logger.info(f"\n[{index + 1}/{total}] Processing session {session_date} ({session_id})")

    # Build cumulative context
    cumulative_context = build_cumulative_context(previous_sessions, previous_cumulative_context)

    if cumulative_context:
        logger.info(f"  📚 Context depth: {context_depth} previous session(s)")
    else:
        logger.info(f"  📚 No previous context (first session)")

    # DEEP_ANALYSIS
    analysis_start = datetime.now()
    logger_instance.log_event(
        LogEvent.DEEP_ANALYSIS,
        session_id=session_id,
        session_date=session_date,
        status="started",
        details={"context_depth": context_depth}
    )

    deep_analysis = await run_deep_analysis(session, cumulative_context)

    if deep_analysis:
        deep_analyzed_at = datetime.now()
        analysis_duration = (deep_analyzed_at - analysis_start).total_seconds() * 1000
        logger_instance.log_event(
            LogEvent.DEEP_ANALYSIS,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            duration_ms=analysis_duration,
            details={
                "confidence": deep_analysis.get("confidence_score"),
                "has_insights": bool(deep_analysis.get("therapeutic_insights"))
            }
        )

        # PROSE_GENERATION
        prose_start = datetime.now()
        logger_instance.log_event(
            LogEvent.PROSE_GENERATION,
            session_id=session_id,
            session_date=session_date,
            status="started",
            details={"confidence": deep_analysis.get("confidence_score")}
        )

        prose_text = await run_prose_generation(
            session_id,
            deep_analysis,
            deep_analysis.get("confidence_score", 0.7)
        )

        if prose_text:
            prose_generated_at = datetime.now()
            prose_duration = (prose_generated_at - prose_start).total_seconds() * 1000

            logger_instance.log_event(
                LogEvent.PROSE_GENERATION,
                session_id=session_id,
                session_date=session_date,
                status="complete",
                duration_ms=prose_duration,
                details={
                    "word_count": len(prose_text.split()),
                    "char_count": len(prose_text)
                }
            )
        else:
            logger_instance.log_event(
                LogEvent.PROSE_GENERATION,
                session_id=session_id,
                session_date=session_date,
                status="failed"
            )
            prose_generated_at = None

        # DB_UPDATE
        db_start = datetime.now()
        logger_instance.log_event(
            LogEvent.DB_UPDATE,
            session_id=session_id,
            session_date=session_date,
            status="started"
        )

        await update_session_wave2(
            session_id,
            deep_analysis,
            prose_text,
            deep_analyzed_at,
            prose_generated_at
        )

        db_duration = (datetime.now() - db_start).total_seconds() * 1000
        logger_instance.log_event(
            LogEvent.DB_UPDATE,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            duration_ms=db_duration
        )

        # COMPLETE event
        total_duration = analysis_duration + (prose_duration if prose_text else 0) + db_duration
        logger_instance.log_event(
            LogEvent.COMPLETE,
            session_id=session_id,
            session_date=session_date,
            duration_ms=total_duration
        )

        print(f"[{index + 1}/{total}] ✅ Wave 2 complete", flush=True)
        logger.info(f"[{index + 1}/{total}] ✅ Session complete")
        return deep_analysis, cumulative_context
    else:
        logger_instance.log_event(
            LogEvent.FAILED,
            session_id=session_id,
            session_date=session_date,
            status="failed"
        )
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

            # PR #3 Phase 5: Generate roadmap after Wave 2 completes (non-blocking)
            print(f"\n[Roadmap] Triggering roadmap generation for session {session['id']}", flush=True)
            try:
                # Run generate_roadmap.py as detached subprocess (fire and forget)
                # This ensures roadmap generation continues even if Wave 2 script exits
                import subprocess
                roadmap_script = os.path.join(os.path.dirname(__file__), 'generate_roadmap.py')

                # Use Popen for non-blocking execution
                # Inherit stdout/stderr so logs appear in Railway
                # start_new_session=True detaches from parent process group
                subprocess.Popen(
                    [sys.executable, roadmap_script, patient_id, session['id']],
                    stdout=None,  # Inherit parent's stdout (Railway captures this)
                    stderr=None,  # Inherit parent's stderr
                    env=os.environ.copy(),  # Pass environment variables (OPENAI_API_KEY, etc.)
                    start_new_session=True  # Detach from parent process group
                )
                print(f"[Roadmap] ✓ Roadmap generation started (async) for session {session['id']}", flush=True)

            except Exception as e:
                print(f"[Roadmap] ✗ Roadmap generation error: {e}", flush=True)

            # Session Bridge generation (PR #4 Phase 8) - runs after roadmap
            print(f"\n[SessionBridge] Triggering session bridge generation for session {session['id']}", flush=True)
            try:
                session_bridge_script = os.path.join(os.path.dirname(__file__), 'generate_session_bridge.py')

                subprocess.Popen(
                    [sys.executable, session_bridge_script, patient_id, session['id']],
                    stdout=None,
                    stderr=None,
                    env=os.environ.copy(),
                    start_new_session=True
                )
                print(f"[SessionBridge] ✓ Session bridge generation started (async) for session {session['id']}", flush=True)

            except Exception as e:
                print(f"[SessionBridge] ✗ Session bridge generation error: {e}", flush=True)

    # Summary
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "=" * 80)
    print("\n" + "=" * 80, flush=True)
    logger.info("✅ Wave 2 Analysis Complete")
    print("✅ Wave 2 Analysis Complete", flush=True)
    logger.info("=" * 80)
    print(f"Sessions processed: {len(sessions)}", flush=True)
    logger.info(f"Sessions processed: {len(sessions)}")
    print(f"Total time: {duration:.1f} seconds ({duration / 60:.1f} minutes)", flush=True)
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
