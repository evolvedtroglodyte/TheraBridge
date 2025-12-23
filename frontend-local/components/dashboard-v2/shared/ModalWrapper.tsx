'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { modalVariants, backdropVariants } from '@/lib/animations';

// ============================================================================
// Types
// ============================================================================

export interface ModalWrapperProps {
  /** Whether the modal is open */
  isOpen: boolean;
  /** Callback when the modal should close */
  onClose: () => void;
  /** Modal content */
  children: React.ReactNode;
  /** Optional title displayed in the header */
  title?: string;
  /** Optional icon to display next to the title */
  titleIcon?: React.ReactNode;
  /** Optional custom className for the modal container */
  className?: string;
  /** Whether to show the close button (default: true) */
  showCloseButton?: boolean;
  /** Whether clicking outside should close the modal (default: true) */
  closeOnBackdropClick?: boolean;
  /** Whether pressing ESC should close the modal (default: true) */
  closeOnEscape?: boolean;
  /** Optional callback when modal open animation completes */
  onAnimationComplete?: () => void;
  /** Optional aria-describedby for accessibility */
  ariaDescribedBy?: string;
}

// ============================================================================
// Focus Trap Hook
// ============================================================================

function useFocusTrap(isOpen: boolean, containerRef: React.RefObject<HTMLDivElement | null>) {
  React.useEffect(() => {
    if (!isOpen || !containerRef.current) return;

    const container = containerRef.current;
    const focusableSelectors = [
      'button:not([disabled])',
      'a[href]',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    const focusableElements = container.querySelectorAll<HTMLElement>(focusableSelectors);
    const firstFocusable = focusableElements[0];
    const lastFocusable = focusableElements[focusableElements.length - 1];

    // Store the previously focused element
    const previouslyFocused = document.activeElement as HTMLElement;

    // Focus the first focusable element
    if (firstFocusable) {
      firstFocusable.focus();
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) {
        // Shift + Tab
        if (document.activeElement === firstFocusable) {
          event.preventDefault();
          lastFocusable?.focus();
        }
      } else {
        // Tab
        if (document.activeElement === lastFocusable) {
          event.preventDefault();
          firstFocusable?.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
      // Restore focus when modal closes
      if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
        previouslyFocused.focus();
      }
    };
  }, [isOpen, containerRef]);
}

// ============================================================================
// ModalWrapper Component
// ============================================================================

export function ModalWrapper({
  isOpen,
  onClose,
  children,
  title,
  titleIcon,
  className,
  showCloseButton = true,
  closeOnBackdropClick = true,
  closeOnEscape = true,
  onAnimationComplete,
  ariaDescribedBy,
}: ModalWrapperProps) {
  const modalRef = React.useRef<HTMLDivElement>(null);
  const modalId = React.useId();
  const titleId = `${modalId}-title`;

  // Focus trap
  useFocusTrap(isOpen, modalRef);

  // Handle ESC key
  React.useEffect(() => {
    if (!closeOnEscape) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isOpen) {
        event.preventDefault();
        onClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, closeOnEscape]);

  // Prevent body scroll when modal is open
  React.useEffect(() => {
    if (isOpen) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [isOpen]);

  // Handle backdrop click
  const handleBackdropClick = (event: React.MouseEvent) => {
    if (closeOnBackdropClick && event.target === event.currentTarget) {
      onClose();
    }
  };

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-[1000] flex items-center justify-center p-4"
          variants={backdropVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          onClick={handleBackdropClick}
          style={{ backgroundColor: 'rgba(0, 0, 0, 0.3)' }}
          role="presentation"
          aria-hidden="true"
        >
          <motion.div
            ref={modalRef}
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onAnimationComplete={onAnimationComplete}
            role="dialog"
            aria-modal="true"
            aria-labelledby={title ? titleId : undefined}
            aria-describedby={ariaDescribedBy}
            className={cn(
              // Base styles
              'relative bg-white dark:bg-card',
              // Size constraints
              'w-full max-w-[80vw] max-h-[80vh]',
              // Border radius and padding
              'rounded-[24px] p-8',
              // Shadow
              'shadow-[0_25px_50px_-12px_rgba(0,0,0,0.25)]',
              // Layout
              'flex flex-col overflow-hidden',
              // Focus outline
              'outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
              className
            )}
            onClick={(e) => e.stopPropagation()}
            tabIndex={-1}
          >
            {/* Header with optional title and close button */}
            {(title || showCloseButton) && (
              <div className="flex items-center justify-between mb-6">
                {title && (
                  <div className="flex items-center gap-3">
                    {titleIcon && (
                      <div className="p-2 bg-primary/10 rounded-xl">
                        {titleIcon}
                      </div>
                    )}
                    <h2
                      id={titleId}
                      className="text-xl font-semibold text-foreground"
                      style={{ fontFamily: 'Crimson Pro, serif' }}
                    >
                      {title}
                    </h2>
                  </div>
                )}
                {!title && <div />}
                {showCloseButton && (
                  <button
                    type="button"
                    onClick={onClose}
                    className={cn(
                      'p-2 rounded-full',
                      'text-muted-foreground hover:text-foreground',
                      'hover:bg-muted/80 transition-colors',
                      'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
                    )}
                    aria-label="Close modal"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            )}

            {/* Scrollable content area */}
            <div className="flex-1 overflow-y-auto">
              {children}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default ModalWrapper;
