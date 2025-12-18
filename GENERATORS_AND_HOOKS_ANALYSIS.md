# PDF/DOCX Generators and Auto-Generation Hooks - Deep Dive Analysis

## Executive Summary

This document provides a comprehensive analysis of the TherapyBridge backend's document generation system and auto-generation hooks. The system uses a sophisticated orchestration pattern where:

1. **Audio processing** triggers automatic note extraction
2. **Note extraction** provides structured data to document generators
3. **Document generators** (PDF/DOCX) create professional exports from templates
4. **Export service** coordinates multi-format generation (PDF, DOCX, JSON)
5. **Auto-generation hooks** trigger downstream processes when session status transitions

---

## 1. PDF GENERATOR SERVICE

**File:** `/backend/app/services/pdf_generator.py`

### Architecture & Libraries

```python
# Core dependencies:
- weasyprint==60.1          # HTML → PDF conversion engine
- jinja2==3.1.2             # Template rendering for dynamic content
- pillow==10.2.0            # Image processing (weasyprint dependency)
```

**System Requirements:**
```bash
# macOS: brew install cairo pango gdk-pixbuf libffi
# Ubuntu: apt-get install libpango-1.0-0 libpangoft2-1.0-0
```

### Class: PDFGeneratorService

**Initialization:**
```python
class PDFGeneratorService:
    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path("app/templates/exports")
        self.env = Environment(loader=FileSystemLoader(...))
        self.env.filters['format_date'] = lambda d: d.strftime('%B %d, %Y')
        self.env.filters['format_datetime'] = lambda d: d.strftime('%B %d, %Y at %I:%M %p')
        self.font_config = FontConfiguration()
```

### Core Methods

#### 1. `render_template(template_name, context) -> str`

**Purpose:** Convert Jinja2 template to HTML string

**Signature:**
```python
async def render_template(
    self,
    template_name: str,           # e.g., 'progress_report.html'
    context: Dict[str, Any]       # Template variables
) -> str:
```

**Data Structures Expected:**
```python
# Example context for progress_report.html:
{
    "patient": {
        "full_name": "John Doe",
        "email": "john@example.com",
        "dob": datetime(1990, 1, 15)
    },
    "therapist": {
        "full_name": "Dr. Jane Smith"
    },
    "start_date": datetime(2025, 1, 1),
    "end_date": datetime(2025, 3, 31),
    "goals": [
        {
            "description": "Reduce anxiety",
            "baseline": "8/10",
            "current": "5/10",
            "progress_percentage": 38
        }
    ],
    "session_count": 12,
    "avg_duration_minutes": 55.5,
    "key_topics": ["anxiety", "work stress", "relationships"],
    "include_sections": {
        "patient_info": True,
        "treatment_goals": True,
        "session_summary": True
    }
}
```

**Features:**
- Jinja2 template loading with autoescape enabled
- Custom filters for date formatting
- Automatic `generated_at` timestamp injection
- Exception handling with detailed error logging

**Example Usage:**
```python
html = await pdf_generator.render_template(
    'progress_report.html',
    {
        'patient': patient_data,
        'therapist': therapist_data,
        'start_date': start_date,
        'end_date': end_date,
        'goals': goals_list,
        'session_count': 12,
        'avg_duration_minutes': 55.5,
        'key_topics': ['anxiety', 'work stress'],
        'include_sections': {'patient_info': True, 'treatment_goals': True}
    }
)
```

#### 2. `generate_pdf(html_content, custom_css=None) -> bytes`

**Purpose:** Convert HTML string to PDF bytes using WeasyPrint

**Signature:**
```python
async def generate_pdf(
    self,
    html_content: str,              # Rendered HTML string
    custom_css: Optional[str] = None  # Custom CSS styling
) -> bytes:
```

**Features:**
- WeasyPrint HTML object creation
- Optional custom CSS injection
- Font configuration for consistent rendering
- Performance metrics logging (duration, file size)
- Exception handling with detailed error traces

**Example Usage:**
```python
pdf_bytes = await pdf_generator.generate_pdf(
    html_content=html_string,
    custom_css="""
        body { font-family: Arial; margin: 20px; }
        .header { color: #2c3e50; border-bottom: 2px solid #3498db; }
    """
)
# Returns: b'%PDF-1.4\n%...' (PDF binary)
```

#### 3. `generate_from_template(template_name, context, custom_css=None) -> bytes`

**Purpose:** One-shot method combining template rendering + PDF generation

**Signature:**
```python
async def generate_from_template(
    self,
    template_name: str,
    context: Dict[str, Any],
    custom_css: Optional[str] = None
) -> bytes:
```

**Flow:**
1. Renders Jinja2 template to HTML
2. Generates PDF from HTML
3. Returns PDF bytes

**Example Usage:**
```python
pdf_bytes = await pdf_generator.generate_from_template(
    'progress_report.html',
    context={
        'patient': {...},
        'therapist': {...},
        'goals': [...]
    }
)
```

### Templates Directory

**Location:** `/backend/app/templates/exports/`

**Available Templates:**
1. **progress_report.html** - Clinical progress summary with goals and metrics
2. **session_notes.html** - Exported session transcripts and AI-extracted notes
3. **treatment_summary.html** - Comprehensive treatment overview
4. **full_record.html** - Complete patient record export
5. **base.html** - Base template extended by others

