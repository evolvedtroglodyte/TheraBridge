'use client';

/**
 * CompactScrollbar - Tiny custom scrollbar for horizontal scroll containers
 *
 * Features:
 * - 60px track width with 20px thumb (Tiny variant)
 * - Click-to-jump and drag-to-scroll
 * - Syncs with container scroll position
 * - Theme-aware colors (purple dark, teal light)
 * - Smooth animations and hover effects
 */

import { useEffect, useRef, useState } from 'react';

interface CompactScrollbarProps {
  /** Ref to the scrollable container */
  containerRef: React.RefObject<HTMLDivElement | null>;
  /** Dark mode flag */
  isDark: boolean;
  /** Additional CSS classes */
  className?: string;
}

export function CompactScrollbar({ containerRef, isDark, className = '' }: CompactScrollbarProps) {
  const trackRef = useRef<HTMLDivElement>(null);
  const thumbRef = useRef<HTMLDivElement>(null);
  const [thumbPosition, setThumbPosition] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  // Update thumb position based on container scroll
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const updateThumbPosition = () => {
      const { scrollLeft, scrollWidth, clientWidth } = container;
      const maxScroll = scrollWidth - clientWidth;

      // Check if scrollbar should be visible
      if (maxScroll <= 0) {
        setIsVisible(false);
        return;
      }

      setIsVisible(true);

      // Calculate thumb position (60px track - 20px thumb = 40px max movement)
      const scrollRatio = scrollLeft / maxScroll;
      const maxThumbMove = 60 - 20; // trackWidth - thumbWidth
      setThumbPosition(scrollRatio * maxThumbMove);
    };

    updateThumbPosition();
    container.addEventListener('scroll', updateThumbPosition);

    // Also update on resize
    const resizeObserver = new ResizeObserver(updateThumbPosition);
    resizeObserver.observe(container);

    return () => {
      container.removeEventListener('scroll', updateThumbPosition);
      resizeObserver.disconnect();
    };
  }, [containerRef]);

  // Handle thumb drag with RAF optimization
  useEffect(() => {
    const thumb = thumbRef.current;
    const track = trackRef.current;
    const container = containerRef.current;

    if (!thumb || !track || !container) return;

    let isDragging = false;
    let animationFrameId: number | null = null;

    const handleMouseDown = (e: MouseEvent) => {
      isDragging = true;
      thumb.style.cursor = 'grabbing';
      e.preventDefault();
    };

    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging) return;

      // Cancel previous frame if still pending
      if (animationFrameId !== null) {
        cancelAnimationFrame(animationFrameId);
      }

      // Use RAF to batch updates at 60fps
      animationFrameId = requestAnimationFrame(() => {
        const trackRect = track.getBoundingClientRect();
        const mouseX = e.clientX - trackRect.left;
        const maxThumbMove = 60 - 20; // trackWidth - thumbWidth

        // Calculate new thumb position (centered on mouse)
        const newThumbLeft = Math.max(0, Math.min(maxThumbMove, mouseX - 10));

        // Direct DOM update (bypass React state during drag)
        thumb.style.left = `${newThumbLeft}px`;

        // Update container scroll
        const scrollRatio = newThumbLeft / maxThumbMove;
        const { scrollWidth, clientWidth } = container;
        const maxScroll = scrollWidth - clientWidth;
        container.scrollLeft = scrollRatio * maxScroll;
      });
    };

    const handleMouseUp = () => {
      isDragging = false;
      thumb.style.cursor = 'grab';

      // Cancel any pending animation frame
      if (animationFrameId !== null) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
      }
    };

    // Track click to jump
    const handleTrackClick = (e: MouseEvent) => {
      if (e.target === track) {
        const rect = track.getBoundingClientRect();
        const clickX = e.clientX - rect.left - 10; // Center thumb (20px / 2)
        const maxThumbMove = 60 - 20;
        const newThumbLeft = Math.max(0, Math.min(maxThumbMove, clickX));

        const scrollRatio = newThumbLeft / maxThumbMove;
        const { scrollWidth, clientWidth } = container;
        const maxScroll = scrollWidth - clientWidth;
        container.scrollLeft = scrollRatio * maxScroll;
      }
    };

    thumb.addEventListener('mousedown', handleMouseDown);
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    track.addEventListener('click', handleTrackClick);

    return () => {
      thumb.removeEventListener('mousedown', handleMouseDown);
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      track.removeEventListener('click', handleTrackClick);

      // Cleanup pending frame
      if (animationFrameId !== null) {
        cancelAnimationFrame(animationFrameId);
      }
    };
  }, [containerRef]);

  if (!isVisible) return null;

  return (
    <div className={`flex justify-center ${className}`}>
      {/* Track - 60px wide, 3px tall */}
      <div
        ref={trackRef}
        className={`relative w-[60px] h-[3px] rounded cursor-pointer ${
          isDark ? 'bg-[#2a2535]' : 'bg-[#D8D8D8]'
        }`}
      >
        {/* Thumb - 20px wide, 3px tall */}
        <div
          ref={thumbRef}
          className={`absolute top-0 w-[20px] h-[3px] rounded cursor-grab transition-opacity duration-200 ${
            isDark
              ? 'bg-[#9B7AC4] hover:bg-[#B794D4]'
              : 'bg-[#5AB9B4] hover:bg-[#4AA9A4]'
          }`}
          style={{
            left: `${thumbPosition}px`,
            boxShadow: isDark
              ? '0 0 6px rgba(155, 122, 196, 0.4)'
              : '0 0 6px rgba(90, 185, 180, 0.3)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.boxShadow = isDark
              ? '0 0 10px rgba(155, 122, 196, 0.6)'
              : '0 0 10px rgba(90, 185, 180, 0.5)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.boxShadow = isDark
              ? '0 0 6px rgba(155, 122, 196, 0.4)'
              : '0 0 6px rgba(90, 185, 180, 0.3)';
          }}
        />
      </div>
    </div>
  );
}
