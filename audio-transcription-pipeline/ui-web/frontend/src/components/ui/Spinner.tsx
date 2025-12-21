import { HTMLAttributes, forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

export interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  size?: 'sm' | 'md' | 'lg';
}

const Spinner = forwardRef<HTMLDivElement, SpinnerProps>(
  ({ className = '', size = 'md', ...props }, ref) => {
    const sizeStyles = {
      sm: 'h-4 w-4',
      md: 'h-8 w-8',
      lg: 'h-12 w-12',
    };

    return (
      <div ref={ref} className={`flex items-center justify-center ${className}`} {...props}>
        <Loader2 className={`animate-spin text-primary ${sizeStyles[size]}`} />
      </div>
    );
  }
);

Spinner.displayName = 'Spinner';

export default Spinner;
