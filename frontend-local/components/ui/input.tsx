import * as React from "react"
import { Check, AlertCircle } from "lucide-react"

import { cn } from "@/lib/utils"

type ValidationState = 'idle' | 'valid' | 'error';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  type?: string;
  /** Validation state of the input */
  validationState?: ValidationState;
  /** Show validation icon */
  showValidationIcon?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, validationState = 'idle', showValidationIcon = true, ...props }, ref) => {
    // Determine border color based on validation state
    const stateBorderColor = {
      idle: 'border-input',
      valid: 'border-green-500',
      error: 'border-red-500',
    }[validationState];

    const stateRingColor = {
      idle: 'focus-visible:ring-ring',
      valid: 'focus-visible:ring-green-500',
      error: 'focus-visible:ring-red-500',
    }[validationState];

    return (
      <div className="relative w-full">
        <input
          type={type}
          className={cn(
            "flex h-10 w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 transition-colors",
            stateBorderColor,
            stateRingColor,
            showValidationIcon && validationState !== 'idle' && 'pr-10',
            className
          )}
          ref={ref}
          {...props}
        />
        {/* Validation icon */}
        {showValidationIcon && validationState === 'valid' && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-green-500">
            <Check className="w-5 h-5" />
          </div>
        )}
        {showValidationIcon && validationState === 'error' && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-red-500">
            <AlertCircle className="w-5 h-5" />
          </div>
        )}
      </div>
    )
  }
)
Input.displayName = "Input"

export { Input }
export type { InputProps, ValidationState }
