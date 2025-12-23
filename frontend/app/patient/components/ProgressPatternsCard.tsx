'use client';

/**
 * Progress Patterns Card - Premium Data Visualization
 * - Compact state: Carousel with 4 metric pages
 * - Expanded modal: Centered modal with collapsible sections for all 4 metrics
 * - FIXED: Dark mode support + gray border on modal
 * - FIXED: Accessibility - focus trap, Escape key, focus restoration
 * - ENHANCED: Real-time consistency data from backend API
 */

import { useState, useRef, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, TrendingUp, Activity, Calendar, Target } from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, CartesianGrid
} from 'recharts';
import { progressMetrics } from '../lib/mockData';
import { modalVariants, backdropVariants } from '../lib/utils';
import { useModalAccessibility } from '../hooks/useModalAccessibility';
import { useConsistencyData } from '../hooks/useConsistencyData';
import { useMoodAnalysis } from '../hooks/useMoodAnalysis';
import { useTheme } from '../contexts/ThemeContext';
import type { ProgressMetric } from '../lib/types';

// Font families - matching SessionCard
const fontSerif = '"Crimson Pro", Georgia, serif';
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

// Icons mapping
const iconMap: Record<string, React.ComponentType<{ size?: number }>> = {
  '📈': TrendingUp,
  '📊': Activity,
  '📅': Calendar,
  '🎯': Target
};

const COLORS = {
  primary: '#5AB9B4',
  secondary: '#B8A5D6',
  accent: '#F4A69D',
  success: '#A8C69F',
  textDark: '#1F2937',
  textMuted: '#6B7280',
};

interface ProgressPatternsCardProps {
  patientId?: string;
  useRealData?: boolean;
}

// CONFIGURATION: Add/remove metric titles here to control which metrics are displayed
// Pagination will automatically adjust based on the number of metrics in this array
const DISPLAYED_METRICS = [
  'Mood Trends',
  'Session Consistency',
  // Add more metric titles here as needed (e.g., 'Homework Impact', 'Strategy Effectiveness')
];

