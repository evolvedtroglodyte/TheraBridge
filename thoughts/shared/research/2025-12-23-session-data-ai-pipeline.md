---
date: 2025-12-23 21:27:41 CST
researcher: NewdlDewdl
git_commit: e39380128dde38556d480bc1938fa7bd410790d9
branch: main
repository: peerbridge proj
topic: "Session Data Pipeline: Audio Upload to UI Display via AI Generation"
tags: [research, codebase, ai-extraction, session-pipeline, topic-extraction, mood-analysis]
status: complete
last_updated: 2025-12-23
last_updated_by: NewdlDewdl
---

# Research: Session Data Pipeline - Audio Upload to UI Display via AI Generation

**Date**: 2025-12-23 21:27:41 CST
**Researcher**: NewdlDewdl
**Git Commit**: e39380128dde38556d480bc1938fa7bd410790d9
**Branch**: main
**Repository**: peerbridge proj

## Research Question

Examine the current pipeline for loading session fields into the UI via AI generation, specifically:

**Core Session Fields:**
- `id`: string - Unique session identifier
- `date`: string - Display date (e.g., "Dec 17")
- `duration`: string - Session length (e.g., "50m", "45m")
- `therapist`: string - Therapist name (e.g., "Dr. Sarah Chen")
- `mood`: MoodType - Patient mood ('positive' | 'neutral' | 'low')
- `topics`: string[] - Array of session topics (e.g., ['Boundaries', 'Family dynamics'])
- `strategy`: string - Primary therapeutic technique used (e.g., "Assertiveness training")
- `actions`: string[] - Action items assigned (e.g., ['Set clear boundaries', 'Practice saying no'])

## Summary

TherapyBridge implements a complete **audio-to-UI pipeline** that processes therapy session audio files through AI analysis and displays structured session data in the frontend dashboard. The system uses a **multi-wave analysis architecture**:

**Wave 1 (Immediate AI Extraction):**
1. Audio/transcript uploaded via REST API endpoints
2. GPT-4o-mini AI services extract:
   - **Mood Analysis**: mood_score (0-10), confidence, rationale, key_indicators
   - **Topic Extraction**: 1-2 topics, 2 action_items, primary technique, 2-sentence summary
   - **Breakthrough Detection**: Identifies therapeutic breakthroughs with confidence scores
3. Results stored in Supabase PostgreSQL database (therapy_sessions table)

**Wave 2 (Deep Analysis - Optional):**
4. Deep clinical analysis and prose generation for comprehensive insights

**Frontend Display:**
5. React hooks fetch session data from backend API
6. SessionDataContext distributes data globally via React Context
7. Specialized components render session cards with mood indicators, topics, action items, strategies

**Key characteristics:**
- **No hardcoded outputs**: AI naturally concludes from transcripts
- **Caching**: Analysis results cached to prevent duplicate API calls
- **Speaker role detection**: Multi-heuristic approach (first-speaker + speaking-ratio)
- **Real-time polling**: Frontend polls processing_status until completion
- **Cost-effective**: ~$0.01 per session using GPT-4o-mini

## Detailed Findings

### 1. Backend API Endpoints (FastAPI)

#### Session Upload Endpoints

**Audio File Upload** - `POST /api/sessions/{session_id}/upload-audio`
Location: `backend/app/routers/sessions.py:293-359`

- Accepts audio files (mp3, wav, m4a, mp4)
- Uploads to Supabase Storage bucket `audio-sessions`
- Stores public URL in `therapy_sessions.audio_file_url`
- Sets `processing_status = "processing"`
- Returns immediately (no async processing triggered)

**Transcript Upload** - `POST /api/sessions/{session_id}/upload-transcript`
Location: `backend/app/routers/sessions.py:222-290`

- Accepts pre-transcribed segments (already diarized with speakers)
- Stores directly to `therapy_sessions.transcript` as JSONB
- Optionally triggers background breakthrough detection
- Format: `[{start, end, speaker, text}, ...]`
- Speaker IDs: `SPEAKER_00`, `SPEAKER_01` or `Therapist`, `Client`

**Demo Transcript Upload** - `POST /api/sessions/upload-demo-transcript`
Location: `backend/app/routers/sessions.py:1301-1406`

- Loads mock transcripts from `mock-therapy-data/sessions/`
- Creates session with full AI analysis pipeline
- Used for demo mode and testing

#### AI Analysis Endpoints

**Mood Analysis** - `POST /api/sessions/{session_id}/analyze-mood`
Location: `backend/app/routers/sessions.py:675-770`

- Analyzes patient mood from transcript using `MoodAnalyzer` service
- Filters to patient dialogue only (by `patient_speaker_id`, default `SPEAKER_01`)
- Returns:
  - `mood_score`: Float 0.0-10.0 (0.5 increments)
  - `confidence`: Float 0.0-1.0
  - `rationale`: Text explanation
  - `key_indicators`: Array of emotional signals
  - `emotional_tone`: Overall emotional quality
