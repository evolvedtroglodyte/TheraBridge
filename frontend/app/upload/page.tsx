'use client';

/**
 * Upload Page - Audio file upload interface
 */

import { Suspense, useState } from 'react';
import { ThemeProvider, useTheme } from '@/app/patient/contexts/ThemeContext';
import { ProcessingProvider, useProcessing } from '@/contexts/ProcessingContext';
import { NavigationBar } from '@/components/NavigationBar';
import FileUploader from '@/app/patient/upload/components/FileUploader';
import AudioRecorder from '@/app/patient/upload/components/AudioRecorder';
import UploadProgress from '@/app/patient/upload/components/UploadProgress';
import ResultsView from '@/app/patient/upload/components/ResultsView';
import { DashboardSkeleton } from '@/app/patient/components/DashboardSkeleton';

type ViewState = 'upload' | 'processing' | 'results';

function UploadPageContent() {
  const [view, setView] = useState<ViewState>('upload');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const { startTracking } = useProcessing();
  const { isDark } = useTheme();

  const handleUploadSuccess = (newSessionId: string, file: File) => {
    console.log('[Upload] Success - navigating to processing', { sessionId: newSessionId, filename: file.name });
    setSessionId(newSessionId);
    setUploadedFile(file);
    setView('processing');
    startTracking(newSessionId);
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

      <main className="w-full px-4 py-8">
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

export default function UploadPage() {
  return (
    <ThemeProvider>
      <ProcessingProvider>
        <Suspense fallback={<DashboardSkeleton />}>
          <UploadPageContent />
        </Suspense>
      </ProcessingProvider>
    </ThemeProvider>
  );
}
