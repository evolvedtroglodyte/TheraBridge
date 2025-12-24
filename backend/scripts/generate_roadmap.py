"""
Roadmap Generation Orchestration Script

Runs after each Wave 2 analysis completes.
Generates session insights, builds compacted context, and generates roadmap.

Usage:
    python scripts/generate_roadmap.py <patient_id> <session_id>

Example:
    python scripts/generate_roadmap.py 550e8400-e29b-41d4-a716-446655440000 650e8400-e29b-41d4-a716-446655440001
"""

import sys
import os
import json
from uuid import UUID
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.session_insights_summarizer import SessionInsightsSummarizer
from app.services.roadmap_generator import RoadmapGenerator
from app.database import get_supabase_admin


def generate_roadmap_for_session(patient_id: str, session_id: str):
    """
    Generate roadmap after a session's Wave 2 completes.

    Steps:
    1. Generate session insights from deep_analysis
    2. Build context based on compaction strategy
    3. Generate roadmap
    4. Update database (patient_roadmap + roadmap_versions)
    """
    supabase = get_supabase_admin()

    print(f"\n{'='*60}", flush=True)
    print(f"ROADMAP GENERATION - Session {session_id}", flush=True)
    print(f"{'='*60}\n", flush=True)

    # Step 1: Get session data
    print("[Step 1/5] Fetching session data...", flush=True)
    session_result = supabase.table("therapy_sessions") \
        .select("*") \
        .eq("id", session_id) \
        .execute()

    if not session_result.data:
        print(f"[ERROR] Session {session_id} not found", flush=True)
        return

    current_session = session_result.data[0]

    # Verify Wave 2 complete
    if not current_session.get("prose_analysis"):
        print(f"[ERROR] Session {session_id} Wave 2 not complete (no prose_analysis)", flush=True)
        return

    print(f"  ✓ Session fetched: {current_session.get('session_date')}", flush=True)

    # Step 2: Generate session insights
    print("\n[Step 2/5] Generating session insights (GPT-5.2)...", flush=True)
    summarizer = SessionInsightsSummarizer()

    insights = summarizer.generate_insights(
        session_id=UUID(session_id),
        deep_analysis=current_session["deep_analysis"],
        confidence_score=current_session.get("analysis_confidence", 0.85)
    )

    print(f"  ✓ Generated {len(insights)} insights", flush=True)
    for i, insight in enumerate(insights, 1):
        print(f"    {i}. {insight[:80]}...", flush=True)

    # Step 3: Build context based on compaction strategy
    strategy = os.getenv("ROADMAP_COMPACTION_STRATEGY", "hierarchical").lower()
    print(f"\n[Step 3/5] Building context (compaction strategy: {strategy})...", flush=True)

    context = build_context(patient_id, session_id, insights, supabase)

    print(f"  ✓ Context built ({len(json.dumps(context))} characters)", flush=True)

    # Step 4: Generate roadmap
    print("\n[Step 4/5] Generating roadmap (GPT-5.2)...", flush=True)

    # Count sessions analyzed
    all_sessions_result = supabase.table("therapy_sessions") \
        .select("id, prose_analysis") \
        .eq("patient_id", patient_id) \
        .execute()

    sessions_with_wave2 = [s for s in all_sessions_result.data if s.get("prose_analysis")]
    sessions_analyzed = len(sessions_with_wave2)
    total_sessions = len(all_sessions_result.data)

    generator = RoadmapGenerator()

    # Build current session data for roadmap
    current_session_data = {
        "wave1": {
            "session_id": session_id,
            "session_date": current_session["session_date"],
            "mood_score": current_session["mood_score"],
            "topics": current_session["topics"],
            "action_items": current_session["action_items"],
            "technique": current_session["technique"],
            "summary": current_session["summary"],
        },
        "wave2": current_session["deep_analysis"],
        "insights": insights
    }

    result = generator.generate_roadmap(
        patient_id=UUID(patient_id),
        current_session=current_session_data,
        context=context,
        sessions_analyzed=sessions_analyzed,
        total_sessions=total_sessions
    )

    roadmap_data = result["roadmap"]
    metadata = result["metadata"]

    print(f"  ✓ Roadmap generated", flush=True)
    print(f"    Summary: {roadmap_data['summary'][:80]}...", flush=True)
    print(f"    Achievements: {len(roadmap_data['achievements'])} items", flush=True)
    print(f"    Current Focus: {len(roadmap_data['currentFocus'])} items", flush=True)
    print(f"    Sections: {len(roadmap_data['sections'])} sections", flush=True)

    # Step 5: Update database
    print("\n[Step 5/5] Updating database...", flush=True)

    # Get current version number
    versions_result = supabase.table("roadmap_versions") \
        .select("version") \
        .eq("patient_id", patient_id) \
        .order("version", desc=True) \
        .limit(1) \
        .execute()

    current_version = versions_result.data[0]["version"] if versions_result.data else 0
    new_version = current_version + 1

    # Insert new version
    supabase.table("roadmap_versions").insert({
        "patient_id": patient_id,
        "version": new_version,
        "roadmap_data": roadmap_data,
        "metadata": metadata,
        "generation_context": context,  # Store for debugging
        "cost": estimate_cost(context, roadmap_data),  # Estimate based on tokens
        "generation_duration_ms": metadata["generation_duration_ms"]
    }).execute()

    print(f"  ✓ Version {new_version} saved to roadmap_versions", flush=True)

    # Upsert to patient_roadmap (latest version)
    supabase.table("patient_roadmap").upsert({
        "patient_id": patient_id,
        "roadmap_data": roadmap_data,
        "metadata": metadata,
        "updated_at": datetime.now().isoformat()
    }, on_conflict="patient_id").execute()

    print(f"  ✓ Latest roadmap updated in patient_roadmap", flush=True)

    print(f"\n{'='*60}", flush=True)
    print(f"ROADMAP GENERATION COMPLETE", flush=True)
    print(f"  Patient: {patient_id}", flush=True)
    print(f"  Version: {new_version}", flush=True)
    print(f"  Sessions analyzed: {sessions_analyzed}/{total_sessions}", flush=True)
    print(f"  Strategy: {metadata['compaction_strategy']}", flush=True)
    print(f"  Duration: {metadata['generation_duration_ms']}ms", flush=True)
    print(f"{'='*60}\n", flush=True)


