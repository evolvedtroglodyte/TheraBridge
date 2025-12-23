'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, ChevronLeft, ChevronRight, Calendar, Clock, User, Users } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  sessionsData,
  getMoodColor,
  getMoodBorderClass,
  type Session,
  type SessionMood,
} from '@/lib/mock-data/dashboard-v2';
import { FullscreenWrapper } from './shared';
import {
  cardHoverVariants,
  staggerContainerVariants,
  staggerItemVariants,
} from '@/lib/animations';

// ============================================================================
// Constants
// ============================================================================

const CARDS_PER_PAGE = 8;
const TOTAL_PAGES = Math.ceil(sessionsData.length / CARDS_PER_PAGE);

// Mood emoji mapping
const getMoodEmojiIcon = (mood: SessionMood): string => {
  switch (mood) {
    case 'positive':
      return '😊';
    case 'neutral':
      return '😐';
    case 'low':
      return '😔';
    default:
      return '😐';
  }
};

// Mood background color for left border (tailwind compatible)
const getMoodBgClass = (mood: SessionMood): string => {
  switch (mood) {
    case 'positive':
      return 'bg-green-400';
    case 'neutral':
      return 'bg-blue-400';
    case 'low':
      return 'bg-rose-400';
    default:
      return 'bg-blue-400';
  }
};

// ============================================================================
// Types
// ============================================================================

interface SessionCardProps {
  session: Session;
  onClick: () => void;
}

