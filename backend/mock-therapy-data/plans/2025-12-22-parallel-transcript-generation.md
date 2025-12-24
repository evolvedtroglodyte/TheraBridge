# Parallel Therapy Transcript Generation Implementation Plan

## Overview

Generate 11 remaining therapy session transcripts (Sessions 2-12) using parallel agents to maximize efficiency while ensuring consistency, clinical accuracy, and compatibility with Hume AI audio generation.

## Current State Analysis

**Completed:**
- ✅ Session 1: 60-minute crisis intake with 213 segments (combined + aligned formats)
- ✅ Comprehensive master plan with 12 session outlines, clinical rationale, patient profile
- ✅ JSON schema matching audio-transcription-pipeline output format
- ✅ TTS configuration for Hume AI Octave

**What's Missing:**
- 11 remaining session transcripts (Sessions 2-12)
- Total: ~540 minutes of dialogue, ~2,400 segments
- Major events JSON, chat messages JSON, clinical documentation

**Key Constraints:**
- **Deadline**: December 22, 2025 (hackathon submission - today!)
- **Consistency**: All transcripts must match Session 1's format exactly
- **Audio compatibility**: Must work seamlessly with Hume AI TTS generation
- **Clinical accuracy**: Each session must follow therapeutic modalities and patient arc

## Desired End State

**Primary Deliverables:**
- 12 complete therapy session JSON files (Session 1 ✅ + Sessions 2-12)
- All sessions follow identical schema and formatting
- Realistic dialogue with accurate timestamps, speaker distribution, segment counts
- Ready for Hume AI audio generation (no format mismatches)

**Verification:**
- [ ] All 12 session JSON files exist in `mock-therapy-data/sessions/`
- [ ] Each session matches the `TranscriptionResult` TypeScript interface exactly
- [ ] Both `segments` (combined) and `aligned_segments` (granular) present in each
- [ ] Breakthrough sessions (7, 10, 12) contain milestone markers and breakthrough quotes
- [ ] Total timeline spans January 2025 → June 2025 with realistic gaps
- [ ] JSON is valid and parseable (no syntax errors)

## What We're NOT Doing

- ❌ Audio generation (comes after transcripts are complete)
- ❌ Frontend integration (separate task after file generation)
- ❌ Backend database insertion (happens via API after MVP demo)
- ❌ Ground truth annotations (nice-to-have, not critical for hackathon)
- ❌ Full clinical methodology documentation (session outlines are sufficient)

## Implementation Approach

### Strategy: Parallel Agent Generation with Template-Based Consistency

**Why Parallel Agents:**
- 11 sessions can be generated concurrently (10x+ faster than sequential)
- Each agent gets identical instructions ensuring consistency
- Session 1 serves as the gold standard template

**Quality Control Mechanisms:**
1. **Detailed agent prompts** with Session 1 as reference
2. **Strict schema enforcement** - agents must match exact JSON structure
3. **Session-specific clinical guidelines** from master plan
4. **Validation agent** to verify format consistency after generation

**Agent Roles:**
- **Transcript Generator Agents** (11 agents): Generate individual session transcripts
- **Validation Agent** (1 agent): Cross-check all outputs for consistency

---

## Phase 1: Parallel Transcript Generation (Sessions 2-12)

### Overview
Launch 11 parallel agents to generate Sessions 2-12 simultaneously, each following the Session 1 template with session-specific clinical content.

### Changes Required:

#### 1.1 Create Session Generation Template Prompt

**File**: `mock-therapy-data/plans/SESSION_GENERATION_TEMPLATE.md`

