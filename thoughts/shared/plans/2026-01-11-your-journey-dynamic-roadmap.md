# Your Journey Dynamic Roadmap - Implementation Plan

## Overview

Implement dynamic roadmap generation for the "Your Journey" card that updates incrementally after each session's Wave 2 analysis completes. The roadmap uses cumulative context across sessions to build a comprehensive therapeutic journey narrative, with support for multiple compaction strategies and experimentation.

## Current State Analysis

### Existing Implementation
- **Frontend:** `NotesGoalsCard.tsx` displays hardcoded mock data
  - Structure: summary + achievements + currentFocus + 5 sections (Clinical Progress, Therapeutic Strategies, Identified Patterns, Current Treatment Focus, Long-term Goals)
  - Compact card + expandable modal
  - Location: `frontend/app/patient/components/NotesGoalsCard.tsx`

- **Backend:** No roadmap generation service exists
  - Wave 2 generates `deep_analysis` (JSONB) and `prose_analysis` (TEXT) per session
  - Uses cumulative context (nested Wave 1 + Wave 2 data from previous sessions)
  - Model: GPT-5.2 for deep analysis + prose
  - Location: `backend/app/services/deep_analyzer.py`, `backend/app/services/prose_generator.py`

- **Loading System:** LoadingOverlay component exists but not showing
  - Component: `frontend/app/patient/components/LoadingOverlay.tsx`
  - Hook: `frontend/app/patient/lib/usePatientSessions.ts` manages `loadingSessions` Set
  - Issue: Likely feature flags or polling detection problem

### Key Discoveries
- Wave 2 uses full nested context (no compaction) - grows to ~50K-80K tokens by Session 10
- Session cards show "Analyzing..." text (not spinner overlay) when Wave 1 incomplete
- Frontend polling detects Wave 2 completion via `last_wave2_update` timestamp
- All models correctly using GPT-5 series (no gpt-4o-mini in production)

## Desired End State

### User Experience
1. **Demo initialization:** Patient dashboard loads, "Your Journey" card shows empty state
2. **After Session 1 Wave 2 completes (~60s):**
   - Card shows loading overlay (spinner, 1000ms)
   - Card updates with roadmap based on Session 1
   - Counter shows "Based on 1 out of 10 uploaded sessions"
3. **After Session 2 Wave 2 completes (~120s):**
   - Card shows loading overlay again
   - Roadmap updates with cumulative insights from Sessions 1-2
   - Counter updates to "Based on 2 out of 10 uploaded sessions"
4. **Process continues incrementally through all 10 sessions**
5. **User can stop/resume processing at any time**

### Technical Goals
- Generate roadmap after each Wave 2 completion (incremental updates)
- Support 3 compaction strategies: Full Context, Progressive Summarization, Hierarchical
- Use GPT-5.2 for session insights + roadmap generation (maximum quality)
- Reuse session card loading overlay pattern (spinner, staggered animations)
- Store all roadmap versions (history tracking for analysis)
- Dynamic "Stop/Resume Processing" button

### Verification
- [ ] Roadmap updates after each Wave 2 completion (tested with 10-session demo)
- [ ] Counter shows "Based on X out of Y uploaded sessions" and increments correctly
- [ ] Loading overlay shows on "Your Journey" card when roadmap updates (1000ms spinner)
- [ ] All 3 compaction strategies switchable via env var
- [ ] Stop button halts processing, Resume button continues from last incomplete session
- [ ] Roadmap versions stored in database (can view history)

---

## What We're NOT Doing

**Out of Scope for This Implementation:**
- ❌ Journey-optimized structure (milestones, trajectories, progress dimensions) - Documented in Future Features
- ❌ Wave 2 context compaction optimization (keep current nested structure) - Documented in Future Features
- ❌ SSE real-time updates (use polling, design for SSE support) - Documented in Future Features
- ❌ Multiple models in parallel for comparison (single model via env var) - Can add later
- ❌ UI toggle for compaction strategy (env var only for MVP) - Can add later
- ❌ Roadmap regeneration API endpoint (automatic only for MVP) - Can add later
- ❌ Extended LoadingOverlay improvements (minimum bug fix only) - Can enhance later

---

## Implementation Approach

**High-Level Strategy:**
1. **Phase 0:** Fix LoadingOverlay bug (ensure spinner shows before building roadmap)
2. **Phase 1:** Backend infrastructure (database, session insights service, roadmap generator)
3. **Phase 2:** Compaction strategies implementation (3 algorithms with env var switching)
4. **Phase 3:** Frontend integration (data fetching, loading overlay, counter display)
5. **Phase 4:** Start/Stop/Resume button enhancement
6. **Phase 5:** Testing & verification

**Architecture:**
```
Wave 2 completes (Session N)
  ↓
SessionInsightsSummarizer (GPT-5.2) - Extract 3-5 key insights from deep_analysis
  ↓
RoadmapGenerator (GPT-5.2) - Generate roadmap using selected compaction strategy
  ↓
Database UPDATE (roadmap_data table + roadmap_versions table)
  ↓
Frontend polling detects change (roadmap_updated_at timestamp)
  ↓
Show loading overlay (1000ms spinner on "Your Journey" card)
  ↓
Fetch updated roadmap from /api/patients/{id}/roadmap
  ↓
Update UI with new roadmap + counter
```

---

## Phase 0: Fix LoadingOverlay Bug

### Overview
Investigate and fix why the LoadingOverlay spinner is not showing on session cards. Ensure the overlay system works before building roadmap loading logic.

### Changes Required

#### 0.1 Verify Feature Flags

**File:** `frontend/.env.local`

**Check current values:**
```bash
NEXT_PUBLIC_GRANULAR_UPDATES=true
NEXT_PUBLIC_SSE_ENABLED=false
NEXT_PUBLIC_POLLING_INTERVAL_WAVE1=1000
NEXT_PUBLIC_POLLING_INTERVAL_WAVE2=3000
```

**Action:** If flags are incorrect, update them and redeploy.

---

#### 0.2 Add Debug Logging

**File:** `frontend/app/patient/lib/usePatientSessions.ts`

**Changes:** Add console logs to track overlay state changes

```typescript
// Line ~115 - In updateChangedSessions function
const setSessionLoading = (sessionId: string, loading: boolean) => {
  console.log(`[LoadingOverlay Debug] ${loading ? 'SHOW' : 'HIDE'} overlay for session ${sessionId}`);
  setLoadingSessions(prev => {
    const next = new Set(prev);
    if (loading) {
      next.add(sessionId);
      console.log(`[LoadingOverlay Debug] loadingSessions Set now has ${next.size} sessions`);
    } else {
      next.delete(sessionId);
      console.log(`[LoadingOverlay Debug] loadingSessions Set now has ${next.size} sessions`);
    }
    return next;
  });
};
```

**Changes:** Add logging to detectChangedSessions

```typescript
// Line ~85 - After detectChangedSessions returns
const changedSessions = detectChangedSessions(status.sessions, sessionStatesRef.current);
console.log(`[LoadingOverlay Debug] Detected ${changedSessions.length} changed sessions:`, changedSessions.map(s => s.session_id));
```

---

#### 0.3 Verify Polling Detection

**File:** `frontend/app/patient/lib/usePatientSessions.ts`

**Test:** Run demo, check browser console for:
```
[LoadingOverlay Debug] Detected 1 changed sessions: [session-uuid]
[LoadingOverlay Debug] SHOW overlay for session session-uuid
[LoadingOverlay Debug] loadingSessions Set now has 1 sessions
```

**If logs don't appear:** Polling is not detecting changes correctly

**Possible fixes:**
1. Check `NEXT_PUBLIC_GRANULAR_UPDATES` flag is `true`
2. Verify `detectChangedSessions()` logic (line 48-90)
3. Ensure `sessionStatesRef` is updating correctly (line 358)

---

#### 0.4 Verify SessionCard Integration

**File:** `frontend/app/patient/components/SessionCard.tsx`

**Check integration (lines 42-43):**
```typescript
const { loadingSessions } = useSessionData();
const isLoading = loadingSessions.has(session.id);
```

**Add debug log:**
```typescript
const isLoading = loadingSessions.has(session.id);
console.log(`[SessionCard Debug] Session ${session.id} isLoading:`, isLoading, 'loadingSessions size:', loadingSessions.size);
```

**Check LoadingOverlay render (line 562):**
```typescript
<LoadingOverlay visible={isLoading} />
```

**If `isLoading` is always false:** Context is not providing updated Set

---

#### 0.5 Test LoadingOverlay Component

**File:** `frontend/app/patient/components/LoadingOverlay.tsx`

**Verify fade duration (line 17):**
```typescript
transition={{ duration: 0.3 }}
```

**Action:** Temporarily increase duration to 2s for testing visibility
```typescript
transition={{ duration: 2.0 }}  // TESTING ONLY - revert to 0.3 after debugging
```

**Test:** Run demo, verify spinner shows for 2 seconds when session updates

---

### Success Criteria

#### Automated Verification:
- [ ] Browser console shows `[LoadingOverlay Debug] SHOW overlay` logs when Wave 2 completes
- [ ] Browser console shows `loadingSessions Set now has 1 sessions` after change detection
- [ ] No errors in browser console related to polling or state updates

#### Manual Verification:
- [ ] Run demo, watch session cards during Wave 1/Wave 2 completion
- [ ] Spinner overlay appears on session card for 1000ms (semi-transparent gray + spinner)
- [ ] Overlay fades in smoothly, fades out after delay
- [ ] Multiple session overlays appear staggered (100ms apart)
- [ ] "Analyzing..." text changes to actual summary after overlay hides

**Implementation Note:** After completing Phase 0 and all automated verification passes, confirm manually that the spinner overlay is visible before proceeding to Phase 1.

---

## Phase 1: Backend Infrastructure

### Overview
Create database tables, session insights summarization service, and roadmap generation service with configurable model selection.

### Changes Required

#### 1.1 Database Schema - Roadmap Data Table

**File:** `backend/supabase/migrations/013_create_roadmap_tables.sql` (NEW)

**Changes:** Create table for current roadmap data

```sql
-- Patient roadmap data (latest version)
CREATE TABLE IF NOT EXISTS patient_roadmap (
    patient_id UUID PRIMARY KEY REFERENCES patients(id) ON DELETE CASCADE,
    roadmap_data JSONB NOT NULL,
    metadata JSONB NOT NULL,  -- sessions_analyzed, total_sessions, compaction_strategy, model_used, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster queries
CREATE INDEX idx_roadmap_patient ON patient_roadmap(patient_id);
CREATE INDEX idx_roadmap_updated ON patient_roadmap(updated_at);

-- Add comment
COMMENT ON TABLE patient_roadmap IS 'Current roadmap data for each patient (Your Journey card)';
COMMENT ON COLUMN patient_roadmap.metadata IS 'Metadata: {sessions_analyzed: int, total_sessions: int, compaction_strategy: str, model_used: str, generation_timestamp: str, last_session_id: uuid}';
```

