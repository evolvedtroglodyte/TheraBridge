'use client';

import { useState, useRef, useEffect } from 'react';
import { Mic, Square } from 'lucide-react';
import { motion } from 'framer-motion';

// Font families - matching SessionCard
const fontSerif = '"Crimson Pro", Georgia, serif';
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

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
    <div className="px-8 py-8">
      {/* Section Title */}
      <h2 style={{ fontFamily: fontSerif }} className="text-[18px] font-semibold text-center mb-5 text-gray-800 dark:text-gray-200">
        Record Audio
      </h2>

      <div className="space-y-4">
        {/* Recording Area */}
        <motion.div
          initial={{ y: 0 }}
          whileHover={{
            y: -2,
            transition: { duration: 0.2, ease: 'easeOut' }
          }}
          className="min-h-[280px] bg-[#F8F8F6] dark:bg-[#252030] rounded-xl p-7 text-center flex flex-col justify-center"
        >
          <div className="flex flex-col items-center gap-4">
            {/* Mic Button */}
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isUploading}
              className={`
                w-16 h-16 rounded-full flex items-center justify-center transition-all duration-200
                ${isRecording
                  ? 'bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400 shadow-[0_0_0_6px_rgba(220,38,38,0.08)] hover:shadow-[0_0_0_10px_rgba(220,38,38,0.12),0_0_24px_rgba(220,38,38,0.2)] hover:scale-105'
                  : 'bg-[#5AB9B4]/[0.12] dark:bg-[#a78bfa]/[0.15] text-[#5AB9B4] dark:text-[#a78bfa] shadow-[0_0_0_6px_rgba(90,185,180,0.08)] dark:shadow-[0_0_0_6px_rgba(167,139,250,0.08)] hover:bg-[#5AB9B4]/[0.2] dark:hover:bg-[#a78bfa]/[0.25] hover:shadow-[0_0_0_10px_rgba(90,185,180,0.12),0_0_24px_rgba(90,185,180,0.2)] dark:hover:shadow-[0_0_0_10px_rgba(167,139,250,0.12),0_0_24px_rgba(167,139,250,0.2)] hover:scale-105'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
              `}
            >
              <Mic className="h-7 w-7" />
            </button>

            {/* Recording Timer */}
            {isRecording && (
              <div className="text-center">
                <div style={{ fontFamily: fontSerif }} className="text-3xl font-mono font-medium text-gray-800 dark:text-gray-200">
                  {formatTime(recordingTime)}
                </div>
                <div style={{ fontFamily: fontSerif }} className="text-sm text-red-600 dark:text-red-400 mt-1 flex items-center justify-center gap-2">
                  <span className="inline-block w-2 h-2 bg-red-600 dark:bg-red-400 rounded-full animate-pulse"></span>
                  Recording...
                </div>
              </div>
            )}

            {/* Upload Status */}
            {isUploading && (
              <div className="text-center">
                <div style={{ fontFamily: fontSerif }} className="text-lg text-[#5AB9B4] dark:text-[#a78bfa]">
                  Uploading recording...
                </div>
              </div>
            )}

            {/* Start Recording Button (when not recording) */}
            {!isRecording && !isUploading && (
              <button
                onClick={startRecording}
                style={{ fontFamily: fontSerif }}
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-[20px] bg-[#5AB9B4] dark:bg-[#8B6AAE] text-white text-[13px] font-semibold hover:bg-[#4AA9A4] dark:hover:bg-[#7B5A9E] hover:shadow-[0_4px_16px_rgba(90,185,180,0.35)] dark:hover:shadow-[0_4px_16px_rgba(139,106,174,0.35)] transition-all duration-200"
              >
                <div className="w-3.5 h-3.5 rounded-full bg-white"></div>
                Start Recording
              </button>
            )}

            {/* Instructions */}
            {!isRecording && !isUploading && (
              <div style={{ fontFamily: fontSerif }} className="text-[11px] text-gray-500 dark:text-gray-400 mt-3 leading-relaxed">
                Recording will automatically<br />upload when you stop.
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
