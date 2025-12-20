'use client';

/**
 * AIChatCard - Dual-mode AI therapy companion interface
 * Compact State: Dashboard widget with prompt carousel
 * Fullscreen State: Immersive chat interface
 * Design: Hume.ai-inspired monospace aesthetic
 *
 * FIXED: Dark mode gradient now matches the rest of the dark mode page
 * - Compact: Uses dark:from-[#1a1625] dark:to-[#2a2435] (same as page background)
 * - "Ask Dobby anything" placeholder also matches dark theme
 */

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, ChevronLeft, ChevronRight, Maximize2 } from 'lucide-react';
import { DobbyLogo } from './DobbyLogo';
import { useTheme } from '../contexts/ThemeContext';

// Types
type ChatMode = 'ai' | 'therapist';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Constants
const MAX_CHARS = 500;

const SUGGESTED_PROMPTS = [
  "Why does my mood drop after family visits?",
  "Help me prep to discuss boundaries with my partner",
  "Explain the TIPP technique again",
  "What should I bring up in next session?",
  "I had a panic attack - what do I do?",
  "Send message to my therapist"
];

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: '1',
    role: 'assistant',
    content: "Hi! I'm Dobby, your AI therapy companion. I can help you prepare for sessions, answer questions about techniques, or forward messages to your therapist. How can I help you today?",
    timestamp: new Date()
  }
];

// Sub-component: Mode Toggle
interface ModeToggleProps {
  mode: ChatMode;
  setMode: (mode: ChatMode) => void;
}

function ModeToggle({ mode, setMode }: ModeToggleProps) {
  return (
    <div className="flex gap-1.5 bg-white dark:bg-[#2a2435] rounded-full p-1 border border-gray-200 dark:border-[#3d3548] shadow-sm">
      <button
        onClick={() => setMode('ai')}
        aria-label="Switch to AI mode"
        className={`
          font-mono text-[12px] font-[450] px-3 py-1.5 rounded-full transition-all uppercase tracking-wide
          ${mode === 'ai'
            ? 'bg-gradient-to-br from-[#5AB9B4] to-[#4A9D99] text-white shadow-sm'
            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#3d3548]'
          }
        `}
      >
        🤖 AI
      </button>
      <button
        onClick={() => setMode('therapist')}
        aria-label="Switch to Therapist mode"
        className={`
          font-mono text-[12px] font-[450] px-3 py-1.5 rounded-full transition-all uppercase tracking-wide
          ${mode === 'therapist'
            ? 'bg-gradient-to-br from-[#F4A69D] to-[#E88B7E] text-white shadow-sm'
            : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#3d3548]'
          }
        `}
      >
        💬 Therapist
      </button>
    </div>
  );
}

