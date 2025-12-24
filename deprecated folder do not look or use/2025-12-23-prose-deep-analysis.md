# Patient-Facing Prose Deep Analysis Implementation Plan

## Overview

Transform the structured Deep Clinical Analysis output into a compassionate, clinically-informed 500-750 word prose narrative that addresses the patient directly. The prose will combine the empowering tone of a therapist's letter with the precision of a clinical summary, showcasing industry knowledge through appropriate therapeutic terminology while remaining accessible and encouraging.

## Current State Analysis

**What exists now:**
- `deep_analyzer.py` (backend/app/services/) - Uses GPT-5.2 to generate structured JSON analysis with 5 categories: progress indicators, therapeutic insights, coping skills, therapeutic relationship, and recommendations
- `DeepAnalysisSection.tsx` (frontend/app/patient/components/) - Displays structured analysis as colored cards with bullet points, icons, and tags
- Database storage in `therapy_sessions` table: `deep_analysis` (JSONB field), `analysis_confidence` (FLOAT)
- Integration point: SessionDetail.tsx lines 210-217 renders DeepAnalysisSection when `session.deep_analysis` exists

**What's missing:**
- Prose generation service to convert structured JSON → flowing narrative
- Database field to store generated prose (`prose_analysis` TEXT field)
- API endpoint to trigger prose generation
- Frontend component to display prose paragraphs
- Integration with Wave 2 analysis pipeline for auto-generation

**Key constraints:**
- Must use GPT-5.2 (same model as deep_analyzer) for consistent quality
- Must generate 500-750 words across 5 paragraphs
- Must balance compassionate tone with clinical terminology
- Must auto-generate during Wave 2 pipeline (not on-demand)

### Key Discoveries:
- Model config verified at backend/app/config/model_config.py:89 - `deep_analysis` uses GPT-5.2
- JSONB storage pattern: Use `to_dict()` method, store directly via Supabase client (backend/app/services/deep_analyzer.py:97-107)
- Analysis orchestrator handles Wave 2 at backend/app/services/analysis_orchestrator.py:421 - ideal insertion point for prose generation
- Frontend SessionDetail already has conditional rendering pattern for analysis (lines 210-217)
- Font standardization: Use `system-ui` throughout (recently updated in SessionDetail.tsx:19-21)

## Desired End State

**Backend:**
- New `prose_generator.py` service that takes structured `deep_analysis` JSON and generates 500-750 word prose
- New `prose_analysis` TEXT field in `therapy_sessions` table
- Prose auto-generates at end of Wave 2 pipeline (after deep_analyzer completes)
- API endpoint `POST /api/sessions/{id}/generate-prose-analysis` for manual regeneration

**Frontend:**
- Replace `DeepAnalysisSection` component with new `ProseAnalysisSection` component
- Display 5 unmarked paragraphs with subtle visual separators (spacing + dividers)
- Maintain "Deep Clinical Analysis" heading and confidence badge
- Seamless integration in SessionDetail.tsx at same location (lines 210-217)

**Verification:**
- Backend test: Call API endpoint → returns 500-750 word prose with 5 paragraphs
- Frontend test: Open SessionDetail → see flowing prose instead of structured cards
- Full pipeline test: Upload session → Wave 1 + Wave 2 complete → prose auto-generated and displayed

## What We're NOT Doing

- ❌ Creating toggle between prose and structured views (prose replaces structured entirely)
- ❌ Adding paragraph headings/labels (prose flows naturally without section markers)
- ❌ Supporting on-demand generation (only auto-generation via pipeline)
- ❌ Backfilling existing sessions (no sessions have deep_analysis yet per user confirmation)
- ❌ Using GPT-5-mini or other cheaper models (must use GPT-5.2 for quality)
- ❌ Storing prose as JSONB with metadata (simple TEXT field sufficient)

## Implementation Approach

**Strategy:** Build backend service first (data model → AI service → API endpoint → pipeline integration), then update frontend to consume new prose data. This follows the established pattern for mood_analyzer.py and topic_extractor.py.

**Phasing:**
1. **Phase 1 (Backend):** Database schema, prose generation service, API endpoint, pipeline integration
2. **Phase 2 (Frontend):** New prose component, replace DeepAnalysisSection, update SessionDetail
3. **Phase 3 (Cleanup):** Fix incorrect model references in system prompts across all analyzers

**Rationale:** Backend-first ensures data is ready before UI changes. Phase 3 cleanup ensures documentation accuracy for future development.

---

## Phase 1: Backend Prose Generation Service

### Overview
Create the complete backend infrastructure for prose generation, including database schema, AI service, API endpoint, and integration with the Wave 2 analysis pipeline.

### Changes Required:

#### 1.1 Database Schema Migration

**File**: `backend/supabase/migrations/006_add_prose_analysis.sql`
**Changes**: Add new TEXT field to store generated prose

