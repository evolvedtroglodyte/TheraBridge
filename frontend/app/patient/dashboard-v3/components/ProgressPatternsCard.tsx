'use client';

/**
 * Progress Patterns Card - Premium Data Visualization
 * - Compact state: Carousel with 4 metric pages
 * - Expanded modal: All 4 metrics with interactive charts
 * - FIXED: Dark mode support + gray border on modal
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronLeft, ChevronRight, Maximize2, TrendingUp, Activity, Calendar, Target } from 'lucide-react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  AreaChart, Area, CartesianGrid
} from 'recharts';
import { progressMetrics } from '../lib/mockData';
import { modalVariants, backdropVariants } from '../lib/utils';

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
              background={{ fill: 'rgba(0,0,0,0.05)', radius: [0, 4, 4, 0] }}
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
        className="relative overflow-hidden rounded-[24px] border border-white/40 dark:border-[#3d3548] shadow-xl h-[280px] bg-gradient-to-br from-white/20 to-white/10 dark:from-[#2a2435] dark:to-[#1a1625]"
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
          <div className="flex justify-between items-start mb-3 flex-shrink-0">
            <div className="flex items-center gap-2.5">
              <div className="p-2 rounded-xl bg-white/40 dark:bg-white/10 shadow-sm border border-white/50 dark:border-white/20 text-[#5AB9B4] dark:text-[#a78bfa]">
                <CurrentIcon size={18} />
              </div>
              <div>
                <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200 tracking-wide uppercase font-mono opacity-80">
                  {currentMetric.title}
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 font-medium mt-0.5">
                  {currentMetric.description}
                </p>
              </div>
            </div>
            <button
              onClick={() => setIsExpanded(true)}
              className="p-1.5 rounded-full hover:bg-white/30 dark:hover:bg-white/10 text-gray-500 dark:text-gray-400 transition-colors flex-shrink-0"
              aria-label="Expand view"
            >
              <Maximize2 size={15} />
            </button>
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
                <p className="text-xs font-medium text-gray-700 dark:text-gray-300 leading-snug">
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
                  onClick={() => setCurrentIndex(idx)}
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
                onClick={prevSlide}
                className="w-7 h-7 flex items-center justify-center rounded-full bg-white/30 dark:bg-white/10 hover:bg-white/60 dark:hover:bg-white/20 text-gray-600 dark:text-gray-300 transition-colors border border-white/40 dark:border-white/20"
              >
                <ChevronLeft size={14} />
              </button>
              <button
                onClick={nextSlide}
                className="w-7 h-7 flex items-center justify-center rounded-full bg-white/30 dark:bg-white/10 hover:bg-white/60 dark:hover:bg-white/20 text-gray-600 dark:text-gray-300 transition-colors border border-white/40 dark:border-white/20"
              >
                <ChevronRight size={14} />
              </button>
            </div>
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
              className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
              onClick={() => setIsExpanded(false)}
            />
            <motion.div
              layoutId="progress-card"
              className="fixed inset-4 md:inset-10 z-50 bg-[#F7F5F3] dark:bg-[#1a1625] rounded-[32px] overflow-hidden shadow-2xl flex flex-col md:flex-row border-2 border-gray-300 dark:border-gray-600"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            >
              {/* Sidebar / Navigation List */}
              <div className="w-full md:w-80 bg-white dark:bg-[#2a2435] border-r border-gray-100 dark:border-[#3d3548] p-6 flex flex-col overflow-y-auto">
                <div className="flex items-center justify-between mb-8">
                  <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200 tracking-tight font-mono">
                    Progress<br/>Patterns
                  </h2>
                  <button
                    onClick={() => setIsExpanded(false)}
                    className="md:hidden p-2 bg-gray-100 dark:bg-[#3d3548] rounded-full"
                  >
                    <X size={20} className="dark:text-gray-200" />
                  </button>
                </div>

                <div className="space-y-3">
                  {progressMetrics.map((metric, idx) => {
                    const Icon = iconMap[metric.emoji] || TrendingUp;
                    const isActive = idx === currentIndex;
                    return (
                      <button
                        key={idx}
                        onClick={() => setCurrentIndex(idx)}
                        className={`
                          w-full text-left p-4 rounded-xl transition-all duration-200 flex items-start gap-3
                          ${isActive
                            ? 'bg-gradient-to-r from-[#5AB9B4]/10 to-[#B8A5D6]/10 dark:from-[#a78bfa]/20 dark:to-[#c084fc]/20 border border-[#5AB9B4]/20 dark:border-[#a78bfa]/30 shadow-sm'
                            : 'hover:bg-gray-50 dark:hover:bg-[#3d3548] border border-transparent'
                          }
                        `}
                      >
                        <div className={`
                          p-2 rounded-lg shrink-0
                          ${isActive ? 'bg-[#5AB9B4] dark:bg-[#a78bfa] text-white' : 'bg-gray-100 dark:bg-[#3d3548] text-gray-500 dark:text-gray-400'}
                        `}>
                          <Icon size={18} />
                        </div>
                        <div>
                          <h4 className={`font-semibold text-sm ${isActive ? 'text-gray-900 dark:text-gray-100' : 'text-gray-600 dark:text-gray-400'}`}>
                            {metric.title}
                          </h4>
                          <p className="text-xs text-gray-500 dark:text-gray-500 mt-0.5 line-clamp-1">
                            {metric.description}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Main Content Area */}
              <div className="flex-1 bg-gradient-to-br from-[#F7F5F3] to-white dark:from-[#1a1625] dark:to-[#2a2435] p-6 md:p-10 overflow-y-auto relative">
                <button
                  onClick={() => setIsExpanded(false)}
                  className="absolute top-6 right-6 p-2 rounded-full hover:bg-gray-100 dark:hover:bg-[#3d3548] text-gray-400 dark:text-gray-500 hover:text-gray-600 dark:hover:text-gray-300 transition-colors hidden md:block"
                >
                  <X size={24} />
                </button>

                <motion.div
                  key={currentIndex}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4 }}
                  className="max-w-4xl mx-auto"
                >
                  <div className="mb-8">
                    <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#5AB9B4]/10 dark:bg-[#a78bfa]/20 text-[#5AB9B4] dark:text-[#a78bfa] text-xs font-semibold uppercase tracking-wider mb-3">
                      {currentMetric.emoji} Analysis
                    </span>
                    <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                      {currentMetric.title}
                    </h2>
                    <p className="text-lg text-gray-500 dark:text-gray-400">
                      {currentMetric.description}
                    </p>
                  </div>

                  {/* Chart Container */}
                  <div className="bg-white dark:bg-[#2a2435] rounded-[24px] p-6 md:p-8 shadow-sm border border-gray-100 dark:border-[#3d3548] mb-8">
                    {renderChart(currentMetric, false)}
                  </div>

                  {/* Insight Box */}
                  <div className="bg-gradient-to-br from-[#5AB9B4]/10 to-[#B8A5D6]/10 dark:from-[#a78bfa]/20 dark:to-[#c084fc]/20 rounded-2xl p-6 border border-[#5AB9B4]/20 dark:border-[#a78bfa]/30">
                    <h3 className="text-[#5AB9B4] dark:text-[#a78bfa] font-semibold uppercase tracking-wider text-xs mb-2">
                      Key Insight
                    </h3>
                    <p className="text-gray-800 dark:text-gray-200 text-lg font-medium">
                      {currentMetric.insight}
                    </p>
                  </div>
                </motion.div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
