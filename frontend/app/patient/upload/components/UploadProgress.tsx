'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, Loader2 } from 'lucide-react';

interface UploadProgressProps {
  sessionId: string;
  onComplete: () => void;
}

const steps = [
  { title: 'Uploading file', key: 'upload' },
  { title: 'Transcribing audio', key: 'transcribe' },
  { title: 'Identifying speakers', key: 'speakers' },
  { title: 'Generating results', key: 'results' },
];

export default function UploadProgress({ sessionId, onComplete }: UploadProgressProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    // Start processing
    fetch('/api/trigger-processing', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    }).catch(err => {
      console.error('Failed to trigger processing:', err);
    });

    // Poll for status
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/status/${sessionId}`);
        const data = await response.json();

        setProgress(data.progress || 0);

        // Update current step based on progress
        if (data.progress >= 80) setCurrentStep(3);
        else if (data.progress >= 60) setCurrentStep(2);
        else if (data.progress >= 30) setCurrentStep(1);
        else setCurrentStep(0);

        if (data.completed) {
          clearInterval(pollInterval);
          setTimeout(() => {
            onComplete();
          }, 1000);
        } else if (data.failed) {
          clearInterval(pollInterval);
          alert('Processing failed. Please try again.');
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [sessionId, onComplete]);

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white border border-gray-200 rounded-lg p-8 shadow-sm">
        <h2 className="text-2xl font-semibold mb-8 text-center">Processing Audio</h2>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="w-full h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-center text-sm text-gray-600 mt-2">{progress}%</p>
        </div>

        {/* Steps */}
        <div className="space-y-4">
          {steps.map((step, index) => {
            const isComplete = index < currentStep;
            const isCurrent = index === currentStep;

            return (
              <div
                key={step.key}
                className={`flex items-center gap-4 p-4 rounded-lg transition-colors ${
                  isCurrent ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'
                }`}
              >
                <div className="flex-shrink-0">
                  {isComplete ? (
                    <CheckCircle className="h-6 w-6 text-green-600" />
                  ) : isCurrent ? (
                    <Loader2 className="h-6 w-6 text-blue-600 animate-spin" />
                  ) : (
                    <div className="h-6 w-6 rounded-full border-2 border-gray-300" />
                  )}
                </div>
                <div className="flex-1">
                  <p className={`font-medium ${isCurrent ? 'text-blue-900' : 'text-gray-700'}`}>
                    {step.title}
                  </p>
                  {isCurrent && (
                    <p className="text-sm text-blue-600">In progress...</p>
                  )}
                  {isComplete && (
                    <p className="text-sm text-green-600">Complete</p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="mt-8 text-center text-sm text-gray-500">
          <p>This may take a few minutes depending on the audio length.</p>
        </div>
      </div>
    </div>
  );
}