```sql
-- Migration: Add prose_analysis field for patient-facing narrative summaries
-- Date: 2025-12-23
-- Description: Stores 500-750 word prose generated from structured deep_analysis

ALTER TABLE therapy_sessions
ADD COLUMN prose_analysis TEXT NULL,
ADD COLUMN prose_generated_at TIMESTAMP NULL;

-- Add comment for clarity
COMMENT ON COLUMN therapy_sessions.prose_analysis IS 'Patient-facing prose narrative (500-750 words) generated from structured deep_analysis';
COMMENT ON COLUMN therapy_sessions.prose_generated_at IS 'Timestamp when prose was last generated';

-- Index for querying sessions with prose
CREATE INDEX idx_therapy_sessions_prose_generated
ON therapy_sessions(prose_generated_at)
WHERE prose_analysis IS NOT NULL;
```

#### 1.2 Prose Generator Service

**File**: `backend/app/services/prose_generator.py`
**Changes**: New file - AI service to convert structured deep_analysis → prose

```python
"""
Prose Analysis Generator Service

Converts structured deep_analysis JSON into patient-facing prose narrative.
Uses GPT-5.2 to generate 500-750 word compassionate clinical summary.

Output: 5 flowing paragraphs addressing patient directly, combining:
- Empowering therapist letter tone
- Clinical precision and terminology
- Accessible language with therapeutic jargon
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import openai
import os
import logging

from app.config.model_config import get_model_name

logger = logging.getLogger(__name__)


@dataclass
class ProseAnalysis:
    """Patient-facing prose narrative generated from deep analysis"""
    session_id: str
    prose_text: str  # 500-750 word narrative
    word_count: int
    paragraph_count: int
    confidence_score: float  # Inherited from deep_analysis
    generated_at: datetime


class ProseGenerator:
    """
    AI-powered prose generation for therapy session analysis.

    Converts structured DeepAnalysis JSON into flowing prose narrative
    that combines compassionate tone with clinical expertise.
    """

    def __init__(self, api_key: Optional[str] = None, override_model: Optional[str] = None):
        """
        Initialize the prose generator.

        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
            override_model: Optional model override for testing (default: gpt-5.2)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required for prose generation")

        openai.api_key = self.api_key
        self.model = get_model_name("deep_analysis", override_model=override_model)  # Uses gpt-5.2

    async def generate_prose(
        self,
        session_id: str,
        deep_analysis: Dict[str, Any],
        confidence_score: float
    ) -> ProseAnalysis:
        """
        Generate patient-facing prose from structured deep analysis.

        Args:
            session_id: Session UUID
            deep_analysis: Complete structured analysis (from deep_analyzer.py)
            confidence_score: Analysis confidence (0.0 - 1.0)

        Returns:
            ProseAnalysis with 500-750 word narrative
        """
        logger.info(f"📝 Generating prose analysis for session {session_id}")

        # Create prose generation prompt
        prompt = self._create_prose_prompt(deep_analysis)

        # Call OpenAI API (GPT-5.2)
        # NOTE: GPT-5 series does NOT support custom temperature
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            prose_text = response.choices[0].message.content.strip()

            # Validate output
            word_count = len(prose_text.split())
            paragraph_count = len([p for p in prose_text.split('\n\n') if p.strip()])

            if word_count < 400 or word_count > 900:
                logger.warning(f"Prose word count ({word_count}) outside target range 500-750")

            if paragraph_count != 5:
                logger.warning(f"Prose has {paragraph_count} paragraphs, expected 5")

            analysis = ProseAnalysis(
                session_id=session_id,
                prose_text=prose_text,
                word_count=word_count,
                paragraph_count=paragraph_count,
                confidence_score=confidence_score,
                generated_at=datetime.utcnow()
            )

            logger.info(f"✓ Prose generated: {word_count} words, {paragraph_count} paragraphs")

            return analysis

        except Exception as e:
            logger.error(f"Prose generation failed for session {session_id}: {e}")
            raise Exception(f"Prose generation failed: {str(e)}")

    def _get_system_prompt(self) -> str:
        """System prompt defining prose generation guidelines."""
        return """You are an expert clinical psychologist writing patient-facing session summaries.

Your task is to convert structured therapeutic analysis into a warm, encouraging prose narrative
that combines the compassionate tone of a therapist's letter with the precision of a clinical summary.

**YOUR ROLE:**
- Write directly to the patient using second person ("you", "your")
- Balance empathy with clinical expertise
- Use therapeutic terminology naturally (show industry knowledge)
- Make complex insights accessible and actionable
- Maintain professional warmth throughout

**OUTPUT REQUIREMENTS:**

**Length:** 500-750 words total (strict)

**Structure:** 5 flowing paragraphs (no headings or labels):
1. **Session Overview & Context** - Introduce the session with mood/emotional tone
2. **Key Insights & Realizations** - Highlight breakthroughs and patterns
3. **Skill Development & Progress** - Discuss coping skills and growth
4. **Therapeutic Progress** - Address relationship quality and engagement
5. **Next Steps & Encouragement** - Provide actionable recommendations with hope

**Tone Guidelines:**
- Compassionate and validating (acknowledge struggles genuinely)
- Empowering (emphasize agency and strengths)
- Clinical precision (use proper therapeutic terms: "cognitive restructuring", "affect regulation", "therapeutic alliance")
- Accessible (explain complex concepts clearly)
- Hopeful (end with encouragement and forward momentum)

**Language Choices:**
- Direct address: "You demonstrated...", "In this session, you..."
- Present therapeutic techniques accurately: "We explored dialectical thinking", "You practiced opposite action"
- Balance validation with growth: "While anxiety persisted, you showed remarkable courage in..."
- Specific evidence: Reference actual session moments when possible

**What to AVOID:**
- Paragraph headings or section labels
- Overly clinical distance ("The patient exhibited...")
- Jargon without context ("Use DBT skills" → "Use the DBT distress tolerance skills we practiced")
- Generic platitudes ("You're doing great!")
- Bullet points or lists (pure prose only)

**Quality Markers:**
- Reads like a personalized letter from therapist
- Demonstrates deep clinical knowledge
- Feels supportive without being patronizing
- Specific to this patient's unique journey
- Natural paragraph flow with clear transitions

Return ONLY the prose text (no JSON, no formatting markers, no metadata).
Separate paragraphs with double newlines."""

    def _create_prose_prompt(self, deep_analysis: Dict[str, Any]) -> str:
        """Create the prose generation prompt from structured analysis."""
        # Extract structured components
        progress = deep_analysis.get("progress_indicators", {})
        insights = deep_analysis.get("therapeutic_insights", {})
        skills = deep_analysis.get("coping_skills", {})
        relationship = deep_analysis.get("therapeutic_relationship", {})
        recommendations = deep_analysis.get("recommendations", {})

        return f"""Convert the following structured therapeutic analysis into a 500-750 word prose narrative.

Create 5 flowing paragraphs that address: session overview, key insights, skill development,
therapeutic progress, and next steps. Adapt the emphasis based on what's most clinically
relevant in this specific session.

**STRUCTURED ANALYSIS DATA:**

**Progress Indicators:**
- Symptom Reduction: {progress.get('symptom_reduction', {})}
- Skill Development: {progress.get('skill_development', [])}
- Goal Progress: {progress.get('goal_progress', [])}
- Behavioral Changes: {progress.get('behavioral_changes', [])}

**Therapeutic Insights:**
- Key Realizations: {insights.get('key_realizations', [])}
- Patterns: {insights.get('patterns', [])}
- Growth Areas: {insights.get('growth_areas', [])}
- Strengths: {insights.get('strengths', [])}

**Coping Skills:**
- Learned: {skills.get('learned', [])}
- Proficiency: {skills.get('proficiency', {})}
- Practice Recommendations: {skills.get('practice_recommendations', [])}

**Therapeutic Relationship:**
- Engagement: {relationship.get('engagement_level', 'N/A')} - {relationship.get('engagement_evidence', '')}
- Openness: {relationship.get('openness', 'N/A')} - {relationship.get('openness_evidence', '')}
- Alliance: {relationship.get('alliance_strength', 'N/A')} - {relationship.get('alliance_evidence', '')}

**Recommendations:**
- Practices: {recommendations.get('practices', [])}
- Resources: {recommendations.get('resources', [])}
- Reflection Prompts: {recommendations.get('reflection_prompts', [])}

---

**INSTRUCTIONS:**

Write a compassionate, clinically-informed prose narrative that integrates all the above insights.

Remember:
- 500-750 words total
- 5 paragraphs (no headings)
- Address the patient directly
- Use therapeutic terminology naturally
- Balance empathy with expertise
- End with hope and encouragement

Begin writing now:"""


# Convenience function
async def generate_prose_from_analysis(
    session_id: str,
    deep_analysis: Dict[str, Any],
    confidence_score: float,
    api_key: Optional[str] = None
) -> ProseAnalysis:
    """
    Convenience function to generate prose from deep analysis.

    Args:
        session_id: Session UUID
        deep_analysis: Structured analysis from deep_analyzer.py
        confidence_score: Analysis confidence
        api_key: Optional OpenAI API key

    Returns:
        ProseAnalysis object
    """
    generator = ProseGenerator(api_key=api_key)
    return await generator.generate_prose(session_id, deep_analysis, confidence_score)
```

