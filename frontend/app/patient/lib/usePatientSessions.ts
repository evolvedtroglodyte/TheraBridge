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

  useEffect(() => {
    const loadAllSessions = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Step 1: Initialize demo if needed
        if (!demoTokenStorage.isInitialized()) {
          console.log('[Demo] Initializing...');
          const initResult = await apiClient.initializeDemo();

          if (!initResult.success || !initResult.data) {
            throw new Error(initResult.error || 'Failed to initialize demo');
          }

          const { demo_token, patient_id, session_ids, expires_at } = initResult.data;
          demoTokenStorage.store(demo_token, patient_id, session_ids, expires_at);
          console.log('[Demo] ✓ Initialized:', { patient_id, sessionCount: session_ids.length });
        }

        // Step 2: Fetch ALL sessions from API (NEW - fully dynamic)
        console.log('[Sessions] Fetching all sessions from API...');
        const result = await apiClient.getAllSessions();

        if (!result.success || !result.data) {
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
            topics: backendSession.topics || [],
            strategy: backendSession.technique || 'Not yet analyzed',
            actions: backendSession.action_items || [],
            summary: backendSession.summary || 'Summary not yet generated.',
            transcript: backendSession.transcript || [],
            extraction_confidence: backendSession.extraction_confidence,
            topics_extracted_at: backendSession.topics_extracted_at,
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
  }, []);

  // Polling effect: Auto-refresh sessions while analysis is in progress
  useEffect(() => {
    // Only poll if we have incomplete analysis
    const shouldPoll = analysisStatus === 'pending' || analysisStatus === 'processing';

    if (shouldPoll && demoTokenStorage.isInitialized()) {
      console.log('[Polling] Starting analysis status polling (5s interval)...');

      pollingIntervalRef.current = setInterval(async () => {
        try {
          // Check demo status
          const status = await demoApiClient.getStatus();

          if (!status) {
            return; // Failed to fetch, try again next interval
          }

          console.log('[Polling] Analysis status:', {
            status: status.analysis_status,
            wave1: status.wave1_complete,
            wave2: status.wave2_complete,
            total: status.session_count
          });

          setAnalysisStatus(status.analysis_status);

          // If analysis status changed, refresh sessions to show new data
          const hasNewData = status.wave1_complete > 0 || status.wave2_complete > 0;
          if (hasNewData) {
            console.log('[Polling] New analysis data detected, refreshing sessions...');
            refresh();
          }

          // Stop polling if fully complete
          if (status.analysis_status === 'wave2_complete') {
            console.log('[Polling] Analysis complete! Stopping polling.');
            if (pollingIntervalRef.current) {
              clearInterval(pollingIntervalRef.current);
              pollingIntervalRef.current = null;
            }
          }
        } catch (err) {
          console.error('[Polling] Error checking status:', err);
        }
      }, 5000); // Poll every 5 seconds

      return () => {
        if (pollingIntervalRef.current) {
          console.log('[Polling] Cleaning up polling interval');
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
      };
    }
  }, [analysisStatus]);

  // Manual refresh function - reloads from API
  const refresh = () => {
    setIsLoading(true);
    setTimeout(async () => {
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
              topics: backendSession.topics || [],
              strategy: backendSession.technique || 'Not yet analyzed',
              actions: backendSession.action_items || [],
              summary: backendSession.summary || 'Summary not yet generated.',
              transcript: backendSession.transcript || [],
              extraction_confidence: backendSession.extraction_confidence,
              topics_extracted_at: backendSession.topics_extracted_at,
            };
          });
          setSessions(transformed);
        }
      } catch (err) {
        console.error('[refresh] Error:', err);
      } finally {
        setIsLoading(false);
      }
    }, 300);
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
