'use client';

/**
 * Upload Page - Audio file upload interface
 */

import { Suspense, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useTheme } from '@/app/patient/contexts/ThemeContext';
import { ProcessingProvider, useProcessing } from '@/contexts/ProcessingContext';
import { SessionDataProvider } from '@/app/patient/contexts/SessionDataContext';
import { WaveCompletionBridge } from '@/app/patient/components/WaveCompletionBridge';
import { NavigationBar } from '@/components/NavigationBar';
import FileUploader from '@/app/patient/upload/components/FileUploader';
import AudioRecorder from '@/app/patient/upload/components/AudioRecorder';
import TranscriptUploader from '@/app/patient/upload/components/TranscriptUploader';
import DemoTranscriptUploader from './components/DemoTranscriptUploader';
import UploadProgress from '@/app/patient/upload/components/UploadProgress';
import ResultsView from '@/app/patient/upload/components/ResultsView';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';

type ViewState = 'upload' | 'processing' | 'results';

function UploadPageContent() {
  const router = useRouter();
  const [view, setView] = useState<ViewState>('upload');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const { startTracking } = useProcessing();
  const { isDark } = useTheme();

  const handleUploadSuccess = (newSessionId: string, file: File) => {
    console.log('[Upload] Success - redirecting to sessions page', { sessionId: newSessionId, filename: file.name });
    startTracking(newSessionId);

    // Redirect to sessions page where SSE will show live updates
    router.push('/sessions');
  };

  const handleProcessingComplete = () => {
    setView('results');
  };

  const handleReset = () => {
    setView('upload');
    setSessionId(null);
    setUploadedFile(null);
  };

  return (
    <div className={`min-h-screen transition-colors duration-300 ${
      isDark ? 'bg-[#1a1625]' : 'bg-[#ECEAE5]'
    }`}>
      <NavigationBar />

      <main className="w-full px-4 py-8 flex justify-center">
        {view === 'upload' && (
          <div className="w-full max-w-[900px] space-y-8">
            {/* Demo Transcript Uploader - Centered */}
            <div className="flex justify-center">
              <DemoTranscriptUploader onUploadSuccess={(sessionId) => {
                console.log('[Upload] Demo upload success - redirecting to sessions:', sessionId);
                startTracking(sessionId);
                router.push('/sessions');
              }} />
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-[#ECEAE5] dark:bg-[#1a1625] text-gray-500 dark:text-gray-400 font-medium">
                  OR UPLOAD AUDIO
                </span>
              </div>
            </div>

            {/* Horizontal Layout Container */}
            <div className="flex items-stretch gap-0">
              {/* Upload Section */}
              <div className="flex-1">
                <FileUploader onUploadSuccess={handleUploadSuccess} />
              </div>

              {/* Vertical Divider with OR */}
              <div className="relative w-px bg-[#D0D0D0] dark:bg-[#3a3545]">
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-[#ECEAE5] dark:bg-[#1a1625] px-0 py-3">
                  <span className="text-[11px] font-semibold tracking-wider text-gray-400 dark:text-gray-600">OR</span>
                </div>
              </div>

              {/* Record Section */}
              <div className="flex-1">
                <AudioRecorder onUploadSuccess={handleUploadSuccess} />
              </div>
            </div>

            {/* Transcript Upload Section */}
            <TranscriptUploader />
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

export default function UploadPage() {
  return (
    <ProcessingProvider>
      <SessionDataProvider>
        <WaveCompletionBridge />
        <Suspense fallback={<DashboardSkeleton />}>
          <UploadPageContent />
        </Suspense>
      </SessionDataProvider>
    </ProcessingProvider>
  );
}
