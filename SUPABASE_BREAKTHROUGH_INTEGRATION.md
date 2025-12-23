# Supabase + Breakthrough Detection - Complete Integration Guide

## 🎯 What Was Built

Complete integration of breakthrough detection with Supabase PostgreSQL database, including:

✅ Database migrations for breakthrough storage
✅ Seed data with 6 realistic therapy sessions (5 with breakthroughs)
✅ FastAPI backend with Supabase client
✅ Automatic breakthrough detection on transcript upload
✅ RESTful API endpoints for session management
✅ Background task processing for async analysis

---

## 📁 Files Created

### Database Layer
- **`supabase/migrations/001_add_breakthrough_detection.sql`** - Schema migration
- **`supabase/seed-breakthrough-data.sql`** - Demo user + 6 sessions with breakthroughs

### Backend Layer
- **`backend/app/config.py`** - Configuration management (Supabase + OpenAI)
- **`backend/app/database.py`** - Supabase client + helper functions
- **`backend/app/main.py`** - FastAPI application
- **`backend/app/routers/sessions.py`** - Session API endpoints
- **`backend/requirements.txt`** - Python dependencies
- **`backend/.env.example`** - Environment variable template

---

## 🗄️ Database Schema

### New Fields in `therapy_sessions` Table

```sql
ALTER TABLE therapy_sessions ADD COLUMN
  has_breakthrough BOOLEAN DEFAULT FALSE,
  breakthrough_data JSONB,
  breakthrough_analyzed_at TIMESTAMP;
```

### New `breakthrough_history` Table

Stores ALL breakthroughs detected in a session (not just primary):

```sql
CREATE TABLE breakthrough_history (
  id UUID PRIMARY KEY,
  session_id UUID REFERENCES therapy_sessions(id),
  breakthrough_type VARCHAR(50),
  description TEXT,
  evidence TEXT,
  confidence_score DECIMAL(3,2),
  timestamp_start DECIMAL(10,2),
  timestamp_end DECIMAL(10,2),
  dialogue_excerpt JSONB,
  is_primary BOOLEAN DEFAULT FALSE
);
```

### Breakthrough Types

```
- cognitive_insight       (connecting past to present)
- emotional_shift         (resistance → acceptance)
- behavioral_commitment   (first boundary-setting)
- relational_realization  (attachment pattern recognition)
- self_compassion         (criticism → kindness)
```

---

## 🚀 Setup Instructions

### 1. Apply Database Migrations

```bash
# Navigate to supabase directory
cd supabase

# Apply migration (via Supabase dashboard or CLI)
supabase db push

# OR manually run in Supabase SQL editor:
# 1. Copy contents of migrations/001_add_breakthrough_detection.sql
# 2. Paste and execute in SQL editor
```

### 2. Seed Demo Data

```bash
# In Supabase SQL editor, execute:
# seed-breakthrough-data.sql

# This creates:
# - Demo patient: alex.chen@demo.com
# - Demo therapist: dr.mitchell@demo.com
# - 6 therapy sessions (5 with breakthroughs, 1 without)
```

### 3. Configure Backend

```bash
cd backend

# Copy environment template
cp .env.example .env

# Edit .env with your credentials:
nano .env
```

**Required Environment Variables:**

```bash
# Get these from Supabase Dashboard → Settings → API
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# OpenAI API key for breakthrough detection
OPENAI_API_KEY=sk-your-openai-key

# JWT settings
JWT_SECRET=your-random-secret-here
```

### 4. Install Dependencies

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 5. Start Backend Server

```bash
cd backend
source venv/bin/activate

# Run with auto-reload
uvicorn app.main:app --reload --port 8000

# You should see:
# 🚀 Starting TherapyBridge API
#    Environment: development
#    Supabase URL: https://...
#    Breakthrough detection: ✓ Enabled
```

---

## 🔌 API Endpoints

### Base URL
```
http://localhost:8000
```

### Health Check
```bash
GET /health

Response:
{
  "status": "healthy",
  "environment": "development",
  "breakthrough_detection": "enabled"
}
```

### Get Patient Sessions
```bash
GET /api/sessions/patient/{patient_id}?include_breakthroughs=true

Response:
[
  {
    "id": "session-uuid",
    "session_date": "2025-12-10T10:00:00Z",
    "duration_minutes": 50,
    "has_breakthrough": true,
    "breakthrough_data": {
      "type": "cognitive_insight",
      "description": "Patient connected...",
      "confidence": 0.87
    },
    "all_breakthroughs": [...]
  }
]
```

