#!/usr/bin/env python3
"""
Wave 1 Analysis Script - Demo Seeding
======================================
Runs Wave 1 AI analysis on demo sessions:
1. Mood Analysis (mood score, confidence, rationale, indicators)
2. Topic Extraction (topics, action items, technique, summary)
3. Breakthrough Detection (identifies transformative moments)
4. Action Items Summarization (45-char condensed summary) - SEQUENTIAL

Usage:
    python scripts/seed_wave1_analysis.py <patient_id>

This script:
- Fetches all sessions for the given patient
- Runs 3 AI services in parallel per session (mood, topics, breakthrough)
- Runs action summarization sequentially (after topic extraction)
- Updates database with Wave 1 results
- Logs progress and errors
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import get_supabase_admin
from app.services.mood_analyzer import MoodAnalyzer
from app.services.topic_extractor import TopicExtractor
from app.services.breakthrough_detector import BreakthroughDetector
from app.services.action_items_summarizer import ActionItemsSummarizer, ActionItemsSummary
from app.config import settings
from app.utils.pipeline_logger import PipelineLogger, LogPhase, LogEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def fetch_patient_sessions(patient_id: str) -> List[Dict[str, Any]]:
    """Fetch all sessions for a patient"""
    db = get_supabase_admin()

    try:
        response = (
            db.table("therapy_sessions")
            .select("*")
            .eq("patient_id", patient_id)
            .order("session_date")
            .execute()
        )

        sessions = response.data
        logger.info(f"✓ Fetched {len(sessions)} sessions for patient {patient_id}")
        return sessions

    except Exception as e:
        logger.error(f"Failed to fetch sessions: {e}")
        raise


async def run_mood_analysis(session: Dict[str, Any]) -> Dict[str, Any]:
    """Run mood analysis on a session"""
    try:
        analyzer = MoodAnalyzer()

        # Parse transcript
        transcript = session.get("transcript", [])
        if isinstance(transcript, str):
            import json
            transcript = json.loads(transcript)

        # Run analysis (assumes SPEAKER_01 is patient)
        result = await analyzer.analyze_session_mood(
            session_id=session["id"],
            segments=transcript,
            patient_speaker_id="SPEAKER_01"
        )

        logger.info(f"  ✓ Mood analysis complete: {result.mood_score}/10.0 (confidence: {result.confidence:.2f})")
        print(f"  ✓ Mood: {result.mood_score}/10.0 (confidence: {result.confidence:.2f})", flush=True)

        return {
            "mood_score": result.mood_score,
            "mood_confidence": result.confidence,
            "mood_rationale": result.rationale,
            "mood_indicators": result.key_indicators,
            "emotional_tone": result.emotional_tone,
            "mood_analyzed_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"  ✗ Mood analysis failed: {e}")
        print(f"  ✗ Mood analysis failed: {e}", flush=True)
        return None


async def run_topic_extraction(session: Dict[str, Any]) -> Dict[str, Any]:
    """Run topic extraction on a session"""
    try:
        extractor = TopicExtractor()

        # Parse transcript
        transcript = session.get("transcript", [])
        if isinstance(transcript, str):
            import json
            transcript = json.loads(transcript)

        # Run extraction
        result = await extractor.extract_metadata(
            session_id=session["id"],
            segments=transcript,
            speaker_roles={"SPEAKER_00": "Therapist", "SPEAKER_01": "Client"}
        )

        logger.info(f"  ✓ Topic extraction complete: {len(result.topics)} topics, {result.technique}")
        print(f"  ✓ Topics: {', '.join(result.topics[:2])}, {result.technique}", flush=True)

        return {
            "topics": result.topics,
            "action_items": result.action_items,
            "technique": result.technique,
            "summary": result.summary,
            "extraction_confidence": result.confidence,
            "topics_extracted_at": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"  ✗ Topic extraction failed: {e}")
        print(f"  ✗ Topic extraction failed: {e}", flush=True)
        return None


async def run_breakthrough_detection(session: Dict[str, Any]) -> Dict[str, Any]:
    """Run breakthrough detection on a session"""
    try:
        detector = BreakthroughDetector()

        # Parse transcript
        transcript = session.get("transcript", [])
        if isinstance(transcript, str):
            import json
            transcript = json.loads(transcript)

        # Run detection
        result = await detector.analyze_session(
            transcript=transcript,
            session_metadata={"session_id": session["id"]}
        )

        logger.info(f"  ✓ Breakthrough detection complete: {result.has_breakthrough} (candidates: {len(result.breakthrough_candidates)})")
        print(f"  ✓ Breakthrough: {result.has_breakthrough}", flush=True)

        # Build response
        response = {
            "has_breakthrough": result.has_breakthrough,
            "breakthrough_analyzed_at": datetime.utcnow().isoformat()
        }

        if result.primary_breakthrough:
            response["breakthrough_data"] = {
                "type": result.primary_breakthrough.breakthrough_type,
                "label": result.primary_breakthrough.label,
                "description": result.primary_breakthrough.description,
                "evidence": result.primary_breakthrough.evidence,
                "confidence": result.primary_breakthrough.confidence_score,
                "timestamp_start": result.primary_breakthrough.timestamp_start,
                "timestamp_end": result.primary_breakthrough.timestamp_end,
                "dialogue_excerpt": [
                    {"speaker": seg["speaker"], "text": seg["text"]}
                    for seg in result.primary_breakthrough.speaker_sequence
                ]
            }

        return response

    except Exception as e:
        logger.error(f"  ✗ Breakthrough detection failed: {e}")
        print(f"  ✗ Breakthrough detection failed: {e}", flush=True)
        return None


async def update_session_wave1(session_id: str, updates: Dict[str, Any]) -> bool:
    """Update session with Wave 1 analysis results"""
    db = get_supabase_admin()

    try:
        # Remove None values
        updates = {k: v for k, v in updates.items() if v is not None}

        response = (
            db.table("therapy_sessions")
            .update(updates)
            .eq("id", session_id)
            .execute()
        )

        logger.info(f"  ✓ Database updated with {len(updates)} fields")
        return True

    except Exception as e:
        logger.error(f"  ✗ Database update failed: {e}")
        return False


async def process_session(session: Dict[str, Any], index: int, total: int):
    """Process a single session with all Wave 1 analyses - granular logging"""
    session_id = session["id"]
    session_date = session.get("session_date", "unknown")
    patient_id = session.get("patient_id")

    logger_instance = PipelineLogger(patient_id, LogPhase.WAVE1)

    # START event
    logger_instance.log_event(
        LogEvent.START,
        session_id=session_id,
        session_date=session_date,
        details={"index": index + 1, "total": total}
    )

    print(f"[{index + 1}/{total}] Processing session {session_date} ({session_id})", flush=True)
    logger.info(f"\n[{index + 1}/{total}] Processing session {session_date} ({session_id})")

    # Run all 3 analyses in parallel
    parallel_start = datetime.now()

    # Start all three analyses simultaneously
    mood_task = run_mood_analysis(session)
    topic_task = run_topic_extraction(session)
    breakthrough_task = run_breakthrough_detection(session)

    # Wait for all to complete
    mood_result, topic_result, breakthrough_result = await asyncio.gather(
        mood_task,
        topic_task,
        breakthrough_task,
        return_exceptions=True  # Prevent one failure from canceling others
    )

    parallel_duration = (datetime.now() - parallel_start).total_seconds() * 1000

    # Handle individual results (including potential exceptions)
    updates = {}

    # Process mood result
    if isinstance(mood_result, Exception):
        logger.error(f"  ✗ Mood analysis failed: {mood_result}")
        print(f"  ✗ Mood analysis failed: {mood_result}", flush=True)
        logger_instance.log_event(
            LogEvent.MOOD_ANALYSIS,
            session_id=session_id,
            session_date=session_date,
            status="failed",
            details={"error": str(mood_result)}
        )
    elif mood_result:
        logger_instance.log_event(
            LogEvent.MOOD_ANALYSIS,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            details={
                "mood_score": mood_result.get("mood_score"),
                "confidence": mood_result.get("mood_confidence")
            }
        )
        updates.update(mood_result)

    # Process topic result
    if isinstance(topic_result, Exception):
        logger.error(f"  ✗ Topic extraction failed: {topic_result}")
        print(f"  ✗ Topic extraction failed: {topic_result}", flush=True)
        logger_instance.log_event(
            LogEvent.TOPIC_EXTRACTION,
            session_id=session_id,
            session_date=session_date,
            status="failed",
            details={"error": str(topic_result)}
        )
    elif topic_result:
        logger_instance.log_event(
            LogEvent.TOPIC_EXTRACTION,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            details={
                "topics_count": len(topic_result.get("topics", [])),
                "technique": topic_result.get("technique")
            }
        )
        updates.update(topic_result)

    # Process breakthrough result
    if isinstance(breakthrough_result, Exception):
        logger.error(f"  ✗ Breakthrough detection failed: {breakthrough_result}")
        print(f"  ✗ Breakthrough detection failed: {breakthrough_result}", flush=True)
        logger_instance.log_event(
            LogEvent.BREAKTHROUGH_DETECTION,
            session_id=session_id,
            session_date=session_date,
            status="failed",
            details={"error": str(breakthrough_result)}
        )
    elif breakthrough_result:
        logger_instance.log_event(
            LogEvent.BREAKTHROUGH_DETECTION,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            details={
                "has_breakthrough": breakthrough_result.get("has_breakthrough"),
                "candidates": len(breakthrough_result.get("breakthrough_candidates", []))
            }
        )
        updates.update(breakthrough_result)

    logger.info(f"  ✓ All analyses complete in {parallel_duration:.0f}ms (parallel execution)")
    print(f"  ✓ All analyses complete in {parallel_duration:.0f}ms", flush=True)

    # SEQUENTIAL: Action items summarization (if action items exist)
    action_items_summary = None
    action_items = updates.get("action_items")
    if action_items and len(action_items) == 2:
        try:
            logger.info(f"📝 Generating action items summary for session {session_id}...")
            print(f"📝 Generating action items summary...", flush=True)

            summarizer = ActionItemsSummarizer()
            summary_result = await summarizer.summarize_action_items(
                action_items=action_items,
                session_id=str(session_id)
            )

            action_items_summary = summary_result.summary
            updates["action_items_summary"] = action_items_summary

            logger.info(
                f"✅ Action items summary complete: "
                f"'{action_items_summary}' ({summary_result.character_count} chars)"
            )
            print(
                f"✅ Action summary: '{action_items_summary}' ({summary_result.character_count} chars)",
                flush=True
            )

        except Exception as e:
            logger.error(f"❌ Action items summarization failed: {str(e)}")
            print(f"❌ Action summarization failed: {str(e)}", flush=True)
            # Continue without summary (non-blocking)

    # Update database
    if updates:
        db_start = datetime.now()
        logger_instance.log_event(
            LogEvent.DB_UPDATE,
            session_id=session_id,
            session_date=session_date,
            status="started"
        )

        await update_session_wave1(session_id, updates)

        db_duration = (datetime.now() - db_start).total_seconds() * 1000
        logger_instance.log_event(
            LogEvent.DB_UPDATE,
            session_id=session_id,
            session_date=session_date,
            status="complete",
            duration_ms=db_duration,
            details={"fields_updated": len(updates)}
        )

        # COMPLETE event
        total_duration = parallel_duration + db_duration
        logger_instance.log_event(
            LogEvent.COMPLETE,
            session_id=session_id,
            session_date=session_date,
            duration_ms=total_duration
        )

        print(f"[{index + 1}/{total}] ✅ Session complete", flush=True)
        logger.info(f"[{index + 1}/{total}] ✅ Session complete")
    else:
        logger_instance.log_event(
            LogEvent.FAILED,
            session_id=session_id,
            session_date=session_date,
            status="failed",
            details={"error": "No results to update"}
        )
        logger.warning(f"[{index + 1}/{total}] ⚠️  No results to update")


async def main(patient_id: str):
    """Main execution flow"""
    logger.info("=" * 80)
    logger.info("Wave 1 Analysis - Demo Seeding")
    logger.info("=" * 80)
    logger.info(f"Patient ID: {patient_id}")
    logger.info(f"Started: {datetime.utcnow().isoformat()}")

    # Fetch sessions
    sessions = await fetch_patient_sessions(patient_id)

    if not sessions:
        logger.error("No sessions found for patient")
        return

    # Process all sessions in parallel (Wave 1 has no inter-session dependencies)
    start_time = datetime.utcnow()

    logger.info(f"🚀 Starting parallel processing of {len(sessions)} sessions...")
    print(f"🚀 Processing {len(sessions)} sessions in parallel...", flush=True)
    logger.info(f"Concurrency: {len(sessions)} parallel operations")

    # Create tasks for all sessions
    tasks = [
        process_session(session, i, len(sessions))
        for i, session in enumerate(sessions)
    ]

    # Run all tasks concurrently
    await asyncio.gather(*tasks)

    # Summary
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "=" * 80)
    print("\n" + "=" * 80, flush=True)
    logger.info("✅ Wave 1 Analysis Complete")
    print("✅ Wave 1 Analysis Complete", flush=True)
    logger.info("=" * 80)
    print(f"Sessions processed: {len(sessions)}", flush=True)
    logger.info(f"Sessions processed: {len(sessions)}")
    print(f"Total time: {duration:.1f} seconds ({duration / 60:.1f} minutes)", flush=True)
    logger.info(f"Total time: {duration:.1f} seconds ({duration / 60:.1f} minutes)")
    logger.info(f"Average per session: {duration / len(sessions):.1f} seconds")
    logger.info(f"Finished: {end_time.isoformat()}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/seed_wave1_analysis.py <patient_id>")
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
