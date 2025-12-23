'use client';

/**
 * Processing Refresh Bridge
 *
 * This component bridges ProcessingContext and SessionDataContext.
 * When audio processing completes, it triggers a refresh of session data.
 *
 * Place this inside both ProcessingProvider and SessionDataProvider.
 */

import { useEffect } from 'react';
import { useProcessing } from '@/contexts/ProcessingContext';
import { useSessionData } from '../contexts/SessionDataContext';

export function ProcessingRefreshBridge() {
  const { onComplete } = useProcessing();
  const { refresh } = useSessionData();

  useEffect(() => {
    const unsubscribe = onComplete((sessionId: string) => {
      console.log(`[ProcessingRefreshBridge] Session ${sessionId} completed, refreshing dashboard...`);
      // Small delay to ensure database has committed the changes
      setTimeout(() => {
        refresh();
      }, 500);
    });

    return unsubscribe;
  }, [onComplete, refresh]);

  // This component renders nothing - it's just a bridge
  return null;
}
