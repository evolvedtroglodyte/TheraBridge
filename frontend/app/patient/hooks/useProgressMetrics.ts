/**
 * Progress Metrics Hook
 *
 * Fetches and transforms progress metrics from backend API for ProgressPatternsCard.
 *
 * Features:
 * - Automatic fetching on mount
 * - Loading and error states
 * - Mock data fallback when API is disabled
 * - Direct compatibility with Recharts components
 *
 * Usage:
 * ```tsx
 * const { metrics, isLoading, error } = useProgressMetrics({
 *   patientId: '123',
 *   useRealData: true
 * });
 * ```
 */

import { useState, useEffect } from 'react';
import type { ProgressMetric } from '../lib/types';

// API base URL - fallback to localhost in development
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface UseProgressMetricsOptions {
  patientId: string;
  limit?: number;
  useRealData?: boolean;
}

interface ProgressMetricsResponse {
  metrics: ProgressMetric[];
  extracted_at: string;
  session_count: number;
  date_range: string;
}

interface UseProgressMetricsReturn {
  metrics: ProgressMetric[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
  sessionCount: number;
  dateRange: string;
}

/**
 * Custom hook to fetch progress metrics for a patient.
 *
 * @param options - Configuration options
 * @param options.patientId - Patient UUID
 * @param options.limit - Maximum number of sessions to include (default: 50)
 * @param options.useRealData - Enable API calls (default: false for mock data)
 *
 * @returns Progress metrics with loading/error states
 */
export function useProgressMetrics({
  patientId,
  limit = 50,
  useRealData = false,
}: UseProgressMetricsOptions): UseProgressMetricsReturn {
  const [metrics, setMetrics] = useState<ProgressMetric[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionCount, setSessionCount] = useState<number>(0);
  const [dateRange, setDateRange] = useState<string>('');

  const fetchMetrics = async () => {
    if (!useRealData) {
      // Return empty for mock mode (ProgressPatternsCard will use mockData.ts)
      setMetrics([]);
      setSessionCount(0);
      setDateRange('');
      setIsLoading(false);
      return;
    }

    if (!patientId) {
      setError('Patient ID is required');
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const url = `${API_BASE_URL}/sessions/patient/${patientId}/progress-metrics?limit=${limit}`;
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include', // Include cookies for authentication
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: Failed to fetch progress metrics`);
      }

      const data: ProgressMetricsResponse = await response.json();

      setMetrics(data.metrics);
      setSessionCount(data.session_count);
      setDateRange(data.date_range);
      setIsLoading(false);
    } catch (err) {
      console.error('Failed to fetch progress metrics:', err);
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
      setIsLoading(false);
    }
  };

  // Fetch on mount and when dependencies change
  useEffect(() => {
    fetchMetrics();
  }, [patientId, limit, useRealData]);

  return {
    metrics,
    isLoading,
    error,
    refetch: fetchMetrics,
    sessionCount,
    dateRange,
  };
}
