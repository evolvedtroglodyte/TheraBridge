import { useSWRTyped, type UseSWRHookReturn } from '@/lib/swr-wrapper';
import { fetcher, type ApiError } from '@/lib/api';
import type { Session } from '@/lib/types';
import { useCallback } from 'react';

/**
 * Configuration options for the useOptimisticSession hook
 */
export interface UseOptimisticSessionOptions {
  /** Override the default refresh interval (ms). By default: 5s while processing, 0 otherwise */
  refreshInterval?: number;
}

/**
 * Extended return type for useOptimisticSession with optimistic mutations
 */
export interface UseOptimisticSessionReturn extends UseSWRHookReturn<Session, ApiError> {
  /** The session data (alias for `data`) */
  session: Session | undefined;
  /** Whether the session is currently being processed */
  isProcessing: boolean;
  /** Mutate session data with optimistic updates */
  mutate: (
    session: Session | ((current: Session | undefined) => Session),
    options?: { revalidate?: boolean }
  ) => Promise<Session | undefined>;
}

/**
 * Fetches a single session with optimistic update support
 *
 * Automatically polls while processing, and supports optimistic updates
 * that immediately show UI changes and revert on error.
 *
 * @param sessionId - The session ID to fetch, or null to disable the request
 * @param options - Configuration options (refreshInterval override, etc.)
 * @returns Hook return with session data, loading state, processing status, and optimistic mutate
 *
 * @example
 * ```ts
 * const { session, mutate } = useOptimisticSession(sessionId);
 *
 * // Optimistically update status while the actual request completes
 * await mutate(
 *   { ...session, status: 'processed' },
 *   { revalidate: true }
 * );
 * ```
 */
export function useOptimisticSession(
  sessionId: string | null,
  options?: UseOptimisticSessionOptions
): UseOptimisticSessionReturn {
  const isProcessing = (data?: Session): boolean =>
    data?.status === 'uploading' ||
    data?.status === 'transcribing' ||
    data?.status === 'extracting_notes';

  const getRefreshInterval = (data?: Session): number => {
    if (options?.refreshInterval !== undefined) {
      return options.refreshInterval;
    }
    return isProcessing(data) ? 5000 : 0;
  };

  const swr = useSWRTyped<Session, ApiError>(
    sessionId ? `/api/sessions/${sessionId}` : null,
    fetcher,
    {
      refreshInterval: (latestData) => getRefreshInterval(latestData),
      dedupingInterval: 60000,
      revalidateOnFocus: false,
      revalidateOnReconnect: true,
    }
  );

  /**
   * Mutate session with optimistic update support
   * Immediately shows optimistic data, reverts on error
   */
  const optimisticMutate = useCallback(
    async (
      optimisticSession: Session | ((current: Session | undefined) => Session),
      options?: { revalidate?: boolean }
    ) => {
      return swr.mutate(optimisticSession, {
        optimisticData:
          typeof optimisticSession === 'function'
            ? optimisticSession(swr.data)
            : optimisticSession,
        rollbackOnError: true,
        revalidate: options?.revalidate !== false,
      });
    },
    [swr]
  );

  return {
    session: swr.data,
    data: swr.data,
    isLoading: swr.isLoading,
    isError: !!swr.error,
    error: swr.error,
    isProcessing: isProcessing(swr.data),
    mutate: optimisticMutate,
    refresh: swr.mutate,
  };
}