**Template Features:**
- Jinja2 conditional blocks (`{% if include_sections.treatment_goals %}`)
- Loop iteration over collections (`{% for goal in goals %}`)
- Custom filters (`.strftime()`, `.join()`, etc.)
- Table generation for structured data
- Responsive styling for PDF printing

**Example: progress_report.html snippet**
```html
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
```

### FastAPI Dependency

```python
def get_pdf_generator() -> PDFGeneratorService:
    """FastAPI dependency to provide PDF generator service"""
    return PDFGeneratorService()

# Usage in routers:
@router.get("/export/pdf")
async def export_as_pdf(
    pdf_gen: PDFGeneratorService = Depends(get_pdf_generator)
):
    pdf_bytes = await pdf_gen.generate_from_template(...)
    return FileResponse(pdf_bytes, media_type="application/pdf")
```

---

## 2. DOCX GENERATOR SERVICE

**File:** `/backend/app/services/docx_generator.py`

### Architecture & Libraries

```python
# Core dependencies:
- python-docx==1.1.0        # DOCX document creation
```

### Class: DOCXGeneratorService

**Initialization:**
```python
class DOCXGeneratorService:
    def __init__(self):
        pass  # Stateless service
```

### Core Methods

#### 1. `generate_progress_report(patient, therapist, goals, sessions, date_range, include_sections) -> bytes`

**Purpose:** Create a formatted DOCX progress report

**Signature:**
```python
async def generate_progress_report(
    self,
    patient: Dict[str, Any],
    therapist: Dict[str, Any],
    goals: List[Dict[str, Any]],
    sessions: List[Dict[str, Any]],
    date_range: Dict[str, datetime],
    include_sections: Dict[str, bool]
) -> bytes:
```

**Data Structures:**

```python
# Patient data
patient = {
    'full_name': 'John Doe',
    'email': 'john@example.com',
    # Optional fields
    'dob': datetime(1990, 1, 15),
    'phone': '555-1234'
}

# Therapist data
therapist = {
    'full_name': 'Dr. Jane Smith',
    'email': 'jane@clinic.com',
    'license': 'LCSW'
}

# Treatment goals
goals = [
    {
        'description': 'Reduce social anxiety',
        'baseline': '8/10',
        'current': '5/10',
        'progress_percentage': 37.5
    },
    {
        'description': 'Improve sleep quality',
        'baseline': 4,  # hours per night
        'current': 6.5,
        'progress_percentage': 62.5
    }
]

# Sessions
sessions = [
    {
        'session_date': datetime(2025, 1, 15),
        'duration_minutes': 55,
        'transcript_text': 'Full transcript...',
        'status': 'processed'
    }
]

# Date range
date_range = {
    'start_date': datetime(2025, 1, 1),
    'end_date': datetime(2025, 3, 31)
}

# Section control
include_sections = {
    'patient_info': True,
    'treatment_goals': True,
    'session_summary': True,
    'clinical_observations': True,
    'recommendations': True
}
```

**Features:**
1. **Header Section:**
   - Confidentiality notice (RED, bold, centered)
   - Title: "Progress Report"
   - Patient/Period/Prepared by info

2. **Patient Information Section:**
   - Name, DOB, email, contact info

3. **Treatment Goals Section:**
   - Table with Goal | Baseline | Current | Progress % columns
   - Formatted rows for each goal

4. **Session Summary Section:**
   - Total sessions count
   - Average duration calculation
   - Session frequency metrics

5. **Document Output:**
   - BytesIO buffer
   - DOCX binary format
   - Proper document formatting and styling

**Example Usage:**
```python
docx_bytes = await docx_generator.generate_progress_report(
    patient={'full_name': 'John Doe', 'email': 'john@example.com'},
    therapist={'full_name': 'Dr. Jane Smith'},
    goals=[
        {
            'description': 'Reduce anxiety',
            'baseline': '8/10',
            'current': '5/10',
            'progress_percentage': 37.5
        }
    ],
    sessions=[...],
    date_range={
        'start_date': datetime(2025, 1, 1),
        'end_date': datetime(2025, 3, 31)
    },
    include_sections={
        'patient_info': True,
        'treatment_goals': True,
        'session_summary': True
    }
)
# Returns: b'PK\x03\x04\x14...' (DOCX binary)
```

**Internal Implementation:**
```python
# Uses python-docx elements:
- Document()  # Create new document
- add_paragraph(text)  # Add paragraphs
- add_heading(title, level)  # Add headings
- add_table(rows, cols)  # Add tables
- RGBColor(r, g, b)  # For colored text
- WD_ALIGN_PARAGRAPH.CENTER  # For alignment
```

#### 2. `generate_treatment_summary(patient, therapist, treatment_data, include_sections) -> bytes`

**Purpose:** Create treatment summary DOCX

**Status:** Stub implementation (returns None)

**Planned Data Structures:**
```python
treatment_data = {
    'treatment_type': 'cognitive_behavioral',  # CBT, DBT, psychodynamic, etc.
    'duration_months': 3,
    'primary_complaints': ['anxiety', 'depression'],
    'diagnoses': ['GAD', 'MDD'],
    'current_status': 'ongoing',
    'prognosis': 'good',
    'discharge_readiness': 'not_ready'
}
```

