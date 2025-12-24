# Implementation Plan: SessionDetail UI Improvements + Wave 1 Action Summarization

**Date**: 2026-01-07
**PR**: #1 (Phase 1C - Extended Scope)
**Complexity**: High (Full-stack: Frontend + Backend + Database)
**Estimated Duration**: 2-3 hours

---

## Overview

This implementation adds multiple UI improvements to SessionDetail and introduces a new Wave 1 LLM call for action items summarization. The changes enhance the user experience with better mood visualization, technique definitions, improved navigation, and condensed action item display in SessionCards.

### Objectives

1. **Display numeric mood score** next to custom emoji in SessionDetail
2. **Show technique definitions** below technique names in SessionDetail
3. **Replace "Back to Dashboard" button** with X icon (top-right corner)
4. **Add theme toggle button** to SessionDetail header
5. **Create 45-char action items summary** via new Wave 1 LLM call
6. **Update SessionCard** to display condensed action summary as second bullet

---

## Architecture Overview

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ NEW: Wave 1 Action Items Summarization                          │
├─────────────────────────────────────────────────────────────────┤
│ topic_extractor.py generates 2 verbose action items             │
│          ↓                                                      │
│ action_items_summarizer.py creates 45-char summary             │
│          ↓                                                      │
│ Database: action_items_summary field                            │
│          ↓                                                      │
│ API: Returns action_items_summary in session response          │
│          ↓                                                      │
│ Frontend: SessionCard displays summary as second bullet        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ NEW: Technique Definitions                                      │
├─────────────────────────────────────────────────────────────────┤
│ technique_library.json (existing)                               │
│          ↓                                                      │
│ API: Lookup definition during session fetch                    │
│          ↓                                                      │
│ Response: technique_definition field added                      │
│          ↓                                                      │
│ SessionDetail: Display definition below technique name         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ NEW: Numeric Mood Score Display                                 │
├─────────────────────────────────────────────────────────────────┤
│ Database: mood_score (0.0-10.0) from Wave 1                    │
│          ↓                                                      │
│ API: Returns mood_score in session response                    │
│          ↓                                                      │
│ Frontend: Map numeric score → categorical emoji                │
│          ↓                                                      │
│ SessionDetail: Display emoji + numeric score (e.g., "😊 7.5")  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Backend Changes

### 1.1 Database Migration - Add action_items_summary Field

**File**: Create new migration file
**Path**: `/backend/supabase/migrations/010_add_action_items_summary.sql`

**Content**:
```sql
-- Migration: Add action_items_summary field for condensed action display
-- Created: 2026-01-07
-- Description: Stores 45-character max summary combining both action items

ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS action_items_summary TEXT;

COMMENT ON COLUMN therapy_sessions.action_items_summary IS
'AI-generated 45-character max summary combining both action items for compact display';
```

**Verification Command**:
```sql
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'therapy_sessions'
AND column_name = 'action_items_summary';
```

---

### 1.2 Create Action Items Summarizer Service

**File**: Create new service
**Path**: `/backend/app/services/action_items_summarizer.py`

