'use client';

import * as React from 'react';
import { motion, AnimatePresence, PanInfo } from 'framer-motion';
import { Send, Bot, User, ChevronLeft, ChevronRight, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import { aiChatData, AIChatPrompt } from '@/lib/mock-data/dashboard-v2';
import { FullscreenWrapper } from '@/components/dashboard-v2/shared';
import { cardHoverVariants, staggerContainerVariants, staggerItemVariants } from '@/lib/animations';

// ============================================================================
// Types
// ============================================================================

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AIChatWidgetProps {
  /** Optional custom className for the compact card */
  className?: string;
  /** Optional callback when widget expands */
  onExpand?: () => void;
  /** Optional callback when widget collapses */
  onCollapse?: () => void;
}

// ============================================================================
// Constants
// ============================================================================

const PROMPTS_PER_PAGE = 2;
const TOTAL_PAGES = Math.ceil(aiChatData.prompts.length / PROMPTS_PER_PAGE);

// Initial welcome message from Dobby
const INITIAL_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  content: "Hi there! I'm Dobby, your therapy companion. I can help you prepare for sessions, explore patterns in your progress, or answer questions about your therapeutic journey. What would you like to talk about?",
  timestamp: new Date(),
};

// ============================================================================
// Animation Variants
// ============================================================================

const carouselVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 200 : -200,
    opacity: 0,
  }),
  center: {
    zIndex: 1,
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    zIndex: 0,
    x: direction < 0 ? 200 : -200,
    opacity: 0,
  }),
};

const messageVariants = {
  hidden: {
    opacity: 0,
    y: 10,
    scale: 0.95,
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring' as const,
      stiffness: 300,
      damping: 25,
    },
  },
};

// ============================================================================
// Dobby Logo Component
// ============================================================================

function DobbyLogo({ size = 60 }: { size?: number }) {
  return (
    <div
      className="relative flex items-center justify-center rounded-full"
      style={{
        width: size,
        height: size,
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%)',
        boxShadow: '0 4px 20px rgba(139, 92, 246, 0.3)',
      }}
    >
      <Bot className="text-white" style={{ width: size * 0.5, height: size * 0.5 }} />
      <Sparkles
        className="absolute -top-1 -right-1 text-yellow-400"
        style={{ width: size * 0.3, height: size * 0.3 }}
      />
    </div>
  );
}

// ============================================================================
// Prompt Card Component
// ============================================================================

interface PromptCardProps {
  prompt: AIChatPrompt;
  onClick: (text: string) => void;
}

function PromptCard({ prompt, onClick }: PromptCardProps) {
  return (
    <motion.button
      variants={staggerItemVariants}
      onClick={() => onClick(prompt.text)}
      className={cn(
        'w-full p-3 rounded-xl text-left',
        'bg-white/60 dark:bg-white/10 backdrop-blur-sm',
        'border border-white/40 dark:border-white/20',
        'hover:bg-white/80 dark:hover:bg-white/20',
        'transition-colors duration-200',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary',
        'text-sm text-foreground/80 line-clamp-2'
      )}
      aria-label={`Use prompt: ${prompt.text}`}
    >
      {prompt.text}
    </motion.button>
  );
}

// ============================================================================
// Carousel Dots Component
// ============================================================================

interface CarouselDotsProps {
  totalPages: number;
  currentPage: number;
  onPageChange: (page: number) => void;
}

function CarouselDots({ totalPages, currentPage, onPageChange }: CarouselDotsProps) {
  return (
    <div className="flex items-center justify-center gap-2 mt-3" role="tablist" aria-label="Carousel pages">
      {Array.from({ length: totalPages }).map((_, index) => (
        <button
          key={index}
          role="tab"
          aria-selected={currentPage === index}
          aria-label={`Go to page ${index + 1}`}
          onClick={() => onPageChange(index)}
          className={cn(
            'w-2 h-2 rounded-full transition-all duration-200',
            currentPage === index
              ? 'bg-primary w-4'
              : 'bg-primary/30 hover:bg-primary/50'
          )}
        />
      ))}
    </div>
  );
}

// ============================================================================
// Chat Input Component
// ============================================================================

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  placeholder?: string;
  compact?: boolean;
}

