'use client';

/**
 * Notes/Goals panel - AI-generated therapy summary (PR #3: Dynamic Roadmap)
 * - Fetches real roadmap data from backend API
 * - Displays loading overlay when roadmap is being generated
 * - Shows session counter ("Based on X out of Y sessions")
 * - Compact state: Preview with key achievements
 * - Expanded modal: Flat display with all sections visible
 * - Spring animation on expansion
 * - Dark mode support + gray border on modal
 * - Accessibility - focus trap, Escape key, focus restoration
 */

import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';
import { modalVariants, backdropVariants } from '../lib/utils';
import { useModalAccessibility } from '../hooks/useModalAccessibility';
import { useSessionData } from '../contexts/SessionDataContext';
import { LoadingOverlay } from './LoadingOverlay';
import { apiClient } from '@/lib/api-client';
import type { RoadmapData, RoadmapMetadata } from '@/lib/types';

// Font families - matching SessionCard
const fontSerif = '"Crimson Pro", Georgia, serif';
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

// Shared card styles for consistent appearance
const cardBaseClasses = "bg-gradient-to-br from-white to-[#FFF9F5] dark:from-[#2a2435] dark:to-[#1a1625] rounded-2xl p-6 shadow-lg h-[400px] overflow-hidden transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548]";

// Reusable bullet component for achievements, focus areas, and sections
interface BulletListProps {
  items: string[];
  bulletSize?: 'small' | 'medium';
}

