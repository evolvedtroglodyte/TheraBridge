'use client';

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Filter } from 'lucide-react';
import type { StatusFilter, DateRangeFilter } from '@/hooks/useSessionFilters';

interface SessionFiltersProps {
  /** Current status filter value */
  statusFilter: StatusFilter;
  /** Callback when status filter changes */
  onStatusFilterChange: (value: StatusFilter) => void;
  /** Current date range filter value */
  dateRangeFilter: DateRangeFilter;
  /** Callback when date range filter changes */
  onDateRangeFilterChange: (value: DateRangeFilter) => void;
}

/**
 * Filter controls for session lists
 *
 * Provides dropdown selects for:
 * - Session Status (all, processing, completed, failed)
 * - Date Range (all time, last 7/30 days, last 3 months)
 *
 * @example
 * ```tsx
 * <SessionFilters
 *   statusFilter={statusFilter}
 *   onStatusFilterChange={setStatusFilter}
 *   dateRangeFilter={dateRangeFilter}
 *   onDateRangeFilterChange={setDateRangeFilter}
 * />
 * ```
 */
export function SessionFilters({
  statusFilter,
  onStatusFilterChange,
  dateRangeFilter,
  onDateRangeFilterChange,
}: SessionFiltersProps) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-2">
        <Filter className="w-5 h-5 text-muted-foreground" />
        <span className="text-sm font-medium text-muted-foreground">Filters:</span>
      </div>

      <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
        {/* Status Filter */}
        <div className="flex flex-col gap-2">
          <label htmlFor="status-filter" className="text-xs font-medium text-muted-foreground">
            Status
          </label>
          <Select value={statusFilter} onValueChange={(value) => onStatusFilterChange(value as StatusFilter)}>
            <SelectTrigger id="status-filter" className="w-full sm:w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sessions</SelectItem>
              <SelectItem value="processing">Processing</SelectItem>
              <SelectItem value="completed">Completed</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Date Range Filter */}
        <div className="flex flex-col gap-2">
          <label htmlFor="date-filter" className="text-xs font-medium text-muted-foreground">
            Date Range
          </label>
          <Select value={dateRangeFilter} onValueChange={(value) => onDateRangeFilterChange(value as DateRangeFilter)}>
            <SelectTrigger id="date-filter" className="w-full sm:w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Time</SelectItem>
              <SelectItem value="last-7-days">Last 7 Days</SelectItem>
              <SelectItem value="last-30-days">Last 30 Days</SelectItem>
              <SelectItem value="last-3-months">Last 3 Months</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </div>
  );
}

export type { SessionFiltersProps };
