'use client';

/**
 * Session Data Context for Dashboard-v3
 *
 * Provides real session data to all dashboard components.
 * This replaces the static mockData imports with live API data.
 *
 * Usage:
 *   const { sessions, tasks, isLoading } = useSessionData();
 */

import { createContext, useContext, ReactNode } from 'react';
import { usePatientSessions } from '../lib/usePatientSessions';
import { Session, Task, TimelineEntry, TimelineEvent, MajorEventEntry } from '../lib/types';

interface SessionDataContextType {
  sessions: Session[];
  tasks: Task[];
  timeline: TimelineEntry[];
  /** Unified timeline with sessions + major events, sorted chronologically */
  unifiedTimeline: TimelineEvent[];
  /** Major events from chatbot conversations */
  majorEvents: MajorEventEntry[];
  isLoading: boolean;
  isError: boolean;
  error: unknown;
  refresh: () => void;
  /** Update reflection text for a major event */
  updateMajorEventReflection: (eventId: string, reflection: string) => void;
  sessionCount: number;
  majorEventCount: number;
  isEmpty: boolean;
}

const SessionDataContext = createContext<SessionDataContextType | null>(null);

/**
 * Provider component that fetches and distributes session data
 */
export function SessionDataProvider({ children }: { children: ReactNode }) {
  const data = usePatientSessions();

  return (
    <SessionDataContext.Provider value={data}>
      {children}
    </SessionDataContext.Provider>
  );
}

/**
 * Hook to access session data in any dashboard component
 *
 * @throws If used outside of SessionDataProvider
 */
export function useSessionData(): SessionDataContextType {
  const context = useContext(SessionDataContext);

  if (!context) {
    throw new Error(
      'useSessionData must be used within a SessionDataProvider. ' +
      'Wrap your dashboard with <SessionDataProvider>.'
    );
  }

  return context;
}
