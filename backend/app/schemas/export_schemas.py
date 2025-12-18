"""
Pydantic schemas for export API requests/responses
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from uuid import UUID


# ============================================================================
# Request Schemas
# ============================================================================

class SessionNotesExportRequest(BaseModel):
    """Request to export session notes"""
    session_ids: List[UUID] = Field(..., min_length=1, description="List of session IDs to export")
    format: Literal["pdf", "docx", "json", "csv"] = Field(..., description="Export format")
    template_id: Optional[UUID] = Field(None, description="Optional custom template ID")
    options: Dict[str, bool] = Field(
        default_factory=dict,
        description="Export options (e.g., include_transcript, include_ai_notes, include_action_items)"
    )

    @field_validator('session_ids')
    @classmethod
    def validate_session_ids_not_empty(cls, v: List[UUID]) -> List[UUID]:
        """Ensure session_ids list is not empty"""
        if not v or len(v) == 0:
            raise ValueError('session_ids cannot be empty')
        if len(v) > 100:
            raise ValueError('Cannot export more than 100 sessions at once')
        return v


class ProgressReportExportRequest(BaseModel):
    """Request to export progress report"""
    patient_id: UUID = Field(..., description="Patient ID for the report")
    start_date: date = Field(..., description="Start date of the reporting period")
    end_date: date = Field(..., description="End date of the reporting period")
    format: Literal["pdf", "docx"] = Field(..., description="Export format (PDF or DOCX only)")
    include_sections: Dict[str, bool] = Field(
        default_factory=lambda: {
            "patient_info": True,
            "treatment_goals": True,
            "goal_progress": True,
            "assessments": True,
            "session_summary": True,
            "clinical_observations": True,
            "recommendations": True
        },
        description="Sections to include in the report"
    )

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v: date, info) -> date:
        """Ensure end_date is after start_date"""
        start_date = info.data.get('start_date')
        if start_date and v < start_date:
            raise ValueError('end_date must be after start_date')
        return v

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_not_future(cls, v: date) -> date:
        """Ensure dates are not in the future"""
        if v > date.today():
            raise ValueError('Date cannot be in the future')
        return v


class TreatmentSummaryExportRequest(BaseModel):
    """Request to export treatment summary"""
    patient_id: UUID = Field(..., description="Patient ID for the summary")
    format: Literal["pdf", "docx", "json"] = Field(..., description="Export format")
    purpose: Literal["insurance", "transfer", "records"] = Field(
        ...,
        description="Purpose of the summary (affects content and formatting)"
    )
    include_sections: Dict[str, bool] = Field(
        default_factory=lambda: {
            "patient_demographics": True,
            "diagnosis": True,
            "treatment_history": True,
            "current_medications": True,
            "session_summary": True,
            "progress_notes": True,
            "clinical_impressions": True,
            "recommendations": True
        },
        description="Sections to include in the summary"
    )


class FullRecordExportRequest(BaseModel):
    """Request to export complete patient record"""
    patient_id: UUID = Field(..., description="Patient ID for the record export")
    format: Literal["json", "pdf"] = Field(..., description="Export format (JSON for machine-readable, PDF for human-readable)")
    include_sections: Dict[str, bool] = Field(
        default_factory=lambda: {
            "patient_info": True,
            "all_sessions": True,
            "transcripts": True,
            "extracted_notes": True,
            "treatment_goals": True,
            "progress_tracking": True,
            "assessments": True,
            "documents": True,
            "audit_log": False  # PHI access log
        },
        description="Sections to include in the full record"
    )
    date_range: Optional[Dict[str, date]] = Field(
        None,
        description="Optional date range filter with 'start' and 'end' keys"
    )

    @field_validator('date_range')
    @classmethod
    def validate_date_range(cls, v: Optional[Dict[str, date]]) -> Optional[Dict[str, date]]:
        """Ensure date_range has valid start and end dates"""
        if v is not None:
            if 'start' not in v or 'end' not in v:
                raise ValueError('date_range must contain both "start" and "end" keys')
            if v['end'] < v['start']:
                raise ValueError('end date must be after start date')
        return v


class ExportTemplateCreate(BaseModel):
    """Create custom export template"""
    name: str = Field(..., min_length=1, max_length=100, description="Template name")
    description: Optional[str] = Field(None, max_length=500, description="Template description")
    export_type: str = Field(..., min_length=1, max_length=50, description="Type of export (e.g., 'progress_report', 'session_notes')")
    format: str = Field(..., min_length=1, max_length=20, description="Export format (e.g., 'pdf', 'docx')")
    template_content: str = Field(..., min_length=1, description="HTML/Jinja2 template content")
    include_sections: Dict[str, bool] = Field(
        default_factory=dict,
        description="Default sections to include when using this template"
    )

    @field_validator('name')
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Ensure name is not empty after stripping"""
        stripped = v.strip()
        if not stripped:
            raise ValueError('Template name cannot be empty')
        return stripped

    @field_validator('template_content')
    @classmethod
    def validate_template_content(cls, v: str) -> str:
        """Ensure template content is not empty"""
        if not v or len(v.strip()) == 0:
            raise ValueError('Template content cannot be empty')
        return v


