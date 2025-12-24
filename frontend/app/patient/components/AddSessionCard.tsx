'use client';

/**
 * AddSessionCard - Special card for adding new therapy sessions
 * - Matches SessionCard dimensions (329.3px × 290.5px)
 * - Centered plus icon with "Add New Session" label
 * - Navigates to upload page on click
 * - Theme-aware colors (teal/purple accent)
 */

import { motion } from 'framer-motion';
import { useRouter } from 'next/navigation';
import { useTheme } from '../contexts/ThemeContext';

interface AddSessionCardProps {
  /** DOM id for accessibility */
  id?: string;
  /** Scale factor for responsive sizing (default 1.0) */
  scale?: number;
}

// Font families - matching SessionCard
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

// Card dimensions - exact match to SessionCard
const cardWidth = 329.3;
const cardHeight = 290.5;

export function AddSessionCard({ id, scale = 1.0 }: AddSessionCardProps) {
  const { isDark } = useTheme();
  const router = useRouter();

  // Color system matching SessionCard
  const colors = {
    teal: '#4ECDC4',
    purple: '#7882E7',
    cardDark: '#1e2025',
    cardLight: '#FFFFFF',
    borderDark: '#2c2e33',
    borderLight: '#E8E8E8',
  };

  const cardBg = isDark ? colors.cardDark : colors.cardLight;
  const cardBorder = isDark ? colors.borderDark : colors.borderLight;
  const text = isDark ? '#e3e4e6' : '#1a1a1a';
  const accent = isDark ? colors.purple : colors.teal;

  const handleClick = () => {
    router.push('/upload');
  };

  return (
    <motion.div
      id={id}
      onClick={handleClick}
      style={{
        width: `${cardWidth}px`,
        height: `${cardHeight}px`,
        backgroundColor: cardBg,
        border: `1px solid ${cardBorder}`,
        borderRadius: '16px',
        padding: '16px 20px 20px 20px',
        position: 'relative',
        overflow: 'hidden',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        cursor: 'pointer',
        transform: `scale(${scale})`,
        transformOrigin: 'center center',
      }}
      whileHover={{ scale: scale * 1.01, boxShadow: '0 4px 16px rgba(0,0,0,0.12)' }}
      transition={{ duration: 0.2 }}
      role="button"
      tabIndex={0}
      aria-label="Add new therapy session"
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleClick();
        }
      }}
    >
      {/* Plus Icon */}
      <svg
        width="64"
        height="64"
        viewBox="0 0 64 64"
        fill="none"
        style={{ marginBottom: '16px' }}
      >
        <circle
          cx="32"
          cy="32"
          r="30"
          stroke={accent}
          strokeWidth="2"
          fill="none"
        />
        <path
          d="M32 18 L32 46 M18 32 L46 32"
          stroke={accent}
          strokeWidth="3"
          strokeLinecap="round"
        />
      </svg>

      {/* Label */}
      <span
        style={{
          fontFamily: fontSans,
          color: text,
          fontSize: '16px',
          fontWeight: 500,
          textAlign: 'center',
        }}
      >
        Add New Session
      </span>
    </motion.div>
  );
}
