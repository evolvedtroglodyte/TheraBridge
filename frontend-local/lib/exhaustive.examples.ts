/**
 * EXAMPLES: Exhaustive Type Checking
 *
 * This file demonstrates best practices for using the exhaustive checking utilities.
 * These are NOT real code - they're educational examples showing patterns.
 * Delete this file once you understand the patterns.
 */

import {
  assertNever,
  buildExhaustive,
  match,
  matchWith,
  isValidValue,
} from './exhaustive';
import type {
  SessionStatus,
  SessionMood,
  MoodTrajectory,
  StrategyStatus,
  StrategyCategory,
  TriggerSeverity,
} from './types';

// ============================================================================
// EXAMPLE 1: Switch Statement with assertNever
// ============================================================================

export function statusToEmoji(status: SessionStatus): string {
  switch (status) {
    case 'uploading':
      return '📤';
    case 'transcribing':
      return '📝';
    case 'transcribed':
      return '✓';
    case 'extracting_notes':
      return '🤖';
    case 'processed':
      return '✅';
    case 'failed':
      return '❌';
    default:
      // TypeScript ERROR if any case is missing from the switch above
      return assertNever(status);
  }
}

// ============================================================================
// EXAMPLE 2: Lookup Table with buildExhaustive
// ============================================================================

export const moodColors = buildExhaustive<SessionMood, string>({
  very_low: '#DC2626',    // red-600
  low: '#F97316',         // orange-500
  neutral: '#9CA3AF',     // gray-400
  positive: '#4ADE80',    // green-400
  very_positive: '#16A34A', // green-600
});

export function getMoodColor(mood: SessionMood): string {
  return moodColors[mood];
}

// ============================================================================
// EXAMPLE 3: Complex Configuration Object
// ============================================================================

interface StrategyConfig {
  label: string;
  description: string;
  icon: string;
  treatmentPhase: 'early' | 'middle' | 'late';
}

export const strategyConfigs = buildExhaustive<StrategyCategory, StrategyConfig>({
  breathing: {
    label: 'Breathing Techniques',
    description: 'Controlled breathing exercises for anxiety',
    icon: '🌬️',
    treatmentPhase: 'early',
  },
  cognitive: {
    label: 'Cognitive Restructuring',
    description: 'Challenge and reframe negative thoughts',
    icon: '💭',
    treatmentPhase: 'middle',
  },
  behavioral: {
    label: 'Behavioral Activation',
    description: 'Gradually increase positive activities',
    icon: '🎯',
    treatmentPhase: 'middle',
  },
  mindfulness: {
    label: 'Mindfulness & Acceptance',
    description: 'Present-moment awareness practices',
    icon: '🧘',
    treatmentPhase: 'late',
  },
  interpersonal: {
    label: 'Interpersonal Therapy',
    description: 'Improve relationships and communication',
    icon: '🤝',
    treatmentPhase: 'middle',
  },
});

// ============================================================================
// EXAMPLE 4: Using match() for Pattern Matching
// ============================================================================

export function statusMessage(status: SessionStatus): string {
  return match(status, {
    uploading: () => 'Audio file is being uploaded to the server...',
    transcribing: () => 'Converting audio to text...',
    transcribed: () => 'Transcription complete. Processing...',
    extracting_notes: () => 'Extracting clinical notes and insights...',
    processed: () => 'Session processing complete!',
    failed: () => 'An error occurred during processing.',
  });
}

// ============================================================================
// EXAMPLE 5: Using matchWith() to Pass Data
// ============================================================================

interface SessionData {
  id: string;
  duration: number;
  timestamp: Date;
}

export function statusWithDetails(
  status: SessionStatus,
  session: SessionData
): string {
  return matchWith(status, session, {
    uploading: (s) => `Uploading ${s.duration}s session...`,
    transcribing: (s) => `Transcribing session ${s.id}...`,
    transcribed: (s) => `Session from ${s.timestamp.toLocaleDateString()} transcribed`,
    extracting_notes: (s) => `Processing notes from ${s.id}...`,
    processed: (s) => `Session ${s.id} is ready!`,
    failed: (s) => `Processing failed for session ${s.id}`,
  });
}

// ============================================================================
// EXAMPLE 6: Conditional Rendering Helper
// ============================================================================

interface RenderHandlers<T, R> {
  [key: string]: (data: T) => R;
}

export function renderByMood(
  mood: SessionMood,
  handlers: {
    very_low: () => React.ReactNode;
    low: () => React.ReactNode;
    neutral: () => React.ReactNode;
    positive: () => React.ReactNode;
    very_positive: () => React.ReactNode;
  }
): React.ReactNode {
  switch (mood) {
    case 'very_low':
      return handlers.very_low();
    case 'low':
      return handlers.low();
    case 'neutral':
      return handlers.neutral();
    case 'positive':
      return handlers.positive();
    case 'very_positive':
      return handlers.very_positive();
    default:
      return assertNever(mood);
  }
}

// ============================================================================
// EXAMPLE 7: Type Guard with isValidValue
// ============================================================================

export function isProcessedStatus(
  status: SessionStatus
): status is 'processed' | 'failed' {
  return isValidValue(status, ['processed', 'failed']);
}

export function isInProgressStatus(
  status: SessionStatus
): status is 'uploading' | 'transcribing' | 'extracting_notes' {
  return isValidValue(status, ['uploading', 'transcribing', 'extracting_notes']);
}

// ============================================================================
// EXAMPLE 8: Severity-Based Styling
// ============================================================================

export const triggerSeverityStyles = buildExhaustive<
  TriggerSeverity,
  { bgColor: string; textColor: string; borderColor: string; label: string }
