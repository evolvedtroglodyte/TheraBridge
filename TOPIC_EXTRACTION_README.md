# Topic Extraction System

## Overview

AI-powered topic extraction system that analyzes therapy session transcripts and extracts structured metadata including:

- **Topics (1-2)**: Main themes or issues discussed in the session
- **Action Items (2)**: Concrete homework or commitments
- **Technique (1)**: Primary therapeutic technique used (CBT, DBT, etc.)
- **Summary (2 sentences)**: Concise clinical summary

## Key Features

✅ **No Hardcoded Output** - AI naturally concludes topics from conversation context
✅ **Meta Summary Approach** - Single AI call generates all metadata for consistency
✅ **Speaker Role Detection** - Uses existing frontend logic to label Therapist/Client
✅ **Cost-Effective** - GPT-4o-mini (~$0.01 per session analysis)
✅ **Production-Ready** - Complete error handling, validation, and caching

## Architecture

### 1. AI Service (`app/services/topic_extractor.py`)

The core extraction logic:

```python
from app.services.topic_extractor import TopicExtractor, extract_session_metadata

# Initialize
extractor = TopicExtractor()

# Extract metadata from transcript
metadata = extractor.extract_metadata(
    session_id="session_123",
    segments=transcript_segments,
    speaker_roles={"SPEAKER_00": "Therapist", "SPEAKER_01": "Client"}
)

# Access results
print(metadata.topics)        # ["Relationship anxiety", "Fear of abandonment"]
print(metadata.action_items)  # ["Practice TIPP skills", "Schedule psychiatrist appt"]
print(metadata.technique)     # "DBT emotion regulation (TIPP)"
print(metadata.summary)       # "Patient discussed overwhelming anxiety..."
print(metadata.confidence)    # 0.85
```

### 2. API Endpoint (`POST /api/sessions/{session_id}/extract-topics`)

**Request:**
```bash
curl -X POST http://localhost:8000/api/sessions/session_01/extract-topics
```

**Response:**
```json
{
  "session_id": "session_01",
  "topics": [
    "Crisis intervention and suicidal ideation",
    "ADHD diagnosis and treatment planning"
  ],
  "action_items": [
    "Create safety plan with crisis contacts",
    "Schedule psychiatrist appointment for ADHD medication evaluation"
  ],
  "technique": "Crisis intervention and psychoeducation",
  "summary": "Patient presented in crisis with passive suicidal ideation, sleep disruption, and complete anhedonia following a breakup. Therapist conducted safety assessment, created crisis plan, and began exploring relationship patterns and ADHD impact on functioning.",
  "confidence": 0.88,
  "extracted_at": "2025-12-22T12:30:00Z"
}
```

**Features:**
- ✅ Auto-caching: Won't re-analyze unless `force=true`
- ✅ Stores results in database automatically
- ✅ Returns previously extracted data if available
- ✅ Full error handling with detailed messages

### 3. Database Schema (`supabase/migrations/003_add_topic_extraction.sql`)

**New Columns:**
```sql
ALTER TABLE therapy_sessions
ADD COLUMN topics TEXT[] DEFAULT '{}',
ADD COLUMN action_items TEXT[] DEFAULT '{}',
ADD COLUMN technique VARCHAR(255),
ADD COLUMN summary TEXT,
ADD COLUMN extraction_confidence DECIMAL(3,2),
ADD COLUMN raw_meta_summary TEXT,
ADD COLUMN topics_extracted_at TIMESTAMP;
```

**Views:**
- `patient_topic_frequency` - Track most discussed topics per patient
- `patient_technique_history` - Track therapeutic techniques used

**Functions:**
- `get_patient_action_items(patient_id, limit, recent_days)` - Fetch recent action items
- `search_sessions_by_topic(patient_id, topic_pattern)` - Search sessions by topic keyword

### 4. Test Script (`backend/tests/test_topic_extraction.py`)

Process all 12 mock therapy sessions:

```bash
cd backend
source venv/bin/activate
python tests/test_topic_extraction.py
```

**Output:**
- Displays extracted metadata for each session in terminal
- Saves results to `mock-therapy-data/topic_extraction_results.json`
- Shows success/failure summary

## How It Works

### Step 1: Format Conversation

The service formats transcript segments with speaker roles:

```
[00:00] Therapist: Hi Alex, welcome. I'm Dr. Rodriguez...
[00:28] Client: Yeah, that makes sense. Um, I'm really nervous...
[00:45] Therapist: It's completely normal to feel nervous...
```

### Step 2: AI Analysis

GPT-4o-mini analyzes the full conversation using a specialized prompt:

**System Prompt Guidelines:**
- Be specific and clinical (not vague)
- Extract actionable items (not generic advice)
- Identify primary technique used
- Generate 2-sentence clinical summary
- Rate confidence based on clarity

**Example Output:**
```json
{
  "topics": [
    "Crisis intervention and passive suicidal ideation",
    "ADHD medication evaluation and academic struggles"
  ],
  "action_items": [
    "Create safety plan with crisis hotline number and trusted contacts",
    "Schedule psychiatrist appointment for ADHD medication assessment"
  ],
  "technique": "Crisis intervention with safety planning",
  "summary": "Patient presented with passive suicidal ideation, severe depression, and ADHD-related academic difficulties. Therapist established safety plan and explored relationship patterns contributing to current crisis.",
  "confidence": 0.92
}
```

