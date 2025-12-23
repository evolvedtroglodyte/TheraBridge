'use client';

import { useState, useRef, useCallback } from 'react';
import { Calendar, ChevronRight, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { PopoverWrapper } from '@/components/dashboard-v2/shared';
import { timelineData, getMoodColor } from '@/lib/mock-data/dashboard-v2';
import type { TimelineEntry, SessionMood } from '@/lib/mock-data/dashboard-v2';

/**
 * TimelineSidebar Component
 *
 * A vertical timeline visualization showing therapy sessions chronologically
 * with popover interactions for session details.
 *
 * Features:
 * - Vertical gradient line (teal -> lavender -> coral)
 * - Mood-colored dots (no emojis)
 * - Star icons with glow for milestone sessions
 * - Popover on click with arrow pointer using PopoverWrapper
 * - Sticky positioning
 * - Scrollable
 *
 * Architecture Reference: PAGE_LAYOUT_ARCHITECTURE.md Section 7
 */

// ============================================================================
// Types
// ============================================================================

interface TimelineSession {
  id: string;
  sessionId: string;
  date: string;
  displayDate: string;
  topicPreview: string;
  mood: SessionMood;
  moodColor: string;
  isMilestone: boolean;
  milestoneText?: string;
  // Extended fields for popover
  duration?: string;
  topics?: string[];
  strategy?: string;
  sessionNumber?: number;
}

// ============================================================================
// Utility Functions
// ============================================================================

const getMoodDotColor = (mood: SessionMood): string => {
  switch (mood) {
    case 'positive':
      return 'bg-emerald-400';
    case 'neutral':
      return 'bg-blue-400';
    case 'low':
      return 'bg-rose-400';
    default:
      return 'bg-slate-400';
  }
};

const getMoodLabel = (mood: SessionMood): string => {
  switch (mood) {
    case 'positive':
      return 'Positive';
    case 'neutral':
      return 'Neutral';
    case 'low':
      return 'Low';
    default:
      return 'Unknown';
  }
};

// ============================================================================
// Star Icon Component (for milestones)
// ============================================================================

const StarIcon = ({ className }: { className?: string }) => (
  <svg
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
    aria-hidden="true"
  >
    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
  </svg>
);

// ============================================================================
// Timeline Entry Component
// ============================================================================

interface TimelineEntryProps {
  session: TimelineSession;
  isLast: boolean;
  onSelect: (session: TimelineSession, element: HTMLElement) => void;
  isSelected: boolean;
}

function TimelineEntryItem({ session, isLast, onSelect, isSelected }: TimelineEntryProps) {
  const entryRef = useRef<HTMLDivElement>(null);

  const handleClick = () => {
    if (entryRef.current) {
      onSelect(session, entryRef.current);
    }
  };

  return (
    <div
      ref={entryRef}
      className={cn(
        'relative flex gap-3 cursor-pointer group transition-all duration-200',
        isSelected ? 'opacity-100' : 'opacity-90 hover:opacity-100'
      )}
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
      aria-label={`Session on ${session.displayDate}${session.isMilestone ? `, milestone: ${session.milestoneText}` : ''}`}
      aria-expanded={isSelected}
    >
      {/* Connector line - vertical gradient */}
      {!isLast && (
        <div
          className="absolute left-[7px] top-6 w-0.5 h-[calc(100%+8px)]"
          style={{
            background: 'linear-gradient(to bottom, #5AB9B4, #B8A5D6, #F4A69D)',
          }}
          aria-hidden="true"
        />
      )}

      {/* Timeline dot or star - NO emojis */}
      <div className="relative z-10 flex-shrink-0">
        {session.isMilestone ? (
          // Milestone: 14px Star with glow effect
          <div className="w-[14px] h-[14px] flex items-center justify-center">
            <div
              className="absolute inset-0 rounded-full animate-pulse"
              style={{
                background: 'rgba(251, 191, 36, 0.4)',
                filter: 'blur(4px)',
              }}
              aria-hidden="true"
            />
            <StarIcon className="w-[14px] h-[14px] text-amber-400 drop-shadow-sm relative z-10" />
          </div>
        ) : (
          // Standard: 10px Mood-colored dot
          <div
            className={cn(
              'w-[10px] h-[10px] rounded-full shadow-sm transition-transform duration-200 group-hover:scale-110',
              getMoodDotColor(session.mood)
            )}
            style={{ marginTop: '2px' }}
            aria-hidden="true"
          />
        )}
      </div>

      {/* Entry content */}
      <div className="flex-1 pb-4">
        <div className="flex items-center gap-2 mb-0.5">
          <span
            className={cn(
              'text-[13px] font-medium transition-colors duration-200',
              isSelected ? 'text-teal-700 dark:text-teal-400' : 'text-slate-700 dark:text-slate-300 group-hover:text-teal-600 dark:group-hover:text-teal-400'
            )}
          >
            {session.displayDate}
          </span>
        </div>
        {/* Topic preview (1-2 words) */}
        <p className="text-[12px] text-slate-500 dark:text-slate-400 leading-relaxed truncate max-w-[140px]">
          {session.topicPreview}
        </p>
        {/* Milestone text if applicable */}
        {session.isMilestone && session.milestoneText && (
          <p className="text-[11px] text-amber-700 dark:text-amber-400 italic mt-1 truncate max-w-[140px]">
            {session.milestoneText}
          </p>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// Session Popover Content Component
// ============================================================================

interface SessionPopoverContentProps {
  session: TimelineSession;
  onClose: () => void;
  onViewFull: (sessionId: string) => void;
}

function SessionPopoverContent({ session, onClose, onViewFull }: SessionPopoverContentProps) {
  // Extract session number from sessionId (e.g., "session-10" -> 10)
  const sessionNumber = session.sessionId?.replace('session-', '') || session.id.replace('timeline-session-', '');

  return (
    <div className="min-w-[280px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 pb-3 border-b border-slate-100 dark:border-slate-800">
        <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">
          Session {sessionNumber} - {session.displayDate}
        </h3>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors"
          aria-label="Close popover"
        >
          <X className="w-4 h-4 text-slate-500 dark:text-slate-400" />
        </button>
      </div>

      {/* Body */}
      <div className="space-y-3">
        {/* Duration */}
        {session.duration && (
          <div>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              Duration
            </span>
            <p className="text-sm text-slate-700 dark:text-slate-300 mt-0.5">
              {session.duration}
            </p>
          </div>
        )}

        {/* Mood */}
        <div>
          <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">
            Mood
          </span>
          <div className="flex items-center gap-2 mt-0.5">
            <div
              className={cn('w-2.5 h-2.5 rounded-full', getMoodDotColor(session.mood))}
              aria-hidden="true"
            />
            <p className="text-sm text-slate-700 dark:text-slate-300">
              {getMoodLabel(session.mood)}
            </p>
          </div>
        </div>

        {/* Topics */}
        {session.topics && session.topics.length > 0 && (
          <div>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              Topics
            </span>
            <ul className="mt-0.5 space-y-0.5">
              {session.topics.map((topic, idx) => (
                <li key={idx} className="text-sm text-slate-700 dark:text-slate-300 flex items-start gap-1.5">
                  <span className="text-slate-400 mt-1" aria-hidden="true">&#8226;</span>
                  {topic}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Strategy */}
        {session.strategy && (
          <div>
            <span className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wide">
              Strategy
            </span>
            <p className="text-sm text-teal-700 dark:text-teal-400 font-medium mt-0.5">
              {session.strategy}
            </p>
          </div>
        )}

        {/* Milestone (if exists) */}
        {session.isMilestone && session.milestoneText && (
          <div>
            <span className="text-xs font-medium text-amber-600 dark:text-amber-400 uppercase tracking-wide">
              Milestone
            </span>
            <p className="text-sm text-amber-800 dark:text-amber-300 italic mt-0.5">
              {session.milestoneText}
            </p>
          </div>
        )}
      </div>

      {/* Footer - View Full Session link */}
      <div className="mt-4 pt-3 border-t border-slate-100 dark:border-slate-800">
        <button
          onClick={() => onViewFull(session.sessionId || session.id)}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-teal-50 dark:bg-teal-900/30 hover:bg-teal-100 dark:hover:bg-teal-900/50 text-teal-700 dark:text-teal-400 rounded-lg transition-colors text-sm font-medium"
        >
          View Full Session
          <ChevronRight className="w-4 h-4" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// Main TimelineSidebar Component
// ============================================================================

interface TimelineSidebarProps {
  sessions?: TimelineSession[];
  onSessionClick?: (sessionId: string) => void;
  onViewFullSession?: (sessionId: string) => void;
  className?: string;
}

export default function TimelineSidebar({
  sessions,
  onSessionClick,
  onViewFullSession,
  className = '',
}: TimelineSidebarProps) {
  // Transform timeline data to include extended session info
  const transformedSessions: TimelineSession[] = sessions || timelineData.map((entry, index) => ({
    ...entry,
    // Add mock extended data for popover display
    duration: `${45 + (index % 3) * 5} minutes`,
    topics: [entry.topicPreview, index % 2 === 0 ? 'Coping strategies' : 'Progress review'],
    strategy: index % 3 === 0 ? 'CBT techniques' : index % 3 === 1 ? 'Mindfulness' : 'Behavioral activation',
    sessionNumber: 10 - index,
  }));

  const [selectedSession, setSelectedSession] = useState<TimelineSession | null>(null);
  const [anchorElement, setAnchorElement] = useState<HTMLElement | null>(null);

  const handleSessionSelect = useCallback((session: TimelineSession, element: HTMLElement) => {
    setSelectedSession(session);
    setAnchorElement(element);
    onSessionClick?.(session.sessionId || session.id);
  }, [onSessionClick]);

  const handleClosePopover = useCallback(() => {
    setSelectedSession(null);
    setAnchorElement(null);
  }, []);

  const handleViewFullSession = useCallback((sessionId: string) => {
    onViewFullSession?.(sessionId);
    handleClosePopover();
  }, [onViewFullSession, handleClosePopover]);

  return (
    <>
      {/* Main Timeline Card */}
      <div
        className={cn(
          'sticky top-6 bg-white dark:bg-card border border-slate-200 dark:border-slate-800 shadow-sm',
          'rounded-xl overflow-hidden',
          className
        )}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800">
          <h3 className="text-base font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-600 dark:text-slate-400" aria-hidden="true" />
            Timeline
          </h3>
        </div>

        {/* Scrollable Timeline Entries */}
        <div className="px-4 py-4 max-h-[60vh] overflow-y-auto">
          <div className="space-y-0">
            {transformedSessions.map((session, idx) => (
              <TimelineEntryItem
                key={session.id}
                session={session}
                isLast={idx === transformedSessions.length - 1}
                onSelect={handleSessionSelect}
                isSelected={selectedSession?.id === session.id}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Popover using PopoverWrapper */}
      <PopoverWrapper
        isOpen={!!selectedSession}
        onClose={handleClosePopover}
        anchorEl={anchorElement}
        placement="left"
        offset={12}
        width={320}
        showArrow={true}
        ariaLabel={selectedSession ? `Session details for ${selectedSession.displayDate}` : undefined}
        className="dark:bg-slate-900"
      >
        {selectedSession && (
          <SessionPopoverContent
            session={selectedSession}
            onClose={handleClosePopover}
            onViewFull={handleViewFullSession}
          />
        )}
      </PopoverWrapper>
    </>
  );
}

// Export types for external use
export type { TimelineSession, TimelineSidebarProps };
