# Feature 6: Goal Tracking & Progress Monitoring

## Overview
Comprehensive system for tracking therapeutic goals, measuring progress, and visualizing patient improvement over time with both quantitative metrics and qualitative observations.

## Requirements

### Goal Types
1. **Behavioral Goals** - Observable actions and behaviors
2. **Cognitive Goals** - Thought patterns and beliefs
3. **Emotional Goals** - Emotional regulation and awareness
4. **Functional Goals** - Daily living and functioning
5. **Relational Goals** - Interpersonal relationships

### Progress Tracking Methods
1. **Self-Report Scales** (1-10 ratings)
2. **Frequency Tracking** (occurrences per time period)
3. **Duration Tracking** (time spent on activities)
4. **Binary Completion** (yes/no achievements)
5. **Standardized Assessments** (PHQ-9, GAD-7, etc.)

### Features
- Goal dashboard with progress overview
- Progress entry logging (session and between-session)
- Trend visualization and analysis
- Goal reminders and check-ins
- Patient self-reporting portal
- Progress reports for insurance/documentation

## Database Schema

```sql
-- Goal tracking configuration
CREATE TABLE goal_tracking_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES treatment_goals(id) ON DELETE CASCADE,
    tracking_method VARCHAR(50) NOT NULL, -- 'scale', 'frequency', 'duration', 'binary', 'assessment'
    tracking_frequency VARCHAR(20) DEFAULT 'session', -- 'daily', 'weekly', 'session', 'custom'
    custom_frequency_days INTEGER,
    scale_min INTEGER DEFAULT 1,
    scale_max INTEGER DEFAULT 10,
    scale_labels JSONB, -- {"1": "Never", "5": "Sometimes", "10": "Always"}
    frequency_unit VARCHAR(20), -- 'per_day', 'per_week'
    duration_unit VARCHAR(20), -- 'minutes', 'hours'
    target_direction VARCHAR(10), -- 'increase', 'decrease', 'maintain'
    reminder_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Progress entries
CREATE TABLE progress_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES treatment_goals(id) ON DELETE CASCADE,
    tracking_config_id UUID REFERENCES goal_tracking_config(id),
    entry_date DATE NOT NULL,
    entry_time TIME,
    value DECIMAL(10,2) NOT NULL, -- numeric value
    value_label VARCHAR(100), -- human-readable value
    notes TEXT,
    context VARCHAR(50), -- 'session', 'self_report', 'assessment'
    session_id UUID REFERENCES sessions(id),
    recorded_by UUID REFERENCES users(id),
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Assessment scores
CREATE TABLE assessment_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES users(id) ON DELETE CASCADE,
    goal_id UUID REFERENCES treatment_goals(id),
    assessment_type VARCHAR(50) NOT NULL, -- 'PHQ-9', 'GAD-7', 'BDI-II', etc.
    score INTEGER NOT NULL,
    severity VARCHAR(20),
    subscores JSONB,
    administered_date DATE NOT NULL,
    administered_by UUID REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Progress milestones
CREATE TABLE progress_milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES treatment_goals(id) ON DELETE CASCADE,
    milestone_type VARCHAR(50), -- 'percentage', 'value', 'streak', 'custom'
    title VARCHAR(200) NOT NULL,
    description TEXT,
    target_value DECIMAL(10,2),
    achieved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Goal check-in reminders
CREATE TABLE goal_reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES treatment_goals(id) ON DELETE CASCADE,
    patient_id UUID REFERENCES users(id),
    reminder_type VARCHAR(20), -- 'check_in', 'progress', 'motivation'
    scheduled_time TIME,
    scheduled_days INTEGER[], -- [1,3,5] for Mon, Wed, Fri
    message TEXT,
    is_active BOOLEAN DEFAULT true,
    last_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### Progress Dashboard

#### GET /api/v1/patients/{patient_id}/goals/dashboard
Get goal tracking dashboard overview.

Response:
```json
{
    "patient_id": "uuid",
    "active_goals": 6,
    "tracking_summary": {
        "entries_this_week": 12,
        "streak_days": 7,
        "completion_rate": 0.85
    },
    "goals": [
        {
            "id": "uuid",
            "description": "Reduce anxiety levels",
            "tracking_method": "scale",
            "current_value": 4,
            "baseline_value": 8,
            "target_value": 3,
            "progress_percentage": 80,
            "trend": "improving",
            "trend_data": [
                {"date": "2024-03-04", "value": 5},
                {"date": "2024-03-07", "value": 4.5},
                {"date": "2024-03-10", "value": 4}
            ],
            "last_entry": "2024-03-10",
            "next_check_in": "2024-03-11"
        }
    ],
    "recent_milestones": [
        {
            "date": "2024-03-08",
            "goal": "Reduce anxiety levels",
            "milestone": "50% improvement from baseline"
        }
    ],
    "assessments_due": [
        {
            "type": "GAD-7",
            "last_administered": "2024-02-10",
            "due_date": "2024-03-10"
        }
    ]
}
```

### Progress Entry

#### POST /api/v1/goals/{goal_id}/progress
Record progress entry.

Request (scale tracking):
```json
{
    "entry_date": "2024-03-10",
    "value": 4,
    "notes": "Had a stressful day at work but used breathing exercises",
    "context": "self_report"
}
```

Request (frequency tracking):
```json
{
    "entry_date": "2024-03-10",
    "value": 2,
    "value_label": "2 panic attacks this week",
    "notes": "Down from 5 last week",
    "context": "session"
}
```

#### GET /api/v1/goals/{goal_id}/progress
Get progress history.

Query params:
- `start_date`: From date
- `end_date`: To date
- `aggregation`: none | daily | weekly | monthly

Response:
```json
{
    "goal_id": "uuid",
    "tracking_method": "scale",
    "entries": [
        {
            "date": "2024-03-10",
            "value": 4,
            "notes": "Good progress today",
            "context": "session"
        }
    ],
    "statistics": {
        "baseline": 8,
        "current": 4,
        "target": 3,
        "average": 5.2,
        "min": 3,
        "max": 8,
        "trend_slope": -0.15,
        "trend_direction": "improving"
    }
}
```

### Assessments

#### POST /api/v1/patients/{patient_id}/assessments
Record assessment score.

Request:
```json
{
    "assessment_type": "GAD-7",
    "score": 8,
    "severity": "mild",
    "subscores": {
        "feeling_nervous": 2,
        "cant_stop_worrying": 1,
        "worrying_too_much": 2
    },
    "administered_date": "2024-03-10",
    "goal_id": "uuid",
    "notes": "Patient reported improvement in worry frequency"
}
```

#### GET /api/v1/patients/{patient_id}/assessments
Get assessment history.

Response:
```json
{
    "assessments": {
        "GAD-7": [
            {"date": "2024-01-10", "score": 14, "severity": "moderate"},
            {"date": "2024-02-10", "score": 10, "severity": "moderate"},
            {"date": "2024-03-10", "score": 8, "severity": "mild"}
        ],
        "PHQ-9": [
            {"date": "2024-01-10", "score": 12, "severity": "moderate"},
            {"date": "2024-03-10", "score": 7, "severity": "mild"}
        ]
    }
}
```

### Patient Self-Reporting

#### POST /api/v1/self-report/check-in
Patient submits daily/weekly check-in.

Request:
```json
{
    "check_in_date": "2024-03-10",
    "goals": [
        {"goal_id": "uuid", "value": 4, "notes": "Better day today"},
        {"goal_id": "uuid", "value": 1, "notes": "Completed my homework"}
    ],
    "general_mood": 6,
    "additional_notes": "Feeling more optimistic this week"
}
```

### Progress Reports

#### GET /api/v1/patients/{patient_id}/progress-report
Generate progress report.

Query params:
- `start_date`: Report period start
- `end_date`: Report period end
- `format`: json | pdf

Response:
```json
{
    "report_period": {
        "start": "2024-01-01",
        "end": "2024-03-10"
    },
    "patient_summary": {
        "name": "John Doe",
        "treatment_start": "2024-01-10",
        "sessions_attended": 10,
        "sessions_missed": 1
    },
    "goals_summary": [
        {
            "goal": "Reduce anxiety levels",
            "baseline": 8,
            "current": 4,
            "change": -4,
            "change_percentage": -50,
            "status": "significant_improvement"
        }
    ],
    "assessment_summary": {
        "GAD-7": {
            "baseline": 14,
            "current": 8,
            "change": -6,
            "interpretation": "Moved from moderate to mild anxiety"
        }
    },
    "clinical_observations": "Patient has shown consistent engagement...",
    "recommendations": "Continue current treatment approach..."
}
```

## Tracking Method Configurations

### Scale Tracking
```json
{
    "tracking_method": "scale",
    "scale_min": 1,
    "scale_max": 10,
    "scale_labels": {
        "1": "None/Absent",
        "3": "Mild",
        "5": "Moderate",
        "7": "Significant",
        "10": "Severe/Constant"
    },
    "target_direction": "decrease"
}
```

### Frequency Tracking
```json
{
    "tracking_method": "frequency",
    "frequency_unit": "per_week",
    "target_direction": "decrease"
}
```

### Duration Tracking
```json
{
    "tracking_method": "duration",
    "duration_unit": "minutes",
    "target_direction": "increase"
}
```

## Standard Assessments

| Assessment | Purpose | Scoring | Frequency |
|------------|---------|---------|-----------|
| PHQ-9 | Depression | 0-27 | Every 4 weeks |
| GAD-7 | Anxiety | 0-21 | Every 4 weeks |
| BDI-II | Depression | 0-63 | Monthly |
| BAI | Anxiety | 0-63 | Monthly |
| PCL-5 | PTSD | 0-80 | As needed |
| AUDIT | Alcohol Use | 0-40 | Intake/Quarterly |

## Implementation Notes

### Trend Calculation
```python
def calculate_trend(entries, days=30):
    """Calculate trend using linear regression."""
    recent = [e for e in entries if e.date >= today - timedelta(days=days)]
    if len(recent) < 3:
        return {"direction": "insufficient_data", "slope": None}

    # Linear regression
    x = [(e.date - recent[0].date).days for e in recent]
    y = [e.value for e in recent]
    slope = calculate_slope(x, y)

    if abs(slope) < 0.05:
        direction = "stable"
    elif slope < 0:
        direction = "improving" if config.target_direction == "decrease" else "declining"
    else:
        direction = "declining" if config.target_direction == "decrease" else "improving"

    return {"direction": direction, "slope": slope}
