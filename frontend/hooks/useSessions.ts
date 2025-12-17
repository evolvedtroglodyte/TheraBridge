import useSWR from 'swr';
import { fetcher } from '@/lib/api';
import type { Session, SessionStatus } from '@/lib/types';

export interface UseSessionsOptions {
  patientId?: string;
  status?: SessionStatus;
}

export function useSessions(options?: UseSessionsOptions) {
  const params = new URLSearchParams();
  if (options?.patientId) params.set('patient_id', options.patientId);
  if (options?.status) params.set('status', options.status);
  const queryString = params.toString();
  const endpoint = `/api/sessions/${queryString ? `?${queryString}` : ''}`;

  const { data, error, mutate, isLoading } = useSWR<Session[]>(
    endpoint,
    fetcher,
    {
      revalidateOnFocus: true,
      refreshInterval: 10000, // Refresh every 10 seconds to catch new sessions
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