### FastAPI Dependency

```python
def get_docx_generator() -> DOCXGeneratorService:
    """FastAPI dependency to provide DOCX generator service"""
    return DOCXGeneratorService()
```

---

## 3. EXPORT SERVICE ARCHITECTURE

**File:** `/backend/app/services/export_service.py`

### Class: ExportService

**Purpose:** Orchestrate data gathering and format negotiation for multi-format exports

**Initialization:**
```python
class ExportService:
    def __init__(
        self,
        pdf_generator: PDFGeneratorService,
        docx_generator: DOCXGeneratorService
    ):
        self.pdf_generator = pdf_generator
        self.docx_generator = docx_generator
        self.export_dir = Path("exports/output")  # Where files are saved
```

### Core Methods

#### 1. `gather_session_notes_data(session_ids, db) -> Dict[str, Any]`

**Purpose:** Assemble context data for session notes export

**Signature:**
```python
async def gather_session_notes_data(
    self,
    session_ids: List[UUID],
    db: AsyncSession
) -> Dict[str, Any]:
```

**Database Queries:**
- Fetches TherapySession records with joinedload for relationships
- Extracts therapist and patients from sessions
- Uses SQLAlchemy ORM relationships to avoid N+1 queries

**Returns:**
```python
{
    "sessions": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "session_date": datetime(2025, 1, 15),
            "duration_minutes": 55.0,
            "transcript_text": "Full session transcript...",
            "extracted_notes": {
                "key_topics": ["anxiety", "work"],
                "session_mood": "positive",
                "mood_trajectory": "improving",
                "treatment_goals": [...]
            },
            "therapist_summary": "Session narrative...",
            "patient_summary": "Summary for patient...",
            "status": "processed"
        }
    ],
    "therapist": {
        "id": "...",
        "full_name": "Dr. Jane Smith",
        "email": "jane@clinic.com",
        "role": "therapist"
    },
    "patients": {
        "550e8400-e29b-41d4-a716-446655440001": {
            "id": "...",
            "full_name": "John Doe",
            "email": "john@example.com",
            "role": "patient"
        }
    },
    "session_count": 3
}
```

#### 2. `gather_progress_report_data(patient_id, start_date, end_date, db) -> Dict[str, Any]`

**Purpose:** Assemble comprehensive progress report context

**Signature:**
```python
async def gather_progress_report_data(
    self,
    patient_id: UUID,
    start_date: datetime,
    end_date: datetime,
    db: AsyncSession
) -> Dict[str, Any]:
```

**Database Operations:**
1. Queries User for patient details
2. Queries TherapistPatient junction for primary therapist relationship
3. Queries TherapySession records with `status == 'processed'` in date range
4. Extracts goals from `extracted_notes.treatment_goals` JSONB field
5. Calculates metrics:
   - Session count
   - Average duration
   - Topic frequency analysis using Counter()

**Returns:**
```python
{
    "patient": {
        "id": "...",
        "full_name": "John Doe",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "role": "patient"
    },
    "therapist": {
        "id": "...",
        "full_name": "Dr. Jane Smith",
        "role": "therapist"
    },
    "start_date": datetime(2025, 1, 1),
    "end_date": datetime(2025, 3, 31),
    "sessions": [...],  # Serialized session data
    "session_count": 12,
    "avg_duration_minutes": 54.3,
    "goals": [
        {
            "description": "Reduce anxiety",
            "baseline": "N/A",
            "current": "N/A",
            "progress_percentage": 0
        }
    ],
    "key_topics": ["anxiety", "work_stress", "relationships"]  # Top 10
}
```

#### 3. `generate_export(export_type, format, context, template_id=None, db=None) -> bytes`

**Purpose:** Route to appropriate generator based on format

**Signature:**
```python
async def generate_export(
    self,
    export_type: str,           # 'session_notes', 'progress_report', etc.
    format: str,                # 'pdf', 'docx', 'json', 'csv'
    context: Dict[str, Any],
    template_id: Optional[UUID] = None,
    db: AsyncSession = None
) -> bytes:
```

**Format Routing:**

```python
# PDF Export
if format == 'pdf':
    template_name = f"{export_type}.html"  # e.g., 'progress_report.html'
    return await self.pdf_generator.generate_from_template(
        template_name,
        context
    )

# DOCX Export - Type-specific handlers
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
    elif export_type == 'treatment_summary':
        return await self.docx_generator.generate_treatment_summary(...)

# JSON Export
elif format == 'json':
    return json.dumps(context, indent=2, default=str).encode('utf-8')

# CSV - Not yet implemented
elif format == 'csv':
    raise ValueError("CSV export format not yet implemented")
```

**Supported Export Types:**
- `session_notes` → PDF/DOCX/JSON
- `progress_report` → PDF/DOCX/JSON
- `treatment_summary` → DOCX (stub)
- `full_record` → DOCX (stub)

#### 4. `_serialize_user(user) -> Dict[str, Any]`

**Purpose:** Convert User ORM model to template-friendly dict

