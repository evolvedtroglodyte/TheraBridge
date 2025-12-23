'use client';

import { cn } from '@/lib/utils';

// ============================================================================
// Shared Skeleton Primitives
// ============================================================================

import type { CSSProperties } from 'react';

interface SkeletonProps {
  className?: string;
  style?: CSSProperties;
}

/**
 * Base shimmer animation using Tailwind's animate-pulse
 * Provides consistent loading animation across all skeletons
 */
function SkeletonBox({ className, style }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded',
        'bg-gray-200/60 dark:bg-gray-700/40',
        className
      )}
      style={style}
    />
  );
}

/**
 * Circular skeleton for avatars, icons, dots
 */
function SkeletonCircle({ className, style }: SkeletonProps) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-full',
        'bg-gray-200/60 dark:bg-gray-700/40',
        className
      )}
      style={style}
    />
  );
}

// ============================================================================
// 1. NotesGoalsSkeleton
// ============================================================================

/**
 * Skeleton for NotesGoalsPanel
 * - Card shape with 16px radius and warm tint background
 * - Title bar with icon placeholder
 * - 3 bullet line skeletons with varying widths
 * - Current focus line at bottom
 */
export function NotesGoalsSkeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'rounded-2xl p-6',
        'border border-border/30',
        className
      )}
      style={{
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        background: 'linear-gradient(135deg, #FFFFFF 0%, #FFFBF7 100%)',
        borderRadius: '16px',
        padding: '24px',
      }}
    >
      {/* Header: Icon + Title */}
      <div className="flex items-center gap-3 mb-4">
        <SkeletonCircle className="w-9 h-9 bg-gray-200/80" />
        <SkeletonBox className="h-5 w-28 rounded-lg" />
      </div>

      {/* 3 Bullet Points with varying widths */}
      <div className="space-y-3 mb-4">
        <div className="flex items-start gap-2">
          <SkeletonCircle className="w-1.5 h-1.5 mt-2 flex-shrink-0" />
          <SkeletonBox className="h-4 w-[85%] rounded" />
        </div>
        <div className="flex items-start gap-2">
          <SkeletonCircle className="w-1.5 h-1.5 mt-2 flex-shrink-0" />
          <SkeletonBox className="h-4 w-[70%] rounded" />
        </div>
        <div className="flex items-start gap-2">
          <SkeletonCircle className="w-1.5 h-1.5 mt-2 flex-shrink-0" />
          <SkeletonBox className="h-4 w-[90%] rounded" />
        </div>
      </div>

      {/* Current Focus Line */}
      <div className="pt-3 border-t border-border/30">
        <div className="flex items-center gap-2">
          <SkeletonBox className="h-3 w-24 rounded" />
          <SkeletonBox className="h-3 w-32 rounded" />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// 2. AIChatSkeleton
// ============================================================================

/**
 * Skeleton for AIChatWidget
 * - Card with gradient blue tint background
 * - Circular logo placeholder (60px)
 * - Description text lines (2-3 lines)
 * - 2 prompt pill skeletons (horizontal layout)
 * - Input bar skeleton at bottom
 */
export function AIChatSkeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-2xl',
        'border border-border/30',
        className
      )}
      style={{
        background: 'linear-gradient(135deg, hsl(220 85% 98%) 0%, hsl(240 80% 98%) 50%, hsl(260 75% 98%) 100%)',
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      }}
    >
      <div className="p-6 flex flex-col items-center">
        {/* Dobby Logo Placeholder */}
        <SkeletonCircle className="w-[60px] h-[60px] bg-gray-200/80" />

        {/* Description Text (2-3 lines) */}
        <div className="mt-4 w-full space-y-2 px-4">
          <SkeletonBox className="h-3 w-full rounded mx-auto" />
          <SkeletonBox className="h-3 w-[80%] rounded mx-auto" />
        </div>

        {/* 2 Prompt Pills */}
        <div className="w-full mt-4 space-y-2 px-6">
          <SkeletonBox className="h-12 w-full rounded-xl bg-white/40" />
          <SkeletonBox className="h-12 w-full rounded-xl bg-white/40" />
        </div>

        {/* Carousel Dots */}
        <div className="flex items-center justify-center gap-2 mt-3">
          <SkeletonCircle className="w-4 h-2 rounded-full" />
          <SkeletonCircle className="w-2 h-2" />
          <SkeletonCircle className="w-2 h-2" />
        </div>

        {/* Chat Input Bar */}
        <div className="w-full mt-4">
          <div className="flex items-center gap-2 p-2 bg-white/60 rounded-xl border border-border/30">
            <SkeletonBox className="flex-1 h-8 rounded-lg" />
            <SkeletonCircle className="w-8 h-8" />
          </div>
        </div>
      </div>

      {/* Click hint */}
      <div className="pb-4 pt-1">
        <SkeletonBox className="h-3 w-28 rounded mx-auto" />
      </div>
    </div>
  );
}

