/**
 * Utility functions for TherapyBridge Dashboard
 * - Mood color mapping
 * - Animation variants
 * - Date formatting helpers
 */

import { MoodType } from './types';

export const getMoodColor = (mood: MoodType): string => {
  switch (mood) {
    case 'positive':
      return '#68D391'; // Soft green
    case 'neutral':
      return '#63B3ED'; // Soft blue
    case 'low':
      return '#FDA4AF'; // Gentle rose
    default:
      return '#A0AEC0';
  }
};

export const getMoodEmoji = (mood: MoodType): string => {
  switch (mood) {
    case 'positive':
      return '😊';
    case 'neutral':
      return '😐';
    case 'low':
      return '😔';
    default:
      return '😐';
  }
};

export const springTransition = {
  type: 'spring',
  stiffness: 300,
  damping: 30
};

export const modalVariants = {
  hidden: {
    opacity: 0,
    scale: 0.9
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.4,
      ease: [0.34, 1.56, 0.64, 1] // cubic-bezier for spring bounce
    }
  },
  exit: {
    opacity: 0,
    scale: 0.9,
    transition: {
      duration: 0.3,
      ease: 'easeOut'
    }
  }
};

export const fullscreenVariants = {
  hidden: {
    opacity: 0,
    scale: 0.95
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.4,
      ease: [0.34, 1.56, 0.64, 1]
    }
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: {
      duration: 0.3,
      ease: 'easeOut'
    }
  }
};

export const popoverVariants = {
  hidden: {
    opacity: 0,
    scale: 0.95
  },
  visible: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.2,
      ease: 'easeOut'
    }
  },
  exit: {
    opacity: 0,
    scale: 0.95,
    transition: {
      duration: 0.15,
      ease: 'easeIn'
    }
  }
};

export const backdropVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.3 }
  },
  exit: {
    opacity: 0,
    transition: { duration: 0.2 }
  }
};

export const formatDate = (dateString: string): string => {
  return dateString;
};

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
};