**Output:**
```python
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "full_name": "John Doe",
    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "role": "patient"
}
```

#### 5. `_serialize_session(session) -> Dict[str, Any]`

**Purpose:** Convert TherapySession ORM model to template-friendly dict

**Output:**
```python
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "session_date": datetime(2025, 1, 15),
    "duration_minutes": 55.0,
    "transcript_text": "Full transcript...",
    "extracted_notes": {
        "key_topics": [...],
        "session_mood": "positive"
    },
    "therapist_summary": "Clinical summary...",
    "patient_summary": "Patient-facing summary...",
    "status": "processed"
}
```

### FastAPI Dependency

```python
def get_export_service(
    pdf_generator: PDFGeneratorService,
    docx_generator: DOCXGeneratorService
) -> ExportService:
    """FastAPI dependency with injected generators"""
    return ExportService(pdf_generator, docx_generator)

# Usage in routers:
@router.post("/export/progress-report")
async def export_progress_report(
    data: ProgressReportExportRequest,
    export_service: ExportService = Depends(get_export_service),
    db: AsyncSession = Depends(get_db)
):
    context = await export_service.gather_progress_report_data(
        data.patient_id,
        data.start_date,
        data.end_date,
        db
    )
    file_bytes = await export_service.generate_export(
        'progress_report',
        data.format,
        context
    )
```

---

## 4. AUTO-GENERATION HOOKS & STATUS TRANSITIONS

### Hook Chain: Audio Upload → Processed Status

**Primary Hook Location:** `/backend/app/routers/sessions.py` - `process_audio_pipeline()` function

#### Step 1: Audio Upload Initiates Pipeline

```python
@router.post("/upload")
async def upload_audio_session(
    patient_id: UUID,
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: AsyncSession
):
    # Create session in database
    new_session = db_models.Session(
        patient_id=patient_id,
        therapist_id=therapist.id,
        session_date=datetime.utcnow(),
        status=SessionStatus.uploading.value  # ← Initial status
    )
    
    # Queue background processing
    background_tasks.add_task(
        process_audio_pipeline,  # ← Hook triggered here
        session_id=new_session.id,
        audio_path=str(file_path),
        db=db
    )
```

#### Step 2: Background Task Orchestrates Processing

```python
async def process_audio_pipeline(
    session_id: UUID,
    audio_path: str,
    db: AsyncSession
):
    """
    Executes complete workflow with status transitions:
    1. uploading → transcribing
    2. transcribing → transcribed
    3. transcribed → extracting_notes
    4. extracting_notes → processed ← FINAL STATUS
    5. [On error] → failed
    """
    
    try:
        # ============ Stage 1: Transcription ============
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(status=SessionStatus.transcribing.value)
        )
        await db.commit()
        
        # Call transcription service
        transcript_result = await transcribe_audio_file(audio_path)
        
        # Save transcript
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                transcript_text=transcript_result["full_text"],
                transcript_segments=transcript_result["segments"],
                duration_seconds=int(transcript_result.get("duration", 0)),
                status=SessionStatus.transcribed.value  # ← Status 2
            )
        )
        await db.commit()
        
        # ============ Stage 2: Note Extraction ============
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(status=SessionStatus.extracting_notes.value)
        )
        await db.commit()
        
        # Call note extraction service
        extraction_service = get_extraction_service()
        notes = await extraction_service.extract_notes_from_transcript(
            transcript=transcript_result["full_text"],
            segments=transcript_result.get("segments")
        )
        
        # Save extracted notes
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                extracted_notes=notes.model_dump(),  # ← Structured data saved
                therapist_summary=notes.therapist_notes,
                patient_summary=notes.patient_summary,
                risk_flags=[flag.model_dump() for flag in notes.risk_flags],
                status=SessionStatus.processed.value  # ← FINAL STATUS
            )
        )
        await db.commit()
        
        # Cleanup audio file
        if os.path.exists(audio_path):
            os.remove(audio_path)
            
    except Exception as e:
        # On any failure → update status to failed
        await db.execute(
            update(db_models.Session)
            .where(db_models.Session.id == session_id)
            .values(
                status=SessionStatus.failed.value,
                error_message=str(e)
            )
        )
        await db.commit()
```

### Hook Chain: Processed Status → Document Generation

**Location:** `/backend/app/routers/export.py` - Export endpoints + background task

#### Hook Pattern 1: Explicit Export Request

```python
@router.post("/progress-report")
async def export_progress_report(
    data: ProgressReportExportRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession
):
    # Create export job record
    job = ExportJob(
        user_id=current_user.id,
        patient_id=data.patient_id,
        export_type='progress_report',
        format=data.format,
        status='pending',  # ← Initial status
        parameters=data.model_dump()
    )
    db.add(job)
    await db.commit()
    
    # Queue background processing ← AUTO-GENERATION HOOK
    background_tasks.add_task(
        process_export_job,  # Hook function
        job.id,
        'progress_report',
        data.model_dump(),
        db
    )
    
    return ExportJobResponse(...)
```

#### Hook Implementation: process_export_job()

