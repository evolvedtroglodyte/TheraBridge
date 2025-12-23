# Breakthrough Detection Refinement Implementation Plan

## Overview

Refine the AI-powered breakthrough detection system to identify only 2-3 major positive self-discoveries per 12 therapy sessions, down from the current 100% detection rate (12/12 sessions). Focus exclusively on transformative "aha moments" where patients learn something fundamentally new about themselves.

## Current State Analysis

**Existing Implementation:**
- `backend/app/services/breakthrough_detector.py` - GPT-5 powered breakthrough detection
- Currently detects breakthroughs in 100% of sessions (12/12)
- Averages 3 breakthrough candidates per session (35 total across all sessions)
- Stores multiple candidates per session in `breakthrough_history` table
- Uses temperature 0.3 for balanced creativity and consistency

**Test Results:**
- Session 3 (ADHD Discovery): Confidence 1.0 ✅ (Correct - major positive discovery)
- Session 7 (Attachment Pattern): Confidence 1.0 ✅ (Correct - major positive discovery)
- Sessions 1, 2, 4-6, 8-12: All marked as breakthroughs ❌ (False positives)

**Current Prompt Issues:**
- Too lenient - marks routine CBT work as breakthroughs
- Allows emotional releases without cognitive discovery
- Includes behavioral commitments that aren't self-discoveries
- No distinction between "progress" and "breakthrough"

## Desired End State

**Target Behavior:**
- Only 2-3 sessions out of 12 marked as breakthroughs (~17-25% rate)
- Maximum 1 breakthrough per session
- Only positive discoveries where patient learns something new about themselves
- Examples: ADHD recognition (Session 3), Attachment pattern discovery (Session 7)

**Verification:**
1. Run `python backend/tests/test_breakthrough_all_sessions.py`
2. Verify only Sessions 3 and 7 are marked as breakthroughs
3. Each breakthrough has both `description` (full) and `label` (2-3 words)
4. Confidence scores remain high (0.9-1.0) for true breakthroughs
5. UI displays star icon on breakthrough session cards

### Key Discoveries:
- Temperature 0.3 is optimal (balances label creativity with consistency)
- Strictness comes from prompt engineering, not temperature setting
- Single API call for both detection + label generation is most efficient
- Model: `gpt-5` (currently used, provides best reasoning for nuanced decisions)

## What We're NOT Doing

- NOT adding fallback models (if GPT-5 fails, the entire detection fails)
- NOT storing multiple breakthrough candidates (only 1 per session)
- NOT detecting negative/neutral insights (only positive discoveries)
- NOT marking emotional releases without cognitive insight
- NOT marking skill applications or routine therapy progress
- NOT changing temperature from 0.3
- NOT creating separate API calls for label generation

## Implementation Approach

**Strategy:**
1. Rewrite AI prompt to be hyper-strict about "positive discoveries"
2. Add breakthrough label generation to same API call (efficient + consistent)
3. Remove multi-candidate logic (return only highest confidence OR none)
4. Update database schema to store breakthrough_label field
5. Test iteratively until only 2 sessions (3 & 7) are marked
6. Update frontend to display labels in expanded session view

**Model Selection:**
- Use `gpt-5` for breakthrough detection (complex reasoning required)
- Keep temperature at 0.3 (optimal for label quality + consistency)
- No fallback models (fail fast if API unavailable)

---

## Phase 1: Refine AI Prompt for Strict Positive-Discovery-Only Detection

### Overview
Rewrite the GPT-5 system prompt to only detect major positive self-discoveries. Add explicit examples of what IS and IS NOT a breakthrough, focusing exclusively on transformative "aha moments."

### Changes Required:

#### 1.1 Breakthrough Detection Prompt (breakthrough_detector.py)

**File**: `backend/app/services/breakthrough_detector.py`
**Changes**: Complete rewrite of `_create_breakthrough_detection_prompt()` method