---

#### 1.2 Database Schema - Roadmap Versions Table

**File:** `backend/supabase/migrations/013_create_roadmap_tables.sql` (continued)

**Changes:** Create table for roadmap version history

```sql
-- Roadmap version history (all previous roadmaps)
CREATE TABLE IF NOT EXISTS roadmap_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
    version INT NOT NULL,  -- Incremental version number (1, 2, 3, ...)
    roadmap_data JSONB NOT NULL,
    metadata JSONB NOT NULL,  -- Same structure as patient_roadmap.metadata
    generation_context JSONB,  -- What context was passed to LLM (for debugging)
    cost FLOAT,  -- Track cost per generation
    generation_duration_ms INT,  -- Track performance
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(patient_id, version)  -- Ensure unique version numbers per patient
);

-- Indexes
CREATE INDEX idx_roadmap_versions_patient ON roadmap_versions(patient_id);
CREATE INDEX idx_roadmap_versions_created ON roadmap_versions(created_at);

-- Add comment
COMMENT ON TABLE roadmap_versions IS 'Version history of all roadmap generations for debugging and analysis';
COMMENT ON COLUMN roadmap_versions.generation_context IS 'Context passed to LLM (tier summaries, session data, etc.) for debugging';
```

---

#### 1.3 Update model_config.py

**File:** `backend/app/config/model_config.py`

**Changes:** Add new task assignments for roadmap services

```python
# Line 93 - Add new task assignments after "speaker_labeling"
TASK_MODEL_ASSIGNMENTS = {
    "mood_analysis": "gpt-5-nano",
    "topic_extraction": "gpt-5-mini",
    "action_summary": "gpt-5-nano",
    "breakthrough_detection": "gpt-5",
    "deep_analysis": "gpt-5.2",
    "prose_generation": "gpt-5.2",
    "speaker_labeling": "gpt-5-mini",
    "session_insights": "gpt-5.2",      # NEW: Extract key insights from deep_analysis
    "roadmap_generation": "gpt-5.2",    # NEW: Generate patient journey roadmap
}
```

**Changes:** Add cost estimates

```python
# Line 105 - Add new cost estimates
ESTIMATED_TOKEN_USAGE = {
    "mood_analysis": {"input": 2000, "output": 200},
    "topic_extraction": {"input": 3000, "output": 300},
    "breakthrough_detection": {"input": 3500, "output": 400},
    "deep_analysis": {"input": 5000, "output": 800},
    "prose_generation": {"input": 2000, "output": 600},
    "speaker_labeling": {"input": 2500, "output": 150},
    "session_insights": {"input": 1500, "output": 150},        # NEW: ~$0.0006 per session
    "roadmap_generation": {"input": 10000, "output": 1000},   # NEW: Varies by strategy (~$0.003-0.020)
}
```

---

#### 1.4 Session Insights Summarizer Service

**File:** `backend/app/services/session_insights_summarizer.py` (NEW)

**Changes:** Create new service for extracting key insights from deep_analysis

```python
"""
Session Insights Summarizer

Extracts 3-5 key therapeutic insights from a session's deep_analysis JSONB.
Used for hierarchical context compaction in roadmap generation.

Model: GPT-5.2 (configurable)
Input: deep_analysis JSONB (~1.5K tokens)
Output: List of 3-5 insight strings (~150 tokens)
Cost: ~$0.0006 per session
"""

import json
from typing import Optional
from uuid import UUID
import openai
from app.config.model_config import get_model_name


class SessionInsightsSummarizer:
    """Extract key therapeutic insights from session deep_analysis"""

    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        """
        Initialize summarizer with OpenAI client.

        Args:
            api_key: OpenAI API key (uses env var if not provided)
            override_model: Override default model (for testing)
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = get_model_name("session_insights", override_model=override_model)

    def generate_insights(
        self,
        session_id: UUID,
        deep_analysis: dict,
        confidence_score: float
    ) -> list[str]:
        """
        Generate 3-5 key therapeutic insights from deep_analysis.

        Args:
            session_id: Session UUID
            deep_analysis: Complete deep_analysis JSONB dict
            confidence_score: Analysis confidence (0.0-1.0)

        Returns:
            List of 3-5 insight strings (1-2 sentences each)

        Example output:
            [
                "Patient identified work stress as primary anxiety trigger during guided reflection",
                "Successfully practiced 4-7-8 breathing technique independently for first time",
                "Breakthrough: Connected current avoidance patterns to childhood experiences"
            ]
        """
        prompt = self._build_prompt(session_id, deep_analysis, confidence_score)

        # Call GPT-5.2
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # Parse response
        result = json.loads(response.choices[0].message.content)
        insights = result.get("insights", [])

        # Validate output
        if not isinstance(insights, list) or len(insights) < 3 or len(insights) > 5:
            print(f"[WARNING] SessionInsightsSummarizer: Expected 3-5 insights, got {len(insights)}")

        return insights

    def _get_system_prompt(self) -> str:
        """System prompt defining task and output format"""
        return """You are a clinical insights extractor for therapy session analysis.

Your task: Extract 3-5 key therapeutic insights from a session's deep analysis.

Focus on the MOST SIGNIFICANT elements:
- Major progress or regression in symptoms/functioning
- New coping skills learned or existing skills practiced effectively
- Breakthrough moments, realizations, or cognitive shifts
- Important patterns, triggers, or behavioral dynamics identified
- Critical changes in therapeutic relationship or engagement

Output format:
{
  "insights": [
    "Insight 1 (1-2 sentences)",
    "Insight 2 (1-2 sentences)",
    "Insight 3 (1-2 sentences)",
    "Insight 4 (1-2 sentences, optional)",
    "Insight 5 (1-2 sentences, optional)"
  ]
}

Guidelines:
- Each insight: 1-2 sentences maximum (30-60 words)
- Be specific and concrete (reference techniques, emotions, situations)
- Prioritize actionable insights over general observations
- Maintain clinical accuracy and therapeutic tone
- Focus on what's NEW or CHANGED in this session
"""

    def _build_prompt(
        self,
        session_id: UUID,
        deep_analysis: dict,
        confidence_score: float
    ) -> str:
        """Build user prompt with deep_analysis data"""
        return f"""Session ID: {session_id}
Confidence Score: {confidence_score:.2f}

Deep Analysis Data:
{json.dumps(deep_analysis, indent=2)}

Extract 3-5 key therapeutic insights from this session's deep analysis.
Focus on the most significant progress, breakthroughs, skills, and patterns.
"""
```

---

#### 1.5 Roadmap Generator Service - Core Structure

**File:** `backend/app/services/roadmap_generator.py` (NEW)

**Changes:** Create roadmap generation service with compaction strategy support

