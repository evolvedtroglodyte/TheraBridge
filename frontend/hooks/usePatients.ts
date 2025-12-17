import useSWR from 'swr';
import { fetcher } from '@/lib/api';
import type { Patient } from '@/lib/types';

export function usePatients() {
  const { data, error, mutate, isLoading } = useSWR<Patient[]>(
    '/api/patients/',
    fetcher,
    {
      revalidateOnFocus: true,
    }
  );

  return {
    patients: data,
    isLoading,
    isError: !!error,
    error,
    refresh: mutate,
  };
}

export function usePatient(patientId: string | null) {
  const { data, error, mutate, isLoading } = useSWR<Patient>(
    patientId ? `/api/patients/${patientId}` : null,
    fetcher,
    {
      revalidateOnFocus: true,
    }
  );

  return {
    patient: data,
    isLoading,
    isError: !!error,
    error,
    refresh: mutate,
  };
}
