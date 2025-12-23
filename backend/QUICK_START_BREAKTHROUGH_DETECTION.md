# 🚀 Quick Start - Breakthrough Detection

## 5-Minute Setup

### 1. Prerequisites
```bash
cd backend
pip install openai
export OPENAI_API_KEY="sk-your-key-here"
```

### 2. Run the Example
```bash
python examples/breakthrough_detection_example.py
```

**Expected output:**
```
================================================================================
BREAKTHROUGH DETECTION - SIMPLE EXAMPLE
================================================================================

✓ Breakthroughs detected: 2
✓ Has primary breakthrough: Yes

🎯 PRIMARY BREAKTHROUGH
Type: Cognitive Insight
Confidence: 92%

📝 Description:
Patient recognized connection between childhood abandonment and current
anxious attachment pattern in romantic relationship
```

### 3. Test with Real Data
```bash
python tests/test_breakthrough_detection.py
```

This will analyze the actual therapy session from your audio pipeline.

---

## Basic Usage

```python
from app.services.breakthrough_detector import BreakthroughDetector

# 1. Initialize
detector = BreakthroughDetector()

# 2. Prepare your transcript
transcript = [
    {"start": 0.0, "end": 3.5, "speaker": "Therapist", "text": "..."},
    {"start": 3.5, "end": 8.2, "speaker": "Patient", "text": "..."}
]

# 3. Analyze
analysis = detector.analyze_session(transcript)

# 4. Check results
if analysis.has_breakthrough:
    bt = analysis.primary_breakthrough
    print(f"Breakthrough: {bt.description}")
    print(f"Type: {bt.breakthrough_type}")
    print(f"Confidence: {bt.confidence_score:.0%}")
```

---

## Integration with Existing Backend

### Add API Endpoint

```python
# In app/routers/sessions.py

from app.services.breakthrough_detector import BreakthroughDetector

@router.post("/sessions/{session_id}/analyze-breakthrough")
async def analyze_breakthrough(
    session_id: str,
    db: Session = Depends(get_db)
):
    # Get session
    session = db.query(TherapySession).filter_by(id=session_id).first()
    if not session or not session.transcript:
        raise HTTPException(404, "Session not found")

    # Analyze
    detector = BreakthroughDetector()
    analysis = detector.analyze_session(
        transcript=session.transcript,
        session_metadata={"session_id": session_id}
    )

    # Store in database (optional)
    session.breakthrough_data = {
        "has_breakthrough": analysis.has_breakthrough,
        "primary_breakthrough": {
            "type": analysis.primary_breakthrough.breakthrough_type,
            "description": analysis.primary_breakthrough.description,
            "confidence": analysis.primary_breakthrough.confidence_score
        } if analysis.primary_breakthrough else None
    }
    db.commit()

    return analysis.breakthrough_data
```

### Test the Endpoint

```bash
# After audio processing completes
curl -X POST http://localhost:8000/api/sessions/session_123/analyze-breakthrough
```

---

## Frontend Integration

### 1. Add Type Definitions

```typescript
// lib/types.ts
interface Breakthrough {
  type: 'cognitive_insight' | 'emotional_shift' | 'behavioral_commitment' | 'relational_realization' | 'self_compassion';
  description: string;
  confidence: number;
  timestamp: string;
  evidence: string;
}

interface Session {
  id: string;
  // ... existing fields
  has_breakthrough?: boolean;
  primary_breakthrough?: Breakthrough;
}
```

### 2. Fetch Breakthrough Data

```typescript
// hooks/use-session-data.ts
const fetchSessionWithBreakthrough = async (sessionId: string) => {
  const session = await fetch(`/api/sessions/${sessionId}`);
  const breakthrough = await fetch(`/api/sessions/${sessionId}/analyze-breakthrough`);

  return {
    ...session,
    ...breakthrough
  };
};
```

### 3. Display in UI

```typescript
// components/SessionCard.tsx
{session.has_breakthrough && (
  <div className="flex items-center gap-2 mt-2">
    <Star className="w-4 h-4 text-amber-500 fill-amber-400" />
    <span className="text-sm text-amber-600">
      Breakthrough: {session.primary_breakthrough.type.replace('_', ' ')}
    </span>
  </div>
)}
```

---

## Common Use Cases

### 1. Analyze After Audio Processing

