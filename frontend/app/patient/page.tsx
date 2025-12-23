'use client';

/**
 * TherapyBridge Dashboard - Main application entry
 * - Full dashboard layout with 7 interactive components
 * - Grid-based responsive layout
 * - Warm cream background with therapy-appropriate aesthetics
 * - FIXED: Full dark mode support across entire page
 * - State lifted for Header "Ask AI" button to control chat fullscreen
 * - State lifted for Timeline → Session integration
 * - NOW CONNECTED: Uses real API data via SessionDataProvider
 */

import { useState, Suspense } from 'react';
import './styles.css';
import { ThemeProvider } from './contexts/ThemeContext';
import { SessionDataProvider } from './contexts/SessionDataContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { Header } from './components/Header';
import { NotesGoalsCard } from './components/NotesGoalsCard';
import { AIChatCard } from './components/AIChatCard';
import { ToDoCard } from './components/ToDoCard';
import { ProgressPatternsCard } from './components/ProgressPatternsCard';
import { TherapistBridgeCard } from './components/TherapistBridgeCard';
import { DashboardSkeleton } from './components/DashboardSkeleton';
import { ProcessingRefreshBridge } from './components/ProcessingRefreshBridge';

export default function DashboardV3Page() {
  // Lifted state: controls fullscreen chat from both Header and AIChatCard
  const [isChatFullscreen, setIsChatFullscreen] = useState(false);

  return (
    <ThemeProvider>
      <ProcessingProvider>
        <SessionDataProvider>
          {/* Bridge that triggers refresh when processing completes */}
          <ProcessingRefreshBridge />
          <Suspense fallback={<DashboardSkeleton />}>
            <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] transition-colors duration-300">
              {/* Header */}
              <Header onAskAIClick={() => setIsChatFullscreen(true)} />

            {/* Main Container */}
            <main className="w-full max-w-[1400px] mx-auto px-12 py-12">
              {/* Top Row - 50/50 Split */}
              <div className="grid grid-cols-2 gap-6 mb-10">
                <NotesGoalsCard />
                <AIChatCard
                  isFullscreen={isChatFullscreen}
                  onFullscreenChange={setIsChatFullscreen}
                />
              </div>

              {/* Middle Row - 3 Equal Cards */}
              <div className="grid grid-cols-3 gap-6 mb-10">
                <ToDoCard />
                <ProgressPatternsCard />
                <TherapistBridgeCard />
              </div>

              {/* Sessions and Timeline moved to /sessions page */}
            </main>
          </div>
        </Suspense>
        </SessionDataProvider>
      </ProcessingProvider>
    </ThemeProvider>
  );
}