```python
async def process_export_job(
    job_id: UUID,
    export_type: str,
    request_data: dict,
    db: AsyncSession
):
    """
    Background task that processes export jobs.
    Auto-generates documents from processed sessions.
    """
    try:
        # Step 1: Mark as processing
        await db.execute(
            update(ExportJob)
            .where(ExportJob.id == job_id)
            .values(status='processing', started_at=datetime.utcnow())
        )
        await db.commit()
        
        # Step 2: Gather data (uses sessions with status='processed')
        export_service = get_export_service(get_pdf_generator(), get_docx_generator())
        
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
                db  # ← Filters for status='processed'
            )
        
        # Step 3: Generate export file
        file_bytes = await export_service.generate_export(
            export_type,
            request_data['format'],
            context
        )
        
        # Step 4: Save file and update job
        file_path = export_service.export_dir / f"{job_id}.{request_data['format']}"
        file_path.write_bytes(file_bytes)
        
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
        
        # Step 5: Create HIPAA audit log
        audit_entry = ExportAuditLog(
            export_job_id=job_id,
            user_id=job.user_id,
            patient_id=job.patient_id,
            action='created'
        )
        db.add(audit_entry)
        await db.commit()
        
    except Exception as e:
        # On failure → mark job as failed
        await db.execute(
            update(ExportJob)
            .where(ExportJob.id == job_id)
            .values(
                status='failed',
                error_message=str(e)
            )
        )
        await db.commit()
```

### Status Transition Diagram

```
Audio Upload Flow:
═══════════════════
    uploading
        ↓
    transcribing (AI service called)
        ↓
    transcribed (transcript saved)
        ↓
    extracting_notes (GPT-4o called)
        ↓
    PROCESSED ←─────────────────────┐
        ↓                           │
    [Session now available          │
     for exports & reports]         │
                                    │
Export Request Flow:                │
═══════════════════════             │
    pending                         │
        ↓                           │
    processing                      │
        ↓                           │
    Queries: TherapySession         │
    WHERE status='processed' ─────→ │ (Hook point!)
        ↓
    Data gathered (goals, sessions, metrics)
        ↓
    Format-specific generation:
    - PDF: Jinja2 template → WeasyPrint
    - DOCX: python-docx API calls
    - JSON: json.dumps()
        ↓
    completed (file saved)
        ↓
    HIPAA audit log created
```

---

## 5. EXPORT SERVICE MODEL & DATABASE TABLES

**File:** `/backend/app/models/export_models.py`

### ExportJob Table

```python
class ExportJob(Base):
    __tablename__ = 'export_jobs'
    
    id: UUID = Column(primary_key=True, default=gen_random_uuid())
    user_id: UUID = ForeignKey('users.id')  # Who requested export
    patient_id: UUID = ForeignKey('users.id', nullable=True)  # For patient filters
    template_id: UUID = ForeignKey('export_templates.id', nullable=True)
    
    export_type: str  # 'session_notes', 'progress_report', 'treatment_summary', 'full_record'
    format: str       # 'pdf', 'docx', 'json', 'csv'
    status: str       # 'pending', 'processing', 'completed', 'failed'
    
    parameters: JSONB # Export options, filters, date ranges
    file_path: str    # Path to generated file
    file_size_bytes: BigInteger
    error_message: str  # If status='failed'
    
    started_at: DateTime    # When processing began
    completed_at: DateTime  # When processing completed
    expires_at: DateTime    # Auto-delete after 7 days
    created_at: DateTime
    
    # Relationships
    user: User
    patient: User
    template: ExportTemplate
    audit_logs: List[ExportAuditLog]
```

### ExportAuditLog Table

```python
class ExportAuditLog(Base):
    __tablename__ = 'export_audit_log'
    
    id: UUID = primary_key
    export_job_id: UUID = ForeignKey('export_jobs.id')
    user_id: UUID = ForeignKey('users.id', nullable=True)
    patient_id: UUID = ForeignKey('users.id', nullable=True)
    
    action: str  # 'created', 'downloaded', 'deleted', 'shared'
    ip_address: str  # IPv4 (15 chars) or IPv6 (45 chars)
    user_agent: str  # Browser/client info
    action_metadata: JSONB  # Additional context
    
    created_at: DateTime
```

### ExportTemplate Table

```python
class ExportTemplate(Base):
    __tablename__ = 'export_templates'
    
    id: UUID = primary_key
    name: str  # Template name
    export_type: str  # 'session_notes', 'progress_report', etc.
    format: str  # 'pdf', 'docx', 'json', 'csv'
    
    template_content: str  # Jinja2 template HTML (for custom templates)
    include_sections: JSONB  # {transcript: true, goals: false, ...}
    is_system: Boolean  # True for built-in templates
    
    created_by: UUID = ForeignKey('users.id')
    created_at: DateTime
    updated_at: DateTime
    
    # Relationships
    creator: User
    jobs: List[ExportJob]
```

---

## 6. DATA FLOW EXAMPLE: Complete Session Processing

### Scenario: Therapist uploads session audio and exports progress report