#### 1.3 Update Model Config Task Mapping

**File**: `backend/app/config/model_config.py`
**Changes**: Add prose_generation task mapping (uses same gpt-5.2 as deep_analysis)

```python
# Task-Based Model Assignments
# Each analysis task is mapped to the optimal GPT-5 model
TASK_MODEL_ASSIGNMENTS = {
    "mood_analysis": "gpt-5-nano",          # Simple 0-10 scoring with rationale
    "topic_extraction": "gpt-5-mini",       # Structured metadata extraction
    "breakthrough_detection": "gpt-5",      # Complex clinical reasoning required
    "deep_analysis": "gpt-5.2",             # Comprehensive synthesis of all data
    "prose_generation": "gpt-5.2",          # Patient-facing prose narrative (NEW)
}

# Cost Estimation (based on typical session processing)
ESTIMATED_TOKEN_USAGE = {
    "mood_analysis": {"input": 2000, "output": 200},       # ~$0.0005 per session
    "topic_extraction": {"input": 3000, "output": 300},    # ~$0.0013 per session
    "breakthrough_detection": {"input": 3500, "output": 400}, # ~$0.0084 per session
    "deep_analysis": {"input": 5000, "output": 800},       # ~$0.0200 per session
    "prose_generation": {"input": 2000, "output": 600},    # ~$0.0118 per session (NEW)
}
```

#### 1.4 API Endpoint for Prose Generation

