'use client';

import { useState } from 'react';
import { ProgressBar } from '@/components/ui/progress-bar';
import { StepIndicator, type Step } from '@/components/ui/step-indicator';
import { SessionProgressTracker } from '@/components/SessionProgressTracker';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import type { Session } from '@/lib/types';

/**
 * Demo component showcasing all progress indicator components
 * Use this for testing and documentation purposes
 */
export function ProgressIndicatorDemo() {
  const [progressValue, setProgressValue] = useState(0);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [sessionStatus, setSessionStatus] = useState<Session['status']>('uploading');

  const demoSteps: Step[] = [
    {
      id: 'step-1',
      label: 'Upload',
      description: 'Select and upload your file',
      status: 'completed',
    },
    {
      id: 'step-2',
      label: 'Processing',
      description: 'Processing your data',
      status: 'in-progress',
    },
    {
      id: 'step-3',
      label: 'Review',
      description: 'Review the results',
      status: 'pending',
    },
    {
      id: 'step-4',
      label: 'Complete',
      description: 'All done',
      status: 'pending',
    },
  ];

  const mockSession: Session = {
    id: 'session-123',
    patient_id: 'patient-123',
    therapist_id: 'therapist-123',
    session_date: new Date().toISOString(),
    duration_seconds: 3600,
    audio_filename: 'session_audio.mp3',
    audio_url: 'https://example.com/audio.mp3',
    transcript_text: 'Sample transcript...',
    transcript_segments: null,
    extracted_notes: null,
    status: sessionStatus,
    error_message: null,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    processed_at: null,
  };

  return (
    <div className="w-full space-y-8 p-8">
      <div>
        <h1 className="text-3xl font-bold mb-2">Progress Indicator Components</h1>
        <p className="text-muted-foreground">
          Reusable components for displaying progress and multi-step processes
        </p>
      </div>

      {/* ProgressBar Examples */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">ProgressBar Component</h2>

        <Card>
          <CardHeader>
            <CardTitle>Basic Progress Bar</CardTitle>
            <CardDescription>
              Simple progress bar with percentage display
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="text-sm font-medium mb-3 block">Progress: {progressValue}%</label>
              <ProgressBar
                value={progressValue}
                showLabel={true}
                labelPosition="inside"
                animated={progressValue < 100}
              />
              <div className="flex gap-2 mt-4">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setProgressValue(Math.min(progressValue + 10, 100))}
                >
                  +10%
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setProgressValue(0)}
                >
                  Reset
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Progress Bar Variants</CardTitle>
            <CardDescription>
              Different color variants for different states
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="text-sm font-medium mb-2 block">Default</label>
              <ProgressBar value={65} variant="default" labelPosition="below" />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Success</label>
              <ProgressBar value={100} variant="success" labelPosition="below" />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Warning</label>
              <ProgressBar value={50} variant="warning" labelPosition="below" />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Error</label>
              <ProgressBar value={30} variant="destructive" labelPosition="below" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Progress Bar Sizes</CardTitle>
            <CardDescription>
              Different height options
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <label className="text-sm font-medium mb-2 block">Small</label>
              <ProgressBar value={40} size="sm" labelPosition="below" />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Medium</label>
              <ProgressBar value={60} size="md" labelPosition="below" />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">Large</label>
              <ProgressBar value={80} size="lg" labelPosition="below" />
            </div>
          </CardContent>
        </Card>
      </section>

      {/* StepIndicator Examples */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">StepIndicator Component</h2>

        <Card>
          <CardHeader>
            <CardTitle>Horizontal Steps</CardTitle>
            <CardDescription>
              Step indicator in horizontal orientation
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <StepIndicator
                steps={demoSteps}
                currentStepIndex={currentStepIndex}
                orientation="horizontal"
                showDescriptions={false}
              />
              <div className="flex gap-2 mt-4">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCurrentStepIndex(Math.max(currentStepIndex - 1, 0))}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setCurrentStepIndex(Math.min(currentStepIndex + 1, demoSteps.length - 1))}
                >
                  Next
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Vertical Steps</CardTitle>
            <CardDescription>
              Step indicator in vertical orientation with descriptions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <StepIndicator
              steps={demoSteps}
              currentStepIndex={currentStepIndex}
              orientation="vertical"
              showDescriptions={true}
            />
          </CardContent>
        </Card>
      </section>

      {/* SessionProgressTracker Examples */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">SessionProgressTracker Component</h2>

        <Card>
          <CardHeader>
            <CardTitle>Session Upload Progress</CardTitle>
            <CardDescription>
              Integrated progress tracker for session processing workflow
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <SessionProgressTracker
              session={mockSession}
              showDescriptions={true}
            />
            <div className="pt-4 border-t">
              <p className="text-sm font-medium mb-3">Simulate different stages:</p>
              <div className="flex flex-wrap gap-2">
                {(['uploading', 'transcribing', 'transcribed', 'extracting_notes', 'processed', 'failed'] as const).map(
                  (status) => (
                    <Button
                      key={status}
                      size="sm"
                      variant={sessionStatus === status ? 'default' : 'outline'}
                      onClick={() => setSessionStatus(status)}
                      className="capitalize"
                    >
                      {status}
                    </Button>
                  )
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Compact Progress Tracker</CardTitle>
            <CardDescription>
              Simplified version for inline progress display
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SessionProgressTracker
              session={mockSession}
              compact={true}
            />
          </CardContent>
        </Card>
      </section>

      {/* Usage Instructions */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Usage Guide</h2>

        <Card>
          <CardHeader>
            <CardTitle>ProgressBar</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-lg text-xs overflow-auto">
{`import { ProgressBar } from '@/components/ui/progress-bar';

// Basic usage
<ProgressBar value={65} />

// With custom label
<ProgressBar
  value={75}
  label="Uploading..."
  labelPosition="above"
/>

// Different variant
<ProgressBar
  value={100}
  variant="success"
  size="lg"
  animated={false}
/>`}
            </pre>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>StepIndicator</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-lg text-xs overflow-auto">
{`import { StepIndicator } from '@/components/ui/step-indicator';

const steps = [
  { id: 'step-1', label: 'Upload', description: 'Select file' },
  { id: 'step-2', label: 'Process', description: 'Processing...' },
  { id: 'step-3', label: 'Complete', description: 'Done' },
];

<StepIndicator
  steps={steps}
  currentStepIndex={1}
  orientation="horizontal"
  showDescriptions={true}
/>`}
            </pre>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>SessionProgressTracker</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded-lg text-xs overflow-auto">
{`import { SessionProgressTracker } from '@/components/SessionProgressTracker';

<SessionProgressTracker
  session={sessionData}
  showDescriptions={true}
  title="Processing Your Session"
/>

// Compact mode for inline display
<SessionProgressTracker
  session={sessionData}
  compact={true}
/>`}
            </pre>
          </CardContent>
        </Card>
      </section>
    </div>
  );
}