```

### Milestone Detection
```python
async def check_milestones(goal, new_entry):
    """Check if entry triggers any milestones."""
    milestones_achieved = []

    # Percentage improvement milestone
    baseline = goal.baseline_value
    current = new_entry.value
    improvement = (baseline - current) / baseline

    thresholds = [0.25, 0.50, 0.75]
    for threshold in thresholds:
        if improvement >= threshold:
            milestone = await get_or_create_milestone(goal, threshold)
            if not milestone.achieved_at:
                milestone.achieved_at = datetime.now()
                milestones_achieved.append(milestone)

    return milestones_achieved
```

## Testing Checklist
- [ ] Create goal with tracking configuration
- [ ] Record progress entries (all types)
- [ ] Calculate trend correctly
- [ ] Detect milestones on achievement
- [ ] Generate progress dashboard
- [ ] Assessment scoring and severity
- [ ] Patient self-reporting flow
- [ ] Progress report generation
- [ ] Date range filtering
- [ ] Aggregation (daily/weekly/monthly)

## Files to Create/Modify
- `app/routers/goal_tracking.py`
- `app/routers/assessments.py`
- `app/routers/self_report.py`
- `app/services/tracking_service.py`
- `app/services/assessment_service.py`
- `app/services/trend_calculator.py`
- `app/services/milestone_detector.py`
- `app/services/report_generator.py`
- `app/models/tracking.py`
- `app/schemas/tracking.py`
- `alembic/versions/xxx_add_tracking_tables.py`
