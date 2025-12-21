"""Request models for API endpoints"""
from pydantic import BaseModel, Field
from typing import Optional

class TranscriptionRequest(BaseModel):
    """Request model for starting a transcription job"""
    language: str = Field(default="english", description="Language of the audio")
    filename: str = Field(..., description="Original filename")