```python
"""
Roadmap Generator

Generates dynamic "Your Journey" roadmap for patient dashboard.
Updates incrementally after each session's Wave 2 analysis completes.

Supports 3 compaction strategies:
1. Full Context: All previous sessions' raw data (expensive, maximum detail)
2. Progressive Summarization: Previous roadmap + current session (cheap, compact)
3. Hierarchical: Multi-tier summaries (balanced cost/detail)

Model: GPT-5.2 (configurable)
Input: Cumulative context (~10K-80K tokens depending on strategy)
Output: Roadmap JSON (~1K tokens)
Cost: ~$0.003-0.020 per generation (varies by strategy)
"""

import json
import os
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime
import openai
from app.config.model_config import get_model_name


CompactionStrategy = Literal["full", "progressive", "hierarchical"]


class RoadmapGenerator:
    """Generate patient journey roadmaps with configurable compaction strategies"""

    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        """
        Initialize roadmap generator with OpenAI client.

        Args:
            api_key: OpenAI API key (uses env var if not provided)
            override_model: Override default model (for testing)
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = get_model_name("roadmap_generation", override_model=override_model)

        # Get compaction strategy from env var
        self.strategy: CompactionStrategy = os.getenv(
            "ROADMAP_COMPACTION_STRATEGY",
            "hierarchical"  # Default to balanced approach
        ).lower()

        # Validate strategy
        if self.strategy not in ["full", "progressive", "hierarchical"]:
            print(f"[WARNING] Invalid ROADMAP_COMPACTION_STRATEGY '{self.strategy}', defaulting to 'hierarchical'")
            self.strategy = "hierarchical"

    def generate_roadmap(
        self,
        patient_id: UUID,
        current_session: dict,  # Current session wave1 + wave2 data
        context: dict,  # Compacted context (structure varies by strategy)
        sessions_analyzed: int,
        total_sessions: int
    ) -> dict:
        """
        Generate roadmap using configured compaction strategy.

        Args:
            patient_id: Patient UUID
            current_session: Current session data (wave1 + wave2)
            context: Previous context (structure depends on strategy)
            sessions_analyzed: Number of sessions analyzed (for counter display)
            total_sessions: Total sessions uploaded (for counter display)

        Returns:
            Roadmap dict matching NotesGoalsCard structure:
            {
                "summary": str,
                "achievements": [str, ...],  # 5 bullets
                "currentFocus": [str, ...],  # 3 bullets
                "sections": [
                    {"title": str, "content": str},  # 5 sections
                    ...
                ]
            }
        """
        start_time = datetime.now()

        # Build prompt based on strategy
        prompt = self._build_prompt_for_strategy(
            patient_id,
            current_session,
            context,
            sessions_analyzed,
            total_sessions
        )

        # Call GPT-5.2
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        # Parse and validate response
        roadmap_data = json.loads(response.choices[0].message.content)
        roadmap_data = self._validate_roadmap_structure(roadmap_data)

        # Calculate generation duration
        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        # Return roadmap with metadata
        return {
            "roadmap": roadmap_data,
            "metadata": {
                "compaction_strategy": self.strategy,
                "sessions_analyzed": sessions_analyzed,
                "total_sessions": total_sessions,
                "model_used": self.model,
                "generation_timestamp": datetime.now().isoformat(),
                "generation_duration_ms": duration_ms
            }
        }

    def _get_system_prompt(self) -> str:
        """System prompt defining roadmap generation task"""
        return """You are a therapeutic journey synthesizer for mental health care.

Your task: Generate a comprehensive "Your Journey" roadmap that summarizes a patient's therapeutic progress across multiple sessions.

The roadmap structure:
{
  "summary": "2-3 sentence overview of patient's journey (where they started, progress made, current state)",
  "achievements": [
    "Achievement 1 (1 sentence)",
    "Achievement 2 (1 sentence)",
    "Achievement 3 (1 sentence)",
    "Achievement 4 (1 sentence)",
    "Achievement 5 (1 sentence)"
  ],
  "currentFocus": [
    "Focus area 1 (1 sentence)",
    "Focus area 2 (1 sentence)",
    "Focus area 3 (1 sentence)"
  ],
  "sections": [
    {
      "title": "Clinical Progress",
      "content": "2-3 sentences describing symptom changes, functioning improvements, or clinical outcomes"
    },
    {
      "title": "Therapeutic Strategies",
      "content": "2-3 sentences about techniques used, interventions applied, and their effectiveness"
    },
    {
      "title": "Identified Patterns",
      "content": "2-3 sentences about recurring themes, triggers, behavioral patterns discovered"
    },
    {
      "title": "Current Treatment Focus",
      "content": "2-3 sentences about active goals, ongoing skill development, immediate priorities"
    },
    {
      "title": "Long-term Goals",
      "content": "2-3 sentences about overarching objectives, future milestones, sustained progress targets"
    }
  ]
}

Guidelines:
- Write for the PATIENT (supportive, encouraging, accessible language)
- Focus on GROWTH and PROGRESS (even if incremental)
- Be SPECIFIC (reference techniques, emotions, situations by name)
- Maintain CLINICAL ACCURACY (don't exaggerate or misrepresent)
- Show CONTINUITY (connect current session to previous journey)
- Each achievement: 1 sentence, concrete, measurable
- Current focus: Active, actionable, forward-looking
- Section content: 2-3 sentences, cohesive narrative

Tone: Warm, professional, empowering, hopeful but realistic
"""

    def _validate_roadmap_structure(self, roadmap: dict) -> dict:
        """Validate and fix roadmap structure"""
        # Ensure required fields exist
        if "summary" not in roadmap:
            roadmap["summary"] = "Your therapeutic journey is in progress."

        if "achievements" not in roadmap or not isinstance(roadmap["achievements"], list):
            roadmap["achievements"] = []

        if "currentFocus" not in roadmap or not isinstance(roadmap["currentFocus"], list):
            roadmap["currentFocus"] = []

        if "sections" not in roadmap or not isinstance(roadmap["sections"], list):
            roadmap["sections"] = []

        # Validate achievements count (should be 5)
        if len(roadmap["achievements"]) < 5:
            print(f"[WARNING] RoadmapGenerator: Expected 5 achievements, got {len(roadmap['achievements'])}")
            # Pad with placeholder if needed
            while len(roadmap["achievements"]) < 5:
                roadmap["achievements"].append("Continued engagement in therapeutic process")
        elif len(roadmap["achievements"]) > 5:
            roadmap["achievements"] = roadmap["achievements"][:5]

        # Validate currentFocus count (should be 3)
        if len(roadmap["currentFocus"]) < 3:
            print(f"[WARNING] RoadmapGenerator: Expected 3 focus areas, got {len(roadmap['currentFocus'])}")
            while len(roadmap["currentFocus"]) < 3:
                roadmap["currentFocus"].append("Ongoing skill development and practice")
        elif len(roadmap["currentFocus"]) > 3:
            roadmap["currentFocus"] = roadmap["currentFocus"][:3]

        # Validate sections (should be 5 with correct titles)
        expected_sections = [
            "Clinical Progress",
            "Therapeutic Strategies",
            "Identified Patterns",
            "Current Treatment Focus",
            "Long-term Goals"
        ]

        if len(roadmap["sections"]) != 5:
            print(f"[WARNING] RoadmapGenerator: Expected 5 sections, got {len(roadmap['sections'])}")

        # Ensure all sections have title and content
        for section in roadmap["sections"]:
            if "title" not in section:
                section["title"] = "Section"
            if "content" not in section:
                section["content"] = "Progress is being made in this area."

        return roadmap

    # Strategy-specific methods will be added in Phase 2
    def _build_prompt_for_strategy(self, *args, **kwargs) -> str:
        """Build prompt based on selected compaction strategy (implemented in Phase 2)"""
        raise NotImplementedError("Compaction strategies implemented in Phase 2")
```

---

### Success Criteria

#### Automated Verification:
- [ ] Database migration applies cleanly: `cd backend && supabase migration up`
- [ ] Tables created: `SELECT * FROM patient_roadmap LIMIT 1;`, `SELECT * FROM roadmap_versions LIMIT 1;`
- [ ] Model config updated: `python -c "from app.config.model_config import get_model_name; assert get_model_name('session_insights') == 'gpt-5.2'"`
- [ ] Services import successfully: `python -c "from app.services.session_insights_summarizer import SessionInsightsSummarizer; from app.services.roadmap_generator import RoadmapGenerator"`

#### Manual Verification:
- [ ] Inspect `roadmap_versions` table schema in Supabase dashboard (has all columns: id, patient_id, version, roadmap_data, metadata, generation_context, cost, generation_duration_ms, created_at)
- [ ] Verify unique constraint on (patient_id, version) exists
- [ ] Check model_config.py cost estimates are reasonable

**Implementation Note:** After completing Phase 1 and all automated verification passes, manually verify database schema in Supabase before proceeding to Phase 2.

---

## Phase 2: Compaction Strategies Implementation

### Overview
Implement 3 context compaction strategies: Full Context, Progressive Summarization, and Hierarchical. Add strategy-specific prompt building and context management logic.

### Changes Required

#### 2.1 Strategy 1: Full Context (No Compaction)

**File:** `backend/app/services/roadmap_generator.py`

**Changes:** Add full context strategy implementation

```python
# Add method after _validate_roadmap_structure

def _build_prompt_for_strategy(
    self,
    patient_id: UUID,
    current_session: dict,
    context: dict,
    sessions_analyzed: int,
    total_sessions: int
) -> str:
    """Build prompt based on selected compaction strategy"""
    if self.strategy == "full":
        return self._build_full_context_prompt(
            patient_id, current_session, context, sessions_analyzed, total_sessions
        )
    elif self.strategy == "progressive":
        return self._build_progressive_prompt(
            patient_id, current_session, context, sessions_analyzed, total_sessions
        )
    elif self.strategy == "hierarchical":
        return self._build_hierarchical_prompt(
            patient_id, current_session, context, sessions_analyzed, total_sessions
        )
    else:
        raise ValueError(f"Unknown compaction strategy: {self.strategy}")

def _build_full_context_prompt(
    self,
    patient_id: UUID,
    current_session: dict,
    context: dict,
    sessions_analyzed: int,
    total_sessions: int
) -> str:
    """
    Strategy 1: Full Context (No Compaction)

    Passes ALL previous sessions' raw Wave 1 + Wave 2 data to LLM.

    Context structure:
    {
        "previous_context": {
            # Nested structure from Wave 2
            "previous_context": {...},
            "session_N_wave1": {...},
            "session_N_wave2": {...}
        },
        "current_session": {
            "wave1": {...},
            "wave2": {...}
        }
    }

    Token count: ~50K-80K by Session 10
    Cost: ~$0.014-0.020 per generation
    """
    prompt = f"""Patient ID: {patient_id}
Sessions Analyzed: {sessions_analyzed} out of {total_sessions} uploaded

COMPACTION STRATEGY: Full Context
You have access to ALL previous sessions' complete Wave 1 and Wave 2 analysis data.

CUMULATIVE CONTEXT (All Previous Sessions):
{json.dumps(context, indent=2)}

CURRENT SESSION DATA:
{json.dumps(current_session, indent=2)}

Generate a comprehensive "Your Journey" roadmap that synthesizes insights across all {sessions_analyzed} sessions.
The roadmap should reflect the patient's full therapeutic journey from Session 1 to Session {sessions_analyzed}.

Focus on:
- Overall trajectory (where they started → where they are now)
- Key milestones and breakthroughs across all sessions
- Cumulative skill development and progress
- Emerging patterns visible only across multiple sessions
- Current state in context of full journey
"""
    return prompt
```

---

#### 2.2 Strategy 2: Progressive Summarization

**File:** `backend/app/services/roadmap_generator.py`

**Changes:** Add progressive summarization strategy

```python
# Add method after _build_full_context_prompt

def _build_progressive_prompt(
    self,
    patient_id: UUID,
    current_session: dict,
    context: dict,
    sessions_analyzed: int,
    total_sessions: int
) -> str:
    """
    Strategy 2: Progressive Summarization

    Passes ONLY previous roadmap + current session data.
    Previous roadmap already contains synthesized insights from Sessions 1 to N-1.

    Context structure:
    {
        "previous_roadmap": {
            "summary": "...",
            "achievements": [...],
            "currentFocus": [...],
            "sections": [...]
        },  # Only exists if sessions_analyzed > 1
        "current_session": {
            "wave1": {...},
            "wave2": {...}
        }
    }

    Token count: ~7K-10K (constant)
    Cost: ~$0.0025 per generation
    """
    # Extract previous roadmap if it exists
    previous_roadmap = context.get("previous_roadmap")

    if previous_roadmap:
        # Session 2+: Build on previous roadmap
        prompt = f"""Patient ID: {patient_id}
Sessions Analyzed: {sessions_analyzed} out of {total_sessions} uploaded

COMPACTION STRATEGY: Progressive Summarization
You are updating an existing roadmap with insights from the latest session.

PREVIOUS ROADMAP (Sessions 1-{sessions_analyzed - 1}):
{json.dumps(previous_roadmap, indent=2)}

CURRENT SESSION DATA (Session {sessions_analyzed}):
{json.dumps(current_session, indent=2)}

Generate an UPDATED "Your Journey" roadmap that:
1. Builds on the previous roadmap's narrative
2. Integrates new insights from Session {sessions_analyzed}
3. Updates achievements (add new ones, keep most significant from before)
4. Updates current focus (shift based on latest session)
5. Updates all 5 sections to reflect cumulative + current progress

Important:
- Maintain narrative continuity (don't contradict previous roadmap)
- Show progression (how Session {sessions_analyzed} builds on earlier work)
- Keep the most important historical insights (don't lose key milestones)
- Emphasize recent progress (Session {sessions_analyzed} should be prominent)
"""
    else:
        # Session 1: No previous roadmap
        prompt = f"""Patient ID: {patient_id}
Sessions Analyzed: {sessions_analyzed} out of {total_sessions} uploaded

COMPACTION STRATEGY: Progressive Summarization
This is the FIRST roadmap generation for this patient.

CURRENT SESSION DATA (Session 1):
{json.dumps(current_session, indent=2)}

Generate the INITIAL "Your Journey" roadmap based on Session 1.
This roadmap will be progressively updated as more sessions are analyzed.

Focus on:
- Initial presentation and presenting concerns
- First steps taken in therapy
- Early insights and rapport building
- Foundation for future progress
"""

    return prompt
```