**New Prompt Criteria:**
```python
def _create_breakthrough_detection_prompt(self) -> str:
    """
    Create ultra-strict system prompt for positive discoveries only.
    """
    return """You are an expert clinical psychologist analyzing therapy session transcripts to identify MAJOR THERAPEUTIC BREAKTHROUGHS.

**CRITICAL: A breakthrough is ONLY a POSITIVE SELF-DISCOVERY where the patient learns something fundamentally NEW about themselves that opens possibilities for healing and growth.**

## What IS a Breakthrough (Positive Discoveries Only):

1. **Root Cause Discovery** - Patient identifies the underlying cause of their struggles
   - Example: "I realize my ADHD is causing my depression, not laziness"
   - Example: "My relationship anxiety comes from childhood abandonment fears"

2. **Pattern Recognition** - Patient connects past experiences to current behavior
   - Example: "My anxious attachment style mirrors how my parents loved me conditionally"
   - Example: "I self-sabotage relationships because I fear being known"

3. **Identity Insight** - Patient discovers a fundamental truth about who they are
   - Example: "I'm not broken, I'm neurodivergent"
   - Example: "My perfectionism is a trauma response, not a personality trait"

4. **Reframe Revelation** - Patient shifts from self-blame to self-understanding
   - Example: "My forgetfulness is ADHD, not personal failure"
   - Example: "My sensitivity is a strength, not a weakness"

**Requirements for a TRUE Breakthrough:**
- Must be a NEW realization (not something they already knew)
- Must be POSITIVE (opens doors, reduces shame, creates hope)
- Must be about SELF (not about others or external circumstances)
- Must be TRANSFORMATIVE (changes how they see themselves or their struggles)
- Must inspire relief, hope, or self-compassion (not just awareness)

## What is NOT a Breakthrough:

❌ **Emotional Releases** - Crying, expressing feelings, vulnerability
   - "Patient shares suicidal ideation" → This is crisis intervention, not discovery
   - "Patient cries about loneliness" → This is catharsis, not insight

❌ **Routine CBT Work** - Identifying triggers, challenging distortions
   - "Patient identifies Instagram as trigger" → This is basic CBT, not breakthrough
   - "Patient challenges negative thought" → This is skill practice, not discovery

❌ **Skill Application** - Using DBT skills, setting boundaries
   - "Patient practices DEAR MAN" → This is skill building, not insight
   - "Patient uses grounding technique" → This is coping, not discovery

❌ **Progress Updates** - Feeling better, making improvements
   - "Patient reports better sleep" → This is progress, not breakthrough
   - "Patient expresses hope" → This is mood improvement, not discovery

❌ **Values Clarification** - Deciding what matters, making choices
   - "Patient decides to come out" → This is courage, not discovery
   - "Patient values authenticity" → This is decision-making, not insight

❌ **Negative Insights** - Recognizing problems without solutions
   - "Patient realizes they're unlovable" → This is negative, not transformative
   - "Patient sees they're stuck" → This is awareness without hope

❌ **External Realizations** - Learning about others, not self
   - "Patient understands parents' perspective" → This is empathy, not self-discovery
   - "Patient recognizes relationship incompatibility" → This is about the relationship, not self

## Analysis Instructions:

1. Read the ENTIRE transcript carefully
2. Look for moments where patient says "Oh!", "Wait...", "I never realized...", "That makes sense now..."
3. Identify if this is a POSITIVE SELF-DISCOVERY (new understanding about themselves)
4. Verify it meets ALL requirements above
5. If you're unsure, it's NOT a breakthrough - be strict!

## Output Format:

If a breakthrough IS found:
```json
{
  "has_breakthrough": true,
  "breakthrough": {
    "description": "<Full description of the breakthrough moment>",
    "label": "<2-3 word concise label>",
    "confidence": <0.0-1.0>,
    "evidence": "<Specific quotes/behavior demonstrating the breakthrough>",
    "timestamp_start": <seconds>,
    "timestamp_end": <seconds>
  }
}
```

If NO breakthrough found:
```json
{
  "has_breakthrough": false,
  "breakthrough": null
}
```

**Label Guidelines:**
- 2-3 words maximum
- Captures the essence of the discovery
- Natural, non-robotic phrasing
- Examples: "ADHD Discovery", "Attachment Pattern", "Trauma Response Recognition"

**Confidence Scoring:**
- 1.0: Clear, transformative positive discovery with strong evidence
- 0.9: Very strong breakthrough with minor ambiguity
- 0.8: Solid breakthrough but less transformative
- <0.8: Probably not a genuine breakthrough - be strict!

**BE EXTREMELY SELECTIVE. Most sessions will NOT have a breakthrough. That's normal and expected.**"""
```

#### 1.2 Update JSON Response Parsing

**File**: `backend/app/services/breakthrough_detector.py`
**Changes**: Modify `_parse_breakthrough_finding()` to handle new JSON structure

