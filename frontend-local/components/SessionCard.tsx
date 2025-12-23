import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { SessionStatusBadge } from './SessionStatusBadge';
import { MoodIndicator } from './MoodIndicator';
import { Button } from './ui/button';
import { formatDate, formatDuration } from '@/lib/utils';
import { Clock, ChevronRight } from 'lucide-react';
import type { Session } from '@/lib/types';

interface SessionCardProps {
  session: Session;
}

export function SessionCard({ session }: SessionCardProps) {
  const notes = session.extracted_notes;
  const keyTopics = notes?.key_topics?.slice(0, 3) || [];

  return (
    <Link href={`/therapist/sessions/${session.id}`}>
      <Card className="hover:shadow-md transition-shadow cursor-pointer">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <CardTitle className="text-base">
                {formatDate(session.session_date)}
              </CardTitle>
              {session.duration_seconds && (
                <div className="flex items-center gap-1 text-sm text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  <span>{formatDuration(session.duration_seconds)}</span>
                </div>
              )}
            </div>
            <SessionStatusBadge status={session.status} />
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {notes?.session_mood && (
            <MoodIndicator
              mood={notes.session_mood}
              trajectory={notes.mood_trajectory}
              size="sm"
            />
          )}

          {keyTopics.length > 0 && (
            <div className="space-y-1">
              <p className="text-xs font-medium text-muted-foreground">Key Topics</p>
              <div className="flex flex-wrap gap-1">
                {keyTopics.map((topic, index) => (
                  <span
                    key={index}
                    className="inline-block px-2 py-1 text-xs bg-secondary rounded-md"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {notes?.topic_summary && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {notes.topic_summary}
            </p>
          )}

          <div className="flex items-center justify-between pt-2">
            <Button variant="link" className="p-0 h-auto text-sm">
              View Details
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}

export type { SessionCardProps };
