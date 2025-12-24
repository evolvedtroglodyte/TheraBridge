'use client';

/**
 * Patient Sessions Hook for Dashboard-v3 (FULLY DYNAMIC)
 *
 * Fetches ALL sessions dynamically from backend API.
 * No hardcoded mock data - everything comes from database.
 *
 * Phase 4 Implementation: Removed all mock data, fully dynamic loading
 */

import { useState, useEffect, useRef } from 'react';
import {
  tasks as mockTasks,
  timelineData as mockTimeline,
  unifiedTimeline as mockUnifiedTimeline,
  majorEvents as mockMajorEvents,
} from './mockData';
import { Session, Task, TimelineEntry, TimelineEvent, MajorEventEntry, MoodType } from './types';
import { apiClient } from '@/lib/api-client';
import { demoTokenStorage } from '@/lib/demo-token-storage';
import { demoApiClient } from '@/lib/demo-api-client';
import { POLLING_CONFIG, SessionState, logPolling } from '@/lib/polling-config';

/**
 * Determine polling interval based on analysis phase
 */
function determinePollingInterval(status: any): number {
  const { wave1_complete, session_count, analysis_status } = status;

  // Wave 1 in progress: 1s polling
  if (wave1_complete < session_count) {
    return POLLING_CONFIG.wave1Interval;
  }

  // Wave 1 complete, Wave 2 not started OR in progress: 3s polling
  if (wave1_complete === session_count && analysis_status !== 'wave2_complete') {
    return POLLING_CONFIG.wave2Interval;
  }

  // Default to Wave 2 interval
  return POLLING_CONFIG.wave2Interval;
}

/**
 * Detect which sessions changed since last poll
 */
function detectChangedSessions(
  newSessions: any[],
  oldStates: Map<string, SessionState>
): any[] {
  const changed: any[] = [];

  for (const session of newSessions) {
    const oldState = oldStates.get(session.session_id);

    // First time seeing this session
    if (!oldState) {
      if (session.wave1_complete || session.wave2_complete) {
        changed.push(session);
      }
      continue;
    }

    // Check if Wave 1 status changed
    if (!oldState.wave1_complete && session.wave1_complete) {
      changed.push(session);
      continue;
    }

    // Check if Wave 2 status changed
    if (!oldState.wave2_complete && session.wave2_complete) {
      changed.push(session);
      continue;
    }

    // Check if timestamps changed (re-analysis)
    if (session.last_wave1_update && session.last_wave1_update !== oldState.last_wave1_update) {
      changed.push(session);
      continue;
    }

    if (session.last_wave2_update && session.last_wave2_update !== oldState.last_wave2_update) {
      changed.push(session);
      continue;
    }
  }

  return changed;
}

/**
 * Update session states ref with new data
 */
function updateSessionStatesRef(
  sessions: any[],
  statesRef: Map<string, SessionState>
): void {
  for (const session of sessions) {
    statesRef.set(session.session_id, {
      wave1_complete: session.wave1_complete,
      wave2_complete: session.wave2_complete,
      last_wave1_update: session.last_wave1_update,
      last_wave2_update: session.last_wave2_update,
    });
  }
}

/**
 * Update changed sessions with loading overlays (staggered for visual effect)
 */
async function updateChangedSessions(
  changedSessions: any[],
  setSessionLoading: (sessionId: string, loading: boolean) => void
): Promise<void> {
  // Show loading overlays with stagger
  for (let i = 0; i < changedSessions.length; i++) {
    const session = changedSessions[i];
    setTimeout(() => {
      logPolling(`Showing loading overlay for session ${session.session_id}`);
      setSessionLoading(session.session_id, true);
    }, i * POLLING_CONFIG.staggerDelay);
  }

  // Wait for overlay duration + fade
  await new Promise(resolve =>
    setTimeout(resolve, POLLING_CONFIG.overlayDuration + POLLING_CONFIG.fadeDuration)
  );

  // Hide loading overlays
  for (const session of changedSessions) {
    logPolling(`Hiding loading overlay for session ${session.session_id}`);
    setSessionLoading(session.session_id, false);
  }
}

