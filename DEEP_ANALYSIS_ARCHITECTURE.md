# Deep Clinical Analysis System - Architecture & Workflow

## 🎯 Overview

A comprehensive AI-powered deep analysis system that extracts clinically meaningful insights from therapy sessions for **patient-facing display**. This system builds on existing mood/topic extraction to provide therapeutic progress indicators.

---

## 📊 Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SESSION UPLOAD PIPELINE                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────┐
                        │  Audio File Upload   │
                        │  (via UploadModal)   │
                        └──────────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────┐
                        │   Transcription      │
                        │  (Whisper + Diarize) │
                        └──────────────────────┘
                                    │
                                    ▼
                        ┌──────────────────────┐
                        │  Store transcript in │
                        │  therapy_sessions    │
                        │  processing_status:  │
                        │     "completed"      │
                        └──────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
        ┌─────────────────────┐         ┌─────────────────────┐
        │  AUTOMATIC ANALYSIS │         │  MANUAL TRIGGER     │
        │  (Background Task)  │         │  (Force Re-analyze) │
        └─────────────────────┘         └─────────────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ANALYSIS ORCHESTRATOR                                  │
│                                                                              │
│  Task: Coordinate AI analysis pipeline with proper dependencies             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
    ┌──────────────┐        ┌──────────────┐      ┌──────────────┐
    │  WAVE 1      │        │  WAVE 1      │      │  WAVE 1      │
    │              │        │              │      │              │
    │ Mood         │        │ Topic        │      │ Breakthrough │
    │ Analysis     │        │ Extraction   │      │ Detection    │
    │              │        │              │      │              │
    │ (GPT-4o-mini)│        │ (GPT-4o-mini)│      │ (Existing)   │
    └──────────────┘        └──────────────┘      └──────────────┘
            │                       │                       │
            │   ✅ mood_score       │   ✅ topics[]        │   ✅ has_breakthrough
            │   ✅ emotional_tone   │   ✅ action_items[]  │   ✅ primary_breakthrough
            │   ✅ mood_indicators  │   ✅ technique       │
            │                       │   ✅ summary         │
            │                       │                      │
            └───────────────────────┼──────────────────────┘
                                    │
                        ⏰ WAIT FOR ALL WAVE 1 TO COMPLETE
                                    │
                                    ▼
            ┌──────────────────────────────────────────────┐
            │         CHECK DEPENDENCY FLAGS               │
            │                                              │
            │  ✅ mood_analyzed_at IS NOT NULL            │
            │  ✅ topics_extracted_at IS NOT NULL         │
            │  ✅ breakthrough_analyzed_at IS NOT NULL    │
            └──────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           WAVE 2: DEEP ANALYSIS                              │
│                                                                              │
│  Task: Synthesize all Wave 1 data + patient history into deep insights      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │  Deep Analysis Service       │
                    │  (GPT-4o for complexity)     │
                    │                              │
                    │  INPUT CONTEXT:              │
                    │  ├─ Full transcript          │
                    │  ├─ Mood score + indicators  │
                    │  ├─ Topics + action items    │
                    │  ├─ Technique used           │
                    │  ├─ Breakthrough data        │
                    │  ├─ Patient history:         │
                    │  │  ├─ Previous 5 sessions   │
                    │  │  ├─ Mood trend (3-session)│
                    │  │  ├─ Recurring topics      │
                    │  │  └─ Technique frequency   │
                    │  └─ Speaker roles (T/C)      │
                    │                              │
                    │  OUTPUT:                     │
                    │  ├─ Clinical insights        │
                    │  ├─ Progress indicators      │
                    │  ├─ Coping skill development │
                    │  ├─ Therapeutic alliance     │
                    │  ├─ Patient engagement       │
                    │  └─ Recommendations          │
                    └──────────────────────────────┘
                                    │
                                    ▼
                    ┌──────────────────────────────┐
                    │  Store in Database           │
                    │                              │
                    │  therapy_sessions:           │
                    │  ├─ deep_analysis (JSONB)    │
                    │  ├─ analysis_confidence      │
                    │  └─ deep_analyzed_at         │
                    │                              │
                    │  analysis_processing_log:    │
                    │  └─ Track each wave          │
                    └──────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND DISPLAY                                    │
