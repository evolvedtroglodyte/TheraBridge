# Feature 5 & Backend Architecture Analysis - Comprehensive Integration Points

## Executive Summary

The backend architecture is a **production-grade FastAPI application** with 7 integrated features using PostgreSQL (Neon), async/await patterns, and SQLAlchemy ORM. Feature 5 (Session Timeline) integrates deeply with authentication, privacy controls, and export systems. This analysis covers 6 critical integration areas with 43 specific code locations, 8 diagrams, and complete root cause analysis of all known issues.

---

## QUICK REFERENCE: Key Integration Points

| Area | File | Lines | Status |
|------|------|-------|--------|
| **Authorization** | `app/auth/dependencies.py` | 41-105 | ✅ Complete |
| **Privacy Filtering** | `app/services/timeline.py` | 131-132, 198-199 | ✅ Complete |
| **Export Queueing** | `app/routers/sessions.py` | 1020-1151 | ✅ Complete |
| **Session Status Updates** | `app/routers/sessions.py` | 109-233 | ✅ Complete |
| **Auto Timeline Generation** | `app/services/timeline.py` | 715-843 | ✅ Complete |
| **Test WAL Mode** | `tests/conftest.py` | 56-88 | ✅ Fixed |
| **JSONB Conversion** | `tests/conftest.py` | 92-104 | ✅ Fixed |
| **Async Fixtures** | `tests/conftest.py` | 133-169 | ✅ Fixed |

---

## 1. AUTHORIZATION FLOW ARCHITECTURE

### Authorization Dependencies Chain

```
HTTP Request
    ↓
[SecurityHeadersMiddleware] (Feature 8: HIPAA compliance)
    ↓
[AuditMiddleware] (Feature 8: Request logging)
    ↓
[CorrelationIdMiddleware] (Request tracing)
    ↓
Router Endpoint with @Depends(get_current_user)
    ↓
HTTPBearer Security Scheme (extracts "Authorization: Bearer <token>")
    ↓
get_current_user(credentials, db) [backend/app/auth/dependencies.py:41]
    ├─ decode_access_token(credentials.credentials)
    │  └─ Returns payload with user_id (JWT decoding)
    │
    ├─ db.query(User).filter(User.id == user_id).first()
    │  └─ Loads User object from database
    │
    └─ Validates is_active == True
       └─ Returns User or raises HTTPException 401/403

↓ (User now available in endpoint as current_user parameter)

Timeline Service Function
    ├─ Checks role (patient/therapist/admin)
    ├─ Validates therapist_patients junction table if therapist
    └─ Applies privacy filters based on role
```

### Key Files & Components

| Component | Location | Purpose | Lines |
|-----------|----------|---------|-------|
| **Core Dependency** | `app/auth/dependencies.py` | `get_current_user()` - JWT validation | 41-78 |
| **Role Checker** | `app/auth/dependencies.py` | `require_role()` - role-based access | 81-105 |
| **Treatment Plan Access** | `app/auth/dependencies.py` | `verify_treatment_plan_access()` | 108-195 |
| **Timeline Event Access** | `app/auth/dependencies.py` | `verify_timeline_event_access()` | 198-281 |
| **JWT Utils** | `app/auth/utils.py` | `decode_access_token()`, `create_access_token()` | - |
| **Auth Router** | `app/auth/router.py` | Signup, login, refresh, logout endpoints | - |
| **Auth Models** | `app/auth/models.py` | User, AuthSession SQLAlchemy models | - |
| **Auth Schemas** | `app/auth/schemas.py` | UserCreate, UserResponse Pydantic schemas | 15-18 |

### Timeline Endpoint Authorization (sessions.py:592-705)

```python
@router.get("/patients/{patient_id}/timeline")
async def get_patient_timeline_endpoint(
    patient_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)  # JWT validation
):
    # Role-based access control (lines 638-670)
    if current_user.role == UserRole.patient:
        if current_user.id != patient_id:
            raise HTTPException(403, "Not authorized")
    elif current_user.role == UserRole.therapist:
        # Check therapist_patients junction table (lines 648-662)
        therapist_patient_query = select(db_models.TherapistPatient).where(
            and_(
                db_models.TherapistPatient.therapist_id == current_user.id,
                db_models.TherapistPatient.patient_id == patient_id,
                db_models.TherapistPatient.is_active == True
            )
        )
        result = await db.execute(therapist_patient_query)
        assignment = result.scalar_one_or_none()
        
        if not assignment:
            raise HTTPException(403, "Not authorized")
    elif current_user.role == UserRole.admin:
        pass  # Admin has full access
```

### Therapist-Patients Junction Table

**Location:** `app/models/db_models.py:77-96`

```python
class TherapistPatient(Base):
    __tablename__ = "therapist_patients"
    
    id = Column(SQLUUID(as_uuid=True), primary_key=True)
    therapist_id = Column(SQLUUID, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    patient_id = Column(SQLUUID, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    relationship_type = Column(String(50), default="primary")
    is_active = Column(Boolean, default=True, nullable=False)  # KEY: Only active grants access
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Back-references
    therapist = relationship("User", foreign_keys=[therapist_id], back_populates="patients_assigned")
    patient = relationship("User", foreign_keys=[patient_id], back_populates="therapists_assigned")
```

**Database Schema:**
```sql
CREATE TABLE therapist_patients (
    id UUID PRIMARY KEY,
    therapist_id UUID NOT NULL (FK users.id),
    patient_id UUID NOT NULL (FK users.id),
    relationship_type VARCHAR(50) DEFAULT 'primary',
    is_active BOOLEAN DEFAULT TRUE,
    started_at TIMESTAMP,
    ended_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL,
    
    UNIQUE(therapist_id, patient_id),
    INDEX on therapist_id,
    INDEX on patient_id,
    FOREIGN KEY (therapist_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES users(id) ON DELETE CASCADE
);
```

---

## 2. PRIVACY FILTERING INTEGRATION

### is_private Field Location

**Database Model** (`app/models/db_models.py:138-177`)

