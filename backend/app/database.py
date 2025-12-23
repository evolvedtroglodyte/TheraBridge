"""
Database Connection - Supabase PostgreSQL
"""

from supabase import create_client, Client
from app.config import settings
import logging

logger = logging.getLogger(__name__)


# Global Supabase client
_supabase_client: Client = None


def get_supabase() -> Client:
    """
    Get Supabase client instance (singleton pattern)

    Returns:
        Client: Supabase client
    """
    global _supabase_client

    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            logger.info("✓ Supabase client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    return _supabase_client


def get_supabase_admin() -> Client:
    """
    Get Supabase client with service role key (bypasses RLS)
    Use for administrative operations only

    Returns:
        Client: Supabase admin client
    """
    try:
        admin_client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
        return admin_client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase admin client: {e}")
        raise


# Dependency for FastAPI
async def get_db() -> Client:
    """
    FastAPI dependency for database access

    Usage:
        @router.get("/sessions")
        async def get_sessions(db: Client = Depends(get_db)):
            ...
    """
    return get_supabase()


# Helper functions for common operations
def execute_query(query_builder, handle_error=True):
    """
    Execute Supabase query with error handling

    Args:
        query_builder: Supabase query builder
        handle_error: Whether to raise exception on error

    Returns:
        Query response data

    Raises:
        Exception: If query fails and handle_error is True
    """
    try:
        response = query_builder.execute()
        return response.data
    except Exception as e:
        logger.error(f"Database query error: {e}")
        if handle_error:
            raise
        return None


async def get_user_by_email(email: str) -> dict:
    """Get user by email"""
    db = get_supabase()
    response = db.table("users").select("*").eq("email", email).execute()
    return response.data[0] if response.data else None


async def get_patient_sessions(patient_id: str, limit: int = 50) -> list:
    """Get therapy sessions for a patient"""
    db = get_supabase()
    response = (
        db.table("therapy_sessions")
        .select("*")
        .eq("patient_id", patient_id)
        .order("session_date", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data


async def get_session_with_breakthrough(session_id: str) -> dict:
    """Get session with breakthrough details"""
    db = get_supabase()

    # Get session
    session_response = (
        db.table("therapy_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )

    if not session_response.data:
        return None

    session = session_response.data

    # Get all breakthroughs for session
    if session.get("has_breakthrough"):
        breakthroughs_response = (
            db.table("breakthrough_history")
            .select("*")
            .eq("session_id", session_id)
            .order("confidence_score", desc=True)
            .execute()
        )
        session["all_breakthroughs"] = breakthroughs_response.data

    return session


async def store_breakthrough_analysis(
    session_id: str,
    has_breakthrough: bool,
    primary_breakthrough: dict = None,
    all_breakthroughs: list = None
):
    """
    Store breakthrough detection results

    Args:
        session_id: Session UUID
        has_breakthrough: Whether breakthrough was detected
        primary_breakthrough: Primary breakthrough dict
        all_breakthroughs: List of all breakthrough candidates
    """
    db = get_supabase()

    # Update session
    update_data = {
        "has_breakthrough": has_breakthrough,
        "breakthrough_analyzed_at": "now()",
    }

    if primary_breakthrough:
        update_data["breakthrough_data"] = primary_breakthrough

    session_update = (
        db.table("therapy_sessions")
        .update(update_data)
        .eq("id", session_id)
        .execute()
    )

    # Store in breakthrough_history
    if all_breakthroughs:
        for i, bt in enumerate(all_breakthroughs):
            history_entry = {
                "session_id": session_id,
                "breakthrough_type": bt["type"],
                "description": bt["description"],
                "evidence": bt["evidence"],
                "confidence_score": bt["confidence"],
                "timestamp_start": bt.get("timestamp_start", 0),
                "timestamp_end": bt.get("timestamp_end", 0),
                "dialogue_excerpt": bt.get("dialogue_excerpt", []),
                "is_primary": (i == 0),  # First one is primary
            }

            db.table("breakthrough_history").insert(history_entry).execute()

    logger.info(f"✓ Stored breakthrough analysis for session {session_id}")
    return session_update.data