│                                                                              │
│  Component: SessionDetail.tsx (new "Deep Analysis" section)                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
            ┌───────────────────────────────────────┐
            │  Display Cards (Patient-Friendly):    │
            │                                       │
            │  📊 Progress Indicators               │
            │  ├─ Symptom reduction                 │
            │  ├─ Skill development                 │
            │  └─ Goal progress                     │
            │                                       │
            │  🧠 Therapeutic Insights               │
            │  ├─ Key realizations                  │
            │  ├─ Growth areas                      │
            │  └─ Strengths demonstrated            │
            │                                       │
            │  🛠️ Coping Skills                     │
            │  ├─ Skills learned                    │
            │  ├─ Confidence level                  │
            │  └─ Practice recommendations          │
            │                                       │
            │  🤝 Therapeutic Relationship           │
            │  ├─ Engagement level                  │
            │  ├─ Openness/vulnerability            │
            │  └─ Alliance strength                 │
            │                                       │
            │  📝 Actionable Next Steps             │
            │  └─ Patient-friendly recommendations  │
            └───────────────────────────────────────┘
```

---

## 🔄 Dependency & Race Condition Handling

### Problem Statement
Deep Analysis requires outputs from 3 parallel Wave 1 services:
1. Mood Analysis
2. Topic Extraction
3. Breakthrough Detection

**Race condition risks:**
- Deep Analysis triggers before Wave 1 completes
- Partial data leads to incomplete insights
- Database consistency issues

### Solution: Orchestration Layer

```python
# app/services/analysis_orchestrator.py

class AnalysisOrchestrator:
    """
    Manages multi-wave analysis pipeline with dependency resolution
    """

    async def process_session(self, session_id: str):
        # WAVE 1: Parallel independent analyses
        await asyncio.gather(
            self.run_mood_analysis(session_id),
            self.run_topic_extraction(session_id),
            self.run_breakthrough_detection(session_id)
        )

        # WAIT: Verify all Wave 1 completed
        if not self.wave1_complete(session_id):
            raise AnalysisIncompleteError("Wave 1 not complete")

        # WAVE 2: Deep analysis (depends on Wave 1)
        await self.run_deep_analysis(session_id)
```

### Database Flags

```sql
-- New columns in therapy_sessions
ALTER TABLE therapy_sessions
ADD COLUMN analysis_status VARCHAR(50) DEFAULT 'pending',
  -- Values: 'pending', 'wave1_running', 'wave1_complete', 'wave2_running', 'complete', 'failed'
ADD COLUMN wave1_completed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN deep_analyzed_at TIMESTAMP WITH TIME ZONE;

-- Processing log table
CREATE TABLE analysis_processing_log (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID NOT NULL REFERENCES therapy_sessions(id) ON DELETE CASCADE,
  wave VARCHAR(20) NOT NULL,  -- 'mood', 'topics', 'breakthrough', 'deep'
  status VARCHAR(20) NOT NULL,  -- 'started', 'completed', 'failed'
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE,
  error_message TEXT,
  retry_count INTEGER DEFAULT 0
);
```

### Status Flow

```
pending → wave1_running → wave1_complete → wave2_running → complete
                    ↓
                 failed (with retry logic)
```

---

## 🧬 Deep Analysis AI Prompt Structure

### Context Assembly

```python
def build_deep_analysis_context(session_id: str) -> dict:
    """
    Assemble all necessary context for deep analysis
    """
    session = get_session(session_id)
    patient_id = session["patient_id"]

    return {
        # Current session data
        "current_session": {
            "transcript": session["transcript"],
            "mood_score": session["mood_score"],
            "mood_indicators": session["mood_indicators"],
            "emotional_tone": session["emotional_tone"],
            "topics": session["topics"],
            "action_items": session["action_items"],
            "technique": session["technique"],
            "summary": session["summary"],
            "breakthrough": session["breakthrough_data"],
        },

        # Historical context
        "patient_history": {
            "previous_sessions": get_recent_sessions(patient_id, limit=5),
            "mood_trend": get_mood_trend(patient_id, days=90),
            "recurring_topics": get_topic_frequency(patient_id),
            "technique_history": get_technique_history(patient_id),
            "breakthrough_history": get_breakthroughs(patient_id),
        },

        # Speaker roles
        "speaker_roles": detect_speaker_roles(session["transcript"]),
    }
```

### System Prompt (Patient-Facing)

```
You are an expert clinical psychologist analyzing therapy sessions to provide
patient-facing insights. Your goal is to help the patient understand their
progress, strengths, and areas for growth in a compassionate, empowering way.

You have access to:
1. Full session transcript with speaker roles (Therapist/Client)
2. AI-extracted mood score, topics, action items, and technique
3. Breakthrough moments detected during the session
4. Patient's therapy history (previous sessions, mood trends, recurring themes)

Your task is to generate a deep clinical analysis with the following dimensions:

**1. Progress Indicators** (clinical but accessible):
   - Symptom reduction or improvement
   - Skill development (DBT, CBT, mindfulness, etc.)
   - Goal progress (if goals mentioned in history)
   - Behavioral changes (sleep, relationships, work/school)

