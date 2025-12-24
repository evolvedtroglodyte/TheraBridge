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
  }, [isInitializing]); // Restart effect when initialization state changes

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
