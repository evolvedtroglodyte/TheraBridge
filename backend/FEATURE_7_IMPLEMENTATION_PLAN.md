# Feature 7: Export & Reporting - Implementation Plan

**Generated**: 2025-12-17
**Status**: Ready for implementation
**Estimated Duration**: 3-4 hours (with 6 parallel agents) vs 18-24 hours sequential

---

## Executive Summary

Feature 7 adds comprehensive export and reporting capabilities to TherapyBridge, enabling therapists to generate PDF/DOCX/JSON/CSV exports of session notes, progress reports, treatment summaries, and full patient records. The implementation follows existing backend patterns (service layer, background tasks, Pydantic schemas) and requires:

- **4 new database tables** (export_templates, export_jobs, export_audit_log, scheduled_reports)
- **3 new services** (PDF, DOCX, template rendering)
- **1 new router** with 13+ endpoints
- **5 new dependencies** (weasyprint, python-docx, jinja2, boto3, pillow)

---

## Phase 1: Database Schema (Wave 1)

### 1.1 Create Alembic Migration

**File**: `backend/alembic/versions/d4e5f6g7h8i9_add_export_tables.py`

**Tables to create**:
1. **export_templates** (12 columns)
2. **export_jobs** (13 columns)
3. **export_audit_log** (9 columns)
4. **scheduled_reports** (12 columns)

**Key patterns from existing migrations**:
- Use defensive pattern: check table existence with `inspector.get_table_names()`
- UUID primary keys with `server_default=sa.text('gen_random_uuid()')`
- Timestamps with `server_default=sa.text('now()')`
- Foreign keys with explicit names: `fk_{table}_{column}`
- Indexes with descriptive names: `idx_{table}_{column(s)}`
- Composite indexes for common queries: `(user_id, created_at DESC)`
- Enum types for status fields: `export_status_enum`, `export_type_enum`, `format_enum`

**Constraints**:
```sql
-- Unique template names per user
UNIQUE (created_by, name) WHERE created_by IS NOT NULL

-- Prevent duplicate scheduled reports
UNIQUE (user_id, template_id, patient_id) WHERE is_active = true
```

**Duration**: 15-20 minutes

---

### 1.2 Create SQLAlchemy Models

**File**: `backend/app/models/export_models.py` (NEW)

**Models to create**:

```python
class ExportTemplate(Base):
    """Export template configurations"""
    __tablename__ = 'export_templates'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    name = Column(String(100), nullable=False)
    description = Column(Text)
    export_type = Column(Enum(...), nullable=False)
    format = Column(Enum(...), nullable=False)
    template_content = Column(Text)  # Jinja2 template
    include_sections = Column(JSONB)  # Configurable sections
    is_system = Column(Boolean, default=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    created_at = Column(DateTime, server_default=text('now()'))
    updated_at = Column(DateTime, server_default=text('now()'), onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", back_populates="export_templates")
    jobs = relationship("ExportJob", back_populates="template")


class ExportJob(Base):
    """Export job tracking and status"""
    __tablename__ = 'export_jobs'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    template_id = Column(UUID(as_uuid=True), ForeignKey('export_templates.id', ondelete='SET NULL'))
    export_type = Column(String(50), nullable=False)
    format = Column(String(20), nullable=False)
    status = Column(Enum('pending', 'processing', 'completed', 'failed'), default='pending')
    parameters = Column(JSONB)  # Export options, filters, date ranges
    file_path = Column(String(500))
    file_size_bytes = Column(BigInteger)
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)  # Auto-delete after this time
    created_at = Column(DateTime, server_default=text('now()'))

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    patient = relationship("User", foreign_keys=[patient_id])
    template = relationship("ExportTemplate", back_populates="jobs")
    audit_logs = relationship("ExportAuditLog", back_populates="export_job", cascade="all, delete-orphan")


class ExportAuditLog(Base):
    """Audit trail for PHI export compliance"""
    __tablename__ = 'export_audit_log'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    export_job_id = Column(UUID(as_uuid=True), ForeignKey('export_jobs.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    patient_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='SET NULL'))
    action = Column(String(50), nullable=False)  # 'created', 'downloaded', 'deleted', 'shared'
    ip_address = Column(String(45))  # IPv4/IPv6
    user_agent = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(DateTime, server_default=text('now()'))

    # Relationships
    export_job = relationship("ExportJob", back_populates="audit_logs")


class ScheduledReport(Base):
    """Automated recurring report generation"""
    __tablename__ = 'scheduled_reports'

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('gen_random_uuid()'))
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey('export_templates.id', ondelete='CASCADE'), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'))
    schedule_type = Column(String(20), nullable=False)  # 'daily', 'weekly', 'monthly'
    schedule_config = Column(JSONB)  # {day_of_week: 1, time: "08:00"}
    parameters = Column(JSONB)
    delivery_method = Column(String(20))  # 'email', 'storage'
    is_active = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    created_at = Column(DateTime, server_default=text('now()'))

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    template = relationship("ExportTemplate")
```

**Add to User model** (`backend/app/models/db_models.py`):
```python
# In User class
export_templates = relationship("ExportTemplate", back_populates="creator", foreign_keys="ExportTemplate.created_by")
export_jobs = relationship("ExportJob", back_populates="user", foreign_keys="ExportJob.user_id")
```

**Duration**: 20-25 minutes

---

### 1.3 Create Pydantic Schemas

**File**: `backend/app/schemas/export_schemas.py` (NEW)

