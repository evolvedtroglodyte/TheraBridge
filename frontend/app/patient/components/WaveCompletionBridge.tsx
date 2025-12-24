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

      if (id) {
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
  }, []); // Run once on mount - don't restart when patientId changes

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