- Stores in database: `mood_score`, `mood_confidence`, `mood_rationale`, `mood_indicators`, `emotional_tone`, `mood_analyzed_at`
- Cached: Returns existing results unless `force=true`

**Topic Extraction** - `POST /api/sessions/{session_id}/extract-topics`
Location: `backend/app/routers/sessions.py:867-960`

- Extracts topics, action items, technique, summary using `TopicExtractor` service
- Analyzes full conversation (both therapist and patient)
- Returns:
  - `topics`: 1-2 main topics
  - `action_items`: 2 action items
  - `technique`: Primary therapeutic technique (validated against technique library)
  - `summary`: Ultra-brief summary (max 150 characters)
  - `confidence`: Float 0.0-1.0
- Stores in database: `topics`, `action_items`, `technique`, `summary`, `extraction_confidence`, `raw_meta_summary`, `topics_extracted_at`
- Cached: Returns existing results unless `force=true`

**Mood History** - `GET /api/sessions/patient/{patient_id}/mood-history`
Location: `backend/app/routers/sessions.py` (referenced in documentation)

- Returns historical mood data for trend analysis
- Used for visualizing mood trajectory over time

#### Session Retrieval Endpoints

**Get Session by ID** - `GET /api/sessions/{session_id}`
Location: `backend/app/routers/sessions.py:127-143`

- Returns complete session object with all AI-extracted fields
- Includes breakthrough data and history
- Returns all fields from database: mood, topics, action_items, technique, summary, deep_analysis

**Get Patient Sessions** - `GET /api/sessions/patient/{patient_id}`
Location: `backend/app/routers/sessions.py:146-188`

- Returns all sessions for a patient (default limit 50)
- Ordered by date (newest first)
- Optional: Include breakthrough history (`include_breakthroughs=true`)
- Returns complete session objects with all analysis data

### 2. AI Extraction Services

#### MoodAnalyzer Service

Location: `backend/app/services/mood_analyzer.py`

**Purpose**: AI-powered mood analysis from therapy session transcripts

**Implementation**:
```python
class MoodAnalyzer:
    def __init__(self, api_key, override_model):
        self.model = get_model_name("mood_analysis", override_model)  # GPT-4o-mini

    def analyze_session_mood(session_id, segments, patient_speaker_id):
        # Filter to patient dialogue only
        patient_segments = [seg for seg in segments if seg["speaker"] == patient_speaker_id]

        # Create analysis prompt
        prompt = self._create_analysis_prompt(patient_segments)

        # Call OpenAI API with GPT-4o-mini
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        # Parse and validate results
        result = json.loads(response.choices[0].message.content)
        mood_score = self._validate_mood_score(result["mood_score"])  # Round to 0.5 increments

        return MoodAnalysis(
            session_id=session_id,
            mood_score=mood_score,
            confidence=result["confidence"],
            rationale=result["rationale"],
            key_indicators=result["key_indicators"],
            emotional_tone=result["emotional_tone"],
            analyzed_at=datetime.utcnow()
        )
```

**Mood Scale**:
- 0.0-2.0: Severe distress (suicidal ideation, crisis, overwhelming despair)
- 2.5-4.0: Significant distress (moderate-severe depression/anxiety symptoms)
- 4.5-5.5: Mild distress to neutral (some symptoms, manageable)
- 6.0-7.5: Positive baseline (stable, functional, minor concerns)
- 8.0-10.0: Very positive (hopeful, energized, thriving)

**Analysis Dimensions**:
1. Emotional language and sentiment
2. Self-reported feelings and experiences
3. Energy level indicators (sleep, appetite, motivation)
4. Anxiety/depression symptom markers
5. Suicidal/self-harm ideation
6. Hopelessness vs. hopefulness expressions
7. Functioning (work/school, relationships, self-care)
8. Engagement level with therapist
9. Speaking patterns and verbal markers
10. Positive indicators (laughter, pride, connection, progress)

**Key Features**:
- Analyzes patient dialogue only (filters by speaker ID)
- No hardcoded outputs (pure AI reasoning)
- Nuanced scoring (considers both positive and negative signals)
- Explainable (provides rationale and key indicators)

#### TopicExtractor Service

Location: `backend/app/services/topic_extractor.py`

**Purpose**: AI-powered extraction of topics, action items, technique, and summary from therapy sessions

