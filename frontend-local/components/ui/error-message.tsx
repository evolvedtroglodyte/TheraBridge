'use client';

import React from 'react';
import { AlertCircle, XCircle, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ErrorMessageVariant = 'inline' | 'alert' | 'toast' | 'banner';
export type ErrorMessageSeverity = 'error' | 'warning' | 'info';

interface ErrorMessageProps {
  /** The error message to display */
  message: string;
  /** Optional description/details */
  description?: string;
  /** Visual variant */
  variant?: ErrorMessageVariant;
  /** Severity level (affects styling) */
  severity?: ErrorMessageSeverity;
  /** Whether to show close button (for dismissible errors) */
  dismissible?: boolean;
  /** Callback when dismissed */
  onDismiss?: () => void;
  /** Optional action button text and handler */
  action?: {
    label: string;
    onClick: () => void;
  };
  /** Additional CSS classes */
  className?: string;
}

/**
 * ErrorMessage component for displaying user-friendly error messages
 *
 * Variants:
 * - inline: Compact inline error (default)
 * - alert: Full-width alert box
 * - toast: Toast notification style (for notifications)
 * - banner: Page-level banner alert
 *
 * @example
 * ```tsx
 * <ErrorMessage
 *   message="Failed to upload file"
 *   description="The file is too large. Maximum size is 100MB."
 *   variant="alert"
 *   severity="error"
 *   dismissible
 *   onDismiss={() => setError(null)}
 * />
 * ```
 */
export function ErrorMessage({
  message,
  description,
  variant = 'inline',
  severity = 'error',
  dismissible = false,
  onDismiss,
  action,
  className,
}: ErrorMessageProps) {
  const [isDismissed, setIsDismissed] = React.useState(false);

  if (isDismissed) {
    return null;
  }

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  // Base styling
  const baseClasses = 'flex items-start gap-3';

  // Severity-based colors
  const severityClasses = {
    error: {
      container: 'bg-red-50 border-red-200 text-red-900',
      icon: 'text-red-600',
      button: 'hover:bg-red-100 text-red-600',
      action: 'bg-red-600 hover:bg-red-700 text-white',
    },
    warning: {
      container: 'bg-amber-50 border-amber-200 text-amber-900',
      icon: 'text-amber-600',
      button: 'hover:bg-amber-100 text-amber-600',
      action: 'bg-amber-600 hover:bg-amber-700 text-white',
    },
    info: {
      container: 'bg-blue-50 border-blue-200 text-blue-900',
      icon: 'text-blue-600',
      button: 'hover:bg-blue-100 text-blue-600',
      action: 'bg-blue-600 hover:bg-blue-700 text-white',
    },
  };

  const colors = severityClasses[severity];

  // Variant-specific styling
  const variantClasses = {
    inline: {
      wrapper: `border-l-4 pl-4 py-2 ${colors.container}`,
      icon: 'w-5 h-5 flex-shrink-0 mt-0.5',
      messageText: 'text-sm font-medium',
      descriptionText: 'text-xs mt-1 opacity-90',
    },
    alert: {
      wrapper: `border rounded-lg p-4 ${colors.container}`,
      icon: 'w-5 h-5 flex-shrink-0 mt-0.5',
      messageText: 'text-sm font-semibold',
      descriptionText: 'text-sm mt-2 opacity-90',
    },
    toast: {
      wrapper: `rounded-lg p-3 shadow-lg border ${colors.container}`,
      icon: 'w-5 h-5 flex-shrink-0',
      messageText: 'text-sm font-medium',
      descriptionText: 'text-xs mt-1 opacity-90',
    },
    banner: {
      wrapper: `border-b ${colors.container} px-4 py-3 w-full`,
      icon: 'w-5 h-5 flex-shrink-0 mt-0.5',
      messageText: 'text-sm font-semibold',
      descriptionText: 'text-sm mt-1 opacity-90',
    },
  };

  const variantStyle = variantClasses[variant];

  return (
    <div className={cn(variantStyle.wrapper, className)}>
      <div className={baseClasses}>
        {/* Icon */}
        <div className={cn(variantStyle.icon, colors.icon)} aria-hidden="true">
          {severity === 'error' && <XCircle className="w-full h-full" />}
          {severity === 'warning' && <AlertCircle className="w-full h-full" />}
          {severity === 'info' && <CheckCircle2 className="w-full h-full" />}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className={variantStyle.messageText}>{message}</p>
          {description && (
            <p className={variantStyle.descriptionText}>{description}</p>
          )}

          {/* Action Button */}
          {action && (
            <button
              onClick={action.onClick}
              className={cn(
                'mt-3 px-3 py-1.5 rounded text-sm font-medium transition-colors',
                colors.action
              )}
            >
              {action.label}
            </button>
          )}
        </div>

        {/* Close Button */}
        {dismissible && (
          <button
            onClick={handleDismiss}
            aria-label="Dismiss error"
            className={cn(
              'flex-shrink-0 p-1 rounded transition-colors',
              colors.button
            )}
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Inline error component for form fields
 * @example
 * ```tsx
 * <ErrorMessageInline
 *   message="Email is required"
 *   description="Please enter a valid email address"
 * />
 * ```
 */
export function ErrorMessageInline(props: Omit<ErrorMessageProps, 'variant'>) {
  return <ErrorMessage {...props} variant="inline" />;
}

/**
 * Alert error component for page-level errors
 * @example
 * ```tsx
 * <ErrorMessageAlert
 *   message="Failed to load data"
 *   description="Please check your connection and try again"
 *   dismissible
 * />
 * ```
 */
export function ErrorMessageAlert(props: Omit<ErrorMessageProps, 'variant'>) {
  return <ErrorMessage {...props} variant="alert" />;
}

/**
 * Toast error component for notifications
 * @example
 * ```tsx
 * <ErrorMessageToast
 *   message="Upload failed"
 *   action={{ label: 'Retry', onClick: () => retry() }}
 * />
 * ```
 */
export function ErrorMessageToast(props: Omit<ErrorMessageProps, 'variant'>) {
  return <ErrorMessage {...props} variant="toast" />;
}

/**
 * Banner error component for full-width alerts
 * @example
 * ```tsx
 * <ErrorMessageBanner
 *   message="System maintenance in progress"
 *   severity="warning"
 * />
 * ```
 */
export function ErrorMessageBanner(props: Omit<ErrorMessageProps, 'variant'>) {
  return <ErrorMessage {...props} variant="banner" />;
}