**Content**:
```python
"""
Action Items Summarizer Service
Condenses 2 verbose action items into a single 45-character phrase.
Uses GPT-5-nano for efficient, cost-effective summarization.
"""

import os
import logging
from typing import List
from openai import AsyncOpenAI
from datetime import datetime
from pydantic import BaseModel

from app.config.model_config import get_model_name

logger = logging.getLogger(__name__)


class ActionItemsSummary(BaseModel):
    """Dataclass for action items summary result"""
    summary: str
    character_count: int
    original_items: List[str]
    summarized_at: datetime


class ActionItemsSummarizer:
    """
    Summarizes two verbose action items into a single 45-character phrase.

    Uses GPT-5-nano for cost-effective summarization while maintaining
    the core meaning of both action items.
    """

    def __init__(self):
        """Initialize the summarizer with OpenAI client"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = AsyncOpenAI(api_key=api_key)

        # Use GPT-5-nano for efficient summarization
        self.model = get_model_name("action_summary", override_model=None)
        logger.info(f"Initialized ActionItemsSummarizer with model: {self.model}")

    async def summarize_action_items(
        self,
        action_items: List[str],
        session_id: str = None
    ) -> ActionItemsSummary:
        """
        Generate a 45-character max summary from 2 action items.

        Args:
            action_items: List of 2 action item strings
            session_id: Optional session ID for logging

        Returns:
            ActionItemsSummary with condensed phrase

        Raises:
            ValueError: If action_items doesn't have exactly 2 items
        """
        if len(action_items) != 2:
            raise ValueError(f"Expected 2 action items, got {len(action_items)}")

        log_prefix = f"Session {session_id}: " if session_id else ""
        logger.info(f"📝 {log_prefix}Generating action items summary...")

        # Construct prompt
        prompt = self._build_prompt(action_items)

        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for consistent, concise output
                max_tokens=30,    # ~45 chars = ~15 tokens, give buffer
            )

            # Extract summary
            summary = response.choices[0].message.content.strip()

            # Truncate if over 45 characters (safety check)
            if len(summary) > 45:
                logger.warning(f"📝 {log_prefix}Summary exceeded 45 chars ({len(summary)}), truncating")
                summary = summary[:42] + "..."

            char_count = len(summary)

            logger.info(
                f"✅ {log_prefix}Action items summary complete: "
                f"'{summary}' ({char_count} chars)"
            )

            return ActionItemsSummary(
                summary=summary,
                character_count=char_count,
                original_items=action_items,
                summarized_at=datetime.utcnow()
            )

        except Exception as e:
            logger.error(f"❌ {log_prefix}Action items summarization failed: {str(e)}")
            raise

    def _get_system_prompt(self) -> str:
        """System prompt for GPT-5-nano summarization"""
        return """You are an expert at condensing therapy action items into ultra-brief phrases.

Your task: Combine TWO action items into ONE phrase of MAXIMUM 45 characters.

Requirements:
- Capture the essence of BOTH action items
- Use action verbs (practice, schedule, talk, write, etc.)
- Be specific enough to be meaningful
- Maximum 45 characters (strict limit)
- No punctuation at the end
- Conversational, patient-friendly tone

Examples:
Input: ["Practice TIPP skills when feeling overwhelmed", "Schedule psychiatrist appointment"]
Output: "Practice TIPP & schedule psychiatrist"

Input: ["Write down 3 daily accomplishments before bed", "Reach out to one friend this week"]
Output: "Track wins & reach out to friend"

Input: ["Use wise mind skill during family conflict", "Complete CBT thought record worksheet"]
Output: "Use wise mind & complete worksheet"

Input: ["Apply radical acceptance when stuck on ex-partner thoughts", "Practice opposite action for urge to isolate"]
Output: "Accept & practice opposite action"

Return ONLY the summary phrase, nothing else."""

    def _build_prompt(self, action_items: List[str]) -> str:
        """Build the user prompt with the two action items"""
        return f"""Condense these TWO action items into ONE phrase (max 45 characters):

1. {action_items[0]}
2. {action_items[1]}

Return only the condensed phrase."""
```

**Key Features**:
- Uses `gpt-5-nano` (cheapest model, sufficient for simple summarization)
- Strict 45-character limit with truncation safety
- Verbose logging matching Wave 1 format
- Pydantic dataclass for structured output
- Temperature 0.3 for consistent results

---

### 1.3 Update Model Configuration

**File**: `/backend/app/config/model_config.py`
**Action**: Add action_summary task to model assignments

**Location**: Line 86 (after "topic_extraction")

**Add**:
```python
"action_summary": "gpt-5-nano",  # Condense action items to 45 chars
```

**Updated Section** (lines 82-92):
```python
# Task-to-model assignments
TASK_MODEL_ASSIGNMENTS = {
    "mood_analysis": "gpt-5-nano",
    "topic_extraction": "gpt-5-mini",
    "action_summary": "gpt-5-nano",        # NEW
    "breakthrough_detection": "gpt-5",
    "deep_analysis": "gpt-5.2",
    "prose_generation": "gpt-5.2",
}
```

---

### 1.4 Integrate Summarization into Wave 1 Orchestration

**File**: `/backend/app/services/analysis_orchestrator.py`

**Changes Required**:

#### Change 1: Import ActionItemsSummarizer

**Location**: After line 30 (after TechniqueLibrary import)

**Add**:
```python
from app.services.action_items_summarizer import ActionItemsSummarizer, ActionItemsSummary
```

#### Change 2: Initialize Summarizer

**Location**: In `__init__` method, after line 89 (after self.technique_library)

**Add**:
```python
self.action_items_summarizer = ActionItemsSummarizer()
```

#### Change 3: Add Sequential Summarization After Topics

**Location**: After `_extract_topics()` method (around line 360)

**Add New Method**:
```python
async def _summarize_action_items(self, session_id: str, force: bool = False):
    """
    Generate 45-character summary of action items (runs after topic extraction).

    This runs SEQUENTIALLY after topic extraction to ensure verbose action items
    are not modified by including summarization in the same LLM call.
    """
    session = await self._get_session(session_id)

    # Skip if already summarized
    if session.get("action_items_summary") and not force:
        logger.info(f"↩️  Action items already summarized for session {session_id}, skipping")
        return

    # Skip if no action items yet (topic extraction not complete)
    if not session.get("action_items") or len(session.get("action_items", [])) < 2:
        logger.warning(
            f"⚠️  Cannot summarize action items for session {session_id}: "
            f"Need 2 action items, found {len(session.get('action_items', []))}"
        )
        return

    logger.info(f"📝 Generating action items summary for session {session_id}...")

    # Run summarization
    summary_result = await self.action_items_summarizer.summarize_action_items(
        action_items=session["action_items"][:2],  # Use first 2 items
        session_id=session_id
    )

    # Update session with summary
    self.db.table("therapy_sessions").update({
        "action_items_summary": summary_result.summary,
        "updated_at": "now()",
    }).eq("id", session_id).execute()

    logger.info(
        f"✅ Action items summary stored for session {session_id}: "
        f"'{summary_result.summary}' ({summary_result.character_count} chars)"
    )
```