function ChatInput({ value, onChange, onSubmit, placeholder = 'Type a message...', compact = false }: ChatInputProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && value.trim()) {
      e.preventDefault();
      onSubmit();
    }
  };

  return (
    <div className={cn(
      'flex items-center gap-2',
      compact ? 'p-2' : 'p-3',
      'bg-white/80 dark:bg-card/80 backdrop-blur-sm',
      'rounded-xl border border-border/30',
      'shadow-sm'
    )}>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        className={cn(
          'flex-1 bg-transparent outline-none',
          'text-sm text-foreground placeholder:text-muted-foreground',
          compact ? 'px-2' : 'px-3'
        )}
        aria-label="Chat message input"
      />
      <button
        onClick={onSubmit}
        disabled={!value.trim()}
        className={cn(
          'p-2 rounded-lg',
          'bg-primary text-primary-foreground',
          'hover:bg-primary/90',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          'transition-colors duration-200',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
        )}
        aria-label="Send message"
      >
        <Send className="w-4 h-4" />
      </button>
    </div>
  );
}

// ============================================================================
// Message Bubble Component
// ============================================================================

interface MessageBubbleProps {
  message: ChatMessage;
}

function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <motion.div
      variants={messageVariants}
      initial="hidden"
      animate="visible"
      className={cn(
        'flex items-end gap-2 mb-4',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isUser
            ? 'bg-primary/10 text-primary'
            : 'bg-gradient-to-br from-violet-500 to-purple-600 text-white'
        )}
      >
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message content */}
      <div
        className={cn(
          'max-w-[75%] px-4 py-3 rounded-2xl',
          isUser
            ? 'bg-primary text-primary-foreground rounded-br-md'
            : 'bg-muted/60 text-foreground rounded-bl-md'
        )}
      >
        <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
        <span className={cn(
          'text-[10px] mt-1 block',
          isUser ? 'text-primary-foreground/70' : 'text-muted-foreground'
        )}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </motion.div>
  );
}

// ============================================================================
// Expanded Description Component
// ============================================================================

function ExpandedDescription() {
  const { capabilities } = aiChatData.expandedDescription;

  return (
    <motion.div
      initial={{ opacity: 0, height: 0 }}
      animate={{ opacity: 1, height: 'auto' }}
      exit={{ opacity: 0, height: 0 }}
      className="px-6 py-4 bg-gradient-to-b from-primary/5 to-transparent border-b border-border/30"
    >
      <h3 className="text-sm font-medium text-foreground mb-3">
        {aiChatData.expandedDescription.title}
      </h3>
      <ul className="space-y-2">
        {capabilities.map((capability, index) => (
          <li key={index} className="flex items-start gap-2 text-sm text-muted-foreground">
            <Sparkles className="w-4 h-4 mt-0.5 text-primary/60 flex-shrink-0" />
            <span>{capability}</span>
          </li>
        ))}
      </ul>
    </motion.div>
  );
}

// ============================================================================
// Fullscreen Chat View
// ============================================================================

interface FullscreenChatProps {
  isOpen: boolean;
  onClose: () => void;
  messages: ChatMessage[];
  inputValue: string;
  onInputChange: (value: string) => void;
  onSendMessage: () => void;
  onPromptClick: (text: string) => void;
  prompts: AIChatPrompt[];
}

function FullscreenChat({
  isOpen,
  onClose,
  messages,
  inputValue,
  onInputChange,
  onSendMessage,
  onPromptClick,
  prompts,
}: FullscreenChatProps) {
  const messagesEndRef = React.useRef<HTMLDivElement>(null);
  const scrollContainerRef = React.useRef<HTMLDivElement>(null);
  const [showDescription, setShowDescription] = React.useState(true);

  // Scroll to bottom when messages change
  React.useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle scroll to detect if user scrolled to top
  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollTop } = scrollContainerRef.current;
      setShowDescription(scrollTop < 50);
    }
  };

  return (
    <FullscreenWrapper
      isOpen={isOpen}
      onClose={onClose}
      title="Chat with Dobby"
      titleIcon={<Bot className="w-5 h-5 text-primary" />}
      showBackArrow
      showCloseButton
      footer={
        <div className="space-y-3">
          {/* Prompt suggestions */}
          {messages.length <= 1 && (
            <motion.div
              variants={staggerContainerVariants}
              initial="hidden"
              animate="visible"
              className="grid grid-cols-2 gap-2"
            >
              {prompts.slice(0, 4).map((prompt) => (
                <PromptCard key={prompt.id} prompt={prompt} onClick={onPromptClick} />
              ))}
            </motion.div>
          )}

          {/* Chat input */}
          <ChatInput
            value={inputValue}
            onChange={onInputChange}
            onSubmit={onSendMessage}
            placeholder="Ask Dobby anything..."
          />
        </div>
      }
    >
      {/* Expanded description (visible when scrolled to top) */}
      <AnimatePresence>
        {showDescription && <ExpandedDescription />}
      </AnimatePresence>

      {/* Messages area */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-6 py-4"
      >
        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}
        <div ref={messagesEndRef} />
      </div>
    </FullscreenWrapper>
  );
}

// ============================================================================
// Main AIChatWidget Component
// ============================================================================

