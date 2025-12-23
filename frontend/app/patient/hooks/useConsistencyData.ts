'use client';

import { useState, useEffect } from 'react';
import { apiClient } from '../../../lib/api-client';

export interface ConsistencyMetrics {
  consistency_score: number;
  attendance_rate: number;
  average_gap_days: number;
  longest_streak_weeks: number;
  missed_weeks: number;
  weekly_data: Array<{
    week: string;
    attended: number;
    session_count: number;
    week_start: string;
  }>;
  total_sessions: number;
  expected_sessions: number;
  period_start: string;
  period_end: string;
}

interface UseConsistencyDataResult {
  data: ConsistencyMetrics | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

/**
 * Hook to fetch patient session consistency metrics
 * @param patientId - Patient UUID
 * @param days - Number of days to analyze (default: 90)
 * @param enabled - Whether to fetch data (default: true)
 */
export function useConsistencyData(
  patientId: string,
  days: number = 90,
  enabled: boolean = true
): UseConsistencyDataResult {
  const [data, setData] = useState<ConsistencyMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    if (!enabled || !patientId) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await apiClient.getPatientConsistency<ConsistencyMetrics>(patientId, days);

      if (result.success) {
        setData(result.data);
      } else {
        setError('error' in result ? result.error : 'Failed to fetch consistency data');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [patientId, days, enabled]);

  return {
    data,
    isLoading,
    error,
    refetch: fetchData,
  };
}
