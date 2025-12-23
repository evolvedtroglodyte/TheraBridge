# Breakthrough Detection - Complete Data Flow

## 📊 System Architecture

```
┌───────────────────────────────────────────────────────────────────────┐
│                        AUDIO TRANSCRIPTION PIPELINE                    │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐              │
│  │   Audio     │──▶│   Whisper    │──▶│  Pyannote    │──▶ JSON      │
│  │   Upload    │   │ Transcription│   │ Diarization  │              │
│  └─────────────┘   └──────────────┘   └──────────────┘              │
└────────────────────────────────┬──────────────────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Transcript JSON        │
                    │  {                      │
                    │    segments: [          │
                    │      {start, end,       │
                    │       speaker, text}    │
                    │    ]                    │
                    │  }                      │
                    └───────────┬─────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────────────┐
│                    BREAKTHROUGH DETECTION ALGORITHM                    │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  Step 1: Conversation Extraction                           │     │
│  │  • Groups consecutive speaker segments                     │     │
│  │  • Creates speaker turns with full context                 │     │
│  │                                                             │     │
│  │  Input:  [{start:0, end:3, speaker:"T", text:"How..."}]   │     │
│  │  Output: [{speaker:"T", text:"How...", start:0, end:3}]   │     │
│  └─────────────────────────┬──────────────────────────────────┘     │
│                            │                                          │
│                            ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  Step 2: AI Analysis (GPT-4o)                              │     │
│  │                                                             │     │
│  │  System Prompt:                                            │     │
│  │  "You are an expert psychologist analyzing therapy         │     │
│  │   sessions. Identify breakthrough moments..."              │     │
│  │                                                             │     │
│  │  AI Analyzes For:                                          │     │
│  │  • Cognitive insights (connecting past → present)          │     │
│  │  • Emotional shifts (resistance → acceptance)              │     │
│  │  • Behavioral commitments (first boundary-setting)         │     │
│  │  • Relational realizations (attachment patterns)           │     │
│  │  • Self-compassion (criticism → kindness)                  │     │
│  │                                                             │     │
│  │  Returns: JSON with breakthrough moments                   │     │
│  └─────────────────────────┬──────────────────────────────────┘     │
│                            │                                          │
│                            ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  Step 3: Candidate Parsing                                 │     │
│  │  • Extracts structured data from AI response               │     │
│  │  • Creates BreakthroughCandidate objects                   │     │
│  │  • Links dialogue excerpts                                 │     │
│  │  • Calculates confidence scores                            │     │
│  └─────────────────────────┬──────────────────────────────────┘     │
│                            │                                          │
│                            ▼                                          │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │  Step 4: Primary Selection                                 │     │
│  │  • Ranks by confidence score                               │     │
│  │  • Selects highest-confidence as primary                   │     │
│  │  • Generates session summary                               │     │
│  └─────────────────────────┬──────────────────────────────────┘     │
│                            │                                          │
└────────────────────────────┼──────────────────────────────────────────┘
                             │
                             ▼
                ┌─────────────────────────────┐
                │  SessionBreakthroughAnalysis│
                │  {                          │
                │    has_breakthrough: true   │
                │    primary_breakthrough: {  │
                │      type, description,     │
                │      confidence, evidence   │
                │    }                        │
                │  }                          │
                └──────────────┬──────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌───────────────┐    ┌──────────────────┐    ┌──────────────┐
│   DATABASE    │    │   FRONTEND UI    │    │  AI CHAT     │
│               │    │                  │    │  CONTEXT     │
│  • Store      │    │  • Timeline      │    │              │
│    results    │    │    markers       │    │  • Inject    │
│  • Cache      │    │  • Session cards │    │    into      │
│    for perf   │    │  • Modal details │    │    Dobby     │
└───────────────┘    └──────────────────┘    └──────────────┘
```

## 🔄 Example Data Flow

### Input (from Audio Pipeline)

```json
{
  "segments": [
    {
      "start": 68.0,
      "end": 82.5,
      "speaker": "SPEAKER_00",
      "text": "Oh my god. I'm that little kid watching out the window. I'm doing the exact same thing."
    }
  ]
}
```

### Processing Steps

**1. Conversation Extraction**
```
Before: 845 small segments with speaker changes
After:  217 coherent speaker turns with full context
```

**2. AI Prompt Construction**
```
[01:08] Therapist: And when you check your phone 50 times...
[01:08] Patient: Oh my god. I'm that little kid watching out the window.
                 I'm doing the exact same thing.
```

**3. AI Response (JSON)**
```json
{
  "breakthrough_moments": [{
    "timestamp_start": 68.0,
    "timestamp_end": 98.5,
    "breakthrough_type": "cognitive_insight",
    "confidence_score": 0.92,
    "description": "Patient connected childhood abandonment to adult anxiety",
    "evidence": "Verbalized 'I'm that little kid' with emotional recognition"
  }]
}
```

**4. Structured Output**
```python
BreakthroughCandidate(
    timestamp_start=68.0,
    timestamp_end=98.5,
    breakthrough_type="cognitive_insight",
    confidence_score=0.92,
    description="Patient connected childhood abandonment...",
    evidence="Verbalized 'I'm that little kid' with emotional recognition",
    speaker_sequence=[
        {"speaker": "Therapist", "text": "And when you check..."},
        {"speaker": "Patient", "text": "Oh my god. I'm that little kid..."}
    ]
)
```

## 📱 Frontend Integration Points

### 1. Timeline View
```typescript
// Show breakthrough stars on timeline
{sessions.map(session => (
  <TimelineEntry>
    {session.has_breakthrough && (
      <BreakthroughStar
        type={session.breakthrough.type}
        confidence={session.breakthrough.confidence}
      />
    )}
  </TimelineEntry>
))}
```

