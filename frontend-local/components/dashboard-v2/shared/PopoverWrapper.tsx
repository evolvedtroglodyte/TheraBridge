'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { popoverVariants } from '@/lib/animations';

// ============================================================================
// Types
// ============================================================================

export type PopoverPlacement =
  | 'top'
  | 'top-start'
  | 'top-end'
  | 'bottom'
  | 'bottom-start'
  | 'bottom-end'
  | 'left'
  | 'left-start'
  | 'left-end'
  | 'right'
  | 'right-start'
  | 'right-end';

export interface PopoverWrapperProps {
  /** Whether the popover is open */
  isOpen: boolean;
  /** Callback when the popover should close */
  onClose: () => void;
  /** Popover content */
  children: React.ReactNode;
  /** The element to anchor the popover to */
  anchorEl: HTMLElement | null;
  /** Placement relative to anchor element (default: 'bottom') */
  placement?: PopoverPlacement;
  /** Offset from anchor in pixels (default: 8) */
  offset?: number;
  /** Optional custom className */
  className?: string;
  /** Whether clicking outside should close (default: true) */
  closeOnClickOutside?: boolean;
  /** Whether pressing ESC should close (default: true) */
  closeOnEscape?: boolean;
  /** Optional width (default: 300px) */
  width?: number | string;
  /** Whether to show the arrow pointer (default: true) */
  showArrow?: boolean;
  /** Optional aria-label for accessibility */
  ariaLabel?: string;
}

// ============================================================================
// Position Calculator
// ============================================================================

interface PopoverPosition {
  top: number;
  left: number;
  arrowPosition: {
    top?: number | string;
    left?: number | string;
    bottom?: number | string;
    right?: number | string;
    transform?: string;
  };
  arrowRotation: number;
}

function calculatePosition(
  anchorRect: DOMRect,
  popoverRect: DOMRect,
  placement: PopoverPlacement,
  offset: number
): PopoverPosition {
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;

  let top = 0;
  let left = 0;
  let arrowPosition: PopoverPosition['arrowPosition'] = {};
  let arrowRotation = 0;

  const arrowSize = 8;

  // Calculate base position
  switch (placement) {
    case 'top':
    case 'top-start':
    case 'top-end':
      top = anchorRect.top - popoverRect.height - offset - arrowSize;
      arrowPosition = { bottom: -arrowSize, left: '50%', transform: 'translateX(-50%)' };
      arrowRotation = 180;
      break;
    case 'bottom':
    case 'bottom-start':
    case 'bottom-end':
      top = anchorRect.bottom + offset + arrowSize;
      arrowPosition = { top: -arrowSize, left: '50%', transform: 'translateX(-50%)' };
      arrowRotation = 0;
      break;
    case 'left':
    case 'left-start':
    case 'left-end':
      left = anchorRect.left - popoverRect.width - offset - arrowSize;
      arrowPosition = { right: -arrowSize, top: '50%', transform: 'translateY(-50%)' };
      arrowRotation = 90;
      break;
    case 'right':
    case 'right-start':
    case 'right-end':
      left = anchorRect.right + offset + arrowSize;
      arrowPosition = { left: -arrowSize, top: '50%', transform: 'translateY(-50%)' };
      arrowRotation = -90;
      break;
  }

  // Calculate horizontal alignment
  if (placement.startsWith('top') || placement.startsWith('bottom')) {
    if (placement.endsWith('-start')) {
      left = anchorRect.left;
      arrowPosition.left = Math.min(24, popoverRect.width / 4);
      arrowPosition.transform = undefined;
    } else if (placement.endsWith('-end')) {
      left = anchorRect.right - popoverRect.width;
      arrowPosition.left = undefined;
      arrowPosition.right = Math.min(24, popoverRect.width / 4);
      arrowPosition.transform = undefined;
    } else {
      left = anchorRect.left + (anchorRect.width - popoverRect.width) / 2;
    }
  }

  // Calculate vertical alignment
  if (placement.startsWith('left') || placement.startsWith('right')) {
    if (placement.endsWith('-start')) {
      top = anchorRect.top;
      arrowPosition.top = Math.min(16, popoverRect.height / 4);
      arrowPosition.transform = undefined;
    } else if (placement.endsWith('-end')) {
      top = anchorRect.bottom - popoverRect.height;
      arrowPosition.top = undefined;
      arrowPosition.bottom = Math.min(16, popoverRect.height / 4);
      arrowPosition.transform = undefined;
    } else {
      top = anchorRect.top + (anchorRect.height - popoverRect.height) / 2;
    }
  }

  // Clamp to viewport bounds
  const padding = 8;
  left = Math.max(padding, Math.min(left, viewportWidth - popoverRect.width - padding));
  top = Math.max(padding, Math.min(top, viewportHeight - popoverRect.height - padding));

  return { top, left, arrowPosition, arrowRotation };
}

