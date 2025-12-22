import { useEffect, useState, useRef } from 'react';
import { AlertCircle, RefreshCw, ArrowLeft, FileAudio, Clock, Zap, Users } from 'lucide-react';
import Card, { CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import Badge from '@/components/ui/Badge';
import Spinner from '@/components/ui/Spinner';
import AudioPlayer from './AudioPlayer';
import TranscriptViewer, { TranscriptViewerRef } from './TranscriptViewer';
import SpeakerTimeline from './SpeakerTimeline';
import ExportOptions from './ExportOptions';
import { useTranscription } from '@/hooks/useTranscription';
import { formatTime, formatFileSize } from '@/lib/utils';

interface ResultsViewProps {
  jobId: string;
  uploadedFile: File;
  onReset: () => void;
}

export default function ResultsView({ jobId, uploadedFile, onReset }: ResultsViewProps) {
  const { result, loading, error, refetch } = useTranscription(jobId);
  const [audioUrl, setAudioUrl] = useState<string>('');
  const [currentAudioTime, setCurrentAudioTime] = useState(0);
  const transcriptRef = useRef<TranscriptViewerRef>(null);

  // Create audio URL from uploaded file
  useEffect(() => {
    const url = URL.createObjectURL(uploadedFile);
    setAudioUrl(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [uploadedFile]);

  // Handle timestamp click - seek audio player
  const handleTimestampClick = (time: number) => {
    if ((window as any).seekAudio) {
      (window as any).seekAudio(time);
    }
  };

  // Handle timeline segment click - scroll to transcript and seek audio
  const handleTimelineSegmentClick = (time: number) => {
    // Scroll transcript viewer to this segment
    transcriptRef.current?.scrollToTime(time);
    // Also seek audio player
    handleTimestampClick(time);
  };

  // Handle audio seek (from buttons like +10s, -10s, prev/next segment)
  const handleAudioSeek = (time: number, shouldScroll: boolean) => {
    if (shouldScroll) {
      transcriptRef.current?.scrollToTime(time);
    }
  };

  // Handle audio time updates (for highlighting AND scrolling)
  const handleAudioTimeUpdate = (time: number) => {
    console.log('[ResultsView] Audio time update:', time);
    setCurrentAudioTime(time);
    // Only scroll on waveform click, not continuous updates
  };


  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <Card>
          <CardContent className="py-12">
            <Spinner size="lg" />
            <p className="text-center text-gray-500 mt-4">Loading transcription results...</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center gap-4">
              <AlertCircle className="h-12 w-12 text-red-600" />
              <div className="text-center">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  Failed to Load Results
                </h3>
                <p className="text-gray-600 mb-4">{error}</p>
                <div className="flex gap-3 justify-center">
                  <Button onClick={refetch} variant="outline">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Retry
                  </Button>
                  <Button onClick={onReset}>
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Start Over
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (!result) {
    return null;
  }

  const duration = result.metadata?.duration || 0;
  const processingTime = result.performance?.total_processing_time_seconds || 0;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header Actions */}
      <div className="flex items-center justify-between">
        <Button onClick={onReset} variant="outline">
          <ArrowLeft className="h-4 w-4 mr-2" />
          New Transcription
        </Button>
        <ExportOptions result={result} />
      </div>

      {/* Metadata Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileAudio className="h-6 w-6" />
            {uploadedFile.name}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-start gap-3">
              <Clock className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-500">Duration</p>
                <p className="font-medium">{formatTime(duration)}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Zap className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-500">Processing Time</p>
                <p className="font-medium">{formatTime(processingTime)}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Users className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-500">Speakers</p>
                <p className="font-medium">{result.speakers.length}</p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <FileAudio className="h-5 w-5 text-gray-400 mt-0.5" />
              <div>
                <p className="text-sm text-gray-500">File Size</p>
                <p className="font-medium">
                  {result.metadata?.file_size_mb
                    ? `${result.metadata.file_size_mb.toFixed(2)} MB`
                    : formatFileSize(uploadedFile.size)}
                </p>
              </div>
            </div>
          </div>

          {result.metadata && (
            <div className="mt-4 pt-4 border-t">
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">
                  Language: {result.metadata.language}
                </Badge>
                <Badge variant="secondary">
                  Pipeline: {result.metadata.pipeline_type}
                </Badge>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Audio Player Card */}
      <Card>
        <CardHeader>
          <CardTitle>Audio Playback</CardTitle>
        </CardHeader>
        <CardContent>
          <AudioPlayer
            audioUrl={audioUrl}
            filename={uploadedFile.name}
            segments={result.segments}
            duration={duration}
            onTimeUpdate={handleAudioTimeUpdate}
            onSeek={handleAudioSeek}
          />
        </CardContent>
      </Card>

      {/* Speaker Timeline Card */}
      <Card>
        <CardHeader>
          <CardTitle>Speaker Timeline</CardTitle>
        </CardHeader>
        <CardContent>
          <SpeakerTimeline
            segments={result.segments}
            speakers={result.speakers}
            duration={duration}
            onSegmentClick={handleTimelineSegmentClick}
          />
        </CardContent>
      </Card>

      {/* Transcript Card */}
      <Card>
        <CardHeader>
          <CardTitle>
            Transcript ({result.segments.length} segments)
          </CardTitle>
        </CardHeader>
        <CardContent>
          <TranscriptViewer
            ref={transcriptRef}
            segments={result.segments}
            speakers={result.speakers}
            alignedSegments={result.aligned_segments}
            currentTime={currentAudioTime}
            onTimestampClick={handleTimestampClick}
          />
        </CardContent>
      </Card>
    </div>
  );
}
