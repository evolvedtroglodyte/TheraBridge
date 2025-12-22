'use client';

/**
 * useModalAccessibility - Accessibility hook for modals
 *
 * Provides:
 * 1. Focus trap - keeps keyboard focus inside modal
 * 2. Escape key - closes modal on Escape press
 * 3. Body scroll lock - prevents background scrolling
 * 4. Focus restoration - returns focus to trigger element on close
 */

import { useEffect, useRef, useCallback } from 'react';

// Selector for all focusable elements
const FOCUSABLE_SELECTORS = [
  'button:not([disabled])',
  'a[href]',
  'input:not([disabled])',
  'textarea:not([disabled])',
  'select:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ');

interface UseModalAccessibilityOptions {
  isOpen: boolean;
  onClose: () => void;
  modalRef: React.RefObject<HTMLElement | null>;
}

export function useModalAccessibility({
  isOpen,
  onClose,
  modalRef,
}: UseModalAccessibilityOptions) {
  // Store the element that triggered the modal
  const triggerRef = useRef<Element | null>(null);

  // Handle Escape key press
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }

      // Focus trap: handle Tab key
      if (event.key === 'Tab' && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll(FOCUSABLE_SELECTORS);
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

        // If Shift+Tab on first element, wrap to last
        if (event.shiftKey && document.activeElement === firstElement) {
          event.preventDefault();
          lastElement?.focus();
        }
        // If Tab on last element, wrap to first
        else if (!event.shiftKey && document.activeElement === lastElement) {
          event.preventDefault();
          firstElement?.focus();
        }
      }
    },
    [onClose, modalRef]
  );

  useEffect(() => {
    if (isOpen) {
      // Save trigger element for focus restoration
      triggerRef.current = document.activeElement;

      // Lock body scroll
      const originalOverflow = document.body.style.overflow;
      document.body.style.overflow = 'hidden';

      // Add keyboard listener
      document.addEventListener('keydown', handleKeyDown);

      // Focus first focusable element in modal after animation
      const timer = setTimeout(() => {
        if (modalRef.current) {
          const firstFocusable = modalRef.current.querySelector(FOCUSABLE_SELECTORS) as HTMLElement;
          firstFocusable?.focus();
        }
      }, 100);

      return () => {
        // Restore body scroll
        document.body.style.overflow = originalOverflow;

        // Remove keyboard listener
        document.removeEventListener('keydown', handleKeyDown);

        clearTimeout(timer);

        // Restore focus to trigger element
        if (triggerRef.current instanceof HTMLElement) {
          triggerRef.current.focus();
        }
      };
    }
  }, [isOpen, handleKeyDown, modalRef]);
}
