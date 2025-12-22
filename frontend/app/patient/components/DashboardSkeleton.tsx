'use client';

/**
 * Loading skeleton for Dashboard-v3
 * Shows placeholder content while data is being fetched
 */

export function DashboardSkeleton() {
  return (
    <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] animate-pulse">
      {/* Header skeleton */}
      <div className="w-full border-b border-[#E0DDD8] dark:border-gray-700 px-12 py-4 bg-[#F8F7F4] dark:bg-[#1a1625]">
        <div className="max-w-[1400px] mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-[#E0DDD8] dark:bg-gray-600 rounded-lg" />
            <div className="h-6 w-32 bg-[#E0DDD8] dark:bg-gray-600 rounded" />
          </div>
          <div className="h-8 w-8 bg-[#E0DDD8] dark:bg-gray-600 rounded" />
        </div>
      </div>

      {/* Main content skeleton */}
      <main className="w-full max-w-[1400px] mx-auto px-12 py-12">
        {/* Top Row - 50/50 */}
        <div className="grid grid-cols-2 gap-6 mb-10">
          <div className="h-[280px] bg-[#F8F7F4] dark:bg-[#2a2435] rounded-2xl shadow-sm" />
          <div className="h-[280px] bg-[#F8F7F4] dark:bg-[#2a2435] rounded-2xl shadow-sm" />
        </div>

        {/* Middle Row - 3 cards */}
        <div className="grid grid-cols-3 gap-6 mb-10">
          <div className="h-[200px] bg-[#F8F7F4] dark:bg-[#2a2435] rounded-2xl shadow-sm" />
          <div className="h-[200px] bg-[#F8F7F4] dark:bg-[#2a2435] rounded-2xl shadow-sm" />
          <div className="h-[200px] bg-[#F8F7F4] dark:bg-[#2a2435] rounded-2xl shadow-sm" />
        </div>

        {/* Bottom Row - Session grid */}
        <div className="grid grid-cols-[1fr_250px] gap-6">
          <div className="h-[650px] bg-[#F8F7F4] dark:bg-[#2a2435] rounded-2xl shadow-sm" />
          <div className="h-[650px] bg-[#F8F7F4] dark:bg-[#2a2435] rounded-2xl shadow-sm" />
        </div>
      </main>
    </div>
  );
}

/**
 * Smaller skeleton for individual cards when refreshing
 */
export function CardSkeleton({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-[#F8F7F4] dark:bg-[#2a2435] rounded-2xl shadow-sm animate-pulse ${className}`}>
      <div className="p-6 space-y-4">
        <div className="h-5 w-1/3 bg-gray-200 dark:bg-gray-700 rounded" />
        <div className="space-y-2">
          <div className="h-4 w-full bg-gray-200 dark:bg-gray-700 rounded" />
          <div className="h-4 w-2/3 bg-gray-200 dark:bg-gray-700 rounded" />
        </div>
      </div>
    </div>
  );
}
