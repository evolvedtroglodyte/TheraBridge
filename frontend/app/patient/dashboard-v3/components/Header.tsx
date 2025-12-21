'use client';

/**
 * Dashboard sticky header component
 * - Navigation links (Dashboard, Ask AI, Upload)
 * - Custom Home icon + theme toggle (Sun/Moon) with glow effects
 * - Minimal height design (~60px)
 * - FIXED: Full dark mode support for entire header
 * - Ask AI button triggers fullscreen chat via callback
 */

import { useTheme } from '../contexts/ThemeContext';

// Custom Home Icon with glow effect (matches fullscreen chat)
function HomeIcon({ isDark }: { isDark: boolean }) {
  const stroke = isDark ? '#9B7AC4' : '#5AB9B4';
  const glow = isDark
    ? 'drop-shadow(0 0 3px rgba(155, 122, 196, 0.4))'
    : 'drop-shadow(0 0 3px rgba(90, 185, 180, 0.4))';

  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke={stroke}
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-[22px] h-[22px]"
      style={{ filter: glow }}
    >
      <path d="M4 10.5V19a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8.5" />
      <path d="M2.5 12L12 3l9.5 9" />
      <rect x="9" y="14" width="6" height="7" rx="1" />
    </svg>
  );
}

// Custom Theme Toggle Icon with glow effect (matches fullscreen chat)
function ThemeIcon({ isDark }: { isDark: boolean }) {
  if (isDark) {
    // Moon icon for dark mode
    return (
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="#93B4DC"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        className="w-[22px] h-[22px]"
        style={{ filter: 'drop-shadow(0 0 4px rgba(147, 180, 220, 0.6)) drop-shadow(0 0 10px rgba(147, 180, 220, 0.3))' }}
      >
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
    );
  }

  // Sun icon for light mode
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="#F5A623"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="w-[22px] h-[22px]"
      style={{ filter: 'drop-shadow(0 0 4px rgba(245, 166, 35, 0.5)) drop-shadow(0 0 8px rgba(245, 166, 35, 0.25))' }}
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
    </svg>
  );
}

interface HeaderProps {
  onAskAIClick?: () => void;
}

export function Header({ onAskAIClick }: HeaderProps) {
  const { isDark, toggleTheme } = useTheme();

  // Scroll to top of dashboard
  const handleHomeClick = () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <header className="sticky top-0 z-50 bg-[#F8F7F4] dark:bg-[#1a1625] border-b border-[#E0DDD8] dark:border-[#3d3548] h-[60px] flex items-center transition-colors duration-300">
      {/* Theme toggle - flush to left edge of screen */}
      <div className="flex items-center gap-2 pl-3">
        <button
          onClick={toggleTheme}
          className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
          <ThemeIcon isDark={isDark} />
        </button>
        <button
          onClick={handleHomeClick}
          className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
          aria-label="Scroll to top"
        >
          <HomeIcon isDark={isDark} />
        </button>
      </div>

      <div className="flex-1 flex items-center justify-center">

        {/* Center section - Navigation */}
        <nav className="flex items-center gap-8">
          <button className="text-sm font-medium text-[#5AB9B4] dark:text-[#a78bfa] border-b-2 border-[#5AB9B4] dark:border-[#a78bfa] pb-1">
            Dashboard
          </button>
          <button
            onClick={onAskAIClick}
            className="text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] transition-colors"
          >
            Ask AI
          </button>
          <button className="text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors">
            Upload
          </button>
        </nav>
      </div>

      {/* Right section - Empty spacer for balance */}
      <div className="w-[84px] pr-3" />
    </header>
  );
}
