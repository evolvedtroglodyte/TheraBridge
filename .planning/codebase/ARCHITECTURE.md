# Architecture

**Analysis Date:** 2026-01-08

## Pattern Overview

**Overall:** Microservices Monorepo with Specialized Components

**Key Characteristics:**
- Four independent services (frontend, backend, audio-pipeline, scraper)
- Event-driven Wave 1 → Wave 2 analysis pipeline
- Real-time UI updates via polling (SSE disabled)
- Demo mode with background subprocess orchestration
- File-based state management with PostgreSQL persistence

## Layers

### **Backend (FastAPI)** - 4-Layer Architecture

**HTTP API Layer:**
- Purpose: Route HTTP requests to services
- Contains: FastAPI router modules
- Location: `backend/app/routers/`
- Key files:
  - `backend/app/routers/sessions.py` - Session CRUD + analysis endpoints
  - `backend/app/routers/demo.py` - Demo init/reset/stop + background orchestration
  - `backend/app/routers/sse.py` - Server-Sent Events (disabled)
  - `backend/app/routers/debug.py` - Development utilities
- Depends on: Service layer, middleware
- Used by: Frontend API client

**Service Layer:**
- Purpose: AI analysis business logic
- Contains: Stateless analyzer modules
- Location: `backend/app/services/`
- Key files:
  - `backend/app/services/analysis_orchestrator.py` - Wave coordination
  - `backend/app/services/mood_analyzer.py` - Emotional tone analysis
  - `backend/app/services/topic_extractor.py` - Topics + action items
  - `backend/app/services/breakthrough_detector.py` - Clinical breakthrough detection
  - `backend/app/services/deep_analyzer.py` - Comprehensive synthesis
  - `backend/app/services/prose_generator.py` - Human-readable output
- Depends on: OpenAI API, database
- Used by: Routers, background scripts

**Data Layer:**
- Purpose: Database operations and persistence
- Contains: Supabase client wrapper
- Location: `backend/app/database.py`
- Pattern: Singleton Supabase client with admin client for RLS bypass
- Depends on: Supabase PostgreSQL (Neon)
- Used by: All layers

**Middleware & Configuration:**
- Purpose: Request preprocessing and settings
- Contains: Auth validation, config management
- Location: `backend/app/middleware/`, `backend/app/config.py`
- Key files:
  - `backend/app/middleware/demo_auth.py` - X-Demo-Token validation
  - `backend/app/config.py` - Environment-based settings
- Depends on: Database
- Used by: Routers (dependency injection)

### **Frontend (Next.js 16)** - 4-Layer Architecture

**Page/Route Layer:**
- Purpose: URL routing and page rendering
- Contains: Next.js App Router pages
- Location: `frontend/app/`
- Key files:
  - `frontend/app/page.tsx` - Demo initialization entry point
  - `frontend/app/patient/layout.tsx` - Dashboard layout wrapper
  - `frontend/app/dashboard/page.tsx` - Session cards grid
  - `frontend/app/patient/upload/page.tsx` - Audio/transcript upload
- Depends on: Components, contexts
- Used by: Next.js router

**Component Layer:**
- Purpose: Reusable UI rendering
- Contains: React components (stateful + stateless)
- Location: `frontend/app/patient/components/`, `frontend/components/`
- Key files:
  - `frontend/app/patient/components/SessionCard.tsx` - Card with mood emoji (normal + breakthrough variants)
  - `frontend/app/patient/components/SessionDetail.tsx` - Full-screen modal with transcript + analysis
  - `frontend/app/patient/components/SessionCardsGrid.tsx` - Grid layout container
  - `frontend/app/patient/components/DeepAnalysisSection.tsx` - Wave 2 prose display
  - `frontend/app/patient/components/LoadingOverlay.tsx` - Per-session loading indicator
- Depends on: Hooks, contexts
- Used by: Pages

**State Management Layer:**
- Purpose: Global state distribution
- Contains: React contexts + custom hooks
- Location: `frontend/app/patient/contexts/`, `frontend/app/patient/hooks/`
- Key files:
  - `frontend/app/patient/contexts/SessionDataContext.tsx` - Session data distribution
  - `frontend/app/patient/contexts/ThemeContext.tsx` - Dark/light mode
  - `frontend/app/patient/lib/usePatientSessions.ts` - Core data fetching + polling
  - `frontend/app/patient/hooks/useMoodAnalysis.ts` - Mood trend analysis
- Depends on: API client
- Used by: Components

**Service & Utility Layer:**
- Purpose: API communication and utilities
- Contains: HTTP client, storage, type definitions
- Location: `frontend/lib/`
- Key files:
  - `frontend/lib/api-client.ts` - Authenticated HTTP client with retry
  - `frontend/lib/demo-api-client.ts` - Demo-specific endpoints
  - `frontend/lib/demo-token-storage.ts` - localStorage management
  - `frontend/lib/api-types.ts` - Discriminated union response types
- Depends on: (none - leaf layer)
- Used by: Hooks, contexts

## Data Flow

### **Demo Initialization Flow**