### Upload Transcript (Auto-Detect Breakthroughs)
```bash
POST /api/sessions/{session_id}/upload-transcript

Body:
{
  "transcript": [
    {"start": 0.0, "end": 3.5, "speaker": "Therapist", "text": "..."},
    {"start": 3.5, "end": 8.2, "speaker": "Patient", "text": "..."}
  ],
  "audio_file_url": "https://..."
}

Response:
{
  "session_id": "session-uuid",
  "status": "processing",
  "message": "Transcript uploaded. Breakthrough detection in progress."
}
```

### Manual Breakthrough Analysis
```bash
POST /api/sessions/{session_id}/analyze-breakthrough?force=true

Response:
{
  "session_id": "session-uuid",
  "has_breakthrough": true,
  "primary_breakthrough": {
    "type": "cognitive_insight",
    "description": "...",
    "confidence": 0.92,
    "timestamp_start": 68.0
  },
  "breakthrough_count": 2,
  "analyzed_at": "2025-12-22T12:34:56Z"
}
```

### Get All Patient Breakthroughs
```bash
GET /api/sessions/patient/{patient_id}/breakthroughs?min_confidence=0.7

Response:
[
  {
    "id": "bt-uuid",
    "session_id": "session-uuid",
    "breakthrough_type": "cognitive_insight",
    "description": "...",
    "confidence_score": 0.87,
    "timestamp_start": 512.3,
    "therapy_sessions": {
      "session_date": "2025-12-10T10:00:00Z"
    }
  }
]
```

---

## 🔄 Integration Flow

### Demo User Login (Seed Data)

```typescript
// Frontend: When demo user logs in
const demoUser = {
  email: 'alex.chen@demo.com',
  password: 'demo' // (In production, use proper auth)
};

// Backend automatically returns pre-populated sessions with breakthroughs
```

### Real User Transcript Upload

```
1. User uploads audio file
   ↓
2. Audio transcription pipeline processes
   ↓
3. POST /api/sessions/{id}/upload-transcript
   ↓
4. Backend stores transcript in Supabase
   ↓
5. Background task triggers breakthrough detection
   ↓
6. Results stored in breakthrough_history table
   ↓
7. Frontend polls /api/sessions/{id} until complete
   ↓
8. Display breakthrough in UI
```

### Frontend Integration Example

```typescript
// 1. Upload transcript after audio processing
const uploadTranscript = async (sessionId: string, transcript: any[]) => {
  const response = await fetch(
    `${API_URL}/api/sessions/${sessionId}/upload-transcript`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transcript })
    }
  );
  return response.json();
};

// 2. Poll for breakthrough results
const checkBreakthroughStatus = async (sessionId: string) => {
  const response = await fetch(`${API_URL}/api/sessions/${sessionId}`);
  const session = await response.json();
  return session.has_breakthrough;
};

// 3. Display in UI
{session.has_breakthrough && (
  <BreakthroughBadge
    type={session.breakthrough_data.type}
    description={session.breakthrough_data.description}
    confidence={session.breakthrough_data.confidence}
  />
)}
```

---

## 🧪 Testing the Integration

### 1. Verify Database Setup

```sql
-- In Supabase SQL Editor
SELECT * FROM therapy_sessions WHERE has_breakthrough = TRUE;
-- Should return 5 sessions

SELECT * FROM breakthrough_history ORDER BY confidence_score DESC;
-- Should return 5 breakthrough records
```

### 2. Test API Endpoints

```bash
# Get demo patient sessions
curl http://localhost:8000/api/sessions/patient/00000000-0000-0000-0000-000000000003

# Get all breakthroughs
curl "http://localhost:8000/api/sessions/patient/00000000-0000-0000-0000-000000000003/breakthroughs?min_confidence=0.8"

# Verify specific session
curl http://localhost:8000/api/sessions/10000000-0000-0000-0000-000000000001
```

### 3. Test Breakthrough Detection

```bash
# Create test session
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "00000000-0000-0000-0000-000000000003",
    "therapist_id": "00000000-0000-0000-0000-000000000002",
    "session_date": "2025-12-22T10:00:00Z",
    "duration_minutes": 50
  }'

# Upload transcript (use example from breakthrough_detection_example.py)
curl -X POST http://localhost:8000/api/sessions/{session_id}/upload-transcript \
  -H "Content-Type: application/json" \
  -d @test_transcript.json

# Check results (wait 30 seconds for analysis)
curl http://localhost:8000/api/sessions/{session_id}
```

---

## 📊 Seed Data Overview

### Session 1: Eating Disorder Discovery
- **Type**: Cognitive Insight
- **Confidence**: 0.87
- **Breakthrough**: Connected mother's criticism to eating disorder development

### Session 2: Emotional Processing
- **Type**: Self-Compassion
- **Confidence**: 0.82
- **Breakthrough**: Shifted from self-criticism to self-acceptance

