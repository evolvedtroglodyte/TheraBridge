'use client';

import { useEffect } from 'react';
import { validateAndLog } from '@/lib/env-validation';

/**
 * Client-side environment validation component.
 * Runs validation on mount and logs results to console.
 *
 * Should be included in the root layout to validate environment on app startup.
 */
export function EnvValidator() {
  useEffect(() => {
    // Only run validation in browser
    if (typeof window !== 'undefined') {
      // Run validation with health check in development mode
      const isDevelopment = process.env.NODE_ENV === 'development';

      validateAndLog({
        performHealthCheck: isDevelopment,
        healthCheckTimeout: 5000,
      }).catch((error) => {
        console.error('Environment validation failed:', error);
      });
    }
  }, []);

  // This component doesn't render anything
  return null;
}
