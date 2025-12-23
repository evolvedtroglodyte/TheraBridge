'use client';

import { useState, useMemo } from 'react';
import type { Session, SessionStatus } from '@/lib/types';

export type DateRangeFilter = 'all' | 'last-7-days' | 'last-30-days' | 'last-3-months';
export type StatusFilter = 'all' | 'processing' | 'completed' | 'failed';

interface UseSessionFiltersOptions {
  /** Initial status filter */
  initialStatus?: StatusFilter;
  /** Initial date range filter */
  initialDateRange?: DateRangeFilter;
}

/**
 * Hook for filtering sessions by status and date range
 *
 * Groups session statuses into three categories:
 * - processing: uploading, transcribing, transcribed, extracting_notes
 * - completed: processed
 * - failed: failed
 *
 * Date range filters are applied to session_date field.
 *
 * @example
 * ```ts
 * const { filteredSessions, statusFilter, dateRangeFilter, setStatusFilter, setDateRangeFilter } =
 *   useSessionFilters(sessions, { initialStatus: 'all', initialDateRange: 'last-30-days' });
 * ```
 */
export function useSessionFilters(
  sessions: Session[] | undefined,
  options?: UseSessionFiltersOptions
) {
  const [statusFilter, setStatusFilter] = useState<StatusFilter>(options?.initialStatus || 'all');
  const [dateRangeFilter, setDateRangeFilter] = useState<DateRangeFilter>(
    options?.initialDateRange || 'all'
  );

  /**
   * Gets the start date for a date range filter
   * Returns null for 'all' (no filtering)
   */
  const getStartDate = (filter: DateRangeFilter): Date | null => {
    const now = new Date();

    switch (filter) {
      case 'last-7-days':
        const sevenDaysAgo = new Date(now);
        sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
        return sevenDaysAgo;

      case 'last-30-days':
        const thirtyDaysAgo = new Date(now);
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        return thirtyDaysAgo;

      case 'last-3-months':
        const threeMonthsAgo = new Date(now);
        threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);
        return threeMonthsAgo;

      case 'all':
      default:
        return null;
    }
  };

  /**
   * Maps SessionStatus values to the filter categories
   */
  const getStatusCategory = (status: SessionStatus): StatusFilter => {
    switch (status) {
      case 'uploading':
      case 'transcribing':
      case 'transcribed':
      case 'extracting_notes':
        return 'processing';
      case 'processed':
        return 'completed';
      case 'failed':
        return 'failed';
      default:
        return 'all';
    }
  };

  /**
   * Filters sessions based on current filter settings
   */
  const filteredSessions = useMemo(() => {
    if (!sessions) return [];

    const startDate = getStartDate(dateRangeFilter);

    return sessions.filter((session) => {
      // Apply status filter
      if (statusFilter !== 'all') {
        const category = getStatusCategory(session.status);
        if (category !== statusFilter) {
          return false;
        }
      }

      // Apply date range filter
      if (startDate) {
        const sessionDate = new Date(session.session_date);
        if (sessionDate < startDate) {
          return false;
        }
      }

      return true;
    });
  }, [sessions, statusFilter, dateRangeFilter]);

  return {
    filteredSessions,
    statusFilter,
    setStatusFilter,
    dateRangeFilter,
    setDateRangeFilter,
  };
}
