/**
 * Animation constants and utilities for consistent, performance-focused animations
 * Uses framer-motion for smooth transitions and effects
 */

// Page transition variants
export const pageTransitionVariants = {
  initial: {
    opacity: 0,
    y: 8,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: 'easeOut' as const,
    },
  },
  exit: {
    opacity: 0,
    y: -8,
    transition: {
      duration: 0.2,
      ease: 'easeIn' as const,
    },
  },
};

// Card hover and tap variants
export const cardVariants = {
  initial: {
    scale: 1,
  },
  hover: {
    scale: 1.02,
    transition: {
      duration: 0.2,
      ease: 'easeOut' as const,
    },
  },
  tap: {
    scale: 0.98,
  },
};

// Subtle shadow elevation on hover
export const shadowElevationVariants = {
  initial: {
    boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
  },
  hover: {
    boxShadow: '0 4px 12px rgba(0,0,0,0.12)',
    transition: {
      duration: 0.2,
      ease: 'easeOut' as const,
    },
  },
};

// Container stagger effect for animating lists
export const containerVariants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
};

// Item animation for staggered lists
export const itemVariants = {
  initial: {
    opacity: 0,
    y: 10,
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: 'easeOut' as const,
    },
  },
};

// Modal entrance/exit animations
export const modalOverlayVariants = {
  initial: {
    opacity: 0,
  },
  animate: {
    opacity: 1,
    transition: {
      duration: 0.2,
      ease: 'easeOut' as const,
    },
  },
  exit: {
    opacity: 0,
    transition: {
      duration: 0.15,
      ease: 'easeIn' as const,
    },
  },
};

export const modalContentVariants = {
  initial: {
    opacity: 0,
    scale: 0.95,
    y: 16,
  },
  animate: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      duration: 0.3,
      ease: 'easeOut' as const,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: 16,
    transition: {
      duration: 0.2,
      ease: 'easeIn' as const,
    },
  },
};

// Loading state animations
export const spinnerVariants = {
  animate: {
    rotate: 360,
    transition: {
      duration: 1,
      repeat: Infinity,
      ease: 'linear' as const,
    },
  },
};

export const pulseVariants = {
  animate: {
    opacity: [1, 0.6, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut' as const,
    },
  },
};

// Skeleton loading animation
export const skeletonVariants = {
  animate: {
    backgroundPosition: ['200% 0', '-200% 0'],
    transition: {
      duration: 1.5,
      repeat: Infinity,
      ease: 'linear' as const,
    },
  },
};

// Button interaction animations
export const buttonVariants = {
  initial: {
    scale: 1,
  },
  hover: {
    scale: 1.05,
    transition: {
      duration: 0.15,
      ease: 'easeOut' as const,
    },
  },
  tap: {
    scale: 0.95,
  },
};

// Combined card with shadow elevation
export const interactiveCardVariants = {
  initial: {
    scale: 1,
    boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
  },
  hover: {
    scale: 1.02,
    boxShadow: '0 8px 16px rgba(0,0,0,0.12)',
    transition: {
      duration: 0.2,
      ease: 'easeOut' as const,
    },
  },
  tap: {
    scale: 0.98,
  },
};

// Transition config for consistent timing
export const transitionConfig = {
  fast: { duration: 0.15, ease: 'easeOut' as const },
  normal: { duration: 0.3, ease: 'easeOut' as const },
  slow: { duration: 0.5, ease: 'easeOut' as const },
};

// ============================================================================
// Dashboard-v2 Expansion State Animations
// ============================================================================

/**
 * Custom spring easing curve for modal/fullscreen animations.
 * cubic-bezier(0.34, 1.56, 0.64, 1) - slight overshoot for bouncy feel
 */
export const SPRING_EASING = [0.34, 1.56, 0.64, 1] as const;

/**
 * Spring transition config for opening animations (400ms)
 */
export const springOpenTransition = {
  type: 'spring' as const,
  stiffness: 300,
  damping: 22,
  mass: 0.8,
  duration: 0.4,
};

/**
 * Spring transition config for closing animations (300ms)
 */
export const springCloseTransition = {
  type: 'spring' as const,
  stiffness: 400,
  damping: 30,
  mass: 0.6,
  duration: 0.3,
};

