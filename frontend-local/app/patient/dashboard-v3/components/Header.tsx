'use client';

/**
 * Dashboard sticky header component
 * - Navigation links (Dashboard, Sessions, Ask AI, Upload)
 * - Custom Home icon + theme toggle (Sun/Moon) with glow effects
 * - Minimal height design (~60px)
 * - FIXED: Full dark mode support for entire header
 * - Ask AI button triggers fullscreen chat via callback
 * - Triple-click theme toggle navigates to auth page (dev testing)
 */

import { useState, useRef } from 'react';
import { useTheme } from '@/app/patient/contexts/ThemeContext';
import { useRouter, usePathname } from 'next/navigation';
import { CombinedLogo } from '@/components/TheraBridgeLogo';

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
  const router = useRouter();
  const pathname = usePathname();

  // Determine active page
  const isSessionsPage = pathname?.includes('/sessions');
  const isDashboardPage = pathname === '/patient';

  // Triple-click detection for home icon (dev testing feature) - Sessions page only
  const homeClickCountRef = useRef(0);
  const homeClickTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Handle home click with triple-click detection (Sessions page only)
  const handleHomeClick = () => {
    homeClickCountRef.current += 1;

    // Clear existing timer
    if (homeClickTimerRef.current) {
      clearTimeout(homeClickTimerRef.current);
    }

    // Check for triple-click
    if (homeClickCountRef.current >= 3) {
      homeClickCountRef.current = 0;
      // Navigate to auth page on triple-click
      router.push('/auth/login');
      return;
    }

    // Single/double click behavior: navigate to dashboard
    if (homeClickCountRef.current === 1) {
      router.push('/patient');
    }

    // Reset click count after 500ms
    homeClickTimerRef.current = setTimeout(() => {
      homeClickCountRef.current = 0;
    }, 500);
  };

  // Triple-click detection for theme toggle (dev testing feature) - Sessions page only
  const themeClickCountRef = useRef(0);
  const themeClickTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Handle theme toggle with triple-click detection (Sessions page only)
  const handleThemeToggle = () => {
    themeClickCountRef.current += 1;

    // Clear existing timer
    if (themeClickTimerRef.current) {
      clearTimeout(themeClickTimerRef.current);
    }

    // Check for triple-click
    if (themeClickCountRef.current >= 3) {
      themeClickCountRef.current = 0;
      // Navigate to auth page on triple-click
      router.push('/auth/login');
      return;
    }

    // Single/double click behavior: toggle theme
    if (themeClickCountRef.current === 1) {
      toggleTheme();
    }

    // Reset click count after 500ms
    themeClickTimerRef.current = setTimeout(() => {
      themeClickCountRef.current = 0;
    }, 500);
  };

  // Navigate to upload page
  const handleUploadClick = () => {
    router.push('/patient/upload');
  };

  // Navigate to sessions page
  const handleSessionsClick = () => {
    router.push('/patient/sessions');
  };

  // Navigate to dashboard
  const handleDashboardClick = () => {
    router.push('/patient');
  };

  // Sessions page layout: Logo left, empty right (matching Dashboard structure)
  if (isSessionsPage) {
    return (
      <header className="sticky top-0 z-50 bg-[#F8F7F4] dark:bg-[#1a1625] border-b border-[#E0DDD8] dark:border-[#3d3548] h-[60px] flex items-center justify-between transition-colors duration-300">
        {/* Left section - TheraBridge logo */}
        <div className="flex items-center pl-6 w-[200px]">
          <CombinedLogo
            iconSize={28}
            textClassName="text-base"
          />
        </div>

        {/* Center section - Navigation (perfectly centered) */}
        <nav className="flex items-center gap-8">
          <button
            onClick={handleDashboardClick}
            className={`text-sm font-medium transition-colors pb-1 ${
              isDashboardPage
                ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-b-2 border-[#5AB9B4] dark:border-[#a78bfa]'
                : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa]'
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={handleSessionsClick}
            className={`text-sm font-medium transition-colors pb-1 ${
              isSessionsPage
                ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-b-2 border-[#5AB9B4] dark:border-[#a78bfa]'
                : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa]'
            }`}
          >
            Sessions
          </button>
          <button
            onClick={onAskAIClick}
            className="text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] transition-colors pb-1"
          >
            Ask AI
          </button>
          <button
            onClick={handleUploadClick}
            className="text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] transition-colors pb-1"
          >
            Upload
          </button>
        </nav>

        {/* Right section - Empty (fixed width matching left for centering) */}
        <div className="w-[200px]"></div>
      </header>
    );
  }

  // Default layout (Dashboard page): Theme left, Logo right
  return (
    <header className="sticky top-0 z-50 bg-[#F8F7F4] dark:bg-[#1a1625] border-b border-[#E0DDD8] dark:border-[#3d3548] h-[60px] flex items-center justify-between transition-colors duration-300">
      {/* Left section - Theme toggle (fixed width for centering) */}
      <div className="flex items-center gap-2 pl-3 w-[200px]">
        <button
          onClick={toggleTheme}
          className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
          <ThemeIcon isDark={isDark} />
        </button>
      </div>

      {/* Center section - Navigation (perfectly centered) */}
      <nav className="flex items-center gap-8">
        <button
          onClick={handleDashboardClick}
          className={`text-sm font-medium transition-colors pb-1 ${
            isDashboardPage
              ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-b-2 border-[#5AB9B4] dark:border-[#a78bfa]'
              : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa]'
          }`}
        >
          Dashboard
        </button>
        <button
          onClick={handleSessionsClick}
          className={`text-sm font-medium transition-colors pb-1 ${
            isSessionsPage
              ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-b-2 border-[#5AB9B4] dark:border-[#a78bfa]'
              : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa]'
          }`}
        >
          Sessions
        </button>
        <button
          onClick={onAskAIClick}
          className="text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] transition-colors pb-1"
        >
          Ask AI
        </button>
        <button
          onClick={handleUploadClick}
          className="text-sm font-medium text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] transition-colors pb-1"
        >
          Upload
        </button>
      </nav>

      {/* Right section - TheraBridge logo (fixed width matching left for centering) */}
      <div className="flex items-center justify-end pr-6 w-[200px]">
        <CombinedLogo
          iconSize={28}
          textClassName="text-base"
        />
      </div>
    </header>
  );
}
