import { useState } from 'react';
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import FileUploader from './components/upload/FileUploader';
import AudioRecorder from './components/upload/AudioRecorder';
import UploadProgress from './components/upload/UploadProgress';
import ResultsView from './components/results/ResultsView';

type ViewState = 'upload' | 'processing' | 'results';

function App() {
  const [view, setView] = useState<ViewState>('upload');
  const [jobId, setJobId] = useState<string | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);

  const handleUploadSuccess = (newJobId: string, file: File) => {
    console.log('[App] Upload success - navigating to processing screen', { jobId: newJobId, filename: file.name });
    setJobId(newJobId);
    setUploadedFile(file);
    setView('processing');
  };

  const handleProcessingComplete = () => {
    setView('results');
  };

  const handleReset = () => {
    setView('upload');
    setJobId(null);
    setUploadedFile(null);
  };

  return (
    <div className="min-h-screen flex flex-col bg-gray-50">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8">
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

        {view === 'processing' && jobId && (
          <UploadProgress
            jobId={jobId}
            onComplete={handleProcessingComplete}
          />
        )}

        {view === 'results' && jobId && uploadedFile && (
          <ResultsView
            jobId={jobId}
            uploadedFile={uploadedFile}
            onReset={handleReset}
          />
        )}
      </main>

      <Footer />
    </div>
  );
}

export default App;
