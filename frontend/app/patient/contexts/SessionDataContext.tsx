'use client';

/**
 * Session Data Context for Dashboard-v3
 *
 * Provides real session data to all dashboard components.
 * This replaces the static mockData imports with live API data.
 *
 * NEW: Auto-refreshes when audio processing completes via ProcessingContext.
 *
 * Usage:
 *   const { sessions, tasks, isLoading } = useSessionData();
 */

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
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
  /** Session IDs currently loading (showing overlay) */
  loadingSessions: Set<string>;
  /** Set a session as loading */
  setSessionLoading: (sessionId: string, loading: boolean) => void;
  /** Patient ID for API calls (from demo token or auth) */
  patientId: string | null;
  /** Whether roadmap is currently being generated */
  loadingRoadmap: boolean;
  /** Increments when roadmap data should be refetched */
  roadmapRefreshTrigger: number;
  /** Trigger roadmap refresh (for SSE handler when Wave 2 completes) */
  setRoadmapRefreshTrigger: React.Dispatch<React.SetStateAction<number>>;
}

const SessionDataContext = createContext<SessionDataContextType | null>(null);

/**
 * Provider component that fetches and distributes session data
 *
 * Note: For auto-refresh on processing complete, wrap this with ProcessingProvider
 * and use the useProcessingRefresh hook in a child component.
 */
export function SessionDataProvider({ children }: { children: ReactNode }) {
  const data = usePatientSessions();

  // loadingSessions and setSessionLoading are now provided by usePatientSessions hook
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