```python
def _parse_breakthrough_finding(
    self,
    finding: Dict[str, Any],
    conversation: List[Dict[str, Any]]
) -> Optional[BreakthroughCandidate]:
    """
    Convert AI finding to BreakthroughCandidate object.
    Handles new JSON structure with label field.
    """
    try:
        # Check if breakthrough was found
        if not finding.get("breakthrough"):
            return None

        bt_data = finding["breakthrough"]

        # Extract speaker sequence from conversation based on timestamp
        start_time = bt_data.get("timestamp_start", 0)
        end_time = bt_data.get("timestamp_end", 0)

        relevant_turns = [
            {"speaker": turn["speaker"], "text": turn["text"]}
            for turn in conversation
            if turn["start"] >= start_time - 10 and turn["end"] <= end_time + 10
        ]

        return BreakthroughCandidate(
            timestamp_start=start_time,
            timestamp_end=end_time,
            speaker_sequence=relevant_turns,
            breakthrough_type="Positive Discovery",  # Single type now
            confidence_score=bt_data.get("confidence", 0.0),
            description=bt_data.get("description", ""),
            evidence=bt_data.get("evidence", ""),
            label=bt_data.get("label", "")  # NEW: Add label field
        )
    except Exception as e:
        print(f"Error parsing breakthrough finding: {e}")
        return None
```

#### 1.3 Update BreakthroughCandidate Dataclass

**File**: `backend/app/services/breakthrough_detector.py`
**Changes**: Add `label` field to BreakthroughCandidate

```python
@dataclass
class BreakthroughCandidate:
    """Represents a potential breakthrough moment in therapy"""
    timestamp_start: float
    timestamp_end: float
    speaker_sequence: List[Dict[str, str]]  # [{speaker, text}]
    breakthrough_type: str  # Now always "Positive Discovery"
    confidence_score: float  # 0.0 to 1.0
    description: str  # Full description
    label: str  # NEW: 2-3 word concise label for UI
    evidence: str  # What made the AI identify this as a breakthrough
```

### Success Criteria:

#### Automated Verification:
- [x] Python code passes linting: `cd backend && python -m pylint app/services/breakthrough_detector.py`
- [x] No syntax errors: `cd backend && python -c "from app.services.breakthrough_detector import BreakthroughDetector"`
- [x] Dataclass has label field: `cd backend && python -c "from app.services.breakthrough_detector import BreakthroughCandidate; print(hasattr(BreakthroughCandidate, 'label'))"`

#### Manual Verification:
- [ ] New prompt is clear and unambiguous
- [ ] Examples cover all major categories of non-breakthroughs
- [ ] Label generation guidelines are specific
- [ ] JSON structure is well-defined

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the prompt reads well before proceeding to Phase 2.

---

## Phase 2: Limit to Single Breakthrough Per Session

### Overview
Modify breakthrough detection logic to return only the highest-confidence breakthrough (or none). Remove multi-candidate storage and simplify the data model.

### Changes Required:

#### 2.1 Single Breakthrough Logic

**File**: `backend/app/services/breakthrough_detector.py`
**Changes**: Simplify `_identify_breakthrough_candidates()` to return 0 or 1 breakthrough

```python
def _identify_breakthrough_candidates(
    self,
    conversation: List[Dict[str, Any]],
    session_metadata: Optional[Dict[str, Any]] = None
) -> List[BreakthroughCandidate]:
    """
    Use AI to identify A breakthrough moment in the conversation.
    Returns a list with 0 or 1 element (keeping list for backwards compatibility).
    """
    # Prepare conversation text for AI analysis
    conversation_text = self._format_conversation_for_ai(conversation)

    # Create AI prompt for breakthrough detection
    system_prompt = self._create_breakthrough_detection_prompt()

    # Call OpenAI API
    try:
        response = openai.chat.completions.create(
            model=self.model,  # gpt-5
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this therapy session transcript:\n\n{conversation_text}"}
            ],
            temperature=0.3,  # Optimal for label quality + consistency
            response_format={"type": "json_object"}
        )

        # Parse AI response
        ai_analysis = json.loads(response.choices[0].message.content)

        # Convert AI finding to BreakthroughCandidate object
        candidate = self._parse_breakthrough_finding(ai_analysis, conversation)

        # Return list with 0 or 1 element
        return [candidate] if candidate else []

    except Exception as e:
        print(f"Error during breakthrough detection: {e}")
        return []
```

