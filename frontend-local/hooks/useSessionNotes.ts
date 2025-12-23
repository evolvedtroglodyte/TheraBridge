import { useSWRTyped, type UseSWRHookReturn } from '@/lib/swr-wrapper';
import { fetcher, type ApiError } from '@/lib/api';
import type { SessionNote } from '@/lib/types';

/**
 * Extended return type for useSessionNotes
 */
export interface UseSessionNotesReturn extends UseSWRHookReturn<SessionNote[], ApiError> {
  /** The session notes data (alias for `data`) */
  notes: SessionNote[] | undefined;
}

/**
 * Fetches all notes for a specific therapy session
 *
 * Returns all SessionNote records associated with a therapy session,
 * ordered by creation date (newest first).
 *
 * @param sessionId - The session ID to fetch notes for, or null to disable the request
 * @returns Hook return with notes data, loading state, error state, and refresh function
 *
 * @example
 * ```ts
 * const { notes, isLoading, refresh } = useSessionNotes(sessionId);
 *
 * // Refresh after creating a new note
 * await createNote(...);
 * refresh();
 * ```
 */
export function useSessionNotes(
  sessionId: string | null
): UseSessionNotesReturn {
  const swr = useSWRTyped<SessionNote[], ApiError>(
    sessionId ? `/api/v1/sessions/${sessionId}/notes` : null,
    fetcher,
    {
      // Cache for 30 seconds - notes may be edited frequently
      dedupingInterval: 30000,
      // Revalidate on focus to pick up changes from other tabs
      revalidateOnFocus: true,
      // Revalidate on reconnect for network resilience
      revalidateOnReconnect: true,
    }
  );

  return {
    notes: swr.data,
    data: swr.data,
    isLoading: swr.isLoading,
    isError: !!swr.error,
    error: swr.error,
    refresh: swr.mutate,
  };
}
