import { useState, useMemo } from 'react';
import type { Session } from '@/lib/types';

export type SortField = 'date' | 'patient_name' | 'status';
export type SortOrder = 'asc' | 'desc';

export interface SortConfig {
  field: SortField;
  order: SortOrder;
}

export interface UseSessionSortReturn {
  sortConfig: SortConfig;
  setSortField: (field: SortField) => void;
  setSortOrder: (order: SortOrder) => void;
  sortedSessions: Session[];
  toggleSortOrder: () => void;
}

/**
 * Hook to manage session sorting with flexible sort field and order
 *
 * @param sessions - Array of sessions to sort
 * @param patientMap - Optional map of patient IDs to patient names (used when sorting by patient_name)
 * @returns Object with current sort config, setters, sorted sessions, and toggle function
 *
 * @example
 * ```ts
 * const { sortConfig, setSortField, sortedSessions } = useSessionSort(sessions, patientMap);
 * ```
 */
export function useSessionSort(
  sessions: Session[] | undefined,
  patientMap?: Record<string, string>
): UseSessionSortReturn {
  const [sortConfig, setSortConfig] = useState<SortConfig>({
    field: 'date',
    order: 'desc',
  });

  const sortedSessions = useMemo(() => {
    if (!sessions) return [];

    const sessionsCopy = [...sessions];

    sessionsCopy.sort((a, b) => {
      let compareValue = 0;

      switch (sortConfig.field) {
        case 'date':
          compareValue =
            new Date(a.session_date).getTime() -
            new Date(b.session_date).getTime();
          break;

        case 'patient_name': {
          // Only available when patientMap is provided
          const nameA = patientMap?.[a.patient_id] || 'Unknown';
          const nameB = patientMap?.[b.patient_id] || 'Unknown';
          compareValue = nameA.localeCompare(nameB);
          break;
        }

        case 'status':
          compareValue = a.status.localeCompare(b.status);
          break;

        default:
          compareValue = 0;
      }

      // Apply sort order (reverse if descending)
      return sortConfig.order === 'desc' ? -compareValue : compareValue;
    });

    return sessionsCopy;
  }, [sessions, sortConfig, patientMap]);

  return {
    sortConfig,
    setSortField: (field: SortField) => {
      setSortConfig((prev) => ({
        ...prev,
        field,
      }));
    },
    setSortOrder: (order: SortOrder) => {
      setSortConfig((prev) => ({
        ...prev,
        order,
      }));
    },
    sortedSessions,
    toggleSortOrder: () => {
      setSortConfig((prev) => ({
        ...prev,
        order: prev.order === 'asc' ? 'desc' : 'asc',
      }));
    },
  };
}
