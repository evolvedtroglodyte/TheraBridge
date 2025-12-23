'use client';

/**
 * HorizontalTimeline - Horizontal timeline component for Sessions page
 *
 * DISPLAYS:
 * - Sessions (from audio transcripts) with mood-colored dots
 * - Major Events (from chatbot) with purple diamond icons
 * - Milestones highlighted with amber stars
 *
 * BEHAVIOR:
 * - Events flow left-to-right chronologically
 * - Horizontal scrolling for many events
 * - Session click → open fullscreen session detail
 * - Major Event click → open MajorEventModal
 * - Search and export functionality
 */

import { useState, useRef, useMemo, useCallback } from 'react';
import { Star, Diamond, Search, X } from 'lucide-react';
import { useSessionData } from '../contexts/SessionDataContext';
import { TimelineEvent, SessionTimelineEvent, MajorEventEntry } from '../lib/types';
import { getMoodColor } from '../lib/utils';
import { MajorEventModal } from './MajorEventModal';
import { ExportDropdown } from './ExportDropdown';
import { filterTimelineByQuery } from '../lib/timelineSearch';

interface HorizontalTimelineProps {
  /** Callback when session entry is clicked - opens fullscreen session detail */
  onViewSession?: (sessionId: string) => void;
}

export function HorizontalTimeline({ onViewSession }: HorizontalTimelineProps) {
  const [selectedMajorEvent, setSelectedMajorEvent] = useState<MajorEventEntry | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
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

  /**
   * Handle timeline entry click based on event type
   */
  const handleEntryClick = (event: TimelineEvent) => {
    if (event.eventType === 'session') {
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
    if (onViewSession) {
      onViewSession(sessionId);
    }
  };

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
  const renderTimelineIcon = (event: TimelineEvent) => {
    if (event.eventType === 'major_event') {
      // Purple diamond for major events
      return (
        <Diamond
          className="w-5 h-5 text-purple-500 fill-purple-400 group-hover:scale-110 transition-transform duration-150"
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
          className="w-5 h-5 text-amber-500 fill-amber-400 group-hover:scale-110 transition-transform duration-150"
          style={{
            filter: 'drop-shadow(0 0 4px rgba(251,191,36,0.4))'
          }}
        />
      );
    }

    // Mood-colored dot
    return (
      <div
        className="w-3 h-3 rounded-full group-hover:scale-125 transition-transform duration-150"
        style={{
          backgroundColor: moodColor,
          boxShadow: `0 0 6px ${moodColor}80`
        }}
      />
    );
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="bg-white dark:bg-[#2a2435] rounded-xl border border-gray-200/50 dark:border-[#3d3548] p-6 h-48 animate-pulse">
        <div className="h-5 w-32 bg-gray-200 dark:bg-gray-700 rounded mb-4" />
        <div className="flex gap-6 overflow-x-hidden">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex flex-col items-center gap-2 flex-shrink-0">
              <div className="w-3 h-3 bg-gray-200 dark:bg-gray-700 rounded-full" />
              <div className="h-3 w-16 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Show empty state
  if (isEmpty) {
    return (
      <div className="bg-white dark:bg-[#2a2435] rounded-xl border border-gray-200/50 dark:border-[#3d3548] p-6 h-48 flex items-center justify-center">
        <p className="text-gray-400 dark:text-gray-500 text-sm text-center">
          Your journey timeline will appear here
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white dark:bg-[#2a2435] rounded-xl border border-gray-200/50 dark:border-[#3d3548] transition-colors duration-300 overflow-hidden flex flex-col h-48">
        {/* Header with title, stats, search, and export */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-[#3d3548]">
          {/* Left: Title + Stats */}
          <div className="flex items-center gap-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Timeline
            </h3>
            <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
              <span>{sessionCount} sessions</span>
              <span>•</span>
              <span>{majorEventCount} major events</span>
            </div>
          </div>

          {/* Right: Search + Export */}
          <div className="flex items-center gap-2">
            {/* Search Bar */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search timeline..."
                value={searchQuery}
                onChange={(e) => handleSearchChange(e.target.value)}
                className="pl-9 pr-8 py-1.5 w-64 text-sm rounded-lg border border-gray-200 dark:border-[#3d3548] bg-white dark:bg-[#1a1625] text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[#5AB9B4] dark:focus:ring-[#a78bfa]"
              />
              {searchQuery && (
                <button
                  onClick={clearSearch}
                  className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 rounded hover:bg-gray-100 dark:hover:bg-[#3d3548]"
                  aria-label="Clear search"
                >
                  <X className="w-3.5 h-3.5 text-gray-400" />
                </button>
              )}
            </div>

            {/* Export Dropdown */}
            <ExportDropdown events={filteredTimeline} />
          </div>
        </div>

        {/* Horizontal scrollable timeline */}
        <div className="flex-1 overflow-x-auto overflow-y-hidden px-6 py-4">
          {filteredTimeline.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-400 dark:text-gray-500 text-sm">
                No results found for "{debouncedQuery}"
              </p>
            </div>
          ) : (
            <div className="flex items-start gap-6 h-full">
              {filteredTimeline.map((event, index) => (
                <button
                  key={event.eventType === 'session' ? event.sessionId : event.id}
                  onClick={() => handleEntryClick(event)}
                  className="flex flex-col items-center gap-2 flex-shrink-0 group cursor-pointer"
                >
                  {/* Icon */}
                  <div className="flex items-center justify-center">
                    {renderTimelineIcon(event)}
                  </div>

                  {/* Date */}
                  <div className="text-xs font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
                    {new Date(event.date).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </div>

                  {/* Title/Topic (truncated) */}
                  <div className="text-xs text-gray-500 dark:text-gray-400 max-w-[100px] truncate">
                    {event.eventType === 'session'
                      ? (event as SessionTimelineEvent).topic
                      : event.title}
                  </div>

                  {/* Connecting line (except for last item) */}
                  {index < filteredTimeline.length - 1 && (
                    <div className="absolute left-full w-6 h-[2px] bg-gray-200 dark:bg-[#3d3548] top-[10px]" />
                  )}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

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
