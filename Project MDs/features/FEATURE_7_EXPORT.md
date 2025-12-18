# Feature 7: Export & Reporting

## Overview
Enable therapists to export patient records, session notes, progress reports, and treatment summaries in various formats for documentation, insurance claims, and records transfer.

## Requirements

### Export Types
1. **Session Notes** - Individual or batch session documentation
2. **Treatment Summaries** - Comprehensive treatment overview
3. **Progress Reports** - Goal progress and assessment results
4. **Full Patient Record** - Complete patient file export
5. **Insurance Reports** - Formatted for claim submission

### Export Formats
- PDF (formatted documents)
- DOCX (editable documents)
- JSON (structured data)
- CSV (tabular data)
- HL7 FHIR (healthcare interoperability)

### Features
- Template-based report generation
- Batch export capability
- Scheduled/automated reports
- Audit trail for exports
- Redaction options for sensitive content

## Database Schema

```sql
-- Export templates
CREATE TABLE export_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    export_type VARCHAR(50) NOT NULL, -- 'session_note', 'progress_report', 'treatment_summary', 'full_record'
    format VARCHAR(20) NOT NULL, -- 'pdf', 'docx', 'json', 'csv'
    template_content TEXT, -- Jinja2/HTML template for PDF/DOCX
    include_sections JSONB, -- configurable sections to include
    is_system BOOLEAN DEFAULT false,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Export jobs
CREATE TABLE export_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    patient_id UUID REFERENCES users(id),
    template_id UUID REFERENCES export_templates(id),
    export_type VARCHAR(50) NOT NULL,
    format VARCHAR(20) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
    parameters JSONB, -- date ranges, filters, options
    file_path VARCHAR(500),
    file_size_bytes BIGINT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP, -- auto-delete after this time
    created_at TIMESTAMP DEFAULT NOW()
);

-- Export audit log
CREATE TABLE export_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    export_job_id UUID REFERENCES export_jobs(id),
    user_id UUID REFERENCES users(id),
    patient_id UUID REFERENCES users(id),
    action VARCHAR(50) NOT NULL, -- 'created', 'downloaded', 'deleted', 'shared'
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Scheduled reports
CREATE TABLE scheduled_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    template_id UUID REFERENCES export_templates(id),
    patient_id UUID REFERENCES users(id), -- null for practice-wide
    schedule_type VARCHAR(20) NOT NULL, -- 'daily', 'weekly', 'monthly'
    schedule_config JSONB, -- day of week, time, etc.
    parameters JSONB,
    delivery_method VARCHAR(20), -- 'email', 'storage'
    is_active BOOLEAN DEFAULT true,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### Export Generation

#### POST /api/v1/export/session-notes
Export session notes.

Request:
```json
{
    "session_ids": ["uuid1", "uuid2"],
    "format": "pdf",
    "template_id": "uuid",
    "options": {
        "include_transcript": false,
        "include_ai_notes": true,
        "include_action_items": true
    }
}
```

Response:
```json
{
    "job_id": "uuid",
    "status": "processing",
    "estimated_completion": "2024-03-10T14:05:00Z"
}
```

#### POST /api/v1/export/progress-report
Export progress report.

Request:
```json
{
    "patient_id": "uuid",
    "start_date": "2024-01-01",
    "end_date": "2024-03-10",
    "format": "pdf",
    "include_sections": {
        "patient_info": true,
        "treatment_goals": true,
        "goal_progress": true,
        "assessments": true,
        "session_summary": true,
        "clinical_observations": true,
        "recommendations": true
    }
}
```

#### POST /api/v1/export/treatment-summary
Export treatment summary.

Request:
```json
{
    "patient_id": "uuid",
    "treatment_plan_id": "uuid",
    "format": "docx",
    "purpose": "insurance", -- 'insurance', 'transfer', 'records'
    "include_sections": {
        "diagnosis": true,
        "treatment_plan": true,
        "interventions_used": true,
        "progress_summary": true,
        "prognosis": true
    }
}
```

#### POST /api/v1/export/full-record
Export complete patient record.

Request:
```json
{
    "patient_id": "uuid",
    "format": "json",
    "include_sections": {
        "demographics": true,
        "treatment_plans": true,
        "sessions": true,
        "notes": true,
        "assessments": true,
        "timeline": true,
        "attachments": false
    },
    "date_range": {
        "start": "2023-01-01",
        "end": "2024-03-10"
    }
}
```

### Export Job Management

#### GET /api/v1/export/jobs
List export jobs.

Query params:
- `status`: Filter by status
- `patient_id`: Filter by patient
- `limit`: Number of results

Response:
```json
{
    "jobs": [
        {
            "id": "uuid",
            "export_type": "progress_report",
            "format": "pdf",
            "status": "completed",
            "patient_name": "John Doe",
            "created_at": "2024-03-10T14:00:00Z",
            "completed_at": "2024-03-10T14:02:00Z",
            "file_size_bytes": 245678,
            "expires_at": "2024-03-17T14:02:00Z"
        }
    ]
}
```

#### GET /api/v1/export/jobs/{job_id}
Get job status and download link.

Response:
```json
{
    "id": "uuid",
    "status": "completed",
    "download_url": "/api/v1/export/download/uuid",
    "expires_at": "2024-03-17T14:02:00Z"
}
```

#### GET /api/v1/export/download/{job_id}
Download exported file.

#### DELETE /api/v1/export/jobs/{job_id}
Delete export job and file.

### Templates

#### GET /api/v1/export/templates
List available templates.

#### POST /api/v1/export/templates
Create custom template.

Request:
```json
{
    "name": "Insurance Progress Report",
    "description": "Formatted for insurance claims",
    "export_type": "progress_report",
    "format": "pdf",
    "template_content": "<html>...</html>",
    "include_sections": {
        "patient_info": true,
        "diagnosis": true,
        "treatment_goals": true,
        "progress": true,
        "medical_necessity": true
    }
}
```

### Scheduled Reports

#### POST /api/v1/export/scheduled
Create scheduled report.

Request:
```json
{
    "template_id": "uuid",
    "patient_id": "uuid",
    "schedule_type": "monthly",
    "schedule_config": {
        "day_of_month": 1,
        "time": "08:00"
    },
    "parameters": {
        "include_sections": {...}
    },
    "delivery_method": "email"
}
```

#### GET /api/v1/export/scheduled
List scheduled reports.

#### DELETE /api/v1/export/scheduled/{id}
Cancel scheduled report.

## Export Templates

### Progress Report Template (PDF)
```html
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .header { border-bottom: 2px solid #333; padding-bottom: 10px; }
        .section { margin: 20px 0; }
        .section-title { font-size: 14pt; font-weight: bold; color: #333; }
        table { width: 100%; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Progress Report</h1>
        <p>Patient: {{ patient.name }}</p>
        <p>Period: {{ start_date }} - {{ end_date }}</p>
        <p>Prepared by: {{ therapist.name }}, {{ therapist.credentials }}</p>
    </div>

    {% if include_sections.diagnosis %}
    <div class="section">
        <div class="section-title">Diagnosis</div>
        {% for dx in diagnoses %}
        <p>{{ dx.code }} - {{ dx.description }}</p>
        {% endfor %}
    </div>
    {% endif %}

    {% if include_sections.goals %}
    <div class="section">
        <div class="section-title">Treatment Goals & Progress</div>
        <table>
            <tr>
                <th>Goal</th>
                <th>Baseline</th>
                <th>Current</th>
                <th>Progress</th>
            </tr>
            {% for goal in goals %}
            <tr>
                <td>{{ goal.description }}</td>
                <td>{{ goal.baseline }}</td>
                <td>{{ goal.current }}</td>
                <td>{{ goal.progress_percentage }}%</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endif %}

    <!-- Additional sections... -->
</body>
</html>
```

### Insurance Claim Format
```json
{
    "claim_info": {
        "provider_npi": "1234567890",
        "provider_name": "Dr. Jane Smith",
        "patient_id": "INS-12345",
        "diagnosis_codes": ["F41.1", "F32.1"],
        "procedure_codes": ["90834", "90837"],
        "service_dates": ["2024-03-01", "2024-03-08"],
        "total_units": 2
    },
    "clinical_summary": {
        "presenting_problem": "...",
        "treatment_provided": "...",
        "progress": "...",
        "medical_necessity": "..."
    }
}
```

## Implementation Notes

### PDF Generation
```python
from weasyprint import HTML
from jinja2 import Template

async def generate_pdf(template: ExportTemplate, data: dict) -> bytes:
    """Generate PDF from template and data."""
    jinja_template = Template(template.template_content)
    html_content = jinja_template.render(**data)
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
```

### Background Job Processing
```python
from celery import shared_task

@shared_task
async def process_export_job(job_id: str):
    """Process export job in background."""
    job = await get_export_job(job_id)
    job.status = "processing"
    job.started_at = datetime.now()
    await save_job(job)

    try:
        data = await gather_export_data(job)
        file_bytes = await generate_export(job.template, data, job.format)
        file_path = await save_export_file(job_id, file_bytes)

        job.status = "completed"
        job.file_path = file_path
        job.file_size_bytes = len(file_bytes)
        job.completed_at = datetime.now()
        job.expires_at = datetime.now() + timedelta(days=7)
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)

    await save_job(job)
    await create_audit_log(job, "created")
```

### File Storage
- Use S3 or similar object storage
- Encrypt files at rest
- Auto-expire files after 7 days
- Signed URLs for secure downloads

## Security Considerations
- All exports logged in audit trail
- PHI encrypted in transit and at rest
- Download links expire after 24 hours
- IP and user agent recorded
- Redaction options for sensitive content

## Testing Checklist
- [ ] Session notes export (PDF, DOCX)
- [ ] Progress report generation
- [ ] Treatment summary export
- [ ] Full record export (JSON)
- [ ] Custom template creation
- [ ] Job status tracking
- [ ] File download with signed URL
- [ ] Audit log entries created
- [ ] Scheduled report execution
- [ ] File expiration cleanup

## Files to Create/Modify
- `app/routers/export.py`
- `app/services/export_service.py`
- `app/services/pdf_generator.py`
- `app/services/docx_generator.py`
- `app/tasks/export_tasks.py`
- `app/tasks/scheduled_reports.py`
- `app/models/export.py`
- `app/schemas/export.py`
- `app/templates/exports/` (Jinja2 templates)
- `alembic/versions/xxx_add_export_tables.py`

## Dependencies
```
weasyprint==60.1
python-docx==1.1.0
jinja2==3.1.2
boto3==1.34.0  # for S3 storage
celery==5.3.6  # for background jobs
```
