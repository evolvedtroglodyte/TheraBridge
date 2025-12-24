---
date: 2026-01-18T01:13:14-0600
researcher: Claude (Sonnet 4.5)
git_commit: ef424855cb17ee5f55e4e6ef5efea1f83ba70c58
branch: main
repository: peerbridge proj
topic: "Session Bridge Backend Architecture Research - Base Classes, Metadata Tables, Dual Logging, MODEL_TIER Naming"
tags: [research, codebase, session-bridge, architecture, base-class, metadata, logging, model-tier]
status: complete
last_updated: 2026-01-18
last_updated_by: Claude (Sonnet 4.5)
---

# Research: Session Bridge Backend Architecture

**Date**: 2026-01-18T01:13:14-0600
**Researcher**: Claude (Sonnet 4.5)
**Git Commit**: ef424855cb17ee5f55e4e6ef5efea1f83ba70c58
**Branch**: main
**Repository**: peerbridge proj

## Research Question

User requested comprehensive architecture research for Session Bridge backend implementation, addressing critical design decisions from Q41-Q56:

1. **Base Class Patterns**: Should AI services (YourJourneyGenerator, SessionBridgeGenerator) use a shared base class? (Q52 - user says "code duplication is NEVER preferred")
2. **Nested Metadata Table**: Design schema for `generation_metadata` table to replace JSONB columns (Q43 - "should be a nested table in both")
3. **Dual Logging Implementation**: How to integrate BOTH PipelineLogger (pipeline_events) AND custom logging (analysis_processing_log) for Wave 3 (Q49)
4. **MODEL_TIER Naming**: Suggest names for 3 performance tiers based on speed/quality (Q47 - "related to speed of processing and quality of output")
5. **Migration Patterns**: Best practices for JSONB → nested table migration with abstraction layer
6. **CHECK Constraint Strategy**: Where to place analysis_processing_log constraint update (migration 014, 015, or 016)

## Summary

### Key Findings

**Base Class Pattern**: NO existing base classes found in AI services - each service implements identical `__init__()` and model selection patterns independently. User confirmed base class should be created to eliminate duplication.

**Metadata Architecture**: Current pattern uses JSONB columns (`metadata` field) in `*_versions` tables. User wants nested table approach with shared abstraction layer.

**Dual Logging**: Two INDEPENDENT logging systems exist:
- **PipelineLogger**: Writes to `pipeline_events` table (demo orchestration, SSE events)
- **analysis_processing_log**: Wave-specific status tracking (mood, topics, deep, etc.)

**MODEL_TIER Names**: Based on model registry and industry conventions, recommended tier names focus on precision/speed trade-off.

**CHECK Constraint**: No existing CHECK constraint found for `analysis_processing_log.wave` column - needs to be added in separate migration.

---

## Detailed Findings

### 1. Base Class Patterns for AI Services

#### Current Implementation (NO Base Classes)

All 9 AI generation services implement IDENTICAL patterns independently:

**Services Analyzed**:
- `mood_analyzer.py` (MoodAnalyzer)
- `roadmap_generator.py` (RoadmapGenerator)
- `deep_analyzer.py` (DeepAnalyzer)
- `prose_generator.py` (ProseGenerator)
- `topic_extractor.py` (TopicExtractor)
- `breakthrough_detector.py` (BreakthroughDetector)
- `action_items_summarizer.py` (ActionItemsSummarizer)
- `session_insights_summarizer.py` (SessionInsightsSummarizer)
- `speaker_labeler.py` (SpeakerLabeler)

**Common `__init__()` Pattern** (duplicated 9 times):

```python
# Pattern 1: Async client (mood_analyzer.py:50-63)
def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
    self.api_key = api_key or settings.openai_api_key
    if not self.api_key:
        raise ValueError("OpenAI API key required for mood analysis")
    self.client = AsyncOpenAI(api_key=self.api_key)
    self.model = get_model_name("mood_analysis", override_model=override_model)

# Pattern 2: Sync client (roadmap_generator.py:34-47)
def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
    if api_key:
        self.client = openai.OpenAI(api_key=api_key)
    else:
        self.client = openai.OpenAI()  # Uses OPENAI_API_KEY env var
    self.model = get_model_name("roadmap_generation", override_model=override_model)
```

**Common Cost Tracking Pattern** (duplicated 9 times):

