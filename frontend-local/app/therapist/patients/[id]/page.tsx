'use client';

import { usePatient } from '@/hooks/usePatients';
import { useSessions } from '@/hooks/useSessions';
import { useSessionSearch } from '@/hooks/useSessionSearch';
import { useSessionFilters } from '@/hooks/useSessionFilters';
import { useSessionSort } from '@/hooks/useSessionSort';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { EmptyState } from '@/components/EmptyState';
import { SessionUploader } from '@/components/SessionUploader';
import { SessionCard } from '@/components/SessionCard';
import { SessionSearchInput } from '@/components/session/SessionSearchInput';
import { SessionFilters } from '@/components/SessionFilters';
import { SessionSortControl } from '@/components/SessionSortControl';
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
  const { searchQuery, filteredSessions, handleSearchChange, clearSearch, hasActiveSearch, resultCount } = useSessionSearch(sessions, patient?.name);
  const {
    filteredSessions: sessionsByFilters,
    statusFilter,
    setStatusFilter,
    dateRangeFilter,
    setDateRangeFilter,
  } = useSessionFilters(sessions);

  // Use sorting hook with patient map for patient_name sorting
  const patientMap = patient ? { [patient.id]: patient.name } : {};
  const {
    sortConfig,
    setSortField,
    setSortOrder,
    sortedSessions: sortedSessionsBySort,
    toggleSortOrder,
  } = useSessionSort(sessions, patientMap);

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

  // Apply both filters and search
  // First filter by status and date range, then search within filtered results
  const sessionsBeforeSearch = sessionsByFilters.sort(
    (a, b) => new Date(b.session_date).getTime() - new Date(a.session_date).getTime()
  );

  // Apply sorting to filtered sessions
  const getDisplaySessions = () => {
    const toSort = hasActiveSearch
      ? filteredSessions.filter(s => sessionsByFilters.some(sf => sf.id === s.id))
      : sessionsBeforeSearch;

    // Apply sorting based on selected sort field
    return toSort.sort((a, b) => {
      let compareValue = 0;

      switch (sortConfig.field) {
        case 'date':
          compareValue =
            new Date(a.session_date).getTime() -
            new Date(b.session_date).getTime();
          break;

        case 'patient_name': {
          const nameA = patientMap?.[a.patient_id] || 'Unknown';
          const nameB = patientMap?.[b.patient_id] || 'Unknown';
          compareValue = nameA.localeCompare(nameB);
          break;
        }

        case 'status':
          compareValue = a.status.localeCompare(b.status);
          break;

        default:
          compareValue = 0;
      }

      return sortConfig.order === 'desc' ? -compareValue : compareValue;
    });
  };

  const displaySessions = getDisplaySessions();

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
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold">Sessions Timeline</h3>
        </div>

        {!loadingSessions && sortedSessions.length > 0 && (
          <div className="space-y-4">
            <SessionFilters
              statusFilter={statusFilter}
              onStatusFilterChange={setStatusFilter}
              dateRangeFilter={dateRangeFilter}
              onDateRangeFilterChange={setDateRangeFilter}
            />

            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <SessionSearchInput
                value={searchQuery}
                onChange={handleSearchChange}
                onClear={clearSearch}
                hasActiveSearch={hasActiveSearch}
                resultCount={resultCount}
              />
              <SessionSortControl
                sortField={sortConfig.field}
                sortOrder={sortConfig.order}
                onSortFieldChange={setSortField}
                onSortOrderChange={setSortOrder}
                onToggleSortOrder={toggleSortOrder}
              />
            </div>
          </div>
        )}

        {loadingSessions ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-6 h-6 animate-spin text-primary" />
          </div>
        ) : sortedSessions.length === 0 ? (
          <EmptyState
            icon={Calendar}
            heading="No sessions yet"
            description="Upload your first session to get started"
            iconSize="md"
            showCard
          />
        ) : sessionsByFilters.length === 0 ? (
          <EmptyState
            icon={Calendar}
            heading="No sessions match your filters"
            description="Try adjusting your status or date range filters"
            iconSize="md"
            showCard
          />
        ) : displaySessions.length === 0 ? (
          <EmptyState
            icon={Calendar}
            heading="No sessions found"
            description={`No sessions match "${searchQuery}"`}
            iconSize="md"
            showCard
          />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {displaySessions.map((session) => (
              <SessionCard key={session.id} session={session} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
