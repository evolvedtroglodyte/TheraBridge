'use client';

/**
 * Processing Context
 *
 * Global context for tracking audio processing status across the app.
 * Provides auto-refresh capability when processing completes.
 *
 * Architecture:
 * - Wraps useProcessingStatus hook
 * - Exposes methods to track sessions
 * - Fires onProcessingComplete callbacks for dashboard refresh
 * - Shows toast notifications on completion/failure
 */

import {
  createContext,
  useContext,
  useCallback,
  useState,
  ReactNode,
} from 'react';
import {
  useProcessingStatus,
  ProcessingStatus,
} from '@/hooks/use-processing-status';

interface ProcessingContextType {
  /** Start tracking a session's processing */
  startTracking: (sessionId: string) => void;
  /** Check if a specific session is processing */
  isSessionProcessing: (sessionId: string) => boolean;
  /** Get progress for a session (0-100) */
  getSessionProgress: (sessionId: string) => number;
  /** Check if any session is processing */
  isAnyProcessing: boolean;
  /** Register a callback for when processing completes */
  onComplete: (callback: (sessionId: string) => void) => () => void;
  /** Most recently completed session ID (for triggering refreshes) */
  lastCompletedSessionId: string | null;
}

const ProcessingContext = createContext<ProcessingContextType | null>(null);

interface ProcessingProviderProps {
  children: ReactNode;
}

export function ProcessingProvider({ children }: ProcessingProviderProps) {
  const [lastCompletedSessionId, setLastCompletedSessionId] = useState<string | null>(null);
  const [completionCallbacks, setCompletionCallbacks] = useState<
    Set<(sessionId: string) => void>
  >(new Set());

  const handleProcessingComplete = useCallback(
    (sessionId: string) => {
      console.log('[ProcessingContext] Processing complete:', sessionId);
      setLastCompletedSessionId(sessionId);

      // Notify all registered callbacks
      completionCallbacks.forEach((callback) => {
        try {
          callback(sessionId);
        } catch (err) {
          console.error('[ProcessingContext] Callback error:', err);
        }
      });
    },
    [completionCallbacks]
  );

  const handleProcessingFailed = useCallback((sessionId: string, error?: string) => {
    console.error('[ProcessingContext] Processing failed:', sessionId, error);
    // Could show a toast notification here
  }, []);

  const {
    processingSessions,
    trackSession,
    isAnyProcessing,
    getSessionStatus,
  } = useProcessingStatus({
    onProcessingComplete: handleProcessingComplete,
    onProcessingFailed: handleProcessingFailed,
    pollInterval: 3000,
    maxPollTime: 10 * 60 * 1000,
  });

  const startTracking = useCallback(
    (sessionId: string) => {
      trackSession(sessionId);
    },
    [trackSession]
  );

  const isSessionProcessing = useCallback(
    (sessionId: string) => {
      const status = getSessionStatus(sessionId);
      return status?.status === 'pending' || status?.status === 'processing';
    },
    [getSessionStatus]
  );

  const getSessionProgress = useCallback(
    (sessionId: string) => {
      return getSessionStatus(sessionId)?.progress || 0;
    },
    [getSessionStatus]
  );

  const onComplete = useCallback(
    (callback: (sessionId: string) => void) => {
      setCompletionCallbacks((prev) => {
        const next = new Set(prev);
        next.add(callback);
        return next;
      });

      // Return unsubscribe function
      return () => {
        setCompletionCallbacks((prev) => {
          const next = new Set(prev);
          next.delete(callback);
          return next;
        });
      };
    },
    []
  );

  return (
    <ProcessingContext.Provider
      value={{
        startTracking,
        isSessionProcessing,
        getSessionProgress,
        isAnyProcessing,
        onComplete,
        lastCompletedSessionId,
      }}
    >
      {children}
    </ProcessingContext.Provider>
  );
}

/**
 * Hook to access processing context
 */
export function useProcessing(): ProcessingContextType {
  const context = useContext(ProcessingContext);

  if (!context) {
    throw new Error(
      'useProcessing must be used within a ProcessingProvider. ' +
      'Add <ProcessingProvider> to your app layout.'
    );
  }

  return context;
}