**Implementation**:
```python
class TopicExtractor:
    def __init__(self, api_key, override_model):
        self.model = get_model_name("topic_extraction", override_model)  # GPT-4o-mini
        self.technique_library = get_technique_library()  # Validate techniques against library

    def extract_metadata(session_id, segments, speaker_roles):
        # Format conversation with role labels
        conversation = self._format_conversation(segments, speaker_roles)

        # Create extraction prompt
        prompt = self._create_extraction_prompt(conversation)

        # Call OpenAI API with GPT-4o-mini
        response = openai.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        # Parse and validate results
        result = json.loads(response.choices[0].message.content)
        topics = result["topics"][:2]  # Max 2 topics
        action_items = result["action_items"][:2]  # Max 2 action items
        raw_technique = result["technique"]
        raw_summary = result["summary"]
        summary = self._truncate_summary(raw_summary, max_length=150)

        # Validate and standardize technique against library
        standardized_technique, technique_confidence, match_type = \
            self.technique_library.validate_and_standardize(raw_technique)

        return SessionMetadata(
            session_id=session_id,
            topics=topics,
            action_items=action_items,
            technique=standardized_technique or "Not specified",
            summary=summary,
            raw_meta_summary=response.choices[0].message.content,
            confidence=result["confidence"],
            extracted_at=datetime.utcnow()
        )
```

**Extraction Guidelines**:
- **Topics (1-2)**: Main themes or issues discussed (specific and clinical)
  - Good: "Relationship anxiety and fear of abandonment", "ADHD medication adjustment"
  - Bad: "Mental health", "Feelings" (too vague)

- **Action Items (2)**: Concrete homework, tasks, or commitments
  - Good: "Practice TIPP skills when feeling overwhelmed", "Schedule psychiatrist appointment"
  - Bad: "Feel better", "Think about things" (not actionable)

- **Technique (1)**: Primary therapeutic technique (validated against technique library)
  - Modalities: CBT, DBT, ACT, Mindfulness-Based, Motivational Interviewing, EMDR, Psychodynamic, Solution-Focused
  - Examples: "Cognitive Restructuring", "TIPP Skills", "Cognitive Defusion"
  - Rules: No made-up techniques, no non-clinical interventions

- **Summary (max 150 characters)**: Ultra-brief clinical summary
  - Direct, active voice without meta-commentary
  - Avoid: "The session focused on", "We discussed"
  - Start immediately with content

**Key Features**:
- Analyzes full conversation (both therapist and patient)
- Technique validation against clinical library
- Summary length enforcement (max 150 chars)
- No hardcoded outputs (AI naturally concludes from transcript)
- Fallback values if AI cannot determine (e.g., "General therapy session")

### 3. Database Schema (Supabase PostgreSQL)

#### therapy_sessions Table

Location: Database migrations and seed data in `backend/supabase/`

**Core Fields**:
- `id`: UUID primary key
- `patient_id`: UUID foreign key to users table
- `therapist_id`: UUID foreign key to users table
- `session_date`: TIMESTAMP
- `duration_minutes`: INTEGER
- `processing_status`: ENUM - `pending`, `processing`, `completed`, `wave1_in_progress`, `deep_complete`
- `analysis_status`: ENUM - `wave1_in_progress`, `deep_complete`

**Transcript & Audio**:
- `transcript`: JSONB array of segments `[{start, end, speaker, text}, ...]`
- `audio_file_url`: VARCHAR (URL to Supabase Storage)

**Mood Analysis Fields** (from mood_analyzer.py):
- `mood_score`: FLOAT (0.0-10.0 in 0.5 increments)
- `mood_confidence`: FLOAT (0.0-1.0)
- `mood_rationale`: TEXT
- `mood_indicators`: JSONB array
- `emotional_tone`: VARCHAR
- `mood_analyzed_at`: TIMESTAMP