```python
# ╔═════════════════════════════════════════════════════════════════╗
# ║ PHASE 1: AUDIO UPLOAD & AUTOMATIC PROCESSING                   ║
# ╚═════════════════════════════════════════════════════════════════╝

# 1. POST /sessions/upload
#    → Creates Session record with status="uploading"
#    → Saves audio file
#    → Queues process_audio_pipeline() background task

# 2. process_audio_pipeline() executes:
#    a. Status: uploading → transcribing
#    b. Calls transcribe_audio_file()
#       Returns: {
#           "full_text": "T: Hello... P: I've been...",
#           "segments": [{start: 0, end: 1.5, text: "..."}],
#           "duration": 3300  # 55 minutes
#       }
#    c. Status: transcribing → transcribed
#       Saves transcript_text, transcript_segments, duration_seconds
#    
#    d. Status: transcribed → extracting_notes
#    e. Calls NoteExtractionService.extract_notes_from_transcript()
#       Returns ExtractedNotes with:
#       {
#           "key_topics": ["anxiety", "work_stress"],
#           "session_mood": "positive",
#           "mood_trajectory": "improving",
#           "strategies": [
#               {
#                   "name": "Box breathing",
#                   "category": "breathing",
#                   "status": "practiced",
#                   "context": "Patient used during session"
#               }
#           ],
#           "action_items": [
#               {
#                   "task": "Practice meditation daily",
#                   "category": "homework",
#                   "details": "5 minutes daily"
#               }
#           ],
#           "risk_flags": [],
#           "therapist_notes": "Session summary for records...",
#           "patient_summary": "You discussed anxiety..."
#       }
#    f. Status: extracting_notes → PROCESSED
#       Saves extracted_notes (JSONB), therapist_summary, patient_summary
#    g. Deletes audio file from disk

# 3. Database state after Phase 1:
#    sessions table:
#    ├─ id: 550e8400-e29b-41d4-a716-446655440000
#    ├─ status: "processed" ← ✓ Ready for exports
#    ├─ transcript_text: "Full transcript..."
#    ├─ extracted_notes: {...AI-extracted data...}
#    ├─ therapist_summary: "..."
#    ├─ duration_seconds: 3300
#    └─ session_date: 2025-12-17

# ╔═════════════════════════════════════════════════════════════════╗
# ║ PHASE 2: EXPLICIT EXPORT REQUEST                               ║
# ╚═════════════════════════════════════════════════════════════════╝

# 4. POST /export/progress-report
#    Request body:
#    {
#        "patient_id": "550e8400-e29b-41d4-a716-446655440001",
#        "start_date": "2025-12-01",
#        "end_date": "2025-12-31",
#        "format": "pdf",  # or "docx"
#        "include_sections": {
#            "patient_info": true,
#            "treatment_goals": true,
#            "session_summary": true
#        }
#    }
#
#    → Creates ExportJob record with status="pending"
#    → Queues process_export_job() background task
#    → Returns immediately with job_id

# 5. process_export_job() executes:
#    a. Status: pending → processing
#    
#    b. Call gather_progress_report_data():
#       - SELECT User WHERE id=patient_id
#       - SELECT TherapistPatient WHERE patient_id AND relationship_type='primary'
#       - SELECT TherapySession WHERE:
#           patient_id = ? AND
#           session_date BETWEEN ? AND ? AND
#           status = 'processed' ← FILTERS FOR PROCESSED!
#       
#       Returns context dict:
#       {
#           "patient": {"full_name": "John Doe", ...},
#           "therapist": {"full_name": "Dr. Jane Smith", ...},
#           "sessions": [
#               {
#                   "session_date": 2025-12-17,
#                   "duration_minutes": 55.0,
#                   "transcript_text": "Full transcript...",
#                   "extracted_notes": {...}
#               },
#               {...more sessions...}
#           ],
#           "session_count": 12,
#           "avg_duration_minutes": 54.3,
#           "goals": [...extracted from sessions...],
#           "key_topics": ["anxiety", "work_stress", ...]
#       }
#    
#    c. Call generate_export('progress_report', 'pdf', context):
#       
#       If format='pdf':
#       └─ PDFGeneratorService.generate_from_template('progress_report.html', context)
#          ├─ Jinja2 renders progress_report.html with context variables
#          │  Template includes conditional sections based on include_sections
#          │  Generates HTML string
#          ├─ WeasyPrint converts HTML → PDF bytes
#          └─ Returns: b'%PDF-1.4\n...'
#       
#       If format='docx':
#       └─ DOCXGeneratorService.generate_progress_report(...)
#          ├─ Creates Document()
#          ├─ Adds heading, paragraphs, tables
#          ├─ Saves to BytesIO buffer
#          └─ Returns: b'PK\x03\x04...' (DOCX binary)
#    
#    d. Save file to exports/output/{job_id}.pdf
#    
#    e. Update ExportJob:
#       status: 'completed'
#       file_path: '/path/to/exports/output/{job_id}.pdf'
#       file_size_bytes: 245678
#       completed_at: 2025-12-17 14:35:22
#       expires_at: 2025-12-24 14:35:22
#    
#    f. Create ExportAuditLog entry:
#       action: 'created'
#       user_id: {current_user.id}
#       patient_id: {patient_id}

# 6. Client polls: GET /export/jobs/{job_id}
#    Response when completed:
#    {
#        "id": "550e8400-e29b-41d4-a716-446655440002",
#        "export_type": "progress_report",
#        "format": "pdf",
#        "status": "completed",
#        "file_size_bytes": 245678,
#        "completed_at": "2025-12-17T14:35:22Z",
#        "expires_at": "2025-12-24T14:35:22Z",
#        "download_url": "/api/v1/export/download/550e8400-e29b-41d4-a716-446655440002"
#    }

# 7. GET /export/download/{job_id}
#    → Creates ExportAuditLog: action='downloaded', ip_address, user_agent
#    → Returns FileResponse with PDF attachment
#    → Client receives: application/pdf binary data
```

