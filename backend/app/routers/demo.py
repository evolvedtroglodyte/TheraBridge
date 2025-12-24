"""
Demo Mode API Router
Handles demo initialization, reset, and status
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from pathlib import Path
import logging
import subprocess
import asyncio
import sys
import os

from app.database import get_db, get_supabase_admin
from app.middleware.demo_auth import get_demo_user, require_demo_auth
from supabase import Client

router = APIRouter(prefix="/api/demo", tags=["demo"])
logger = logging.getLogger(__name__)

# In-memory tracking of analysis completion (keyed by patient_id)
analysis_status = {}

# In-memory tracking of running processes (keyed by patient_id)
# Stores subprocess references so they can be terminated
running_processes = {}


# ============================================================================
# Request/Response Models
# ============================================================================

class DemoInitResponse(BaseModel):
    """Response for demo initialization"""
    demo_token: str
    patient_id: str
    session_ids: List[str]
    expires_at: str
    message: str
    analysis_status: str  # "pending", "processing", "completed"


class DemoResetResponse(BaseModel):
    """Response for demo reset"""
    patient_id: str
    session_ids: List[str]
    message: str


class SessionStatus(BaseModel):
    """Individual session completion status with full analysis data"""
    # Existing fields
    session_id: str
    session_date: str
    has_transcript: bool
    wave1_complete: bool
    wave2_complete: bool

    # NEW: Wave 1 analysis fields (nullable until Wave 1 completes)
    topics: Optional[list[str]] = None
    mood_score: Optional[float] = None
    summary: Optional[str] = None
    technique: Optional[str] = None
    action_items: Optional[list[str]] = None

    # NEW: Wave 2 analysis fields (nullable until Wave 2 completes)
    prose_analysis: Optional[str] = None
    deep_analysis: Optional[dict] = None

    # NEW: Timestamps for change detection
    last_wave1_update: Optional[str] = None  # ISO timestamp
    last_wave2_update: Optional[str] = None  # ISO timestamp

    # NEW: Change detection flag
    changed_since_last_poll: bool = False


class DemoStatusResponse(BaseModel):
    """Enhanced demo status with per-session completion tracking"""
    demo_token: str
    patient_id: str
    session_count: int
    created_at: str
    expires_at: str
    is_expired: bool
    analysis_status: str  # "pending" | "processing" | "wave1_complete" | "wave2_complete"
    wave1_complete: int  # Total sessions with Wave 1 complete
    wave2_complete: int  # Total sessions with Wave 2 complete
    sessions: List[SessionStatus]  # Per-session status
    roadmap_updated_at: Optional[str] = None  # PR #3: Timestamp of last roadmap update

    # PR #3 Phase 4: Processing state fields
    processing_state: str  # "running" | "stopped" | "complete" | "not_started"
    stopped_at_session_id: Optional[str] = None  # Which session was being processed when stopped
    can_resume: bool  # Whether resume is possible


# ============================================================================
# Background Tasks
# ============================================================================

async def populate_session_transcripts_background(patient_id: str):
    """Background task to populate session transcripts from JSON files"""
    print(f"📝 Step 1/3: Populating session transcripts for patient {patient_id}", flush=True)
    logger.info(f"📝 Populating session transcripts for patient {patient_id}")

    try:
        # Get Python executable from current environment
        python_exe = sys.executable

        # Resolve absolute path to script
        script_path = Path(__file__).parent.parent.parent / "scripts" / "seed_all_sessions.py"

        logger.info(f"Running transcript population: {python_exe} {script_path} {patient_id}")

        # Run transcript population script with environment variables (NON-BLOCKING)
        process = await asyncio.create_subprocess_exec(
            python_exe, str(script_path), patient_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=os.environ.copy()  # Pass all environment variables
        )

        # Track process for potential termination
        if patient_id not in running_processes:
            running_processes[patient_id] = {}
        running_processes[patient_id]["transcript"] = process

        # Wait for completion (async, non-blocking)
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=300  # 5 minute timeout
            )
            stdout_text = stdout.decode('utf-8') if stdout else ''
            stderr_text = stderr.decode('utf-8') if stderr else ''

            if process.returncode == 0:
                print(f"✅ Step 1/3 Complete: Session transcripts populated", flush=True)
                logger.info(f"✅ Session transcripts populated for patient {patient_id}")
                logger.info(stdout_text)
                # Show script output in Railway logs
                if stdout_text:
                    print(f"[Transcript Script Output]:\n{stdout_text}", flush=True)
            else:
                print(f"❌ Step 1/3 Failed: {stderr_text}", flush=True)
                logger.error(f"❌ Transcript population failed: {stderr_text}")
                # Show error details in Railway logs
                if stderr_text:
                    print(f"[Transcript Script Error]:\n{stderr_text}", flush=True)

        except asyncio.TimeoutError:
            logger.error(f"❌ Transcript population timeout for patient {patient_id}")
            process.kill()
            await process.wait()

    except Exception as e:
        logger.error(f"❌ Transcript population error: {e}")


async def run_wave1_analysis_background(patient_id: str):
    """Background task to run Wave 1 analysis with real-time streaming logs"""
    print(f"🚀 Step 2/3: Starting Wave 1 analysis for patient {patient_id}", flush=True)
    logger.info(f"🚀 Starting Wave 1 analysis for patient {patient_id}")

    try:
        # Get Python executable from current environment
        python_exe = sys.executable

        # Resolve absolute path to script
        script_path = Path(__file__).parent.parent.parent / "scripts" / "seed_wave1_analysis.py"

        logger.info(f"Running Wave 1 analysis: {python_exe} {script_path} {patient_id}")

        # Run Wave 1 script with STREAMING output (NON-BLOCKING)
        process = await asyncio.create_subprocess_exec(
            python_exe, str(script_path), patient_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Merge stderr into stdout
            env=os.environ.copy()  # Pass all environment variables
        )

        # Track process for potential termination
        if patient_id not in running_processes:
            running_processes[patient_id] = {}
        running_processes[patient_id]["wave1"] = process

        # Stream output line by line in real-time (async, non-blocking)
        try:
            async def stream_output():
                """Stream stdout line by line"""
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    line_text = line.decode('utf-8').rstrip()
                    print(f"[Wave1] {line_text}", flush=True)
                    logger.info(f"[Wave1] {line_text}")

            # Wait for streaming to complete with timeout
            await asyncio.wait_for(stream_output(), timeout=600)  # 10 minute timeout

            # Wait for process to complete
            await process.wait()

            if process.returncode == 0:
                print(f"✅ Step 2/3 Complete: Wave 1 analysis complete", flush=True)
                logger.info(f"✅ Wave 1 analysis complete for patient {patient_id}")
                # Mark Wave 1 as complete
                if patient_id not in analysis_status:
                    analysis_status[patient_id] = {}
                analysis_status[patient_id]["wave1_complete"] = True
                analysis_status[patient_id]["wave1_completed_at"] = datetime.now().isoformat()
            else:
                print(f"❌ Step 2/3 Failed with return code {process.returncode}", flush=True)
                logger.error(f"❌ Wave 1 analysis failed with return code {process.returncode}")

        except asyncio.TimeoutError:
            print(f"❌ Wave 1 analysis TIMEOUT (10 minutes exceeded)", flush=True)
            logger.error(f"❌ Wave 1 analysis timeout for patient {patient_id}")
            process.kill()
            await process.wait()

    except Exception as e:
        print(f"❌ Wave 1 analysis ERROR: {e}", flush=True)
        logger.error(f"❌ Wave 1 analysis error: {e}")


async def run_wave2_analysis_background(patient_id: str):
    """Background task to run Wave 2 analysis with real-time streaming logs"""
    print(f"🚀 Step 3/3: Starting Wave 2 analysis for patient {patient_id}", flush=True)
    logger.info(f"🚀 Starting Wave 2 analysis for patient {patient_id}")

    try:
        # Get Python executable from current environment
        python_exe = sys.executable

        # Resolve absolute path to script
        script_path = Path(__file__).parent.parent.parent / "scripts" / "seed_wave2_analysis.py"

        logger.info(f"Running Wave 2 analysis: {python_exe} {script_path} {patient_id}")

        # Run Wave 2 script with STREAMING output (NON-BLOCKING)
        process = await asyncio.create_subprocess_exec(
            python_exe, str(script_path), patient_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,  # Merge stderr into stdout
            env=os.environ.copy()  # Pass all environment variables
        )

        # Track process for potential termination
        if patient_id not in running_processes:
            running_processes[patient_id] = {}
        running_processes[patient_id]["wave2"] = process

        # Stream output line by line in real-time (async, non-blocking)
        try:
            async def stream_output():
                """Stream stdout line by line"""
                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    line_text = line.decode('utf-8').rstrip()
                    print(f"[Wave2] {line_text}", flush=True)
                    logger.info(f"[Wave2] {line_text}")

            # Wait for streaming to complete with timeout
            await asyncio.wait_for(stream_output(), timeout=900)  # 15 minute timeout

            # Wait for process to complete
            await process.wait()

            if process.returncode == 0:
                print(f"✅ Step 3/3 Complete: Wave 2 analysis complete", flush=True)
                logger.info(f"✅ Wave 2 analysis complete for patient {patient_id}")
                # Mark Wave 2 as complete
                if patient_id not in analysis_status:
                    analysis_status[patient_id] = {}
                analysis_status[patient_id]["wave2_complete"] = True
                analysis_status[patient_id]["wave2_completed_at"] = datetime.now().isoformat()
            else:
                print(f"❌ Step 3/3 Failed with return code {process.returncode}", flush=True)
                logger.error(f"❌ Wave 2 analysis failed with return code {process.returncode}")

        except asyncio.TimeoutError:
            print(f"❌ Wave 2 analysis TIMEOUT (15 minutes exceeded)", flush=True)
            logger.error(f"❌ Wave 2 analysis timeout for patient {patient_id}")
            process.kill()
            await process.wait()

    except Exception as e:
        print(f"❌ Wave 2 analysis ERROR: {e}", flush=True)
        logger.error(f"❌ Wave 2 analysis error: {e}")


async def run_full_initialization_pipeline(patient_id: str):
    """Run complete initialization: transcripts (blocking) → Wave 1 + Wave 2 (background)"""
    print("=" * 80, flush=True)
    print(f"🔥 BACKGROUND TASK EXECUTING: patient_id={patient_id}", flush=True)
    print("=" * 80, flush=True)
    logger.info("=" * 80)
    logger.info(f"🎬 BACKGROUND TASK STARTED: Full initialization pipeline for patient {patient_id}")
    logger.info("=" * 80)

    # Step 1: Populate transcripts from JSON files (BLOCKING - required for frontend)
    await populate_session_transcripts_background(patient_id)

    print(f"✅ Transcripts loaded - demo ready for frontend", flush=True)
    logger.info(f"✅ Transcripts loaded for patient {patient_id}")

    # Step 2 & 3: Run Wave 1 and Wave 2 in background (non-blocking)
    # Frontend will poll and update when analysis completes
    import asyncio

    async def run_wave1_then_wave2():
        """Run Wave 1, then start Wave 2 when Wave 1 completes"""
        await run_wave1_analysis_background(patient_id)
        # After Wave 1 completes, start Wave 2
        asyncio.create_task(run_wave2_analysis_background(patient_id))

    asyncio.create_task(run_wave1_then_wave2())

    print(f"🚀 Wave 1 + Wave 2 analysis running in background (non-blocking)", flush=True)
    logger.info(f"🚀 Analysis pipeline running independently for patient {patient_id}")


# ============================================================================
# Demo Endpoints
# ============================================================================

@router.post("/initialize", response_model=DemoInitResponse)
async def initialize_demo(
    db: Client = Depends(get_db),
    run_analysis: bool = True  # Query param to enable/disable analysis
):
    """
    Initialize a new demo user with 10 pre-loaded therapy sessions

    This endpoint:
    1. Generates a unique demo token (UUID)
    2. Calls seed_demo_user_sessions() SQL function
    3. Optionally triggers Wave 1 + Wave 2 analysis in background
    4. Returns demo token for localStorage storage

    Args:
        run_analysis: If True, runs Wave 1 + Wave 2 analysis in background (default: True)

    Returns:
        DemoInitResponse with token and session IDs
    """
    # Generate unique demo token
    demo_token = str(uuid4())

    print(f"🔥 DEMO INIT START: token={demo_token}", flush=True)
    logger.info(f"Initializing demo user with token: {demo_token}")

    try:
        # Call SQL function to seed demo data (v4 creates all 10 sessions)
        response = db.rpc("seed_demo_v4", {"p_demo_token": demo_token}).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to create demo user and sessions"
            )

        result = response.data[0]
        patient_id = result["patient_id"]
        session_ids = result["session_ids"]
        logger.info(f"📝 Extracted patient_id: {patient_id}, session_ids count: {len(session_ids)}")

        # Fetch patient record to get user_id, then get expiry from users table
        patient_response = db.table("patients").select("user_id").eq("id", patient_id).single().execute()
        user_id = patient_response.data["user_id"]
        logger.info(f"📝 Fetched user_id: {user_id}")

        user_response = db.table("users").select("demo_expires_at").eq("id", user_id).single().execute()
        expires_at = user_response.data["demo_expires_at"]
        logger.info(f"📝 Fetched expires_at: {expires_at}")

        logger.info(f"✓ Demo user created: {patient_id} with {len(session_ids)} sessions")

        # Initialize demo data if enabled - ALL processing happens in background
        analysis_status = "pending"
        logger.info(f"📝 run_analysis parameter: {run_analysis}")
        if run_analysis:
            # Use asyncio.create_task() instead of background_tasks to avoid blocking other requests
            # This allows multiple demo initializations to run concurrently without blocking
            import asyncio
            asyncio.create_task(run_full_initialization_pipeline(str(patient_id)))
            analysis_status = "processing"
            logger.info(f"🎬 Started full initialization pipeline (transcripts + Wave 1 + Wave 2) for patient {patient_id}")

        return DemoInitResponse(
            demo_token=demo_token,
            patient_id=str(patient_id),
            session_ids=[str(sid) for sid in session_ids],
            expires_at=expires_at,
            analysis_status=analysis_status,
            message=f"Demo initialized with {len(session_ids)} sessions. Session data loading in background (~30s)." if run_analysis else f"Demo initialized with {len(session_ids)} sessions."
        )

    except Exception as e:
        logger.error(f"Demo initialization error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize demo: {str(e)}"
        )


@router.post("/reset", response_model=DemoResetResponse)
async def reset_demo(
    request: Request,
    demo_user: dict = Depends(require_demo_auth),
    db: Client = Depends(get_db)
):
    """
    Reset demo user by deleting all sessions and re-seeding with fresh 10 sessions

    This endpoint:
    1. Validates demo token
    2. Deletes all existing sessions and patient records
    3. Calls seed_demo_v4 to recreate patient + 10 sessions
    4. Re-runs transcript population and analysis pipeline

    Returns:
        DemoResetResponse with new session IDs
    """
    demo_token = demo_user["demo_token"]
    user_id = demo_user["id"]

    # Look up current patient_id before deletion
    patient_response = db.table("patients").select("id").eq("user_id", user_id).single().execute()

    if patient_response.data:
        old_patient_id = patient_response.data["id"]
        logger.info(f"Resetting demo for user: {user_id}, patient: {old_patient_id}")

        # Delete existing sessions and patient record
        db.table("therapy_sessions").delete().eq("patient_id", old_patient_id).execute()
        db.table("patients").delete().eq("id", old_patient_id).execute()
    else:
        logger.info(f"Resetting demo for user: {user_id} (no existing patient)")

    try:
        # Re-seed using seed_demo_v4 (creates new patient + 10 sessions)
        response = db.rpc("seed_demo_v4", {"p_demo_token": demo_token}).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset demo sessions"
            )

        result = response.data[0]
        new_patient_id = result["patient_id"]
        session_ids = result["session_ids"]

        logger.info(f"✓ Demo reset complete: new patient {new_patient_id} with {len(session_ids)} sessions")

        # Re-run initialization pipeline in background
        import asyncio
        asyncio.create_task(run_full_initialization_pipeline(str(new_patient_id)))
        logger.info(f"🎬 Started initialization pipeline for reset demo (patient {new_patient_id})")

        return DemoResetResponse(
            patient_id=str(new_patient_id),
            session_ids=[str(sid) for sid in session_ids],
            message=f"Demo reset with {len(session_ids)} fresh sessions. Analysis running in background."
        )

    except Exception as e:
        logger.error(f"Demo reset error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset demo: {str(e)}"
        )


@router.get("/status", response_model=DemoStatusResponse)
async def get_demo_status(
    request: Request,
    demo_user: dict = Depends(require_demo_auth),
    db: Client = Depends(get_db)
):
    """
    Get current demo user status with per-session analysis progress

    Returns:
        DemoStatusResponse with user info, session count, and per-session completion
    """
    user_id = demo_user["id"]

    # Look up the patient record to get patient_id
    patient_response = db.table("patients").select("id").eq("user_id", user_id).single().execute()

    if not patient_response.data:
        raise HTTPException(
            status_code=404,
            detail="Patient record not found for demo user"
        )

    patient_id = patient_response.data["id"]

    # Fetch all sessions with analysis data (enhanced for delta updates)
    sessions_response = db.table("therapy_sessions").select("""
        id,
        session_date,
        transcript,
        topics,
        mood_score,
        summary,
        technique,
        action_items,
        prose_analysis,
        deep_analysis,
        topics_extracted_at,
        mood_analyzed_at,
        deep_analyzed_at,
        prose_generated_at
    """).eq("patient_id", patient_id).order("session_date").execute()

    sessions = sessions_response.data or []
    session_count = len(sessions)

    # Build per-session status with full analysis data
    session_statuses = []
    wave1_complete_count = 0
    wave2_complete_count = 0

    for session in sessions:
        # Determine Wave 1/Wave 2 completion
        has_transcript = bool(session.get("transcript"))
        wave1_complete = (session.get("topics") is not None or
                         session.get("mood_score") is not None)
        wave2_complete = session.get("prose_analysis") is not None

        if wave1_complete:
            wave1_complete_count += 1
        if wave2_complete:
            wave2_complete_count += 1

        # Get timestamps (ISO format)
        last_wave1_update = None
        if session.get("topics_extracted_at"):
            last_wave1_update = session["topics_extracted_at"]
        elif session.get("mood_analyzed_at"):
            last_wave1_update = session["mood_analyzed_at"]

        last_wave2_update = None
        if session.get("prose_generated_at"):
            last_wave2_update = session["prose_generated_at"]
        elif session.get("deep_analyzed_at"):
            last_wave2_update = session["deep_analyzed_at"]

        # Build enhanced SessionStatus
        session_statuses.append(SessionStatus(
            session_id=session["id"],
            session_date=session.get("session_date", ""),
            has_transcript=has_transcript,
            wave1_complete=wave1_complete,
            wave2_complete=wave2_complete,

            # Wave 1 fields (null if not complete)
            topics=session.get("topics") if wave1_complete else None,
            mood_score=session.get("mood_score") if wave1_complete else None,
            summary=session.get("summary") if wave1_complete else None,
            technique=session.get("technique") if wave1_complete else None,
            action_items=session.get("action_items") if wave1_complete else None,

            # Wave 2 fields (null if not complete)
            prose_analysis=session.get("prose_analysis") if wave2_complete else None,
            deep_analysis=session.get("deep_analysis") if wave2_complete else None,

            # Timestamps
            last_wave1_update=last_wave1_update,
            last_wave2_update=last_wave2_update,

            # Change detection (frontend will override this based on comparison)
            changed_since_last_poll=False
        ))

    # Determine overall analysis status
    if session_count == 0:
        # No sessions yet - still pending
        analysis_status = "pending"
    elif wave2_complete_count == session_count:
        analysis_status = "wave2_complete"
    elif wave1_complete_count == session_count:
        analysis_status = "wave1_complete"
    elif wave1_complete_count > 0 or wave2_complete_count > 0:
        analysis_status = "processing"
    else:
        analysis_status = "pending"

    # Check if expired
    from datetime import datetime
    expires_at = datetime.fromisoformat(demo_user["demo_expires_at"].replace("Z", "+00:00"))
    is_expired = expires_at < datetime.now(expires_at.tzinfo)

    # Query roadmap for updated_at timestamp (PR #3)
    roadmap_updated_at = None
    try:
        roadmap_response = db.table("patient_roadmap").select("updated_at").eq("patient_id", patient_id).execute()
        if roadmap_response.data and len(roadmap_response.data) > 0:
            roadmap_updated_at = roadmap_response.data[0].get("updated_at")
    except Exception as e:
        # Roadmap table might not exist yet (Phase 5 not complete)
        logger.debug(f"Could not query roadmap table: {e}")

    # PR #3 Phase 4: Determine processing state
    processing_state = "not_started"
    stopped_at_session_id = None
    can_resume = False

    # Check if processing is currently running (check running_processes dict)
    is_running = patient_id in running_processes and any(
        proc.returncode is None for proc in running_processes[patient_id].values() if proc
    )

    # Check if stopped (stopped flag in analysis_status dict)
    analysis_status_dict = analysis_status.get(patient_id, {})
    wave1_stopped = analysis_status_dict.get("wave1_stopped", False)
    wave2_stopped = analysis_status_dict.get("wave2_stopped", False)

    if is_running:
        processing_state = "running"
    elif wave2_complete_count == session_count:
        processing_state = "complete"
    elif wave1_stopped or wave2_stopped:
        processing_state = "stopped"
        can_resume = True

        # Find which session was being processed when stopped
        for session in sessions:
            if session.get("topics") and not session.get("prose_analysis"):
                # Wave 1 complete but Wave 2 incomplete - this is where we stopped
                stopped_at_session_id = session["id"]
                break
    elif wave1_complete_count > 0 or wave2_complete_count > 0:
        # Some sessions analyzed but not stopped - still processing
        processing_state = "running"

    return DemoStatusResponse(
        demo_token=demo_user["demo_token"],
        patient_id=patient_id,
        session_count=session_count,
        created_at=demo_user.get("created_at", ""),
        expires_at=demo_user["demo_expires_at"],
        is_expired=is_expired,
        analysis_status=analysis_status,
        wave1_complete=wave1_complete_count,
        wave2_complete=wave2_complete_count,
        sessions=session_statuses,
        roadmap_updated_at=roadmap_updated_at,
        processing_state=processing_state,
        stopped_at_session_id=stopped_at_session_id,
        can_resume=can_resume
    )


@router.get("/logs/{patient_id}")
async def get_pipeline_logs(
    patient_id: str,
    demo_user: dict = Depends(require_demo_auth)
):
    """
    Get pipeline logs for a patient

    Returns:
        JSON array of log events

    Note: Logs are ephemeral and reset on deployment
    """
    from pathlib import Path
    import json

    # Verify patient_id matches demo user
    if demo_user["id"] != patient_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these logs")

    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_file = log_dir / f"pipeline_{patient_id}.log"

    if not log_file.exists():
        return {"logs": [], "message": "No logs found for this patient"}

    # Read log file and parse JSON lines
    logs = []
    with open(log_file, "r") as f:
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue

    return {
        "patient_id": patient_id,
        "log_count": len(logs),
        "logs": logs
    }


@router.post("/stop")
async def stop_demo_processing(
    request: Request,
    demo_user: dict = Depends(require_demo_auth),
    db: Client = Depends(get_db)
):
    """
    Stop all running background processes for the current demo.
    Terminates transcript population, Wave 1, and Wave 2 analysis.

    Returns:
        Status of terminated processes
    """
    user_id = demo_user["id"]

    # Look up the patient record to get patient_id
    patient_response = db.table("patients").select("id").eq("user_id", user_id).single().execute()

    if not patient_response.data:
        raise HTTPException(
            status_code=404,
            detail="Patient record not found for demo user"
        )

    patient_id = patient_response.data["id"]

    print(f"🛑 Stop requested for patient {patient_id}", flush=True)
    logger.info(f"🛑 Stop requested for patient {patient_id}")

    # PR #3 Phase 4: Set stopped flags for resume detection
    if patient_id not in analysis_status:
        analysis_status[patient_id] = {}
    analysis_status[patient_id]["wave1_stopped"] = True
    analysis_status[patient_id]["wave2_stopped"] = True

    if patient_id not in running_processes:
        return {
            "message": "No running processes found for this demo",
            "patient_id": patient_id,
            "terminated": []
        }

    terminated = []
    processes = running_processes.get(patient_id, {})

    for process_name, process in processes.items():
        try:
            if process and process.returncode is None:  # Process is still running
                print(f"  🛑 Terminating {process_name} process...", flush=True)
                logger.info(f"Terminating {process_name} process for patient {patient_id}")

                process.terminate()  # Send SIGTERM
                try:
                    # Wait up to 5 seconds for graceful shutdown
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                    print(f"  ✓ {process_name} terminated gracefully", flush=True)
                except asyncio.TimeoutError:
                    # Force kill if not terminated
                    process.kill()
                    await process.wait()
                    print(f"  ✓ {process_name} force killed", flush=True)

                terminated.append(process_name)
        except Exception as e:
            logger.error(f"Error terminating {process_name}: {e}")
            print(f"  ✗ Error terminating {process_name}: {e}", flush=True)

    # Clear process references
    running_processes[patient_id] = {}

    print(f"✅ Stopped {len(terminated)} processes: {', '.join(terminated)}", flush=True)
    logger.info(f"Stopped {len(terminated)} processes for patient {patient_id}")

    return {
        "message": f"Successfully stopped {len(terminated)} running processes",
        "patient_id": patient_id,
        "terminated": terminated
    }


@router.post("/resume")
async def resume_demo_processing(
    request: Request,
    demo_user: dict = Depends(require_demo_auth),
    db: Client = Depends(get_db)
):
    """
    Resume processing from where it was stopped.

    Smart resume logic:
    1. Find incomplete sessions (Wave 1 complete but Wave 2 incomplete)
    2. Re-run Wave 2 for incomplete session
    3. Continue with remaining sessions (Wave 1 → Wave 2 → Roadmap)

    Returns immediately after scheduling background tasks.
    """
    user_id = demo_user["id"]

    # Look up the patient record to get patient_id
    patient_response = db.table("patients").select("id").eq("user_id", user_id).single().execute()

    if not patient_response.data:
        raise HTTPException(
            status_code=404,
            detail="Patient record not found for demo user"
        )

    patient_id = patient_response.data["id"]

    print(f"▶️ Resume requested for patient {patient_id}", flush=True)
    logger.info(f"▶️ Resume requested for patient {patient_id}")

    # Reset stopped flags
    if patient_id not in analysis_status:
        analysis_status[patient_id] = {}
    analysis_status[patient_id]["wave1_stopped"] = False
    analysis_status[patient_id]["wave2_stopped"] = False

    # Find incomplete sessions
    sessions_result = db.table("therapy_sessions") \
        .select("id, topics, prose_analysis") \
        .eq("patient_id", patient_id) \
        .order("session_date") \
        .execute()

    sessions = sessions_result.data
    incomplete_session = None
    next_sessions = []

    for session in sessions:
        if session.get("topics") and not session.get("prose_analysis"):
            # Wave 1 complete but Wave 2 incomplete - this is the stopped session
            if not incomplete_session:
                incomplete_session = session
        elif not session.get("topics"):
            # Wave 1 not started - these are next sessions
            next_sessions.append(session)

    # Schedule resume tasks
    if incomplete_session:
        # Re-run Wave 2 for incomplete session
        print(f"[RESUME] Re-running Wave 2 for Session {incomplete_session['id']}", flush=True)
        asyncio.create_task(run_wave2_analysis_background(patient_id))

    # Continue with remaining sessions (Wave 1 → Wave 2 → Roadmap)
    if next_sessions:
        print(f"[RESUME] Continuing with {len(next_sessions)} remaining sessions", flush=True)

        async def run_wave1_then_wave2_resume():
            """Run Wave 1, then start Wave 2 when Wave 1 completes"""
            await run_wave1_analysis_background(patient_id)
            # After Wave 1 completes, start Wave 2
            asyncio.create_task(run_wave2_analysis_background(patient_id))

        asyncio.create_task(run_wave1_then_wave2_resume())

    return {
        "message": "Processing resumed",
        "incomplete_session_id": incomplete_session["id"] if incomplete_session else None,
        "remaining_sessions": len(next_sessions)
    }
