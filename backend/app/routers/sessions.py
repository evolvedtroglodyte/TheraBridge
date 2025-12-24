"""
Therapy Sessions API Router
Handles session management, transcript upload, and breakthrough detection
"""

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, BackgroundTasks, Request
from typing import List, Optional, Dict
from pydantic import BaseModel, field_validator
from datetime import datetime, timedelta
import json
import logging

from app.database import get_db, get_session_with_breakthrough, store_breakthrough_analysis
from app.services.breakthrough_detector import BreakthroughDetector
from app.services.mood_analyzer import MoodAnalyzer
from app.services.topic_extractor import TopicExtractor
from app.services.prose_generator import ProseGenerator
from app.services.analysis_orchestrator import AnalysisOrchestrator, analyze_session_full_pipeline
from app.services.technique_library import get_technique_library
from app.services.speaker_labeler import label_session_transcript, SpeakerLabelingResult
from app.services.progress_metrics_extractor import ProgressMetricsExtractor, ProgressMetricsResponse
from app.middleware.demo_auth import get_demo_user
from app.config import settings
from supabase import Client

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)


# ============================================================================
# Request/Response Models
# ============================================================================

class SessionCreate(BaseModel):
    """Request model for creating a new session"""
    patient_id: str
    therapist_id: str
    session_date: datetime
    duration_minutes: Optional[int] = None


class TranscriptUpload(BaseModel):
    """Request model for uploading a transcript"""
    transcript: List[dict]  # [{start, end, speaker, text}]
    audio_file_url: Optional[str] = None


class BreakthroughResponse(BaseModel):
    """Response model for breakthrough detection"""
    session_id: str
    has_breakthrough: bool
    primary_breakthrough: Optional[dict] = None
    breakthrough_count: int
    confidence_threshold: float
    analyzed_at: datetime


class MoodAnalysisResponse(BaseModel):
    """Response model for mood analysis"""
    session_id: str
    mood_score: float  # 0.0 to 10.0 (0.5 increments)
    confidence: float  # 0.0 to 1.0
    rationale: str
    key_indicators: List[str]
    emotional_tone: str
    analyzed_at: datetime


class TopicExtractionResponse(BaseModel):
    """Response model for topic extraction"""
    session_id: str
    topics: List[str]  # 1-2 main topics
    action_items: List[str]  # 2 action items
    technique: str  # Primary therapeutic technique
    summary: str  # Ultra-brief summary (max 150 characters)
    confidence: float  # 0.0 to 1.0
    extracted_at: datetime

    @field_validator('summary')
    @classmethod
    def validate_summary_length(cls, v: str) -> str:
        """Ensure summary is within 150-character limit"""
        if len(v) > 150:
            raise ValueError(f"Summary exceeds 150 characters: {len(v)} chars")
        return v


class DeepAnalysisResponse(BaseModel):
    """Response model for deep clinical analysis"""
    session_id: str
    analysis: dict  # Complete JSONB analysis structure
    confidence: float  # 0.0 to 1.0
    analyzed_at: datetime


class ProseAnalysisResponse(BaseModel):
    """Response model for prose analysis"""
    session_id: str
    prose_text: str
    word_count: int
    paragraph_count: int
    confidence: float
    generated_at: datetime


class PipelineStatusResponse(BaseModel):
    """Response model for analysis pipeline status"""
    session_id: str
    analysis_status: str
    mood_complete: bool
    topics_complete: bool
    breakthrough_complete: bool
    wave1_complete: bool
    deep_complete: bool
    wave1_completed_at: Optional[datetime] = None
    deep_analyzed_at: Optional[datetime] = None


class TechniqueDefinitionResponse(BaseModel):
    """Response model for technique definition lookup"""
    technique: str  # Formatted name: "MODALITY - TECHNIQUE"
    definition: str  # Clinical definition


class SpeakerLabelingResponse(BaseModel):
    """Response model for speaker labeling"""
    session_id: str
    labeled_transcript: List[Dict[str, str]]  # [{speaker, text, timestamp}]
    therapist_name: str
    confidence: float
    detected_roles: Dict[str, str]  # {therapist_speaker_id, patient_speaker_id}


# ============================================================================
# Session CRUD Endpoints
# ============================================================================