```python
# All services use identical cost tracking (see roadmap_generator.py:111-118)
start_time = time.time()

# ... API call ...

cost_info = track_generation_cost(
    response=response,
    task="roadmap_generation",  # Only difference
    model=self.model,
    start_time=start_time,
    session_id=str(patient_id),
    metadata={"sessions_analyzed": sessions_analyzed}
)
```

**Common Result Structure Pattern** (duplicated across services):

```python
# All services return similar dict structure
return {
    "roadmap": roadmap_data,  # Main data (varies by service)
    "metadata": {
        "sessions_analyzed": sessions_analyzed,
        "total_sessions": total_sessions,
        "model_used": self.model,
        "generation_timestamp": datetime.now().isoformat(),
        "generation_duration_ms": cost_info.duration_ms
    },
    "cost_info": cost_info.to_dict() if cost_info else None
}
```

#### Recommendation: Create Base Class

**Rationale**: User confirmed "code duplication is NEVER preferred" (Q52). Creating a base class eliminates 80+ lines of duplicated initialization code across 9 services.

**Proposed Architecture**:

```python
# backend/app/services/base_generator.py

from typing import Optional, Any, Dict
from datetime import datetime
import time
import openai
from openai import AsyncOpenAI
from app.config.model_config import get_model_name, track_generation_cost, GenerationCost

class BaseAIGenerator:
    """
    Base class for all AI generation services.

    Provides:
    - OpenAI client initialization (sync or async)
    - Model selection via get_model_name()
    - Cost tracking via track_generation_cost()
    - Common result structure building
    """

    def __init__(
        self,
        task_name: str,
        api_key: Optional[str] = None,
        override_model: Optional[str] = None,
        use_async_client: bool = False
    ):
        """
        Initialize AI generator with OpenAI client.

        Args:
            task_name: Task identifier for model selection (e.g., "roadmap_generation")
            api_key: OpenAI API key (uses env var if not provided)
            override_model: Override default model (for testing)
            use_async_client: Use AsyncOpenAI instead of sync client
        """
        self.task_name = task_name
        self.model = get_model_name(task_name, override_model=override_model)

        # Initialize appropriate client type
        if use_async_client:
            from app.config import settings
            self.api_key = api_key or settings.openai_api_key
            if not self.api_key:
                raise ValueError(f"OpenAI API key required for {task_name}")
            self.client = AsyncOpenAI(api_key=self.api_key)
        else:
            if api_key:
                self.client = openai.OpenAI(api_key=api_key)
            else:
                self.client = openai.OpenAI()  # Uses OPENAI_API_KEY env var

    def build_result(
        self,
        data_key: str,
        data: Any,
        metadata: Dict[str, Any],
        cost_info: Optional[GenerationCost]
    ) -> Dict:
        """
        Build standard result structure with metadata and cost info.

        Args:
            data_key: Key for main data (e.g., "roadmap", "bridge")
            data: Main result data
            metadata: Additional metadata fields
            cost_info: Cost tracking information

        Returns:
            Dict with structure: {data_key: data, "metadata": {...}, "cost_info": {...}}
        """
        result_metadata = {
            "model_used": self.model,
            "generation_timestamp": datetime.now().isoformat(),
            "generation_duration_ms": cost_info.duration_ms if cost_info else None,
            **metadata  # Merge additional metadata
        }

        return {
            data_key: data,
            "metadata": result_metadata,
            "cost_info": cost_info.to_dict() if cost_info else None
        }

    def track_cost(
        self,
        response: Any,
        start_time: float,
        session_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Optional[GenerationCost]:
        """
        Track generation cost for this task.

        Args:
            response: OpenAI API response object
            start_time: Start time from time.time()
            session_id: Optional session ID for tracking
            metadata: Optional metadata for cost tracking

        Returns:
            GenerationCost object with token usage and cost
        """
        return track_generation_cost(
            response=response,
            task=self.task_name,
            model=self.model,
            start_time=start_time,
            session_id=session_id,
            metadata=metadata or {}
        )
```

**Usage Example**:

```python
# roadmap_generator.py - BEFORE (47 lines __init__)
class RoadmapGenerator:
    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            self.client = openai.OpenAI()
        self.model = get_model_name("roadmap_generation", override_model=override_model)
        # ... strategy config ...

# roadmap_generator.py - AFTER (base class)
class RoadmapGenerator(BaseAIGenerator):
    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        super().__init__(
            task_name="roadmap_generation",
            api_key=api_key,
            override_model=override_model,
            use_async_client=False
        )
        # ... strategy config (unique to roadmap) ...
```