### Session 3: CBT - Cognitive Restructuring
- **Type**: Cognitive Insight
- **Confidence**: 0.91
- **Breakthrough**: Recognized catastrophizing pattern in real-time

### Session 4: Boundary Setting
- **Type**: Behavioral Commitment
- **Confidence**: 0.85
- **Breakthrough**: First successful boundary with mother

### Session 5: Attachment Patterns
- **Type**: Relational Realization
- **Confidence**: 0.94
- **Breakthrough**: Connected childhood abandonment to adult relationship anxiety

### Session 6: Maintenance Session
- **NO BREAKTHROUGH** - Routine check-in session

---

## 🎨 Frontend UI Components (To Build)

### 1. Breakthrough Timeline Marker

```typescript
<TimelineSidebar sessions={sessions}>
  {session.has_breakthrough && (
    <BreakthroughStar
      className="absolute -top-2 left-1/2"
      glowColor="amber"
    />
  )}
</TimelineSidebar>
```

### 2. Session Card Badge

```typescript
<SessionCard session={session}>
  {session.has_breakthrough && (
    <Badge variant="gold" className="ml-auto">
      ⭐ {session.breakthrough_data.type.replace('_', ' ')}
    </Badge>
  )}
</SessionCard>
```

### 3. Breakthrough Detail Modal

```typescript
<BreakthroughModal
  open={showModal}
  breakthrough={session.breakthrough_data}
  allBreakthroughs={session.all_breakthroughs}
>
  <BreakthroughHeader
    type={breakthrough.type}
    confidence={breakthrough.confidence}
  />

  <BreakthroughDescription>
    {breakthrough.description}
  </BreakthroughDescription>

  <BreakthroughEvidence>
    {breakthrough.evidence}
  </BreakthroughEvidence>

  <DialogueExcerpt turns={breakthrough.dialogue_excerpt} />
</BreakthroughModal>
```

### 4. Breakthrough Summary Stats

```typescript
const breakthroughSummary = await fetch(
  `/api/sessions/patient/${patientId}/breakthroughs`
);

<StatsCard>
  <Stat label="Total Breakthroughs" value={breakthroughs.length} />
  <Stat label="Avg Confidence" value="0.87" />
  <Stat label="Most Common" value="Cognitive Insight" />
</StatsCard>
```

---

## 🔧 Configuration Options

### `backend/app/config.py`

```python
# Minimum confidence to report breakthroughs
BREAKTHROUGH_MIN_CONFIDENCE=0.6  # Default: 0.6 (60%)

# Auto-analyze new transcripts
BREAKTHROUGH_AUTO_ANALYZE=True   # Default: True
```

### Adjust Confidence Threshold

```python
# In routers/sessions.py
@router.get("/patient/{patient_id}/breakthroughs")
async def get_patient_breakthroughs(
    min_confidence: float = 0.7  # Increase for more selective
):
    ...
```

---

## 🐛 Troubleshooting

### "Configuration errors: SUPABASE_URL is required"

```bash
# Create .env file
cd backend
cp .env.example .env

# Add your Supabase credentials
nano .env
```

### "Breakthrough detection failed"

```bash
# Check OpenAI API key
echo $OPENAI_API_KEY

# Verify in logs
tail -f backend/logs/app.log
```

### "Session not found"

```bash
# Verify seed data loaded
SELECT COUNT(*) FROM therapy_sessions;
# Should return at least 6

# Check patient ID
SELECT id FROM patients;
```

### No breakthroughs detected

- Check transcript quality (speaker labels correct?)
- Lower confidence threshold (min_confidence=0.5)
- Review session summary for context
- Verify OpenAI API is responding

---

## 💰 Cost Estimation

**Per breakthrough detection:**
- GPT-4o API call: ~$0.05-0.10
- Supabase queries: Free (within limits)

**For 100 sessions/month:**
- ~$5-10/month in OpenAI costs
- Results cached in database (analyze once per session)

---

## 🎯 Next Steps

1. ✅ **Database setup** - Apply migrations and seed data
2. ✅ **Backend running** - Start FastAPI server
3. 🔲 **Test endpoints** - Verify API responses
4. 🔲 **Build frontend UI** - Create breakthrough components
5. 🔲 **Integrate frontend** - Connect to backend API
6. 🔲 **Deploy** - Production deployment with environment variables

---

## 📚 Additional Resources

- **Breakthrough Algorithm**: `backend/app/services/BREAKTHROUGH_DETECTION_README.md`
- **API Routes**: `backend/app/routers/sessions.py`
- **Database Schema**: `supabase/schema.sql`
- **Seed Data**: `supabase/seed-breakthrough-data.sql`

---

**🎉 Integration Complete!** Your backend is now ready to detect and store breakthroughs automatically.

When you're ready to connect the frontend, let me know the UI component destinations for breakthrough displays!