**File**: `backend/app/routers/sessions.py`
**Changes**: Add endpoint for manual prose regeneration

```python
# Add import at top
from app.services.prose_generator import ProseGenerator

# Add response model after existing models (around line 90)
class ProseAnalysisResponse(BaseModel):
    """Response model for prose analysis"""
    session_id: str
    prose_text: str
    word_count: int
    paragraph_count: int
    confidence: float
    generated_at: datetime

# Add endpoint after deep analysis endpoint (around line 1150)
@router.post("/sessions/{session_id}/generate-prose-analysis", response_model=ProseAnalysisResponse)
async def generate_prose_analysis(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    db: Client = Depends(get_db)
):
    """
    Generate patient-facing prose narrative from existing deep analysis.

    Requires:
    - Session must have completed deep_analysis
    - User must be patient or therapist for this session

    Returns:
    - 500-750 word prose narrative
    - Word/paragraph counts
    - Generation timestamp
    """
    try:
        # Fetch session
        session_response = db.table("therapy_sessions").select("*").eq("id", session_id).single().execute()
        session = session_response.data

        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        # Verify access (patient or therapist)
        user_id = current_user["id"]
        if session["patient_id"] != user_id and session.get("therapist_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Check if deep_analysis exists
        if not session.get("deep_analysis"):
            raise HTTPException(
                status_code=400,
                detail="Deep analysis must be completed before generating prose"
            )

        # Check if prose already exists (optional caching)
        if session.get("prose_analysis"):
            logger.info(f"Prose already exists for session {session_id}, regenerating...")

        # Generate prose
        generator = ProseGenerator()
        prose = await generator.generate_prose(
            session_id=session_id,
            deep_analysis=session["deep_analysis"],
            confidence_score=session.get("analysis_confidence", 0.8)
        )

        # Update database
        db.table("therapy_sessions").update({
            "prose_analysis": prose.prose_text,
            "prose_generated_at": prose.generated_at.isoformat()
        }).eq("id", session_id).execute()

        logger.info(f"✓ Prose analysis saved for session {session_id}")

        return ProseAnalysisResponse(
            session_id=session_id,
            prose_text=prose.prose_text,
            word_count=prose.word_count,
            paragraph_count=prose.paragraph_count,
            confidence=prose.confidence_score,
            generated_at=prose.generated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prose generation failed for session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Prose generation failed: {str(e)}")
```

#### 1.5 Integrate with Analysis Orchestrator (Wave 2)

**File**: `backend/app/services/analysis_orchestrator.py`
**Changes**: Auto-generate prose after deep_analysis completes

```python
# Add import at top
from app.services.prose_generator import ProseGenerator

# Modify the _run_wave2_deep_analysis method (around line 421)
# Add prose generation after deep analysis completes

async def _run_wave2_deep_analysis(
    self,
    session_id: str,
    session: Dict[str, Any],
    cumulative_context: Optional[Dict[str, Any]] = None
) -> None:
    """Run Wave 2: Deep Clinical Analysis + Prose Generation"""

    # ... existing deep analysis code ...

    # Update session with deep analysis (existing code around line 421)
    self.db.table("therapy_sessions").update({
        "deep_analysis": analysis.to_dict(),
        "analysis_confidence": analysis.confidence_score,
        "deep_analyzed_at": datetime.utcnow().isoformat(),
    }).eq("id", session_id).execute()

    logger.info(f"✓ Wave 2 deep analysis complete for session {session_id}")

    # NEW: Auto-generate prose from deep analysis
    try:
        logger.info(f"📝 Auto-generating prose for session {session_id}")
        prose_generator = ProseGenerator()
        prose = await prose_generator.generate_prose(
            session_id=session_id,
            deep_analysis=analysis.to_dict(),
            confidence_score=analysis.confidence_score
        )

        # Update session with prose
        self.db.table("therapy_sessions").update({
            "prose_analysis": prose.prose_text,
            "prose_generated_at": prose.generated_at.isoformat()
        }).eq("id", session_id).execute()

        logger.info(f"✓ Prose auto-generated: {prose.word_count} words, {prose.paragraph_count} paragraphs")

    except Exception as e:
        # Don't fail entire Wave 2 if prose generation fails
        logger.error(f"Prose auto-generation failed for session {session_id}: {e}")
        logger.warning("Wave 2 deep analysis succeeded, but prose generation failed (non-critical)")
```

### Success Criteria:

#### Automated Verification:
- [x] Database migration runs successfully: `cd backend && alembic upgrade head`
- [x] Python imports work: `cd backend && python -c "from app.services.prose_generator import ProseGenerator; print('OK')"`
- [x] Model config includes prose_generation: `cd backend && python -c "from app.config.model_config import TASK_MODEL_ASSIGNMENTS; assert 'prose_generation' in TASK_MODEL_ASSIGNMENTS"`
- [x] Backend starts without errors: `cd backend && uvicorn app.main:app --reload` (check for import errors)

#### Manual Verification:
- [ ] API endpoint responds: `curl -X POST http://localhost:8000/api/sessions/{test_session_id}/generate-prose-analysis -H "Authorization: Bearer {token}"`
- [ ] Prose is 500-750 words with 5 paragraphs
- [ ] Tone is compassionate + clinically informed (not too casual, not too technical)
- [ ] Prose addresses patient directly ("you", "your")
- [ ] Database field `prose_analysis` populated after generation
- [ ] Wave 2 pipeline auto-generates prose (test full analysis pipeline)