export function ProgressPatternsCard({ patientId, useRealData = false }: ProgressPatternsCardProps) {
  const { isDark } = useTheme();
  const [isExpanded, setIsExpanded] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  // Track which page is shown in the modal (0 = Mood Trends, 1 = Session Consistency)
  const [modalPageIndex, setModalPageIndex] = useState(0);
  const modalRef = useRef<HTMLDivElement>(null);

  // Swipe gesture support for compact card
  const compactSwipeRef = useRef<HTMLDivElement>(null);
  const compactSwipeAccumulator = useRef(0);
  const swipeThreshold = 50; // pixels to trigger page change

  // Swipe gesture support for modal
  const modalSwipeRef = useRef<HTMLDivElement>(null);
  const modalSwipeAccumulator = useRef(0);

  // Fetch real consistency data if enabled
  const { data: consistencyData, isLoading } = useConsistencyData(
    patientId || '',
    90,
    useRealData && !!patientId
  );

  // Fetch real mood data if enabled
  const { moodHistory, trend: moodTrend, isLoading: isMoodLoading } = useMoodAnalysis({
    patientId: patientId || '',
    limit: 50,
  });

  // Merge real consistency and mood data with mock metrics
  // Filter to only show metrics defined in DISPLAYED_METRICS configuration
  const mergedMetrics = useMemo<ProgressMetric[]>(() => {
    // Dynamically filter progressMetrics based on DISPLAYED_METRICS array
    const filteredMetrics = progressMetrics.filter(
      metric => DISPLAYED_METRICS.includes(metric.title)
    );

    if (!useRealData || (!consistencyData && !moodHistory.length)) {
      return filteredMetrics;
    }

    return filteredMetrics.map(metric => {
      // Update Session Consistency metric
      if (metric.title === 'Session Consistency' && consistencyData) {
        const score = consistencyData.consistency_score;
        let scoreText = 'Excellent';

        if (score < 60) {
          scoreText = 'Needs improvement';
        } else if (score < 80) {
          scoreText = 'Good';
        }

        return {
          ...metric,
          chartData: consistencyData.weekly_data,
          insight: `${consistencyData.attendance_rate.toFixed(0)}% attendance rate - ${scoreText} (Score: ${score}/100). ${consistencyData.longest_streak_weeks} week streak, avg ${consistencyData.average_gap_days.toFixed(1)} days between sessions.`,
        };
      }

      // Update Mood Trends metric with real AI-analyzed mood data
      if (metric.title === 'Mood Trends' && moodHistory.length > 0) {
        // Transform mood history to chart data format
        const chartData = moodHistory.map((point, idx) => ({
          session: `S${idx + 1}`,
          mood: point.mood_score,
          date: new Date(point.session_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        }));

        // Calculate mood improvement
        const firstMood = moodHistory[0].mood_score;
        const lastMood = moodHistory[moodHistory.length - 1].mood_score;
        const improvement = ((lastMood - firstMood) / firstMood) * 100;
        const improvementSign = improvement > 0 ? '+' : '';

        // Build insight with trend information
        let insight = `${improvementSign}${improvement.toFixed(0)}% mood change over ${moodHistory.length} sessions`;

        if (moodTrend) {
          const trendEmoji = {
            improving: '📈',
            declining: '📉',
            stable: '➡️',
            variable: '↕️',
          }[moodTrend.direction];

          insight = `${trendEmoji} ${moodTrend.direction.replace('_', ' ').toUpperCase()}: ${improvementSign}${improvement.toFixed(0)}% overall (Recent avg: ${moodTrend.recent_avg.toFixed(1)}/10, Historical: ${moodTrend.historical_avg.toFixed(1)}/10)`;
        }

        return {
          ...metric,
          chartData,
          insight,
        };
      }

      return metric;
    });
  }, [useRealData, consistencyData, moodHistory, moodTrend]);

  // Accessibility: focus trap, Escape key, scroll lock
  useModalAccessibility({
    isOpen: isExpanded,
    onClose: () => setIsExpanded(false),
    modalRef,
  });

  // Swipe gesture for compact card carousel
  useEffect(() => {
    const element = compactSwipeRef.current;
    if (!element || mergedMetrics.length <= 1) return;

    const handleWheel = (e: WheelEvent) => {
      // Only handle horizontal scroll (trackpad two-finger swipe)
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
        e.preventDefault();
        compactSwipeAccumulator.current += e.deltaX;

        if (compactSwipeAccumulator.current > swipeThreshold) {
          // Swipe left = next page
          setCurrentIndex(prev => Math.min(prev + 1, mergedMetrics.length - 1));
          compactSwipeAccumulator.current = 0;
        } else if (compactSwipeAccumulator.current < -swipeThreshold) {
          // Swipe right = previous page
          setCurrentIndex(prev => Math.max(prev - 1, 0));
          compactSwipeAccumulator.current = 0;
        }
      }
    };

    element.addEventListener('wheel', handleWheel, { passive: false });
    return () => element.removeEventListener('wheel', handleWheel);
  }, [mergedMetrics.length]);

  // Swipe gesture for modal pagination
  useEffect(() => {
    const element = modalSwipeRef.current;
    if (!element || mergedMetrics.length <= 1 || !isExpanded) return;

    const handleWheel = (e: WheelEvent) => {
      // Only handle horizontal scroll (trackpad two-finger swipe)
      if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) {
        e.preventDefault();
        modalSwipeAccumulator.current += e.deltaX;

        if (modalSwipeAccumulator.current > swipeThreshold) {
          // Swipe left = next page
          setModalPageIndex(prev => Math.min(prev + 1, mergedMetrics.length - 1));
          modalSwipeAccumulator.current = 0;
        } else if (modalSwipeAccumulator.current < -swipeThreshold) {
          // Swipe right = previous page
          setModalPageIndex(prev => Math.max(prev - 1, 0));
          modalSwipeAccumulator.current = 0;
        }
      }
    };

    element.addEventListener('wheel', handleWheel, { passive: false });
    return () => element.removeEventListener('wheel', handleWheel);
  }, [mergedMetrics.length, isExpanded]);

  const currentMetric = mergedMetrics[currentIndex];
  const CurrentIcon = iconMap[currentMetric.emoji] || TrendingUp;

  // Custom Chart Components
  const renderChart = (metric: typeof currentMetric, isCompact: boolean, theme: boolean = isDark) => {
    const height = isCompact ? 110 : 250;
    const showGrid = !isCompact;
    const fontSize = isCompact ? 10 : 12;

    if (metric.title === 'Mood Trends') {
      return (
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={metric.chartData}>
            <defs>
              <linearGradient id="colorMood" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.4}/>
                <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0.05}/>
              </linearGradient>
            </defs>
            {showGrid && <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />}
            <XAxis
              dataKey="session"
              hide={isCompact}
              tick={{ fontSize, fill: COLORS.textMuted }}
              axisLine={false}
              tickLine={false}
            />
            <YAxis hide domain={[0, 10]} />
            <Tooltip
              contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
              cursor={{ stroke: COLORS.primary, strokeWidth: 1, strokeDasharray: '4 4' }}
            />
            <Area
              type="monotone"
              dataKey="mood"
              stroke={COLORS.primary}
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorMood)"
            />
          </AreaChart>
        </ResponsiveContainer>
      );
    }

    if (metric.title === 'Session Consistency') {
      // Use teal in light mode, purple in dark mode
      const barColor = theme ? '#a78bfa' : '#5AB9B4';

      return (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={metric.chartData}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />}
            <XAxis
              dataKey="week"
              hide={isCompact}
              tick={{ fontSize, fill: COLORS.textMuted }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
            />
            <Bar
              dataKey="attended"
              fill={barColor}
              radius={[4, 4, 4, 4]}
              barSize={isCompact ? 8 : 20}
            />
          </BarChart>
        </ResponsiveContainer>
      );
    }

    return null;
  };

  return (
    <>
      {/* Compact Card */}
      <motion.div
        ref={compactSwipeRef}
        layoutId="progress-card"
        onClick={() => setIsExpanded(true)}
        className="relative overflow-hidden rounded-[24px] border border-white/50 dark:border-[#4d4558] shadow-xl h-[280px] bg-gradient-to-br from-white/30 to-white/15 dark:from-[#322940] dark:to-[#221c2e] cursor-pointer"
        style={{
          backdropFilter: 'blur(20px)',
          boxShadow: '0 4px 6px rgba(0,0,0,0.05), 0 10px 20px rgba(0,0,0,0.10), 0 25px 50px rgba(90,185,180,0.20)'
        }}
        whileHover={{ scale: 1.01 }}
        transition={{ duration: 0.3 }}
      >
        {/* Dynamic Gradient Background Layer */}
        <div className="absolute inset-0 opacity-10 pointer-events-none dark:opacity-20"
          style={{
            background: 'linear-gradient(135deg, #5AB9B4 0%, #B8A5D6 50%, #F4A69D 100%)'
          }}
        />

        {/* Content Container */}
        <div className="relative z-10 p-5 flex flex-col h-full">
          {/* Header */}
          <div className="flex flex-col mb-3 flex-shrink-0 text-center">
            <h3 style={{ fontFamily: fontSans }} className="text-sm font-semibold text-gray-800 dark:text-gray-200 tracking-wide uppercase opacity-80">
              {currentMetric.title}
            </h3>
            <p style={{ fontFamily: fontSans }} className="text-xs text-gray-500 dark:text-gray-400">
              {currentMetric.description}
            </p>
          </div>

          {/* Chart Area */}
          <div className="flex-1 min-h-0 w-full mb-3">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentIndex}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3 }}
                className="h-full w-full"
              >
                {renderChart(currentMetric, true)}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Insight Pill */}
          <div className="mb-3 flex-shrink-0">
            <motion.div
              key={currentIndex}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white/40 dark:bg-white/5 border border-white/50 dark:border-white/10 rounded-lg p-2.5 backdrop-blur-sm"
            >
              <div className="flex items-center gap-2">
                <span className="text-base">{currentMetric.emoji}</span>
                <p style={{ fontFamily: fontSerif }} className="text-xs font-light text-gray-700 dark:text-gray-300 leading-snug">
                  {currentMetric.insight}
                </p>
              </div>
            </motion.div>
          </div>

          {/* Navigation Controls - Dots pagination like sessions page */}
          <div className="flex items-center justify-center flex-shrink-0">
            <div className="flex gap-3">
              {mergedMetrics.map((_, idx) => (
                <button
                  key={idx}
                  onClick={(e) => {
                    e.stopPropagation();
                    setCurrentIndex(idx);
                  }}
                  aria-label={`Go to ${mergedMetrics[idx].title}`}
                  className="w-6 h-2 flex items-center justify-center"
                >
                  <span
                    className={`transition-all duration-300 rounded-full h-2 ${
                      idx === currentIndex
                        ? 'bg-[#5AB9B4] dark:bg-[#a78bfa] w-6'
                        : 'bg-white/40 dark:bg-white/20 hover:bg-white/60 dark:hover:bg-white/30 w-2'
                    }`}
                  />
                </button>
              ))}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Expanded Modal - Centered with collapsible sections */}
      <AnimatePresence>
        {isExpanded && (
          <>
            <motion.div
              variants={backdropVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="fixed inset-0 bg-black/30 backdrop-blur-sm z-[1000]"
              onClick={() => setIsExpanded(false)}
            />
            <motion.div
              ref={modalRef}
              variants={modalVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="fixed w-[800px] max-h-[85vh] bg-[#F8F7F4] dark:bg-[#2a2435] rounded-3xl shadow-2xl p-8 z-[1001] overflow-y-auto border-2 border-[#E0DDD8] dark:border-gray-600"
              style={{
                top: '50%',
                left: '50%'
              }}
              role="dialog"
              aria-modal="true"
              aria-labelledby="progress-patterns-title"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Close Button - Must be above all content */}
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  setIsExpanded(false);
                }}
                onMouseDown={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                }}
                className="absolute top-6 right-6 w-11 h-11 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors z-[9999] cursor-pointer"
                aria-label="Close modal"
                style={{ pointerEvents: 'auto' }}
              >
                <X className="w-6 h-6 text-gray-600 dark:text-gray-400" />
              </button>

              {/* Dynamic title based on current page */}
              <h2 id="progress-patterns-title" style={{ fontFamily: fontSans }} className="text-sm font-semibold text-gray-800 dark:text-gray-200 tracking-wide uppercase opacity-80 mb-6 text-center">
                {mergedMetrics[modalPageIndex]?.title || 'Progress Patterns'}
              </h2>

              {/* Paginated Content */}
              <AnimatePresence mode="wait">
                {(() => {
                  // Use mergedMetrics directly (already filtered by DISPLAYED_METRICS)
                  const currentMetric = mergedMetrics[modalPageIndex];
                  const Icon = iconMap[currentMetric.emoji] || TrendingUp;

                  return (
                    <motion.div
                      ref={modalSwipeRef}
                      key={modalPageIndex}
                      initial={{ opacity: 0, x: 20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -20 }}
                      transition={{ duration: 0.3 }}
                    >
                      {/* Metric Header */}
                      <div className="flex items-center gap-3 mb-6">
                        <div className="p-2 rounded-lg bg-[#5AB9B4]/10 dark:bg-[#a78bfa]/20 text-[#5AB9B4] dark:text-[#a78bfa]">
                          <Icon size={24} />
                        </div>
                        <div>
                          <p style={{ fontFamily: fontSans }} className="text-sm font-light text-gray-500 dark:text-gray-400">
                            {currentMetric.description}
                          </p>
                        </div>
                      </div>

                      {/* Chart Container */}
                      <div className="bg-gray-50 dark:bg-[#1a1625] rounded-xl p-6 mb-6">
                        {renderChart(currentMetric, false)}
                      </div>

                      {/* Insight Box */}
                      <div className="bg-gradient-to-br from-[#5AB9B4]/10 to-[#B8A5D6]/10 dark:from-[#a78bfa]/20 dark:to-[#c084fc]/20 rounded-xl p-5 border border-[#5AB9B4]/20 dark:border-[#a78bfa]/30">
                        <h4 style={{ fontFamily: fontSans }} className="text-[#5AB9B4] dark:text-[#a78bfa] font-semibold uppercase tracking-wider text-xs mb-2">
                          Key Insight
                        </h4>
                        <p style={{ fontFamily: fontSerif }} className="text-gray-700 dark:text-gray-300 text-sm font-light">
                          {currentMetric.insight}
                        </p>
                      </div>

                      {/* Navigation Controls - Dots pagination like sessions page */}
                      <div className="flex justify-center gap-3 mt-8">
                        {mergedMetrics.map((metric, idx) => (
                          <button
                            key={idx}
                            onClick={() => setModalPageIndex(idx)}
                            aria-label={`Go to ${metric.title}`}
                            className="w-6 h-2 flex items-center justify-center"
                          >
                            <span
                              className={`transition-all duration-300 rounded-full h-2 ${
                                idx === modalPageIndex
                                  ? 'bg-[#5AB9B4] dark:bg-[#a78bfa] w-6'
                                  : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500 w-2'
                              }`}
                            />
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  );
                })()}
              </AnimatePresence>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
