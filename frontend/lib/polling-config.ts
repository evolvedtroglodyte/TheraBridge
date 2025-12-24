export const POLLING_CONFIG = {
  // Feature flags
  granularUpdatesEnabled: process.env.NEXT_PUBLIC_GRANULAR_UPDATES === 'true',
  sseEnabled: process.env.NEXT_PUBLIC_SSE_ENABLED === 'true',

  // Polling intervals (milliseconds)
  wave1Interval: parseInt(process.env.NEXT_PUBLIC_POLLING_INTERVAL_WAVE1 || '1000', 10),
  wave2Interval: parseInt(process.env.NEXT_PUBLIC_POLLING_INTERVAL_WAVE2 || '3000', 10),

  // Loading overlay timing (milliseconds)
  overlayDuration: parseInt(process.env.NEXT_PUBLIC_LOADING_OVERLAY_DURATION || '500', 10),
  fadeDuration: parseInt(process.env.NEXT_PUBLIC_LOADING_FADE_DURATION || '200', 10),
  staggerDelay: parseInt(process.env.NEXT_PUBLIC_STAGGER_DELAY || '100', 10),

  // Debug logging
  debugLogging: process.env.NEXT_PUBLIC_DEBUG_POLLING === 'true',
} as const;

// Type for session state tracking
export interface SessionState {
  wave1_complete: boolean;
  wave2_complete: boolean;
  last_wave1_update: string | null;
  last_wave2_update: string | null;
}

// Helper to log debug messages
export function logPolling(message: string, ...args: any[]) {
  if (POLLING_CONFIG.debugLogging) {
    console.log(`[Polling]`, message, ...args);
  }
}
