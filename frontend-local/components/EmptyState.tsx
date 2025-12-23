'use client';

import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  /** Icon component from lucide-react */
  icon: LucideIcon;
  /** Main heading text */
  heading: string;
  /** Description text */
  description: string;
  /** Optional action button label */
  actionLabel?: string;
  /** Optional action button handler */
  onAction?: () => void;
  /** Optional action button variant */
  actionVariant?: 'default' | 'outline' | 'secondary' | 'ghost' | 'link' | 'destructive';
  /** Optional custom className for the container */
  className?: string;
  /** Optional custom className for the icon */
  iconClassName?: string;
  /** Show within a card or as standalone */
  showCard?: boolean;
  /** Icon size variant */
  iconSize?: 'sm' | 'md' | 'lg';
}

const iconSizeMap = {
  sm: 'w-8 h-8',
  md: 'w-12 h-12',
  lg: 'w-16 h-16',
};

export function EmptyState({
  icon: Icon,
  heading,
  description,
  actionLabel,
  onAction,
  actionVariant = 'default',
  className,
  iconClassName,
  showCard = true,
  iconSize = 'lg',
}: EmptyStateProps) {
  const content = (
    <div className={cn('flex flex-col items-center justify-center gap-4 py-12', className)}>
      <div
        className={cn(
          'text-muted-foreground',
          iconSizeMap[iconSize],
          iconClassName
        )}
      >
        <Icon className="w-full h-full" />
      </div>
      <div className="text-center space-y-2 max-w-sm">
        <h3 className="text-lg font-semibold">{heading}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {actionLabel && onAction && (
        <Button variant={actionVariant} onClick={onAction} className="mt-4">
          {actionLabel}
        </Button>
      )}
    </div>
  );

  if (showCard) {
    return (
      <Card>
        <CardContent>{content}</CardContent>
      </Card>
    );
  }

  return content;
}

export type { EmptyStateProps };