#### Change 4: Update Wave 1 Execution to Include Sequential Summarization

**Location**: `_run_wave1()` method, after line 173 (after parallel execution)

**Modify Method** (lines 150-193):

**BEFORE**:
```python
async def _run_wave1(self, session_id: str, force: bool = False):
    """Run Wave 1 analysis: mood, topics, breakthrough (parallel)"""
    logger.info(f"🌊 Starting Wave 1 analysis for session {session_id}...")

    # Run all three analyses in parallel
    results = await asyncio.gather(
        self._run_with_retry(session_id, "mood", self._analyze_mood, force),
        self._run_with_retry(session_id, "topics", self._extract_topics, force),
        self._run_with_retry(session_id, "breakthrough", self._detect_breakthrough, force),
        return_exceptions=True
    )

    # Check if all succeeded
    if not await self._is_wave1_complete(session_id):
        logger.error(f"❌ Wave 1 incomplete for session {session_id}")
        return

    logger.info(f"✅ Wave 1 complete for session {session_id}")
```

**AFTER**:
```python
async def _run_wave1(self, session_id: str, force: bool = False):
    """Run Wave 1 analysis: mood, topics, breakthrough (parallel) + action summary (sequential)"""
    logger.info(f"🌊 Starting Wave 1 analysis for session {session_id}...")

    # Run mood, topics, breakthrough in parallel (unchanged)
    results = await asyncio.gather(
        self._run_with_retry(session_id, "mood", self._analyze_mood, force),
        self._run_with_retry(session_id, "topics", self._extract_topics, force),
        self._run_with_retry(session_id, "breakthrough", self._detect_breakthrough, force),
        return_exceptions=True
    )

    # Check if core Wave 1 analyses succeeded
    if not await self._is_wave1_complete(session_id):
        logger.error(f"❌ Wave 1 core analyses incomplete for session {session_id}")
        return

    logger.info(f"✅ Wave 1 core analyses complete for session {session_id}")

    # Run action items summarization SEQUENTIALLY (requires topic extraction to be complete)
    try:
        await self._run_with_retry(
            session_id,
            "action_summary",
            self._summarize_action_items,
            force
        )
    except Exception as e:
        # Don't fail Wave 1 if summarization fails (non-critical)
        logger.error(
            f"⚠️  Action items summarization failed for session {session_id}: {str(e)}. "
            f"Wave 1 will continue without summary."
        )

    logger.info(f"✅ Wave 1 complete (with summary) for session {session_id}")
```

**Key Changes**:
- Core Wave 1 (mood, topics, breakthrough) stays parallel
- Action summarization runs **after** topics complete (sequential)
- Summarization failure doesn't fail Wave 1 (try/except wrapper)
- Updated logging to reflect new step

---

### 1.5 Update Sessions API to Include Technique Definition

**File**: `/backend/app/routers/sessions.py`

**Changes Required**:

#### Change 1: Import TechniqueLibrary

**Location**: After line 15 (after other imports)

**Add**:
```python
from app.services.technique_library import TechniqueLibrary
```

#### Change 2: Initialize TechniqueLibrary

**Location**: After line 30 (after database client initialization)

**Add**:
```python
# Initialize technique library for definition lookup
technique_library = TechniqueLibrary()
```

#### Change 3: Add Definition Lookup to Session Response

**Location**: In `GET /api/sessions/` endpoint, after line 213 (after database query)

**Find** (around lines 213-225):
```python
response = (
    db.table("therapy_sessions")
    .select("*")
    .eq("patient_id", patient_id)
    .order("session_date", desc=True)
    .execute()
)

if response.data:
    return {"sessions": response.data}
else:
    return {"sessions": []}
```

**Replace With**:
```python
response = (
    db.table("therapy_sessions")
    .select("*")
    .eq("patient_id", patient_id)
    .order("session_date", desc=True)
    .execute()
)

if response.data:
    # Enrich sessions with technique definitions
    enriched_sessions = []
    for session in response.data:
        # Add technique definition if technique exists
        if session.get("technique"):
            try:
                technique_def = technique_library.get_technique_definition(
                    session["technique"]
                )
                session["technique_definition"] = technique_def
            except Exception as e:
                logger.warning(
                    f"Could not find definition for technique '{session.get('technique')}': {e}"
                )
                session["technique_definition"] = None
        else:
            session["technique_definition"] = None

        enriched_sessions.append(session)

    return {"sessions": enriched_sessions}
else:
    return {"sessions": []}
```

**Key Features**:
- Looks up technique definition from technique_library.json
- Adds `technique_definition` field to each session
- Graceful fallback: `None` if technique not found or lookup fails
- No breaking changes: existing fields unchanged

---

## Phase 2: Frontend Changes

### 2.1 Create Numeric Mood Score Mapper Utility

**File**: Create new utility
**Path**: `/frontend/lib/mood-mapper.ts`