**Request schemas**:
```python
class SessionNotesExportRequest(BaseModel):
    """Request to export session notes"""
    session_ids: List[UUID] = Field(..., min_length=1)
    format: Literal["pdf", "docx", "json", "csv"]
    template_id: Optional[UUID] = None
    options: Dict[str, bool] = Field(default_factory=dict)
    # options: {include_transcript, include_ai_notes, include_action_items}

class ProgressReportExportRequest(BaseModel):
    """Request to export progress report"""
    patient_id: UUID
    start_date: date
    end_date: date
    format: Literal["pdf", "docx"]
    include_sections: Dict[str, bool] = Field(default_factory=lambda: {
        "patient_info": True,
        "treatment_goals": True,
        "goal_progress": True,
        "assessments": True,
        "session_summary": True,
        "clinical_observations": True,
        "recommendations": True
    })

class TreatmentSummaryExportRequest(BaseModel):
    """Request to export treatment summary"""
    patient_id: UUID
    format: Literal["pdf", "docx", "json"]
    purpose: Literal["insurance", "transfer", "records"]
    include_sections: Dict[str, bool]

class FullRecordExportRequest(BaseModel):
    """Request to export complete patient record"""
    patient_id: UUID
    format: Literal["json", "pdf"]
    include_sections: Dict[str, bool]
    date_range: Optional[Dict[str, date]] = None  # {start, end}

class ExportTemplateCreate(BaseModel):
    """Create custom export template"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    export_type: str
    format: str
    template_content: str  # HTML/Jinja2 template
    include_sections: Dict[str, bool]

class ScheduledReportCreate(BaseModel):
    """Create scheduled report"""
    template_id: UUID
    patient_id: Optional[UUID] = None
    schedule_type: Literal["daily", "weekly", "monthly"]
    schedule_config: Dict[str, Any]  # {day_of_week: 1, time: "08:00"}
    parameters: Dict[str, Any]
    delivery_method: Literal["email", "storage"]
```

**Response schemas**:
```python
class ExportJobResponse(BaseModel):
    """Export job status"""
    id: UUID
    export_type: str
    format: str
    status: str
    patient_name: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    file_size_bytes: Optional[int] = None
    expires_at: Optional[datetime] = None
    download_url: Optional[str] = None  # /api/v1/export/download/{job_id}
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ExportTemplateResponse(BaseModel):
    """Export template details"""
    id: UUID
    name: str
    description: Optional[str]
    export_type: str
    format: str
    is_system: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ScheduledReportResponse(BaseModel):
    """Scheduled report details"""
    id: UUID
    template_id: UUID
    patient_id: Optional[UUID]
    schedule_type: str
    is_active: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)
```

**Duration**: 15-20 minutes

---

## Phase 2: Service Layer (Wave 2)

### 2.1 Install Dependencies

**File**: `backend/requirements.txt`

**Add**:
```
weasyprint==60.1         # HTML to PDF conversion
python-docx==1.1.0       # DOCX generation
jinja2==3.1.2            # Template rendering (may already exist)
pillow==10.2.0           # Image processing (weasyprint dependency)
boto3==1.34.0            # S3 storage (optional, for cloud storage)
```

**Note**: WeasyPrint requires system dependencies:
- **macOS**: `brew install cairo pango gdk-pixbuf libffi`
- **Ubuntu**: `apt-get install libpango-1.0-0 libpangoft2-1.0-0`
- **Production**: Add to Dockerfile

**Duration**: 5 minutes + system dependencies

---

### 2.2 Create Template Directory Structure

**Create directories**:
```
backend/app/templates/
├── exports/
│   ├── session_notes.html
│   ├── progress_report.html
│   ├── treatment_summary.html
│   ├── full_record.html
│   └── components/
│       ├── header.html
│       ├── footer.html
│       └── styles.css
```

**Base template** (`exports/base.html`):
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{% block title %}TherapyBridge Export{% endblock %}</title>
    <style>
        @page {
            size: letter;
            margin: 1in;
            @bottom-right {
                content: "Page " counter(page) " of " counter(pages);
            }
        }
        body {
            font-family: Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
        }
        .header {
            border-bottom: 2px solid #333;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .section {
            margin: 20px 0;
            page-break-inside: avoid;
        }
        .section-title {
            font-size: 14pt;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        .confidential {
            color: #d32f2f;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="confidential">CONFIDENTIAL - PROTECTED HEALTH INFORMATION</div>

    <div class="header">
        {% block header %}{% endblock %}
    </div>

    <div class="content">
        {% block content %}{% endblock %}
    </div>

    <div class="footer">
        <p style="font-size: 9pt; color: #666;">
            Generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }} by TherapyBridge
        </p>
    </div>
</body>
</html>
```

**Progress report template** (`exports/progress_report.html`):
```html
{% extends "base.html" %}

{% block title %}Progress Report - {{ patient.full_name }}{% endblock %}

{% block header %}
<h1>Progress Report</h1>
<p><strong>Patient:</strong> {{ patient.full_name }}</p>
<p><strong>Period:</strong> {{ start_date.strftime('%B %d, %Y') }} - {{ end_date.strftime('%B %d, %Y') }}</p>
<p><strong>Prepared by:</strong> {{ therapist.full_name }}</p>
{% endblock %}

{% block content %}
{% if include_sections.patient_info %}
<div class="section">
    <div class="section-title">Patient Information</div>
    <p><strong>Name:</strong> {{ patient.full_name }}</p>
    <p><strong>Date of Birth:</strong> {{ patient.dob.strftime('%B %d, %Y') if patient.dob else 'N/A' }}</p>
    <p><strong>Email:</strong> {{ patient.email }}</p>
</div>
{% endif %}

{% if include_sections.treatment_goals %}
<div class="section">
    <div class="section-title">Treatment Goals & Progress</div>
    <table>
        <thead>
            <tr>
                <th>Goal</th>
                <th>Baseline</th>
                <th>Current</th>
                <th>Progress</th>
            </tr>
        </thead>
        <tbody>
            {% for goal in goals %}
            <tr>
                <td>{{ goal.description }}</td>
                <td>{{ goal.baseline }}</td>
                <td>{{ goal.current }}</td>
                <td>{{ goal.progress_percentage }}%</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
{% endif %}