// ============================================================================
// 3. ToDoSkeleton
// ============================================================================

/**
 * Skeleton for ToDoCard
 * - Card with 8px sharp radius, flat white background
 * - Title + percentage skeleton
 * - Progress bar skeleton (8px height)
 * - 3 task line skeletons with checkbox circles
 * - Carousel dots skeleton
 */
export function ToDoSkeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden',
        'rounded-lg p-5',
        'bg-white dark:bg-gray-900',
        'border border-gray-200 dark:border-gray-700',
        className
      )}
      style={{
        boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
      }}
    >
      {/* Header: Title + Percentage */}
      <div className="flex items-center justify-between mb-4">
        <SkeletonBox className="h-5 w-14 rounded" />
        <SkeletonBox className="h-4 w-10 rounded" />
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <SkeletonBox className="w-full h-2 rounded-full" />
      </div>

      {/* 3 Task Lines with Checkboxes */}
      <div className="space-y-3">
        {[85, 70, 60].map((width, idx) => (
          <div key={idx} className="flex items-start gap-3 py-1.5">
            <SkeletonCircle className="w-4 h-4 flex-shrink-0" />
            <SkeletonBox className="h-4 rounded" style={{ width: `${width}%` }} />
          </div>
        ))}
      </div>

      {/* +N more tasks */}
      <SkeletonBox className="h-3 w-20 rounded mt-2" />

      {/* Carousel Dots */}
      <div className="flex items-center justify-center gap-1.5 mt-3">
        <SkeletonCircle className="w-3 h-1.5 rounded-full" />
        <SkeletonCircle className="w-1.5 h-1.5" />
        <SkeletonCircle className="w-1.5 h-1.5" />
      </div>
    </div>
  );
}

// ============================================================================
// 4. ProgressPatternsSkeleton
// ============================================================================

/**
 * Skeleton for ProgressPatternsCard
 * - Card with gradient background (teal to lavender)
 * - Title skeleton
 * - Large rectangle for chart area
 * - Insight text skeleton (2 lines)
 * - Carousel dots skeleton
 */
export function ProgressPatternsSkeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden',
        'rounded-[16px] p-5',
        'border border-transparent',
        className
      )}
      style={{
        background: 'linear-gradient(135deg, #5AB9B4 0%, #8BC4C1 50%, #B8A5D6 100%)',
        boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
      }}
    >
      {/* Header: Icon + Title */}
      <div className="flex items-center gap-2 mb-4">
        <SkeletonCircle className="w-8 h-8 bg-white/20" />
        <SkeletonBox className="h-4 w-32 rounded bg-white/30" />
      </div>

      {/* Chart Container */}
      <div className="relative bg-white/80 dark:bg-gray-900/80 rounded-xl p-4 mb-3">
        {/* Chart Title */}
        <div className="flex items-center justify-center gap-2 mb-3">
          <SkeletonCircle className="w-4 h-4 bg-gray-200/80" />
          <SkeletonBox className="h-4 w-24 rounded" />
        </div>

        {/* Chart Area (Large Rectangle) */}
        <SkeletonBox className="w-full h-[100px] rounded-lg mb-3 bg-gray-200/60" />

        {/* Insight Text (2 lines) */}
        <div className="space-y-1">
          <SkeletonBox className="h-3 w-full rounded" />
          <SkeletonBox className="h-3 w-[70%] rounded" />
        </div>
      </div>

      {/* Carousel Dots */}
      <div className="flex justify-center gap-2">
        <SkeletonCircle className="w-4 h-2 rounded-full bg-white/60" />
        <SkeletonCircle className="w-2 h-2 bg-white/30" />
        <SkeletonCircle className="w-2 h-2 bg-white/30" />
        <SkeletonCircle className="w-2 h-2 bg-white/30" />
      </div>

      {/* Expand hint */}
      <div className="mt-3 text-center">
        <SkeletonBox className="h-3 w-32 rounded mx-auto bg-white/30" />
      </div>
    </div>
  );
}