// ============================================================================
// PopoverWrapper Component
// ============================================================================

export function PopoverWrapper({
  isOpen,
  onClose,
  children,
  anchorEl,
  placement = 'bottom',
  offset = 8,
  className,
  closeOnClickOutside = true,
  closeOnEscape = true,
  width = 300,
  showArrow = true,
  ariaLabel,
}: PopoverWrapperProps) {
  const popoverRef = React.useRef<HTMLDivElement>(null);
  const [position, setPosition] = React.useState<PopoverPosition | null>(null);
  const popoverId = React.useId();

  // Calculate position when popover opens or anchor changes
  React.useEffect(() => {
    if (!isOpen || !anchorEl || !popoverRef.current) {
      setPosition(null);
      return;
    }

    const updatePosition = () => {
      const anchorRect = anchorEl.getBoundingClientRect();
      const popoverRect = popoverRef.current!.getBoundingClientRect();
      const newPosition = calculatePosition(anchorRect, popoverRect, placement, offset);
      setPosition(newPosition);
    };

    // Initial position calculation
    // Use requestAnimationFrame to ensure popover has rendered
    requestAnimationFrame(updatePosition);

    // Update position on scroll or resize
    window.addEventListener('scroll', updatePosition, true);
    window.addEventListener('resize', updatePosition);

    return () => {
      window.removeEventListener('scroll', updatePosition, true);
      window.removeEventListener('resize', updatePosition);
    };
  }, [isOpen, anchorEl, placement, offset]);

  // Handle ESC key
  React.useEffect(() => {
    if (!closeOnEscape || !isOpen) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, closeOnEscape]);

  // Handle click outside
  React.useEffect(() => {
    if (!closeOnClickOutside || !isOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;

      // Don't close if clicking on the anchor element
      if (anchorEl?.contains(target)) return;

      // Don't close if clicking inside the popover
      if (popoverRef.current?.contains(target)) return;

      onClose();
    };

    // Use setTimeout to avoid closing immediately on the click that opened it
    const timeoutId = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 0);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen, onClose, closeOnClickOutside, anchorEl]);

  // Focus management
  React.useEffect(() => {
    if (!isOpen || !popoverRef.current) return;

    const focusableElements = popoverRef.current.querySelectorAll<HTMLElement>(
      'button:not([disabled]), a[href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
    );

    if (focusableElements.length > 0) {
      focusableElements[0].focus();
    }
  }, [isOpen]);

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <motion.div
          ref={popoverRef}
          id={popoverId}
          variants={popoverVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          role="dialog"
          aria-modal="false"
          aria-label={ariaLabel}
          className={cn(
            // Positioning
            'fixed z-[1500]',
            // Sizing
            'min-w-[200px] max-w-[90vw]',
            // Styling
            'bg-white dark:bg-card',
            'rounded-xl',
            'border border-border/30',
            // Shadow
            'shadow-[0_10px_40px_-10px_rgba(0,0,0,0.2)]',
            // Layout
            'overflow-hidden',
            className
          )}
          style={{
            width: typeof width === 'number' ? `${width}px` : width,
            top: position?.top ?? -9999,
            left: position?.left ?? -9999,
            visibility: position ? 'visible' : 'hidden',
          }}
        >
          {/* Arrow pointer */}
          {showArrow && position && (
            <div
              className="absolute w-0 h-0"
              style={{
                ...position.arrowPosition,
                borderLeft: '8px solid transparent',
                borderRight: '8px solid transparent',
                borderBottom: '8px solid hsl(var(--background))',
                transform: `${position.arrowPosition.transform ?? ''} rotate(${position.arrowRotation}deg)`.trim(),
                filter: 'drop-shadow(0 -1px 1px rgba(0,0,0,0.05))',
              }}
              aria-hidden="true"
            />
          )}

          {/* Content */}
          <div className="p-4">
            {children}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default PopoverWrapper;
