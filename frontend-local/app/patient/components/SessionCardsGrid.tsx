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
import { useSessionData } from '../contexts/SessionDataContext';
import { SessionCard } from './SessionCard';
import { SessionDetail } from './SessionDetail';
import { Session } from '../lib/types';
import { CardSkeleton } from './DashboardSkeleton';

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

  const cardsPerPage = 6;
  const totalPages = Math.ceil(sessions.length / cardsPerPage);
  const currentSessions = sessions.slice(
    currentPage * cardsPerPage,
    (currentPage + 1) * cardsPerPage
  );

  // ALL HOOKS MUST BE BEFORE ANY CONDITIONAL RETURNS (Rules of Hooks)

  // Calculate card scale based on available width
  useEffect(() => {
    const calculateScale = () => {
      if (!containerRef.current) return;

      const containerWidth = containerRef.current.offsetWidth;
      const cardWidth = 329.3;
      const gap = 21;
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
          setCurrentPage(Math.floor(sessionIndex / cardsPerPage));
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

  // Show empty state
  if (isEmpty) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center p-8">
        <div className="text-gray-400 dark:text-gray-500 text-lg font-medium mb-2">
          No sessions yet
        </div>
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          Your therapy sessions will appear here after they are processed.
        </p>
      </div>
    );
  }

  return (
    <>
      {/* Container uses full height with flex layout - overflow-anchor:none prevents scroll jumping */}
      <div ref={swipeRef} className="h-full flex flex-col" style={{ overflowAnchor: 'none' }}>
        {/* Grid area - fixed 3x2 grid with invisible placeholders for empty cells */}
        <div ref={containerRef} className="flex-1 min-h-0">
          <motion.div
            key={currentPage}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.3 }}
            style={{ gap: '21px' }}
            className="grid grid-cols-3 grid-rows-2 h-full"
          >
            {/* Always render 6 cells - real cards + invisible placeholders */}
            {Array.from({ length: cardsPerPage }).map((_, idx) => {
              const session = currentSessions[idx];
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

        {/* Pagination - Always at bottom, never shifts */}
        {totalPages > 1 && (
          <nav aria-label="Session pages" className="flex justify-center items-center gap-3 h-12 flex-shrink-0">
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
