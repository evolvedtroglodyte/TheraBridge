# Hard Refresh SSE Race Condition Fix - Implementation Plan

## Overview

Fix critical race condition on hard refresh where SSE attempts to connect with stale patient ID before localStorage is cleared, causing CORS/404 errors and preventing proper demo reinitialization.

**Root Cause:** Hard refresh detection clears localStorage and redirects to home, but SSE hook mounts with cached patient ID from React state before redirect completes, attempting connection to non-existent patient.

**User Requirements:**
1. Use robust solution (Option C): Make SSE reactive to patient ID changes
2. Remove hard refresh redirect (keep in-place, just clear localStorage)
3. Add comprehensive SSE error handling (distinguish 404 from CORS issues)
4. Remove `/auth/login` redirects from demo mode

## Current State Analysis

### Key Discoveries:

**Backend is Healthy:**
- Railway logs show successful Wave 1 + Wave 2 analysis completion
- Backend processing patient `66dde9b6-b222-46f3-b1e7-817962824f65` successfully
- All API endpoints responding (OpenAI calls working, DB updates successful)

**Frontend Race Condition:**
```
03:03:40.832 [WaveCompletionBridge] ✓ Patient ID found: 6caf6913-f0e3-468e-9aae-2d7bbf2236c6  ← OLD PATIENT
03:03:40.834 🔥 Hard refresh detected - clearing demo data and redirecting to home
03:03:40.846 [SSE] Connecting to patient 6caf6913-f0e3-468e-9aae-2d7bbf2236c6  ← WRONG PATIENT!
03:03:40.973 Cross-Origin Request Blocked: CORS request did not succeed  ← 404 masquerading as CORS
```

**Problem Files:**
- `frontend/hooks/use-pipeline-events.ts:157` - SSE hook doesn't handle patient ID changes
- `frontend/app/sessions/page.tsx:26-30` - Hard refresh redirects instead of handling in-place
- `frontend/app/patient/components/WaveCompletionBridge.tsx:74` - Patient ID polling doesn't restart on change
- `frontend/lib/api-client.ts:261,275` - Redirects to non-existent `/auth/login` in demo mode

## Desired End State

### Success Criteria:

**Hard Refresh Behavior:**
- ✅ Hard refresh clears localStorage immediately
- ✅ Page stays on `/sessions` (no redirect)
- ✅ SSE disconnects from old patient ID
- ✅ WaveCompletionBridge detects cleared patient ID
- ✅ User sees "Initializing demo..." message on same page
- ✅ After demo init completes, sessions load automatically

**SSE Error Handling:**
- ✅ Distinguish 404 (patient not found) from CORS errors
- ✅ Log clear error messages for debugging
- ✅ Automatically disconnect on 404/403
- ✅ Handle patient ID changes gracefully