**Topic Extraction Fields** (from topic_extractor.py):
- `topics`: JSONB array (1-2 topics)
- `action_items`: JSONB array (2 items)
- `technique`: VARCHAR (primary therapeutic technique)
- `summary`: VARCHAR(150) (ultra-brief summary)
- `extraction_confidence`: FLOAT (0.0-1.0)
- `raw_meta_summary`: TEXT (AI's raw JSON response)
- `topics_extracted_at`: TIMESTAMP

**Breakthrough Detection Fields**:
- `has_breakthrough`: BOOLEAN
- `breakthrough_data`: JSONB (primary breakthrough details)
- `breakthrough_label`: VARCHAR(50) (2-3 word label)
- `breakthrough_analyzed_at`: TIMESTAMP

**Deep Analysis Fields** (Wave 2):
- `deep_analysis`: JSONB (comprehensive clinical insights)
- `analysis_confidence`: FLOAT (0.0-1.0)
- `deep_analyzed_at`: TIMESTAMP

**Prose Fields**:
- `prose_analysis`: TEXT (500-750 word patient-facing narrative)
- `prose_generated_at`: TIMESTAMP

**Timestamps**:
- `created_at`: TIMESTAMP (auto-set)
- `updated_at`: TIMESTAMP (auto-updated)

### 4. Speaker Role Detection

Location: `frontend/lib/speaker-role-detection.ts:43-115`

**Purpose**: Determine which speaker is Therapist vs. Client from raw diarized transcript

**Implementation**: Multi-heuristic approach with confidence scoring

**Heuristic 1 - First Speaker**:
- Assumption: Therapist typically opens therapy sessions
- Finds first non-"UNKNOWN" speaker
- Confidence: 0.7

**Heuristic 2 - Speaking Ratio**:
- Assumption: Therapists speak 25-45% of session time, clients 55-75%
- Calculates speaking time percentage for each speaker
- Identifies speaker closest to ideal therapist ratio (0.25-0.45)
- Confidence: Based on how close to ideal range

**Combined Scoring**:
- If both heuristics agree: confidence up to 0.95
- If ratio confident (>0.6): use ratio-based assignment
- Otherwise: fallback to first-speaker with 0.7 confidence

**Output**:
- Replaces `SPEAKER_00`/`SPEAKER_01` with `"Therapist"`/`"Client"` labels
- Attaches confidence score to detection
- Returns labeled segments ready for AI analysis

**Note**: Backend receives segments with labels already applied and stores as-is. No re-processing at backend layer.

### 5. Audio Processing Pipeline

#### Flow Diagram

```
1. Frontend: Audio file selected by user
   ↓
2. POST /api/sessions/{id}/upload-audio
   ↓
3. Backend: Validate file type (mp3, wav, m4a, mp4)
   ↓
4. Upload to Supabase Storage bucket 'audio-sessions'
   ↓
5. Store URL in therapy_sessions.audio_file_url
   ↓
6. Set processing_status = "processing"
   ↓
7. Return session ID + audio URL + status
   ↓
8. Frontend: Poll processing_status every 3s (useProcessingStatus hook)
   ↓

[SEPARATE TRANSCRIPTION STEP - Not integrated]
   ↓
9. Transcript generated externally (audio-transcription-pipeline project)
   ↓
10. POST /api/sessions/{id}/upload-transcript
   ↓
11. Backend: Store transcript JSONB in therapy_sessions.transcript
   ↓
12. Optional: Trigger background breakthrough detection
   ↓
13. Wave 1 AI Analysis (if auto-analyze enabled):
    ├─ MoodAnalyzer.analyze_session_mood() → mood fields
    ├─ TopicExtractor.extract_metadata() → topic fields
    └─ BreakthroughDetector.analyze_session() → breakthrough fields
   ↓
14. Update database with all analysis results
   ↓
15. Set processing_status = "completed"
   ↓
16. Frontend: Polling detects completion, triggers onProcessingComplete callback
   ↓
17. Frontend: Refresh session data via GET /api/sessions/{id}
   ↓
18. Display in dashboard with all AI-extracted fields
```

#### Current Limitations

1. **Audio-to-Transcript Gap**:
   - `upload-audio` stores file but doesn't transcribe
   - Expects separate `upload-transcript` call
   - No integration between audio storage and transcription pipeline

2. **Separate Transcription Pipeline**:
   - `audio-transcription-pipeline/` is standalone project
   - Not automatically triggered by audio upload
   - Must manually call transcription pipeline and then upload transcript

3. **Speaker Role Labels**:
   - Backend accepts speaker values as-is from transcript
   - No validation that speakers are SPEAKER_00/SPEAKER_01 or Therapist/Client
   - No re-processing of roles at backend layer

### 6. Frontend API Client

Location: `frontend/lib/api-client.ts`

**Purpose**: Authenticated HTTP client for backend API with error handling and token refresh

**Key Features**:
- Generic `<T>` type parameter for type-safe responses
- Returns discriminated union `ApiResult<T>` for exhaustive error handling
- Automatic token refresh on 401 (expired token)
- Retry logic with exponential backoff
- Timeout handling (default 30s)
- Network error handling
- Demo token support for demo mode

**Methods**:
```typescript
class ApiClient {
  get<T>(endpoint: string, options?: ApiRequestOptions): Promise<ApiResult<T>>
  post<T>(endpoint: string, data?: Record<string, unknown>, options?: ApiRequestOptions): Promise<ApiResult<T>>
  put<T>(endpoint: string, data?: Record<string, unknown>, options?: ApiRequestOptions): Promise<ApiResult<T>>
  delete<T = null>(endpoint: string, options?: ApiRequestOptions): Promise<ApiResult<T>>
  patch<T>(endpoint: string, data?: Record<string, unknown>, options?: ApiRequestOptions): Promise<ApiResult<T>>

  // Specialized session methods
  createSessionNote<T>(sessionId: string, data: {...}, options?: ApiRequestOptions): Promise<ApiResult<T>>
  updateSessionNote<T>(noteId: string, data: {...}, options?: ApiRequestOptions): Promise<ApiResult<T>>
  autofillTemplate<T>(sessionId: string, templateType: string, options?: ApiRequestOptions): Promise<ApiResult<T>>
  getPatientConsistency<T>(patientId: string, days: number, options?: ApiRequestOptions): Promise<ApiResult<T>>
}

export const apiClient = new ApiClient();
```

**Usage Example**:
```typescript
const result = await apiClient.get<{ sessions: Session[] }>(
  `/api/sessions/patient/${patientId}`
);

if (result.success) {
  console.log('Sessions:', result.data.sessions);
} else {
  console.error('Error:', result.error, result.status);
}
```

### 7. Frontend Data Hooks

#### usePatientSessions Hook

Location: `frontend/app/patient/lib/usePatientSessions.ts`

**Purpose**: Fetch and manage session data for the dashboard

**Implementation**:
```typescript
export function usePatientSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSessions = async () => {
      const patientId = demoTokenStorage.getPatientId();

      const result = await apiClient.get<{ sessions: Session[] }>(
        `/api/sessions/patient/${patientId}`
      );

      if (result.success) {
        setSessions(result.data.sessions);
      }
      setIsLoading(false);
    };

    fetchSessions();
  }, []);

  return { sessions, isLoading, refresh, ... };
}
```

**Features**:
- Toggle between mock and real data via `USE_MOCK_DATA` flag
- Fetches from `/api/sessions/patient/{patientId}` endpoint
- Provides `refresh()` function for manual reloading
- Manages loading and error states
- Returns unified timeline with sessions + major events

**Returned Data**:
```typescript
{
  sessions: Session[],           // All sessions with AI-extracted fields
  tasks: Task[],                 // Action items from sessions
  timeline: TimelineEntry[],     // Session timeline
  unifiedTimeline: TimelineEvent[], // Sessions + major events merged
  majorEvents: MajorEventEntry[], // Chatbot-detected major events
  isLoading: boolean,
  isError: boolean,
  error: unknown,
  refresh: () => void,
  updateMajorEventReflection: (eventId, reflection) => void,
  sessionCount: number,
  majorEventCount: number,
  isEmpty: boolean
}
```

### 8. Frontend Context Provider

#### SessionDataContext

Location: `frontend/app/patient/contexts/SessionDataContext.tsx`

**Purpose**: Distribute session data globally to all dashboard components

**Implementation**:
```typescript
const SessionDataContext = createContext<SessionDataContextType | null>(null);

export function SessionDataProvider({ children }: { children: ReactNode }) {
  const data = usePatientSessions();

  return (
    <SessionDataContext.Provider value={data}>
      {children}
    </SessionDataContext.Provider>
  );
}

export function useSessionData(): SessionDataContextType {
  const context = useContext(SessionDataContext);
  if (!context) {
    throw new Error('useSessionData must be used within SessionDataProvider');
  }
  return context;
}
```

**Usage in Components**:
```typescript
function SessionCardsGrid() {
  const { sessions, isLoading } = useSessionData();

  return (
    <div>
      {sessions.map(session => (
        <SessionCard key={session.id} session={session} />
      ))}
    </div>
  );
}
```

**Features**:
- Single source of truth for session data
- Provides all data from `usePatientSessions` hook
- Components access via `useSessionData()` hook
- Supports auto-refresh on processing completion

### 9. Frontend Type Definitions

Location: `frontend/app/patient/lib/types.ts:68-88`

**Session Interface** (Matching Backend Schema):
```typescript
export interface Session {
  // Core fields
  id: string;
  date: string;
  duration: string;
  therapist: string;

  // Wave 1 AI Analysis - Mood
  mood: MoodType;  // Mapped from mood_score

  // Wave 1 AI Analysis - Topic Extraction
  topics: string[];  // From backend topics field
  strategy: string;  // Mapped from technique field
  actions: string[];  // From backend action_items field
  summary?: string;  // Ultra-brief summary (max 150 chars) - AI-generated
  extraction_confidence?: number;  // 0.0 to 1.0
  topics_extracted_at?: string;  // ISO timestamp

  // Additional fields
  milestone?: Milestone;
  transcript?: TranscriptEntry[];
  deep_analysis?: DeepAnalysis;
  analysis_confidence?: number;

  // Deprecated field
  patientSummary?: string;  // Use summary instead
}
```

**MoodType** (Mapped from mood_score):
```typescript
export type MoodType = 'very_low' | 'low' | 'neutral' | 'positive' | 'very_positive';

// Mapping from mood_score (0.0-10.0) to MoodType:
// 0.0-2.0 → very_low
// 2.5-4.0 → low
// 4.5-5.5 → neutral
// 6.0-7.5 → positive
// 8.0-10.0 → very_positive
```

### 10. Frontend Display Components

#### SessionCardsGrid

Location: `frontend/app/patient/dashboard-v3/components/SessionCardsGrid.tsx`

**Purpose**: Display paginated grid of session cards with all AI-extracted data

**Implementation**:
```typescript
export function SessionCardsGrid() {
  const { sessions, isLoading } = useSessionData();

  // Pagination: 6 cards per page (3x2 grid)
  // Page 1: AddSessionCard + 5 sessions
  // Page 2+: 6 sessions each

  const currentSessions = isFirstPage
    ? sessions.slice(0, 5)
    : sessions.slice(firstPageSessionCount + (currentPage - 1) * 6, ...);

  return (
    <div className="grid grid-cols-3 grid-rows-2 gap-4">
      {currentSessions.map(session => (
        <SessionCard key={session.id} session={session} />
      ))}
    </div>
  );
}
```

**Features**:
- 3x2 grid layout (6 cards per page)
- Pagination with slide animation
- Loads data from SessionDataProvider
- Displays all AI-extracted fields from each session

#### MoodIndicator

Location: `frontend/components/MoodIndicator.tsx`

**Purpose**: Display mood score with emoji and color coding

**Implementation**:
```typescript
interface MoodIndicatorProps {
  mood: SessionMood;
  trajectory?: MoodTrajectory;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function MoodIndicator({ mood, trajectory, showLabel, size }: MoodIndicatorProps) {
  const moodConfig = {
    very_low: { emoji: '😢', label: 'Very Low', color: 'bg-red-600', textColor: 'text-red-700' },
    low: { emoji: '😔', label: 'Low', color: 'bg-orange-500', textColor: 'text-orange-700' },
    neutral: { emoji: '😐', label: 'Neutral', color: 'bg-gray-400', textColor: 'text-gray-700' },
    positive: { emoji: '🙂', label: 'Positive', color: 'bg-green-400', textColor: 'text-green-700' },
    very_positive: { emoji: '😊', label: 'Very Positive', color: 'bg-green-600', textColor: 'text-green-700' },
  };

  const { emoji, label, color } = moodConfig[mood];

  return (
    <div className={`${color} rounded-full p-2`}>
      <span className="text-2xl">{emoji}</span>
      {showLabel && <span>{label}</span>}
    </div>
  );
}
```

**Features**:
- Emoji indicators for visual feedback
- Color-coded backgrounds
- Optional trajectory indicator (improving/declining/stable)
- Configurable size

#### ActionItemCard

Location: `frontend/components/ActionItemCard.tsx`

**Purpose**: Display action items extracted from topic analysis

**Implementation**:
```typescript
export function ActionItemCard({ actionItem }: ActionItemCardProps) {
  const [completed, setCompleted] = useState(false);

  return (
    <Card className={completed ? 'opacity-60' : ''}>
      <CardContent>
        <div className="flex items-start gap-3">
          <Checkbox
            checked={completed}
            onCheckedChange={(checked) => setCompleted(!!checked)}
          />
          <div>
            <p className={completed ? 'line-through' : ''}>
              {actionItem.task}
            </p>
            <Badge>{actionItem.category}</Badge>
            <p className="text-muted-foreground">{actionItem.details}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

**Features**:
- Checkbox for marking completed
- Category badge
- Local completion state tracking
- Strikethrough when completed

#### StrategyCard

Location: `frontend/components/StrategyCard.tsx`

**Purpose**: Display therapeutic techniques/strategies

**Implementation**:
```typescript
export function StrategyCard({ strategy }: StrategyCardProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{strategy.name}</CardTitle>
        <Badge className={categoryColors[strategy.category]}>
          {strategy.category}
        </Badge>
      </CardHeader>
      <CardContent>
        <Badge>{statusLabels[strategy.status]}</Badge>
        <p>{strategy.context}</p>
      </CardContent>
    </Card>
  );
}
```

**Features**:
- Category color coding
- Status badges (introduced/practiced/assigned/reviewed)
- Context/details text

## Complete Data Flow

### End-to-End Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. USER INTERACTION                                                 │
│    - Patient dashboard loads (app/patient/dashboard-v3/page.tsx)   │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. CONTEXT INITIALIZATION                                           │
│    - <SessionDataProvider> wraps dashboard                          │
│    - usePatientSessions() hook is called (from context)            │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. API FETCH (if not using mock data)                               │
│    - apiClient.get<{ sessions: Session[] }>(                        │
│        `/api/sessions/patient/{patientId}`                          │
│      )                                                               │
│    - Calls backend endpoint: GET /api/sessions/patient/{patientId} │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. BACKEND DATABASE QUERY                                           │
│    - Supabase.table("therapy_sessions")                             │
│        .select("*")                                                  │
│        .eq("patient_id", patientId)                                 │
│        .execute()                                                    │
│    - Returns sessions with ALL fields:                              │
│      • mood_score (from mood analyzer)                              │
│      • topics (from topic extractor)                                │
│      • action_items (from topic extractor)                          │
│      • technique (from topic extractor)                             │
│      • summary (from topic extractor)                               │
│      • deep_analysis (optional, from deep analyzer)                 │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. FRONTEND RECEIVES DATA                                           │
│    - setSessions(result.data.sessions)                              │
│    - Sets state in usePatientSessions hook                          │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. CONTEXT DISTRIBUTION                                             │
│    - SessionDataContext provides sessions to all children           │
│    - Components access via: const { sessions } = useSessionData()  │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 7. COMPONENT RENDERING                                              │
│    - SessionCardsGrid maps over sessions:                           │
│      {sessions.map(session => (                                     │
│        <SessionCard session={session} />                            │
│      ))}                                                             │
│    - SessionCard displays:                                          │
│      • MoodIndicator (uses session.mood_score)                      │
│      • Topics (uses session.topics)                                 │
│      • ActionItemCard (uses session.action_items)                   │
│      • StrategyCard (uses session.technique)                        │
│      • Summary text (uses session.summary)                          │
└─────────────────────────────────────────────────────────────────────┘
```

