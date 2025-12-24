# Session 1 Summary - Vertical Integration Implementation Plan

## Overview

Vertically integrate the first session's summary from database → backend API → frontend UI, replacing mock data with real data for Session 1 only while maintaining mock data for sessions 2-10.

## Execution Instructions

**For the AI implementing this plan:**

1. Read this entire plan before starting
2. Execute phases sequentially (Phase 1 → 2 → 3 → 4)
3. After completing each phase, run ALL success criteria checks (automated + manual)
4. Ask user for confirmation before proceeding to next phase
5. If any success criterion fails, fix it before proceeding
6. Use the exact code snippets provided (adjust only for file structure differences)
7. Log all changes clearly to the user

**Repository Structure:**
- **Root:** `/Users/newdldewdl/Global Domination 2/peerbridge proj/`
- **Backend:** `backend/` (FastAPI + Supabase)
- **Frontend:** `frontend/` (Next.js 16 + React 19)
- **Current Branch:** `main`

**Prerequisites:**
- Backend server must be running: `cd backend && uvicorn app.main:app --reload`
- Frontend dev server: `cd frontend && npm run dev`
- Database: Neon PostgreSQL (already configured)

**Git Workflow (CRITICAL - Follow GIT_COMMIT_RULES.md):**

**All commits MUST be backdated to December 23, 2025, starting at 21:00:00, incrementing by 1 minute.**

1. **BEFORE STARTING:** Create git commit with current state
   ```bash
   cd "/Users/newdldewdl/Global Domination 2/peerbridge proj"
   git add -A
   git commit -m "Pre-implementation backup: Session 1 vertical integration"
   git commit --amend --date="2025-12-23 21:00:00"
   git push
   ```

2. **AFTER PHASE 3 COMPLETION:** Create another commit
   ```bash
   git add -A
   git commit -m "Implement Session 1 vertical integration: hybrid data hook"
   git commit --amend --date="2025-12-23 21:01:00"
   git push
   ```

3. **IF ANYTHING GOES WRONG:** Rollback with `git reset --hard HEAD~1`

**Important:**
- Each commit uses format: `git commit -m "message" && git commit --amend --date="2025-12-23 HH:MM:SS"`
- Increment time by 1 minute for each commit (21:00, 21:01, 21:02, etc.)
- See `.claude/GIT_COMMIT_RULES.md` for complete workflow

## Current State Analysis

### Backend (✅ Complete)
- **Demo Flow:** Complete demo initialization exists at `POST /api/demo/initialize`
  - Generates demo token (UUID)
  - Creates patient + therapist users
  - Seeds 10 therapy sessions via SQL function `seed_demo_user_sessions()`
  - Returns `demo_token`, `patient_id`, `session_ids[]`
- **Session API:** `GET /api/sessions/patient/{patient_id}` returns sessions
- **Database:** Neon PostgreSQL with Supabase
  - Session 1 data seeded with `summary` field: "Crisis intake for recent breakup with passive SI, safety plan created"
  - Full transcript, mood analysis, topics, technique, action items available

### Frontend (⏳ Needs Integration)
- **Current Mode:** Mock data mode (`USE_MOCK_DATA = true` in `usePatientSessions.ts`)
- **SessionCard Component:** Displays `session.summary` field at lines 410-438 (normal card) and 256-284 (breakthrough card)
- **Data Flow:** `usePatientSessions` hook → `SessionDataContext` → `SessionCardsGrid` → `SessionCard`
- **Error Handling:** Currently uses fallback: `session.summary || session.patientSummary || 'Summary not yet generated.'`

## Desired End State

**Session 1 Card:**
- ✅ Displays real summary from database: "Crisis intake for recent breakup with passive SI, safety plan created"
- ✅ Fetched via backend API on page load
- ✅ Demo token stored in localStorage for persistence
- ✅ Error text replaces summary if API fails: "Error loading session summary"

**Sessions 2-10:**
- ✅ Continue using mock data (no changes)
- ✅ Same UI/UX as before

