import { useSWRTyped } from '@/lib/swr-wrapper';
import { fetcher, type ApiError } from '@/lib/api';
import type { Patient } from '@/lib/types';

// SWR configuration for patient data - prevents duplicate requests
const patientSWRConfig = {
  // Prevent duplicate requests within 5 minutes (patient data doesn't change often)
  dedupingInterval: 300000,
  // Don't revalidate on focus to avoid unnecessary refetches
  revalidateOnFocus: false,
  // Revalidate on reconnect for network resilience
  revalidateOnReconnect: true,
} as const;

/**
 * Fetches all patients for the current therapist
 *
 * @returns Hook return with patients array, loading state, error, and refresh function
 *
 * @example
 * ```ts
 * const { patients, isLoading, error, refresh } = usePatients();
 * ```
 */
export function usePatients() {
  const swr = useSWRTyped<Patient[], ApiError>(
    '/api/v1/patients/',
    fetcher,
    patientSWRConfig
  );

  return {
    patients: swr.data,
    data: swr.data,
    isLoading: swr.isLoading,
    isError: !!swr.error,
    error: swr.error,
    refresh: swr.mutate,
  };
}

/**
 * Fetches a single patient by ID
 *
 * @param patientId - The patient ID to fetch, or null to disable the request
 * @returns Hook return with patient object, loading state, error, and refresh function
 *
 * @example
 * ```ts
 * const { data: patient, isLoading } = usePatient(patientId);
 * ```
 */
export function usePatient(patientId: string | null) {
  const swr = useSWRTyped<Patient, ApiError>(
    patientId ? `/api/v1/patients/${patientId}` : null,
    fetcher,
    patientSWRConfig
  );

  return {
    patient: swr.data,
    data: swr.data,
    isLoading: swr.isLoading,
    isError: !!swr.error,
    error: swr.error,
    refresh: swr.mutate,
  };
}