### 2. Session Card Enhancement
```typescript
<SessionCard session={session}>
  {session.breakthrough && (
    <Badge variant="gold">
      ⭐ Breakthrough: {session.breakthrough.type}
    </Badge>
  )}
</SessionCard>
```

### 3. Breakthrough Modal
```typescript
<BreakthroughModal
  type={breakthrough.type}
  description={breakthrough.description}
  evidence={breakthrough.evidence}
  dialogue={breakthrough.speaker_sequence}
  timestamp={breakthrough.timestamp}
  confidence={breakthrough.confidence}
/>
```

### 4. AI Chat Context Injection
```typescript
// In lib/chat-context.ts
function buildAIContext(sessions: Session[]): string {
  const breakthroughs = sessions
    .filter(s => s.has_breakthrough)
    .map(s => s.primary_breakthrough.description);

  return `
    Patient's key breakthroughs:
    ${breakthroughs.join('\n')}
  `;
}
```

## 🎯 Real-World Example

### Session Input
```
Therapist: "How did the boundary-setting go this week?"
Patient: "I actually said no to my mom's request to babysit."
Therapist: "That's a significant step. How did it feel?"
Patient: "Scary at first, but then relieving. Like a weight lifted."
```

### Algorithm Detection
```
✓ Detected: Behavioral Commitment
✓ Confidence: 0.78
✓ Evidence: First successful boundary-setting with mother
✓ Timestamp: 02:15 - 02:45
```

### Frontend Display
```
┌─────────────────────────────────────────┐
│  Session #10 - Dec 17                   │
│  ⭐ Breakthrough: Behavioral Commitment  │
│                                          │
│  "Successfully set first boundary with   │
│   family member (declined babysitting    │
│   request). Patient reported relief      │
│   and empowerment."                      │
│                                          │
│  [View Full Details] Confidence: 78%     │
└─────────────────────────────────────────┘
```

## 🔧 API Endpoint Flow

### POST /sessions/{id}/analyze-breakthrough

```
1. Request received
   ↓
2. Load session from database
   ↓
3. Extract transcript JSON
   ↓
4. Initialize BreakthroughDetector
   ↓
5. Call detector.analyze_session()
   ↓
6. Store results in database
   ↓
7. Return JSON response
```

### Example Request/Response

**Request:**
```bash
POST /api/sessions/session_123/analyze-breakthrough
```

**Response:**
```json
{
  "session_id": "session_123",
  "has_breakthrough": true,
  "primary_breakthrough": {
    "type": "cognitive_insight",
    "description": "Patient recognized connection between childhood experiences and current patterns",
    "confidence": 0.92,
    "timestamp": "01:08",
    "evidence": "Verbalized 'Oh my god, I just realized...' with visible emotional shift"
  },
  "breakthrough_count": 2,
  "processing_time_seconds": 23.5
}
```

## 💾 Database Schema

```sql
-- Add to therapy_sessions table
ALTER TABLE therapy_sessions ADD COLUMN has_breakthrough BOOLEAN DEFAULT FALSE;
ALTER TABLE therapy_sessions ADD COLUMN breakthrough_data JSONB;

-- Example stored data
{
  "primary_breakthrough": {
    "type": "cognitive_insight",
    "description": "...",
    "confidence": 0.92,
    "timestamp_start": 68.0,
    "timestamp_end": 98.5
  },
  "all_breakthroughs": [...],
  "analyzed_at": "2025-12-22T12:34:56Z"
}
```

## 🎨 UI Components

### Timeline Marker
```typescript
{session.has_breakthrough && (
  <div className="absolute -top-2 left-1/2 -translate-x-1/2">
    <div className="relative">
      <Star className="w-6 h-6 text-amber-500 fill-amber-400" />
      <div className="absolute inset-0 animate-ping">
        <Star className="w-6 h-6 text-amber-300 opacity-75" />
      </div>
    </div>
  </div>
)}
```

### Confidence Badge
```typescript
function ConfidenceBadge({ score }: { score: number }) {
  const color = score >= 0.8 ? 'green' : score >= 0.6 ? 'amber' : 'gray';
  return (
    <Badge variant={color}>
      {(score * 100).toFixed(0)}% confidence
    </Badge>
  );
}
```

## 📈 Performance Optimization

### Caching Strategy
```python
# Check if already analyzed
cached = db.query(TherapySession).filter_by(id=session_id).first()
if cached.breakthrough_data:
    return cached.breakthrough_data

# Analyze and cache
analysis = detector.analyze_session(transcript)
cached.breakthrough_data = analysis
db.commit()
```

### Background Processing
```python
# Don't block audio processing
@celery.task
def analyze_breakthrough_async(session_id: str):
    detector = BreakthroughDetector()
    analysis = detector.analyze_session(...)
    store_results(session_id, analysis)
```

## 🎯 Integration Checklist

- [ ] Add `breakthrough_detector.py` to backend services
- [ ] Add OpenAI API key to environment variables
- [ ] Create database migration for breakthrough columns
- [ ] Add API endpoint for breakthrough analysis
- [ ] Add background job for async processing
- [ ] Update frontend types to include breakthrough data
- [ ] Add breakthrough indicators to timeline UI
- [ ] Create breakthrough detail modal
- [ ] Inject breakthroughs into AI chat context
- [ ] Add breakthrough analytics to therapist dashboard
- [ ] Test with real therapy sessions
- [ ] Monitor API costs and optimize as needed

---

**Ready to integrate!** Start with the simple example, then gradually add backend API endpoints and frontend UI components.