**Implementation Note**: After completing Phase 1 and all automated verification passes, manually test the API endpoint with a real session containing deep_analysis. Verify prose quality, tone, and word count before proceeding to Phase 2.

---

## Phase 2: Frontend Prose Display Component

### Overview
Replace the structured DeepAnalysisSection component with a new ProseAnalysisSection component that displays flowing prose paragraphs. Update SessionDetail to use the new component.

### Changes Required:

#### 2.1 New Prose Analysis Display Component

**File**: `frontend/app/patient/components/ProseAnalysisSection.tsx`
**Changes**: New file - prose display component replacing structured cards

```typescript
'use client';

/**
 * Prose Analysis Section Component
 *
 * Displays patient-facing prose narrative generated from deep clinical analysis.
 * Replaces the structured DeepAnalysisSection with flowing prose paragraphs.
 *
 * Format:
 * - 5 unmarked paragraphs (no headings)
 * - Subtle visual separators (spacing + dividers)
 * - Compassionate tone + clinical precision
 * - 500-750 words total
 */

import { Brain } from 'lucide-react';

// Font families - using system-ui throughout (matching SessionDetail)
const fontSans = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
const fontSerif = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

interface ProseAnalysisSectionProps {
  proseText: string;      // 500-750 word prose narrative
  confidence: number;     // 0.0 to 1.0
  generatedAt?: string;   // ISO timestamp
  wordCount?: number;     // For debugging/validation
}

export function ProseAnalysisSection({
  proseText,
  confidence,
  generatedAt,
  wordCount
}: ProseAnalysisSectionProps) {

  // Split prose into paragraphs (separated by double newlines)
  const paragraphs = proseText
    .split('\n\n')
    .map(p => p.trim())
    .filter(p => p.length > 0);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 style={{ fontFamily: fontSans }} className="text-xl font-semibold text-gray-800 dark:text-gray-200">
              Deep Clinical Analysis
            </h3>
            <p style={{ fontFamily: fontSans }} className="text-xs text-gray-500 dark:text-gray-400">
              AI-powered insights • {Math.round(confidence * 100)}% confidence
            </p>
          </div>
        </div>
      </div>

      {/* Prose Content */}
      <div className="space-y-4">
        {paragraphs.map((paragraph, index) => (
          <div key={index}>
            <p
              style={{ fontFamily: fontSerif }}
              className="text-base leading-relaxed text-gray-700 dark:text-gray-300"
            >
              {paragraph}
            </p>

            {/* Subtle divider between paragraphs (except last) */}
            {index < paragraphs.length - 1 && (
              <div className="mt-4 h-px bg-gradient-to-r from-transparent via-gray-200 dark:via-gray-700 to-transparent" />
            )}
          </div>
        ))}
      </div>

      {/* Optional: Word count footer for debugging (remove in production) */}
      {wordCount && process.env.NODE_ENV === 'development' && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <p style={{ fontFamily: fontSans }} className="text-xs text-gray-400 dark:text-gray-600">
            {wordCount} words • {paragraphs.length} paragraphs
            {generatedAt && ` • Generated ${new Date(generatedAt).toLocaleString()}`}
          </p>
        </div>
      )}
    </div>
  );
}
```

#### 2.2 Update Session Type Definition

**File**: `frontend/app/patient/lib/types.ts`
**Changes**: Add prose_analysis field to Session interface

```typescript
// Add these fields to the Session interface (around line 15-20)
export interface Session {
  id: string;
  date: string;
  duration: string;
  therapist: string;
  mood: 'positive' | 'neutral' | 'challenging';
  topics: string[];
  strategy: string;
  actions: string[];
  transcript?: TranscriptEntry[];
  patientSummary?: string;
  summary?: string;
  milestone?: SessionMilestone;
  deep_analysis?: DeepAnalysis;           // Existing
  analysis_confidence?: number;           // Existing
  prose_analysis?: string;                // NEW: 500-750 word prose narrative
  prose_generated_at?: string;            // NEW: ISO timestamp
  prose_word_count?: number;              // NEW: Word count (for validation)
}
```

#### 2.3 Update SessionDetail Component

**File**: `frontend/app/patient/components/SessionDetail.tsx`
**Changes**: Replace DeepAnalysisSection with ProseAnalysisSection

```typescript
// Update import (line 17)
import { ProseAnalysisSection } from './ProseAnalysisSection';  // Changed from DeepAnalysisSection

// Replace the Deep Clinical Analysis section (lines 209-217)
{/* Deep Clinical Analysis - Prose Format */}
{session.prose_analysis && (
  <div className="mt-6 p-4 bg-[#5AB9B4]/5 dark:bg-[#a78bfa]/10 rounded-xl border border-[#5AB9B4]/20 dark:border-[#a78bfa]/30">
    <ProseAnalysisSection
      proseText={session.prose_analysis}
      confidence={session.analysis_confidence || 0.8}
      generatedAt={session.prose_generated_at}
      wordCount={session.prose_word_count}
    />
  </div>
)}
```