**Content**:
```typescript
/**
 * Mood Mapper Utility
 * Maps numeric mood scores (0.0-10.0) to categorical mood types
 * for use with custom emoji rendering.
 */

export type MoodCategory = 'sad' | 'neutral' | 'happy';

/**
 * Maps a numeric mood score (0.0-10.0) to a categorical mood type.
 *
 * Ranges:
 * - 0.0-3.5: sad (distressed, severe symptoms)
 * - 4.0-6.5: neutral (mild symptoms to stable baseline)
 * - 7.0-10.0: happy (positive, thriving)
 *
 * @param score - Numeric mood score from 0.0 to 10.0
 * @returns Categorical mood type ('sad', 'neutral', or 'happy')
 */
export function mapNumericMoodToCategory(score: number | null | undefined): MoodCategory {
  // Handle null/undefined
  if (score === null || score === undefined) {
    return 'neutral'; // Default to neutral for missing data
  }

  // Clamp to valid range
  const clampedScore = Math.max(0, Math.min(10, score));

  // Map to categories
  if (clampedScore <= 3.5) {
    return 'sad';
  } else if (clampedScore <= 6.5) {
    return 'neutral';
  } else {
    return 'happy';
  }
}

/**
 * Formats a numeric mood score for display.
 *
 * @param score - Numeric mood score from 0.0 to 10.0
 * @returns Formatted string (e.g., "7.5") or "N/A" if missing
 */
export function formatMoodScore(score: number | null | undefined): string {
  if (score === null || score === undefined) {
    return 'N/A';
  }

  return score.toFixed(1);
}
```

---

### 2.2 Update Session Type to Include New Fields

**File**: `/frontend/app/patient/lib/types.ts`

**Location**: Session interface (around line 68-91)

**Add Fields** (after line 87, before closing brace):
```typescript
  // Mood analysis (Wave 1)
  mood_score?: number;              // Numeric 0.0-10.0 score
  mood_confidence?: number;         // AI confidence 0.0-1.0
  mood_rationale?: string;          // Clinical explanation
  mood_indicators?: string[];       // Key emotional indicators
  emotional_tone?: string;          // Overall emotional quality

  // Action items summary (Wave 1 sequential)
  action_items_summary?: string;    // 45-char max condensed phrase

  // Technique definition (from API enrichment)
  technique_definition?: string;    // 2-3 sentence definition
```

**Updated Interface** (lines 68-105):
```typescript
export interface Session {
  id: string;
  date: string;
  duration: string;
  therapist: string;
  mood: MoodType;
  topics: string[];
  strategy: string;
  actions: string[];
  milestone?: Milestone;
  transcript?: TranscriptEntry[];
  patientSummary?: string;
  deep_analysis?: DeepAnalysis;

  // Wave 1 AI Analysis
  summary?: string;
  action_items?: string[];
  technique?: string;
  extraction_confidence?: number;
  topics_extracted_at?: string;

  // Mood analysis (Wave 1) - NEW
  mood_score?: number;
  mood_confidence?: number;
  mood_rationale?: string;
  mood_indicators?: string[];
  emotional_tone?: string;

  // Action items summary (Wave 1 sequential) - NEW
  action_items_summary?: string;

  // Technique definition (from API enrichment) - NEW
  technique_definition?: string;

  // Wave 2 AI Analysis
  prose_analysis?: string;
  prose_generated_at?: string;
  deep_analyzed_at?: string;
}
```

---

### 2.3 Update Frontend Data Mapping in usePatientSessions

**File**: `/frontend/app/patient/lib/usePatientSessions.ts`

**Location**: `transformedSessions` mapping (around lines 235-265)

**Add Field Mappings** (after line 252, before closing brace):
```typescript
      // Mood analysis fields (Wave 1)
      mood_score: backendSession.mood_score,
      mood_confidence: backendSession.mood_confidence,
      mood_rationale: backendSession.mood_rationale,
      mood_indicators: backendSession.mood_indicators,
      emotional_tone: backendSession.emotional_tone,

      // Action items summary (Wave 1)
      action_items_summary: backendSession.action_items_summary,

      // Technique definition (API enrichment)
      technique_definition: backendSession.technique_definition,
```

**Updated Mapping** (lines 235-270):
```typescript
const transformedSessions: Session[] = backendSessions.map((backendSession) => {
  const sessionDate = new Date(backendSession.session_date);

  return {
    id: backendSession.id,
    date: sessionDate.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
    }),
    duration: `${backendSession.duration_minutes || 60} min`,
    therapist: 'Dr. Rodriguez',
    mood: mapMoodScore(backendSession.mood_score),
    topics: backendSession.topics || [],
    strategy: backendSession.technique || '',
    actions: backendSession.action_items || [],
    summary: backendSession.summary || '',
    transcript: backendSession.transcript || [],
    extraction_confidence: backendSession.extraction_confidence,
    topics_extracted_at: backendSession.topics_extracted_at,

    // Mood analysis fields (Wave 1) - NEW
    mood_score: backendSession.mood_score,
    mood_confidence: backendSession.mood_confidence,
    mood_rationale: backendSession.mood_rationale,
    mood_indicators: backendSession.mood_indicators,
    emotional_tone: backendSession.emotional_tone,

    // Action items summary (Wave 1) - NEW
    action_items_summary: backendSession.action_items_summary,

    // Technique definition (API enrichment) - NEW
    technique_definition: backendSession.technique_definition,

    // Wave 2 fields
    deep_analysis: backendSession.deep_analysis,
    prose_analysis: backendSession.prose_analysis,
    deep_analyzed_at: backendSession.deep_analyzed_at,
    prose_generated_at: backendSession.prose_generated_at,
  };
});
```