>({
  mild: {
    bgColor: 'bg-yellow-50',
    textColor: 'text-yellow-800',
    borderColor: 'border-yellow-200',
    label: 'Mild Trigger',
  },
  moderate: {
    bgColor: 'bg-orange-50',
    textColor: 'text-orange-800',
    borderColor: 'border-orange-200',
    label: 'Moderate Trigger',
  },
  severe: {
    bgColor: 'bg-red-50',
    textColor: 'text-red-800',
    borderColor: 'border-red-200',
    label: 'Severe Trigger',
  },
});

// ============================================================================
// EXAMPLE 9: Trajectory Animation Mapping
// ============================================================================

export const trajectoryAnimation = buildExhaustive<
  MoodTrajectory,
  { animation: string; direction: 'up' | 'down' | 'flat'; speed: 'slow' | 'normal' | 'fast' }
>({
  improving: {
    animation: 'trend-up',
    direction: 'up',
    speed: 'normal',
  },
  declining: {
    animation: 'trend-down',
    direction: 'down',
    speed: 'normal',
  },
  stable: {
    animation: 'trend-flat',
    direction: 'flat',
    speed: 'slow',
  },
  fluctuating: {
    animation: 'trend-wave',
    direction: 'up', // arbitrary
    speed: 'fast',
  },
});

// ============================================================================
// EXAMPLE 10: Real-World Component Pattern
// ============================================================================

interface BadgeProps {
  status: SessionStatus;
  size?: 'sm' | 'md' | 'lg';
}

// This is how SessionStatusBadge.tsx is structured
export const statusBadgeConfig = buildExhaustive<
  SessionStatus,
  {
    label: string;
    icon: string;
    className: string;
    spinning: boolean;
  }
>({
  uploading: {
    label: 'Uploading',
    icon: '📤',
    className: 'bg-blue-100 text-blue-800',
    spinning: true,
  },
  transcribing: {
    label: 'Transcribing',
    icon: '📝',
    className: 'bg-yellow-100 text-yellow-800',
    spinning: true,
  },
  transcribed: {
    label: 'Transcribed',
    icon: '✓',
    className: 'bg-purple-100 text-purple-800',
    spinning: false,
  },
  extracting_notes: {
    label: 'Extracting Notes',
    icon: '🤖',
    className: 'bg-purple-100 text-purple-800',
    spinning: true,
  },
  processed: {
    label: 'Processed',
    icon: '✅',
    className: 'bg-green-100 text-green-800',
    spinning: false,
  },
  failed: {
    label: 'Failed',
    icon: '❌',
    className: 'bg-red-100 text-red-800',
    spinning: false,
  },
});

// Usage in a React component (pseudocode):
/*
export function StatusBadge({ status, size }: BadgeProps) {
  const config = statusBadgeConfig[status];
  const sizeClass = size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-lg' : 'text-base';

  return (
    <div className={`badge ${config.className} ${sizeClass}`}>
      <span className={config.spinning ? 'spin' : ''}>{config.icon}</span>
      {config.label}
    </div>
  );
}
*/

// ============================================================================
// BONUS: Union Type Combinations
// ============================================================================

/**
 * Example of handling multiple related types exhaustively.
 * This pattern is useful when you need to coordinate different enum types.
 */
export const strategyPhaseMapping = buildExhaustive<
  StrategyCategory,
  {
    bestForMood: SessionMood;
    trajectory: MoodTrajectory;
    status: StrategyStatus;
  }
>({
  breathing: {
    bestForMood: 'very_low',
    trajectory: 'improving',
    status: 'introduced',
  },
  cognitive: {
    bestForMood: 'low',
    trajectory: 'improving',
    status: 'practiced',
  },
  behavioral: {
    bestForMood: 'neutral',
    trajectory: 'stable',
    status: 'assigned',
  },
  mindfulness: {
    bestForMood: 'positive',
    trajectory: 'improving',
    status: 'reviewed',
  },
  interpersonal: {
    bestForMood: 'very_positive',
    trajectory: 'fluctuating',
    status: 'practiced',
  },
});

// ============================================================================
// LEARNING CHECKLIST
// ============================================================================

/**
 * How to know when you need exhaustive checking:
 *
 * ✓ You have a switch statement handling a union type or enum
 * ✓ You have multiple if-else conditions checking type/status values
 * ✓ You have a lookup object/config mapping all enum values
 * ✓ You want TypeScript to error when new enum values are added but not handled
 * ✓ You want to prevent runtime errors from missing cases
 *
 * When to use each utility:
 *
 * assertNever(x: never)
 * - Use in: default case of switch statements, end of if-else chains
 * - When: You want to guarantee all cases are handled
 * - Result: Compile error if any case is missing
 *
 * buildExhaustive<T, V>()
 * - Use in: Configuration objects, lookup tables, style mappings
 * - When: Creating an object with one entry per enum/union value
 * - Result: Compile error if any key is missing
 *
 * match(value, handlers)
 * - Use in: When you want pattern matching without a switch statement
 * - When: Multiple handlers based on a single value
 * - Result: Cleaner, more functional style code
 *
 * matchWith(value, data, handlers)
 * - Use in: When handlers need access to additional data
 * - When: Passing context through handlers
 * - Result: Cleaner than closures or complex switch statements
 *
 * isValidValue(value, allowed)
 * - Use in: Runtime type guards, validation
 * - When: Need to narrow a union type at runtime
 * - Result: TypeScript recognizes narrowed type after guard
 */

export type { SessionStatus, SessionMood, MoodTrajectory, StrategyStatus, StrategyCategory, TriggerSeverity };
