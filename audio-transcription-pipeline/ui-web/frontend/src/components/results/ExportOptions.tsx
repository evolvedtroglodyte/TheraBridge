import { useState } from 'react';
import { Download, FileText, FileJson, FileType } from 'lucide-react';
import Button from '@/components/ui/Button';
import type { TranscriptionResult, Segment } from '@/types/transcription';
import { downloadAsFile } from '@/lib/utils';

interface ExportOptionsProps {
  result: TranscriptionResult;
}

export default function ExportOptions({ result }: ExportOptionsProps) {
  const [isOpen, setIsOpen] = useState(false);

  const exportAsJSON = () => {
    // Filter out confidence field from segments
    const filteredResult = {
      ...result,
      segments: result.segments.map(({ confidence, ...segment }) => segment),
    };
    const json = JSON.stringify(filteredResult, null, 2);
    downloadAsFile(json, `${result.filename}_transcription.json`, 'application/json');
    setIsOpen(false);
  };

  const exportAsText = () => {
    const text = generatePlainText(result.segments);
    downloadAsFile(text, `${result.filename}_transcript.txt`, 'text/plain');
    setIsOpen(false);
  };

  const exportAsSRT = () => {
    const srt = generateSRT(result.segments);
    downloadAsFile(srt, `${result.filename}_subtitles.srt`, 'text/plain');
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <Button
        onClick={() => setIsOpen(!isOpen)}
        variant="outline"
        className="gap-2"
      >
        <Download className="h-4 w-4" />
        Export
      </Button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown Menu */}
          <div className="absolute right-0 mt-2 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-20">
            <div className="p-1">
              <button
                onClick={exportAsJSON}
                className="w-full flex items-center gap-3 px-3 py-2 text-sm text-left hover:bg-gray-100 rounded-md transition-colors"
              >
                <FileJson className="h-4 w-4 text-blue-600" />
                <div>
                  <div className="font-medium">Export as JSON</div>
                  <div className="text-xs text-gray-500">Full data with metadata</div>
                </div>
              </button>

              <button
                onClick={exportAsText}
                className="w-full flex items-center gap-3 px-3 py-2 text-sm text-left hover:bg-gray-100 rounded-md transition-colors"
              >
                <FileText className="h-4 w-4 text-green-600" />
                <div>
                  <div className="font-medium">Export as Text</div>
                  <div className="text-xs text-gray-500">Plain text transcript</div>
                </div>
              </button>

              <button
                onClick={exportAsSRT}
                className="w-full flex items-center gap-3 px-3 py-2 text-sm text-left hover:bg-gray-100 rounded-md transition-colors"
              >
                <FileType className="h-4 w-4 text-purple-600" />
                <div>
                  <div className="font-medium">Export as SRT</div>
                  <div className="text-xs text-gray-500">Subtitle file format</div>
                </div>
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// Generate plain text transcript
function generatePlainText(segments: Segment[]): string {
  return segments
    .map((segment) => {
      const speaker = segment.speaker_id || 'UNKNOWN';
      return `[${speaker}] ${segment.text}`;
    })
    .join('\n\n');
}

// Generate SRT subtitle format
function generateSRT(segments: Segment[]): string {
  return segments
    .map((segment, index) => {
      const startTime = formatSRTTime(segment.start);
      const endTime = formatSRTTime(segment.end);
      return `${index + 1}\n${startTime} --> ${endTime}\n${segment.text}\n`;
    })
    .join('\n');
}

// Format time for SRT (HH:MM:SS,mmm)
function formatSRTTime(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  const millis = Math.floor((seconds % 1) * 1000);

  return `${hours.toString().padStart(2, '0')}:${minutes
    .toString()
    .padStart(2, '0')}:${secs.toString().padStart(2, '0')},${millis
    .toString()
    .padStart(3, '0')}`;
}
