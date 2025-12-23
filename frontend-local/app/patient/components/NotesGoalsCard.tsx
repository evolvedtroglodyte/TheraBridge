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
        className="bg-gradient-to-br from-white to-[#FFF9F5] dark:from-[#2a2435] dark:to-[#1a1625] rounded-2xl p-6 shadow-lg cursor-pointer h-[400px] flex flex-col transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548]"
        whileHover={{ scale: 1.01, boxShadow: '0 4px 16px rgba(0,0,0,0.12)' }}
        transition={{ duration: 0.2 }}
      >
        {/* Header - Fixed height */}
        <div className="flex-shrink-0 mb-4">
          <h2 className="text-lg font-serif font-semibold text-gray-800 dark:text-gray-200">Notes / Goals</h2>
        </div>

        {/* Session Summary - Fixed height with overflow */}
        <div className="flex-shrink-0 mb-4 h-[80px]">
          <p className="text-xs font-serif font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
            Session Summary
          </p>
          <p className="text-sm font-serif text-gray-600 dark:text-gray-400 line-clamp-3">
            {notesGoalsContent.summary}
          </p>
        </div>

        {/* Key Achievements - Fixed height section */}
        <div className="flex-shrink-0 mb-4 h-[110px]">
          <p className="text-xs font-serif font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
            Key Achievements
          </p>
          <ul className="space-y-1.5 overflow-hidden">
            {notesGoalsContent.achievements.slice(0, 3).map((achievement, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm font-serif text-gray-700 dark:text-gray-300">
                <span className="w-1.5 h-1.5 rounded-full bg-[#5AB9B4] dark:bg-[#a78bfa] mt-1.5 flex-shrink-0" />
                <span className="line-clamp-1">{achievement}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Current Focus - Fixed height section */}
        <div className="flex-1 pt-4 border-t border-gray-200/50 dark:border-[#3d3548] overflow-hidden">
          <p className="text-xs font-serif font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
            Current Focus
          </p>
          <div className="space-y-1 overflow-hidden">
            {notesGoalsContent.currentFocus.slice(0, 2).map((focus, idx) => (
              <p key={idx} className="text-sm font-serif text-gray-700 dark:text-gray-300 line-clamp-1">
                • {focus}
              </p>
            ))}
          </div>
        </div>

        {/* View More Indicator */}
        <div className="flex-shrink-0 mt-3 pt-3 border-t border-gray-200/30 dark:border-[#3d3548]/30">
          <p className="text-xs font-serif text-gray-400 dark:text-gray-500 text-center italic">
            Click to view full details
          </p>
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
              className="fixed w-[700px] max-h-[80vh] bg-gradient-to-br from-white to-[#FFF9F5] dark:from-[#2a2435] dark:to-[#1a1625] rounded-3xl shadow-2xl p-8 z-[1001] overflow-y-auto border-2 border-[#E0DDD8] dark:border-gray-600"
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
              <h2 className="text-2xl font-serif font-semibold text-gray-800 dark:text-gray-200 mb-4 pr-12">
                Your Therapy Journey
              </h2>

              <p className="text-base font-serif text-gray-700 dark:text-gray-300 mb-6 leading-relaxed">
                {notesGoalsContent.summary}
              </p>

              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-3">
                  Key Achievements
                </h3>
                <ul className="space-y-2">
                  {notesGoalsContent.achievements.map((achievement, idx) => (
                    <li key={idx} className="flex items-start gap-3 text-sm font-serif text-gray-700 dark:text-gray-300">
                      <span className="w-2 h-2 rounded-full bg-[#5AB9B4] dark:bg-[#a78bfa] mt-1.5 flex-shrink-0" />
                      <span>{achievement}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wide mb-3">
                  Current Focus Areas
                </h3>
                <ul className="space-y-2">
                  {notesGoalsContent.currentFocus.map((focus, idx) => (
                    <li key={idx} className="flex items-start gap-3 text-sm font-serif text-gray-700 dark:text-gray-300">
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
                      <span className="text-sm font-medium text-gray-800 dark:text-gray-200">{section.title}</span>
                      <ChevronDown
                        className={`w-5 h-5 text-gray-600 dark:text-gray-400 transition-transform ${
                          openSections.has(idx) ? 'rotate-180' : ''
                        }`}
                      />
                    </button>
                    {openSections.has(idx) && (
                      <div className="p-4 bg-white dark:bg-[#2a2435]">
                        <p className="text-sm font-serif text-gray-700 dark:text-gray-300 leading-relaxed">{section.content}</p>
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
