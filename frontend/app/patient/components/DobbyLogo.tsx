'use client';

/**
 * Dobby AI Logo - Minimal Geometric Design
 * - Light mode: Teal (#5AB9B4) - soft, calming
 * - Dark mode: Purple (#8B6AAE) - matches dark theme
 * - Animated ears wiggle + eyes blink on hover
 * - Scalable SVG via viewBox
 * - FIXED: Color transitions smoothly when theme changes
 */

import { useTheme } from '../contexts/ThemeContext';

interface DobbyLogoProps {
  size?: number;
}

export function DobbyLogo({ size = 48 }: DobbyLogoProps) {
  const { isDark } = useTheme();

  // Color based on theme - derived from isDark state
  const mainColor = isDark ? '#8B6AAE' : '#5AB9B4';
  const pupilColor = isDark ? '#1a1625' : '#1a1a1a';

  return (
    <div
      className="group flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg
        key={isDark ? 'dark' : 'light'}
        width={size}
        height={size}
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="transition-all duration-300"
      >
        {/* Left Ear - Triangle */}
        <polygon
          className="ear-left origin-[35px_50px] group-hover:animate-[earWiggle_0.4s_ease-in-out]"
          points="15,55 35,35 35,65"
          fill={mainColor}
        />
        {/* Right Ear - Triangle */}
        <polygon
          className="ear-right origin-[85px_50px] group-hover:animate-[earWiggle_0.4s_ease-in-out_0.05s]"
          points="105,55 85,35 85,65"
          fill={mainColor}
        />
        {/* Head - Rounded Square */}
        <rect
          x="30"
          y="30"
          width="60"
          height="60"
          rx="14"
          fill={mainColor}
        />
        {/* Left Eye - White circle */}
        <circle
          className="eye origin-center group-hover:animate-[blink_1.5s_ease-in-out]"
          cx="45"
          cy="55"
          r="8"
          fill="white"
        />
        {/* Left Pupil */}
        <circle cx="45" cy="57" r="4" fill={pupilColor} />
        {/* Left Eye Highlight */}
        <circle cx="47" cy="54" r="1.5" fill="white" />

        {/* Right Eye - White circle */}
        <circle
          className="eye origin-center group-hover:animate-[blink_1.5s_ease-in-out]"
          cx="75"
          cy="55"
          r="8"
          fill="white"
        />
        {/* Right Pupil */}
        <circle cx="75" cy="57" r="4" fill={pupilColor} />
        {/* Right Eye Highlight */}
        <circle cx="77" cy="54" r="1.5" fill="white" />

        {/* Smile - Simple arc */}
        <path
          d="M48 74 Q60 82 72 74"
          stroke="white"
          strokeWidth="3"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
    </div>
  );
}