export function AIChatWidget({ className, onExpand, onCollapse }: AIChatWidgetProps) {
  // State
  const [isFullscreen, setIsFullscreen] = React.useState(false);
  const [messages, setMessages] = React.useState<ChatMessage[]>([INITIAL_MESSAGE]);
  const [inputValue, setInputValue] = React.useState('');
  const [currentPromptPage, setCurrentPromptPage] = React.useState(0);
  const [animationDirection, setAnimationDirection] = React.useState(0);

  // Get prompts for current page
  const currentPrompts = React.useMemo(() => {
    const startIndex = currentPromptPage * PROMPTS_PER_PAGE;
    return aiChatData.prompts.slice(startIndex, startIndex + PROMPTS_PER_PAGE);
  }, [currentPromptPage]);

  // Handlers
  const handleExpand = () => {
    setIsFullscreen(true);
    onExpand?.();
  };

  const handleCollapse = () => {
    setIsFullscreen(false);
    onCollapse?.();
  };

  const handleSendMessage = () => {
    if (!inputValue.trim()) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');

    // Simulate AI response (in real app, this would call an API)
    setTimeout(() => {
      const aiResponse: ChatMessage = {
        id: `ai-${Date.now()}`,
        role: 'assistant',
        content: generateMockResponse(userMessage.content),
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, aiResponse]);
    }, 1000);
  };

  const handlePromptClick = (text: string) => {
    setInputValue(text);
    // If in fullscreen, optionally auto-send
    // For now, just set the input so user can review before sending
  };

  const handlePageChange = (newPage: number) => {
    const newDirection = newPage > currentPromptPage ? 1 : -1;
    setAnimationDirection(newDirection);
    setCurrentPromptPage(newPage);
  };

  const handleDragEnd = (_: unknown, info: PanInfo) => {
    const swipeThreshold = 50;
    if (info.offset.x < -swipeThreshold && currentPromptPage < TOTAL_PAGES - 1) {
      handlePageChange(currentPromptPage + 1);
    } else if (info.offset.x > swipeThreshold && currentPromptPage > 0) {
      handlePageChange(currentPromptPage - 1);
    }
  };

  const handlePrevPage = () => {
    if (currentPromptPage > 0) {
      handlePageChange(currentPromptPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPromptPage < TOTAL_PAGES - 1) {
      handlePageChange(currentPromptPage + 1);
    }
  };

  return (
    <>
      {/* Compact Card View */}
      <motion.div
        variants={cardHoverVariants}
        initial="initial"
        whileHover="hover"
        whileTap="tap"
        onClick={handleExpand}
        className={cn(
          'relative overflow-hidden rounded-2xl cursor-pointer',
          'border border-border/30',
          'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
          className
        )}
        style={{
          background: 'linear-gradient(135deg, hsl(220 85% 98%) 0%, hsl(240 80% 98%) 50%, hsl(260 75% 98%) 100%)',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        }}
        role="button"
        tabIndex={0}
        aria-label="Open chat with Dobby"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleExpand();
          }
        }}
      >
        <div className="p-6 flex flex-col items-center">
          {/* Dobby Logo */}
          <DobbyLogo size={60} />

          {/* Description */}
          <p className="mt-4 text-sm text-center text-muted-foreground px-4 leading-relaxed">
            {aiChatData.description}
          </p>

          {/* Prompt Carousel */}
          <div className="w-full mt-4 relative">
            {/* Navigation arrows */}
            <button
              onClick={(e) => {
                e.stopPropagation();
                handlePrevPage();
              }}
              disabled={currentPromptPage === 0}
              className={cn(
                'absolute left-0 top-1/2 -translate-y-1/2 z-10',
                'p-1 rounded-full bg-white/80 shadow-sm',
                'text-muted-foreground hover:text-foreground',
                'disabled:opacity-0 disabled:cursor-default',
                'transition-all duration-200'
              )}
              aria-label="Previous prompts"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            <button
              onClick={(e) => {
                e.stopPropagation();
                handleNextPage();
              }}
              disabled={currentPromptPage === TOTAL_PAGES - 1}
              className={cn(
                'absolute right-0 top-1/2 -translate-y-1/2 z-10',
                'p-1 rounded-full bg-white/80 shadow-sm',
                'text-muted-foreground hover:text-foreground',
                'disabled:opacity-0 disabled:cursor-default',
                'transition-all duration-200'
              )}
              aria-label="Next prompts"
            >
              <ChevronRight className="w-4 h-4" />
            </button>

            {/* Carousel content */}
            <div className="overflow-hidden mx-6">
              <AnimatePresence initial={false} custom={animationDirection} mode="wait">
                <motion.div
                  key={currentPromptPage}
                  custom={animationDirection}
                  variants={carouselVariants}
                  initial="enter"
                  animate="center"
                  exit="exit"
                  transition={{
                    x: { type: 'spring', stiffness: 300, damping: 30 },
                    opacity: { duration: 0.2 },
                  }}
                  drag="x"
                  dragConstraints={{ left: 0, right: 0 }}
                  dragElastic={0.2}
                  onDragEnd={handleDragEnd}
                  className="grid grid-cols-1 gap-2"
                >
                  {currentPrompts.map((prompt) => (
                    <motion.button
                      key={prompt.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePromptClick(prompt.text);
                        handleExpand();
                      }}
                      className={cn(
                        'w-full p-3 rounded-xl text-left',
                        'bg-white/60 backdrop-blur-sm',
                        'border border-white/40',
                        'hover:bg-white/80',
                        'transition-colors duration-200',
                        'text-sm text-foreground/80 line-clamp-2'
                      )}
                      aria-label={`Use prompt: ${prompt.text}`}
                    >
                      {prompt.text}
                    </motion.button>
                  ))}
                </motion.div>
              </AnimatePresence>
            </div>

            {/* Carousel dots */}
            <CarouselDots
              totalPages={TOTAL_PAGES}
              currentPage={currentPromptPage}
              onPageChange={(page) => {
                handlePageChange(page);
              }}
            />
          </div>

          {/* Chat Input */}
          <div className="w-full mt-4" onClick={(e) => e.stopPropagation()}>
            <ChatInput
              value={inputValue}
              onChange={setInputValue}
              onSubmit={() => {
                if (inputValue.trim()) {
                  handleExpand();
                  // Small delay to ensure fullscreen is open before sending
                  setTimeout(handleSendMessage, 100);
                }
              }}
              placeholder="Ask Dobby..."
              compact
            />
          </div>
        </div>

        {/* Click hint */}
        <div className="pb-4 pt-1">
          <p className="text-xs text-muted-foreground text-center">
            Tap to open full chat
          </p>
        </div>
      </motion.div>

      {/* Fullscreen Chat */}
      <FullscreenChat
        isOpen={isFullscreen}
        onClose={handleCollapse}
        messages={messages}
        inputValue={inputValue}
        onInputChange={setInputValue}
        onSendMessage={handleSendMessage}
        onPromptClick={handlePromptClick}
        prompts={aiChatData.prompts}
      />
    </>
  );
}