class ScheduledReportCreate(BaseModel):
    """Create scheduled report"""
    template_id: UUID = Field(..., description="Template to use for the report")
    patient_id: Optional[UUID] = Field(None, description="Optional patient ID (if None, applies to all patients)")
    schedule_type: Literal["daily", "weekly", "monthly"] = Field(..., description="Report frequency")
    schedule_config: Dict[str, Any] = Field(
        ...,
        description="Schedule configuration (e.g., {day_of_week: 1, hour: 8} for weekly reports)"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional parameters for report generation (e.g., include_sections, date_range_days)"
    )
    delivery_method: Literal["email", "storage"] = Field(
        ...,
        description="How to deliver the generated report"
    )

    @field_validator('schedule_config')
    @classmethod
    def validate_schedule_config(cls, v: Dict[str, Any], info) -> Dict[str, Any]:
        """Validate schedule_config based on schedule_type"""
        schedule_type = info.data.get('schedule_type')

        if schedule_type == 'weekly':
            if 'day_of_week' not in v:
                raise ValueError('Weekly schedule requires "day_of_week" (0-6, 0=Monday)')
            if not isinstance(v['day_of_week'], int) or not (0 <= v['day_of_week'] <= 6):
                raise ValueError('day_of_week must be an integer between 0 (Monday) and 6 (Sunday)')

        if schedule_type == 'monthly':
            if 'day_of_month' not in v:
                raise ValueError('Monthly schedule requires "day_of_month" (1-28)')
            if not isinstance(v['day_of_month'], int) or not (1 <= v['day_of_month'] <= 28):
                raise ValueError('day_of_month must be an integer between 1 and 28')

        # Validate hour if provided
        if 'hour' in v:
            if not isinstance(v['hour'], int) or not (0 <= v['hour'] <= 23):
                raise ValueError('hour must be an integer between 0 and 23')

        return v


# ============================================================================
# Response Schemas
# ============================================================================

class ExportJobResponse(BaseModel):
    """Export job status"""
    id: UUID = Field(..., description="Unique export job identifier")
    export_type: str = Field(..., description="Type of export (e.g., 'session_notes', 'progress_report')")
    format: str = Field(..., description="Export format (e.g., 'pdf', 'docx', 'json')")
    status: str = Field(..., description="Job status (pending, processing, completed, failed)")
    patient_name: Optional[str] = Field(None, description="Patient name if applicable")
    created_at: datetime = Field(..., description="When the job was created")
    completed_at: Optional[datetime] = Field(None, description="When the job completed")
    file_size_bytes: Optional[int] = Field(None, description="Size of the generated file in bytes")
    expires_at: Optional[datetime] = Field(None, description="When the file will be automatically deleted")
    download_url: Optional[str] = Field(None, description="URL to download the file (e.g., /api/v1/export/download/{job_id})")
    error_message: Optional[str] = Field(None, description="Error message if job failed")

    model_config = ConfigDict(from_attributes=True)


class ExportTemplateResponse(BaseModel):
    """Export template details"""
    id: UUID = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    export_type: str = Field(..., description="Type of export this template is for")
    format: str = Field(..., description="Export format")
    is_system: bool = Field(..., description="Whether this is a system template (cannot be modified)")
    created_at: datetime = Field(..., description="When the template was created")

    model_config = ConfigDict(from_attributes=True)


class ScheduledReportResponse(BaseModel):
    """Scheduled report details"""
    id: UUID = Field(..., description="Unique scheduled report identifier")
    template_id: UUID = Field(..., description="Template used for this scheduled report")
    patient_id: Optional[UUID] = Field(None, description="Patient ID if report is patient-specific")
    schedule_type: str = Field(..., description="Report frequency (daily, weekly, monthly)")
    is_active: bool = Field(..., description="Whether the scheduled report is currently active")
    last_run_at: Optional[datetime] = Field(None, description="When the report was last generated")
    next_run_at: Optional[datetime] = Field(None, description="When the report will next be generated")

    model_config = ConfigDict(from_attributes=True)
