'use client';

/**
 * Ask AI Page - Dedicated chat interface with Dobby
 * - Full page chat experience (not overlay)
 * - Same providers as other pages
 */

import { Suspense, useState } from 'react';
import { ThemeProvider } from '@/app/patient/contexts/ThemeContext';
import { SessionDataProvider } from '@/app/patient/contexts/SessionDataContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { NavigationBar } from '@/components/NavigationBar';
import { FullscreenChat, ChatMessage, ChatMode } from '@/app/patient/components/FullscreenChat';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';

export default function AskAIPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [mode, setMode] = useState<ChatMode>('ai');
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

  return (
    <ThemeProvider>
      <ProcessingProvider>
        <SessionDataProvider>
          <Suspense fallback={<DashboardSkeleton />}>
            <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] transition-colors duration-300">
              <NavigationBar />

              {/* Chat as main content (always open, not overlay) */}
              <FullscreenChat
                isOpen={true}
                onClose={() => {}} // No-op since it's a dedicated page
                messages={messages}
                setMessages={setMessages}
                mode={mode}
                setMode={setMode}
                conversationId={conversationId}
                setConversationId={setConversationId}
              />
            </div>
          </Suspense>
        </SessionDataProvider>
      </ProcessingProvider>
    </ThemeProvider>
  );
}
