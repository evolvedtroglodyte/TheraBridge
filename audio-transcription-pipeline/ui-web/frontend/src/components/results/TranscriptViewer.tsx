import { useState, useMemo, useRef, useImperativeHandle, forwardRef, useEffect } from 'react';
import { Search, User, MousePointerClick, MoveVertical } from 'lucide-react';
import type { Segment, Speaker } from '@/types/transcription';
import { formatTime, getSpeakerColor } from '@/lib/utils';
import TranscriptTooltip from './TranscriptTooltip';

interface TranscriptViewerProps {
  segments: Segment[];
  speakers: Speaker[];
  alignedSegments?: Segment[]; // Granular segments for highlighting
  currentTime?: number;
  onTimestampClick?: (time: number) => void;
}

export interface TranscriptViewerRef {
  scrollToTime: (time: number) => void;
}

const TranscriptViewer = forwardRef<TranscriptViewerRef, TranscriptViewerProps>(
  function TranscriptViewer({ segments, speakers, alignedSegments, currentTime = 0, onTimestampClick }, ref) {
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedSpeaker, setSelectedSpeaker] = useState<string | null>(null);
    const segmentRefs = useRef<(HTMLDivElement | null)[]>([]);
    const containerRef = useRef<HTMLDivElement>(null);

    // Toggle states (persisted in localStorage)
    const [autoScrollEnabled, setAutoScrollEnabled] = useState(() => {
      const saved = localStorage.getItem('transcript-auto-scroll');
      return saved !== null ? JSON.parse(saved) : true; // Default: enabled
    });
    const [clickScrollEnabled, setClickScrollEnabled] = useState(() => {
      const saved = localStorage.getItem('transcript-click-scroll');
      return saved !== null ? JSON.parse(saved) : true; // Default: enabled
    });

    // Tooltip state
    const [tooltip, setTooltip] = useState<{
      show: boolean;
      message: string;
      type: 'auto-scroll-enabled' | 'auto-scroll-disabled' | 'click-scroll-enabled' | 'click-scroll-disabled' | 'auto-scroll-paused';
    }>({ show: false, message: '', type: 'auto-scroll-enabled' });

    // Auto-scroll pause state
    const [autoScrollPaused, setAutoScrollPaused] = useState(false);
    const lastManualScrollTime = useRef<number>(0);
    const autoScrollResumeTimer = useRef<NodeJS.Timeout | null>(null);

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

  // Persist toggle states to localStorage
  useEffect(() => {
    localStorage.setItem('transcript-auto-scroll', JSON.stringify(autoScrollEnabled));
  }, [autoScrollEnabled]);

  useEffect(() => {
    localStorage.setItem('transcript-click-scroll', JSON.stringify(clickScrollEnabled));
  }, [clickScrollEnabled]);

  // Toggle handlers
  const handleAutoScrollToggle = () => {
    const newValue = !autoScrollEnabled;
    setAutoScrollEnabled(newValue);

    // Auto-scroll enables click-to-scroll
    if (newValue && !clickScrollEnabled) {
      setClickScrollEnabled(true);
      showTooltip('Click scrolling enabled', 'click-scroll-enabled');
      setTimeout(() => {
        showTooltip(newValue ? 'Auto-scroll enabled' : 'Auto-scroll disabled', newValue ? 'auto-scroll-enabled' : 'auto-scroll-disabled');
      }, 100);
    } else {
      showTooltip(newValue ? 'Auto-scroll enabled' : 'Auto-scroll disabled', newValue ? 'auto-scroll-enabled' : 'auto-scroll-disabled');
    }
  };

  const handleClickScrollToggle = () => {
    const newValue = !clickScrollEnabled;
    setClickScrollEnabled(newValue);

    // Disabling click-to-scroll disables auto-scroll
    if (!newValue && autoScrollEnabled) {
      setAutoScrollEnabled(false);
      showTooltip('Auto-scroll disabled', 'auto-scroll-disabled');
      setTimeout(() => {
        showTooltip('Click scrolling disabled', 'click-scroll-disabled');
      }, 100);
    } else {
      showTooltip(newValue ? 'Click scrolling enabled' : 'Click scrolling disabled', newValue ? 'click-scroll-enabled' : 'click-scroll-disabled');
    }
  };

  const showTooltip = (message: string, type: typeof tooltip.type) => {
    setTooltip({ show: true, message, type });
  };

  const hideTooltip = () => {
    setTooltip((prev) => ({ ...prev, show: false }));
  };

  // Auto-scroll functionality: scroll to center active segment
  useEffect(() => {
    if (!autoScrollEnabled || autoScrollPaused || !containerRef.current) return;

    // Find the currently playing segment
    const activeIndex = filteredSegments.findIndex(
      (seg) => currentTime >= seg.start && currentTime < seg.end
    );

    if (activeIndex !== -1 && segmentRefs.current[activeIndex]) {
      const segmentElement = segmentRefs.current[activeIndex];
      const container = containerRef.current;

      // Calculate scroll position to center the segment
      const segmentTop = segmentElement!.offsetTop;
      const segmentHeight = segmentElement!.offsetHeight;
      const containerHeight = container.offsetHeight;
      const scrollTop = segmentTop - (containerHeight / 2) + (segmentHeight / 2);

      // Smooth scroll to center the active segment
      container.scrollTo({
        top: scrollTop,
        behavior: 'smooth',
      });
    }
  }, [currentTime, filteredSegments, autoScrollEnabled, autoScrollPaused]);

  // Detect manual scrolling and pause auto-scroll
  useEffect(() => {
    const container = containerRef.current;
    if (!container || !autoScrollEnabled) return;

    const handleScroll = () => {
      const now = Date.now();
      const timeSinceLastManualScroll = now - lastManualScrollTime.current;

      // Only treat as manual scroll if it's been more than 500ms since last auto-scroll
      // (This prevents auto-scroll from triggering the pause logic)
      if (timeSinceLastManualScroll > 500) {
        lastManualScrollTime.current = now;

        // Pause auto-scroll
        if (!autoScrollPaused) {
          setAutoScrollPaused(true);
          showTooltip('Auto-scroll paused (resumes in 5s)', 'auto-scroll-paused');
        }

        // Clear existing timer
        if (autoScrollResumeTimer.current) {
          clearTimeout(autoScrollResumeTimer.current);
        }

        // Resume auto-scroll after 5 seconds
        autoScrollResumeTimer.current = setTimeout(() => {
          setAutoScrollPaused(false);
          autoScrollResumeTimer.current = null;
        }, 5000);
      }
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      container.removeEventListener('scroll', handleScroll);
      if (autoScrollResumeTimer.current) {
        clearTimeout(autoScrollResumeTimer.current);
      }
    };
  }, [autoScrollEnabled, autoScrollPaused]);

  // Expose scrollToTime method to parent
  useImperativeHandle(ref, () => ({
    scrollToTime: (time: number) => {
      // Respect click-to-scroll toggle
      if (!clickScrollEnabled) return;

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

        // Update last manual scroll time to prevent pause detection
        lastManualScrollTime.current = Date.now();

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

        {/* Toggle Controls */}
        <div className="flex items-center gap-2">
          {/* Auto-scroll Toggle */}
          <button
            onClick={handleAutoScrollToggle}
            onMouseEnter={(e) => {
              const btn = e.currentTarget;
              const pulse = btn.querySelector('.pulse-animation');
              if (pulse) (pulse as HTMLElement).style.animationPlayState = 'paused';
            }}
            onMouseLeave={(e) => {
              const btn = e.currentTarget;
              const pulse = btn.querySelector('.pulse-animation');
              if (pulse && autoScrollEnabled) (pulse as HTMLElement).style.animationPlayState = 'running';
            }}
            className={`relative p-2 rounded-lg border transition-all ${
              autoScrollEnabled
                ? 'bg-green-100 border-green-300 text-green-700'
                : 'bg-gray-100 border-gray-300 text-gray-600'
            }`}
            title={autoScrollEnabled ? 'Auto-scroll enabled' : 'Auto-scroll disabled'}
          >
            <MoveVertical className="h-4 w-4" />
            {autoScrollEnabled && (
              <span className="pulse-animation absolute inset-0 rounded-lg bg-green-500 opacity-20 animate-ping" />
            )}
          </button>

          {/* Click-to-scroll Toggle */}
          <button
            onClick={handleClickScrollToggle}
            className={`p-2 rounded-lg border transition-all ${
              clickScrollEnabled
                ? 'bg-blue-100 border-blue-300 text-blue-700'
                : 'bg-gray-100 border-gray-300 text-gray-600'
            }`}
            title={clickScrollEnabled ? 'Click scrolling enabled' : 'Click scrolling disabled'}
          >
            <MousePointerClick className="h-4 w-4" />
          </button>
        </div>
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

            // Use aligned_segments for highlighting if available, otherwise use combined segments
            const highlightSegments = alignedSegments || segments;
            // Find if any granular segment within this combined segment is currently playing
            const isActive = highlightSegments.some(
              (alignedSeg) =>
                currentTime >= alignedSeg.start &&
                currentTime < alignedSeg.end &&
                alignedSeg.start >= segment.start &&
                alignedSeg.end <= segment.end
            );

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

      {/* Tooltip */}
      <TranscriptTooltip
        message={tooltip.message}
        type={tooltip.type}
        show={tooltip.show}
        onHide={hideTooltip}
      />
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
