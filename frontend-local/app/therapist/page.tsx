'use client';

import { usePatients } from '@/hooks/usePatients';
import { useSessions } from '@/hooks/useSessions';
import { usePatientSort } from '@/hooks/usePatientSort';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/EmptyState';
import { PatientSortControl } from '@/components/PatientSortControl';
import { TherapistDashboardSkeleton } from '@/components/skeletons';
import { ErrorMessageAlert } from '@/components/ui/error-message';
import { Plus, Users, Calendar, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { formatDate } from '@/lib/utils';
import { useMemo } from 'react';

export default function TherapistDashboard() {
  const { patients, isLoading: loadingPatients, isError: patientsError } = usePatients();
  const { sessions } = useSessions();

  // Build stats map for all patients
  const patientStats = useMemo(() => {
    if (!patients) return {};

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
        latestSessionDate: latestSession?.session_date,
        actionItems,
        riskFlags,
      };
    };

    type PatientStats = ReturnType<typeof getPatientStats>;
    const statsMap: Record<string, PatientStats> = {};
    patients.forEach((patient) => {
      statsMap[patient.id] = getPatientStats(patient.id);
    });
    return statsMap;
  }, [patients, sessions]);

  // Use patient sorting hook
  const {
    sortConfig,
    setSortField,
    setSortOrder,
    sortedPatients,
    toggleSortOrder,
  } = usePatientSort(patients, patientStats);

  if (loadingPatients) {
    return <TherapistDashboardSkeleton />;
  }

  if (patientsError) {
    return (
      <div className="space-y-4">
        <ErrorMessageAlert
          message="Failed to load patients"
          description="Unable to connect to the server"
        />
      </div>
    );
  }

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
        <EmptyState
          icon={Users}
          heading="No patients yet"
          description="Add your first patient to get started"
          actionLabel="Add Patient"
          onAction={() => {
            // TODO: Implement patient creation flow
          }}
        />
      ) : (
        <>
          <div className="flex items-center justify-end">
            <PatientSortControl
              sortField={sortConfig.field}
              sortOrder={sortConfig.order}
              onSortFieldChange={setSortField}
              onSortOrderChange={setSortOrder}
              onToggleSortOrder={toggleSortOrder}
            />
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {sortedPatients.map((patient) => {
              const stats = patientStats[patient.id];

              return (
                <Link key={patient.id} href={`/therapist/patients/${patient.id}`}>
                  <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="space-y-1">
                          <CardTitle className="text-xl">{patient.name}</CardTitle>
                          <CardDescription>{patient.email}</CardDescription>
                        </div>
                        {stats && stats.riskFlags > 0 && (
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
                          <p className="text-2xl font-bold">{stats?.totalSessions || 0}</p>
                        </div>
                        <div className="space-y-1">
                          <p className="text-sm text-muted-foreground">Action Items</p>
                          <p className="text-2xl font-bold">{stats?.actionItems || 0}</p>
                        </div>
                      </div>

                      {stats?.latestSession && (
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
        </>
      )}
    </div>
  );
}
