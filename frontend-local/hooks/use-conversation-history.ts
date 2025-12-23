/**
 * useConversationHistory Hook
 *
 * Loads chat conversation history from the database for the current user.
 * Automatically refreshes when a new conversation is created.
 */

import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/lib/supabase';
import { useAuth } from '@/contexts/AuthContext';

export interface ConversationHistory {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
  messageCount: number;
  sessionId: string | null; // If chat is session-specific
}

interface UseConversationHistoryReturn {
  conversations: ConversationHistory[];
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
}

/**
 * Hook to load conversation history for the authenticated user
 *
 * @param limit - Maximum number of conversations to load (default: 20)
 * @returns Conversation history, loading state, error state, and refresh function
 */
export function useConversationHistory(limit: number = 20): UseConversationHistoryReturn {
  const { user } = useAuth();
  const [conversations, setConversations] = useState<ConversationHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadConversations = useCallback(async () => {
    if (!user?.id) {
      setConversations([]);
      setLoading(false);
      return;
    }

    // Check if using dev bypass mode (no real Supabase auth)
    const isDevBypass = user.id === 'dev-bypass-user-id';

    if (isDevBypass) {
      // In dev bypass mode, skip database queries (RLS will block them anyway)
      console.log('📝 Dev bypass mode: Skipping conversation history load (no auth session)');
      setConversations([]);
      setLoading(false);
      setError(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      // Fetch conversations with their last message
      const { data: conversationsData, error: conversationsError } = await supabase
        .from('chat_conversations')
        .select(`
          id,
          title,
          message_count,
          last_message_at,
          session_id,
          chat_messages (
            content,
            created_at
          )
        `)
        .eq('user_id', user.id)
        .order('last_message_at', { ascending: false })
        .limit(limit);

      if (conversationsError) throw conversationsError;

      // Transform data into ConversationHistory format
      const formattedConversations: ConversationHistory[] = (conversationsData || []).map((conv: any) => {
        // Get the last message content
        const lastMessage = conv.chat_messages && conv.chat_messages.length > 0
          ? conv.chat_messages[conv.chat_messages.length - 1].content
          : 'No messages yet';

        return {
          id: conv.id,
          title: conv.title,
          lastMessage: lastMessage.slice(0, 100), // Truncate to 100 chars
          timestamp: new Date(conv.last_message_at),
          messageCount: conv.message_count,
          sessionId: conv.session_id,
        };
      });

      setConversations(formattedConversations);
    } catch (err) {
      console.error('Failed to load conversation history:', err);
      setError(err instanceof Error ? err.message : 'Failed to load conversations');
      // Don't crash the UI - just show empty conversations
      setConversations([]);
    } finally {
      setLoading(false);
    }
  }, [user?.id, limit]);

  // Load conversations on mount and when user changes
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  return {
    conversations,
    loading,
    error,
    refresh: loadConversations,
  };
}
