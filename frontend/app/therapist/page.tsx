'use client';

import { usePatients } from '@/hooks/usePatients';
import { useSessions } from '@/hooks/useSessions';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, Users, Calendar, AlertCircle, Loader2 } from 'lucide-react';
import Link from 'next/link';
import { formatDate } from '@/lib/utils';

export default function TherapistDashboard() {
  const { patients, isLoading: loadingPatients, isError: patientsError } = usePatients();
  const { sessions, isLoading: loadingSessions } = useSessions();

  if (loadingPatients) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  if (patientsError) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-4">
        <AlertCircle className="w-12 h-12 text-destructive" />
        <p className="text-lg text-muted-foreground">Failed to load patients</p>
        <p className="text-sm text-muted-foreground">
          Make sure the backend server is running on http://localhost:8000
        </p>
      </div>
    );
  }

  const getPatientStats = (patientId: string) => {
    const patientSessions = sessions?.filter(s => s.patient_id === patientId) || [];
    const latestSession = patientSessions.sort(
      (a, b) => new Date(b.session_date).getTime() - new Date(a.session_date).getTime()
    )[0];

    const actionItems = patientSessions
      .flatMap(s => s.extracted_notes?.action_items || [])
      .length;

    const riskFlags = patientSessions
      .flatMap(s => s.extracted_notes?.risk_flags || [])
      .length;

    return {
      totalSessions: patientSessions.length,
      latestSession,
      actionItems,
      riskFlags,
    };
  };

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Patients</h2>
          <p className="text-muted-foreground">
            Manage your patients and their therapy sessions
          </p>
        </div>
        <Button>
          <Plus className="w-4 h-4 mr-2" />
          Add Patient
        </Button>
      </div>

      {!patients || patients.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center h-64 gap-4">
            <Users className="w-16 h-16 text-muted-foreground" />
            <div className="text-center">
              <h3 className="text-lg font-semibold">No patients yet</h3>
              <p className="text-sm text-muted-foreground">
                Add your first patient to get started
              </p>
            </div>
            <Button>
              <Plus className="w-4 h-4 mr-2" />
              Add Patient
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {patients.map((patient) => {
            const stats = getPatientStats(patient.id);

            return (
              <Link key={patient.id} href={`/therapist/patients/${patient.id}`}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="space-y-1">
                        <CardTitle className="text-xl">{patient.name}</CardTitle>
                        <CardDescription>{patient.email}</CardDescription>
                      </div>
                      {stats.riskFlags > 0 && (
                        <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
                          <AlertCircle className="w-5 h-5 text-red-600" />
                        </div>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Calendar className="w-4 h-4" />
                          Sessions
                        </div>
                        <p className="text-2xl font-bold">{stats.totalSessions}</p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-sm text-muted-foreground">Action Items</p>
                        <p className="text-2xl font-bold">{stats.actionItems}</p>
                      </div>
                    </div>

                    {stats.latestSession && (
                      <div className="pt-4 border-t">
                        <p className="text-xs text-muted-foreground">Latest Session</p>
                        <p className="text-sm font-medium">
                          {formatDate(stats.latestSession.session_date)}
                        </p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
