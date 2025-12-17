import type { SessionMood, MoodTrajectory } from '@/lib/types';
import { TrendingUp, TrendingDown, Minus, ArrowUpDown } from 'lucide-react';

interface MoodIndicatorProps {
  mood: SessionMood;
  trajectory?: MoodTrajectory;
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function MoodIndicator({ mood, trajectory, showLabel = true, size = 'md' }: MoodIndicatorProps) {
  const moodConfig = {
    very_low: {
      emoji: '😢',
      label: 'Very Low',
      color: 'bg-red-600',
      textColor: 'text-red-700',
    },
    low: {
      emoji: '😔',
      label: 'Low',
      color: 'bg-orange-500',
      textColor: 'text-orange-700',
    },
    neutral: {
      emoji: '😐',
      label: 'Neutral',
      color: 'bg-gray-400',
      textColor: 'text-gray-700',
    },
    positive: {
      emoji: '🙂',
      label: 'Positive',
      color: 'bg-green-400',
      textColor: 'text-green-700',
    },
    very_positive: {
      emoji: '😊',
      label: 'Very Positive',
      color: 'bg-green-600',
      textColor: 'text-green-700',
    },
  };

  const trajectoryConfig = {
    improving: { icon: TrendingUp, label: 'Improving', color: 'text-green-600' },
    declining: { icon: TrendingDown, label: 'Declining', color: 'text-red-600' },
    stable: { icon: Minus, label: 'Stable', color: 'text-gray-600' },
    fluctuating: { icon: ArrowUpDown, label: 'Fluctuating', color: 'text-orange-600' },
  };

  const { emoji, label, color, textColor } = moodConfig[mood];
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  const TrajectoryIcon = trajectory ? trajectoryConfig[trajectory].icon : null;

  return (
    <div className="flex items-center gap-2">
      <div className={`flex items-center justify-center ${sizeClasses[size]} ${color} rounded-full`}>
        <span className="text-xs">{emoji}</span>
      </div>
      {showLabel && (
        <div className="flex flex-col">
          <span className={`text-sm font-medium ${textColor}`}>{label}</span>
          {trajectory && TrajectoryIcon && (
            <div className={`flex items-center gap-1 text-xs ${trajectoryConfig[trajectory].color}`}>
              <TrajectoryIcon className="w-3 h-3" />
              <span>{trajectoryConfig[trajectory].label}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
