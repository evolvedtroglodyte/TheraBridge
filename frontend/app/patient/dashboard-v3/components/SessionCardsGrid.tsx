'use client';

/**
 * Session cards grid component
 * - 3x2 grid (6 cards per page)
 * - Pagination with slide animation
 * - Click card to open fullscreen detail
 * - Supports external session selection (from Timeline sidebar)
 * - NOW USES REAL DATA from SessionDataContext
 */

import { useState, useEffect, useLayoutEffect, useCallback, useRef } from 'react';
import { motion } from 'framer-motion';
import { useSessionData } from '@/app/patient/contexts/SessionDataContext';
import { SessionCard } from '@/app/patient/components/SessionCard';
import { AddSessionCard } from '@/app/patient/components/AddSessionCard';
import { SessionDetail } from '@/app/patient/components/SessionDetail';
import { Session } from '@/app/patient/lib/types';
import { CardSkeleton } from '@/app/patient/components/DashboardSkeleton';

interface SessionCardsGridProps {
  /** Session ID to open in fullscreen (controlled externally, e.g., from Timeline) */
  externalSelectedSessionId?: string | null;
  /** Callback when SessionDetail is closed (to sync external state) */
  onSessionClose?: () => void;
}

export function SessionCardsGrid({
  externalSelectedSessionId,
  onSessionClose
}: SessionCardsGridProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);
  const [cardScale, setCardScale] = useState(1.0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Use real data from context instead of mock imports
  const { sessions, isLoading, isError, isEmpty } = useSessionData();

  // Page 1: AddSessionCard + 5 sessions (6 cards total)
  // Page 2+: 6 sessions only (no AddSessionCard)
  const isFirstPage = currentPage === 0;
  const firstPageSessionCount = 5;
  const otherPageSessionCount = 6;

  // Calculate total pages
  // First page takes 5 sessions, remaining pages take 6 each
  const totalPages = sessions.length === 0
    ? 1
    : Math.ceil((sessions.length - firstPageSessionCount) / otherPageSessionCount) + 1;

  // Get current page sessions
  const currentSessions = isFirstPage
    ? sessions.slice(0, firstPageSessionCount)
    : sessions.slice(
        firstPageSessionCount + (currentPage - 1) * otherPageSessionCount,
        firstPageSessionCount + currentPage * otherPageSessionCount
      );

  // ALL HOOKS MUST BE BEFORE ANY CONDITIONAL RETURNS (Rules of Hooks)

  // Calculate card scale based on available width
  useEffect(() => {
    const calculateScale = () => {
      if (!containerRef.current) return;

      const containerWidth = containerRef.current.offsetWidth;
      const cardWidth = 329.3;
      const gap = 20; // Spacing between cards
      const cols = 3;

      // Available width per card: (totalWidth - (gaps between cards)) / cols
      // With 3 cards there are 2 gaps between them
      const availableWidthPerCard = (containerWidth - (gap * (cols - 1))) / cols;
      const scale = availableWidthPerCard / cardWidth;

      // Set scale (capped at 1.5x for reasonable max size)
      setCardScale(Math.min(scale, 1.5));
    };

    calculateScale();
    window.addEventListener('resize', calculateScale);
    return () => window.removeEventListener('resize', calculateScale);
  }, []);

  // Handle external session selection (e.g., from Timeline "View Full Session")
  useEffect(() => {
    if (externalSelectedSessionId && sessions.length > 0) {
      const session = sessions.find(s => s.id === externalSelectedSessionId);
      if (session) {
        setSelectedSession(session);
        // Navigate to the page containing this session
        const sessionIndex = sessions.findIndex(s => s.id === externalSelectedSessionId);
        if (sessionIndex !== -1) {
          // Page 1 has sessions 0-4 (5 sessions)
          // Page 2+ have 6 sessions each
          if (sessionIndex < firstPageSessionCount) {
            setCurrentPage(0);
          } else {
            const remainingIndex = sessionIndex - firstPageSessionCount;
            setCurrentPage(Math.floor(remainingIndex / otherPageSessionCount) + 1);
          }
        }
      }
    }
  }, [externalSelectedSessionId, sessions]);

  // Handle closing the session detail
  const handleClose = useCallback(() => {
    setSelectedSession(null);
    onSessionClose?.();
  }, [onSessionClose]);

  // Trackpad horizontal swipe gesture support
  const swipeRef = useRef<HTMLDivElement>(null);
  const swipeAccumulator = useRef(0);
  const swipeThreshold = 50; // pixels of horizontal scroll to trigger page change

  // Track scroll position to restore after page change
  const savedScrollY = useRef<number | null>(null);

  // Restore scroll position after page change (runs synchronously before paint)
  useLayoutEffect(() => {
    if (savedScrollY.current !== null) {
      window.scrollTo({ top: savedScrollY.current, behavior: 'instant' });
      savedScrollY.current = null;
    }
  }, [currentPage]);

  useEffect(() => {
    const element = swipeRef.current;
    if (!element || totalPages <= 1) return;

    const handleWheel = (e: WheelEvent) => {
      // Only handle horizontal scroll (trackpad two-finger swipe)
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
        e.preventDefault();
        swipeAccumulator.current += e.deltaX;

        if (swipeAccumulator.current > swipeThreshold) {
          // Swipe left = next page - preserve scroll position
          savedScrollY.current = window.scrollY;
          setCurrentPage(prev => Math.min(prev + 1, totalPages - 1));
          swipeAccumulator.current = 0;
        } else if (swipeAccumulator.current < -swipeThreshold) {
          // Swipe right = previous page - preserve scroll position
          savedScrollY.current = window.scrollY;
          setCurrentPage(prev => Math.max(prev - 1, 0));
          swipeAccumulator.current = 0;
        }
      }
    };

    element.addEventListener('wheel', handleWheel, { passive: false });
    return () => element.removeEventListener('wheel', handleWheel);
  }, [totalPages]);

  // Show loading state
  if (isLoading) {
    return (
      <div style={{ gap: '21px' }} className="grid grid-cols-3 auto-rows-fr">
        {Array.from({ length: 6 }).map((_, i) => (
          <CardSkeleton key={i} className="h-[150px]" />
        ))}
      </div>
    );
  }

  // Show error state
  if (isError) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <div className="text-red-500 dark:text-red-400 text-lg font-medium mb-2">
          Failed to load sessions
        </div>
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          Please check your connection and try again.
        </p>
      </div>
    );
  }

  // Show empty state: just the AddSessionCard
  if (isEmpty) {
    return (
      <div className="h-full flex flex-col">
        <div className="flex-1 min-h-0 flex items-center justify-center">
          <div
            ref={containerRef}
            className="inline-grid grid-cols-3 grid-rows-2 gap-[20px]"
          >
            {/* Single AddSessionCard in position 1 */}
            <AddSessionCard
              id="add-session-card"
              scale={cardScale}
            />
            {/* Invisible placeholders for remaining 5 cells */}
            {Array.from({ length: 5 }).map((_, idx) => (
              <div key={`placeholder-${idx}`} className="invisible" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Container uses full height with flex layout - overflow-anchor:none prevents scroll jumping */}
      <div ref={swipeRef} className="h-full flex flex-col" style={{ overflowAnchor: 'none' }}>
        {/* Grid area - fixed 3x2 grid with tighter spacing */}
        <div ref={containerRef} className="flex-1 min-h-0 flex items-center justify-center">
          <motion.div
            key={currentPage}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
            className="inline-grid grid-cols-3 grid-rows-2 gap-[20px]"
          >
            {/* Page 1: AddSessionCard + 5 sessions, Page 2+: 6 sessions only */}
            {Array.from({ length: 6 }).map((_, idx) => {
              // Position 0 on page 1 ONLY: AddSessionCard
              if (idx === 0 && isFirstPage) {
                return (
                  <AddSessionCard
                    key="add-session-card"
                    id="add-session-card"
                    scale={cardScale}
                  />
                );
              }

              // Session cards: offset by 1 on page 1, no offset on page 2+
              const sessionIndex = isFirstPage ? idx - 1 : idx;
              const session = currentSessions[sessionIndex];

              if (session) {
                return (
                  <SessionCard
                    key={session.id}
                    id={`session-${session.id}`}
                    session={session}
                    onClick={() => setSelectedSession(session)}
                    scale={cardScale}
                  />
                );
              }

              // Invisible placeholder to maintain grid structure
              return <div key={`placeholder-${idx}`} className="invisible" />;
            })}
          </motion.div>
        </div>

        {/* Pagination - Centered on viewport */}
        {totalPages > 1 && (
          <nav
            aria-label="Session pages"
            className="flex justify-center items-center gap-3 h-16 flex-shrink-0 relative"
          >
            <div className="flex items-center gap-3">
              {Array.from({ length: totalPages }).map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    // Save scroll position before page change to restore after render
                    savedScrollY.current = window.scrollY;
                    setCurrentPage(idx);
                  }}
                  aria-label={`Go to page ${idx + 1}`}
                  aria-current={idx === currentPage ? 'page' : undefined}
                  className="w-6 h-2 flex items-center justify-center"
                >
                  <span
                    className={`transition-all duration-300 rounded-full h-2 ${
                      idx === currentPage
                        ? 'bg-[#5AB9B4] dark:bg-[#a78bfa] w-6'
                        : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500 w-2'
                    }`}
                  />
                </button>
              ))}
            </div>
          </nav>
        )}
      </div>

      {/* Session Detail Fullscreen */}
      {selectedSession && (
        <SessionDetail
          session={selectedSession}
          onClose={handleClose}
        />
      )}
    </>
  );
}
