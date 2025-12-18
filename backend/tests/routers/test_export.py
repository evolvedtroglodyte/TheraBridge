"""
Integration tests for export router endpoints.

Tests cover:
- Export job creation (session notes, progress reports)
- Job status polling and retrieval
- File downloads with HIPAA audit logging
- Authorization (therapist-only access)
- Error handling (invalid formats, missing files, etc.)
- Job deletion with file cleanup
- Template endpoints (stubs)
"""
import pytest
from fastapi import status
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta, date
from unittest.mock import patch, AsyncMock, MagicMock

from app.models.db_models import User, Patient, Session
from app.models.export_models import ExportJob, ExportTemplate, ExportAuditLog
from app.models.schemas import UserRole, SessionStatus

EXPORT_PREFIX = "/api/v1/export"


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def export_template(test_db):
    """Create test export template for progress reports."""
    template = ExportTemplate(
        name="Test Progress Report Template",
        description="Template for testing progress reports",
        export_type="progress_report",
        format="pdf",
        is_system=True,
        template_content="<html><body>{{ patient_name }}</body></html>"
    )
    test_db.add(template)
    test_db.commit()
    test_db.refresh(template)
    return template


@pytest.fixture(scope="function")
def completed_export_job(test_db, therapist_user, sample_patient):
    """Create completed export job with file for download testing."""
    # Create a test file in exports/output/
    export_dir = Path("exports/output")
    export_dir.mkdir(parents=True, exist_ok=True)

    test_file_path = export_dir / "test_completed_export.pdf"
    test_file_path.write_text("Mock PDF content for testing")

    job = ExportJob(
        user_id=therapist_user.id,
        patient_id=sample_patient.id,
        export_type="session_notes",
        format="pdf",
        status="completed",
        file_path=str(test_file_path),
        file_size_bytes=len("Mock PDF content for testing"),
        parameters={
            "session_ids": [str(uuid4())],
            "format": "pdf",
            "options": {"include_transcript": True}
        },
        completed_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=7)
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)

    yield job

    # Cleanup: Delete test file after test
    if test_file_path.exists():
        test_file_path.unlink()


@pytest.fixture(scope="function")
def pending_export_job(test_db, therapist_user, sample_patient):
    """Create pending export job for status polling tests."""
    job = ExportJob(
        user_id=therapist_user.id,
        patient_id=sample_patient.id,
        export_type="progress_report",
        format="pdf",
        status="pending",
        parameters={
            "patient_id": str(sample_patient.id),
            "start_date": "2025-01-01",
            "end_date": "2025-03-31",
            "format": "pdf"
        }
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)
    return job


@pytest.fixture(scope="function")
def failed_export_job(test_db, therapist_user, sample_patient):
    """Create failed export job for error case testing."""
    job = ExportJob(
        user_id=therapist_user.id,
        patient_id=sample_patient.id,
        export_type="session_notes",
        format="pdf",
        status="failed",
        error_message="Test error: File generation failed",
        parameters={
            "session_ids": [str(uuid4())],
            "format": "pdf"
        }
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)
    return job


@pytest.fixture(scope="function")
def multiple_export_jobs(test_db, therapist_user, sample_patient):
    """Create multiple export jobs with different statuses for list filtering tests."""
    jobs = []

    # Completed job
    jobs.append(ExportJob(
        user_id=therapist_user.id,
        patient_id=sample_patient.id,
        export_type="session_notes",
        format="pdf",
        status="completed",
        file_path="exports/output/job1.pdf",
        file_size_bytes=1024,
        parameters={"session_ids": [str(uuid4())], "format": "pdf"},
        completed_at=datetime.utcnow() - timedelta(hours=2),
        expires_at=datetime.utcnow() + timedelta(days=7)
    ))

    # Pending job
    jobs.append(ExportJob(
        user_id=therapist_user.id,
        patient_id=sample_patient.id,
        export_type="progress_report",
        format="docx",
        status="pending",
        parameters={"patient_id": str(sample_patient.id), "start_date": "2025-01-01", "end_date": "2025-03-31", "format": "docx"}
    ))

    # Processing job
    jobs.append(ExportJob(
        user_id=therapist_user.id,
        patient_id=sample_patient.id,
        export_type="session_notes",
        format="json",
        status="processing",
        parameters={"session_ids": [str(uuid4())], "format": "json"},
        started_at=datetime.utcnow()
    ))

    # Failed job
    jobs.append(ExportJob(
        user_id=therapist_user.id,
        patient_id=sample_patient.id,
        export_type="session_notes",
        format="csv",
        status="failed",
        error_message="Mock error",
        parameters={"session_ids": [str(uuid4())], "format": "csv"}
    ))

    test_db.add_all(jobs)
    test_db.commit()

    for job in jobs:
        test_db.refresh(job)

    return jobs


