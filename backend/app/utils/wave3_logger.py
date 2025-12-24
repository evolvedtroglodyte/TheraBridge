"""
Wave3 Logger - Logging for Your Journey and Session Bridge generation

Extends PipelineLogger pattern to support Wave 3 operations:
- Your Journey roadmap generation
- Session Bridge generation

Logs to:
- stdout (for Railway dashboard and debugging)
- File (structured JSON logs)
- Database (pipeline_events table)

Usage:
    from app.utils.wave3_logger import Wave3Logger, Wave3Phase, Wave3Event

    logger = Wave3Logger(patient_id, Wave3Phase.YOUR_JOURNEY)
    logger.log_event(Wave3Event.START, details={"version": 1})
    logger.log_event(Wave3Event.COMPACTION, details={"strategy": "hierarchical"})
    logger.log_event(Wave3Event.COMPLETE, duration_ms=25000, details={"version": 5})
"""

import logging
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum

# Configure module logger
logger = logging.getLogger(__name__)


class Wave3Phase(str, Enum):
    """Wave 3 phases."""
    YOUR_JOURNEY = "your_journey"
    SESSION_BRIDGE = "session_bridge"


class Wave3Event(str, Enum):
    """Wave 3 events."""
    # Lifecycle events
    START = "START"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"

    # Your Journey specific events
    CONTEXT_BUILD = "CONTEXT_BUILD"
    COMPACTION = "COMPACTION"
    ROADMAP_GENERATE = "ROADMAP_GENERATE"
    VERSION_SAVE = "VERSION_SAVE"

    # Session Bridge specific events
    INSIGHTS_EXTRACT = "INSIGHTS_EXTRACT"
    BRIDGE_GENERATE = "BRIDGE_GENERATE"
    BRIDGE_SAVE = "BRIDGE_SAVE"

    # Shared events
    DB_UPDATE = "DB_UPDATE"
    COST_TRACK = "COST_TRACK"


