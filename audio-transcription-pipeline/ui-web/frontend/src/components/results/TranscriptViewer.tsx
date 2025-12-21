import { useState, useMemo, useRef, useImperativeHandle, forwardRef } from 'react';
import { Search, User } from 'lucide-react';
import type { Segment, Speaker } from '@/types/transcription';
import { formatTime, getSpeakerColor } from '@/lib/utils';

interface TranscriptViewerProps {
  segments: Segment[];
  speakers: Speaker[];
  currentTime?: number;
  onTimestampClick?: (time: number) => void;
}

export interface TranscriptViewerRef {
  scrollToTime: (time: number) => void;
}

const TranscriptViewer = forwardRef<TranscriptViewerRef, TranscriptViewerProps>(
  function TranscriptViewer({ segments, speakers, currentTime = 0, onTimestampClick }, ref) {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedSpeaker, setSelectedSpeaker] = useState<string | null>(null);
    const segmentRefs = useRef<(HTMLDivElement | null)[]>([]);
    const containerRef = useRef<HTMLDivElement>(null);

  // Filter segments based on search and speaker
  const filteredSegments = useMemo(() => {
    return segments.filter((segment) => {
      const matchesSearch = searchQuery
        ? segment.text.toLowerCase().includes(searchQuery.toLowerCase())
        : true;

      const matchesSpeaker = selectedSpeaker
        ? segment.speaker_id === selectedSpeaker
        : true;

      return matchesSearch && matchesSpeaker;
    });
  }, [segments, searchQuery, selectedSpeaker]);

  // Expose scrollToTime method to parent
  useImperativeHandle(ref, () => ({
    scrollToTime: (time: number) => {
      // Find the segment that contains this time
      const segmentIndex = filteredSegments.findIndex(
        (seg) => time >= seg.start && time <= seg.end
      );

      if (segmentIndex !== -1 && segmentRefs.current[segmentIndex] && containerRef.current) {
        const segmentElement = segmentRefs.current[segmentIndex];
        const container = containerRef.current;

        // Calculate scroll position to center the segment in the container
        const segmentTop = segmentElement!.offsetTop;
        const segmentHeight = segmentElement!.offsetHeight;
        const containerHeight = container.offsetHeight;
        const scrollTop = segmentTop - (containerHeight / 2) + (segmentHeight / 2);

        // Smooth scroll within container only (doesn't scroll the page)
        container.scrollTo({
          top: scrollTop,
          behavior: 'smooth',
        });
      }
    },
  }));

  // Get speaker label
  const getSpeakerLabel = (speakerId?: string): string => {
    if (!speakerId) return 'Unknown';
    const speaker = speakers.find((s) => s.id === speakerId);
    return speaker?.label || speakerId;
  };

  return (
    <div className="space-y-4">
      {/* Search and Filter Bar */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search transcript..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>

        {/* Speaker Filter */}
        <select
          value={selectedSpeaker || ''}
          onChange={(e) => setSelectedSpeaker(e.target.value || null)}
          className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
        >
          <option value="">All Speakers</option>
          {speakers.map((speaker) => (
            <option key={speaker.id} value={speaker.id}>
              {speaker.label}
            </option>
          ))}
        </select>
      </div>

      {/* Results Count */}
      {(searchQuery || selectedSpeaker) && (
        <p className="text-sm text-gray-500">
          Showing {filteredSegments.length} of {segments.length} segments
        </p>
      )}

      {/* Transcript Segments */}
      <div ref={containerRef} className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
        {filteredSegments.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p>No segments found</p>
          </div>
        ) : (
          filteredSegments.map((segment, index) => {
            const speakerColor = getSpeakerColor(segment.speaker_id || 'UNKNOWN');
            const isActive = currentTime >= segment.start && currentTime <= segment.end;

            return (
              <div
                key={index}
                ref={(el) => (segmentRefs.current[index] = el)}
                className={`group flex gap-3 p-4 border rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-primary/10 border-primary ring-2 ring-primary/30 shadow-md'
                    : 'bg-white border-gray-200 hover:border-gray-300'
                }`}
              >
                {/* Speaker Avatar */}
                <div
                  className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-white font-medium text-sm"
                  style={{ backgroundColor: speakerColor }}
                >
                  <User className="h-5 w-5" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  {/* Header */}
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <span
                      className="font-medium text-sm"
                      style={{ color: speakerColor }}
                    >
                      {getSpeakerLabel(segment.speaker_id)}
                    </span>
                    <button
                      onClick={() => onTimestampClick?.(segment.start)}
                      className="text-xs text-gray-600 hover:text-primary hover:bg-primary/10 font-mono transition-all px-2 py-1 rounded border border-transparent hover:border-primary/30 cursor-pointer"
                      title="Click to jump to audio timestamp"
                    >
                      {formatTime(segment.start)} → {formatTime(segment.end)}
                    </button>
                  </div>

                  {/* Text */}
                  <p className="text-gray-800 leading-relaxed">
                    {highlightSearchQuery(segment.text, searchQuery)}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
});

export default TranscriptViewer;

// Helper function to highlight search query
function highlightSearchQuery(text: string, query: string): React.ReactNode {
  if (!query) return text;

  const parts = text.split(new RegExp(`(${query})`, 'gi'));
  return parts.map((part, i) =>
    part.toLowerCase() === query.toLowerCase() ? (
      <mark key={i} className="bg-yellow-200 px-1 rounded">
        {part}
      </mark>
    ) : (
      part
    )
  );
}