**Demo Token Flow:**
1. On first visit → Call `/api/demo/initialize` → Store token in localStorage
2. On subsequent visits → Retrieve token from localStorage → Use existing demo sessions
3. On new device/browser → Fresh token initialization (old tokens expire after 24h)

## What We're NOT Doing

- ❌ Converting all sessions to real data (only Session 1)
- ❌ Adding loading spinners or skeleton states
- ❌ Modifying SessionCard component layout/styling
- ❌ Implementing full authentication (demo token only)
- ❌ Fetching other fields beyond `summary` (date, mood, topics remain mock for now)

---

## Implementation Approach

**Strategy:** Hybrid data mode using `usePatientSessions` hook
- Fetch Session 1 from API
- Merge with mock sessions 2-10
- No changes to SessionCard component (already supports `session.summary` field)

---

## Phase 1: Backend Demo Token Storage Utility

### Overview
Create frontend utility to manage demo token lifecycle in localStorage.

### Changes Required

#### 1.1 Demo Token Storage Module

**File**: `frontend/lib/demo-token-storage.ts`
**Changes**: Create new file

```typescript
/**
 * Demo Token Storage Utility
 * Manages demo token lifecycle in localStorage
 */

const DEMO_TOKEN_KEY = 'therapybridge_demo_token';
const PATIENT_ID_KEY = 'therapybridge_patient_id';
const SESSION_IDS_KEY = 'therapybridge_session_ids';
const EXPIRES_AT_KEY = 'therapybridge_demo_expires';

export const demoTokenStorage = {
  /**
   * Store demo credentials after initialization
   */
  store(demoToken: string, patientId: string, sessionIds: string[], expiresAt: string) {
    if (typeof window === 'undefined') return;

    localStorage.setItem(DEMO_TOKEN_KEY, demoToken);
    localStorage.setItem(PATIENT_ID_KEY, patientId);
    localStorage.setItem(SESSION_IDS_KEY, JSON.stringify(sessionIds));
    localStorage.setItem(EXPIRES_AT_KEY, expiresAt);
  },

  /**
   * Retrieve stored demo token (returns null if expired or missing)
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null;

    const token = localStorage.getItem(DEMO_TOKEN_KEY);
    const expiresAt = localStorage.getItem(EXPIRES_AT_KEY);

    if (!token || !expiresAt) return null;

    // Check if expired
    const expiry = new Date(expiresAt);
    if (expiry < new Date()) {
      this.clear();
      return null;
    }

    return token;
  },

  /**
   * Get patient ID
   */
  getPatientId(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem(PATIENT_ID_KEY);
  },

  /**
   * Get session IDs
   */
  getSessionIds(): string[] | null {
    if (typeof window === 'undefined') return null;

    const sessionIdsJson = localStorage.getItem(SESSION_IDS_KEY);
    if (!sessionIdsJson) return null;

    try {
      return JSON.parse(sessionIdsJson);
    } catch {
      return null;
    }
  },

  /**
   * Check if demo is initialized
   */
  isInitialized(): boolean {
    return this.getToken() !== null && this.getPatientId() !== null;
  },

  /**
   * Clear all demo data
   */
  clear() {
    if (typeof window === 'undefined') return;

    localStorage.removeItem(DEMO_TOKEN_KEY);
    localStorage.removeItem(PATIENT_ID_KEY);
    localStorage.removeItem(SESSION_IDS_KEY);
    localStorage.removeItem(EXPIRES_AT_KEY);
  }
};
```

### Success Criteria

#### Automated Verification:
- [ ] TypeScript compiles without errors: `npm run typecheck`
- [ ] Module exports all functions correctly

#### Manual Verification:
- [ ] Can store demo token in localStorage
- [ ] Can retrieve token and check expiry
- [ ] Expired tokens return null and are cleared
- [ ] Works correctly in SSR (returns null server-side)

---

## Phase 2: Demo Initialization API Client

### Overview
Add API methods to initialize demo and fetch Session 1 data.

### Changes Required

#### 2.1 API Client - Demo Endpoints

**File**: `frontend/lib/api-client.ts`
**Changes**: Add demo initialization methods

**Find this section (around line 50-100):**
```typescript
// Existing API client methods...
```

