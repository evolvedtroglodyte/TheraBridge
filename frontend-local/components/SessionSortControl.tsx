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
import type { SortField, SortOrder } from '@/hooks/useSessionSort';

interface SessionSortControlProps {
  sortField: SortField;
  sortOrder: SortOrder;
  onSortFieldChange: (field: SortField) => void;
  onSortOrderChange: (order: SortOrder) => void;
  onToggleSortOrder?: () => void;
}

export function SessionSortControl({
  sortField,
  sortOrder,
  onSortFieldChange,
  onSortOrderChange,
  onToggleSortOrder,
}: SessionSortControlProps) {
  const handleToggleSortOrder = () => {
    const newOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    onSortOrderChange(newOrder);
    onToggleSortOrder?.();
  };

  const getSortOrderLabel = (): string => {
    if (sortField === 'date') {
      return sortOrder === 'desc' ? 'Newest First' : 'Oldest First';
    } else if (sortField === 'patient_name') {
      return sortOrder === 'asc' ? 'A-Z' : 'Z-A';
    } else {
      return sortOrder === 'asc' ? 'A-Z' : 'Z-A';
    }
  };

  const SortIcon = sortOrder === 'asc' ? ArrowUp : ArrowDown;

  return (
    <div className="flex items-center gap-2">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-muted-foreground">Sort:</span>
        <Select value={sortField} onValueChange={(value) => onSortFieldChange(value as SortField)}>
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="date">Date</SelectItem>
            <SelectItem value="patient_name">Patient Name</SelectItem>
            <SelectItem value="status">Status</SelectItem>
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
