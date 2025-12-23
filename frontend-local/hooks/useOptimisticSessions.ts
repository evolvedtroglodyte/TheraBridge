import { useSWRTyped } from '@/lib/swr-wrapper';
import { fetcher, type ApiError } from '@/lib/api';
import type { Session, SessionStatus } from '@/lib/types';
import { useCallback } from 'react';

/**
 * Configuration options for the useOptimisticSessions hook
 */
export interface UseOptimisticSessionsOptions {
  /** Filter sessions by patient ID */
  patientId?: string;
  /** Filter sessions by status (processed, failed, uploading, etc.) */
  status?: SessionStatus;
  /** Override the default refresh interval (ms). By default: 30s for in-progress, 0 for completed */
  refreshInterval?: number;
}

/**
 * Fetches sessions with optimistic update support
 *
 * Immediately updates the UI with optimistic data when mutations are triggered,
 * then reverts if the operation fails. Uses SWR's optimisticData pattern.
 *
 * @param options - Configuration options (patientId, status filter, refreshInterval override)
 * @returns Hook return with sessions array, loading state, error, refresh function, and optimistic mutate
 *
 * @example
 * ```ts
 * const { sessions, mutate } = useOptimisticSessions({ patientId: 'patient-123' });
 *
 * // When uploading, immediately show the new session in the list
 * const optimisticSession = {
 *   id: 'temp-id',
 *   status: 'uploading',
 *   // ... other fields
 * };
 *
 * await mutate(
 *   [...(sessions || []), optimisticSession],
 *   {
 *     optimisticData: [...(sessions || []), optimisticSession],
 *     rollbackOnError: true,
 *     revalidate: false,
 *   }
 * );
 * ```
 */
export function useOptimisticSessions(options?: UseOptimisticSessionsOptions) {
  const params = new URLSearchParams();
  if (options?.patientId) params.set('patient_id', options.patientId);
  if (options?.status) params.set('status', options.status);
  const queryString = params.toString();
  const endpoint = `/api/sessions/${queryString ? `?${queryString}` : ''}`;

  const getRefreshInterval = (): number => {
    if (options?.refreshInterval !== undefined) {
      return options.refreshInterval;
    }
    if (options?.status === 'processed' || options?.status === 'failed') {
      return 0;
    }
    return 30000;
  };

  const swr = useSWRTyped<Session[], ApiError>(endpoint, fetcher, {
    refreshInterval: getRefreshInterval(),
    dedupingInterval: 120000,
    revalidateOnFocus: false,
    revalidateOnReconnect: true,
  });

  /**
   * Mutate sessions with optimistic update support
   * Immediately shows optimistic data, reverts on error
   */
  const optimisticMutate = useCallback(
    async (
      optimisticSessions: Session[] | ((current: Session[] | undefined) => Session[]),
      options?: {
        /** Whether to revalidate after mutation completes */
        revalidate?: boolean;
      }
    ) => {
      return swr.mutate(optimisticSessions, {
        optimisticData:
          typeof optimisticSessions === 'function'
            ? optimisticSessions(swr.data)
            : optimisticSessions,
        rollbackOnError: true,
        revalidate: options?.revalidate !== false,
      });
    },
    [swr]
  );

  return {
    sessions: swr.data,
    data: swr.data,
    isLoading: swr.isLoading,
    isError: !!swr.error,
    error: swr.error,
    mutate: optimisticMutate,
    refresh: swr.mutate,
  };
}
