'use client';

/**
 * TheraBridge Logo Components - Geometric Bridge Design
 * - BridgeIcon: Geometric bridge with support pillars
 * - TextLogo: THERA (muted) + BRIDGE (accent) uppercase text
 * - CombinedLogo: Full logo with icon + text for branding
 *
 * Design: Mountain-shaped bridge with vertical support pillars
 * Colors: Teal (light mode) / Purple (dark mode) for accent
 */

import { useTheme } from '@/app/patient/contexts/ThemeContext';

interface LogoProps {
  className?: string;
  size?: number;
}

/**
 * Geometric Bridge Icon - Mountain-shaped bridge with support pillars
 */
export function BridgeIcon({ size = 48 }: LogoProps) {
  const { isDark } = useTheme();
  const accent = isDark ? '#7882E7' : '#4ECDC4';
  const supportColor = isDark ? '#ffffff' : '#333333';

  return (
    <svg width={size} height={size} viewBox="0 0 80 80" fill="none">
      {/* Main bridge arc - mountain shape */}
      <path
        d="M10 55 L25 30 L40 40 L55 30 L70 55"
        stroke={accent}
        strokeWidth="4"
        strokeLinejoin="round"
        strokeLinecap="round"
        fill="none"
      />
      {/* Support pillars */}
      <line x1="25" y1="30" x2="25" y2="55" stroke={supportColor} strokeWidth="2.5" opacity="0.5"/>
      <line x1="40" y1="40" x2="40" y2="55" stroke={supportColor} strokeWidth="2.5" opacity="0.5"/>
      <line x1="55" y1="30" x2="55" y2="55" stroke={supportColor} strokeWidth="2.5" opacity="0.5"/>
    </svg>
  );
}

/**
 * Text Logo - THERA (muted) + BRIDGE (accent)
 */
export function TextLogo({ fontSize = 18 }: { fontSize?: number }) {
  const { isDark } = useTheme();
  const theraColor = isDark ? '#B8B5B0' : '#6B6560';
  const accent = isDark ? '#7882E7' : '#4ECDC4';

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '5px',
        fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
        fontSize: `${fontSize}px`,
        letterSpacing: '3px',
        textTransform: 'uppercase',
      }}
    >
      <span style={{ fontWeight: 300, color: theraColor }}>THERA</span>
      <span style={{ fontWeight: 500, color: accent }}>BRIDGE</span>
    </div>
  );
}

/**
 * Combined Logo - Icon + Text for full branding
 */
export function CombinedLogo({
  className = '',
  iconSize = 36,
  textClassName = 'text-base'
}: LogoProps & { textClassName?: string; iconSize?: number }) {
  // Extract font size from textClassName
  const fontSizeMap: Record<string, number> = {
    'text-xs': 12,
    'text-sm': 14,
    'text-base': 16,
    'text-lg': 18,
    'text-xl': 20,
    'text-2xl': 24,
  };

  const fontSize = fontSizeMap[textClassName] || 16;
  const gap = Math.max(8, iconSize / 3);

  return (
    <div
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: `${gap}px`
      }}
    >
      <BridgeIcon size={iconSize} />
      <TextLogo fontSize={fontSize} />
    </div>
  );
}
