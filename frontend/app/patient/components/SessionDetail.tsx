'use client';

/**
 * Session detail fullscreen view
 * - Two-column layout (transcript left, analysis right)
 * - Top bar with navigation
 * - FIXED: Dark mode support + gray border
 * - FIXED: Accessibility - focus trap, Escape key, focus restoration
 */

import { useRef, useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowLeft, Star } from 'lucide-react';
import { Session } from '../lib/types';
import { getMoodEmoji, fullscreenVariants } from '../lib/utils';
import { useModalAccessibility } from '../hooks/useModalAccessibility';
import { useSessionData } from '../contexts/SessionDataContext';
import { DeepAnalysisSection } from './DeepAnalysisSection';
import { LoadingOverlay } from './LoadingOverlay';
import { DobbyLogo } from './DobbyLogo';
import { mapNumericMoodToCategory, formatMoodScore } from '../../../lib/mood-mapper';
import { renderMoodEmoji } from './SessionIcons';
import { useTheme } from 'next-themes';

// Font families - matching dashboard standard (Inter + Crimson Pro)
const TYPOGRAPHY = {
  serif: '"Crimson Pro", Georgia, serif',
  sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
} as const;

// Analysis view type
type AnalysisView = 'prose' | 'structured';

// Tab Toggle Component
interface TabToggleProps {
  activeView: AnalysisView;
  onViewChange: (view: AnalysisView) => void;
  hasProse: boolean;
  hasStructured: boolean;
}

function TabToggle({ activeView, onViewChange, hasProse, hasStructured }: TabToggleProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  // Color palette (matching dashboard theme)
  const activeColor = isDark ? '#a78bfa' : '#5AB9B4'; // Purple (dark) / Teal (light)
  const inactiveColor = isDark ? '#64748b' : '#94a3b8'; // Slate gray
  const activeBg = isDark ? 'rgba(167, 139, 250, 0.15)' : 'rgba(90, 185, 180, 0.15)';

  return (
    <div
      className="flex items-center gap-2 mb-6 p-1 bg-gray-100 dark:bg-[#1a1625] rounded-lg border border-gray-200 dark:border-[#3d3548]"
      role="tablist"
      aria-label="Analysis view selector"
    >
      {/* Prose Tab */}
      <button
        role="tab"
        aria-selected={activeView === 'prose'}
        aria-controls="prose-panel"
        disabled={!hasProse}
        onClick={() => onViewChange('prose')}
        className={`
          flex-1 px-4 py-2.5 rounded-md transition-all duration-200
          ${activeView === 'prose' ? 'shadow-sm' : 'opacity-60 hover:opacity-80'}
          ${!hasProse && 'cursor-not-allowed opacity-40'}
        `}
        style={{
          backgroundColor: activeView === 'prose' ? activeBg : 'transparent',
          fontFamily: TYPOGRAPHY.sans,
          fontSize: '13px',
          fontWeight: activeView === 'prose' ? 600 : 500,
          color: activeView === 'prose' ? activeColor : inactiveColor,
        }}
      >
        📖 Narrative
      </button>

      {/* Structured Tab */}
      <button
        role="tab"
        aria-selected={activeView === 'structured'}
        aria-controls="structured-panel"
        disabled={!hasStructured}
        onClick={() => onViewChange('structured')}
        className={`
          flex-1 px-4 py-2.5 rounded-md transition-all duration-200
          ${activeView === 'structured' ? 'shadow-sm' : 'opacity-60 hover:opacity-80'}
          ${!hasStructured && 'cursor-not-allowed opacity-40'}
        `}
        style={{
          backgroundColor: activeView === 'structured' ? activeBg : 'transparent',
          fontFamily: TYPOGRAPHY.sans,
          fontSize: '13px',
          fontWeight: activeView === 'structured' ? 600 : 500,
          color: activeView === 'structured' ? activeColor : inactiveColor,
        }}
      >
        📊 Structured
      </button>
    </div>
  );
}

// Prose Analysis View Component
interface ProseAnalysisViewProps {
  prose: string;
  generatedAt?: string;
  confidence: number;
}

