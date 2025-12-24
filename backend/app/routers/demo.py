"""
Demo Mode API Router
Handles demo initialization, reset, and status
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from pathlib import Path
import logging
import subprocess
import sys
import os

from app.database import get_db, get_supabase_admin
from app.middleware.demo_auth import get_demo_user, require_demo_auth
from supabase import Client

router = APIRouter(prefix="/api/demo", tags=["demo"])
logger = logging.getLogger(__name__)

# In-memory tracking of analysis completion (keyed by patient_id)
analysis_status = {}


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
    """Individual session completion status"""
    session_id: str
    session_date: str
    has_transcript: bool
    wave1_complete: bool
    wave2_complete: bool


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

        # Run transcript population script with environment variables
        result = subprocess.run(
            [python_exe, str(script_path), patient_id],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            env=os.environ.copy()  # Pass all environment variables
        )

        if result.returncode == 0:
            print(f"✅ Step 1/3 Complete: Session transcripts populated", flush=True)
            logger.info(f"✅ Session transcripts populated for patient {patient_id}")
            logger.info(result.stdout)
            # Show script output in Railway logs
            if result.stdout:
                print(f"[Transcript Script Output]:\n{result.stdout}", flush=True)
        else:
            print(f"❌ Step 1/3 Failed: {result.stderr}", flush=True)
            logger.error(f"❌ Transcript population failed: {result.stderr}")
            # Show error details in Railway logs
            if result.stderr:
                print(f"[Transcript Script Error]:\n{result.stderr}", flush=True)

    except subprocess.TimeoutExpired:
        logger.error(f"❌ Transcript population timeout for patient {patient_id}")
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

        # Run Wave 1 script with STREAMING output (not buffered)
        process = subprocess.Popen(
            [python_exe, str(script_path), patient_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,
            bufsize=1,  # Line buffered
            env=os.environ.copy()  # Pass all environment variables
        )

        # Stream output line by line in real-time
        for line in process.stdout:
            print(f"[Wave1] {line.rstrip()}", flush=True)
            logger.info(f"[Wave1] {line.rstrip()}")

        # Wait for process to complete
        returncode = process.wait(timeout=600)  # 10 minute timeout

        if returncode == 0:
            print(f"✅ Step 2/3 Complete: Wave 1 analysis complete", flush=True)
            logger.info(f"✅ Wave 1 analysis complete for patient {patient_id}")
            # Mark Wave 1 as complete
            if patient_id not in analysis_status:
                analysis_status[patient_id] = {}
            analysis_status[patient_id]["wave1_complete"] = True
            analysis_status[patient_id]["wave1_completed_at"] = datetime.now().isoformat()
        else:
            print(f"❌ Step 2/3 Failed with return code {returncode}", flush=True)
            logger.error(f"❌ Wave 1 analysis failed with return code {returncode}")

    except subprocess.TimeoutExpired:
        print(f"❌ Wave 1 analysis TIMEOUT (10 minutes exceeded)", flush=True)
        logger.error(f"❌ Wave 1 analysis timeout for patient {patient_id}")
        if 'process' in locals():
            process.kill()
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

        # Run Wave 2 script with STREAMING output (not buffered)
        process = subprocess.Popen(
            [python_exe, str(script_path), patient_id],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,
            bufsize=1,  # Line buffered
            env=os.environ.copy()  # Pass all environment variables
        )

        # Stream output line by line in real-time
        for line in process.stdout:
            print(f"[Wave2] {line.rstrip()}", flush=True)
            logger.info(f"[Wave2] {line.rstrip()}")

        # Wait for process to complete
        returncode = process.wait(timeout=900)  # 15 minute timeout

        if returncode == 0:
            print(f"✅ Step 3/3 Complete: Wave 2 analysis complete", flush=True)
            logger.info(f"✅ Wave 2 analysis complete for patient {patient_id}")
            # Mark Wave 2 as complete
            if patient_id not in analysis_status:
                analysis_status[patient_id] = {}
            analysis_status[patient_id]["wave2_complete"] = True
            analysis_status[patient_id]["wave2_completed_at"] = datetime.now().isoformat()
        else:
            print(f"❌ Step 3/3 Failed with return code {returncode}", flush=True)
            logger.error(f"❌ Wave 2 analysis failed with return code {returncode}")

    except subprocess.TimeoutExpired:
        print(f"❌ Wave 2 analysis TIMEOUT (15 minutes exceeded)", flush=True)
        logger.error(f"❌ Wave 2 analysis timeout for patient {patient_id}")
        if 'process' in locals():
            process.kill()
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
    background_tasks: BackgroundTasks,
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
            # Queue ALL initialization steps (transcripts + Wave 1 + Wave 2) in background
            # This ensures the endpoint returns immediately and can handle concurrent requests
            background_tasks.add_task(run_full_initialization_pipeline, str(patient_id))
            analysis_status = "processing"
            logger.info(f"🎬 Queued full initialization pipeline (transcripts + Wave 1 + Wave 2) for patient {patient_id}")

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
    2. Deletes all existing sessions for demo user
    3. Calls seed function to recreate 10 sessions
    4. Extends expiry by 24 hours

    Returns:
        DemoResetResponse with new session IDs
    """
    demo_token = demo_user["demo_token"]
    patient_id = demo_user["id"]

    logger.info(f"Resetting demo for user: {patient_id}")

    try:
        # Delete existing sessions
        db.table("therapy_sessions").delete().eq("patient_id", patient_id).execute()

        # Re-seed sessions using SQL function
        response = db.rpc("seed_demo_user_sessions", {"p_demo_token": demo_token}).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to reset demo sessions"
            )

        result = response.data[0]
        session_ids = result["session_ids"]

        logger.info(f"✓ Demo reset complete: {len(session_ids)} sessions recreated")

        return DemoResetResponse(
            patient_id=patient_id,
            session_ids=[str(sid) for sid in session_ids],
            message=f"Demo reset with {len(session_ids)} fresh sessions"
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

    # Fetch all sessions with analysis data
    sessions_response = db.table("therapy_sessions").select(
        "id, session_date, transcript, topics, mood_score, prose_analysis"
    ).eq("patient_id", patient_id).order("session_date").execute()

    sessions = sessions_response.data or []
    session_count = len(sessions)

    # Build per-session status
    session_statuses = []
    wave1_complete_count = 0
    wave2_complete_count = 0

    for session in sessions:
        has_transcript = bool(session.get("transcript"))
        wave1_complete = (session.get("topics") is not None or
                         session.get("mood_score") is not None)
        wave2_complete = session.get("prose_analysis") is not None

        if wave1_complete:
            wave1_complete_count += 1
        if wave2_complete:
            wave2_complete_count += 1

        session_statuses.append(SessionStatus(
            session_id=session["id"],
            session_date=session["session_date"],
            has_transcript=has_transcript,
            wave1_complete=wave1_complete,
            wave2_complete=wave2_complete
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
        sessions=session_statuses
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