---

### 2.4 Update SessionCard to Use Action Items Summary

**File**: `/frontend/app/patient/components/SessionCard.tsx`

**Location**: Lines 72-76 (techniquesAndActions construction)

**BEFORE**:
```typescript
// Extract 1 strategy + 1 action (show both types)
const techniquesAndActions = [
  session.strategy,
  ...(session.actions.slice(0, 1))
].filter(Boolean);
```

**AFTER**:
```typescript
// Extract 1 strategy + 1 condensed action summary (45 chars max)
const techniquesAndActions = [
  session.strategy,
  session.action_items_summary || session.actions[0] || ''  // Use summary if available, fallback to first action
].filter(Boolean);
```

**Key Changes**:
- Primary: Uses `session.action_items_summary` (45-char AI-generated phrase)
- Fallback 1: Uses `session.actions[0]` if summary not available
- Fallback 2: Empty string if no actions at all
- Maintains backward compatibility

---

### 2.5 Update SessionDetail - Add Mood Score Display

**File**: `/frontend/app/patient/components/SessionDetail.tsx`

**Changes Required**:

#### Change 1: Import Mood Utilities

**Location**: After line 5 (after other imports)

**Add**:
```typescript
import { mapNumericMoodToCategory, formatMoodScore } from '../../../lib/mood-mapper';
import { renderMoodEmoji } from './SessionIcons';
```

#### Change 2: Add Mood Score Display Section

**Location**: Find the "Technique Used" section (search for "STRATEGY USED" or "technique")

**Typical Location**: Around line 200-250 (varies based on component structure)

**Add BEFORE the technique section**:
```typescript
{/* Mood Score Section */}
{session.mood_score !== undefined && session.mood_score !== null && (
  <div style={{
    marginBottom: '24px',
    paddingBottom: '20px',
    borderBottom: `1px solid ${borderColor}`,
  }}>
    <h3 style={{
      fontFamily: TYPOGRAPHY.sans,
      fontSize: '11px',
      fontWeight: 500,
      textTransform: 'uppercase',
      letterSpacing: '1px',
      color: mutedText,
      marginBottom: '12px',
    }}>
      Session Mood
    </h3>
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
    }}>
      {/* Custom emoji based on numeric score */}
      {renderMoodEmoji(
        mapNumericMoodToCategory(session.mood_score),
        28,
        isDark
      )}

      {/* Numeric score */}
      <span style={{
        fontFamily: TYPOGRAPHY.sans,
        fontSize: '18px',
        fontWeight: 600,
        color: text,
      }}>
        {formatMoodScore(session.mood_score)}
      </span>

      {/* Emotional tone (optional) */}
      {session.emotional_tone && (
        <span style={{
          fontFamily: TYPOGRAPHY.serif,
          fontSize: '14px',
          fontWeight: 400,
          color: mutedText,
          fontStyle: 'italic',
        }}>
          ({session.emotional_tone})
        </span>
      )}
    </div>
  </div>
)}
```

**Key Features**:
- Shows custom emoji (happy/neutral/sad) based on numeric score mapping
- Displays numeric score (e.g., "7.5")
- Optionally shows emotional tone (e.g., "hopeful, engaged")
- Conditional rendering (only shows if mood_score exists)
- Matches SessionDetail styling (typography, colors, spacing)

---

### 2.6 Update SessionDetail - Add Technique Definition Display

**File**: `/frontend/app/patient/components/SessionDetail.tsx`

**Location**: Find the technique display section (where `session.strategy` or `session.technique` is shown)

**BEFORE** (typical structure):
```typescript
<div>
  <h3 style={{...}}>STRATEGY USED</h3>
  <p style={{...}}>
    {session.strategy || session.technique}
  </p>
  <p style={{...}}>
    This therapeutic approach was applied during the session to address the identified concerns.
  </p>
</div>
```