function ProseAnalysisView({ prose, generatedAt, confidence }: ProseAnalysisViewProps) {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div
      role="tabpanel"
      id="prose-panel"
      aria-labelledby="prose-tab"
      className="animate-fadeIn"
    >
      {/* Header with Dobby logo */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 flex items-center justify-center">
            <DobbyLogo size={40} />
          </div>
          <div>
            <h3 style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200">
              Clinical Narrative
            </h3>
            <p style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px' }} className="text-gray-500 dark:text-gray-400">
              AI-powered analysis • {Math.round(confidence * 100)}% confidence
            </p>
          </div>
        </div>
      </div>

      {/* Prose content */}
      <div className="prose-container p-6 bg-white dark:bg-[#1a1625] rounded-xl border border-gray-200 dark:border-[#3d3548]">
        {/* Split prose into paragraphs for better readability */}
        {prose.split('\n\n').map((paragraph, idx) => (
          <p
            key={idx}
            style={{
              fontFamily: TYPOGRAPHY.serif,
              fontSize: '15px',
              fontWeight: 400,
              lineHeight: 1.8,
              marginBottom: idx < prose.split('\n\n').length - 1 ? '16px' : '0'
            }}
            className="text-gray-700 dark:text-gray-300"
          >
            {paragraph}
          </p>
        ))}
      </div>

      {/* Timestamp footer */}
      {generatedAt && (
        <p style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px' }} className="text-gray-400 dark:text-gray-500 mt-3 text-right">
          Generated {new Date(generatedAt).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: 'numeric',
            minute: '2-digit'
          })}
        </p>
      )}
    </div>
  );
}

// Theme Toggle Icon (matching NavigationBar style)
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

interface SessionDetailProps {
  session: Session | null;
  onClose: () => void;
}