// ============================================================================
// 5. TherapistBridgeSkeleton
// ============================================================================

/**
 * Skeleton for TherapistBridgeCard
 * - Card with 20px pill radius, warm gradient background
 * - Title skeleton
 * - 3 section skeletons (header + 2 items each)
 */
export function TherapistBridgeSkeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'relative overflow-hidden',
        'rounded-[20px] p-5',
        'bg-gradient-to-br from-amber-50/90 via-orange-50/80 to-rose-50/70',
        'dark:from-amber-950/30 dark:via-orange-950/20 dark:to-rose-950/20',
        'border border-amber-100/50 dark:border-amber-800/30',
        className
      )}
      style={{
        boxShadow: '0 2px 16px rgba(91, 185, 180, 0.15)',
      }}
    >
      {/* Header: Icon + Title */}
      <div className="flex items-center gap-2 mb-4">
        <SkeletonCircle className="w-8 h-8 bg-gray-200/60" />
        <SkeletonBox className="h-4 w-32 rounded bg-gray-200/60" />
      </div>

      {/* 3 Sections */}
      <div className="space-y-4">
        {['teal', 'emerald', 'amber'].map((_, idx) => (
          <div key={idx} className="space-y-1.5">
            {/* Section Header */}
            <div className="flex items-center gap-1.5">
              <SkeletonCircle className="w-3.5 h-3.5 bg-gray-200/60" />
              <SkeletonBox className="h-3 w-28 rounded bg-gray-200/60" />
            </div>
            {/* Section Content */}
            <div className="pl-5">
              <SkeletonBox className="h-4 w-[90%] rounded bg-gray-200/60" />
            </div>
          </div>
        ))}
      </div>

      {/* Expand hint */}
      <div className="mt-4 text-center">
        <SkeletonBox className="h-3 w-24 rounded mx-auto bg-gray-200/60" />
      </div>
    </div>
  );
}

// ============================================================================
// 6. SessionCardsGridSkeleton
// ============================================================================

/**
 * Skeleton for SessionCardsGrid
 * - Grid layout (4 columns)
 * - 8 session card skeletons per page
 * - Each card: metadata row + two-column split
 * - Pagination dots skeleton
 */
export function SessionCardsGridSkeleton({ className }: SkeletonProps) {
  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Grid Container - 4 columns x 2 rows */}
      <div className="grid grid-cols-4 grid-rows-2 gap-4 flex-1">
        {Array.from({ length: 8 }).map((_, idx) => (
          <SessionCardSkeleton key={idx} />
        ))}
      </div>

      {/* Pagination Dots */}
      <div className="flex items-center justify-center gap-3 mt-4">
        <SkeletonCircle className="w-7 h-7" />
        <div className="flex items-center gap-2">
          <SkeletonCircle className="w-3 h-3" />
          <SkeletonCircle className="w-2.5 h-2.5" />
          <SkeletonCircle className="w-2.5 h-2.5" />
        </div>
        <SkeletonCircle className="w-7 h-7" />
      </div>
    </div>
  );
}

/**
 * Individual Session Card Skeleton
 * - Mood-colored left border (simulated with gray)
 * - Metadata row: date, duration, mood
 * - Two-column split: Topics | Strategy + Actions
 */
