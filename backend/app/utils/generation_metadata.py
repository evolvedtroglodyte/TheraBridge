"""
Generation Metadata Utilities

CRUD operations and editing utilities for the generation_metadata table.
This table uses polymorphic foreign keys to link metadata to either:
- your_journey_versions (Your Journey roadmap)
- session_bridge_versions (Session Bridge)

Design decisions (from planning):
- Q97: Trust callers, let database enforce types
- Q98: Require UUID objects only (strict type safety)
- Q99: Use .single() and return dict (enforces polymorphic constraint)
- Q86: CRUD + editing utilities for specific fields
- Q87: Edits only affect generation_metadata table (normalized source of truth)

Usage:
    from app.utils.generation_metadata import (
        create_generation_metadata,
        get_generation_metadata,
        update_sessions_analyzed,
    )

    # Create metadata for Your Journey version
    metadata = create_generation_metadata(
        db=supabase,
        your_journey_version_id=version_id,
        sessions_analyzed=5,
        total_sessions=10,
        model_used="gpt-5.2",
        generation_timestamp=datetime.now(),
        generation_duration_ms=25000,
    )
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

logger = logging.getLogger(__name__)


# ============================================================================
# Validation Helpers
# ============================================================================

def validate_exactly_one_fk(
    your_journey_version_id: Optional[UUID],
    session_bridge_version_id: Optional[UUID]
) -> None:
    """
    Validate that exactly one foreign key is provided.

    The polymorphic design requires exactly one FK to be set:
    - Either your_journey_version_id OR session_bridge_version_id
    - But not both, and not neither

    Raises:
        ValueError: If zero or both FKs are provided
    """
    fks_set = sum([
        your_journey_version_id is not None,
        session_bridge_version_id is not None
    ])

    if fks_set == 0:
        raise ValueError("Must provide exactly one version_id (your_journey_version_id OR session_bridge_version_id)")
    elif fks_set > 1:
        raise ValueError("Cannot set both your_journey_version_id AND session_bridge_version_id")


# ============================================================================
# CRUD Operations
# ============================================================================

def create_generation_metadata(
    db,
    your_journey_version_id: Optional[UUID] = None,
    session_bridge_version_id: Optional[UUID] = None,
    sessions_analyzed: int = 0,
    total_sessions: int = 0,
    model_used: str = "",
    generation_timestamp: Optional[datetime] = None,
    generation_duration_ms: int = 0,
    last_session_id: Optional[UUID] = None,
    compaction_strategy: Optional[str] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a new generation_metadata record.

    Args:
        db: Supabase client
        your_journey_version_id: FK to your_journey_versions (mutually exclusive with session_bridge_version_id)
        session_bridge_version_id: FK to session_bridge_versions (mutually exclusive with your_journey_version_id)
        sessions_analyzed: Number of sessions analyzed for this generation
        total_sessions: Total sessions available at time of generation
        model_used: Model name used for generation (e.g., "gpt-5.2")
        generation_timestamp: When generation occurred (defaults to now)
        generation_duration_ms: Generation duration in milliseconds
        last_session_id: ID of the most recent session included
        compaction_strategy: Strategy used (e.g., "hierarchical", "progressive")
        metadata_json: Additional metadata as JSONB

    Returns:
        Dict containing the created metadata record

    Raises:
        ValueError: If FK validation fails
    """
    # Validate polymorphic FK constraint
    validate_exactly_one_fk(your_journey_version_id, session_bridge_version_id)

    # Build insert data
    insert_data = {
        "sessions_analyzed": sessions_analyzed,
        "total_sessions": total_sessions,
        "model_used": model_used,
        "generation_timestamp": (generation_timestamp or datetime.now()).isoformat(),
        "generation_duration_ms": generation_duration_ms,
    }

    # Add optional FKs (one must be set, validated above)
    if your_journey_version_id:
        insert_data["your_journey_version_id"] = str(your_journey_version_id)
    if session_bridge_version_id:
        insert_data["session_bridge_version_id"] = str(session_bridge_version_id)

    # Add optional fields
    if last_session_id:
        insert_data["last_session_id"] = str(last_session_id)
    if compaction_strategy:
        insert_data["compaction_strategy"] = compaction_strategy
    if metadata_json:
        insert_data["metadata_json"] = metadata_json

    # Execute insert
    result = db.table("generation_metadata").insert(insert_data).execute()

    if result.data:
        logger.info(f"Created generation_metadata: {result.data[0]['id']}")
        return result.data[0]
    else:
        logger.error("Failed to create generation_metadata")
        raise RuntimeError("Failed to create generation_metadata record")


