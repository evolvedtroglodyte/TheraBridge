/**
 * useMoodAnalysis Hook
 *
 * Fetches and manages mood analysis data for therapy sessions.
 * Provides mood scores, trends, and analysis for ProgressPatternsCard visualization.
 */

import { useState, useEffect } from "react";
import { apiClient } from "@/lib/api-client";

export interface MoodAnalysisResult {
  session_id: string;
  mood_score: number; // 0.0 to 10.0
  confidence: number; // 0.0 to 1.0
  rationale: string;
  key_indicators: string[];
  emotional_tone: string;
  analyzed_at: string;
}

export interface MoodHistoryPoint {
  id: string;
  session_date: string;
  mood_score: number;
  mood_confidence: number;
  emotional_tone: string;
}

export interface MoodTrend {
  direction: "improving" | "declining" | "stable" | "variable";
  recent_avg: number;
  historical_avg: number;
  change: number;
}

interface UseMoodAnalysisOptions {
  patientId: string;
  autoAnalyze?: boolean; // Auto-trigger analysis for sessions without mood data
  limit?: number;
}

export function useMoodAnalysis({
  patientId,
  autoAnalyze = false,
  limit = 50,
}: UseMoodAnalysisOptions) {
  const [moodHistory, setMoodHistory] = useState<MoodHistoryPoint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trend, setTrend] = useState<MoodTrend | null>(null);

  // Fetch mood history for patient
  const fetchMoodHistory = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await apiClient.get<MoodHistoryPoint[]>(
        `/sessions/patient/${patientId}/mood-history?limit=${limit}`
      );

      const data = result.success ? result.data : [];
      setMoodHistory(data);

      // Calculate trend
      if (data.length >= 4) {
        const midpoint = Math.floor(data.length / 2);
        const recentScores = data.slice(midpoint);
        const historicalScores = data.slice(0, midpoint);

        const recentAvg =
          recentScores.reduce((sum, pt) => sum + pt.mood_score, 0) /
          recentScores.length;
        const historicalAvg =
          historicalScores.reduce((sum, pt) => sum + pt.mood_score, 0) /
          historicalScores.length;

        const change = recentAvg - historicalAvg;

        let direction: MoodTrend["direction"] = "stable";
        if (change > 1.0) direction = "improving";
        else if (change < -1.0) direction = "declining";
        else if (Math.abs(change) < 0.5) direction = "stable";
        else direction = "variable";

        setTrend({
          direction,
          recent_avg: recentAvg,
          historical_avg: historicalAvg,
          change,
        });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch mood history");
      console.error("Error fetching mood history:", err);
    } finally {
      setIsLoading(false);
    }
  };

  // Analyze mood for a specific session
  const analyzeSessionMood = async (
    sessionId: string,
    force = false
  ): Promise<MoodAnalysisResult | null> => {
    try {
      const result = await apiClient.post<MoodAnalysisResult>(
        `/sessions/${sessionId}/analyze-mood`,
        { force }
      );

      // Refresh mood history after analysis
      await fetchMoodHistory();

      return result.success ? result.data : null;
    } catch (err) {
      console.error("Error analyzing session mood:", err);
      return null;
    }
  };

  // Auto-fetch on mount
  useEffect(() => {
    if (patientId) {
      fetchMoodHistory();
    }
  }, [patientId, limit]);

  return {
    moodHistory,
    trend,
    isLoading,
    error,
    analyzeSessionMood,
    refetch: fetchMoodHistory,
  };
}