**Template Structure:**
```markdown
# Session [N] Generation Instructions

## Your Task
Generate a complete, realistic therapy session transcript matching the exact format of Session 1.

## Session Details
- **Session Number**: [N]
- **Date**: [YYYY-MM-DD]
- **Duration**: [X] minutes ([X*60] seconds)
- **Modality**: [CBT/DBT/ACT/Psychodynamic/etc.]
- **Clinical Focus**: [From master plan]

## Clinical Content (from Master Plan)
[Copy session outline from master implementation plan]

**Key Dialogue Moments:**
- Timestamp ~XXs: [Quote from plan]
- Timestamp ~YYs: [Quote from plan]
- [BREAKTHROUGH if applicable]: Timestamp ~ZZs: [Breakthrough quote]

## JSON Format Requirements

**CRITICAL**: Your output must be valid JSON matching this EXACT structure:

```json
{
  "id": "session_0[N]_alex_chen",
  "status": "completed",
  "filename": "session_0[N]_YYYY-MM-DD.mp3",
  "metadata": { ... },
  "performance": { ... },
  "speakers": [ ... ],
  "segments": [ ... ],           // Combined speaker turns
  "aligned_segments": [ ... ],   // Granular utterances
  "quality": { ... },
  "created_at": "YYYY-MM-DDTHH:MM:SSZ",
  "completed_at": "YYYY-MM-DDTHH:MM:SSZ"
}
```

**Reference Session 1** at: `mock-therapy-data/sessions/session_01_crisis_intake.json`

## Speaker Distribution Guidelines
- **SPEAKER_00** (Therapist): 35-45% of total duration
- **SPEAKER_01** (Alex, Patient): 55-65% of total duration
- Therapist: Longer turns in psychoeducation, shorter in active listening
- Patient: Variable turn lengths, longer monologues when processing emotions

## Dialogue Realism Checklist
✅ Include verbal markers: "um", "like", "you know", "I mean"
✅ Hesitations and pauses in patient speech (especially emotional moments)
✅ Therapist uses validation phrases: "That makes sense", "I hear you", "That's really hard"
✅ Natural interruptions and incomplete sentences where appropriate
✅ Cultural language patterns for Alex (Asian-American, Gen-Z)
✅ Non-binary pronouns (they/them) used correctly throughout

## Timestamp Calculation
- Start at 0.0 seconds
- Average speaking rate: 150 words per minute = 2.5 words per second
- Add natural pauses between turns (1-3 seconds)
- Longer pauses (5-10 seconds) during emotional moments
- For aligned_segments: Break combined turns every 15-30 seconds

## Quality Checks Before Submission
- [ ] Valid JSON syntax (no trailing commas, proper escaping)
- [ ] Both `segments` and `aligned_segments` arrays populated
- [ ] Total duration matches session length exactly
- [ ] Speaker distribution within acceptable range
- [ ] All required fields present (id, status, filename, metadata, etc.)
- [ ] Timestamps are sequential and non-overlapping
- [ ] Breakthrough quote present (if milestone session)
- [ ] Clinical content follows session outline from master plan
```

#### 1.2 Launch Parallel Transcript Generator Agents

**Agent Configuration:**

```typescript
// Pseudo-code for agent orchestration
const sessionSpecs = [
  { num: 2, date: "2025-01-17", duration: 50, modality: "CBT", focus: "Stabilization" },
  { num: 3, date: "2025-01-24", duration: 50, modality: "ACT", focus: "Values Clarification" },
  { num: 4, date: "2025-01-31", duration: 45, modality: "CBT", focus: "Cognitive Restructuring" },
  { num: 5, date: "2025-02-14", duration: 50, modality: "DBT", focus: "Emotion Regulation" },
  { num: 6, date: "2025-02-28", duration: 45, modality: "Psychodynamic", focus: "Attachment Patterns" },
  { num: 7, date: "2025-03-07", duration: 50, modality: "ADHD Coaching", focus: "BREAKTHROUGH", milestone: true },
  { num: 8, date: "2025-03-21", duration: 45, modality: "MBCT", focus: "Mindfulness" },
  { num: 9, date: "2025-04-04", duration: 50, modality: "IPT", focus: "Interpersonal Therapy" },
  { num: 10, date: "2025-04-18", duration: 50, modality: "Integration", focus: "BREAKTHROUGH", milestone: true },
  { num: 11, date: "2025-05-02", duration: 30, modality: "Crisis DBT", focus: "Emergency Panic Attack" },
  { num: 12, date: "2025-05-16", duration: 50, modality: "Integration", focus: "BREAKTHROUGH", milestone: true }
];

// Launch agents in parallel
const agents = sessionSpecs.map(spec =>
  spawnTranscriptGeneratorAgent({
    sessionNumber: spec.num,
    templatePath: "SESSION_GENERATION_TEMPLATE.md",
    masterPlanPath: "IMPLEMENTATION_PLAN.md",
    referencePath: "sessions/session_01_crisis_intake.json",
    outputPath: `sessions/session_${String(spec.num).padStart(2, '0')}_*.json`,
    spec: spec
  })
);
```