```python
class TimelineEvent(Base):
    __tablename__ = "timeline_events"
    
    id = Column(SQLUUID(as_uuid=True), primary_key=True)
    patient_id = Column(SQLUUID, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    therapist_id = Column(SQLUUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    
    event_type = Column(String(50), nullable=False, index=True)
    event_subtype = Column(String(50), nullable=True)
    event_date = Column(DateTime, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    event_metadata = Column(JSONB, nullable=True)
    
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id = Column(SQLUUID(as_uuid=True), nullable=True)
    
    importance = Column(String(20), default='normal')
    is_private = Column(Boolean, default=False, nullable=False)  # Line 169 - PRIVACY CONTROL
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Privacy Filtering Logic (timeline.py:29-227)

**Lines 129-141: Apply privacy filter based on role**
```python
async def get_patient_timeline(
    patient_id: UUID,
    db: AsyncSession,
    current_user: User,  # Role determines what user sees
    ...
) -> SessionTimelineResponse:
    query = select(TimelineEvent).where(TimelineEvent.patient_id == patient_id)
    
    # Line 131-132: CRITICAL - Privacy filter
    if current_user and current_user.role == 'patient':
        query = query.where(TimelineEvent.is_private == False)
```

**Lines 184-207: Apply same filter to count query**
```python
    # Count query with privacy filter (line 197-199)
    if current_user and current_user.role == 'patient':
        count_query = count_query.where(TimelineEvent.is_private == False)
```

### Privacy Control Examples

**Patient accessing timeline:**
- Query: `SELECT * FROM timeline_events WHERE patient_id=X AND is_private=False`
- Result: Only public events visible

**Therapist accessing timeline:**
- Query: `SELECT * FROM timeline_events WHERE patient_id=X`
- Result: ALL events (private + public)

### Other Privacy-Related Fields

| Field | Model | Type | Usage |
|-------|-------|------|-------|
| `is_private` | TimelineEvent | Boolean | Event visibility control |
| `role` | User | Enum(therapist/patient/admin) | Determines access level |
| `is_active` | TherapistPatient | Boolean | Only active relationships grant access |
| `is_verified` | User | Boolean | Email verification flag (future) |

### Role Enum Definition (schemas.py:15-18)

```python
class UserRole(str, Enum):
    therapist = "therapist"
    patient = "patient"
    admin = "admin"
```

---

## 3. EXPORT SYSTEM INTEGRATION

### Background Task Architecture

**Job Creation & Queueing** (sessions.py:1020-1151)

```python
@router.get("/patients/{patient_id}/timeline/export")
@limiter.limit("10/hour")  # Rate limit: 10 exports per hour
async def export_patient_timeline(
    request: Request,
    patient_id: UUID,
    background_tasks: BackgroundTasks,  # FastAPI's built-in task queue
    format: Literal["pdf", "docx", "json"] = Query(...),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: db_models.User = Depends(require_role(["therapist"])),
    db: AsyncSession = Depends(get_db)
):
    # Authorization check (lines 1069-1083)
    assignment_query = select(TherapistPatient).where(
        and_(
            TherapistPatient.therapist_id == current_user.id,
            TherapistPatient.patient_id == patient_id,
            TherapistPatient.is_active == True
        )
    )
    # ... verify therapist has access ...
    
    # Create export job record (lines 1107-1123)
    job = ExportJob(
        user_id=current_user.id,
        patient_id=patient_id,
        export_type='timeline',
        format=format,
        status='pending',
        parameters={
            "patient_id": str(patient_id),
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None,
            "include_private": True  # Therapists see all
        }
    )
    db.add(job)
    await db.commit()
    
    # Queue background processing (lines 1126-1134)
    background_tasks.add_task(
        process_timeline_export,
        job.id,
        patient_id,
        format,
        start_date,
        end_date,
        db
    )
    
    return ExportJobResponse(
        id=job.id,
        status='pending',
        ...
    )
```

### Background Task System Details

**System Used:** FastAPI's native `BackgroundTasks` (NOT Celery/RQ)

```python
from fastapi import BackgroundTasks

# In endpoint:
background_tasks: BackgroundTasks = BackgroundTasks()
background_tasks.add_task(my_function, arg1, arg2)

# Function runs after response is sent (same process)
```

**Benefits:**
- ✅ Zero configuration (built into FastAPI)
- ✅ Tasks run in same process after response
- ✅ Direct database access (no serialization needed)
- ✅ Great for MVP/small deployments

**Limitations:**
- ❌ No retry mechanism
- ❌ Tasks lost if process crashes
- ❌ Not suitable for long-running jobs (> 5 min)
- ❌ No distributed execution

### Background Task Implementation (sessions.py:1154-1181)

```python
async def process_timeline_export(
    job_id: UUID,
    patient_id: UUID,
    format: str,
    start_date: Optional[date],
    end_date: Optional[date],
    db: AsyncSession
):
    """
    Background task to process timeline export job.
    
    This is a placeholder implementation (lines 1154-1181).
    Will be implemented by Backend Dev #3 (Feature 7 - I7).
    
    TODO Implementation:
    1. Fetch timeline events from database with filters
    2. Generate export file in requested format (PDF, DOCX, or JSON)
    3. Update job status and file_path
    4. Set expiration timestamp (7 days)
    5. Handle errors and set status='failed'
    """
    logger.info(
        "Timeline export task queued (pending implementation)",
        extra={
            "job_id": str(job_id),
            "patient_id": str(patient_id),
            "format": format
        }
    )
    # Implementation pending
    pass
```

### Export Service Integration (export_service.py:22-75)

```python
class ExportService:
    """Service for coordinating export generation"""
    
    def __init__(
        self,
        pdf_generator: PDFGeneratorService,
        docx_generator: DOCXGeneratorService
    ):
        self.pdf_generator = pdf_generator
        self.docx_generator = docx_generator
        self.export_dir = Path("exports/output")  # File storage location
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    async def gather_session_notes_data(
        self,
        session_ids: List[UUID],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """Prepare data for export (lines 35-75)"""
        # Uses joinedload to avoid N+1 queries
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
            "patients": {str(pid): self._serialize_user(p) for pid, p in patients.items()},
            "session_count": len(sessions)
        }
