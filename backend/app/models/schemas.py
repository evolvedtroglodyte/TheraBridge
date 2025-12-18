"""
Pydantic schemas for API requests/responses and AI extraction
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
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


class TimelineImportance(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"
    milestone = "milestone"


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


# ============================================================================
# Analytics Response Schemas
# ============================================================================

class AnalyticsOverviewResponse(BaseModel):
    """Therapist's practice overview metrics"""
    total_patients: int = Field(..., description="Total number of patients")
    active_patients: int = Field(..., description="Number of active patients")
    sessions_this_week: int = Field(..., description="Sessions completed this week")
    sessions_this_month: int = Field(..., description="Sessions completed this month")
    upcoming_sessions: int = Field(..., description="Number of upcoming sessions")
    completion_rate: float = Field(..., description="Session completion rate (0.0-1.0)")


class SessionFrequency(BaseModel):
    """Patient's session frequency metrics"""
    weekly_average: float = Field(..., description="Average sessions per week")
    trend: str = Field(..., description="Frequency trend: stable, increasing, or decreasing")


class MoodTrendData(BaseModel):
    """Mood data point for a specific period"""
    date: str = Field(..., description="Period in YYYY-MM format")
    avg_pre: float = Field(..., description="Average pre-session mood score")
    avg_post: float = Field(..., description="Average post-session mood score")


class MoodTrend(BaseModel):
    """Patient's mood trend over time"""
    data: List[MoodTrendData] = Field(..., description="Mood data points by period")
    trend: str = Field(..., description="Overall trend: improving, declining, or stable")


class GoalStatus(BaseModel):
    """Patient's goal completion status"""
    total: int = Field(..., description="Total number of goals")
    completed: int = Field(..., description="Number of completed goals")
    in_progress: int = Field(..., description="Number of goals in progress")
    not_started: int = Field(..., description="Number of not started goals")


class PatientProgressResponse(BaseModel):
    """Detailed progress metrics for a specific patient"""
    patient_id: UUID = Field(..., description="Patient identifier")
    total_sessions: int = Field(..., description="Total number of sessions")
    first_session_date: str = Field(..., description="Date of first session (YYYY-MM-DD)")
    last_session_date: str = Field(..., description="Date of last session (YYYY-MM-DD)")
    session_frequency: SessionFrequency
    mood_trend: MoodTrend
    goals: GoalStatus

    model_config = ConfigDict(from_attributes=True)


class SessionTrendDataPoint(BaseModel):
    """Data point for session trends chart"""
    label: str = Field(..., description="Period label (e.g., 'Jan', 'Week 1')")
    sessions: int = Field(..., description="Number of sessions in period")
    unique_patients: int = Field(..., description="Number of unique patients seen")


class SessionTrendsResponse(BaseModel):
    """Session trends over time"""
    period: str = Field(..., description="Aggregation period: week, month, quarter, or year")
    data: List[SessionTrendDataPoint] = Field(..., description="Trend data points")


class TopicFrequency(BaseModel):
    """Frequency data for a specific topic"""
    name: str = Field(..., description="Topic name")
    count: int = Field(..., description="Number of occurrences")
    percentage: float = Field(..., description="Percentage of total sessions (0.0-1.0)")


class TopicsResponse(BaseModel):
    """Frequently discussed topics across sessions"""
    topics: List[TopicFrequency] = Field(..., description="Topics sorted by frequency")


# ============================================================================
# Timeline Schemas
# ============================================================================

class TimelineEventBase(BaseModel):
    """Base schema for timeline events with common fields"""
    event_type: str = Field(..., description="Type of event (e.g., 'session', 'milestone', 'note')")
    event_subtype: Optional[str] = Field(None, description="Optional subtype for categorization")
    event_date: datetime = Field(..., description="When the event occurred")
    title: str = Field(..., min_length=1, max_length=200, description="Event title")
    description: Optional[str] = Field(None, description="Detailed description of the event")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional structured data")
    related_entity_type: Optional[str] = Field(None, description="Type of related entity (e.g., 'session', 'goal')")
    related_entity_id: Optional[UUID] = Field(None, description="ID of related entity")
    importance: TimelineImportance = Field(default=TimelineImportance.normal, description="Event importance level")
    is_private: bool = Field(default=False, description="Whether event is private to therapist")


