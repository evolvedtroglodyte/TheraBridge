'use client';

import React, { createContext, useContext, useState, useCallback } from 'react';
import type { FormattedError } from './error-formatter';

export interface ErrorState extends FormattedError {
  id: string;
}

interface ErrorContextType {
  errors: ErrorState[];
  showError: (error: FormattedError, options?: { duration?: number; dismissible?: boolean }) => string;
  dismissError: (id: string) => void;
  clearErrors: () => void;
}

const ErrorContext = createContext<ErrorContextType | undefined>(undefined);

/**
 * Error provider for global error management
 *
 * @example
 * ```tsx
 * <ErrorProvider>
 *   <App />
 * </ErrorProvider>
 * ```
 */
export function ErrorProvider({ children }: { children: React.ReactNode }): React.ReactNode {
  const [errors, setErrors] = useState<ErrorState[]>([]);

  const showError = useCallback(
    (error: FormattedError, options?: { duration?: number; dismissible?: boolean }): string => {
      const id = Math.random().toString(36).substring(7);
      const duration = options?.duration ?? 5000;
      const newError: ErrorState = {
        ...error,
        id,
      };

      setErrors((prev) => [...prev, newError]);

      // Auto-dismiss after duration (default 5 seconds)
      if (duration > 0) {
        setTimeout(() => {
          setErrors((prev) => prev.filter((e) => e.id !== id));
        }, duration);
      }

      return id;
    },
    []
  );

  const dismissError = useCallback((id: string) => {
    setErrors((prev) => prev.filter((e) => e.id !== id));
  }, []);

  const clearErrors = useCallback(() => {
    setErrors([]);
  }, []);

  const value = {
    errors,
    showError,
    dismissError,
    clearErrors,
  };

  return <ErrorContext.Provider value={value}>{children}</ErrorContext.Provider>;
}

/**
 * Hook to use error context
 *
 * @example
 * ```tsx
 * const { showError, dismissError } = useErrorContext();
 *
 * try {
 *   await doSomething();
 * } catch (err) {
 *   showError(formatApiError(err));
 * }
 * ```
 */
export function useErrorContext(): ErrorContextType {
  const context = useContext(ErrorContext);
  if (context === undefined) {
    throw new Error('useErrorContext must be used within ErrorProvider');
  }
  return context;
}

/**
 * Hook to manage a single error state
 * Useful for component-level error handling
 *
 * @example
 * ```tsx
 * const { error, setError, clearError } = useError();
 *
 * try {
 *   await upload(file);
 * } catch (err) {
 *   setError(formatUploadError(err));
 * }
 * ```
 */
export function useError() {
  const [error, setError] = useState<FormattedError | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const showError = useCallback((newError: FormattedError) => {
    setError(newError);
  }, []);

  return {
    error,
    setError: showError,
    clearError,
  };
}