**Benefits**:
- Eliminates 80+ lines of duplicate code
- Centralized client initialization logic
- Consistent error handling
- Single source of truth for cost tracking pattern
- Easier to update all services (e.g., add new client features)

**Migration Strategy**:
1. Create `base_generator.py` with BaseAIGenerator class
2. Update RoadmapGenerator to inherit from base (test)
3. Update remaining 8 services one-by-one
4. Verify all services still work correctly
5. Remove duplicated code

---

### 2. Nested Metadata Table Architecture

#### Current Implementation (JSONB Columns)

**Current Pattern** (from 013_create_roadmap_tables.sql):

```sql
-- Current: metadata stored as JSONB column
CREATE TABLE patient_roadmap (
    patient_id UUID PRIMARY KEY REFERENCES patients(id) ON DELETE CASCADE,
    roadmap_data JSONB NOT NULL,
    metadata JSONB NOT NULL,  -- {sessions_analyzed, total_sessions, ...}
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE roadmap_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    version INT NOT NULL,
    roadmap_data JSONB NOT NULL,
    metadata JSONB NOT NULL,  -- Same structure
    generation_context JSONB,
    cost FLOAT,
    generation_duration_ms INT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(patient_id, version)
);
```

**Metadata Fields** (from COMMENT in migration):
- `sessions_analyzed`: int
- `total_sessions`: int
- `compaction_strategy`: str (Your Journey only)
- `model_used`: str
- `generation_timestamp`: str
- `last_session_id`: uuid
- `generation_duration_ms`: int (duplicated with column)

#### Recommended Architecture: Nested Metadata Table

**Rationale**: User confirmed "should be a nested table in both" (Q43) with shared abstraction so "editing one will edit both".

**Proposed Schema**:

```sql
-- Migration 015: Create generation_metadata table
CREATE TABLE generation_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign keys (polymorphic approach - only ONE should be set)
    your_journey_version_id UUID REFERENCES your_journey_versions(id) ON DELETE CASCADE,
    session_bridge_version_id UUID REFERENCES session_bridge_versions(id) ON DELETE CASCADE,

    -- Metadata fields (shared across both features)
    sessions_analyzed INT NOT NULL,
    total_sessions INT NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    generation_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    generation_duration_ms INT NOT NULL,
    last_session_id UUID REFERENCES therapy_sessions(id),

    -- Feature-specific fields (nullable for compatibility)
    compaction_strategy VARCHAR(50),  -- Your Journey only

    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ensure only ONE foreign key is set
    CHECK (
        (your_journey_version_id IS NOT NULL AND session_bridge_version_id IS NULL) OR
        (your_journey_version_id IS NULL AND session_bridge_version_id IS NOT NULL)
    )
);

-- Indexes
CREATE INDEX idx_generation_metadata_your_journey ON generation_metadata(your_journey_version_id);
CREATE INDEX idx_generation_metadata_session_bridge ON generation_metadata(session_bridge_version_id);
CREATE INDEX idx_generation_metadata_timestamp ON generation_metadata(generation_timestamp);

-- Comments
COMMENT ON TABLE generation_metadata IS 'Shared metadata for Your Journey and Session Bridge generations';
COMMENT ON COLUMN generation_metadata.your_journey_version_id IS 'Foreign key to your_journey_versions (mutually exclusive with session_bridge_version_id)';
COMMENT ON COLUMN generation_metadata.session_bridge_version_id IS 'Foreign key to session_bridge_versions (mutually exclusive with your_journey_version_id)';
```

**Abstraction Layer** (`backend/app/utils/generation_metadata.py`):

