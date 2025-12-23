import { useSWRTyped } from '@/lib/swr-wrapper';
import { fetcher, type ApiError } from '@/lib/api';
import type { Session, SessionStatus } from '@/lib/types';

/**
 * Configuration options for the useSessions hook
 */
export interface UseSessionsOptions {
  /** Filter sessions by patient ID */
  patientId?: string;
  /** Filter sessions by status (processed, failed, uploading, etc.) */
  status?: SessionStatus;
  /** Override the default refresh interval (ms). By default: 30s for in-progress, 0 for completed */
  refreshInterval?: number;
}

/**
 * Fetches a list of sessions with filtering and intelligent polling
 *
 * Sessions are automatically filtered by patient ID and/or status.
 * Automatically polls every 30 seconds for in-progress sessions,
 * and disables polling for completed/failed sessions.
 *
 * @param options - Configuration options (patientId, status filter, refreshInterval override)
 * @returns Hook return with sessions array, loading state, error, and refresh function
 *
 * @example
 * ```ts
 * // Fetch all sessions for a specific patient
 * const { data: sessions, isLoading } = useSessions({ patientId: 'patient-123' });
 *
 * // Fetch only completed sessions
 * const { data: completedSessions } = useSessions({ status: 'processed' });
 * ```
 */
export function useSessions(
  options?: UseSessionsOptions
) {
  const params = new URLSearchParams();
  if (options?.patientId) params.set('patient_id', options.patientId);
  if (options?.status) params.set('status', options.status);
  const queryString = params.toString();
  const endpoint = `/api/v1/sessions/${queryString ? `?${queryString}` : ''}`;

  // Determine refresh interval:
  // - Processed/failed sessions: no refresh (they don't change)
  // - In-progress sessions: poll every 30s
  // - Explicit override: use provided refreshInterval
  const getRefreshInterval = (): number => {
    if (options?.refreshInterval !== undefined) {
      return options.refreshInterval;
    }
    // Don't poll processed/failed sessions - they're static
    if (options?.status === 'processed' || options?.status === 'failed') {
      return 0;
    }
    // Poll in-progress sessions but less aggressively than useSession
    return 30000;
  };

  const swr = useSWRTyped<Session[], ApiError>(
    endpoint,
    fetcher,
    {
      // Dynamic refresh interval based on session status
      refreshInterval: getRefreshInterval(),
      // Prevent duplicate requests within 2 minutes
      dedupingInterval: 120000,
      // Don't revalidate on focus to avoid unnecessary refetches
      revalidateOnFocus: false,
      // Revalidate on reconnect for network resilience
      revalidateOnReconnect: true,
    }
  );

  return {
    sessions: swr.data,
    data: swr.data,
    isLoading: swr.isLoading,
    isError: !!swr.error,
    error: swr.error,
    refresh: swr.mutate,
  };
}