function SessionCardSkeleton() {
  return (
    <div
      className={cn(
        'relative w-full',
        'bg-white dark:bg-card',
        'rounded-xl overflow-hidden',
        'border border-border/50',
        'border-l-4 border-l-gray-300'
      )}
      style={{
        boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
      }}
    >
      <div className="p-4">
        {/* Metadata Row */}
        <div className="flex items-center gap-2 text-xs mb-3">
          <SkeletonBox className="h-3 w-16 rounded" />
          <SkeletonCircle className="w-1 h-1" />
          <SkeletonBox className="h-3 w-8 rounded" />
          <SkeletonCircle className="w-1 h-1" />
          <SkeletonCircle className="w-4 h-4" />
        </div>

        {/* Two-Column Split */}
        <div className="grid grid-cols-2 gap-3">
          {/* Left Column: Topics */}
          <div>
            <SkeletonBox className="h-2 w-12 rounded mb-2" />
            <div className="space-y-1.5">
              <SkeletonBox className="h-3 w-full rounded" />
              <SkeletonBox className="h-3 w-[85%] rounded" />
              <SkeletonBox className="h-3 w-[70%] rounded" />
            </div>
          </div>

          {/* Right Column: Strategy + Actions */}
          <div>
            <SkeletonBox className="h-2 w-14 rounded mb-2" />
            <SkeletonBox className="h-3 w-full rounded mb-3" />
            <SkeletonBox className="h-2 w-12 rounded mb-1.5" />
            <div className="space-y-1">
              <div className="flex items-start gap-1">
                <SkeletonCircle className="w-1.5 h-1.5 mt-1" />
                <SkeletonBox className="h-2.5 w-[80%] rounded" />
              </div>
              <div className="flex items-start gap-1">
                <SkeletonCircle className="w-1.5 h-1.5 mt-1" />
                <SkeletonBox className="h-2.5 w-[65%] rounded" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// 7. TimelineSkeleton
// ============================================================================

/**
 * Skeleton for TimelineSidebar
 * - Vertical container with sticky positioning
 * - Title skeleton
 * - 6-8 timeline entry skeletons
 * - Each entry: dot + date + topic line
 */
export function TimelineSkeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        'sticky top-6 bg-white dark:bg-card border border-slate-200 dark:border-slate-800 shadow-sm',
        'rounded-xl overflow-hidden',
        className
      )}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <SkeletonCircle className="w-4 h-4" />
          <SkeletonBox className="h-4 w-20 rounded" />
        </div>
      </div>

      {/* Timeline Entries */}
      <div className="px-4 py-4 max-h-[60vh] overflow-hidden">
        <div className="space-y-0">
          {Array.from({ length: 7 }).map((_, idx) => (
            <TimelineEntrySkeleton key={idx} isLast={idx === 6} />
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Individual Timeline Entry Skeleton
 * - Dot/star placeholder
 * - Vertical connector line (except last)
 * - Date + topic text
 */
function TimelineEntrySkeleton({ isLast }: { isLast: boolean }) {
  return (
    <div className="relative flex gap-3">
      {/* Connector line */}
      {!isLast && (
        <div
          className="absolute left-[7px] top-6 w-0.5 h-[calc(100%+8px)] bg-gray-200/60"
          style={{
            background: 'linear-gradient(to bottom, rgba(200,200,200,0.4), rgba(200,200,200,0.2))',
          }}
        />
      )}

      {/* Dot */}
      <div className="relative z-10 flex-shrink-0">
        <SkeletonCircle className="w-[10px] h-[10px]" style={{ marginTop: '2px' }} />
      </div>

      {/* Entry content */}
      <div className="flex-1 pb-4">
        <SkeletonBox className="h-3 w-20 rounded mb-1" />
        <SkeletonBox className="h-2.5 w-24 rounded" />
      </div>
    </div>
  );
}

// ============================================================================
// Composite Dashboard Skeleton
// ============================================================================

/**
 * Complete Dashboard V2 Skeleton
 * Matches the layout of the actual dashboard with all 7 widget skeletons
 */
export function DashboardV2Skeleton() {
  return (
    <div className="space-y-10">
      {/* TOP ROW: Notes/Goals + AI Chat (2 columns) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <NotesGoalsSkeleton />
        <AIChatSkeleton />
      </div>

      {/* MIDDLE ROW: To-Do + Progress Patterns + Therapist Bridge (3 columns) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <ToDoSkeleton />
        <ProgressPatternsSkeleton />
        <TherapistBridgeSkeleton />
      </div>

      {/* BOTTOM ROW: Session Cards Grid + Timeline (4fr : 1fr split) */}
      <div className="grid grid-cols-1 md:grid-cols-[4fr_1fr] gap-6">
        <SessionCardsGridSkeleton />
        <TimelineSkeleton />
      </div>
    </div>
  );
}

// ============================================================================
// Exports
// ============================================================================

export type { SkeletonProps };
