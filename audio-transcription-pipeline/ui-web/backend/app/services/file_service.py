"""File upload and validation service"""
import os
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile, HTTPException

class FileService:
    """Handles file uploads and validation"""

    ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".aac"}
    ALLOWED_MIME_TYPES = {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/x-wav",
        "audio/m4a",
        "audio/x-m4a",
        "audio/ogg",
        "audio/flac",
        "audio/aac",
        "application/octet-stream",  # Generic binary type
        "audio/*",  # Any audio type
    }

    def __init__(self, upload_dir: Path, max_size_mb: int = 100):
        self.upload_dir = upload_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file: UploadFile) -> None:
        """Validate uploaded file"""
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(self.ALLOWED_EXTENSIONS)}"
            )

        # Check MIME type
        if file.content_type and file.content_type not in self.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid MIME type: {file.content_type}"
            )

    async def save_upload(self, file: UploadFile) -> Tuple[str, str]:
        """
        Save uploaded file and return (job_id, file_path)

        Returns:
            Tuple of (job_id, absolute_path_to_saved_file)
        """
        self.validate_file(file)

        # Generate unique job ID
        job_id = str(uuid.uuid4())

        # Create job directory
        job_dir = self.upload_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Save file with original name
        file_ext = Path(file.filename).suffix
        file_path = job_dir / f"original{file_ext}"

        # Write file in chunks to handle large files
        with open(file_path, "wb") as f:
            total_size = 0
            chunk_size = 1024 * 1024  # 1MB chunks

            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                total_size += len(chunk)
                if total_size > self.max_size_bytes:
                    # Clean up partial file
                    file_path.unlink(missing_ok=True)
                    job_dir.rmdir()
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum size: {self.max_size_bytes / (1024 * 1024)}MB"
                    )

                f.write(chunk)

        return job_id, str(file_path.absolute())

    def get_file_path(self, job_id: str) -> Path:
        """Get the uploaded file path for a job"""
        job_dir = self.upload_dir / job_id
        if not job_dir.exists():
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Find the original file
        files = list(job_dir.glob("original.*"))
        if not files:
            raise HTTPException(status_code=404, detail=f"File for job {job_id} not found")

        return files[0]

    def delete_job_files(self, job_id: str) -> None:
        """Delete all files for a job"""
        import shutil

        job_dir = self.upload_dir / job_id
        if job_dir.exists():
            shutil.rmtree(job_dir)
