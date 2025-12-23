'use client';

import { useMemo } from 'react';
import { ProgressBar } from './ui/progress-bar';
import { StepIndicator, type Step } from './ui/step-indicator';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import type { Session } from '@/lib/types';

interface SessionProgressTrackerProps {
  /**
   * Session data with status information
   */
  session: Session | null;
  /**
   * Show simplified progress bar only
   */
  compact?: boolean;
  /**
   * Show step descriptions
   */
  showDescriptions?: boolean;
  /**
   * Custom title
   */
  title?: string;
  /**
   * Custom description
   */
  description?: string;
}

/**
 * Processing steps for session workflow
 * Maps to backend session status values
 */
const SESSION_STEPS = [
  {
    id: 'uploading',
    label: 'Uploading',
    description: 'Uploading audio file to server',
  },
  {
    id: 'transcribing',
    label: 'Transcribing',
    description: 'Converting audio to text using Whisper',
  },
  {
    id: 'extracting_notes',
    label: 'Extracting Notes',
    description: 'Analyzing transcript with AI',
  },
  {
    id: 'processed',
    label: 'Complete',
    description: 'Session processing finished',
  },
] as const;

/**
 * Maps backend session status to step progress
 */
const STATUS_TO_STEP_INDEX: Record<Session['status'] | 'failed', number> = {
  uploading: 0,
  transcribing: 1,
  transcribed: 2,
  extracting_notes: 2,
  processed: 3,
  failed: 0,
};

/**
 * Calculates progress percentage based on session status
 */
const getProgressPercentage = (status: Session['status'] | 'failed'): number => {
  switch (status) {
    case 'uploading':
      return 25;
    case 'transcribing':
      return 50;
    case 'transcribed':
      return 50;
    case 'extracting_notes':
      return 75;
    case 'processed':
      return 100;
    case 'failed':
      return 0;
    default:
      return 0;
  }
};

/**
 * SessionProgressTracker - Display session processing progress
 *
 * Shows a visual representation of session processing through multiple stages:
 * 1. Uploading - File being sent to server
 * 2. Transcribing - Converting audio to text
 * 3. Extracting Notes - AI analysis of transcript
 * 4. Complete - All processing finished
 *
 * @example
 * ```tsx
 * <SessionProgressTracker
 *   session={sessionData}
 *   showDescriptions={true}
 * />
 * ```
 */
export function SessionProgressTracker({
  session,
  compact = false,
  showDescriptions = false,
  title = 'Session Processing',
  description = 'Your session is being processed',
}: SessionProgressTrackerProps) {
  const steps = useMemo<Step[]>(() => {
    return SESSION_STEPS.map((step) => ({
      id: step.id,
      label: step.label,
      description: step.description,
      status: 'pending' as const,
    }));
  }, []);

  const currentStepIndex = useMemo(() => {
    if (!session) return 0;
    return STATUS_TO_STEP_INDEX[session.status] ?? 0;
  }, [session]);

  const progressPercentage = useMemo(() => {
    if (!session) return 0;
    return getProgressPercentage(session.status);
  }, [session]);

  // Determine step statuses
  const stepsWithStatus = useMemo<Step[]>(() => {
    return steps.map((step, index) => {
      if (!session) {
        return { ...step, status: 'pending' };
      }

      if (session.status === 'failed') {
        return { ...step, status: 'error' as const };
      }

      if (index < currentStepIndex) {
        return { ...step, status: 'completed' as const };
      } else if (index === currentStepIndex) {
        return { ...step, status: 'in-progress' as const };
      }

      return { ...step, status: 'pending' as const };
    });
  }, [steps, currentStepIndex, session]);

  // Get current step label
  const currentStepLabel = useMemo(() => {
    if (!session) return 'Waiting to start';

    switch (session.status) {
      case 'uploading':
        return 'Uploading your audio file...';
      case 'transcribing':
        return 'Converting audio to text...';
      case 'transcribed':
        return 'Preparing for analysis...';
      case 'extracting_notes':
        return 'Analyzing session content...';
      case 'processed':
        return 'Processing complete!';
      case 'failed':
        return `Processing failed: ${session.error_message || 'Unknown error'}`;
      default:
        return 'Processing...';
    }
  }, [session]);

  if (compact) {
    return (
      <div className="space-y-3">
        <div className="flex justify-between items-baseline">
          <p className="text-sm font-medium text-foreground">{currentStepLabel}</p>
          <p className="text-xs text-muted-foreground">{progressPercentage}%</p>
        </div>
        <ProgressBar
          value={progressPercentage}
          variant={session?.status === 'failed' ? 'destructive' : 'default'}
          showLabel={false}
          animated={session?.status !== 'processed' && session?.status !== 'failed'}
        />
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Progress Bar */}
        <div className="space-y-2">
          <div className="flex justify-between items-baseline">
            <p className="text-sm font-medium text-foreground">{currentStepLabel}</p>
            <p className="text-xs text-muted-foreground">{progressPercentage}%</p>
          </div>
          <ProgressBar
            value={progressPercentage}
            size="md"
            variant={session?.status === 'failed' ? 'destructive' : 'default'}
            showLabel={false}
            animated={session?.status !== 'processed' && session?.status !== 'failed'}
          />
        </div>

        {/* Step Indicator */}
        <StepIndicator
          steps={stepsWithStatus}
          currentStepIndex={currentStepIndex}
          orientation="horizontal"
          showDescriptions={showDescriptions}
        />

        {/* Error message if failed */}
        {session?.status === 'failed' && session?.error_message && (
          <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
            <p className="text-sm font-medium text-destructive">Processing Error</p>
            <p className="text-xs text-destructive/80 mt-2">{session.error_message}</p>
          </div>
        )}

        {/* Success message if complete */}
        {session?.status === 'processed' && (
          <div className="p-4 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800">
            <p className="text-sm font-medium text-green-700 dark:text-green-300">
              Session Ready
            </p>
            <p className="text-xs text-green-600 dark:text-green-400 mt-2">
              Your session has been fully processed and is ready to review.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export type { SessionProgressTrackerProps };
