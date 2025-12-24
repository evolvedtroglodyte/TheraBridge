/**
 * Mood Mapper Utility
 * Maps numeric mood scores (0.0-10.0) to categorical mood types
 * for use with custom emoji rendering.
 */

export type MoodCategory = 'sad' | 'neutral' | 'happy';

/**
 * Maps a numeric mood score (0.0-10.0) to a categorical mood type.
 *
 * Ranges:
 * - 0.0-3.5: sad (distressed, severe symptoms)
 * - 4.0-6.5: neutral (mild symptoms to stable baseline)
 * - 7.0-10.0: happy (positive, thriving)
 *
 * @param score - Numeric mood score from 0.0 to 10.0
 * @returns Categorical mood type ('sad', 'neutral', or 'happy')
 */
export function mapNumericMoodToCategory(score: number | null | undefined): MoodCategory {
  // Handle null/undefined
  if (score === null || score === undefined) {
    return 'neutral'; // Default to neutral for missing data
  }

  // Clamp to valid range
  const clampedScore = Math.max(0, Math.min(10, score));

  // Map to categories
  if (clampedScore <= 3.5) {
    return 'sad';
  } else if (clampedScore <= 6.5) {
    return 'neutral';
  } else {
    return 'happy';
  }
}

/**
 * Formats a numeric mood score for display.
 *
 * @param score - Numeric mood score from 0.0 to 10.0
 * @returns Formatted string (e.g., "7.5") or "N/A" if missing
 */
export function formatMoodScore(score: number | null | undefined): string {
  if (score === null || score === undefined) {
    return 'N/A';
  }

  return score.toFixed(1);
}