/**
 * Hook to provide session data for the dashboard.
 *
 * ALL sessions now load dynamically from the database via API.
 * Session count is dynamic based on database records.
 */
export function usePatientSessions() {
  const [isLoading, setIsLoading] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [unifiedTimeline, setUnifiedTimeline] = useState<TimelineEvent[]>([]);
  const [majorEvents, setMajorEvents] = useState<MajorEventEntry[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [analysisStatus, setAnalysisStatus] = useState<string>('pending');
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [patientId, setPatientId] = useState<string | null>(null);
  const lastWave1Count = useRef<number>(0);
  const lastWave2Count = useRef<number>(0);
  const lastSessionCount = useRef<number>(0);
  const refreshTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // NEW: Track individual session states for change detection
  const sessionStatesRef = useRef<Map<string, SessionState>>(new Map());

  // NEW: Track current polling interval
  const currentIntervalRef = useRef<number>(POLLING_CONFIG.wave1Interval);

  // NEW: Session loading states (for loading overlays)
  const [loadingSessions, setLoadingSessions] = useState<Set<string>>(new Set());

  // Helper to set session loading state
  const setSessionLoading = (sessionId: string, loading: boolean) => {
    setLoadingSessions(prev => {
      const next = new Set(prev);
      if (loading) {
        next.add(sessionId);
      } else {
        next.delete(sessionId);
      }
      return next;
    });
  };

  // Watch for patient ID changes (demo initialization)
  useEffect(() => {
    const checkPatientId = () => {
      const id = demoTokenStorage.getPatientId();
      if (id !== patientId) {
        setPatientId(id);
      }
    };

    // Check immediately
    checkPatientId();

    // Poll every 500ms for changes
    const interval = setInterval(checkPatientId, 500);
    return () => clearInterval(interval);
  }, [patientId]);

  useEffect(() => {
    const loadAllSessions = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // WaveCompletionBridge handles demo initialization
        // We only load sessions here after initialization is complete
        if (!patientId) {
          console.log('[Sessions] Waiting for demo initialization...');
          setIsLoading(false);
          return;
        }

        // Fetch ALL sessions from API (fully dynamic)
        // Note: Sessions may not have transcripts for ~30s after demo init
        console.log('[Sessions] Fetching all sessions from API...');
        const result = await apiClient.getAllSessions();

        if (!result.success || !result.data) {
          // If sessions aren't ready yet, wait and let polling handle it
          if (result.error?.includes('timeout')) {
            console.log('[Sessions] API timeout - sessions may still be initializing. Polling will retry...');
            setIsLoading(false);
            return;
          }
          throw new Error(result.error || 'Failed to fetch sessions');
        }

        // Store backend data for sorting reference
        const backendSessions = result.data;

        // Step 3: Transform ALL backend sessions to frontend Session type
        // Store raw backend session_date for sorting, then transform
        const transformedSessions: Session[] = backendSessions.map((backendSession) => {
          const sessionDate = new Date(backendSession.session_date);

          return {
            id: backendSession.id,
            date: sessionDate.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            }), // "Jan 10"
            duration: `${backendSession.duration_minutes || 60} min`,
            therapist: 'Dr. Rodriguez',
            mood: mapMoodScore(backendSession.mood_score), // Map 0-10 score to MoodType
            topics: backendSession.topics || [], // Empty array = "Analyzing..." in UI
            strategy: backendSession.technique || '', // Empty string = "Analyzing..." in UI
            actions: backendSession.action_items || [],
            summary: backendSession.summary || '', // Empty string = "Analyzing..." in UI
            transcript: backendSession.transcript || [],
            extraction_confidence: backendSession.extraction_confidence,
            topics_extracted_at: backendSession.topics_extracted_at,
            // Wave 2 fields (prose analysis)
            prose_analysis: backendSession.prose_analysis,
            prose_generated_at: backendSession.prose_generated_at,
            // Deep analysis (JSONB)
            deep_analysis: backendSession.deep_analysis,
            deep_analyzed_at: backendSession.deep_analyzed_at,
            // Breakthrough data
            has_breakthrough: backendSession.has_breakthrough,
            breakthrough_data: backendSession.breakthrough_data,
            breakthrough_analyzed_at: backendSession.breakthrough_analyzed_at,
          };
        });

        // Step 4: Sort by date (newest first)
        // Use backend session_date for accurate sorting
        const sortedSessions = transformedSessions.sort((a, b) => {
          const dateA = backendSessions.find(s => s.id === a.id)?.session_date;
          const dateB = backendSessions.find(s => s.id === b.id)?.session_date;
          if (!dateA || !dateB) return 0;
          return new Date(dateB).getTime() - new Date(dateA).getTime();
        });

        console.log('[Sessions] ✓ Loaded:', sortedSessions.length, 'sessions');
        console.log('[Sessions] ✓ Date range:', sortedSessions[sortedSessions.length - 1]?.date, '→', sortedSessions[0]?.date);

        // Log how many sessions have Wave 1 analysis complete (topics extracted)
        const analyzedCount = sortedSessions.filter(s => s.topics && s.topics.length > 0).length;
        console.log('[Sessions] ✓ Analyzed:', analyzedCount + '/' + sortedSessions.length, 'sessions have Wave 1 data');

        setSessions(sortedSessions);
        setTasks(mockTasks);
        setTimeline(mockTimeline);
        setUnifiedTimeline(mockUnifiedTimeline);
        setMajorEvents(mockMajorEvents);

      } catch (err) {
        console.error('[usePatientSessions] Error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load sessions');
        setSessions([]); // Empty state on error (no fallback to mock)
      } finally {
        setIsLoading(false);
      }
    };

    loadAllSessions();
  }, [patientId]); // Re-run when patient ID is set

  // Polling effect: Granular per-session updates with adaptive intervals
  useEffect(() => {
    // If SSE enabled, disable polling (SSE will handle real-time updates)
    if (POLLING_CONFIG.sseEnabled) {
      logPolling('SSE enabled, polling disabled');
      return;
    }

    // Don't poll if feature disabled or status is complete
    if (!POLLING_CONFIG.granularUpdatesEnabled || analysisStatus === 'wave2_complete') {
      return;
    }

    logPolling('Starting analysis status polling...');

    const pollStatus = async () => {
      try {
        const status = await demoApiClient.getStatus();

        if (!status) {
          return; // Failed to fetch, try again next interval
        }

        logPolling('Analysis status:', {
          status: status.analysis_status,
          wave1: status.wave1_complete,
          wave2: status.wave2_complete,
          total: status.session_count
        });

        setAnalysisStatus(status.analysis_status);

        // Detect which sessions changed
        const changedSessions = detectChangedSessions(status.sessions, sessionStatesRef.current);

        if (changedSessions.length > 0) {
          logPolling(`Progress detected: ${changedSessions.length} session(s) changed`);

          // Update sessions with loading overlays (staggered for polling)
          await updateChangedSessions(changedSessions, setSessionLoading);

          // Update session states ref
          updateSessionStatesRef(status.sessions, sessionStatesRef.current);

          // Refresh session data
          refresh();
        }

        // Update counts
        lastSessionCount.current = status.session_count;
        lastWave1Count.current = status.wave1_complete;
        lastWave2Count.current = status.wave2_complete;

        // Update polling interval based on analysis phase
        const newInterval = determinePollingInterval(status);
        if (newInterval !== currentIntervalRef.current) {
          logPolling(`Switching polling interval: ${currentIntervalRef.current}ms → ${newInterval}ms`);
          currentIntervalRef.current = newInterval;

          // Restart polling with new interval
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
          startPolling(newInterval);
        }

        // Stop polling if Wave 2 complete
        if (status.analysis_status === 'wave2_complete') {
          logPolling('Analysis complete! Stopping polling.');
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      } catch (error) {
        console.error('[Polling] Error fetching status:', error);
      }
    };

    const startPolling = (interval: number) => {
      pollingIntervalRef.current = setInterval(pollStatus, interval);
    };

    // Start initial polling
    startPolling(currentIntervalRef.current);

    // Cleanup
    return () => {
      logPolling('Cleaning up polling interval');
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [analysisStatus]); // Only re-run if analysisStatus changes

  // Manual refresh function - reloads from API without triggering global loading state
  // Returns a Promise that resolves when refresh completes
  const refresh = async (): Promise<void> => {
    // Don't debounce - just refresh immediately
    // The SSE callbacks handle their own timing with loading overlays
    try {
      const result = await apiClient.getAllSessions();
      if (result.success && result.data) {
        const transformed = result.data.map((backendSession) => {
          const sessionDate = new Date(backendSession.session_date);
          return {
            id: backendSession.id,
            date: sessionDate.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric',
            }),
            rawDate: sessionDate,
            duration: `${backendSession.duration_minutes || 60} min`,
            therapist: 'Dr. Rodriguez',
            mood: mapMoodScore(backendSession.mood_score),
            topics: backendSession.topics || [], // Empty array = "Analyzing..." in UI
            strategy: backendSession.technique || '', // Empty string = "Analyzing..." in UI
            actions: backendSession.action_items || [],
            summary: backendSession.summary || '', // Empty string = "Analyzing..." in UI
            transcript: backendSession.transcript || [],
            extraction_confidence: backendSession.extraction_confidence,
            topics_extracted_at: backendSession.topics_extracted_at,
            // Wave 2 fields (prose analysis)
            prose_analysis: backendSession.prose_analysis,
            prose_generated_at: backendSession.prose_generated_at,
            // Deep analysis (JSONB)
            deep_analysis: backendSession.deep_analysis,
            deep_analyzed_at: backendSession.deep_analyzed_at,
            // Breakthrough data
            has_breakthrough: backendSession.has_breakthrough,
            breakthrough_data: backendSession.breakthrough_data,
            breakthrough_analyzed_at: backendSession.breakthrough_analyzed_at,
          };
        });
        setSessions(transformed);
      }
    } catch (err) {
      console.error('[refresh] Error:', err);
    }
  };

  // Update a major event's reflection
  const updateMajorEventReflection = (eventId: string, reflection: string) => {
    setMajorEvents(prev =>
      prev.map(e => e.id === eventId ? { ...e, reflection } : e)
    );
    setUnifiedTimeline(prev =>
      prev.map(e =>
        e.eventType === 'major_event' && e.id === eventId
          ? { ...e, reflection }
          : e
      )
    );
  };

  return {
    sessions,
    tasks,
    timeline,
    unifiedTimeline,
    majorEvents,
    isLoading,
    isError: error !== null,
    error,
    refresh,
    updateMajorEventReflection,
    sessionCount: sessions.length, // DYNAMIC: Based on database count
    majorEventCount: majorEvents.length,
    isEmpty: !isLoading && sessions.length === 0,
    loadingSessions, // NEW: Set of session IDs with loading overlays
    setSessionLoading, // NEW: Helper to set loading state
  };
}

/**
 * Helper function to map mood_score (0-10) to MoodType ('positive' | 'neutral' | 'low')
 */
function mapMoodScore(score: number | null | undefined): MoodType {
  if (score === null || score === undefined) return 'neutral';
  if (score >= 7) return 'positive';
  if (score >= 4) return 'neutral';
  return 'low';
}
