'use client';

import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search, X } from 'lucide-react';

interface SessionSearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onClear?: () => void;
  placeholder?: string;
  className?: string;
  hasActiveSearch?: boolean;
  resultCount?: number;
}

export function SessionSearchInput({
  value,
  onChange,
  onClear,
  placeholder = 'Search sessions by date or keywords...',
  className = '',
  hasActiveSearch = false,
  resultCount = 0,
}: SessionSearchInputProps) {
  const [displayValue, setDisplayValue] = useState(value);

  useEffect(() => {
    setDisplayValue(value);
  }, [value]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setDisplayValue(newValue);
    onChange(newValue);
  };

  const handleClear = () => {
    setDisplayValue('');
    if (onClear) {
      onClear();
    } else {
      onChange('');
    }
  };

  return (
    <div className={`space-y-2 ${className}`}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder={placeholder}
          value={displayValue}
          onChange={handleInputChange}
          className="pl-10 pr-10"
          aria-label="Search sessions"
        />
        {displayValue && (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 p-0"
            onClick={handleClear}
            aria-label="Clear search"
          >
            <X className="w-4 h-4" />
          </Button>
        )}
      </div>
      {hasActiveSearch && (
        <p className="text-xs text-muted-foreground">
          Found {resultCount} session{resultCount !== 1 ? 's' : ''}
        </p>
      )}
    </div>
  );
}

export type { SessionSearchInputProps };