#### 2.2 Simplify Analysis Response

**File**: `backend/app/services/breakthrough_detector.py`
**Changes**: Update `analyze_session()` to handle single breakthrough

```python
def analyze_session(
    self,
    transcript: List[Dict[str, Any]],
    session_metadata: Optional[Dict[str, Any]] = None
) -> SessionBreakthroughAnalysis:
    """
    Analyze a therapy session transcript to identify A breakthrough (0 or 1).

    Args:
        transcript: List of segments with {start, end, text, speaker}
        session_metadata: Optional context (patient history, session number, etc.)

    Returns:
        SessionBreakthroughAnalysis with 0 or 1 breakthrough
    """
    # Extract conversational segments (group by speaker turns)
    conversation = self._extract_conversation_turns(transcript)

    # Use AI to identify potential breakthrough moment
    breakthrough_candidates = self._identify_breakthrough_candidates(
        conversation,
        session_metadata
    )

    # Primary breakthrough is the only breakthrough (or None)
    primary_breakthrough = breakthrough_candidates[0] if breakthrough_candidates else None

    # Generate session-level analysis
    session_summary, emotional_trajectory = self._generate_session_analysis(
        conversation,
        breakthrough_candidates
    )

    return SessionBreakthroughAnalysis(
        session_id=session_metadata.get("session_id", "unknown") if session_metadata else "unknown",
        has_breakthrough=len(breakthrough_candidates) > 0,
        breakthrough_candidates=breakthrough_candidates,  # List of 0 or 1
        primary_breakthrough=primary_breakthrough,
        session_summary=session_summary,
        emotional_trajectory=emotional_trajectory
    )
```

### Success Criteria:

#### Automated Verification:
- [ ] Code passes linting: `cd backend && python -m pylint app/services/breakthrough_detector.py`
- [ ] No syntax errors: `cd backend && python -c "from app.services.breakthrough_detector import BreakthroughDetector"`
- [ ] Test script runs without errors: `cd backend && python tests/test_breakthrough_all_sessions.py 2>&1 | head -50`

#### Manual Verification:
- [ ] Logic only returns 0 or 1 breakthrough per session
- [ ] Code is cleaner and easier to understand
- [ ] Backwards compatibility maintained (still returns list)

**Implementation Note**: After completing this phase and all automated verification passes, proceed directly to Phase 3.

---

## Phase 3: Add Database Schema for Breakthrough Label

### Overview
Update the database schema to store the breakthrough_label field alongside breakthrough_data. This allows the UI to display concise 2-3 word labels without parsing the full description.

### Changes Required:

#### 3.1 Database Migration

**File**: `backend/supabase/migrations/005_add_breakthrough_label.sql`
**Changes**: Add breakthrough_label column to therapy_sessions table

```sql
-- Migration: Add breakthrough_label field to therapy_sessions
-- Date: 2025-12-23
-- Purpose: Store concise 2-3 word AI-generated label for UI display

-- Add breakthrough_label column (nullable, since existing sessions won't have it)
ALTER TABLE therapy_sessions
ADD COLUMN IF NOT EXISTS breakthrough_label VARCHAR(50);

-- Add comment for documentation
COMMENT ON COLUMN therapy_sessions.breakthrough_label IS
'Concise 2-3 word AI-generated label for breakthrough moments (e.g., "ADHD Discovery", "Attachment Pattern")';

-- Index for filtering sessions with breakthroughs
CREATE INDEX IF NOT EXISTS idx_therapy_sessions_breakthrough_label
ON therapy_sessions(breakthrough_label)
WHERE breakthrough_label IS NOT NULL;
```

#### 3.2 Update Analysis Orchestrator

**File**: `backend/app/services/analysis_orchestrator.py`
**Changes**: Store breakthrough_label when saving breakthrough data

