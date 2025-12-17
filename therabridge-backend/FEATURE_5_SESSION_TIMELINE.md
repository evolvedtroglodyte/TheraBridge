# Feature 5: Session Timeline

## Overview
Provide a comprehensive, chronological view of a patient's therapy journey with filterable events, milestones, and session summaries.

## Requirements

### Timeline Events
1. **Sessions**
   - Session date and duration
   - Key topics discussed
   - Mood indicators
   - Link to full session notes

2. **Milestones**
   - Treatment plan created/updated
   - Goals achieved
   - Significant breakthroughs
   - Assessment completions

3. **Clinical Events**
   - Diagnosis changes
   - Medication changes (if tracked)
   - Crisis events
   - Referrals made

4. **Administrative Events**
   - First session
   - Missed appointments
   - Treatment plan reviews
   - Discharge/Transfer

### Features
- Infinite scroll with lazy loading
- Filter by event type
- Search within timeline
- Date range selection
- Export timeline summary

## Database Schema

```sql
-- Timeline events (unified event store)
CREATE TABLE timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES users(id) ON DELETE CASCADE,
    therapist_id UUID REFERENCES users(id),
    event_type VARCHAR(50) NOT NULL,
    event_subtype VARCHAR(50),
    event_date TIMESTAMP NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    metadata JSONB, -- type-specific data
    related_entity_type VARCHAR(50), -- 'session', 'goal', 'plan', etc.
    related_entity_id UUID,
    importance VARCHAR(20) DEFAULT 'normal', -- 'low', 'normal', 'high', 'milestone'
    is_private BOOLEAN DEFAULT false, -- therapist-only visibility
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_timeline_patient_date ON timeline_events(patient_id, event_date DESC);
CREATE INDEX idx_timeline_type ON timeline_events(event_type);

-- Event types enum reference:
-- 'session' - therapy sessions
-- 'milestone' - achievements, breakthroughs
-- 'clinical' - diagnosis, medication, crisis
-- 'administrative' - scheduling, transfers
-- 'goal' - goal status changes
-- 'assessment' - completed assessments
-- 'note' - therapist notes/observations
```

## API Endpoints

### GET /api/v1/patients/{patient_id}/timeline
Get patient timeline with pagination.

Query params:
- `limit`: Number of events (default: 20)
- `cursor`: Pagination cursor (event ID)
- `event_types`: Comma-separated types to include
- `start_date`: Filter from date
- `end_date`: Filter to date
- `importance`: Filter by importance level
- `search`: Search in title/description

Response:
```json
{
    "events": [
        {
            "id": "uuid",
            "event_type": "session",
            "event_date": "2024-03-10T14:00:00Z",
            "title": "Session #15 - Progress Review",
            "description": "Discussed anxiety management progress. Patient reported improved sleep.",
            "metadata": {
                "session_id": "uuid",
                "duration_minutes": 50,
                "mood_pre": 5,
                "mood_post": 7,
                "topics": ["anxiety", "sleep", "coping strategies"]
            },
            "importance": "normal",
            "related_entity_type": "session",
            "related_entity_id": "uuid"
        },
        {
            "id": "uuid",
            "event_type": "milestone",
            "event_subtype": "goal_achieved",
            "event_date": "2024-03-10T14:50:00Z",
            "title": "Goal Achieved: Daily Relaxation Practice",
            "description": "Patient has consistently practiced relaxation techniques for 30 days.",
            "metadata": {
                "goal_id": "uuid",
                "goal_description": "Practice relaxation techniques daily for one month",
                "days_to_achieve": 45
            },
            "importance": "milestone"
        },
        {
            "id": "uuid",
            "event_type": "clinical",
            "event_subtype": "assessment_completed",
            "event_date": "2024-03-01T10:00:00Z",
            "title": "GAD-7 Assessment Completed",
            "description": "Score: 8 (Mild anxiety). Improvement from baseline score of 14.",
            "metadata": {
                "assessment_type": "GAD-7",
                "score": 8,
                "severity": "mild",
                "baseline_score": 14,
                "change": -6
            },
            "importance": "high"
        }
    ],
    "next_cursor": "uuid-of-last-event",
    "has_more": true,
    "total_count": 156
}
```