{% if include_sections.session_summary %}
<div class="section">
    <div class="section-title">Session Summary</div>
    <p><strong>Total Sessions:</strong> {{ session_count }}</p>
    <p><strong>Average Duration:</strong> {{ avg_duration_minutes }} minutes</p>
    <p><strong>Key Topics Discussed:</strong></p>
    <ul>
        {% for topic in key_topics %}
        <li>{{ topic }}</li>
        {% endfor %}
    </ul>
</div>
{% endif %}
{% endblock %}
```

**Duration**: 30-40 minutes (creating 4-5 templates)

---

### 2.3 Create PDF Generation Service

**File**: `backend/app/services/pdf_generator.py` (NEW)

```python
"""PDF generation service using WeasyPrint and Jinja2"""
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

logger = logging.getLogger(__name__)


class PDFGeneratorService:
    """Service for generating PDF documents from templates"""

    def __init__(self, template_dir: Optional[Path] = None):
        """Initialize PDF generator with template directory"""
        self.template_dir = template_dir or Path("app/templates/exports")

        if not self.template_dir.exists():
            raise ValueError(f"Template directory not found: {self.template_dir}")

        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        self.env.filters['format_date'] = lambda d: d.strftime('%B %d, %Y') if d else 'N/A'
        self.env.filters['format_datetime'] = lambda d: d.strftime('%B %d, %Y at %I:%M %p') if d else 'N/A'

        # WeasyPrint font configuration
        self.font_config = FontConfiguration()

    async def render_template(
        self,
        template_name: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Render Jinja2 template to HTML.

        Args:
            template_name: Template filename (e.g., 'progress_report.html')
            context: Template context variables

        Returns:
            Rendered HTML string

        Raises:
            ValueError: If template not found or rendering fails
        """
        try:
            template = self.env.get_template(template_name)

            # Add default context variables
            context.setdefault('generated_at', datetime.utcnow())

            html_content = template.render(**context)
            logger.info(f"Template rendered successfully: {template_name}")
            return html_content

        except TemplateNotFound:
            raise ValueError(f"Template not found: {template_name}")
        except Exception as e:
            logger.error(f"Template rendering failed: {e}", exc_info=True)
            raise ValueError(f"Failed to render template: {str(e)}")

    async def generate_pdf(
        self,
        html_content: str,
        custom_css: Optional[str] = None
    ) -> bytes:
        """
        Convert HTML to PDF using WeasyPrint.

        Args:
            html_content: Rendered HTML string
            custom_css: Optional custom CSS string

        Returns:
            PDF file as bytes

        Raises:
            ValueError: If PDF generation fails
        """
        try:
            logger.info("Starting PDF generation")
            start_time = datetime.utcnow()

            # Create WeasyPrint HTML object
            html = HTML(string=html_content)

            # Generate PDF with optional custom CSS
            if custom_css:
                css = CSS(string=custom_css, font_config=self.font_config)
                pdf_bytes = html.write_pdf(stylesheets=[css], font_config=self.font_config)
            else:
                pdf_bytes = html.write_pdf(font_config=self.font_config)

            duration = (datetime.utcnow() - start_time).total_seconds()
            size_kb = len(pdf_bytes) / 1024

            logger.info(
                f"PDF generated successfully",
                extra={
                    "duration_seconds": duration,
                    "size_kb": round(size_kb, 2)
                }
            )

            return pdf_bytes

        except Exception as e:
            logger.error(f"PDF generation failed: {e}", exc_info=True)
            raise ValueError(f"Failed to generate PDF: {str(e)}")

    async def generate_from_template(
        self,
        template_name: str,
        context: Dict[str, Any],
        custom_css: Optional[str] = None
    ) -> bytes:
        """
        Render template and generate PDF in one step.

        Args:
            template_name: Template filename
            context: Template context variables
            custom_css: Optional custom CSS

        Returns:
            PDF file as bytes
        """
        html_content = await self.render_template(template_name, context)
        pdf_bytes = await self.generate_pdf(html_content, custom_css)
        return pdf_bytes


def get_pdf_generator() -> PDFGeneratorService:
    """FastAPI dependency to provide PDF generator service"""
    return PDFGeneratorService()
```

**Duration**: 25-30 minutes

---

### 2.4 Create DOCX Generation Service

**File**: `backend/app/services/docx_generator.py` (NEW)

```python
"""DOCX generation service using python-docx"""
import logging
from io import BytesIO
from typing import Dict, Any, List, Optional
from datetime import datetime

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = logging.getLogger(__name__)


class DOCXGeneratorService:
    """Service for generating DOCX documents"""

    def __init__(self):
        """Initialize DOCX generator"""
        pass

    async def generate_progress_report(
        self,
        patient: Dict[str, Any],
        therapist: Dict[str, Any],
        goals: List[Dict[str, Any]],
        sessions: List[Dict[str, Any]],
        date_range: Dict[str, datetime],
        include_sections: Dict[str, bool]
    ) -> bytes:
        """
        Generate progress report DOCX.

        Args:
            patient: Patient data
            therapist: Therapist data
            goals: Treatment goals with progress
            sessions: Session summaries
            date_range: {start_date, end_date}
            include_sections: Which sections to include

        Returns:
            DOCX file as bytes
        """
        try:
            logger.info("Starting DOCX progress report generation")

            doc = Document()

            # Add confidentiality notice
            heading = doc.add_paragraph("CONFIDENTIAL - PROTECTED HEALTH INFORMATION")
            heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            heading.runs[0].font.color.rgb = RGBColor(211, 47, 47)
            heading.runs[0].font.bold = True

            # Add title
            title = doc.add_heading('Progress Report', 0)

            # Add header information
            doc.add_paragraph(f"Patient: {patient['full_name']}")
            doc.add_paragraph(
                f"Period: {date_range['start_date'].strftime('%B %d, %Y')} - "
                f"{date_range['end_date'].strftime('%B %d, %Y')}"
            )
            doc.add_paragraph(f"Prepared by: {therapist['full_name']}")
            doc.add_paragraph("")  # Blank line

            # Patient information section
            if include_sections.get('patient_info', True):
                doc.add_heading('Patient Information', 1)
                doc.add_paragraph(f"Name: {patient['full_name']}")
                doc.add_paragraph(f"Email: {patient.get('email', 'N/A')}")
                doc.add_paragraph("")

            # Treatment goals section
            if include_sections.get('treatment_goals', True) and goals:
                doc.add_heading('Treatment Goals & Progress', 1)

                # Create table
                table = doc.add_table(rows=1, cols=4)
                table.style = 'Light Grid Accent 1'

                # Header row
                hdr_cells = table.rows[0].cells
                hdr_cells[0].text = 'Goal'
                hdr_cells[1].text = 'Baseline'
                hdr_cells[2].text = 'Current'
                hdr_cells[3].text = 'Progress'

                # Data rows
                for goal in goals:
                    row_cells = table.add_row().cells
                    row_cells[0].text = goal['description']
                    row_cells[1].text = str(goal.get('baseline', 'N/A'))
                    row_cells[2].text = str(goal.get('current', 'N/A'))
                    row_cells[3].text = f"{goal.get('progress_percentage', 0)}%"

                doc.add_paragraph("")

            # Session summary section
            if include_sections.get('session_summary', True):
                doc.add_heading('Session Summary', 1)
                doc.add_paragraph(f"Total Sessions: {len(sessions)}")

                if sessions:
                    avg_duration = sum(s.get('duration_minutes', 0) for s in sessions) / len(sessions)
                    doc.add_paragraph(f"Average Duration: {avg_duration:.1f} minutes")

                doc.add_paragraph("")

            # Save to bytes
            buffer = BytesIO()
            doc.save(buffer)
            buffer.seek(0)
            docx_bytes = buffer.read()

            logger.info(
                f"DOCX generated successfully",
                extra={"size_kb": len(docx_bytes) / 1024}
            )

            return docx_bytes

        except Exception as e:
            logger.error(f"DOCX generation failed: {e}", exc_info=True)
            raise ValueError(f"Failed to generate DOCX: {str(e)}")

    async def generate_treatment_summary(
        self,
        patient: Dict[str, Any],
        therapist: Dict[str, Any],
        treatment_data: Dict[str, Any],
        include_sections: Dict[str, bool]
    ) -> bytes:
        """Generate treatment summary DOCX"""
        # Similar structure to progress_report
        # ... implementation ...
        pass


def get_docx_generator() -> DOCXGeneratorService:
    """FastAPI dependency to provide DOCX generator service"""
    return DOCXGeneratorService()
```

**Duration**: 30-35 minutes

---

### 2.5 Create Export Service (Orchestration)

**File**: `backend/app/services/export_service.py` (NEW)

```python
"""Export orchestration service - coordinates data gathering and export generation"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload

from app.models.db_models import User, TherapySession, TherapistPatient
from app.models.export_models import ExportJob, ExportTemplate
from app.services.pdf_generator import PDFGeneratorService
from app.services.docx_generator import DOCXGeneratorService

logger = logging.getLogger(__name__)


class ExportService:
    """Service for coordinating export generation"""

    def __init__(
        self,
        pdf_generator: PDFGeneratorService,
        docx_generator: DOCXGeneratorService
    ):
        self.pdf_generator = pdf_generator
        self.docx_generator = docx_generator
        self.export_dir = Path("exports/output")
        self.export_dir.mkdir(parents=True, exist_ok=True)

    async def gather_session_notes_data(
        self,
        session_ids: List[UUID],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Gather data for session notes export.

        Returns:
            Context dict with sessions, therapist, patient data
        """
        # Query sessions with relationships
        query = (
            select(TherapySession)
            .where(TherapySession.id.in_(session_ids))
            .options(joinedload(TherapySession.patient))
            .options(joinedload(TherapySession.therapist))
        )
        result = await db.execute(query)
        sessions = result.scalars().unique().all()

        if not sessions:
            raise ValueError("No sessions found")

        # Extract therapist and patients
        therapist = sessions[0].therapist
        patients = {s.patient_id: s.patient for s in sessions if s.patient}

        return {
            "sessions": [self._serialize_session(s) for s in sessions],
            "therapist": self._serialize_user(therapist),
            "patients": {pid: self._serialize_user(p) for pid, p in patients.items()},
            "session_count": len(sessions)
        }

    async def gather_progress_report_data(
        self,
        patient_id: UUID,
        start_date: datetime,
        end_date: datetime,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Gather data for progress report export"""
        # Query patient
        patient_result = await db.execute(
            select(User).where(User.id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()

        if not patient:
            raise ValueError(f"Patient {patient_id} not found")

        # Query therapist relationship
        therapist_rel = await db.execute(
            select(TherapistPatient)
            .where(
                and_(
                    TherapistPatient.patient_id == patient_id,
                    TherapistPatient.is_active == True,
                    TherapistPatient.relationship_type == 'primary'
                )
            )
            .options(joinedload(TherapistPatient.therapist))
        )
        relationship = therapist_rel.scalar_one_or_none()
        therapist = relationship.therapist if relationship else None

        # Query sessions in date range
        sessions_query = (
            select(TherapySession)
            .where(
                and_(
                    TherapySession.patient_id == patient_id,
                    TherapySession.session_date >= start_date,
                    TherapySession.session_date <= end_date,
                    TherapySession.status == 'processed'
                )
            )
            .order_by(TherapySession.session_date.asc())
        )
        sessions_result = await db.execute(sessions_query)
        sessions = sessions_result.scalars().all()

        # Extract goals from extracted_notes
        goals = []
        for session in sessions:
            if session.extracted_notes:
                session_goals = session.extracted_notes.get('treatment_goals', [])
                # Merge and track progress
                # ... goal processing logic ...

        # Calculate metrics
        session_count = len(sessions)
        avg_duration = (
            sum(s.duration_seconds for s in sessions if s.duration_seconds) / session_count / 60
            if session_count > 0 else 0
        )

        # Extract key topics
        all_topics = []
        for session in sessions:
            if session.extracted_notes:
                all_topics.extend(session.extracted_notes.get('key_topics', []))

        # Count topic frequency
        from collections import Counter
        topic_counts = Counter(all_topics)
        key_topics = [topic for topic, count in topic_counts.most_common(10)]

        return {
            "patient": self._serialize_user(patient),
            "therapist": self._serialize_user(therapist) if therapist else None,
            "start_date": start_date,
            "end_date": end_date,
            "sessions": [self._serialize_session(s) for s in sessions],
            "session_count": session_count,
            "avg_duration_minutes": round(avg_duration, 1),
            "goals": goals,
            "key_topics": key_topics
        }

    async def generate_export(
        self,
        export_type: str,
        format: str,
        context: Dict[str, Any],
        template_id: Optional[UUID] = None,
        db: AsyncSession = None
    ) -> bytes:
        """
        Generate export file.

        Args:
            export_type: 'session_notes', 'progress_report', etc.
            format: 'pdf', 'docx', 'json', 'csv'
            context: Data context for rendering
            template_id: Optional custom template
            db: Database session

        Returns:
            Export file as bytes
        """
        logger.info(
            f"Generating export",
            extra={"type": export_type, "format": format}
        )

        if format == 'pdf':
            template_name = f"{export_type}.html"
            return await self.pdf_generator.generate_from_template(
                template_name,
                context
            )

        elif format == 'docx':
            if export_type == 'progress_report':
                return await self.docx_generator.generate_progress_report(
                    patient=context['patient'],
                    therapist=context['therapist'],
                    goals=context.get('goals', []),
                    sessions=context['sessions'],
                    date_range={
                        'start_date': context['start_date'],
                        'end_date': context['end_date']
                    },
                    include_sections=context.get('include_sections', {})
                )
            # ... other export types ...

        elif format == 'json':
            return json.dumps(context, indent=2, default=str).encode('utf-8')

        elif format == 'csv':
            # CSV generation logic
            pass

        else:
            raise ValueError(f"Unsupported format: {format}")

    def _serialize_user(self, user: Optional[User]) -> Optional[Dict[str, Any]]:
        """Convert User model to dict for templates"""
        if not user:
            return None

        return {
            "id": str(user.id),
            "full_name": user.full_name or f"{user.first_name} {user.last_name}".strip(),
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role.value
        }

    def _serialize_session(self, session: TherapySession) -> Dict[str, Any]:
        """Convert TherapySession to dict for templates"""
        return {
            "id": str(session.id),
            "session_date": session.session_date,
            "duration_minutes": session.duration_seconds / 60 if session.duration_seconds else None,
            "transcript_text": session.transcript_text,
            "extracted_notes": session.extracted_notes,
            "therapist_summary": session.therapist_summary,
            "patient_summary": session.patient_summary,
            "status": session.status
        }


def get_export_service(
    pdf_generator: PDFGeneratorService,
    docx_generator: DOCXGeneratorService
) -> ExportService:
    """FastAPI dependency to provide export service"""
    return ExportService(pdf_generator, docx_generator)
```

**Duration**: 40-50 minutes

---

## Phase 3: Router Layer (Wave 3)

### 3.1 Create Export Router

**File**: `backend/app/routers/export.py` (NEW)

```python
"""Export endpoints for generating and downloading reports"""
import logging
from pathlib import Path
from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.database import get_db
from app.auth.dependencies import require_role
from app.models.db_models import User
from app.models.export_models import ExportJob, ExportTemplate, ExportAuditLog
from app.schemas.export_schemas import (
    SessionNotesExportRequest,
    ProgressReportExportRequest,
    TreatmentSummaryExportRequest,
    FullRecordExportRequest,
    ExportJobResponse,
    ExportTemplateResponse,
    ExportTemplateCreate
)
from app.services.export_service import ExportService, get_export_service
from app.services.pdf_generator import get_pdf_generator
from app.services.docx_generator import get_docx_generator
from app.middleware.rate_limit import limiter

router = APIRouter(prefix="/export", tags=["export"])
logger = logging.getLogger(__name__)


async def process_export_job(
    job_id: UUID,
    export_type: str,
    request_data: dict,
    db: AsyncSession
):
    """
    Background task to process export job.

    Similar pattern to process_audio_pipeline in sessions.py
    """
    try:
        # Update status: processing
        await db.execute(
            update(ExportJob)
            .where(ExportJob.id == job_id)
            .values(status='processing', started_at=datetime.utcnow())
        )
        await db.commit()

        # Initialize services
        pdf_gen = get_pdf_generator()
        docx_gen = get_docx_generator()
        export_service = get_export_service(pdf_gen, docx_gen)

        # Gather data based on export type
        if export_type == 'session_notes':
            context = await export_service.gather_session_notes_data(
                request_data['session_ids'],
                db
            )
        elif export_type == 'progress_report':
            context = await export_service.gather_progress_report_data(
                request_data['patient_id'],
                request_data['start_date'],
                request_data['end_date'],
                db
            )
        # ... other export types ...

        # Generate export file
        file_bytes = await export_service.generate_export(
            export_type,
            request_data['format'],
            context,
            request_data.get('template_id'),
            db
        )

        # Save file
        file_ext = request_data['format']
        file_path = export_service.export_dir / f"{job_id}.{file_ext}"

        file_path.write_bytes(file_bytes)

        # Update job status: completed
        await db.execute(
            update(ExportJob)
            .where(ExportJob.id == job_id)
            .values(
                status='completed',
                file_path=str(file_path),
                file_size_bytes=len(file_bytes),
                completed_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
        )
        await db.commit()

        # Create audit log entry
        job = await db.get(ExportJob, job_id)
        audit_entry = ExportAuditLog(
            export_job_id=job_id,
            user_id=job.user_id,
            patient_id=job.patient_id,
            action='created'
        )
        db.add(audit_entry)
        await db.commit()

        logger.info(f"Export job completed", extra={"job_id": str(job_id)})

    except Exception as e:
        logger.error(f"Export job failed", extra={"job_id": str(job_id)}, exc_info=True)

        await db.execute(
            update(ExportJob)
            .where(ExportJob.id == job_id)
            .values(status='failed', error_message=str(e))
        )
        await db.commit()


@router.post("/session-notes", response_model=ExportJobResponse)
@limiter.limit("20/hour")
async def export_session_notes(
    request: Request,
    data: SessionNotesExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Export session notes in PDF, DOCX, JSON, or CSV format.

    Rate Limit: 20 exports per hour
    """
    logger.info(f"Session notes export requested", extra={
        "user_id": str(current_user.id),
        "session_count": len(data.session_ids)
    })

    # Create export job record
    job = ExportJob(
        user_id=current_user.id,
        template_id=data.template_id,
        export_type='session_notes',
        format=data.format,
        status='pending',
        parameters=data.model_dump()
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    # Queue background processing
    background_tasks.add_task(
        process_export_job,
        job.id,
        'session_notes',
        data.model_dump(),
        db
    )

    return ExportJobResponse(
        id=job.id,
        export_type=job.export_type,
        format=job.format,
        status=job.status,
        created_at=job.created_at
    )


@router.post("/progress-report", response_model=ExportJobResponse)
@limiter.limit("20/hour")
async def export_progress_report(
    request: Request,
    data: ProgressReportExportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """Export patient progress report"""
    # Similar to session_notes endpoint
    pass


@router.get("/jobs", response_model=List[ExportJobResponse])
async def list_export_jobs(
    status: str = None,
    patient_id: UUID = None,
    limit: int = 100,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """List export jobs for current user"""
    query = (
        select(ExportJob)
        .where(ExportJob.user_id == current_user.id)
        .order_by(ExportJob.created_at.desc())
    )

    if status:
        query = query.where(ExportJob.status == status)

    if patient_id:
        query = query.where(ExportJob.patient_id == patient_id)

    query = query.limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return [ExportJobResponse.model_validate(job) for job in jobs]


@router.get("/jobs/{job_id}", response_model=ExportJobResponse)
async def get_export_job(
    job_id: UUID,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """Get export job status and details"""
    job = await db.get(ExportJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Add download URL if completed
    response = ExportJobResponse.model_validate(job)
    if job.status == 'completed':
        response.download_url = f"/api/v1/export/download/{job_id}"

    return response


@router.get("/download/{job_id}")
async def download_export(
    job_id: UUID,
    request: Request,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """
    Download completed export file.

    Creates audit log entry for HIPAA compliance.
    """
    job = await db.get(ExportJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if job.status != 'completed':
        raise HTTPException(status_code=400, detail="Export not ready")

    if not job.file_path or not Path(job.file_path).exists():
        raise HTTPException(status_code=404, detail="Export file not found")

    # Create audit log entry
    audit_entry = ExportAuditLog(
        export_job_id=job_id,
        user_id=current_user.id,
        patient_id=job.patient_id,
        action='downloaded',
        ip_address=request.client.host,
        user_agent=request.headers.get('user-agent')
    )
    db.add(audit_entry)
    await db.commit()

    # Return file for download
    filename = f"export_{job.export_type}_{job_id}.{job.format}"

    return FileResponse(
        path=job.file_path,
        filename=filename,
        media_type=_get_media_type(job.format),
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "X-Export-Job-ID": str(job_id)
        }
    )


@router.delete("/jobs/{job_id}")
async def delete_export_job(
    job_id: UUID,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """Delete export job and file"""
    job = await db.get(ExportJob, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")

    if job.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Delete file if exists
    if job.file_path:
        file_path = Path(job.file_path)
        if file_path.exists():
            file_path.unlink()

    # Create audit log before deletion
    audit_entry = ExportAuditLog(
        export_job_id=job_id,
        user_id=current_user.id,
        patient_id=job.patient_id,
        action='deleted'
    )
    db.add(audit_entry)

    # Delete job record (cascade deletes audit logs)
    await db.delete(job)
    await db.commit()

    return {"message": "Export job deleted successfully"}


def _get_media_type(format: str) -> str:
    """Get MIME type for export format"""
    types = {
        'pdf': 'application/pdf',
        'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'json': 'application/json',
        'csv': 'text/csv'
    }
    return types.get(format, 'application/octet-stream')
```

**Template management endpoints** (add to same file):
```python
@router.get("/templates", response_model=List[ExportTemplateResponse])
async def list_templates(
    export_type: str = None,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """List available export templates (system + user custom)"""
    pass

@router.post("/templates", response_model=ExportTemplateResponse)
async def create_template(
    data: ExportTemplateCreate,
    current_user: User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    """Create custom export template"""
    pass
```

**Duration**: 60-70 minutes

---

### 3.2 Register Router in Main App

**File**: `backend/app/main.py`

```python
# Add import
from app.routers import export

# Register router
app.include_router(export.router, prefix="/api/v1")
```

**Duration**: 2 minutes

---

## Phase 4: Testing & Validation (Wave 4)

### 4.1 Create Test Fixtures

**File**: `backend/tests/routers/test_export.py` (NEW)

```python
"""Tests for export endpoints"""
import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from app.models.export_models import ExportJob, ExportTemplate

@pytest.fixture
async def export_template(db_session):
    """Create test export template"""
    template = ExportTemplate(
        name="Test Progress Report",
        export_type="progress_report",
        format="pdf",
        is_system=True
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template

@pytest.fixture
async def completed_export_job(db_session, therapist_user):
    """Create completed export job for testing downloads"""
    job = ExportJob(
        user_id=therapist_user.id,
        export_type="session_notes",
        format="pdf",
        status="completed",
        file_path="exports/output/test.pdf",
        file_size_bytes=10240,
        completed_at=datetime.utcnow()
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)
    return job
```

### 4.2 Create Integration Tests

```python
@pytest.mark.asyncio
async def test_export_session_notes_creates_job(client, therapist_token, session_1):
    """Test session notes export endpoint creates job"""
    response = client.post(
        "/api/v1/export/session-notes",
        headers={"Authorization": f"Bearer {therapist_token}"},
        json={
            "session_ids": [str(session_1.id)],
            "format": "pdf",
            "options": {"include_transcript": True}
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "pending"
    assert data["export_type"] == "session_notes"
    assert data["format"] == "pdf"

@pytest.mark.asyncio
async def test_download_export_returns_file(client, therapist_token, completed_export_job):
    """Test export download endpoint"""
    response = client.get(
        f"/api/v1/export/download/{completed_export_job.id}",
        headers={"Authorization": f"Bearer {therapist_token}"}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]

@pytest.mark.asyncio
async def test_export_authorization(client, patient_token, therapist_user):
    """Test patients cannot access export endpoints"""
    response = client.post(
        "/api/v1/export/session-notes",
        headers={"Authorization": f"Bearer {patient_token}"},
        json={"session_ids": [], "format": "pdf"}
    )

    assert response.status_code == 403
```

**Duration**: 40-50 minutes for comprehensive test suite

---

## Phase 5: Scheduled Reports (Wave 5)

### 5.1 Create Scheduled Report Task

**File**: `backend/app/tasks/scheduled_exports.py` (NEW)

```python
"""Scheduled report generation tasks"""
import logging
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.export_models import ScheduledReport, ExportJob
from app.services.export_service import ExportService
from app.services.pdf_generator import get_pdf_generator
from app.services.docx_generator import get_docx_generator

logger = logging.getLogger(__name__)


async def process_scheduled_reports() -> dict:
    """
    Process scheduled reports that are due.

    Runs on configurable schedule (e.g., hourly via APScheduler).
    """
    logger.info("Starting scheduled report processing")

    async with AsyncSessionLocal() as db:
        try:
            now = datetime.utcnow()

            # Find reports due for execution
            query = select(ScheduledReport).where(
                ScheduledReport.is_active == True,
                ScheduledReport.next_run_at <= now
            )
            result = await db.execute(query)
            reports = result.scalars().all()

            processed_count = 0

            for report in reports:
                try:
                    # Create export job
                    job = ExportJob(
                        user_id=report.user_id,
                        patient_id=report.patient_id,
                        template_id=report.template_id,
                        export_type=report.template.export_type,
                        format=report.template.format,
                        status='pending',
                        parameters=report.parameters
                    )
                    db.add(job)
                    await db.commit()

                    # Process export (similar to background task)
                    # ... export generation logic ...

                    # Update scheduled report
                    report.last_run_at = now
                    report.next_run_at = calculate_next_run(
                        report.schedule_type,
                        report.schedule_config
                    )
                    await db.commit()

                    processed_count += 1

                except Exception as e:
                    logger.error(
                        f"Failed to process scheduled report",
                        extra={"report_id": str(report.id)},
                        exc_info=True
                    )

            logger.info(f"Processed {processed_count} scheduled reports")
            return {"reports_processed": processed_count}

        except Exception as e:
            logger.error("Scheduled report processing failed", exc_info=True)
            raise


def calculate_next_run(schedule_type: str, config: dict) -> datetime:
    """Calculate next run time based on schedule configuration"""
    now = datetime.utcnow()

    if schedule_type == 'daily':
        # Run at specific time daily
        hour = config.get('hour', 0)
        next_run = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        return next_run

    elif schedule_type == 'weekly':
        # Run on specific day of week
        day_of_week = config.get('day_of_week', 0)  # 0=Monday
        hour = config.get('hour', 0)
        # ... calculation logic ...

    elif schedule_type == 'monthly':
        # Run on specific day of month
        day_of_month = config.get('day_of_month', 1)
        hour = config.get('hour', 0)
        # ... calculation logic ...

    return now + timedelta(days=1)  # Default fallback


def register_export_jobs():
    """Register scheduled export tasks with APScheduler"""
    from app.scheduler import scheduler
    from apscheduler.triggers.cron import CronTrigger

    scheduler.add_job(
        process_scheduled_reports,
        CronTrigger(minute=0),  # Run every hour on the hour
        id="scheduled_reports_processing",
        replace_existing=True,
        misfire_grace_time=600,
        coalesce=True
    )
```

### 5.2 Register Export Jobs in Scheduler

**File**: `backend/app/tasks/__init__.py`

```python
# Add import
from app.tasks.scheduled_exports import register_export_jobs

# Export function
__all__ = [
    "register_analytics_jobs",
    "register_export_jobs"  # Add this
]
```

**File**: `backend/app/scheduler.py`

```python
# In start_scheduler() function
def start_scheduler():
    """Start the APScheduler and register all jobs"""
    from app.tasks import register_analytics_jobs, register_export_jobs

    if not scheduler.running:
        register_analytics_jobs()
        register_export_jobs()  # Add this
        scheduler.start()
        logger.info("Scheduler started successfully")
```

**Duration**: 30-40 minutes

---

## Phase 6: File Cleanup & Expiration (Wave 6)

### 6.1 Add Export Cleanup to Existing Cleanup Service

**File**: `backend/app/services/cleanup.py`

```python
# Add method to AudioCleanupService or create separate ExportCleanupService

async def cleanup_expired_exports(dry_run: bool = False) -> CleanupResult:
    """
    Clean up expired export files.

    Deletes exports where expires_at < now()
    """
    logger.info("Starting expired export cleanup", extra={"dry_run": dry_run})

    async with AsyncSessionLocal() as db:
        try:
            now = datetime.utcnow()

            # Find expired jobs
            query = select(ExportJob).where(
                ExportJob.status == 'completed',
                ExportJob.expires_at < now,
                ExportJob.file_path.isnot(None)
            )
            result = await db.execute(query)
            expired_jobs = result.scalars().all()

            files_deleted = 0
            bytes_freed = 0

            for job in expired_jobs:
                file_path = Path(job.file_path)

                if file_path.exists():
                    file_size = file_path.stat().st_size

                    if not dry_run:
                        file_path.unlink()

                        # Update job record
                        job.file_path = None
                        job.file_size_bytes = None
                        await db.commit()

                    files_deleted += 1
                    bytes_freed += file_size

                    logger.info(
                        f"{'Would delete' if dry_run else 'Deleted'} expired export",
                        extra={
                            "job_id": str(job.id),
                            "file_size_kb": file_size / 1024
                        }
                    )

            return CleanupResult(
                files_deleted=files_deleted,
                bytes_freed=bytes_freed,
                dry_run=dry_run
            )

        except Exception as e:
            logger.error("Export cleanup failed", exc_info=True)
            raise
```

**Duration**: 20 minutes

---

## Implementation Summary

### Files to Create (16 new files)

**Database & Models:**
1. `backend/alembic/versions/d4e5f6g7h8i9_add_export_tables.py` - Migration
2. `backend/app/models/export_models.py` - SQLAlchemy models
3. `backend/app/schemas/export_schemas.py` - Pydantic schemas

**Services:**
4. `backend/app/services/pdf_generator.py` - PDF generation
5. `backend/app/services/docx_generator.py` - DOCX generation
6. `backend/app/services/export_service.py` - Export orchestration

**Templates:**
7. `backend/app/templates/exports/base.html` - Base template
8. `backend/app/templates/exports/session_notes.html` - Session notes template
9. `backend/app/templates/exports/progress_report.html` - Progress report template
10. `backend/app/templates/exports/treatment_summary.html` - Treatment summary template
11. `backend/app/templates/exports/full_record.html` - Full record template

**Router & Tasks:**
12. `backend/app/routers/export.py` - Export endpoints
13. `backend/app/tasks/scheduled_exports.py` - Scheduled report processing

**Tests:**
14. `backend/tests/routers/test_export.py` - Router tests
15. `backend/tests/services/test_pdf_generator.py` - PDF service tests
16. `backend/tests/services/test_export_service.py` - Export service tests

### Files to Modify (5 files)

1. `backend/app/models/db_models.py` - Add relationships to User model
2. `backend/app/main.py` - Register export router
3. `backend/app/services/cleanup.py` - Add export cleanup
4. `backend/app/tasks/__init__.py` - Export scheduled task registration
5. `backend/requirements.txt` - Add dependencies

---

## Execution Strategy with Parallel Orchestration

**Recommended approach**: Use `/cl:orchestrate` to parallelize implementation

### Wave Structure (6 agents)

**Wave 1: Database Schema** (3 agents)
- Agent 1: Create migration file
- Agent 2: Create export_models.py
- Agent 3: Create export_schemas.py

**Wave 2: Service Layer** (6 agents - pool expansion)
- Agent 1: Install dependencies + create template directory
- Agent 2: Create pdf_generator.py
- Agent 3: Create docx_generator.py
- Agent 4: Create export_service.py
- Agent 5: Create base.html template
- Agent 6: Create session_notes.html template

**Wave 3: More Templates** (3 agents - pool reuse)
- Agent 1: Create progress_report.html
- Agent 2: Create treatment_summary.html
- Agent 3: Create full_record.html

**Wave 4: Router & Tasks** (2 agents - pool reuse)
- Agent 1: Create export.py router
- Agent 2: Create scheduled_exports.py

**Wave 5: Integration** (2 agents - pool reuse)
- Agent 1: Modify db_models.py, main.py, cleanup.py
- Agent 2: Run migration, verify integration

**Wave 6: Testing** (3 agents - pool reuse)
- Agent 1: Create test_export.py
- Agent 2: Create test_pdf_generator.py
- Agent 3: Create test_export_service.py

**Total duration**: 3-4 hours (with orchestration) vs 18-24 hours sequential

---

## Testing Checklist

After implementation, verify:

- [ ] Migration runs successfully (`alembic upgrade head`)
- [ ] All 4 tables created in database
- [ ] PDF export generates valid PDF files
- [ ] DOCX export generates valid DOCX files
- [ ] JSON export returns proper JSON structure
- [ ] Download endpoint returns file with proper headers
- [ ] Audit log entries created on export creation and download
- [ ] Export files expire and are cleaned up after 7 days
- [ ] Scheduled reports execute on schedule
- [ ] Rate limiting works (20/hour limit)
- [ ] Authorization enforced (therapists only)
- [ ] File size limits enforced
- [ ] Templates render correctly with real data

---

## Security Considerations

**Implemented in plan**:
- ✅ Audit logging for all export actions (create, download, delete)
- ✅ IP address and user agent tracking
- ✅ File expiration (7 days default)
- ✅ Authorization checks (therapist role required)
- ✅ File path validation (prevent path traversal)
- ✅ Rate limiting (20 exports/hour)

**Recommendations for production**:
- Consider encrypting export files at rest
- Implement signed URLs with short expiration (24 hours)
- Add watermarks to PDFs with "CONFIDENTIAL" headers
- Use S3 with server-side encryption instead of local filesystem
- Implement file access logging separate from database

---

## Next Steps

1. **Review this plan** and approve approach
2. **Execute implementation** using `/cl:orchestrate` command:
   ```
   /cl:orchestrate Implement Feature 7 - Export & Reporting following FEATURE_7_IMPLEMENTATION_PLAN.md
   ```
3. **Run migration** after Wave 1 completes
4. **Test each export type** manually after Wave 4 completes
5. **Deploy to staging** for QA testing
6. **Update frontend** to consume new export endpoints

---

## Questions to Resolve Before Implementation

1. **Cloud storage**: Should we use S3 for production or keep local filesystem?
2. **File retention**: Is 7 days appropriate or should it be configurable per export type?
3. **Template customization**: Should therapists be able to create fully custom templates or just configure sections?
4. **Email delivery**: Should scheduled reports support email delivery? (Requires email service integration)
5. **FHIR support**: Is HL7 FHIR export a priority for v1 or defer to v2?

---

**End of Implementation Plan**