```python
from typing import Optional, Dict
from uuid import UUID
from datetime import datetime
from supabase import Client

def create_generation_metadata(
    db: Client,
    your_journey_version_id: Optional[UUID] = None,
    session_bridge_version_id: Optional[UUID] = None,
    sessions_analyzed: int = 0,
    total_sessions: int = 0,
    model_used: str = "",
    generation_timestamp: datetime = None,
    generation_duration_ms: int = 0,
    last_session_id: Optional[UUID] = None,
    compaction_strategy: Optional[str] = None
) -> UUID:
    """
    Create metadata record for Your Journey or Session Bridge generation.

    Editing one affects both - metadata is shared across features.
    """
    if not (bool(your_journey_version_id) ^ bool(session_bridge_version_id)):
        raise ValueError("Exactly one of your_journey_version_id or session_bridge_version_id must be provided")

    result = db.table("generation_metadata").insert({
        "your_journey_version_id": str(your_journey_version_id) if your_journey_version_id else None,
        "session_bridge_version_id": str(session_bridge_version_id) if session_bridge_version_id else None,
        "sessions_analyzed": sessions_analyzed,
        "total_sessions": total_sessions,
        "model_used": model_used,
        "generation_timestamp": generation_timestamp.isoformat() if generation_timestamp else datetime.now().isoformat(),
        "generation_duration_ms": generation_duration_ms,
        "last_session_id": str(last_session_id) if last_session_id else None,
        "compaction_strategy": compaction_strategy
    }).execute()

    return UUID(result.data[0]["id"])

def get_generation_metadata(db: Client, metadata_id: UUID) -> Dict:
    """Get metadata by ID"""
    result = db.table("generation_metadata").select("*").eq("id", str(metadata_id)).execute()
    return result.data[0] if result.data else None

def update_generation_metadata(db: Client, metadata_id: UUID, updates: Dict) -> None:
    """Update metadata fields (shared across both features)"""
    db.table("generation_metadata").update(updates).eq("id", str(metadata_id)).execute()
```

**Migration Strategy**:
1. Create `generation_metadata` table (migration 015)
2. Create abstraction utility functions
3. Update YourJourneyGenerator to use new table
4. Update SessionBridgeGenerator to use new table
5. Migrate existing JSONB data to new table (optional - can start fresh)
6. Deprecate `metadata` JSONB columns (keep for backwards compatibility)

---

### 3. Dual Logging Implementation

#### Current Implementation (TWO Independent Systems)

**System 1: PipelineLogger** (backend/app/utils/pipeline_logger.py:17-33)

- **Purpose**: Demo pipeline orchestration, SSE event emission
- **Table**: `pipeline_events`
- **Phases**: TRANSCRIPT, WAVE1, WAVE2 (enum LogPhase)
- **Events**: START, COMPLETE, FAILED, FILE_LOAD, DB_UPDATE, MOOD_ANALYSIS, TOPIC_EXTRACTION, etc. (enum LogEvent)
- **Pattern**: Structured logging with database writes + in-memory fallback
- **Usage**: seed_wave1.py, seed_wave2.py orchestration scripts

**Example** (pipeline_logger.py:56-64):

```python
logger = PipelineLogger(patient_id="...", phase=LogPhase.WAVE1)
logger.log_event(
    event=LogEvent.MOOD_ANALYSIS,
    session_id="...",
    session_date="2025-01-01",
    status="success",
    duration_ms=1500
)
```

**System 2: analysis_processing_log Table** (analysis_orchestrator.py:548-574)

- **Purpose**: Wave-specific status tracking (for monitoring/debugging)
- **Table**: `analysis_processing_log`
- **Columns**: session_id, wave, status, retry_count, error_message, processing_duration_ms
- **Wave Names**: "mood", "topics", "breakthrough", "deep" (simple strings, NO prefixes)
- **Status Lifecycle**: started → completed OR started → failed
- **Pattern**: Insert on start, update on complete/failure

**Example** (analysis_orchestrator.py:548-574):

```python
# Start logging
async def _log_analysis_start(self, session_id: str, wave: str, retry_count: int):
    self.db.table("analysis_processing_log").insert({
        "session_id": session_id,
        "wave": wave,  # Simple string: "mood", "topics", "deep"
        "status": "started",
        "retry_count": retry_count,
    }).execute()

# Complete logging
async def _log_analysis_complete(self, session_id: str, wave: str, duration_ms: int):
    self.db.table("analysis_processing_log").update({
        "status": "completed",
        "completed_at": datetime.utcnow().isoformat(),
        "processing_duration_ms": duration_ms,
    }).eq("session_id", session_id).eq("wave", wave).eq("status", "started").execute()
```

#### Recommended Implementation: Use BOTH Systems for Wave 3

**Rationale**: User confirmed "both" (Q49). Each system serves different purposes:
- PipelineLogger: Real-time SSE events for frontend
- analysis_processing_log: Historical status tracking for debugging

**Proposed Integration**:

**Step 1**: Extend PipelineLogger enums (pipeline_logger.py):