#### 2.4 Update Mock Data (for Development Testing)

**File**: `frontend/app/patient/lib/mockData.ts`
**Changes**: Add sample prose_analysis to mock sessions

```typescript
// Add to one or more mock sessions (around line 35-40) for testing
export const sessions: Session[] = [
  {
    id: 's12',
    date: 'Dec 22',
    duration: '50 min',
    therapist: 'Dr. Sarah Chen',
    mood: 'positive',
    topics: ['Emotional Regulation', 'Mindfulness Practice'],
    strategy: 'Dialectical Behavior Therapy (DBT)',
    actions: ['Practice TIPP skill daily', 'Complete emotion diary'],
    transcript: [...],  // existing transcript
    patientSummary: 'Session focused on distress tolerance skills...',
    // NEW: Add sample prose for testing
    prose_analysis: `In this session, you demonstrated remarkable courage in exploring the connection between your anxiety triggers and early attachment patterns. Your willingness to engage with difficult emotions, particularly the vulnerability you expressed when discussing your relationship with your mother, reflects a deepening therapeutic alliance and growing capacity for affect regulation.

The breakthrough moment came when you recognized the pattern of seeking external validation during moments of self-doubt. This insight—that your worth isn't contingent on others' approval—represents a significant shift in your cognitive schema. You've been practicing cognitive restructuring for several weeks now, and this session showed clear evidence of your developing proficiency. The way you challenged your automatic thought ("I'm failing at everything") by examining the evidence demonstrates mastery of this crucial DBT skill.

Your progress with distress tolerance techniques has been noteworthy. You reported successfully using the TIPP skill during last week's panic episode, which prevented escalation and helped you regain emotional equilibrium. This marks a transition from beginner to developing proficiency—you're now able to deploy these skills independently in real-world situations. We also introduced the concept of radical acceptance, which you grasped quickly and applied to your ongoing grief about your father's illness.

The quality of our therapeutic relationship continues to strengthen. Your engagement level remains high, as evidenced by your active participation in exploring difficult material and your openness in sharing vulnerable moments. The alliance we've built provides a secure base for this important therapeutic work, and your growing trust enables us to address increasingly complex emotional territory.

Looking ahead, I encourage you to continue your daily emotion diary practice and to experiment with the radical acceptance exercise we discussed. Consider journaling about this question: "What would it mean to accept my feelings without judging them as good or bad?" You have the inner resources and growing skillset to navigate the challenges ahead, and I'm honored to support you on this journey of healing and self-discovery.`,
    prose_generated_at: '2024-12-22T14:30:00Z',
    prose_word_count: 342,
    analysis_confidence: 0.92
  },
  // ... other sessions
];
```

### Success Criteria:

#### Automated Verification:
- [ ] TypeScript compiles without errors: `cd frontend && npm run build`
- [ ] No linting errors: `cd frontend && npm run lint`
- [ ] Component imports successfully: Check no import errors in browser console

#### Manual Verification:
- [ ] Open SessionDetail in browser at `http://localhost:3000/sessions`
- [ ] Click session with prose_analysis mock data
- [ ] Verify prose displays as 5 flowing paragraphs (not structured cards)
- [ ] Verify subtle dividers appear between paragraphs
- [ ] Verify heading still says "Deep Clinical Analysis"
- [ ] Verify confidence badge displays correctly
- [ ] Test dark mode - prose readable in both themes
- [ ] Verify fonts use system-ui (consistent with rest of UI)
- [ ] Verify word count footer appears in dev mode only

**Implementation Note**: After completing Phase 2, manually test with the mock prose data. Verify readability, formatting, and visual consistency with the rest of SessionDetail. Test both light and dark modes. Once satisfied with UI, proceed to Phase 3.

---

## Phase 3: System Prompt Cleanup (Model Reference Corrections)

### Overview
Fix incorrect GPT model references in system prompts across all analyzer services. Ensure all documentation accurately reflects GPT-5.2 usage.

### Changes Required:

#### 3.1 Fix Deep Analyzer System Prompt

**File**: `backend/app/services/deep_analyzer.py`
**Changes**: Correct model references in system prompt and comments

```python
# Line 14: Update docstring
"""
Deep Clinical Analysis Service

Uses GPT-5.2 to synthesize all Wave 1 analysis outputs + patient history to generate
comprehensive, patient-facing clinical insights.
...
"""

# Lines 199-209: Update system prompt header
def _get_system_prompt(self) -> str:
    """System prompt defining the AI's role and instructions."""
    return """You are an expert clinical psychologist running on GPT-5.2, analyzing therapy sessions to provide
patient-facing insights. Your goal is to help the patient understand their progress, strengths,
and areas for growth in a compassionate, empowering way.

**YOUR CAPABILITIES (GPT-5.2):**
- You have advanced synthesis and reasoning capabilities
- You excel at integrating complex longitudinal data across multiple sessions
- You can identify subtle patterns and generate deep therapeutic insights
- You have a 400K token context window for comprehensive analysis
...
```

#### 3.2 Verify Other Analyzer System Prompts

**Files to check:**
- `backend/app/services/mood_analyzer.py` (should reference GPT-5-nano)
- `backend/app/services/topic_extractor.py` (should reference GPT-5-mini)
- `backend/app/services/breakthrough_detector.py` (should reference GPT-5)

