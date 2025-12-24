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
        const newStatus: WaveCompletionStatus = {
          wave1Complete: response.wave1_complete === response.session_count,
          wave2Complete: response.wave2_complete === response.session_count,
          sessionCount: response.session_count,
          wave1CompletedCount: response.wave1_complete,
          wave2CompletedCount: response.wave2_complete,
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