**Agent Prompt Structure:**

Each agent receives:
1. **Session Generation Template** (formatting rules)
2. **Session-specific outline** (from master plan)
3. **Session 1 reference** (format gold standard)
4. **Patient profile** (Alex Chen background)
5. **Clinical guidelines** (therapeutic techniques for this modality)

**Agent Instructions:**
```
You are generating Session [N] for Alex Chen's therapy journey.

REFERENCE FILES:
- Format template: SESSION_GENERATION_TEMPLATE.md
- Session outline: [Extracted from IMPLEMENTATION_PLAN.md, Session N section]
- Format example: session_01_crisis_intake.json
- Patient background: [Alex Chen profile]

YOUR TASK:
1. Read the session outline for Session [N]
2. Generate realistic dialogue following the clinical arc
3. Create both `segments` (combined) and `aligned_segments` (granular) arrays
4. Calculate accurate timestamps based on dialogue length
5. Output valid JSON matching Session 1's exact structure
6. Include breakthrough moment if this is Session 7, 10, or 12

CRITICAL REQUIREMENTS:
- Valid JSON syntax (test with JSON parser before submitting)
- Exact schema match with Session 1
- Realistic dialogue with verbal markers and hesitations
- Accurate timestamp calculations
- Speaker distribution: Therapist 35-45%, Patient 55-65%
- Include performance metrics (processing times, quality stats)

OUTPUT FORMAT:
Save your generated transcript as:
`sessions/session_[NN]_[description].json`

Where:
- NN = zero-padded session number (02, 03, etc.)
- description = kebab-case focus (e.g., "stabilization", "adhd-breakthrough")
```

### Success Criteria:

#### Automated Verification:
- [ ] 11 new JSON files exist in `mock-therapy-data/sessions/` directory
- [ ] All JSON files parse without syntax errors: `python3 -c "import json; [json.load(open(f'sessions/session_{i:02d}_*.json')) for i in range(2, 13)]"`
- [ ] File naming convention followed: `session_[NN]_[description].json`
- [ ] Each file size > 50KB (indicates full transcript, not stub)
- [ ] All files contain both "segments" and "aligned_segments" keys

#### Manual Verification:
- [ ] Each session's dialogue follows its clinical outline from master plan
- [ ] Breakthrough sessions (7, 10, 12) contain milestone markers at correct timestamps
- [ ] Speaker distribution is realistic (therapist 35-45%, patient 55-65%)
- [ ] Timestamps are sequential within each session
- [ ] Dialogue includes realistic verbal markers and hesitations
- [ ] Total duration matches specified session length (±30 seconds acceptable)
- [ ] Clinical content is therapeutically sound and follows modality conventions

**Implementation Note**: After all agents complete, proceed immediately to Phase 2 validation. Do not wait for manual review.

---

## Phase 2: Format Validation & Consistency Check

### Overview
Validate all 12 generated transcripts (Session 1 + Sessions 2-12) to ensure identical formatting, schema compliance, and audio generation compatibility.

### Changes Required:

#### 2.1 Create Validation Agent Prompt

**Agent Task**: Cross-check all 12 session files for consistency and identify any format deviations.

**Validation Checklist:**

