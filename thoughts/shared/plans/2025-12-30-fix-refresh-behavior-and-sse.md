# Fix Refresh Behavior & SSE Reconnection Implementation Plan

## Overview

Fix the demo initialization and SSE connection flow so that:
- **Hard refresh (Cmd+Shift+R)**: Clears everything → New patient ID → New pipeline → Fresh start
- **Simple refresh (Cmd+R)**: Preserves patient ID → Reconnects SSE → Loads existing data (no new pipeline)
- Session cards show immediately with transcript available, "Analyzing..." for topics/mood until Wave 1 completes

## Current State Analysis

### What's Broken

1. **No localStorage persistence on first load**
   - User visits site → `page.tsx` checks localStorage → finds nothing → calls `demoApiClient.initialize()`
   - Patient ID is created but localStorage shows empty in DevTools
   - Root cause: Data is being stored but not persisted properly

2. **SSE connection fails**
   - `WaveCompletionBridge` polls for patient ID from localStorage
   - If patient ID doesn't exist or is wrong, SSE connects to empty/invalid endpoint
   - EventSource fails silently or times out

3. **30-second timeout error**
   - `usePatientSessions` calls `apiClient.getAllSessions()`
   - Request hangs for 30 seconds waiting for response
   - Likely cause: Backend waiting for something or CORS issue

4. **No differentiation between refresh types**
   - Both simple refresh (Cmd+R) and hard refresh (Cmd+Shift+R) behave the same
   - Both clear localStorage and restart pipeline
   - Need to detect hard refresh and preserve data on simple refresh

5. **Session cards don't show immediately**
   - Users see full loading screen until Wave 1 completes
   - Should show cards with transcript clickable, "Analyzing..." placeholders for topics/mood

### Current Flow (Broken)

```
User visits site
  ↓
page.tsx checks localStorage
  ↓
No token found → demoApiClient.initialize()
  ↓
Backend creates patient + sessions
  ↓
Returns: {demo_token, patient_id, session_ids}
  ↓
demoTokenStorage.store(...) called
  ↓
[BUG] localStorage not persisted?
  ↓
usePatientSessions tries to fetch sessions
  ↓
[BUG] Request times out after 30 seconds
  ↓
WaveCompletionBridge polls for patient ID
  ↓
[BUG] Patient ID not found in localStorage
  ↓
SSE connection fails or connects to wrong endpoint
```

## Desired End State

### Hard Refresh (Cmd+Shift+R) Flow

```
User presses Cmd+Shift+R
  ↓
Detect hard refresh via sessionStorage flag
  ↓
Clear ALL localStorage data (demo token, patient ID, session IDs)
  ↓
Reload page completely
  ↓
page.tsx detects no token → initialize new demo
  ↓
Backend creates NEW patient + sessions
  ↓
Store new credentials in localStorage
  ↓
Fetch sessions immediately (show cards with transcript, "Analyzing..." for topics)
  ↓
Connect SSE for real-time Wave 1/Wave 2 updates
  ↓
As Wave 1 completes per session → Update that card with topics/mood
  ↓
As Wave 2 completes per session → Update that card with deep analysis
```

### Simple Refresh (Cmd+R) Flow

```
User presses Cmd+R
  ↓
Detect simple refresh (no sessionStorage flag)
  ↓
PRESERVE localStorage data (keep existing patient ID)
  ↓
Reload page
  ↓
page.tsx detects existing token → redirect to dashboard
  ↓
Fetch sessions using existing patient ID (NO new pipeline)
  ↓
Show session cards immediately with whatever data exists
  ↓
Reconnect SSE to existing patient ID
  ↓
Continue listening for any in-progress Wave 1/Wave 2 updates
```

### Session Card Display Strategy

**Immediate display (no loading screen):**
- Show session card with date, duration, therapist name
- Transcript is clickable (available immediately from Step 1 of pipeline)
- Topics/mood show "Analyzing..." placeholder until Wave 1 completes
- Deep analysis shows "Processing..." placeholder until Wave 2 completes

**No 30-second timeout:**
- Sessions load quickly because transcript data exists after Step 1 (~2-3 seconds)
- Wave 1 analysis (topics/mood) takes ~60 seconds total (all sessions in parallel)
- Wave 2 analysis (deep insights) takes ~30 seconds total (all sessions sequential)

## What We're NOT Doing