### Step 3: Validation & Storage

- Ensures 1-2 topics (max)
- Ensures 2 action items (provides defaults if missing)
- Validates technique field
- Stores results in database with timestamp

## Integration with Frontend

### Session Cards UI

The extracted metadata populates `SessionCard` components:

```typescript
// Example session card data from API
{
  id: "session_01",
  date: "2025-01-10",
  topic: "Crisis intervention and suicidal ideation",  // topics[0]
  strategy: "Crisis intervention with safety planning", // technique
  moodScore: 3.5,
  isMilestone: false
}
```

### Fullscreen Session Detail

Shows complete extraction:

```typescript
<SessionDetail
  topics={["Crisis intervention", "ADHD evaluation"]}
  actionItems={[
    "Create safety plan",
    "Schedule psychiatrist appointment"
  ]}
  technique="Crisis intervention with safety planning"
  summary="Patient presented in crisis..."
  confidence={0.92}
/>
```

## Speaker Role Detection

Reuses existing frontend logic from `frontend/lib/speaker-role-detection.ts`:

**Multi-heuristic approach:**
1. **First speaker** = Therapist (sessions typically start with therapist)
2. **Speaking ratio** = Therapist speaks 30-40%, Client 60-70%
3. **Combined confidence** scoring for reliability

**Example:**
```typescript
import { detectSpeakerRoles } from '@/lib/speaker-role-detection';

const result = detectSpeakerRoles(segments);
// {
//   assignments: Map {
//     "SPEAKER_00" => { role: "Therapist", confidence: 0.92 },
//     "SPEAKER_01" => { role: "Client", confidence: 0.92 }
//   }
// }
```

## Cost Analysis

**Using GPT-4o-mini:**
- Input: ~3,000 tokens (1-hour session)
- Output: ~200 tokens (metadata JSON)
- Cost: **~$0.01 per session**

**For 100 sessions/month:**
- Total cost: **~$1.00**

Much cheaper than GPT-4o ($0.15/session) with comparable quality for this task.

## Testing

### Unit Test

```bash
cd backend
python tests/test_topic_extraction.py
```

### API Test

```bash
# Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Test endpoint (in another terminal)
curl -X POST http://localhost:8000/api/sessions/session_01/extract-topics | jq
```

### Database Test

```bash
# Apply migration
cd supabase
psql $DATABASE_URL -f migrations/003_add_topic_extraction.sql

# Verify columns
psql $DATABASE_URL -c "\d therapy_sessions"
```

## Example Usage

### Backend Service

```python
from app.services.topic_extractor import extract_session_metadata

# Load your transcript
segments = [
    {"start": 0.0, "end": 5.2, "speaker": "SPEAKER_00", "text": "Hi Alex..."},
    {"start": 5.2, "end": 12.4, "speaker": "SPEAKER_01", "text": "Hi, I'm nervous..."},
    # ... more segments
]

# Extract metadata
metadata = extract_session_metadata(
    session_id="session_123",
    segments=segments
)

# Use results
print(f"Topics: {', '.join(metadata.topics)}")
print(f"Confidence: {metadata.confidence:.0%}")
```

### API Integration

```typescript
// Frontend code
async function extractTopics(sessionId: string) {
  const response = await fetch(
    `${API_URL}/api/sessions/${sessionId}/extract-topics`,
    { method: 'POST' }
  );

  const data = await response.json();

  return {
    topics: data.topics,
    actionItems: data.action_items,
    technique: data.technique,
    summary: data.summary,
    confidence: data.confidence
  };
}
```

## Error Handling

The service handles common errors gracefully:

- **No transcript found**: Returns 400 with clear message
- **Empty transcript**: Raises validation error
- **API failure**: Logs error and returns 500 with details
- **Already extracted**: Returns cached result (unless `force=true`)

## Future Enhancements

Potential improvements:

1. **Batch Processing**: Extract topics for multiple sessions in parallel
2. **Trend Analysis**: Track topic evolution over time
3. **Action Item Completion**: Mark action items as completed in future sessions
4. **Technique Effectiveness**: Correlate techniques with mood improvements
5. **Custom Prompts**: Allow therapists to customize extraction criteria

## Files Created

### Backend
- `app/services/topic_extractor.py` - Core AI service
- `tests/test_topic_extraction.py` - Test script

### Database
- `supabase/migrations/003_add_topic_extraction.sql` - Schema migration

### API
- `app/routers/sessions.py` - Added `POST /api/sessions/{id}/extract-topics` endpoint

### Documentation
- `TOPIC_EXTRACTION_README.md` - This file

## Next Steps

1. **Apply Migration**: Run the SQL migration to add database columns
2. **Test Extraction**: Run test script on mock sessions
3. **Frontend Integration**: Update SessionCard to use extracted topics
4. **Deploy**: Deploy backend with new endpoint

## Questions?

See also:
- `MOOD_ANALYSIS_README.md` - Related AI mood analysis system
- `app/services/mood_analyzer.py` - Similar AI service pattern
- `frontend/lib/speaker-role-detection.ts` - Speaker role detection logic