```markdown
# Transcript Validation Agent Instructions

## Your Task
Validate all 12 therapy session transcripts for format consistency and audio generation compatibility.

## Validation Steps

### 1. Schema Validation
For each session file (session_01 through session_12):

✅ Check required top-level keys exist:
- id, status, filename, metadata, performance, speakers, segments, aligned_segments, quality, created_at, completed_at

✅ Validate metadata structure:
- source_file (string), file_size_mb (number), duration (number), language (string), timestamp (string), pipeline_type (string)

✅ Validate performance structure:
- total_processing_time_seconds, preprocessing_time_seconds, transcription_time_seconds, diarization_time_seconds, alignment_time_seconds (all numbers)

✅ Validate speakers array:
- Each speaker has: id, label, total_duration, segment_count
- Exactly 2 speakers: SPEAKER_00 and SPEAKER_01

✅ Validate segments array (combined):
- Each segment has: start, end, text, speaker, speaker_id
- start < end for all segments
- Segments are chronologically ordered

✅ Validate aligned_segments array (granular):
- Same structure as segments
- More segments than combined array (should be 1.5-3x more)

✅ Validate quality object:
- total_segments, speaker_segment_distribution, unknown_segments_count, unknown_segments_percent

### 2. Cross-Session Consistency Check

Compare all sessions and flag deviations:

✅ **Speaker labeling**: All sessions use SPEAKER_00 (therapist) and SPEAKER_01 (patient)
✅ **Timestamp format**: All use float seconds (e.g., 123.45)
✅ **Date progression**: Sessions are chronologically ordered (Jan 10 → May 16, 2025)
✅ **Filename pattern**: session_[NN]_[description].json
✅ **Patient name consistency**: All sessions reference "Alex Chen" with they/them pronouns
✅ **Therapist name consistency**: All sessions reference "Dr. Rodriguez"

### 3. Audio Generation Compatibility

Ensure Hume AI TTS can process these files:

✅ **Text encoding**: All text fields use UTF-8, no special characters that break TTS
✅ **Segment length**: No segments exceed 500 characters (Hume AI limit for some models)
✅ **Speaker consistency**: speaker and speaker_id fields match exactly
✅ **Timestamp gaps**: No overlapping segments (end[n] ≤ start[n+1])

### 4. Clinical Content Spot-Check

Verify breakthrough sessions contain milestones:

✅ **Session 7** (ADHD Breakthrough):
- Timestamp ~1935-2135s contains breakthrough quote: "Oh my god. I'm not lazy. My brain just works differently."
- Segment exists in both segments and aligned_segments arrays

✅ **Session 10** (Attachment Insight):
- Timestamp ~1830-2520s contains breakthrough quote about attachment patterns
- Emotional markers present (tears, realization language)

✅ **Session 12** (Identity Integration):
- Timestamp ~2430-2700s contains breakthrough quote about identity integration
- Termination themes present (progress review, relapse prevention)

## Output Format

Generate a validation report as JSON:

```json
{
  "validation_timestamp": "2025-12-22T[HH:MM:SS]Z",
  "total_sessions_checked": 12,
  "sessions": [
    {
      "session_id": "session_01_alex_chen",
      "file_path": "sessions/session_01_crisis_intake.json",
      "schema_valid": true,
      "format_issues": [],
      "audio_compatible": true,
      "clinical_content_verified": true
    },
    // ... entries for sessions 2-12
  ],
  "cross_session_checks": {
    "speaker_labeling_consistent": true,
    "chronological_order": true,
    "patient_name_consistent": true,
    "therapist_name_consistent": true
  },
  "summary": {
    "all_sessions_valid": true,
    "sessions_with_errors": 0,
    "ready_for_audio_generation": true
  },
  "errors": [
    // List any format issues found
  ]
}
```

Save this report to: `mock-therapy-data/validation_report.json`

## If Errors Found

For each session with errors:
1. Document the specific issue in validation report
2. If critical (schema mismatch, invalid JSON), flag for regeneration
3. If minor (typo, small timestamp gap), note for manual fix
```

#### 2.2 Launch Validation Agent

**Command:**
```bash
# Spawn validation agent
spawnValidationAgent({
  taskDescription: "Validate all 12 therapy session transcripts",
  inputDirectory: "mock-therapy-data/sessions/",
  outputReport: "mock-therapy-data/validation_report.json",
  validationPromptPath: "plans/VALIDATION_AGENT_PROMPT.md"
})
```

### Success Criteria:

#### Automated Verification:
- [ ] Validation report JSON exists: `mock-therapy-data/validation_report.json`
- [ ] Report is valid JSON and parseable
- [ ] `summary.all_sessions_valid` is `true`
- [ ] `summary.sessions_with_errors` is `0`
- [ ] `summary.ready_for_audio_generation` is `true`

#### Manual Verification:
- [ ] Review validation report for any flagged issues
- [ ] Spot-check 2-3 sessions manually by opening JSON files
- [ ] Verify breakthrough quotes are present in Sessions 7, 10, 12
- [ ] Confirm timeline spans January → June 2025 with realistic gaps

**Implementation Note**: If validation fails (errors > 0), regenerate problem sessions before proceeding to Phase 3.

---

## Phase 3: Supporting Deliverables Generation

### Overview
Generate major_events.json, chat_messages.json, and integration documentation now that all session transcripts are complete.

### Changes Required:

#### 3.1 Generate major_events.json

**File**: `mock-therapy-data/timeline/major_events.json`

**Content**: 10 major events (7 external + 3 in-session breakthroughs) with context pointers to sessions and chat messages.

**Generation Method**: Manual creation based on master plan (already defined in implementation plan above).

**Structure**:
```json
[
  {
    "id": "event_01",
    "type": "external_life_event",
    "title": "Academic probation warning",
    "date": "2025-01-15",
    "summary": "...",
    "context": {
      "source": "session",
      "session_id": "session_02",
      "timestamp_start": 480.0,
      "timestamp_end": 1200.0
    }
  },
  // ... 9 more events
]
```

#### 3.2 Generate chat_messages.json

**File**: `mock-therapy-data/timeline/chat_messages.json`

**Content**: 4 chat threads (ADHD med start, panic attack crisis, relationship update, academic progress).

**Structure**:
```json
[
  {
    "id": "chat_004",
    "timestamp": "2025-03-08T09:47:00Z",
    "sender": "patient",
    "text": "hey!! so i started the adderall yesterday like we talked about",
    "related_event_id": "event_04",
    "session_context": "session_07"
  },
  // ... more messages
]
```

#### 3.3 Create INTEGRATION_GUIDE.md

**File**: `mock-therapy-data/INTEGRATION_GUIDE.md`

**Content**: Step-by-step instructions for integrating generated transcripts into frontend `mockData.ts`.

**Sections**:
1. File placement instructions
2. Import statements needed
3. Transform functions (TranscriptionResult → SessionData)
4. Timeline merging logic
5. Testing verification steps

### Success Criteria:

#### Automated Verification:
- [ ] `timeline/major_events.json` exists and is valid JSON
- [ ] `timeline/chat_messages.json` exists and is valid JSON
- [ ] `INTEGRATION_GUIDE.md` exists with all sections
- [ ] All files pass JSON linting: `python3 -m json.tool [file] > /dev/null`

#### Manual Verification:
- [ ] major_events.json contains all 10 events from master plan
- [ ] Each event has correct date, context pointers, and clinical significance
- [ ] chat_messages.json contains realistic Gen-Z texting language
- [ ] INTEGRATION_GUIDE.md is clear and actionable for frontend integration

---

## Testing Strategy

### Validation Tests

**Schema Validation**:
```python
import json
import jsonschema

# Load schema (derived from TypeScript interface)
with open('schemas/transcription_result_schema.json') as f:
    schema = json.load(f)

# Validate each session
for i in range(1, 13):
    with open(f'sessions/session_{i:02d}_*.json') as f:
        session = json.load(f)
        jsonschema.validate(instance=session, schema=schema)
        print(f"✅ Session {i} valid")
```

**Consistency Tests**:
```python
# Check speaker labeling consistency
sessions = [json.load(open(f'sessions/session_{i:02d}_*.json')) for i in range(1, 13)]

speaker_ids = set()
for session in sessions:
    for speaker in session['speakers']:
        speaker_ids.add(speaker['id'])

assert speaker_ids == {'SPEAKER_00', 'SPEAKER_01'}, "Inconsistent speaker labeling!"
print("✅ Speaker labeling consistent across all sessions")
```