---

## 7. TEMPLATE AUTO-FILL SERVICE

**File:** `/backend/app/services/template_autofill.py`

### Purpose

Auto-fill clinical note templates (SOAP, DAP, BIRP, Progress Notes) from AI-extracted session data.

### Class: TemplateAutoFillService

#### Main Method: `fill_template(notes, template_type) -> Dict`

**Signature:**
```python
async def fill_template(
    self,
    notes: ExtractedNotes,
    template_type: TemplateType  # Enum: soap, dap, birp, progress
) -> Dict[str, Any]:
```

**Returns:**
```python
{
    'sections': {
        'subjective': {
            'chief_complaint': '...',
            'mood': 'positive',
            'presenting_issues': '• Anxiety\n• Work stress'
        },
        'objective': {...},
        'assessment': {...},
        'plan': {...}
    },
    'confidence_scores': {
        'subjective': 0.85,
        'objective': 0.75,
        'assessment': 0.92,
        'plan': 0.88
    },
    'missing_fields': {
        'assessment': ['clinical_impression']  # Fields needing review
    },
    'metadata': {
        'template_type': 'soap',
        'overall_confidence': 0.85,
        'mapped_fields_count': 18
    }
}
```

### Template Formats Supported

**1. SOAP (Subjective, Objective, Assessment, Plan)**
```python
# Mapping:
subjective:
  - chief_complaint: session_mood + topic_summary
  - mood: session_mood
  - presenting_issues: key_topics
  - patient_concerns: unresolved_concerns
  - significant_statements: significant_quotes

objective:
  - presentation: emotional_themes + mood observation
  - mood_affect: session_mood
  - triggers_identified: triggers

assessment:
  - clinical_impression: therapist_notes
  - strategies_reviewed: strategies (status='reviewed')
  - risk_assessment: risk_flags

plan:
  - interventions: all strategies
  - homework: action_items
  - follow_up_topics: follow_up_topics
```

**2. DAP (Data, Assessment, Plan)**
```python
data:
  - observations: Combined subjective + objective
  - topics_discussed: key_topics
  - emotional_presentation: emotional_themes
  - triggers: triggers

assessment:
  - clinical_impression: therapist_notes
  - interventions_used: strategies
  - risk_assessment: risk_flags

plan:
  - homework: action_items
  - next_session_focus: follow_up_topics[:3]
```

**3. BIRP (Behavior, Intervention, Response, Plan)**
```python
behavior:
  - presentation: mood + key topics
  - emotional_state: emotional_themes
  - triggers_exhibited: triggers

intervention:
  - techniques: strategies
  - interventions_applied: strategies (status in ['practiced', 'introduced'])

response:
  - patient_response: Engagement summary
  - mood_trajectory: mood_trajectory

plan:
  - next_steps: action_items
  - homework: strategies (status='assigned')
```

**4. Progress Note**
```python
session_summary:
  - overview: topic_summary
  - topics_covered: key_topics

clinical_presentation:
  - mood_affect: mood description
  - emotional_themes: emotional_themes

progress:
  - changes: mood_trajectory
  - strategies_effectiveness: reviewed strategies

risk_assessment:
  - risk_flags: risk_flags

plan:
  - next_steps: action_items
```

### Confidence Scoring Algorithm

```python
def _calculate_section_confidence(field_values):
    """
    Score based on field completeness:
    - Empty: 0.0
    - Short (< 20 chars): 0.5
    - Medium (< 100 chars): 0.8
    - Comprehensive (> 100 chars): 1.0
    - Empty list: 0.3
    - Short list (< 3 items): 0.7
    - Good list (3+ items): 1.0
    """
    # Returns average of all field scores (0.0 - 1.0)
```

### Usage Example

```python
from app.services.template_autofill import TemplateAutoFillService

service = TemplateAutoFillService()

# After note extraction
extracted_notes = ExtractedNotes(
    topic_summary="Discussed anxiety management strategies",
    session_mood="positive",
    mood_trajectory="improving",
    key_topics=["anxiety", "breathing"],
    emotional_themes=["hopeful", "engaged"],
    strategies=[
        Strategy(
            name="Box breathing",
            category="breathing",
            status="practiced",
            context="Patient used during session"
        )
    ],
    action_items=[
        ActionItem(
            task="Practice breathing exercises",
            category="homework",
            details="5 minutes daily"
        )
    ],
    risk_flags=[],
    therapist_notes="Good engagement, making progress on anxiety management",
    # ... other fields
)

# Auto-fill SOAP template
result = await service.fill_template(
    notes=extracted_notes,
    template_type=TemplateType.soap
)

# Returns:
# {
#     'sections': {
#         'subjective': {
#             'chief_complaint': 'Discussed anxiety management strategies',
#             'mood': 'positive',
#             'presenting_issues': '• anxiety\n• breathing',
#             ...
#         },
#         'objective': {...},
#         'assessment': {...},
#         'plan': {...}
#     },
#     'confidence_scores': {
#         'subjective': 0.85,
#         ...
#     },
#     'missing_fields': {...}
# }

# Use in therapist workflow:
# Therapist reviews template with confidence scores
# Fills in any missing fields manually
# Generates final clinical note
```

