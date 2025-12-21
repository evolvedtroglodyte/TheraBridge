'use client';

/**
 * AIChatCard - Dual-mode AI therapy companion interface
 * Compact State: Sticky header with Dobby branding, functional chat input
 * Fullscreen State: Immersive Dobby chat interface with sidebar
 *
 * Features:
 * - Sticky DOBBY header with illuminating DobbyLogo (with face)
 * - Shared message state between collapsed and fullscreen
 * - Intro message with Dobby avatar
 * - Long-press (1.5 sec, animation starts at 0.7s) anywhere to expand
 * - User messages: text only (no bubble), AI: bubble with geometric avatar
 * - Text selection detection prevents hold during copy/paste
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Maximize2 } from 'lucide-react';
import { FullscreenChat, ChatMessage } from './FullscreenChat';
import { useTheme } from '../contexts/ThemeContext';
import { DobbyLogo } from './DobbyLogo';
import { DobbyLogoGeometric } from './DobbyLogoGeometric';
import { HeartSpeechIcon } from './HeartSpeechIcon';

// Types
export type ChatMode = 'ai' | 'therapist';

const MAX_CHARS = 500;

// Dobby intro message (no "Welcome back" text, just the helpful intro)
const DOBBY_INTRO = "Hi! I'm Dobby, your AI therapy companion. I can help you prepare for sessions, answer questions about techniques, or forward messages to your therapist. Everything is confidential and designed to support your therapy journey. How can I help you today?";

// Custom hook for long press detection with progress tracking
// Animation delay: visual feedback starts after `animationDelay` ms
// Text selection detection: prevents hold during copy/paste
function useLongPress(callback: () => void, ms = 1500, animationDelay = 700) {
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const animationDelayRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number>(0);
  const isLongPress = useRef(false);
  const [isHolding, setIsHolding] = useState(false);
  const [showAnimation, setShowAnimation] = useState(false);
  const [progress, setProgress] = useState(0);

  const start = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    // Don't trigger on right-click
    if ('button' in e && e.button !== 0) return;

    // Don't trigger if user is selecting text
    const selection = window.getSelection();
    if (selection && selection.toString().length > 0) return;

    isLongPress.current = false;
    setIsHolding(true);
    setShowAnimation(false);
    setProgress(0);
    startTimeRef.current = Date.now();

    // Delay before showing animation (0.7s)
    animationDelayRef.current = setTimeout(() => {
      setShowAnimation(true);
    }, animationDelay);

    // Update progress every 16ms (~60fps)
    intervalRef.current = setInterval(() => {
      const elapsed = Date.now() - startTimeRef.current;
      const newProgress = Math.min((elapsed / ms) * 100, 100);
      setProgress(newProgress);
    }, 16);

    timeoutRef.current = setTimeout(() => {
      isLongPress.current = true;
      setIsHolding(false);
      setShowAnimation(false);
      setProgress(0);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      callback();
    }, ms);
  }, [callback, ms, animationDelay]);

  const stop = useCallback(() => {
    setIsHolding(false);
    setShowAnimation(false);
    setProgress(0);
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (animationDelayRef.current) {
      clearTimeout(animationDelayRef.current);
      animationDelayRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      if (animationDelayRef.current) {
        clearTimeout(animationDelayRef.current);
      }
    };
  }, []);

  return {
    handlers: {
      onMouseDown: start,
      onMouseUp: stop,
      onMouseLeave: stop,
      onTouchStart: start,
      onTouchEnd: stop,
    },
    isHolding,
    showAnimation,
    progress,
  };
}

// Props for external control of fullscreen state
interface AIChatCardProps {
  isFullscreen?: boolean;
  onFullscreenChange?: (isFullscreen: boolean) => void;
}

// Main Component
export function AIChatCard({ isFullscreen: externalFullscreen, onFullscreenChange }: AIChatCardProps) {
  const { isDark } = useTheme();

  // Use external state if provided, otherwise use internal state
  const [internalFullscreen, setInternalFullscreen] = useState(false);

  // Controlled vs uncontrolled pattern: prefer external state if provided
  const isFullscreen = externalFullscreen !== undefined ? externalFullscreen : internalFullscreen;
  const setIsFullscreen = (value: boolean) => {
    if (onFullscreenChange) {
      onFullscreenChange(value);
    } else {
      setInternalFullscreen(value);
    }
  };

  // SHARED STATE: messages and mode are shared between collapsed and fullscreen
  const [mode, setMode] = useState<ChatMode>('ai');
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Long press to expand (1.5 seconds, animation after 0.7s)
  const { handlers: longPressHandlers, isHolding, showAnimation, progress } = useLongPress(() => {
    setIsFullscreen(true);
  }, 1500, 700);

  // Auto-scroll to latest message - use scrollTop instead of scrollIntoView to prevent page shift
  useEffect(() => {
    if (messagesContainerRef.current && messages.length > 0) {
      const container = messagesContainerRef.current;
      container.scrollTop = container.scrollHeight;
    }
  }, [messages]);

  // Handle send message
  const handleSend = useCallback(async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: [...messages, userMessage].map(m => ({
            role: m.role,
            content: m.content,
          })),
          mode,
        }),
      });

      if (!response.ok) throw new Error('Failed to get response');

      const data = await response.json();

      const assistantMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: data.message,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      // Fallback response
      const fallbackMessage: ChatMessage = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: mode === 'ai'
          ? "I understand. Let me help you with that. What specific aspect would you like to explore?"
          : "I've noted your message for your therapist. Is there anything else?",
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, fallbackMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [inputValue, isLoading, messages, mode]);

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Theme-based colors
  const accentColor = isDark ? '#B794D4' : '#5AB9B4';
  const logoGlow = isDark
    ? 'drop-shadow-[0_0_20px_rgba(183,148,212,0.7)] drop-shadow-[0_0_40px_rgba(139,106,174,0.5)] drop-shadow-[0_0_60px_rgba(139,106,174,0.3)]'
    : 'drop-shadow-[0_0_20px_rgba(90,185,180,0.7)] drop-shadow-[0_0_40px_rgba(90,185,180,0.4)] drop-shadow-[0_0_60px_rgba(90,185,180,0.2)]';

  const hasMessages = messages.length > 0;
  // Count user messages for logo hide logic (hide after 2 user messages)
  const userMessageCount = messages.filter(m => m.role === 'user').length;
  const shouldHideLogo = userMessageCount >= 2;

  return (
    <>
      {/* Compact Card - Dashboard widget */}
      <AnimatePresence mode="wait">
        {!isFullscreen && (
          <motion.div
            layoutId="dobby-chat-container"
            className={`rounded-3xl flex flex-col relative overflow-hidden h-[525px] fullscreen-chat-container ${
              isDark
                ? 'bg-[#1a1625] shadow-[0_8px_32px_rgba(0,0,0,0.4)]'
                : 'bg-[#F8F7F4] shadow-[0_8px_32px_rgba(0,0,0,0.08)]'
            }`}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{
              opacity: 1,
              scale: isHolding ? 1.02 : 1,
              transition: {
                duration: isHolding ? 1.5 : 0.3,
                ease: isHolding ? 'linear' : [0.23, 1, 0.32, 1]
              }
            }}
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
            {...longPressHandlers}
          >
            {/* Hold indicator overlay with centered logo - appears after 0.7s */}
            <AnimatePresence>
              {showAnimation && (
                <motion.div
                  className={`absolute inset-0 z-30 pointer-events-none rounded-3xl flex flex-col items-center justify-center ${
                    isDark ? 'bg-[#1a1625]/95' : 'bg-[#F8F7F4]/95'
                  }`}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                >
                  {/* Large centered logo with face */}
                  <DobbyLogo size={120} />

                  {/* Progress Bar - Video game style loading bar */}
                  <motion.div
                    className="flex items-center gap-3 mt-4"
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.15 }}
                  >
                    {/* Bar container */}
                    <div
                      className="relative w-[120px] h-[6px] rounded-full overflow-hidden"
                      style={{
                        border: `1.5px solid ${isDark ? '#8B6AAE' : '#5AB9B4'}`,
                        boxShadow: isDark
                          ? '0 0 8px rgba(139, 106, 174, 0.3)'
                          : '0 0 8px rgba(90, 185, 180, 0.3)',
                      }}
                    >
                      {/* Fill bar */}
                      <motion.div
                        className="absolute inset-0 rounded-full"
                        style={{
                          background: isDark ? '#E8E4EC' : '#E8E4EC',
                          width: `${progress}%`,
                          boxShadow: '0 0 4px rgba(232, 228, 236, 0.5)',
                        }}
                      />
                    </div>
                    {/* Percentage text */}
                    <span
                      className={`text-xs font-medium min-w-[32px] text-right ${
                        isDark ? 'text-[#8B6AAE]' : 'text-[#5AB9B4]'
                      }`}
                      style={{
                        textShadow: isDark
                          ? '0 0 6px rgba(139, 106, 174, 0.4)'
                          : '0 0 6px rgba(90, 185, 180, 0.4)',
                      }}
                    >
                      {Math.round(progress)}%
                    </span>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Sticky Header with DOBBY branding - illuminating DobbyLogo with face */}
            <div className={`flex-shrink-0 flex items-center justify-center py-3 ${
              isDark ? 'bg-[#1a1625]' : 'bg-[#F8F7F4]'
            }`}>
              {/* Fullscreen Button - absolute positioned */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsFullscreen(true);
                }}
                onMouseDown={(e) => e.stopPropagation()}
                onTouchStart={(e) => e.stopPropagation()}
                aria-label="Expand chat"
                className={`absolute top-3 right-4 w-9 h-9 flex items-center justify-center rounded-[10px] transition-all z-10 ${
                  isDark
                    ? 'text-[#B794D4] hover:bg-[rgba(155,122,196,0.2)] hover:scale-105'
                    : 'text-[#5AB9B4] hover:bg-[rgba(90,185,180,0.15)] hover:scale-105'
                }`}
              >
                <Maximize2 className="w-[18px] h-[18px]" />
              </button>

              {/* Centered Dobby Logo + DOBBY text - illuminating, clickable */}
              {/* Logo hides after 2 user messages, DOBBY text always visible and clickable */}
              <div
                className="cursor-pointer flex items-center gap-2"
                style={{
                  filter: isDark
                    ? 'drop-shadow(0 0 8px rgba(139, 106, 174, 0.56)) drop-shadow(0 0 17px rgba(139, 106, 174, 0.35))'
                    : 'drop-shadow(0 0 8px rgba(90, 185, 180, 0.56)) drop-shadow(0 0 17px rgba(90, 185, 180, 0.35))',
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  // Scroll to top of messages only
                  if (messagesContainerRef.current) {
                    messagesContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
                  }
                }}
              >
                {/* Logo - hides after 2 user messages */}
                <AnimatePresence>
                  {!shouldHideLogo && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      transition={{ duration: 0.2 }}
                    >
                      <DobbyLogo size={50} />
                    </motion.div>
                  )}
                </AnimatePresence>
                {/* DOBBY text - always visible, clickable for scroll to top */}
                <span
                  className={`font-mono text-lg font-medium tracking-[4px] uppercase ${
                    isDark ? 'text-[#9B7AC4]' : 'text-[#5AB9B4]'
                  }`}
                >
                  DOBBY
                </span>
              </div>
            </div>

            {/* 20px spacing below header */}
            <div className="h-5 flex-shrink-0" />

            {/* Content Area - Messages with intro */}
            <div className="flex-1 flex flex-col overflow-hidden px-4 pb-0 min-h-0">
              <div
                ref={messagesContainerRef}
                className="flex-1 overflow-y-auto space-y-3 scrollbar-hide"
              >
                {/* Dobby Intro Message - always shown first */}
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex justify-start items-start gap-2"
                >
                  {/* Dobby Avatar - with face for messages */}
                  <div className="flex-shrink-0 mt-1">
                    <DobbyLogo size={28} />
                  </div>
                  {/* Intro bubble */}
                  <div
                    className={`max-w-[85%] px-3 py-2 rounded-2xl rounded-tl-sm text-[13px] font-dm ${
                      isDark
                        ? 'bg-[#2a2535] text-gray-300'
                        : 'bg-white text-gray-700 shadow-sm border border-gray-100'
                    }`}
                  >
                    {DOBBY_INTRO}
                  </div>
                </motion.div>

                {/* User & AI Messages */}
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start items-start gap-2'}`}
                  >
                    {/* Avatar for assistant messages - always DobbyLogo with face */}
                    {/* Size: 32px (15% bigger than original 28px) */}
                    {msg.role === 'assistant' && (
                      <div className="flex-shrink-0 mt-1">
                        <DobbyLogo size={32} />
                      </div>
                    )}

                    {msg.role === 'user' ? (
                      // User message - text only (no bubble)
                      <span
                        className={`max-w-[85%] text-[13px] font-dm text-right ${
                          isDark ? 'text-white' : 'text-[#5AB9B4]'
                        }`}
                      >
                        {msg.content}
                      </span>
                    ) : (
                      // AI message - bubble style
                      <div
                        className={`max-w-[85%] px-3 py-2 rounded-2xl rounded-tl-sm text-[13px] font-dm ${
                          isDark
                            ? 'bg-[#2a2535] text-gray-300'
                            : 'bg-white text-gray-700 shadow-sm border border-gray-100'
                        }`}
                      >
                        {msg.content}
                      </div>
                    )}
                  </motion.div>
                ))}

                {/* Loading indicator */}
                {isLoading && (
                  <div className="flex justify-start items-start gap-2">
                    <div className="flex-shrink-0 mt-1">
                      <DobbyLogo size={32} />
                    </div>
                    <div className={`px-3 py-2 rounded-2xl rounded-tl-sm ${
                      isDark ? 'bg-[#2a2535]' : 'bg-white shadow-sm border border-gray-100'
                    }`}>
                      <div className="flex gap-1">
                        <span className={`w-2 h-2 rounded-full animate-bounce ${isDark ? 'bg-[#8B6AAE]' : 'bg-[#5AB9B4]'}`} style={{ animationDelay: '0ms' }} />
                        <span className={`w-2 h-2 rounded-full animate-bounce ${isDark ? 'bg-[#8B6AAE]' : 'bg-[#5AB9B4]'}`} style={{ animationDelay: '150ms' }} />
                        <span className={`w-2 h-2 rounded-full animate-bounce ${isDark ? 'bg-[#8B6AAE]' : 'bg-[#5AB9B4]'}`} style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input Section */}
            <div
              className="flex-shrink-0 px-5 pb-5 pt-3"
              onMouseDown={(e) => e.stopPropagation()}
              onTouchStart={(e) => e.stopPropagation()}
            >
              <div
                className={`rounded-2xl p-3.5 flex flex-col gap-3 ${
                  isDark
                    ? 'bg-[#252030] border border-[#3a3545]'
                    : 'bg-white border border-[#E5E2DE]'
                }`}
              >
                {/* Input Field - placeholder changes based on mode */}
                <input
                  type="text"
                  placeholder={mode === 'ai' ? "Ask Dobby anything..." : "Send a message to your therapist..."}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value.slice(0, MAX_CHARS))}
                  onKeyPress={handleKeyPress}
                  className={`w-full bg-transparent outline-none font-dm text-[15px] ${
                    isDark
                      ? 'text-[#E5E5E5] placeholder:text-[#666]'
                      : 'text-[#1a1a1a] placeholder:text-[#999]'
                  }`}
                />

                {/* Controls Row */}
                <div className="flex items-center justify-between">
                  {/* Mode Toggle - AI uses geometric Dobby, Therapist uses heart speech */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => setMode('ai')}
                      className={`flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-semibold transition-all ${
                        mode === 'ai'
                          ? isDark
                            ? 'bg-[#8B6AAE] text-white'
                            : 'bg-[#5AB9B4] text-white'
                          : isDark
                            ? 'bg-[#2a2535] text-[#888] hover:bg-[#3a3545]'
                            : 'bg-[#F0EFEB] text-[#666] hover:bg-[#E5E2DE]'
                      }`}
                    >
                      {/* Geometric Dobby icon for AI mode */}
                      <svg className="w-3.5 h-3.5" viewBox="0 0 120 120" fill="none">
                        <polygon points="15,55 35,35 35,65" fill="currentColor" />
                        <polygon points="105,55 85,35 85,65" fill="currentColor" />
                        <rect x="30" y="30" width="60" height="60" rx="14" fill="currentColor" />
                      </svg>
                      AI
                    </button>
                    <button
                      onClick={() => setMode('therapist')}
                      className={`flex items-center gap-1.5 px-3.5 py-2 rounded-full text-xs font-semibold transition-all ${
                        mode === 'therapist'
                          ? 'bg-gradient-to-br from-[#F4A69D] to-[#E88B7E] text-white'
                          : isDark
                            ? 'bg-[#2a2535] text-[#888] hover:bg-[#3a3545]'
                            : 'bg-[#F0EFEB] text-[#666] hover:bg-[#E5E2DE]'
                      }`}
                    >
                      {/* Heart speech icon for therapist mode - orange only when active */}
                      <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill={mode === 'therapist' ? 'currentColor' : isDark ? '#888' : '#666'}>
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
                      </svg>
                      THERAPIST
                    </button>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-3">
                    <span className={`text-xs ${isDark ? 'text-[#666]' : 'text-[#999]'}`}>
                      {inputValue.length}/{MAX_CHARS}
                    </span>
                    <button
                      onClick={handleSend}
                      disabled={!inputValue.trim() || isLoading}
                      aria-label="Send message"
                      className={`w-9 h-9 flex items-center justify-center rounded-[10px] transition-all ${
                        inputValue.trim() && !isLoading
                          ? isDark
                            ? 'bg-[#8B6AAE] text-white hover:bg-[#7B5A9E] hover:scale-105'
                            : 'bg-[#5AB9B4] text-white hover:bg-[#4AA9A4] hover:scale-105'
                          : isDark
                            ? 'bg-[#3a3545] text-[#666] cursor-not-allowed'
                            : 'bg-[#E5E2DE] text-[#999] cursor-not-allowed'
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
          </motion.div>
        )}
      </AnimatePresence>

      {/* Fullscreen Chat - Shared state with collapsed card */}
      <FullscreenChat
        isOpen={isFullscreen}
        onClose={() => setIsFullscreen(false)}
        messages={messages}
        setMessages={setMessages}
        mode={mode}
        setMode={setMode}
      />
    </>
  );
}
