'use client';

/**
 * ⚠️ DEPRECATED - DO NOT USE
 *
 * This component has been deprecated as of 2025-01-06.
 * Timeline navigation has been replaced by session list view.
 *
 * This file is kept for reference only and will be removed in a future cleanup.
 * See SessionCard.tsx for current session navigation patterns.
 */

/**
 * Timeline sidebar component - Mixed Events Version
 *
 * DISPLAYS:
 * - Sessions (from audio transcripts) with mood-colored dots
 * - Major Events (from chatbot) with purple diamond icons
 * - Milestones highlighted with amber stars
 *
 * BEHAVIOR:
 * - Session click → scroll to session card + open fullscreen session detail
 * - Major Event click → open MajorEventModal
 * - Expand button opens modal with enhanced timeline view
 */

import { useState, useRef, useMemo, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Star, Maximize2, X, Clock, Diamond, Search } from 'lucide-react';
import { useSessionData } from '../contexts/SessionDataContext';
import { TimelineEvent, SessionTimelineEvent, MajorEventEntry } from '../lib/types';
import { getMoodColor, modalVariants, backdropVariants } from '../lib/utils';
import { useModalAccessibility } from '../hooks/useModalAccessibility';
import { MajorEventModal } from './MajorEventModal';
import { ExportDropdown } from './ExportDropdown';
import { filterTimelineByQuery } from '../lib/timelineSearch';

interface TimelineSidebarProps {
  /** Callback when session entry is clicked - opens fullscreen session detail */
  onViewSession?: (sessionId: string) => void;
  /** Callback when session entry is clicked - scrolls to session card */
  onScrollToSession?: (sessionId: string) => void;
}

