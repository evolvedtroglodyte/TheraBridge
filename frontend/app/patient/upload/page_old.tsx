'use client';

/**
 * Audio Upload Page
 * Allows patients to upload therapy session recordings
 * Shows real-time processing progress and results
 */

import { useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { supabase, type TranscriptSegment } from '@/lib/supabase';

export default function UploadPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [results, setResults] = useState<any>(null);

  // Mock patient/therapist IDs (in production, get from auth context)
  const MOCK_PATIENT_ID = 'patient-123';
  const MOCK_THERAPIST_ID = 'therapist-456';

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setError(null);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    setError(null);

    try {
      // Upload file
      const formData = new FormData();
      formData.append('file', file);
      formData.append('patient_id', MOCK_PATIENT_ID);
      formData.append('therapist_id', MOCK_THERAPIST_ID);

      const uploadRes = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const uploadData = await uploadRes.json();

      if (!uploadRes.ok) {
        throw new Error(uploadData.error || 'Upload failed');
      }

      setSessionId(uploadData.session_id);
      setUploading(false);
      setProcessing(true);
      setProgress(10);

      // Trigger background processing
      await fetch('/api/trigger-processing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: uploadData.session_id }),
      });

      // Poll for status
      pollStatus(uploadData.session_id);

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setUploading(false);
    }
  };

  const pollStatus = async (sid: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(`/api/status/${sid}`);
        const data = await res.json();

        setProgress(data.progress || 0);

        if (data.completed) {
          clearInterval(pollInterval);
          setProcessing(false);
          setResults(data.results);
        } else if (data.failed) {
          clearInterval(pollInterval);
          setProcessing(false);
          setError('Processing failed. Please try again.');
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000); // Poll every 2 seconds

    // Timeout after 5 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (processing) {
        setError('Processing timeout. Please check back later.');
        setProcessing(false);
      }
    }, 300000);
  };

  return (
    <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] p-12">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/patient/dashboard-v3')}
            className="text-sm text-gray-600 dark:text-gray-400 hover:text-[#5AB9B4] dark:hover:text-[#a78bfa] mb-4"
          >
            ← Back to Dashboard
          </button>
          <h1 className="text-3xl font-light text-gray-800 dark:text-gray-200">
            Upload Session Recording
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
            Upload your therapy session audio for automatic transcription and analysis
          </p>
        </div>

        {/* Upload Area */}
        {!sessionId && (
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-12 text-center bg-white dark:bg-[#2a2336] hover:border-[#5AB9B4] dark:hover:border-[#a78bfa] transition-colors"
          >
            <div className="mb-4">
              <svg
                className="mx-auto h-16 w-16 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>

            {file ? (
              <div className="mb-4">
                <p className="text-lg font-medium text-gray-800 dark:text-gray-200">
                  {file.name}
                </p>
                <p className="text-sm text-gray-500">
                  {(file.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            ) : (
              <div className="mb-4">
                <p className="text-lg text-gray-600 dark:text-gray-400">
                  Drop your audio file here, or click to browse
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  Supported formats: MP3, WAV, M4A, OGG, FLAC
                </p>
              </div>
            )}

            <input
              type="file"
              accept="audio/*"
              onChange={handleFileChange}
              className="hidden"
              id="file-upload"
            />
            <label
              htmlFor="file-upload"
              className="inline-block px-6 py-3 bg-[#5AB9B4] dark:bg-[#a78bfa] text-white rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
            >
              {file ? 'Change File' : 'Select File'}
            </label>

            {file && (
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="ml-4 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {uploading ? 'Uploading...' : 'Upload & Process'}
              </button>
            )}
          </div>
        )}

        {/* Processing Status */}
        {(uploading || processing) && (
          <div className="mt-8 bg-white dark:bg-[#2a2336] rounded-lg p-8">
            <h2 className="text-xl font-light text-gray-800 dark:text-gray-200 mb-4">
              {uploading ? 'Uploading...' : 'Processing Audio...'}
            </h2>

            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3 mb-4">
              <div
                className="bg-[#5AB9B4] dark:bg-[#a78bfa] h-3 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>

            <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
              {progress}% complete
            </p>

            <div className="mt-6 text-sm text-gray-500 dark:text-gray-400 space-y-2">
              <p>✓ Uploading audio file...</p>
              {progress >= 30 && <p>✓ Transcribing with Whisper AI...</p>}
              {progress >= 60 && <p>✓ Identifying speakers...</p>}
              {progress >= 80 && <p>✓ Analyzing session content...</p>}
            </div>
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="mt-8 space-y-6">
            <div className="bg-white dark:bg-[#2a2336] rounded-lg p-8">
              <h2 className="text-2xl font-light text-gray-800 dark:text-gray-200 mb-4">
                Processing Complete!
              </h2>

              {/* Summary */}
              <div className="mb-6">
                <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-2">
                  Session Summary
                </h3>
                <p className="text-gray-700 dark:text-gray-300">{results.summary}</p>
              </div>

              {/* Mood */}
              {results.mood && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Overall Mood
                  </h3>
                  <span className="inline-block px-4 py-2 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-full">
                    {results.mood}
                  </span>
                </div>
              )}

              {/* Topics */}
              {results.topics && results.topics.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Topics Discussed
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {results.topics.map((topic: string, idx: number) => (
                      <span
                        key={idx}
                        className="px-3 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full text-sm"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Key Insights */}
              {results.key_insights && results.key_insights.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Key Insights
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                    {results.key_insights.map((insight: string, idx: number) => (
                      <li key={idx}>{insight}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Action Items */}
              {results.action_items && results.action_items.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-2">
                    Action Items
                  </h3>
                  <ul className="list-disc list-inside space-y-1 text-gray-700 dark:text-gray-300">
                    {results.action_items.map((item: string, idx: number) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Transcript Preview */}
              {results.transcript && results.transcript.length > 0 && (
                <div>
                  <h3 className="text-lg font-medium text-gray-800 dark:text-gray-200 mb-4">
                    Transcript Preview
                  </h3>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 max-h-96 overflow-y-auto space-y-4">
                    {results.transcript.slice(0, 10).map((segment: TranscriptSegment, idx: number) => (
                      <div key={idx} className="border-l-4 border-gray-300 dark:border-gray-600 pl-4">
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                          {segment.speaker}
                        </p>
                        <p className="text-gray-800 dark:text-gray-200">{segment.text}</p>
                      </div>
                    ))}
                    {results.transcript.length > 10 && (
                      <p className="text-sm text-gray-500 text-center">
                        ... and {results.transcript.length - 10} more segments
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="mt-8 flex gap-4">
                <button
                  onClick={() => router.push('/patient/dashboard-v3')}
                  className="px-6 py-3 bg-[#5AB9B4] dark:bg-[#a78bfa] text-white rounded-lg hover:opacity-90 transition-opacity"
                >
                  View in Dashboard
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                >
                  Upload Another
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="mt-8 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <p className="text-red-800 dark:text-red-200">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
}
