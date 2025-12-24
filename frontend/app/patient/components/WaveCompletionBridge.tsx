"use client";

/**
 * WaveCompletionBridge - SSE-based Real-Time Updates
 *
 * Connects to SSE endpoint and triggers per-session updates as they complete.
 *
 * Behavior:
 *   - Connects to SSE stream on mount
 *   - When Wave 1 completes for a session: triggers loading state + refresh for that session
 *   - When Wave 2 completes for a session: triggers loading state + refresh for that session
 *   - Disconnects when all analysis complete
 */

import { useEffect, useState } from "react";
import { useSessionData } from "../contexts/SessionDataContext";
import { usePipelineEvents } from "@/hooks/use-pipeline-events";
import { demoTokenStorage } from "@/lib/demo-token-storage";

export function WaveCompletionBridge() {
  const { refresh, setSessionLoading } = useSessionData();
  const [patientId, setPatientId] = useState<string | null>(null);

  // Get patient ID from localStorage (populated by SessionDataContext's usePatientSessions)
  useEffect(() => {
    const checkPatientId = () => {
      const id = demoTokenStorage.getPatientId();
      if (id && id !== patientId) {
        console.log('[WaveCompletionBridge] Patient ID found:', id);
        setPatientId(id);
      }
    };

    // Check immediately
    checkPatientId();

    // Poll every 500ms until we have a patient ID
    const interval = setInterval(checkPatientId, 500);

    return () => clearInterval(interval);
  }, [patientId]);

  // Connect to SSE and handle events (only after we have patient ID)
  const { isConnected, events } = usePipelineEvents({
    patientId: patientId || "",
    enabled: !!patientId,

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
    if (isConnected) {
      console.log("✅ Real-time pipeline events connected");
    }
  }, [isConnected]);

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
