'use client';

/**
 * Individual session card component
 * - Two-column layout with implicit hierarchy
 * - Mood-based left border accent
 * - Milestone indicator (horizontal top banner)
 * - FIXED: Dark mode support
 * - UPDATED: Horizontal banner replaces diagonal ribbon for better UX
 */

import { motion } from 'framer-motion';
import { Star, Sparkles } from 'lucide-react';
import { Session } from '../lib/types';
import { getMoodColor, getMoodEmoji } from '../lib/utils';

interface SessionCardProps {
  session: Session;
  onClick: () => void;
  /** DOM id for scroll targeting from Timeline */
  id?: string;
}

/**
 * Truncates milestone title to fit banner width
 * @param title - Full milestone title
 * @param maxLength - Maximum characters before truncation (default 30)
 */
function truncateMilestoneTitle(title: string, maxLength: number = 30): string {
  if (title.length <= maxLength) return title;
  return title.slice(0, maxLength).trim() + '…';
}

export function SessionCard({ session, onClick, id }: SessionCardProps) {
  const moodColor = getMoodColor(session.mood);
  const moodEmoji = getMoodEmoji(session.mood);

  return (
    <motion.div
      id={id}
      onClick={onClick}
      className={`relative bg-gradient-to-br from-white to-[#FEFDFB] dark:from-[#2a2435] dark:to-[#1a1625] rounded-xl cursor-pointer overflow-hidden flex flex-col min-h-[280px] transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548] ${session.milestone ? 'ring-2 ring-amber-300/50 dark:ring-amber-500/30' : ''}`}
      style={{
        borderLeft: `3px solid ${moodColor}`,
        boxShadow: session.milestone
          ? '0 2px 8px rgba(0,0,0,0.08), 0 0 20px rgba(251,191,36,0.15)'
          : '0 2px 8px rgba(0,0,0,0.08)'
      }}
      whileHover={{
        y: -4,
        boxShadow: session.milestone
          ? '0 6px 16px rgba(0,0,0,0.12), 0 0 30px rgba(251,191,36,0.2)'
          : '0 6px 16px rgba(0,0,0,0.12)'
      }}
      transition={{ duration: 0.2 }}
      role="button"
      tabIndex={0}
      aria-label={`Session on ${session.date}, mood ${session.mood}, topics ${session.topics.join(', ')}, strategy ${session.strategy}${session.milestone ? ', breakthrough session: ' + session.milestone.title : ''}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onClick();
        }
      }}
    >
      {/* Milestone Horizontal Banner - spans full width at top */}
      {session.milestone && (
        <div className="w-full h-7 bg-gradient-to-r from-amber-400 to-amber-500 dark:from-amber-500 dark:to-amber-600 flex items-center justify-center gap-2 px-3 rounded-t-[11px] flex-shrink-0">
          <Sparkles className="w-3.5 h-3.5 text-amber-900 flex-shrink-0" />
          <span className="text-xs font-semibold text-amber-900 truncate">
            {truncateMilestoneTitle(session.milestone.title)}
          </span>
        </div>
      )}

      {/* Card Content Container - applies padding uniformly */}
      <div className="p-5 flex flex-col flex-1">
        {/* Metadata Row */}
        <div className="flex items-center justify-center gap-2.5 mb-5 flex-shrink-0">
          <span className="text-sm font-mono uppercase text-gray-500 dark:text-gray-500">{session.duration}</span>
          <span className="text-gray-400 dark:text-gray-600">•</span>
          <span className="text-lg font-bold text-gray-800 dark:text-gray-200">{session.date}</span>
          <span className="text-gray-400 dark:text-gray-600">•</span>
          <span className="text-xl">{moodEmoji}</span>
          {/* Inline star indicator for milestone */}
          {session.milestone && (
            <Star className="w-4 h-4 text-amber-500 fill-amber-400 ml-1" />
          )}
        </div>

        {/* Two-column Layout */}
        <div className="flex-1 flex flex-col">
          {/* Upper 2/3: Two columns with separator */}
          <div className="grid grid-cols-2 gap-5 relative flex-[2] pt-3">
            {/* Vertical Separator Line */}
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-200 dark:bg-[#3d3548] opacity-50 -translate-x-1/2" />

            {/* Left Column - Topics */}
            <div className="pr-3 min-w-0">
              <ul className="space-y-2.5">
                {session.topics.map((topic, idx) => (
                  <li key={idx} className="text-[15px] font-[350] text-gray-700 dark:text-gray-300 leading-relaxed break-words">
                    {topic}
                  </li>
                ))}
              </ul>
            </div>

            {/* Right Column - Strategy */}
            <div className="pl-3 min-w-0">
              <p className="text-[15px] font-semibold text-[#5AB9B4] dark:text-[#a78bfa] leading-relaxed break-words">
                {session.strategy}
              </p>
            </div>
          </div>

          {/* Bottom 1/3: Action items full width */}
          {session.actions.length > 0 && (
            <div className="flex-1 pt-4 border-t border-gray-100 dark:border-[#3d3548] mt-4">
              <ul className="space-y-2">
                {session.actions.map((action, idx) => (
                  <li key={idx} className="flex items-start gap-2.5 text-[14px] font-[350] text-gray-600 dark:text-gray-400 leading-relaxed">
                    <span className="text-[#5AB9B4] dark:text-[#a78bfa] mt-0.5 flex-shrink-0 font-semibold">•</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