function BulletList({ items, bulletSize = 'small' }: BulletListProps): React.ReactElement {
  const sizeClasses = bulletSize === 'small' ? 'w-1.5 h-1.5' : 'w-2 h-2';

  return (
    <ul className="space-y-2">
      {items.map((item, idx) => (
        <li key={idx} style={{ fontFamily: fontSerif, fontSize: '13px', fontWeight: 300, lineHeight: 1.5 }} className="flex items-start gap-2 text-gray-700 dark:text-gray-300">
          <span className={`${sizeClasses} rounded-full bg-[#5AB9B4] dark:bg-[#a78bfa] mt-1.5 flex-shrink-0`} />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}

// Split section content into bullet points
function splitIntoBullets(content: string): string[] {
  return content
    .split('. ')
    .map(s => s.trim())
    .filter(s => s.length > 0)
    .map(s => s.endsWith('.') ? s : s + '.');
}

// Generate session counter text
function getSessionCounterText(sessionsAnalyzed: number, totalSessions: number): string {
  const plural = totalSessions !== 1 ? 's' : '';
  return `Based on ${sessionsAnalyzed} out of ${totalSessions} uploaded session${plural}`;
}

export function NotesGoalsCard() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [roadmapData, setRoadmapData] = useState<RoadmapData | null>(null);
  const [metadata, setMetadata] = useState<RoadmapMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const modalRef = useRef<HTMLDivElement>(null);

  const { patientId, loadingRoadmap, roadmapRefreshTrigger } = useSessionData();

  // Fetch roadmap data on mount, when patientId changes, OR when roadmapRefreshTrigger increments
  useEffect(() => {
    if (!patientId) return;

    // Capture non-null patientId for async closure
    const currentPatientId = patientId;

    async function fetchRoadmap(): Promise<void> {
      setIsLoading(true);
      const result = await apiClient.getRoadmap(currentPatientId);

      if (!result.success) {
        setError(result.error || 'Failed to load roadmap');
        setIsLoading(false);
        return;
      }

      // Success - either with data or null (no roadmap yet)
      setRoadmapData(result.data?.roadmap ?? null);
      setMetadata(result.data?.metadata ?? null);
      setError(null);
      setIsLoading(false);
    }

    fetchRoadmap();
  }, [patientId, roadmapRefreshTrigger]);

  // Accessibility hook
  useModalAccessibility({
    isOpen: isExpanded,
    onClose: () => setIsExpanded(false),
    modalRef,
  });

  // Show loading state if initial load or roadmap being generated
  if (isLoading || loadingRoadmap) {
    return (
      <div className={`relative ${cardBaseClasses}`}>
        <LoadingOverlay visible={true} />
        <div className="flex flex-col items-center justify-center h-full">
          <h2 style={{ fontFamily: fontSerif, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200 mb-4">
            Your Journey
          </h2>
          <p style={{ fontFamily: fontSerif, fontSize: '14px' }} className="text-gray-600 dark:text-gray-400">
            {isLoading ? 'Loading roadmap...' : 'Generating roadmap...'}
          </p>
        </div>
      </div>
    );
  }

  // Show error state if fetch failed
  if (error) {
    return (
      <div className={cardBaseClasses}>
        <div className="flex flex-col items-center justify-center h-full">
          <h2 style={{ fontFamily: fontSerif, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200 mb-4">
            Your Journey
          </h2>
          <p style={{ fontFamily: fontSerif, fontSize: '14px' }} className="text-red-600 dark:text-red-400">
            {error}
          </p>
        </div>
      </div>
    );
  }

  // Show empty state if no roadmap yet (0 sessions analyzed)
  if (!roadmapData || !metadata) {
    return (
      <div className={cardBaseClasses}>
        <div className="flex flex-col items-center justify-center h-full text-center">
          <h2 style={{ fontFamily: fontSerif, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200 mb-4">
            Your Journey
          </h2>
          <p style={{ fontFamily: fontSerif, fontSize: '14px' }} className="text-gray-600 dark:text-gray-400 mb-2">
            Upload therapy sessions to generate your personalized journey roadmap
          </p>
          <p style={{ fontFamily: fontSans, fontSize: '12px' }} className="text-gray-500 dark:text-gray-500">
            Your roadmap will appear here after your first session is analyzed
          </p>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Compact Card */}
      <motion.div
        onClick={() => setIsExpanded(true)}
        className="bg-gradient-to-br from-white to-[#FFF9F5] dark:from-[#2a2435] dark:to-[#1a1625] rounded-2xl p-6 shadow-lg cursor-pointer h-[400px] overflow-hidden transition-colors duration-300 border border-gray-200/50 dark:border-[#3d3548]"
        whileHover={{ scale: 1.01, boxShadow: '0 4px 16px rgba(0,0,0,0.12)' }}
        transition={{ duration: 0.2 }}
      >
        <div className="flex flex-col mb-5 text-center">
          <h2 style={{ fontFamily: fontSerif, fontSize: '20px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200">Your Journey</h2>
          {/* Session Counter */}
          <p style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500 }} className="text-gray-500 dark:text-gray-500 mt-1">
            {getSessionCounterText(metadata.sessions_analyzed, metadata.total_sessions)}
          </p>
        </div>

        <p style={{ fontFamily: fontSerif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6, color: 'var(--text-gray-600)' }} className="dark:text-gray-400 mb-5">{roadmapData.summary}</p>

        <BulletList items={roadmapData.achievements.slice(0, 3)} />

        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-[#3d3548]">
          <p style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }} className="text-gray-500 dark:text-gray-500 mb-2">Current focus:</p>
          <BulletList items={roadmapData.currentFocus.slice(0, 3)} />
        </div>
      </motion.div>

      {/* Expanded Modal */}
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
              <h2 style={{ fontFamily: fontSerif, fontSize: '24px', fontWeight: 600 }} className="text-gray-800 dark:text-gray-200 mb-2 pr-12 text-center">
                Your Journey
              </h2>

              {/* Session Counter in Modal */}
              <p style={{ fontFamily: fontSans, fontSize: '12px', fontWeight: 500 }} className="text-gray-500 dark:text-gray-500 mb-6 text-center">
                {getSessionCounterText(metadata.sessions_analyzed, metadata.total_sessions)}
              </p>

              <p style={{ fontFamily: fontSerif, fontSize: '14px', fontWeight: 400, lineHeight: 1.6 }} className="text-gray-700 dark:text-gray-300 mb-8">
                {roadmapData.summary}
              </p>

              <div className="mb-6">
                <h3 style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }} className="text-gray-600 dark:text-gray-400 mb-3">
                  Key Achievements
                </h3>
                <BulletList items={roadmapData.achievements} bulletSize="medium" />
              </div>

              <div className="mb-6">
                <h3 style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }} className="text-gray-600 dark:text-gray-400 mb-3">
                  Current Focus Areas
                </h3>
                <BulletList items={roadmapData.currentFocus} bulletSize="medium" />
              </div>

              {/* Additional Sections - Flat Display with Bullets */}
              {roadmapData.sections.map((section, idx) => (
                <div key={idx} className="mb-6">
                  <h3 style={{ fontFamily: fontSans, fontSize: '11px', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '1px' }} className="text-gray-600 dark:text-gray-400 mb-3">
                    {section.title}
                  </h3>
                  <BulletList items={splitIntoBullets(section.content)} bulletSize="medium" />
                </div>
              ))}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