**2. Therapeutic Insights** (patient empowerment):
   - Key realizations or "aha moments" from this session
   - Connections to previous sessions (patterns emerging)
   - Growth areas (framed positively)
   - Strengths demonstrated (resilience, openness, effort)

**3. Coping Skill Development**:
   - Skills learned or practiced (TIPP, grounding, opposite action, etc.)
   - Confidence level in using skills (beginner/developing/proficient)
   - Practice recommendations (specific, actionable, encouraging)

**4. Therapeutic Relationship Quality**:
   - Engagement level (active participation, asking questions, etc.)
   - Openness/vulnerability (sharing difficult emotions, trust)
   - Alliance strength (working together, collaborative goal-setting)

**5. Recommendations** (patient-friendly, actionable):
   - Specific practices to try before next session
   - Resources to explore (apps, books, videos - if applicable)
   - Reflection prompts for journaling

**Guidelines**:
- Use accessible language (not overly clinical jargon)
- Frame everything with compassion and hope
- Acknowledge both struggles and strengths
- Be specific with evidence from transcript
- Avoid making the patient feel judged or inadequate
- Celebrate small wins and efforts, not just outcomes

**Output Format**: JSON with structured fields for each dimension.
```

---

## 📦 Database Schema

### New Columns in `therapy_sessions`

```sql
-- Deep analysis results
ALTER TABLE therapy_sessions
ADD COLUMN deep_analysis JSONB,
ADD COLUMN analysis_confidence DECIMAL(3,2) CHECK (analysis_confidence >= 0 AND analysis_confidence <= 1),
ADD COLUMN deep_analyzed_at TIMESTAMP WITH TIME ZONE,

-- Analysis orchestration status
ADD COLUMN analysis_status VARCHAR(50) DEFAULT 'pending',
ADD COLUMN wave1_completed_at TIMESTAMP WITH TIME ZONE;

-- Indexes
CREATE INDEX idx_therapy_sessions_analysis_status
ON therapy_sessions(analysis_status);

CREATE INDEX idx_therapy_sessions_deep_analyzed
ON therapy_sessions(deep_analyzed_at)
WHERE deep_analyzed_at IS NOT NULL;
```

### Deep Analysis JSONB Structure

```json
{
  "progress_indicators": {
    "symptom_reduction": {
      "detected": true,
      "description": "Patient reports sleeping 7 hours (up from 4 hours in previous sessions)",
      "confidence": 0.9
    },
    "skill_development": [
      {
        "skill": "TIPP (Temperature, Intense exercise, Paced breathing, Progressive relaxation)",
        "proficiency": "developing",
        "evidence": "Patient successfully used cold water technique when feeling overwhelmed"
      }
    ],
    "goal_progress": [
      {
        "goal": "Improve sleep hygiene",
        "status": "on_track",
        "evidence": "Patient implemented wind-down routine discussed in Session 8"
      }
    ]
  },

  "therapeutic_insights": {
    "key_realizations": [
      "Patient connected childhood invalidation to current fear of expressing needs in relationships"
    ],
    "patterns": [
      "Recurring theme of relationship anxiety across last 4 sessions - showing deeper engagement with core issue"
    ],
    "growth_areas": [
      "Building confidence in setting boundaries"
    ],
    "strengths": [
      "Demonstrated remarkable self-awareness when discussing difficult childhood memories",
      "Took initiative to practice skills between sessions"
    ]
  },

  "coping_skills": {
    "learned": ["TIPP skills", "Opposite Action"],
    "proficiency": {
      "TIPP": "developing",
      "Opposite_Action": "beginner"
    },
    "practice_recommendations": [
      "Practice cold water technique 2-3 times this week, even when not in crisis (builds muscle memory)",
      "Journal about one instance where you used Opposite Action"
    ]
  },

  "therapeutic_relationship": {
    "engagement_level": "high",
    "engagement_evidence": "Asked clarifying questions, brought up topic from last session unprompted",
    "openness": "very_open",
    "openness_evidence": "Shared vulnerable childhood memory, cried during session but stayed engaged",
    "alliance_strength": "strong",
    "alliance_evidence": "Collaborative goal-setting, patient expressed feeling understood"
  },

  "recommendations": {
    "practices": [
      "Try TIPP skills 2-3x this week (even when calm)",
      "Practice setting one small boundary in a low-stakes situation"
    ],
    "resources": [
      "DBT Skills Training Handouts (provided by therapist)"
    ],
    "reflection_prompts": [
      "What does it feel like in your body when you successfully set a boundary?",
      "Write about a time you advocated for yourself - what made that possible?"
    ]
  },

  "confidence_score": 0.88,
  "analyzed_at": "2024-12-22T10:30:00Z"
}
```

---

## 🎨 Frontend Integration

### New Section in SessionDetail.tsx

```tsx
{/* Deep Clinical Analysis Section */}
{session.deep_analysis && (
  <div className="mb-6 p-6 bg-gradient-to-br from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl border border-purple-200 dark:border-purple-800">
    <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-4 flex items-center gap-2">
      <Brain className="w-6 h-6 text-purple-600" />
      Deep Clinical Analysis
    </h3>

    {/* Progress Indicators */}
    <DeepAnalysisSection
      title="📊 Your Progress"
      data={session.deep_analysis.progress_indicators}
    />

    {/* Therapeutic Insights */}
    <DeepAnalysisSection
      title="🧠 Key Insights"
      data={session.deep_analysis.therapeutic_insights}
    />

    {/* Coping Skills */}
    <DeepAnalysisSection
      title="🛠️ Skills You're Building"
      data={session.deep_analysis.coping_skills}
    />

    {/* Recommendations */}
    <DeepAnalysisSection
      title="📝 Between Sessions"
      data={session.deep_analysis.recommendations}
    />
  </div>
)}
```

---

## 🚦 Error Handling & Retry Logic

### Retry Strategy

```python
class AnalysisRetryPolicy:
    MAX_RETRIES = 3
    BACKOFF_MULTIPLIER = 2  # Exponential backoff

    async def run_with_retry(self, func, session_id: str, wave: str):
        for attempt in range(self.MAX_RETRIES):
            try:
                result = await func(session_id)
                self.log_success(session_id, wave)
                return result
            except Exception as e:
                self.log_failure(session_id, wave, str(e), attempt + 1)
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.BACKOFF_MULTIPLIER ** attempt)
                else:
                    raise
