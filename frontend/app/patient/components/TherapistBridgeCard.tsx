'use client';

/**
 * Therapist Bridge card - Session prep and communication
 * - Compact state: 3 sections visible
 * - Expanded modal: Full details for each section (read-only)
 * - FIXED: Dark mode support + gray border on modal
 * - FIXED: Accessibility - focus trap, Escape key, focus restoration
 */

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { therapistBridgeContent } from '../lib/mockData';
import { modalVariants, backdropVariants } from '../lib/utils';
import { useModalAccessibility } from '../hooks/useModalAccessibility';

// Font families - matching SessionCard
const fontSerif = '"Crimson Pro", Georgia, serif';
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

export function TherapistBridgeCard() {
  const [isExpanded, setIsExpanded] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  // Accessibility: focus trap, Escape key, scroll lock
  useModalAccessibility({
    isOpen: isExpanded,
    onClose: () => setIsExpanded(false),
    modalRef,
  });

  return (
    <>
      {/* Compact Card */}
      <motion.div
        onClick={() => setIsExpanded(true)}
        className="bg-gradient-to-br from-[#FFF5F0] to-[#FFF8F3] dark:from-[#2a2435] dark:to-[#1a1625] rounded-3xl p-6 cursor-pointer h-[280px] flex flex-col overflow-hidden transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548]"
        style={{
          boxShadow: '0 2px 16px rgba(90,185,180,0.15)'
        }}
        whileHover={{
          boxShadow: '0 4px 20px rgba(90,185,180,0.25)',
          y: -2
        }}
        transition={{ duration: 0.2 }}
      >
        <h2 style={{ fontFamily: fontSans }} className="text-lg font-light text-gray-800 dark:text-gray-200 mb-6 text-center">Session Bridge</h2>

        <div className="space-y-5 flex-1 overflow-hidden">
          {/* Next Session Topics */}
          <div>
            <h3 style={{ fontFamily: fontSans }} className="text-sm font-medium text-[#5AB9B4] dark:text-[#a78bfa] mb-2">Next Session Topics</h3>
            <ul className="space-y-1">
              {therapistBridgeContent.nextSessionTopics.slice(0, 2).map((topic, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm font-light text-gray-700 dark:text-gray-300">
                  <span className="text-[#5AB9B4] dark:text-[#a78bfa] mt-0.5">•</span>
                  <span style={{ fontFamily: fontSerif }}>{topic}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Share Progress */}
          <div>
            <h3 style={{ fontFamily: fontSans }} className="text-sm font-medium text-[#5AB9B4] dark:text-[#a78bfa] mb-2">Share Progress</h3>
            <ul className="space-y-1">
              {therapistBridgeContent.shareProgress.slice(0, 2).map((item, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm font-light text-gray-700 dark:text-gray-300">
                  <span className="text-[#5AB9B4] dark:text-[#a78bfa] mt-0.5">•</span>
                  <span style={{ fontFamily: fontSerif }}>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Session Prep */}
          <div>
            <h3 style={{ fontFamily: fontSans }} className="text-sm font-medium text-[#5AB9B4] dark:text-[#a78bfa] mb-2">Session Prep</h3>
            <ul className="space-y-1">
              {therapistBridgeContent.sessionPrep.slice(0, 2).map((item, idx) => (
                <li key={idx} className="flex items-start gap-2 text-sm font-light text-gray-700 dark:text-gray-300">
                  <span className="text-[#5AB9B4] dark:text-[#a78bfa] mt-0.5">•</span>
                  <span style={{ fontFamily: fontSerif }}>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </motion.div>

      {/* Expanded Modal - FIXED: Gray border added */}
      <AnimatePresence>
        {isExpanded && (
          <>
            <motion.div
              variants={backdropVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={() => setIsExpanded(false)}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-[1000]"
            />

            <motion.div
              ref={modalRef}
              variants={modalVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="fixed w-[800px] max-h-[85vh] bg-gradient-to-br from-[#FFF5F0] to-[#FFF8F3] dark:from-[#2a2435] dark:to-[#1a1625] rounded-3xl shadow-2xl p-8 z-[1001] overflow-y-auto border-2 border-[#E0DDD8] dark:border-gray-600"
              role="dialog"
              aria-modal="true"
              aria-labelledby="therapist-bridge-title"
              style={{
                top: '50%',
                left: '50%'
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <button
                onClick={() => setIsExpanded(false)}
                className="absolute top-6 right-6 w-11 h-11 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
              >
                <X className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </button>

              <div className="mb-6 pr-12 text-center">
                <h2 style={{ fontFamily: fontSans }} className="text-2xl font-medium text-gray-800 dark:text-gray-200 mb-1">
                  Session Bridge
                </h2>
                <p style={{ fontFamily: fontSans }} className="text-sm font-light text-gray-600 dark:text-gray-400">
                  Preparing for your next session
                </p>
              </div>

              {/* Next Session Topics */}
              <div className="mb-8">
                <h3 style={{ fontFamily: fontSans }} className="text-base font-semibold text-[#5AB9B4] dark:text-[#a78bfa] mb-4">Conversation Starters</h3>
                <ul className="space-y-3">
                  {therapistBridgeContent.nextSessionTopics.map((topic, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <span className="w-2 h-2 rounded-full bg-[#5AB9B4] dark:bg-[#a78bfa] mt-2 flex-shrink-0" />
                      <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{topic}</p>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Share Progress */}
              <div className="mb-8">
                <h3 style={{ fontFamily: fontSans }} className="text-base font-semibold text-[#5AB9B4] dark:text-[#a78bfa] mb-4">Share Progress with Therapist</h3>
                <ul className="space-y-3">
                  {therapistBridgeContent.shareProgress.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <span className="w-2 h-2 rounded-full bg-[#B8A5D6] dark:bg-[#c084fc] mt-2 flex-shrink-0" />
                      <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{item}</p>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Session Prep */}
              <div>
                <h3 style={{ fontFamily: fontSans }} className="text-base font-semibold text-[#5AB9B4] dark:text-[#a78bfa] mb-4">Session Preparation</h3>
                <ul className="space-y-3">
                  {therapistBridgeContent.sessionPrep.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <span className="w-2 h-2 rounded-full bg-[#F4A69D] dark:bg-[#f4a69d] mt-2 flex-shrink-0" />
                      <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{item}</p>
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
