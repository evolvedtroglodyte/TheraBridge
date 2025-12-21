import { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';
import { Play, Pause, Volume2, VolumeX } from 'lucide-react';
import Button from '@/components/ui/Button';
import { formatTime, getSpeakerColor } from '@/lib/utils';
import type { Segment } from '@/types/transcription';

interface AudioPlayerProps {
  audioUrl: string;
  filename?: string;
  segments?: Segment[];
  duration?: number;
  onTimeUpdate?: (time: number) => void;
}

export default function AudioPlayer({ audioUrl, filename, segments, duration: totalDuration, onTimeUpdate }: AudioPlayerProps) {
  const waveformRef = useRef<HTMLDivElement>(null);
  const wavesurferRef = useRef<WaveSurfer | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(0.7);
  const [isMuted, setIsMuted] = useState(false);
  const [isReady, setIsReady] = useState(false);

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

    wavesurfer.on('seek', () => {
      const time = wavesurfer.getCurrentTime();
      setCurrentTime(time);
      onTimeUpdate?.(time);
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
    }
  };

  const handleSkipForward = () => {
    if (wavesurferRef.current) {
      wavesurferRef.current.skip(10);
    }
  };

  const handleMuteToggle = () => {
    setIsMuted(!isMuted);
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

              return (
                <div
                  key={index}
                  className="absolute h-full opacity-30"
                  style={{
                    left: `${startPercent}%`,
                    width: `${widthPercent}%`,
                    backgroundColor: color,
                  }}
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
            className="w-12 h-12 rounded-full"
            title={isPlaying ? 'Pause' : 'Play'}
          >
            {isPlaying ? (
              <Pause className="h-5 w-5" />
            ) : (
              <Play className="h-5 w-5 ml-0.5" />
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
