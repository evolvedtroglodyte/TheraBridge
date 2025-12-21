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

import { useState, useCallback, Suspense } from 'react';
import './styles.css';
import { ThemeProvider } from './contexts/ThemeContext';
import { SessionDataProvider } from './contexts/SessionDataContext';
import { Header } from './components/Header';
import { NotesGoalsCard } from './components/NotesGoalsCard';
import { AIChatCard } from './components/AIChatCard';
import { ToDoCard } from './components/ToDoCard';
import { ProgressPatternsCard } from './components/ProgressPatternsCard';
import { TherapistBridgeCard } from './components/TherapistBridgeCard';
import { SessionCardsGrid } from './components/SessionCardsGrid';
import { TimelineSidebar } from './components/TimelineSidebar';
import { DashboardSkeleton } from './components/DashboardSkeleton';

export default function DashboardV3Page() {
  // Lifted state: controls fullscreen chat from both Header and AIChatCard
  const [isChatFullscreen, setIsChatFullscreen] = useState(false);

  // Lifted state: controls which session is opened in fullscreen from Timeline
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  // Scroll to a session card in the grid (triggered by timeline entry click)
  const handleScrollToSession = useCallback((sessionId: string) => {
    const element = document.getElementById(`session-${sessionId}`);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' });
      // Add a brief highlight effect
      element.classList.add('ring-2', 'ring-[#5AB9B4]', 'dark:ring-[#a78bfa]');
      setTimeout(() => {
        element.classList.remove('ring-2', 'ring-[#5AB9B4]', 'dark:ring-[#a78bfa]');
      }, 2000);
    }
  }, []);

  return (
    <ThemeProvider>
      <SessionDataProvider>
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

              {/* Bottom Row - 80/20 Split */}
              <div className="grid grid-cols-[1fr_250px] gap-6">
                <div className="h-[650px]">
                  <SessionCardsGrid
                    externalSelectedSessionId={selectedSessionId}
                    onSessionClose={() => setSelectedSessionId(null)}
                  />
                </div>
                <div className="h-[650px]">
                  <TimelineSidebar
                    onViewSession={(sessionId) => setSelectedSessionId(sessionId)}
                    onScrollToSession={handleScrollToSession}
                  />
                </div>
              </div>
            </main>
          </div>
        </Suspense>
      </SessionDataProvider>
    </ThemeProvider>
  );
}