**AFTER**:
```typescript
<div style={{
  marginBottom: '24px',
  paddingBottom: '20px',
  borderBottom: `1px solid ${borderColor}`,
}}>
  <h3 style={{
    fontFamily: TYPOGRAPHY.sans,
    fontSize: '11px',
    fontWeight: 500,
    textTransform: 'uppercase',
    letterSpacing: '1px',
    color: mutedText,
    marginBottom: '12px',
  }}>
    STRATEGY USED
  </h3>

  {/* Technique Name */}
  <p style={{
    fontFamily: TYPOGRAPHY.serif,
    fontSize: '16px',
    fontWeight: 600,
    color: accent,
    marginBottom: '8px',
  }}>
    {session.strategy || session.technique || 'Not specified'}
  </p>

  {/* Technique Definition (NEW) */}
  {session.technique_definition && (
    <p style={{
      fontFamily: TYPOGRAPHY.serif,
      fontSize: '14px',
      fontWeight: 400,
      lineHeight: 1.6,
      color: text,
      marginTop: '8px',
    }}>
      {session.technique_definition}
    </p>
  )}

  {/* Fallback for missing definition */}
  {!session.technique_definition && session.strategy && (
    <p style={{
      fontFamily: TYPOGRAPHY.serif,
      fontSize: '14px',
      fontWeight: 400,
      lineHeight: 1.6,
      color: mutedText,
      fontStyle: 'italic',
      marginTop: '8px',
    }}>
      Definition not available for this technique.
    </p>
  )}
</div>
```

**Key Changes**:
- **Removes** placeholder text "This therapeutic approach was applied..."
- **Adds** real technique definition from `session.technique_definition`
- Shows fallback message if definition not available
- Technique name styled in accent color (teal/purple)
- Definition styled in body text color for readability

---

### 2.7 Update SessionDetail - Replace Button with X Icon and Add Theme Toggle

**File**: `/frontend/app/patient/components/SessionDetail.tsx`

**Changes Required**:

#### Change 1: Import X Icon and ThemeToggle

**Location**: After line 5 (with other imports)

**Add**:
```typescript
import { X } from 'lucide-react';
import { ThemeToggle } from '../../../components/ui/theme-toggle';
```

#### Change 2: Update Header Section

**Location**: Find the header with "Back to Dashboard" button (around lines 110-120)

**BEFORE** (typical structure):
```typescript
<div style={{
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '20px 24px',
  borderBottom: `1px solid ${borderColor}`,
}}>
  <button
    onClick={onClose}
    className="flex items-center gap-2 text-[#5AB9B4] dark:text-[#a78bfa] hover:opacity-80 transition-colors"
  >
    <ArrowLeft className="w-5 h-5" />
    <span style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '14px', fontWeight: 500 }}>
      Back to Dashboard
    </span>
  </button>
</div>
```

**AFTER**:
```typescript
<div style={{
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '20px 24px',
  borderBottom: `1px solid ${borderColor}`,
}}>
  {/* Session Title (Left) */}
  <h2 style={{
    fontFamily: TYPOGRAPHY.serif,
    fontSize: '24px',
    fontWeight: 600,
    color: text,
  }}>
    Session Details
  </h2>

  {/* Controls (Right) */}
  <div style={{
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  }}>
    {/* Theme Toggle */}
    <ThemeToggle />

    {/* Close Button (X icon) */}
    <button
      onClick={onClose}
      className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
      aria-label="Close session details"
    >
      <X className="w-5 h-5" style={{ color: text }} />
    </button>
  </div>
</div>
```

**Key Changes**:
- **Removes** "Back to Dashboard" button with arrow
- **Adds** "Session Details" title on left side
- **Adds** ThemeToggle component (reuses existing component)
- **Adds** X icon button in top-right corner
- Theme toggle and X button side-by-side
- Matches NavigationBar button styling (40x40px, rounded-lg, hover effects)

---

## Phase 3: Testing & Verification

### 3.1 Database Migration Verification

**Commands**:
```bash
# Connect to Railway Postgres
railway connect

# Verify column exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'therapy_sessions'
AND column_name = 'action_items_summary';

# Check for existing data
SELECT id, technique, action_items, action_items_summary
FROM therapy_sessions
LIMIT 5;
```

**Expected Output**:
- Column `action_items_summary` exists with type `text`
- Existing sessions have `NULL` for action_items_summary (will be populated on next analysis)

---

### 3.2 Backend Logging Verification (Railway MCP)

**Steps**:

1. **Trigger Demo Pipeline** to generate new sessions with Wave 1 analysis
2. **Check Railway Logs** using MCP tool

**Commands**:
```typescript
// In Claude Code interface
mcp__Railway__get-logs({
  workspacePath: "/Users/newdldewdl/Global Domination 2/peerbridge proj/backend",
  logType: "deploy",
  lines: 200,
  filter: "Wave 1",
  json: false
})
```

**Expected Log Format** (matching existing Wave 1 logs):
```
🌊 Starting Wave 1 analysis for session abc-123...
🎭 Running mood analysis for session abc-123...
✅ Mood analysis complete for session abc-123
📊 Running topic extraction for session abc-123...
✅ Topic extraction complete for session abc-123
🔍 Running breakthrough detection for session abc-123...
✅ Breakthrough detection complete for session abc-123
✅ Wave 1 core analyses complete for session abc-123
📝 Generating action items summary for session abc-123...
✅ Action items summary complete: 'Practice TIPP & schedule psychiatrist' (43 chars)
✅ Wave 1 complete (with summary) for session abc-123
```