### AI Extraction Pipeline (Wave 1)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. TRANSCRIPT UPLOAD                                                │
│    - POST /api/sessions/{id}/upload-transcript                      │
│    - Transcript stored in therapy_sessions.transcript (JSONB)       │
│    - Triggers background analysis if auto-analyze enabled           │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. MOOD ANALYSIS (Async)                                            │
│    - MoodAnalyzer.analyze_session_mood(session_id, segments)        │
│    - Filters to patient dialogue only (SPEAKER_01)                  │
│    - GPT-4o-mini analyzes 10+ emotional/clinical dimensions         │
│    - Returns: mood_score (0-10), confidence, rationale, indicators  │
│    - Stores in database: mood_score, mood_confidence,               │
│      mood_rationale, mood_indicators, emotional_tone,               │
│      mood_analyzed_at                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. TOPIC EXTRACTION (Async)                                         │
│    - TopicExtractor.extract_metadata(session_id, segments)          │
│    - Analyzes full conversation (therapist + patient)               │
│    - GPT-4o-mini extracts: topics, action_items, technique, summary │
│    - Validates technique against clinical library                   │
│    - Truncates summary to max 150 characters                        │
│    - Stores in database: topics, action_items, technique, summary,  │
│      extraction_confidence, raw_meta_summary, topics_extracted_at   │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. BREAKTHROUGH DETECTION (Async)                                   │
│    - BreakthroughDetector.analyze_session(transcript, metadata)     │
│    - Identifies therapeutic breakthroughs                           │
│    - Stores in database: has_breakthrough, breakthrough_data,       │
│      breakthrough_label, breakthrough_analyzed_at                   │
│    - Inserts rows into breakthrough_history table                   │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. STATUS UPDATE                                                    │
│    - Update processing_status = "completed"                         │
│    - Update analysis_status = "wave1_complete"                      │
└────────────────────────────┬────────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 6. FRONTEND POLLING                                                 │
│    - useProcessingStatus() polls every 3s                           │
│    - Detects processing_status = "completed"                        │
│    - Triggers onProcessingComplete callback                         │
│    - Dashboard auto-refreshes session data                          │
└─────────────────────────────────────────────────────────────────────┘
```

## Code References

### Backend

- **Session Router**: `backend/app/routers/sessions.py`
  - Audio upload endpoint: line 293-359
  - Transcript upload endpoint: line 222-290
  - Mood analysis endpoint: line 675-770
  - Topic extraction endpoint: line 867-960
  - Session retrieval: line 127-143, 146-188

- **AI Services**:
  - Mood analyzer: `backend/app/services/mood_analyzer.py`
  - Topic extractor: `backend/app/services/topic_extractor.py`

- **Database Schema**:
  - Migrations: `backend/supabase/migrations/`
  - Seed data: `backend/supabase/seed_demo_data.sql:64-100`

### Frontend

- **API Client**: `frontend/lib/api-client.ts`
  - GET request method: line 332-334
  - POST request method: line 339-345

- **Data Hooks**: `frontend/app/patient/lib/usePatientSessions.ts`

- **Context Provider**: `frontend/app/patient/contexts/SessionDataContext.tsx`

- **Type Definitions**: `frontend/app/patient/lib/types.ts:68-88`

- **Display Components**:
  - SessionCardsGrid: `frontend/app/patient/dashboard-v3/components/SessionCardsGrid.tsx`
  - MoodIndicator: `frontend/components/MoodIndicator.tsx`
  - ActionItemCard: `frontend/components/ActionItemCard.tsx`
  - StrategyCard: `frontend/components/StrategyCard.tsx`

- **Speaker Detection**: `frontend/lib/speaker-role-detection.ts:43-115`

## Architecture Patterns

### 1. Multi-Wave Analysis Architecture

**Wave 1 (Immediate Analysis)**:
- Mood analysis (0-10 score)
- Topic extraction (1-2 topics)
- Action items (2 items)
- Technique identification
- Summary generation (max 150 chars)
- Breakthrough detection

**Wave 2 (Deep Analysis - Optional)**:
- Comprehensive clinical insights
- Prose generation (500-750 words)

**Benefits**:
- Fast initial results for dashboard display
- Optional deeper analysis for detailed reports
- Cost-effective (uses GPT-4o-mini for Wave 1)

### 2. Caching Strategy

**Pattern**: Check for existing analysis before re-running AI

```python
if session.get("mood_analyzed_at") and not force:
    return {
        "session_id": session_id,
        "status": "already_analyzed",
        "mood_score": session.get("mood_score"),
        # ... (cached results)
    }
