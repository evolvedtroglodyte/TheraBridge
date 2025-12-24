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

import { useEffect } from "react";
import { useSessionData } from "../contexts/SessionDataContext";
import { usePipelineEvents } from "@/hooks/use-pipeline-events";
import { useDemoInitialization } from "@/hooks/useDemoInitialization";

export function WaveCompletionBridge() {
  const { refresh, setSessionLoading } = useSessionData();
  const { patientId, isReady } = useDemoInitialization();

  // Connect to SSE and handle events (only after demo is ready)
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
