'use client';

import { use, useState } from 'react';
import { useSession } from '@/hooks/useSession';
import { usePatient } from '@/hooks/usePatients';
import { useSessionNotes } from '@/hooks/useSessionNotes';
import { useTemplates } from '@/hooks/useTemplates';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { SessionStatusBadge } from '@/components/SessionStatusBadge';
import { MoodIndicator } from '@/components/MoodIndicator';
import { StrategyCard } from '@/components/StrategyCard';
import { TriggerCard } from '@/components/TriggerCard';
import { ActionItemCard } from '@/components/ActionItemCard';
import { TranscriptViewer } from '@/components/TranscriptViewer';
import { SessionDetailSkeleton } from '@/components/skeletons';
import { NoteWritingModal } from '@/components/session/NoteWritingModal';
import { SessionNoteCard } from '@/components/session/SessionNoteCard';
import {
  ArrowLeft,
  Clock,
  Calendar,
  AlertTriangle,
  Quote,
  Target,
  AlertCircle,
  CheckCircle,
  Loader2,
  FileText,
  PenSquare,
} from 'lucide-react';
import Link from 'next/link';
import { formatDateTime, formatDuration } from '@/lib/utils';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function SessionDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const { session, isLoading, isError, isProcessing } = useSession(id);
  const { patient } = usePatient(session?.patient_id || null);
  const { notes, refresh: refreshNotes } = useSessionNotes(id);
  const { templates } = useTemplates();
  const [isNoteModalOpen, setIsNoteModalOpen] = useState(false);

  // Note: useSession hook automatically handles polling at 5s intervals while processing
  // No manual polling needed here - the hook's dynamic refreshInterval handles it

  const handleNoteSaved = () => {
    refreshNotes();
  };

  // Find template for each note
  const getTemplateForNote = (templateId: string | null | undefined) => {
    if (!templateId || !templates) return null;
    return templates.find((t) => t.id === templateId) || null;
  };

  if (isLoading) {
    return <SessionDetailSkeleton />;
  }

  if (isError || !session) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <AlertCircle className="w-12 h-12 text-destructive" />
        <p className="text-lg text-muted-foreground">Session not found</p>
        <Link href="/therapist">
          <Button variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
        </Link>
      </div>
    );
  }

  const notes = session.extracted_notes;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <Link href={patient ? `/therapist/patients/${patient.id}` : '/therapist'}>
          <Button variant="ghost">
            <ArrowLeft className="w-4 h-4 mr-2" />
            {patient ? `Back to ${patient.name}` : 'Back'}
          </Button>
        </Link>
      </div>

      {/* Session Header */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2 flex-1">
              <div className="flex items-center gap-4">
                <CardTitle className="text-2xl">
                  {patient ? `${patient.name}'s Session` : 'Session Details'}
                </CardTitle>
                <SessionStatusBadge status={session.status} />
              </div>
              <div className="flex items-center gap-4 text-sm text-muted-foreground">
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  {formatDateTime(session.session_date)}
                </div>
                {session.duration_seconds && (
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    {formatDuration(session.duration_seconds)}
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3">
              {notes?.session_mood && (
                <MoodIndicator mood={notes.session_mood} trajectory={notes.mood_trajectory} />
              )}
              {session.status === 'processed' && (
                <Button onClick={() => setIsNoteModalOpen(true)}>
                  <PenSquare className="w-4 h-4 mr-2" />
                  Write Note
                </Button>
              )}
            </div>
          </div>
        </CardHeader>

        {isProcessing && (
          <CardContent>
            <div className="flex items-center gap-3 p-4 bg-blue-50 border border-blue-200 rounded-md">
              <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
              <div className="flex-1">
                <p className="font-medium text-blue-900">Processing session...</p>
                <p className="text-sm text-blue-700">
                  {session.status === 'uploading' && 'Uploading audio file...'}
                  {session.status === 'transcribing' && 'Transcribing audio with Whisper...'}
                  {session.status === 'extracting_notes' && 'Extracting clinical notes with AI...'}
                </p>
              </div>
            </div>
          </CardContent>
        )}

        {session.error_message && (
          <CardContent>
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-md">
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium text-red-900">Processing Failed</p>
                <p className="text-sm text-red-700">{session.error_message}</p>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {notes && (
        <>
          {/* Clinical Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Clinical Summary</CardTitle>
              <CardDescription>Therapist notes for clinical record</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{notes.therapist_notes}</p>
            </CardContent>
          </Card>

          {/* Key Topics */}
          <Card>
            <CardHeader>
              <CardTitle>Key Topics & Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-2">
                {notes.key_topics.map((topic, index) => (
                  <Badge key={index} variant="secondary">
                    {topic}
                  </Badge>
                ))}
              </div>
              <p className="text-sm text-muted-foreground">{notes.topic_summary}</p>
            </CardContent>
          </Card>

          {/* Strategies and Triggers */}
          {(notes.strategies.length > 0 || notes.triggers.length > 0) && (
            <div className="grid gap-6 md:grid-cols-2">
              {notes.strategies.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    Strategies ({notes.strategies.length})
                  </h3>
                  <div className="space-y-3">
                    {notes.strategies.map((strategy, index) => (
                      <StrategyCard key={index} strategy={strategy} />
                    ))}
                  </div>
                </div>
              )}

              {notes.triggers.length > 0 && (
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5" />
                    Triggers ({notes.triggers.length})
                  </h3>
                  <div className="space-y-3">
                    {notes.triggers.map((trigger, index) => (
                      <TriggerCard key={index} trigger={trigger} />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Action Items */}
          {notes.action_items.length > 0 && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <CheckCircle className="w-5 h-5" />
                Action Items ({notes.action_items.length})
              </h3>
              <div className="grid gap-3 md:grid-cols-2">
                {notes.action_items.map((item, index) => (
                  <ActionItemCard key={index} actionItem={item} />
                ))}
              </div>
            </div>
          )}

          {/* Mood & Emotional Themes */}
          <Card>
            <CardHeader>
              <CardTitle>Mood & Emotional Themes</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <p className="text-sm font-medium">Session Mood:</p>
                <MoodIndicator
                  mood={notes.session_mood}
                  trajectory={notes.mood_trajectory}
                  size="md"
                />
              </div>
              {notes.emotional_themes.length > 0 && (
                <div>
                  <p className="text-sm font-medium mb-2">Emotional Themes:</p>
                  <div className="flex flex-wrap gap-2">
                    {notes.emotional_themes.map((theme, index) => (
                      <Badge key={index} variant="outline">
                        {theme}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Significant Quotes */}
          {notes.significant_quotes.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Quote className="w-5 h-5" />
                  Significant Quotes ({notes.significant_quotes.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {notes.significant_quotes.map((quoteObj, index) => (
                  <div key={index} className="border-l-4 border-primary pl-4 py-2">
                    <p className="text-sm italic mb-2">&ldquo;{quoteObj.quote}&rdquo;</p>
                    <p className="text-xs text-muted-foreground">Context: {quoteObj.context}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Risk Flags */}
          {notes.risk_flags.length > 0 && (
            <Card className="border-red-200 bg-red-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-red-900">
                  <AlertTriangle className="w-5 h-5" />
                  Risk Flags ({notes.risk_flags.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {notes.risk_flags.map((flag, index) => (
                  <div key={index} className="bg-white p-4 rounded-md border border-red-200">
                    <div className="flex items-start justify-between mb-2">
                      <p className="font-semibold text-red-900">{flag.type}</p>
                      <Badge variant="destructive">{flag.severity}</Badge>
                    </div>
                    <p className="text-sm text-red-800">{flag.evidence}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Follow-up Topics */}
          {(notes.follow_up_topics.length > 0 || notes.unresolved_concerns.length > 0) && (
            <Card>
              <CardHeader>
                <CardTitle>Follow-up Topics & Unresolved Concerns</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {notes.follow_up_topics.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-2">Follow-up Topics:</p>
                    <ul className="list-disc list-inside space-y-1">
                      {notes.follow_up_topics.map((topic, index) => (
                        <li key={index} className="text-sm text-muted-foreground">
                          {topic}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {notes.unresolved_concerns.length > 0 && (
                  <div>
                    <p className="text-sm font-medium mb-2">Unresolved Concerns:</p>
                    <ul className="list-disc list-inside space-y-1">
                      {notes.unresolved_concerns.map((concern, index) => (
                        <li key={index} className="text-sm text-muted-foreground">
                          {concern}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </>
      )}

      {/* Session Notes */}
      {notes && notes.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            <h3 className="text-lg font-semibold">Session Notes ({notes.length})</h3>
          </div>
          <div className="space-y-3">
            {notes.map((note) => (
              <SessionNoteCard
                key={note.id}
                note={note}
                template={getTemplateForNote(note.template_id)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Transcript */}
      {(session.transcript_segments || session.transcript_text) && (
        <TranscriptViewer
          segments={session.transcript_segments}
          transcriptText={session.transcript_text}
        />
      )}

      {/* Note Writing Modal */}
      <NoteWritingModal
        isOpen={isNoteModalOpen}
        onClose={() => setIsNoteModalOpen(false)}
        sessionId={id}
        onNoteSaved={handleNoteSaved}
      />
    </div>
  );
}
