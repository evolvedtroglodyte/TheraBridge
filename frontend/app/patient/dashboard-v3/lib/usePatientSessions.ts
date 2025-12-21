'use client';

/**
 * Patient Sessions Hook for Dashboard-v3
 *
 * Uses MOCK DATA for frontend development and testing.
 * This allows you to see visual changes immediately without needing
 * backend authentication or API calls.
 *
 * When ready for production, set USE_MOCK_DATA = false to use real API.
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

// ═══════════════════════════════════════════════════════════════════════════
// TOGGLE THIS TO SWITCH BETWEEN MOCK AND REAL DATA
// Set to `false` when you have a working authenticated backend
// ═══════════════════════════════════════════════════════════════════════════
const USE_MOCK_DATA = true;

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

    // TODO: When USE_MOCK_DATA is false, fetch from real API here
    setIsLoading(false);
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