// Main Component
export function AIChatCard() {
  const { isDark } = useTheme();
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [mode, setMode] = useState<ChatMode>('ai');
  const [inputValue, setInputValue] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [promptIndex, setPromptIndex] = useState(0);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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
    if (isFullscreen && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isFullscreen]);

  // Focus textarea on fullscreen
  useEffect(() => {
    if (isFullscreen && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [isFullscreen]);

  // Handlers
  const handleSend = () => {
    if (!inputValue.trim()) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: inputValue,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');

    // Simulate AI response
    setTimeout(() => {
      const aiMsg: ChatMessage = {
        id: `msg-${Date.now()}-ai`,
        role: 'assistant',
        content: mode === 'ai'
          ? "I understand you're working through that. Based on your recent sessions, this connects to the boundary-setting work you've been doing. Would you like to explore this further?"
          : "I've forwarded your message to your therapist. They typically respond within 24 hours. Is there anything else I can help you with in the meantime?",
        timestamp: new Date()
      };
      setMessages(prev => [...prev, aiMsg]);
    }, 1000);
  };

  const handlePromptClick = (prompt: string) => {
    setInputValue(prompt);
    if (isFullscreen) {
      setTimeout(() => {
        if (textareaRef.current) {
          handleSend();
        }
      }, 100);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const charCount = inputValue.length;

  // Sub-component: Input Area
  const InputArea = ({ isCompact }: { isCompact: boolean }) => (
    <div className={`flex flex-col gap-2 ${isCompact ? '' : 'w-full'}`}>
      <div className={`
        flex items-end gap-2 bg-white dark:bg-[#2a2435] rounded-3xl border border-gray-200 dark:border-[#3d3548]
        focus-within:border-[#5AB9B4] focus-within:ring-2 focus-within:ring-[#5AB9B4]/20
        transition-all shadow-sm
        ${isCompact ? 'p-2' : 'p-3'}
        ${isCompact ? '' : 'w-full'}
      `}>
        <div className="flex-1 flex flex-col gap-1.5">
          <textarea
            ref={textareaRef}
            placeholder={mode === 'ai' ? "Ask Dobby anything..." : "Message your therapist..."}
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value.slice(0, MAX_CHARS))}
            onKeyPress={handleKeyPress}
            className={`
              font-mono font-[350] outline-none bg-transparent text-gray-800 dark:text-gray-200
              placeholder:text-gray-400 dark:placeholder:text-gray-500 resize-none w-full
              ${isCompact ? 'text-[12px] min-h-[20px]' : 'text-[14px] min-h-[48px]'}
            `}
            style={{ maxHeight: isCompact ? '60px' : '120px' }}
          />
          <div className="flex items-center justify-between">
            <ModeToggle mode={mode} setMode={setMode} />
            <span
              className="font-mono text-[10px] font-[350] text-gray-400 dark:text-gray-500"
              aria-live="polite"
              aria-label={`${charCount} of ${MAX_CHARS} characters`}
            >
              {charCount}/{MAX_CHARS}
            </span>
          </div>
        </div>
        <button
          onClick={handleSend}
          disabled={!inputValue.trim()}
          aria-label="Send message"
          className={`
            flex items-center justify-center rounded-full flex-shrink-0
            transition-all shadow-md
            ${isCompact ? 'w-10 h-10' : 'w-12 h-12'}
            ${inputValue.trim()
              ? 'bg-gradient-to-br from-[#5AB9B4] to-[#4A9D99] text-white hover:shadow-lg hover:scale-105'
              : 'bg-gray-100 dark:bg-[#3d3548] text-gray-400 cursor-not-allowed'
            }
          `}
        >
          <Send className={isCompact ? 'w-4 h-4' : 'w-5 h-5'} />
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Compact Card - FIXED: Dark mode gradient matches page background */}
      {!isFullscreen && (
        <motion.div
          layoutId="chat-card"
          className="bg-gradient-to-br from-[#EBF8FF] to-[#F0F9FF] dark:from-[#1a1625] dark:to-[#2a2435] rounded-2xl p-4 shadow-lg h-[280px] flex flex-col relative overflow-hidden transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548]"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          {/* Expand Button */}
          <button
            onClick={() => setIsFullscreen(true)}
            className="absolute top-3 right-3 w-8 h-8 flex items-center justify-center rounded-full hover:bg-white/50 dark:hover:bg-white/10 transition-colors z-10"
            aria-label="Expand chat"
          >
            <Maximize2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>

          {/* Logo & Header */}
          <div className="text-center mb-2 flex-shrink-0">
            <div className="w-12 h-12 mx-auto mb-1.5">
              <DobbyLogo size={48} />
            </div>
            <h3 className="font-mono text-[14px] font-[450] text-gray-800 dark:text-gray-200 mb-0.5 uppercase tracking-wide">
              Chat with Dobby
            </h3>
            <p className="font-mono text-[10px] font-[350] text-gray-600 dark:text-gray-400 leading-tight">
              AI therapy companion
            </p>
          </div>

          {/* Prompt Carousel */}
          <div className="flex-shrink-0 mb-2">
            <div className="flex items-center justify-center gap-1">
              <button
                onClick={() => setPromptIndex(Math.max(0, promptIndex - 2))}
                disabled={promptIndex === 0}
                className="w-6 h-6 flex items-center justify-center rounded-full hover:bg-white/50 dark:hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                aria-label="Previous prompts"
              >
                <ChevronLeft className="w-3 h-3 text-gray-600 dark:text-gray-400" />
              </button>

              <div className="flex gap-1.5 overflow-hidden px-1">
                {SUGGESTED_PROMPTS.slice(promptIndex, promptIndex + 2).map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handlePromptClick(prompt)}
                    className="
                      font-mono text-[10px] font-[350] px-2.5 py-1.5 bg-white dark:bg-[#2a2435] rounded-xl
                      shadow-sm hover:shadow-md hover:bg-[#5AB9B4]/5 dark:hover:bg-[#a78bfa]/10
                      hover:text-[#5AB9B4] dark:hover:text-[#a78bfa]
                      transition-all border border-gray-200 dark:border-[#3d3548]
                      whitespace-nowrap overflow-hidden text-ellipsis max-w-[110px]
                      text-gray-700 dark:text-gray-300
                    "
                  >
                    {prompt.slice(0, 20)}...
                  </button>
                ))}
              </div>

              <button
                onClick={() => setPromptIndex(Math.min(SUGGESTED_PROMPTS.length - 2, promptIndex + 2))}
                disabled={promptIndex >= SUGGESTED_PROMPTS.length - 2}
                className="w-6 h-6 flex items-center justify-center rounded-full hover:bg-white/50 dark:hover:bg-white/10 disabled:opacity-30 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                aria-label="Next prompts"
              >
                <ChevronRight className="w-3 h-3 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            {/* Pagination Dots */}
            <div className="flex justify-center gap-1 mt-1.5">
              {Array.from({ length: Math.ceil(SUGGESTED_PROMPTS.length / 2) }).map((_, idx) => (
                <div
                  key={idx}
                  className={`w-1 h-1 rounded-full transition-colors ${
                    idx === promptIndex / 2 ? 'bg-[#5AB9B4] dark:bg-[#a78bfa]' : 'bg-gray-300 dark:bg-gray-600'
                  }`}
                />
              ))}
            </div>
          </div>

          {/* Separator Line */}
          <div className="h-px bg-gray-200 dark:bg-[#3d3548] mb-2 flex-shrink-0" />

          {/* Input Area */}
          <div className="flex-1 min-h-0 flex flex-col justify-end">
            <InputArea isCompact={true} />
          </div>
        </motion.div>
      )}

      {/* Fullscreen Chat - FIXED: Dark mode gradient for entire overlay */}
      <AnimatePresence>
        {isFullscreen && (
          <motion.div
            layoutId="chat-card"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
            className="fixed inset-0 z-[2000] bg-white dark:bg-[#1a1625] flex flex-col"
          >
            {/* Top Bar */}
            <div className="h-[72px] border-b border-gray-200 dark:border-[#3d3548] flex items-center justify-between px-8 flex-shrink-0 bg-white dark:bg-[#1a1625]">
              <div className="flex items-center gap-3">
                <DobbyLogo size={40} />
                <div>
                  <h2 className="font-mono text-[18px] font-[450] text-gray-800 dark:text-gray-200 uppercase tracking-wide">
                    Chat with Dobby
                  </h2>
                  <div className="flex items-center gap-1.5">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                    <span className="font-mono text-[11px] font-[350] text-gray-500 dark:text-gray-400">
                      Online
                    </span>
                  </div>
                </div>
              </div>
              <button
                onClick={() => setIsFullscreen(false)}
                className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
                aria-label="Close fullscreen"
              >
                <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </button>
            </div>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto px-8 py-6 bg-gray-50 dark:bg-[#1a1625]">
              <div className="max-w-3xl mx-auto space-y-6">
                {/* Intro Card - FIXED: Dark mode gradient */}
                <div className="bg-gradient-to-br from-[#EBF8FF] to-[#F0F9FF] dark:from-[#2a2435] dark:to-[#3d3548] rounded-2xl p-6 border border-gray-200 dark:border-[#3d3548]">
                  <div className="flex items-start gap-4">
                    <DobbyLogo size={48} />
                    <div>
                      <h3 className="font-mono text-[16px] font-[450] text-gray-800 dark:text-gray-200 mb-2 uppercase">
                        Meet Dobby
                      </h3>
                      <p className="font-mono text-[13px] font-[350] text-gray-600 dark:text-gray-400 leading-relaxed">
                        I&apos;m your AI therapy companion. I can help you prepare for sessions,
                        answer questions about techniques, track your mood, or forward messages
                        to your therapist. Everything is confidential and designed to support
                        your therapy journey.
                      </p>
                    </div>
                  </div>
                </div>

                {/* Messages */}
                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                  >
                    {/* Avatar */}
                    <div className="flex-shrink-0">
                      {msg.role === 'assistant' ? (
                        <DobbyLogo size={32} />
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-gray-300 dark:bg-[#3d3548] flex items-center justify-center">
                          <span className="text-sm">👤</span>
                        </div>
                      )}
                    </div>

                    {/* Message Bubble */}
                    <div
                      className={`
                        font-mono text-[14px] font-[350] leading-relaxed max-w-[70%] p-4 rounded-2xl
                        ${msg.role === 'user'
                          ? 'bg-gradient-to-br from-[#5AB9B4] to-[#4A9D99] text-white rounded-tr-sm'
                          : 'bg-white dark:bg-[#2a2435] text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-[#3d3548] rounded-tl-sm shadow-sm'
                        }
                      `}
                    >
                      {msg.content}
                    </div>
                  </motion.div>
                ))}

                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Bottom Section */}
            <div className="flex-shrink-0 border-t border-gray-200 dark:border-[#3d3548] bg-white dark:bg-[#1a1625]">
              {/* Suggested Prompts */}
              <div className="px-8 pt-4">
                <div className="max-w-3xl mx-auto">
                  <p className="font-mono text-[11px] font-[450] text-gray-500 dark:text-gray-400 mb-2 uppercase tracking-wide">
                    Suggested Prompts
                  </p>
                  <div className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide">
                    {SUGGESTED_PROMPTS.map((prompt, idx) => (
                      <button
                        key={idx}
                        onClick={() => handlePromptClick(prompt)}
                        className="
                          font-mono text-[13px] font-[350] px-4 py-2 bg-white dark:bg-[#2a2435] rounded-full
                          border border-gray-200 dark:border-[#3d3548] hover:bg-[#5AB9B4]/5 dark:hover:bg-[#a78bfa]/10
                          hover:text-[#5AB9B4] dark:hover:text-[#a78bfa]
                          transition-all whitespace-nowrap shadow-sm hover:shadow-md flex-shrink-0
                          text-gray-700 dark:text-gray-300
                        "
                      >
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Input Area */}
              <div className="px-8 py-4">
                <div className="max-w-3xl mx-auto">
                  <InputArea isCompact={false} />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
