'use client';

/**
 * Audio Upload Page - EXACT MATCH to original UI
 * Matches audio-transcription-pipeline/ui-web/frontend exactly
 *
 * NEW: Integrated with ProcessingContext for dashboard auto-refresh
 */

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import FileUploader from './components/FileUploader';
import AudioRecorder from './components/AudioRecorder';
import UploadProgress from './components/UploadProgress';
import ResultsView from './components/ResultsView';
import { ProcessingProvider, useProcessing } from '@/contexts/ProcessingContext';
import { SessionDataProvider } from '@/app/patient/contexts/SessionDataContext';
import { WaveCompletionBridge } from '@/app/patient/components/WaveCompletionBridge';

type ViewState = 'upload' | 'processing' | 'results';

/**
 * Inner component that uses ProcessingContext
 */
function UploadPageInner() {
  const router = useRouter();
  const [view, setView] = useState<ViewState>('upload');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const { startTracking } = useProcessing();

  const handleUploadSuccess = (newSessionId: string, file: File) => {
    console.log('[Upload] Success - redirecting to sessions page', { sessionId: newSessionId, filename: file.name });

    // Start tracking this session for dashboard auto-refresh
    startTracking(newSessionId);

    // Redirect to sessions page where SSE will show live updates
    router.push('/sessions');
  };

  const handleProcessingComplete = () => {
    setView('results');
    // Note: ProcessingContext will auto-notify dashboard when status changes to 'completed'
  };

  const handleReset = () => {
    setView('upload');
    setSessionId(null);
    setUploadedFile(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <main className="container mx-auto px-4">
        {view === 'upload' && (
          <div className="space-y-8">
            <FileUploader onUploadSuccess={handleUploadSuccess} />

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-gray-50 text-gray-500 font-medium">OR</span>
              </div>
            </div>

            <AudioRecorder onUploadSuccess={handleUploadSuccess} />
          </div>
        )}

        {view === 'processing' && sessionId && (
          <UploadProgress
            sessionId={sessionId}
            onComplete={handleProcessingComplete}
          />
        )}

        {view === 'results' && sessionId && uploadedFile && (
          <ResultsView
            sessionId={sessionId}
            uploadedFile={uploadedFile}
            onReset={handleReset}
          />
        )}
      </main>
    </div>
  );
}

/**
 * Wrapper that provides ProcessingContext and SessionDataContext
 */
export default function UploadPage() {
  return (
    <ProcessingProvider>
      <SessionDataProvider>
        <WaveCompletionBridge />
        <UploadPageInner />
      </SessionDataProvider>
    </ProcessingProvider>
  );
}
