'use client';

import { useState, useRef, useEffect } from 'react';
import { Mic, Square } from 'lucide-react';

interface AudioRecorderProps {
  onUploadSuccess: (sessionId: string, file: File) => void;
}

const MOCK_PATIENT_ID = '00000000-0000-0000-0000-000000000003';
const MOCK_THERAPIST_ID = '00000000-0000-0000-0000-000000000001';

export default function AudioRecorder({ onUploadSuccess }: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        setRecordedBlob(blob);

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());

        // Upload automatically
        uploadRecording(blob);
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Failed to access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  const uploadRecording = async (blob: Blob) => {
    setIsUploading(true);

    try {
      // Convert Blob to File
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
      const file = new File([blob], `recording_${timestamp}.webm`, {
        type: 'audio/webm',
      });

      console.log('[AudioRecorder] Uploading recording...', { filename: file.name });

      const formData = new FormData();
      formData.append('file', file);
      formData.append('patient_id', MOCK_PATIENT_ID);
      formData.append('therapist_id', MOCK_THERAPIST_ID);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Upload failed');
      }

      console.log('[AudioRecorder] Upload complete, got session ID:', data.session_id);
      onUploadSuccess(data.session_id, file);
    } catch (error) {
      console.error('[AudioRecorder] Upload failed:', error);
      alert('Upload failed: ' + (error instanceof Error ? error.message : 'Unknown error'));
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h2 className="text-xl font-semibold mb-6">Record Audio</h2>
        <div className="space-y-4">
          {/* Recording Status */}
          <div className="bg-gray-50 rounded-lg p-8 text-center">
            <div className="flex flex-col items-center gap-4">
              <div className={`p-6 rounded-full ${isRecording ? 'bg-red-100' : 'bg-blue-100'}`}>
                <Mic className={`h-12 w-12 ${isRecording ? 'text-red-600' : 'text-blue-600'}`} />
              </div>

              {isRecording && (
                <div className="text-center">
                  <div className="text-3xl font-mono font-medium">
                    {formatTime(recordingTime)}
                  </div>
                  <div className="text-sm text-red-600 mt-1 flex items-center justify-center gap-2">
                    <span className="inline-block w-2 h-2 bg-red-600 rounded-full animate-pulse"></span>
                    Recording...
                  </div>
                </div>
              )}

              {isUploading && (
                <div className="text-center">
                  <div className="text-lg text-blue-600">
                    Uploading recording...
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Control Buttons */}
          <div className="flex gap-3 justify-center">
            {!isRecording && !isUploading && (
              <button
                onClick={startRecording}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center gap-2"
              >
                <Mic className="h-4 w-4" />
                Start Recording
              </button>
            )}

            {isRecording && (
              <button
                onClick={stopRecording}
                className="px-6 py-2 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 transition-colors flex items-center gap-2"
              >
                <Square className="h-4 w-4" />
                Stop Recording
              </button>
            )}
          </div>

          {/* Instructions */}
          {!isRecording && !isUploading && (
            <div className="text-center text-sm text-gray-500">
              <p>Click "Start Recording" to begin recording from your microphone.</p>
              <p className="mt-1">Recording will automatically upload when you stop.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