**Timeline Continuity Test**:
```python
# Verify chronological order
dates = [session['created_at'] for session in sessions]
assert dates == sorted(dates), "Sessions not in chronological order!"
print("✅ Sessions in correct chronological order")
```

### Manual Testing Steps

1. **Open Session 7 JSON** → Verify breakthrough quote exists at ~1935s
2. **Open Session 11 JSON** → Verify crisis/emergency tone in dialogue
3. **Open Session 12 JSON** → Verify termination themes and progress review
4. **Compare Sessions 1 & 7** → Confirm identical schema structure
5. **Check major_events.json** → Verify all 10 events present with correct context pointers

### Audio Generation Compatibility Test

**Hume AI Test Script**:
```python
import json

# Load a sample session
with open('sessions/session_07_adhd_breakthrough.json') as f:
    session = json.load(f)

# Check segment lengths (Hume AI limit: 500 chars for some models)
for seg in session['aligned_segments']:
    assert len(seg['text']) <= 500, f"Segment too long: {len(seg['text'])} chars"

# Check timestamp validity
for i, seg in enumerate(session['aligned_segments'][:-1]):
    next_seg = session['aligned_segments'][i+1]
    assert seg['end'] <= next_seg['start'], f"Overlapping segments at {i}"

print("✅ Session 7 ready for Hume AI audio generation")
```

---

## Performance Considerations

**Parallel Generation Benefits**:
- **Sequential approach**: 11 sessions × 30 min/session = 5.5 hours
- **Parallel approach**: Max session time (~60 min) + validation (15 min) = ~1.25 hours
- **Speedup**: 4.4x faster

**Token Usage Estimate**:
- Session 1 consumed: ~16K tokens
- 11 remaining sessions: ~176K tokens needed
- Current budget: ~92K tokens remaining
- **Conclusion**: Single conversation insufficient; parallel agents OR multiple conversation windows required

**Risk Mitigation**:
- If any session fails generation, regenerate that specific session only
- Validation agent catches errors before audio generation phase
- Session 1 serves as gold standard reference for all agents

---

## Migration Notes

**Not Applicable** - This is net-new content generation, no existing data to migrate.

**Post-Generation Steps**:
1. Run validation agent → fix any errors
2. Generate supporting files (major_events.json, chat_messages.json)
3. Test one session with Hume AI to confirm audio compatibility
4. Integrate into frontend `mockData.ts` using INTEGRATION_GUIDE.md
5. Generate audio files for all 12 sessions (separate task)

---

## References

- **Master implementation plan**: `mock-therapy-data/IMPLEMENTATION_PLAN.md` (created earlier in conversation)
- **Session 1 reference**: `mock-therapy-data/sessions/session_01_crisis_intake.json`
- **Patient profile**: Alex Chen (23, non-binary, Chinese-American, GAD+MDD+ADHD)
- **Audio pipeline schema**: `audio-transcription-pipeline/ui-web/frontend/src/types/transcription.ts`
- **Hume AI documentation**: https://docs.hume.ai/text-to-speech

---

## Execution Summary

**Total Phases**: 3
**Estimated Time**: 1.5-2 hours (with parallel agents)
**Dependencies**: Session 1 must be complete before starting (✅ Done)

**Critical Path**:
1. Launch 11 parallel transcript generator agents → 60-90 min
2. Run validation agent → 15 min
3. Generate supporting files → 15 min
4. **Total**: ~1.5 hours to completion

**Deliverables Upon Completion**:
- ✅ 12 complete therapy session transcripts
- ✅ Validation report confirming format consistency
- ✅ major_events.json (10 events)
- ✅ chat_messages.json (4 threads)
- ✅ INTEGRATION_GUIDE.md
- ✅ Ready for Hume AI audio generation
- ✅ Ready for frontend integration

**Success Metrics**:
- All 12 sessions match Session 1 format exactly
- Validation report shows 0 errors
- Breakthrough sessions contain milestone markers
- Timeline spans 6 months (Jan-June 2025) realistically
- Compatible with Hume AI TTS API
