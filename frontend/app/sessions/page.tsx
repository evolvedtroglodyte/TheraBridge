'use client';

/**
 * Sessions Page - Dedicated view for session history
 * - Shows session cards grid + timeline
 * - Same cream/dark purple background as dashboard
 */

import { Suspense, useState } from 'react';
import { ThemeProvider } from '@/app/patient/contexts/ThemeContext';
import { SessionDataProvider } from '@/app/patient/contexts/SessionDataContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { NavigationBar } from '@/components/NavigationBar';
import { SessionCardsGrid } from '@/app/patient/dashboard-v3/components/SessionCardsGrid';
import { FullscreenChat, ChatMessage, ChatMode } from '@/app/patient/components/FullscreenChat';
import { ProcessingRefreshBridge } from '@/app/patient/components/ProcessingRefreshBridge';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';

export default function SessionsPage() {
  return (
    <ThemeProvider>
      <ProcessingProvider>
        <SessionDataProvider>
          <ProcessingRefreshBridge />
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
    </ThemeProvider>
  );
}
