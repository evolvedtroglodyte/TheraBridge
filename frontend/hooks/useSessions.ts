import useSWR from 'swr';
import { fetcher } from '@/lib/api';
import type { Session, SessionStatus } from '@/lib/types';

export interface UseSessionsOptions {
  patientId?: string;
  status?: SessionStatus;
  // Allow override of refresh interval if needed (default: 30s, disabled when status is 'processed' or 'failed')
  refreshInterval?: number;
}

export function useSessions(options?: UseSessionsOptions) {
  const params = new URLSearchParams();
  if (options?.patientId) params.set('patient_id', options.patientId);
  if (options?.status) params.set('status', options.status);
  const queryString = params.toString();
  const endpoint = `/api/sessions/${queryString ? `?${queryString}` : ''}`;

  // Determine refresh interval:
  // - Processed/failed sessions: no refresh (they don't change)
  // - In-progress sessions: poll every 30s
  // - Explicit override: use provided refreshInterval
  const getRefreshInterval = () => {
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

  const { data, error, mutate, isLoading } = useSWR<Session[]>(
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
    sessions: data,
    isLoading,
    isError: !!error,
    error,
    refresh: mutate,
  };
}
