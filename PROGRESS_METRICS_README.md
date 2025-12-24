# Progress Metrics Extraction System

**Complete system for extracting and visualizing progress metrics from therapy session analysis.**

---

## Overview

This system automatically extracts progress metrics from audio pipeline analysis and serves them to the frontend **ProgressPatternsCard** for visualization.

### Key Features

- ✅ **Mood Trends:** AI-analyzed mood scores with trend detection (improving/declining/stable/variable)
- ✅ **Session Consistency:** Attendance patterns, streaks, and engagement metrics
- ✅ **Direct Recharts integration:** Chart data formatted for immediate use
- ✅ **Smart insights:** AI-generated insights based on trend analysis
- ✅ **Real-time updates:** Automatically refreshes when new sessions complete analysis

---

## Architecture

```
Audio Pipeline → Wave 1 Analysis → Database → API Endpoint → Frontend Hook → ProgressPatternsCard
                 (mood_score,                 (extraction)    (fetch)        (visualization)
                  session_date)
```

### Components

1. **Backend Service:** `backend/app/services/progress_metrics_extractor.py`
2. **API Endpoint:** `GET /api/sessions/patient/{patient_id}/progress-metrics`
3. **Frontend Hook:** `frontend/app/patient/hooks/useProgressMetrics.ts`
4. **UI Component:** `frontend/app/patient/components/ProgressPatternsCard.tsx`

---

## Data Flow

### Step 1: Audio Pipeline Completes Wave 1
```json
{
  "session_id": "uuid",
  "session_num": 10,
  "mood_score": 5.5,
  "mood_confidence": 0.85,
  "session_date": "2025-12-23T10:00:00Z"
}
```

### Step 2: Backend Extraction Service
```python
# Transform database sessions → pipeline format → extract metrics
metrics = ProgressMetricsExtractor.extract_from_pipeline_json(pipeline_data)
```

### Step 3: API Response
```json
{
  "metrics": [
    {
      "title": "Mood Trends",
      "description": "AI-analyzed emotional state over time",
      "emoji": "📈",
      "insight": "📈 IMPROVING: +36% overall (Recent avg: 6.5/10, Historical: 5.5/10)",
      "chartData": [
        {"session": "S10", "mood": 5.5, "date": "Dec 23", "confidence": 0.85},
        {"session": "S11", "mood": 6.5, "date": "Dec 24", "confidence": 0.85},
        {"session": "S12", "mood": 7.5, "date": "Dec 25", "confidence": 0.85}
      ]
    },
    {
      "title": "Session Consistency",
      "description": "Attendance patterns and engagement",
      "emoji": "📅",
      "insight": "100% attendance rate - Excellent (Score: 100/100). 3 week streak.",
      "chartData": [
        {"week": "Week 1", "attended": 1},
        {"week": "Week 2", "attended": 1},
        {"week": "Week 3", "attended": 1}
      ]
    }
  ],
  "extracted_at": "2025-12-24T00:40:00Z",
  "session_count": 3,
  "date_range": "Dec 23 - Dec 25, 2025"
}
```

### Step 4: Frontend Hook
```tsx
const { metrics, isLoading, sessionCount, dateRange } = useProgressMetrics({
  patientId: 'patient-uuid',
  useRealData: true
});
```

### Step 5: Recharts Visualization
```tsx
<AreaChart data={metric.chartData}>
  <Area dataKey="mood" stroke="#5AB9B4" />
</AreaChart>
```

---

## API Usage

### Endpoint
```
GET /api/sessions/patient/{patient_id}/progress-metrics
```

### Query Parameters
- `limit` (optional): Maximum number of sessions to include (default: 50)

### Response Schema
```typescript
interface ProgressMetricsResponse {
  metrics: ProgressMetric[];
  extracted_at: string;
  session_count: number;
  date_range: string;
}

interface ProgressMetric {
  title: string;
  description: string;
  emoji: string;
  insight: string;
  chartData: ChartDataPoint[];
}
```

### Example Request
```bash
curl http://localhost:8000/api/sessions/patient/abc123/progress-metrics?limit=50
```

---

## Frontend Integration

### 1. Using the Hook

```tsx
import { useProgressMetrics } from '@/app/patient/hooks/useProgressMetrics';

function MyComponent() {
  const {
    metrics,
    isLoading,
    error,
    sessionCount,
    dateRange
  } = useProgressMetrics({
    patientId: 'patient-uuid',
    limit: 50,
    useRealData: true
  });

  if (isLoading) return <div>Loading metrics...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Progress Overview ({sessionCount} sessions)</h2>
      <p>{dateRange}</p>
      {metrics.map(metric => (
        <MetricCard key={metric.title} metric={metric} />
      ))}
    </div>
  );
}
```

### 2. Displaying Metrics

```tsx
{metrics.map(metric => (
  <div key={metric.title}>
    <h3>{metric.emoji} {metric.title}</h3>
    <p>{metric.description}</p>
    <ResponsiveContainer width="100%" height={250}>
      <AreaChart data={metric.chartData}>
        <Area dataKey="mood" stroke="#5AB9B4" />
      </AreaChart>
    </ResponsiveContainer>
    <p>{metric.insight}</p>
  </div>
))}
```

---

## Metric Types

### 1. Mood Trends

**What it measures:** AI-analyzed emotional state over time (0-10 scale)