def get_generation_metadata(db, metadata_id: UUID) -> Optional[Dict[str, Any]]:
    """
    Get a generation_metadata record by ID.

    Args:
        db: Supabase client
        metadata_id: UUID of the metadata record

    Returns:
        Dict containing the metadata record, or None if not found
    """
    result = db.table("generation_metadata") \
        .select("*") \
        .eq("id", str(metadata_id)) \
        .maybe_single() \
        .execute()

    return result.data


def get_generation_metadata_by_version(
    db,
    your_journey_version_id: Optional[UUID] = None,
    session_bridge_version_id: Optional[UUID] = None
) -> Optional[Dict[str, Any]]:
    """
    Get generation_metadata by version FK.

    Args:
        db: Supabase client
        your_journey_version_id: FK to your_journey_versions
        session_bridge_version_id: FK to session_bridge_versions

    Returns:
        Dict containing the metadata record, or None if not found

    Raises:
        ValueError: If FK validation fails
    """
    # Validate exactly one FK
    validate_exactly_one_fk(your_journey_version_id, session_bridge_version_id)

    query = db.table("generation_metadata").select("*")

    if your_journey_version_id:
        query = query.eq("your_journey_version_id", str(your_journey_version_id))
    elif session_bridge_version_id:
        query = query.eq("session_bridge_version_id", str(session_bridge_version_id))

    result = query.maybe_single().execute()

    return result.data


def update_generation_metadata(
    db,
    metadata_id: UUID,
    **updates
) -> Dict[str, Any]:
    """
    Update a generation_metadata record.

    Allowed fields: sessions_analyzed, total_sessions, model_used,
    generation_timestamp, generation_duration_ms, last_session_id,
    compaction_strategy, metadata_json

    Forbidden fields: id, your_journey_version_id, session_bridge_version_id, created_at
    (FKs are immutable after creation to prevent orphaned metadata)

    Args:
        db: Supabase client
        metadata_id: UUID of the metadata record
        **updates: Field-value pairs to update

    Returns:
        Dict containing the updated record

    Raises:
        ValueError: If attempting to update forbidden fields
        RuntimeError: If record not found
    """
    # Forbidden fields (immutable after creation)
    forbidden_fields = {"id", "your_journey_version_id", "session_bridge_version_id", "created_at"}

    # Check for forbidden updates
    forbidden_updates = set(updates.keys()) & forbidden_fields
    if forbidden_updates:
        raise ValueError(f"Cannot update immutable fields: {forbidden_updates}")

    # Allowed fields
    allowed_fields = {
        "sessions_analyzed", "total_sessions", "model_used",
        "generation_timestamp", "generation_duration_ms", "last_session_id",
        "compaction_strategy", "metadata_json"
    }

    # Filter to allowed fields only
    update_data = {}
    for key, value in updates.items():
        if key in allowed_fields:
            # Convert UUIDs to strings, timestamps to ISO format
            if isinstance(value, UUID):
                update_data[key] = str(value)
            elif isinstance(value, datetime):
                update_data[key] = value.isoformat()
            else:
                update_data[key] = value

    if not update_data:
        logger.warning(f"No valid fields to update for metadata {metadata_id}")
        return get_generation_metadata(db, metadata_id)

    # Execute update
    result = db.table("generation_metadata") \
        .update(update_data) \
        .eq("id", str(metadata_id)) \
        .execute()

    if result.data:
        logger.info(f"Updated generation_metadata {metadata_id}: {list(update_data.keys())}")
        return result.data[0]
    else:
        raise RuntimeError(f"Failed to update generation_metadata {metadata_id} (not found?)")


def delete_generation_metadata(db, metadata_id: UUID) -> bool:
    """
    Delete a generation_metadata record.

    Args:
        db: Supabase client
        metadata_id: UUID of the metadata record

    Returns:
        True if deleted, False if not found
    """
    result = db.table("generation_metadata") \
        .delete() \
        .eq("id", str(metadata_id)) \
        .execute()

    deleted = len(result.data) > 0 if result.data else False

    if deleted:
        logger.info(f"Deleted generation_metadata: {metadata_id}")
    else:
        logger.warning(f"generation_metadata not found for deletion: {metadata_id}")

    return deleted


# ============================================================================
# Editing Utilities (convenience wrappers for common updates)
# ============================================================================