**Verification Checklist**:
- ✅ Emoji icons match existing Wave 1 logs (🌊, 🎭, 📊, 🔍, ✅, 📝)
- ✅ Session ID included in all log messages
- ✅ Character count shown in summary completion log
- ✅ Summary text included in log output
- ✅ Logs appear in correct chronological order
- ✅ No errors or warnings for successful runs

---

### 3.3 Frontend UI Verification

**Test Cases**:

#### Test 1: Mood Score Display
- **Action**: Open SessionDetail for session with `mood_score`
- **Expected**:
  - Emoji shows correct category (sad/neutral/happy based on score)
  - Numeric score displays next to emoji (e.g., "😊 7.5")
  - Emotional tone shows if available (e.g., "(hopeful, engaged)")
  - Section renders with proper spacing and styling

#### Test 2: Technique Definition Display
- **Action**: Open SessionDetail for session with `technique_definition`
- **Expected**:
  - Technique name shows in accent color (teal/purple)
  - Definition displays below technique name (2-3 sentences)
  - No placeholder text "This therapeutic approach was applied..."
  - Proper typography (Crimson Pro serif for definition)

#### Test 3: SessionCard Action Summary
- **Action**: View SessionCard in sessions grid
- **Expected**:
  - First bullet: Technique name (e.g., "CBT - Cognitive Restructuring")
  - Second bullet: 45-char summary (e.g., "Practice TIPP & schedule psychiatrist")
  - Summary fits on one line with ellipsis if needed
  - Matches accent color (teal/purple)

#### Test 4: SessionDetail Header
- **Action**: Open SessionDetail
- **Expected**:
  - "Session Details" title on left side
  - Theme toggle button next to X button (right side)
  - X icon button in top-right corner (40x40px)
  - Clicking X closes modal and returns to sessions grid
  - Theme toggle works (light ↔ dark mode)

#### Test 5: Light/Dark Mode Consistency
- **Action**: Toggle theme while SessionDetail open
- **Expected**:
  - All colors update correctly
  - Custom emojis change color (teal → purple)
  - Hover states work on X button and theme toggle
  - No visual glitches or layout shifts

---

### 3.4 Data Flow Integration Test

**End-to-End Test**:

1. **Trigger Demo Pipeline**: POST `/api/demo/initialize`
2. **Wait for Wave 1**: Monitor Railway logs for completion
3. **Fetch Sessions**: GET `/api/sessions/`
4. **Verify Response Fields**:
   - `action_items_summary` present (45 chars max)
   - `technique_definition` present (2-3 sentences)
   - `mood_score` present (0.0-10.0)
5. **Open SessionDetail**: Click any session card
6. **Visual Verification**: Check all UI elements render correctly

**API Response Example**:
```json
{
  "sessions": [
    {
      "id": "abc-123",
      "session_date": "2026-01-10",
      "technique": "CBT - Cognitive Restructuring",
      "technique_definition": "Cognitive Behavioral Therapy focuses on identifying and challenging unhelpful thought patterns. This technique helps patients recognize cognitive distortions and replace them with more balanced, realistic thoughts.",
      "action_items": [
        "Practice identifying cognitive distortions using thought record worksheet",
        "Schedule follow-up appointment to review progress"
      ],
      "action_items_summary": "Track distortions & schedule follow-up",
      "mood_score": 6.5,
      "mood_confidence": 0.88,
      "emotional_tone": "cautiously hopeful"
    }
  ]
}
```

---

## Phase 4: Error Handling & Edge Cases

### 4.1 Backend Error Scenarios

#### Scenario 1: Action Items Summarization Fails
- **Cause**: OpenAI API error, invalid action items, etc.
- **Handling**: Wave 1 continues without summary (try/except wrapper)
- **Logging**: `⚠️ Action items summarization failed for session {id}: {error}. Wave 1 will continue without summary.`
- **Frontend**: Fallback to displaying first action item in SessionCard

#### Scenario 2: Technique Definition Not Found
- **Cause**: Technique name not in technique_library.json
- **Handling**: API returns `technique_definition: null`
- **Frontend**: Shows "Definition not available for this technique."

#### Scenario 3: Missing Action Items (< 2 items)
- **Cause**: Topic extraction generated 0-1 action items
- **Handling**: Summarization skipped, logged warning
- **Logging**: `⚠️ Cannot summarize action items for session {id}: Need 2 action items, found {count}`
- **Frontend**: SessionCard uses first action item or empty string

#### Scenario 4: Summary Exceeds 45 Characters
- **Cause**: AI generates longer phrase
- **Handling**: Truncate to 42 chars + "..." (safety check in summarizer)
- **Logging**: `📝 Summary exceeded 45 chars ({count}), truncating`

---

### 4.2 Frontend Error Scenarios

#### Scenario 1: Missing mood_score
- **Handling**: Mood section doesn't render (conditional rendering)
- **No Error**: Component gracefully handles undefined

#### Scenario 2: Missing technique_definition
- **Handling**: Shows fallback message "Definition not available for this technique."
- **Styling**: Italic, muted color to indicate missing data

