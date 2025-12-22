import { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { Play, Pause, Volume2, VolumeX, SkipBack, SkipForward } from 'lucide-react';
import Button from '@/components/ui/Button';
import { formatTime, getSpeakerColor } from '@/lib/utils';
import type { Segment } from '@/types/transcription';

interface AudioPlayerProps {
  audioUrl: string;
  filename?: string;
  segments?: Segment[];
  duration?: number;
  onTimeUpdate?: (time: number) => void;
  onSeek?: (time: number, shouldScroll: boolean) => void;
}

export default function AudioPlayer({ audioUrl, segments, duration: totalDuration, onTimeUpdate, onSeek }: AudioPlayerProps) {
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.7);
  const [isMuted, setIsMuted] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [hoveredSegmentIndex, setHoveredSegmentIndex] = useState<number | null>(null);

  // Initialize WaveSurfer
  useEffect(() => {
    if (!waveformRef.current) return;

    const wavesurfer = WaveSurfer.create({
      container: waveformRef.current,
      waveColor: '#94a3b8',
      progressColor: '#1e293b',
      cursorColor: '#0f172a',
      barWidth: 2,
      barGap: 1,
      barRadius: 2,
      height: 80,
      normalize: true,
      backend: 'WebAudio',
    });

    wavesurfer.load(audioUrl);

    // Event listeners
    wavesurfer.on('ready', () => {
      setDuration(wavesurfer.getDuration());
      setIsReady(true);
      wavesurfer.setVolume(volume);
    });

    wavesurfer.on('play', () => setIsPlaying(true));
    wavesurfer.on('pause', () => setIsPlaying(false));

    wavesurfer.on('audioprocess', () => {
      const time = wavesurfer.getCurrentTime();
      setCurrentTime(time);
      onTimeUpdate?.(time);
    });

    wavesurfer.on('interaction', () => {
      const time = wavesurfer.getCurrentTime();
      setCurrentTime(time);
      onTimeUpdate?.(time);
      // Trigger scroll on waveform click (interaction event)
      onSeek?.(time, true);
    });

    wavesurferRef.current = wavesurfer;

    return () => {
      wavesurfer.destroy();
    };
  }, [audioUrl]);

  // Update volume and mute state
  useEffect(() => {
    if (wavesurferRef.current) {
      wavesurferRef.current.setVolume(isMuted ? 0 : volume);
    }
  }, [volume, isMuted]);

  const handlePlayPause = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.playPause();
    }
  };

  const handleSkipBackward = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.skip(-10);
      const newTime = wavesurferRef.current.getCurrentTime();
      onSeek?.(newTime, true); // Scroll to new position
    }
  };

  const handleSkipForward = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.skip(10);
      const newTime = wavesurferRef.current.getCurrentTime();
      onSeek?.(newTime, true); // Scroll to new position
    }
  };

  const handleMuteToggle = () => {
    setIsMuted(!isMuted);
  };

  // Helper to find current segment index
  const getCurrentSegmentIndex = () => {
    if (!segments || segments.length === 0) return -1;
    return segments.findIndex(
      (seg) => currentTime >= seg.start && currentTime < seg.end
    );
  };

  // Navigate to previous segment
  const handlePrevSegment = () => {
    if (!segments || segments.length === 0 || !wavesurferRef.current) return;
    const currentIndex = getCurrentSegmentIndex();

    if (currentIndex === -1) {
      // Not in any segment, go to first segment
      const seekTime = segments[0].start;
      wavesurferRef.current.seekTo(seekTime / duration);
      onSeek?.(seekTime, true);
    } else if (currentIndex > 0) {
      // Go to previous segment
      const seekTime = segments[currentIndex - 1].start;
      wavesurferRef.current.seekTo(seekTime / duration);
      onSeek?.(seekTime, true);
    } else {
      // Already at first segment, go to its start
      const seekTime = segments[0].start;
      wavesurferRef.current.seekTo(seekTime / duration);
      onSeek?.(seekTime, true);
    }
  };

  // Navigate to next segment
  const handleNextSegment = () => {
    if (!segments || segments.length === 0 || !wavesurferRef.current) return;
    const currentIndex = getCurrentSegmentIndex();

    if (currentIndex === -1 || currentIndex >= segments.length - 1) {
      // Not in any segment or at last segment, go to last segment start
      const seekTime = segments[segments.length - 1].start;
      wavesurferRef.current.seekTo(seekTime / duration);
      onSeek?.(seekTime, true);
    } else {
      // Go to next segment
      const seekTime = segments[currentIndex + 1].start;
      wavesurferRef.current.seekTo(seekTime / duration);
      onSeek?.(seekTime, true);
    }
  };

  // Expose seek method for external use (e.g., transcript timestamp clicks)
  useEffect(() => {
    (window as any).seekAudio = (time: number) => {
      if (wavesurferRef.current && isReady) {
        const seekPosition = time / duration;
        wavesurferRef.current.seekTo(seekPosition);
      }
    };

    return () => {
      delete (window as any).seekAudio;
    };
  }, [isReady, duration]);

  // Spacebar play/pause
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Only trigger if not typing in an input/textarea
      const target = e.target as HTMLElement;
      if (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA') return;

      if (e.code === 'Space' && isReady) {
        e.preventDefault();
        handlePlayPause();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [isReady, isPlaying]);

  return (
    <div className="space-y-4">
      {/* Waveform with Colored Speaker Bars */}
      <div className="relative">
        {/* Speaker Color Bars (behind waveform) */}
        {segments && totalDuration && (
          <div className="absolute inset-0 flex rounded-lg overflow-hidden" style={{ height: '80px' }}>
            {segments.map((segment, index) => {
              const startPercent = (segment.start / totalDuration) * 100;
              const widthPercent = ((segment.end - segment.start) / totalDuration) * 100;
              const color = getSpeakerColor(segment.speaker_id || 'UNKNOWN');

              // Determine if this segment is currently playing
              const isPlaying = currentTime >= segment.start && currentTime < segment.end;
              const isHovered = hoveredSegmentIndex === index;

              // Calculate opacity: 30% normal, 55% for single state, 75% for both
              let opacity = 0.3; // Normal
              if (isHovered && isPlaying) {
                opacity = 0.75; // Both hovered and playing (brightest)
              } else if (isHovered || isPlaying) {
                opacity = 0.55; // Either hovered or playing
              }

              return (
                <div
                  key={index}
                  className="absolute h-full transition-opacity duration-200 cursor-pointer"
                  style={{
                    left: `${startPercent}%`,
                    width: `${widthPercent}%`,
                    backgroundColor: color,
                    opacity: opacity,
                  }}
                  onMouseEnter={() => setHoveredSegmentIndex(index)}
                  onMouseLeave={() => setHoveredSegmentIndex(null)}
                />
              );
            })}
          </div>
        )}

        {/* Waveform (on top of colored bars) */}
        <div
          ref={waveformRef}
          className="relative w-full bg-transparent rounded-lg"
          style={{ minHeight: '80px' }}
        />
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4">
        {/* Play/Pause and Skip Controls */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handlePrevSegment}
            disabled={!isReady || !segments || segments.length === 0}
            title="Previous segment"
          >
            <SkipBack className="h-4 w-4" />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleSkipBackward}
            disabled={!isReady}
            title="Skip backward 10 seconds"
            className="font-mono text-xs"
          >
            -10s
          </Button>

          <Button
            onClick={handlePlayPause}
            disabled={!isReady}
            size="lg"
            className="w-14 h-14 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-lg disabled:bg-gray-400"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? (
              <Pause className="h-6 w-6" />
            ) : (
              <Play className="h-6 w-6 ml-0.5" />
            )}
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleSkipForward}
            disabled={!isReady}
            title="Skip forward 10 seconds"
            className="font-mono text-xs"
          >
            +10s
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={handleNextSegment}
            disabled={!isReady || !segments || segments.length === 0}
            title="Next segment"
          >
            <SkipForward className="h-4 w-4" />
          </Button>
        </div>

        {/* Time Display */}
        <div className="flex-1">
          <div className="text-sm font-mono text-gray-600">
            {formatTime(currentTime)} / {formatTime(duration)}
          </div>
        </div>

        {/* Volume Control */}
        <div className="flex items-center gap-2 min-w-[140px]">
          <button
            onClick={handleMuteToggle}
            className="flex-shrink-0 p-1 hover:bg-gray-100 rounded transition-colors"
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? (
              <VolumeX className="h-4 w-4 text-red-600" />
            ) : (
              <Volume2 className="h-4 w-4 text-gray-600" />
            )}
          </button>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={isMuted ? 0 : volume}
            onChange={(e) => {
              const newVolume = parseFloat(e.target.value);
              setVolume(newVolume);
              if (isMuted && newVolume > 0) {
                setIsMuted(false);
              }
            }}
            className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary"
            title={`Volume: ${Math.round(volume * 100)}%`}
          />
        </div>
      </div>
    </div>
  );
}
