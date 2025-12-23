# Breakthrough Detection Algorithm

## Overview

The Breakthrough Detection Algorithm uses GPT-4 to analyze therapy session transcripts and identify genuine therapeutic breakthroughs. Unlike rule-based approaches, this system uses AI to understand context, emotional nuance, and the complex dynamics of therapeutic progress.

## What is a Breakthrough?

A breakthrough is a significant moment of therapeutic progress, including:

### 1. **Cognitive Insight** 🧠
Patient gains new understanding of their patterns, beliefs, or behaviors.

**Examples:**
- Connecting childhood experiences to current struggles
- Recognizing cognitive distortions ("I realize I'm catastrophizing")
- Reframing situations in healthier ways

**Real example from testing:**
> "Oh my god. I just realized... I do the same thing to myself that she did to me. I'm constantly comparing myself to others."

### 2. **Emotional Shift** 💙
Genuine emotional processing or release.

**Examples:**
- Moving from resistance to acceptance
- Expressing previously suppressed emotions
- Experiencing relief, hope, or self-compassion
- Crying followed by insight

**Real example:**
> "I wrote that letter to my younger self. I cried for an hour but it helped me realize I was never the problem."

### 3. **Behavioral Commitment** ✅
Concrete decision to change behavior.

**Examples:**
- First successful application of coping skill
- Boundary-setting for the first time
- Choosing vulnerability over avoidance

**Real example:**
> "I actually said no to my mom's request to babysit on my work day. Scary at first, but then relieving."

### 4. **Relational Realization** 💭
New understanding of relationship patterns.

**Examples:**
- Recognizing attachment patterns
- Understanding impact of childhood on adult relationships
- Taking accountability or showing empathy

**Real example:**
> "I think Bruce is the one who partially caused the divorce. It was so soon after they got married."

### 5. **Self-Compassion** 🌱
Shift from self-criticism to self-kindness.

**Examples:**
- Challenging internalized shame
- Recognizing inherent worth
- Practicing self-forgiveness

**Real example:**
> "I think... I think I deserve kindness. Even from myself."

---

## Algorithm Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Input: Raw Transcript                    │
│  [{start, end, text, speaker}, {start, end, text, speaker}]  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Step 1: Conversation Extraction                 │
│  Groups consecutive segments by speaker into turns           │
│  Output: [{speaker, text, start, end}, ...]                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Step 2: AI Breakthrough Detection               │
│  GPT-4 analyzes conversation for breakthrough moments        │
│  - Identifies emotional shifts                               │
│  - Detects cognitive insights                                │
│  - Recognizes behavioral commitments                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Step 3: Candidate Parsing                       │
│  Converts AI findings to structured BreakthroughCandidate    │
│  objects with timestamps, confidence, evidence               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Step 4: Primary Breakthrough Selection          │
│  Selects highest-confidence breakthrough as primary          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Output: SessionBreakthroughAnalysis                  │
│  - has_breakthrough (bool)                                   │
│  - breakthrough_candidates (list)                            │
│  - primary_breakthrough (object)                             │
│  - session_summary (str)                                     │
│  - emotional_trajectory (str)                                │
└─────────────────────────────────────────────────────────────┘
```

---

## Usage

### Basic Usage

```python
from app.services.breakthrough_detector import BreakthroughDetector

# Initialize detector
detector = BreakthroughDetector()

# Load your transcript
transcript = [
    {
        "start": 0.0,
        "end": 3.5,
        "speaker": "Therapist",
        "text": "How did the boundary-setting go this week?"
    },
    {
        "start": 3.5,
        "end": 8.2,
        "speaker": "Patient",
        "text": "I actually said no to my mom for the first time!"
    },
    # ... more segments
]

# Analyze session
analysis = detector.analyze_session(
    transcript=transcript,
    session_metadata={"session_id": "session_123", "patient_id": "patient_456"}
)

# Check results
if analysis.has_breakthrough:
    print(f"Breakthrough detected: {analysis.primary_breakthrough.description}")
    print(f"Type: {analysis.primary_breakthrough.breakthrough_type}")
    print(f"Confidence: {analysis.primary_breakthrough.confidence_score}")
```

### Integration with Audio Pipeline

```python
import json
from app.services.breakthrough_detector import BreakthroughDetector

# Load audio pipeline output
with open("pipeline_output.json", "r") as f:
    data = json.load(f)

transcript = data["segments"]
metadata = data["metadata"]

# Analyze for breakthroughs
detector = BreakthroughDetector()
analysis = detector.analyze_session(transcript, metadata)

# Export results
detector.export_breakthrough_report(analysis, "breakthrough_report.json")
```

### API Integration

```python
# In your FastAPI endpoint
from app.services.breakthrough_detector import BreakthroughDetector