### GET /api/v1/patients/{patient_id}/timeline/summary
Get timeline summary statistics.

Response:
```json
{
    "patient_id": "uuid",
    "first_session": "2023-06-15",
    "last_session": "2024-03-10",
    "total_sessions": 15,
    "total_events": 156,
    "events_by_type": {
        "session": 15,
        "milestone": 8,
        "clinical": 12,
        "goal": 24,
        "administrative": 5
    },
    "milestones_achieved": 8,
    "recent_highlights": [
        {
            "date": "2024-03-10",
            "title": "Goal Achieved: Daily Relaxation Practice",
            "type": "milestone"
        }
    ]
}
```

### POST /api/v1/patients/{patient_id}/timeline
Create manual timeline event.

Request:
```json
{
    "event_type": "milestone",
    "event_subtype": "breakthrough",
    "event_date": "2024-03-10T14:30:00Z",
    "title": "Significant Insight",
    "description": "Patient made connection between childhood experiences and current anxiety patterns.",
    "importance": "high",
    "is_private": true
}
```

### GET /api/v1/patients/{patient_id}/timeline/export
Export timeline as PDF/document.

Query params:
- `format`: pdf | docx | json
- `start_date`: From date
- `end_date`: To date
- `include_private`: Include therapist-only notes

## Event Auto-Generation

Events are automatically created when:

```python
# Session completed
async def on_session_completed(session):
    await create_timeline_event(
        patient_id=session.patient_id,
        event_type="session",
        title=f"Session #{session.number}",
        description=extract_summary(session.notes),
        metadata={
            "session_id": session.id,
            "duration_minutes": session.duration,
            "topics": session.topics
        }
    )

# Goal status changed
async def on_goal_status_changed(goal, old_status, new_status):
    if new_status == "achieved":
        await create_timeline_event(
            patient_id=goal.plan.patient_id,
            event_type="milestone",
            event_subtype="goal_achieved",
            title=f"Goal Achieved: {goal.description[:50]}",
            importance="milestone"
        )

# Treatment plan created
async def on_plan_created(plan):
    await create_timeline_event(
        patient_id=plan.patient_id,
        event_type="administrative",
        event_subtype="plan_created",
        title=f"Treatment Plan Created: {plan.title}",
        importance="high"
    )
```

## Timeline Visualization Data

For frontend chart rendering:

### GET /api/v1/patients/{patient_id}/timeline/chart-data
Response:
```json
{
    "mood_trend": [
        {"date": "2024-01", "avg": 4.5},
        {"date": "2024-02", "avg": 5.2},
        {"date": "2024-03", "avg": 6.1}
    ],
    "session_frequency": [
        {"date": "2024-01", "count": 4},
        {"date": "2024-02", "count": 5},
        {"date": "2024-03", "count": 3}
    ],
    "milestones": [
        {"date": "2024-02-15", "title": "First goal achieved"},
        {"date": "2024-03-10", "title": "Anxiety score improved"}
    ]
}
```

## Implementation Notes

### Performance Optimization
- Use cursor-based pagination (not offset)
- Index on (patient_id, event_date DESC)
- Cache recent events (last 30 days)
- Lazy load event details

### Privacy Considerations
- `is_private` flag for therapist-only events
- Patient view excludes private events
- Export respects privacy settings

## Testing Checklist
- [ ] Timeline returns events in reverse chronological order
- [ ] Cursor pagination works correctly
- [ ] Filtering by event type
- [ ] Date range filtering
- [ ] Search functionality
- [ ] Auto-generation on session completion
- [ ] Auto-generation on goal achievement
- [ ] Private events hidden from patient view
- [ ] Export generates valid PDF/DOCX

## Files to Create/Modify
- `app/routers/timeline.py`
- `app/services/timeline_service.py`
- `app/services/event_generator.py`
- `app/models/timeline.py`
- `app/schemas/timeline.py`
- `alembic/versions/xxx_add_timeline_tables.py`
