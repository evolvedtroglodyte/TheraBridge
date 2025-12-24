"""
Session Bridge Generation Orchestration Script

Runs after each Wave 2 analysis completes to generate patient-facing
shareable content (shareConcerns, shareProgress, setGoals).

Usage:
    python scripts/generate_session_bridge.py <patient_id> <session_id>

Example:
    python scripts/generate_session_bridge.py 550e8400-e29b-41d4-a716-446655440000 650e8400-e29b-41d4-a716-446655440001
"""

import sys
import os
import json
from uuid import UUID
from datetime import datetime
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.session_bridge_generator import SessionBridgeGenerator
from app.database import get_supabase_admin
from app.utils.wave3_logger import create_session_bridge_logger, Wave3Event
from app.utils.generation_metadata import create_generation_metadata


def log_step(step: str, message: str) -> None:
    """Print a formatted step message with flush for Railway logs."""
    print(f"[{step}] {message}", flush=True)


def log_success(message: str) -> None:
    """Print a success message with flush for Railway logs."""
    print(f"  ✓ {message}", flush=True)


def log_error(message: str) -> None:
    """Print an error message with flush for Railway logs."""
    print(f"[ERROR] {message}", flush=True)


def generate_session_bridge_for_session(patient_id: str, session_id: str):
    """
    Generate session bridge after a session's Wave 2 completes.

    Steps:
    1. Verify Wave 2 is complete
    2. Build tiered context from previous sessions
    3. Generate session bridge content
    4. Update database (patient_session_bridge + session_bridge_versions)
    """
    start_time = time.time()
    supabase = get_supabase_admin()
    wave3_logger = create_session_bridge_logger(patient_id)

    print(f"\n{'='*60}", flush=True)
    print(f"SESSION BRIDGE GENERATION - Session {session_id}", flush=True)
    print(f"{'='*60}\n", flush=True)

    wave3_logger.log_start(details={"session_id": session_id})

    try:
        # Step 1: Get session data and verify Wave 2 complete
        log_step("Step 1/5", "Fetching session data...")

        session_result = supabase.table("therapy_sessions") \
            .select("*") \
            .eq("id", session_id) \
            .execute()

        if not session_result.data:
            log_error(f"Session {session_id} not found")
            wave3_logger.log_failed("Session not found")
            return

        current_session = session_result.data[0]

        # Verify Wave 2 complete
        if not current_session.get("deep_analysis"):
            log_error(f"Session {session_id} Wave 2 not complete (no deep_analysis)")
            wave3_logger.log_failed("Wave 2 not complete")
            return

        log_success(f"Session fetched: {current_session.get('session_date')}")

        # Get session number
        all_sessions = supabase.table("therapy_sessions") \
            .select("id, session_date") \
            .eq("patient_id", patient_id) \
            .order("session_date") \
            .execute()

        session_ids = [s["id"] for s in all_sessions.data]
        session_number = session_ids.index(session_id) + 1 if session_id in session_ids else len(session_ids)

        log_success(f"Session number: {session_number} of {len(session_ids)}")

        # Step 2: Build tiered context
        log_step("Step 2/5", "Building tiered context...")

        context = build_tiered_context(patient_id, session_id, supabase)

        # Add current session data to context
        context["current_session"] = {
            "session_id": session_id,
            "session_date": current_session.get("session_date"),
            "mood_score": current_session.get("mood_score"),
            "topics": current_session.get("topics", []),
            "technique": current_session.get("technique"),
            "summary": current_session.get("summary"),
            "deep_analysis": current_session.get("deep_analysis"),
        }

        # Get roadmap data if available
        roadmap_result = supabase.table("patient_your_journey") \
            .select("roadmap_data") \
            .eq("patient_id", patient_id) \
            .execute()

        if roadmap_result.data:
            context["roadmap_data"] = roadmap_result.data[0].get("roadmap_data")

        tier_counts = (
            f"tier1={len(context.get('tier1_insights', {}))}, "
            f"tier2={len(context.get('tier2_insights', {}))}, "
            f"tier3={'yes' if context.get('tier3_insights') else 'no'}"
        )
        log_success(f"Context built ({tier_counts})")

        wave3_logger.log_event(
            Wave3Event.CONTEXT_BUILD,
            session_number=session_number,
            details={"tiers": tier_counts}
        )

        # Step 3: Generate session bridge
        log_step("Step 3/5", "Generating session bridge content...")

        generator = SessionBridgeGenerator()

        bridge_data = generator.generate_session_bridge(
            patient_id=patient_id,
            session_id=session_id,
            session_number=session_number,
            context=context,
            log_events=False  # We're already logging
        )

        log_success(f"Generated with confidence {bridge_data.confidence_score:.2f}")
        print(f"    shareConcerns: {len(bridge_data.share_concerns)} items", flush=True)
        print(f"    shareProgress: {len(bridge_data.share_progress)} items", flush=True)
        print(f"    setGoals: {len(bridge_data.set_goals)} items", flush=True)

        # Step 4: Get or create patient_session_bridge record
        log_step("Step 4/5", "Updating patient_session_bridge...")

        bridge_record = supabase.table("patient_session_bridge") \
            .select("id") \
            .eq("patient_id", patient_id) \
            .execute()

        if bridge_record.data:
            session_bridge_id = bridge_record.data[0]["id"]
            log_success(f"Found existing bridge record: {session_bridge_id[:8]}...")
        else:
            # Create new record
            new_record = supabase.table("patient_session_bridge").insert({
                "patient_id": patient_id
            }).execute()

            session_bridge_id = new_record.data[0]["id"]
            log_success(f"Created new bridge record: {session_bridge_id[:8]}...")

        # Step 5: Save version to session_bridge_versions
        log_step("Step 5/5", "Saving bridge version...")

        # Get current version number
        versions_result = supabase.table("session_bridge_versions") \
            .select("version_number") \
            .eq("patient_id", patient_id) \
            .order("version_number", desc=True) \
            .limit(1) \
            .execute()

        current_version = versions_result.data[0]["version_number"] if versions_result.data else 0
        new_version = current_version + 1

        # Prepare version record
        version_record = {
            "patient_id": patient_id,
            "session_bridge_id": session_bridge_id,
            "version_number": new_version,
            "bridge_data": bridge_data.to_bridge_data(),
            "generation_context": {
                "tier1_count": len(context.get("tier1_insights", {})),
                "tier2_count": len(context.get("tier2_insights", {})),
                "has_tier3": bool(context.get("tier3_insights")),
                "session_number": session_number,
                "confidence_score": bridge_data.confidence_score,
            },
            "model_used": generator.model,
        }

        # Add cost info if available
        if bridge_data.cost_info:
            version_record["cost"] = bridge_data.cost_info.cost
            version_record["generation_duration_ms"] = bridge_data.cost_info.duration_ms

        # Insert version
        version_result = supabase.table("session_bridge_versions").insert(version_record).execute()

        version_id = version_result.data[0]["id"]
        log_success(f"Version {new_version} saved: {version_id[:8]}...")

        # Create generation_metadata record for this version
        try:
            metadata = create_generation_metadata(
                db=supabase,
                session_bridge_version_id=UUID(version_id),
                sessions_analyzed=session_number,
                total_sessions=len(session_ids),
                model_used=generator.model,
                generation_timestamp=datetime.utcnow(),
                generation_duration_ms=bridge_data.cost_info.duration_ms if bridge_data.cost_info else 0,
                last_session_id=UUID(session_id),
                compaction_strategy="tiered",
                metadata_json={
                    "tier1_count": len(context.get("tier1_insights", {})),
                    "tier2_count": len(context.get("tier2_insights", {})),
                    "has_tier3": bool(context.get("tier3_insights")),
                    "confidence_score": bridge_data.confidence_score,
                }
            )
            metadata_id = metadata["id"]
            log_success(f"Generation metadata created: {metadata_id[:8]}...")

            # Link metadata to version
            supabase.table("session_bridge_versions").update({
                "generation_metadata_id": metadata_id
            }).eq("id", version_id).execute()

        except Exception as e:
            print(f"  ⚠ Warning: Failed to create generation_metadata: {e}", flush=True)
            # Continue - metadata is optional enhancement

        wave3_logger.log_event(
            Wave3Event.VERSION_SAVE,
            session_number=session_number,
            version_number=new_version,
            details={"version_id": version_id}
        )

        # Update current_version_id in patient_session_bridge
        supabase.table("patient_session_bridge").update({
            "current_version_id": version_id,
            "updated_at": datetime.utcnow().isoformat()
        }).eq("id", session_bridge_id).execute()

        log_success("Updated current_version_id in patient_session_bridge")

        # Calculate total duration
        total_duration_ms = int((time.time() - start_time) * 1000)
        total_cost = bridge_data.cost_info.cost if bridge_data.cost_info else 0.0

        # Log completion
        wave3_logger.log_complete(
            version_number=new_version,
            duration_ms=total_duration_ms,
            cost=total_cost,
            details={
                "session_number": session_number,
                "confidence": bridge_data.confidence_score
            }
        )

        # Print summary
        print(f"\n{'='*60}", flush=True)
        print(f"SESSION BRIDGE GENERATION COMPLETE", flush=True)
        print(f"  Patient: {patient_id}", flush=True)
        print(f"  Session: {session_number}", flush=True)
        print(f"  Version: {new_version}", flush=True)
        print(f"  Confidence: {bridge_data.confidence_score:.2f}", flush=True)
        print(f"  Duration: {total_duration_ms}ms", flush=True)
        if bridge_data.cost_info:
            print(f"  Cost: ${bridge_data.cost_info.cost:.6f}", flush=True)
        print(f"{'='*60}\n", flush=True)

    except Exception as e:
        log_error(f"Generation failed: {e}")
        wave3_logger.log_failed(str(e), details={"session_id": session_id})
        raise