```

### Graceful Degradation

If deep analysis fails:
1. Session still displays Wave 1 data (mood, topics, breakthrough)
2. Frontend shows "Analysis pending" message
3. Manual retry button available
4. Error logged for debugging

---

## 📈 Cost Estimation

**Per Session:**
- Mood Analysis: ~$0.01 (GPT-4o-mini, ~2K tokens)
- Topic Extraction: ~$0.01 (GPT-4o-mini, ~2K tokens)
- Breakthrough Detection: ~$0.02 (existing)
- **Deep Analysis: ~$0.05** (GPT-4o, ~5K input + 2K output tokens)

**Total per session: ~$0.09**

For 1000 sessions/month: **~$90/month**

---

## 🧪 Testing Strategy

1. **Unit Tests**:
   - Each AI service in isolation
   - JSONB schema validation
   - Retry logic

2. **Integration Tests**:
   - Full Wave 1 → Wave 2 pipeline
   - Race condition scenarios
   - Database flag transitions

3. **E2E Tests**:
   - Upload audio → see deep analysis in UI
   - Manual retry flow
   - Error states

4. **Load Tests**:
   - 100 concurrent sessions
   - Verify no race conditions at scale

---

## 🎯 Implementation Phases

### Phase 1: Backend Foundation ✅ READY TO START
- [ ] Create `analysis_orchestrator.py`
- [ ] Create `deep_analyzer.py` (AI service)
- [ ] Add database schema (migrations)
- [ ] Add `/api/sessions/{id}/analyze-deep` endpoint
- [ ] Implement retry logic

### Phase 2: Pipeline Integration
- [ ] Hook orchestrator into transcript upload flow
- [ ] Add background task for automatic deep analysis
- [ ] Create processing log table
- [ ] Implement status tracking

### Phase 3: Frontend Display
- [ ] Create `DeepAnalysisSection` component
- [ ] Add to `SessionDetail.tsx`
- [ ] Create loading/error states
- [ ] Add manual retry button

### Phase 4: Testing & Refinement
- [ ] Test on all 12 mock sessions
- [ ] Validate JSONB output quality
- [ ] Tune AI prompts based on results
- [ ] Performance optimization

---

## ❓ Key Questions Answered

1. **What analysis to extract?**
   → Progress indicators, insights, coping skills, relationship quality, recommendations

2. **Which AI model?**
   → GPT-4o (more complex reasoning needed for synthesis)

3. **When to run?**
   → Automatically after Wave 1 completes (orchestrated)

4. **UI placement?**
   → New section in `SessionDetail.tsx` (right column)

5. **Database storage?**
   → JSONB in `therapy_sessions.deep_analysis`

6. **Dependency management?**
   → Orchestrator with status flags + processing log

---

## 🚀 Ready to Implement?

This architecture ensures:
- ✅ No race conditions (wave-based dependencies)
- ✅ Intelligent AI synthesis (uses all available data)
- ✅ Patient-friendly output (empowering, not clinical jargon)
- ✅ Robust error handling (retry + graceful degradation)
- ✅ Cost-effective (~$0.09/session)
- ✅ Scalable (async + background tasks)

**Next step:** Implement Phase 1 (Backend Foundation)
