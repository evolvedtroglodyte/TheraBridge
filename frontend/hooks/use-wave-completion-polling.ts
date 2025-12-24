"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { demoApiClient } from "@/lib/demo-api-client";

interface WaveCompletionStatus {
  wave1Complete: boolean;
  wave2Complete: boolean;
  sessionCount: number;
  wave1CompletedCount: number;
  wave2CompletedCount: number;
}

interface UseWaveCompletionPollingOptions {
  enabled?: boolean;
  interval?: number; // milliseconds
  onWave1Complete?: () => void;
  onWave2Complete?: () => void;
}

export function useWaveCompletionPolling(
  options: UseWaveCompletionPollingOptions = {}
) {
  const {
    enabled = true,
    interval = 5000, // 5 seconds default
    onWave1Complete,
    onWave2Complete,
  } = options;

  const [status, setStatus] = useState<WaveCompletionStatus>({
    wave1Complete: false,
    wave2Complete: false,
    sessionCount: 0,
    wave1CompletedCount: 0,
    wave2CompletedCount: 0,
  });

  const [isPolling, setIsPolling] = useState(false);

  // Track previous state to detect transitions
  const prevStatusRef = useRef<WaveCompletionStatus>(status);

  const checkStatus = useCallback(async () => {
    try {
      const response = await demoApiClient.getStatus();

      if (response) {
        // Count completed sessions from the sessions array
        const wave1CompletedCount = response.sessions?.filter(s => s.wave1_complete).length || 0;
        const wave2CompletedCount = response.sessions?.filter(s => s.wave2_complete).length || 0;

        const newStatus: WaveCompletionStatus = {
          wave1Complete: wave1CompletedCount === response.session_count,
          wave2Complete: wave2CompletedCount === response.session_count,
          sessionCount: response.session_count,
          wave1CompletedCount: wave1CompletedCount,
          wave2CompletedCount: wave2CompletedCount,
        };

        setStatus(newStatus);

        // Detect Wave 1 completion transition
        if (
          !prevStatusRef.current.wave1Complete &&
          newStatus.wave1Complete &&
          onWave1Complete
        ) {
          console.log("✅ Wave 1 analysis completed!");
          onWave1Complete();
        }

        // Detect Wave 2 completion transition
        if (
          !prevStatusRef.current.wave2Complete &&
          newStatus.wave2Complete &&
          onWave2Complete
        ) {
          console.log("✅ Wave 2 analysis completed!");
          onWave2Complete();
        }

        prevStatusRef.current = newStatus;

        // Stop polling if both waves are complete
        if (newStatus.wave1Complete && newStatus.wave2Complete) {
          setIsPolling(false);
        }
      }
    } catch (error) {
      console.error("Error polling wave completion status:", error);
    }
  }, [onWave1Complete, onWave2Complete]);

  useEffect(() => {
    if (!enabled) {
      setIsPolling(false);
      return;
    }

    // Start polling
    setIsPolling(true);

    // Initial check
    checkStatus();

    // Set up polling interval
    const intervalId = setInterval(checkStatus, interval);

    return () => {
      clearInterval(intervalId);
      setIsPolling(false);
    };
  }, [enabled, interval, checkStatus]);

  return {
    ...status,
    isPolling,
    refetch: checkStatus,
  };
}
