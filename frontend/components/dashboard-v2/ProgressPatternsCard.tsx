'use client';

import React, { useState, useCallback, useRef, useEffect } from 'react';
import { motion, AnimatePresence, PanInfo } from 'framer-motion';
import { TrendingUp, BarChart3, Calendar, Target, ChevronLeft, ChevronRight, ChevronDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ModalWrapper } from '@/components/dashboard-v2/shared';
import { progressPatternsData } from '@/lib/mock-data/dashboard-v2';

// ============================================================================
// Types
// ============================================================================

type CarouselPage = 'mood' | 'homework' | 'consistency' | 'strategy';

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  content: string;
}

// ============================================================================
// Animation Variants
// ============================================================================

const cardVariants = {
  initial: { scale: 1 },
  hover: { scale: 1.02, transition: { type: 'spring' as const, stiffness: 400, damping: 25 } },
  tap: { scale: 0.98 },
};

const carouselVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 200 : -200,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
    transition: { type: 'spring' as const, stiffness: 300, damping: 30 },
  },
  exit: (direction: number) => ({
    x: direction < 0 ? 200 : -200,
    opacity: 0,
    transition: { duration: 0.2 },
  }),
};

const collapseVariants = {
  collapsed: {
    height: 0,
    opacity: 0,
    transition: { duration: 0.2 },
  },
  expanded: {
    height: 'auto' as const,
    opacity: 1,
    transition: { duration: 0.25, ease: [0.4, 0, 0.2, 1] as const },
  },
};

// ============================================================================
// Chart Components (Custom SVG implementations)
// ============================================================================

interface MoodTrendChartProps {
  data: typeof progressPatternsData.moodTrend.data;
  onHover?: (tooltip: TooltipState) => void;
  size?: 'compact' | 'expanded';
}