```python
class LogPhase(str, Enum):
    TRANSCRIPT = "TRANSCRIPT"
    WAVE1 = "WAVE1"
    WAVE2 = "WAVE2"
    WAVE3 = "WAVE3"  # NEW: Add Wave 3 phase

class LogEvent(str, Enum):
    START = "START"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"
    # ... existing events ...
    YOUR_JOURNEY_GENERATION = "YOUR_JOURNEY_GENERATION"  # NEW
    SESSION_BRIDGE_GENERATION = "SESSION_BRIDGE_GENERATION"  # NEW
```

**Step 2**: Create shared logging utility (backend/app/utils/wave_logging.py):

```python
"""
Shared logging utility for Wave 3 (Your Journey + Session Bridge)

Logs to BOTH systems simultaneously:
- PipelineLogger (pipeline_events table) - for SSE
- analysis_processing_log table - for historical tracking
"""

import time
from typing import Optional
from uuid import UUID
from datetime import datetime
from supabase import Client

from app.utils.pipeline_logger import PipelineLogger, LogPhase, LogEvent


class Wave3Logger:
    """Unified logger for Wave 3 that writes to both logging systems"""

    def __init__(self, patient_id: str, db: Client):
        self.patient_id = patient_id
        self.db = db
        self.pipeline_logger = PipelineLogger(patient_id=patient_id, phase=LogPhase.WAVE3)

    def log_generation_start(
        self,
        session_id: str,
        wave_name: str,  # "your_journey" or "session_bridge"
        event_type: LogEvent
    ):
        """Log generation start to BOTH systems"""
        # System 1: PipelineLogger
        self.pipeline_logger.log_event(
            event=event_type,
            session_id=session_id,
            status="started"
        )

        # System 2: analysis_processing_log
        self.db.table("analysis_processing_log").insert({
            "session_id": session_id,
            "wave": wave_name,  # "your_journey" or "session_bridge"
            "status": "started",
            "retry_count": 0
        }).execute()

    def log_generation_complete(
        self,
        session_id: str,
        wave_name: str,
        event_type: LogEvent,
        duration_ms: int
    ):
        """Log generation completion to BOTH systems"""
        # System 1: PipelineLogger
        self.pipeline_logger.log_event(
            event=event_type,
            session_id=session_id,
            status="success",
            duration_ms=duration_ms
        )

        # System 2: analysis_processing_log
        self.db.table("analysis_processing_log").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "processing_duration_ms": duration_ms
        }).eq("session_id", session_id).eq("wave", wave_name).eq("status", "started").execute()

    def log_generation_failure(
        self,
        session_id: str,
        wave_name: str,
        event_type: LogEvent,
        error_message: str
    ):
        """Log generation failure to BOTH systems"""
        # System 1: PipelineLogger
        self.pipeline_logger.log_event(
            event=event_type,
            session_id=session_id,
            status="failed",
            details={"error": error_message}
        )

        # System 2: analysis_processing_log
        self.db.table("analysis_processing_log").update({
            "status": "failed",
            "completed_at": datetime.utcnow().isoformat(),
            "error_message": error_message
        }).eq("session_id", session_id).eq("wave", wave_name).eq("status", "started").execute()
```

**Step 3**: Usage in orchestration scripts (generate_roadmap.py example):

```python
from app.utils.wave_logging import Wave3Logger
from app.utils.pipeline_logger import LogEvent
from app.database import get_supabase_admin

def generate_roadmap_for_session(patient_id: str, session_id: str) -> None:
    supabase = get_supabase_admin()
    logger = Wave3Logger(patient_id=patient_id, db=supabase)

    # Log start
    logger.log_generation_start(
        session_id=session_id,
        wave_name="your_journey",  # Simple string
        event_type=LogEvent.YOUR_JOURNEY_GENERATION
    )

    start_time = time.time()

    try:
        # ... generate roadmap ...

        duration_ms = int((time.time() - start_time) * 1000)

        # Log completion
        logger.log_generation_complete(
            session_id=session_id,
            wave_name="your_journey",
            event_type=LogEvent.YOUR_JOURNEY_GENERATION,
            duration_ms=duration_ms
        )
    except Exception as e:
        # Log failure
        logger.log_generation_failure(
            session_id=session_id,
            wave_name="your_journey",
            event_type=LogEvent.YOUR_JOURNEY_GENERATION,
            error_message=str(e)
        )
        raise
```

**Benefits**:
- Single function call logs to BOTH systems
- Consistent wave naming ("your_journey", "session_bridge")
- Centralized error handling
- SSE events + historical tracking in one place