```

**Benefits**:
- Prevents duplicate API calls to OpenAI
- Reduces costs
- Faster response times
- Optional `force=true` parameter for re-analysis

### 3. Background Processing

**Pattern**: Use FastAPI BackgroundTasks for long operations

```python
@router.post("/{session_id}/upload-transcript")
async def upload_transcript(
    session_id: str,
    background_tasks: BackgroundTasks,
    ...
):
    # Store transcript immediately
    # ...

    # Trigger analysis in background
    if settings.breakthrough_auto_analyze:
        background_tasks.add_task(
            analyze_breakthrough_background,
            session_id,
            transcript
        )

    # Return immediately
    return {"status": "processing"}
```

**Benefits**:
- HTTP endpoints return immediately
- Long AI analysis doesn't block response
- Status polling pattern for completion detection

### 4. Discriminated Union Error Handling

**Pattern**: Type-safe error handling with ApiResult<T>

```typescript
type ApiResult<T> = SuccessResult<T> | FailureResult;

const result = await apiClient.get<Session>('/api/sessions/123');

if (result.success) {
  console.log(result.data);  // TypeScript knows data exists
} else {
  console.error(result.error, result.status);  // TypeScript knows error exists
}
```

**Benefits**:
- Exhaustive error checking
- Type safety
- No need for try/catch blocks
- Forces explicit error handling

### 5. Speaker Role Detection

**Pattern**: Multi-heuristic approach with confidence scoring

```typescript
const therapistDetection = detectTherapistRole(segments);

