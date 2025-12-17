'use client';

import { usePatient } from '@/hooks/usePatients';
import { useSessions } from '@/hooks/useSessions';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { SessionUploader } from '@/components/SessionUploader';
import { SessionCard } from '@/components/SessionCard';
import { ArrowLeft, Mail, Phone, Calendar, Target, Loader2, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { use } from 'react';

interface PageProps {
  params: Promise<{ id: string }>;
}

export default function PatientDetailPage({ params }: PageProps) {
  const { id } = use(params);
  const { patient, isLoading: loadingPatient, isError: patientError } = usePatient(id);
  const { sessions, isLoading: loadingSessions, refresh: refreshSessions } = useSessions({ patientId: id });

  if (loadingPatient) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (patientError || !patient) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <AlertCircle className="w-12 h-12 text-destructive" />
        <p className="text-lg text-muted-foreground">Patient not found</p>
        <Link href="/therapist">
          <Button variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Patients
          </Button>
        </Link>
      </div>
    );
  }

  const sortedSessions = sessions
    ?.sort((a, b) => new Date(b.session_date).getTime() - new Date(a.session_date).getTime()) || [];

  const totalStrategies = new Set(
    sortedSessions.flatMap(s => s.extracted_notes?.strategies.map(st => st.name) || [])
  ).size;

  const totalActionItems = sortedSessions
    .flatMap(s => s.extracted_notes?.action_items || [])
    .length;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <Link href="/therapist">
          <Button variant="ghost">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Patients
          </Button>
        </Link>
      </div>

      <div>
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="text-3xl font-bold tracking-tight">{patient.name}</h2>
            <div className="flex flex-col gap-1 mt-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Mail className="w-4 h-4" />
                {patient.email}
              </div>
              {patient.phone && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <Phone className="w-4 h-4" />
                  {patient.phone}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3 mb-8">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                  <Calendar className="w-6 h-6 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{sortedSessions.length}</p>
                  <p className="text-sm text-muted-foreground">Total Sessions</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                  <Target className="w-6 h-6 text-green-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{totalStrategies}</p>
                  <p className="text-sm text-muted-foreground">Active Strategies</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <Target className="w-6 h-6 text-blue-600" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{totalActionItems}</p>
                  <p className="text-sm text-muted-foreground">Action Items</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-xl font-semibold">Upload New Session</h3>
        <SessionUploader
          patientId={id}
          onUploadComplete={() => {
            refreshSessions();
          }}
        />
      </div>

      <div className="space-y-4">
        <h3 className="text-xl font-semibold">Sessions Timeline</h3>
        {loadingSessions ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        ) : sortedSessions.length === 0 ? (
          <Card>
            <CardContent className="flex flex-col items-center justify-center h-32 gap-2">
              <Calendar className="w-12 h-12 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">No sessions yet</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sortedSessions.map((session) => (
              <SessionCard key={session.id} session={session} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
