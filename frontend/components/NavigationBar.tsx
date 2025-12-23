'use client';

/**
 * Centralized Navigation Bar Component
 * - Single source of truth for all navigation routing
 * - Ensures consistent navigation across all pages
 * - Unified layout with TheraBridge icon + theme toggle on left, full logo on right
 */

import { useRouter, usePathname } from 'next/navigation';
import { useTheme } from '@/app/patient/contexts/ThemeContext';
import { CombinedLogo, BridgeIcon } from './TheraBridgeLogo';

// Theme Toggle Icon
function ThemeIcon({ isDark }: { isDark: boolean }) {
  if (isDark) {
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

export function NavigationBar() {
  const { isDark, toggleTheme } = useTheme();
  const router = useRouter();
  const pathname = usePathname();

  // Determine active page
  const isSessionsPage = pathname === '/sessions';
  const isDashboardPage = pathname === '/dashboard';
  const isUploadPage = pathname === '/upload';
  const isAskAIPage = pathname === '/ask-ai';

  // Navigation handlers - CENTRALIZED ROUTING
  const handleDashboardClick = () => {
    router.push('/dashboard');
  };

  const handleSessionsClick = () => {
    router.push('/sessions');
  };

  const handleAskAIClick = () => {
    router.push('/ask-ai');
  };

  const handleUploadClick = () => {
    router.push('/upload');
  };

  return (
    <header className="sticky top-0 z-50 bg-[#F8F7F4] dark:bg-[#1a1625] border-b border-[#E0DDD8] dark:border-[#3d3548] h-[60px] flex items-center justify-between transition-colors duration-300">
      {/* Left section - TheraBridge Icon + Theme toggle */}
      <div className="flex items-center gap-3 pl-3 w-[200px]">
        {/* Clickable TheraBridge Logo */}
        <div
          onClick={handleDashboardClick}
          style={{
            cursor: 'pointer',
            transition: 'transform 0.2s ease, filter 0.2s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'scale(1.05)';
            e.currentTarget.style.filter = 'brightness(1.2)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'scale(1)';
            e.currentTarget.style.filter = 'brightness(1)';
          }}
        >
          <BridgeIcon size={32} />
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
          aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
          <ThemeIcon isDark={isDark} />
        </button>
      </div>

      {/* Center section - Navigation */}
      <nav className="flex items-center gap-8">
        <button
          onClick={handleDashboardClick}
          className={`text-sm font-medium transition-all pb-1 border-b-2 ${
            isDashboardPage
              ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-[#5AB9B4] dark:border-[#a78bfa]'
              : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] border-transparent'
          }`}
          style={isDashboardPage ? {
            filter: 'drop-shadow(0 0 6px rgba(90, 185, 180, 0.4)) brightness(1.1)',
          } : {}}
        >
          Dashboard
        </button>
        <button
          onClick={handleSessionsClick}
          className={`text-sm font-medium transition-all pb-1 border-b-2 ${
            isSessionsPage
              ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-[#5AB9B4] dark:border-[#a78bfa]'
              : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] border-transparent'
          }`}
          style={isSessionsPage ? {
            filter: 'drop-shadow(0 0 6px rgba(90, 185, 180, 0.4)) brightness(1.1)',
          } : {}}
        >
          Sessions
        </button>
        <button
          onClick={handleUploadClick}
          className={`text-sm font-medium transition-all pb-1 border-b-2 ${
            isUploadPage
              ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-[#5AB9B4] dark:border-[#a78bfa]'
              : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] border-transparent'
          }`}
          style={isUploadPage ? {
            filter: 'drop-shadow(0 0 6px rgba(90, 185, 180, 0.4)) brightness(1.1)',
          } : {}}
        >
          Upload
        </button>
        <button
          onClick={handleAskAIClick}
          className={`text-sm font-medium transition-all pb-1 border-b-2 ${
            isAskAIPage
              ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-[#5AB9B4] dark:border-[#a78bfa]'
              : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] border-transparent'
          }`}
          style={isAskAIPage ? {
            filter: 'drop-shadow(0 0 6px rgba(90, 185, 180, 0.4)) brightness(1.1)',
          } : {}}
        >
          Ask AI
        </button>
      </nav>

      {/* Right section - Full TheraBridge Logo */}
      <div className="flex items-center justify-end pr-6 w-[200px]">
        <CombinedLogo iconSize={28} textClassName="text-base" />
      </div>
    </header>
  );
}
