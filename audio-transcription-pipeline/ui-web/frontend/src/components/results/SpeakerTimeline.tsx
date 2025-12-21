import { useState } from 'react';
import type { Segment, Speaker } from '@/types/transcription';
import { formatTime, getSpeakerColor } from '@/lib/utils';

interface SpeakerTimelineProps {
  segments: Segment[];
  speakers: Speaker[];
  duration: number;
  onSegmentClick?: (time: number) => void;
}

export default function SpeakerTimeline({
  segments,
  speakers,
  duration,
  onSegmentClick,
}: SpeakerTimelineProps) {
  const [hoveredSegment, setHoveredSegment] = useState<Segment | null>(null);

  // Get speaker label
  const getSpeakerLabel = (speakerId?: string): string => {
    if (!speakerId) return 'Unknown';
    const speaker = speakers.find((s) => s.id === speakerId);
    return speaker?.label || speakerId;
  };

  return (
    <div className="space-y-4">
      {/* Timeline Container */}
      <div className="relative h-24 bg-gray-100 rounded-lg overflow-hidden">
        {/* Timeline Segments */}
        {segments.map((segment, index) => {
          const startPercent = (segment.start / duration) * 100;
          const widthPercent = ((segment.end - segment.start) / duration) * 100;
          const speakerColor = getSpeakerColor(segment.speaker_id || 'UNKNOWN');

          return (
            <div
              key={index}
              className="absolute top-0 h-full cursor-pointer transition-opacity hover:opacity-80"
              style={{
                left: `${startPercent}%`,
                width: `${widthPercent}%`,
                backgroundColor: speakerColor,
              }}
              onClick={() => onSegmentClick?.(segment.start)}
              onMouseEnter={() => setHoveredSegment(segment)}
              onMouseLeave={() => setHoveredSegment(null)}
              title={`${getSpeakerLabel(segment.speaker_id)}: ${segment.text.substring(0, 50)}...`}
            />
          );
        })}

        {/* Time Markers */}
        <div className="absolute inset-0 pointer-events-none">
          {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
            <div
              key={fraction}
              className="absolute top-0 bottom-0 border-l border-white/30"
              style={{ left: `${fraction * 100}%` }}
            />
          ))}
        </div>
      </div>

      {/* Time Labels */}
      <div className="flex justify-between text-xs text-gray-500 font-mono">
        {[0, 0.25, 0.5, 0.75, 1].map((fraction) => (
          <span key={fraction}>{formatTime(duration * fraction)}</span>
        ))}
      </div>

      {/* Hover Tooltip */}
      {hoveredSegment && (
        <div className="p-3 bg-gray-900 text-white rounded-lg text-sm">
          <div className="flex items-center gap-2 mb-1">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: getSpeakerColor(hoveredSegment.speaker_id || 'UNKNOWN') }}
            />
            <span className="font-medium">
              {getSpeakerLabel(hoveredSegment.speaker_id)}
            </span>
            <span className="text-gray-400 font-mono text-xs">
              {formatTime(hoveredSegment.start)} - {formatTime(hoveredSegment.end)}
            </span>
          </div>
          <p className="text-gray-200 line-clamp-2">
            {hoveredSegment.text}
          </p>
        </div>
      )}

      {/* Speaker Legend */}
      <div className="flex flex-wrap gap-3">
        {speakers.map((speaker) => (
          <div key={speaker.id} className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: getSpeakerColor(speaker.id) }}
            />
            <span className="text-sm text-gray-700">{speaker.label}</span>
            <span className="text-xs text-gray-500">
              ({speaker.segment_count} segments, {formatTime(speaker.total_duration)})
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