---

#### 2.3 Strategy 3: Hierarchical Summarization - Core Logic

**File:** `backend/app/services/roadmap_generator.py`

**Changes:** Add hierarchical strategy with tier management

```python
# Add method after _build_progressive_prompt

def _build_hierarchical_prompt(
    self,
    patient_id: UUID,
    current_session: dict,
    context: dict,
    sessions_analyzed: int,
    total_sessions: int
) -> str:
    """
    Strategy 3: Hierarchical Summarization

    Uses multi-tier summaries that compact at different granularities:
    - Tier 1: Per-session insights (3-5 bullets) - Recent sessions
    - Tier 2: Every 5 sessions → compacted paragraph - Mid-range history
    - Tier 3: Every 10 sessions → journey arc narrative - Long-term trajectory

    Context structure:
    {
        "tier3_summary": "Sessions 1-10 arc narrative",  # Only if sessions_analyzed > 10
        "tier2_summaries": {
            "sessions_11_15": "Paragraph summary",
            "sessions_16_20": "Paragraph summary"
        },  # Only if sessions_analyzed > 10
        "tier1_summaries": {
            "session_N": ["insight 1", "insight 2", ...],  # Recent sessions
            "session_N+1": [...]
        },
        "previous_roadmap": {...},  # Previous roadmap
        "current_session": {
            "wave1": {...},
            "wave2": {...},
            "insights": [...]  # Generated by SessionInsightsSummarizer
        }
    }

    Token count: ~10K-12K
    Cost: ~$0.003-0.004 per generation
    """
    # Determine tier structure based on sessions_analyzed
    tier3_threshold = 10
    tier2_threshold = 5

    # Build tier context
    tier3_summary = context.get("tier3_summary")
    tier2_summaries = context.get("tier2_summaries", {})
    tier1_summaries = context.get("tier1_summaries", {})
    previous_roadmap = context.get("previous_roadmap")

    # Build prompt with appropriate tier context
    prompt = f"""Patient ID: {patient_id}
Sessions Analyzed: {sessions_analyzed} out of {total_sessions} uploaded

COMPACTION STRATEGY: Hierarchical Summarization
Multi-tier context provides both high-level trajectory and recent session details.
"""

    # Add Tier 3 if exists (Sessions 1-10+ arc)
    if tier3_summary:
        prompt += f"""
TIER 3 - LONG-TERM TRAJECTORY (Sessions 1-{tier3_threshold}):
{tier3_summary}

"""

    # Add Tier 2 summaries if exist (5-session chunks)
    if tier2_summaries:
        prompt += "TIER 2 - MID-RANGE HISTORY (5-session summaries):\n"
        for session_range, summary in tier2_summaries.items():
            prompt += f"\n{session_range}: {summary}\n"
        prompt += "\n"

    # Add Tier 1 summaries (recent sessions)
    if tier1_summaries:
        prompt += "TIER 1 - RECENT SESSIONS (detailed insights):\n"
        for session_key, insights in tier1_summaries.items():
            prompt += f"\n{session_key}:\n"
            for insight in insights:
                prompt += f"  - {insight}\n"
        prompt += "\n"

    # Add previous roadmap
    if previous_roadmap:
        prompt += f"""PREVIOUS ROADMAP (Sessions 1-{sessions_analyzed - 1}):
{json.dumps(previous_roadmap, indent=2)}

"""

    # Add current session
    prompt += f"""CURRENT SESSION DATA (Session {sessions_analyzed}):
{json.dumps(current_session, indent=2)}

Generate an UPDATED "Your Journey" roadmap that synthesizes:
1. Long-term trajectory (Tier 3) - Overall journey arc
2. Mid-range patterns (Tier 2) - Themes across recent sessions
3. Recent progress (Tier 1) - Specific recent insights
4. Latest session (Current) - New developments

The roadmap should reflect BOTH the big picture AND recent details.
Show how Session {sessions_analyzed} fits into the larger journey narrative.
"""

    return prompt
```

---

#### 2.4 Hierarchical Strategy - Tier Compaction Logic

**File:** `backend/app/services/roadmap_generator.py`

**Changes:** Add helper methods for tier management

```python
# Add class method for tier compaction

@staticmethod
def compact_tier1_to_tier2(tier1_summaries: dict) -> str:
    """
    Compact Tier 1 insights (5 sessions worth) into Tier 2 paragraph summary.

    Called every 5 sessions to prevent Tier 1 from growing too large.

    Args:
        tier1_summaries: Dict of {session_id: [insights]} for 5 sessions

    Returns:
        Paragraph summary (2-3 sentences) synthesizing 5 sessions

    Example:
        Input: {
            "session_01": ["Anxiety trigger identified", "Breathing practiced"],
            "session_02": ["Breakthrough with avoidance", ...],
            ...
        }
        Output: "Patient made significant progress in Sessions 1-5, identifying work stress as primary anxiety trigger and practicing breathing techniques independently. Breakthrough moment occurred in Session 2 when connecting avoidance patterns to childhood experiences. By Session 5, patient demonstrated consistent skill application."
    """
    # This will be called by the orchestration script, not the generator itself
    # Placeholder for now - actual implementation in orchestration (Phase 3)
    pass

@staticmethod
def compact_tier2_to_tier3(tier2_summaries: list[str]) -> str:
    """
    Compact Tier 2 summaries (10 sessions worth) into Tier 3 journey arc.

    Called every 10 sessions to create high-level trajectory narrative.

    Args:
        tier2_summaries: List of 2 Tier 2 paragraph summaries (Sessions 1-5, 6-10)

    Returns:
        Journey arc narrative (3-4 sentences) synthesizing 10 sessions

    Example:
        Output: "Patient's journey began with acute anxiety symptoms and work-related stress (Sessions 1-5), progressing through skill acquisition and breakthrough insights about avoidance patterns. Mid-journey (Sessions 6-10) focused on applying learned techniques in real-world situations, with increasing confidence and reduced symptom severity. Overall trajectory shows steady improvement in emotional regulation and social functioning."
    """
    # Placeholder - implemented in orchestration script
    pass
```

---

### Success Criteria

#### Automated Verification:
- [ ] Strategy methods implemented: `python -c "from app.services.roadmap_generator import RoadmapGenerator; rg = RoadmapGenerator(); assert hasattr(rg, '_build_full_context_prompt')"`
- [ ] All 3 strategies callable: Test each strategy method exists and doesn't raise NotImplementedError
- [ ] Env var switching works: Set `ROADMAP_COMPACTION_STRATEGY=full`, verify `RoadmapGenerator().strategy == 'full'`

#### Manual Verification:
- [ ] Read through each strategy's prompt template - verify it makes clinical sense
- [ ] Check token count estimates are reasonable for each strategy
- [ ] Verify tier thresholds (5 sessions → Tier 2, 10 sessions → Tier 3) are hardcoded correctly

**Implementation Note:** After completing Phase 2, test that each compaction strategy can be selected via env var before proceeding to Phase 3.

---

## Phase 3: Frontend Integration

### Overview
Integrate roadmap API, add loading overlay to "Your Journey" card, implement session counter, and add polling detection for roadmap updates.

### Changes Required

#### 3.1 API Client - Roadmap Endpoints

**File:** `frontend/lib/api-client.ts`

**Changes:** Add roadmap fetch method

```typescript
// Add after existing session methods (around line 600)

/**
 * Get patient roadmap data
 */
async getRoadmap(patientId: string): Promise<ApiResponse<RoadmapData>> {
  try {
    const response = await fetch(`${this.baseUrl}/api/patients/${patientId}/roadmap`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      if (response.status === 404) {
        // Roadmap doesn't exist yet (no sessions analyzed)
        return { success: true, data: null };
      }
      throw new Error(`Failed to fetch roadmap: ${response.statusText}`);
    }

    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error('[API] Error fetching roadmap:', error);
    return { success: false, error: error instanceof Error ? error.message : 'Unknown error' };
  }
}
```

---

#### 3.2 TypeScript Interfaces

**File:** `frontend/lib/types.ts` (or create new `frontend/lib/roadmap-types.ts`)

**Changes:** Add roadmap data interfaces

```typescript
// Add roadmap interfaces

export interface RoadmapSection {
  title: string;
  content: string;
}

export interface RoadmapData {
  summary: string;
  achievements: string[];  // 5 items
  currentFocus: string[];  // 3 items
  sections: RoadmapSection[];  // 5 sections
}

export interface RoadmapMetadata {
  compaction_strategy: 'full' | 'progressive' | 'hierarchical';
  sessions_analyzed: number;
  total_sessions: number;
  model_used: string;
  generation_timestamp: string;
  generation_duration_ms: number;
}

export interface RoadmapResponse {
  roadmap: RoadmapData;
  metadata: RoadmapMetadata;
}
```

---

#### 3.3 Update NotesGoalsCard - Data Fetching

**File:** `frontend/app/patient/components/NotesGoalsCard.tsx`

**Changes:** Replace mock data with API fetching

