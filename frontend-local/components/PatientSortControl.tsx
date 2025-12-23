'use client';

import React from 'react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { ArrowUp, ArrowDown } from 'lucide-react';
import type { PatientSortField, SortOrder } from '@/hooks/usePatientSort';

interface PatientSortControlProps {
  sortField: PatientSortField;
  sortOrder: SortOrder;
  onSortFieldChange: (field: PatientSortField) => void;
  onSortOrderChange: (order: SortOrder) => void;
  onToggleSortOrder?: () => void;
}

export function PatientSortControl({
  sortField,
  sortOrder,
  onSortFieldChange,
  onSortOrderChange,
  onToggleSortOrder,
}: PatientSortControlProps) {
  const handleToggleSortOrder = () => {
    const newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    onSortOrderChange(newOrder);
    onToggleSortOrder?.();
  };

  const getSortOrderLabel = (): string => {
    if (sortField === 'name') {
      return sortOrder === 'asc' ? 'A-Z' : 'Z-A';
    } else if (sortField === 'latest_session') {
      return sortOrder === 'desc' ? 'Newest First' : 'Oldest First';
    } else {
      return sortOrder === 'desc' ? 'Most' : 'Least';
    }
  };

  const SortIcon = sortOrder === 'asc' ? ArrowUp : ArrowDown;

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-muted-foreground">Sort:</span>
        <Select value={sortField} onValueChange={(value) => onSortFieldChange(value as PatientSortField)}>
          <SelectTrigger className="w-[170px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="name">Patient Name</SelectItem>
            <SelectItem value="latest_session">Latest Session</SelectItem>
            <SelectItem value="total_sessions">Total Sessions</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <Button
        variant="outline"
        size="sm"
        onClick={handleToggleSortOrder}
        title={`Sort order: ${getSortOrderLabel()}`}
        className="flex items-center gap-2"
      >
        <SortIcon className="w-4 h-4" />
        <span className="text-xs">{getSortOrderLabel()}</span>
      </Button>
    </div>
  );
}