@router.get("/")
async def get_all_sessions(
    request: Request,
    demo_user: dict = Depends(get_demo_user),
    db: Client = Depends(get_db)
):
    """
    Get ALL sessions for the current demo patient

    This endpoint is designed for fully dynamic session loading in the frontend.
    It fetches all sessions for the authenticated demo user and returns them
    sorted by date (newest first).

    **Authentication:** Requires Demo-Token header

    **Returns:**
        List of sessions with all fields:
        - id, patient_id, therapist_id
        - session_date, duration_minutes, status
        - transcript (JSONB array of segments)
        - AI analysis fields (topics, action_items, technique, summary)
        - mood analysis fields (mood_score, mood_confidence, emotional_tone)
        - Wave 2 fields (deep_analysis, prose_analysis)

    **Example Response:**
    ```json
    [
      {
        "id": "uuid",
        "patient_id": "uuid",
        "session_date": "2025-01-10",
        "duration_minutes": 60,
        "status": "completed",
        "transcript": [{...}],
        "topics": ["Depression", "Family conflict"],
        "action_items": ["Practice mindfulness", "Talk to parents"],
        "technique": "CBT - Cognitive Restructuring",
        "summary": "Discussed coping strategies for family stress.",
        "mood_score": 6.5,
        "mood_confidence": 0.85,
        "emotional_tone": "hopeful"
      },
      ...
    ]
    ```

    **Use Case:**
        Frontend calls this endpoint on dashboard load to fetch all sessions
        dynamically instead of using hardcoded mock data.
    """
    if not demo_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing demo token. Initialize demo first."
        )

    user_id = demo_user["id"]

    # Get patient record for this user
    patient_response = (
        db.table("patients")
        .select("id")
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    if not patient_response.data:
        raise HTTPException(
            status_code=404,
            detail="Patient record not found for this user"
        )

    patient_id = patient_response.data["id"]

    # Fetch all sessions for this patient, ordered by date DESC (newest first)
    response = (
        db.table("therapy_sessions")
        .select("*")
        .eq("patient_id", patient_id)
        .order("session_date", desc=True)
        .execute()
    )

    if not response.data:
        return []

    sessions = response.data

    # Get technique library for definition lookups
    technique_lib = get_technique_library()

    # Enrich sessions with technique definitions
    for session in sessions:
        # Add technique definition if technique exists
        if session.get("technique"):
            try:
                technique_def = technique_lib.get_technique_definition(
                    session["technique"]
                )
                session["technique_definition"] = technique_def
            except Exception as e:
                logger.warning(
                    f"Could not find definition for technique '{session.get('technique')}': {e}"
                )
                session["technique_definition"] = None
        else:
            session["technique_definition"] = None

    return sessions


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    db: Client = Depends(get_db)
):
    """
    Get session by ID with breakthrough details

    Returns:
        Session object with breakthrough data and history
    """
    session = await get_session_with_breakthrough(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.get("/patient/{patient_id}")
async def get_patient_sessions(
    patient_id: str,
    limit: int = 50,
    include_breakthroughs: bool = True,
    db: Client = Depends(get_db)
):
    """
    Get all sessions for a patient

    Args:
        patient_id: Patient UUID
        limit: Maximum number of sessions to return
        include_breakthroughs: Include breakthrough details

    Returns:
        List of sessions
    """
    response = (
        db.table("therapy_sessions")
        .select("*")
        .eq("patient_id", patient_id)
        .order("session_date", desc=True)
        .limit(limit)
        .execute()
    )

    sessions = response.data

    # Get technique library for definition lookups
    technique_lib = get_technique_library()

    # NOTE: breakthrough_history table reference removed (production fix 2026-01-08)
    # Breakthrough detection results are stored in therapy_sessions.has_breakthrough
    # Historical tracking via separate table is not currently implemented
    # if include_breakthroughs:
    #     for session in sessions:
    #         if session.get("has_breakthrough"):
    #             bt_response = (
    #                 db.table("breakthrough_history")
    #                 .select("*")
    #                 .eq("session_id", session["id"])
    #                 .order("confidence_score", desc=True)
    #                 .execute()
    #             )
    #             session["all_breakthroughs"] = bt_response.data

    # Enrich sessions with technique definitions
    for session in sessions:
        # Add technique definition if technique exists
        if session.get("technique"):
            try:
                technique_def = technique_lib.get_technique_definition(
                    session["technique"]
                )
                session["technique_definition"] = technique_def
            except Exception as e:
                logger.warning(
                    f"Could not find definition for technique '{session.get('technique')}': {e}"
                )
                session["technique_definition"] = None
        else:
            session["technique_definition"] = None

    return sessions


@router.post("/")
async def create_session(
    session: SessionCreate,
    db: Client = Depends(get_db)
):
    """
    Create a new therapy session

    Returns:
        Created session object
    """
    session_data = {
        "patient_id": session.patient_id,
        "therapist_id": session.therapist_id,
        "session_date": session.session_date.isoformat(),
        "duration_minutes": session.duration_minutes,
        "processing_status": "pending",
    }

    response = db.table("therapy_sessions").insert(session_data).execute()

    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to create session")

    return response.data[0]


# ============================================================================
# Transcript Upload & Processing
# ============================================================================

@router.post("/{session_id}/upload-transcript")
async def upload_transcript(
    session_id: str,
    data: TranscriptUpload,
    background_tasks: BackgroundTasks,
    db: Client = Depends(get_db)
):
    """
    Upload transcript and trigger breakthrough detection

    This endpoint:
    1. Stores the transcript in the session
    2. Triggers breakthrough detection (async if enabled)
    3. Returns immediately with processing status

    Args:
        session_id: Session UUID
        data: Transcript data
        background_tasks: FastAPI background tasks

    Returns:
        Session with processing status
    """
    # Verify session exists
    session_response = (
        db.table("therapy_sessions")
        .select("id, patient_id")
        .eq("id", session_id)
        .single()
        .execute()
    )

    if not session_response.data:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update session with transcript
    update_data = {
        "transcript": data.transcript,
        "processing_status": "completed",
        "updated_at": "now()",
    }

    if data.audio_file_url:
        update_data["audio_file_url"] = data.audio_file_url

    db.table("therapy_sessions").update(update_data).eq("id", session_id).execute()

    # Trigger breakthrough detection
    if settings.breakthrough_auto_analyze:
        logger.info(f"🔍 Triggering breakthrough detection for session {session_id}")

        # Add to background tasks for async processing
        background_tasks.add_task(
            analyze_breakthrough_background,
            session_id,
            data.transcript
        )

        return {
            "session_id": session_id,
            "status": "processing",
            "message": "Transcript uploaded. Breakthrough detection in progress.",
        }
    else:
        return {
            "session_id": session_id,
            "status": "completed",
            "message": "Transcript uploaded successfully.",
        }


@router.post("/{session_id}/upload-audio")
async def upload_audio_file(
    session_id: str,
    audio_file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Client = Depends(get_db)
):
    """
    Upload audio file to Supabase Storage

    This endpoint:
    1. Uploads audio to Supabase storage bucket
    2. Updates session with audio URL
    3. Triggers audio transcription pipeline (if configured)

    Args:
        session_id: Session UUID
        audio_file: Audio file (mp3, wav, m4a)

    Returns:
        Session with audio URL
    """
    # Validate file type
    allowed_types = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/x-m4a"]
    if audio_file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_types)}"
        )

    # Generate unique filename
    file_extension = audio_file.filename.split(".")[-1]
    storage_path = f"{session_id}.{file_extension}"

    try:
        # Read file content
        file_content = await audio_file.read()

        # Upload to Supabase Storage
        storage_response = db.storage.from_("audio-sessions").upload(
            path=storage_path,
            file=file_content,
            file_options={"content-type": audio_file.content_type}
        )

        # Get public URL
        audio_url = db.storage.from_("audio-sessions").get_public_url(storage_path)

        # Update session
        db.table("therapy_sessions").update({
            "audio_file_url": audio_url,
            "processing_status": "processing",
            "updated_at": "now()",
        }).eq("id", session_id).execute()

        logger.info(f"✓ Audio uploaded for session {session_id}")

        return {
            "session_id": session_id,
            "audio_url": audio_url,
            "status": "processing",
            "message": "Audio uploaded. Transcription in progress.",
        }

    except Exception as e:
        logger.error(f"Audio upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Audio upload failed: {str(e)}")


