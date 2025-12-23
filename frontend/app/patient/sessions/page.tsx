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
import { ThemeProvider } from '../contexts/ThemeContext';
import { SessionDataProvider } from '../contexts/SessionDataContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { Header } from '../components/Header';
import { SessionsSidebar } from '../components/SessionsSidebar';
import { SessionCardsGrid } from '../components/SessionCardsGrid';
import { HorizontalTimeline } from '../components/HorizontalTimeline';
import { DashboardSkeleton } from '../components/DashboardSkeleton';
import { ProcessingRefreshBridge } from '../components/ProcessingRefreshBridge';
import { FullscreenChat, ChatMessage, ChatMode } from '../components/FullscreenChat';
import { Session } from '../lib/types';

export default function SessionsPage() {
  const [isChatFullscreen, setIsChatFullscreen] = useState(false);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);

  // Chat state - required by FullscreenChat
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [mode, setMode] = useState<ChatMode>('ai');
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

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
                    <SessionCardsGrid />
                  </div>

                  {/* Horizontal Timeline */}
                  <HorizontalTimeline />
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

