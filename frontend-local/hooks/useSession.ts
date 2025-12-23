import { useSWRTyped, type UseSWRHookReturn } from '@/lib/swr-wrapper';
import { fetcher, type ApiError } from '@/lib/api';
import type { Session } from '@/lib/types';

/**
 * Configuration options for the useSession hook
 */
export interface UseSessionOptions {
  /** Override the default refresh interval (ms). By default: 5s while processing, 0 otherwise */
  refreshInterval?: number;
}

/**
 * Extended return type for useSession with processing status
 * Includes additional processing state beyond the base hook return
 */
export interface UseSessionReturn extends UseSWRHookReturn<Session, ApiError> {
  /** The session data (alias for `data`) */
  session: Session | undefined;
  /** Whether the session is currently being processed (uploading, transcribing, or extracting notes) */
  isProcessing: boolean;
}

/**
 * Fetches a single session with intelligent polling based on processing status
 *
 * Automatically polls every 5 seconds while the session is being processed
 * (uploading, transcribing, or extracting notes), then stops polling once complete.
 *
 * @param sessionId - The session ID to fetch, or null to disable the request
 * @param options - Configuration options (refreshInterval override, etc.)
 * @returns Hook return with session data, loading state, processing status, and refresh function
 *
 * @example
 * ```ts
 * const { data: session, isProcessing, refresh } = useSession(sessionId);
 * if (isProcessing) {
 *   // Show loading indicator
 * }
 * ```
 */
export function useSession(
  sessionId: string | null,
  options?: UseSessionOptions
): UseSessionReturn {
  const isProcessing = (data?: Session): boolean =>
    data?.status === 'uploading' ||
    data?.status === 'transcribing' ||
    data?.status === 'extracting_notes';

  // Determine refresh interval: 5s while processing, 0 (disabled) otherwise
  // Respects explicit refreshInterval override from options
  const getRefreshInterval = (data?: Session): number => {
    if (options?.refreshInterval !== undefined) {
      return options.refreshInterval;
    }
    return isProcessing(data) ? 5000 : 0;
  };

  const swr = useSWRTyped<Session, ApiError>(
    sessionId ? `/api/v1/sessions/${sessionId}` : null,
    fetcher,
    {
      // Dynamic refresh interval based on processing status
      refreshInterval: (latestData) => getRefreshInterval(latestData),
      // Prevent duplicate requests within 60 seconds
      dedupingInterval: 60000,
      // Don't revalidate on focus - let manual refresh be explicit
      revalidateOnFocus: false,
      // Revalidate on reconnect for network resilience
      revalidateOnReconnect: true,
    }
  );

  return {
    session: swr.data,
    data: swr.data,
    isLoading: swr.isLoading,
    isError: !!swr.error,
    error: swr.error,
    isProcessing: isProcessing(swr.data),
    refresh: swr.mutate,
  };
}