```typescript
// Add imports at top
import { useEffect, useState } from 'react';
import { useSessionData } from '../contexts/SessionDataContext';
import { LoadingOverlay } from './LoadingOverlay';
import { apiClient } from '@/lib/api-client';
import type { RoadmapData, RoadmapMetadata } from '@/lib/types';

// Replace existing component
export function NotesGoalsCard() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [roadmapData, setRoadmapData] = useState<RoadmapData | null>(null);
  const [metadata, setMetadata] = useState<RoadmapMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  const { patientId, loadingRoadmap } = useSessionData();  // NEW: Get patientId and loading state from context

  // Fetch roadmap data on mount and when patientId changes
  useEffect(() => {
    if (!patientId) return;

    const fetchRoadmap = async () => {
      setIsLoading(true);
      const result = await apiClient.getRoadmap(patientId);

      if (result.success && result.data) {
        setRoadmapData(result.data.roadmap);
        setMetadata(result.data.metadata);
        setError(null);
      } else if (result.success && !result.data) {
        // No roadmap yet (0 sessions analyzed)
        setRoadmapData(null);
        setMetadata(null);
        setError(null);
      } else {
        setError(result.error || 'Failed to load roadmap');
      }

      setIsLoading(false);
    };

    fetchRoadmap();
  }, [patientId]);

  // Accessibility hook unchanged
  useModalAccessibility({
    isOpen: isExpanded,
    onClose: () => setIsExpanded(false),
    modalRef,
  });

  // Show loading state if initial load or roadmap being generated
  if (isLoading || loadingRoadmap) {
    return (
      <div className="relative bg-gradient-to-br from-white to-[#FFF9F5] dark:from-[#2a2435] dark:to-[#1a1625] rounded-2xl p-6 shadow-lg h-[400px] overflow-hidden transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548]">
        <LoadingOverlay visible={true} />
        <div className="flex flex-col items-center justify-center h-full">
          <h2 style={{ fontFamily: fontSerif, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200 mb-4">
            Your Journey
          </h2>
          <p style={{ fontFamily: fontSerif, fontSize: '14px' }} className="text-gray-600 dark:text-gray-400">
            {isLoading ? 'Loading roadmap...' : 'Generating roadmap...'}
          </p>
        </div>
      </div>
    );
  }

  // Show error state if fetch failed
  if (error) {
    return (
      <div className="bg-gradient-to-br from-white to-[#FFF9F5] dark:from-[#2a2435] dark:to-[#1a1625] rounded-2xl p-6 shadow-lg h-[400px] overflow-hidden transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548]">
        <div className="flex flex-col items-center justify-center h-full">
          <h2 style={{ fontFamily: fontSerif, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200 mb-4">
            Your Journey
          </h2>
          <p style={{ fontFamily: fontSerif, fontSize: '14px' }} className="text-red-600 dark:text-red-400">
            {error}
          </p>
        </div>
      </div>
    );
  }

  // Show empty state if no roadmap yet (0 sessions analyzed)
  if (!roadmapData || !metadata) {
    return (
      <div className="bg-gradient-to-br from-white to-[#FFF9F5] dark:from-[#2a2435] dark:to-[#1a1625] rounded-2xl p-6 shadow-lg h-[400px] overflow-hidden transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548]">
        <div className="flex flex-col items-center justify-center h-full text-center">
          <h2 style={{ fontFamily: fontSerif, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200 mb-4">
            Your Journey
          </h2>
          <p style={{ fontFamily: fontSerif, fontSize: '14px' }} className="text-gray-600 dark:text-gray-400 mb-2">
            Upload therapy sessions to generate your personalized journey roadmap
          </p>
          <p style={{ fontFamily: fontSans, fontSize: '12px' }} className="text-gray-500 dark:text-gray-500">
            Your roadmap will appear here after your first session is analyzed
          </p>
        </div>
      </div>
    );
  }

  // Render card with roadmap data (rest of component unchanged, but use roadmapData instead of notesGoalsContent)
  // ... existing JSX with {roadmapData.summary}, {roadmapData.achievements}, etc.
```

---

#### 3.4 Update NotesGoalsCard - Add Session Counter

**File:** `frontend/app/patient/components/NotesGoalsCard.tsx`

**Changes:** Add "Based on X out of Y sessions" counter

```typescript
// In the compact card section (around line 40-70), add counter above summary

<div className="flex flex-col mb-5 text-center">
  <h2 style={{ fontFamily: fontSerif, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200">
    Your Journey
  </h2>

  {/* NEW: Session counter */}
  {metadata && (
    <p style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500, letterSpacing: '0.5px' }} className="text-gray-500 dark:text-gray-500 mt-2">
      Based on {metadata.sessions_analyzed} out of {metadata.total_sessions} uploaded session{metadata.total_sessions !== 1 ? 's' : ''}
    </p>
  )}
</div>

<p style={{ fontFamily: fontSerif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6, color: 'var(--text-gray-600)' }} className="dark:text-gray-400 mb-5">
  {roadmapData.summary}
</p>
```

**Changes:** Add counter to expanded modal too

```typescript
// In the modal section (around line 110-120), add counter below title

<h2 style={{ fontFamily: fontSerif, fontSize: '24px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200 mb-2 pr-12 text-center">
  Your Journey
</h2>

{/* NEW: Session counter in modal */}
{metadata && (
  <p style={{ fontFamily: fontSans, fontSize: '12px', fontWeight: 500, letterSpacing: '0.5px' }} className="text-gray-500 dark:text-gray-500 mb-6 text-center">
    Based on {metadata.sessions_analyzed} out of {metadata.total_sessions} uploaded session{metadata.total_sessions !== 1 ? 's' : ''}
  </p>
)}

<p style={{ fontFamily: fontSerif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }} className="text-gray-700 dark:text-gray-300 mb-8">
  {roadmapData.summary}
</p>
```

---

#### 3.5 Update SessionDataContext - Add Roadmap Loading State

**File:** `frontend/app/patient/contexts/SessionDataContext.tsx`

**Changes:** Add roadmap loading state to context

```typescript
// Update context interface (around line 15)
interface SessionDataContextType {
  sessions: Session[];
  isLoading: boolean;
  error: string | null;
  selectedSession: Session | null;
  setSelectedSession: (session: Session | null) => void;
  loadingSessions: Set<string>;  // Existing
  loadingRoadmap: boolean;  // NEW: Roadmap loading state
  patientId: string | null;  // NEW: Patient ID for API calls
}

// Update context provider (around line 50)
export function SessionDataProvider({ children }: { children: React.ReactNode }) {
  const {
    sessions,
    isLoading,
    error,
    loadingSessions,
    loadingRoadmap,  // NEW: Get from usePatientSessions
    patientId,  // NEW: Get from usePatientSessions
  } = usePatientSessions();

  const [selectedSession, setSelectedSession] = useState<Session | null>(null);

  // ... existing useEffect ...

  return (
    <SessionDataContext.Provider
      value={{
        sessions,
        isLoading,
        error,
        selectedSession,
        setSelectedSession,
        loadingSessions,
        loadingRoadmap,  // NEW: Expose to consumers
        patientId,  // NEW: Expose to consumers
      }}
    >
      {children}
    </SessionDataContext.Provider>
  );
}
```

---

#### 3.6 Update usePatientSessions - Add Roadmap Polling

**File:** `frontend/app/patient/lib/usePatientSessions.ts`

**Changes:** Add roadmap loading state and polling detection

```typescript
// Add state for roadmap loading (around line 170)
const [loadingRoadmap, setLoadingRoadmap] = useState(false);

// Add roadmap timestamp tracking to sessionStatesRef
// Modify SessionState interface in polling-config.ts to include roadmap_updated_at

// In detectChangedSessions function (around line 85), add roadmap change detection
// After checking wave2 completion:
if (session.roadmap_updated_at && session.roadmap_updated_at !== oldState.roadmap_updated_at) {
  // Roadmap updated - trigger "Your Journey" card loading overlay
  console.log(`[Polling Debug] Roadmap updated for patient, timestamp changed`);
  setLoadingRoadmap(true);

  // Hide loading overlay after 1000ms (same pattern as session cards)
  setTimeout(() => {
    setLoadingRoadmap(false);
  }, 1000);
}

// Update return value (around line 510)
return {
  sessions,
  isLoading,
  error,
  loadingSessions,
  setSessionLoading,
  refresh,
  loadingRoadmap,  // NEW: Expose roadmap loading state
  patientId,  // NEW: Expose patient ID
};
```

---

#### 3.7 Update Demo Status Endpoint - Add Roadmap Timestamp

**File:** `backend/app/routers/demo.py`

**Changes:** Add roadmap_updated_at to status response

```python
# In get_demo_status function (around line 600), add roadmap query

# After querying sessions, query roadmap
roadmap_result = supabase.table("patient_roadmap").select("updated_at").eq("patient_id", patient_id).execute()
roadmap_updated_at = None
if roadmap_result.data and len(roadmap_result.data) > 0:
    roadmap_updated_at = roadmap_result.data[0].get("updated_at")

# Add to response (around line 610)
return DemoStatusResponse(
    demo_token=demo_user["demo_token"],
    patient_id=patient_id,
    session_count=session_count,
    created_at=demo_user.get("created_at", ""),
    expires_at=demo_user["demo_expires_at"],
    is_expired=is_expired,
    analysis_status=analysis_status,
    wave1_complete=wave1_complete_count,
    wave2_complete=wave2_complete_count,
    sessions=session_statuses,
    roadmap_updated_at=roadmap_updated_at,  # NEW
)
```

---

### Success Criteria

#### Automated Verification:
- [ ] TypeScript compiles: `cd frontend && npm run build`
- [ ] API client method exists: Check `frontend/lib/api-client.ts` has `getRoadmap` method
- [ ] Context provides new fields: Verify `SessionDataContext` exports `loadingRoadmap` and `patientId`

#### Manual Verification:
- [ ] Run demo, verify "Your Journey" card shows empty state before Session 1 Wave 2 completes
- [ ] After Session 1 Wave 2 completes, verify loading overlay appears on card for 1000ms
- [ ] Verify card updates with roadmap data and shows "Based on 1 out of 10 uploaded sessions"
- [ ] After Session 2 Wave 2 completes, verify counter updates to "2 out of 10"
- [ ] Verify roadmap data changes (summary, achievements, etc. reflect cumulative insights)
- [ ] Open expanded modal, verify counter also appears there

**Implementation Note:** After completing Phase 3, test in browser that roadmap loading overlay appears and counter increments correctly before proceeding to Phase 4.

---

## Phase 4: Start/Stop/Resume Button Enhancement

### Overview
Upgrade existing "Stop Processing" button to dynamic "Start/Stop/Resume Processing" button with smart resume logic.

### Changes Required

#### 4.1 Backend - Add Processing State Tracking

**File:** `backend/app/routers/demo.py`

**Changes:** Add processing state fields to status response

```python
# Update DemoStatusResponse model (around line 50)
class DemoStatusResponse(BaseModel):
    demo_token: str
    patient_id: str
    session_count: int
    created_at: str
    expires_at: str
    is_expired: bool
    analysis_status: str
    wave1_complete: int
    wave2_complete: int
    sessions: list[SessionStatus]
    roadmap_updated_at: Optional[str] = None

    # NEW: Processing state fields
    processing_state: str  # "running" | "stopped" | "complete" | "not_started"
    stopped_at_session_id: Optional[str] = None  # Which session was being processed when stopped
    can_resume: bool  # Whether resume is possible
```

**Changes:** Add state detection logic in get_demo_status