class TimelineEventCreate(TimelineEventBase):
    """Schema for creating a new timeline event"""

    @field_validator('event_date')
    @classmethod
    def validate_event_date_not_future(cls, v: datetime) -> datetime:
        """Ensure event date is not in the future"""
        if v > datetime.now():
            raise ValueError('Event date cannot be in the future')
        return v

    @field_validator('title')
    @classmethod
    def validate_title_length(cls, v: str) -> str:
        """Ensure title is between 1 and 200 characters"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        if len(v) > 200:
            raise ValueError('Title cannot exceed 200 characters')
        return v.strip()


class TimelineEventResponse(TimelineEventBase):
    """Schema for timeline event responses from API"""
    id: UUID = Field(..., description="Unique event identifier")
    patient_id: UUID = Field(..., description="Associated patient ID")
    therapist_id: Optional[UUID] = Field(None, description="Associated therapist ID (if applicable)")
    created_at: datetime = Field(..., description="When the event record was created")

    model_config = ConfigDict(from_attributes=True)


class SessionTimelineResponse(BaseModel):
    """Paginated timeline response for a patient's history"""
    events: List[TimelineEventResponse] = Field(..., description="List of timeline events")
    next_cursor: Optional[UUID] = Field(None, description="Cursor for next page of results")
    has_more: bool = Field(..., description="Whether more events are available")
    total_count: int = Field(..., description="Total number of events for this patient")


class TimelineSummaryResponse(BaseModel):
    """Summary statistics for a patient's timeline"""
    patient_id: UUID = Field(..., description="Patient identifier")
    first_session: Optional[date] = Field(None, description="Date of first session")
    last_session: Optional[date] = Field(None, description="Date of most recent session")
    total_sessions: int = Field(..., description="Total number of sessions completed")
    total_events: int = Field(..., description="Total number of timeline events")
    events_by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of events grouped by type"
    )
    milestones_achieved: int = Field(..., description="Number of milestone events")
    recent_highlights: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recent significant events (last 5)"
    )


class TimelineChartDataResponse(BaseModel):
    """Chart data for visualizing patient timeline"""
    mood_trend: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Mood trend data points over time"
    )
    session_frequency: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Session frequency distribution over time"
    )
    milestones: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Milestone events with dates and details"
    )


# ============================================================================
# Template and Note Schemas (Feature 3)
# ============================================================================

class NoteStatus(str, Enum):
    """Session note status"""
    draft = "draft"
    completed = "completed"
    signed = "signed"


class TemplateFieldType(str, Enum):
    """Types of fields in a template"""
    text = "text"
    textarea = "textarea"
    select = "select"
    multiselect = "multiselect"
    checkbox = "checkbox"
    number = "number"
    date = "date"
    scale = "scale"


class TemplateType(str, Enum):
    """Template types"""
    soap = "soap"
    dap = "dap"
    birp = "birp"
    progress = "progress"
    custom = "custom"


class TemplateField(BaseModel):
    """A single field within a template section"""
    id: str = Field(..., description="Unique field identifier within the section")
    label: str = Field(..., description="Display label for the field")
    type: TemplateFieldType = Field(..., description="Field input type")
    required: bool = Field(default=False, description="Whether field is required")
    options: Optional[List[str]] = Field(None, description="Options for select/multiselect types")
    ai_mapping: Optional[str] = Field(None, description="Maps to ExtractedNotes field for auto-fill")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    help_text: Optional[str] = Field(None, description="Help text for users")

    @model_validator(mode='after')
    def validate_options_for_select_types(self):
        """Ensure select/multiselect fields have options"""
        if self.type in [TemplateFieldType.select, TemplateFieldType.multiselect]:
            if not self.options or len(self.options) == 0:
                raise ValueError(f'Field type {self.type} requires at least one option')
        return self


class TemplateSection(BaseModel):
    """A section within a template (e.g., Subjective in SOAP)"""
    id: str = Field(..., description="Unique section identifier within the template")
    name: str = Field(..., description="Display name of the section")
    description: Optional[str] = Field(None, description="Section description or instructions")
    fields: List[TemplateField] = Field(..., description="Fields in this section")

    @field_validator('fields')
    @classmethod
    def validate_fields_not_empty(cls, v: List[TemplateField]) -> List[TemplateField]:
        """Ensure each section has at least one field"""
        if not v or len(v) == 0:
            raise ValueError('Each section must have at least one field')
        return v


class TemplateStructure(BaseModel):
    """Complete template structure"""
    sections: List[TemplateSection] = Field(..., description="All sections in the template")

    @field_validator('sections')
    @classmethod
    def validate_sections_not_empty(cls, v: List[TemplateSection]) -> List[TemplateSection]:
        """Ensure template has at least one section"""
        if not v or len(v) == 0:
            raise ValueError('Template must have at least one section')
        return v

    @field_validator('sections')
    @classmethod
    def validate_unique_section_ids(cls, v: List[TemplateSection]) -> List[TemplateSection]:
        """Ensure all section IDs are unique"""
        section_ids = [section.id for section in v]
        if len(section_ids) != len(set(section_ids)):
            raise ValueError('All section IDs must be unique')
        return v