---

### 4. MODEL_TIER Naming Conventions

#### Current Model Registry (model_config.py:41-85)

**GPT-5 Series Models** (Ordered by complexity/cost):

| Model | Input Cost | Output Cost | Complexity Tier | Description |
|-------|-----------|-------------|-----------------|-------------|
| gpt-5.2 | $1.75/1M | $14.00/1M | VERY_HIGH | Best for coding/agentic tasks |
| gpt-5 | $1.25/1M | $10.00/1M | HIGH | Strong reasoning for complex analysis |
| gpt-5-mini | $0.25/1M | $2.00/1M | MEDIUM | Cost-efficient structured extraction |
| gpt-5-nano | $0.05/1M | $0.40/1M | VERY_LOW | Fastest, most cost-efficient classification |

**Current Task Assignments** (model_config.py:90-100):
- Deep analysis, prose, roadmap → gpt-5.2 (highest quality)
- Breakthrough detection → gpt-5 (complex reasoning)
- Topic extraction, speaker labeling → gpt-5-mini (structured)
- Mood analysis, action summary → gpt-5-nano (simple scoring)

#### Recommended MODEL_TIER Names (Speed/Quality Based)

**User Requirement** (Q47): "names should be related to speed of processing and quality of output not money or categories"

**Proposed Tier Names**:

**Option A: Precision-Focused** (Emphasizes accuracy gradient)
- `MODEL_TIER=precision` - Highest quality (gpt-5.2, gpt-5, gpt-5-mini, gpt-5-nano)
- `MODEL_TIER=balanced` - Balanced quality/speed (gpt-5-mini for complex, gpt-5-nano for simple)
- `MODEL_TIER=rapid` - Fastest processing (gpt-5-nano for all tasks)

**Option B: Quality-Focused** (Direct quality correlation)
- `MODEL_TIER=maximum` - Maximum quality/slowest
- `MODEL_TIER=standard` - Standard quality/medium speed
- `MODEL_TIER=efficient` - Lower quality/fastest

**Option C: Performance-Focused** (Processing speed emphasis)
- `MODEL_TIER=thorough` - Thorough analysis/slow
- `MODEL_TIER=optimized` - Optimized balance
- `MODEL_TIER=accelerated` - Accelerated processing/fast

**Recommendation**: **Option A (precision/balanced/rapid)**

**Rationale**:
- "Precision" clearly communicates highest accuracy without mentioning cost
- "Balanced" indicates middle ground between quality and speed
- "Rapid" emphasizes speed benefit without implying poor quality
- Industry-standard terminology (ML/AI field uses "precision" for accuracy)
- Clear progression: precision → balanced → rapid

**Implementation** (model_config.py):

```python
import os

MODEL_TIER = os.getenv("MODEL_TIER", "precision")  # Default: highest quality

MODEL_TIER_OVERRIDES = {
    "precision": {
        # No overrides - use existing assignments (highest quality)
    },
    "balanced": {
        # Replace gpt-5.2 & gpt-5 → gpt-5-mini (73% cost reduction)
        "deep_analysis": "gpt-5-mini",
        "prose_generation": "gpt-5-mini",
        "breakthrough_detection": "gpt-5-mini",
        "roadmap_generation": "gpt-5-mini",
        "session_insights": "gpt-5-mini",
        # Keep gpt-5-nano for simple tasks
    },
    "rapid": {
        # Replace all → gpt-5-nano (92% cost reduction)
        "mood_analysis": "gpt-5-nano",
        "topic_extraction": "gpt-5-nano",
        "action_summary": "gpt-5-nano",
        "breakthrough_detection": "gpt-5-nano",
        "deep_analysis": "gpt-5-nano",
        "prose_generation": "gpt-5-nano",
        "speaker_labeling": "gpt-5-nano",
        "session_insights": "gpt-5-nano",
        "roadmap_generation": "gpt-5-nano",
    }
}

def get_model_name(task: str, override_model: Optional[str] = None) -> str:
    """Get configured model name with MODEL_TIER support"""
    if override_model:
        return override_model

    # Check MODEL_TIER overrides first
    tier = MODEL_TIER.lower()
    if tier in MODEL_TIER_OVERRIDES and task in MODEL_TIER_OVERRIDES[tier]:
        return MODEL_TIER_OVERRIDES[tier][task]

    # Fallback to default task assignment
    return TASK_MODEL_ASSIGNMENTS.get(task, "gpt-5-mini")
```