# ============================================================================
# Breakthrough Detection Endpoints
# ============================================================================

@router.post("/{session_id}/analyze-breakthrough")
async def analyze_breakthrough(
    session_id: str,
    force: bool = False,
    db: Client = Depends(get_db)
):
    """
    Manually trigger breakthrough detection for a session

    Args:
        session_id: Session UUID
        force: Force re-analysis even if already analyzed

    Returns:
        Breakthrough analysis results
    """
    # Get session
    session_response = (
        db.table("therapy_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )

    if not session_response.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session = session_response.data

    # Check if already analyzed
    if session.get("breakthrough_analyzed_at") and not force:
        return {
            "session_id": session_id,
            "status": "already_analyzed",
            "has_breakthrough": session.get("has_breakthrough", False),
            "analyzed_at": session.get("breakthrough_analyzed_at"),
            "breakthrough_data": session.get("breakthrough_data"),
        }

    # Check transcript exists
    transcript = session.get("transcript")
    if not transcript:
        raise HTTPException(status_code=400, detail="Session has no transcript to analyze")

    # Run breakthrough detection
    try:
        logger.info(f"🔍 Analyzing breakthrough for session {session_id}")

        detector = BreakthroughDetector()
        analysis = detector.analyze_session(
            transcript=transcript,
            session_metadata={"session_id": session_id}
        )

        # Prepare breakthrough data
        primary_breakthrough = None
        all_breakthroughs = []

        if analysis.primary_breakthrough:
            bt = analysis.primary_breakthrough
            primary_breakthrough = {
                "type": bt.breakthrough_type,
                "description": bt.description,
                "evidence": bt.evidence,
                "confidence": float(bt.confidence_score),
                "timestamp_start": float(bt.timestamp_start),
                "timestamp_end": float(bt.timestamp_end),
                "dialogue_excerpt": bt.speaker_sequence,
            }

        for bt in analysis.breakthrough_candidates:
            all_breakthroughs.append({
                "type": bt.breakthrough_type,
                "description": bt.description,
                "evidence": bt.evidence,
                "confidence": float(bt.confidence_score),
                "timestamp_start": float(bt.timestamp_start),
                "timestamp_end": float(bt.timestamp_end),
                "dialogue_excerpt": bt.speaker_sequence,
            })

        # Store results
        await store_breakthrough_analysis(
            session_id=session_id,
            has_breakthrough=analysis.has_breakthrough,
            primary_breakthrough=primary_breakthrough,
            all_breakthroughs=all_breakthroughs
        )

        logger.info(f"✓ Breakthrough analysis complete for session {session_id}")

        return BreakthroughResponse(
            session_id=session_id,
            has_breakthrough=analysis.has_breakthrough,
            primary_breakthrough=primary_breakthrough,
            breakthrough_count=len(all_breakthroughs),
            confidence_threshold=settings.breakthrough_min_confidence,
            analyzed_at=datetime.now()
        )

    except Exception as e:
        logger.error(f"Breakthrough detection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Breakthrough detection failed: {str(e)}"
        )


# NOTE: Endpoint disabled - breakthrough_history table does not exist (production fix 2026-01-08)
# Breakthrough detection results are stored in therapy_sessions.has_breakthrough
# Historical tracking via separate table is not currently implemented
# @router.get("/patient/{patient_id}/breakthroughs")
# async def get_patient_breakthroughs(
#     patient_id: str,
#     min_confidence: Optional[float] = None,
#     breakthrough_type: Optional[str] = None,
#     db: Client = Depends(get_db)
# ):
#     """
#     Get all breakthroughs for a patient across all sessions
#
#     Args:
#         patient_id: Patient UUID
#         min_confidence: Minimum confidence score filter
#         breakthrough_type: Filter by type (cognitive_insight, etc.)
#
#     Returns:
#         List of breakthroughs with session context
#     """
#     # Build query
#     query = (
#         db.table("breakthrough_history")
#         .select("*, therapy_sessions(session_date, duration_minutes)")
#         .in_("session_id",
#             db.table("therapy_sessions")
#             .select("id")
#             .eq("patient_id", patient_id)
#         )
#     )
#
#     if min_confidence:
#         query = query.gte("confidence_score", min_confidence)
#
#     if breakthrough_type:
#         query = query.eq("breakthrough_type", breakthrough_type)
#
#     response = query.order("created_at", desc=True).execute()
#
#     return response.data


@router.get("/patient/{patient_id}/consistency")
async def get_patient_consistency(
    patient_id: str,
    days: int = 90,
    db: Client = Depends(get_db)
):
    """
    Calculate patient session consistency metrics

    Analyzes session attendance patterns to measure consistency.
    Assumes weekly sessions (every 7 days) as the "regular" pattern.

    Args:
        patient_id: Patient UUID
        days: Number of days to analyze (default: 90)

    Returns:
        {
            "consistency_score": 0-100 score,
            "attendance_rate": percentage of expected weekly sessions attended,
            "average_gap_days": average days between sessions,
            "longest_streak_weeks": consecutive weeks with sessions,
            "missed_weeks": number of weeks without sessions,
            "weekly_data": chart data for visualization,
            "total_sessions": count of sessions in period,
            "period_start": ISO date,
            "period_end": ISO date
        }
    """
    from datetime import datetime, timedelta

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # Fetch sessions in the period
    response = (
        db.table("therapy_sessions")
        .select("id, session_date")
        .eq("patient_id", patient_id)
        .gte("session_date", start_date.isoformat())
        .lte("session_date", end_date.isoformat())
        .order("session_date", desc=False)
        .execute()
    )

    sessions = response.data

    if not sessions:
        return {
            "consistency_score": 0,
            "attendance_rate": 0,
            "average_gap_days": 0,
            "longest_streak_weeks": 0,
            "missed_weeks": 0,
            "weekly_data": [],
            "total_sessions": 0,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
        }

    # Parse session dates
    session_dates = [datetime.fromisoformat(s["session_date"].replace("Z", "+00:00")) for s in sessions]

    # Calculate gaps between sessions
    gaps = []
    for i in range(1, len(session_dates)):
        gap_days = (session_dates[i] - session_dates[i-1]).days
        gaps.append(gap_days)

    average_gap = sum(gaps) / len(gaps) if gaps else 0

    # Calculate expected weekly sessions
    weeks_in_period = days / 7
    expected_sessions = int(weeks_in_period)
    actual_sessions = len(sessions)
    attendance_rate = min(100, (actual_sessions / expected_sessions * 100)) if expected_sessions > 0 else 0

    # Calculate weekly attendance for chart (group sessions by week)
    weekly_data = []
    current_week_start = start_date
    week_num = 1

    while current_week_start < end_date:
        week_end = current_week_start + timedelta(days=7)

        # Count sessions in this week
        sessions_in_week = sum(
            1 for date in session_dates
            if current_week_start <= date < week_end
        )

        weekly_data.append({
            "week": f"W{week_num}",
            "attended": 1 if sessions_in_week > 0 else 0,
            "session_count": sessions_in_week,
            "week_start": current_week_start.strftime("%Y-%m-%d"),
        })

        current_week_start = week_end
        week_num += 1

    # Calculate longest streak (consecutive weeks with sessions)
    current_streak = 0
    longest_streak = 0

    for week in weekly_data:
        if week["attended"] == 1:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0

    # Count missed weeks
    missed_weeks = sum(1 for week in weekly_data if week["attended"] == 0)

    # Calculate regularity score (how close gaps are to 7 days)
    # Tolerance: ±3 days from ideal 7-day interval
    regularity_scores = []
    for gap in gaps:
        deviation = abs(gap - 7)
        if deviation <= 3:
            regularity_scores.append(100)  # Perfect
        elif deviation <= 7:
            regularity_scores.append(70)   # Good
        elif deviation <= 14:
            regularity_scores.append(40)   # Fair
        else:
            regularity_scores.append(10)   # Poor

    regularity_score = sum(regularity_scores) / len(regularity_scores) if regularity_scores else 0

    # Calculate overall consistency score (weighted combination)
    # 40% attendance rate, 40% regularity, 20% streak bonus
    streak_bonus = min(20, (longest_streak / weeks_in_period) * 20) if weeks_in_period > 0 else 0
    consistency_score = (
        (attendance_rate * 0.4) +
        (regularity_score * 0.4) +
        streak_bonus
    )
    consistency_score = round(min(100, consistency_score), 1)

    return {
        "consistency_score": consistency_score,
        "attendance_rate": round(attendance_rate, 1),
        "average_gap_days": round(average_gap, 1),
        "longest_streak_weeks": longest_streak,
        "missed_weeks": missed_weeks,
        "weekly_data": weekly_data,
        "total_sessions": actual_sessions,
        "expected_sessions": expected_sessions,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
    }


# ============================================================================
# Mood Analysis Endpoints
# ============================================================================

@router.post("/{session_id}/analyze-mood")
async def analyze_mood(
    session_id: str,
    force: bool = False,
    patient_speaker_id: str = "SPEAKER_01",
    db: Client = Depends(get_db)
):
    """
    Analyze patient mood from session transcript using AI

    This endpoint:
    1. Extracts patient dialogue from transcript
    2. Uses GPT-4o-mini to analyze emotional state
    3. Returns mood score (0.0-10.0) with rationale and indicators
    4. Stores mood score in session record

    Args:
        session_id: Session UUID
        force: Force re-analysis even if already analyzed
        patient_speaker_id: Speaker ID for patient (default: SPEAKER_01)

    Returns:
        MoodAnalysisResponse with mood score and analysis details
    """
    # Get session
    session_response = (
        db.table("therapy_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )

    if not session_response.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session = session_response.data

    # Check if already analyzed
    if session.get("mood_analyzed_at") and not force:
        return {
            "session_id": session_id,
            "status": "already_analyzed",
            "mood_score": session.get("mood_score"),
            "analyzed_at": session.get("mood_analyzed_at"),
            "rationale": session.get("mood_rationale", "Previously analyzed"),
            "key_indicators": session.get("mood_indicators", []),
            "emotional_tone": session.get("emotional_tone", ""),
            "confidence": session.get("mood_confidence", 0.8),
        }

    # Check transcript exists
    transcript = session.get("transcript")
    if not transcript:
        raise HTTPException(status_code=400, detail="Session has no transcript to analyze")

    # Run mood analysis
    try:
        logger.info(f"🎭 Analyzing mood for session {session_id}")

        analyzer = MoodAnalyzer()
        analysis = analyzer.analyze_session_mood(
            session_id=session_id,
            segments=transcript,
            patient_speaker_id=patient_speaker_id
        )

        # Update session with mood data
        db.table("therapy_sessions").update({
            "mood_score": analysis.mood_score,
            "mood_confidence": analysis.confidence,
            "mood_rationale": analysis.rationale,
            "mood_indicators": analysis.key_indicators,
            "emotional_tone": analysis.emotional_tone,
            "mood_analyzed_at": datetime.now().isoformat(),
            "updated_at": "now()",
        }).eq("id", session_id).execute()

        logger.info(f"✓ Mood analysis complete for session {session_id}: {analysis.mood_score}/10.0")

        return MoodAnalysisResponse(
            session_id=session_id,
            mood_score=analysis.mood_score,
            confidence=analysis.confidence,
            rationale=analysis.rationale,
            key_indicators=analysis.key_indicators,
            emotional_tone=analysis.emotional_tone,
            analyzed_at=analysis.analyzed_at
        )

    except Exception as e:
        logger.error(f"Mood analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Mood analysis failed: {str(e)}"
        )


@router.get("/patient/{patient_id}/mood-history")
async def get_patient_mood_history(
    patient_id: str,
    limit: int = 50,
    db: Client = Depends(get_db)
):
    """
    Get mood history for a patient across all sessions

    Returns sessions with mood scores for visualization in ProgressPatternsCard

    Args:
        patient_id: Patient UUID
        limit: Maximum number of sessions to return

    Returns:
        List of sessions with mood data sorted by date
    """
    response = (
        db.table("therapy_sessions")
        .select("id, session_date, mood_score, mood_confidence, emotional_tone")
        .eq("patient_id", patient_id)
        .not_.is_("mood_score", "null")  # Only sessions with mood analysis
        .order("session_date", desc=False)  # Chronological order
        .limit(limit)
        .execute()
    )

    return response.data


# ============================================================================
# Speaker Labeling Endpoints
# ============================================================================

@router.post("/sessions/{session_id}/label-speakers", response_model=SpeakerLabelingResponse)
async def label_session_speakers(
    session_id: str,
    override_model: Optional[str] = None,
    db: Client = Depends(get_db)
) -> SpeakerLabelingResponse:
    """
    Label session transcript with speaker labels and format for patient-facing view.

    Returns:
    - Merged consecutive same-speaker segments
    - Therapist identified as "Therapist"
    - Patient identified as "You"
    - Timestamps in MM:SS format

    Example response:
    {
      "session_id": "uuid",
      "labeled_transcript": [
        {"speaker": "Therapist", "text": "...", "timestamp": "00:00"},
        {"speaker": "You", "text": "...", "timestamp": "00:28"}
      ],
      "therapist_name": "Therapist",
      "confidence": 0.92,
      "detected_roles": {
        "therapist_speaker_id": "SPEAKER_00",
        "patient_speaker_id": "SPEAKER_01"
      }
    }
    """
    try:
        # Step 1: Get session from database
        session_response = (
            db.table("therapy_sessions")
            .select("id, transcript")
            .eq("id", session_id)
            .single()
            .execute()
        )

        if not session_response.data:
            raise HTTPException(status_code=404, detail="Session not found")

        session = session_response.data

        # Validate transcript exists
        if not session.get("transcript"):
            raise HTTPException(
                status_code=400,
                detail="Session has no transcript to label"
            )

        # Step 2: Call speaker labeling service
        result: SpeakerLabelingResult = label_session_transcript(
            session_id=session_id,
            raw_segments=session["transcript"],
            openai_api_key=settings.OPENAI_API_KEY,
            override_model=override_model
        )

        # Step 3: Format response
        return SpeakerLabelingResponse(
            session_id=session_id,
            labeled_transcript=[seg.model_dump() for seg in result.labeled_transcript],
            therapist_name=result.therapist_name,
            confidence=result.detection.confidence,
            detected_roles={
                "therapist_speaker_id": result.detection.therapist_speaker_id,
                "patient_speaker_id": result.detection.patient_speaker_id
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Speaker labeling failed for session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Speaker labeling failed: {str(e)}"
        )


# ============================================================================
# Background Task Functions
# ============================================================================

async def analyze_breakthrough_background(session_id: str, transcript: list):
    """
    Background task for breakthrough detection
    Runs asynchronously without blocking the API response
    """
    try:
        logger.info(f"📊 Background: Starting breakthrough detection for {session_id}")

        detector = BreakthroughDetector()
        analysis = detector.analyze_session(
            transcript=transcript,
            session_metadata={"session_id": session_id}
        )

        # Prepare data
        primary_breakthrough = None
        all_breakthroughs = []

        if analysis.primary_breakthrough:
            bt = analysis.primary_breakthrough
            primary_breakthrough = {
                "type": bt.breakthrough_type,
                "description": bt.description,
                "evidence": bt.evidence,
                "confidence": float(bt.confidence_score),
                "timestamp_start": float(bt.timestamp_start),
                "timestamp_end": float(bt.timestamp_end),
            }

        for bt in analysis.breakthrough_candidates:
            all_breakthroughs.append({
                "type": bt.breakthrough_type,
                "description": bt.description,
                "evidence": bt.evidence,
                "confidence": float(bt.confidence_score),
                "timestamp_start": float(bt.timestamp_start),
                "timestamp_end": float(bt.timestamp_end),
                "dialogue_excerpt": bt.speaker_sequence,
            })

        # Store results
        await store_breakthrough_analysis(
            session_id=session_id,
            has_breakthrough=analysis.has_breakthrough,
            primary_breakthrough=primary_breakthrough,
            all_breakthroughs=all_breakthroughs
        )

        logger.info(f"✓ Background: Breakthrough detection complete for {session_id}")

    except Exception as e:
        logger.error(f"Background breakthrough detection failed: {e}")
        # Don't raise - just log the error


# ============================================================================
# Topic Extraction Endpoints
# ============================================================================

@router.post("/{session_id}/extract-topics")
async def extract_topics(
    session_id: str,
    force: bool = False,
    db: Client = Depends(get_db)
):
    """
    Extract topics, action items, technique, and summary from session transcript using AI

    This endpoint:
    1. Analyzes full conversation (both therapist and client)
    2. Uses GPT-4o-mini to extract structured metadata
    3. Returns 1-2 topics, 2 action items, primary technique, and 2-sentence summary
    4. Stores extracted metadata in session record

    Args:
        session_id: Session UUID
        force: Force re-extraction even if already extracted

    Returns:
        TopicExtractionResponse with topics, action items, technique, and summary
    """
    # Get session
    session_response = (
        db.table("therapy_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )

    if not session_response.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session = session_response.data

    # Check if already extracted
    if session.get("topics_extracted_at") and not force:
        return {
            "session_id": session_id,
            "status": "already_extracted",
            "topics": session.get("topics", []),
            "action_items": session.get("action_items", []),
            "technique": session.get("technique", ""),
            "summary": session.get("summary", ""),
            "confidence": session.get("extraction_confidence", 0.8),
            "extracted_at": session.get("topics_extracted_at"),
        }

    # Check transcript exists
    transcript = session.get("transcript")
    if not transcript:
        raise HTTPException(status_code=400, detail="Session has no transcript to analyze")

    # Run topic extraction
    try:
        logger.info(f"📝 Extracting topics for session {session_id}")

        extractor = TopicExtractor()
        metadata = extractor.extract_metadata(
            session_id=session_id,
            segments=transcript
        )

        # Update session with extracted metadata
        db.table("therapy_sessions").update({
            "topics": metadata.topics,
            "action_items": metadata.action_items,
            "technique": metadata.technique,
            "summary": metadata.summary,
            "extraction_confidence": metadata.confidence,
            "raw_meta_summary": metadata.raw_meta_summary,
            "topics_extracted_at": datetime.now().isoformat(),
            "updated_at": "now()",
        }).eq("id", session_id).execute()

        logger.info(f"✓ Topic extraction complete for session {session_id}: {len(metadata.topics)} topics")

        return TopicExtractionResponse(
            session_id=session_id,
            topics=metadata.topics,
            action_items=metadata.action_items,
            technique=metadata.technique,
            summary=metadata.summary,
            confidence=metadata.confidence,
            extracted_at=metadata.extracted_at
        )

    except Exception as e:
        logger.error(f"Topic extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Topic extraction failed: {str(e)}"
        )


# ============================================================================
# Deep Analysis & Pipeline Orchestration Endpoints
# ============================================================================

@router.post("/{session_id}/analyze-full-pipeline")
async def analyze_full_pipeline(
    session_id: str,
    force: bool = False,
    background_tasks: BackgroundTasks = None,
    db: Client = Depends(get_db)
):
    """
    Run complete analysis pipeline: Wave 1 (mood, topics, breakthrough) → Wave 2 (deep analysis)

    This endpoint orchestrates the entire analysis process with proper dependency management.

    Args:
        session_id: Session UUID
        force: Force re-analysis even if already completed
        background_tasks: FastAPI background tasks for async processing

    Returns:
        PipelineStatusResponse with current status
    """
    # Verify session exists
    session_response = (
        db.table("therapy_sessions")
        .select("id, transcript")
        .eq("id", session_id)
        .single()
        .execute()
    )

    if not session_response.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session = session_response.data

    # Check if transcript exists
    if not session.get("transcript"):
        raise HTTPException(status_code=400, detail="Session has no transcript to analyze")

    # Add to background tasks for async processing
    if background_tasks:
        background_tasks.add_task(
            run_full_pipeline_background,
            session_id,
            force
        )

        return {
            "session_id": session_id,
            "status": "processing",
            "message": "Full analysis pipeline started. Check status with GET /api/sessions/{id}/analysis-status",
        }
    else:
        # Run synchronously (blocking)
        try:
            orchestrator = AnalysisOrchestrator(db=db)
            status = await orchestrator.process_session_full_pipeline(session_id, force)

            return PipelineStatusResponse(
                session_id=status.session_id,
                analysis_status=status.analysis_status,
                mood_complete=status.mood_complete,
                topics_complete=status.topics_complete,
                breakthrough_complete=status.breakthrough_complete,
                wave1_complete=status.wave1_complete,
                deep_complete=status.deep_complete,
                wave1_completed_at=status.wave1_completed_at,
                deep_analyzed_at=status.deep_analyzed_at
            )

        except Exception as e:
            logger.error(f"Full pipeline failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Analysis pipeline failed: {str(e)}"
            )


@router.get("/{session_id}/analysis-status")
async def get_analysis_status(
    session_id: str,
    db: Client = Depends(get_db)
):
    """
    Get current status of analysis pipeline for a session

    Returns detailed status including which analyses have completed and any errors.

    Args:
        session_id: Session UUID

    Returns:
        Detailed pipeline status with recent logs
    """
    try:
        response = db.rpc("get_analysis_pipeline_status", {"p_session_id": session_id}).execute()

        if not response.data or len(response.data) == 0:
            raise HTTPException(status_code=404, detail="Session not found")

        return response.data[0]

    except Exception as e:
        logger.error(f"Failed to get analysis status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analysis status: {str(e)}"
        )


@router.post("/{session_id}/analyze-deep")
async def analyze_deep(
    session_id: str,
    force: bool = False,
    db: Client = Depends(get_db)
):
    """
    Run deep clinical analysis for a session (Wave 2 only)

    **Prerequisites:** All Wave 1 analyses must be complete (mood, topics, breakthrough)

    This endpoint:
    1. Verifies Wave 1 is complete
    2. Gathers patient history and context
    3. Uses GPT-4o to synthesize comprehensive insights
    4. Returns patient-facing analysis with progress, insights, skills, and recommendations

    Args:
        session_id: Session UUID
        force: Force re-analysis even if already analyzed

    Returns:
        DeepAnalysisResponse with comprehensive clinical insights
    """
    # Get session
    session_response = (
        db.table("therapy_sessions")
        .select("*")
        .eq("id", session_id)
        .single()
        .execute()
    )

    if not session_response.data:
        raise HTTPException(status_code=404, detail="Session not found")

    session = session_response.data

    # Check if already analyzed
    if session.get("deep_analyzed_at") and not force:
        return {
            "session_id": session_id,
            "status": "already_analyzed",
            "analysis": session.get("deep_analysis"),
            "confidence": session.get("analysis_confidence"),
            "analyzed_at": session.get("deep_analyzed_at"),
        }

    # Verify Wave 1 is complete
    orchestrator = AnalysisOrchestrator(db=db)
    wave1_complete = await orchestrator._is_wave1_complete(session_id)

    if not wave1_complete:
        raise HTTPException(
            status_code=400,
            detail="Cannot run deep analysis: Wave 1 not complete. Run /analyze-full-pipeline first."
        )

    # Run deep analysis
    try:
        logger.info(f"🧠 Running deep analysis for session {session_id}")

        await orchestrator._analyze_deep(session_id, force)

        # Get updated session
        updated_session = (
            db.table("therapy_sessions")
            .select("deep_analysis, analysis_confidence, deep_analyzed_at")
            .eq("id", session_id)
            .single()
            .execute()
        ).data

        logger.info(f"✓ Deep analysis complete for session {session_id}")

        return DeepAnalysisResponse(
            session_id=session_id,
            analysis=updated_session["deep_analysis"],
            confidence=updated_session["analysis_confidence"],
            analyzed_at=datetime.fromisoformat(updated_session["deep_analyzed_at"].replace("Z", "+00:00"))
        )

    except Exception as e:
        logger.error(f"Deep analysis failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Deep analysis failed: {str(e)}"
        )


@router.post("/{session_id}/generate-prose-analysis", response_model=ProseAnalysisResponse)
async def generate_prose_analysis(
    session_id: str,
    db: Client = Depends(get_db)
):
    """
    Generate patient-facing prose narrative from existing deep analysis.

    Requires:
    - Session must have completed deep_analysis

    Returns:
    - 500-750 word prose narrative
    - Word/paragraph counts
    - Generation timestamp
    """
    try:
        # Fetch session
        session_response = db.table("therapy_sessions").select("*").eq("id", session_id).single().execute()
        session = session_response.data

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Check if deep_analysis exists
        if not session.get("deep_analysis"):
            raise HTTPException(
                status_code=400,
                detail="Deep analysis must be completed before generating prose"
            )

        # Check if prose already exists (optional caching)
        if session.get("prose_analysis"):
            logger.info(f"Prose already exists for session {session_id}, regenerating...")

        # Generate prose
        generator = ProseGenerator()
        prose = await generator.generate_prose(
            session_id=session_id,
            deep_analysis=session["deep_analysis"],
            confidence_score=session.get("analysis_confidence", 0.8)
        )

        # Update database
        db.table("therapy_sessions").update({
            "prose_analysis": prose.prose_text,
            "prose_generated_at": prose.generated_at.isoformat()
        }).eq("id", session_id).execute()

        logger.info(f"✓ Prose analysis saved for session {session_id}")

        return ProseAnalysisResponse(
            session_id=session_id,
            prose_text=prose.prose_text,
            word_count=prose.word_count,
            paragraph_count=prose.paragraph_count,
            confidence=prose.confidence_score,
            generated_at=prose.generated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prose generation failed for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Prose generation failed: {str(e)}")


# ============================================================================
# Background Task Functions
# ============================================================================

async def run_full_pipeline_background(session_id: str, force: bool = False):
    """
    Background task for full analysis pipeline
    Runs asynchronously without blocking the API response
    """
    try:
        logger.info(f"📊 Background: Starting full analysis pipeline for {session_id}")

        await analyze_session_full_pipeline(session_id, force)

        logger.info(f"✓ Background: Full pipeline complete for {session_id}")

    except Exception as e:
        logger.error(f"Background pipeline failed for {session_id}: {e}")
        # Don't raise - just log the error


# ============================================================================
# Technique Library Endpoints
# ============================================================================

@router.get("/techniques/{technique_name}/definition", response_model=TechniqueDefinitionResponse)
async def get_technique_definition(technique_name: str):
    """
    Get definition for a clinical technique.

    **Args:**
    - technique_name: Formatted technique name (e.g., "CBT - Cognitive Restructuring")
      URL encoding required for special characters (e.g., "CBT%20-%20Cognitive%20Restructuring")

    **Returns:**
    - JSON with technique name and definition

    **Example:**
    ```
    GET /api/sessions/techniques/CBT%20-%20Cognitive%20Restructuring/definition
    {
      "technique": "CBT - Cognitive Restructuring",
      "definition": "The therapeutic process of identifying and challenging..."
    }
    ```

    **Errors:**
    - 404: Technique not found in library
    """
    library = get_technique_library()
    definition = library.get_technique_definition(technique_name)

    if not definition:
        raise HTTPException(
            status_code=404,
            detail=f"Technique '{technique_name}' not found in library"
        )

    return TechniqueDefinitionResponse(
        technique=technique_name,
        definition=definition
    )


# ============================================================================
# Progress Metrics Endpoints
# ============================================================================

@router.get("/patient/{patient_id}/progress-metrics", response_model=ProgressMetricsResponse)
async def get_patient_progress_metrics(
    patient_id: str,
    limit: int = 50,
    db: Client = Depends(get_db)
):
    """
    Get progress metrics for visualization in ProgressPatternsCard.

    Extracts metrics from completed Wave 1 + Wave 2 analyses:
    - **Mood Trends:** AI-analyzed mood scores over time
    - **Session Consistency:** Attendance patterns and streaks

    **Args:**
    - patient_id: Patient UUID
    - limit: Maximum number of sessions to include (default: 50)

    **Returns:**
    - ProgressMetricsResponse with chart data ready for Recharts

    **Example Response:**
    ```json
    {
      "metrics": [
        {
          "title": "Mood Trends",
          "description": "AI-analyzed emotional state over time",
          "emoji": "📈",
          "insight": "📈 IMPROVING: +36% overall (Recent avg: 6.5/10, Historical: 5.5/10)",
          "chartData": [
            {"session": "S10", "mood": 5.5, "date": "Dec 23", "confidence": 0.85},
            {"session": "S11", "mood": 6.5, "date": "Dec 24", "confidence": 0.85}
          ]
        },
        {
          "title": "Session Consistency",
          "description": "Attendance patterns and engagement",
          "emoji": "📅",
          "insight": "100% attendance rate - Excellent (Score: 100/100). 10 week streak.",
          "chartData": [
            {"week": "Week 1", "attended": 1},
            {"week": "Week 2", "attended": 1}
          ]
        }
      ],
      "extracted_at": "2025-12-24T00:40:00Z",
      "session_count": 10,
      "date_range": "Nov 15 - Dec 24, 2025"
    }
    ```

    **Notes:**
    - Only sessions with completed Wave 1 (mood_score present) are included
    - Chart data is formatted for direct use with Recharts components
    - Insights are AI-generated based on trend analysis
    """
    # Get sessions with Wave 1 mood analysis complete
    sessions_response = (
        db.table("therapy_sessions")
        .select("*")
        .eq("patient_id", patient_id)
        .not_.is_("mood_score", "null")  # Only sessions with mood analysis
        .order("session_date", desc=False)  # Chronological order
        .limit(limit)
        .execute()
    )

    if not sessions_response.data:
        # Return empty metrics if no sessions found
        return ProgressMetricsResponse(
            metrics=[],
            extracted_at=datetime.now().isoformat() + "Z",
            session_count=0,
            date_range="No sessions"
        )

    # Transform database sessions to pipeline-like structure
    pipeline_data = {
        "sessions": []
    }

    for idx, session in enumerate(sessions_response.data, start=1):
        pipeline_data["sessions"].append({
            "session_num": idx,
            "session_id": session["id"],
            "wave1": {
                "session_num": idx,
                "mood_score": session.get("mood_score"),
                "mood_confidence": session.get("mood_confidence", 0.8),
                "analyzed_at": session.get("mood_analyzed_at") or session.get("created_at"),
            },
            "wave2": {
                "deep_analysis": session.get("deep_analysis"),
                "analyzed_at": session.get("deep_analyzed_at"),
            } if session.get("deep_analysis") else None,
        })

    # Extract metrics using the service
    try:
        metrics = ProgressMetricsExtractor.extract_from_pipeline_json(pipeline_data)
        logger.info(f"✓ Extracted {len(metrics.metrics)} progress metrics for patient {patient_id}")
        return metrics

    except Exception as e:
        logger.error(f"Progress metrics extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract progress metrics: {str(e)}"
        )


# ============================================================================
# Demo Mode - Transcript Upload
# ============================================================================

@router.get("/../patients/{patient_id}/roadmap")
async def get_patient_roadmap(
    patient_id: str,
    db: Client = Depends(get_db)
):
    """
    Get patient's latest roadmap data (PR #3: Your Journey Dynamic Roadmap)

    Full path: /api/patients/{patient_id}/roadmap
    (Using ../ to escape /api/sessions prefix)

    Fetches the current roadmap from patient_roadmap table.
    Returns 404 if no roadmap exists yet (0 sessions analyzed).

    Args:
        patient_id: Patient UUID

    Returns:
        {
            "roadmap": RoadmapData,
            "metadata": RoadmapMetadata
        }
    """
    try:
        # Query patient_roadmap table
        result = db.table("patient_roadmap") \
            .select("roadmap_data, metadata") \
            .eq("patient_id", patient_id) \
            .execute()

        if not result.data or len(result.data) == 0:
            # No roadmap yet (0 sessions analyzed)
            raise HTTPException(
                status_code=404,
                detail="No roadmap found for this patient. Sessions need to be analyzed first."
            )

        roadmap_record = result.data[0]

        return {
            "roadmap": roadmap_record["roadmap_data"],
            "metadata": roadmap_record["metadata"]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch roadmap for patient {patient_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch roadmap: {str(e)}"
        )


@router.post("/upload-demo-transcript")
async def upload_demo_transcript(
    request: Request,
    session_file: str,  # e.g., "session_12_thriving.json"
    background_tasks: BackgroundTasks,
    db: Client = Depends(get_db)
):
    """
    Upload a pre-selected demo transcript from mock-therapy-data/

    This endpoint:
    1. Validates demo token from headers
    2. Loads JSON transcript from mock-therapy-data/sessions/{session_file}
    3. Creates new session with transcript
    4. Triggers full AI analysis pipeline (mood, topics, breakthrough, deep)
    5. Returns session ID for status tracking

    Args:
        session_file: Filename from mock-therapy-data/sessions/ (e.g., "session_12_thriving.json")

    Returns:
        Session ID and processing status
    """
    # Get demo user from token
    demo_user = await get_demo_user(request)
    if not demo_user:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing demo token. Initialize demo first."
        )

    patient_id = demo_user["id"]

    # Load transcript JSON
    from pathlib import Path

    mock_data_dir = Path(__file__).parent.parent.parent.parent / "mock-therapy-data" / "sessions"
    transcript_path = mock_data_dir / session_file

    if not transcript_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Demo transcript not found: {session_file}"
        )

    try:
        with open(transcript_path, "r") as f:
            transcript_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load transcript {session_file}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load demo transcript: {str(e)}"
        )

    # Extract transcript segments
    segments = transcript_data.get("segments", [])
    if not segments:
        raise HTTPException(
            status_code=400,
            detail="Demo transcript has no segments"
        )

    # Get therapist ID (find demo therapist with same demo_token)
    therapist_response = db.table("users").select("id").eq("demo_token", demo_user["demo_token"]).eq("role", "therapist").single().execute()
    therapist_id = therapist_response.data["id"]

    # Calculate session date (after last existing session)
    last_session_response = db.table("therapy_sessions").select("session_date").eq("patient_id", patient_id).order("session_date", desc=True).limit(1).execute()

    if last_session_response.data:
        last_date = datetime.fromisoformat(last_session_response.data[0]["session_date"].replace("Z", "+00:00"))
        new_session_date = last_date + timedelta(days=7)  # 1 week later
    else:
        new_session_date = datetime.now()

    session_data = {
        "patient_id": patient_id,
        "therapist_id": therapist_id,
        "session_date": new_session_date.isoformat(),
        "duration_minutes": transcript_data.get("metadata", {}).get("duration", 3600) // 60,
        "processing_status": "wave1_in_progress",
        "analysis_status": "wave1_in_progress",
        "transcript": segments,
    }

    session_response = db.table("therapy_sessions").insert(session_data).execute()

    if not session_response.data:
        raise HTTPException(status_code=500, detail="Failed to create session")

    session = session_response.data[0]
    session_id = session["id"]

    # Trigger full AI analysis in background
    background_tasks.add_task(analyze_session_full_pipeline, session_id)

    logger.info(f"✓ Demo transcript uploaded: {session_file} → Session {session_id}")

    return {
        "session_id": session_id,
        "status": "processing",
        "message": f"Demo session created from {session_file}. AI analysis in progress.",
        "transcript_segments": len(segments)
    }
