'use client';

/**
 * SessionsSidebar - Sidebar for Sessions page (matches ChatSidebar structure)
 *
 * Features:
 * - TheraBridge branding at top
 * - Home button navigation
 * - Theme toggle
 * - Matches Ask AI sidebar styling and behavior (without chat-specific elements)
 */

import { useRouter } from 'next/navigation';
import { useTheme } from '../contexts/ThemeContext';
import { BridgeIcon } from '@/components/TheraBridgeLogo';

export function SessionsSidebar() {
  const { isDark, toggleTheme } = useTheme();
  const router = useRouter();

  const bgColor = isDark ? 'bg-[#1a1625]' : 'bg-[#F8F7F4]';
  const borderColor = isDark ? 'border-[#2a2535]' : 'border-[#E5E2DE]';
  const hoverBg = isDark ? 'hover:bg-white/5' : 'hover:bg-black/5';
  const tooltipColor = isDark ? 'text-[#8B6AAE]' : 'text-[#5AB9B4]';

  return (
    <div className={`${bgColor} border-r ${borderColor} flex flex-col w-[60px] flex-shrink-0`}>
      {/* Header - TheraBridge Logo */}
      <div className="flex items-center h-14 px-4 justify-center">
        <div className={isDark ? 'text-[#8B6AAE]' : 'text-[#5AB9B4]'}>
          <BridgeIcon size={28} />
        </div>
      </div>

      {/* Navigation */}
      <div className="flex-1 px-2 flex flex-col gap-2 overflow-visible items-center">
        {/* Home Button */}
        <button
          onClick={() => router.push('/patient')}
          className={`relative flex items-center gap-3 rounded-lg transition-colors ${hoverBg} w-10 h-10 justify-center group`}
        >
          <svg
            className="w-5 h-5"
            viewBox="0 0 24 24"
            fill="none"
            stroke={isDark ? '#8B6AAE' : '#5AB9B4'}
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M4 10.5V19a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8.5" />
            <path d="M2.5 12L12 3l9.5 9" />
            <rect x="9" y="14" width="6" height="7" rx="1" />
          </svg>
          {/* Tooltip */}
          <span
            className={`absolute left-[calc(100%+16px)] top-1/2 -translate-y-1/2 font-nunito text-sm font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 ${tooltipColor}`}
          >
            Home
          </span>
        </button>

        {/* Theme Toggle Button */}
        <button
          onClick={toggleTheme}
          className={`relative flex items-center gap-3 rounded-lg transition-colors ${hoverBg} w-10 h-10 justify-center group`}
        >
          {isDark ? (
            // Moon icon for dark mode
            <svg
              className="w-5 h-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#8B6AAE"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          ) : (
            // Sun icon for light mode
            <svg
              className="w-5 h-5"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#5AB9B4"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="4" />
              <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
            </svg>
          )}
          {/* Tooltip */}
          <span
            className={`absolute left-[calc(100%+16px)] top-1/2 -translate-y-1/2 font-nunito text-sm font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 ${tooltipColor}`}
          >
            {isDark ? 'Dark Mode' : 'Light Mode'}
          </span>
        </button>
      </div>
    </div>
  );
}
