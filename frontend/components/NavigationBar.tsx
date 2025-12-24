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
import { demoApiClient, DemoStatusResponse } from '@/lib/demo-api-client';

const TYPOGRAPHY = {
  sans: 'var(--font-inter)',
} as const;

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
  const [isStopping, setIsStopping] = useState(false);
  const [isResuming, setIsResuming] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [processingState, setProcessingState] = useState<'running' | 'stopped' | 'complete' | 'not_started'>('not_started');
  const [canResume, setCanResume] = useState(false);

  // Prevent hydration mismatch by only rendering theme-dependent content after mount
  useEffect(() => {
    setMounted(true);
  }, []);

  // PR #3 Phase 4: Poll for processing state (every 2 seconds)
  useEffect(() => {
    const pollProcessingState = async () => {
      const status = await demoApiClient.getStatus();
      if (status) {
        setProcessingState(status.processing_state);
        setCanResume(status.can_resume);
      }
    };

    // Initial fetch
    pollProcessingState();

    // Poll every 2 seconds
    const interval = setInterval(pollProcessingState, 2000);

    return () => clearInterval(interval);
  }, []);

  const isDark = theme === 'dark';
  const toggleTheme = () => setTheme(isDark ? 'light' : 'dark');

  const handleStopProcessing = async () => {
    setIsStopping(true);
    try {
      const result = await demoApiClient.stop();
      if (result) {
        alert(`Processing stopped! Terminated: ${result.terminated.join(', ') || 'none'}`);
        // Immediately update state
        setProcessingState('stopped');
        setCanResume(true);
      } else {
        alert('Failed to stop processing. It may have already completed.');
      }
    } catch (error) {
      console.error('Stop processing error:', error);
      alert('Error stopping processing. Please try again.');
    } finally {
      setIsStopping(false);
    }
  };

  const handleResumeProcessing = async () => {
    setIsResuming(true);
    try {
      const result = await demoApiClient.resume();
      if (result) {
        alert(`Processing resumed! ${result.incomplete_session_id ? 'Re-running incomplete session. ' : ''}${result.remaining_sessions} sessions remaining.`);
        // Immediately update state
        setProcessingState('running');
        setCanResume(false);
      } else {
        alert('Failed to resume processing. Please try again.');
      }
    } catch (error) {
      console.error('Resume processing error:', error);
      alert('Error resuming processing. Please try again.');
    } finally {
      setIsResuming(false);
    }
  };

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
          style={{
            fontFamily: TYPOGRAPHY.sans,
            fontSize: '14px',
            fontWeight: 500,
            ...(isDashboardPage ? {
              filter: 'drop-shadow(0 0 6px rgba(90, 185, 180, 0.4)) brightness(1.1)',
            } : {})
          }}
          className={`transition-all pb-1 border-b-2 ${
            isDashboardPage
              ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-[#5AB9B4] dark:border-[#a78bfa]'
              : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] border-transparent'
          }`}
        >
          Dashboard
        </button>
        <button
          onClick={handleSessionsClick}
          style={{
            fontFamily: TYPOGRAPHY.sans,
            fontSize: '14px',
            fontWeight: 500,
            ...(isSessionsPage ? {
              filter: 'drop-shadow(0 0 6px rgba(90, 185, 180, 0.4)) brightness(1.1)',
            } : {})
          }}
          className={`transition-all pb-1 border-b-2 ${
            isSessionsPage
              ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-[#5AB9B4] dark:border-[#a78bfa]'
              : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] border-transparent'
          }`}
        >
          Sessions
        </button>
        <button
          onClick={handleUploadClick}
          style={{
            fontFamily: TYPOGRAPHY.sans,
            fontSize: '14px',
            fontWeight: 500,
            ...(isUploadPage ? {
              filter: 'drop-shadow(0 0 6px rgba(90, 185, 180, 0.4)) brightness(1.1)',
            } : {})
          }}
          className={`transition-all pb-1 border-b-2 ${
            isUploadPage
              ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-[#5AB9B4] dark:border-[#a78bfa]'
              : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] border-transparent'
          }`}
        >
          Upload
        </button>
        <button
          onClick={handleAskAIClick}
          style={{
            fontFamily: TYPOGRAPHY.sans,
            fontSize: '14px',
            fontWeight: 500,
            ...(isAskAIPage ? {
              filter: 'drop-shadow(0 0 6px rgba(90, 185, 180, 0.4)) brightness(1.1)',
            } : {})
          }}
          className={`transition-all pb-1 border-b-2 ${
            isAskAIPage
              ? 'text-[#5AB9B4] dark:text-[#a78bfa] border-[#5AB9B4] dark:border-[#a78bfa]'
              : 'text-gray-500 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] border-transparent'
          }`}
        >
          Ask AI
        </button>
      </nav>

      {/* Right section - Stop/Resume/Reset Buttons + TheraBridge Logo */}
      <div className="flex items-center justify-end gap-2 pr-6 w-[320px]">
        {/* PR #3 Phase 4: Dynamic Stop/Resume Button */}
        {processingState === 'running' && (
          <button
            onClick={handleStopProcessing}
            disabled={isStopping}
            className="text-[13px] font-medium text-white bg-red-500 dark:bg-red-600 border border-red-500 dark:border-red-600 rounded-[10px] px-[14px] py-[8px] whitespace-nowrap cursor-pointer transition-all duration-200 shadow-[0_0_12px_rgba(239,68,68,0.25)] dark:shadow-[0_0_12px_rgba(220,38,38,0.3)] hover:bg-red-600 dark:hover:bg-red-700 hover:shadow-[0_0_18px_rgba(239,68,68,0.4)] dark:hover:shadow-[0_0_18px_rgba(220,38,38,0.5)] active:bg-red-700 dark:active:bg-red-800 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-red-500 dark:disabled:hover:bg-red-600"
          >
            {isStopping ? 'Stopping...' : 'Stop Processing'}
          </button>
        )}
        {processingState === 'stopped' && canResume && (
          <button
            onClick={handleResumeProcessing}
            disabled={isResuming}
            className="text-[13px] font-medium text-white bg-green-500 dark:bg-green-600 border border-green-500 dark:border-green-600 rounded-[10px] px-[14px] py-[8px] whitespace-nowrap cursor-pointer transition-all duration-200 shadow-[0_0_12px_rgba(34,197,94,0.25)] dark:shadow-[0_0_12px_rgba(22,163,74,0.3)] hover:bg-green-600 dark:hover:bg-green-700 hover:shadow-[0_0_18px_rgba(34,197,94,0.4)] dark:hover:shadow-[0_0_18px_rgba(22,163,74,0.5)] active:bg-green-700 dark:active:bg-green-800 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-green-500 dark:disabled:hover:bg-green-600"
          >
            {isResuming ? 'Resuming...' : 'Resume Processing'}
          </button>
        )}
        {processingState === 'complete' && (
          <button
            disabled
            className="text-[13px] font-medium text-gray-400 dark:text-gray-500 bg-gray-100 dark:bg-[#252030] border border-gray-300 dark:border-gray-600 rounded-[10px] px-[14px] py-[8px] whitespace-nowrap cursor-not-allowed opacity-60"
          >
            Processing Complete
          </button>
        )}
        <button
          onClick={() => setShowResetConfirm(true)}
          className="text-[13px] font-medium text-[#5AB9B4] dark:text-[#9B7AC4] bg-white dark:bg-[#252030] border border-[#5AB9B4] dark:border-[#9B7AC4] rounded-[10px] px-[14px] py-[8px] whitespace-nowrap cursor-pointer transition-all duration-200 shadow-[0_0_12px_rgba(90,185,180,0.25)] dark:shadow-[0_0_12px_rgba(155,122,196,0.3)] hover:bg-[#5AB9B4]/[0.05] dark:hover:bg-[#9B7AC4]/[0.08] hover:shadow-[0_0_18px_rgba(90,185,180,0.4)] dark:hover:shadow-[0_0_18px_rgba(155,122,196,0.5)] active:bg-[#5AB9B4]/[0.1] dark:active:bg-[#9B7AC4]/[0.15] active:scale-[0.98]"
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
