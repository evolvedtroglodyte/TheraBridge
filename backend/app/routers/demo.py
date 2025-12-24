"""
Demo Mode API Router
Handles demo initialization, reset, and status
"""

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
import logging
import subprocess
import sys

from app.database import get_db, get_supabase_admin
from app.middleware.demo_auth import get_demo_user, require_demo_auth
from supabase import Client

router = APIRouter(prefix="/api/demo", tags=["demo"])
logger = logging.getLogger(__name__)


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


class DemoStatusResponse(BaseModel):
    """Response for demo status check"""
    demo_token: str
    patient_id: str
    session_count: int
    created_at: str
    expires_at: str
    is_expired: bool
    analysis_status: str  # "pending", "wave1_complete", "wave2_complete"
    wave1_complete: int  # Count of sessions with Wave 1 analysis
    wave2_complete: int  # Count of sessions with Wave 2 analysis


# ============================================================================
# Background Tasks
# ============================================================================

async def run_wave1_analysis_background(patient_id: str):
    """Background task to run Wave 1 analysis"""
    logger.info(f"🚀 Starting Wave 1 analysis for patient {patient_id}")

    try:
        # Get Python executable from current environment
        python_exe = sys.executable

        # Run Wave 1 script
        result = subprocess.run(
            [python_exe, "backend/scripts/seed_wave1_analysis.py", patient_id],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )

        if result.returncode == 0:
            logger.info(f"✅ Wave 1 analysis complete for patient {patient_id}")
        else:
            logger.error(f"❌ Wave 1 analysis failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error(f"❌ Wave 1 analysis timeout for patient {patient_id}")
    except Exception as e:
        logger.error(f"❌ Wave 1 analysis error: {e}")


async def run_wave2_analysis_background(patient_id: str):
    """Background task to run Wave 2 analysis (after Wave 1 completes)"""
    logger.info(f"🚀 Starting Wave 2 analysis for patient {patient_id}")

    try:
        # Get Python executable from current environment
        python_exe = sys.executable

        # Run Wave 2 script
        result = subprocess.run(
            [python_exe, "backend/scripts/seed_wave2_analysis.py", patient_id],
            capture_output=True,
            text=True,
            timeout=900  # 15 minute timeout
        )

        if result.returncode == 0:
            logger.info(f"✅ Wave 2 analysis complete for patient {patient_id}")
        else:
            logger.error(f"❌ Wave 2 analysis failed: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.error(f"❌ Wave 2 analysis timeout for patient {patient_id}")
    except Exception as e:
        logger.error(f"❌ Wave 2 analysis error: {e}")


async def run_full_analysis_pipeline(patient_id: str):
    """Run both Wave 1 and Wave 2 analysis sequentially"""
    logger.info(f"🧠 Starting full analysis pipeline for patient {patient_id}")

    # Run Wave 1 first
    await run_wave1_analysis_background(patient_id)

    # Then run Wave 2 (requires Wave 1 to be complete)
    await run_wave2_analysis_background(patient_id)

    logger.info(f"🎉 Full analysis pipeline complete for patient {patient_id}")


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

    logger.info(f"Initializing demo user with token: {demo_token}")

    try:
        # Call SQL function to seed demo data
        response = db.rpc("seed_demo_v2", {"p_demo_token": demo_token}).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(
                status_code=500,
                detail="Failed to create demo user and sessions"
            )

        result = response.data[0]
        patient_id = result["patient_id"]
        session_ids = result["session_ids"]

        # Fetch demo user to get expiry
        user_response = db.table("users").select("demo_expires_at").eq("id", patient_id).single().execute()
        expires_at = user_response.data["demo_expires_at"]

        logger.info(f"✓ Demo user created: {patient_id} with {len(session_ids)} sessions")

        # Trigger background analysis if enabled
        analysis_status = "pending"
        if run_analysis:
            background_tasks.add_task(run_full_analysis_pipeline, str(patient_id))
            analysis_status = "processing"
            logger.info(f"🧠 Queued Wave 1 + Wave 2 analysis for patient {patient_id}")

        return DemoInitResponse(
            demo_token=demo_token,
            patient_id=str(patient_id),
            session_ids=[str(sid) for sid in session_ids],
            expires_at=expires_at,
            analysis_status=analysis_status,
            message=f"Demo initialized with {len(session_ids)} sessions. AI analysis {'running in background' if run_analysis else 'skipped'}."
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
    Get current demo user status with analysis progress

    Returns:
        DemoStatusResponse with user info, session count, and analysis status
    """
    patient_id = demo_user["id"]

    # Count sessions
    session_response = db.table("therapy_sessions").select("id", count="exact").eq("patient_id", patient_id).execute()
    session_count = session_response.count or 0

    # Count sessions with Wave 1 analysis (have mood_score)
    wave1_response = db.table("therapy_sessions").select("id", count="exact").eq("patient_id", patient_id).not_.is_("mood_score", "null").execute()
    wave1_complete = wave1_response.count or 0

    # Count sessions with Wave 2 analysis (have deep_analysis)
    wave2_response = db.table("therapy_sessions").select("id", count="exact").eq("patient_id", patient_id).not_.is_("deep_analysis", "null").execute()
    wave2_complete = wave2_response.count or 0

    # Determine overall analysis status
    if wave2_complete == session_count:
        analysis_status = "wave2_complete"
    elif wave1_complete == session_count:
        analysis_status = "wave1_complete"
    elif wave1_complete > 0 or wave2_complete > 0:
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
        wave1_complete=wave1_complete,
        wave2_complete=wave2_complete
    )