@router.post("/sessions/{session_id}/analyze-breakthrough")
async def analyze_breakthrough(session_id: str, db: Session = Depends(get_db)):
    # Get session from database
    session = db.query(TherapySession).filter_by(id=session_id).first()
    if not session or not session.transcript:
        raise HTTPException(404, "Session or transcript not found")

    # Analyze breakthroughs
    detector = BreakthroughDetector()
    analysis = detector.analyze_session(
        transcript=session.transcript,
        session_metadata={"session_id": session_id, "patient_id": session.patient_id}
    )

    # Store breakthrough in database
    if analysis.has_breakthrough:
        breakthrough = analysis.primary_breakthrough
        # Save to database...

    return {
        "has_breakthrough": analysis.has_breakthrough,
        "breakthrough_count": len(analysis.breakthrough_candidates),
        "primary_breakthrough": {
            "type": breakthrough.breakthrough_type,
            "description": breakthrough.description,
            "confidence": breakthrough.confidence_score
        } if analysis.primary_breakthrough else None
    }
```

---

## Output Format

### SessionBreakthroughAnalysis

```python
{
    "session_id": "session_123",
    "has_breakthrough": True,
    "breakthrough_candidates": [...],  # List of BreakthroughCandidate objects
    "primary_breakthrough": {
        "timestamp_start": 145.2,
        "timestamp_end": 178.5,
        "breakthrough_type": "cognitive_insight",
        "confidence_score": 0.92,
        "description": "Patient recognized connection between childhood neglect and adult self-worth issues",
        "evidence": "Patient verbalized 'I was never the problem' with emotional release",
        "speaker_sequence": [
            {"speaker": "Therapist", "text": "Tell me about..."},
            {"speaker": "Patient", "text": "I just realized..."}
        ]
    },
    "session_summary": "Session showed significant breakthrough...",
    "emotional_trajectory": "resistant → reflective → insight → relief"
}
```

### BreakthroughCandidate

Each breakthrough candidate includes:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp_start` | float | Start time in seconds |
| `timestamp_end` | float | End time in seconds |
| `speaker_sequence` | list | Dialogue turns during breakthrough |
| `breakthrough_type` | str | Type (insight, emotional_shift, etc.) |
| `confidence_score` | float | 0.0-1.0 confidence rating |
| `description` | str | Brief description of breakthrough |
| `evidence` | str | Why this qualifies as breakthrough |

---

## AI Prompt Engineering

The algorithm uses a carefully crafted system prompt that:

1. **Defines breakthrough criteria** - Clear examples of what qualifies
2. **Provides counter-examples** - What NOT to identify as breakthroughs
3. **Requests structured output** - JSON format for parsing
4. **Emphasizes discernment** - "Be discerning - only identify genuine breakthroughs"

### Key Prompt Elements

```python
"""
A BREAKTHROUGH is a significant moment of progress in therapy, such as:

1. Cognitive Insight - Patient gains new understanding
2. Emotional Shift - Genuine emotional processing
3. Behavioral Commitment - Concrete decision to change
4. Relational Realization - New understanding of patterns
5. Self-Compassion - Shift from criticism to kindness

WHAT IS NOT A BREAKTHROUGH:
- Routine check-ins or progress updates
- Simple agreement with therapist
- Describing problems without insight
- Planning future tasks (unless emotionally significant)
"""
```

---

## Expected Breakthroughs in Test Data

### Session 1 (Eating Disorder - Initial Phase)

**Expected breakthroughs:**

1. **Cognitive Insight** (~8-12 min)
   - Patient connects mother's pressure to body image issues
   - "She was very vocal towards me about my eating and my looks"

2. **Relational Realization** (~18-22 min)
   - Recognition that Bruce may have caused parents' divorce
   - Understanding of family dynamics' impact

3. **Emotional Pattern Recognition** (~35-40 min)
   - Connection between stress/conflict and binge episodes
   - Awareness of roommate conflict triggering eating disorder

### Mock Session Data (Dashboard v3)

**Session s9 - "Breakthrough: Self-compassion"**
- Type: Self-compassion + Emotional shift
- Dialogue: "I wrote that letter to my younger self. I cried for an hour but it helped me realize I was never the problem."
- Expected confidence: 0.85+

**Session s10 - Boundary Setting**
- Type: Behavioral commitment
- Dialogue: "I actually said no to my mom's request to babysit on my work day."
- Expected confidence: 0.75+

---

## Testing

### Run Tests

```bash
cd backend
python tests/test_breakthrough_detection.py
```

### Test Coverage

1. **Real Transcript Test**
   - Uses actual therapy session from audio pipeline
   - Tests full algorithm pipeline
   - Validates against expected breakthroughs

2. **Known Breakthrough Test**
   - Synthetic transcript with obvious breakthrough
   - Validates algorithm can detect clear cases
   - Ensures minimum confidence threshold met