**Add after existing methods:**
```typescript
/**
 * Initialize demo user and get demo token
 */
async initializeDemo(): Promise<{
  success: boolean;
  data?: {
    demo_token: string;
    patient_id: string;
    session_ids: string[];
    expires_at: string;
    message: string;
  };
  error?: string;
}> {
  return this.post('/api/demo/initialize', {});
},

/**
 * Fetch single session by ID
 */
async getSessionById(sessionId: string): Promise<{
  success: boolean;
  data?: any;
  error?: string;
}> {
  return this.get(`/api/sessions/${sessionId}`);
},
```

#### 2.2 API Client - Add Demo Token Header

**File**: `frontend/lib/api-client.ts`
**Changes**: Inject demo token into request headers

**Find this section (around line 20-40):**
```typescript
private async request<T>(/* ... */) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    // ... existing headers
  };
```

**Add after existing headers:**
```typescript
  // Add demo token if available (import at top of file)
  const demoToken = demoTokenStorage.getToken();
  if (demoToken) {
    headers['X-Demo-Token'] = demoToken;
  }
```

**Also add this import at the top of the file (around line 1-10):**
```typescript
import { demoTokenStorage } from './demo-token-storage';
```

### Success Criteria

#### Automated Verification:
- [ ] TypeScript compiles: `npm run typecheck`
- [ ] ESLint passes: `npm run lint`

#### Manual Verification:
- [ ] Can call `apiClient.initializeDemo()` and receive demo token
- [ ] Can call `apiClient.getSessionById(id)` with demo token in headers
- [ ] Headers include `X-Demo-Token` when token is stored

---

## Phase 3: Hybrid Data Hook (Session 1 Real + 2-10 Mock)

### Overview
Modify `usePatientSessions` to fetch Session 1 from API and merge with mock data.

### Changes Required

#### 3.1 usePatientSessions Hook - Hybrid Mode

**File**: `frontend/app/patient/lib/usePatientSessions.ts`
**Changes**: Replace mock-only mode with hybrid mode

**Current code (lines 26-95):**
```typescript
const USE_MOCK_DATA = true;  // Using mock data for development

export function usePatientSessions() {
  // ... existing state ...

  useEffect(() => {
    if (USE_MOCK_DATA) {
      // Simulate loading with mock data
      const timer = setTimeout(() => {
        setSessions(mockSessions);
        // ...
      }, 300);
      return () => clearTimeout(timer);
    }

    // Real data fetch (not used)
    // ...
  }, []);
}
```

