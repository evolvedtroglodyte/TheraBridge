'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

interface DeleteSessionOptions {
  sessionId: string;
  patientName?: string;
  onSuccess?: () => void | Promise<void>;
}

export function useDeleteSession() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const deleteSession = async (options: DeleteSessionOptions) => {
    const { sessionId, patientName, onSuccess } = options;
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/sessions/${sessionId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete session');
      }

      if (onSuccess) {
        await onSuccess();
      }

      // Redirect to therapist dashboard after deletion
      router.push('/therapist');
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete session';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    deleteSession,
    isLoading,
    error,
  };
}
