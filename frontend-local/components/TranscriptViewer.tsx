'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { ChevronDown, ChevronUp } from 'lucide-react';
import type { TranscriptSegment } from '@/lib/types';
import { formatTimestamp } from '@/lib/utils';

interface TranscriptViewerProps {
  segments: ReadonlyArray<TranscriptSegment> | null;
  transcriptText?: string | null;
}

export function TranscriptViewer({ segments, transcriptText }: TranscriptViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!segments && !transcriptText) {
    return null;
  }

  return (
    <Card>
      <CardHeader className="cursor-pointer" onClick={(e: React.MouseEvent<HTMLDivElement>) => setIsExpanded(!isExpanded)}>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Full Transcript</CardTitle>
          <Button variant="ghost" size="sm">
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </Button>
        </div>
      </CardHeader>
      {isExpanded && (
        <CardContent>
          <div className="space-y-4 max-h-[600px] overflow-y-auto">
            {segments ? (
              segments.map((segment, index) => (
                <div
                  key={index}
                  className="flex gap-4 p-3 hover:bg-accent rounded-md transition-colors"
                >
                  <div className="flex-shrink-0 text-sm text-muted-foreground font-mono w-16">
                    [{formatTimestamp(segment.start)}]
                  </div>
                  <div className="flex-shrink-0 font-semibold text-sm w-20">
                    {segment.speaker}:
                  </div>
                  <div className="flex-1 text-sm">{segment.text}</div>
                </div>
              ))
            ) : (
              <div className="whitespace-pre-wrap text-sm">{transcriptText}</div>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

export type { TranscriptViewerProps };
