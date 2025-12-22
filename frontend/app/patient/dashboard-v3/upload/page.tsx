'use client';

/**
 * Audio Upload Page - EXACT MATCH to original UI
 * Matches audio-transcription-pipeline/ui-web/frontend exactly
 */

import { useState } from 'react';
import FileUploader from './components/FileUploader';
import AudioRecorder from './components/AudioRecorder';
import UploadProgress from './components/UploadProgress';
import ResultsView from './components/ResultsView';

type ViewState = 'upload' | 'processing' | 'results';

export default function UploadPage() {
  const [view, setView] = useState<ViewState>('upload');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const handleUploadSuccess = (newSessionId: string, file: File) => {
    console.log('[Upload] Success - navigating to processing', { sessionId: newSessionId, filename: file.name });
    setSessionId(newSessionId);
    setUploadedFile(file);
    setView('processing');
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