**Changes**: Ensure all system prompts accurately state their model tier

**Example fix for mood_analyzer.py (if needed):**
```python
def _get_system_prompt(self) -> str:
    return """You are an expert mood analyst running on GPT-5-nano, optimized for fast, accurate scoring.

Your task is to analyze therapy session transcripts and assign a mood score (0.0 to 10.0)...
```

#### 3.3 Update README/Documentation

**File**: `backend/README.md` (if exists)
**Changes**: Ensure any model references are accurate

**File**: `backend/app/services/BREAKTHROUGH_DETECTION_README.md`
**Changes**: Update model references if mentioned

**File**: `.claude/CLAUDE.md`
**Changes**: Update Session Log to reflect GPT-5.2 usage

```markdown
### 2025-12-23 - Patient-Facing Prose Deep Analysis ✅
**Complete prose generation system using GPT-5.2 to transform structured analysis into compassionate narratives:**

1. **Backend Prose Generator (`app/services/prose_generator.py`)**:
   - Uses GPT-5.2 (same model as deep_analyzer) for consistent quality
   - Generates 500-750 word prose from structured deep_analysis JSON
   - Balances compassionate tone with clinical terminology
   - Auto-generates during Wave 2 pipeline

2. **Database Schema**:
   - Added `prose_analysis` (TEXT) field to therapy_sessions
   - Added `prose_generated_at` (TIMESTAMP) for tracking
   - Migration `006_add_prose_analysis.sql`

3. **API Endpoint**:
   - `POST /api/sessions/{id}/generate-prose-analysis` - Manual regeneration
   - Returns ProseAnalysisResponse with word count and timestamps

4. **Frontend Component**:
   - Created `ProseAnalysisSection.tsx` - Prose display component
   - Replaced structured DeepAnalysisSection cards with flowing prose
   - 5 unmarked paragraphs with subtle visual dividers
   - Maintains "Deep Clinical Analysis" heading

5. **System Prompt Cleanup**:
   - Fixed all incorrect model references across analyzers
   - Verified: deep_analyzer (GPT-5.2), mood_analyzer (GPT-5-nano), topic_extractor (GPT-5-mini), breakthrough_detector (GPT-5)

**Cost**: ~$0.0118 per prose generation (GPT-5.2 input/output)
```

### Success Criteria:

#### Automated Verification:
- [ ] Grep for incorrect model references: `cd backend && grep -r "GPT-4" app/services/` (should return 0 results)
- [ ] Grep for "gpt-4o" references: `cd backend && grep -r "gpt-4o" app/services/` (should return 0 results)
- [ ] Verify model config consistency: `cd backend && python app/config/model_config.py` (prints summary)

#### Manual Verification:
- [ ] Read through all system prompts in analyzer files
- [ ] Verify each mentions correct model tier (5-nano, 5-mini, 5, 5.2)
- [ ] Check documentation files for outdated model references
- [ ] Verify Session Log in CLAUDE.md is up to date

**Implementation Note**: This is a cleanup phase - no functional changes, only documentation accuracy improvements.

---

## Testing Strategy

### Unit Tests:

**New test file**: `backend/tests/test_prose_generator.py`

```python
"""Unit tests for prose generator service"""

import pytest
from app.services.prose_generator import ProseGenerator, ProseAnalysis

@pytest.mark.asyncio
async def test_prose_generation_from_mock_analysis():
    """Test prose generation from structured deep_analysis JSON"""

    mock_deep_analysis = {
        "progress_indicators": {
            "symptom_reduction": {"detected": True, "description": "Anxiety reduced", "confidence": 0.9},
            "skill_development": [{"skill": "DBT", "proficiency": "developing", "evidence": "Used TIPP"}],
            "goal_progress": [],
            "behavioral_changes": ["Improved sleep"]
        },
        "therapeutic_insights": {
            "key_realizations": ["Recognized validation-seeking pattern"],
            "patterns": ["Avoidance during stress"],
            "growth_areas": ["Assertiveness"],
            "strengths": ["Resilience", "Openness"]
        },
        "coping_skills": {
            "learned": ["TIPP", "Radical Acceptance"],
            "proficiency": {"TIPP": "developing", "Radical_Acceptance": "beginner"},
            "practice_recommendations": ["Daily emotion diary"]
        },
        "therapeutic_relationship": {
            "engagement_level": "high",
            "engagement_evidence": "Active participation",
            "openness": "very_open",
            "openness_evidence": "Shared vulnerable moments",
            "alliance_strength": "strong",
            "alliance_evidence": "Trust and collaboration"
        },
        "recommendations": {
            "practices": ["Continue TIPP practice"],
            "resources": ["DBT workbook"],
            "reflection_prompts": ["What would radical acceptance look like?"]
        }
    }

    generator = ProseGenerator()
    prose = await generator.generate_prose(
        session_id="test-session-123",
        deep_analysis=mock_deep_analysis,
        confidence_score=0.85
    )

    # Assertions
    assert isinstance(prose, ProseAnalysis)
    assert prose.session_id == "test-session-123"
    assert 400 <= prose.word_count <= 900  # Allow some margin outside target
    assert prose.paragraph_count >= 4  # At least 4 paragraphs (allow slight variation)
    assert prose.confidence_score == 0.85
    assert len(prose.prose_text) > 0
    assert "you" in prose.prose_text.lower()  # Direct address check

@pytest.mark.asyncio
async def test_prose_quality_indicators():
    """Test that prose meets quality indicators"""

    # Use same mock_deep_analysis from above
    generator = ProseGenerator()
    prose = await generator.generate_prose("test-session", mock_deep_analysis, 0.9)

    text_lower = prose.prose_text.lower()

    # Quality checks
    assert "you" in text_lower or "your" in text_lower  # Direct address
    assert not text_lower.startswith("the patient")  # Not third person
    assert "\n\n" in prose.prose_text  # Has paragraph breaks

    # Clinical terminology check (at least one should appear)
    clinical_terms = ["dbt", "cognitive", "affect", "therapeutic", "alliance", "distress tolerance"]
    assert any(term in text_lower for term in clinical_terms)
```

