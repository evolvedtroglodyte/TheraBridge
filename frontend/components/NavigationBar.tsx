'use client';

/**
 * Centralized Navigation Bar Component
 * - Single source of truth for all navigation routing
 * - Ensures consistent navigation across all pages
 * - Unified layout with TheraBridge icon + theme toggle on left, full logo on right
 */

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useTheme } from 'next-themes';
import { CombinedLogo, BridgeIcon } from './TheraBridgeLogo';
import { demoApiClient } from '@/lib/demo-api-client';

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
  const { theme, setTheme } = useTheme();
  const router = useRouter();
  const pathname = usePathname();

  const [showResetConfirm, setShowResetConfirm] = useState(false);
  const [isResetting, setIsResetting] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch by only rendering theme-dependent content after mount
  useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = theme === 'dark';
  const toggleTheme = () => setTheme(isDark ? 'light' : 'dark');

  const handleResetDemo = async () => {
    setIsResetting(true);
    try {
      const result = await demoApiClient.reset();
      if (result) {
        // Show success and reload page
        alert('Demo reset successfully! Page will reload.');
        window.location.reload();
      } else {
        alert('Failed to reset demo. Please try again.');
      }
    } catch (error) {
      console.error('Reset demo error:', error);
      alert('An error occurred while resetting demo.');
    } finally {
      setIsResetting(false);
      setShowResetConfirm(false);
    }
  };

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

  // Don't render theme-dependent content until mounted to prevent hydration mismatch
  if (!mounted) {
    return (
      <header className="sticky top-0 z-50 bg-[#F8F7F4] border-b border-[#E0DDD8] h-[60px] flex items-center justify-between">
        <div className="flex items-center gap-3 pl-3 w-[200px]">
          <div className="w-8 h-8" /> {/* Placeholder for logo */}
          <div className="w-10 h-10" /> {/* Placeholder for theme toggle */}
        </div>
        <div className="flex items-center gap-8">
          <div className="w-20 h-4" /> {/* Placeholder for nav items */}
        </div>
        <div className="w-[200px]" />
      </header>
    );
  }

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

      {/* Right section - Reset Demo Button + TheraBridge Logo */}
      <div className="flex items-center justify-end gap-3 pr-6 w-[240px]">
        <button
          onClick={() => setShowResetConfirm(true)}
          className="text-[13px] font-medium text-[#5AB9B4] dark:text-[#9B7AC4] bg-white dark:bg-[#252030] border border-[#5AB9B4] dark:border-[#9B7AC4] rounded-[10px] px-[18px] py-[10px] whitespace-nowrap cursor-pointer transition-all duration-200 shadow-[0_0_12px_rgba(90,185,180,0.25)] dark:shadow-[0_0_12px_rgba(155,122,196,0.3)] hover:bg-[#5AB9B4]/[0.05] dark:hover:bg-[#9B7AC4]/[0.08] hover:shadow-[0_0_18px_rgba(90,185,180,0.4)] dark:hover:shadow-[0_0_18px_rgba(155,122,196,0.5)] active:bg-[#5AB9B4]/[0.1] dark:active:bg-[#9B7AC4]/[0.15] active:shadow-[0_0_24px_rgba(90,185,180,0.6),0_0_40px_rgba(90,185,180,0.3)] dark:active:shadow-[0_0_24px_rgba(155,122,196,0.7),0_0_40px_rgba(155,122,196,0.4)] active:scale-[0.98]"
        >
          Reset Demo
        </button>
        <CombinedLogo iconSize={28} textClassName="text-base" />
      </div>

      {/* Reset Confirmation Modal */}
      {showResetConfirm && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-[#1a1625] border border-gray-200 dark:border-[#3d3548] rounded-lg p-6 max-w-md mx-4 shadow-xl">
            <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-3">
              Reset Demo?
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-6">
              This will delete all your demo data and restore the original 10 sessions. Any uploaded sessions will be lost.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowResetConfirm(false)}
                disabled={isResetting}
                className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-[#3d3548] rounded-md transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleResetDemo}
                disabled={isResetting}
                className="px-4 py-2 text-sm font-medium text-white bg-[#5AB9B4] dark:bg-[#a78bfa] hover:bg-[#4a9a95] dark:hover:bg-[#9370db] rounded-md transition-colors disabled:opacity-50"
              >
                {isResetting ? 'Resetting...' : 'Reset Demo'}
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
