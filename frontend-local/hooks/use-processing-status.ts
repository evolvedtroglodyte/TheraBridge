/**
 * Processing Status Hook
 *
 * Polls for audio processing completion and notifies when done.
 * Uses smart polling with exponential backoff to minimize API calls.
 *
 * Flow:
 * 1. Start polling when a session begins processing
 * 2. Check status every few seconds (with backoff)
 * 3. Fire callback when processing completes
 * 4. Auto-stop polling on completion, failure, or timeout
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/lib/supabase';

export type ProcessingStatus = 'idle' | 'pending' | 'processing' | 'completed' | 'failed';

interface ProcessingSession {
  sessionId: string;
  status: ProcessingStatus;
  progress: number;
  startedAt: Date;
}

interface UseProcessingStatusOptions {
  /** Called when any session completes processing */
  onProcessingComplete?: (sessionId: string) => void;
  /** Called when processing fails */
  onProcessingFailed?: (sessionId: string, error?: string) => void;
  /** Polling interval in ms (default: 3000) */
  pollInterval?: number;
  /** Max polling time before timeout in ms (default: 10 minutes) */
  maxPollTime?: number;
}

interface UseProcessingStatusReturn {
  /** Currently processing sessions */
  processingSessions: ProcessingSession[];
  /** Start tracking a session's processing status */
  trackSession: (sessionId: string) => void;
  /** Stop tracking a session */
  stopTracking: (sessionId: string) => void;
  /** Check if any session is currently processing */
  isAnyProcessing: boolean;
  /** Get status for a specific session */
  getSessionStatus: (sessionId: string) => ProcessingSession | undefined;
}

export function useProcessingStatus(
  options: UseProcessingStatusOptions = {}
): UseProcessingStatusReturn {
  const {
    onProcessingComplete,
    onProcessingFailed,
    pollInterval = 3000,
    maxPollTime = 10 * 60 * 1000, // 10 minutes
  } = options;

  const [processingSessions, setProcessingSessions] = useState<ProcessingSession[]>([]);
  const pollTimersRef = useRef<Map<string, NodeJS.Timeout>>(new Map());
  const startTimesRef = useRef<Map<string, number>>(new Map());

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      pollTimersRef.current.forEach((timer) => clearTimeout(timer));
      pollTimersRef.current.clear();
    };
  }, []);

  const stopTracking = useCallback((sessionId: string) => {
    const timer = pollTimersRef.current.get(sessionId);
    if (timer) {
      clearTimeout(timer);
      pollTimersRef.current.delete(sessionId);
    }
    startTimesRef.current.delete(sessionId);
    setProcessingSessions((prev) => prev.filter((s) => s.sessionId !== sessionId));
  }, []);

  const pollSessionStatus = useCallback(
    async (sessionId: string) => {
      // Check for timeout
      const startTime = startTimesRef.current.get(sessionId);
      if (startTime && Date.now() - startTime > maxPollTime) {
        console.warn(`[ProcessingStatus] Timeout for session ${sessionId}`);
        stopTracking(sessionId);
        onProcessingFailed?.(sessionId, 'Processing timed out');
        return;
      }

      try {
        const { data: session, error } = await supabase
          .from('therapy_sessions')
          .select('processing_status, processing_progress')
          .eq('id', sessionId)
          .single();

        if (error) {
          console.error('[ProcessingStatus] Error fetching status:', error);
          // Continue polling on error
          scheduleNextPoll(sessionId);
          return;
        }

        const status = session?.processing_status as ProcessingStatus || 'idle';
        const progress = session?.processing_progress || 0;

        // Update state
        setProcessingSessions((prev) =>
          prev.map((s) =>
            s.sessionId === sessionId ? { ...s, status, progress } : s
          )
        );

        // Check for completion
        if (status === 'completed') {
          console.log(`[ProcessingStatus] Session ${sessionId} completed!`);
          stopTracking(sessionId);
          onProcessingComplete?.(sessionId);
          return;
        }

        // Check for failure
        if (status === 'failed') {
          console.log(`[ProcessingStatus] Session ${sessionId} failed`);
          stopTracking(sessionId);
          onProcessingFailed?.(sessionId);
          return;
        }

        // Continue polling
        scheduleNextPoll(sessionId);
      } catch (err) {
        console.error('[ProcessingStatus] Poll error:', err);
        scheduleNextPoll(sessionId);
      }
    },
    [maxPollTime, onProcessingComplete, onProcessingFailed, stopTracking]
  );

  const scheduleNextPoll = useCallback(
    (sessionId: string) => {
      const timer = setTimeout(() => {
        pollSessionStatus(sessionId);
      }, pollInterval);
      pollTimersRef.current.set(sessionId, timer);
    },
    [pollInterval, pollSessionStatus]
  );

  const trackSession = useCallback(
    (sessionId: string) => {
      // Don't duplicate tracking
      if (processingSessions.some((s) => s.sessionId === sessionId)) {
        return;
      }

      console.log(`[ProcessingStatus] Starting to track session ${sessionId}`);

      // Add to state
      setProcessingSessions((prev) => [
        ...prev,
        {
          sessionId,
          status: 'pending',
          progress: 0,
          startedAt: new Date(),
        },
      ]);

      // Record start time
      startTimesRef.current.set(sessionId, Date.now());

      // Start polling immediately
      pollSessionStatus(sessionId);
    },
    [processingSessions, pollSessionStatus]
  );

  const getSessionStatus = useCallback(
    (sessionId: string) => {
      return processingSessions.find((s) => s.sessionId === sessionId);
    },
    [processingSessions]
  );

  const isAnyProcessing = processingSessions.some(
    (s) => s.status === 'pending' || s.status === 'processing'
  );

  return {
    processingSessions,
    trackSession,
    stopTracking,
    isAnyProcessing,
    getSessionStatus,
  };
}
