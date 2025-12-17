import { Badge } from './ui/badge';
import type { SessionStatus } from '@/lib/types';
import { Loader2 } from 'lucide-react';

interface SessionStatusBadgeProps {
  status: SessionStatus;
  className?: string;
}

export function SessionStatusBadge({ status, className }: SessionStatusBadgeProps) {
  const config = {
    uploading: {
      label: 'Uploading',
      className: 'bg-blue-100 text-blue-800 border-blue-200',
      icon: <Loader2 className="w-3 h-3 animate-spin mr-1" />,
    },
    transcribing: {
      label: 'Transcribing',
      className: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      icon: <Loader2 className="w-3 h-3 animate-spin mr-1" />,
    },
    transcribed: {
      label: 'Transcribed',
      className: 'bg-purple-100 text-purple-800 border-purple-200',
      icon: null,
    },
    extracting_notes: {
      label: 'Extracting Notes',
      className: 'bg-purple-100 text-purple-800 border-purple-200',
      icon: <Loader2 className="w-3 h-3 animate-spin mr-1" />,
    },
    processed: {
      label: 'Processed',
      className: 'bg-green-100 text-green-800 border-green-200',
      icon: null,
    },
    failed: {
      label: 'Failed',
      className: 'bg-red-100 text-red-800 border-red-200',
      icon: null,
    },
  };

  const { label, className: statusClassName, icon } = config[status];

  return (
    <Badge variant="outline" className={`${statusClassName} ${className || ''}`}>
      {icon}
      {label}
    </Badge>
  );
}
