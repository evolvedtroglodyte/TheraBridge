import { HTMLAttributes, forwardRef } from 'react';

export interface ProgressProps extends HTMLAttributes<HTMLDivElement> {
  value: number; // 0-100
  max?: number;
  showLabel?: boolean;
}

const Progress = forwardRef<HTMLDivElement, ProgressProps>(
  ({ className = '', value, max = 100, showLabel = false, ...props }, ref) => {
    const percentage = Math.min(Math.max(value, 0), max);

    return (
      <div ref={ref} className={`w-full ${className}`} {...props}>
        <div className="relative h-4 w-full overflow-hidden rounded-full bg-secondary">
          <div
            className="h-full bg-primary transition-all duration-300 ease-in-out"
            style={{ width: `${percentage}%` }}
          />
        </div>
        {showLabel && (
          <div className="mt-1 text-right text-sm text-muted-foreground">
            {Math.round(percentage)}%
          </div>
        )}
      </div>
    );
  }
);

Progress.displayName = 'Progress';

export default Progress;
