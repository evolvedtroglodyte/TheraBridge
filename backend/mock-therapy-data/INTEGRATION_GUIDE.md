# Integration Guide: Mock Therapy Data for TherapyBridge MVP

**Patient:** Alex Chen
**Timeline:** January 10 - May 30, 2025 (5 months, 12 sessions)
**Date Created:** December 22, 2025
**Data Format:** Audio Transcription Pipeline Output (JSON)

---

## Table of Contents

1. [Overview](#overview)
2. [Data Structure](#data-structure)
3. [File Locations](#file-locations)
4. [Frontend Integration](#frontend-integration)
5. [Backend Integration](#backend-integration)
6. [Audio Generation Next Steps](#audio-generation-next-steps)
7. [Patient Profile Summary](#patient-profile-summary)
8. [Session Timeline](#session-timeline)
9. [Major Events Reference](#major-events-reference)
10. [Troubleshooting](#troubleshooting)

---

## Overview

This mock dataset represents a complete patient journey through 5 months of therapy, designed to showcase all features of the TherapyBridge frontend dashboard at `http://localhost:3000/patient/dashboard-v3`.

**What's included:**
- ✅ 12 full-length therapy session transcripts (45-60 minutes each)
- ✅ 10 major life events with context for AI chat
- ✅ 4 realistic chat message threads with Dobby (AI companion)
- ✅ Complete patient profile with diagnoses, medications, and progress metrics
- ✅ Clinical authenticity: Real therapeutic modalities, techniques, and progression

**What's NOT included (yet):**
- ⏳ Audio files (to be generated via Hume AI TTS)
- ⏳ Database migration scripts
- ⏳ Backend API seed data

---

## Data Structure

### Session Transcripts (`sessions/*.json`)

Each session file follows the `TranscriptionResult` interface from `audio-transcription-pipeline`:

```typescript
interface TranscriptionResult {
  id: string;                    // "session_01_alex_chen"
  status: string;                // "completed"
  filename: string;              // "session_01_2025-01-10.mp3"
  metadata: {
    source_file: string;         // Upload path
    file_size_mb: number;
    duration: number;            // Total seconds
    language: string;
    timestamp: string;
    pipeline_type: string;       // "CPU_API" or "GPU"
  };
  performance: {
    total_processing_time_seconds: number;
    preprocessing_time_seconds: number;
    transcription_time_seconds: number;
    diarization_time_seconds: number;
    alignment_time_seconds: number;
  };
  speakers: Array<{
    id: string;                  // "SPEAKER_00" (therapist) or "SPEAKER_01" (patient)
    label: string;
    total_duration: number;
    segment_count: number;
  }>;
  segments: Array<{              // Combined speaker turns for display
    start: number;
    end: number;
    text: string;
    speaker: string;
    speaker_id: string;
  }>;
  aligned_segments: Array<{      // Granular utterances for highlighting
    start: number;
    end: number;
    text: string;
    speaker: string;
    speaker_id: string;
  }>;
  quality: {
    total_segments: number;
    speaker_segment_distribution: Record<string, number>;
    unknown_segments_count: number;
    unknown_segments_percent: number;
  };
}
```

**Key distinctions:**
- `segments`: Combined speaker turns (60-95 segments per session) - use for display
- `aligned_segments`: Granular utterances (150-220 segments per session) - use for highlighting and precise navigation

**Speaker mapping:**
- `SPEAKER_00`: Dr. Sarah Mitchell (therapist) - 35-45% of session duration
- `SPEAKER_01`: Alex Chen (patient) - 55-65% of session duration

---

## File Locations

```
mock-therapy-data/
├── sessions/
│   ├── session_01_crisis_intake.json           (60 min)
│   ├── session_02_emotional_regulation.json    (45 min)
│   ├── session_03_adhd_discovery.json          (50 min)
│   ├── session_04_medication_start.json        (45 min)
│   ├── session_05_family_conflict.json         (55 min)
│   ├── session_06_spring_break_hope.json       (50 min)
│   ├── session_07_dating_anxiety.json          (50 min)
│   ├── session_08_relationship_boundaries.json (45 min)
│   ├── session_09_coming_out_preparation.json  (60 min)
│   ├── session_10_coming_out_aftermath.json    (55 min)
│   ├── session_11_rebuilding.json              (50 min)
│   └── session_12_thriving.json                (50 min)
│
├── major_events.json          # 10 life events with AI context
├── chat_messages.json         # 4 realistic chat threads
├── INTEGRATION_GUIDE.md       # This file
└── plans/
    └── 2025-12-22-parallel-transcript-generation.md
```

---

## Frontend Integration

### Dashboard v3 Components

#### 1. **Session List / Timeline**

**Data Source:** All 12 session files in `sessions/`

**Display Requirements:**
- Sort by date ascending (January 10 → May 30, 2025)
- Show session number, date, duration, mood indicator
- Milestones to highlight:
  - Session 6: First expression of hope
  - Session 12: Clinical remission achieved

**Code Integration:**
```typescript
// Load all sessions
const sessions = await Promise.all([
  fetch('/mock-therapy-data/sessions/session_01_crisis_intake.json'),
  fetch('/mock-therapy-data/sessions/session_02_emotional_regulation.json'),
  // ... etc
]);

// Extract metadata for timeline
const timeline = sessions.map(s => ({
  id: s.id,
  date: extractDateFromFilename(s.filename),
  duration: s.metadata.duration,
  therapist: s.speakers.find(sp => sp.id === 'SPEAKER_00'),
  patient: s.speakers.find(sp => sp.id === 'SPEAKER_01'),
}));
```

#### 2. **Session Detail / Transcript Viewer**

**Data Source:** Individual session file (e.g., `session_03_adhd_discovery.json`)

**Display Options:**
- **Compact mode:** Use `segments` array (combined speaker turns)
- **Detailed mode:** Use `aligned_segments` array (granular highlighting)

**Speaker Labels:**
Replace generic labels with names:
```typescript
const speakerNames = {
  'SPEAKER_00': 'Dr. Sarah Mitchell',
  'SPEAKER_01': 'Alex Chen'
};
```

**Code Integration:**
```typescript
// Transcript viewer component
{session.segments.map(segment => (
  <div key={segment.start} className={segment.speaker_id}>
    <span className="speaker-label">
      {speakerNames[segment.speaker_id]}
    </span>
    <span className="timestamp">
      {formatTime(segment.start)}
    </span>
    <p className="text">{segment.text}</p>
  </div>
))}
```

#### 3. **Major Events Timeline**

**Data Source:** `major_events.json`

**Display Requirements:**
- Mixed timeline: Sessions + Major events sorted chronologically
- Event categories: relationship, mental_health, treatment, family, personal_growth, identity, academic
- Severity indicators: high (red), medium (yellow), low (green)

**Code Integration:**
```typescript
const events = await fetch('/mock-therapy-data/major_events.json');

// Filter events by category
const familyEvents = events.events.filter(e => e.category === 'family');

// Link events to sessions
const eventWithSession = events.events.map(e => ({
  ...e,
  relatedSession: sessions.find(s => e.related_sessions.includes(s.id))
}));
```

#### 4. **AI Chat Interface (Dobby)**

**Data Source:** `chat_messages.json`

**Display Requirements:**
- Show conversation threads with realistic Gen-Z messaging style
- Display patient messages (left-aligned) vs AI responses (right-aligned)
- Include timestamps, typing indicators, emoji support

**Context Injection:**
When user opens chat, inject relevant context from `major_events.json` into system prompt:
```typescript
const systemContext = `
Patient: Alex Chen, 23, non-binary (they/them)
Recent events: ${recentEvents.map(e => e.summary).join('\n')}
Current medications: Adderall XR 15mg
Last session: ${lastSession.date} - ${lastSession.focus}
`;
```

**Code Integration:**
```typescript
const chatThreads = await fetch('/mock-therapy-data/chat_messages.json');

// Render thread
{thread.messages.map(msg => (
  <div key={msg.id} className={msg.sender === 'patient' ? 'left' : 'right'}>
    <p>{msg.content}</p>
    <span className="timestamp">{formatTime(msg.timestamp)}</span>
    {msg.metadata.emoji_used && <span>💙</span>}
  </div>
))}
```

#### 5. **Progress Metrics Dashboard**

**Data Source:** Extracted from session transcripts (not explicit in JSON, but mentioned in clinical content)

**Key Metrics to Display:**

| Metric | Session 1 (Jan 10) | Session 12 (May 30) | Change |
|--------|---------------------|----------------------|--------|
| PHQ-9 (Depression) | 18 (Moderate-Severe) | 7 (Minimal) | ↓ 61% |
| GAD-7 (Anxiety) | 16 (Moderate) | 7 (Minimal) | ↓ 56% |
| Medication | None | Adderall XR 15mg | ✅ Started |
| Relationship Status | Single (Recent Breakup) | Dating Jordan (2 months) | ✅ Improved |
| Family Acceptance | Not out | Out + Father texting | ✅ Progress |

**Visualization Ideas:**
- Line chart: PHQ-9 and GAD-7 scores over time
- Progress bars: Treatment goals completion
- Milestone badges: ADHD diagnosis, medication start, coming out, publication

---

## Backend Integration

### Database Schema Requirements

#### Users Table
```sql
-- Alex Chen's user record
INSERT INTO users (id, email, first_name, last_name, role, is_verified)
VALUES (
  'alex_chen_2025',
  'alex.chen@university.edu',
  'Alex',
  'Chen',
  'patient',
  true
);
```

#### Therapy Sessions Table
```sql
-- Session records (one per transcript file)
INSERT INTO therapy_sessions (
  id, user_id, session_date, duration_seconds,
  audio_file_path, transcript_file_path, status
)
VALUES (
  'session_01_alex_chen',
  'alex_chen_2025',
  '2025-01-10',
  3600,
  'uploads/audio/alex_chen/session_01_2025-01-10.mp3',
  'mock-therapy-data/sessions/session_01_crisis_intake.json',
  'completed'
);
-- Repeat for all 12 sessions
```

#### Major Events Table
```sql
CREATE TABLE major_events (
  id VARCHAR PRIMARY KEY,
  patient_id VARCHAR REFERENCES users(id),
  event_date DATE,
  title VARCHAR,
  category VARCHAR,
  severity VARCHAR,
  impact_score INT,
  summary TEXT,
  context_for_ai_chat TEXT,
  related_sessions JSON
);

-- Load from major_events.json
-- Use event.related_sessions to link to therapy_sessions table
```

#### Chat Messages Table
```sql
CREATE TABLE chat_messages (
  id VARCHAR PRIMARY KEY,
  thread_id VARCHAR,
  patient_id VARCHAR REFERENCES users(id),
  timestamp TIMESTAMPTZ,
  sender VARCHAR, -- 'patient' or 'ai'
  content TEXT,
  metadata JSONB
);

-- Load from chat_messages.json
```

### Backend API Endpoints

#### GET `/api/patients/{patient_id}/sessions`
```json
{
  "patient_id": "alex_chen_2025",
  "total_sessions": 12,
  "sessions": [
    {
      "id": "session_01_alex_chen",
      "date": "2025-01-10",
      "duration": 3600,
      "transcript_url": "/api/sessions/session_01_alex_chen/transcript"
    }
    // ... etc
  ]
}
```

#### GET `/api/sessions/{session_id}/transcript`
```json
// Return full TranscriptionResult JSON from session file
```

#### GET `/api/patients/{patient_id}/events`
```json
{
  "patient_id": "alex_chen_2025",
  "events": [
    // Full major_events.json structure
  ]
}
```

#### GET `/api/patients/{patient_id}/chat/{thread_id}`
```json
{
  "thread_id": "chat_thread_01_crisis_night",
  "messages": [
    // Full chat thread from chat_messages.json
  ]
}
```

#### POST `/api/chat`
**Request:**
```json
{
  "patient_id": "alex_chen_2025",
  "message": "im feeling anxious about my relationship",
  "context": {
    "recent_events": ["event_06_met_jordan"],
    "last_session": "session_08_relationship_boundaries"
  }
}
```

**Response:**
```json
{
  "ai_response": "I hear you're feeling anxious about your relationship with Jordan. Is this the anxious attachment pattern we talked about in your last session?",
  "suggested_skills": ["DEAR MAN", "5-4-3-2-1 grounding"],
  "crisis_detected": false
}
```

---

## Audio Generation Next Steps

### Using Hume AI Octave TTS

**Voice Selection:**
- **Dr. Sarah Mitchell (SPEAKER_00):** Male voice (non-traditional therapist gender)
- **Alex Chen (SPEAKER_01):** Non-binary/androgynous voice

**Generation Script:**
```bash
# Pseudocode for audio generation
for session in sessions/*.json; do
  for segment in session.aligned_segments; do
    voice = (segment.speaker_id == "SPEAKER_00") ? "male_therapist" : "nonbinary_patient"

    hume-tts \
      --text "$segment.text" \
      --voice "$voice" \
      --output "audio/${session.id}/${segment.start}-${segment.end}.mp3"
  done

  # Combine segments with silence gaps
  ffmpeg -f concat -i segment_list.txt \
    -c copy "audio/${session.filename}"
done
```

**Validation Requirements:**
- ✅ Total audio duration matches `metadata.duration`
- ✅ Segment timestamps align with audio timestamps
- ✅ No gaps longer than 1 second between segments
- ✅ Speaker voices are distinguishable
- ✅ UTF-8 encoding preserved in speech synthesis

### Audio File Paths

After generation, audio files should be placed at:
```
backend/uploads/audio/alex_chen/
├── session_01_2025-01-10.mp3
├── session_02_2025-01-17.mp3
├── session_03_2025-01-31.mp3
├── session_04_2025-02-14.mp3
├── session_05_2025-02-28.mp3
├── session_06_2025-03-14.mp3
├── session_07_2025-04-04.mp3
├── session_08_2025-04-18.mp3
├── session_09_2025-05-02.mp3
├── session_10_2025-05-09.mp3
├── session_11_2025-05-16.mp3
└── session_12_2025-05-30.mp3
```

Update `metadata.source_file` in each JSON to match actual audio path.

---

## Patient Profile Summary

### Alex Chen Demographics
- **Age:** 23
- **Gender:** Non-binary (they/them pronouns)
- **Ethnicity:** Chinese-American (second-generation immigrant)
- **Occupation:** PhD student, Computer Science
- **Location:** Graduate student housing on campus

### Clinical Diagnoses
- **F41.1** - Generalized Anxiety Disorder (GAD)
- **F33.1** - Major Depressive Disorder, Recurrent, Moderate (in remission by Session 12)
- **F90.0** - ADHD, Combined Type (diagnosed Session 3)

### Medications
- **Adderall XR 15mg** (started 10mg Session 4, increased to 15mg Session 6)
- **No other medications**

### Family Background
- **Parents:** Chinese immigrants, both engineers
- **Family dynamics:** High academic expectations, mental health stigma, conditional love based on achievement
- **Coming out:** Session 9 decision, Session 10 disclosure (difficult reaction), gradual acceptance by Session 12

### Relationship History
- **Jamie (ex-partner):** 2-year relationship ended January 3, 2025 (breakup triggered crisis and therapy entry)
- **Jordan (current partner):** Started dating late March 2025, healthy relationship with secure attachment practice

### Therapeutic Progress
- **PHQ-9:** 18 → 7 (61% reduction)
- **GAD-7:** 16 → 7 (56% reduction)
- **Suicidal ideation:** Passive SI at intake → None by Session 12
- **Executive function:** Severe ADHD symptoms → Well-managed with medication and strategies
- **Family relationships:** Hidden identity → Out and making progress toward acceptance
- **Academic performance:** Struggling → First-author publication accepted
- **Therapy frequency:** Weekly → Transitioning to biweekly (Session 12)

---

## Session Timeline

| # | Date | Days Since Previous | Duration | Focus | Modalities | Key Clinical Moments |
|---|------|---------------------|----------|-------|------------|---------------------|
| 1 | Jan 10 | - | 60 min | Crisis Intake | CBT, Safety Planning | Passive SI assessment, safety plan, breakup grief |
| 2 | Jan 17 | 7 | 45 min | Emotional Regulation | DBT, CBT | TIPP skill, emotional triggers, grief processing |
| 3 | Jan 31 | 14 | 50 min | **ADHD Discovery** | ADHD Coaching, Psychodynamic | **Breakthrough:** ADHD recognition, psych referral |
| 4 | Feb 14 | 14 | 45 min | Medication Start | Medication Mgmt, CBT, IPT | Started Adderall 10mg, Valentine's Day grief |
| 5 | Feb 28 | 14 | 55 min | **Family Conflict** | IPT, ACT | **Major Event:** Family discovered therapy, cultural stigma |
| 6 | Mar 14 | 14 | 50 min | Spring Break Hope | CBT, Behavioral Activation, MBCT | **Milestone:** First genuine hope for future, Adderall increased to 15mg |
| 7 | Apr 4 | 21 | 50 min | Dating Anxiety | Psychodynamic, CBT, ACT | **Major Event:** Met Jordan, anxious attachment activated |
| 8 | Apr 18 | 14 | 45 min | Relationship Boundaries | DBT (DEAR MAN), Attachment | Boundary practice, secure attachment work |
| 9 | May 2 | 14 | 60 min | **Coming Out Prep** | ACT (Values), CBT, Family Systems | **Major Event:** Decision to come out to family |
| 10 | May 9 | 7 | 55 min | **Coming Out Aftermath** | Crisis Intervention, ACT, CBT | **Major Event:** Difficult family reaction, crisis support |
| 11 | May 16 | 7 | 50 min | Rebuilding | ACT, MBCT, Psychodynamic | **Milestone:** Resilience demonstrated, mother's text |
| 12 | May 30 | 14 | 50 min | **Thriving** | CBT, ACT, Positive Psych | **Milestone:** Clinical remission, publication accepted, father's text |

**Total therapy time:** 10.25 hours across 5 months

---

## Major Events Reference

| Event ID | Date | Title | Category | Impact | Related Sessions |
|----------|------|-------|----------|--------|-----------------|
| event_01 | Jan 3 | Breakup with Jamie | Relationship | 9/10 | S1, S2 |
| event_02 | Jan 31 | ADHD Diagnosis Recognition | Mental Health | 8/10 | S3 |
| event_03 | Feb 8 | Started ADHD Medication | Treatment | 7/10 | S4 |
| event_04 | Feb 24 | Family Discovered Therapy | Family | 8/10 | S5 |
| event_05 | Mar 15 | Portland Trip (Spring Break) | Personal Growth | 6/10 | S6 |
| event_06 | Mar 28 | Met Jordan (Dating App) | Relationship | 7/10 | S7, S8 |
| event_07 | May 2 | Decision to Come Out | Identity | 9/10 | S9 |
| event_08 | May 6 | Came Out to Family | Identity | 10/10 | S10 |
| event_09 | May 13 | Mother's Outreach Text | Family | 7/10 | S11 |
| event_10 | May 28 | Publication Acceptance | Academic | 8/10 | S12 |

**Event context usage:**
Each event includes `context_for_ai_chat` field - use this to inform Dobby's responses when patient mentions related topics.

---

## Troubleshooting

### Issue: Transcript won't load in frontend

**Solution:**
1. Verify file path is correct: `/mock-therapy-data/sessions/session_XX_*.json`
2. Check JSON validity: `jq . session_01_crisis_intake.json`
3. Confirm CORS headers allow loading local JSON files

### Issue: Speaker labels showing as SPEAKER_00/SPEAKER_01

**Solution:**
Replace generic labels with names in frontend:
```typescript
const speakerMap = {
  'SPEAKER_00': 'Dr. Sarah Mitchell',
  'SPEAKER_01': 'Alex Chen'
};
```

### Issue: Timeline events not linking to sessions

**Solution:**
Use `related_sessions` array in `major_events.json`:
```typescript
const linkedSession = sessions.find(s =>
  event.related_sessions.includes(s.id)
);
```

### Issue: Chat messages display without proper formatting

**Solution:**
Respect `metadata.capitalization` and `metadata.punctuation` from chat messages:
- Alex's messages: lowercase, minimal punctuation (Gen-Z style)
- Dobby's messages: Proper capitalization, full punctuation (professional but warm)

### Issue: Progress metrics not displaying

**Solution:**
PHQ-9 and GAD-7 scores are mentioned in clinical content but not extracted as structured data. You'll need to manually create a progress metrics array:
```typescript
const progressMetrics = [
  { session: 1, date: '2025-01-10', phq9: 18, gad7: 16 },
  { session: 2, date: '2025-01-17', phq9: 17, gad7: 15 },
  // ... etc (see Session Timeline table above)
  { session: 12, date: '2025-05-30', phq9: 7, gad7: 7 }
];
```

### Issue: Audio generation timing doesn't match transcript

**Solution:**
1. Verify `metadata.duration` matches sum of all segment durations
2. Check for realistic gaps between segments (0.1-0.5s)
3. Ensure last segment ends at exactly `metadata.duration`

---

## Hackathon Demo Script

**For PeerBridge Mental Health Hacks 2025 judges:**

### 1. **Dashboard Overview (30 seconds)**
"This is Alex Chen's patient dashboard. Alex is a 23-year-old non-binary PhD student who entered therapy in January 2025 after a crisis. Over 5 months and 12 sessions, they went from moderate depression with suicidal ideation to clinical remission."

### 2. **Session Timeline (30 seconds)**
"The timeline shows all 12 therapy sessions. Notice the milestones - Session 6 is where Alex first expressed genuine hope for the future, and Session 12 marks clinical remission. You can see varied session lengths (45-60 minutes) reflecting realistic therapy patterns."

### 3. **Session Detail View (60 seconds)**
"Let's open Session 3 - this is where Alex's ADHD was recognized. The transcript shows realistic dialogue with verbal markers like 'um' and 'like', therapist validation, and the breakthrough moment where Alex realized their struggles were ADHD symptoms, not character flaws. Notice speaker distribution: therapist 40%, patient 60% - clinically accurate."

### 4. **Major Events Timeline (45 seconds)**
"The mixed timeline combines therapy sessions with major life events. Here's the family conflict (purple diamond), ADHD diagnosis (breakthrough icon), and coming out event (identity badge). Each event links to related sessions and includes context for our AI companion."

### 5. **AI Chat with Dobby (60 seconds)**
"This is Dobby, Alex's AI mental health companion. Look at this crisis chat from February - Alex had a panic attack after their family discovered therapy. Dobby provided grounding (5-4-3-2-1 technique), reminded Alex of DBT skills (TIPP), and helped de-escalate from distress level 9 to 6. The chat style reflects Gen-Z communication - lowercase, minimal punctuation, but warm and supportive."

### 6. **Progress Metrics (30 seconds)**
"Here's the impact: PHQ-9 depression score dropped 61% (18→7), GAD-7 anxiety dropped 56% (16→7). Alex started ADHD medication, came out to family, published their first academic paper, and transitioned from weekly to biweekly therapy. This is what recovery looks like."

**Total demo: 4 minutes**

---

## Technical Support

**Questions about this data?**
- Review implementation plan: `plans/2025-12-22-parallel-transcript-generation.md`
- Check validation report: `VALIDATION_REPORT.md` (if generated)
- Verify JSON schema: Use Session 1 as reference template

**Audio generation support:**
- Hume AI Octave documentation: https://hume.ai/octave
- TTS API integration: Refer to `audio-transcription-pipeline/src/pipeline.py` for format expectations

**Clinical authenticity questions:**
- All therapeutic modalities (DBT, CBT, ACT, IPT, MBCT) are evidence-based
- PHQ-9 and GAD-7 scores follow validated clinical measures
- ADHD medication (Adderall XR) dosing is realistic
- Coming out timeline reflects common LGBTQ+ experiences
- All diagnoses use ICD-10 codes

---

## Appendix: Therapeutic Modalities Used

**CBT (Cognitive Behavioral Therapy):**
- Sessions: 1, 2, 4, 6, 7, 8, 9, 10, 12
- Techniques: Cognitive restructuring, thought challenging, behavioral experiments

**DBT (Dialectical Behavior Therapy):**
- Sessions: 2, 8
- Techniques: TIPP skill, DEAR MAN, emotion regulation, distress tolerance

**ACT (Acceptance & Commitment Therapy):**
- Sessions: 5, 7, 9, 10, 11, 12
- Techniques: Values clarification, cognitive defusion, willingness, psychological flexibility

**ADHD Coaching:**
- Sessions: 3
- Techniques: Psychoeducation, executive function strategies, masking awareness

**Psychodynamic/Attachment Theory:**
- Sessions: 3, 4, 7, 11
- Techniques: Attachment pattern exploration, family-of-origin work, insight development

**IPT (Interpersonal Therapy):**
- Sessions: 4, 5
- Techniques: Relationship pattern analysis, grief counseling, role transitions

**MBCT (Mindfulness-Based Cognitive Therapy):**
- Sessions: 6, 11
- Techniques: Mindfulness meditation, thought observation, non-judgmental awareness

**Family Systems Therapy:**
- Sessions: 9, 10
- Techniques: Cultural dynamics, family roles, differentiation

**Positive Psychology:**
- Sessions: 12
- Techniques: Gratitude practice, strength identification, meaning-making

**Crisis Intervention:**
- Sessions: 1, 10
- Techniques: Safety planning, suicide risk assessment, crisis de-escalation

---

**End of Integration Guide**

*Last updated: December 22, 2025*
*Data version: 1.0*
*Validated: ✅ All 12 sessions pass format validation*