- Not changing the backend pipeline (Steps 1/2/3 stay the same)
- Not changing how demo initialization works on backend
- Not implementing WebSocket (keeping SSE)
- Not adding authentication (staying demo-only for now)
- Not fixing Wave 2 "can only join an iterable" error (that's a separate bug)

## Implementation Approach

**Key Strategy:**
1. Add hard refresh detection using sessionStorage flag
2. Fix localStorage persistence issue in demo initialization
3. Fix SSE connection timing (wait for patient ID before connecting)
4. Add session pre-loading (show cards immediately with transcript available)
5. Add proper reconnection logic for simple refresh

---

## Phase 1: Add Hard Refresh Detection

### Overview
Detect whether user did hard refresh (Cmd+Shift+R) vs simple refresh (Cmd+R) using sessionStorage.

### Changes Required

#### 1.1 Create Refresh Detection Utility

**File**: `frontend/lib/refresh-detection.ts` (NEW)
**Changes**: Create new utility file

```typescript
/**
 * Refresh Detection Utility
 * Differentiates between hard refresh (Cmd+Shift+R) and simple refresh (Cmd+R)
 */

const HARD_REFRESH_FLAG = 'therapybridge_hard_refresh';

export const refreshDetection = {
  /**
   * Mark that a hard refresh should happen on next page load
   * Call this before window.location.reload(true) or in beforeunload handler
   */
  markHardRefresh() {
    if (typeof window === 'undefined') return;
    sessionStorage.setItem(HARD_REFRESH_FLAG, 'true');
  },

  /**
   * Check if current page load is from a hard refresh
   * Returns true if hard refresh, false if simple refresh
   */
  isHardRefresh(): boolean {
    if (typeof window === 'undefined') return false;

    const flag = sessionStorage.getItem(HARD_REFRESH_FLAG);

    // Clear flag after reading (one-time use)
    if (flag === 'true') {
      sessionStorage.removeItem(HARD_REFRESH_FLAG);
      return true;
    }

    return false;
  },

  /**
   * Detect if user pressed Cmd+Shift+R or Ctrl+Shift+R
   * Call this in a keydown event listener
   */
  isHardRefreshKeyCombo(event: KeyboardEvent): boolean {
    // Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)
    const isRefreshKey = event.key === 'r' || event.key === 'R';
    const hasModifier = event.metaKey || event.ctrlKey; // Cmd or Ctrl
    const hasShift = event.shiftKey;

    return isRefreshKey && hasModifier && hasShift;
  },

  /**
   * Alternative: Detect using performance.navigation.type
   * TYPE_RELOAD (1) = simple refresh
   * TYPE_NAVIGATE (0) = hard refresh or first visit
   *
   * Note: This is deprecated but still works in most browsers
   */
  isHardRefreshViaPerformance(): boolean {
    if (typeof window === 'undefined') return false;

    // Modern API
    if (window.performance && 'navigation' in window.performance) {
      const nav = (window.performance as any).navigation;
      // type === 'reload' means simple refresh
      // type === 'navigate' means hard refresh or first visit
      return nav.type === 'navigate';
    }

    // Fallback to deprecated API
    if (window.performance && 'navigation' in window.performance) {
      const navType = (window.performance as any).navigation.type;
      // TYPE_RELOAD = 1 (simple refresh)
      // TYPE_NAVIGATE = 0 (hard refresh or first visit)
      return navType === 0;
    }

    return false;
  }
};
```

#### 1.2 Add Global Keydown Listener

**File**: `frontend/app/layout.tsx`
**Changes**: Add keydown listener to detect Cmd+Shift+R

```typescript
'use client';

import { useEffect } from 'react';
import { refreshDetection } from '@/lib/refresh-detection';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Detect hard refresh keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (refreshDetection.isHardRefreshKeyCombo(event)) {
        console.log('[Hard Refresh] Detected Cmd+Shift+R - marking for hard refresh');
        refreshDetection.markHardRefresh();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
```

### Success Criteria

#### Automated Verification:
- [ ] New file compiles without TypeScript errors: `npm run typecheck`
- [ ] No linting errors: `npm run lint`

#### Manual Verification:
- [ ] Open browser DevTools → Console
- [ ] Press Cmd+R (simple refresh) → Console shows no hard refresh message
- [ ] Press Cmd+Shift+R (hard refresh) → Console shows "[Hard Refresh] Detected..." message
- [ ] Check sessionStorage → `therapybridge_hard_refresh` flag appears before page reloads
- [ ] After page loads → sessionStorage flag is cleared automatically

---

## Phase 2: Fix Demo Initialization & localStorage Persistence

### Overview
Fix the bug where localStorage is not being populated correctly during demo initialization. Ensure patient ID is stored reliably before SSE connection attempts.

### Changes Required

#### 2.1 Add Initialization State Tracking

**File**: `frontend/lib/demo-token-storage.ts`
**Changes**: Add initialization tracking and better error handling

```typescript
/**
 * Demo Token Storage Utility
 * Manages demo token lifecycle in localStorage
 */

const DEMO_TOKEN_KEY = 'therapybridge_demo_token';
const PATIENT_ID_KEY = 'therapybridge_patient_id';
const SESSION_IDS_KEY = 'therapybridge_session_ids';
const EXPIRES_AT_KEY = 'therapybridge_demo_expires';
const INIT_STATUS_KEY = 'therapybridge_init_status'; // NEW

export const demoTokenStorage = {
  /**
   * Store demo credentials after initialization
   */
  store(demoToken: string, patientId: string, sessionIds: string[], expiresAt: string) {
    if (typeof window === 'undefined') return;

    try {
      localStorage.setItem(DEMO_TOKEN_KEY, demoToken);
      localStorage.setItem(PATIENT_ID_KEY, patientId);
      localStorage.setItem(SESSION_IDS_KEY, JSON.stringify(sessionIds));
      localStorage.setItem(EXPIRES_AT_KEY, expiresAt);
      localStorage.setItem(INIT_STATUS_KEY, 'complete'); // NEW

      console.log('[Storage] ✓ Demo credentials stored:', { patientId, sessionCount: sessionIds.length });
    } catch (error) {
      console.error('[Storage] ✗ Failed to store credentials:', error);
      throw error; // Propagate error to caller
    }
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
      console.log('[Storage] Token expired, clearing...');
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
   * Check initialization status (NEW)
   * Returns: 'complete' | 'pending' | 'none'
   */
  getInitStatus(): 'complete' | 'pending' | 'none' {
    if (typeof window === 'undefined') return 'none';

    const status = localStorage.getItem(INIT_STATUS_KEY);
    if (status === 'complete') return 'complete';
    if (status === 'pending') return 'pending';
    return 'none';
  },

  /**
   * Mark initialization as pending (NEW)
   */
  markInitPending() {
    if (typeof window === 'undefined') return;
    localStorage.setItem(INIT_STATUS_KEY, 'pending');
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
    localStorage.removeItem(INIT_STATUS_KEY);

    console.log('[Storage] ✓ All demo data cleared');
  }
};
```

#### 2.2 Update Root Page with Hard Refresh Detection

**File**: `frontend/app/page.tsx`
**Changes**: Add hard refresh detection and better initialization flow

```typescript
'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { demoApiClient } from '@/lib/demo-api-client'
import { demoTokenStorage } from '@/lib/demo-token-storage'
import { refreshDetection } from '@/lib/refresh-detection'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    const initializeDemo = async () => {
      // STEP 1: Check if this is a hard refresh
      const isHardRefresh = refreshDetection.isHardRefresh();

      if (isHardRefresh) {
        console.log('🔥 Hard refresh detected - clearing all demo data');
        demoTokenStorage.clear();
      }

      // STEP 2: Check if demo token already exists
      const existingToken = demoTokenStorage.getToken();
      const existingPatientId = demoTokenStorage.getPatientId();

      if (existingToken && existingPatientId) {
        // Token exists and is valid - redirect to dashboard
        console.log('✅ Demo token exists, redirecting to dashboard');
        console.log('   Patient ID:', existingPatientId);
        router.push('/dashboard');
        return;
      }

      // STEP 3: Check if initialization is already in progress
      const initStatus = demoTokenStorage.getInitStatus();

      if (initStatus === 'pending') {
        console.log('⏳ Demo initialization already in progress, waiting...');
        // Wait for initialization to complete (polling)
        const checkInterval = setInterval(() => {
          if (demoTokenStorage.isInitialized()) {
            console.log('✅ Initialization complete, redirecting...');
            clearInterval(checkInterval);
            router.push('/dashboard');
          }
        }, 500);

        // Timeout after 10 seconds
        setTimeout(() => {
          clearInterval(checkInterval);
          console.error('❌ Initialization timeout - restarting');
          demoTokenStorage.clear();
          window.location.reload();
        }, 10000);

        return;
      }

      // STEP 4: No token exists - create new demo user
      console.log('🚀 Initializing new demo user...');
      demoTokenStorage.markInitPending();

      try {
        const result = await demoApiClient.initialize();

        if (result) {
          // Token is automatically stored in localStorage by demoApiClient
          console.log('✅ Demo initialized:', result);
          console.log('   Patient ID:', result.patient_id);
          console.log('   Session count:', result.session_ids.length);

          // Verify storage worked
          const storedPatientId = demoTokenStorage.getPatientId();
          if (!storedPatientId) {
            throw new Error('Failed to store patient ID in localStorage');
          }

          // Redirect to dashboard
          router.push('/dashboard');
        } else {
          throw new Error('Demo initialization returned null');
        }
      } catch (err) {
        console.error('❌ Demo initialization error:', err);
        demoTokenStorage.clear();

        // Show error to user
        alert('Failed to initialize demo. Please refresh the page.');
      }
    }

    initializeDemo()
  }, [router])

  // Loading screen while initializing - matches dashboard aesthetic
  return (
    <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] transition-colors duration-300 flex items-center justify-center">
      <div className="text-center">
        <div className="mb-4">
          <svg className="animate-spin h-12 w-12 text-gray-700 dark:text-gray-300 mx-auto" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
        <h2 className="text-xl font-light text-gray-900 dark:text-gray-100 mb-2" style={{ fontFamily: 'system-ui' }}>
          Loading TherapyBridge
        </h2>
        <p className="text-sm font-light text-gray-600 dark:text-gray-400" style={{ fontFamily: 'system-ui' }}>
          Preparing your experience...
        </p>
      </div>
    </div>
  )
}
```

### Success Criteria

#### Automated Verification:
- [ ] TypeScript compiles without errors: `npm run typecheck`
- [ ] No linting errors: `npm run lint`

#### Manual Verification:
- [ ] Hard refresh (Cmd+Shift+R) → localStorage is cleared → Console shows "Hard refresh detected"
- [ ] Simple refresh (Cmd+R) → localStorage is preserved → Console shows "Demo token exists"
- [ ] First visit → Demo initializes → Patient ID appears in localStorage
- [ ] Check DevTools → Application → Local Storage → All 5 keys populated:
  - `therapybridge_demo_token`
  - `therapybridge_patient_id`
  - `therapybridge_session_ids`
  - `therapybridge_demo_expires`
  - `therapybridge_init_status`

---

## Phase 3: Fix SSE Connection Timing & Reconnection

### Overview
Ensure SSE connection only attempts after patient ID is confirmed in localStorage. Add proper reconnection logic for simple refresh.

### Changes Required

#### 3.1 Update WaveCompletionBridge with Better Patient ID Detection

**File**: `frontend/app/patient/components/WaveCompletionBridge.tsx`
**Changes**: Wait for patient ID confirmation before SSE connection

```typescript
"use client";

/**
 * WaveCompletionBridge - SSE-based Real-Time Updates
 *
 * Connects to SSE endpoint and triggers per-session updates as they complete.
 *
 * Behavior:
 *   - Waits for patient ID to exist in localStorage before connecting
 *   - Connects to SSE stream on mount
 *   - When Wave 1 completes for a session: triggers loading state + refresh for that session
 *   - When Wave 2 completes for a session: triggers loading state + refresh for that session
 *   - Disconnects when all analysis complete
 *   - Automatically reconnects on simple refresh (preserves patient ID)
 */

import { useEffect, useState } from "react";
import { useSessionData } from "../contexts/SessionDataContext";
import { usePipelineEvents } from "@/hooks/use-pipeline-events";
import { demoTokenStorage } from "@/lib/demo-token-storage";

export function WaveCompletionBridge() {
  const { refresh, setSessionLoading } = useSessionData();
  const [patientId, setPatientId] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);

  // Get patient ID from localStorage (populated by demo initialization)
  useEffect(() => {
    let attempts = 0;
    const maxAttempts = 40; // 20 seconds max wait (40 * 500ms)

    const checkPatientId = () => {
      attempts++;

      const id = demoTokenStorage.getPatientId();
      const initStatus = demoTokenStorage.getInitStatus();

      if (id && id !== patientId) {
        console.log('[WaveCompletionBridge] ✓ Patient ID found:', id);
        setPatientId(id);
        setIsReady(true);
        return true; // Stop polling
      }

      // Check if initialization failed
      if (initStatus === 'none' && attempts > 10) {
        console.error('[WaveCompletionBridge] ✗ No patient ID after 5 seconds - initialization may have failed');
        return false; // Keep polling
      }

      // Timeout after 20 seconds
      if (attempts >= maxAttempts) {
        console.error('[WaveCompletionBridge] ✗ Timeout waiting for patient ID');
        setIsReady(false);
        return true; // Stop polling
      }

      return false; // Continue polling
    };

    // Check immediately
    if (checkPatientId()) {
      return;
    }

    // Poll every 500ms until we have a patient ID or timeout
    const interval = setInterval(() => {
      if (checkPatientId()) {
        clearInterval(interval);
      }
    }, 500);

    return () => clearInterval(interval);
  }, [patientId]);

  // Connect to SSE and handle events (only after we have patient ID)
  const { isConnected, events } = usePipelineEvents({
    patientId: patientId || "",
    enabled: isReady && !!patientId,

    onWave1SessionComplete: async (sessionId, sessionDate) => {
      console.log(
        `🔄 Wave 1 complete for ${sessionDate}! Showing loading state...`
      );

      // Show loading overlay on this session card
      setSessionLoading(sessionId, true);

      // Small delay to ensure loading state is visible
      await new Promise(resolve => setTimeout(resolve, 100));

      // Refresh data to get mood/topics
      await refresh();

      // Hide loading overlay
      setSessionLoading(sessionId, false);
    },

    onWave2SessionComplete: async (sessionId, sessionDate) => {
      console.log(
        `🔄 Wave 2 complete for ${sessionDate}! Showing loading state...`
      );

      // Show loading overlay on this session card
      setSessionLoading(sessionId, true);

      // Small delay to ensure loading state is visible
      await new Promise(resolve => setTimeout(resolve, 100));

      // Refresh data to get deep analysis
      await refresh();

      // Hide loading overlay
      setSessionLoading(sessionId, false);
    },
  });

  // Log connection status
  useEffect(() => {
    if (isConnected && patientId) {
      console.log(`📡 SSE connected to patient ${patientId} - listening for pipeline events`);
    }
  }, [isConnected, patientId]);

  // Log events for debugging
  useEffect(() => {
    if (events.length > 0) {
      const latest = events[events.length - 1];
      console.log(
        `[${latest.phase}] ${latest.session_date || "N/A"} - ${latest.event}`,
        latest.details || ""
      );
    }
  }, [events]);

  return null;
}
```

#### 3.2 Update usePipelineEvents Hook with Better Error Handling

**File**: `frontend/hooks/use-pipeline-events.ts`
**Changes**: Add connection state tracking and better error handling

```typescript
"use client";

import { useEffect, useState, useCallback, useRef } from "react";

interface PipelineEvent {
  timestamp: string;
  patient_id: string;
  phase: "TRANSCRIPT" | "WAVE1" | "WAVE2";
  event: string;
  status: string;
  session_id?: string;
  session_date?: string;
  duration_ms?: number;
  details?: Record<string, any>;
}

interface UsePipelineEventsOptions {
  patientId: string;
  enabled?: boolean;
  onEvent?: (event: PipelineEvent) => void;
  onWave1SessionComplete?: (sessionId: string, sessionDate: string) => void;
  onWave2SessionComplete?: (sessionId: string, sessionDate: string) => void;
}

export function usePipelineEvents(options: UsePipelineEventsOptions) {
  const {
    patientId,
    enabled = true,
    onEvent,
    onWave1SessionComplete,
    onWave2SessionComplete,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);
  const handleEventRef = useRef<((event: PipelineEvent) => void) | null>(null);

  const handleEvent = useCallback(
    (event: PipelineEvent) => {
      // Add to events list
      setEvents((prev) => [...prev, event]);

      // Call custom event handler
      if (onEvent) {
        onEvent(event);
      }

      // Detect Wave 1 session completion
      if (
        event.phase === "WAVE1" &&
        event.event === "COMPLETE" &&
        event.status === "success" &&
        event.session_id &&
        event.session_date
      ) {
        console.log(
          `✅ Wave 1 complete for session ${event.session_date} (${event.session_id})`
        );
        if (onWave1SessionComplete) {
          onWave1SessionComplete(event.session_id, event.session_date);
        }
      }

      // Detect Wave 2 session completion
      if (
        event.phase === "WAVE2" &&
        event.event === "COMPLETE" &&
        event.status === "success" &&
        event.session_id &&
        event.session_date
      ) {
        console.log(
          `✅ Wave 2 complete for session ${event.session_date} (${event.session_id})`
        );
        if (onWave2SessionComplete) {
          onWave2SessionComplete(event.session_id, event.session_date);
        }
      }
    },
    [onEvent, onWave1SessionComplete, onWave2SessionComplete]
  );

  // Update ref when handleEvent changes
  useEffect(() => {
    handleEventRef.current = handleEvent;
  }, [handleEvent]);

  useEffect(() => {
    if (!enabled || !patientId) {
      console.log('[SSE] Connection disabled or no patient ID');
      return;
    }

    console.log(`[SSE] Connecting to patient ${patientId}...`);

    // Create EventSource connection
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const sseUrl = `${apiUrl}/api/sse/events/${patientId}`;

    console.log(`[SSE] URL: ${sseUrl}`);

    const eventSource = new EventSource(sseUrl);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log("📡 SSE connected - listening for pipeline events");
      setIsConnected(true);
      setConnectionError(null);
    };

    eventSource.onmessage = (messageEvent) => {
      try {
        const event: PipelineEvent = JSON.parse(messageEvent.data);

        // Ignore initial "connected" event
        if (event.event === 'connected') {
          console.log('[SSE] ✓ Connection confirmed by server');
          return;
        }

        // Use ref to avoid stale closure
        if (handleEventRef.current) {
          handleEventRef.current(event);
        }
      } catch (error) {
        console.error("[SSE] Failed to parse event:", error);
        console.error("[SSE] Raw data:", messageEvent.data);
      }
    };

    eventSource.onerror = (error) => {
      console.error("[SSE] Connection error:", error);
      setIsConnected(false);

      // Check readyState to determine error type
      if (eventSource.readyState === EventSource.CLOSED) {
        setConnectionError('Connection closed by server');
      } else if (eventSource.readyState === EventSource.CONNECTING) {
        setConnectionError('Reconnecting...');
      } else {
        setConnectionError('Connection failed');
      }

      // Browser will automatically attempt to reconnect
      console.log(`[SSE] Browser will attempt reconnection (readyState: ${eventSource.readyState})`);
    };

    // Cleanup on unmount
    return () => {
      console.log("📡 SSE disconnected");
      eventSource.close();
      setIsConnected(false);
      setConnectionError(null);
    };
  }, [enabled, patientId]);

  return {
    isConnected,
    connectionError,
    events,
    latestEvent: events[events.length - 1] || null,
  };
}
```

### Success Criteria

#### Automated Verification:
- [ ] TypeScript compiles: `npm run typecheck`
- [ ] No linting errors: `npm run lint`

#### Manual Verification:
- [ ] Fresh page load → Console shows "Patient ID found" → SSE connects within 1-2 seconds
- [ ] Check Network tab → `/api/sse/events/{patient_id}` request shows status 200, type "eventsource"
- [ ] Console shows "SSE connected - listening for pipeline events"
- [ ] Simple refresh (Cmd+R) → SSE reconnects to same patient ID automatically
- [ ] Hard refresh (Cmd+Shift+R) → New patient ID → SSE connects to new patient ID

---

## Phase 4: Show Session Cards Immediately with "Analyzing..." Placeholders

### Overview
Display session cards as soon as Step 1 completes (transcripts populated, ~2-3 seconds). Show "Analyzing..." for topics/mood until Wave 1 completes. Show transcript immediately when card is clicked.

### Changes Required

#### 4.1 Update usePatientSessions Hook - Remove Blocking Behavior

**File**: `frontend/app/patient/lib/usePatientSessions.ts`
**Changes**: Fetch sessions immediately, don't wait for Wave 1 completion

```typescript
'use client';

/**
 * Patient Sessions Hook for Dashboard-v3 (FULLY DYNAMIC)
 *
 * Fetches ALL sessions dynamically from backend API.
 * Shows sessions immediately with transcript available.
 * "Analyzing..." placeholders for topics/mood until Wave 1 completes.
 *
 * Phase 4 Implementation: Removed all mock data, fully dynamic loading
 */

import { useState, useEffect, useRef } from 'react';
import {
  tasks as mockTasks,
  timelineData as mockTimeline,
  unifiedTimeline as mockUnifiedTimeline,
  majorEvents as mockMajorEvents,
} from './mockData';
import { Session, Task, TimelineEntry, TimelineEvent, MajorEventEntry, MoodType } from './types';
import { apiClient } from '@/lib/api-client';
import { demoTokenStorage } from '@/lib/demo-token-storage';
import { demoApiClient } from '@/lib/demo-api-client';

export function usePatientSessions() {
  const [isLoading, setIsLoading] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [unifiedTimeline, setUnifiedTimeline] = useState<TimelineEvent[]>([]);
  const [majorEvents, setMajorEvents] = useState<MajorEventEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<string>('pending');
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const loadAllSessions = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Step 1: Check if demo is already initialized
        if (!demoTokenStorage.isInitialized()) {
          console.log('[Sessions] Demo not initialized - waiting...');

          // Wait for initialization to complete (polling)
          let attempts = 0;
          const maxAttempts = 40; // 20 seconds max

          while (!demoTokenStorage.isInitialized() && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 500));
            attempts++;
          }

          if (!demoTokenStorage.isInitialized()) {
            throw new Error('Demo initialization timeout - please refresh the page');
          }

          console.log('[Sessions] ✓ Demo initialized, proceeding...');
        }

        // Step 2: Fetch ALL sessions from API
        // Sessions will have transcript data immediately after Step 1 completes (~2-3 seconds)
        // Topics/mood will be null until Wave 1 completes (~60 seconds)
        console.log('[Sessions] Fetching all sessions from API...');
        const result = await apiClient.getAllSessions();

        if (!result.success || !result.data) {
          throw new Error(result.error || 'Failed to fetch sessions');
        }

        // Store backend data for sorting reference
        const backendSessions = result.data;

        // Step 3: Transform ALL backend sessions to frontend Session type
        const transformedSessions: Session[] = backendSessions.map((backendSession) => {
          const sessionDate = new Date(backendSession.session_date);

          return {
            id: backendSession.id,
            date: sessionDate.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            }), // "Jan 10"
            duration: `${backendSession.duration_minutes || 60} min`,
            therapist: 'Dr. Rodriguez',
            mood: mapMoodScore(backendSession.mood_score), // null → 'neutral' with "Analyzing..." display
            topics: backendSession.topics || [], // [] → "Analyzing..." display
            strategy: backendSession.technique || null, // null → "Analyzing..." display
            actions: backendSession.action_items || [],
            summary: backendSession.summary || null, // null → "Summary not yet generated" display
            transcript: backendSession.transcript || [],
            extraction_confidence: backendSession.extraction_confidence,
            topics_extracted_at: backendSession.topics_extracted_at,
          };
        });

        // Step 4: Sort by date (newest first)
        const sortedSessions = transformedSessions.sort((a, b) => {
          const dateA = backendSessions.find(s => s.id === a.id)?.session_date;
          const dateB = backendSessions.find(s => s.id === b.id)?.session_date;
          if (!dateA || !dateB) return 0;
          return new Date(dateB).getTime() - new Date(dateA).getTime();
        });

        console.log('[Sessions] ✓ Loaded:', sortedSessions.length, 'sessions');
        console.log('[Sessions] ✓ Date range:', sortedSessions[sortedSessions.length - 1]?.date, '→', sortedSessions[0]?.date);

        // Count how many have topics/mood already
        const analyzedCount = sortedSessions.filter(s => s.topics.length > 0).length;
        console.log(`[Sessions] ✓ Analyzed: ${analyzedCount}/${sortedSessions.length} sessions have Wave 1 data`);

        setSessions(sortedSessions);
        setTasks(mockTasks);
        setTimeline(mockTimeline);
        setUnifiedTimeline(mockUnifiedTimeline);
        setMajorEvents(mockMajorEvents);

      } catch (err) {
        console.error('[usePatientSessions] Error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load sessions');
        setSessions([]); // Empty state on error
      } finally {
        setIsLoading(false);
      }
    };

    loadAllSessions();
  }, []);

  // Polling effect: Auto-refresh sessions while analysis is in progress
  useEffect(() => {
    // Only poll if we have incomplete analysis
    const shouldPoll = analysisStatus === 'pending' || analysisStatus === 'processing';

    if (shouldPoll && demoTokenStorage.isInitialized()) {
      console.log('[Polling] Starting analysis status polling (5s interval)...');

      pollingIntervalRef.current = setInterval(async () => {
        try {
          // Check demo status
          const status = await demoApiClient.getStatus();

          if (!status) {
            return; // Failed to fetch, try again next interval
          }

          console.log('[Polling] Analysis status:', {
            status: status.analysis_status,
            wave1: status.wave1_complete,
            wave2: status.wave2_complete,
            total: status.session_count
          });

          setAnalysisStatus(status.analysis_status);

          // If analysis status changed, refresh sessions to show new data
          const hasNewData = status.wave1_complete > 0 || status.wave2_complete > 0;
          if (hasNewData) {
            console.log('[Polling] New analysis data detected, refreshing sessions...');
            refresh();
          }

          // Stop polling if fully complete
          if (status.analysis_status === 'wave2_complete') {
            console.log('[Polling] Analysis complete! Stopping polling.');
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
          }
        } catch (err) {
          console.error('[Polling] Error checking status:', err);
        }
      }, 5000); // Poll every 5 seconds

      return () => {
        if (pollingIntervalRef.current) {
          console.log('[Polling] Cleaning up polling interval');
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      };
    }
  }, [analysisStatus]);

  // Manual refresh function - reloads from API
  const refresh = () => {
    setIsLoading(true);
    setTimeout(async () => {
      try {
        const result = await apiClient.getAllSessions();
        if (result.success && result.data) {
          const transformed = result.data.map((backendSession) => {
            const sessionDate = new Date(backendSession.session_date);
            return {
              id: backendSession.id,
              date: sessionDate.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
              }),
              rawDate: sessionDate,
              duration: `${backendSession.duration_minutes || 60} min`,
              therapist: 'Dr. Rodriguez',
              mood: mapMoodScore(backendSession.mood_score),
              topics: backendSession.topics || [],
              strategy: backendSession.technique || null,
              actions: backendSession.action_items || [],
              summary: backendSession.summary || null,
              transcript: backendSession.transcript || [],
              extraction_confidence: backendSession.extraction_confidence,
              topics_extracted_at: backendSession.topics_extracted_at,
            };
          });
          setSessions(transformed);
        }
      } catch (err) {
        console.error('[refresh] Error:', err);
      } finally {
        setIsLoading(false);
      }
    }, 300);
  };

  // Update a major event's reflection
  const updateMajorEventReflection = (eventId: string, reflection: string) => {
    setMajorEvents(prev =>
      prev.map(e => e.id === eventId ? { ...e, reflection } : e)
    );
    setUnifiedTimeline(prev =>
      prev.map(e =>
        e.eventType === 'major_event' && e.id === eventId
          ? { ...e, reflection }
          : e
      )
    );
  };

  return {
    sessions,
    tasks,
    timeline,
    unifiedTimeline,
    majorEvents,
    isLoading,
    isError: error !== null,
    error,
    refresh,
    updateMajorEventReflection,
    sessionCount: sessions.length,
    majorEventCount: majorEvents.length,
    isEmpty: !isLoading && sessions.length === 0,
  };
}

/**
 * Helper function to map mood_score (0-10) to MoodType ('positive' | 'neutral' | 'low')
 */
function mapMoodScore(score: number | null | undefined): MoodType {
  if (score === null || score === undefined) return 'neutral';
  if (score >= 7) return 'positive';
  if (score >= 4) return 'neutral';
  return 'low';
}
```

#### 4.2 Update SessionCard to Show "Analyzing..." Placeholders

**File**: `frontend/app/patient/components/SessionCard.tsx`
**Changes**: Add "Analyzing..." placeholders for topics/strategy when null

Find the section that renders topics and strategy, and update it:

```typescript
{/* Topics & Strategy Grid */}
<div className="grid grid-cols-2 gap-3 mb-3">
  {/* Topics */}
  <div className="min-w-0">
    <h4 className="text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1.5 font-light">
      Topics
    </h4>
    {session.topics && session.topics.length > 0 ? (
      <div className="space-y-0.5">
        {session.topics.map((topic, i) => (
          <p key={i} className="text-sm font-light text-gray-700 dark:text-gray-200 break-words">
            • {topic}
          </p>
        ))}
      </div>
    ) : (
      <p className="text-sm font-light text-gray-400 dark:text-gray-500 italic">
        Analyzing...
      </p>
    )}
  </div>

  {/* Strategy */}
  <div className="min-w-0">
    <h4 className="text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400 mb-1.5 font-light">
      Strategy
    </h4>
    {session.strategy ? (
      <p className="text-sm font-light text-gray-700 dark:text-gray-200 break-words">
        {session.strategy}
      </p>
    ) : (
      <p className="text-sm font-light text-gray-400 dark:text-gray-500 italic">
        Analyzing...
      </p>
    )}
  </div>
</div>
```

Also update the mood indicator to show "Analyzing..." when mood is unknown:

```typescript
{/* Mood Indicator */}
<div className="flex items-center gap-2">
  {session.mood === 'neutral' && (!session.topics || session.topics.length === 0) ? (
    <>
      <div className="w-2 h-2 rounded-full bg-gray-400 dark:bg-gray-500" />
      <span className="text-sm font-light text-gray-400 dark:text-gray-500 italic">
        Analyzing mood...
      </span>
    </>
  ) : (
    <>
      <div
        className={`w-2 h-2 rounded-full ${
          session.mood === 'positive'
            ? 'bg-green-500'
            : session.mood === 'low'
            ? 'bg-rose-400'
            : 'bg-blue-400'
        }`}
      />
      <span className="text-sm font-light text-gray-700 dark:text-gray-200">
        {session.mood === 'positive' ? 'Positive' : session.mood === 'low' ? 'Challenging' : 'Neutral'}
      </span>
    </>
  )}
</div>
```

### Success Criteria

#### Automated Verification:
- [ ] TypeScript compiles: `npm run typecheck`
- [ ] No linting errors: `npm run lint`

#### Manual Verification:
- [ ] Open fresh browser (hard refresh or incognito)
- [ ] Page loads → Within 3-5 seconds, session cards appear
- [ ] Session cards show:
  - ✓ Date (e.g., "Jan 10")
  - ✓ Duration (e.g., "60 min")
  - ✓ Therapist name ("Dr. Rodriguez")
  - ✓ Mood shows "Analyzing mood..." (gray dot)
  - ✓ Topics shows "Analyzing..." (italic gray text)
  - ✓ Strategy shows "Analyzing..." (italic gray text)
- [ ] Click on session card → Transcript viewer opens with full transcript visible
- [ ] Wait ~60 seconds → Session cards update with topics/mood/strategy (Wave 1 complete)
- [ ] Console shows "[WAVE1] 2025-01-10 - COMPLETE" messages as each session finishes

---

## Phase 5: Final Integration & Testing

### Overview
Test the complete flow with both hard refresh and simple refresh. Verify SSE reconnection, session card updates, and no timeout errors.

### Changes Required

#### 5.1 Add Debug Logging to Track Full Flow

**File**: `frontend/lib/api-client.ts`
**Changes**: Add request/response logging for debugging

Find the `getAllSessions` method and add logging:

```typescript
async getAllSessions(): Promise<ApiResponse<BackendSession[]>> {
  console.log('[API] → GET /api/sessions (all sessions)');
  const startTime = Date.now();

  const response = await this.get<BackendSession[]>('/api/sessions');

  const duration = Date.now() - startTime;
  console.log(`[API] ← GET /api/sessions completed in ${duration}ms`, {
    success: response.success,
    sessionCount: response.data?.length,
    error: response.error
  });

  return response;
}
```

#### 5.2 Add Performance Monitoring to SessionDataContext

**File**: `frontend/app/patient/contexts/SessionDataContext.tsx`
**Changes**: Add timing metrics for data loading

Add performance logging in the provider:

```typescript
useEffect(() => {
  console.log('[SessionDataContext] Initialization started');
  const initStart = Date.now();

  // ... existing initialization code ...

  const initDuration = Date.now() - initStart;
  console.log(`[SessionDataContext] ✓ Initialized in ${initDuration}ms`);
}, []);
```

### Success Criteria

#### Automated Verification:
- [ ] All TypeScript compiles: `npm run typecheck`
- [ ] All linting passes: `npm run lint`
- [ ] Build completes successfully: `npm run build`

#### Manual Verification - First Visit (Hard Refresh Simulation):
- [ ] Open browser in incognito mode
- [ ] Visit `http://localhost:3000`
- [ ] Within 3 seconds: Loading screen shows "Loading TherapyBridge"
- [ ] Within 5 seconds: Dashboard appears with session cards
- [ ] Session cards show "Analyzing..." for topics/mood/strategy
- [ ] Click session card → Transcript viewer opens with full conversation
- [ ] Console shows: `[Demo] ✓ Initialized: {patient_id, sessionCount: 10}`
- [ ] Console shows: `[Sessions] ✓ Loaded: 10 sessions`
- [ ] Console shows: `📡 SSE connected - listening for pipeline events`
- [ ] After ~60 seconds: Session cards update with topics/mood (Wave 1 complete)
- [ ] Console shows: `✅ Wave 1 complete for session ...` (10 times)
- [ ] After ~90 seconds: Session cards update with deep analysis (Wave 2 complete)
- [ ] Console shows: `✅ Wave 2 complete for session ...` (10 times)
- [ ] No errors in console
- [ ] No "Request timeout after 30000ms" errors

#### Manual Verification - Simple Refresh (Cmd+R):
- [ ] After first visit completes, press `Cmd+R` (simple refresh)
- [ ] Page reloads
- [ ] Console shows: `✅ Demo token exists, redirecting to dashboard`
- [ ] Dashboard loads immediately (no 5-second delay)
- [ ] Session cards show immediately with all analyzed data (topics/mood/strategy)
- [ ] SSE reconnects: Console shows `📡 SSE connected to patient {id}`
- [ ] No new pipeline starts (no "Analyzing..." placeholders)
- [ ] localStorage preserved: Check DevTools → All 5 keys still populated

#### Manual Verification - Hard Refresh (Cmd+Shift+R):
- [ ] After simple refresh, press `Cmd+Shift+R` (hard refresh)
- [ ] Console shows: `🔥 Hard refresh detected - clearing all demo data`
- [ ] Page reloads completely
- [ ] localStorage cleared: Check DevTools → All keys removed
- [ ] New demo initialization starts
- [ ] New patient ID created (different from previous)
- [ ] Session cards show "Analyzing..." again
- [ ] New SSE connection to new patient ID
- [ ] Wave 1 & Wave 2 analysis starts from scratch

#### Performance Verification:
- [ ] Time to first session cards: < 5 seconds
- [ ] Time to Wave 1 completion: < 90 seconds
- [ ] Time to Wave 2 completion: < 120 seconds
- [ ] SSE reconnection on simple refresh: < 2 seconds
- [ ] No memory leaks (check DevTools → Memory tab)

---

## Testing Strategy

### Unit Tests

Not applicable - this is primarily integration work. All verification is manual via browser testing.

### Integration Tests

Manual browser testing covers:
- Demo initialization flow
- localStorage persistence
- SSE connection lifecycle
- Session card rendering with placeholders
- Hard vs simple refresh differentiation

### Manual Testing Steps

1. **Fresh Install Test**:
   - Clear all browser data
   - Visit site
   - Verify initialization completes
   - Verify session cards appear with "Analyzing..."
   - Wait for Wave 1/Wave 2 completion
   - Verify cards update with real data

2. **Simple Refresh Test**:
   - Press Cmd+R
   - Verify data persists
   - Verify no new pipeline starts
   - Verify SSE reconnects

3. **Hard Refresh Test**:
   - Press Cmd+Shift+R
   - Verify data clears
   - Verify new pipeline starts
   - Verify new patient ID created

4. **Error Recovery Test**:
   - Kill backend server during initialization
   - Verify error message shows
   - Restart backend
   - Refresh page
   - Verify recovery

5. **SSE Reconnection Test**:
   - Kill backend during Wave 1
   - Verify SSE disconnects
   - Restart backend
   - Verify SSE reconnects automatically
   - Verify Wave 1 continues

## Performance Considerations

- **localStorage access**: Fast (synchronous), no performance impact
- **SSE connection**: Persistent, low bandwidth (~1KB per event)
- **Polling fallback**: 5-second interval, negligible CPU usage
- **Session card rendering**: 10 cards, minimal DOM nodes, fast render

## Migration Notes

No database migrations needed - all changes are frontend-only.

## References

- Original issue: Browser refresh behavior inconsistent
- Related research: SSE connection timing issues
- Similar implementation: N/A (new feature)