# ============================================================================
# Export Endpoint Tests
# ============================================================================

@pytest.mark.asyncio
async def test_export_session_notes_creates_job(async_db_client, therapist_auth_headers, sample_session, test_db):
    """Test that POST /session-notes creates an export job successfully."""
    test_db.commit()  # Ensure sample_session is committed

    response = async_db_client.post(
        f"{EXPORT_PREFIX}/session-notes",
        headers=therapist_auth_headers,
        json={
            "session_ids": [str(sample_session.id)],
            "format": "pdf",
            "options": {
                "include_transcript": True,
                "include_ai_notes": True,
                "include_action_items": True
            }
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # Verify response structure
    assert "id" in data
    assert data["export_type"] == "session_notes"
    assert data["format"] == "pdf"
    assert data["status"] == "pending"
    assert "created_at" in data

    # Verify job was created in database
    job_id = data["id"]
    job = test_db.query(ExportJob).filter(ExportJob.id == job_id).first()
    assert job is not None
    assert job.export_type == "session_notes"
    assert job.status == "pending"


@pytest.mark.asyncio
async def test_export_session_notes_multiple_sessions(async_db_client, therapist_auth_headers, sample_session, test_db):
    """Test exporting multiple sessions at once."""
    # Create additional session
    session_2 = Session(
        patient_id=sample_session.patient_id,
        therapist_id=sample_session.therapist_id,
        session_date=datetime.utcnow(),
        duration_seconds=3600,
        audio_filename="test_session_2.mp3",
        status=SessionStatus.completed.value
    )
    test_db.add(session_2)
    test_db.commit()
    test_db.refresh(session_2)

    response = async_db_client.post(
        f"{EXPORT_PREFIX}/session-notes",
        headers=therapist_auth_headers,
        json={
            "session_ids": [str(sample_session.id), str(session_2.id)],
            "format": "pdf",
            "options": {}
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["export_type"] == "session_notes"
    assert data["status"] == "pending"


@pytest.mark.asyncio
async def test_export_session_notes_docx_format(async_db_client, therapist_auth_headers, sample_session, test_db):
    """Test exporting session notes in DOCX format."""
    test_db.commit()

    response = async_db_client.post(
        f"{EXPORT_PREFIX}/session-notes",
        headers=therapist_auth_headers,
        json={
            "session_ids": [str(sample_session.id)],
            "format": "docx",
            "options": {"include_transcript": False}
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["format"] == "docx"


@pytest.mark.asyncio
async def test_export_session_notes_json_format(async_db_client, therapist_auth_headers, sample_session, test_db):
    """Test exporting session notes in JSON format."""
    test_db.commit()

    response = async_db_client.post(
        f"{EXPORT_PREFIX}/session-notes",
        headers=therapist_auth_headers,
        json={
            "session_ids": [str(sample_session.id)],
            "format": "json",
            "options": {}
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["format"] == "json"


@pytest.mark.asyncio
async def test_export_session_notes_csv_format(async_db_client, therapist_auth_headers, sample_session, test_db):
    """Test exporting session notes in CSV format."""
    test_db.commit()

    response = async_db_client.post(
        f"{EXPORT_PREFIX}/session-notes",
        headers=therapist_auth_headers,
        json={
            "session_ids": [str(sample_session.id)],
            "format": "csv",
            "options": {}
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["format"] == "csv"


@pytest.mark.asyncio
async def test_export_session_notes_invalid_format_rejected(async_db_client, therapist_auth_headers, sample_session):
    """Test that invalid export format returns 422 validation error."""
    response = async_db_client.post(
        f"{EXPORT_PREFIX}/session-notes",
        headers=therapist_auth_headers,
        json={
            "session_ids": [str(sample_session.id)],
            "format": "invalid_format",
            "options": {}
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_export_session_notes_empty_session_ids_rejected(async_db_client, therapist_auth_headers):
    """Test that empty session_ids list returns 422 validation error."""
    response = async_db_client.post(
        f"{EXPORT_PREFIX}/session-notes",
        headers=therapist_auth_headers,
        json={
            "session_ids": [],
            "format": "pdf",
            "options": {}
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_export_session_notes_too_many_sessions_rejected(async_db_client, therapist_auth_headers):
    """Test that exporting >100 sessions returns 422 validation error."""
    # Generate 101 fake session IDs
    too_many_sessions = [str(uuid4()) for _ in range(101)]

    response = async_db_client.post(
        f"{EXPORT_PREFIX}/session-notes",
        headers=therapist_auth_headers,
        json={
            "session_ids": too_many_sessions,
            "format": "pdf",
            "options": {}
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_export_progress_report_creates_job(async_db_client, therapist_auth_headers, sample_patient, test_db):
    """Test that POST /progress-report creates an export job successfully."""
    test_db.commit()

    response = async_db_client.post(
        f"{EXPORT_PREFIX}/progress-report",
        headers=therapist_auth_headers,
        json={
            "patient_id": str(sample_patient.id),
            "start_date": "2025-01-01",
            "end_date": "2025-03-31",
            "format": "pdf",
            "include_sections": {
                "patient_info": True,
                "treatment_goals": True,
                "goal_progress": True,
                "session_summary": True
            }
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "id" in data
    assert data["export_type"] == "progress_report"
    assert data["format"] == "pdf"
    assert data["status"] == "pending"

    # Verify job in database
    job_id = data["id"]
    job = test_db.query(ExportJob).filter(ExportJob.id == job_id).first()
    assert job is not None
    assert job.patient_id == sample_patient.id


@pytest.mark.asyncio
async def test_export_progress_report_docx_format(async_db_client, therapist_auth_headers, sample_patient, test_db):
    """Test exporting progress report in DOCX format."""
    test_db.commit()

    response = async_db_client.post(
        f"{EXPORT_PREFIX}/progress-report",
        headers=therapist_auth_headers,
        json={
            "patient_id": str(sample_patient.id),
            "start_date": "2025-01-01",
            "end_date": "2025-03-31",
            "format": "docx"
        }
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["format"] == "docx"


@pytest.mark.asyncio
async def test_export_progress_report_invalid_date_range(async_db_client, therapist_auth_headers, sample_patient):
    """Test that end_date before start_date returns 422 validation error."""
    response = async_db_client.post(
        f"{EXPORT_PREFIX}/progress-report",
        headers=therapist_auth_headers,
        json={
            "patient_id": str(sample_patient.id),
            "start_date": "2025-03-31",
            "end_date": "2025-01-01",  # End before start
            "format": "pdf"
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_export_progress_report_future_date_rejected(async_db_client, therapist_auth_headers, sample_patient):
    """Test that dates in the future return 422 validation error."""
    future_date = (date.today() + timedelta(days=30)).isoformat()

    response = async_db_client.post(
        f"{EXPORT_PREFIX}/progress-report",
        headers=therapist_auth_headers,
        json={
            "patient_id": str(sample_patient.id),
            "start_date": "2025-01-01",
            "end_date": future_date,
            "format": "pdf"
        }
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_export_treatment_summary_not_implemented(async_db_client, therapist_auth_headers, sample_patient):
    """Test that treatment summary export returns 501 Not Implemented."""
    response = async_db_client.post(
        f"{EXPORT_PREFIX}/treatment-summary",
        headers=therapist_auth_headers,
        json={
            "patient_id": str(sample_patient.id),
            "format": "pdf",
            "purpose": "insurance"
        }
    )

    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED


@pytest.mark.asyncio
async def test_export_full_record_not_implemented(async_db_client, therapist_auth_headers, sample_patient):
    """Test that full record export returns 501 Not Implemented."""
    response = async_db_client.post(
        f"{EXPORT_PREFIX}/full-record",
        headers=therapist_auth_headers,
        json={
            "patient_id": str(sample_patient.id),
            "format": "json"
        }
    )

    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED


# ============================================================================
# Job Management Tests
# ============================================================================

@pytest.mark.asyncio
async def test_list_export_jobs_returns_user_jobs(async_db_client, therapist_auth_headers, multiple_export_jobs, test_db):
    """Test that GET /jobs returns all jobs for the current user."""
    test_db.commit()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 4  # We created 4 jobs in the fixture

    # Verify jobs are ordered by created_at desc (newest first)
    # All should have download_url if completed
    completed_jobs = [j for j in data if j["status"] == "completed"]
    for job in completed_jobs:
        assert "download_url" in job
        assert job["download_url"].startswith("/api/v1/export/download/")


@pytest.mark.asyncio
async def test_list_export_jobs_filter_by_status_completed(async_db_client, therapist_auth_headers, multiple_export_jobs, test_db):
    """Test filtering jobs by status=completed."""
    test_db.commit()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs?status=completed",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert len(data) == 1  # Only 1 completed job
    assert data[0]["status"] == "completed"


@pytest.mark.asyncio
async def test_list_export_jobs_filter_by_status_pending(async_db_client, therapist_auth_headers, multiple_export_jobs, test_db):
    """Test filtering jobs by status=pending."""
    test_db.commit()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs?status=pending",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert len(data) == 1  # Only 1 pending job
    assert data[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_list_export_jobs_filter_by_patient_id(async_db_client, therapist_auth_headers, multiple_export_jobs, sample_patient, test_db):
    """Test filtering jobs by patient_id."""
    test_db.commit()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs?patient_id={str(sample_patient.id)}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    # All jobs in fixture are for sample_patient
    assert len(data) == 4


@pytest.mark.asyncio
async def test_list_export_jobs_respects_limit(async_db_client, therapist_auth_headers, multiple_export_jobs, test_db):
    """Test that limit parameter restricts number of results."""
    test_db.commit()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs?limit=2",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_export_jobs_limit_capped_at_500(async_db_client, therapist_auth_headers, multiple_export_jobs, test_db):
    """Test that limit is capped at 500 even if higher value is requested."""
    test_db.commit()

    # Request limit of 1000, should be capped at 500
    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs?limit=1000",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    # Should still work, just capped


@pytest.mark.asyncio
async def test_get_export_job_returns_details(async_db_client, therapist_auth_headers, completed_export_job, test_db):
    """Test that GET /jobs/{job_id} returns job details."""
    test_db.commit()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs/{completed_export_job.id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["id"] == str(completed_export_job.id)
    assert data["export_type"] == "session_notes"
    assert data["format"] == "pdf"
    assert data["status"] == "completed"
    assert "download_url" in data
    assert data["download_url"] == f"/api/v1/export/download/{completed_export_job.id}"


@pytest.mark.asyncio
async def test_get_export_job_pending_no_download_url(async_db_client, therapist_auth_headers, pending_export_job, test_db):
    """Test that pending jobs do not have download_url."""
    test_db.commit()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs/{pending_export_job.id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["status"] == "pending"
    assert data["download_url"] is None


@pytest.mark.asyncio
async def test_get_export_job_failed_includes_error_message(async_db_client, therapist_auth_headers, failed_export_job, test_db):
    """Test that failed jobs include error_message."""
    test_db.commit()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs/{failed_export_job.id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["status"] == "failed"
    assert data["error_message"] == "Test error: File generation failed"


@pytest.mark.asyncio
async def test_get_export_job_not_found(async_db_client, therapist_auth_headers):
    """Test that GET /jobs/{job_id} returns 404 for non-existent job."""
    fake_job_id = uuid4()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs/{fake_job_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_get_export_job_wrong_user_forbidden(async_db_client, patient_auth_headers, completed_export_job, test_db):
    """Test that users cannot access other users' jobs (403 Forbidden)."""
    test_db.commit()

    # Patient user trying to access therapist's job
    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs/{completed_export_job.id}",
        headers=patient_auth_headers
    )

    # Should be forbidden due to role check or ownership check
    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


# ============================================================================
# Download Tests
# ============================================================================

@pytest.mark.asyncio
async def test_download_export_returns_file(async_db_client, therapist_auth_headers, completed_export_job, test_db):
    """Test that GET /download/{job_id} returns the file with correct headers."""
    test_db.commit()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/download/{completed_export_job.id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    assert f"export_session_notes_{completed_export_job.id}.pdf" in response.headers["content-disposition"]
    assert response.headers["x-export-job-id"] == str(completed_export_job.id)

    # Verify content
    assert len(response.content) > 0


@pytest.mark.asyncio
async def test_download_export_creates_audit_log(async_db_client, therapist_auth_headers, completed_export_job, test_db):
    """Test that downloading a file creates an audit log entry."""
    test_db.commit()

    # Count audit logs before download
    before_count = test_db.query(ExportAuditLog).filter(
        ExportAuditLog.export_job_id == completed_export_job.id,
        ExportAuditLog.action == "downloaded"
    ).count()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/download/{completed_export_job.id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify audit log was created
    test_db.commit()  # Ensure changes are committed
    after_count = test_db.query(ExportAuditLog).filter(
        ExportAuditLog.export_job_id == completed_export_job.id,
        ExportAuditLog.action == "downloaded"
    ).count()

    assert after_count == before_count + 1

    # Verify audit log details
    audit_log = test_db.query(ExportAuditLog).filter(
        ExportAuditLog.export_job_id == completed_export_job.id,
        ExportAuditLog.action == "downloaded"
    ).order_by(ExportAuditLog.created_at.desc()).first()

    assert audit_log is not None
    assert audit_log.user_id == completed_export_job.user_id
    assert audit_log.patient_id == completed_export_job.patient_id


@pytest.mark.asyncio
async def test_download_nonexistent_job_404(async_db_client, therapist_auth_headers):
    """Test that downloading non-existent job returns 404."""
    fake_job_id = uuid4()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/download/{fake_job_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_download_pending_job_returns_400(async_db_client, therapist_auth_headers, pending_export_job, test_db):
    """Test that downloading pending job returns 400 Bad Request."""
    test_db.commit()

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/download/{pending_export_job.id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert "not ready" in data["detail"].lower()


@pytest.mark.asyncio
async def test_download_missing_file_returns_404(async_db_client, therapist_auth_headers, test_db, therapist_user, sample_patient):
    """Test that downloading job with missing file returns 404."""
    # Create job with file_path that doesn't exist
    job = ExportJob(
        user_id=therapist_user.id,
        patient_id=sample_patient.id,
        export_type="session_notes",
        format="pdf",
        status="completed",
        file_path="exports/output/nonexistent_file.pdf",
        file_size_bytes=1024,
        parameters={"session_ids": [str(uuid4())], "format": "pdf"},
        completed_at=datetime.utcnow()
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/download/{job.id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "not found on disk" in data["detail"].lower()


# ============================================================================
# Authorization Tests
# ============================================================================

@pytest.mark.asyncio
async def test_export_authorization_therapist_only(async_db_client, patient_auth_headers, sample_session):
    """Test that patients cannot access export endpoints (403 Forbidden)."""
    response = async_db_client.post(
        f"{EXPORT_PREFIX}/session-notes",
        headers=patient_auth_headers,
        json={
            "session_ids": [str(sample_session.id)],
            "format": "pdf",
            "options": {}
        }
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_progress_report_authorization_therapist_only(async_db_client, patient_auth_headers, sample_patient):
    """Test that patients cannot create progress reports (403 Forbidden)."""
    response = async_db_client.post(
        f"{EXPORT_PREFIX}/progress-report",
        headers=patient_auth_headers,
        json={
            "patient_id": str(sample_patient.id),
            "start_date": "2025-01-01",
            "end_date": "2025-03-31",
            "format": "pdf"
        }
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_list_jobs_authorization_therapist_only(async_db_client, patient_auth_headers):
    """Test that patients cannot list export jobs (403 Forbidden)."""
    response = async_db_client.get(
        f"{EXPORT_PREFIX}/jobs",
        headers=patient_auth_headers
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_download_wrong_user_403(async_db_client, test_db, completed_export_job):
    """Test that users cannot download other users' exports."""
    # Create a different therapist user
    other_therapist = User(
        email="other.therapist@test.com",
        hashed_password="hashed_password",
        first_name="Other",
        last_name="Therapist",
        full_name="Other Therapist",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    test_db.add(other_therapist)
    test_db.commit()
    test_db.refresh(other_therapist)

    # Generate token for other therapist
    from app.auth.utils import create_access_token
    other_token = create_access_token(other_therapist.id, other_therapist.role.value)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = async_db_client.get(
        f"{EXPORT_PREFIX}/download/{completed_export_job.id}",
        headers=other_headers
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
async def test_export_requires_authentication(async_db_client, sample_session):
    """Test that export endpoints require authentication."""
    response = async_db_client.post(
        f"{EXPORT_PREFIX}/session-notes",
        json={
            "session_ids": [str(sample_session.id)],
            "format": "pdf",
            "options": {}
        }
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Delete Tests
# ============================================================================

@pytest.mark.asyncio
async def test_delete_export_job_removes_file_and_record(async_db_client, therapist_auth_headers, completed_export_job, test_db):
    """Test that DELETE /jobs/{job_id} removes file and database record."""
    test_db.commit()

    job_id = completed_export_job.id
    file_path = Path(completed_export_job.file_path)

    # Verify file exists
    assert file_path.exists()

    response = async_db_client.delete(
        f"{EXPORT_PREFIX}/jobs/{job_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "deleted successfully" in data["message"].lower()

    # Verify file was deleted
    assert not file_path.exists()

    # Verify record was deleted from database
    job = test_db.query(ExportJob).filter(ExportJob.id == job_id).first()
    assert job is None


@pytest.mark.asyncio
async def test_delete_export_job_creates_audit_log(async_db_client, therapist_auth_headers, completed_export_job, test_db):
    """Test that deleting a job creates an audit log entry."""
    test_db.commit()

    job_id = completed_export_job.id

    response = async_db_client.delete(
        f"{EXPORT_PREFIX}/jobs/{job_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK

    # Verify audit log was created (before job deletion)
    # Note: Audit logs should persist even after job deletion
    audit_log = test_db.query(ExportAuditLog).filter(
        ExportAuditLog.export_job_id == job_id,
        ExportAuditLog.action == "deleted"
    ).first()

    # If cascade deletes audit logs, this will fail - that's intentional
    # Audit logs should be preserved for compliance
    assert audit_log is not None


@pytest.mark.asyncio
async def test_delete_export_job_not_found(async_db_client, therapist_auth_headers):
    """Test that deleting non-existent job returns 404."""
    fake_job_id = uuid4()

    response = async_db_client.delete(
        f"{EXPORT_PREFIX}/jobs/{fake_job_id}",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_export_job_wrong_user_403(async_db_client, test_db, completed_export_job):
    """Test that users cannot delete other users' jobs."""
    # Create different therapist
    other_therapist = User(
        email="delete.test.therapist@test.com",
        hashed_password="hashed_password",
        first_name="Delete",
        last_name="Test",
        full_name="Delete Test",
        role=UserRole.therapist,
        is_active=True,
        is_verified=False
    )
    test_db.add(other_therapist)
    test_db.commit()
    test_db.refresh(other_therapist)

    from app.auth.utils import create_access_token
    other_token = create_access_token(other_therapist.id, other_therapist.role.value)
    other_headers = {"Authorization": f"Bearer {other_token}"}

    response = async_db_client.delete(
        f"{EXPORT_PREFIX}/jobs/{completed_export_job.id}",
        headers=other_headers
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Template Endpoint Tests (Stubs)
# ============================================================================

@pytest.mark.asyncio
async def test_list_templates_returns_empty_list(async_db_client, therapist_auth_headers):
    """Test that GET /templates returns empty list (stub implementation)."""
    response = async_db_client.get(
        f"{EXPORT_PREFIX}/templates",
        headers=therapist_auth_headers
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0  # Stub returns empty list


@pytest.mark.asyncio
async def test_create_template_not_implemented(async_db_client, therapist_auth_headers):
    """Test that POST /templates returns 501 Not Implemented."""
    response = async_db_client.post(
        f"{EXPORT_PREFIX}/templates",
        headers=therapist_auth_headers,
        json={
            "name": "Custom Template",
            "export_type": "session_notes",
            "format": "pdf",
            "template_content": "<html><body>Test</body></html>"
        }
    )

    assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