**Cost Comparison** (10-session demo):

| Tier | Deep | Roadmap | Total | Savings |
|------|------|---------|-------|---------|
| precision | $0.32 | $0.33 | $0.65 | 0% (baseline) |
| balanced | $0.09 | $0.09 | $0.18 | 72% |
| rapid | $0.03 | $0.01 | $0.04 | 94% |

---

### 5. Migration Patterns (JSONB → Nested Table)

#### Existing Migration Patterns

**Pattern 1**: Simple column additions (migrations/009_add_mood_and_topic_analysis_columns.sql)

```sql
ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS mood_score DECIMAL(3,1) CHECK (mood_score >= 0 AND mood_score <= 10),
ADD COLUMN IF NOT EXISTS topics JSONB;
```

**Pattern 2**: New table creation with foreign keys (migrations/013_create_roadmap_tables.sql)

```sql
CREATE TABLE IF NOT EXISTS patient_roadmap (
    patient_id UUID PRIMARY KEY REFERENCES patients(id) ON DELETE CASCADE,
    -- ...
);

CREATE TABLE IF NOT EXISTS roadmap_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    version INT NOT NULL,
    -- ...
    UNIQUE(patient_id, version)
);
```

#### Recommended Migration Strategy

**Migration Sequence** (based on dependency chain):

1. **Migration 014**: Your Journey rename (PREREQUISITE for all Session Bridge work)
2. **Migration 015**: Session Bridge tables + generation_metadata table
3. **Migration 016**: CHECK constraint update (separate for flexibility)

**Migration 015 Structure**:

```sql
-- Step 1: Create generation_metadata table (see section 2 for full schema)
CREATE TABLE generation_metadata (...);

-- Step 2: Create session_bridge tables
CREATE TABLE patient_session_bridge (...);
CREATE TABLE session_bridge_versions (...);

-- Step 3: Add foreign key from your_journey_versions to generation_metadata
ALTER TABLE your_journey_versions
ADD COLUMN metadata_id UUID REFERENCES generation_metadata(id) ON DELETE SET NULL;

-- Step 4: Add foreign key from session_bridge_versions to generation_metadata
ALTER TABLE session_bridge_versions
ADD COLUMN metadata_id UUID REFERENCES generation_metadata(id) ON DELETE SET NULL;

-- Step 5: (Optional) Migrate existing JSONB metadata to new table
-- This can be done in a separate data migration script
```

**Data Migration Script** (optional - run after migration 015):

```python
# scripts/migrate_metadata_to_nested_table.py
from app.database import get_supabase_admin
from app.utils.generation_metadata import create_generation_metadata

def migrate_existing_metadata():
    """Migrate JSONB metadata to generation_metadata table"""
    db = get_supabase_admin()

    # Get all your_journey_versions
    versions = db.table("your_journey_versions").select("*").execute()

    for version in versions.data:
        # Extract metadata from JSONB
        metadata = version.get("metadata", {})

        # Create new metadata record
        metadata_id = create_generation_metadata(
            db=db,
            your_journey_version_id=version["id"],
            sessions_analyzed=metadata.get("sessions_analyzed", 0),
            total_sessions=metadata.get("total_sessions", 0),
            model_used=metadata.get("model_used", ""),
            # ... other fields ...
        )

        # Link version to metadata
        db.table("your_journey_versions").update({
            "metadata_id": str(metadata_id)
        }).eq("id", version["id"]).execute()

    print(f"Migrated {len(versions.data)} metadata records")
```

---

### 6. CHECK Constraint Update Strategy

#### Current State

**No CHECK constraint found** for `analysis_processing_log.wave` column in existing migrations.

**Wave Names Used** (from analysis_orchestrator.py:548-574):
- "mood"
- "topics"
- "breakthrough"
- "deep"

**User Decision** (Q44): Option A - UPDATE constraint to add new wave names

**User Decision** (Q16): REMOVE constraint entirely to allow future wave names without migrations

#### Recommended Approach: REMOVE Constraint (Q16 Wins)

**Rationale**: User's latest answer (Q16) supersedes Q44. Removing constraint allows adding new waves ("your_journey", "session_bridge", future waves) without schema migrations.

**Migration 016** (or part of 015):