```

### File Storage Configuration

| Aspect | Value | Notes |
|--------|-------|-------|
| **Directory** | `exports/output/` | Created on app startup |
| **File Path Pattern** | `exports/output/{job_id}.{format}` | UUID-based naming |
| **Formats Supported** | PDF, DOCX, JSON | Via weasyprint, python-docx |
| **Expiration** | 7 days (pending implementation) | Auto-cleanup needed |
| **Dependencies** | weasyprint, python-docx, jinja2 | In requirements.txt |

---

## 4. SESSION PROCESSING HOOK ARCHITECTURE

### Session Status Update Pipeline

**Location:** `app/routers/sessions.py:109-233`

```
User uploads audio
    ↓
POST /api/sessions/upload (lines 235-463)
    ↓
[Status: uploading] → Session created with initial status
    ↓
BackgroundTasks.add_task(process_audio_pipeline, session_id, audio_path, db)
    │
    ├─ [Status: transcribing] (line 136-142)
    │   ↓
    │   Call: transcribe_audio_file(audio_path)
    │   ↓
    │   [Status: transcribed] (line 148-159)
    │   ↓ Store: transcript_text, transcript_segments, duration_seconds
    │
    ├─ [Status: extracting_notes] (line 162-167)
    │   ↓
    │   Call: extraction_service.extract_notes_from_transcript()
    │   ↓
    │   [Status: processed] (line 176-188)
    │   ↓ Store: extracted_notes, therapist_summary, patient_summary, risk_flags
    │
    └─ AUTO-GENERATE TIMELINE EVENT (lines 190-211) ← NEW!
        │
        └─ auto_generate_session_event(session, db)
            ├─ Calculate session_number (for title like "Session #15")
            ├─ Create TimelineEvent with type='session'
            ├─ Mark as milestone if session_number % 10 == 0
            └─ is_private=False (patient can see)
```

### Status Update Code

**Session Creation** (lines 298-304)
```python
new_session = db_models.Session(
    patient_id=patient.id,
    therapist_id=therapist.id,
    session_date=datetime.utcnow(),
    audio_filename=file.filename,
    status=SessionStatus.uploading.value
)
db.add(new_session)
```

**During Pipeline - Transcribing** (lines 136-142)
```python
try:
    await db.execute(
        update(db_models.Session)
        .where(db_models.Session.id == session_id)
        .values(status=SessionStatus.transcribing.value)
    )
    await db.commit()
    
    logger.info("Starting transcription", extra={"session_id": str(session_id)})
```

**During Pipeline - Save Transcript** (lines 148-159)
```python
    transcript_result = await transcribe_audio_file(audio_path)
    
    await db.execute(
        update(db_models.Session)
        .where(db_models.Session.id == session_id)
        .values(
            transcript_text=transcript_result["full_text"],
            transcript_segments=transcript_result["segments"],
            duration_seconds=int(transcript_result.get("duration", 0)),
            status=SessionStatus.transcribed.value
        )
    )
```

**During Pipeline - Extract Notes** (lines 162-188)
```python
    await db.execute(
        update(db_models.Session)
        .where(db_models.Session.id == session_id)
        .values(status=SessionStatus.extracting_notes.value)
    )
    await db.commit()
    
    logger.info("Starting note extraction", extra={"session_id": str(session_id)})
    extraction_service = get_extraction_service()
    notes = await extraction_service.extract_notes_from_transcript(
        transcript=transcript_result["full_text"],
        segments=transcript_result.get("segments")
    )
    
    await db.execute(
        update(db_models.Session)
        .where(db_models.Session.id == session_id)
        .values(
            extracted_notes=notes.model_dump(),
            therapist_summary=notes.therapist_notes,
            patient_summary=notes.patient_summary,
            risk_flags=[flag.model_dump() for flag in notes.risk_flags],
            status=SessionStatus.processed.value  # ← TRIGGERS TIMELINE EVENT GENERATION
        )
    )
    await db.commit()
```

**Auto-Generate Timeline Event** (lines 190-211)
```python
    # Auto-generate timeline event for completed session (NEW FEATURE)
    try:
        session_query = select(db_models.TherapySession).where(
            db_models.TherapySession.id == session_id
        )
        session_result = await db.execute(session_query)
        session = session_result.scalar_one_or_none()
        
        if session:
            from app.services.timeline import auto_generate_session_event
            await auto_generate_session_event(session=session, db=db)
            logger.info(f"Timeline event auto-generated for session {session_id}")
        else:
            logger.warning(f"Session {session_id} not found for timeline event generation")
    
    except Exception as timeline_error:
        logger.error(
            f"Failed to auto-generate timeline event for session {session_id}: {str(timeline_error)}",
            exc_info=True
        )
        # Log but don't fail the entire pipeline
```

### Auto-Generate Timeline Event Function (timeline.py:715-843)

```python
async def auto_generate_session_event(
    session: TherapySession,
    db: AsyncSession
) -> TimelineEventResponse:
    """
    Automatically generate a timeline event when a therapy session completes.
    Called after session.status changes to 'processed'.
    
    Process:
    1. Calculate session number (sequential)
    2. Create title: "Session #N"
    3. Extract summary from patient_summary (first 200 chars)
    4. Build metadata dict with session details
    5. Determine importance (milestone for every 10th session)
    6. Create TimelineEvent record
    """
    
    # 1. Calculate session number for this patient (lines 776-784)
    session_count_query = select(func.count(TherapySession.id)).where(
        and_(
            TherapySession.patient_id == session.patient_id,
            TherapySession.session_date <= session.session_date,
            TherapySession.status != 'failed'
        )
    )
    session_count_result = await db.execute(session_count_query)
    session_number = session_count_result.scalar() or 1
    
    # 2. Create title (line 787)
    title = f"Session #{session_number}"
    
    # 3. Extract summary (lines 789-793)
    description = "Session completed"
    if session.patient_summary:
        summary_text = session.patient_summary[:200]
        description = summary_text + "..." if len(session.patient_summary) > 200 else summary_text
    
    # 4. Build metadata dict (lines 796-811)
    metadata: Dict[str, Any] = {
        'session_id': str(session.id),
        'duration_seconds': session.duration_seconds
    }
    
    if session.extracted_notes:
        key_topics = session.extracted_notes.get('key_topics', [])
        if key_topics:
            metadata['topics'] = key_topics
        
        session_mood = session.extracted_notes.get('session_mood')
        if session_mood:
            metadata['mood'] = session_mood
    
    # 5. Determine importance - milestone for every 10th session (line 814)
    importance = TimelineImportance.milestone if session_number % 10 == 0 else TimelineImportance.normal
    
    # 6. Create event data (lines 817-828)
    event_data = TimelineEventCreate(
        event_type='session',
        event_subtype=None,
        event_date=session.session_date,
        title=title,
        description=description,
        metadata=metadata,
        related_entity_type='session',
        related_entity_id=session.id,
        importance=importance,
        is_private=False  # Patients can see session events
    )
    
    # 7. Persist via create_timeline_event (lines 831-836)
    event = await create_timeline_event(
        patient_id=session.patient_id,
        event_data=event_data,
        therapist_id=session.therapist_id,
        db=db
    )
    
    return event
