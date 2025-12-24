'use client';

/**
 * Sessions Page - Dedicated view for session history
 * - Shows session cards grid + timeline
 * - Same cream/dark purple background as dashboard
 */

import { Suspense, useEffect } from 'react';
import { useRouter } from 'next/navigation';
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
  const router = useRouter();

  // Check for hard refresh and clear localStorage if detected
  useEffect(() => {
    const isHardRefresh = refreshDetection.isHardRefresh();
    if (isHardRefresh) {
      console.log('🔥 Hard refresh detected on /sessions - clearing demo data and redirecting to home');
      demoTokenStorage.clear();
      router.push('/');
      return;
    }

    // If no demo token exists, redirect to home for initialization
    if (!demoTokenStorage.isInitialized()) {
      console.log('⚠️ No demo token found - redirecting to home for initialization');
      router.push('/');
      return;
    }
  }, [router]);

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