```python
# After determining analysis_status (around line 590), add processing state detection

# Determine processing state
processing_state = "not_started"
stopped_at_session_id = None
can_resume = False

# Check if processing is currently running (Wave 1 or Wave 2 in progress)
wave1_running = analysis_status_dict.get("wave1_running", False)
wave2_running = analysis_status_dict.get("wave2_running", False)

if wave1_running or wave2_running:
    processing_state = "running"
elif wave2_complete_count == session_count:
    processing_state = "complete"
elif wave1_complete_count > 0 or wave2_complete_count > 0:
    # Some sessions analyzed but not all - could be stopped or just in progress
    wave1_stopped = analysis_status_dict.get("wave1_stopped", False)
    wave2_stopped = analysis_status_dict.get("wave2_stopped", False)

    if wave1_stopped or wave2_stopped:
        processing_state = "stopped"
        can_resume = True

        # Find which session was being processed when stopped
        for session in sessions:
            if session.get("topics") and not session.get("prose_analysis"):
                # Wave 1 complete but Wave 2 incomplete - this is where we stopped
                stopped_at_session_id = session["id"]
                break

# Add to response
return DemoStatusResponse(
    # ... existing fields ...
    processing_state=processing_state,
    stopped_at_session_id=stopped_at_session_id,
    can_resume=can_resume,
    roadmap_updated_at=roadmap_updated_at,
)
```

---

#### 4.2 Backend - Resume Endpoint

**File:** `backend/app/routers/demo.py`

**Changes:** Add resume endpoint

```python
# Add new endpoint after stop endpoint (around line 700)

@router.post("/resume")
async def resume_demo_processing(
    background_tasks: BackgroundTasks,
    demo_user = Depends(get_current_demo_user)
):
    """
    Resume processing from where it was stopped.

    Smart resume logic:
    1. Find incomplete sessions (Wave 1 complete but Wave 2 incomplete)
    2. Re-run Wave 2 for incomplete session
    3. Continue with remaining sessions (Wave 1 → Wave 2 → Roadmap)

    Returns immediately after scheduling background tasks.
    """
    patient_id = demo_user["patient_id"]

    # Reset stopped flags
    analysis_status_dict["wave1_stopped"] = False
    analysis_status_dict["wave2_stopped"] = False
    analysis_status_dict["roadmap_stopped"] = False

    # Find incomplete sessions
    sessions_result = supabase.table("therapy_sessions") \
        .select("id, topics, prose_analysis") \
        .eq("patient_id", patient_id) \
        .order("session_date") \
        .execute()

    sessions = sessions_result.data
    incomplete_session = None
    next_sessions = []

    for session in sessions:
        if session.get("topics") and not session.get("prose_analysis"):
            # Wave 1 complete but Wave 2 incomplete - this is the stopped session
            if not incomplete_session:
                incomplete_session = session
        elif not session.get("topics"):
            # Wave 1 not started - these are next sessions
            next_sessions.append(session)

    # Schedule resume tasks
    if incomplete_session:
        # Re-run Wave 2 for incomplete session
        print(f"[RESUME] Re-running Wave 2 for Session {incomplete_session['id']}")
        background_tasks.add_task(
            run_wave2_for_session,
            patient_id,
            incomplete_session["id"]
        )

    # Continue with remaining sessions (Wave 1 → Wave 2 → Roadmap)
    if next_sessions:
        print(f"[RESUME] Continuing with {len(next_sessions)} remaining sessions")
        background_tasks.add_task(
            run_wave1_then_wave2,
            patient_id
        )

    return {
        "message": "Processing resumed",
        "incomplete_session_id": incomplete_session["id"] if incomplete_session else None,
        "remaining_sessions": len(next_sessions)
    }


async def run_wave2_for_session(patient_id: str, session_id: str):
    """Run Wave 2 analysis for a single session (used by resume endpoint)"""
    # Implementation similar to existing Wave 2 execution
    # Call deep_analyzer.analyze_session() and update database
    # Then trigger roadmap generation
    pass
```

---

#### 4.3 Frontend - Update Stop Button Component

**File:** `frontend/app/patient/components/StopProcessingButton.tsx` (rename from existing stop button if it exists, or create new)

**Changes:** Create dynamic start/stop/resume button

```typescript
'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Square, Play, CheckCircle } from 'lucide-react';
import { demoApiClient } from '@/lib/api-client';

interface StopProcessingButtonProps {
  processingState: 'running' | 'stopped' | 'complete' | 'not_started';
  canResume: boolean;
  onStateChange: () => void;  // Callback to refresh status after stop/resume
}

export function StartStopResumeButton({
  processingState,
  canResume,
  onStateChange
}: StopProcessingButtonProps) {
  const [isLoading, setIsLoading] = useState(false);

  // Determine button appearance based on state
  const getButtonConfig = () => {
    switch (processingState) {
      case 'running':
        return {
          text: 'Stop Processing',
          icon: Square,
          color: 'bg-red-600 hover:bg-red-700 dark:bg-red-700 dark:hover:bg-red-800',
          action: handleStop
        };
      case 'stopped':
        return {
          text: 'Resume Processing',
          icon: Play,
          color: 'bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800',
          action: handleResume
        };
      case 'complete':
        return {
          text: 'Processing Complete',
          icon: CheckCircle,
          color: 'bg-gray-400 dark:bg-gray-600 cursor-not-allowed',
          action: null
        };
      case 'not_started':
        return {
          text: 'Start Processing',
          icon: Play,
          color: 'bg-green-600 hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-800',
          action: handleStart
        };
    }
  };

  const handleStop = async () => {
    setIsLoading(true);
    try {
      await demoApiClient.stopProcessing();
      onStateChange();  // Refresh status
    } catch (error) {
      console.error('[StopButton] Error stopping processing:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResume = async () => {
    setIsLoading(true);
    try {
      await demoApiClient.resumeProcessing();
      onStateChange();  // Refresh status
    } catch (error) {
      console.error('[StopButton] Error resuming processing:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStart = async () => {
    // Trigger demo initialization or manual processing start
    // Implementation depends on existing start flow
    console.log('[StopButton] Start processing clicked');
  };

  const config = getButtonConfig();
  const Icon = config.icon;
  const isDisabled = processingState === 'complete' || isLoading;

  return (
    <motion.button
      onClick={config.action || undefined}
      disabled={isDisabled}
      className={`${config.color} text-white font-medium py-2 px-4 rounded-lg flex items-center gap-2 transition-colors`}
      whileHover={isDisabled ? {} : { scale: 1.02 }}
      whileTap={isDisabled ? {} : { scale: 0.98 }}
    >
      <Icon className="w-5 h-5" />
      <span>{isLoading ? 'Processing...' : config.text}</span>
    </motion.button>
  );
}
```

---

#### 4.4 Frontend - Integrate Button into Dashboard

**File:** `frontend/app/patient/page.tsx` (or wherever dashboard renders)

**Changes:** Add Start/Stop/Resume button to dashboard

```typescript
// Import component
import { StartStopResumeButton } from './components/StartStopResumeButton';

// In dashboard render, add button above session cards

const { processingState, canResume } = useSessionData();  // Get from context

<div className="mb-6 flex justify-end">
  <StartStopResumeButton
    processingState={processingState}
    canResume={canResume}
    onStateChange={refreshStatus}
  />
</div>
```

---

### Success Criteria

#### Automated Verification:
- [ ] Resume endpoint exists: `curl -X POST http://localhost:8000/api/demo/resume`
- [ ] TypeScript compiles: `cd frontend && npm run build`
- [ ] Button component imports successfully

#### Manual Verification:
- [ ] Run demo, verify button shows "Stop Processing" (red) while Wave 1/Wave 2 running
- [ ] Click stop button, verify processing stops and button changes to "Resume Processing" (green)
- [ ] Click resume button, verify processing continues from incomplete session
- [ ] Wait for all sessions to complete, verify button shows "Processing Complete" (gray, disabled)
- [ ] Verify roadmap generation stops when stop button clicked
- [ ] Verify roadmap generation resumes when resume button clicked

**Implementation Note:** After completing Phase 4, test stop/resume flow end-to-end in browser before proceeding to Phase 5.

---

## Phase 5: Orchestration & Testing

### Overview
Wire all components together with orchestration script that runs after Wave 2, generates insights, builds context based on strategy, and generates roadmap.

### Changes Required

#### 5.1 Roadmap Orchestration Script

**File:** `backend/scripts/generate_roadmap.py` (NEW)

**Changes:** Create orchestration script

