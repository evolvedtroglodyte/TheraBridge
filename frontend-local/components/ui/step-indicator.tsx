'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { CheckCircle2, Circle, AlertCircle, Clock } from 'lucide-react';

interface Step {
  /**
   * Unique identifier for the step
   */
  id: string;
  /**
   * Display label for the step
   */
  label: string;
  /**
   * Optional description of the step
   */
  description?: string;
  /**
   * Status of the step: 'pending' | 'in-progress' | 'completed' | 'error'
   */
  status?: 'pending' | 'in-progress' | 'completed' | 'error';
}

interface StepIndicatorProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Array of steps to display
   */
  steps: Step[];
  /**
   * Current active step index
   */
  currentStepIndex: number;
  /**
   * Orientation: 'horizontal' or 'vertical'
   */
  orientation?: 'horizontal' | 'vertical';
  /**
   * Show step descriptions
   */
  showDescriptions?: boolean;
  /**
   * Allow clicking on steps (interactive)
   */
  clickable?: boolean;
  /**
   * Callback when a step is clicked
   */
  onStepClick?: (stepIndex: number) => void;
}

const StepIndicator = React.forwardRef<HTMLDivElement, StepIndicatorProps>(
  (
    {
      className,
      steps,
      currentStepIndex,
      orientation = 'horizontal',
      showDescriptions = false,
      clickable = false,
      onStepClick,
      ...props
    },
    ref
  ) => {
    const getStepStatus = (index: number): Step['status'] => {
      if (steps[index]?.status) return steps[index].status;

      if (index < currentStepIndex) {
        return 'completed';
      } else if (index === currentStepIndex) {
        return 'in-progress';
      }
      return 'pending';
    };

    const getStepIcon = (index: number) => {
      const status = getStepStatus(index);

      switch (status) {
        case 'completed':
          return <CheckCircle2 className="w-6 h-6 text-green-600" />;
        case 'in-progress':
          return (
            <div className="relative w-6 h-6">
              <Clock className="w-6 h-6 text-primary animate-spin" />
            </div>
          );
        case 'error':
          return <AlertCircle className="w-6 h-6 text-destructive" />;
        case 'pending':
        default:
          return <Circle className="w-6 h-6 text-muted-foreground" />;
      }
    };

    const getStepBgColor = (index: number) => {
      const status = getStepStatus(index);

      switch (status) {
        case 'completed':
          return 'bg-green-50 dark:bg-green-950';
        case 'in-progress':
          return 'bg-primary/10';
        case 'error':
          return 'bg-destructive/10';
        case 'pending':
        default:
          return 'bg-muted';
      }
    };

    const getStepTextColor = (index: number) => {
      const status = getStepStatus(index);

      switch (status) {
        case 'completed':
          return 'text-green-700 dark:text-green-300';
        case 'in-progress':
          return 'text-primary font-semibold';
        case 'error':
          return 'text-destructive';
        case 'pending':
        default:
          return 'text-muted-foreground';
      }
    };

    if (orientation === 'vertical') {
      return (
        <div
          ref={ref}
          className={cn('flex flex-col gap-6 w-full', className)}
          {...props}
        >
          {steps.map((step, index) => (
            <div key={step.id} className="flex gap-4">
              {/* Icon and line */}
              <div className="flex flex-col items-center">
                <button
                  onClick={() => clickable && onStepClick?.(index)}
                  className={cn(
                    'relative z-10 rounded-full p-1 transition-colors',
                    clickable && 'cursor-pointer hover:bg-secondary'
                  )}
                  disabled={!clickable}
                  aria-current={getStepStatus(index) === 'in-progress' ? 'step' : undefined}
                >
                  {getStepIcon(index)}
                </button>

                {/* Connector line to next step */}
                {index < steps.length - 1 && (
                  <div
                    className={cn(
                      'w-1 flex-1 my-2 transition-colors',
                      index < currentStepIndex ? 'bg-green-600' : 'bg-muted'
                    )}
                  />
                )}
              </div>

              {/* Step content */}
              <div className={cn('flex-1 pt-1', getStepTextColor(index))}>
                <div
                  className={cn(
                    'px-4 py-2 rounded-lg transition-colors',
                    getStepBgColor(index)
                  )}
                >
                  <p className="font-medium text-sm">{step.label}</p>
                  {showDescriptions && step.description && (
                    <p className="text-xs opacity-75 mt-1">{step.description}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      );
    }

    // Horizontal orientation
    return (
      <div
        ref={ref}
        className={cn('flex w-full items-start', className)}
        {...props}
      >
        {steps.map((step, index) => (
          <div key={step.id} className="flex flex-col flex-1">
            {/* Step indicator and connector */}
            <div className="flex items-center gap-2 mb-3">
              <button
                onClick={() => clickable && onStepClick?.(index)}
                className={cn(
                  'relative z-10 rounded-full p-1 transition-colors flex-shrink-0',
                  clickable && 'cursor-pointer hover:bg-secondary'
                )}
                disabled={!clickable}
                aria-current={getStepStatus(index) === 'in-progress' ? 'step' : undefined}
              >
                {getStepIcon(index)}
              </button>

              {/* Connector line */}
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    'flex-1 h-1 transition-colors',
                    index < currentStepIndex ? 'bg-green-600' : 'bg-muted'
                  )}
                />
              )}
            </div>

            {/* Step label and description */}
            <div className={cn('flex-1 pl-1', getStepTextColor(index))}>
              <div
                className={cn(
                  'px-3 py-2 rounded-lg text-center transition-colors',
                  getStepBgColor(index)
                )}
              >
                <p className="font-medium text-xs sm:text-sm">{step.label}</p>
                {showDescriptions && step.description && (
                  <p className="text-xs opacity-75 mt-1">{step.description}</p>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }
);

StepIndicator.displayName = 'StepIndicator';

export { StepIndicator };
export type { StepIndicatorProps, Step };