export function SessionDetail({ session, onClose }: SessionDetailProps) {
  const modalRef = useRef<HTMLDivElement>(null);

  // Refs for scroll preservation
  const leftColumnRef = useRef<HTMLDivElement>(null);
  const rightColumnRef = useRef<HTMLDivElement>(null);
  const previousSessionIdRef = useRef<string | null>(null);

  const { loadingSessions } = useSessionData();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Analysis view toggle state
  const [analysisView, setAnalysisView] = useState<AnalysisView>('prose');

  // Load preference from localStorage on mount
  useEffect(() => {
    const savedView = localStorage.getItem('therabridge_analysis_view') as AnalysisView | null;
    if (savedView === 'prose' || savedView === 'structured') {
      setAnalysisView(savedView);
    }
  }, []);

  // Save preference to localStorage when changed
  useEffect(() => {
    localStorage.setItem('therabridge_analysis_view', analysisView);
  }, [analysisView]);

  // Prevent hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = theme === 'dark';
  const toggleTheme = () => setTheme(isDark ? 'light' : 'dark');

  // Accessibility: focus trap, Escape key, scroll lock
  useModalAccessibility({
    isOpen: !!session,
    onClose,
    modalRef,
  });

  // Preserve scroll position when session updates
  useEffect(() => {
    if (!session) return;

    // If session ID changed (user navigated to different session), reset scroll
    if (previousSessionIdRef.current !== session.id) {
      previousSessionIdRef.current = session.id;

      // Reset scroll to top for new session
      if (leftColumnRef.current) leftColumnRef.current.scrollTop = 0;
      if (rightColumnRef.current) rightColumnRef.current.scrollTop = 0;
      return;
    }

    // Same session, preserve scroll position during updates
    const leftScroll = leftColumnRef.current?.scrollTop || 0;
    const rightScroll = rightColumnRef.current?.scrollTop || 0;

    // Restore scroll after React re-renders
    requestAnimationFrame(() => {
      if (leftColumnRef.current) {
        leftColumnRef.current.scrollTo({
          top: leftScroll,
          behavior: 'smooth'
        });
      }
      if (rightColumnRef.current) {
        rightColumnRef.current.scrollTo({
          top: rightScroll,
          behavior: 'smooth'
        });
      }
    });
  }, [session?.id, session?.topics, session?.prose_analysis]); // Re-run when data changes

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
          {/* Session Title (Left) */}
          <h2 id="session-detail-title" style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '24px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200">
            Session Details
          </h2>

          {/* Center (Empty - for balance) */}
          <div></div>

          {/* Controls (Right) */}
          <div className="flex items-center gap-3">
            {/* Theme Toggle */}
            {mounted && (
              <button
                onClick={toggleTheme}
                className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
                aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
              >
                <ThemeIcon isDark={isDark} />
              </button>
            )}

            {/* Close Button (X icon) */}
            <button
              onClick={onClose}
              className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
              aria-label="Close session details"
            >
              <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>
        </div>

        {/* Two-column Content */}
        <div className="flex-1 grid grid-cols-2 overflow-hidden">
          {/* Left Column - Transcript */}
          <div
            ref={leftColumnRef}
            className="border-r border-[#E0DDD8] dark:border-[#3d3548] overflow-y-auto p-8 bg-[#F8F7F4] dark:bg-[#1a1625]"
          >
            <h3 style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200 mb-6">
              Session Transcript
            </h3>

            {session.transcript && session.transcript.length > 0 ? (
              <div className="space-y-6">
                {session.transcript.map((entry, idx) => (
                  <div key={idx} className="flex gap-4">
                    {/* Timestamp on the left */}
                    <div className="flex-shrink-0 w-[50px] pt-0.5">
                      {entry.timestamp && (
                        <span style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px', fontWeight: 500 }} className="text-gray-400 dark:text-gray-500">
                          {entry.timestamp}
                        </span>
                      )}
                    </div>

                    {/* Speaker and text */}
                    <div className="flex-1">
                      <p style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '13px', fontWeight: 600 }} className="text-gray-700 dark:text-gray-300 mb-2">
                        {entry.speaker}:
                      </p>
                      <p style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }} className="text-gray-600 dark:text-gray-400 pl-4 border-l-2 border-gray-200 dark:border-[#3d3548]">
                        {entry.text}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '14px', fontStyle: 'italic' }} className="text-gray-500 dark:text-gray-500">
                Transcript not available for this session.
              </p>
            )}
          </div>

          {/* Right Column - Analysis */}
          <div
            ref={rightColumnRef}
            className="overflow-y-auto p-8 bg-gray-50 dark:bg-[#2a2435]"
          >
            <h3 style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200 mb-6">
              Session Analysis
            </h3>

            {/* Metadata */}
            <div className="mb-6 p-4 bg-[#ECEAE5] dark:bg-[#1a1625] rounded-xl border border-[#E0DDD8] dark:border-[#3d3548]">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px', fontWeight: 500 }} className="text-gray-500 dark:text-gray-500 mb-1">Duration</p>
                  <p style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '13px', fontWeight: 500 }} className="text-gray-800 dark:text-gray-200">{session.duration}</p>
                </div>
                <div>
                  <p style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px', fontWeight: 500 }} className="text-gray-500 dark:text-gray-500 mb-1">Session Mood</p>
                  {/* Use numeric mood score if available, otherwise fall back to categorical mood */}
                  {session.mood_score !== undefined && session.mood_score !== null ? (
                    <div className="flex items-center gap-2">
                      {/* Custom emoji based on numeric score */}
                      {mounted && renderMoodEmoji(
                        mapNumericMoodToCategory(session.mood_score),
                        18,
                        isDark
                      )}
                      {/* Numeric score */}
                      <span style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '13px', fontWeight: 500 }} className="text-gray-800 dark:text-gray-200">
                        {formatMoodScore(session.mood_score)}
                      </span>
                    </div>
                  ) : (
                    <p style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '13px', fontWeight: 500 }} className="text-gray-800 dark:text-gray-200 flex items-center gap-2">
                      <span style={{ fontSize: '18px' }}>{moodEmoji}</span>
                      <span className="capitalize">{session.mood}</span>
                    </p>
                  )}
                </div>
              </div>
            </div>

            {/* Topics Discussed */}
            <div className="mb-6">
              <h4 style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }} className="text-gray-700 dark:text-gray-300 mb-3">
                Topics Discussed
              </h4>
              <ul className="space-y-2">
                {session.topics.map((topic, idx) => (
                  <li key={idx} style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '13px', fontWeight: 400 }} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#5AB9B4] dark:bg-[#a78bfa] mt-2 flex-shrink-0" />
                    <span>{topic}</span>
                  </li>
                ))}
              </ul>
            </div>


            {/* Strategy Used */}
            <div className="mb-6">
              <h4 style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }} className="text-gray-700 dark:text-gray-300 mb-3">
                Strategy Used
              </h4>

              {/* Technique Name */}
              <p style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '16px', fontWeight: 600 }} className="text-[#5AB9B4] dark:text-[#a78bfa] mb-2">
                {session.strategy || 'Not specified'}
              </p>

              {/* Technique Definition (NEW) */}
              {session.technique_definition && (
                <p style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }} className="text-gray-700 dark:text-gray-300 mt-2">
                  {session.technique_definition}
                </p>
              )}

              {/* Fallback for missing definition */}
              {!session.technique_definition && session.strategy && (
                <p style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6, fontStyle: 'italic' }} className="text-gray-500 dark:text-gray-500 mt-2">
                  Definition not available for this technique.
                </p>
              )}
            </div>

            {/* Action Items */}
            <div className="mb-6">
              <h4 style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }} className="text-gray-700 dark:text-gray-300 mb-3">
                Action Items
              </h4>
              <ul className="space-y-2">
                {session.actions.map((action, idx) => (
                  <li key={idx} style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '13px', fontWeight: 400 }} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
                    <span className="w-1.5 h-1.5 rounded-full bg-[#B8A5D6] dark:bg-[#c084fc] mt-2 flex-shrink-0" />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Patient Summary (AI-generated from Wave 1 analysis) */}
            {(session.summary || session.patientSummary) && (
              <div className="p-4 bg-[#5AB9B4]/5 dark:bg-[#a78bfa]/10 rounded-xl border border-[#5AB9B4]/20 dark:border-[#a78bfa]/30">
                <h4 style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }} className="text-[#5AB9B4] dark:text-[#a78bfa] mb-3">
                  Session Summary
                </h4>
                <p style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }} className="text-gray-700 dark:text-gray-300">
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
                    <h4 style={{ fontFamily: TYPOGRAPHY.sans, fontSize: '14px', fontWeight: 500 }} className="text-amber-900 dark:text-amber-400 mb-2">
                      {session.milestone.title}
                    </h4>
                    <p style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }} className="text-amber-800 dark:text-amber-300">
                      {session.milestone.description}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Analysis Section with Toggle */}
            {(session.prose_analysis || session.deep_analysis) && (
              <div className="mt-6">
                {/* Tab Toggle */}
                <TabToggle
                  activeView={analysisView}
                  onViewChange={setAnalysisView}
                  hasProse={!!session.prose_analysis}
                  hasStructured={!!session.deep_analysis}
                />

                {/* Prose View */}
                {analysisView === 'prose' && session.prose_analysis && (
                  <motion.div
                    key="prose"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                  >
                    <ProseAnalysisView
                      prose={session.prose_analysis}
                      generatedAt={session.prose_generated_at}
                      confidence={session.analysis_confidence || 0.8}
                    />
                  </motion.div>
                )}

                {/* Structured View */}
                {analysisView === 'structured' && session.deep_analysis && (
                  <motion.div
                    key="structured"
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.2 }}
                  >
                    <div className="p-4 bg-[#5AB9B4]/5 dark:bg-[#a78bfa]/10 rounded-xl border border-[#5AB9B4]/20 dark:border-[#a78bfa]/30">
                      <DeepAnalysisSection
                        analysis={session.deep_analysis}
                        confidence={session.analysis_confidence || 0.8}
                      />
                    </div>
                  </motion.div>
                )}

                {/* Fallback: No analysis available */}
                {analysisView === 'prose' && !session.prose_analysis && (
                  <div className="p-6 bg-gray-50 dark:bg-[#1a1625] rounded-xl border border-gray-200 dark:border-[#3d3548] text-center">
                    <p style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '14px', fontStyle: 'italic' }} className="text-gray-500 dark:text-gray-500">
                      Narrative analysis not yet available for this session.
                    </p>
                  </div>
                )}

                {analysisView === 'structured' && !session.deep_analysis && (
                  <div className="p-6 bg-gray-50 dark:bg-[#1a1625] rounded-xl border border-gray-200 dark:border-[#3d3548] text-center">
                    <p style={{ fontFamily: TYPOGRAPHY.serif, fontSize: '14px', fontStyle: 'italic' }} className="text-gray-500 dark:text-gray-500">
                      Structured analysis not yet available for this session.
                    </p>
                  </div>
                )}
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
