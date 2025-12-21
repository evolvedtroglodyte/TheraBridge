import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { classifyError } from '@/lib/utils';
import type { TranscriptionResult } from '@/types/transcription';

interface UseTranscriptionReturn {
  result: TranscriptionResult | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useTranscription(jobId: string | null): UseTranscriptionReturn {
  const [result, setResult] = useState<TranscriptionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchTranscription = async () => {
    if (!jobId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await apiClient.getTranscription(jobId);
      setResult(data);
    } catch (err) {
      setError(classifyError(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTranscription();
  }, [jobId]);

  return {
    result,
    loading,
    error,
    refetch: fetchTranscription,
  };
}