```python
async def _detect_breakthrough(self, session_id: str, force: bool = False):
    """Run breakthrough detection for a session"""
    # Get session
    session = await self._get_session(session_id)

    # Skip if already analyzed and not forcing
    if session.get("breakthrough_analyzed_at") and not force:
        logger.info(f"↩️ Breakthrough already analyzed for session {session_id}, skipping")
        return

    # Run detection
    analysis = self.breakthrough_detector.analyze_session(
        transcript=session["transcript"],
        session_metadata={"session_id": session_id}
    )

    # Prepare breakthrough data
    primary_breakthrough = None
    breakthrough_label = None  # NEW

    if analysis.primary_breakthrough:
        bt = analysis.primary_breakthrough
        primary_breakthrough = {
            "type": bt.breakthrough_type,
            "description": bt.description,
            "label": bt.label,  # NEW: Include label in JSONB
            "evidence": bt.evidence,
            "confidence": float(bt.confidence_score),
            "timestamp_start": float(bt.timestamp_start),
            "timestamp_end": float(bt.timestamp_end),
        }
        breakthrough_label = bt.label  # NEW: Store as separate column for easy querying

    # Update session (now includes breakthrough_label column)
    self.db.table("therapy_sessions").update({
        "has_breakthrough": analysis.has_breakthrough,
        "breakthrough_data": primary_breakthrough,
        "breakthrough_label": breakthrough_label,  # NEW
        "breakthrough_analyzed_at": datetime.utcnow().isoformat(),
    }).eq("id", session_id).execute()

    # No longer storing in breakthrough_history table
    # (we're only keeping 1 breakthrough per session now)
```

### Success Criteria:

#### Automated Verification:
- [x] Migration file is valid SQL: `cd backend && cat supabase/migrations/005_add_breakthrough_label.sql | grep -i "ALTER TABLE"`
- [x] No syntax errors in orchestrator: `cd backend && python -c "from app.services.analysis_orchestrator import AnalysisOrchestrator"`

#### Manual Verification:
- [ ] Migration can be applied to database: `cd backend && alembic upgrade head`
- [ ] breakthrough_label column exists in therapy_sessions table
- [ ] Index exists on breakthrough_label column
- [ ] No errors when running orchestrator

**Implementation Note**: After completing this phase and migration is applied, proceed to Phase 4.

---

## Phase 4: Test & Iterate on All Sessions

### Overview
Run the refined breakthrough detection algorithm on all 12 mock sessions and verify that only Sessions 3 and 7 are marked as breakthroughs. If results don't match, adjust the AI prompt and re-test.

### Changes Required:

#### 4.1 Run Full Test Suite

**File**: `backend/tests/test_breakthrough_all_sessions.py` (already exists)
**Changes**: No changes needed - script already tests all 12 sessions

**Command to run:**
```bash
cd backend
source venv/bin/activate
python tests/test_breakthrough_all_sessions.py
```

**Expected Output:**
```
================================================================================
SUMMARY
================================================================================
Total sessions analyzed: 12
Sessions with breakthroughs: 2
Breakthrough rate: 16.7%

✅ GOOD: Breakthrough count is within desired range (2-3 sessions)

Sessions with breakthroughs:
  - Session 3: session_03_alex_chen
    Type: Positive Discovery
    Label: ADHD Discovery
    Description: Alex realizes the connection between untreated ADHD and their depression and anxiety.

  - Session 7: session_07_alex_chen
    Type: Positive Discovery
    Label: Attachment Pattern
    Description: Alex connects their anxious attachment style to childhood experiences with their parents.
```

#### 4.2 Iterative Prompt Refinement (if needed)

**If test results show MORE than 2-3 breakthroughs:**

1. Identify which sessions are false positives
2. Analyze why the AI marked them as breakthroughs
3. Add specific examples to the prompt's "What is NOT a Breakthrough" section
4. Re-test until only 2-3 sessions are marked

**Example iteration:**
```python
# If Session 4 (emotional release) is marked as breakthrough, add:
❌ **Grief Processing** - Acknowledging loss, feeling sadness
   - "Patient cries about loneliness on Valentine's Day" → This is catharsis, not discovery
   - "Patient acknowledges intensity of grief" → This is emotional processing, not insight
```

**If test results show FEWER than 2 breakthroughs:**

1. Check if Session 3 or Session 7 were missed
2. Lower confidence threshold slightly (from 0.8 to 0.7)
3. Verify prompt isn't TOO strict

#### 4.3 Update Test Script Output

**File**: `backend/tests/test_breakthrough_all_sessions.py`
**Changes**: Add label to output display

```python
# Update the primary breakthrough display section
if analysis.primary_breakthrough:
    breakthrough_count += 1
    print(f"\n⭐ PRIMARY BREAKTHROUGH:")
    print(f"  Label: {analysis.primary_breakthrough.label}")  # NEW
    print(f"  Type: {analysis.primary_breakthrough.breakthrough_type}")
    print(f"  Description: {analysis.primary_breakthrough.description}")
    print(f"  Confidence: {analysis.primary_breakthrough.confidence_score:.2f}")
    print(f"  Evidence: {analysis.primary_breakthrough.evidence}")
```

