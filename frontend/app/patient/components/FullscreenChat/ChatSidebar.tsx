'use client';

/**
 * ChatSidebar - Expandable sidebar for Dobby AI chat
 *
 * Features:
 * - Collapse/expand toggle with smooth animation
 * - New chat button
 * - Chats navigation
 * - Recent chats list
 * - User avatar with name
 * - Tooltips on collapsed state
 */

import { BridgeIcon, TextLogo } from '@/components/TheraBridgeLogo';
import type { ChatSession } from './index';

interface ChatSidebarProps {
  isExpanded: boolean;
  onToggle: () => void;
  recentChats: ChatSession[];
  onNewChat: () => void;
  onSelectChat: (id: string) => void;
  userName: string;
  isDark: boolean;
  onHomeClick?: () => void;
  onThemeToggle?: () => void;
}

export function ChatSidebar({
  isExpanded,
  onToggle,
  recentChats,
  onNewChat,
  onSelectChat,
  userName,
  isDark,
  onHomeClick,
  onThemeToggle,
}: ChatSidebarProps) {
  const bgColor = isDark ? 'bg-[#1a1625]' : 'bg-[#F8F7F4]';
  const borderColor = isDark ? 'border-[#2a2535]' : 'border-[#E5E2DE]';
  const textColor = isDark ? 'text-gray-300' : 'text-gray-700';
  const textMuted = isDark ? 'text-gray-500' : 'text-gray-500';
  const hoverBg = isDark ? 'hover:bg-white/5' : 'hover:bg-black/5';
  const tooltipColor = isDark ? 'text-[#8B6AAE]' : 'text-[#5AB9B4]';
  const accentColor = isDark ? '#8B6AAE' : '#5AB9B4';

  return (
    <div
      className={`${bgColor} border-r ${borderColor} flex flex-col transition-all duration-[250ms] ease-out overflow-visible flex-shrink-0 ${
        isExpanded ? 'w-[260px]' : 'w-[60px]'
      }`}
    >
      {/* Header */}
      <div className={`flex items-center h-14 px-4 ${isExpanded ? 'justify-between' : 'justify-center'}`}>
        {/* TheraBridge branding - icon + text when expanded, icon only when collapsed */}
        {isExpanded ? (
          <div className={`flex items-center gap-2 ${isDark ? 'text-gray-200' : 'text-[#1a1a1a]'}`}>
            <BridgeIcon size={24} />
            <TextLogo fontSize={16} />
          </div>
        ) : (
          <div
            onClick={onHomeClick}
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
            className={isDark ? 'text-[#8B6AAE]' : 'text-[#5AB9B4]'}
          >
            <BridgeIcon size={28} />
          </div>
        )}

        {/* Toggle Button - only visible when expanded */}
        {isExpanded && (
          <button
            onClick={onToggle}
            aria-label="Close sidebar"
            className={`relative w-8 h-8 flex items-center justify-center rounded-lg ${hoverBg} ${textMuted} group`}
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="3" width="18" height="18" rx="2"/>
              <line x1="9" y1="3" x2="9" y2="21"/>
            </svg>
            {/* Tooltip */}
            <span
              className={`absolute left-[calc(100%+16px)] top-1/2 -translate-y-1/2 font-nunito text-sm font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 ${tooltipColor}`}
            >
              Close sidebar
            </span>
          </button>
        )}
      </div>

      {/* Navigation */}
      <div className={`flex-1 px-2 flex flex-col gap-2 overflow-visible ${isExpanded ? 'items-stretch' : 'items-center'}`}>
        {/* New Chat Button - Teal (light) / Purple (dark) solid background */}
        <button
          onClick={onNewChat}
          className={`relative flex items-center gap-3 rounded-[10px] transition-colors group ${
            isExpanded
              ? 'px-4 py-2.5 w-full justify-start'
              : 'w-10 h-10 justify-center'
          } ${
            isDark
              ? 'bg-[#8B6AAE] hover:bg-[#9B7ABE]'
              : 'bg-[#5AB9B4] hover:bg-[#4AA9A4]'
          }`}
        >
          <svg className="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          {isExpanded && (
            <span className="font-nunito text-sm font-medium text-white">New chat</span>
          )}
          {/* Tooltip */}
          {!isExpanded && (
            <span
              className={`absolute left-[calc(100%+16px)] top-1/2 -translate-y-1/2 font-nunito text-sm font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none ${tooltipColor}`}
            >
              New chat
            </span>
          )}
        </button>

        {/* Chats Button */}
        <button
          className={`relative flex items-center gap-3 rounded-lg transition-colors ${hoverBg} ${
            isExpanded ? 'px-3 py-2 w-full' : 'w-10 h-10 justify-center'
          } group`}
        >
          <svg className={`w-5 h-5 ${textMuted}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          {isExpanded && (
            <span className={`font-nunito text-sm font-medium ${textColor}`}>Chats</span>
          )}
          {/* Tooltip */}
          {!isExpanded && (
            <span
              className={`absolute left-[calc(100%+16px)] top-1/2 -translate-y-1/2 font-nunito text-sm font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none ${tooltipColor}`}
            >
              Chats
            </span>
          )}
        </button>

        {/* Recents Section - only visible when expanded */}
        {isExpanded && (
          <div className="mt-4">
            <span className={`px-3 font-nunito text-xs font-semibold uppercase tracking-wide ${textMuted}`}>
              Recents
            </span>
            <div className="mt-2 space-y-1">
              {recentChats.map((chat) => (
                <button
                  key={chat.id}
                  onClick={() => onSelectChat(chat.id)}
                  className={`w-full px-3 py-2 rounded-lg text-left transition-colors ${hoverBg}`}
                >
                  <span className={`font-nunito text-sm ${textColor} line-clamp-1`}>
                    {chat.title}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
