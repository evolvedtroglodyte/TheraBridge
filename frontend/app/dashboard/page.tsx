'use client';

import { Suspense } from 'react';
import '../patient/styles.css';
import { ThemeProvider } from '@/app/patient/contexts/ThemeContext';
import { SessionDataProvider } from '@/app/patient/contexts/SessionDataContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { NavigationBar } from '@/components/NavigationBar';
import { NotesGoalsCard } from '@/app/patient/components/NotesGoalsCard';
import { AIChatCard } from '@/app/patient/components/AIChatCard';
import { ToDoCard } from '@/app/patient/components/ToDoCard';
import { ProgressPatternsCard } from '@/app/patient/components/ProgressPatternsCard';
import { TherapistBridgeCard } from '@/app/patient/components/TherapistBridgeCard';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';
import { ProcessingRefreshBridge } from '@/app/patient/components/ProcessingRefreshBridge';

export default function DashboardPage() {
  return (
    <ThemeProvider>
      <ProcessingProvider>
        <SessionDataProvider>
          <ProcessingRefreshBridge />
          <Suspense fallback={<DashboardSkeleton />}>
            <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] transition-colors duration-300">
              <NavigationBar />
              <main className="w-full max-w-[1400px] mx-auto px-12 py-12">
                <div className="grid grid-cols-2 gap-6 mb-10">
                  <NotesGoalsCard />
                  <AIChatCard isFullscreen={false} onFullscreenChange={() => {}} />
                </div>
                <div className="grid grid-cols-3 gap-6 mb-10">
                  <ToDoCard />
                  <ProgressPatternsCard />
                  <TherapistBridgeCard />
                </div>
              </main>
            </div>
          </Suspense>
        </SessionDataProvider>
      </ProcessingProvider>
    </ThemeProvider>
  );
}