def update_sessions_analyzed(db, metadata_id: UUID, new_count: int) -> Dict[str, Any]:
    """
    Update the sessions_analyzed count for a metadata record.

    Args:
        db: Supabase client
        metadata_id: UUID of the metadata record
        new_count: New sessions_analyzed value

    Returns:
        Dict containing the updated record
    """
    return update_generation_metadata(db, metadata_id, sessions_analyzed=new_count)


def update_model_used(db, metadata_id: UUID, new_model: str) -> Dict[str, Any]:
    """
    Update the model_used for a metadata record.

    Args:
        db: Supabase client
        metadata_id: UUID of the metadata record
        new_model: New model name (e.g., "gpt-5.2")

    Returns:
        Dict containing the updated record
    """
    return update_generation_metadata(db, metadata_id, model_used=new_model)


def update_generation_timestamp(db, metadata_id: UUID, new_timestamp: datetime) -> Dict[str, Any]:
    """
    Update the generation_timestamp for a metadata record.

    Args:
        db: Supabase client
        metadata_id: UUID of the metadata record
        new_timestamp: New timestamp

    Returns:
        Dict containing the updated record
    """
    return update_generation_metadata(db, metadata_id, generation_timestamp=new_timestamp)


def update_total_sessions(db, metadata_id: UUID, new_total: int) -> Dict[str, Any]:
    """
    Update the total_sessions count for a metadata record.

    Args:
        db: Supabase client
        metadata_id: UUID of the metadata record
        new_total: New total_sessions value

    Returns:
        Dict containing the updated record
    """
    return update_generation_metadata(db, metadata_id, total_sessions=new_total)


def update_compaction_strategy(db, metadata_id: UUID, new_strategy: str) -> Dict[str, Any]:
    """
    Update the compaction_strategy for a metadata record.

    Args:
        db: Supabase client
        metadata_id: UUID of the metadata record
        new_strategy: New strategy name (e.g., "hierarchical", "progressive")

    Returns:
        Dict containing the updated record
    """
    return update_generation_metadata(db, metadata_id, compaction_strategy=new_strategy)


# ============================================================================
# Query Utilities
# ============================================================================

def list_metadata_for_patient(
    db,
    patient_id: UUID,
    feature: str = "all"
) -> list[Dict[str, Any]]:
    """
    List all generation_metadata records for a patient.

    Args:
        db: Supabase client
        patient_id: Patient UUID
        feature: "your_journey", "session_bridge", or "all"

    Returns:
        List of metadata records
    """
    if feature == "your_journey":
        # Join through your_journey_versions
        result = db.table("generation_metadata") \
            .select("*, your_journey_versions!inner(patient_id)") \
            .eq("your_journey_versions.patient_id", str(patient_id)) \
            .order("created_at", desc=True) \
            .execute()
    elif feature == "session_bridge":
        # Join through session_bridge_versions
        result = db.table("generation_metadata") \
            .select("*, session_bridge_versions!inner(patient_id)") \
            .eq("session_bridge_versions.patient_id", str(patient_id)) \
            .order("created_at", desc=True) \
            .execute()
    else:
        # Get all (union via two queries)
        yj_result = db.table("generation_metadata") \
            .select("*, your_journey_versions!inner(patient_id)") \
            .eq("your_journey_versions.patient_id", str(patient_id)) \
            .execute()

        sb_result = db.table("generation_metadata") \
            .select("*, session_bridge_versions!inner(patient_id)") \
            .eq("session_bridge_versions.patient_id", str(patient_id)) \
            .execute()

        # Combine and dedupe by ID
        all_records = (yj_result.data or []) + (sb_result.data or [])
        seen_ids = set()
        result_data = []
        for record in all_records:
            if record["id"] not in seen_ids:
                seen_ids.add(record["id"])
                result_data.append(record)

        # Sort by created_at descending
        result_data.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result_data

    return result.data or []


def get_latest_metadata_for_patient(
    db,
    patient_id: UUID,
    feature: str
) -> Optional[Dict[str, Any]]:
    """
    Get the most recent generation_metadata for a patient and feature.

    Args:
        db: Supabase client
        patient_id: Patient UUID
        feature: "your_journey" or "session_bridge"

    Returns:
        Dict containing the latest metadata record, or None
    """
    if feature not in ("your_journey", "session_bridge"):
        raise ValueError(f"feature must be 'your_journey' or 'session_bridge', got '{feature}'")

    records = list_metadata_for_patient(db, patient_id, feature)
    return records[0] if records else None
