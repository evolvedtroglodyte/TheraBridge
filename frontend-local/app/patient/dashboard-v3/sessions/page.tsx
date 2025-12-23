'use client';

/**
 * Sessions Page - Dedicated view for session history
 * - Header with navigation (Dashboard | Sessions | Ask AI | Upload)
 * - Left sidebar with TherapyBridge branding + navigation
 * - Scaled session cards (fill available width)
 * - Horizontal timeline below cards
 * - Same cream/dark purple background as dashboard
 */

import { Suspense, useState, useCallback } from 'react';
import { ThemeProvider } from '@/app/patient/contexts/ThemeContext';
import { SessionDataProvider } from '@/app/patient/contexts/SessionDataContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { Header } from '../components/Header';
import { SessionsSidebar } from '@/app/patient/components/SessionsSidebar';
import { SessionCardsGrid } from '../components/SessionCardsGrid';
import { TimelineSidebar } from '@/app/patient/components/TimelineSidebar';
import { SessionDetail } from '@/app/patient/components/SessionDetail';
import { FullscreenChat, ChatMessage, ChatMode } from '@/app/patient/components/FullscreenChat';
import { ProcessingRefreshBridge } from '@/app/patient/components/ProcessingRefreshBridge';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';
import { Session } from '@/app/patient/lib/types';

function SessionsPageContent() {
  const [isChatFullscreen, setIsChatFullscreen] = useState(false);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);

  // Chat state - required by FullscreenChat
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [mode, setMode] = useState<ChatMode>('ai');
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

  // Handle session selection from timeline
  const handleViewSession = useCallback((sessionId: string) => {
    // SessionDataContext will provide the sessions via useSessionData hook in TimelineSidebar
    // The SessionCardsGrid will handle opening the session detail
    // We just need to notify the grid about the selection
    setSelectedSession(null); // Will be set by SessionCardsGrid
  }, []);

  return (
    <ThemeProvider>
      <ProcessingProvider>
        <SessionDataProvider>
          <ProcessingRefreshBridge />
          <Suspense fallback={<DashboardSkeleton />}>
            <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] transition-colors duration-300">
              {/* Header Navigation */}
              <Header onAskAIClick={() => setIsChatFullscreen(true)} />

              <div className="flex">
                {/* Sidebar */}
                <SessionsSidebar />

                {/* Main Content Area */}
                <main className="flex-1 flex flex-col px-12 py-12">
                  {/* Session Cards Grid */}
                  <div className="flex-1 mb-8">
                    <SessionCardsGrid
                      externalSelectedSessionId={selectedSession?.id || null}
                      onSessionClose={() => setSelectedSession(null)}
                    />
                  </div>

                  {/* Vertical Timeline */}
                  <div className="h-[400px]">
                    <TimelineSidebar
                      onViewSession={handleViewSession}
                    />
                  </div>
                </main>
              </div>
            </div>

            {/* Fullscreen Chat - renders on top when active */}
            <FullscreenChat
              isOpen={isChatFullscreen}
              onClose={() => setIsChatFullscreen(false)}
              messages={messages}
              setMessages={setMessages}
              mode={mode}
              setMode={setMode}
              conversationId={conversationId}
              setConversationId={setConversationId}
            />
          </Suspense>
        </SessionDataProvider>
      </ProcessingProvider>
    </ThemeProvider>
  );
}

export default function SessionsPage() {
  return <SessionsPageContent />;
}
