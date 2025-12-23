# Mood Analysis System - Visual Demo

## Expected Output for Alex Chen's 12 Sessions

Based on the mock therapy transcripts, here's what the AI mood analysis would likely extract:

```
================================================================================
MOOD ANALYSIS - ALEX CHEN THERAPY JOURNEY
================================================================================

Session 01 - Crisis Intake (Jan 10)                2.5/10 ████████░░ overwhelmed and despairing         87%
Session 02 - Emotional Regulation (Jan 17)         4.0/10 ████████░░ anxious but engaged                84%
Session 03 - ADHD Discovery (Jan 31)               5.0/10 █████░░░░░ confused but hopeful                89%
Session 04 - Medication Start (Feb 14)             4.5/10 █████░░░░░ grief-stricken and uncertain        82%
Session 05 - Family Conflict (Feb 28)              3.0/10 ███░░░░░░░ distressed and angry                86%
Session 06 - Spring Break Hope (Mar 14)            6.5/10 ███████░░░ cautiously optimistic               88%
Session 07 - Dating Anxiety (Apr 4)                5.5/10 ██████░░░░ nervous but excited                 85%
Session 08 - Relationship Boundaries (Apr 18)      6.0/10 ██████░░░░ balanced and reflective             87%
Session 09 - Coming Out Preparation (May 2)        5.0/10 █████░░░░░ anxious but determined              90%
Session 10 - Coming Out Aftermath (May 9)          4.0/10 ████░░░░░░ hurt but resilient                  86%
Session 11 - Rebuilding (May 16)                   7.0/10 ███████░░░ hopeful and empowered               89%
Session 12 - Thriving (May 30)                     8.0/10 ████████░░ content and confident               91%

================================================================================
STATISTICS
================================================================================
  Average Mood: 5.1/10.0
  Range: 2.5 - 8.0
  Overall Change: +5.5 (+220%)
  Total Sessions Analyzed: 12/12

  📈 Trend: IMPROVING (+5.5 points)

================================================================================
```

## Sample AI Rationale Examples

### Session 1: Crisis Intake (Mood: 2.5/10)