### Success Criteria:

#### Automated Verification:
- [ ] Test script completes without errors: `cd backend && python tests/test_breakthrough_all_sessions.py`
- [ ] Results saved to JSON file: `test -f mock-therapy-data/breakthrough_analysis_all_sessions.json`
- [ ] JSON is valid: `cd backend && python -c "import json; json.load(open('../mock-therapy-data/breakthrough_analysis_all_sessions.json'))"`

#### Manual Verification:
- [ ] Only 2 sessions marked as breakthroughs (Sessions 3 & 7)
- [ ] Breakthrough rate is 16.7% (2/12)
- [ ] Both breakthroughs have labels ("ADHD Discovery", "Attachment Pattern" or similar)
- [ ] Both breakthroughs have confidence ≥ 0.9
- [ ] No false positives (Sessions 1, 2, 4-6, 8-12 should NOT be marked)
- [ ] Labels are natural and concise (2-3 words)

**Implementation Note**: This phase is iterative. Repeat testing and prompt refinement until success criteria are met before proceeding to Phase 5.

---

## Phase 5: Update API Endpoints & Frontend Integration

### Overview
Ensure the session API returns the new breakthrough_label field and update the frontend to display it in the expanded session view.

### Changes Required:

#### 5.1 Update Session Response Schema

**File**: `backend/app/routers/sessions.py`
**Changes**: Add breakthrough_label to session response

```python
# Find the session response model (likely SessionResponse or similar)
# Add breakthrough_label field

class SessionResponse(BaseModel):
    """Session response schema"""
    id: str
    patient_id: str
    session_date: str
    duration: int
    # ... other fields ...
    has_breakthrough: bool
    breakthrough_data: Optional[Dict[str, Any]] = None
    breakthrough_label: Optional[str] = None  # NEW
    # ... other fields ...
```

**Verify endpoint returns label:**
```python
@router.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: Client = Depends(get_db)):
    """
    Get a single session by ID.
    Returns breakthrough_label if available.
    """
    response = db.table("therapy_sessions").select("*").eq("id", session_id).single().execute()

    if not response.data:
        raise HTTPException(status_code=404, detail="Session not found")

    return response.data  # Includes breakthrough_label now
```

#### 5.2 Update Frontend Types

**File**: `frontend/app/patient/lib/types.ts`
**Changes**: Add breakthrough_label to Session type

```typescript
export interface Session {
  id: string;
  patient_id: string;
  session_date: string;
  duration: number;
  // ... other fields ...
  has_breakthrough: boolean;
  breakthrough_data?: {
    type: string;
    description: string;
    label: string;  // NEW
    evidence: string;
    confidence: number;
    timestamp_start: number;
    timestamp_end: number;
  } | null;
  breakthrough_label?: string;  // NEW: redundant but convenient
  // ... other fields ...
  milestone?: {
    title: string;  // This should map to breakthrough_label
  };
}
```

#### 5.3 Update SessionDetail Component

**File**: `frontend/app/patient/components/SessionDetail.tsx`
**Changes**: Display breakthrough label in expanded session view

```typescript
// Find the section that displays session metadata
// Add breakthrough label display

{session.has_breakthrough && session.breakthrough_label && (
  <div className="breakthrough-section" style={{
    padding: '16px',
    backgroundColor: isDark ? 'rgba(255, 202, 0, 0.1)' : 'rgba(255, 202, 0, 0.05)',
    borderLeft: `4px solid ${isDark ? '#FFE066' : '#FFCA00'}`,
    borderRadius: '8px',
    marginBottom: '24px',
  }}>
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      marginBottom: '8px',
    }}>
      <BreakthroughStar size={20} isDark={isDark} />
      <span style={{
        fontFamily: 'system-ui, -apple-system, sans-serif',
        fontSize: '14px',
        fontWeight: 600,
        color: isDark ? '#FFE066' : '#FFCA00',
        textTransform: 'uppercase',
        letterSpacing: '0.5px',
      }}>
        Breakthrough Moment
      </span>
    </div>
    <p style={{
      fontFamily: '"Inter", sans-serif',
      fontSize: '16px',
      fontWeight: 500,
      color: isDark ? '#e3e4e6' : '#1a1a1a',
      margin: 0,
    }}>
      {session.breakthrough_label}
    </p>
  </div>
)}
```

