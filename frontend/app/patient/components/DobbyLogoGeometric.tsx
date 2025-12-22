'use client';

/**
 * DobbyLogoGeometric - Minimal geometric Dobby logo without face
 * Used for AI message avatars in chat (not the header)
 *
 * - Light mode: Teal (#5AB9B4)
 * - Dark mode: Purple (#8B6AAE)
 * - No eyes, no mouth - just ears and head shape
 */

import { useTheme } from '../contexts/ThemeContext';

interface DobbyLogoGeometricProps {
  size?: number;
}

export function DobbyLogoGeometric({ size = 28 }: DobbyLogoGeometricProps) {
  const { isDark } = useTheme();
  const mainColor = isDark ? '#8B6AAE' : '#5AB9B4';

  return (
    <div
      className="flex items-center justify-center"
      style={{ width: size, height: size }}
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 120 120"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="transition-all duration-300"
      >
        {/* Left Ear - Triangle */}
        <polygon
          points="15,55 35,35 35,65"
          fill={mainColor}
        />
        {/* Right Ear - Triangle */}
        <polygon
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
      </svg>
    </div>
  );
}