**Chart type:** Area chart

**Data format:**
```typescript
{
  session: "S10",      // Session label
  mood: 5.5,           // Mood score (0-10)
  date: "Dec 23",      // Display date
  confidence: 0.85     // AI confidence (0-1)
}
```

**Trend detection:**
- **📈 IMPROVING:** Recent avg > historical avg by 0.5+
- **📉 DECLINING:** Recent avg < historical avg by 0.5+
- **↕️ VARIABLE:** Range > 2.0 points
- **➡️ STABLE:** Minimal variance

**Example insight:**
> "📈 IMPROVING: +36% overall (Recent avg: 6.5/10, Historical: 5.5/10)"

---

### 2. Session Consistency

**What it measures:** Attendance patterns and engagement

**Chart type:** Bar chart

**Data format:**
```typescript
{
  week: "Week 1",      // Week label
  attended: 1          // Binary (0 or 1)
}
```

**Metrics calculated:**
- Attendance rate (%)
- Consistency score (0-100)
- Longest streak (weeks)
- Average gap between sessions (days)

**Example insight:**
> "100% attendance rate - Excellent (Score: 100/100). 10 week streak."

---

## Testing

### Backend Service Test

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

📅 Session Consistency
Insight: 100% attendance rate - Excellent (Score: 100/100). 3 week streak.
```

### API Endpoint Test

```bash
# Start backend server
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Test endpoint
curl http://localhost:8000/api/sessions/patient/PATIENT_UUID/progress-metrics
```

### Frontend Integration Test

1. Set `NEXT_PUBLIC_USE_REAL_API=true` in `frontend/.env.local`
2. Start frontend: `npm run dev`
3. Navigate to patient dashboard
4. Open ProgressPatternsCard
5. Verify metrics display correctly

---

## Configuration

### Adding New Metrics

**Step 1:** Add extraction logic to `ProgressMetricsExtractor`:

```python
@staticmethod
def _extract_new_metric(sessions: List[Dict[str, Any]]) -> ProgressMetric:
    chart_data = []
    # ... extraction logic

    return ProgressMetric(
        title="New Metric",
        description="Description",
        emoji="🎯",
        insight="Insight text",
        chartData=chart_data
    )
```

**Step 2:** Update `extract_from_pipeline_json`:

```python
new_metric = ProgressMetricsExtractor._extract_new_metric(sessions)
return ProgressMetricsResponse(
    metrics=[mood_metric, consistency_metric, new_metric],
    ...
)
```

**Step 3:** Add to frontend `DISPLAYED_METRICS`:

```tsx
const DISPLAYED_METRICS = [
  'Mood Trends',
  'Session Consistency',
  'New Metric'  // Add here
];
```

**Step 4:** Add chart rendering in `renderChart`:

```tsx
if (metric.title === 'New Metric') {
  return <LineChart data={metric.chartData}>...</LineChart>;
}
```

---

## Performance

### Optimization Strategies

1. **Caching:** API responses are cached at the database level
2. **Lazy loading:** Metrics load on-demand when card is opened
3. **Batch processing:** All metrics extracted in single pass
4. **Efficient queries:** Only sessions with `mood_score` are fetched

### Expected Load Times

- **Backend extraction:** ~50ms for 50 sessions
- **API response:** ~100-200ms (including DB query)
- **Frontend render:** ~50ms for charts

---

## Troubleshooting

### Issue: No metrics returned

**Cause:** No sessions with completed Wave 1 analysis

**Solution:**
1. Verify sessions exist: `SELECT * FROM therapy_sessions WHERE patient_id = 'uuid'`
2. Check Wave 1 completion: `SELECT mood_score FROM therapy_sessions WHERE mood_score IS NOT NULL`
3. Run analysis: `POST /api/sessions/{session_id}/analyze-mood`

---

### Issue: Chart data not displaying

**Cause:** Incorrect data format for Recharts

**Solution:**
1. Verify `chartData` structure matches expected format
2. Check console for Recharts warnings
3. Validate data types (numbers vs strings)

---

### Issue: API returns 500 error

**Cause:** Missing dependencies or malformed pipeline data

**Solution:**
1. Check backend logs: `tail -f backend/app.log`
2. Verify pipeline data structure matches expected format
3. Ensure all sessions have `mood_score` and `session_date`

---

## Future Enhancements

### Planned Metrics

1. **Homework Impact:** Correlation between homework completion and mood
2. **Strategy Effectiveness:** Which therapeutic techniques yield best results
3. **Goal Progress:** Tracking progress toward treatment goals
4. **Breakthrough Frequency:** Rate of therapeutic breakthroughs

### Roadmap

- [ ] Week-over-week comparison views
- [ ] Export metrics to PDF/CSV
- [ ] Custom date range filtering
- [ ] Therapist-facing analytics dashboard
- [ ] Predictive analytics (relapse risk, dropout risk)

---

## Related Documentation

- **Backend Analysis Pipeline:** `backend/README.md`
- **Frontend Dashboard:** `frontend/app/patient/README.md`
- **Mood Analysis System:** `MOOD_ANALYSIS_README.md`
- **Topic Extraction System:** `TOPIC_EXTRACTION_README.md`

---

## Support

For questions or issues, see:
- **GitHub Issues:** https://github.com/anthropics/claude-code/issues
- **Project Documentation:** `Project MDs/TherapyBridge.md`
