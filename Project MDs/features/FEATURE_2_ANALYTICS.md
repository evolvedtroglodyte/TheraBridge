# Feature 2: Analytics Dashboard

## Overview
Provide therapists with insights into patient progress, session patterns, and treatment effectiveness through data visualization.

## Requirements

### Key Metrics
1. **Session Statistics**
   - Total sessions per patient
   - Session frequency trends
   - Average session duration
   - Sessions by status (completed, cancelled, no-show)

2. **Mood Tracking**
   - Mood scores over time (if captured)
   - Mood trends by patient
   - Pre/post session mood comparisons

3. **Progress Indicators**
   - Goal completion rates
   - Treatment plan progress
   - Action item completion

4. **Practice Overview** (Therapist-level)
   - Total active patients
   - Sessions this week/month
   - Revenue tracking (future)

## Database Schema

```sql
-- Session metrics (denormalized for performance)
CREATE TABLE session_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES users(id),
    therapist_id UUID REFERENCES users(id),
    session_date DATE NOT NULL,
    duration_minutes INTEGER,
    mood_pre INTEGER CHECK (mood_pre BETWEEN 1 AND 10),
    mood_post INTEGER CHECK (mood_post BETWEEN 1 AND 10),
    topics_discussed JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Aggregated daily stats (materialized for dashboard)
CREATE TABLE daily_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    therapist_id UUID REFERENCES users(id),
    stat_date DATE NOT NULL,
    total_sessions INTEGER DEFAULT 0,
    total_patients_seen INTEGER DEFAULT 0,
    avg_session_duration DECIMAL(5,2),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(therapist_id, stat_date)
);

-- Patient progress snapshots
CREATE TABLE patient_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES users(id),
    snapshot_date DATE NOT NULL,
    goals_total INTEGER DEFAULT 0,
    goals_completed INTEGER DEFAULT 0,
    action_items_total INTEGER DEFAULT 0,
    action_items_completed INTEGER DEFAULT 0,
    overall_progress_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### GET /api/v1/analytics/overview
Returns therapist's practice overview.

Response:
```json
{
    "total_patients": 24,
    "active_patients": 18,
    "sessions_this_week": 12,
    "sessions_this_month": 48,
    "upcoming_sessions": 5,
    "completion_rate": 0.92
}
```

### GET /api/v1/analytics/patients/{patient_id}/progress
Returns detailed progress for a specific patient.

Response:
```json
{
    "patient_id": "uuid",
    "total_sessions": 15,
    "first_session_date": "2024-01-15",
    "last_session_date": "2024-03-10",
    "session_frequency": {
        "weekly_average": 1.2,
        "trend": "stable"
    },
    "mood_trend": {
        "data": [
            {"date": "2024-01", "avg_pre": 4.2, "avg_post": 5.8},
            {"date": "2024-02", "avg_pre": 5.1, "avg_post": 6.3},
            {"date": "2024-03", "avg_pre": 5.8, "avg_post": 7.1}
        ],
        "trend": "improving"
    },
    "goals": {
        "total": 8,
        "completed": 5,
        "in_progress": 2,
        "not_started": 1
    }
}
```

### GET /api/v1/analytics/sessions/trends
Returns session trends over time.

Query params:
- `period`: week | month | quarter | year
- `patient_id`: (optional) filter by patient

Response:
```json
{
    "period": "month",
    "data": [
        {"label": "Jan", "sessions": 12, "unique_patients": 8},
        {"label": "Feb", "sessions": 15, "unique_patients": 10},
        {"label": "Mar", "sessions": 18, "unique_patients": 11}
    ]
}
```

### GET /api/v1/analytics/topics
Returns frequently discussed topics across sessions.

Response:
```json
{
    "topics": [
        {"name": "anxiety", "count": 45, "percentage": 0.35},
        {"name": "relationships", "count": 38, "percentage": 0.29},
        {"name": "work stress", "count": 25, "percentage": 0.19},
        {"name": "depression", "count": 22, "percentage": 0.17}
    ]
}
```

## Implementation Notes

### Performance Considerations
- Use materialized views or daily aggregation jobs for dashboard metrics
- Cache frequently accessed analytics (Redis, 5-minute TTL)
- Paginate historical data queries

### Background Jobs
```python
# Daily aggregation task (run at midnight)
async def aggregate_daily_stats():
    """Compute and store daily statistics for all therapists."""
    pass

# Weekly progress snapshot
async def snapshot_patient_progress():
    """Create weekly progress snapshots for trend analysis."""
    pass
```

### Privacy & Security
- All analytics endpoints require authentication
- Therapists can only see their own patients' data
- Patients can only see their own progress
- No PII in topic analysis (anonymized/aggregated)

## Dependencies
- Background task scheduler (APScheduler or Celery)
- Redis for caching (optional but recommended)

## Testing Checklist
- [ ] Overview endpoint returns correct counts
- [ ] Patient progress calculates trends correctly
- [ ] Session trends aggregation is accurate
- [ ] Topic extraction from notes works
- [ ] Authorization: therapist can't see other's patients
- [ ] Authorization: patient can only see own data
- [ ] Caching works and invalidates correctly

## Files to Create/Modify
- `app/routers/analytics.py`
- `app/services/analytics.py`
- `app/models/analytics.py`
- `app/tasks/aggregation.py`
- `alembic/versions/xxx_add_analytics_tables.py`
