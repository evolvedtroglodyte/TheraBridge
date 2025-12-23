'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';

interface ProgressBarProps extends React.HTMLAttributes<HTMLDivElement> {
  /**
   * Current progress percentage (0-100)
   */
  value: number;
  /**
   * Maximum value (default: 100)
   */
  max?: number;
  /**
   * Show percentage text
   */
  showLabel?: boolean;
  /**
   * Label position: 'inside', 'above', 'below', or 'none'
   */
  labelPosition?: 'inside' | 'above' | 'below' | 'none';
  /**
   * Progress bar size: 'sm' | 'md' | 'lg'
   */
  size?: 'sm' | 'md' | 'lg';
  /**
   * Color variant
   */
  variant?: 'default' | 'success' | 'warning' | 'destructive';
  /**
   * Show animated stripe pattern
   */
  animated?: boolean;
  /**
   * Custom label text (overrides percentage)
   */
  label?: string | React.ReactNode;
  /**
   * Aria label for accessibility
   */
  ariaLabel?: string;
}

const ProgressBar = React.forwardRef<HTMLDivElement, ProgressBarProps>(
  (
    {
      className,
      value = 0,
      max = 100,
      showLabel = true,
      labelPosition = 'inside',
      size = 'md',
      variant = 'default',
      animated = true,
      label,
      ariaLabel = 'Progress',
      ...props
    },
    ref
  ) => {
    // Ensure value is between 0 and max
    const normalizedValue = Math.min(Math.max(value, 0), max);
    const percentage = (normalizedValue / max) * 100;

    // Size classes
    const sizeClasses = {
      sm: 'h-1.5',
      md: 'h-2.5',
      lg: 'h-4',
    };

    // Variant classes for the fill
    const variantClasses = {
      default: 'bg-primary',
      success: 'bg-green-600',
      warning: 'bg-yellow-500',
      destructive: 'bg-destructive',
    };

    // Variant classes for the container
    const containerVariantClasses = {
      default: 'bg-secondary',
      success: 'bg-green-100 dark:bg-green-950',
      warning: 'bg-yellow-100 dark:bg-yellow-950',
      destructive: 'bg-destructive/10',
    };

    const displayLabel = label || (showLabel && `${Math.round(percentage)}%`);

    return (
      <div
        className={cn('flex flex-col gap-1.5 w-full', className)}
        ref={ref}
        {...props}
      >
        {labelPosition === 'above' && displayLabel && (
          <div className="flex justify-between items-center">
            {typeof displayLabel === 'string' ? (
              <span className="text-sm font-medium text-foreground">{displayLabel}</span>
            ) : (
              displayLabel
            )}
          </div>
        )}

        <div
          className={cn(
            'relative w-full rounded-full overflow-hidden transition-colors',
            sizeClasses[size],
            containerVariantClasses[variant]
          )}
          role="progressbar"
          aria-valuenow={Math.round(percentage)}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={ariaLabel}
        >
          <div
            className={cn(
              'h-full rounded-full transition-all duration-300 ease-out',
              variantClasses[variant],
              animated && 'relative overflow-hidden before:absolute before:inset-0 before:translate-x-[-100%] before:animate-pulse'
            )}
            style={{ width: `${percentage}%` }}
          />
        </div>

        {labelPosition === 'inside' && displayLabel && (
          <div className="relative -mt-7 flex justify-center pointer-events-none">
            {typeof displayLabel === 'string' ? (
              <span className="text-xs font-semibold text-foreground drop-shadow-sm">
                {displayLabel}
              </span>
            ) : (
              <div className="drop-shadow-sm">{displayLabel}</div>
            )}
          </div>
        )}

        {labelPosition === 'below' && displayLabel && (
          <div className="flex justify-between items-center">
            {typeof displayLabel === 'string' ? (
              <span className="text-sm font-medium text-foreground">{displayLabel}</span>
            ) : (
              displayLabel
            )}
          </div>
        )}
      </div>
    );
  }
);

ProgressBar.displayName = 'ProgressBar';

export { ProgressBar };
export type { ProgressBarProps };
