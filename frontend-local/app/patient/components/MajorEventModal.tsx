'use client';

/**
 * MajorEventModal - Modal for displaying major life events from chatbot
 *
 * Features:
 * - Displays event title, date, AI summary, and chat context
 * - Optional link to related therapy session
 * - Reflection section (add/edit patient reflections)
 * - Consistent styling with other dashboard modals
 * - Full accessibility support (focus trap, Escape, keyboard nav)
 */

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Diamond, Calendar, MessageSquare, Link2, Edit3, Save } from 'lucide-react';
import { MajorEventEntry } from '../lib/types';
import { modalVariants, backdropVariants } from '../lib/utils';
import { useModalAccessibility } from '../hooks/useModalAccessibility';

interface MajorEventModalProps {
  event: MajorEventEntry | null;
  isOpen: boolean;
  onClose: () => void;
  onViewRelatedSession?: (sessionId: string) => void;
  onSaveReflection?: (eventId: string, reflection: string) => void;
}

export function MajorEventModal({
  event,
  isOpen,
  onClose,
  onViewRelatedSession,
  onSaveReflection,
}: MajorEventModalProps) {
  const [isEditingReflection, setIsEditingReflection] = useState(false);
  const [reflectionText, setReflectionText] = useState('');
  const modalRef = useRef<HTMLDivElement>(null);

  // Accessibility: focus trap, Escape key, scroll lock
  useModalAccessibility({
    isOpen,
    onClose,
    modalRef,
  });

  // Reset state when modal opens with new event
  const handleOpen = () => {
    if (event) {
      setReflectionText(event.reflection || '');
      setIsEditingReflection(!event.reflection);
    }
  };

  // Handle saving reflection
  const handleSaveReflection = () => {
    if (event && onSaveReflection) {
      onSaveReflection(event.id, reflectionText);
    }
    setIsEditingReflection(false);
  };

  // Handle viewing related session
  const handleViewRelatedSession = () => {
    if (event?.relatedSessionId && onViewRelatedSession) {
      onClose();
      // Small delay to allow modal close animation
      setTimeout(() => {
        onViewRelatedSession(event.relatedSessionId!);
      }, 150);
    }
  };

  if (!event) return null;

  return (
    <AnimatePresence onExitComplete={() => setIsEditingReflection(false)}>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={onClose}
            className="fixed inset-0 bg-black/30 backdrop-blur-sm z-[1000]"
          />

          {/* Modal */}
          <motion.div
            ref={modalRef}
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            onAnimationComplete={(definition) => {
              if (definition === 'visible') handleOpen();
            }}
            className="fixed w-[550px] max-h-[85vh] bg-[#F8F7F4] dark:bg-[#2a2435] rounded-3xl shadow-2xl z-[1001] overflow-hidden border-2 border-[#E0DDD8] dark:border-gray-600"
            style={{
              top: '50%',
              left: '50%',
            }}
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
            aria-labelledby="major-event-title"
          >
            {/* Header with purple accent */}
            <div className="bg-gradient-to-r from-purple-500/10 to-violet-500/10 dark:from-purple-500/20 dark:to-violet-500/20 px-8 py-6 border-b border-gray-200 dark:border-[#3d3548]">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-purple-500/20 dark:bg-purple-500/30 flex items-center justify-center">
                    <Diamond className="w-5 h-5 text-purple-600 dark:text-purple-400" />
                  </div>
                  <div>
                    <h2
                      id="major-event-title"
                      className="text-xl font-light text-gray-800 dark:text-gray-100"
                    >
                      {event.title}
                    </h2>
                    <div className="flex items-center gap-2 mt-1 text-sm text-gray-500 dark:text-gray-400">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{event.date}</span>
                      <span className="text-purple-500 dark:text-purple-400">• Major Event</span>
                    </div>
                  </div>
                </div>

                {/* Close button */}
                <button
                  onClick={onClose}
                  className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
                  aria-label="Close modal"
                >
                  <X className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="p-8 overflow-y-auto max-h-[calc(85vh-120px)]">
              {/* AI Summary */}
              <section className="mb-6">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2">
                  Summary
                </h3>
                <p className="text-gray-700 dark:text-gray-300 font-light leading-relaxed">
                  {event.summary}
                </p>
              </section>

              {/* Chat Context */}
              <section className="mb-6">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-2 flex items-center gap-2">
                  <MessageSquare className="w-4 h-4" />
                  Context from Chat
                </h3>
                <div className="bg-gray-50 dark:bg-[#1a1625] rounded-xl p-4 border border-gray-200 dark:border-[#3d3548]">
                  <p className="text-gray-600 dark:text-gray-400 font-light text-sm leading-relaxed italic">
                    &ldquo;{event.chatContext}&rdquo;
                  </p>
                </div>
              </section>

              {/* Related Session Link */}
              {event.relatedSessionId && (
                <section className="mb-6">
                  <button
                    onClick={handleViewRelatedSession}
                    className="flex items-center gap-2 text-sm text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 transition-colors group"
                  >
                    <Link2 className="w-4 h-4" />
                    <span className="group-hover:underline">View related therapy session</span>
                  </button>
                </section>
              )}

              {/* Reflection Section */}
              <section className="pt-6 border-t border-gray-200 dark:border-[#3d3548]">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
                    My Reflection
                  </h3>
                  {event.reflection && !isEditingReflection && (
                    <button
                      onClick={() => setIsEditingReflection(true)}
                      className="flex items-center gap-1 text-sm text-gray-500 dark:text-gray-400 hover:text-purple-600 dark:hover:text-purple-400 transition-colors"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      Edit
                    </button>
                  )}
                </div>

                {isEditingReflection || !event.reflection ? (
                  /* Edit/Add Mode */
                  <div className="space-y-3">
                    <textarea
                      value={reflectionText}
                      onChange={(e) => setReflectionText(e.target.value)}
                      placeholder="Add your thoughts about this moment..."
                      className="w-full h-24 px-4 py-3 bg-gray-50 dark:bg-[#1a1625] border border-gray-200 dark:border-[#3d3548] rounded-xl text-gray-700 dark:text-gray-300 font-light text-sm placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none"
                    />
                    <div className="flex justify-end gap-2">
                      {event.reflection && (
                        <button
                          onClick={() => {
                            setReflectionText(event.reflection || '');
                            setIsEditingReflection(false);
                          }}
                          className="px-4 py-2 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 transition-colors"
                        >
                          Cancel
                        </button>
                      )}
                      <button
                        onClick={handleSaveReflection}
                        disabled={!reflectionText.trim()}
                        className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 disabled:bg-gray-300 dark:disabled:bg-gray-600 text-white rounded-lg text-sm font-medium transition-colors disabled:cursor-not-allowed"
                      >
                        <Save className="w-4 h-4" />
                        Save Reflection
                      </button>
                    </div>
                  </div>
                ) : (
                  /* Display Mode */
                  <div className="bg-purple-50 dark:bg-purple-500/10 rounded-xl p-4 border border-purple-200 dark:border-purple-500/30">
                    <p className="text-gray-700 dark:text-gray-300 font-light leading-relaxed">
                      {event.reflection}
                    </p>
                  </div>
                )}
              </section>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
