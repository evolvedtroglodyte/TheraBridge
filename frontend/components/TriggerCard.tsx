import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { AlertTriangle } from 'lucide-react';
import type { Trigger } from '@/lib/types';

interface TriggerCardProps {
  trigger: Trigger;
}

const severityConfig = {
  mild: {
    className: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    label: 'Mild',
  },
  moderate: {
    className: 'bg-orange-100 text-orange-800 border-orange-200',
    label: 'Moderate',
  },
  severe: {
    className: 'bg-red-100 text-red-800 border-red-200',
    label: 'Severe',
  },
};

export function TriggerCard({ trigger }: TriggerCardProps) {
  const { className, label } = severityConfig[trigger.severity];

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-orange-600" />
            <CardTitle className="text-base">{trigger.trigger}</CardTitle>
          </div>
          <Badge variant="outline" className={className}>
            {label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">{trigger.context}</p>
      </CardContent>
    </Card>
  );
}
