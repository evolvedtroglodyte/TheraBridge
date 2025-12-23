import { useState, useMemo } from 'react';
import type { Patient } from '@/lib/types';

export type PatientSortField = 'name' | 'latest_session' | 'total_sessions';
export type SortOrder = 'asc' | 'desc';

export interface PatientSortConfig {
  field: PatientSortField;
  order: SortOrder;
}

export interface PatientStats {
  totalSessions: number;
  latestSessionDate?: string;
  actionItems: number;
  riskFlags: number;
}

export interface UsePatientSortReturn {
  sortConfig: PatientSortConfig;
  setSortField: (field: PatientSortField) => void;
  setSortOrder: (order: SortOrder) => void;
  sortedPatients: Patient[];
  toggleSortOrder: () => void;
}

/**
 * Hook to manage patient sorting with flexible sort field and order
 *
 * @param patients - Array of patients to sort
 * @param patientStats - Object mapping patient IDs to their stats (sessions, etc.)
 * @returns Object with current sort config, setters, sorted patients, and toggle function
 *
 * @example
 * ```ts
 * const { sortConfig, setSortField, sortedPatients } = usePatientSort(patients, statsMap);
 * ```
 */
export function usePatientSort(
  patients: Patient[] | undefined,
  patientStats?: Record<string, PatientStats>
): UsePatientSortReturn {
  const [sortConfig, setSortConfig] = useState<PatientSortConfig>({
    field: 'name',
    order: 'asc',
  });

  const sortedPatients = useMemo(() => {
    if (!patients) return [];

    const patientsCopy = [...patients];

    patientsCopy.sort((a, b) => {
      let compareValue = 0;

      switch (sortConfig.field) {
        case 'name':
          compareValue = a.name.localeCompare(b.name);
          break;

        case 'latest_session': {
          const dateA = patientStats?.[a.id]?.latestSessionDate || '';
          const dateB = patientStats?.[b.id]?.latestSessionDate || '';
          compareValue = new Date(dateA).getTime() - new Date(dateB).getTime();
          break;
        }

        case 'total_sessions': {
          const sessionsA = patientStats?.[a.id]?.totalSessions || 0;
          const sessionsB = patientStats?.[b.id]?.totalSessions || 0;
          compareValue = sessionsA - sessionsB;
          break;
        }

        default:
          compareValue = 0;
      }

      // Apply sort order (reverse if descending)
      return sortConfig.order === 'desc' ? -compareValue : compareValue;
    });

    return patientsCopy;
  }, [patients, sortConfig, patientStats]);

  return {
    sortConfig,
    setSortField: (field: PatientSortField) => {
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
    sortedPatients,
    toggleSortOrder: () => {
      setSortConfig((prev) => ({
        ...prev,
        order: prev.order === 'asc' ? 'desc' : 'asc',
      }));
    },
  };
}