```python
"""
Roadmap Generation Orchestration Script

Runs after each Wave 2 analysis completes.
Generates session insights, builds compacted context, and generates roadmap.

Usage:
    python scripts/generate_roadmap.py <patient_id> <session_id>

Example:
    python scripts/generate_roadmap.py 550e8400-e29b-41d4-a716-446655440000 650e8400-e29b-41d4-a716-446655440001
"""

import sys
import os
import json
from uuid import UUID
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.session_insights_summarizer import SessionInsightsSummarizer
from app.services.roadmap_generator import RoadmapGenerator
from app.database import get_supabase_client


def generate_roadmap_for_session(patient_id: str, session_id: str):
    """
    Generate roadmap after a session's Wave 2 completes.

    Steps:
    1. Generate session insights from deep_analysis
    2. Build context based on compaction strategy
    3. Generate roadmap
    4. Update database (patient_roadmap + roadmap_versions)
    """
    supabase = get_supabase_client()

    print(f"\n{'='*60}")
    print(f"ROADMAP GENERATION - Session {session_id}")
    print(f"{'='*60}\n")

    # Step 1: Get session data
    print("[Step 1/5] Fetching session data...")
    session_result = supabase.table("therapy_sessions") \
        .select("*") \
        .eq("id", session_id) \
        .execute()

    if not session_result.data:
        print(f"[ERROR] Session {session_id} not found")
        return

    current_session = session_result.data[0]

    # Verify Wave 2 complete
    if not current_session.get("prose_analysis"):
        print(f"[ERROR] Session {session_id} Wave 2 not complete (no prose_analysis)")
        return

    print(f"  ✓ Session fetched: {current_session.get('session_date')}")

    # Step 2: Generate session insights
    print("\n[Step 2/5] Generating session insights (GPT-5.2)...")
    summarizer = SessionInsightsSummarizer()

    insights = summarizer.generate_insights(
        session_id=UUID(session_id),
        deep_analysis=current_session["deep_analysis"],
        confidence_score=current_session.get("analysis_confidence", 0.85)
    )

    print(f"  ✓ Generated {len(insights)} insights")
    for i, insight in enumerate(insights, 1):
        print(f"    {i}. {insight[:80]}...")

    # Step 3: Build context based on compaction strategy
    print("\n[Step 3/5] Building context (compaction strategy: {})...".format(
        os.getenv("ROADMAP_COMPACTION_STRATEGY", "hierarchical")
    ))

    context = build_context(patient_id, session_id, insights, supabase)

    print(f"  ✓ Context built ({len(json.dumps(context))} characters)")

    # Step 4: Generate roadmap
    print("\n[Step 4/5] Generating roadmap (GPT-5.2)...")

    # Count sessions analyzed
    all_sessions_result = supabase.table("therapy_sessions") \
        .select("id, prose_analysis") \
        .eq("patient_id", patient_id) \
        .execute()

    sessions_with_wave2 = [s for s in all_sessions_result.data if s.get("prose_analysis")]
    sessions_analyzed = len(sessions_with_wave2)
    total_sessions = len(all_sessions_result.data)

    generator = RoadmapGenerator()

    # Build current session data for roadmap
    current_session_data = {
        "wave1": {
            "session_id": session_id,
            "session_date": current_session["session_date"],
            "mood_score": current_session["mood_score"],
            "topics": current_session["topics"],
            "action_items": current_session["action_items"],
            "technique": current_session["technique"],
            "summary": current_session["summary"],
        },
        "wave2": current_session["deep_analysis"],
        "insights": insights
    }

    result = generator.generate_roadmap(
        patient_id=UUID(patient_id),
        current_session=current_session_data,
        context=context,
        sessions_analyzed=sessions_analyzed,
        total_sessions=total_sessions
    )

    roadmap_data = result["roadmap"]
    metadata = result["metadata"]

    print(f"  ✓ Roadmap generated")
    print(f"    Summary: {roadmap_data['summary'][:80]}...")
    print(f"    Achievements: {len(roadmap_data['achievements'])} items")
    print(f"    Current Focus: {len(roadmap_data['currentFocus'])} items")
    print(f"    Sections: {len(roadmap_data['sections'])} sections")

    # Step 5: Update database
    print("\n[Step 5/5] Updating database...")

    # Get current version number
    versions_result = supabase.table("roadmap_versions") \
        .select("version") \
        .eq("patient_id", patient_id) \
        .order("version", desc=True) \
        .limit(1) \
        .execute()

    current_version = versions_result.data[0]["version"] if versions_result.data else 0
    new_version = current_version + 1

    # Insert new version
    supabase.table("roadmap_versions").insert({
        "patient_id": patient_id,
        "version": new_version,
        "roadmap_data": roadmap_data,
        "metadata": metadata,
        "generation_context": context,  # Store for debugging
        "cost": estimate_cost(context, roadmap_data),  # Estimate based on tokens
        "generation_duration_ms": metadata["generation_duration_ms"]
    }).execute()

    print(f"  ✓ Version {new_version} saved to roadmap_versions")

    # Upsert to patient_roadmap (latest version)
    supabase.table("patient_roadmap").upsert({
        "patient_id": patient_id,
        "roadmap_data": roadmap_data,
        "metadata": metadata,
        "updated_at": datetime.now().isoformat()
    }, on_conflict="patient_id").execute()

    print(f"  ✓ Latest roadmap updated in patient_roadmap")

    print(f"\n{'='*60}")
    print(f"ROADMAP GENERATION COMPLETE")
    print(f"  Patient: {patient_id}")
    print(f"  Version: {new_version}")
    print(f"  Sessions analyzed: {sessions_analyzed}/{total_sessions}")
    print(f"  Strategy: {metadata['compaction_strategy']}")
    print(f"  Duration: {metadata['generation_duration_ms']}ms")
    print(f"{'='*60}\n")


def build_context(patient_id: str, current_session_id: str, current_insights: list[str], supabase) -> dict:
    """
    Build context based on compaction strategy.

    Returns context dict with structure specific to the selected strategy.
    """
    strategy = os.getenv("ROADMAP_COMPACTION_STRATEGY", "hierarchical").lower()

    if strategy == "full":
        return build_full_context(patient_id, current_session_id, supabase)
    elif strategy == "progressive":
        return build_progressive_context(patient_id, current_session_id, supabase)
    elif strategy == "hierarchical":
        return build_hierarchical_context(patient_id, current_session_id, current_insights, supabase)
    else:
        raise ValueError(f"Unknown compaction strategy: {strategy}")


def build_full_context(patient_id: str, current_session_id: str, supabase) -> dict:
    """Build full context (all previous sessions' raw data)"""
    # Get all previous sessions (excluding current)
    sessions_result = supabase.table("therapy_sessions") \
        .select("*") \
        .eq("patient_id", patient_id) \
        .neq("id", current_session_id) \
        .order("session_date") \
        .execute()

    # Build nested context (same structure as Wave 2)
    cumulative_context = None

    for session in sessions_result.data:
        session_context = {
            f"session_{session['id'][:8]}_wave1": {
                "session_id": session["id"],
                "session_date": session["session_date"],
                "mood_score": session["mood_score"],
                "topics": session["topics"],
                "summary": session["summary"]
            },
            f"session_{session['id'][:8]}_wave2": session["deep_analysis"]
        }

        if cumulative_context:
            session_context["previous_context"] = cumulative_context

        cumulative_context = session_context

    return cumulative_context or {}


def build_progressive_context(patient_id: str, current_session_id: str, supabase) -> dict:
    """Build progressive context (previous roadmap only)"""
    # Get previous roadmap
    roadmap_result = supabase.table("patient_roadmap") \
        .select("roadmap_data") \
        .eq("patient_id", patient_id) \
        .execute()

    if roadmap_result.data:
        return {"previous_roadmap": roadmap_result.data[0]["roadmap_data"]}
    else:
        return {}  # First roadmap, no previous context


def build_hierarchical_context(patient_id: str, current_session_id: str, current_insights: list[str], supabase) -> dict:
    """Build hierarchical context (tiered summaries)"""
    # Implementation of hierarchical tier management
    # This is the most complex strategy - manages Tier 1, Tier 2, Tier 3 summaries

    # Get all previous sessions with insights
    sessions_result = supabase.table("therapy_sessions") \
        .select("id, session_date, deep_analysis") \
        .eq("patient_id", patient_id) \
        .neq("id", current_session_id) \
        .order("session_date") \
        .execute()

    sessions = sessions_result.data
    num_sessions = len(sessions)

    context = {
        "tier1_summaries": {},
        "tier2_summaries": {},
        "tier3_summary": None,
        "previous_roadmap": None
    }

    # Tier 1: Keep last 4 sessions as detailed insights
    # Tier 2: Every 5 sessions → compact to paragraph
    # Tier 3: Every 10 sessions → compact to journey arc

    # ... detailed tier management logic ...
    # This would be a substantial implementation
    # For MVP, can start with simplified version

    return context


def estimate_cost(context: dict, roadmap: dict) -> float:
    """Estimate generation cost based on token counts"""
    # Rough estimate: ~$0.003-0.020 depending on context size
    context_size = len(json.dumps(context))
    roadmap_size = len(json.dumps(roadmap))

    # Approximate tokens (1 token ≈ 4 characters)
    input_tokens = context_size / 4
    output_tokens = roadmap_size / 4

    # GPT-5.2 pricing
    input_cost = (input_tokens / 1_000_000) * 1.75
    output_cost = (output_tokens / 1_000_000) * 14.00

    return round(input_cost + output_cost, 6)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/generate_roadmap.py <patient_id> <session_id>")
        sys.exit(1)

    patient_id = sys.argv[1]
    session_id = sys.argv[2]

    generate_roadmap_for_session(patient_id, session_id)
```

---

#### 5.2 Integrate Roadmap Generation into Wave 2 Flow

**File:** `backend/app/routers/demo.py`

**Changes:** Trigger roadmap generation after Wave 2 completes

```python
# In run_wave2_analysis_background function (around line 280), add roadmap trigger

async def run_wave2_analysis_background(patient_id: str):
    """Run Wave 2 analysis in background subprocess"""
    try:
        # ... existing Wave 2 execution ...

        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "scripts/seed_wave2_analysis.py",
            patient_id,
            # ... existing args ...
        )

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            analysis_status_dict["wave2_complete"] = True

            # NEW: Trigger roadmap generation for each completed session
            print(f"[DEMO] Wave 2 complete, triggering roadmap generation...")

            # Get all sessions with Wave 2 complete
            sessions_result = supabase.table("therapy_sessions") \
                .select("id, prose_analysis") \
                .eq("patient_id", patient_id) \
                .order("session_date") \
                .execute()

            # Generate roadmap for last completed session
            completed_sessions = [s for s in sessions_result.data if s.get("prose_analysis")]
            if completed_sessions:
                last_session_id = completed_sessions[-1]["id"]

                # Run roadmap generation in subprocess
                roadmap_process = await asyncio.create_subprocess_exec(
                    sys.executable,
                    "scripts/generate_roadmap.py",
                    patient_id,
                    last_session_id,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )

                roadmap_stdout, roadmap_stderr = await roadmap_process.communicate()

                if roadmap_process.returncode == 0:
                    print(f"[DEMO] Roadmap generated successfully for session {last_session_id}")
                else:
                    print(f"[DEMO] Roadmap generation failed: {roadmap_stderr.decode()}")

    except Exception as e:
        print(f"[ERROR] Wave 2 background task failed: {e}")
```

---

#### 5.3 End-to-End Testing Script

**File:** `backend/tests/test_roadmap_full_flow.py` (NEW)

**Changes:** Create comprehensive test script

```python
"""
End-to-End Roadmap Generation Test

Tests full flow:
1. Create demo patient
2. Upload 3 sessions
3. Run Wave 1 analysis
4. Run Wave 2 analysis
5. Verify roadmap generated after each Wave 2
6. Verify counter increments (1/3, 2/3, 3/3)
7. Verify all 3 compaction strategies work
"""

import asyncio
import os
from app.database import get_supabase_client


async def test_roadmap_full_flow():
    """Test complete roadmap generation flow"""

    print("\n" + "="*80)
    print("ROADMAP GENERATION - END-TO-END TEST")
    print("="*80 + "\n")

    # Test each compaction strategy
    strategies = ["full", "progressive", "hierarchical"]

    for strategy in strategies:
        print(f"\n{'='*80}")
        print(f"TESTING STRATEGY: {strategy.upper()}")
        print(f"{'='*80}\n")

        # Set env var
        os.environ["ROADMAP_COMPACTION_STRATEGY"] = strategy

        # Run test flow
        await test_strategy(strategy)

    print("\n" + "="*80)
    print("ALL TESTS COMPLETE")
    print("="*80 + "\n")


async def test_strategy(strategy: str):
    """Test a single compaction strategy"""
    # Implementation of full test flow
    # 1. Create demo patient
    # 2. Upload 3 mock sessions
    # 3. Run Wave 1, Wave 2, Roadmap for each
    # 4. Verify roadmap updates correctly
    # 5. Verify version history
    pass


if __name__ == "__main__":
    asyncio.run(test_roadmap_full_flow())
```

