import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import type { Strategy } from '@/lib/types';

interface StrategyCardProps {
  strategy: Strategy;
}

const categoryColors = {
  breathing: 'bg-blue-100 text-blue-800 border-blue-200',
  cognitive: 'bg-purple-100 text-purple-800 border-purple-200',
  behavioral: 'bg-green-100 text-green-800 border-green-200',
  mindfulness: 'bg-teal-100 text-teal-800 border-teal-200',
  interpersonal: 'bg-pink-100 text-pink-800 border-pink-200',
};

const statusLabels = {
  introduced: 'Introduced',
  practiced: 'Practiced',
  assigned: 'Assigned',
  reviewed: 'Reviewed',
};

export function StrategyCard({ strategy }: StrategyCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <CardTitle className="text-base">{strategy.name}</CardTitle>
          <Badge variant="outline" className={categoryColors[strategy.category]}>
            {strategy.category}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <Badge variant="secondary" className="text-xs">
            {statusLabels[strategy.status]}
          </Badge>
          <p className="text-sm text-muted-foreground">{strategy.context}</p>
        </div>
      </CardContent>
    </Card>
  );
}

export type { StrategyCardProps };
