"""Response models for API endpoints"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    """Status of a transcription job"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Speaker(BaseModel):
    """Speaker information"""
    id: str
    label: str  # "SPEAKER_00", "SPEAKER_01", etc.
    total_duration: float = 0.0
    segment_count: int = 0

class Segment(BaseModel):
    """Transcript segment with speaker and timing"""
    start: float
    end: float
    text: str
    speaker_id: Optional[str] = None
    confidence: Optional[float] = None

class PerformanceMetrics(BaseModel):
    """Performance metrics for the transcription job"""
    total_processing_time_seconds: float
    api_latency_seconds: Optional[float] = None
    computation_time_seconds: Optional[float] = None
    current_memory_mb: Optional[float] = None

class TranscriptionMetadata(BaseModel):
    """Metadata about the transcription"""
    source_file: str
    file_size_mb: float
    duration: float
    language: str
    timestamp: str
    pipeline_type: str = "CPU_API"

class TranscriptionResult(BaseModel):
    """Complete transcription result"""
    id: str
    status: JobStatus
    filename: str
    metadata: Optional[TranscriptionMetadata] = None
    performance: Optional[PerformanceMetrics] = None
    speakers: List[Speaker] = []
    segments: List[Segment] = []
    quality: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class JobResponse(BaseModel):
    """Response when creating a new job"""
    job_id: str
    status: JobStatus
    message: str

class JobListResponse(BaseModel):
    """Response for listing all jobs"""
    jobs: List[TranscriptionResult]
    total: int