function MoodTrendChart({ data, onHover, size = 'compact' }: MoodTrendChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const width = size === 'compact' ? 240 : 400;
  const height = size === 'compact' ? 100 : 180;
  const padding = { top: 10, right: 20, bottom: 25, left: 30 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const xScale = (i: number) => padding.left + (i / (data.length - 1)) * chartWidth;
  const yScale = (v: number) => padding.top + chartHeight - ((v - 1) / 9) * chartHeight;

  const pathD = data
    .map((d, i) => `${i === 0 ? 'M' : 'L'} ${xScale(i)} ${yScale(d.mood)}`)
    .join(' ');

  const areaD = `${pathD} L ${xScale(data.length - 1)} ${height - padding.bottom} L ${xScale(0)} ${height - padding.bottom} Z`;

  const handleMouseMove = (e: React.MouseEvent, point: typeof data[0], index: number) => {
    if (!svgRef.current || !onHover) return;
    const rect = svgRef.current.getBoundingClientRect();
    onHover({
      visible: true,
      x: e.clientX - rect.left,
      y: e.clientY - rect.top - 40,
      content: `Session ${point.session}: ${point.mood}/10`,
    });
  };

  const handleMouseLeave = () => {
    onHover?.({ visible: false, x: 0, y: 0, content: '' });
  };

  return (
    <svg ref={svgRef} width={width} height={height} className="overflow-visible">
      <defs>
        <linearGradient id="moodGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#5AB9B4" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#B8A5D6" stopOpacity="0.1" />
        </linearGradient>
      </defs>

      {/* Y-axis labels */}
      {[1, 5, 10].map((v) => (
        <text
          key={v}
          x={padding.left - 8}
          y={yScale(v) + 4}
          className="text-[10px] fill-gray-400"
          textAnchor="end"
          style={{ fontFamily: 'Space Mono, monospace' }}
        >
          {v}
        </text>
      ))}

      {/* X-axis labels */}
      {data.filter((_, i) => i % 3 === 0 || i === data.length - 1).map((d, i, arr) => {
        const originalIndex = i === arr.length - 1 ? data.length - 1 : i * 3;
        return (
          <text
            key={d.session}
            x={xScale(originalIndex)}
            y={height - 5}
            className="text-[9px] fill-gray-400"
            textAnchor="middle"
            style={{ fontFamily: 'Space Mono, monospace' }}
          >
            S{d.session}
          </text>
        );
      })}

      {/* Area fill */}
      <path d={areaD} fill="url(#moodGradient)" />

      {/* Line */}
      <path d={pathD} fill="none" stroke="#5AB9B4" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

      {/* Data points */}
      {data.map((d, i) => (
        <circle
          key={d.session}
          cx={xScale(i)}
          cy={yScale(d.mood)}
          r={size === 'compact' ? 3 : 5}
          fill="#5AB9B4"
          stroke="white"
          strokeWidth="2"
          className="cursor-pointer transition-transform hover:scale-125"
          onMouseMove={(e) => handleMouseMove(e, d, i)}
          onMouseLeave={handleMouseLeave}
        />
      ))}
    </svg>
  );
}

interface HomeworkImpactChartProps {
  data: typeof progressPatternsData.homeworkImpact.data;
  onHover?: (tooltip: TooltipState) => void;
  size?: 'compact' | 'expanded';
}

function HomeworkImpactChart({ data, onHover, size = 'compact' }: HomeworkImpactChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const width = size === 'compact' ? 240 : 400;
  const height = size === 'compact' ? 100 : 180;
  const padding = { top: 10, right: 20, bottom: 25, left: 35 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  const barWidth = (chartWidth / data.length) * 0.7;
  const gap = (chartWidth / data.length) * 0.3;

  const handleMouseMove = (e: React.MouseEvent, point: typeof data[0]) => {
    if (!svgRef.current || !onHover) return;
    const rect = svgRef.current.getBoundingClientRect();
    onHover({
      visible: true,
      x: e.clientX - rect.left,
      y: e.clientY - rect.top - 40,
      content: `${point.week}: ${point.completionRate}% completed, Mood: ${point.averageMood}`,
    });
  };

  const handleMouseLeave = () => {
    onHover?.({ visible: false, x: 0, y: 0, content: '' });
  };

  return (
    <svg ref={svgRef} width={width} height={height} className="overflow-visible">
      {/* Y-axis labels */}
      {[0, 50, 100].map((v) => (
        <text
          key={v}
          x={padding.left - 8}
          y={padding.top + chartHeight - (v / 100) * chartHeight + 4}
          className="text-[10px] fill-gray-400"
          textAnchor="end"
          style={{ fontFamily: 'Space Mono, monospace' }}
        >
          {v}%
        </text>
      ))}

      {/* Bars */}
      {data.map((d, i) => {
        const x = padding.left + i * (barWidth + gap) + gap / 2;
        const barHeight = (d.completionRate / 100) * chartHeight;
        const y = padding.top + chartHeight - barHeight;

        // Color based on completion rate
        const color = d.completionRate >= 80 ? '#5AB9B4' : d.completionRate >= 60 ? '#B8A5D6' : '#F4A69D';

        return (
          <g key={d.week}>
            <rect
              x={x}
              y={y}
              width={barWidth}
              height={barHeight}
              fill={color}
              rx="3"
              className="cursor-pointer transition-opacity hover:opacity-80"
              onMouseMove={(e) => handleMouseMove(e, d)}
              onMouseLeave={handleMouseLeave}
            />
            {size === 'expanded' && (
              <text
                x={x + barWidth / 2}
                y={height - 5}
                className="text-[8px] fill-gray-400"
                textAnchor="middle"
                style={{ fontFamily: 'Space Mono, monospace' }}
              >
                W{i + 1}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

interface SessionConsistencyChartProps {
  data: typeof progressPatternsData.sessionConsistency.data;
  onHover?: (tooltip: TooltipState) => void;
  size?: 'compact' | 'expanded';
}

function SessionConsistencyChart({ data, onHover, size = 'compact' }: SessionConsistencyChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const cellSize = size === 'compact' ? 8 : 12;
  const cellGap = 2;
  const weeks = 13; // Oct to Dec = ~13 weeks
  const days = 7;
  const width = weeks * (cellSize + cellGap) + 40;
  const height = days * (cellSize + cellGap) + 20;

  // Group data by week
  const weeklyData: (typeof data[0] | null)[][] = [];
  let currentWeek: (typeof data[0] | null)[] = [];

  data.forEach((day, i) => {
    if (day.dayOfWeek === 0 && currentWeek.length > 0) {
      weeklyData.push(currentWeek);
      currentWeek = [];
    }
    currentWeek.push(day);
    if (i === data.length - 1) {
      weeklyData.push(currentWeek);
    }
  });

  const handleMouseMove = (e: React.MouseEvent, day: typeof data[0]) => {
    if (!svgRef.current || !onHover) return;
    const rect = svgRef.current.getBoundingClientRect();
    const date = new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    onHover({
      visible: true,
      x: e.clientX - rect.left,
      y: e.clientY - rect.top - 40,
      content: `${date}: ${day.hasSession ? 'Session' : 'No session'}`,
    });
  };

  const handleMouseLeave = () => {
    onHover?.({ visible: false, x: 0, y: 0, content: '' });
  };

  const dayLabels = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

  return (
    <svg ref={svgRef} width={width} height={height} className="overflow-visible">
      {/* Day labels */}
      {dayLabels.map((label, i) => (
        <text
          key={i}
          x={12}
          y={15 + i * (cellSize + cellGap) + cellSize / 2 + 3}
          className="text-[9px] fill-gray-400"
          textAnchor="middle"
        >
          {label}
        </text>
      ))}

      {/* Calendar grid */}
      {weeklyData.slice(0, weeks).map((week, weekIndex) => (
        <g key={weekIndex}>
          {week.map((day, dayIndex) => {
            if (!day) return null;
            const x = 25 + weekIndex * (cellSize + cellGap);
            const y = 10 + day.dayOfWeek * (cellSize + cellGap);

            return (
              <rect
                key={day.date}
                x={x}
                y={y}
                width={cellSize}
                height={cellSize}
                rx="2"
                fill={day.hasSession ? '#5AB9B4' : '#E5E7EB'}
                className="cursor-pointer transition-opacity hover:opacity-80"
                onMouseMove={(e) => handleMouseMove(e, day)}
                onMouseLeave={handleMouseLeave}
              />
            );
          })}
        </g>
      ))}
    </svg>
  );
}

interface StrategyEffectivenessChartProps {
  data: typeof progressPatternsData.strategyEffectiveness.data;
  onHover?: (tooltip: TooltipState) => void;
  size?: 'compact' | 'expanded';
}

function StrategyEffectivenessChart({ data, onHover, size = 'compact' }: StrategyEffectivenessChartProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const width = size === 'compact' ? 240 : 400;
  const barHeight = size === 'compact' ? 16 : 24;
  const gap = size === 'compact' ? 8 : 12;
  const height = data.length * (barHeight + gap) + 10;
  const maxWidth = width - 100;

  const handleMouseMove = (e: React.MouseEvent, strategy: typeof data[0]) => {
    if (!svgRef.current || !onHover) return;
    const rect = svgRef.current.getBoundingClientRect();
    onHover({
      visible: true,
      x: e.clientX - rect.left,
      y: e.clientY - rect.top - 40,
      content: `${strategy.strategy}: ${(strategy.moodCorrelation * 100).toFixed(0)}% correlation, Used ${strategy.timesUsed}x`,
    });
  };

  const handleMouseLeave = () => {
    onHover?.({ visible: false, x: 0, y: 0, content: '' });
  };

  return (
    <svg ref={svgRef} width={width} height={height} className="overflow-visible">
      {data.map((strategy, i) => {
        const y = i * (barHeight + gap) + 5;
        const barWidthCalc = strategy.moodCorrelation * maxWidth;

        // Truncate strategy name for compact view
        const displayName = size === 'compact'
          ? strategy.strategy.split(' ')[0]
          : strategy.strategy.split(' ').slice(0, 2).join(' ');

        return (
          <g key={strategy.strategy}>
            {/* Label */}
            <text
              x={0}
              y={y + barHeight / 2 + 4}
              className="text-[10px] fill-gray-600 font-medium"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              {displayName}
            </text>

            {/* Background bar */}
            <rect
              x={size === 'compact' ? 60 : 100}
              y={y}
              width={maxWidth}
              height={barHeight}
              fill="#E5E7EB"
              rx="4"
            />

            {/* Value bar */}
            <rect
              x={size === 'compact' ? 60 : 100}
              y={y}
              width={barWidthCalc}
              height={barHeight}
              fill={`hsl(${170 + strategy.moodCorrelation * 30}, 60%, 55%)`}
              rx="4"
              className="cursor-pointer transition-opacity hover:opacity-80"
              onMouseMove={(e) => handleMouseMove(e, strategy)}
              onMouseLeave={handleMouseLeave}
            />

            {/* Value label */}
            <text
              x={(size === 'compact' ? 60 : 100) + barWidthCalc + 5}
              y={y + barHeight / 2 + 4}
              className="text-[10px] fill-gray-500"
              style={{ fontFamily: 'Space Mono, monospace' }}
            >
              {(strategy.moodCorrelation * 100).toFixed(0)}%
            </text>
          </g>
        );
      })}
    </svg>
  );
}

// ============================================================================
// Carousel Page Components
// ============================================================================

const pages: { key: CarouselPage; icon: React.ReactNode; title: string }[] = [
  { key: 'mood', icon: <TrendingUp className="w-4 h-4" />, title: 'Mood Trend' },
  { key: 'homework', icon: <BarChart3 className="w-4 h-4" />, title: 'Homework Impact' },
  { key: 'consistency', icon: <Calendar className="w-4 h-4" />, title: 'Session Consistency' },
  { key: 'strategy', icon: <Target className="w-4 h-4" />, title: 'Strategy Effectiveness' },
];

interface CarouselPageContentProps {
  page: CarouselPage;
  tooltip: TooltipState;
  setTooltip: (tooltip: TooltipState) => void;
  size?: 'compact' | 'expanded';
}

function CarouselPageContent({ page, tooltip, setTooltip, size = 'compact' }: CarouselPageContentProps) {
  const insights = {
    mood: progressPatternsData.moodTrend.insight,
    homework: progressPatternsData.homeworkImpact.insight,
    consistency: progressPatternsData.sessionConsistency.insight,
    strategy: progressPatternsData.strategyEffectiveness.insight,
  };

  const charts = {
    mood: <MoodTrendChart data={progressPatternsData.moodTrend.data} onHover={setTooltip} size={size} />,
    homework: <HomeworkImpactChart data={progressPatternsData.homeworkImpact.data} onHover={setTooltip} size={size} />,
    consistency: <SessionConsistencyChart data={progressPatternsData.sessionConsistency.data} onHover={setTooltip} size={size} />,
    strategy: <StrategyEffectivenessChart data={progressPatternsData.strategyEffectiveness.data} onHover={setTooltip} size={size} />,
  };

  return (
    <div className="relative">
      {/* Chart */}
      <div className="flex justify-center mb-3">
        {charts[page]}
      </div>

      {/* Insight text (compact only shows truncated) */}
      <p className={cn(
        "text-xs font-light text-gray-600 dark:text-gray-400 leading-relaxed",
        size === 'compact' && "line-clamp-2"
      )}>
        {size === 'compact' ? insights[page].slice(0, 100) + '...' : insights[page]}
      </p>

      {/* Tooltip */}
      <AnimatePresence>
        {tooltip.visible && (
          <motion.div
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 5 }}
            className="absolute z-10 px-2 py-1 text-xs bg-gray-900 text-white rounded shadow-lg pointer-events-none"
            style={{
              left: tooltip.x,
              top: tooltip.y,
              transform: 'translateX(-50%)',
              fontFamily: 'Space Mono, monospace',
            }}
          >
            {tooltip.content}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================================
// Collapsible Section for Modal
// ============================================================================

interface CollapsibleSectionProps {
  title: string;
  icon: React.ReactNode;
  isExpanded: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

function CollapsibleSection({ title, icon, isExpanded, onToggle, children }: CollapsibleSectionProps) {
  return (
    <div className="border border-gray-100 dark:border-gray-800 rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
        className={cn(
          "w-full flex items-center justify-between p-4",
          "bg-gray-50/50 dark:bg-gray-800/50",
          "hover:bg-gray-100/50 dark:hover:bg-gray-700/50 transition-colors"
        )}
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-gradient-to-br from-teal-100 to-purple-100 dark:from-teal-900/40 dark:to-purple-900/40">
            <span className="text-teal-600 dark:text-teal-400">{icon}</span>
          </div>
          <span className="font-medium text-gray-800 dark:text-gray-200" style={{ fontFamily: 'Inter, sans-serif' }}>
            {title}
          </span>
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
        >
          <ChevronDown className="w-5 h-5 text-gray-400" />
        </motion.div>
      </button>

      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial="collapsed"
            animate="expanded"
            exit="collapsed"
            variants={collapseVariants}
            className="overflow-hidden"
          >
            <div className="p-4 bg-white dark:bg-gray-900">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================================
// Main Component
// ============================================================================

interface ProgressPatternsCardProps {
  className?: string;
}

export function ProgressPatternsCard({ className }: ProgressPatternsCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [currentPage, setCurrentPage] = useState(0);
  const [direction, setDirection] = useState(0);
  const [expandedSections, setExpandedSections] = useState<Record<CarouselPage, boolean>>({
    mood: true,
    homework: false,
    consistency: false,
    strategy: false,
  });
  const [tooltip, setTooltip] = useState<TooltipState>({ visible: false, x: 0, y: 0, content: '' });

  // Touch handling for carousel
  const touchStartX = useRef(0);
  const touchEndX = useRef(0);

  const handleTouchStart = (e: React.TouchEvent) => {
    touchStartX.current = e.touches[0].clientX;
  };

  const handleTouchMove = (e: React.TouchEvent) => {
    touchEndX.current = e.touches[0].clientX;
  };

  const handleTouchEnd = () => {
    const diff = touchStartX.current - touchEndX.current;
    if (Math.abs(diff) > 50) {
      if (diff > 0 && currentPage < pages.length - 1) {
        setDirection(1);
        setCurrentPage((prev) => prev + 1);
      } else if (diff < 0 && currentPage > 0) {
        setDirection(-1);
        setCurrentPage((prev) => prev - 1);
      }
    }
  };

  const handleDragStart = (e: MouseEvent | TouchEvent | PointerEvent) => {
    // Prevent modal from interfering with drag gesture
    e.stopPropagation();
  };

  const handleDragEnd = (e: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    // Prevent modal from closing on drag
    e.stopPropagation();

    if (info.offset.x < -50 && currentPage < pages.length - 1) {
      setDirection(1);
      setCurrentPage((prev) => prev + 1);
    } else if (info.offset.x > 50 && currentPage > 0) {
      setDirection(-1);
      setCurrentPage((prev) => prev - 1);
    }
  };

  const goToPage = useCallback((index: number) => {
    setDirection(index > currentPage ? 1 : -1);
    setCurrentPage(index);
  }, [currentPage]);

  const goToPrev = useCallback(() => {
    if (currentPage > 0) {
      setDirection(-1);
      setCurrentPage((prev) => prev - 1);
    }
  }, [currentPage]);

  const goToNext = useCallback(() => {
    if (currentPage < pages.length - 1) {
      setDirection(1);
      setCurrentPage((prev) => prev + 1);
    }
  }, [currentPage]);

  // Keyboard navigation for carousel
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      goToPrev();
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      goToNext();
    }
  };

  const toggleSection = (section: CarouselPage) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  const currentPageData = pages[currentPage];

  return (
    <>
      {/* Compact Card */}
      <motion.div
        className={cn(
          "relative overflow-hidden cursor-pointer",
          "rounded-[16px] p-5",
          "border border-transparent",
          className
        )}
        style={{
          background: 'linear-gradient(135deg, #5AB9B4 0%, #8BC4C1 50%, #B8A5D6 100%)',
          boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
        }}
        variants={cardVariants}
        initial="initial"
        whileHover="hover"
        whileTap="tap"
        onClick={() => setIsExpanded(true)}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            setIsExpanded(true);
          }
        }}
        role="button"
        tabIndex={0}
        aria-label="Open progress patterns details"
      >
        {/* Header */}
        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 rounded-full bg-white/20">
            <TrendingUp className="w-4 h-4 text-white" />
          </div>
          <h3
            className="font-medium text-base text-white tracking-wide"
            style={{ fontFamily: 'Inter, sans-serif' }}
          >
            Progress Patterns
          </h3>
        </div>

        {/* Carousel Container */}
        <div
          className="relative bg-white/90 dark:bg-gray-900/90 rounded-xl p-4 mb-3"
          onTouchStart={handleTouchStart}
          onTouchMove={handleTouchMove}
          onTouchEnd={handleTouchEnd}
          onKeyDown={handleKeyDown}
          tabIndex={0}
          role="region"
          aria-label="Progress patterns carousel"
          aria-roledescription="carousel"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Page Title */}
          <div className="flex items-center justify-center gap-2 mb-3">
            <span className="text-teal-600 dark:text-teal-400">{currentPageData.icon}</span>
            <span
              className="text-sm font-medium text-gray-700 dark:text-gray-300"
              style={{ fontFamily: 'Inter, sans-serif' }}
            >
              {currentPageData.title}
            </span>
          </div>

          {/* Carousel Content */}
          <div className="relative overflow-hidden min-h-[140px]">
            <AnimatePresence initial={false} custom={direction} mode="wait">
              <motion.div
                key={currentPage}
                custom={direction}
                variants={carouselVariants}
                initial="enter"
                animate="center"
                exit="exit"
                drag="x"
                dragConstraints={{ left: 0, right: 0 }}
                dragElastic={0.2}
                onDragStart={handleDragStart}
                onDragEnd={handleDragEnd}
              >
                <CarouselPageContent
                  page={currentPageData.key}
                  tooltip={tooltip}
                  setTooltip={setTooltip}
                  size="compact"
                />
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Navigation Arrows */}
          <button
            onClick={(e) => { e.stopPropagation(); goToPrev(); }}
            disabled={currentPage === 0}
            className={cn(
              "absolute left-1 top-1/2 -translate-y-1/2 p-1 rounded-full",
              "bg-white/80 dark:bg-gray-800/80 shadow-sm",
              "transition-opacity",
              currentPage === 0 ? "opacity-30 cursor-not-allowed" : "opacity-70 hover:opacity-100"
            )}
            aria-label="Previous chart"
          >
            <ChevronLeft className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>

          <button
            onClick={(e) => { e.stopPropagation(); goToNext(); }}
            disabled={currentPage === pages.length - 1}
            className={cn(
              "absolute right-1 top-1/2 -translate-y-1/2 p-1 rounded-full",
              "bg-white/80 dark:bg-gray-800/80 shadow-sm",
              "transition-opacity",
              currentPage === pages.length - 1 ? "opacity-30 cursor-not-allowed" : "opacity-70 hover:opacity-100"
            )}
            aria-label="Next chart"
          >
            <ChevronRight className="w-4 h-4 text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        {/* Carousel Dots */}
        <div
          className="flex justify-center gap-2"
          role="tablist"
          aria-label="Chart navigation"
        >
          {pages.map((page, i) => (
            <button
              key={page.key}
              onClick={(e) => { e.stopPropagation(); goToPage(i); }}
              role="tab"
              aria-selected={currentPage === i}
              aria-label={`View ${page.title}`}
              className={cn(
                "w-2 h-2 rounded-full transition-all duration-200",
                currentPage === i
                  ? "bg-white w-4"
                  : "bg-white/40 hover:bg-white/60"
              )}
            />
          ))}
        </div>

        {/* Expand hint */}
        <div className="mt-3 text-center">
          <span className="text-xs font-light text-white/70">
            Tap for detailed insights
          </span>
        </div>
      </motion.div>

      {/* Expanded Modal */}
      <ModalWrapper
        isOpen={isExpanded}
        onClose={() => setIsExpanded(false)}
        title="Progress Patterns"
        titleIcon={<TrendingUp className="w-5 h-5 text-teal-600" />}
        className="max-w-2xl"
      >
        <div className="space-y-4">
          {/* Mood Trend Section */}
          <CollapsibleSection
            title="Mood Trend"
            icon={<TrendingUp className="w-4 h-4" />}
            isExpanded={expandedSections.mood}
            onToggle={() => toggleSection('mood')}
          >
            <div className="space-y-4">
              <div className="flex justify-center">
                <MoodTrendChart
                  data={progressPatternsData.moodTrend.data}
                  onHover={setTooltip}
                  size="expanded"
                />
              </div>
              <div className="flex items-center gap-2 p-3 bg-teal-50 dark:bg-teal-900/20 rounded-lg">
                <span
                  className="text-2xl font-bold text-teal-600 dark:text-teal-400"
                  style={{ fontFamily: 'Space Mono, monospace' }}
                >
                  +{progressPatternsData.moodTrend.improvement}%
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400">improvement</span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                {progressPatternsData.moodTrend.insight}
              </p>
            </div>
          </CollapsibleSection>

          {/* Homework Impact Section */}
          <CollapsibleSection
            title="Homework Impact"
            icon={<BarChart3 className="w-4 h-4" />}
            isExpanded={expandedSections.homework}
            onToggle={() => toggleSection('homework')}
          >
            <div className="space-y-4">
              <div className="flex justify-center">
                <HomeworkImpactChart
                  data={progressPatternsData.homeworkImpact.data}
                  onHover={setTooltip}
                  size="expanded"
                />
              </div>
              <div className="flex items-center gap-2 p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <span
                  className="text-lg font-bold text-purple-600 dark:text-purple-400"
                  style={{ fontFamily: 'Space Mono, monospace' }}
                >
                  {progressPatternsData.homeworkImpact.correlation}
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400">correlation</span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                {progressPatternsData.homeworkImpact.insight}
              </p>
            </div>
          </CollapsibleSection>

          {/* Session Consistency Section */}
          <CollapsibleSection
            title="Session Consistency"
            icon={<Calendar className="w-4 h-4" />}
            isExpanded={expandedSections.consistency}
            onToggle={() => toggleSection('consistency')}
          >
            <div className="space-y-4">
              <div className="flex justify-center">
                <SessionConsistencyChart
                  data={progressPatternsData.sessionConsistency.data}
                  onHover={setTooltip}
                  size="expanded"
                />
              </div>
              <div className="flex items-center gap-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <span
                  className="text-2xl font-bold text-blue-600 dark:text-blue-400"
                  style={{ fontFamily: 'Space Mono, monospace' }}
                >
                  {progressPatternsData.sessionConsistency.averageDaysBetween}
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400">days avg between sessions</span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                {progressPatternsData.sessionConsistency.insight}
              </p>
            </div>
          </CollapsibleSection>

          {/* Strategy Effectiveness Section */}
          <CollapsibleSection
            title="Strategy Effectiveness"
            icon={<Target className="w-4 h-4" />}
            isExpanded={expandedSections.strategy}
            onToggle={() => toggleSection('strategy')}
          >
            <div className="space-y-4">
              <div className="flex justify-center">
                <StrategyEffectivenessChart
                  data={progressPatternsData.strategyEffectiveness.data}
                  onHover={setTooltip}
                  size="expanded"
                />
              </div>
              <div className="flex items-center gap-2 p-3 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg">
                <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
                  Top Strategy:
                </span>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  {progressPatternsData.strategyEffectiveness.topStrategy}
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                {progressPatternsData.strategyEffectiveness.insight}
              </p>

              {/* Detailed strategy breakdown */}
              <div className="space-y-2 mt-4">
                {progressPatternsData.strategyEffectiveness.data.map((strategy) => (
                  <div
                    key={strategy.strategy}
                    className="p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-sm text-gray-700 dark:text-gray-300">
                        {strategy.strategy}
                      </span>
                      <span
                        className="text-xs text-gray-500"
                        style={{ fontFamily: 'Space Mono, monospace' }}
                      >
                        {strategy.timesUsed}x used
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {strategy.description}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </CollapsibleSection>
        </div>

        {/* Tooltip for expanded charts */}
        <AnimatePresence>
          {tooltip.visible && (
            <motion.div
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 5 }}
              className="fixed z-50 px-3 py-2 text-xs bg-gray-900 text-white rounded-lg shadow-lg pointer-events-none"
              style={{
                left: tooltip.x,
                top: tooltip.y,
                transform: 'translateX(-50%)',
                fontFamily: 'Space Mono, monospace',
              }}
            >
              {tooltip.content}
            </motion.div>
          )}
        </AnimatePresence>
      </ModalWrapper>
    </>
  );
}

export default ProgressPatternsCard;
