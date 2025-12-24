'use client';

/**
 * Sessions Page - Dedicated view for session history
 * - Shows session cards grid + timeline
 * - Same cream/dark purple background as dashboard
 */

import { Suspense, useEffect } from 'react';
import { SessionDataProvider } from '@/app/patient/contexts/SessionDataContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { NavigationBar } from '@/components/NavigationBar';
import { SessionCardsGrid } from '@/app/patient/components/SessionCardsGrid';
import { ProcessingRefreshBridge } from '@/app/patient/components/ProcessingRefreshBridge';
import { WaveCompletionBridge } from '@/app/patient/components/WaveCompletionBridge';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';
import { refreshDetection } from '@/lib/refresh-detection';
import { demoTokenStorage } from '@/lib/demo-token-storage';

export default function SessionsPage() {
  // Check for hard refresh and clear localStorage if detected
  useEffect(() => {
    const isHardRefresh = refreshDetection.isHardRefresh();
    if (isHardRefresh) {
      console.log('🔥 Hard refresh detected on /sessions - clearing demo data (staying on page)');
      demoTokenStorage.clear();
      // Don't redirect - WaveCompletionBridge will detect missing patient ID and handle reinitialization
    }
  }, []); // Remove router from deps since we're not using it

  return (
    <ProcessingProvider>
      <SessionDataProvider>
        <ProcessingRefreshBridge />
        <WaveCompletionBridge />
        <Suspense fallback={<DashboardSkeleton />}>
          <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] transition-colors duration-300">
            <NavigationBar />

            <main className="px-12 py-12">
              <SessionCardsGrid />
            </main>
          </div>
        </Suspense>
      </SessionDataProvider>
    </ProcessingProvider>
  );
}