#### 5.4 Update API Client Mapping

**File**: `frontend/lib/api-client.ts`
**Changes**: Ensure breakthrough_label is included in session data mapping

```typescript
// Find the getSession or similar function
export async function getSession(sessionId: string): Promise<Session> {
  const response = await fetch(`${API_URL}/api/sessions/${sessionId}`);
  const data = await response.json();

  return {
    ...data,
    // Map breakthrough_label to milestone.title for backwards compatibility
    milestone: data.has_breakthrough && data.breakthrough_label
      ? { title: data.breakthrough_label }
      : undefined,
  };
}
```

### Success Criteria:

#### Automated Verification:
- [ ] TypeScript compiles without errors: `cd frontend && npm run typecheck`
- [ ] No linting errors: `cd frontend && npm run lint`
- [ ] Build succeeds: `cd frontend && npm run build`

#### Manual Verification:
- [ ] API returns breakthrough_label field for sessions with breakthroughs
- [ ] SessionCard displays star icon for breakthrough sessions
- [ ] SessionDetail displays breakthrough label in dedicated section
- [ ] Label text is readable and well-formatted (2-3 words)
- [ ] No breakthrough label shown for non-breakthrough sessions
- [ ] Works in both light and dark mode

**Implementation Note**: After completing this phase and all verification passes, the feature is complete and ready for production testing.

---

## Testing Strategy

### Unit Tests:
- Test BreakthroughDetector with various transcript scenarios
- Verify prompt correctly identifies positive discoveries
- Verify prompt correctly rejects non-breakthroughs
- Test label generation quality (2-3 words, natural phrasing)
- Test single breakthrough per session logic

### Integration Tests:
- Test full pipeline: upload → transcription → analysis → breakthrough detection
- Verify breakthrough_label is stored in database
- Verify API returns breakthrough_label correctly
- Test UI displays star and label for breakthrough sessions

### Manual Testing Steps:
1. Run full test suite on all 12 mock sessions
2. Verify only Sessions 3 and 7 are marked as breakthroughs
3. Check breakthrough labels are concise and meaningful
4. Upload a new therapy audio file and verify breakthrough detection works
5. Test frontend displays star icon and label correctly
6. Verify expanded session view shows breakthrough section
7. Test in both light and dark mode
8. Verify no regressions in other session features

## Performance Considerations

**API Costs:**
- GPT-5 is more expensive than GPT-4o-mini
- Single API call per session (efficient)
- Cost: ~$0.02-0.05 per session (estimate based on GPT-4o pricing)
- 12 sessions = ~$0.24-0.60 total

**Processing Time:**
- GPT-5 may be slower than GPT-4o
- Expect 5-15 seconds per session analysis
- Acceptable for background processing

**Optimization:**
- Keep temperature at 0.3 (balanced creativity + speed)
- Use JSON mode for structured output (faster parsing)
- No fallback models (fail fast to avoid cascading delays)

## Migration Notes

**Database Migration:**
```bash
cd backend
alembic upgrade head
```

**Existing Sessions:**
- Existing sessions will have NULL breakthrough_label
- Re-run breakthrough detection to populate labels:
  ```bash
  cd backend
  python scripts/reprocess_breakthroughs.py --all
  ```

**Backwards Compatibility:**
- SessionCard already checks for `milestone.title` (will use breakthrough_label)
- API continues to return `has_breakthrough` boolean
- No breaking changes to existing API contracts

## References

- Test results: `mock-therapy-data/breakthrough_analysis_all_sessions.json`
- Current implementation: `backend/app/services/breakthrough_detector.py:1-357`
- UI component: `frontend/app/patient/components/SessionCard.tsx:1-496`
- Database schema: `backend/supabase/migrations/`
- OpenAI API docs: https://platform.openai.com/docs/models

## Cost Analysis

**Per Session:**
- GPT-5 API call: ~$0.02-0.05 (based on transcript length)
- Temperature: 0.3 (optimal balance)
- JSON mode: Included (no extra cost)

**Total for 12 Sessions:**
- Initial analysis: ~$0.24-0.60
- Re-testing iterations: ~$0.50-1.00 (2-3 iterations expected)
- Total development cost: ~$0.75-1.60

**Production Scaling:**
- 100 sessions/month: ~$2-5/month
- 1000 sessions/month: ~$20-50/month
- Acceptable cost for high-value feature
