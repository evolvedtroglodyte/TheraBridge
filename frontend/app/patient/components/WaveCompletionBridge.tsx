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

import { useEffect, useState, useRef } from "react";
import { useSessionData } from "../contexts/SessionDataContext";
import { usePipelineEvents } from "@/hooks/use-pipeline-events";
import { demoTokenStorage } from "@/lib/demo-token-storage";

export function WaveCompletionBridge() {
  const { refresh, setSessionLoading, setRoadmapRefreshTrigger } = useSessionData();
  const [patientId, setPatientId] = useState<string | null>(null);
  const [isReady, setIsReady] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const refreshDebounceRef = useRef<NodeJS.Timeout | null>(null);
  const pendingRefreshRef = useRef<Promise<void> | null>(null);

  // Continuously poll for patient ID - detects when it changes or gets cleared (hard refresh)
  useEffect(() => {
    const checkPatientId = () => {
      const id = demoTokenStorage.getPatientId();
      const initStatus = demoTokenStorage.getInitStatus();

      // Patient ID exists - set it and mark as ready
      if (id) {
        // Only log if patient ID changed
        if (id !== patientId) {
          console.log('[WaveCompletionBridge] ✓ Patient ID found:', id);
        }
        setPatientId(id);
        setIsReady(true);
        setIsInitializing(false);
        return;
      }

      // No patient ID - check if we need to initialize
      if (!id && patientId) {
        // Patient ID was cleared (hard refresh!)
        console.log('[WaveCompletionBridge] Patient ID cleared - resetting state');
        setPatientId(null);
        setIsReady(false);
        setIsInitializing(false);
        return;
      }

      // No patient ID and initialization pending
      if (initStatus === 'pending') {
        if (!isInitializing) {
          console.log('[WaveCompletionBridge] Demo initialization in progress...');
          setIsInitializing(true);
        }
        return;
      }

      // No patient ID and no initialization - trigger it
      if (initStatus === 'none' && !isInitializing && !patientId) {
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
    };

    // Check immediately
    checkPatientId();

    // Poll every 500ms continuously
    const interval = setInterval(checkPatientId, 500);

    return () => clearInterval(interval);
  }, [patientId, isInitializing]); // Re-run when patient ID or init state changes

  // Connect to SSE and handle events (only after we have patient ID)
  const { isConnected, events, errorType, connectionError } = usePipelineEvents({
    patientId: patientId || "",
    enabled: isReady && !!patientId,

    onWave1SessionComplete: async (sessionId, sessionDate) => {
      console.log(
        `🔄 Wave 1 complete for ${sessionDate}! Showing loading state...`
      );

      // Show loading overlay on this session card
      setSessionLoading(sessionId, true);

      // Create or reuse pending refresh promise (don't clear existing timeout)
      if (!pendingRefreshRef.current) {
        pendingRefreshRef.current = new Promise(resolve => {
          refreshDebounceRef.current = setTimeout(async () => {
            console.log('[DEBUG] Debounced refresh executing after delay...');
            // Extra delay to allow backend database write to complete
            await new Promise(r => setTimeout(r, 1000));
            console.log('[DEBUG] Starting refresh API call...');
            await refresh();
            pendingRefreshRef.current = null;
            refreshDebounceRef.current = null;
            console.log('[DEBUG] Debounced refresh complete');
            resolve();
          }, 200); // Wait 200ms to batch rapid events
        });
      }

      // Wait for the batched refresh to complete
      console.log(`[DEBUG] ${sessionDate} waiting for refresh...`);
      await pendingRefreshRef.current;
      console.log(`[DEBUG] ${sessionDate} refresh complete, clearing overlay in 300ms`);

      // Small delay to ensure user sees the overlay before it disappears
      await new Promise(resolve => setTimeout(resolve, 300));

      // Hide loading overlay
      console.log(`[DEBUG] ${sessionDate} clearing loading overlay`);
      setSessionLoading(sessionId, false);
    },

    onWave2SessionComplete: async (sessionId, sessionDate) => {
      console.log(
        `🔄 Wave 2 complete for ${sessionDate}! Showing loading state...`
      );

      // Show loading overlay on this session card
      setSessionLoading(sessionId, true);

      // Create or reuse pending refresh promise (don't clear existing timeout)
      if (!pendingRefreshRef.current) {
        pendingRefreshRef.current = new Promise(resolve => {
          refreshDebounceRef.current = setTimeout(async () => {
            console.log('[DEBUG] Debounced refresh executing after delay...');
            // Extra delay to allow backend database write to complete
            await new Promise(r => setTimeout(r, 1000));
            console.log('[DEBUG] Starting refresh API call...');
            await refresh();
            pendingRefreshRef.current = null;
            refreshDebounceRef.current = null;
            console.log('[DEBUG] Debounced refresh complete');
            resolve();
          }, 200); // Wait 200ms to batch rapid events
        });
      }

      // Wait for the batched refresh to complete
      console.log(`[DEBUG] ${sessionDate} waiting for refresh...`);
      await pendingRefreshRef.current;
      console.log(`[DEBUG] ${sessionDate} refresh complete, clearing overlay in 300ms`);

      // Trigger roadmap refresh (roadmap is generated after each Wave 2 completion)
      console.log(`[Roadmap] 🔄 Triggering roadmap refresh after Wave 2 for ${sessionDate}`);
      setRoadmapRefreshTrigger(prev => prev + 1);

      // Small delay to ensure user sees the overlay before it disappears
      await new Promise(resolve => setTimeout(resolve, 300));

      // Hide loading overlay
      console.log(`[DEBUG] ${sessionDate} clearing loading overlay`);
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

  return null;
}