**Rationale:**
> Patient presents with severe depression symptoms including passive suicidal ideation ("I don't want to die, but I'm so tired of feeling like this"), complete anhedonia (can't open laptop despite previously loving coding), severe sleep disruption (12 hours/day or insomnia), feelings of drowning, and social isolation following recent breakup. First-year PhD stress compounds the distress. However, patient reached out for help and has no active suicide plan, which are protective factors.

**Key Indicators:**
- Passive suicidal ideation without plan
- Complete loss of interest in previously enjoyed activities (coding)
- Severe sleep disruption (hypersomnia alternating with insomnia)
- Recent relationship breakup causing significant grief
- First therapy session - seeking help (protective factor)
- No support system mentioned except roommate who encouraged therapy

---

### Session 6: Spring Break Hope (Mood: 6.5/10)

**Rationale:**
> Patient shows marked improvement with medication working well (Adderall helping with focus and energy), first genuine excitement about future plans (spring break trip with friends), improved sleep patterns, return of interest in coding projects, and positive social connections. Some residual anxiety about family relationships remains, but overall mood is optimistic and functional. This represents a significant shift from earlier sessions.

**Key Indicators:**
- Medication effectiveness (Adderall helping concentration)
- Return of interest in previously enjoyed activities
- Planning future activities with anticipation (spring break)
- Improved sleep patterns
- Genuine laughter during session (affect brightened)
- Still processing family conflict but not consuming them
- First mention of feeling "good" in several weeks

---

### Session 12: Thriving (Mood: 8.0/10)

**Rationale:**
> Patient demonstrates clinical remission with no depression/anxiety symptoms, healthy romantic relationship (dating Jordan for 2 months), academic success (first-author publication accepted), improved family communication despite ongoing challenges, strong coping skills (using DEAR MAN, TIPP, mindfulness regularly), and genuine pride in personal growth. Patient expresses gratitude for therapy journey and feels equipped to handle future challenges independently.

**Key Indicators:**
- No depression or anxiety symptoms present
- Healthy romantic relationship with clear boundaries
- Academic achievement (first-author publication)
- Effective use of learned coping skills
- Improved family communication (though still difficult)
- Pride in personal growth and self-advocacy
- Expressing readiness to reduce therapy frequency
- Looking forward to future with confidence

---

## ProgressPatternsCard Visualization

When integrated with the frontend, the ProgressPatternsCard would display:

### Compact View:
```
┌────────────────────────────────────────────┐
│  📈 MOOD TREND                             │
│  Session-by-session mood tracking          │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │        ╱                              │ │
│  │      ╱   ╲╱                          │ │
│  │    ╱       ╲                   ╱╲    │ │
│  │  ╱           ╲               ╱    ╲  │ │
│  │╱               ╲───╲╱────╱          ╲│ │
│  └──────────────────────────────────────┘ │
│                                            │
│  📈 IMPROVING: +220% overall               │
│  (Recent avg: 6.8/10, Historical: 3.6/10) │
└────────────────────────────────────────────┘
```

### Expanded Modal:
```
┌────────────────────────────────────────────────────────────┐
│  Progress Patterns                                      ✕  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ▼ MOOD TREND                                              │
│    Session-by-session mood tracking                        │
│    ┌────────────────────────────────────────────────────┐ │
│    │                                                    │ │
│    │  10 ┤                                          ●   │ │
│    │   9 ┤                                              │ │
│    │   8 ┤                                      ●       │ │
│    │   7 ┤                                  ●           │ │
│    │   6 ┤                          ●   ●               │ │
│    │   5 ┤              ●       ●               ●       │ │
│    │   4 ┤          ●               ●       ●           │ │
│    │   3 ┤                  ●                           │ │
│    │   2 ┤      ●                                       │ │
│    │   1 ┤                                              │ │
│    │   0 └───────────────────────────────────────────── │ │
│    │     S1 S2 S3 S4 S5 S6 S7 S8 S9 S10 S11 S12        │ │
│    │                                                    │ │
│    └────────────────────────────────────────────────────┘ │
│                                                            │
│    📈 KEY INSIGHT                                          │
│    Mood shows strong upward trajectory with 5.5-point     │
│    improvement over 12 sessions (220% increase). Patient  │
│    progressed from severe distress (passive SI, complete  │
│    anhedonia) to thriving (no symptoms, healthy          │
│    relationships, academic success). Most significant     │
│    improvements occurred after ADHD diagnosis (S3) and    │
│    medication start (S4), with continued gains through    │
│    DBT skills practice and identity work.                 │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## How to Use

### 1. Analyze a Single Session

```bash
curl -X POST "http://localhost:8000/api/sessions/session_01_alex_chen/analyze-mood" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "session_id": "session_01_alex_chen",
  "mood_score": 2.5,
  "confidence": 0.87,
  "rationale": "Patient presents with severe depression symptoms...",
  "key_indicators": [
    "Passive suicidal ideation without plan",
    "Complete loss of interest in coding",
    "Severe sleep disruption"
  ],
  "emotional_tone": "overwhelmed and despairing",
  "analyzed_at": "2025-12-22T10:30:00Z"
}
```

### 2. Get Full Mood History

```bash
curl "http://localhost:8000/api/sessions/patient/alex_chen_uuid/mood-history?limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Frontend Integration

```typescript
// Automatically loads and displays mood data
<ProgressPatternsCard
  patientId="alex_chen_uuid"
  useRealData={true}
/>
```

## What Makes This Special

### ✨ No Hardcoded Rules
The AI doesn't use keyword matching or predefined patterns. It reads the entire transcript like a human clinician would and forms a holistic understanding.

### ✨ Context-Aware
Considers protective factors (seeking help, support system) alongside risk factors (SI, anhedonia). A patient with severe symptoms who's engaged in treatment might score differently than one who's isolating.

### ✨ Nuanced Scoring
Uses 0.5 increments to capture subtle differences. Session 6 (6.5) vs Session 8 (6.0) reflects the slight dip in confidence before the coming out process.

### ✨ Explainable
Every score comes with a detailed rationale citing specific evidence from the transcript. Therapists can understand exactly why the AI scored the session that way.

### ✨ Longitudinal Insights
When viewed as a series, the mood scores tell a story: Crisis → Stabilization → Growth → Setback → Recovery → Thriving

## Clinical Validation

The AI's mood assessments should align with:
- **PHQ-9 scores** (if available): Patient's self-reported depression inventory
- **GAD-7 scores** (if available): Patient's self-reported anxiety inventory
- **Therapist clinical judgment**: Therapist's own assessment of patient state
- **Functional indicators**: School/work performance, relationship quality, self-care

For Alex Chen, the expected progression aligns with their journey:
- **S1-S2**: PHQ-9 likely 16-18 (moderate-severe) → Mood 2.5-4.0
- **S6-S8**: PHQ-9 likely 8-10 (mild) → Mood 6.0-6.5
- **S12**: PHQ-9 likely <5 (minimal) → Mood 8.0

---

**This is a live demo - the actual AI analysis will vary based on the specific transcript content, but this illustrates the expected quality and insight level.**