interface PaginationDotsProps {
  currentPage: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

interface SessionDetailViewProps {
  session: Session;
  onClose: () => void;
}

// ============================================================================
// Milestone Badge Component
// ============================================================================

function MilestoneBadge({ text }: { text: string }) {
  return (
    <div
      className={cn(
        'absolute -top-3 left-1/2 -translate-x-1/2',
        'flex items-center gap-1.5 px-3 py-1',
        'bg-amber-100 text-amber-800',
        'rounded-full text-xs font-medium',
        'border border-amber-200',
        'shadow-sm',
        // Glow effect
        'shadow-amber-200/50'
      )}
      style={{
        boxShadow: '0 0 12px rgba(251, 191, 36, 0.3), 0 2px 4px rgba(0,0,0,0.08)',
      }}
    >
      <Star className="w-3 h-3 fill-amber-500 text-amber-500" />
      <span className="whitespace-nowrap">{text}</span>
    </div>
  );
}

// ============================================================================
// Session Card Component
// ============================================================================

function SessionCard({ session, onClick }: SessionCardProps) {
  const [isHovered, setIsHovered] = React.useState(false);

  return (
    <motion.button
      variants={cardHoverVariants}
      initial="initial"
      whileHover="hover"
      whileTap="tap"
      onHoverStart={() => setIsHovered(true)}
      onHoverEnd={() => setIsHovered(false)}
      onClick={onClick}
      className={cn(
        'relative w-full text-left',
        'bg-white dark:bg-card',
        'rounded-xl overflow-hidden',
        'border border-border/50',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
        'transition-all duration-200',
        // Mood-based left border
        'border-l-4',
        getMoodBorderClass(session.mood),
        // Add extra top padding for milestone badge
        session.isMilestone ? 'mt-4' : ''
      )}
      style={{
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      }}
      aria-label={`Session ${session.sessionNumber} - ${session.displayDate}. Topics: ${session.topics.join(', ')}`}
    >
      {/* Milestone Badge */}
      {session.isMilestone && session.milestoneText && (
        <MilestoneBadge text={session.milestoneText} />
      )}

      {/* Top accent bar on hover */}
      <div
        className={cn(
          'absolute top-0 left-0 right-0 h-1',
          getMoodBgClass(session.mood),
          'transition-opacity duration-200',
          isHovered ? 'opacity-100' : 'opacity-0'
        )}
      />

      {/* Card Content */}
      <div className="p-4">
        {/* Metadata Row */}
        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-3">
          <span className="font-medium">{session.displayDate}</span>
          <span className="text-border">•</span>
          <span>{session.duration}m</span>
          <span className="text-border">•</span>
          <span className="text-base">{getMoodEmojiIcon(session.mood)}</span>
        </div>

        {/* Two-Column Split */}
        <div className="grid grid-cols-2 gap-3">
          {/* Left Column: Topics */}
          <div>
            <h4 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
              Topics
            </h4>
            <ul className="space-y-1">
              {session.topics.slice(0, 3).map((topic, idx) => (
                <li
                  key={idx}
                  className="text-xs text-foreground leading-tight truncate"
                >
                  {topic}
                </li>
              ))}
            </ul>
          </div>

          {/* Right Column: Strategy + Actions */}
          <div>
            <h4 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1.5">
              Strategy
            </h4>
            <p className="text-xs text-foreground font-medium mb-2 truncate">
              {session.strategy}
            </p>
            {session.actions.length > 0 && (
              <>
                <h4 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                  Actions
                </h4>
                <ul className="space-y-0.5">
                  {session.actions.slice(0, 2).map((action) => (
                    <li
                      key={action.id}
                      className="text-[11px] text-muted-foreground leading-tight truncate flex items-start gap-1"
                    >
                      <span className="text-primary">•</span>
                      <span className="truncate">{action.text}</span>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </div>
        </div>
      </div>
    </motion.button>
  );
}

// ============================================================================
// Pagination Dots Component
// ============================================================================

function PaginationDots({ currentPage, totalPages, onPageChange }: PaginationDotsProps) {
  return (
    <div className="flex items-center justify-center gap-3 mt-4">
      {/* Previous Arrow */}
      <button
        type="button"
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className={cn(
          'p-1.5 rounded-full transition-colors',
          currentPage === 1
            ? 'text-muted-foreground/30 cursor-not-allowed'
            : 'text-muted-foreground hover:text-foreground hover:bg-muted/80'
        )}
        aria-label="Previous page"
      >
        <ChevronLeft className="w-4 h-4" />
      </button>

      {/* Dots */}
      <div className="flex items-center gap-2">
        {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
          <button
            key={page}
            type="button"
            onClick={() => onPageChange(page)}
            className={cn(
              'w-2.5 h-2.5 rounded-full transition-all duration-200',
              page === currentPage
                ? 'bg-primary scale-110'
                : 'bg-muted-foreground/30 hover:bg-muted-foreground/50'
            )}
            aria-label={`Go to page ${page}`}
            aria-current={page === currentPage ? 'page' : undefined}
          />
        ))}
      </div>

      {/* Next Arrow */}
      <button
        type="button"
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className={cn(
          'p-1.5 rounded-full transition-colors',
          currentPage === totalPages
            ? 'text-muted-foreground/30 cursor-not-allowed'
            : 'text-muted-foreground hover:text-foreground hover:bg-muted/80'
        )}
        aria-label="Next page"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    </div>
  );
}

// ============================================================================
// Transcript Line Component
// ============================================================================

function TranscriptLine({
  speaker,
  text,
  isTherapist,
}: {
  speaker: string;
  text: string;
  isTherapist: boolean;
}) {
  return (
    <div className={cn('flex gap-3 py-3', isTherapist ? '' : 'bg-muted/30 -mx-4 px-4')}>
      <div
        className={cn(
          'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
          isTherapist ? 'bg-primary/10' : 'bg-secondary/50'
        )}
      >
        {isTherapist ? (
          <User className="w-4 h-4 text-primary" />
        ) : (
          <Users className="w-4 h-4 text-muted-foreground" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <span
          className={cn(
            'text-xs font-semibold block mb-1',
            isTherapist ? 'text-primary' : 'text-muted-foreground'
          )}
        >
          {speaker}
        </span>
        <p className="text-sm text-foreground leading-relaxed">{text}</p>
      </div>
    </div>
  );
}

// ============================================================================
// Session Detail View (Fullscreen Content)
// ============================================================================

function SessionDetailView({ session, onClose }: SessionDetailViewProps) {
  // Parse transcript into lines
  const transcriptLines = React.useMemo(() => {
    const lines: { speaker: string; text: string; isTherapist: boolean }[] = [];
    const rawLines = session.transcript.split('\n\n');

    for (const line of rawLines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      if (trimmed.startsWith('Therapist:')) {
        lines.push({
          speaker: 'Therapist',
          text: trimmed.replace('Therapist:', '').trim(),
          isTherapist: true,
        });
      } else if (trimmed.startsWith('Patient:')) {
        lines.push({
          speaker: 'Patient',
          text: trimmed.replace('Patient:', '').trim(),
          isTherapist: false,
        });
      } else if (trimmed.startsWith('[')) {
        // Stage direction / note
        lines.push({
          speaker: 'Note',
          text: trimmed,
          isTherapist: true,
        });
      }
    }

    return lines;
  }, [session.transcript]);

  return (
    <FullscreenWrapper
      isOpen={true}
      onClose={onClose}
      title={`Session ${session.sessionNumber} - ${session.displayDate}`}
      titleIcon={<Calendar className="w-5 h-5 text-primary" />}
      subtitle={session.isMilestone ? session.milestoneText : undefined}
      headerActions={
        session.isMilestone && session.milestoneText ? (
          <div className="flex items-center gap-1.5 px-3 py-1.5 bg-amber-100 text-amber-800 rounded-full text-sm font-medium">
            <Star className="w-4 h-4 fill-amber-500 text-amber-500" />
            <span>Milestone</span>
          </div>
        ) : undefined
      }
    >
      <div className="flex h-full">
        {/* Left Column: Transcript (50%) */}
        <div className="w-1/2 border-r border-border/50 flex flex-col">
          <div className="px-6 py-4 border-b border-border/30 bg-muted/20">
            <h2
              className="text-lg font-semibold text-foreground"
              style={{ fontFamily: 'Crimson Pro, serif' }}
            >
              Session Transcript
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              {session.duration} minutes • {transcriptLines.length} exchanges
            </p>
          </div>
          <div className="flex-1 overflow-y-auto px-6 py-4">
            <div className="space-y-0 divide-y divide-border/30">
              {transcriptLines.map((line, idx) => (
                <TranscriptLine
                  key={idx}
                  speaker={line.speaker}
                  text={line.text}
                  isTherapist={line.isTherapist}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Analysis (50%) */}
        <div className="w-1/2 flex flex-col">
          <div className="px-6 py-4 border-b border-border/30 bg-muted/20">
            <h2
              className="text-lg font-semibold text-foreground"
              style={{ fontFamily: 'Crimson Pro, serif' }}
            >
              Session Analysis
            </h2>
            <p className="text-sm text-muted-foreground mt-1">
              AI-generated insights and action items
            </p>
          </div>
          <div className="flex-1 overflow-y-auto px-6 py-4 space-y-6">
            {/* Topics */}
            <section>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Discussion Topics
              </h3>
              <div className="flex flex-wrap gap-2">
                {session.topics.map((topic, idx) => (
                  <span
                    key={idx}
                    className="px-3 py-1.5 bg-primary/10 text-primary rounded-full text-sm font-medium"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </section>

            {/* Strategy */}
            <section>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Therapeutic Strategy
              </h3>
              <div className="p-4 bg-muted/30 rounded-xl">
                <p className="text-sm font-medium text-foreground">{session.strategy}</p>
                {session.strategyDescription && (
                  <p className="text-sm text-muted-foreground mt-2">
                    {session.strategyDescription}
                  </p>
                )}
              </div>
            </section>

            {/* Mood */}
            <section>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Session Mood
              </h3>
              <div className="flex items-center gap-3">
                <div
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center text-2xl',
                    session.mood === 'positive' && 'bg-green-100',
                    session.mood === 'neutral' && 'bg-blue-100',
                    session.mood === 'low' && 'bg-rose-100'
                  )}
                >
                  {getMoodEmojiIcon(session.mood)}
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground capitalize">{session.mood}</p>
                  <p className="text-xs text-muted-foreground">Overall session mood</p>
                </div>
              </div>
            </section>

            {/* Action Items */}
            {session.actions.length > 0 && (
              <section>
                <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                  Action Items
                </h3>
                <ul className="space-y-2">
                  {session.actions.map((action) => (
                    <li
                      key={action.id}
                      className="flex items-start gap-3 p-3 bg-muted/30 rounded-lg"
                    >
                      <div className="w-5 h-5 rounded border-2 border-primary/30 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-foreground">{action.text}</span>
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Session Summary */}
            <section>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-3">
                Session Summary
              </h3>
              <div className="p-4 bg-gradient-to-br from-primary/5 to-primary/10 rounded-xl border border-primary/10">
                <p className="text-sm text-foreground leading-relaxed">{session.summary}</p>
              </div>
            </section>
          </div>
        </div>
      </div>
    </FullscreenWrapper>
  );
}

// ============================================================================
// Main SessionCardsGrid Component
// ============================================================================

export interface SessionCardsGridProps {
  /** Optional custom className */
  className?: string;
}

export function SessionCardsGrid({ className }: SessionCardsGridProps) {
  const [currentPage, setCurrentPage] = React.useState(1);
  const [selectedSession, setSelectedSession] = React.useState<Session | null>(null);

  // Sort sessions by date (newest first) and paginate
  const sortedSessions = React.useMemo(() => {
    return [...sessionsData].sort(
      (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
    );
  }, []);

  const currentPageSessions = React.useMemo(() => {
    const startIndex = (currentPage - 1) * CARDS_PER_PAGE;
    return sortedSessions.slice(startIndex, startIndex + CARDS_PER_PAGE);
  }, [sortedSessions, currentPage]);

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= TOTAL_PAGES) {
      setCurrentPage(page);
    }
  };

  const handleCardClick = (session: Session) => {
    setSelectedSession(session);
  };

  const handleCloseDetail = () => {
    setSelectedSession(null);
  };

  // Determine if we need to center cards (for last page with fewer items)
  const isLastPage = currentPage === TOTAL_PAGES;
  const cardsOnPage = currentPageSessions.length;
  const shouldCenter = isLastPage && cardsOnPage < CARDS_PER_PAGE && cardsOnPage <= 4;

  return (
    <>
      <div className={cn('flex flex-col h-full', className)}>
        {/* Grid Container */}
        <motion.div
          variants={staggerContainerVariants}
          initial="hidden"
          animate="visible"
          key={currentPage} // Re-animate on page change
          className={cn(
            'grid gap-4 flex-1',
            // 4 columns x 2 rows layout
            'grid-cols-4 grid-rows-2',
            // Center items if fewer than a full row on last page
            shouldCenter && 'justify-items-center'
          )}
          style={{
            // Ensure cards fill available space
            gridAutoRows: 'minmax(0, 1fr)',
          }}
        >
          <AnimatePresence mode="wait">
            {currentPageSessions.map((session, index) => (
              <motion.div
                key={session.id}
                variants={staggerItemVariants}
                className={cn(
                  'w-full min-w-0',
                  // On last page with few cards, limit width for centering
                  shouldCenter && 'max-w-[calc(25%-12px)]'
                )}
                style={{
                  // For centering on partial pages
                  ...(shouldCenter && cardsOnPage === 2 && index === 0
                    ? { gridColumn: '2 / 3' }
                    : {}),
                }}
              >
                <SessionCard session={session} onClick={() => handleCardClick(session)} />
              </motion.div>
            ))}
          </AnimatePresence>
        </motion.div>

        {/* Pagination */}
        {TOTAL_PAGES > 1 && (
          <PaginationDots
            currentPage={currentPage}
            totalPages={TOTAL_PAGES}
            onPageChange={handlePageChange}
          />
        )}
      </div>

      {/* Fullscreen Session Detail */}
      <AnimatePresence>
        {selectedSession && (
          <SessionDetailView session={selectedSession} onClose={handleCloseDetail} />
        )}
      </AnimatePresence>
    </>
  );
}

export default SessionCardsGrid;