#### Scenario 3: Missing action_items_summary
- **Handling**: SessionCard falls back to `session.actions[0]`
- **No Error**: Backward compatible with existing data

#### Scenario 4: Invalid mood_score (outside 0-10 range)
- **Handling**: `mapNumericMoodToCategory()` clamps to valid range
- **No Error**: Math.max(0, Math.min(10, score)) ensures valid mapping

---

## Cost Analysis

### Per-Session Costs (Wave 1 Extended)

| Analysis Component | Model | Estimated Cost | Change |
|--------------------|-------|----------------|--------|
| Mood Analysis | gpt-5-nano | $0.0005 | Unchanged |
| Topic Extraction | gpt-5-mini | $0.0013 | Unchanged |
| Breakthrough Detection | gpt-5 | $0.0084 | Unchanged |
| **Action Items Summary** | **gpt-5-nano** | **$0.0003** | **NEW** |
| **Wave 1 Total** | - | **$0.0105** | **+$0.0003** |

### Full Pipeline Costs

| Phase | Total Cost | Change |
|-------|------------|--------|
| Wave 1 (Extended) | $0.0105 | +$0.0003 (+2.9%) |
| Wave 2 | $0.0318 | Unchanged |
| **Full Pipeline** | **$0.0423** | **+$0.0003 (+0.7%)** |

### Demo Cost (10 Sessions)

- **Before**: $0.42
- **After**: $0.423
- **Increase**: $0.003 (0.7%)

**Conclusion**: Negligible cost increase (<1%) for significant UX improvement.

---

## File Summary

### New Files Created (3)

1. `/backend/supabase/migrations/010_add_action_items_summary.sql` - Database migration
2. `/backend/app/services/action_items_summarizer.py` - Summarization service
3. `/frontend/lib/mood-mapper.ts` - Mood mapping utility

### Files Modified (7)

1. `/backend/app/config/model_config.py` - Add action_summary model config
2. `/backend/app/services/analysis_orchestrator.py` - Integrate summarization into Wave 1
3. `/backend/app/routers/sessions.py` - Add technique definition lookup
4. `/frontend/app/patient/lib/types.ts` - Add new Session fields
5. `/frontend/app/patient/lib/usePatientSessions.ts` - Map new backend fields
6. `/frontend/app/patient/components/SessionCard.tsx` - Use action summary
7. `/frontend/app/patient/components/SessionDetail.tsx` - Add mood score, technique def, X button, theme toggle

---

## Rollback Plan

### If Issues Arise

1. **Database**: Migration is additive (adds column), safe to leave in place
2. **Backend**:
   - Remove import of `ActionItemsSummarizer` from orchestrator
   - Comment out sequential summarization call in `_run_wave1()`
   - Remove technique definition enrichment from sessions endpoint
3. **Frontend**:
   - Revert SessionCard to use `session.actions[0]` instead of summary
   - Hide mood score section in SessionDetail (conditional rendering)
   - Restore "Back to Dashboard" button
4. **Model Config**: Remove `action_summary` entry (optional, no harm if left)

### Git Safety

- All changes in single commit: "Feature: PR #1 SessionDetail improvements + Wave 1 action summarization"
- Can revert entire feature with `git revert <commit-hash>`
- Database migration can be rolled back with DROP COLUMN (if needed)

---

## Success Criteria

✅ **Backend**:
- [ ] Migration applies successfully
- [ ] Action items summarizer generates 45-char phrases
- [ ] Wave 1 logs show summarization step
- [ ] API returns `action_items_summary` and `technique_definition` fields
- [ ] Railway logs match existing format

✅ **Frontend**:
- [ ] SessionCard displays 45-char summary as second bullet
- [ ] SessionDetail shows numeric mood score with emoji
- [ ] SessionDetail shows technique definitions
- [ ] X button closes modal correctly
- [ ] Theme toggle works in SessionDetail header
- [ ] Light/dark mode consistent across all elements

✅ **Integration**:
- [ ] End-to-end flow works: Wave 1 → DB → API → Frontend
- [ ] All edge cases handled gracefully
- [ ] No breaking changes to existing functionality
- [ ] Cost increase < 1%

---

## Implementation Timeline

1. **Phase 1 (Backend)**: 45-60 minutes
   - Database migration
   - Action items summarizer service
   - Orchestrator integration
   - Sessions API enrichment

2. **Phase 2 (Frontend)**: 45-60 minutes
   - Mood mapper utility
   - Type updates
   - SessionCard changes
   - SessionDetail improvements

3. **Phase 3 (Testing)**: 30-45 minutes
   - Database verification
   - Railway logs check
   - UI testing (all scenarios)
   - Integration testing

4. **Total**: 2-3 hours

---

## Next Steps

1. Review this implementation plan
2. Create git backup commit
3. Execute Phase 1 (Backend)
4. Execute Phase 2 (Frontend)
5. Execute Phase 3 (Testing)
6. Create final commit and push to remote
7. Update SESSION_LOG.md with completion notes
8. Update TheraBridge.md Development Status section