def build_context(patient_id: str, current_session_id: str, current_insights: list[str], supabase) -> dict:
    """
    Build context based on compaction strategy.

    Returns context dict with structure specific to the selected strategy.
    """
    strategy = os.getenv("ROADMAP_COMPACTION_STRATEGY", "hierarchical").lower()

    if strategy == "full":
        return build_full_context(patient_id, current_session_id, supabase)
    elif strategy == "progressive":
        return build_progressive_context(patient_id, current_session_id, supabase)
    elif strategy == "hierarchical":
        return build_hierarchical_context(patient_id, current_session_id, current_insights, supabase)
    else:
        raise ValueError(f"Unknown compaction strategy: {strategy}")


def build_full_context(patient_id: str, current_session_id: str, supabase) -> dict:
    """Build full context (all previous sessions' raw data)"""
    # Get all previous sessions (excluding current)
    sessions_result = supabase.table("therapy_sessions") \
        .select("*") \
        .eq("patient_id", patient_id) \
        .neq("id", current_session_id) \
        .order("session_date") \
        .execute()

    # Build nested context (same structure as Wave 2)
    cumulative_context = None

    for session in sessions_result.data:
        session_context = {
            f"session_{session['id'][:8]}_wave1": {
                "session_id": session["id"],
                "session_date": session["session_date"],
                "mood_score": session["mood_score"],
                "topics": session["topics"],
                "summary": session["summary"]
            },
            f"session_{session['id'][:8]}_wave2": session["deep_analysis"]
        }

        if cumulative_context:
            session_context["previous_context"] = cumulative_context

        cumulative_context = session_context

    return cumulative_context or {}


