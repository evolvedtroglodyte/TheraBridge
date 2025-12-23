# Backend Setup Checklist

Use this checklist to verify your Supabase + Breakthrough Detection integration is working.

---

## ✅ Database Setup

- [ ] Applied `migrations/001_add_breakthrough_detection.sql` in Supabase
- [ ] Verified `breakthrough_history` table exists
- [ ] Executed `seed-breakthrough-data.sql`
- [ ] Verified 6 sessions loaded: `SELECT COUNT(*) FROM therapy_sessions;`
- [ ] Verified 5 breakthroughs loaded: `SELECT COUNT(*) FROM breakthrough_history;`

---

## ✅ Backend Configuration

- [ ] Created `backend/.env` from `.env.example`
- [ ] Added `SUPABASE_URL` from Supabase dashboard
- [ ] Added `SUPABASE_KEY` (anon key)
- [ ] Added `SUPABASE_SERVICE_KEY` (service role key)
- [ ] Added `OPENAI_API_KEY` for breakthrough detection
- [ ] Set `JWT_SECRET` to random string
- [ ] Installed dependencies: `pip install -r requirements.txt`

---

## ✅ Server Running

- [ ] Started server: `uvicorn app.main:app --reload`
- [ ] Saw "🚀 Starting TherapyBridge API" in console
- [ ] Saw "Breakthrough detection: ✓ Enabled"
- [ ] Health check works: `curl http://localhost:8000/health`
- [ ] Returns `{"status": "healthy"}`

---

## ✅ API Endpoints Working

### Test 1: Get Demo Patient Sessions
```bash
curl http://localhost:8000/api/sessions/patient/00000000-0000-0000-0000-000000000003
```
- [ ] Returns array of 6 sessions
- [ ] 5 sessions have `"has_breakthrough": true`
- [ ] Each breakthrough has `type`, `description`, `confidence`

### Test 2: Get Specific Session
```bash
curl http://localhost:8000/api/sessions/10000000-0000-0000-0000-000000000001
```
- [ ] Returns session object
- [ ] Has `breakthrough_data` field
- [ ] Has `all_breakthroughs` array

### Test 3: Get All Breakthroughs
```bash
curl "http://localhost:8000/api/sessions/patient/00000000-0000-0000-0000-000000000003/breakthroughs?min_confidence=0.8"
```
- [ ] Returns array of breakthroughs
- [ ] All have `confidence_score >= 0.8`
- [ ] Includes `session_date` from join

---

## ✅ Breakthrough Detection Working

### Test 1: Manual Analysis
```bash
curl -X POST http://localhost:8000/api/sessions/10000000-0000-0000-0000-000000000001/analyze-breakthrough
```
- [ ] Returns `"status": "already_analyzed"`
- [ ] Shows breakthrough data

### Test 2: Force Re-Analysis
```bash
curl -X POST "http://localhost:8000/api/sessions/10000000-0000-0000-0000-000000000001/analyze-breakthrough?force=true"
```
- [ ] Takes 15-45 seconds
- [ ] Returns breakthrough analysis
- [ ] Has `primary_breakthrough` object
- [ ] Has `breakthrough_count`

### Test 3: Create New Session + Upload Transcript

**Step 3a: Create Session**
```bash
curl -X POST http://localhost:8000/api/sessions/ \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "00000000-0000-0000-0000-000000000003",
    "therapist_id": "00000000-0000-0000-0000-000000000002",
    "session_date": "2025-12-22T10:00:00Z",
    "duration_minutes": 50
  }'
```
- [ ] Returns new session with `id`
- [ ] Save the `id` for next step

**Step 3b: Upload Test Transcript**
```bash
# Create test_transcript.json with this content:
{
  "transcript": [
    {"start": 0.0, "end": 3.5, "speaker": "Therapist", "text": "How did the boundary-setting go this week?"},
    {"start": 3.5, "end": 8.2, "speaker": "Patient", "text": "I actually said no to my mom for the first time! It was scary but liberating."},
    {"start": 8.2, "end": 12.0, "speaker": "Therapist", "text": "That's a significant step. How did it feel?"},
    {"start": 12.0, "end": 16.5, "speaker": "Patient", "text": "Like a weight lifted. I didn't realize how much I was carrying."}
  ]
}

# Upload it
curl -X POST http://localhost:8000/api/sessions/{SESSION_ID}/upload-transcript \
  -H "Content-Type: application/json" \
  -d @test_transcript.json
```
- [ ] Returns `"status": "processing"`
- [ ] Wait 30 seconds

**Step 3c: Check Results**
```bash
curl http://localhost:8000/api/sessions/{SESSION_ID}
```
- [ ] Has `"has_breakthrough": true` (should detect behavioral_commitment)
- [ ] Has `breakthrough_data` with type, description, confidence
- [ ] `breakthrough_analyzed_at` is set

---

## ✅ Database Verification

```sql
-- In Supabase SQL editor

-- Check sessions
SELECT id, has_breakthrough, breakthrough_analyzed_at
FROM therapy_sessions
ORDER BY created_at DESC
LIMIT 10;

-- Check breakthroughs
SELECT
  bh.breakthrough_type,
  bh.confidence_score,
  ts.session_date
FROM breakthrough_history bh
JOIN therapy_sessions ts ON bh.session_id = ts.id
ORDER BY bh.confidence_score DESC;

-- Check patient summary
SELECT * FROM get_patient_breakthrough_summary('00000000-0000-0000-0000-000000000003');
```

- [ ] All queries return expected data
- [ ] No errors in console

---

## ✅ Troubleshooting Passed

### If "Configuration errors: SUPABASE_URL is required":
- [ ] Created `.env` file
- [ ] Added all required environment variables
- [ ] Restarted server

### If "Breakthrough detection failed":
- [ ] Verified `OPENAI_API_KEY` is valid
- [ ] Checked OpenAI account has credits
- [ ] Reviewed server logs for error details

### If "Session not found":
- [ ] Ran seed data SQL script
- [ ] Verified patient ID exists
- [ ] Checked RLS policies in Supabase

### If No breakthroughs detected:
- [ ] Checked transcript format (has `start`, `end`, `speaker`, `text`)
- [ ] Verified speaker labels are correct
- [ ] Tried lowering `min_confidence` to 0.5
- [ ] Reviewed `session_summary` for context

---

## 🎉 All Checks Passed?

**Congratulations!** Your backend is fully integrated and working.

**Next steps:**
1. Review `SUPABASE_BREAKTHROUGH_INTEGRATION.md` for frontend integration
2. Tell me which UI components should display breakthroughs
3. I'll create the frontend integration code

---

## 📊 Expected Results Summary

After completing all checks, you should have:

✅ **Database**: 6 sessions, 5 breakthroughs stored
✅ **API**: 7+ endpoints responding correctly
✅ **Detection**: New transcripts automatically analyzed
✅ **Background Jobs**: Async processing working
✅ **Error Handling**: Graceful failures and logging

**Approximate costs:** $0.05-0.10 per breakthrough detection

**Performance:** 15-45 seconds per session analysis
