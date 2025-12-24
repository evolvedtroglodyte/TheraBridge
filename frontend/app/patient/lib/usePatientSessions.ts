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
// TOGGLE THIS TO SWITCH BETWEEN MOCK AND REAL DATA
// Set to `false` when you have a working authenticated backend
// ═══════════════════════════════════════════════════════════════════════════
const USE_MOCK_DATA = true;  // Using mock data for development

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
  // New: unified timeline with sessions + major events
  const [unifiedTimeline, setUnifiedTimeline] = useState<TimelineEvent[]>([]);
  const [majorEvents, setMajorEvents] = useState<MajorEventEntry[]>([]);

  useEffect(() => {
    if (USE_MOCK_DATA) {
      // Simulate a brief loading state for realistic UX
      const timer = setTimeout(() => {
        setSessions(mockSessions);
        setTasks(mockTasks);
        setTimeline(mockTimeline);
        setUnifiedTimeline(mockUnifiedTimeline);
        setMajorEvents(mockMajorEvents);
        setIsLoading(false);
      }, 300); // 300ms delay simulates network request

      return () => clearTimeout(timer);
    }

    // Fetch real data from API
    const fetchSessions = async () => {
      // Get demo patient ID
      const patientId = demoTokenStorage.getPatientId();
      if (!patientId) {
        console.error('[SessionData] No patient ID found');
        setIsLoading(false);
        return;
      }

      console.log('[SessionData] Fetching sessions for patient:', patientId);

      try {
        // Fetch sessions from API
        const result = await apiClient.get<{ sessions: Session[] }>(
          `/api/sessions/patient/${patientId}`
        );

        if (result.success) {
          console.log('[SessionData] ✓ Loaded sessions:', result.data.sessions.length);
          setSessions(result.data.sessions);
          // TODO: Fetch tasks from API when endpoint is ready
          setTasks([]);
          setTimeline([]);
          setUnifiedTimeline([]);
          setMajorEvents([]);
        } else {
          console.error('[SessionData] ✗ Failed to fetch sessions:', result.error);
        }
      } catch (error) {
        console.error('[SessionData] Error:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSessions();
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
    isError: false,
    error: null,
    refresh,
    updateMajorEventReflection,
    sessionCount: sessions.length,
    majorEventCount: majorEvents.length,
    isEmpty: !isLoading && sessions.length === 0,
  };
}
