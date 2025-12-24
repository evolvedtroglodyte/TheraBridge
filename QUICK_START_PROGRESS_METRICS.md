# Quick Start: Progress Metrics System

**Get progress metrics working in 3 steps** ⚡

---

## Step 1: Run Backend Extraction Test

```bash
cd backend
source venv/bin/activate
python app/services/progress_metrics_extractor.py
```

**Expected output:**
```
✅ Extracted 2 metrics
📊 Date Range: Dec 24 - Dec 24, 2025
📈 Session Count: 3

📈 Mood Trends
Insight: 📈 IMPROVING: +36% overall (Recent avg: 6.5/10, Historical: 5.5/10)
```

---

## Step 2: Test API Endpoint

**Start backend server:**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

**Test endpoint (replace `PATIENT_UUID`):**
```bash
curl http://localhost:8000/api/sessions/patient/PATIENT_UUID/progress-metrics
```

**Expected response:**
```json
{
  "metrics": [
    {
      "title": "Mood Trends",
      "emoji": "📈",
      "insight": "📈 IMPROVING: +36% overall",
      "chartData": [...]
    },
    {
      "title": "Session Consistency",
      "emoji": "📅",
      "insight": "100% attendance rate - Excellent",
      "chartData": [...]
    }
  ],
  "session_count": 10,
  "date_range": "Nov 15 - Dec 24, 2025"
}
```

---

## Step 3: Enable in Frontend

**Edit `frontend/.env.local`:**
```bash
NEXT_PUBLIC_USE_REAL_API=true
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Start frontend:**
```bash
cd frontend
npm run dev
```

**Navigate to:** http://localhost:3000/patient/dashboard-v3

**Open ProgressPatternsCard** → Metrics should display from API

---

## Verify It Works

### ✅ Backend Test Passes
- Extraction logic produces valid metrics
- JSON output saved to `progress_metrics_extraction_results.json`

### ✅ API Responds
- Returns 200 OK with metrics array
- `session_count` > 0
- Chart data has correct structure

### ✅ Frontend Displays
- ProgressPatternsCard shows real metrics
- Charts render with API data
- Insights display correctly

---

## Troubleshooting

### No sessions found
**Solution:** Upload demo transcripts first:
```bash
POST /api/sessions/upload-demo-transcript
{
  "session_file": "session_10_alex_chen.json"
}
```

### 404 Patient not found
**Solution:** Use correct patient UUID from database:
```sql
SELECT id FROM users WHERE role = 'patient' LIMIT 1;
```

### Frontend shows mock data
**Solution:** Check `NEXT_PUBLIC_USE_REAL_API=true` in `.env.local`

---

## What's Next?

1. **Add more sessions:** Upload 10-12 transcripts for better trends
2. **Test trend detection:** Upload sessions with varying mood scores
3. **Custom metrics:** Add new metric types (see `PROGRESS_METRICS_README.md`)
4. **Export data:** Implement CSV/PDF export for therapist reports

---

## File Locations

```
backend/
├── app/services/progress_metrics_extractor.py  # Extraction service
└── app/routers/sessions.py                     # API endpoint (line 1398)

frontend/
├── app/patient/hooks/useProgressMetrics.ts     # React hook
└── app/patient/components/ProgressPatternsCard.tsx  # UI component
```

---

## Complete Documentation

See `PROGRESS_METRICS_README.md` for:
- Full architecture details
- API reference
- Frontend integration guide
- Adding custom metrics
- Performance optimization
