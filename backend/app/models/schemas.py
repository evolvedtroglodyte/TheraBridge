"""
Pydantic schemas for API requests/responses and AI extraction
"""
from datetime import datetime
from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID


# ============================================================================
# Enums
# ============================================================================

class UserRole(str, Enum):
    therapist = "therapist"
    patient = "patient"
    admin = "admin"


class SessionStatus(str, Enum):
    pending = "pending"
    uploading = "uploading"
    transcribing = "transcribing"
    transcribed = "transcribed"
    extracting_notes = "extracting_notes"
    processed = "processed"
    failed = "failed"


class MoodLevel(str, Enum):
    very_low = "very_low"
    low = "low"
    neutral = "neutral"
    positive = "positive"
    very_positive = "very_positive"


class StrategyStatus(str, Enum):
    introduced = "introduced"  # First time mentioned
    practiced = "practiced"    # Actively used in session
    assigned = "assigned"      # Given as homework
    reviewed = "reviewed"      # Discussed effectiveness


class ActionItemStatus(str, Enum):
    assigned = "assigned"
    in_progress = "in_progress"
    completed = "completed"
    abandoned = "abandoned"


# ============================================================================
# AI Extraction Schemas
# ============================================================================

class Strategy(BaseModel):
    """A coping strategy or therapeutic technique"""
    name: str = Field(..., description="Name of strategy (e.g., 'Box breathing')")
    category: str = Field(..., description="Category (e.g., 'Breathing technique')")
    status: StrategyStatus
    context: str = Field(..., description="Brief description of how it came up")


class Trigger(BaseModel):
    """A situation or event that causes distress"""
    trigger: str = Field(..., description="The trigger (e.g., 'Team meetings')")
    context: str = Field(..., description="How it was discussed")
    severity: Optional[str] = Field(None, description="mild, moderate, or severe")


class ActionItem(BaseModel):
    """Homework or task assigned to patient"""
    task: str = Field(..., description="What to do")
    category: str = Field(..., description="homework, reflection, behavioral, etc.")
    details: Optional[str] = Field(None, description="Additional context")


class SignificantQuote(BaseModel):
    """Important statement from patient"""
    quote: str = Field(..., description="The actual quote")
    context: str = Field(..., description="Why it's significant")
    timestamp_start: Optional[float] = Field(None, description="When in session (seconds)")


class RiskFlag(BaseModel):
    """Safety concern that needs attention"""
    type: str = Field(..., description="self_harm, suicidal_ideation, crisis, etc.")
    evidence: str = Field(..., description="What triggered this flag")
    severity: str = Field(..., description="low, medium, or high")


class ExtractedNotes(BaseModel):
    """Complete set of AI-extracted notes from a session"""

    # Core content
    key_topics: List[str] = Field(..., description="Main subjects discussed (3-7 items)")
    topic_summary: str = Field(..., description="2-3 sentence overview")

    # Clinical data
    strategies: List[Strategy] = Field(default_factory=list)
    emotional_themes: List[str] = Field(default_factory=list)
    triggers: List[Trigger] = Field(default_factory=list)
    action_items: List[ActionItem] = Field(default_factory=list)

    # Insights
    significant_quotes: List[SignificantQuote] = Field(default_factory=list)
    session_mood: MoodLevel
    mood_trajectory: str = Field(..., description="improving, declining, stable, or fluctuating")

    # Continuity
    follow_up_topics: List[str] = Field(default_factory=list)
    unresolved_concerns: List[str] = Field(default_factory=list)

    # Safety
    risk_flags: List[RiskFlag] = Field(default_factory=list)

    # Summaries
    therapist_notes: str = Field(..., description="Clinical summary for therapist (150-200 words)")
    patient_summary: str = Field(..., description="Friendly summary for patient (100-150 words)")


# ============================================================================
# Database Models (API representations)
# ============================================================================

class TranscriptSegment(BaseModel):
    """A single segment of transcribed speech"""
    start: float
    end: float
    text: str
    speaker: Optional[str] = None  # "Therapist" or "Client"


class SessionBase(BaseModel):
    """Base session data"""
    patient_id: UUID
    session_date: datetime


class SessionCreate(SessionBase):
    """Request to create a new session"""
    pass


class SessionResponse(SessionBase):
    """Complete session data returned by API"""
    id: UUID
    therapist_id: UUID
    duration_seconds: Optional[int] = None

    audio_filename: Optional[str] = None
    audio_url: Optional[str] = None

    transcript_text: Optional[str] = None
    transcript_segments: Optional[List[TranscriptSegment]] = None

    extracted_notes: Optional[ExtractedNotes] = None
    therapist_summary: Optional[str] = None
    patient_summary: Optional[str] = None
    risk_flags: Optional[List[RiskFlag]] = None

    status: SessionStatus
    error_message: Optional[str] = None

    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PatientBase(BaseModel):
    """Base patient data"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class PatientCreate(PatientBase):
    """Request to create a new patient"""
    therapist_id: UUID


class PatientResponse(PatientBase):
    """Patient data returned by API"""
    id: UUID
    therapist_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# API Request/Response Models
# ============================================================================

class ExtractNotesRequest(BaseModel):
    """Request to extract notes from a transcript"""
    transcript: str
    segments: Optional[List[TranscriptSegment]] = None


class ExtractNotesResponse(BaseModel):
    """Response from note extraction"""
    extracted_notes: ExtractedNotes
    processing_time: float


class SessionStatusUpdate(BaseModel):
    """Update session status"""
    status: SessionStatus
    error_message: Optional[str] = None