---

### Success Criteria

#### Automated Verification:
- [ ] Orchestration script runs successfully: `python backend/scripts/generate_roadmap.py <patient_id> <session_id>`
- [ ] All 3 compaction strategies execute: Test with `ROADMAP_COMPACTION_STRATEGY=full`, `progressive`, `hierarchical`
- [ ] Database writes succeed: Check `roadmap_versions` table has new rows after generation
- [ ] Cost estimation works: Verify `cost` field in `roadmap_versions` has reasonable value

#### Manual Verification:
- [ ] Run full demo (10 sessions), verify roadmap generates after each Wave 2 completion
- [ ] Verify roadmap versions stored (10 versions in `roadmap_versions` table)
- [ ] Verify "Your Journey" card updates 10 times (counter shows 1/10, 2/10, ..., 10/10)
- [ ] Switch compaction strategy mid-demo (change env var), verify new patient uses new strategy
- [ ] Test stop/resume: Stop after Session 5, resume, verify roadmap generation continues
- [ ] Inspect version history in database, verify each version shows cumulative progress

**Implementation Note:** This is the final phase. After completing all automated and manual verification, the feature is ready for production deployment.

---

## Testing Strategy

### Unit Tests

**Session Insights Summarizer Tests:**
```python
# backend/tests/test_session_insights_summarizer.py
def test_generate_insights_returns_3_to_5_bullets()
def test_insights_format_is_valid()
def test_handles_empty_deep_analysis()
def test_uses_correct_model()
```

**Roadmap Generator Tests:**
```python
# backend/tests/test_roadmap_generator.py
def test_full_context_strategy()
def test_progressive_strategy()
def test_hierarchical_strategy()
def test_roadmap_structure_validation()
def test_env_var_strategy_selection()
```

**Context Building Tests:**
```python
# backend/tests/test_roadmap_context.py
def test_build_full_context()
def test_build_progressive_context()
def test_build_hierarchical_context()
def test_tier_compaction_logic()
```

### Integration Tests

**Full Flow Test:**
1. Create demo patient
2. Upload 10 sessions
3. Run Wave 1 → Wave 2 → Roadmap for all sessions
4. Verify 10 roadmap versions created
5. Verify each roadmap builds on previous
6. Verify counter increments correctly

**Strategy Comparison Test:**
1. Create 3 demo patients
2. Set different compaction strategy for each
3. Upload same 10 sessions to all 3
4. Compare roadmap outputs (quality, cost, token usage)
5. Verify all strategies produce valid roadmaps

### Manual Testing Steps

**UI Testing:**
1. Load patient dashboard
2. Verify "Your Journey" card shows empty state
3. Upload 6 sessions via UI
4. Watch card update after each Wave 2 completion
5. Verify loading overlay appears (1000ms spinner)
6. Verify counter increments (1/6, 2/6, ..., 6/6)
7. Click card, verify expanded modal shows full roadmap
8. Verify counter also appears in modal

**Stop/Resume Testing:**
1. Start demo with 10 sessions
2. After Session 3 Wave 2 completes, click "Stop Processing"
3. Verify button changes to "Resume Processing"
4. Verify roadmap shows "Based on 3 out of 10 sessions"
5. Wait 30 seconds, verify no more updates
6. Click "Resume Processing"
7. Verify processing continues from Session 4
8. Verify roadmap continues updating (4/10, 5/10, ...)

**Compaction Strategy Testing:**
1. Set `ROADMAP_COMPACTION_STRATEGY=full`
2. Run demo, inspect roadmap content
3. Set `ROADMAP_COMPACTION_STRATEGY=progressive`
4. Create new demo patient, run demo
5. Compare roadmap quality between strategies
6. Set `ROADMAP_COMPACTION_STRATEGY=hierarchical`
7. Create new demo patient, run demo
8. Compare all 3 roadmaps for quality vs cost trade-off

---

## Performance Considerations

### Token Usage by Strategy

**Full Context (Strategy 1):**
- Session 1: ~5K input tokens
- Session 10: ~80K input tokens
- Total (10 sessions): ~425K input tokens
- Cost: ~$0.80 per demo

**Progressive Summarization (Strategy 2):**
- All sessions: ~7K input tokens (constant)
- Total (10 sessions): ~70K input tokens
- Cost: ~$0.25 per demo

**Hierarchical (Strategy 3):**
- All sessions: ~10K-12K input tokens
- Total (10 sessions): ~110K input tokens
- Cost: ~$0.35 per demo

### Latency

**Per Roadmap Generation:**
- Session Insights: 1-2 seconds (GPT-5.2 API call)
- Roadmap Generation: 2-3 seconds (GPT-5.2 API call)
- Database Writes: <100ms
- **Total: ~3-5 seconds per roadmap**

**Full Demo (10 sessions):**
- Wave 1: ~60 seconds (parallel processing)
- Wave 2: ~600 seconds (sequential processing, 60s per session)
- Roadmaps: ~50 seconds (5s per roadmap × 10 sessions)
- **Total: ~11-12 minutes** (vs 10 minutes without roadmaps)

### Database Storage

**Per Patient:**
- `patient_roadmap`: ~5KB (latest roadmap)
- `roadmap_versions`: ~5KB × N versions
- **10 sessions: ~55KB total**

**Scalability:**
- 1000 patients × 10 sessions = ~55MB
- Postgres JSONB indexes: fast queries
- Version history cleanup: Delete versions older than 90 days (optional)

---

## Migration Notes

### Database Migration

**Apply migration:**
```bash
cd backend
supabase migration up
```

**Verify tables:**
```sql
SELECT * FROM patient_roadmap LIMIT 1;
SELECT * FROM roadmap_versions LIMIT 1;
```

**Rollback (if needed):**
```bash
supabase migration down
```

### Environment Variables

**Add to `backend/.env`:**
```env
# Roadmap Configuration
ROADMAP_COMPACTION_STRATEGY=hierarchical  # full | progressive | hierarchical
```

**Add to `frontend/.env.local`:**
```env
# No new frontend env vars needed (reuses existing polling config)
```

### Code Deployment

**Backend:**
1. Deploy new services: `session_insights_summarizer.py`, `roadmap_generator.py`
2. Deploy orchestration script: `scripts/generate_roadmap.py`
3. Update `demo.py` with roadmap triggers
4. Apply database migration

**Frontend:**
1. Deploy updated `NotesGoalsCard.tsx` with API integration
2. Deploy `StartStopResumeButton.tsx` component
3. Update `api-client.ts` with roadmap endpoint
4. Update `SessionDataContext.tsx` with roadmap state

### Backward Compatibility

**Existing Features:**
- ✅ Wave 1/Wave 2 analysis: No changes, continues working
- ✅ Session cards: No changes, continues working
- ✅ Stop button: Enhanced to Start/Stop/Resume, backward compatible

**New Features:**
- ✅ "Your Journey" card: Gracefully shows empty state if no roadmap exists
- ✅ Roadmap generation: Only runs for new sessions after deployment
- ✅ Existing patients: Will generate roadmaps retroactively if Wave 2 re-runs

---

## References

**Original Requirements:**
- User request: "Your Journey card should update after each Wave 2 completes with cumulative context"
- Session log: `.claude/SESSION_LOG.md`
- Project documentation: `Project MDs/TheraBridge.md`

**Related Implementation Plans:**
- Wave 2 Deep Analysis: `thoughts/shared/plans/2025-12-XX-deep-analysis.md` (if exists)
- LoadingOverlay System: `frontend/app/patient/components/LoadingOverlay.tsx`
- Polling System: `frontend/app/patient/lib/usePatientSessions.ts`

**Model Configuration:**
- `backend/app/config/model_config.py` - GPT-5 series model assignments
- GPT-5.2 used for insights + roadmap generation (maximum quality)

**Similar Implementations:**
- Wave 2 cumulative context: `backend/scripts/seed_wave2_analysis.py:105-143`
- Session card loading overlay: `frontend/app/patient/components/SessionCard.tsx:562`
- Polling detection: `frontend/app/patient/lib/usePatientSessions.ts:48-90`

---

## Future Features & Enhancements

*This section documents improvements for future implementation. See `Project MDs/TheraBridge.md` for full backlog.*

### High Priority

**SSE Real-Time Updates**
- Fix database-backed event queue for subprocess isolation
- Test SSE in Railway production environment
- Enable `NEXT_PUBLIC_SSE_ENABLED=true` flag
- Location: `backend/app/services/pipeline_logger.py`, `frontend/app/patient/components/WaveCompletionBridge.tsx`
- Estimated: 4-6 hours
- Related: Future PR #4

### Medium Priority

**Wave 2 Context Compaction**
- Apply progressive summarization to Wave 2 (currently uses full nested context)
- Reduce token usage from ~50K-80K to ~10K-15K by Session 10
- Saves ~$0.10 per demo run
- Location: `backend/scripts/seed_wave2_analysis.py:105-143`
- Estimated: 2-3 hours

**Roadmap Regeneration API**
- Add `POST /api/patients/{id}/roadmap/regenerate` endpoint
- Allow manual roadmap regeneration with different strategies
- Useful for experimentation and debugging
- Location: `backend/app/routers/roadmap.py` (new file)
- Estimated: 1-2 hours

### Low Priority

**Journey-Optimized Roadmap Structure (Option B)**
- Alternative roadmap structure with milestones, trajectories, progress dimensions
- Requires frontend redesign (new UI components)
- Better for longitudinal tracking than current section-based approach
- Location: `frontend/app/patient/components/NotesGoalsCard.tsx`
- Estimated: 6-8 hours
- Details:
  ```typescript
  {
    summary: string,  // Journey narrative
    milestones: [{session_number, date, description}],
    progress_dimensions: [{dimension, baseline, current, trajectory}],
    current_focus: string[],
    next_steps: string[],
    therapist_notes: string
  }
  ```

**Roadmap Export Features**
- PDF export of full roadmap
- Email summaries to therapists
- Weekly progress reports
- Location: `backend/app/services/roadmap_exporter.py` (new service)
- Estimated: 4-6 hours

**UI Compaction Strategy Toggle**
- Allow users to switch compaction strategies via UI (not just env var)
- Compare roadmap outputs side-by-side
- Location: `frontend/app/patient/components/RoadmapSettings.tsx` (new component)
- Estimated: 3-4 hours

**Extended LoadingOverlay Improvements**
- Increase overlay duration to 1500ms (more visible)
- Add fade-in animation (currently instant)
- Add progress bar (show which session is processing)
- Location: `frontend/app/patient/components/LoadingOverlay.tsx`
- Estimated: 2-3 hours

---

*End of Implementation Plan*
