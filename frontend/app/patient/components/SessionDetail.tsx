'use client';

/**
 * Session detail fullscreen view
 * - Two-column layout (transcript left, analysis right)
 * - Top bar with navigation
 * - FIXED: Dark mode support + gray border
 * - FIXED: Accessibility - focus trap, Escape key, focus restoration
 */

import { useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowLeft, Star } from 'lucide-react';
import { Session } from '../lib/types';
import { getMoodEmoji, fullscreenVariants } from '../lib/utils';
import { useModalAccessibility } from '../hooks/useModalAccessibility';
import { useSessionData } from '../contexts/SessionDataContext';
import { DeepAnalysisSection } from './DeepAnalysisSection';
import { LoadingOverlay } from './LoadingOverlay';

// Font families - matching SessionCard (using system-ui throughout)
const fontSerif = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
const fontSans = 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

interface SessionDetailProps {
  session: Session | null;
  onClose: () => void;
}

export function SessionDetail({ session, onClose }: SessionDetailProps) {
  const modalRef = useRef<HTMLDivElement>(null);
  const { loadingSessions } = useSessionData();

  // Accessibility: focus trap, Escape key, scroll lock
  useModalAccessibility({
    isOpen: !!session,
    onClose,
    modalRef,
  });

  if (!session) return null;

  const isLoading = loadingSessions.has(session.id);

  // Debug: Check if deep_analysis exists
  console.log('[SessionDetail] Session:', session.id, 'has deep_analysis:', !!session.deep_analysis);
  if (session.deep_analysis) {
    console.log('[SessionDetail] Deep analysis data:', session.deep_analysis);
  }

  const moodEmoji = getMoodEmoji(session.mood);

  return (
    <AnimatePresence>
      <motion.div
        ref={modalRef}
        variants={fullscreenVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
        className="fixed top-0 left-0 right-0 bottom-0 bg-[#F8F7F4] dark:bg-[#1a1625] z-[2000] flex flex-col border-2 border-[#E0DDD8] dark:border-gray-600"
        style={{ margin: 0 }}
        role="dialog"
        aria-modal="true"
        aria-labelledby="session-detail-title"
      >
        {/* Top Bar */}
        <div className="h-[60px] border-b border-[#E0DDD8] dark:border-[#3d3548] flex items-center justify-between px-6 flex-shrink-0 bg-[#F8F7F4] dark:bg-[#1a1625]">
          <button
            onClick={onClose}
            className="flex items-center gap-2 text-[#5AB9B4] dark:text-[#a78bfa] hover:opacity-80 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-medium">Back to Dashboard</span>
          </button>

          <div className="text-center">
            <h2 id="session-detail-title" className="text-lg font-semibold text-gray-800 dark:text-gray-200">
              Session {session.id.replace('s', '')} - {session.date}, 2024
            </h2>
            {session.milestone && (
              <div className="flex items-center justify-center gap-2 mt-1">
                <Star className="w-4 h-4 text-amber-600 fill-amber-600" />
                <span className="text-sm text-amber-900 dark:text-amber-400 font-medium">
                  {session.milestone.title}
                </span>
              </div>
            )}
          </div>

          <button
            onClick={onClose}
            className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
          >
            <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        {/* Two-column Content */}
        <div className="flex-1 grid grid-cols-2 overflow-hidden">
          {/* Left Column - Transcript */}
          <div className="border-r border-[#E0DDD8] dark:border-[#3d3548] overflow-y-auto p-8 bg-[#F8F7F4] dark:bg-[#1a1625]">
            <h3 style={{ fontFamily: fontSans }} className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-6">
              Session Transcript
            </h3>

            {session.transcript && session.transcript.length > 0 ? (
              <div className="space-y-6">
                {session.transcript.map((entry, idx) => (
                  <div key={idx} className="flex gap-4">
                    {/* Timestamp on the left */}
                    <div className="flex-shrink-0 w-[50px] pt-0.5">
                      {entry.timestamp && (
                        <span style={{ fontFamily: fontSans }} className="text-xs font-medium text-gray-400 dark:text-gray-500">
                          {entry.timestamp}
                        </span>
                      )}
                    </div>

                    {/* Speaker and text */}
                    <div className="flex-1">
                      <p style={{ fontFamily: fontSans }} className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                        {entry.speaker}:
                      </p>
                      <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed pl-4 border-l-2 border-gray-200 dark:border-[#3d3548]">
                        {entry.text}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-500 dark:text-gray-500 italic">
                Transcript not available for this session.
              </p>
            )}
          </div>

          {/* Right Column - Analysis */}
          <div className="overflow-y-auto p-8 bg-gray-50 dark:bg-[#2a2435]">
            <h3 style={{ fontFamily: fontSans }} className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-6">
              Session Analysis
            </h3>

            {/* Metadata */}
            <div className="mb-6 p-4 bg-[#ECEAE5] dark:bg-[#1a1625] rounded-xl border border-[#E0DDD8] dark:border-[#3d3548]">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p style={{ fontFamily: fontSans }} className="text-gray-500 dark:text-gray-500 mb-1">Duration</p>
                  <p style={{ fontFamily: fontSerif }} className="text-gray-800 dark:text-gray-200 font-medium">{session.duration}</p>
                </div>
                <div>
                  <p style={{ fontFamily: fontSans }} className="text-gray-500 dark:text-gray-500 mb-1">Session Mood</p>
                  <p style={{ fontFamily: fontSerif }} className="text-gray-800 dark:text-gray-200 font-medium flex items-center gap-2">
                    <span className="text-lg">{moodEmoji}</span>
                    <span className="capitalize">{session.mood}</span>
                  </p>
                </div>
              </div>
            </div>

            {/* Topics Discussed */}
            <div className="mb-6">
              <h4 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-3">
                Topics Discussed
              </h4>
              <ul className="space-y-2">
                {session.topics.map((topic, idx) => (
                  <li key={idx} style={{ fontFamily: fontSerif }} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#5AB9B4] dark:bg-[#a78bfa] mt-2 flex-shrink-0" />
                    <span>{topic}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Strategy Used */}
            <div className="mb-6">
              <h4 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-3">
                Strategy Used
              </h4>
              <p style={{ fontFamily: fontSerif }} className="text-base font-semibold text-[#5AB9B4] dark:text-[#a78bfa] mb-2">{session.strategy}</p>
              <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                This therapeutic approach was applied during the session to address the identified concerns.
              </p>
            </div>

            {/* Action Items */}
            <div className="mb-6">
              <h4 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wide mb-3">
                Action Items
              </h4>
              <ul className="space-y-2">
                {session.actions.map((action, idx) => (
                  <li key={idx} style={{ fontFamily: fontSerif }} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#B8A5D6] dark:bg-[#c084fc] mt-2 flex-shrink-0" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Patient Summary (AI-generated from Wave 1 analysis) */}
            {(session.summary || session.patientSummary) && (
              <div className="p-4 bg-[#5AB9B4]/5 dark:bg-[#a78bfa]/10 rounded-xl border border-[#5AB9B4]/20 dark:border-[#a78bfa]/30">
                <h4 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-[#5AB9B4] dark:text-[#a78bfa] uppercase tracking-wide mb-3">
                  Session Summary
                </h4>
                <p style={{ fontFamily: fontSerif }} className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
                  {session.summary || session.patientSummary}
                </p>
              </div>
            )}

            {/* Milestone Description */}
            {session.milestone && (
              <div className="mt-6 p-4 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-700/50">
                <div className="flex items-start gap-3">
                  <Star className="w-5 h-5 text-amber-600 fill-amber-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <h4 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-amber-900 dark:text-amber-400 mb-2">
                      {session.milestone.title}
                    </h4>
                    <p style={{ fontFamily: fontSerif }} className="text-sm text-amber-800 dark:text-amber-300 leading-relaxed">
                      {session.milestone.description}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Deep Clinical Analysis */}
            {session.deep_analysis && (
              <div className="mt-6 p-4 bg-[#5AB9B4]/5 dark:bg-[#a78bfa]/10 rounded-xl border border-[#5AB9B4]/20 dark:border-[#a78bfa]/30">
                <DeepAnalysisSection
                  analysis={session.deep_analysis}
                  confidence={session.analysis_confidence || 0.8}
                />
              </div>
            )}
          </div>
        </div>

        {/* Loading Overlay */}
        <LoadingOverlay visible={isLoading} />
      </motion.div>
    </AnimatePresence>
  );
}