/**
 * Ease-out transition for subtle animations (200ms)
 */
export const easeOutTransition = {
  duration: 0.2,
  ease: 'easeOut' as const,
};

/**
 * Spring pop animation for modal dialogs.
 * Opens with bounce effect (400ms), closes smoothly (300ms).
 */
export const modalVariants = {
  hidden: {
    opacity: 0,
    scale: 0.85,
    y: 20,
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: springOpenTransition,
  },
  exit: {
    opacity: 0,
    scale: 0.92,
    y: 10,
    transition: {
      duration: 0.3,
      ease: [0.32, 0, 0.67, 0] as const,
    },
  },
};

/**
 * Backdrop fade animation for modal overlays.
 */
export const backdropVariants = {
  hidden: {
    opacity: 0,
  },
  visible: {
    opacity: 1,
    transition: { duration: 0.25 },
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.2 },
  },
};

/**
 * Fullscreen expansion animation.
 * Scales from widget position to full viewport.
 */
export const fullscreenVariants = {
  hidden: {
    opacity: 0,
    scale: 0.9,
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: springOpenTransition,
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: {
      duration: 0.25,
      ease: [0.32, 0, 0.67, 0] as const,
    },
  },
};

/**
 * Popover fade + scale animation.
 * Quick fade in with subtle scale (200ms ease-out).
 */
export const popoverVariants = {
  hidden: {
    opacity: 0,
    scale: 0.95,
    y: -4,
  },
  visible: {
    opacity: 1,
    scale: 1,
    y: 0,
    transition: easeOutTransition,
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    y: -4,
    transition: { duration: 0.15, ease: 'easeIn' as const },
  },
};

/**
 * Slide in from right animation (for side panels, drawers).
 */
export const slideFromRightVariants = {
  hidden: {
    opacity: 0,
    x: 40,
  },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      type: 'spring' as const,
      stiffness: 350,
      damping: 30,
    },
  },
  exit: {
    opacity: 0,
    x: 40,
    transition: { duration: 0.2, ease: 'easeIn' as const },
  },
};

/**
 * Slide in from bottom animation (for bottom sheets, mobile modals).
 */
export const slideFromBottomVariants = {
  hidden: {
    opacity: 0,
    y: 40,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: springOpenTransition,
  },
  exit: {
    opacity: 0,
    y: 40,
    transition: { duration: 0.25, ease: 'easeIn' as const },
  },
};

/**
 * Simple fade in/out animation.
 */
export const fadeVariants = {
  hidden: {
    opacity: 0,
  },
  visible: {
    opacity: 1,
    transition: { duration: 0.2 },
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.15 },
  },
};

/**
 * Staggered children animation for lists.
 */
export const staggerContainerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1,
    },
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.2 },
  },
};

/**
 * Individual item animation for staggered lists.
 */
export const staggerItemVariants = {
  hidden: {
    opacity: 0,
    y: 10,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.2, ease: 'easeOut' as const },
  },
  exit: {
    opacity: 0,
    y: -10,
    transition: { duration: 0.15 },
  },
};

/**
 * Subtle hover effect for interactive cards.
 */
export const cardHoverVariants = {
  initial: {
    scale: 1,
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
  },
  hover: {
    scale: 1.01,
    boxShadow: '0 4px 20px rgba(0,0,0,0.12)',
    transition: { duration: 0.2, ease: 'easeOut' as const },
  },
  tap: {
    scale: 0.99,
    transition: { duration: 0.1 },
  },
};

/**
 * Collapsible content animation (height 0 to auto).
 */
export const collapseVariants = {
  collapsed: {
    height: 0,
    opacity: 0,
    transition: {
      height: { duration: 0.2 },
      opacity: { duration: 0.15 },
    },
  },
  expanded: {
    height: 'auto',
    opacity: 1,
    transition: {
      height: { duration: 0.25, ease: 'easeOut' as const },
      opacity: { duration: 0.2, delay: 0.05 },
    },
  },
};

// ============================================================================
// Type Exports
// ============================================================================

export type AnimationVariantKey = 'hidden' | 'visible' | 'exit';
export type CollapseVariantKey = 'collapsed' | 'expanded';
export type CardVariantKey = 'initial' | 'hover' | 'tap';
