'use client';

/**
 * Ask AI Page - Dedicated chat interface with Dobby
 * - Full page chat experience (not overlay)
 * - Same providers as other pages
 */

import { Suspense, useState } from 'react';
import { SessionDataProvider } from '@/app/patient/contexts/SessionDataContext';
import { ProcessingProvider } from '@/contexts/ProcessingContext';
import { WaveCompletionBridge } from '@/app/patient/components/WaveCompletionBridge';
import { FullscreenChat, ChatMessage, ChatMode } from '@/app/patient/components/FullscreenChat';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';

export default function AskAIPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [mode, setMode] = useState<ChatMode>('ai');
  const [conversationId, setConversationId] = useState<string | undefined>(undefined);

  return (
    <ProcessingProvider>
      <SessionDataProvider>
        <WaveCompletionBridge />
        <Suspense fallback={<DashboardSkeleton />}>
          {/* Fullscreen chat without NavigationBar */}
          <FullscreenChat
            isOpen={true}
            onClose={() => {}} // No-op since it's a dedicated page
            messages={messages}
            setMessages={setMessages}
            mode={mode}
            setMode={setMode}
            conversationId={conversationId}
            setConversationId={setConversationId}
            isEmbedded={false} // Changed to false for true fullscreen
            enableHomeNavigation={true} // Enable home icon navigation to dashboard
          />
        </Suspense>
      </SessionDataProvider>
    </ProcessingProvider>
  );
}
