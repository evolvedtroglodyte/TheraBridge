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

import { DobbyLogo } from '../DobbyLogo';
import type { ChatSession } from './index';

interface ChatSidebarProps {
  isExpanded: boolean;
  onToggle: () => void;
  recentChats: ChatSession[];
  onNewChat: () => void;
  onSelectChat: (id: string) => void;
  userName: string;
  isDark: boolean;
}

export function ChatSidebar({
  isExpanded,
  onToggle,
  recentChats,
  onNewChat,
  onSelectChat,
  userName,
  isDark,
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
        {/* Brand text - only visible when expanded */}
        {isExpanded && (
          <span
            className={`font-mono text-base font-medium tracking-[0.5px] uppercase ${
              isDark ? 'text-gray-200' : 'text-[#1a1a1a]'
            }`}
          >
            Dobby
          </span>
        )}

        {/* Toggle Button */}
        <button
          onClick={onToggle}
          aria-label={isExpanded ? 'Close sidebar' : 'Open sidebar'}
          className={`relative w-8 h-8 flex items-center justify-center rounded-lg ${hoverBg} ${textMuted} group`}
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="18" height="18" rx="2"/>
            <line x1="9" y1="3" x2="9" y2="21"/>
          </svg>
          {/* Tooltip - shows on hover regardless of expanded state */}
          <span
            className={`absolute left-[calc(100%+16px)] top-1/2 -translate-y-1/2 font-nunito text-sm font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 ${tooltipColor}`}
          >
            {isExpanded ? 'Close sidebar' : 'Open sidebar'}
          </span>
        </button>
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

      {/* User Section */}
      <div className={`px-2 py-3 border-t ${borderColor}`}>
        <div className={`flex items-center gap-3 ${isExpanded ? 'px-2' : 'justify-center'}`}>
          {/* User Avatar - Dobby logo style */}
          <div className="w-8 h-8 flex-shrink-0">
            <svg width="32" height="32" viewBox="0 0 120 120" fill="none">
              <polygon points="15,55 35,35 35,65" fill={accentColor}/>
              <polygon points="105,55 85,35 85,65" fill={accentColor}/>
              <rect x="30" y="30" width="60" height="60" rx="14" fill={accentColor}/>
              <circle cx="45" cy="55" r="8" fill="white"/>
              <circle cx="45" cy="57" r="4" fill={isDark ? '#1a1625' : '#1a1a1a'}/>
              <circle cx="75" cy="55" r="8" fill="white"/>
              <circle cx="75" cy="57" r="4" fill={isDark ? '#1a1625' : '#1a1a1a'}/>
              <path d="M48 74 Q60 82 72 74" stroke="white" strokeWidth="3" strokeLinecap="round" fill="none"/>
            </svg>
          </div>
          {isExpanded && (
            <span className={`font-nunito text-sm font-medium ${textColor}`}>
              {userName}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
