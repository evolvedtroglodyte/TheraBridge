'use client';

/**
 * Dev Tools Loader
 * Loads testing utilities in development mode only
 */

import { useEffect } from 'react';

export function DevToolsLoader() {
  useEffect(() => {
    // Only load in development
    if (process.env.NODE_ENV === 'development') {
      import('@/lib/auth-flow-test').then((module) => {
        console.log('🔧 Dev tools loaded! Try: window.testAuthFlow.getStatus()');
      });
    }
  }, []);

  return null; // This component doesn't render anything
}
