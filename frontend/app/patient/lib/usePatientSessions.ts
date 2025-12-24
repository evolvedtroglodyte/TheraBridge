'use client';

/**
 * Patient Sessions Hook for Dashboard-v3
 *
 * Fetches real session data from backend API using demo patient ID.
 * Falls back to MOCK DATA if demo token is not available.
 */

import { useState, useEffect } from 'react';
import {
  sessions as mockSessions,
  tasks as mockTasks,
  timelineData as mockTimeline,
  unifiedTimeline as mockUnifiedTimeline,
  majorEvents as mockMajorEvents,
} from './mockData';
import { Session, Task, TimelineEntry, TimelineEvent, MajorEventEntry } from './types';
import { apiClient } from '@/lib/api-client';
import { demoTokenStorage } from '@/lib/demo-token-storage';

// ═══════════════════════════════════════════════════════════════════════════
// TOGGLE THIS TO SWITCH BETWEEN HYBRID AND MOCK DATA
// HYBRID MODE: Session 1 from API, Sessions 2-10 from mock data
// Set USE_HYBRID_MODE to `false` to use full mock data
// ═══════════════════════════════════════════════════════════════════════════
const USE_HYBRID_MODE = true;

/**
 * Hook to provide session data for the dashboard.
 *
 * Currently uses mock data for development. Edit mockData.ts to change
 * what appears in the dashboard - changes will appear after hot reload.
 */
export function usePatientSessions() {
  const [isLoading, setIsLoading] = useState(true);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [timeline, setTimeline] = useState<TimelineEntry[]>([]);
  const [unifiedTimeline, setUnifiedTimeline] = useState<TimelineEvent[]>([]);
  const [majorEvents, setMajorEvents] = useState<MajorEventEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeAndFetch = async () => {
      setIsLoading(true);
      setError(null);

      try {
        // Step 1: Initialize demo if needed
        if (!demoTokenStorage.isInitialized()) {
          console.log('[Demo] No token found, initializing demo...');
          const initResult = await apiClient.initializeDemo();

          if (!initResult.success || !initResult.data) {
            throw new Error(initResult.error || 'Failed to initialize demo');
          }

          // Store demo credentials
          const { demo_token, patient_id, session_ids, expires_at } = initResult.data;
          demoTokenStorage.store(demo_token, patient_id, session_ids, expires_at);
          console.log('[Demo] ✓ Initialized:', { patient_id, sessionCount: session_ids.length });
        }

        // Step 2: Get session IDs
        const sessionIds = demoTokenStorage.getSessionIds();
        if (!sessionIds || sessionIds.length === 0) {
          throw new Error('No session IDs found');
        }

        // Step 3: Fetch Session 1 from API
        const session1Id = sessionIds[0];
        console.log('[Session1] Fetching from API:', session1Id);

        const sessionResult = await apiClient.getSessionById(session1Id);

        let session1Data: Session;
        if (!sessionResult.success || !sessionResult.data) {
          console.error('[Session1] Failed to fetch:', sessionResult.error);
          // Use mock Session 1 with error text
          session1Data = {
            ...mockSessions[0],
            summary: 'Error loading session summary'
          };
        } else {
          // Transform backend session to frontend Session type
          const backendSession = sessionResult.data;
          const sessionDate = new Date(backendSession.session_date);

          session1Data = {
            id: backendSession.id,
            date: sessionDate.toLocaleDateString('en-US', {
              month: 'short',
              day: 'numeric'
            }), // "Jan 10"
            rawDate: sessionDate, // Date object for sorting
            duration: `${backendSession.duration_minutes || 60} min`,
            therapist: 'Dr. Rodriguez',
            mood: 'neutral' as const, // TODO: Map mood_score to MoodType
            topics: backendSession.topics || [],
            strategy: backendSession.technique || 'Not yet analyzed',
            actions: backendSession.action_items || [],
            summary: backendSession.summary || 'Summary not yet generated.',
            transcript: backendSession.transcript || [],
            extraction_confidence: backendSession.extraction_confidence,
            topics_extracted_at: backendSession.topics_extracted_at,
          };
          console.log('[Session1] ✓ Loaded date:', backendSession.session_date);
          console.log('[Session1] ✓ Loaded summary:', session1Data.summary);
        }

        // Step 4: Merge Session 1 (real) + Sessions 2-10 (mock)
        const allSessions = [session1Data, ...mockSessions.slice(1)];

        // Step 5: Sort by rawDate in descending order (newest first)
        const sortedSessions = allSessions.sort((a, b) => {
          if (!a.rawDate || !b.rawDate) return 0;
          return b.rawDate.getTime() - a.rawDate.getTime();
        });

        console.log('[Sessions] ✓ Sorted:', sortedSessions.map((s, i) => `${i}: ${s.date}`).join(', '));
        console.log('[Session1] ✓ Position:', sortedSessions.findIndex(s => s.id === session1Data.id));

        // Step 6: Update state
        setSessions(sortedSessions);
        setTasks(mockTasks);
        setTimeline(mockTimeline);
        setUnifiedTimeline(mockUnifiedTimeline);
        setMajorEvents(mockMajorEvents);

      } catch (err) {
        console.error('[usePatientSessions] Error:', err);
        setError(err instanceof Error ? err.message : 'Failed to load sessions');

        // Fallback to full mock data on error
        setSessions(mockSessions);
        setTasks(mockTasks);
        setTimeline(mockTimeline);
        setUnifiedTimeline(mockUnifiedTimeline);
        setMajorEvents(mockMajorEvents);
      } finally {
        setIsLoading(false);
      }
    };

    if (USE_HYBRID_MODE) {
      initializeAndFetch();
    } else {
      // Full mock mode (legacy)
      const timer = setTimeout(() => {
        setSessions(mockSessions);
        setTasks(mockTasks);
        setTimeline(mockTimeline);
        setUnifiedTimeline(mockUnifiedTimeline);
        setMajorEvents(mockMajorEvents);
        setIsLoading(false);
      }, 300);
      return () => clearTimeout(timer);
    }
  }, []);

  // Manual refresh function - reloads mock data
  const refresh = () => {
    setIsLoading(true);
    setTimeout(() => {
      setSessions([...mockSessions]);
      setTasks([...mockTasks]);
      setTimeline([...mockTimeline]);
      setUnifiedTimeline([...mockUnifiedTimeline]);
      setMajorEvents([...mockMajorEvents]);
      setIsLoading(false);
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
    sessionCount: sessions.length,
    majorEventCount: majorEvents.length,
    isEmpty: !isLoading && sessions.length === 0,
  };
}
