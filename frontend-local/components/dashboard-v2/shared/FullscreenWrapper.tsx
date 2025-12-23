'use client';

import * as React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import { fullscreenVariants } from '@/lib/animations';

// ============================================================================
// Types
// ============================================================================

export interface FullscreenWrapperProps {
  /** Whether the fullscreen view is open */
  isOpen: boolean;
  /** Callback when the fullscreen view should close */
  onClose: () => void;
  /** Fullscreen content */
  children: React.ReactNode;
  /** Title displayed in the top bar */
  title: string;
  /** Optional icon to display next to the title */
  titleIcon?: React.ReactNode;
  /** Optional subtitle or breadcrumb text */
  subtitle?: string;
  /** Optional custom className for the container */
  className?: string;
  /** Whether to show the back arrow (default: true) */
  showBackArrow?: boolean;
  /** Whether to show the close button (default: true) */
  showCloseButton?: boolean;
  /** Whether pressing ESC should close (default: true) */
  closeOnEscape?: boolean;
  /** Optional callback when animation completes */
  onAnimationComplete?: () => void;
  /** Optional actions to render in the top bar (right side) */
  headerActions?: React.ReactNode;
  /** Optional footer content */
  footer?: React.ReactNode;
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

    // Focus the first focusable element (back button or close button)
    if (firstFocusable) {
      firstFocusable.focus();
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key !== 'Tab') return;

      if (event.shiftKey) {
        if (document.activeElement === firstFocusable) {
          event.preventDefault();
          lastFocusable?.focus();
        }
      } else {
        if (document.activeElement === lastFocusable) {
          event.preventDefault();
          firstFocusable?.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
      if (previouslyFocused && typeof previouslyFocused.focus === 'function') {
        previouslyFocused.focus();
      }
    };
  }, [isOpen, containerRef]);
}

// ============================================================================
// FullscreenWrapper Component
// ============================================================================

export function FullscreenWrapper({
  isOpen,
  onClose,
  children,
  title,
  titleIcon,
  subtitle,
  className,
  showBackArrow = true,
  showCloseButton = true,
  closeOnEscape = true,
  onAnimationComplete,
  headerActions,
  footer,
}: FullscreenWrapperProps) {
  const containerRef = React.useRef<HTMLDivElement>(null);
  const fullscreenId = React.useId();
  const titleId = `${fullscreenId}-title`;

  // Focus trap
  useFocusTrap(isOpen, containerRef);

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

  // Prevent body scroll when fullscreen is open
  React.useEffect(() => {
    if (isOpen) {
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = originalOverflow;
      };
    }
  }, [isOpen]);

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <motion.div
          ref={containerRef}
          variants={fullscreenVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
          onAnimationComplete={onAnimationComplete}
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          className={cn(
            // Full viewport coverage
            'fixed inset-0 w-screen h-screen',
            // High z-index for fullscreen
            'z-[2000]',
            // Background
            'bg-white dark:bg-background',
            // Layout
            'flex flex-col',
            // No border radius for fullscreen
            'rounded-none',
            // Focus outline
            'outline-none',
            className
          )}
          tabIndex={-1}
        >
          {/* Top Bar */}
          <header
            className={cn(
              'flex items-center justify-between',
              'px-6 py-4',
              'border-b border-border/50',
              'bg-white dark:bg-background',
              // Sticky header
              'sticky top-0 z-10'
            )}
          >
            {/* Left side: Back arrow + Title */}
            <div className="flex items-center gap-4">
              {showBackArrow && (
                <button
                  type="button"
                  onClick={onClose}
                  className={cn(
                    'p-2 rounded-full',
                    'text-muted-foreground hover:text-foreground',
                    'hover:bg-muted/80 transition-colors',
                    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring'
                  )}
                  aria-label="Go back"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
              )}

              <div className="flex items-center gap-3">
                {titleIcon && (
                  <div className="p-2 bg-primary/10 rounded-xl">
                    {titleIcon}
                  </div>
                )}
                <div>
                  <h1
                    id={titleId}
                    className="text-xl font-semibold text-foreground"
                    style={{ fontFamily: 'Crimson Pro, serif' }}
                  >
                    {title}
                  </h1>
                  {subtitle && (
                    <p className="text-sm text-muted-foreground mt-0.5">
                      {subtitle}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Right side: Actions + Close button */}
            <div className="flex items-center gap-3">
              {headerActions}
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
                  aria-label="Close fullscreen view"
                >
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
          </header>

          {/* Main Content Area */}
          <main className="flex-1 overflow-y-auto">
            {children}
          </main>

          {/* Optional Footer */}
          {footer && (
            <footer
              className={cn(
                'px-6 py-4',
                'border-t border-border/50',
                'bg-white dark:bg-background'
              )}
            >
              {footer}
            </footer>
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default FullscreenWrapper;