def build_tiered_context(patient_id: str, current_session_id: str, supabase) -> dict:
    """
    Build tiered context for session bridge generation.

    Similar to roadmap's hierarchical context but focused on insights
    relevant for patient sharing.

    Tier 1: Last 1-3 sessions - Full Wave 1 + Wave 2 data
    Tier 2: Sessions 4-7 - Key insights only
    Tier 3: Sessions 8+ - Journey arc summary
    """
    # Get all previous sessions with Wave 2 complete
    sessions_result = supabase.table("therapy_sessions") \
        .select("id, session_date, mood_score, topics, technique, summary, deep_analysis, prose_analysis") \
        .eq("patient_id", patient_id) \
        .neq("id", current_session_id) \
        .order("session_date") \
        .execute()

    sessions_with_wave2 = [s for s in sessions_result.data if s.get("deep_analysis")]
    num_sessions = len(sessions_with_wave2)

    # Reverse to get most recent first
    sessions_reversed = list(reversed(sessions_with_wave2))

    # Tier 1: Last 1-3 sessions (full insights)
    tier1_insights = {}
    for session in sessions_reversed[:3]:
        session_key = session["id"]
        tier1_insights[session_key] = {
            "wave1": {
                "session_date": session.get("session_date"),
                "mood_score": session.get("mood_score"),
                "topics": session.get("topics", []),
                "technique": session.get("technique"),
                "summary": session.get("summary"),
            },
            "wave2": session.get("deep_analysis", {}),
        }

    # Tier 2: Sessions 4-7 (summarized insights)
    tier2_insights = {}
    if num_sessions >= 4:
        for session in sessions_reversed[3:7]:
            session_key = session["id"]
            deep = session.get("deep_analysis", {})
            tier2_insights[session_key] = {
                "wave1": {
                    "session_date": session.get("session_date"),
                    "mood_score": session.get("mood_score"),
                    "topics": session.get("topics", []),
                },
                "wave2": {
                    # Extract only key insights for tier 2
                    "therapeutic_insights": deep.get("therapeutic_insights", {}),
                    "coping_skills": deep.get("coping_skills", {}),
                }
            }

    # Tier 3: Sessions 8+ (journey arc)
    tier3_insights = None
    if num_sessions >= 8:
        # Create summary of older sessions
        arc_sessions = sessions_reversed[7:]
        topics_seen = set()
        strengths_seen = set()
        techniques_seen = set()

        for session in arc_sessions:
            topics_seen.update(session.get("topics", []))
            techniques_seen.add(session.get("technique"))
            deep = session.get("deep_analysis", {})
            strengths_seen.update(
                deep.get("therapeutic_insights", {}).get("strengths", [])
            )

        tier3_insights = {
            "summary": f"Journey began with {len(arc_sessions)} earlier sessions",
            "recurring_topics": list(topics_seen)[:5],
            "techniques_explored": list(techniques_seen - {None})[:5],
            "demonstrated_strengths": list(strengths_seen)[:5],
        }

    return {
        "tier1_insights": tier1_insights,
        "tier2_insights": tier2_insights,
        "tier3_insights": tier3_insights,
    }


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/generate_session_bridge.py <patient_id> <session_id>")
        sys.exit(1)

    patient_id = sys.argv[1]
    session_id = sys.argv[2]

    generate_session_bridge_for_session(patient_id, session_id)