class TemplateBase(BaseModel):
    """Base template fields"""
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    template_type: TemplateType = Field(..., description="Template type (soap, dap, birp, etc.)")
    is_shared: bool = Field(default=False, description="Whether template is shared with other therapists")


class TemplateCreate(TemplateBase):
    """Request to create a template"""
    structure: TemplateStructure = Field(..., description="Complete template structure with sections and fields")


class TemplateUpdate(BaseModel):
    """Request to update a template (partial updates allowed)"""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Updated template name")
    description: Optional[str] = Field(None, description="Updated template description")
    is_shared: Optional[bool] = Field(None, description="Updated sharing status")
    structure: Optional[TemplateStructure] = Field(None, description="Updated template structure")


class TemplateResponse(TemplateBase):
    """Template data returned by API"""
    id: UUID = Field(..., description="Unique template identifier")
    is_system: bool = Field(..., description="Whether this is a system-provided template")
    created_by: Optional[UUID] = Field(None, description="User ID of template creator (null for system templates)")
    structure: TemplateStructure = Field(..., description="Complete template structure")
    created_at: datetime = Field(..., description="Template creation timestamp")
    updated_at: datetime = Field(..., description="Template last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class TemplateListItem(BaseModel):
    """Minimal template data for list views"""
    id: UUID = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    template_type: TemplateType = Field(..., description="Template type")
    is_system: bool = Field(..., description="Whether this is a system template")
    is_shared: bool = Field(..., description="Whether template is shared")
    section_count: int = Field(..., description="Number of sections in template (computed from structure)")
    created_at: datetime = Field(..., description="Template creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class NoteCreate(BaseModel):
    """Request to create a session note"""
    template_id: UUID = Field(..., description="Template used for this note")
    content: Dict[str, Any] = Field(..., description="Filled template data (JSONB structure)")

    @field_validator('content')
    @classmethod
    def validate_content_not_empty(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure content has at least one entry"""
        if not v or len(v) == 0:
            raise ValueError('Note content cannot be empty')
        return v


class NoteUpdate(BaseModel):
    """Request to update a session note"""
    content: Optional[Dict[str, Any]] = Field(None, description="Updated note content")
    status: Optional[NoteStatus] = Field(None, description="Updated note status")

    @field_validator('content')
    @classmethod
    def validate_content_not_empty_if_provided(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """If content is provided, ensure it's not empty"""
        if v is not None and len(v) == 0:
            raise ValueError('Note content cannot be empty if provided')
        return v


class NoteResponse(BaseModel):
    """Session note data returned by API"""
    id: UUID = Field(..., description="Unique note identifier")
    session_id: UUID = Field(..., description="Associated therapy session ID")
    template_id: Optional[UUID] = Field(None, description="Template used for this note (null for legacy notes)")
    content: Dict[str, Any] = Field(..., description="Filled template data (JSONB structure)")
    status: NoteStatus = Field(..., description="Note status (draft, completed, signed)")
    signed_at: Optional[datetime] = Field(None, description="When note was signed (null if not signed)")
    signed_by: Optional[UUID] = Field(None, description="User ID who signed the note (null if not signed)")
    created_at: datetime = Field(..., description="Note creation timestamp")
    updated_at: datetime = Field(..., description="Note last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class AutoFillRequest(BaseModel):
    """Request to auto-fill a template from extracted notes"""
    template_type: TemplateType = Field(..., description="Type of template to auto-fill (soap, dap, birp, progress)")


class AutoFillResponse(BaseModel):
    """Auto-filled template data response"""
    template_type: TemplateType = Field(..., description="Type of template that was auto-filled")
    auto_filled_content: Dict[str, Any] = Field(..., description="Filled template sections with extracted data")
    confidence_scores: Dict[str, float] = Field(
        ...,
        description="Per-section confidence scores (0.0-1.0) indicating data quality"
    )
    missing_fields: Dict[str, List[str]] = Field(
        ...,
        description="Sections with missing or low-confidence data that need manual review"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata (e.g., extraction_time, ai_model, etc.)"
    )

    @field_validator('confidence_scores')
    @classmethod
    def validate_confidence_range(cls, v: Dict[str, float]) -> Dict[str, float]:
        """Ensure all confidence scores are between 0.0 and 1.0"""
        for section, score in v.items():
            if not 0.0 <= score <= 1.0:
                raise ValueError(f'Confidence score for section "{section}" must be between 0.0 and 1.0')
        return v
