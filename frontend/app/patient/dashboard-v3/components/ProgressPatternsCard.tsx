'use client';

/**
 * Progress Patterns Card - Premium Data Visualization
 * - Compact state: Carousel with 4 metric pages
 * - Expanded modal: Centered modal with collapsible sections for all 4 metrics
 * - FIXED: Dark mode support + gray border on modal
 * - FIXED: Accessibility - focus trap, Escape key, focus restoration
 */

import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronLeft, ChevronRight, ChevronDown, TrendingUp, Activity, Calendar, Target } from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, CartesianGrid
} from 'recharts';
import { progressMetrics } from '../lib/mockData';
import { modalVariants, backdropVariants } from '../lib/utils';
import { useModalAccessibility } from '../hooks/useModalAccessibility';

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

export function ProgressPatternsCard() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  // Track which sections are expanded in the modal (first one open by default)
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set([0]));
  const modalRef = useRef<HTMLDivElement>(null);

  const toggleSection = (index: number) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  // Accessibility: focus trap, Escape key, scroll lock
  useModalAccessibility({
    isOpen: isExpanded,
    onClose: () => setIsExpanded(false),
    modalRef,
  });

  const nextSlide = () => {
    setCurrentIndex((prev) => (prev + 1) % progressMetrics.length);
  };

  const prevSlide = () => {
    setCurrentIndex((prev) => (prev - 1 + progressMetrics.length) % progressMetrics.length);
  };

  const currentMetric = progressMetrics[currentIndex];
  const CurrentIcon = iconMap[currentMetric.emoji] || TrendingUp;

  // Custom Chart Components
  const renderChart = (metric: typeof currentMetric, isCompact: boolean) => {
    const height = isCompact ? 110 : 250;
    const showGrid = !isCompact;
    const fontSize = isCompact ? 10 : 12;

    if (metric.title === 'Mood Trend') {
      return (
        <ResponsiveContainer width="100%" height={height}>
          <AreaChart data={metric.chartData}>
            <defs>
              <linearGradient id="colorMood" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0}/>
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

    if (metric.title === 'Homework Impact') {
      return (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={metric.chartData} barGap={isCompact ? 2 : 4}>
            {showGrid && <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(0,0,0,0.05)" />}
            <XAxis
              dataKey="week"
              hide={isCompact}
              tick={{ fontSize, fill: COLORS.textMuted }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: 'rgba(0,0,0,0.02)' }}
              contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
            />
            <Bar dataKey="completion" fill={COLORS.secondary} radius={[4, 4, 0, 0]} name="Completion %" />
            <Bar dataKey="mood" fill={COLORS.accent} radius={[4, 4, 0, 0]} name="Mood Rating" />
          </BarChart>
        </ResponsiveContainer>
      );
    }

    if (metric.title === 'Session Consistency') {
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
              fill={COLORS.success}
              radius={[4, 4, 4, 4]}
              barSize={isCompact ? 8 : 20}
            />
          </BarChart>
        </ResponsiveContainer>
      );
    }

    if (metric.title === 'Strategy Effectiveness') {
      return (
        <ResponsiveContainer width="100%" height={height}>
          <BarChart data={metric.chartData} layout="vertical" margin={{ left: isCompact ? 0 : 40 }}>
            <XAxis type="number" hide />
            <YAxis
              dataKey="strategy"
              type="category"
              hide={isCompact}
              tick={{ fontSize, fill: COLORS.textMuted }}
              width={100}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
            />
            <Bar
              dataKey="effectiveness"
              fill={COLORS.primary}
              radius={[0, 4, 4, 0]}
              barSize={isCompact ? 12 : 24}
              background={{ fill: 'rgba(0,0,0,0.05)' }}
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
        layoutId="progress-card"
        onClick={() => setIsExpanded(true)}
        className="relative overflow-hidden rounded-[24px] border border-white/40 dark:border-[#3d3548] shadow-xl h-[280px] bg-gradient-to-br from-white/20 to-white/10 dark:from-[#2a2435] dark:to-[#1a1625] cursor-pointer"
        style={{
          backdropFilter: 'blur(20px)',
          boxShadow: '0 4px 6px rgba(0,0,0,0.05), 0 10px 20px rgba(0,0,0,0.08), 0 25px 50px rgba(90,185,180,0.15)'
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
          <div className="flex flex-col items-center mb-3 flex-shrink-0">
            <h3 className="text-lg font-light text-gray-800 dark:text-gray-200 text-center mb-1">
              {currentMetric.title}
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 font-light text-center">
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
                <p className="text-xs font-light text-gray-700 dark:text-gray-300 leading-snug">
                  {currentMetric.insight}
                </p>
              </div>
            </motion.div>
          </div>

          {/* Navigation Controls */}
          <div className="flex items-center justify-between flex-shrink-0">
            <div className="flex gap-1.5">
              {progressMetrics.map((_, idx) => (
                <button
                  key={idx}
                  onClick={(e) => { e.stopPropagation(); setCurrentIndex(idx); }}
                  className={`
                    transition-all duration-300 rounded-full
                    ${idx === currentIndex ? 'w-6 h-1.5 bg-[#5AB9B4] dark:bg-[#a78bfa]' : 'w-1.5 h-1.5 bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500'}
                  `}
                  aria-label={`Go to slide ${idx + 1}`}
                />
              ))}
            </div>

            <div className="flex gap-2">
              <button
                onClick={(e) => { e.stopPropagation(); prevSlide(); }}
                className="w-7 h-7 flex items-center justify-center rounded-full bg-white/30 dark:bg-white/10 hover:bg-white/60 dark:hover:bg-white/20 text-gray-600 dark:text-gray-300 transition-colors border border-white/40 dark:border-white/20"
              >
                <ChevronLeft size={14} />
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); nextSlide(); }}
                className="w-7 h-7 flex items-center justify-center rounded-full bg-white/30 dark:bg-white/10 hover:bg-white/60 dark:hover:bg-white/20 text-gray-600 dark:text-gray-300 transition-colors border border-white/40 dark:border-white/20"
              >
                <ChevronRight size={14} />
              </button>
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
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h2 id="progress-patterns-title" className="text-2xl font-light text-gray-800 dark:text-gray-200">
                  Progress Patterns
                </h2>
                <button
                  onClick={() => setIsExpanded(false)}
                  className="w-11 h-11 flex items-center justify-center rounded-full hover:bg-gray-100 dark:hover:bg-[#3d3548] transition-colors"
                >
                  <X className="w-6 h-6 text-gray-600 dark:text-gray-400" />
                </button>
              </div>

              {/* Collapsible Metric Sections */}
              <div className="space-y-4">
                {progressMetrics.map((metric, idx) => {
                  const Icon = iconMap[metric.emoji] || TrendingUp;
                  const isOpen = expandedSections.has(idx);

                  return (
                    <div
                      key={idx}
                      className="border border-gray-200 dark:border-[#3d3548] rounded-2xl overflow-hidden"
                    >
                      {/* Section Header */}
                      <button
                        onClick={() => toggleSection(idx)}
                        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-[#3d3548]/50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-[#5AB9B4]/10 dark:bg-[#a78bfa]/20 text-[#5AB9B4] dark:text-[#a78bfa]">
                            <Icon size={20} />
                          </div>
                          <div className="text-left">
                            <h3 className="font-light text-gray-800 dark:text-gray-200">
                              {metric.title}
                            </h3>
                            <p className="text-sm font-light text-gray-500 dark:text-gray-400">
                              {metric.description}
                            </p>
                          </div>
                        </div>
                        <motion.div
                          animate={{ rotate: isOpen ? 180 : 0 }}
                          transition={{ duration: 0.2 }}
                        >
                          <ChevronDown className="w-5 h-5 text-gray-500 dark:text-gray-400" />
                        </motion.div>
                      </button>

                      {/* Section Content - Collapsible */}
                      <AnimatePresence initial={false}>
                        {isOpen && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.3, ease: 'easeInOut' }}
                            className="overflow-hidden"
                          >
                            <div className="px-4 pb-4">
                              {/* Chart Container */}
                              <div className="bg-gray-50 dark:bg-[#1a1625] rounded-xl p-4 mb-4">
                                {renderChart(metric, false)}
                              </div>

                              {/* Insight Box */}
                              <div className="bg-gradient-to-br from-[#5AB9B4]/10 to-[#B8A5D6]/10 dark:from-[#a78bfa]/20 dark:to-[#c084fc]/20 rounded-xl p-4 border border-[#5AB9B4]/20 dark:border-[#a78bfa]/30">
                                <h4 className="text-[#5AB9B4] dark:text-[#a78bfa] font-semibold uppercase tracking-wider text-xs mb-1">
                                  Key Insight
                                </h4>
                                <p className="text-gray-700 dark:text-gray-300 text-sm font-light">
                                  {metric.insight}
                                </p>
                              </div>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </div>
                  );
                })}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
