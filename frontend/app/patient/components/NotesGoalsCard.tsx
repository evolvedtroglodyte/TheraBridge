'use client';

/**
 * Notes/Goals panel - AI-generated therapy summary
 * - Compact state: Preview with key achievements
 * - Expanded modal: Collapsible sections with full details
 * - Spring animation on expansion
 * - FIXED: Dark mode support + gray border on modal
 * - FIXED: Accessibility - focus trap, Escape key, focus restoration
 */

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronDown } from 'lucide-react';
import { notesGoalsContent } from '../lib/mockData';
import { modalVariants, backdropVariants } from '../lib/utils';
import { useModalAccessibility } from '../hooks/useModalAccessibility';

// Font families - matching SessionCard
const fontSerif = '"Crimson Pro", Georgia, serif';
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

export function NotesGoalsCard() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [openSections, setOpenSections] = useState<Set<number>>(new Set([0]));
  const modalRef = useRef<HTMLDivElement>(null);

  // Accessibility: focus trap, Escape key, scroll lock
  useModalAccessibility({
    isOpen: isExpanded,
    onClose: () => setIsExpanded(false),
    modalRef,
  });

  const toggleSection = (index: number) => {
    const newOpenSections = new Set(openSections);
    if (newOpenSections.has(index)) {
      newOpenSections.delete(index);
    } else {
      newOpenSections.add(index);
    }
    setOpenSections(newOpenSections);
  };

  return (
    <>
      {/* Compact Card */}
      <motion.div
        onClick={() => setIsExpanded(true)}
        className="bg-gradient-to-br from-white to-[#FFF9F5] dark:from-[#2a2435] dark:to-[#1a1625] rounded-2xl p-6 shadow-lg cursor-pointer h-[400px] overflow-hidden transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548]"
        whileHover={{ scale: 1.01, boxShadow: '0 4px 16px rgba(0,0,0,0.12)' }}
        transition={{ duration: 0.2 }}
      >
        <h2 style={{ fontFamily: fontSans }} className="text-lg font-light text-gray-800 dark:text-gray-200 mb-6 text-center">Your Journey</h2>

        <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-600 dark:text-gray-400 mb-5">{notesGoalsContent.summary}</p>

        <ul className="space-y-2">
          {notesGoalsContent.achievements.slice(0, 3).map((achievement, idx) => (
            <li key={idx} style={{ fontFamily: fontSerif }} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
              <span className="w-1.5 h-1.5 rounded-full bg-[#5AB9B4] dark:bg-[#a78bfa] mt-1.5 flex-shrink-0" />
              <span>{achievement}</span>
            </li>
          ))}
        </ul>

        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-[#3d3548]">
          <p style={{ fontFamily: fontSans }} className="text-xs text-gray-500 dark:text-gray-500 font-semibold">Current focus:</p>
          <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-700 dark:text-gray-300 mt-1">{notesGoalsContent.currentFocus.join(', ')}</p>
        </div>
      </motion.div>

      {/* Expanded Modal - FIXED: Gray border added */}
      <AnimatePresence>
        {isExpanded && (
          <>
            {/* Backdrop */}
            <motion.div
              variants={backdropVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={() => setIsExpanded(false)}
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-[1000]"
            />

            {/* Modal */}
            <motion.div
              ref={modalRef}
              variants={modalVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="fixed w-[800px] max-h-[85vh] bg-gradient-to-br from-white to-[#FFF9F5] dark:from-[#2a2435] dark:to-[#1a1625] rounded-3xl shadow-2xl p-8 z-[1001] overflow-y-auto border-2 border-[#E0DDD8] dark:border-gray-600"
              style={{
                top: '50%',
                left: '50%'
              }}
              onClick={(e) => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-labelledby="notes-goals-title"
            >
              {/* Close button */}
              <button
                onClick={() => setIsExpanded(false)}
                className="absolute top-6 right-6 w-11 h-11 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
              >
                <X className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </button>

              {/* Content */}
              <h2 style={{ fontFamily: fontSans }} className="text-2xl font-medium text-gray-800 dark:text-gray-200 mb-6 pr-12 text-center">
                Your Journey
              </h2>

              <p style={{ fontFamily: fontSerif }} className="text-base text-gray-700 dark:text-gray-300 mb-8 leading-relaxed">
                {notesGoalsContent.summary}
              </p>

              <div className="mb-6">
                <h3 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-3">
                  Key Achievements
                </h3>
                <ul className="space-y-2">
                  {notesGoalsContent.achievements.map((achievement, idx) => (
                    <li key={idx} style={{ fontFamily: fontSerif }} className="flex items-start gap-3 text-sm text-gray-700 dark:text-gray-300">
                      <span className="w-2 h-2 rounded-full bg-[#5AB9B4] dark:bg-[#a78bfa] mt-1.5 flex-shrink-0" />
                      <span>{achievement}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mb-6">
                <h3 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-3">
                  Current Focus Areas
                </h3>
                <ul className="space-y-2">
                  {notesGoalsContent.currentFocus.map((focus, idx) => (
                    <li key={idx} style={{ fontFamily: fontSerif }} className="flex items-start gap-3 text-sm text-gray-700 dark:text-gray-300">
                      <span className="w-2 h-2 rounded-full bg-[#B8A5D6] dark:bg-[#c084fc] mt-1.5 flex-shrink-0" />
                      <span>{focus}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Collapsible Sections */}
              <div className="space-y-3">
                {notesGoalsContent.sections.map((section, idx) => (
                  <div key={idx} className="border border-gray-200 dark:border-[#3d3548] rounded-xl overflow-hidden">
                    <button
                      onClick={() => toggleSection(idx)}
                      className="w-full flex items-center justify-between p-4 bg-gray-50 dark:bg-[#1a1625] hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
                    >
                      <span style={{ fontFamily: fontSans }} className="text-sm font-medium text-gray-800 dark:text-gray-200">{section.title}</span>
                      <ChevronDown
                        className={`w-5 h-5 text-gray-600 dark:text-gray-400 transition-transform ${
                          openSections.has(idx) ? 'rotate-180' : ''
                        }`}
                      />
                    </button>
                    {openSections.has(idx) && (
                      <div className="p-4 bg-white dark:bg-[#2a2435]">
                        <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{section.content}</p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