```python
# After transcription pipeline completes
def on_transcription_complete(session_id: str, transcript: list):
    # Store transcript
    session.transcript = transcript
    db.commit()

    # Analyze for breakthroughs (async recommended)
    detector = BreakthroughDetector()
    analysis = detector.analyze_session(transcript)

    # Store results
    session.breakthrough_data = analysis
    db.commit()
```

### 2. Show in Patient Timeline

```typescript
const renderTimelineEntry = (session: Session) => (
  <div className="relative">
    {session.has_breakthrough && (
      <BreakthroughIndicator
        type={session.primary_breakthrough.type}
        confidence={session.primary_breakthrough.confidence}
      />
    )}
    <SessionSummary session={session} />
  </div>
);
```

### 3. Inject into AI Chat Context

```typescript
// lib/chat-context.ts
const buildContext = (sessions: Session[]) => {
  const breakthroughs = sessions
    .filter(s => s.has_breakthrough)
    .map(s => `- ${s.date}: ${s.primary_breakthrough.description}`);

  return `
Patient's Breakthrough History:
${breakthroughs.join('\n')}
  `;
};
```

---

## Testing Checklist

- [ ] ✅ Run example script successfully
- [ ] ✅ Run test script with real therapy data
- [ ] ✅ API endpoint returns breakthrough data
- [ ] ✅ Frontend fetches and displays breakthroughs
- [ ] ✅ Timeline shows breakthrough indicators
- [ ] ✅ AI chat context includes breakthrough history

---

## Performance Tips

### 1. Cache Results
```python
# Don't re-analyze same session
if session.breakthrough_data:
    return session.breakthrough_data

# First time - analyze and cache
analysis = detector.analyze_session(transcript)
session.breakthrough_data = analysis
db.commit()
```

### 2. Background Processing
```python
# Don't block the main thread
from celery import Celery

@celery.task
def analyze_breakthrough_async(session_id: str):
    # Analyze in background
    detector = BreakthroughDetector()
    # ... store results
```

### 3. Batch Processing
```python
# Analyze multiple sessions together
sessions = db.query(TherapySession).filter(
    TherapySession.breakthrough_data.is_(None)
).all()

for session in sessions:
    analysis = detector.analyze_session(session.transcript)
    # ... store results
```

---

## Cost Estimation

**Per session:**
- Average transcript: ~3,000 tokens
- GPT-4o cost: ~$0.05-0.10
- Processing time: 15-45 seconds

**For 100 sessions/day:**
- Daily cost: ~$5-10
- Monthly cost: ~$150-300

**Optimization:**
- Analyze once per session (cache results)
- Only analyze sessions with sufficient length (>10 min)
- Filter by confidence threshold (>0.6)

---

## Troubleshooting

### "No breakthroughs detected"
**Possible reasons:**
- Early sessions (rapport-building)
- Maintenance/check-in sessions
- Algorithm needs tuning for therapy style

**Solutions:**
- Check `session_summary` for context
- Lower confidence threshold (try 0.5)
- Review transcript quality

### API Errors
```python
try:
    analysis = detector.analyze_session(transcript)
except Exception as e:
    logger.error(f"Breakthrough detection failed: {e}")
    # Fall back to no-breakthrough
    analysis = SessionBreakthroughAnalysis(
        has_breakthrough=False,
        ...
    )
```

### Low Confidence Scores
**Review evidence:**
```python
for bt in analysis.breakthrough_candidates:
    if bt.confidence_score < 0.7:
        print(f"Evidence: {bt.evidence}")
        # Manually verify if it's a real breakthrough
```

---

## Next Steps

1. **Start simple** - Run the example script
2. **Test with real data** - Use your therapy transcripts
3. **Add API endpoint** - Integrate with backend
4. **Update frontend** - Show breakthroughs in UI
5. **Monitor & optimize** - Track costs and performance

---

## 📚 Additional Resources

- **Complete docs**: `app/services/BREAKTHROUGH_DETECTION_README.md`
- **Data flow diagram**: `examples/BREAKTHROUGH_DETECTION_FLOW.md`
- **Full summary**: `BREAKTHROUGH_DETECTION_SUMMARY.md`
- **Target output**: `examples/example_breakthrough_target_output.json`

---

## Support

**Issues? Questions?**
1. Check the comprehensive README
2. Review test output: `tests/breakthrough_analysis_output.json`
3. Adjust AI prompt if needed: `app/services/breakthrough_detector.py` line 134

**Happy breakthrough detecting! 🎯**