// ============================================================================
// Helper Functions
// ============================================================================

function generateMockResponse(userMessage: string): string {
  const lowerMessage = userMessage.toLowerCase();

  if (lowerMessage.includes('mood') || lowerMessage.includes('stress')) {
    return "Based on your session data, I've noticed your mood tends to dip after high-pressure work days, especially when you haven't had time for your grounding exercises. Your therapist mentioned this pattern in Session 7. Would you like me to suggest some quick techniques you can use during busy days?";
  }

  if (lowerMessage.includes('boundary') || lowerMessage.includes('boundaries')) {
    return "Setting boundaries has been a key focus in your recent sessions. In Session 10, you successfully set a boundary with a friend about time commitments - that's great progress! Your therapist suggested practicing 'I feel' statements. Would you like to work through a scenario together?";
  }

  if (lowerMessage.includes('pattern') || lowerMessage.includes('patterns')) {
    return "I've identified a few patterns from your 10 sessions:\n\n1. Work stress often triggers relationship tension\n2. Your mood improves significantly after completing homework\n3. Grounding techniques have the highest correlation with mood improvement (+0.85)\n\nWould you like to explore any of these patterns in more detail?";
  }

  if (lowerMessage.includes('session') || lowerMessage.includes('therapist')) {
    return "Your next session is scheduled for December 20th. Based on your recent progress, some topics you might want to discuss include:\n\n- Your success with boundary-setting\n- The laddering technique from Session 9\n- Any challenges with the behavioral experiment\n\nWould you like me to help you prepare notes for your therapist?";
  }

  if (lowerMessage.includes('breathing') || lowerMessage.includes('technique')) {
    return "You've been practicing the 4-7-8 breathing technique, which your therapist introduced in Session 8. Here's a quick refresher:\n\n1. Breathe in for 4 counts\n2. Hold for 7 counts\n3. Exhale for 8 counts\n\nThe data shows this technique has a 0.78 correlation with improved mood when practiced consistently. Would you like to try it now?";
  }

  return "I hear you. Based on what you've shared, this connects to themes from your recent sessions. Your therapist has noted the importance of self-compassion in these moments. Would you like to explore this further, or would you prefer I save this topic for your next session?";
}

// ============================================================================
// Exports
// ============================================================================

export type { AIChatWidgetProps, ChatMessage };
export default AIChatWidget;