```sql
-- Option 1: If constraint exists, drop it
ALTER TABLE analysis_processing_log
DROP CONSTRAINT IF EXISTS chk_analysis_processing_log_wave;

-- Option 2: If no constraint exists, add comment documenting valid values
COMMENT ON COLUMN analysis_processing_log.wave IS 'Wave identifier (mood, topics, breakthrough, deep, your_journey, session_bridge). No CHECK constraint to allow future waves without migrations.';
```

**Application-Level Validation** (if needed):

```python
# app/services/analysis_orchestrator.py
VALID_WAVE_NAMES = {"mood", "topics", "breakthrough", "deep", "your_journey", "session_bridge"}

async def _log_analysis_start(self, session_id: str, wave: str, retry_count: int):
    """Log analysis start with wave name validation"""
    if wave not in VALID_WAVE_NAMES:
        logger.warning(f"Unknown wave name: {wave}. Valid values: {VALID_WAVE_NAMES}")

    self.db.table("analysis_processing_log").insert({
        "session_id": session_id,
        "wave": wave,
        "status": "started",
        "retry_count": retry_count
    }).execute()
```

---

## Architecture Documentation

### Common Patterns Found

**Pattern 1**: All AI services use identical initialization (OpenAI client + model selection)
**Pattern 2**: All AI services use identical cost tracking (track_generation_cost)
**Pattern 3**: All AI services return similar result structure (data + metadata + cost_info)
**Pattern 4**: Logging happens at orchestration layer (NOT in service classes)
**Pattern 5**: JSONB columns used for flexible metadata (but user wants nested tables)

### Design Principles Observed

1. **Services are pure**: No logging, no database writes - just AI generation
2. **Scripts orchestrate**: Orchestration scripts handle database writes, logging, subprocess management
3. **Cost tracking is centralized**: All services use `track_generation_cost()` utility
4. **Model selection is centralized**: All services use `get_model_name()` utility
5. **Metadata follows similar structure**: All features use similar metadata fields

### Recommended Architecture Changes

1. **Create BaseAIGenerator**: Eliminate code duplication across 9 services
2. **Create generation_metadata table**: Replace JSONB columns with normalized table
3. **Create Wave3Logger utility**: Unified logging to both systems
4. **Implement MODEL_TIER**: Add precision/balanced/rapid tiers
5. **Remove CHECK constraint**: Allow future wave names without migrations

---

## Code References

- `backend/app/services/mood_analyzer.py:50` - MoodAnalyzer.__init__() (Pattern 1)
- `backend/app/services/roadmap_generator.py:34` - RoadmapGenerator.__init__() (Pattern 2)
- `backend/app/services/deep_analyzer.py:125` - DeepAnalyzer.__init__() (Pattern 3)
- `backend/app/utils/pipeline_logger.py:17-33` - LogPhase and LogEvent enums
- `backend/app/services/analysis_orchestrator.py:548-574` - analysis_processing_log logging
- `backend/supabase/migrations/013_create_roadmap_tables.sql:1-40` - Current JSONB metadata pattern
- `backend/app/config/model_config.py:41-100` - Model registry and task assignments

---

## Open Questions

**CRITICAL - Need User Answers (Q57-Q73)**:

1. **Polymorphic Foreign Keys** (Q57): Should generation_metadata use polymorphic FKs (one FK column, one type column) or dual FKs with CHECK constraint?
2. **Metadata Abstraction Details** (Q59): How should "editing one edits both" work? Shared utility functions?
3. **Base Class Type** (Q60): Should BaseAIGenerator be abstract class, concrete class, or mixin?
4. **Existing Service Refactor** (Q61): Should existing 9 services be refactored to use base class?
5. **Base Class Name** (Q62): Is BaseAIGenerator the right name?
6. **Dual Logging Event Distribution** (Q63-Q64): Which events go to PipelineLogger vs analysis_processing_log?
7. **Migration Sequence** (Q65-Q67): Exact order for migrations 014, 015, 016?
8. **MODEL_TIER Implementation Timing** (Q70): Implement in same session or separate PR?
9. **MODEL_TIER Naming Approval** (Q71): Approve precision/balanced/rapid names?

---

## Related Research

- None yet (first comprehensive Session Bridge architecture research)

## Next Steps

1. **Wait for user answers Q57-Q73**
2. **Create base_generator.py** based on research findings
3. **Design generation_metadata migration SQL** with user's FK approach choice
4. **Create wave_logging.py utility** for dual logging
5. **Implement MODEL_TIER feature** with approved naming
6. **Update planning doc** with concrete implementation steps
