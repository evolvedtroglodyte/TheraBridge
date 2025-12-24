"use client";

/**
 * WaveCompletionBridge
 *
 * Polls for Wave 1 and Wave 2 analysis completion and auto-refreshes
 * the dashboard when each wave finishes.
 *
 * Usage:
 *   Place this component inside SessionDataProvider to enable auto-refresh.
 *
 * Behavior:
 *   - Polls /api/demo/status every 5 seconds
 *   - When Wave 1 completes: refreshes session data (cards update with mood/topics)
 *   - When Wave 2 completes: refreshes session data again (cards update with deep analysis)
 *   - Stops polling after Wave 2 completes
 */

import { useEffect } from "react";
import { useSessionData } from "../contexts/SessionDataContext";
import { useWaveCompletionPolling } from "@/hooks/use-wave-completion-polling";

export function WaveCompletionBridge() {
  const { refresh } = useSessionData();

  const {
    wave1Complete,
    wave2Complete,
    wave1CompletedCount,
    wave2CompletedCount,
    sessionCount,
    isPolling,
  } = useWaveCompletionPolling({
    enabled: true,
    interval: 5000, // Poll every 5 seconds
    onWave1Complete: () => {
      console.log(
        "🔄 Wave 1 complete! Refreshing dashboard to show mood/topics..."
      );
      refresh();
    },
    onWave2Complete: () => {
      console.log(
        "🔄 Wave 2 complete! Refreshing dashboard to show deep analysis..."
      );
      refresh();
    },
  });

  // Log polling status for debugging
  useEffect(() => {
    if (isPolling) {
      console.log(
        `⏳ Polling wave completion: Wave 1: ${wave1CompletedCount}/${sessionCount}, Wave 2: ${wave2CompletedCount}/${sessionCount}`
      );
    }
  }, [isPolling, wave1CompletedCount, wave2CompletedCount, sessionCount]);

  // This component doesn't render anything
  return null;
}