**Demo Mode:**
- ✅ No redirects to `/auth/login` (page doesn't exist)
- ✅ Token refresh failures clear demo data and show error message
- ✅ Clear user feedback when demo initialization fails

### Verification:

**Automated Verification:**
- [ ] TypeScript compilation passes: `cd frontend && npm run build`
- [ ] ESLint passes: `cd frontend && npm run lint`
- [ ] No console errors on page load
- [ ] Demo initialization completes within 120 seconds

**Manual Verification:**
- [ ] Simple refresh (Cmd+R): SSE reconnects automatically, same patient ID preserved
- [ ] Hard refresh (Cmd+Shift+R): localStorage cleared, page stays on `/sessions`, new patient ID initialized
- [ ] SSE connection logs show correct patient ID after hard refresh
- [ ] No "CORS request did not succeed" errors in console
- [ ] Error messages are clear and actionable (not generic "NetworkError")
- [ ] No redirects to `/auth/login` in any scenario

## What We're NOT Doing

- NOT adding authentication system (out of scope)
- NOT creating `/auth/login` page (demo mode only)
- NOT implementing SSE reconnection backoff (browser handles this)
- NOT adding SSE message persistence (events are ephemeral)
- NOT changing backend SSE endpoint (backend is working correctly)

## Implementation Approach

**Strategy:** Fix the race condition at multiple levels for maximum robustness:

1. **SSE Hook Reactivity** - Disconnect and reconnect when patient ID changes
2. **Hard Refresh In-Place** - Clear data without redirect, show loading state
3. **Error Handling** - Distinguish 404 from CORS, log actionable errors
4. **Demo Mode Cleanup** - Remove redirects to non-existent auth pages

**Phased Approach:** Each phase is independently testable and adds incremental safety.

---

## Phase 1: Fix SSE Patient ID Reactivity

### Overview
Make SSE hook properly handle patient ID changes by disconnecting old connection and establishing new one. This prevents stale patient ID connections.

### Changes Required:

#### 1.1 Update SSE Hook to Handle Patient ID Changes

**File**: `frontend/hooks/use-pipeline-events.ts`

**Changes**: Add patient ID change detection and cleanup

**Current problematic code (line 90-157):**
```typescript
useEffect(() => {
  if (!enabled || !patientId) {
    console.log('[SSE] Connection disabled or no patient ID');
    return;
  }

  console.log(`[SSE] Connecting to patient ${patientId}...`);
  // ... creates EventSource without checking if patient ID changed

  return () => {
    console.log("📡 SSE disconnected");
    eventSource.close();
  };
}, [enabled, patientId]);  // ← Dependency array includes patientId but doesn't handle cleanup properly
```

**Problem:** When `patientId` changes, the cleanup runs but React may have already read the OLD patient ID from memory before localStorage was cleared.

**New code:**
```typescript
useEffect(() => {
  if (!enabled || !patientId) {
    console.log('[SSE] Connection disabled or no patient ID');

    // Clean up existing connection if patient ID was cleared
    if (eventSourceRef.current) {
      console.log('[SSE] Patient ID cleared - disconnecting existing SSE');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
      setConnectionError(null);
    }
    return;
  }

  // Check if this is a patient ID change (not initial mount)
  const previousPatientId = eventSourceRef.current?.url.split('/').pop();
  if (previousPatientId && previousPatientId !== patientId) {
    console.log(`[SSE] Patient ID changed: ${previousPatientId} → ${patientId}`);
    console.log('[SSE] Disconnecting from old patient...');
    eventSourceRef.current.close();
    eventSourceRef.current = null;
    setIsConnected(false);
    setConnectionError(null);
  }

  console.log(`[SSE] Connecting to patient ${patientId}...`);

  // Create EventSource connection
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const sseUrl = `${apiUrl}/api/sse/events/${patientId}`;

  console.log(`[SSE] URL: ${sseUrl}`);

  const eventSource = new EventSource(sseUrl);
  eventSourceRef.current = eventSource;

  eventSource.onopen = () => {
    console.log(`📡 SSE connected to patient ${patientId}`);
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

    // Check readyState to determine error type
    const readyState = eventSource.readyState;

    if (readyState === EventSource.CLOSED) {
      console.error(`[SSE] ✗ Connection closed by server (patient ${patientId} may not exist)`);
      setConnectionError('Patient not found (404) or forbidden (403)');
      setIsConnected(false);

      // Close connection permanently for 404/403
      eventSource.close();
      eventSourceRef.current = null;
    } else if (readyState === EventSource.CONNECTING) {
      console.log('[SSE] Reconnecting...');
      setConnectionError('Reconnecting...');
      setIsConnected(false);
    } else {
      console.error('[SSE] ✗ Unknown error state');
      setConnectionError('Connection failed');
      setIsConnected(false);
    }
  };

  // Cleanup on unmount or patient ID change
  return () => {
    console.log(`📡 SSE disconnected from patient ${patientId}`);
    eventSource.close();
    setIsConnected(false);
    setConnectionError(null);
  };
}, [enabled, patientId]);
```

**Key improvements:**
- Detects patient ID changes and disconnects old connection
- Handles case where patient ID is cleared (hard refresh)
- Better error logging distinguishing 404/403 from network errors
- Prevents reconnection attempts for non-existent patients

---

## Phase 2: Remove Hard Refresh Redirect

### Overview
Keep user on current page during hard refresh, show in-place loading state instead of redirecting to home.

### Changes Required:

#### 2.1 Remove Redirect from Sessions Page

**File**: `frontend/app/sessions/page.tsx`

**Changes**: Remove redirect, keep in-place

**Current code (lines 23-40):**
```typescript
useEffect(() => {
  const isHardRefresh = refreshDetection.isHardRefresh();
  if (isHardRefresh) {
    console.log('🔥 Hard refresh detected on /sessions - clearing demo data and redirecting to home');
    demoTokenStorage.clear();
    router.push('/');  // ← REMOVE THIS
    return;
  }

  // If no demo token exists, redirect to home for initialization
  if (!demoTokenStorage.isInitialized()) {
    console.log('⚠️ No demo token found - redirecting to home for initialization');
    router.push('/');  // ← REMOVE THIS TOO
    return;
  }
}, [router]);
```

**New code:**
```typescript
useEffect(() => {
  const isHardRefresh = refreshDetection.isHardRefresh();
  if (isHardRefresh) {
    console.log('🔥 Hard refresh detected on /sessions - clearing demo data (staying on page)');
    demoTokenStorage.clear();
    // Don't redirect - WaveCompletionBridge will detect missing patient ID and handle reinitialization
  }
}, []); // Remove router from deps since we're not using it
```

**Rationale:**
- WaveCompletionBridge already polls for patient ID and handles missing ID gracefully
- SessionDataProvider will show loading state while waiting for initialization
- No need to redirect - initialization can happen on any page

#### 2.2 Update WaveCompletionBridge to Show Initialization State

**File**: `frontend/app/patient/components/WaveCompletionBridge.tsx`

**Changes**: Add state to track initialization in progress

**Current code (lines 22-75):**
```typescript
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

      if (id) {
        console.log('[WaveCompletionBridge] ✓ Patient ID found:', id);
        setPatientId(id);
        setIsReady(true);
        return true; // Stop polling
      }

      // ... existing logic
    };
    // ... polling logic
  }, []); // ← Doesn't restart when patient ID changes!
```

**New code:**
```typescript
export function WaveCompletionBridge() {
  const { refresh, setSessionLoading } = useSessionData();
  const [patientId, setPatientId] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);

  // Poll for patient ID - restarts if patient ID is cleared (hard refresh)
  useEffect(() => {
    let attempts = 0;
    const maxAttempts = 240; // 120 seconds max wait (240 * 500ms)

    const checkPatientId = () => {
      attempts++;

      const id = demoTokenStorage.getPatientId();
      const initStatus = demoTokenStorage.getInitStatus();

      if (id) {
        console.log('[WaveCompletionBridge] ✓ Patient ID found:', id);
        setPatientId(id);
        setIsReady(true);
        setIsInitializing(false);
        return true; // Stop polling
      }

      // Check if initialization is in progress
      if (initStatus === 'pending') {
        if (!isInitializing) {
          console.log('[WaveCompletionBridge] Demo initialization in progress...');
          setIsInitializing(true);
        }
        return false; // Keep polling
      }

      // Check if initialization failed
      if (initStatus === 'none' && attempts > 10) {
        console.warn('[WaveCompletionBridge] No patient ID after 5 seconds - may need manual initialization');

        // Trigger demo initialization if not started
        if (attempts === 11) {
          console.log('[WaveCompletionBridge] Triggering demo initialization...');
          setIsInitializing(true);

          // Import and call demo initialization
          import('@/lib/demo-api-client').then(({ demoApiClient }) => {
            demoApiClient.initialize().catch(err => {
              console.error('[WaveCompletionBridge] Demo init failed:', err);
              setIsInitializing(false);
            });
          });
        }

        return false; // Keep polling
      }

      // Timeout after 120 seconds
      if (attempts >= maxAttempts) {
        console.error('[WaveCompletionBridge] ✗ Timeout waiting for patient ID (120s)');
        setIsReady(false);
        setIsInitializing(false);
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
  }, [isInitializing]); // ← Restart effect when initialization state changes

  // ... rest of component
}
```

**Key improvements:**
- Polls continuously for patient ID (handles hard refresh clearing it)
- Auto-triggers demo initialization if not started after 5 seconds
- Increased timeout to 120 seconds (demo init can take 30-90s)
- Effect restarts if initialization state changes

---

## Phase 3: Add Comprehensive SSE Error Handling

### Overview
Improve SSE error handling to distinguish between 404 (patient not found), CORS errors, and network failures. Add detailed logging for debugging.

### Changes Required:

#### 3.1 Add Error Type Detection in SSE Hook

**File**: `frontend/hooks/use-pipeline-events.ts`

**Changes**: Enhanced error detection and logging (already included in Phase 1 changes)

**Additional improvements:**
```typescript
// Add to interface at top of file (after line 15)
interface UsePipelineEventsReturn {
  isConnected: boolean;
  connectionError: string | null;
  errorType: 'none' | 'patient_not_found' | 'cors' | 'network' | 'unknown';
  events: PipelineEvent[];
  latestEvent: PipelineEvent | null;
}

// Update state (after line 36)
const [errorType, setErrorType] = useState<'none' | 'patient_not_found' | 'cors' | 'network' | 'unknown'>('none');

// Update onerror handler (replace lines 133-148)
eventSource.onerror = (error) => {
  const readyState = eventSource.readyState;

  console.group(`[SSE] Connection Error (patient: ${patientId})`);
  console.error('Error event:', error);
  console.log('ReadyState:', readyState, readyState === EventSource.CLOSED ? '(CLOSED)' : readyState === EventSource.CONNECTING ? '(CONNECTING)' : '(OPEN)');
  console.groupEnd();

  if (readyState === EventSource.CLOSED) {
    // Connection permanently closed - likely 404 or 403
    console.error(`[SSE] ✗ Server closed connection - patient ${patientId} may not exist or access denied`);
    setConnectionError('Patient not found or access denied');
    setErrorType('patient_not_found');
    setIsConnected(false);

    // Close connection permanently
    eventSource.close();
    eventSourceRef.current = null;

  } else if (readyState === EventSource.CONNECTING) {
    // Temporary failure, browser will retry
    console.log('[SSE] Connection lost, retrying...');
    setConnectionError('Reconnecting...');
    setErrorType('network');
    setIsConnected(false);

  } else {
    // Unknown state
    console.error('[SSE] ✗ Unknown error state');
    setConnectionError('Connection failed');
    setErrorType('unknown');
    setIsConnected(false);
  }
};

// Update onopen to clear error state (after line 107)
eventSource.onopen = () => {
  console.log(`📡 SSE connected to patient ${patientId}`);
  setIsConnected(true);
  setConnectionError(null);
  setErrorType('none');  // ← Add this
};

// Update return statement (line 159)
return {
  isConnected,
  connectionError,
  errorType,  // ← Add this
  events,
  latestEvent: events[events.length - 1] || null,
};
```

**Key improvements:**
- Distinguish between patient_not_found (404/403), network errors, and CORS
- Grouped console logging for easier debugging
- Return error type for UI to display appropriate messages
- Clear error state when connection succeeds

#### 3.2 Add SSE Error Display in WaveCompletionBridge

**File**: `frontend/app/patient/components/WaveCompletionBridge.tsx`

**Changes**: Display error messages to user

**Add after line 76 (after SSE hook call):**
```typescript
const { isConnected, events, errorType, connectionError } = usePipelineEvents({
  patientId: patientId || "",
  enabled: isReady && !!patientId,
  // ... existing handlers
});

// Log error state changes
useEffect(() => {
  if (errorType !== 'none' && connectionError) {
    console.group('[WaveCompletionBridge] SSE Error Detected');
    console.error('Error type:', errorType);
    console.error('Error message:', connectionError);
    console.log('Patient ID:', patientId);
    console.log('Is ready:', isReady);
    console.groupEnd();

    // If patient not found, patient ID may be stale
    if (errorType === 'patient_not_found' && patientId) {
      console.warn('[WaveCompletionBridge] Patient not found - may need to reinitialize demo');
    }
  }
}, [errorType, connectionError, patientId, isReady]);
```

**Rationale:** Better visibility into SSE failures for debugging production issues

---

## Phase 4: Remove /auth/login Redirects

### Overview
Remove hardcoded redirects to `/auth/login` (which doesn't exist) from demo mode. Let errors surface naturally or show user-friendly messages.

### Changes Required:

#### 4.1 Remove Login Redirects from API Client

**File**: `frontend/lib/api-client.ts`

**Changes**: Remove redirects, just clear tokens and let app handle missing auth

**Current code (lines 254-264):**
```typescript
private async handleTokenRefresh(): Promise<ApiResult<RefreshTokenResponse>> {
  const refreshToken = tokenStorage.getRefreshToken();

  if (!refreshToken) {
    tokenStorage.clearTokens();
    // Redirect to login in browser context
    if (typeof window !== 'undefined') {
      window.location.href = '/auth/login';  // ← REMOVE THIS
    }
    return createFailureResult('No refresh token available', HTTP_STATUS.UNAUTHORIZED);
  }
```

**New code:**
```typescript
private async handleTokenRefresh(): Promise<ApiResult<RefreshTokenResponse>> {
  const refreshToken = tokenStorage.getRefreshToken();

  if (!refreshToken) {
    tokenStorage.clearTokens();

    // In demo mode, also clear demo tokens
    if (typeof window !== 'undefined') {
      import('./demo-token-storage').then(({ demoTokenStorage }) => {
        demoTokenStorage.clear();
        console.log('[API Client] No refresh token - demo data cleared');
      });
    }

    return createFailureResult('No refresh token available', HTTP_STATUS.UNAUTHORIZED);
  }
```

**Also update lines 273-277:**
```typescript
if (!response.ok) {
  tokenStorage.clearTokens();
  if (typeof window !== 'undefined') {
    window.location.href = '/auth/login';  // ← REMOVE THIS
  }
  return createFailureResult('Session expired', HTTP_STATUS.UNAUTHORIZED);
}
```

**New code:**
```typescript
if (!response.ok) {
  tokenStorage.clearTokens();

  if (typeof window !== 'undefined') {
    import('./demo-token-storage').then(({ demoTokenStorage }) => {
      demoTokenStorage.clear();
      console.log('[API Client] Token refresh failed - demo data cleared');
    });
  }

  return createFailureResult('Session expired', HTTP_STATUS.UNAUTHORIZED);
}
```

**Also update lines 284-288:**
```typescript
} catch (error) {
  tokenStorage.clearTokens();
  if (typeof window !== 'undefined') {
    window.location.href = '/auth/login';  // ← REMOVE THIS
  }
  return createFailureResult(
    error instanceof Error ? error.message : 'Token refresh failed',
    HTTP_STATUS.INTERNAL_SERVER_ERROR
  );
}
```

**New code:**
```typescript
} catch (error) {
  tokenStorage.clearTokens();

  if (typeof window !== 'undefined') {
    import('./demo-token-storage').then(({ demoTokenStorage }) => {
      demoTokenStorage.clear();
      console.log('[API Client] Token refresh exception - demo data cleared');
    });
  }

  return createFailureResult(
    error instanceof Error ? error.message : 'Token refresh failed',
    HTTP_STATUS.INTERNAL_SERVER_ERROR
  );
}
```

**Key improvements:**
- No redirects to non-existent `/auth/login` page
- Clears both regular tokens AND demo tokens on failure
- Better logging for debugging
- Let React components handle missing auth state naturally

---

## Testing Strategy

### Unit Tests:
**Not required** - these are integration-level fixes affecting browser APIs (EventSource, localStorage, window.location)

### Manual Testing Steps:

#### Test 1: Simple Refresh (Cmd+R)
1. Open `https://therabridge.up.railway.app/sessions`
2. Wait for sessions to load
3. Note the patient ID in console logs
4. Press **Cmd+R** (simple refresh)
5. **Expected:**
   - ✅ localStorage preserved (same patient ID)
   - ✅ SSE reconnects automatically
   - ✅ Sessions reload with same data
   - ✅ No errors in console

#### Test 2: Hard Refresh (Cmd+Shift+R) on Sessions Page
1. Open `https://therabridge.up.railway.app/sessions`
2. Wait for sessions to load
3. Note the patient ID in console logs
4. Press **Cmd+Shift+R** (hard refresh)
5. **Expected:**
   - ✅ Console shows "🔥 Hard refresh detected - clearing demo data (staying on page)"
   - ✅ Console shows "[Storage] ✓ All demo data cleared"
   - ✅ Console shows "[SSE] Patient ID cleared - disconnecting existing SSE"
   - ✅ Console shows "[WaveCompletionBridge] Demo initialization in progress..."
   - ✅ Page stays on `/sessions` (no redirect)
   - ✅ After 5-10 seconds, console shows new patient ID
   - ✅ Sessions load with new demo data
   - ✅ No "CORS request did not succeed" errors
   - ✅ No redirects to `/auth/login`

#### Test 3: Hard Refresh (Cmd+Shift+R) on Home Page
1. Open `https://therabridge.up.railway.app/`
2. Wait for demo to initialize
3. Press **Cmd+Shift+R** (hard refresh)
4. **Expected:**
   - ✅ Console shows hard refresh detected
   - ✅ localStorage cleared
   - ✅ New demo initialization starts
   - ✅ Redirects to `/dashboard` after complete

#### Test 4: Direct Navigation to Sessions (No Patient ID)
1. Open new incognito window
2. Navigate directly to `https://therabridge.up.railway.app/sessions`
3. **Expected:**
   - ✅ Console shows "[WaveCompletionBridge] No patient ID after 5 seconds - may need manual initialization"
   - ✅ Console shows "[WaveCompletionBridge] Triggering demo initialization..."
   - ✅ Demo initialization completes
   - ✅ Sessions load automatically

#### Test 5: SSE Error Handling (Patient Not Found)
1. Open browser console
2. Manually set invalid patient ID: `localStorage.setItem('therapybridge_patient_id', 'invalid-uuid')`
3. Refresh page
4. **Expected:**
   - ✅ Console shows "[SSE] Connecting to patient invalid-uuid..."
   - ✅ Console shows "[SSE] ✗ Server closed connection - patient invalid-uuid may not exist"
   - ✅ Console shows error type: "patient_not_found"
   - ✅ SSE stops retrying (doesn't spam console)
   - ✅ No generic "NetworkError" messages

#### Test 6: Network Failure Handling
1. Open page with working connection
2. Turn off Wi-Fi / disconnect network
3. Wait 10 seconds
4. Reconnect network
5. **Expected:**
   - ✅ Console shows "[SSE] Connection lost, retrying..."
   - ✅ Error type: "network"
   - ✅ Browser automatically reconnects when network restored
   - ✅ Console shows "📡 SSE connected to patient {id}"

### Performance Considerations

**SSE Connection Overhead:**
- Minimal - EventSource is efficient
- Connection only established when patient ID exists
- Automatic browser reconnection (no custom retry logic needed)

**Polling Overhead:**
- WaveCompletionBridge polls localStorage every 500ms
- Only polls for max 120 seconds (then gives up)
- Polls only when patient ID is missing (not continuous)

**Memory Leaks:**
- EventSource properly closed in cleanup functions
- Intervals cleared in cleanup functions
- No memory leaks expected

## Migration Notes

**No database migrations required** - this is purely frontend code changes.

**Deployment:**
1. Build frontend: `cd frontend && npm run build`
2. Test build locally: `npm start`
3. Deploy to Railway (will auto-deploy on git push)

**Rollback:**
If issues arise, revert these commits:
- Phase 1: SSE reactivity changes
- Phase 2: Hard refresh redirect removal
- Phase 3: Error handling improvements
- Phase 4: /auth/login redirect removal

Git history will preserve all previous behavior.

## References

- Original issue: Browser console logs showing CORS errors on hard refresh
- Railway backend logs: Backend is healthy, processing different patient ID
- Related components:
  - `frontend/hooks/use-pipeline-events.ts:90-157` (SSE hook)
  - `frontend/app/sessions/page.tsx:23-40` (hard refresh detection)
  - `frontend/app/patient/components/WaveCompletionBridge.tsx:28-74` (patient ID polling)
  - `frontend/lib/api-client.ts:254-293` (token refresh logic)