class Wave3Logger:
    """
    Logger for Wave 3 operations (Your Journey and Session Bridge).

    Supports logging to stdout, file, and database (pipeline_events table).
    Compatible with existing PipelineLogger pattern for SSE integration.
    """

    def __init__(self, patient_id: str, phase: Wave3Phase):
        """
        Initialize Wave3 logger.

        Args:
            patient_id: UUID of the patient
            phase: Wave3Phase (YOUR_JOURNEY or SESSION_BRIDGE)
        """
        self.patient_id = patient_id
        self.phase = phase
        self._logger = logging.getLogger(f"wave3.{phase.value}")

        # Ensure log directory exists
        self.log_dir = Path(__file__).parent.parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)

        # Create patient-specific log file
        self.log_file = self.log_dir / f"wave3_{patient_id}.log"

    def log_event(
        self,
        event: Wave3Event,
        session_id: Optional[str] = None,
        session_number: Optional[int] = None,
        version_number: Optional[int] = None,
        status: str = "success",
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        cost: Optional[float] = None
    ):
        """
        Log a structured event.

        Args:
            event: Wave3Event type
            session_id: Optional session UUID
            session_number: Optional session number (1-N)
            version_number: Optional version number for roadmap/bridge
            status: Status string (success, failed, skipped)
            details: Optional dict with additional details
            duration_ms: Optional duration in milliseconds
            cost: Optional cost in USD
        """
        timestamp = datetime.utcnow()

        # Build structured log entry
        log_entry = {
            "timestamp": timestamp.isoformat() + "Z",
            "patient_id": self.patient_id,
            "phase": self.phase.value,
            "event": event.value,
            "status": status,
        }

        if session_id:
            log_entry["session_id"] = session_id
        if session_number is not None:
            log_entry["session_number"] = session_number
        if version_number is not None:
            log_entry["version_number"] = version_number
        if duration_ms is not None:
            log_entry["duration_ms"] = round(duration_ms, 2)
        if cost is not None:
            log_entry["cost"] = round(cost, 6)
        if details:
            log_entry["details"] = details

        # Format for human readability (stdout)
        version_info = f"v{version_number}" if version_number is not None else ""
        session_info = f"session_{session_number}" if session_number is not None else ""
        duration_info = f"({duration_ms:.0f}ms)" if duration_ms else ""
        cost_info = f"[${cost:.6f}]" if cost else ""
        status_display = status.upper() if status != "success" else "✓"

        context = " ".join(filter(None, [version_info, session_info]))
        context_str = f"[{context}]" if context else ""

        log_message = (
            f"[{self.phase.value.upper()}] {context_str} "
            f"{event.value} {status_display} {duration_info} {cost_info}"
        ).strip()

        # Remove extra spaces
        log_message = " ".join(log_message.split())

        # Log to stdout (for Railway dashboard)
        if status == "failed":
            self._logger.error(log_message)
            print(f"❌ {log_message}", flush=True)
        else:
            self._logger.info(log_message)
            print(f"📝 {log_message}", flush=True)

        # Write to file (structured JSON)
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"[Wave3Logger] Failed to write to file: {e}", flush=True)

        # Write to database
        self._write_event_to_database(log_entry)

    def _write_event_to_database(self, log_entry: dict):
        """Write event to pipeline_events table."""
        try:
            from app.database import get_supabase
            db = get_supabase()

            # Build metadata with all extra fields
            metadata = log_entry.get("details", {}) or {}
            if log_entry.get("version_number") is not None:
                metadata["version_number"] = log_entry["version_number"]
            if log_entry.get("session_number") is not None:
                metadata["session_number"] = log_entry["session_number"]
            if log_entry.get("duration_ms") is not None:
                metadata["duration_ms"] = log_entry["duration_ms"]
            if log_entry.get("cost") is not None:
                metadata["cost"] = log_entry["cost"]

            # Insert event into pipeline_events table
            response = db.table("pipeline_events").insert({
                "patient_id": log_entry["patient_id"],
                "session_id": log_entry.get("session_id"),
                "phase": log_entry["phase"],  # "your_journey" or "session_bridge"
                "event": log_entry["event"],
                "status": log_entry["status"],
                "message": "",
                "metadata": metadata,
                "consumed": False
            }).execute()

            if response.data:
                logger.debug(f"Wave3 event logged to DB: {log_entry['phase']} {log_entry['event']}")
            else:
                print(f"[Wave3Logger] DB insert returned no data", flush=True)

        except Exception as e:
            # Don't fail the main operation if logging fails
            print(f"[Wave3Logger] DB write error: {e}", flush=True)
            logger.warning(f"Failed to log Wave3 event to database: {e}")

    def log_start(
        self,
        session_number: Optional[int] = None,
        version_number: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Convenience method to log start event."""
        self.log_event(
            Wave3Event.START,
            session_number=session_number,
            version_number=version_number,
            details=details
        )

    def log_complete(
        self,
        version_number: Optional[int] = None,
        duration_ms: Optional[float] = None,
        cost: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Convenience method to log complete event."""
        self.log_event(
            Wave3Event.COMPLETE,
            version_number=version_number,
            duration_ms=duration_ms,
            cost=cost,
            details=details
        )

    def log_failed(
        self,
        error: str,
        version_number: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Convenience method to log failed event."""
        error_details = {"error": error}
        if details:
            error_details.update(details)
        self.log_event(
            Wave3Event.FAILED,
            version_number=version_number,
            status="failed",
            details=error_details
        )

    def log_cost(
        self,
        task: str,
        model: str,
        cost: float,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float
    ):
        """Log cost tracking event."""
        self.log_event(
            Wave3Event.COST_TRACK,
            cost=cost,
            duration_ms=duration_ms,
            details={
                "task": task,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        )


# =============================================================================
# Factory functions
# =============================================================================

def create_your_journey_logger(patient_id: str) -> Wave3Logger:
    """Create a logger for Your Journey operations."""
    return Wave3Logger(patient_id, Wave3Phase.YOUR_JOURNEY)


def create_session_bridge_logger(patient_id: str) -> Wave3Logger:
    """Create a logger for Session Bridge operations."""
    return Wave3Logger(patient_id, Wave3Phase.SESSION_BRIDGE)
