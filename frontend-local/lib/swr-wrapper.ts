import useSWR, { SWRConfiguration, SWRResponse } from 'swr';
import type { Fetcher } from 'swr';

/**
 * Typed configuration for SWR hooks with strict generics
 * Ensures consistent typing across all SWR usage in the application
 */
export interface UseSWROptions<T, E = Error> extends SWRConfiguration<T, E> {
  // Configuration options inherit from SWR's SWRConfiguration
}

/**
 * Wrapper for useSWR with explicit typing
 * Provides better type inference for data, error, and return types
 *
 * @template T - The type of data being fetched
 * @template E - The type of error (defaults to Error)
 *
 * @param key - SWR key (URL string or array, or null to disable)
 * @param fetcher - Async function that fetches the data
 * @param options - SWR configuration options
 * @returns SWRResponse with typed data and error
 *
 * @example
 * ```ts
 * const { data, error, isLoading } = useSWRTyped<Patient[]>(
 *   '/api/patients',
 *   fetcher,
 *   { revalidateOnFocus: false }
 * );
 * ```
 */
export function useSWRTyped<T, E = Error>(
  key: string | null | (string | null)[],
  fetcher: Fetcher<T>,
  options?: UseSWROptions<T, E>
): SWRResponse<T, E> {
  return useSWR<T, E>(key, fetcher, options);
}

/**
 * Typed hook return shape for consistency across all data-fetching hooks
 * Provides a standardized interface with data, loading, error, and refresh states
 */
export interface UseSWRHookReturn<T, E = Error> {
  /** The fetched data - undefined while loading */
  data: T | undefined;
  /** Whether the hook is currently loading data */
  isLoading: boolean;
  /** Whether an error occurred during fetch */
  isError: boolean;
  /** The error object if one occurred */
  error: E | undefined;
  /** Function to manually refresh/mutate the cached data */
  refresh: (data?: T | Promise<T>, shouldRevalidate?: boolean) => Promise<T | undefined>;
}

/**
 * Converts SWRResponse to the standardized UseSWRHookReturn format
 * Ensures consistent API across all data-fetching hooks
 *
 * @template T - The type of data being fetched
 * @template E - The type of error (defaults to Error)
 *
 * @param swr - The SWRResponse from useSWR
 * @returns Normalized hook return value
 *
 * @example
 * ```ts
 * const swr = useSWRTyped<Patient[]>('/api/patients', fetcher);
 * return normalizeSWRResponse(swr);
 * ```
 */
export function normalizeSWRResponse<T, E = Error>(
  swr: SWRResponse<T, E>
): UseSWRHookReturn<T, E> {
  return {
    data: swr.data,
    isLoading: swr.isLoading,
    isError: !!swr.error,
    error: swr.error,
    refresh: swr.mutate,
  };
}
