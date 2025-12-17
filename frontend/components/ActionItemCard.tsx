'use client';

import { useState } from 'react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Checkbox } from './ui/checkbox';
import type { ActionItem } from '@/lib/types';

interface ActionItemCardProps {
  actionItem: ActionItem;
  initialCompleted?: boolean;
}

export function ActionItemCard({ actionItem, initialCompleted = false }: ActionItemCardProps) {
  const [completed, setCompleted] = useState(initialCompleted);

  return (
    <Card className={completed ? 'opacity-60' : ''}>
      <CardContent className="pt-6">
        <div className="flex items-start gap-3">
          <Checkbox
            checked={completed}
            onCheckedChange={(checked) => setCompleted(!!checked)}
            className="mt-1"
          />
          <div className="flex-1 space-y-2">
            <p className={`text-sm font-medium ${completed ? 'line-through' : ''}`}>
              {actionItem.task}
            </p>
            <Badge variant="secondary" className="text-xs">
              {actionItem.category}
            </Badge>
            <p className="text-sm text-muted-foreground">{actionItem.details}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
