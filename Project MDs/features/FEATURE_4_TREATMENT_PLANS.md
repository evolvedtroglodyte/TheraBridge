# Feature 4: Treatment Plans

## Overview
Enable therapists to create, manage, and track structured treatment plans for patients, including goals, interventions, and progress monitoring.

## Requirements

### Core Features
1. **Treatment Plan Creation**
   - Diagnosis-linked plans
   - Measurable goals with timelines
   - Intervention strategies
   - Progress indicators

2. **Goal Management**
   - SMART goal framework (Specific, Measurable, Achievable, Relevant, Time-bound)
   - Goal hierarchies (long-term → short-term → objectives)
   - Progress tracking with milestones
   - Goal status updates

3. **Intervention Tracking**
   - Link interventions to goals
   - Evidence-based intervention library
   - Effectiveness ratings
   - Session-intervention mapping

4. **Review & Updates**
   - Periodic review reminders
   - Plan versioning
   - Progress reports generation

## Database Schema

```sql
-- Treatment plans
CREATE TABLE treatment_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID REFERENCES users(id) ON DELETE CASCADE,
    therapist_id UUID REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    diagnosis_codes JSONB, -- ICD-10 codes
    presenting_problems TEXT[],
    start_date DATE NOT NULL,
    target_end_date DATE,
    actual_end_date DATE,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'completed', 'discontinued', 'on_hold'
    review_frequency_days INTEGER DEFAULT 90,
    next_review_date DATE,
    version INTEGER DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Treatment goals
CREATE TABLE treatment_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES treatment_plans(id) ON DELETE CASCADE,
    parent_goal_id UUID REFERENCES treatment_goals(id), -- for goal hierarchy
    goal_type VARCHAR(20) NOT NULL, -- 'long_term', 'short_term', 'objective'
    description TEXT NOT NULL,
    measurable_criteria TEXT,
    baseline_value VARCHAR(100),
    target_value VARCHAR(100),
    current_value VARCHAR(100),
    target_date DATE,
    status VARCHAR(20) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'achieved', 'modified', 'discontinued'
    progress_percentage INTEGER DEFAULT 0,
    priority INTEGER DEFAULT 1, -- 1=highest
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Interventions
CREATE TABLE interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    modality VARCHAR(50), -- 'CBT', 'DBT', 'psychodynamic', etc.
    evidence_level VARCHAR(20), -- 'strong', 'moderate', 'emerging'
    is_system BOOLEAN DEFAULT false,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Goal-Intervention mapping
CREATE TABLE goal_interventions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES treatment_goals(id) ON DELETE CASCADE,
    intervention_id UUID REFERENCES interventions(id),
    frequency VARCHAR(50), -- 'every session', 'weekly', 'as needed'
    notes TEXT,
    effectiveness_rating INTEGER CHECK (effectiveness_rating BETWEEN 1 AND 5),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Goal progress entries
CREATE TABLE goal_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID REFERENCES treatment_goals(id) ON DELETE CASCADE,
    session_id UUID REFERENCES sessions(id),
    progress_note TEXT NOT NULL,
    progress_value VARCHAR(100),
    rating INTEGER CHECK (rating BETWEEN 1 AND 10),
    recorded_by UUID REFERENCES users(id),
    recorded_at TIMESTAMP DEFAULT NOW()
);

-- Treatment plan reviews
CREATE TABLE plan_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID REFERENCES treatment_plans(id) ON DELETE CASCADE,
    review_date DATE NOT NULL,
    reviewer_id UUID REFERENCES users(id),
    summary TEXT NOT NULL,
    goals_reviewed INTEGER,
    goals_on_track INTEGER,
    modifications_made TEXT,
    next_review_date DATE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## API Endpoints

### Treatment Plans

#### POST /api/v1/patients/{patient_id}/treatment-plans
Create treatment plan.

Request:
```json
{
    "title": "Anxiety Management Plan",
    "diagnosis_codes": [{"code": "F41.1", "description": "Generalized anxiety disorder"}],
    "presenting_problems": ["chronic worry", "sleep difficulties", "physical tension"],
    "start_date": "2024-03-01",
    "target_end_date": "2024-09-01",
    "review_frequency_days": 90
}
```

#### GET /api/v1/patients/{patient_id}/treatment-plans
List patient's treatment plans.

#### GET /api/v1/treatment-plans/{plan_id}
Get full treatment plan with goals.

Response:
```json
{
    "id": "uuid",
    "title": "Anxiety Management Plan",
    "status": "active",
    "progress_summary": {
        "total_goals": 8,
        "achieved": 2,
        "in_progress": 4,
        "not_started": 2,
        "overall_progress": 45
    },
    "goals": [
        {
            "id": "uuid",
            "goal_type": "long_term",
            "description": "Reduce overall anxiety levels to manageable state",
            "status": "in_progress",
            "progress_percentage": 40,
            "sub_goals": [...]
        }
    ],
    "next_review_date": "2024-06-01"
}
```

#### PUT /api/v1/treatment-plans/{plan_id}
Update treatment plan.

#### POST /api/v1/treatment-plans/{plan_id}/review
Record plan review.

### Goals

#### POST /api/v1/treatment-plans/{plan_id}/goals
Add goal to plan.

Request:
```json
{
    "goal_type": "short_term",
    "parent_goal_id": "uuid-of-long-term-goal",
    "description": "Learn and practice 3 relaxation techniques",
    "measurable_criteria": "Patient can demonstrate techniques independently",
    "baseline_value": "No techniques known",
    "target_value": "3 techniques mastered",
    "target_date": "2024-04-15",
    "interventions": [
        {"intervention_id": "uuid", "frequency": "every session"}
    ]
}
```

#### PUT /api/v1/goals/{goal_id}
Update goal.

#### POST /api/v1/goals/{goal_id}/progress
Record progress entry.

Request:
```json
{
    "session_id": "uuid",
    "progress_note": "Patient successfully practiced deep breathing. Reported using it twice this week.",
    "progress_value": "1 technique learned",
    "rating": 7
}
```

#### GET /api/v1/goals/{goal_id}/history
Get goal progress history.

### Interventions

#### GET /api/v1/interventions
List available interventions.

Query params:
- `modality`: Filter by therapy modality
- `search`: Search by name/description

#### POST /api/v1/interventions
Create custom intervention.

## SMART Goal Template

```json
{
    "template": {
        "specific": {
            "what": "What exactly will be accomplished?",
            "who": "Who is involved?",
            "where": "Where will it happen?"
        },
        "measurable": {
            "indicator": "How will progress be measured?",
            "target": "What is the target value?"
        },
        "achievable": {
            "resources": "What resources are needed?",
            "barriers": "What barriers might exist?"
        },
        "relevant": {
            "alignment": "How does this align with treatment goals?",
            "importance": "Why is this goal important?"
        },
        "time_bound": {
            "deadline": "Target completion date",
            "milestones": "Key milestone dates"
        }
    }
}
```

## Built-in Interventions Library

Categories:
- **CBT Interventions**: Cognitive restructuring, Behavioral activation, Exposure therapy
- **DBT Skills**: Mindfulness, Distress tolerance, Emotion regulation, Interpersonal effectiveness
- **Relaxation**: Progressive muscle relaxation, Deep breathing, Guided imagery
- **Behavioral**: Activity scheduling, Sleep hygiene, Assertiveness training

## Implementation Notes

### Progress Calculation
```python
def calculate_goal_progress(goal):
    """Calculate goal progress based on sub-goals and entries."""
    if goal.sub_goals:
        # Weighted average of sub-goals
        return sum(g.progress_percentage * g.priority for g in goal.sub_goals) / sum(g.priority for g in goal.sub_goals)
    elif goal.progress_entries:
        # Latest progress entry rating
        latest = goal.progress_entries[-1]
        return (latest.rating / 10) * 100
    return goal.progress_percentage
```

### Review Reminders
- Check `next_review_date` daily
- Send reminder 7 days before
- Send urgent reminder on due date
- Auto-update to overdue status

## Testing Checklist
- [ ] Create treatment plan with goals
- [ ] Goal hierarchy (long-term → short-term → objectives)
- [ ] Add interventions to goals
- [ ] Record progress entries
- [ ] Progress percentage calculation
- [ ] Plan review workflow
- [ ] Status transitions
- [ ] Authorization (only assigned therapist)

## Files to Create/Modify
- `app/routers/treatment_plans.py`
- `app/routers/goals.py`
- `app/routers/interventions.py`
- `app/services/treatment_plan_service.py`
- `app/services/goal_service.py`
- `app/models/treatment_plans.py`
- `app/schemas/treatment_plans.py`
- `alembic/versions/xxx_add_treatment_plan_tables.py`
- `app/data/interventions_library.json`