// Combines two heuristics:
// 1. First speaker (therapist opens session)
// 2. Speaking ratio (therapist speaks 25-45% of time)

if (therapistDetection.confidence > 0.7) {
  // Use detected roles
  labeledSegments = applyRoles(segments, therapistDetection);
} else {
  // Fallback to default (SPEAKER_00 = Therapist)
  labeledSegments = applyDefaultRoles(segments);
}
```

**Benefits**:
- More accurate than single heuristic
- Confidence scoring for quality control
- Fallback mechanism for low confidence

## Current Limitations

1. **Audio-to-Transcript Gap**:
   - `upload-audio` stores file but doesn't transcribe
   - Expects separate `upload-transcript` call
   - No integration between audio storage and transcription pipeline

2. **Separate Transcription Pipeline**:
   - `audio-transcription-pipeline/` is standalone project
   - Not automatically triggered by audio upload
   - Must manually call transcription pipeline and then upload transcript

3. **Speaker Role Labels**:
   - Backend accepts speaker values as-is from transcript
   - No validation that speakers are SPEAKER_00/SPEAKER_01 or Therapist/Client
   - No re-processing of roles at backend layer

4. **Missing SessionCard Component**:
   - Referenced in code but not yet implemented
   - Expected at: `frontend/components/SessionCard.tsx`
   - Would display individual session data with all AI-extracted fields

## Related Research

- Session log in `.claude/CLAUDE.md` documents implementation history
- Database migrations in `backend/supabase/migrations/` show schema evolution
- Mock data in `frontend/app/patient/lib/mockData.ts` shows expected data structure

## Open Questions

None - all research questions answered.

## Cost Analysis

**Per-Session Analysis Cost** (using GPT-4o-mini):
- Mood analysis: ~$0.005 per session
- Topic extraction: ~$0.005 per session
- **Total Wave 1**: ~$0.01 per session

**Assumptions**:
- Average transcript: 3,000 tokens
- GPT-4o-mini pricing: $0.15/1M input tokens, $0.60/1M output tokens
- Analysis output: ~500 tokens per service

**Cost-Effectiveness**:
- 100 sessions analyzed = ~$1.00
- 1,000 sessions analyzed = ~$10.00
- Highly affordable for production use