**Replace with:**
```typescript
// HYBRID MODE: Session 1 from API, Sessions 2-10 from mock data
const USE_HYBRID_MODE = true;

export function usePatientSessions() {
  const [isLoading, setIsLoading] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [unifiedTimeline, setUnifiedTimeline] = useState<TimelineEvent[]>([]);
  const [majorEvents, setMajorEvents] = useState<MajorEventEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  // NOTE: Add these imports at the top of the file:
  // import { demoTokenStorage } from '@/lib/demo-token-storage';
  // import { apiClient } from '@/lib/api-client';

  useEffect(() => {
    const initializeAndFetch = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Step 1: Initialize demo if needed
        if (!demoTokenStorage.isInitialized()) {
          console.log('[Demo] No token found, initializing demo...');
          const initResult = await apiClient.initializeDemo();

          if (!initResult.success || !initResult.data) {
            throw new Error(initResult.error || 'Failed to initialize demo');
          }

          // Store demo credentials
          const { demo_token, patient_id, session_ids, expires_at } = initResult.data;
          demoTokenStorage.store(demo_token, patient_id, session_ids, expires_at);
          console.log('[Demo] ✓ Initialized:', { patient_id, sessionCount: session_ids.length });
        }

        // Step 2: Get session IDs
        const sessionIds = demoTokenStorage.getSessionIds();
        if (!sessionIds || sessionIds.length === 0) {
          throw new Error('No session IDs found');
        }

        // Step 3: Fetch Session 1 from API
        const session1Id = sessionIds[0];
        console.log('[Session1] Fetching from API:', session1Id);

        const sessionResult = await apiClient.getSessionById(session1Id);

        let session1Data: Session;
        if (!sessionResult.success || !sessionResult.data) {
          console.error('[Session1] Failed to fetch:', sessionResult.error);
          // Use mock Session 1 with error text
          session1Data = {
            ...mockSessions[0],
            summary: 'Error loading session summary'
          };
        } else {
          // Transform backend session to frontend Session type
          const backendSession = sessionResult.data;
          session1Data = {
            id: backendSession.id,
            date: new Date(backendSession.session_date).toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric'
            }),
            duration: `${backendSession.duration_minutes || 60} min`,
            therapist: 'Dr. Rodriguez',
            mood: 'neutral' as MoodType, // TODO: Map mood_score to MoodType
            topics: backendSession.topics || [],
            strategy: backendSession.technique || 'Not yet analyzed',
            actions: backendSession.action_items || [],
            summary: backendSession.summary || 'Summary not yet generated.',
            transcript: backendSession.transcript || [],
            extraction_confidence: backendSession.extraction_confidence,
            topics_extracted_at: backendSession.topics_extracted_at,
          };
          console.log('[Session1] ✓ Loaded summary:', session1Data.summary);
        }

        // Step 4: Merge Session 1 (real) + Sessions 2-10 (mock)
        const hybridSessions = [session1Data, ...mockSessions.slice(1)];

        // Step 5: Update state
        setSessions(hybridSessions);
        setTasks(mockTasks);
        setTimeline(mockTimeline);
        setUnifiedTimeline(mockUnifiedTimeline);
        setMajorEvents(mockMajorEvents);

      } catch (err) {
        console.error('[usePatientSessions] Error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load sessions');

        // Fallback to full mock data on error
        setSessions(mockSessions);
        setTasks(mockTasks);
        setTimeline(mockTimeline);
        setUnifiedTimeline(mockUnifiedTimeline);
        setMajorEvents(mockMajorEvents);
      } finally {
        setIsLoading(false);
      }
    };

    if (USE_HYBRID_MODE) {
      initializeAndFetch();
    } else {
      // Full mock mode (legacy)
      const timer = setTimeout(() => {
        setSessions(mockSessions);
        setTasks(mockTasks);
        setTimeline(mockTimeline);
        setUnifiedTimeline(mockUnifiedTimeline);
        setMajorEvents(mockMajorEvents);
        setIsLoading(false);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, []);

  // Manual refresh function
  const refresh = () => {
    setIsLoading(true);
    // Re-run the effect by forcing a state update
    setError(null);
  };

  // ... rest of the hook unchanged ...
}
```

### Success Criteria

#### Automated Verification:
- [ ] TypeScript compiles: `npm run typecheck`
- [ ] ESLint passes: `npm run lint`
- [ ] No console errors during build: `npm run build`

#### Manual Verification:
- [ ] On first load, demo initializes and Session 1 summary displays real data
- [ ] Sessions 2-10 display mock data unchanged
- [ ] On refresh, token is reused (no new demo initialization)
- [ ] On error, Session 1 shows "Error loading session summary"
- [ ] localStorage contains demo token after initialization
- [ ] Opening in new browser tab reuses existing demo token

---

## Phase 4: Testing & Validation

### Overview
Verify the complete vertical integration works end-to-end.

### Testing Strategy

#### 4.1 Unit Tests (Optional for MVP)
- Test `demoTokenStorage` get/set/clear functions
- Test expired token handling

#### 4.2 Integration Tests

**Manual Test Cases:**

1. **Fresh Browser Test:**
   - Clear localStorage
   - Navigate to `/patient/sessions`
   - ✅ Verify demo initializes (check console)
   - ✅ Verify Session 1 card shows real summary from database
   - ✅ Verify Sessions 2-10 show mock data

2. **Token Persistence Test:**
   - Refresh page
   - ✅ Verify no new demo initialization (check console)
   - ✅ Verify Session 1 still shows real summary
   - ✅ Verify localStorage contains demo token

3. **New Browser/Device Test:**
   - Open in incognito/different browser
   - ✅ Verify new demo token is generated
   - ✅ Verify Session 1 shows real summary