1. User visits "/" (`frontend/app/page.tsx`)
2. Check localStorage for demo token (`frontend/lib/demo-token-storage.ts`)
3. **If no token:** Call `/api/demo/initialize` → `backend/app/routers/demo.py`
4. Backend creates user with demo_token + patient_id (UUID)
5. Launch 3 background subprocesses (non-blocking):
   - Step 1: Populate transcripts (`backend/scripts/seed_all_sessions.py`)
   - Step 2: Run Wave 1 analysis (`backend/scripts/seed_wave1_analysis.py`)
   - Step 3: Run Wave 2 analysis (`backend/scripts/seed_wave2_analysis.py`)
6. Return { demo_token, patient_id, session_ids } immediately (~30s)
7. Frontend saves to localStorage, redirects to `/dashboard`

### **Session Display & Polling Flow**

1. Dashboard loads → SessionDataProvider wraps children
2. usePatientSessions() fetches `/api/sessions/patient/{patient_id}`
3. Start polling `/api/demo/status` every 5 seconds
4. When wave1_complete → Fetch updated sessions → Show loading overlay per session
5. When wave2_complete → Fetch again → Remove overlay + show prose analysis
6. SessionCard displays summary (AI-generated), mood emoji, technique
7. On click → SessionDetail modal opens with transcript + full analysis

### **Analysis Pipeline Flow (Background)**

**Wave 1 (Parallel Execution ~60s):**
```
For each session:
  ├─ MoodAnalyzer.analyze() → mood_score (0-10)
  ├─ TopicExtractor.extract() → topics, technique, action_items, summary
  └─ BreakthroughDetector.detect() → has_breakthrough flag
      ↓
  Update therapy_sessions table with Wave 1 results
```

**Wave 2 (Sequential after Wave 1 completes ~9.6 min):**
```
For each session:
  ├─ DeepAnalyzer.analyze() → structured deep_analysis JSONB
  └─ ProseGenerator.generate() → prose_analysis TEXT
      ↓
  Update therapy_sessions table with Wave 2 results
```

**State Management:**
- File-based state in `.planning/` directory (not used in production)
- PostgreSQL state in therapy_sessions table
- In-memory state in `analysis_status` dict (backend/app/routers/demo.py)

## Key Abstractions

**AnalysisOrchestrator:**
- Purpose: Coordinates Wave 1 (parallel) → Wave 2 (sequential)
- Examples: `backend/app/services/analysis_orchestrator.py`
- Pattern: Dependency manager with retry logic (3 attempts, exponential backoff)

**Service:**
- Purpose: Encapsulate AI analysis for single domain
- Examples: `backend/app/services/mood_analyzer.py`, `backend/app/services/topic_extractor.py`
- Pattern: Stateless classes with OpenAI client injection

**ApiClient:**
- Purpose: Type-safe HTTP communication with error handling
- Examples: `frontend/lib/api-client.ts`
- Pattern: Discriminated union return type (ApiResult<T> = success | failure)

**SessionDataContext:**
- Purpose: Global session state distribution
- Examples: `frontend/app/patient/contexts/SessionDataContext.tsx`
- Pattern: Provider pattern with custom hook (useSessionData)

**Demo Token Storage:**
- Purpose: Persistent demo state management
- Examples: `frontend/lib/demo-token-storage.ts`
- Pattern: localStorage wrapper with type-safe getters

## Entry Points

**Backend Entry:**
- Location: `backend/app/main.py`
- Triggers: `uvicorn app.main:app --reload` (dev) or Railway deployment
- Responsibilities: Initialize FastAPI app, register routers, configure CORS middleware

**Frontend Entry:**
- Location: `frontend/app/page.tsx` (root route "/")
- Triggers: User visits site, `npm run dev` or `next start`
- Responsibilities: Demo initialization check, redirect to dashboard

**Background Scripts:**
- Location: `backend/scripts/seed_all_sessions.py`, `backend/scripts/seed_wave1_analysis.py`, `backend/scripts/seed_wave2_analysis.py`
- Triggers: Called by `backend/app/routers/demo.py` via subprocess
- Responsibilities: Populate database with demo data + analysis results

## Error Handling

**Strategy:** Throw exceptions at boundaries, catch in routers/components

**Patterns:**
- Backend: `raise HTTPException(status_code=...)` in routers
- Frontend: `ApiResult<T>` discriminated union (success | network | timeout | server | validation)
- Subprocess: Try/catch with logging in background scripts

## Cross-Cutting Concerns

**Logging:**
- Backend: Python logging module + `print(..., flush=True)` for Railway visibility
- Frontend: Conditional `console.log()` via `NEXT_PUBLIC_DEBUG_POLLING` flag
- Location: All service modules, routers

**Validation:**
- Backend: Pydantic models for request/response validation
- Frontend: Zod schemas for API type validation (`frontend/lib/api-types.ts`)
- Pattern: Validate at API boundaries only

**Authentication:**
- Pattern: JWT middleware + demo token middleware
- Location: `backend/app/middleware/demo_auth.py`
- Flow: Extract X-Demo-Token header → Validate UUID → Check database

**State Synchronization:**
- Pattern: Polling with status endpoint (`/api/demo/status`)
- Frequency: 5 seconds baseline, 1s Wave 1, 3s Wave 2
- Location: `frontend/app/patient/lib/usePatientSessions.ts`

---

*Architecture analysis: 2026-01-08*
*Update when major patterns change*