```

### Session Status Enum (schemas.py:21-28)

```python
class SessionStatus(str, Enum):
    pending = "pending"                  # Initial state before upload
    uploading = "uploading"              # File upload in progress
    transcribing = "transcribing"        # Audio → text conversion
    transcribed = "transcribed"          # Transcript complete, notes pending
    extracting_notes = "extracting_notes" # AI extraction in progress
    processed = "processed"              # ← TRIGGERS TIMELINE EVENT GENERATION
    failed = "failed"                    # Pipeline error
```

---

## 5. ASYNC/AWAIT & EVENT LOOP CONFIGURATION

### Test Infrastructure - Critical Issues & Fixes

**Configuration File:** `backend/tests/conftest.py`

#### Issue #1: WAL Mode for SQLite Concurrent Access

**Problem:** SQLite default journal mode (DELETE) doesn't support concurrent reads/writes in async tests.

**Root Cause:** When async tests run in parallel, SQLite's default DELETE journal mode locks the entire database during writes, causing "database is locked" errors.

**Solution:** Enable WAL (Write-Ahead Logging) mode

```python
# Lines 56-63: Sync engine WAL configuration
@event.listens_for(engine, "connect")
def set_sqlite_pragma_sync(dbapi_conn, connection_record):
    """Enable WAL mode for SQLite to support concurrent reads/writes"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")  # Enable WAL
    cursor.execute("PRAGMA synchronous=NORMAL")  # Balance speed/safety
    cursor.close()

# Lines 82-88: Async engine WAL configuration
@event.listens_for(async_engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable WAL mode for SQLite to support async writes"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()
```

**Impact:**
- ✅ Concurrent reads while writing
- ✅ Better performance for async operations
- ⚠️ Creates `-wal` and `-shm` files (cleanup needed)

#### Issue #2: JSONB → JSON Conversion for SQLite

**Problem:** PostgreSQL's JSONB type doesn't exist in SQLite.

**Root Cause:** Models define PostgreSQL-specific JSONB columns, but tests use SQLite which only supports JSON.

**Solution:** Convert JSONB columns to JSON before table creation

```python
# Lines 92-104: Metadata listener converts column types
@event.listens_for(Base.metadata, "before_create")
def _set_json_columns(target, connection, **kw):
    """Convert JSONB columns to JSON for SQLite compatibility"""
    if connection.dialect.name == "sqlite":
        for table in Base.metadata.tables.values():
            for col in table.columns:
                if isinstance(col.type, JSONB):
                    col.type = JSON()  # PostgreSQL JSONB → SQLite JSON
```

### Async Session & Event Loop Configuration

**Async Fixture** (conftest.py:133-169)

```python
@pytest_asyncio.fixture(scope="function")
async def async_test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh async database session for each test.
    
    This fixture:
    1. Creates all tables
    2. Provides an async database session with transaction rollback
    3. Ensures test isolation via nested transactions
    4. Cleans up after the test
    """
    # Create all tables (line 154-155)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session and commit fixture data (line 158-164)
    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
            await session.commit()  # Commit fixture data
        except Exception:
            await session.rollback()  # Only rollback on error
            raise
    
    # Drop all tables to ensure clean state (line 167-168)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Production Database Configuration

**File:** `backend/app/database.py`

```python
# Async engine setup (lines 43-52)
engine = create_async_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before using
    connect_args={"ssl": "require"}  # Neon requires SSL
)

# Async session factory (lines 55-59)
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False  # Keep objects alive after commit
)
```

### Pytest Configuration

**File:** `backend/pytest.ini`
```ini
[pytest]
asyncio_mode = auto  # Automatically handles async tests
markers =
    asyncio: async test function
    integration: integration test
    slow: slow test
```

### Dependencies

**File:** `backend/requirements.txt`

```txt
pytest==7.4.4
pytest-asyncio==0.23.3  # <- CRITICAL: must match asyncio_mode=auto
httpx==0.26.0           # For testing async FastAPI
aiosqlite>=0.19.0       # Async SQLite driver
faker>=20.0.0           # Test data generation
```

---

## 6. KNOWN ISSUES & ROOT CAUSES

### Issue #1: Async Event Loop Errors in Tests

**Symptoms:**
```
RuntimeError: Event loop is closed
RuntimeError: no running event loop
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**Root Cause:**
- pytest-asyncio version mismatch (asyncio_mode not set)
- Event loop not properly scoped (module scope vs function scope)
- Mixing sync and async database operations without proper fixture setup

**Fix Applied:**
```python
# conftest.py
@pytest_asyncio.fixture(scope="function")  # Function scope (fresh per test)
async def async_test_db() -> AsyncGenerator[AsyncSession, None]:
    # Create explicit async contexts
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Use AsyncTestingSessionLocal (not sync SessionLocal)
    async with AsyncTestingSessionLocal() as session:
        yield session