---

## 8. INTEGRATION PATTERNS & CURRENT USAGE

### Pattern 1: Background Task Auto-Generation

**Example:** Session processing triggers automatic note extraction

```python
# Endpoint triggers background task
background_tasks.add_task(
    process_audio_pipeline,  # Function executes in background
    session_id=new_session.id,
    audio_path=str(file_path),
    db=db
)
# Returns immediately to client with uploading status
# Processing continues asynchronously
```

**Used By:**
- POST /sessions/upload → process_audio_pipeline
- POST /export/progress-report → process_export_job
- POST /export/session-notes → process_export_job

### Pattern 2: Status-Based Filtering

**Example:** Only processed sessions are included in exports

```python
# In gather_progress_report_data():
sessions_query = (
    select(TherapySession)
    .where(
        and_(
            TherapySession.patient_id == patient_id,
            TherapySession.session_date >= start_date,
            TherapySession.session_date <= end_date,
            TherapySession.status == 'processed'  # ← Hook point!
        )
    )
)
```

**Used By:**
- Export service queries
- Analytics/reporting calculations
- Patient dashboard session display

### Pattern 3: Format Negotiation

**Example:** Single endpoint handles multiple output formats

```python
# POST /export/progress-report can return:
# - PDF (via WeasyPrint)
# - DOCX (via python-docx)
# - JSON (via json.dumps)
# - CSV (not yet implemented)

# Router receives format parameter and routes accordingly:
await export_service.generate_export(
    export_type='progress_report',
    format=request.format,  # pdf | docx | json | csv
    context=context
)
```

### Pattern 4: Dependency Injection for Services

```python
# Services are provided as dependencies:
@router.post("/export/progress-report")
async def export_progress_report(
    export_service: ExportService = Depends(get_export_service),
    pdf_gen: PDFGeneratorService = Depends(get_pdf_generator),
    docx_gen: DOCXGeneratorService = Depends(get_docx_generator),
    db: AsyncSession = Depends(get_db)
):
    # Services are automatically instantiated and injected
```

---

## 9. KEY TECHNICAL DECISIONS

### Why WeasyPrint for PDF?

✓ HTML-to-PDF conversion (vs. ReportLab binary generation)  
✓ Templating-friendly (Jinja2 HTML → WeasyPrint PDF)  
✓ CSS styling support  
✓ Print-optimized output  
✗ System dependencies (libpango, cairo) required

### Why python-docx for DOCX?

✓ Structured document creation (tables, styles, formatting)  
✓ Native .docx format support  
✓ Editable output (vs. PDF)  
✓ Therapist-friendly (therapists can modify before sharing)

### Why JSON for exports?

✓ Machine-readable format  
✓ Structured data preservation  
✓ API integration  
✓ Data analysis/BI tools  

### JSONB for extracted_notes Storage

✓ Flexible schema (AI outputs vary)  
✓ Indexable and queryable  
✓ Version-independent  
✗ Requires deserialization to Python objects

---

## 10. MISSING PIECES & FUTURE EXTENSIONS

**Status:** Phase 3 (Export System)

### Implemented ✓
- Session notes export (PDF, DOCX, JSON)
- Progress report export (PDF, DOCX, JSON)
- Export job tracking
- HIPAA audit logging
- Template auto-fill (SOAP, DAP, BIRP, Progress)

### Not Yet Implemented ✗
- Treatment summary export (Phase 4)
- Full record export (Phase 4)
- Custom user templates (Phase 4)
- CSV format export
- Scheduled/recurring exports
- Email delivery integration

### Scalability Considerations

**Current Bottlenecks:**
1. Single export_dir for all users (filesystem path limitations)
2. No file cleanup job (relies on manual 7-day expiration)
3. Background task queue not persistent (uses FastAPI BackgroundTasks)

**Future Improvements:**
1. Move exports to object storage (S3, GCS)
2. Implement APScheduler-based cleanup job
3. Replace BackgroundTasks with Celery/RQ for reliability
4. Add export templates marketplace
5. Support bulk exports (multiple patients)

---

## Summary

The TherapyBridge export system is a sophisticated multi-layer architecture:

1. **Audio Processing Layer** - Transcription + AI extraction
2. **Data Gathering Layer** - ExportService queries and serializes ORM models
3. **Template Layer** - Jinja2 for PDF, python-docx for DOCX
4. **Document Generation Layer** - Format-specific generators
5. **Auto-Generation Hooks** - Status transitions trigger downstream processes
6. **Audit & Compliance Layer** - HIPAA-compliant logging and file tracking

The key integration pattern is **status-based filtering**: only sessions with `status='processed'` are included in exports, ensuring data quality and consistency.