### Integration Tests:

**Test file**: `backend/tests/test_full_prose_pipeline.py`

```python
"""Integration test for full prose generation pipeline"""

import pytest
from app.services.analysis_orchestrator import AnalysisOrchestrator

@pytest.mark.asyncio
async def test_wave2_auto_generates_prose():
    """Test that prose auto-generates during Wave 2 pipeline"""

    # This test requires a full session with transcript
    # Use one of the 12 mock sessions from test_mood_analysis.py

    orchestrator = AnalysisOrchestrator()

    # Run full pipeline
    await orchestrator.run_full_pipeline(session_id="mock-session-1")

    # Verify prose was generated
    session = db.table("therapy_sessions").select("*").eq("id", "mock-session-1").single().execute()

    assert session.data["prose_analysis"] is not None
    assert session.data["prose_generated_at"] is not None
    assert len(session.data["prose_analysis"]) > 0

    word_count = len(session.data["prose_analysis"].split())
    assert 400 <= word_count <= 900
```

### Manual Testing Steps:

1. **Backend API Test:**
   - Start backend: `cd backend && uvicorn app.main:app --reload`
   - Create test session with deep_analysis (or use mock session)
   - Call API: `curl -X POST http://localhost:8000/api/sessions/{session_id}/generate-prose-analysis -H "Authorization: Bearer {token}"`
   - Verify response contains prose_text, word_count, paragraph_count
   - Verify database field updated: `SELECT prose_analysis FROM therapy_sessions WHERE id='{session_id}'`

2. **Frontend UI Test:**
   - Start frontend: `cd frontend && npm run dev`
   - Navigate to `http://localhost:3000/sessions`
   - Click session with prose_analysis mock data
   - Verify SessionDetail shows prose (not structured cards)
   - Verify 5 paragraphs with subtle dividers
   - Verify heading "Deep Clinical Analysis" with confidence badge
   - Test dark mode toggle - verify readability

3. **Full Pipeline Test:**
   - Upload new audio session via frontend
   - Wait for Wave 1 + Wave 2 completion
   - Open session detail
   - Verify prose_analysis auto-generated and displayed
   - Verify prose quality (compassionate tone + clinical terms)

4. **Edge Cases:**
   - Test session with minimal deep_analysis data (sparse insights)
   - Test session with rich deep_analysis (all fields populated)
   - Test API call on session without deep_analysis (should return 400 error)

## Performance Considerations

**GPT-5.2 API Latency:**
- Prose generation adds ~3-5 seconds to Wave 2 pipeline
- Non-blocking: Wave 2 completes even if prose fails
- Consider adding loading indicator in frontend if needed

**Cost Analysis:**
- Prose generation: ~$0.0118 per session
- Total per-session cost (all analyzers + prose): ~$0.0420
- For 100 sessions/day: ~$4.20/day, ~$126/month

**Database Storage:**
- TEXT field for prose_analysis (typically 3-5KB per session)
- Minimal impact on query performance
- Consider archiving old prose if sessions exceed 100K+

## Migration Notes

**No data migration needed:**
- User confirmed no existing sessions have deep_analysis yet
- All new sessions will generate prose during Wave 2
- Old sessions can manually trigger `/generate-prose-analysis` if deep_analysis exists

**Rollback plan (if needed):**
```sql
-- Rollback migration
ALTER TABLE therapy_sessions
DROP COLUMN IF EXISTS prose_analysis,
DROP COLUMN IF EXISTS prose_generated_at;
```

**Frontend rollback:**
- Revert SessionDetail.tsx to use DeepAnalysisSection
- Remove ProseAnalysisSection.tsx
- Remove prose_analysis from Session type

## References

- **Model Configuration**: `backend/app/config/model_config.py` - GPT-5.2 settings
- **Deep Analyzer Pattern**: `backend/app/services/deep_analyzer.py:86-107` - to_dict() serialization
- **Analysis Orchestrator**: `backend/app/services/analysis_orchestrator.py:421` - Wave 2 integration point
- **SessionDetail Component**: `frontend/app/patient/components/SessionDetail.tsx:209-217` - Rendering location
- **JSONB Storage Pattern**: `backend/app/services/analysis_orchestrator.py:319-326` - Database update example