export function TimelineSidebar({ onViewSession, onScrollToSession }: TimelineSidebarProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedMajorEvent, setSelectedMajorEvent] = useState<MajorEventEntry | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const modalRef = useRef<HTMLDivElement>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Use unified timeline data from context
  const {
    unifiedTimeline,
    isLoading,
    isEmpty,
    sessionCount,
    majorEventCount,
    updateMajorEventReflection,
  } = useSessionData();

  // Debounced search handler
  const handleSearchChange = useCallback((value: string) => {
    setSearchQuery(value);

    // Clear existing timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Set new debounce timer (300ms)
    debounceTimerRef.current = setTimeout(() => {
      setDebouncedQuery(value);
    }, 300);
  }, []);

  // Filter timeline based on debounced search query
  const filteredTimeline = useMemo(() => {
    return filterTimelineByQuery(unifiedTimeline, debouncedQuery);
  }, [unifiedTimeline, debouncedQuery]);

  // Clear search
  const clearSearch = useCallback(() => {
    setSearchQuery('');
    setDebouncedQuery('');
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    searchInputRef.current?.focus();
  }, []);

  // Reset search when modal closes
  const handleCloseModal = useCallback(() => {
    setIsExpanded(false);
    setSearchQuery('');
    setDebouncedQuery('');
  }, []);

  // Accessibility: focus trap, Escape key, scroll lock
  useModalAccessibility({
    isOpen: isExpanded,
    onClose: handleCloseModal,
    modalRef,
  });

  /**
   * Handle timeline entry click based on event type
   */
  const handleEntryClick = (event: TimelineEvent) => {
    if (event.eventType === 'session') {
      // Scroll to the session card
      if (onScrollToSession) {
        onScrollToSession(event.sessionId);
      }
      // Open fullscreen session detail
      if (onViewSession) {
        onViewSession(event.sessionId);
      }
    } else {
      // Open major event modal
      setSelectedMajorEvent(event);
    }
  };

  /**
   * Handle viewing related session from major event modal
   */
  const handleViewRelatedSession = (sessionId: string) => {
    if (onScrollToSession) {
      onScrollToSession(sessionId);
    }
    if (onViewSession) {
      onViewSession(sessionId);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="bg-[#F8F7F4] dark:bg-[#2a2435] rounded-xl border border-[#E0DDD8] dark:border-[#3d3548] p-4 h-full animate-pulse">
        <div className="h-5 w-20 bg-gray-200 dark:bg-gray-700 rounded mb-6 mx-auto" />
        <div className="space-y-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="flex items-start gap-3">
              <div className="w-3 h-3 bg-gray-200 dark:bg-gray-700 rounded-full" />
              <div className="flex-1 space-y-1">
                <div className="h-4 w-16 bg-gray-200 dark:bg-gray-700 rounded" />
                <div className="h-3 w-24 bg-gray-200 dark:bg-gray-700 rounded" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Show empty state
  if (isEmpty) {
    return (
      <div className="bg-[#F8F7F4] dark:bg-[#2a2435] rounded-xl border border-[#E0DDD8] dark:border-[#3d3548] p-4 h-full flex items-center justify-center">
        <p className="text-gray-400 dark:text-gray-500 text-sm text-center">
          Your journey timeline will appear here
        </p>
      </div>
    );
  }

  // Format duration for display (e.g., "50m" -> "50 min")
  const formatDuration = (duration: string): string => {
    const match = duration.match(/(\d+)m?/);
    if (match) {
      return `${match[1]} min`;
    }
    return duration;
  };

  /**
   * Render timeline icon based on event type
   */
  const renderTimelineIcon = (event: TimelineEvent, size: 'sm' | 'lg' = 'sm') => {
    const iconSize = size === 'sm' ? 'w-[14px] h-[14px]' : 'w-[18px] h-[18px]';
    const dotSize = size === 'sm' ? 'w-[10px] h-[10px]' : 'w-3 h-3';

    if (event.eventType === 'major_event') {
      // Purple diamond for major events
      return (
        <Diamond
          className={`${iconSize} text-purple-500 fill-purple-400 relative z-10
            group-hover:scale-110 transition-transform duration-150`}
          style={{
            filter: 'drop-shadow(0 0 4px rgba(168,85,247,0.4))'
          }}
        />
      );
    }

    // Session event
    const sessionEvent = event as SessionTimelineEvent;
    const isMilestone = !!sessionEvent.milestone;
    const moodColor = getMoodColor(sessionEvent.mood);

    if (isMilestone) {
      return (
        <Star
          className={`${iconSize} text-amber-500 fill-amber-400 relative z-10
            group-hover:scale-110 transition-transform duration-150`}
          style={{
            filter: 'drop-shadow(0 0 6px rgba(251,191,36,0.5))'
          }}
        />
      );
    }

    return (
      <div
        className={`${dotSize} rounded-full relative z-10
          ring-2 ring-white dark:ring-[#2a2435]
          group-hover:scale-125 transition-transform duration-150`}
        style={{ backgroundColor: moodColor }}
      />
    );
  };

  /**
   * Render compact entry content for sidebar
   */
  const renderCompactEntry = (event: TimelineEvent) => {
    if (event.eventType === 'major_event') {
      return (
        <>
          <p className="text-[13px] font-medium text-gray-800 dark:text-gray-200
            group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
            {event.date}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
            {event.title}
          </p>
          <p className="text-[11px] italic text-purple-600 dark:text-purple-400 mt-0.5">
            Major Event
          </p>
        </>
      );
    }

    // Session event
    const sessionEvent = event as SessionTimelineEvent;
    const isMilestone = !!sessionEvent.milestone;

    return (
      <>
        <p className="text-[13px] font-medium text-gray-800 dark:text-gray-200
          group-hover:text-[#5AB9B4] dark:group-hover:text-[#a78bfa] transition-colors">
          {sessionEvent.date}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
          {sessionEvent.topic}
        </p>
        {isMilestone && sessionEvent.milestone && (
          <p className="text-[11px] italic text-amber-600 dark:text-amber-400 mt-0.5">
            {sessionEvent.milestone.title.includes(':')
              ? sessionEvent.milestone.title.split(':')[0]
              : sessionEvent.milestone.title}
          </p>
        )}
      </>
    );
  };

  /**
   * Render enhanced entry content for expanded modal
   */
  const renderExpandedEntry = (event: TimelineEvent) => {
    if (event.eventType === 'major_event') {
      return (
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-semibold text-gray-800 dark:text-gray-200
              group-hover:text-purple-600 dark:group-hover:text-purple-400 transition-colors">
              {event.date}
            </p>
            <span className="text-xs px-1.5 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded">
              Event
            </span>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">
            {event.title}
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 line-clamp-2">
            {event.summary}
          </p>
        </div>
      );
    }

    // Session event
    const sessionEvent = event as SessionTimelineEvent;
    const isMilestone = !!sessionEvent.milestone;
    const moodColor = getMoodColor(sessionEvent.mood);

    return (
      <>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-semibold text-gray-800 dark:text-gray-200
              group-hover:text-[#5AB9B4] dark:group-hover:text-[#a78bfa] transition-colors">
              {sessionEvent.date}
            </p>
            <span className="text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {formatDuration(sessionEvent.duration)}
            </span>
          </div>

          <p className="text-sm text-gray-600 dark:text-gray-300 mb-1">
            {sessionEvent.topic}
          </p>

          <p className="text-xs text-gray-400 dark:text-gray-500">
            {sessionEvent.strategy}
          </p>

          {isMilestone && sessionEvent.milestone && (
            <div className="mt-2 px-2 py-1 bg-amber-50 dark:bg-amber-900/20 rounded-md inline-block">
              <p className="text-xs font-medium text-amber-700 dark:text-amber-400">
                {sessionEvent.milestone.title}
              </p>
            </div>
          )}
        </div>

        {/* Mood indicator */}
        <div
          className="w-2 h-2 rounded-full flex-shrink-0 mt-2"
          style={{ backgroundColor: moodColor }}
          title={`Mood: ${sessionEvent.mood}`}
        />
      </>
    );
  };

  return (
    <>
      {/* Compact Sidebar */}
      <div
        ref={containerRef}
        className="bg-[#F8F7F4] dark:bg-[#2a2435] rounded-xl border border-[#E0DDD8] dark:border-[#3d3548] p-4 h-full overflow-y-auto relative transition-colors duration-300"
      >
        {/* Header: Title centered, expand button on right */}
        <div className="flex items-center justify-between mb-6">
          {/* Spacer for centering */}
          <div className="w-8" />

          {/* Centered Title */}
          <h3 className="text-base font-semibold text-gray-800 dark:text-gray-200">Timeline</h3>

          {/* Expand Button */}
          <button
            onClick={() => setIsExpanded(true)}
            className="w-8 h-8 flex items-center justify-center rounded-lg
              hover:bg-gray-100 dark:hover:bg-[#3d3548]
              transition-colors duration-150"
            aria-label="Expand timeline"
          >
            <Maximize2 className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          </button>
        </div>

        {/* Timeline Entries Container */}
        <div className="relative">
          {/* Gradient Connector Line */}
          <div
            className="absolute left-[7px] top-4 bottom-4 w-[2px] z-0"
            style={{
              background: 'linear-gradient(180deg, #5AB9B4 0%, #B8A5D6 50%, #F4A69D 100%)'
            }}
          />

          {/* Entries */}
          <div className="space-y-0.5">
            {unifiedTimeline.map((event) => (
              <button
                key={event.id}
                onClick={() => handleEntryClick(event)}
                data-event-id={event.id}
                data-event-type={event.eventType}
                className="flex items-start gap-3 w-full text-left rounded-lg py-2 pr-2
                  hover:bg-gray-50 dark:hover:bg-[#3d3548]/50
                  active:bg-gray-100 dark:active:bg-[#3d3548]
                  transition-colors duration-150 group cursor-pointer"
              >
                {/* Timeline Icon Container */}
                <div className="relative flex-shrink-0 w-4 h-4 flex items-center justify-center">
                  {renderTimelineIcon(event, 'sm')}
                </div>

                {/* Entry Content */}
                <div className="flex-1 min-w-0 pt-0.5">
                  {renderCompactEntry(event)}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Expanded Modal */}
      <AnimatePresence>
        {isExpanded && (
          <>
            {/* Backdrop */}
            <motion.div
              variants={backdropVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={handleCloseModal}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-[1000]"
            />

            {/* Modal */}
            <motion.div
              ref={modalRef}
              variants={modalVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="fixed w-[550px] max-h-[85vh] bg-[#F8F7F4] dark:bg-[#2a2435] rounded-3xl shadow-2xl z-[1001] overflow-hidden border-2 border-[#E0DDD8] dark:border-gray-600 flex flex-col"
              style={{
                top: '50%',
                left: '50%',
              }}
              onClick={(e) => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-labelledby="timeline-modal-title"
            >
              {/* Modal Header - Fixed */}
              <div className="p-8 pb-4 border-b border-gray-200 dark:border-[#3d3548]">
                {/* Header Row: Title + Export + Close */}
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h2
                      id="timeline-modal-title"
                      className="text-2xl font-light text-gray-800 dark:text-gray-200"
                    >
                      Your Journey
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {sessionCount} sessions • {majorEventCount} major events
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Export Dropdown */}
                    <ExportDropdown events={unifiedTimeline} />

                    {/* Close button */}
                    <button
                      onClick={handleCloseModal}
                      className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
                      aria-label="Close timeline"
                    >
                      <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                    </button>
                  </div>
                </div>

                {/* Search Bar */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
                  <input
                    ref={searchInputRef}
                    type="text"
                    value={searchQuery}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    placeholder="Search sessions and events..."
                    className="w-full pl-10 pr-10 py-2.5 bg-gray-50 dark:bg-[#1a1625] border border-gray-200 dark:border-[#3d3548] rounded-xl text-sm text-gray-700 dark:text-gray-300 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-[#5AB9B4]/50 dark:focus:ring-[#a78bfa]/50 transition-shadow"
                  />
                  {searchQuery && (
                    <button
                      onClick={clearSearch}
                      className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 flex items-center justify-center rounded-full bg-gray-200 dark:bg-gray-600 hover:bg-gray-300 dark:hover:bg-gray-500 transition-colors"
                      aria-label="Clear search"
                    >
                      <X className="w-3 h-3 text-gray-500 dark:text-gray-300" />
                    </button>
                  )}
                </div>
              </div>

              {/* Scrollable Timeline Content */}
              <div className="flex-1 overflow-y-auto p-8 pt-4">
                {/* Search Results Summary */}
                {debouncedQuery && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
                    {filteredTimeline.length} result{filteredTimeline.length !== 1 ? 's' : ''} for &ldquo;{debouncedQuery}&rdquo;
                  </p>
                )}

                {/* Empty State */}
                {filteredTimeline.length === 0 && debouncedQuery && (
                  <div className="text-center py-12">
                    <Search className="w-10 h-10 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                    <p className="text-gray-500 dark:text-gray-400 text-sm">
                      No results found for &ldquo;{debouncedQuery}&rdquo;
                    </p>
                    <button
                      onClick={clearSearch}
                      className="mt-2 text-sm text-[#5AB9B4] dark:text-[#a78bfa] hover:underline"
                    >
                      Clear search
                    </button>
                  </div>
                )}

                {/* Enhanced Timeline View */}
                {filteredTimeline.length > 0 && (
                  <div className="relative">
                    {/* Gradient Connector Line */}
                    <div
                      className="absolute left-[9px] top-4 bottom-4 w-[2px] z-0"
                      style={{
                        background: 'linear-gradient(180deg, #5AB9B4 0%, #B8A5D6 50%, #F4A69D 100%)'
                      }}
                    />

                    {/* Timeline Entries - Enhanced for Modal */}
                    <div className="space-y-1">
                      {filteredTimeline.map((event) => (
                        <button
                          key={event.id}
                          onClick={() => {
                            handleCloseModal();
                            // Small delay to let modal close, then handle click
                            setTimeout(() => handleEntryClick(event), 150);
                          }}
                          className="flex items-start gap-3 w-full text-left rounded-xl py-3 pr-3
                            hover:bg-gray-50 dark:hover:bg-[#3d3548]/50
                            active:bg-gray-100 dark:active:bg-[#3d3548]
                            transition-colors duration-150 group cursor-pointer"
                        >
                          {/* Icon Container - 20px width, icon centered */}
                          <div className="relative flex-shrink-0 w-5 h-5 flex items-center justify-center">
                            {renderTimelineIcon(event, 'lg')}
                          </div>

                          {/* Content - Enhanced with more details */}
                          {renderExpandedEntry(event)}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Major Event Modal */}
      <MajorEventModal
        event={selectedMajorEvent}
        isOpen={!!selectedMajorEvent}
        onClose={() => setSelectedMajorEvent(null)}
        onViewRelatedSession={handleViewRelatedSession}
        onSaveReflection={updateMajorEventReflection}
      />
    </>
  );
}