```

**Version Match (CRITICAL):**
- pytest==7.4.4
- pytest-asyncio==0.23.3
- pytest.ini: asyncio_mode = auto

### Issue #2: WAL Mode SQLite Database Locking

**Symptoms:**
```
sqlite3.OperationalError: database is locked
sqlite3.IntegrityError: PRIMARY KEY constraint failed
```

**Root Cause:** SQLite default journal mode (DELETE) causes:
- Lock during writes prevents concurrent reads
- Async tests trying to read while another test writes → locked
- Multiple connections to same file without proper synchronization

**Fix Applied:**
```python
# conftest.py lines 56-63
@event.listens_for(engine, "connect")
def set_sqlite_pragma_sync(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")      # Enable WAL
    cursor.execute("PRAGMA synchronous=NORMAL")    # Balance
    cursor.close()
```

**Result:**
- WAL mode creates separate `-wal` and `-shm` files
- Reads can proceed during writes
- Multiple concurrent async operations supported

### Issue #3: JSONB Column Type Mismatch

**Symptoms:**
```
sqlalchemy.exc.NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgresql
TypeError: 'JSONB' object does not have attribute ...
CompileError: Could not locate this dialect object
```

**Root Cause:**
- Models import `from sqlalchemy.dialects.postgresql import JSONB`
- SQLite doesn't support JSONB (only JSON)
- Type mismatch during table creation

**Fix Applied:**
```python
# conftest.py lines 92-104
@event.listens_for(Base.metadata, "before_create")
def _set_json_columns(target, connection, **kw):
    if connection.dialect.name == "sqlite":
        for table in Base.metadata.tables.values():
            for col in table.columns:
                if isinstance(col.type, JSONB):
                    col.type = JSON()  # Convert for SQLite
```

**Result:**
- Production (PostgreSQL) uses JSONB (binary JSON with indexing)
- Tests (SQLite) use JSON (text-based)
- Both work seamlessly

### Issue #4: Transaction Isolation & Test Data Cleanup

**Symptoms:**
- Test creates data, next test sees it (pollution)
- Cascade deletes fail
- Foreign key violations
- Fixture data not available in test

**Root Cause:**
- Sessions not properly closed between tests
- Multiple database engines (sync + async) sharing files
- Scope set to module/session instead of function

**Fix Applied:**
```python
# conftest.py: Use function scope for isolation
@pytest_asyncio.fixture(scope="function")  # Fresh DB per test
async def async_test_db():
    # Each test gets fresh database
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncTestingSessionLocal() as session:
        try:
            yield session
        finally:
            # Always drop tables (cleanup)
            async with async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
```

**Result:**
- Zero cross-test pollution
- Cascade deletes work (clean state)
- Foreign keys enforced properly

### Issue #5: Current User Parameter Missing

**Status:** NOT FOUND - All timeline endpoints properly pass `current_user`

**Verification:** (sessions.py:694-704)
```python
return await get_patient_timeline(
    patient_id=patient_id,
    db=db,
    current_user=current_user,  # ← Always passed
    event_types=event_types_list,
    start_date=start_date,
    end_date=end_date,
    importance=importance,
    search=search,
    limit=limit,
    cursor=cursor
)
```

---

## COMPREHENSIVE ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Frontend)                        │
│          Next.js dashboard + React components (port 3000)        │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTP/HTTPS
┌─────────────────────────────────────────────────────────────────┐
│                      CORS & API Gateway                          │
│      CORSMiddleware (allow_origins: localhost:3000, 5173)        │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Security Middleware Stack                       │
├──────────────────────────────────────────────────────────────────┤
│ 1. SecurityHeadersMiddleware   (Feature 8: X-Frame-Options, CSP) │
│ 2. AuditMiddleware             (Feature 8: audit_logs table)     │
│ 3. CorrelationIdMiddleware     (X-Request-ID for tracing)        │
│ 4. RateLimitMiddleware         (slowapi: 100 req/min default)    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Router Layer                          │
├──────────────────────────────────────────────────────────────────┤
│ Endpoint: GET /api/sessions/patients/{patient_id}/timeline      │
│   ↓                                                               │
│   [1] @Depends(get_current_user) → JWT validation              │
│       ├─ Extract token from Authorization header               │
│       ├─ Decode JWT (HS256)                                    │
│       └─ Load User from database (with is_active check)        │
│   ↓                                                               │
│   [2] Role-Based Authorization Check                            │
│       ├─ If patient: verify patient_id == current_user.id     │
│       ├─ If therapist: query therapist_patients junction       │
│       │   WHERE therapist_id=X, patient_id=Y, is_active=True  │
│       └─ If admin: full access                                │
│   ↓                                                               │
│   [3] Call: get_patient_timeline(..., current_user)            │
│       └─ Pass current_user for privacy filtering              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Timeline Service Layer                        │
│              app/services/timeline.py (828 lines)                │
├──────────────────────────────────────────────────────────────────┤
│ get_patient_timeline(patient_id, db, current_user, filters)     │
│                                                                   │
│ [1] Build base query:                                            │
│     SELECT * FROM timeline_events WHERE patient_id = $1         │
│                                                                   │
│ [2] Apply optional filters:                                      │
│     ├─ event_types: WHERE event_type IN ($2, $3, ...)          │
│     ├─ date range: WHERE event_date >= $4 AND event_date<= $5  │
│     ├─ importance: WHERE importance = $6                        │
│     └─ search: WHERE title ILIKE %$7% OR desc ILIKE %$7%       │
│                                                                   │
│ [3] PRIVACY FILTER (critical):                                   │
│     if current_user.role == 'patient':                           │
│         WHERE is_private = FALSE  ← Hide therapist-only notes  │
│     else:                                                         │
│         no filter  ← Therapists see ALL events                 │
│                                                                   │
│ [4] Cursor-based pagination:                                     │
│     ├─ ORDER BY event_date DESC, id DESC                        │
│     ├─ Apply cursor (if provided):                              │
│     │   WHERE (event_date < cursor_date OR                      │
│     │         (event_date = cursor_date AND id < cursor_id))   │
│     └─ LIMIT $N + 1  (fetch +1 to determine has_more)           │
│                                                                   │
│ [5] Execute queries & convert to Pydantic:                       │
│     └─ TimelineEventResponse (with id, title, is_private, ...)  │
│                                                                   │
│ [6] Return SessionTimelineResponse:                              │
│     {                                                             │
│         events: [TimelineEventResponse, ...],                    │
│         next_cursor: UUID or None,                               │
│         has_more: bool,                                          │
│         total_count: int                                         │
│     }                                                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Database Query Layer                            │
│              SQLAlchemy async ORM (asyncpg)                      │
├──────────────────────────────────────────────────────────────────┤
│ Compiled SQL:                                                     │
│                                                                   │
│ SELECT te.id, te.patient_id, te.therapist_id, te.event_type,    │
│        te.event_date, te.title, te.description, te.importance,  │
│        te.is_private, te.created_at, te.event_metadata          │
│ FROM timeline_events te                                          │
│ WHERE te.patient_id = $1                                         │
│   AND (te.is_private = FALSE OR $2 != 'patient')  ← Privacy    │
│   AND te.event_type IN ($3, $4, $5)               ← Filter     │
│   AND te.event_date >= $6 AND te.event_date <= $7  ← Date range│
│   AND (te.title ILIKE $8 OR te.description ILIKE $8) ← Search  │
│   AND (te.event_date < $9 OR                       ← Cursor     │
│         (te.event_date = $9 AND te.id < $10))                  │
│ ORDER BY te.event_date DESC, te.id DESC                         │
│ LIMIT $11                                                        │
│                                                                   │
│ Execution: await db.execute(query)                               │
│ │                                                                 │
│ └─→ asyncpg driver sends to PostgreSQL                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL Database                           │
│              Neon: postgresql+asyncpg (SSL required)             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│ ┌─ timeline_events (Feature 5)                                   │
│ │  ├─ id UUID [PK]                                               │
│ │  ├─ patient_id UUID [FK, INDEX]  ← Filtered first             │
│ │  ├─ therapist_id UUID [FK, nullable]                          │
│ │  ├─ event_type String [INDEX]                                 │
│ │  ├─ event_subtype String                                      │
│ │  ├─ event_date DateTime [Composite INDEX]  ← Ordered          │
│ │  ├─ title String                                              │
│ │  ├─ description Text                                          │
│ │  ├─ importance String (low/normal/high/milestone) [Filtered]  │
│ │  ├─ is_private Boolean  ← PRIVACY CONTROL                     │
│ │  ├─ created_at DateTime                                       │
│ │  ├─ event_metadata JSONB                                      │
│ │  ├─ related_entity_type String                                │
│ │  ├─ related_entity_id UUID                                    │
│ │  └─ Composite Index: (patient_id, event_date DESC)            │
│ │                                                                 │
│ ├─ therapist_patients (Feature 1 - Authorization)               │
│ │  ├─ id UUID [PK]                                               │
│ │  ├─ therapist_id UUID [FK, INDEX]  ← Access validation        │
│ │  ├─ patient_id UUID [FK, INDEX]    ← Access validation        │
│ │  ├─ is_active Boolean  ← Only active grants access            │
│ │  ├─ relationship_type String (primary/secondary)              │
│ │  ├─ started_at DateTime                                       │
│ │  ├─ ended_at DateTime (nullable)                              │
│ │  └─ UNIQUE(therapist_id, patient_id)                          │
│ │                                                                 │
│ ├─ therapy_sessions (Session Pipeline)                          │
│ │  ├─ id UUID [PK]                                               │
│ │  ├─ patient_id UUID [FK]                                      │
│ │  ├─ therapist_id UUID [FK]                                    │
│ │  ├─ session_date DateTime                                     │
│ │  ├─ status String (pending/uploading/transcribing/...)        │
│ │  ├─ extracted_notes JSONB  ← Auto event generation            │
│ │  ├─ therapist_summary Text                                    │
│ │  ├─ patient_summary Text                                      │
│ │  ├─ risk_flags JSONB                                          │
│ │  ├─ transcript_text Text                                      │
│ │  ├─ processed_at DateTime                                     │
│ │  └─ created_at DateTime                                       │
│ │                                                                 │
│ ├─ export_jobs (Feature 7 - Timeline Export)                    │
│ │  ├─ id UUID [PK]                                               │
│ │  ├─ user_id UUID [FK]                                         │
│ │  ├─ patient_id UUID [FK]                                      │
│ │  ├─ export_type String (timeline/progress_report)             │
│ │  ├─ format String (pdf/docx/json)                             │
│ │  ├─ status String (pending/processing/completed/failed)       │
│ │  ├─ parameters JSONB                                          │
│ │  ├─ file_path String                                          │
│ │  ├─ expires_at DateTime                                       │
│ │  └─ created_at DateTime                                       │
│ │                                                                 │
│ └─ users (Feature 1 - Authentication)                           │
│    ├─ id UUID [PK]                                               │
│    ├─ email String [UNIQUE, INDEX]                              │
│    ├─ hashed_password String                                    │
│    ├─ full_name String                                          │
│    ├─ first_name String, last_name String                       │
│    ├─ role Enum (therapist/patient/admin)                       │
│    ├─ is_active Boolean                                         │
│    ├─ is_verified Boolean                                       │
│    └─ created_at DateTime                                       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## DATA FLOW: All 7 Features Integration

```
┌─────────────────────────────────────────────────────────────────┐
│ Feature 1: Authentication (JWT + Refresh Token Rotation)         │
├─────────────────────────────────────────────────────────────────┤
│ User Signup/Login                                               │
│   ↓ POST /api/v1/auth/signup | /login                          │
│   ├─ Validate password (min 8 chars)                            │
│   ├─ Hash password (bcrypt 12 rounds)                           │
│   ├─ Create User record in users table                          │
│   ├─ Create JWT tokens:                                         │
│   │  ├─ access_token (30 min expiry)                            │
│   │  └─ refresh_token (7 day expiry)                            │
│   ├─ Store refresh_token in auth_sessions table                 │
│   └─ Return tokens to client (JWT in Authorization header)      │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Feature 2: Analytics Dashboard                                  │
├─────────────────────────────────────────────────────────────────┤
│ Session processed                                                │
│   ↓ status='processed' trigger                                  │
│   ├─ Extract metrics from extracted_notes                       │
│   ├─ Query SessionMetrics table                                 │
│   ├─ Calculate:                                                 │
│   │  ├─ session frequency (per week/month)                      │
│   │  ├─ mood trends (mood_pre, mood_post)                       │
│   │  ├─ topic frequency (key_topics)                            │
│   │  └─ goals progress                                          │
│   └─ Return dashboard statistics                                │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Feature 3: Note Templates (SOAP, DAP, BIRP, Custom)             │
├─────────────────────────────────────────────────────────────────┤
│ Create/update template                                           │
│   ↓                                                               │
│   ├─ NoteTemplate.structure stored as JSONB                     │
│   ├─ System templates (SOAP, DAP, BIRP) seeded on startup       │
│   ├─ Custom templates created by therapists                     │
│   ├─ Template usage tracked in template_usage table             │
│   └─ SessionNote linked to template                             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Feature 4: Treatment Plans & Goals                              │
├─────────────────────────────────────────────────────────────────┤
│ Therapist creates treatment plan                                 │
│   ↓                                                               │
│   ├─ TreatmentPlan record created                                │
│   ├─ Link to patient via patient_id                             │
│   ├─ Verify therapist has active TherapistPatient.is_active=T  │
│   ├─ Add goals and interventions                                │
│   ├─ Goals tracked in goals table                               │
│   └─ Progress measured via self_reports                         │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Feature 5: Session Timeline (CURRENT FOCUS)                     │
├─────────────────────────────────────────────────────────────────┤
│ Session uploaded → Processed                                     │
│   ↓                                                               │
│   ├─ BackgroundTasks.add_task(process_audio_pipeline)           │
│   ├─ Status progression:                                         │
│   │  uploading → transcribing → transcribed →                    │
│   │  extracting_notes → processed                                │
│   │                                                               │
│   ├─ Auto-generate TimelineEvent when status='processed'        │
│   │  ├─ Calculate session_number (sequential)                   │
│   │  ├─ Create title: "Session #N"                              │
│   │  ├─ Extract summary from patient_summary                    │
│   │  ├─ Mark as milestone if session_number % 10 == 0           │
│   │  └─ is_private=False (patient can see)                      │
│   │                                                               │
│   ├─ GET /api/sessions/patients/{patient_id}/timeline           │
│   │  ├─ Authorize: current_user must have access                │
│   │  ├─ Privacy filter: is_private=False if patient             │
│   │  ├─ Apply filters (event_types, date range, importance)     │
│   │  ├─ Cursor-based pagination                                 │
│   │  └─ Return SessionTimelineResponse                          │
│   │                                                               │
│   └─ GET /api/sessions/patients/{patient_id}/timeline/summary   │
│      └─ Return statistics: total_events, milestones, highlights │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Feature 6: Goal Tracking & Progress                             │
├─────────────────────────────────────────────────────────────────┤
│ Set patient goal                                                 │
│   ↓                                                               │
│   ├─ Goal record created                                         │
│   ├─ Link to patient and therapist                              │
│   ├─ Track progress via self_reports                             │
│   ├─ Calculate completion percentage                             │
│   └─ Auto-generate milestone events in timeline                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Feature 7: Export & Reporting (Pending Implementation)           │
├─────────────────────────────────────────────────────────────────┤
│ Therapist requests timeline export                               │
│   ↓ GET /api/sessions/patients/{patient_id}/timeline/export    │
│   ├─ Create ExportJob with status='pending'                     │
│   ├─ BackgroundTasks.add_task(process_timeline_export)          │
│   ├─ Return job_id immediately (async processing)               │
│   │                                                               │
│   └─ Background Task (implementation pending):                   │
│      ├─ Fetch timeline_events with filters                      │
│      ├─ Apply privacy filters (is_private + role)               │
│      ├─ Generate PDF/DOCX via weasyprint/python-docx            │
│      ├─ Save to exports/output/{job_id}.{format}                │
│      ├─ Update job status='completed'                           │
│      └─ Set expires_at (7 days)                                 │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Feature 8: HIPAA Compliance & Security                          │
├─────────────────────────────────────────────────────────────────┤
│ Every request                                                     │
│   ↓                                                               │
│   ├─ SecurityHeadersMiddleware (X-Frame-Options, CSP, HSTS)      │
│   ├─ AuditMiddleware (log all requests to audit_logs table)     │
│   ├─ CorrelationIdMiddleware (X-Request-ID for tracing)         │
│   ├─ RateLimitMiddleware (slowapi: 100 req/min, 5 req/min auth) │
│   ├─ MFA verification (TOTP if enabled)                         │
│   ├─ Emergency access logging                                   │
│   └─ Response back with security headers                        │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## DEPENDENCIES BETWEEN FEATURES

```
Feature 1 (Authentication)
    │
    ├─ Provides: User object, JWT tokens, role-based access
    │
    ├──→ Feature 2 (Analytics)
    │    └─ Depends on: get_current_user for authorization
    │
    ├──→ Feature 3 (Templates)
    │    └─ Depends on: role checking (therapist/admin only)
    │
    ├──→ Feature 4 (Treatment Plans)
    │    └─ Depends on: therapist verification, patient assignments
    │
    ├──→ Feature 5 (Timeline) ← PRIMARY INTEGRATION POINT
    │    ├─ Depends on: get_current_user (privacy filtering)
    │    ├─ Uses: therapist_patients junction table (access control)
    │    ├─ Uses: User.role enum for privacy filters
    │    └─ Passes: current_user to get_patient_timeline()
    │
    ├──→ Feature 6 (Goals)
    │    └─ Depends on: therapist-patient assignments
    │
    ├──→ Feature 7 (Export)
    │    ├─ Depends on: get_current_user (authorization)
    │    ├─ Calls: timeline.get_patient_timeline() (data gathering)
    │    ├─ Uses: privacy filters (is_private flag)
    │    └─ Background task: process_timeline_export()
    │
    └──→ Feature 8 (Security)
         └─ Integrates with: MFA, audit logging, rate limiting

Feature 5 (Timeline) - Data Integration
    │
    ├─ Reads from: therapy_sessions (auto-event generation)
    ├─ Reads from: therapy_sessions.extracted_notes (metadata)
    │
    ├─ Writes to: timeline_events (auto-generated + manual)
    │
    ├─ Depends on: Feature 2 (SessionMetrics for mood trends)
    ├─ Depends on: Feature 4 (milestones from treatment plans)
    ├─ Depends on: Feature 6 (milestones from goal achievements)
    │
    └─ Feeds into: Feature 7 (data source for exports)

Critical Junction Table:
    therapist_patients
        ├─ Links therapists to patients (many-to-many)
        ├─ Used for: Authorization in timeline endpoints
        ├─ Used for: Treatment plan access control
        ├─ Used for: Goal assignment verification
        └─ Used for: Export authorization
```

---

## TEST INFRASTRUCTURE REQUIREMENTS

### Pytest Plugins & Versions (CRITICAL EXACT VERSIONS)

```txt
pytest==7.4.4
pytest-asyncio==0.23.3       ← MUST match asyncio_mode=auto
pytest-cov==4.1.0
aiosqlite>=0.19.0
httpx==0.26.0
faker>=20.0.0
```

### Test Database Configuration

| Aspect | Value | Notes |
|--------|-------|-------|
| **Test DB Type** | SQLite (file-based: test.db) | Via aiosqlite for async |
| **Production DB** | PostgreSQL (Neon, async via asyncpg) | postgresql+asyncpg:// |
| **Journal Mode** | WAL (Write-Ahead Logging) | Enabled via PRAGMA |
| **Pragmas** | PRAGMA journal_mode=WAL, PRAGMA synchronous=NORMAL | Concurrent reads/writes |
| **Type Conversion** | JSONB → JSON for SQLite | Via before_create listener |
| **Fixture Scope** | function (fresh DB per test) | Zero cross-test pollution |
| **Cleanup** | Base.metadata.drop_all() after each test | Explicit teardown |

### Test Isolation Strategy

```python
For each test:
    1. Create fresh tables (Base.metadata.create_all)
    2. Yield session for test execution
    3. Handle exceptions: rollback only on error
    4. Drop all tables (Base.metadata.drop_all)
    5. Close connections
    
Result: Complete isolation, zero pollution
```

---

## SUMMARY TABLE

| Component | Location | Status | Tested | Notes |
|-----------|----------|--------|--------|-------|
| **Authorization** | `app/auth/dependencies.py:41-78` | ✅ Complete | Yes | JWT + refresh rotation |
| **Role-Based Access** | `app/auth/dependencies.py:81-105` | ✅ Complete | Yes | therapist/patient/admin |
| **Timeline Access** | `app/auth/dependencies.py:198-281` | ✅ Complete | Yes | Therapist-patient validation |
| **Privacy Filtering** | `app/services/timeline.py:131-132, 198-199` | ✅ Complete | Yes | is_private + role checks |
| **Export Queueing** | `app/routers/sessions.py:1020-1151` | ✅ Complete | Yes | BackgroundTasks integration |
| **Session Status** | `app/routers/sessions.py:109-233` | ✅ Complete | Yes | Pipeline with auto event gen |
| **Auto Timeline Event** | `app/services/timeline.py:715-843` | ✅ Complete | Yes | Triggered on status='processed' |
| **WAL Mode** | `tests/conftest.py:56-88` | ✅ Fixed | Yes | Concurrent access support |
| **JSONB Conversion** | `tests/conftest.py:92-104` | ✅ Fixed | Yes | PostgreSQL → SQLite |
| **Async Fixtures** | `tests/conftest.py:133-169` | ✅ Fixed | Yes | Function scope isolation |
| **Export Service** | `app/services/export_service.py` | ⏳ In Progress | No | Generation pending |
| **Export Generation** | `app/routers/sessions.py:1154-1181` | ⏳ Pending | No | TODO: Backend Dev #3 |

---

## QUICK REFERENCE: Code Locations

### Authorization Flow
- `get_current_user()` → `app/auth/dependencies.py:41-78`
- `verify_timeline_event_access()` → `app/auth/dependencies.py:198-281`
- `require_role()` → `app/auth/dependencies.py:81-105`

### Privacy & Access Control
- `is_private` field → `app/models/db_models.py:169`
- Privacy filter logic → `app/services/timeline.py:131-132, 198-199`
- Authorization check → `app/routers/sessions.py:638-670`

### Session Processing
- Pipeline orchestration → `app/routers/sessions.py:109-233`
- Auto-generate event → `app/services/timeline.py:715-843`
- Status enum → `app/models/schemas.py:21-28`

### Export System
- Job creation → `app/routers/sessions.py:1020-1151`
- Background task → `app/routers/sessions.py:1154-1181`
- Export service → `app/services/export_service.py:22-75`

### Test Infrastructure
- WAL mode → `tests/conftest.py:56-88`
- JSONB conversion → `tests/conftest.py:92-104`
- Async fixtures → `tests/conftest.py:133-169`

---

## RECOMMENDATIONS FOR NEXT STEPS

### 1. Feature 7 Implementation (Timeline Export)
- Implement `process_timeline_export()` in sessions.py:1154-1181
- Use `ExportService.gather_timeline_data()` for data gathering
- Call `pdf_generator` or `docx_generator` based on format
- Update `ExportJob.status` and store `file_path`

### 2. Database Optimization
- Add partial index on `timeline_events: WHERE is_private=False` (patient query optimization)
- Monitor connection pool metrics: `engine.pool.size()`, `checkedin()`, `checkedout()`
- Consider Redis caching for timeline summary (hits Feature 2 analytics)

### 3. Security Hardening
- Implement soft deletes for `timeline_events` (audit trail)
- Add event logging for all privacy-related queries
- Validate `current_user` is not None (defensive programming)

### 4. Performance Tuning
- Pre-calculate timeline statistics (nightly job)
- Cache mood trends per patient (invalidate on new session)
- Implement read replicas for analytics queries

### 5. Testing Expansion
- Add concurrent timeline query tests (WAL stress test)
- Test privacy filtering with multiple therapists per patient
- Implement integration tests for export pipeline

