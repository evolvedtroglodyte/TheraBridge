import useSWR from 'swr';
import { fetcher } from '@/lib/api';
import type { Session } from '@/lib/types';

export interface UseSessionOptions {
  refreshInterval?: number;
}

export function useSession(sessionId: string | null, options?: UseSessionOptions) {
  const { data, error, mutate, isLoading } = useSWR<Session>(
    sessionId ? `/api/sessions/${sessionId}` : null,
    fetcher,
    {
      refreshInterval: options?.refreshInterval ?? 0,
      revalidateOnFocus: true,
      revalidateOnReconnect: true,
    }
  );

  const isProcessing =
    data?.status === 'uploading' ||
    data?.status === 'transcribing' ||
    data?.status === 'extracting_notes';

  // Automatically poll while processing
  const shouldPoll = isProcessing && !options?.refreshInterval;

  useSWR<Session>(
    shouldPoll && sessionId ? `/api/sessions/${sessionId}` : null,
    fetcher,
    {
      refreshInterval: 5000, // Poll every 5 seconds while processing
      revalidateOnFocus: true,
    }
  );

  return {
    session: data,
    isLoading,
    isError: !!error,
    error,
    isProcessing,
    refresh: mutate,
  };
}
