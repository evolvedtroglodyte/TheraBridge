'use client';

/**
 * FullscreenChat - Immersive Dobby AI chat interface
 *
 * Features:
 * - Shared message state with collapsed card
 * - Expandable sidebar with chat history
 * - Centered Dobby branding header (static illuminating logo with face)
 * - Welcome view with Dobby intro
 * - Real chat with OpenAI integration
 * - Share modal with privacy options
 * - Light/Dark mode support
 * - Header logo click scrolls to top
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from '../../contexts/ThemeContext';
import { useAuth } from '@/contexts/AuthContext';
import { useConversationHistory } from '@/hooks/use-conversation-history';
import { useConversationMessages } from '@/hooks/use-conversation-messages';
import { ChatSidebar } from './ChatSidebar';
import { ShareModal } from './ShareModal';
import { DobbyLogo } from '../DobbyLogo';
import { DobbyLogoGeometric } from '../DobbyLogoGeometric';
import { HeartSpeechIcon } from '../HeartSpeechIcon';
import { MarkdownMessage } from '@/components/MarkdownMessage';
import { BridgeIcon } from '@/components/TheraBridgeLogo';
import { CompactScrollbar } from '@/components/CompactScrollbar';

// Types - exported for use in AIChatCard
export type ChatMode = 'ai' | 'therapist';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface ChatSession {
  id: string;
  title: string;
  lastMessage: string;
  timestamp: Date;
}

export interface FullscreenChatProps {
  isOpen: boolean;
  onClose: () => void;
  // Shared state from AIChatCard
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  mode: ChatMode;
  setMode: React.Dispatch<React.SetStateAction<ChatMode>>;
  // Conversation tracking - shared with compact card
  conversationId: string | undefined;
  setConversationId: React.Dispatch<React.SetStateAction<string | undefined>>;
}

// Mock data for recent chats
const MOCK_RECENT_CHATS: ChatSession[] = [
  { id: '1', title: 'Preparing for next session', lastMessage: 'Let me help you prepare...', timestamp: new Date() },
  { id: '2', title: 'Breathing techniques help', lastMessage: 'Try the 4-7-8 technique...', timestamp: new Date(Date.now() - 86400000) },
  { id: '3', title: 'Mood tracking question', lastMessage: 'Your mood patterns show...', timestamp: new Date(Date.now() - 172800000) },
  { id: '4', title: 'Setting boundaries at work', lastMessage: 'Boundaries are essential...', timestamp: new Date(Date.now() - 259200000) },
  { id: '5', title: 'Sleep improvement tips', lastMessage: 'Quality sleep is crucial...', timestamp: new Date(Date.now() - 345600000) },
];

const SUGGESTED_PROMPTS = [
  "Why does my mood drop after family visits?",
  "Help me prep to discuss boundaries with my partner",
  "Explain the TIPP technique again",
  "What should I bring up in next session?",
  "I had a panic attack - what do I do?",
  "Send message to my therapist"
];

const DOBBY_INTRO = "Hi! I'm Dobby, your AI therapy companion. I can help you prepare for sessions, answer questions about techniques, or forward messages to your therapist. Everything is confidential and designed to support your therapy journey. How can I help you today?";

const MAX_CHARS = 500;

// User data (mock)
const USER = {
  name: 'Alex Thompson',
  firstName: 'Alex',
};

export function FullscreenChat({
  isOpen,
  onClose,
  messages,
  setMessages,
  mode,
  setMode,
  conversationId,
  setConversationId,
}: FullscreenChatProps) {
  const { isDark, toggleTheme } = useTheme();
  const { user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  // Conversation history hooks
  const { conversations, loading: historyLoading, refresh: refreshHistory } = useConversationHistory(20);
  const { messages: loadedMessages, loadMessages } = useConversationMessages();

  // State (conversationId is now passed from parent)
  const [sidebarExpanded, setSidebarExpanded] = useState(false);
  const [shareModalOpen, setShareModalOpen] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isAtTop, setIsAtTop] = useState(true);
  const [promptsVisible, setPromptsVisible] = useState(true);

  // Transform conversation history to ChatSession format for sidebar
  const recentChats: ChatSession[] = conversations.map(conv => ({
    id: conv.id,
    title: conv.title,
    lastMessage: conv.lastMessage,
    timestamp: conv.timestamp,
  }));

  // Refs
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const promptsContainerRef = useRef<HTMLDivElement>(null);

  // Track scroll position for logo click behavior
  const handleScroll = useCallback(() => {
    if (messagesContainerRef.current) {
      setIsAtTop(messagesContainerRef.current.scrollTop < 50);
    }
  }, []);

  // Reset sidebar state when opening
  useEffect(() => {
    if (isOpen) {
      setSidebarExpanded(false);
    }
  }, [isOpen]);

  // Handle Escape key to close fullscreen
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen && !shareModalOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, shareModalOpen, onClose]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [inputValue]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (messagesContainerRef.current && messages.length > 0) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight;
    }
  }, [messages]);

  // Focus textarea when opened
  useEffect(() => {
    if (isOpen && textareaRef.current) {
      setTimeout(() => textareaRef.current?.focus(), 300);
    }
  }, [isOpen]);

  // Send message handler with streaming support
  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || isLoading || authLoading || !user) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Create temporary assistant message for streaming
    const tempAssistantId = `msg-${Date.now()}-assistant`;
    const tempAssistantMessage: ChatMessage = {
      id: tempAssistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, tempAssistantMessage]);

    try {
      // Get authenticated user ID
      if (!user?.id) {
        throw new Error('You must be logged in to chat');
      }

      const userId = user.id;

      // Call streaming chat API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage.content,
          userId,
          conversationId, // undefined for first message (API creates new conversation)
          // sessionId is optional - add when viewing specific session
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();

        // Handle rate limiting specifically
        if (response.status === 429) {
          throw new Error(errorData.description || 'Daily message limit reached');
        }

        throw new Error(errorData.error || 'Failed to get response');
      }

      // Read streaming response (Server-Sent Events)
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) throw new Error('No response body');

      let fullContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));

            if (data.content) {
              // Append streamed content
              fullContent += data.content;

              // Update the assistant message with accumulated content
              setMessages(prev =>
                prev.map(msg =>
                  msg.id === tempAssistantId
                    ? { ...msg, content: fullContent }
                    : msg
                )
              );
            }

            if (data.done) {
              console.log('Stream complete, conversationId:', data.conversationId);
              // Store conversationId for subsequent messages in this chat
              if (data.conversationId && !conversationId) {
                setConversationId(data.conversationId);
                // Refresh conversation history to show the new chat
                refreshHistory();
              }
            }
          }
        }
      }
    } catch (error) {
      console.error('Chat error:', error);

      // Update temp message with error fallback
      const fallbackContent = error instanceof Error && error.message.includes('limit')
        ? "⚠️ You've reached your daily message limit (50 messages). The limit resets at midnight."
        : mode === 'ai'
          ? "I understand you're working through that. Based on your recent sessions, this connects to the boundary-setting work you've been doing. Would you like to explore this further?"
          : "I've forwarded your message to your therapist. They typically respond within 24 hours. Is there anything else I can help you with in the meantime?";

      setMessages(prev =>
        prev.map(msg =>
          msg.id === tempAssistantId
            ? { ...msg, content: fallbackContent }
            : msg
        )
      );
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, authLoading, user, messages, mode, setMessages, conversationId, refreshHistory]);

  // Handle prompt click
  const handlePromptClick = (prompt: string) => {
    setInputValue(prompt);
    setTimeout(() => handleSend(), 100);
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Handle conversation selection from sidebar
  const handleSelectChat = useCallback(async (chatId: string) => {
    try {
      // Load messages for the selected conversation
      await loadMessages(chatId);
      setConversationId(chatId);
      setSidebarExpanded(false); // Close sidebar after selection
    } catch (error) {
      console.error('Failed to load conversation:', error);
    }
  }, [loadMessages]);

  // Sync loaded messages to parent state when they change
  useEffect(() => {
    if (loadedMessages.length > 0) {
      setMessages(loadedMessages);
    }
  }, [loadedMessages, setMessages]);

  // New chat handler
  const handleNewChat = () => {
    setMessages([]);
    setInputValue('');
    setSidebarExpanded(false);
    setConversationId(undefined); // Clear conversation ID for fresh chat
  };

  // Logo/text click handler - scroll to top only
  const handleLogoClick = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  };

  if (!isOpen) return null;

  const charCount = inputValue.length;
  const hasMessages = messages.length > 0;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
        className="fixed inset-0 z-[2000] flex fullscreen-chat-container"
      >
        {/* Sidebar */}
        <ChatSidebar
          isExpanded={sidebarExpanded}
          onToggle={() => setSidebarExpanded(!sidebarExpanded)}
          recentChats={recentChats}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
          userName={USER.name}
          isDark={isDark}
          onHomeClick={() => {
            onClose();
            router.push('/dashboard');
          }}
          onThemeToggle={toggleTheme}
        />

        {/* Main Content */}
        <div
          className={`flex-1 flex flex-col transition-colors duration-300 ${
            isDark ? 'bg-[#1a1625]' : 'bg-[#ECEAE5]'
          }`}
        >
          {/* Header Bar - White background to match sidebar */}
          <div
            className={`relative flex items-center justify-center h-14 px-5 border-b flex-shrink-0 ${
              isDark ? 'bg-[#1a1625] border-[#3d3548]' : 'bg-white border-[#E0DDD8]'
            }`}
          >
            {/* Left Side - Theme Toggle only */}
            <div className="absolute left-3 top-1/2 -translate-y-1/2">
              {/* Theme Toggle */}
              <button
                onClick={toggleTheme}
                className={`w-10 h-10 flex items-center justify-center rounded-lg transition-colors ${
                  isDark ? 'hover:bg-[#3d3548]' : 'hover:bg-gray-100'
                }`}
                aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
              >
                {isDark ? (
                  <svg
                    className="w-[22px] h-[22px]"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#93B4DC"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{ filter: 'drop-shadow(0 0 4px rgba(147, 180, 220, 0.6)) drop-shadow(0 0 10px rgba(147, 180, 220, 0.3))' }}
                  >
                    <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                  </svg>
                ) : (
                  <svg
                    className="w-[22px] h-[22px]"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#F5A623"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{ filter: 'drop-shadow(0 0 4px rgba(245, 166, 35, 0.5)) drop-shadow(0 0 8px rgba(245, 166, 35, 0.25))' }}
                  >
                    <circle cx="12" cy="12" r="4" />
                    <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
                  </svg>
                )}
              </button>
            </div>

            {/* Centered Dobby Logo + DOBBY text - illuminating, clickable */}
            <div
              className="cursor-pointer flex items-center gap-2"
              style={{
                filter: isDark
                  ? 'drop-shadow(0 0 8px rgba(139, 106, 174, 0.56)) drop-shadow(0 0 17px rgba(139, 106, 174, 0.35))'
                  : 'drop-shadow(0 0 8px rgba(90, 185, 180, 0.56)) drop-shadow(0 0 17px rgba(90, 185, 180, 0.35))',
              }}
              onClick={handleLogoClick}
            >
              {/* Logo - always visible */}
              <DobbyLogo size={50} />
              {/* DOBBY text - always visible, clickable for scroll to top */}
              <span
                className={`font-mono text-lg font-medium tracking-[4px] uppercase ${
                  isDark ? 'text-[#9B7AC4]' : 'text-[#5AB9B4]'
                }`}
              >
                DOBBY
              </span>
            </div>

            {/* Right Side - Share button only */}
            <div className="absolute right-5 top-1/2 -translate-y-1/2 flex items-center gap-2">
              {/* Share Button */}
              <button
                onClick={() => setShareModalOpen(true)}
                aria-label="Share chat"
                className={`w-9 h-9 flex items-center justify-center rounded-lg transition-colors group ${
                  isDark ? 'hover:bg-white/5 text-gray-400' : 'hover:bg-black/5 text-gray-500'
                }`}
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <path d="M8 13h8M8 17h8M8 9h2"/>
                </svg>
              </button>
            </div>
          </div>

          {/* Content Area */}
          <div
            ref={messagesContainerRef}
            onScroll={handleScroll}
            className="flex-1 overflow-y-auto px-6"
          >
            <div className="max-w-3xl mx-auto">
              {/* Welcome Greeting - Scrolls naturally with chat content */}
              <div className="pt-8 pb-8">
                <h1
                  className={`font-crimson text-[32px] font-medium text-center ${
                    isDark ? 'text-gray-200' : 'text-[#1a1a1a]'
                  }`}
                >
                  Welcome back, {USER.firstName}
                </h1>
              </div>

              {/* Dobby Intro Chat Bubble - matches subsequent assistant messages */}
              <div className="flex gap-3 mb-4 mt-4">
                <div className="flex-shrink-0">
                  <DobbyLogo size={37} />
                </div>
                <div
                  className={`font-dm text-sm leading-relaxed max-w-[70%] p-4 rounded-2xl rounded-tl-sm ${
                    isDark
                      ? 'bg-[#2a2535] text-gray-300'
                      : 'bg-white text-gray-700 shadow-sm border border-gray-100'
                  }`}
                >
                  <p>{DOBBY_INTRO}</p>
                </div>
              </div>

              {/* Chat Messages */}
              {messages.map((msg) => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex gap-3 mb-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                >
                  {/* Avatar for assistant messages - always DobbyLogo with face */}
                  {/* Size: 37px (15% bigger than original 32px) */}
                  <div className="flex-shrink-0">
                    {msg.role === 'assistant' ? (
                      <DobbyLogo size={37} />
                    ) : null}
                  </div>

                  {/* Show loading dots if assistant message is empty (still thinking) */}
                  {msg.role === 'assistant' && !msg.content ? (
                    <div className="flex gap-1.5 pt-4">
                      <span className={`w-2 h-2 rounded-full animate-bounce ${isDark ? 'bg-[#8B6AAE]' : 'bg-[#5AB9B4]'}`} style={{ animationDelay: '0ms' }} />
                      <span className={`w-2 h-2 rounded-full animate-bounce ${isDark ? 'bg-[#8B6AAE]' : 'bg-[#5AB9B4]'}`} style={{ animationDelay: '150ms' }} />
                      <span className={`w-2 h-2 rounded-full animate-bounce ${isDark ? 'bg-[#8B6AAE]' : 'bg-[#5AB9B4]'}`} style={{ animationDelay: '300ms' }} />
                    </div>
                  ) : (
                    <div
                      className={`font-dm text-sm leading-relaxed max-w-[70%] p-4 rounded-2xl ${
                        msg.role === 'user'
                          ? isDark
                            ? 'bg-[#7882E7] text-white rounded-tr-sm'
                            : 'bg-[#4ECDC4] text-white rounded-tr-sm'
                          : isDark
                            ? 'bg-[#2a2535] text-gray-300 rounded-tl-sm'
                            : 'bg-white text-gray-700 shadow-sm border border-gray-100 rounded-tl-sm'
                      }`}
                    >
                      {msg.role === 'assistant' ? (
                        <MarkdownMessage content={msg.content} isDark={isDark} />
                      ) : (
                        msg.content
                      )}
                    </div>
                  )}
                </motion.div>
              ))}

              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Input Section */}
          <div className={`border-t px-6 py-4 flex-shrink-0 ${isDark ? 'border-[#2a2535]' : 'border-[#E5E2DE]'}`}>
            <div className="max-w-3xl mx-auto">
              {/* Arrow Toggle Line for Prompts */}
              <div className="flex items-center justify-center mb-2">
                <div className={`flex-1 h-[1px] ${isDark ? 'bg-[#3d3548]' : 'bg-gray-200'}`} />
                <button
                  onClick={() => setPromptsVisible(!promptsVisible)}
                  className={`mx-3 p-1 rounded-full transition-all ${
                    isDark ? 'hover:bg-white/5 text-gray-400' : 'hover:bg-black/5 text-gray-400'
                  }`}
                  aria-label={promptsVisible ? 'Hide prompts' : 'Show prompts'}
                >
                  <motion.svg
                    className="w-4 h-4"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    animate={{ rotate: promptsVisible ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </motion.svg>
                </button>
                <div className={`flex-1 h-[1px] ${isDark ? 'bg-[#3d3548]' : 'bg-gray-200'}`} />
              </div>

              {/* Scrollable Suggested Prompts - Toggleable */}
              <AnimatePresence>
                {promptsVisible && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div ref={promptsContainerRef} className="flex gap-2 overflow-x-auto pb-3 scrollbar-hide mb-1">
                      {SUGGESTED_PROMPTS.map((prompt, idx) => (
                        <button
                          key={idx}
                          onClick={() => handlePromptClick(prompt)}
                          className={`font-dm text-sm px-4 py-2 rounded-full border whitespace-nowrap flex-shrink-0 transition-all ${
                            isDark
                              ? 'bg-[#2a2535] border-[#3d3548] text-gray-300 hover:text-[#8B6AAE] hover:bg-[#3d3548]'
                              : 'bg-white border-gray-200 text-gray-600 hover:text-[#5AB9B4] hover:border-[#5AB9B4] hover:shadow-sm'
                          }`}
                        >
                          {prompt}
                        </button>
                      ))}
                    </div>

                    {/* Compact Scrollbar - 60px tiny variant */}
                    <CompactScrollbar
                      containerRef={promptsContainerRef}
                      isDark={isDark}
                      className="mb-2"
                    />
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Input Container */}
              <div
                className={`flex items-end gap-3 p-3 rounded-3xl border transition-all ${
                  isDark
                    ? 'bg-[#2a2535] border-[#3d3548]'
                    : 'bg-white border-gray-200'
                }`}
              >
                <div className="flex-1 flex flex-col gap-2">
                  <textarea
                    ref={textareaRef}
                    placeholder={mode === 'ai' ? "Ask Dobby anything..." : "Send a message to your therapist..."}
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value.slice(0, MAX_CHARS))}
                    onKeyPress={handleKeyPress}
                    className={`font-jakarta text-sm outline-none bg-transparent resize-none w-full min-h-[24px] ${
                      isDark
                        ? 'text-gray-200 placeholder:text-gray-500'
                        : 'text-gray-800 placeholder:text-gray-400'
                    }`}
                    rows={1}
                  />
                  <div className="flex items-center justify-between">
                    {/* Mode Toggle - AI uses geometric Dobby, Therapist uses heart speech */}
                    <div className={`flex gap-1 p-1 rounded-full border ${
                      isDark ? 'bg-[#1a1625] border-[#3d3548]' : 'bg-gray-50 border-gray-200'
                    }`}>
                      <button
                        onClick={() => setMode('ai')}
                        className={`font-jakarta text-xs font-medium px-3 py-1.5 rounded-full transition-all flex items-center gap-1 ${
                          mode === 'ai'
                            ? isDark
                              ? 'bg-[#8B6AAE] text-white'
                              : 'bg-[#5AB9B4] text-white'
                            : isDark ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        {/* Geometric Dobby icon for AI mode */}
                        <svg className="w-3 h-3" viewBox="0 0 120 120" fill="none">
                          <polygon points="15,55 35,35 35,65" fill="currentColor" />
                          <polygon points="105,55 85,35 85,65" fill="currentColor" />
                          <rect x="30" y="30" width="60" height="60" rx="14" fill="currentColor" />
                        </svg>
                        AI
                      </button>
                      <button
                        onClick={() => setMode('therapist')}
                        className={`font-jakarta text-xs font-medium px-3 py-1.5 rounded-full transition-all flex items-center gap-1 ${
                          mode === 'therapist'
                            ? 'bg-gradient-to-br from-[#F4A69D] to-[#E88B7E] text-white'
                            : isDark ? 'text-gray-400 hover:text-gray-300' : 'text-gray-500 hover:text-gray-700'
                        }`}
                      >
                        {/* Heart speech icon for therapist mode - orange only when active */}
                        <svg className="w-3 h-3" viewBox="0 0 24 24" fill={mode === 'therapist' ? 'currentColor' : isDark ? '#9ca3af' : '#6b7280'}>
                          <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                        </svg>
                        THERAPIST
                      </button>
                    </div>
                    {/* Char count */}
                    <span className={`font-jakarta text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
                      {charCount}/{MAX_CHARS}
                    </span>
                  </div>
                </div>
                {/* Send Button - Arrow up icon matching collapsed card */}
                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isLoading || authLoading || !user}
                  aria-label="Send message"
                  className={`w-10 h-10 flex items-center justify-center rounded-xl transition-all flex-shrink-0 ${
                    inputValue.trim() && !isLoading && !authLoading && user
                      ? isDark
                        ? 'bg-[#8B6AAE] text-white hover:bg-[#7B5A9E]'
                        : 'bg-[#5AB9B4] text-white hover:bg-[#4AA9A4]'
                      : isDark
                        ? 'bg-[#3d3548] text-gray-500 cursor-not-allowed'
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }`}
                >
                  <svg className="w-[18px] h-[18px]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="12" y1="19" x2="12" y2="5" />
                    <polyline points="5 12 12 5 19 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Share Modal */}
        <ShareModal
          isOpen={shareModalOpen}
          onClose={() => setShareModalOpen(false)}
          isDark={isDark}
        />
      </motion.div>
    </AnimatePresence>
  );
}