### Expected Output

```
================================================================================
BREAKTHROUGH DETECTION TEST
================================================================================

1. Initializing BreakthroughDetector...
   ✓ Detector initialized with OpenAI API

2. Loading therapy session transcript...
   ✓ Loaded transcript: Initial Phase and Interpersonal Inventory.mp3
   ✓ Duration: 2091.6 seconds
   ✓ Total segments: 845

3. Analyzing session with AI...
   (This may take 30-60 seconds...)

================================================================================
ANALYSIS RESULTS
================================================================================

✓ Breakthroughs detected: 3
✓ Has primary breakthrough: Yes

📊 Session Summary:
   Session showed 3 significant breakthrough moment(s). Primary insight:
   Patient recognized connection between mother's pressure and eating disorder.

💭 Emotional Trajectory:
   exploratory → resistant → reflective → insight

🎯 BREAKTHROUGH MOMENTS (3):
--------------------------------------------------------------------------------

   Breakthrough #1
   Type: cognitive_insight
   Confidence: 0.89
   Timestamp: 08:45 - 12:30

   Description:
   Patient connected mother's critical comments about appearance to development
   of body image issues and eating disorder onset in middle school.

   Evidence:
   Patient verbalized "I felt like more pressure from my mom. She was very vocal
   towards me about my eating and my looks" with recognition of causal relationship.

   Dialogue Excerpt:
   Therapist: When did you first start feeling that you weren't good enough?
   Patient: I think it started when I was really young. Maybe 8 or 9?...

--------------------------------------------------------------------------------
```

---

## Performance Considerations

### API Costs

- **Model**: GPT-4o
- **Average tokens per session**: ~3,000-5,000 tokens
- **Cost per analysis**: ~$0.05-0.10
- **Batch processing**: Process multiple sessions in parallel for efficiency

### Optimization Strategies

1. **Cache results** - Store breakthrough analysis in database
2. **Incremental processing** - Only analyze new sessions
3. **Confidence filtering** - Only show breakthroughs above 0.6 confidence
4. **Background jobs** - Process breakthroughs asynchronously after transcription

---

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional
BREAKTHROUGH_MIN_CONFIDENCE=0.6  # Minimum confidence to report
BREAKTHROUGH_MODEL=gpt-4o        # AI model to use
```

### Customization

```python
# Adjust confidence threshold
analysis = detector.analyze_session(transcript)
high_confidence_breakthroughs = [
    bt for bt in analysis.breakthrough_candidates
    if bt.confidence_score >= 0.75
]

# Filter by breakthrough type
insights = [
    bt for bt in analysis.breakthrough_candidates
    if bt.breakthrough_type == "cognitive_insight"
]
```

---

## Future Enhancements

### Planned Features

1. **Multi-session tracking** - Identify breakthrough themes across sessions
2. **Patient-specific tuning** - Learn patient's breakthrough patterns
3. **Therapist feedback loop** - Allow therapists to confirm/reject detections
4. **Sentiment analysis** - Track emotional intensity during breakthroughs
5. **Visualization** - Timeline view of breakthroughs across therapy journey

### Research Opportunities

- Validate against therapist-identified breakthroughs
- Compare different therapy modalities (CBT vs DBT vs psychodynamic)
- Correlate breakthroughs with clinical outcomes (PHQ-9, GAD-7)
- Study breakthrough density vs treatment effectiveness

---

## Troubleshooting

### No breakthroughs detected

**Possible causes:**
- Early sessions (rapport-building phase)
- Maintenance/check-in sessions
- Algorithm needs adjustment for therapy style

**Solutions:**
- Review session_summary for context
- Check confidence threshold (try lowering to 0.5)
- Examine transcript quality (speaker diarization errors?)

### Low confidence scores

**Possible causes:**
- Subtle/gradual insights vs dramatic moments
- Poor transcript quality
- Ambiguous emotional cues

**Solutions:**
- Review evidence field to understand AI reasoning
- Check speaker labels (Therapist vs Patient correctly assigned?)
- Consider manual review for confidence 0.5-0.7

### API errors

```python
try:
    analysis = detector.analyze_session(transcript)
except Exception as e:
    print(f"Breakthrough detection failed: {e}")
    # Fall back to no-breakthrough analysis
```

---

## License & Attribution

This algorithm uses OpenAI's GPT-4 API. Ensure compliance with:
- OpenAI's usage policies
- HIPAA requirements for PHI
- Patient consent for AI analysis

**Privacy note**: Transcripts are sent to OpenAI's API. Ensure proper de-identification or patient consent.

---

## Contact & Support

For questions or issues:
- Check test output: `tests/breakthrough_analysis_output.json`
- Review AI prompt: `app/services/breakthrough_detector.py` line 134
- Adjust confidence threshold if too strict/lenient