def build_progressive_context(patient_id: str, current_session_id: str, supabase) -> dict:
    """Build progressive context (previous roadmap only)"""
    # Get previous roadmap
    roadmap_result = supabase.table("patient_roadmap") \
        .select("roadmap_data") \
        .eq("patient_id", patient_id) \
        .execute()

    if roadmap_result.data:
        return {"previous_roadmap": roadmap_result.data[0]["roadmap_data"]}
    else:
        return {}  # First roadmap, no previous context


def build_hierarchical_context(patient_id: str, current_session_id: str, current_insights: list[str], supabase) -> dict:
    """
    Build hierarchical context (tiered summaries)

    Tier 1: Last 1-3 sessions - Full insights (3-5 per session)
    Tier 2: Mid-range (sessions 4-7) - Paragraph summaries
    Tier 3: Long-term (sessions 8+) - Journey arc summary
    """
    # Get all previous sessions with Wave 2 complete
    sessions_result = supabase.table("therapy_sessions") \
        .select("id, session_date, deep_analysis, prose_analysis") \
        .eq("patient_id", patient_id) \
        .neq("id", current_session_id) \
        .order("session_date") \
        .execute()

    sessions_with_wave2 = [s for s in sessions_result.data if s.get("prose_analysis")]
    num_sessions = len(sessions_with_wave2)

    context = {
        "tier1_insights": [],  # Last 1-3 sessions (full insights)
        "tier2_summaries": [],  # Sessions 4-7 (paragraph summaries)
        "tier3_arc": None,  # Sessions 8+ (journey arc)
        "previous_roadmap": None
    }

    # Get previous roadmap if exists
    roadmap_result = supabase.table("patient_roadmap") \
        .select("roadmap_data") \
        .eq("patient_id", patient_id) \
        .execute()

    if roadmap_result.data:
        context["previous_roadmap"] = roadmap_result.data[0]["roadmap_data"]

    # Distribute sessions into tiers (from most recent backwards)
    sessions_reversed = list(reversed(sessions_with_wave2))

    # Tier 1: Last 1-3 sessions (full insights)
    tier1_sessions = sessions_reversed[:3]
    for session in tier1_sessions:
        # Extract insights from deep_analysis
        deep_analysis = session.get("deep_analysis", {})
        insights = []

        # Extract key insights from deep_analysis structure
        if "breakthrough_patterns" in deep_analysis:
            insights.extend(deep_analysis["breakthrough_patterns"][:2])
        if "themes" in deep_analysis:
            insights.extend([theme["description"] for theme in deep_analysis.get("themes", [])[:2]])

        context["tier1_insights"].append({
            "session_date": session["session_date"],
            "insights": insights[:5]  # Max 5 insights per session
        })

    # Tier 2: Sessions 4-7 (paragraph summaries)
    if num_sessions >= 4:
        tier2_sessions = sessions_reversed[3:7]
        for session in tier2_sessions:
            prose = session.get("prose_analysis", "")
            # Use first 300 characters as summary
            summary = prose[:300] + "..." if len(prose) > 300 else prose
            context["tier2_summaries"].append({
                "session_date": session["session_date"],
                "summary": summary
            })

    # Tier 3: Sessions 8+ (journey arc - combine into single narrative)
    if num_sessions >= 8:
        tier3_sessions = sessions_reversed[7:]
        arc_pieces = []
        for session in tier3_sessions:
            prose = session.get("prose_analysis", "")
            # Extract first sentence or ~100 characters
            first_sentence = prose.split('.')[0] if prose else ""
            arc_pieces.append(f"{session['session_date']}: {first_sentence}")

        context["tier3_arc"] = " | ".join(arc_pieces)

    return context


def estimate_cost(context: dict, roadmap: dict) -> float:
    """Estimate generation cost based on token counts (GPT-5.2 pricing)"""
    # Token estimation: 1 token ~ 4 characters
    input_tokens = len(json.dumps(context)) / 4
    output_tokens = len(json.dumps(roadmap)) / 4

    # GPT-5.2: $1.75/M input, $14.00/M output
    return round((input_tokens * 1.75 + output_tokens * 14.00) / 1_000_000, 6)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/generate_roadmap.py <patient_id> <session_id>")
        sys.exit(1)

    patient_id = sys.argv[1]
    session_id = sys.argv[2]

    generate_roadmap_for_session(patient_id, session_id)