4. **Error Handling Test:**
   - Stop backend server
   - Refresh frontend
   - ✅ Verify Session 1 shows "Error loading session summary"
   - ✅ Verify no app crash
   - ✅ Verify console shows error message

5. **Token Expiry Test (24h simulation):**
   - Manually edit localStorage to set expired date
   - Refresh page
   - ✅ Verify new demo initialization
   - ✅ Verify new token stored

### Success Criteria

#### Automated Verification:
- [ ] Backend server starts successfully: `cd backend && uvicorn app.main:app --reload`
- [ ] Frontend builds without errors: `npm run build`
- [ ] TypeScript passes: `npm run typecheck`
- [ ] ESLint passes: `npm run lint`

#### Manual Verification:
- [ ] Session 1 displays real summary: "Crisis intake for recent breakup with passive SI, safety plan created"
- [ ] Summary text matches database exactly (check Supabase)
- [ ] Sessions 2-10 display mock summaries unchanged
- [ ] Demo token persists across page refreshes
- [ ] New browser/device creates new demo token
- [ ] API errors display "Error loading session summary" in Session 1 card
- [ ] No visual differences in card layout/styling
- [ ] Console shows clear logging for demo initialization steps

---

## Migration Notes

### Database
- No database changes required
- Uses existing `seed_demo_user_sessions()` SQL function
- Session 1 data already seeded with correct summary field

### Environment Variables
- No new environment variables required
- Uses existing `NEXT_PUBLIC_API_URL` from `.env.local`

### Backwards Compatibility
- Falls back to full mock mode if `USE_HYBRID_MODE = false`
- Falls back to mock Session 1 if API fetch fails
- No breaking changes to existing components

---

## References

### Backend Files
- Demo initialization: `backend/app/routers/demo.py:132-199`
- Demo auth middleware: `backend/app/middleware/demo_auth.py`
- Session seeding: `backend/supabase/seed_demo_data.sql:4-95`
- Session API: `backend/app/routers/sessions.py:138-154`

### Frontend Files
- Session Card component: `frontend/app/patient/components/SessionCard.tsx:410-438`
- Session type: `frontend/app/patient/lib/types.ts:67-87`
- Data hook: `frontend/app/patient/lib/usePatientSessions.ts:34-95`
- Mock data: `frontend/app/patient/lib/mockData.ts`
- API client: `frontend/lib/api-client.ts`

### API Endpoints
- `POST /api/demo/initialize` - Initialize demo user
- `GET /api/sessions/{session_id}` - Get session by ID
- `GET /api/sessions/patient/{patient_id}` - Get all patient sessions

### Critical Implementation Notes

1. **Import Paths:**
   - Use `@/lib/` for root-level lib imports (configured in tsconfig.json)
   - Use relative paths for app-level imports

2. **Type Safety:**
   - The `Session` type already has the `summary` field (line 82 in types.ts)
   - Backend returns different field names (snake_case) - transform to camelCase

3. **Error Handling:**
   - Always wrap API calls in try-catch
   - Log errors to console for debugging
   - Provide user-friendly fallback text

4. **localStorage SSR Safety:**
   - Always check `typeof window === 'undefined'` before accessing localStorage
   - Return null/default values on server-side

5. **Backend URL:**
   - Check `.env.local` for `NEXT_PUBLIC_API_URL`
   - Default: `http://localhost:8000`

6. **Testing Checklist:**
   - Clear localStorage before each test scenario
   - Check browser console for initialization logs
   - Verify demo token in localStorage (DevTools → Application → Local Storage)

---

## Next Steps After Completion

Once this implementation is complete and tested:

1. **Expand to More Fields:**
   - Fetch `mood_score` and map to `MoodType`
   - Fetch `topics[]` and display in card
   - Fetch `technique` and display as strategy

2. **Convert More Sessions:**
   - Fetch Sessions 2-5 from API
   - Eventually remove all mock data

3. **Add Real-Time Updates:**
   - Poll for new sessions after audio upload
   - Update cards when AI analysis completes

4. **Implement Full Authentication:**
   - Replace demo token with proper JWT auth
   - Add user signup/login flow
