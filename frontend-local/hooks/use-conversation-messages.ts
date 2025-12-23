/**
 * useConversationMessages Hook
 *
 * Loads all messages for a specific conversation from the database.
 */

import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/lib/supabase';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface UseConversationMessagesReturn {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  loadMessages: (conversationId: string) => Promise<void>;
}

/**
 * Hook to load messages for a specific conversation
 *
 * @returns Messages array, loading state, error state, and load function
 */
export function useConversationMessages(): UseConversationMessagesReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadMessages = useCallback(async (conversationId: string) => {
    try {
      setLoading(true);
      setError(null);

      // Fetch all messages for this conversation
      const { data: messagesData, error: messagesError } = await supabase
        .from('chat_messages')
        .select('id, role, content, created_at')
        .eq('conversation_id', conversationId)
        .order('created_at', { ascending: true });

      if (messagesError) throw messagesError;

      // Transform into ChatMessage format
      const formattedMessages: ChatMessage[] = (messagesData || []).map((msg) => ({
        id: msg.id,
        role: msg.role as 'user' | 'assistant',
        content: msg.content,
        timestamp: new Date(msg.created_at),
      }));

      setMessages(formattedMessages);
    } catch (err) {
      console.error('Failed to load conversation messages:', err);
      setError(err instanceof Error ? err.message : 'Failed to load messages');
      setMessages([]); // Clear messages on error
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    messages,
    loading,
    error,
    loadMessages,
  };
}
