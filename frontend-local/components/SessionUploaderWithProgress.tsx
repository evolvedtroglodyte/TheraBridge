'use client';

import { useState, useCallback, useRef, useEffect } from 'react';
import { uploadSession } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { Upload, File, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { SessionProgressTracker } from './SessionProgressTracker';
import { ProgressBar } from './ui/progress-bar';
import type { Session } from '@/lib/types';
import { formatUploadError } from '@/lib/error-formatter';
import type { FormattedError } from '@/lib/error-formatter';
import type { FailureResult } from '@/lib/api-types';

interface SessionUploaderWithProgressProps {
  patientId: string;
  onUploadComplete?: (sessionId: string) => void;
  pollInterval?: number;
}

const ALLOWED_TYPES = [
  'audio/mpeg',
  'audio/wav',
  'audio/mp4',
  'audio/x-m4a',
  'audio/webm',
  'audio/mpga',
  'video/mp4',
  'video/mpeg',
];

const ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.mp4', '.mpeg', '.webm', '.mpga'];
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

interface ValidationError {
  type: 'extension' | 'size';
  message: string;
  description: string;
}

/**
 * SessionUploaderWithProgress - Enhanced uploader with multi-stage progress tracking
 *
 * Features:
 * - File upload with progress percentage
 * - Multi-stage processing visualization (uploading → transcribing → extracting notes → complete)
 * - Real-time polling for processing status
 * - Comprehensive error handling and recovery
 *
 * @example
 * ```tsx
 * <SessionUploaderWithProgress
 *   patientId="patient-123"
 *   onUploadComplete={(sessionId) => {
 *     router.push(`/therapist/sessions/${sessionId}`);
 *   }}
 * />
 * ```
 */
export function SessionUploaderWithProgress({
  patientId,
  onUploadComplete,
  pollInterval = 2000,
}: SessionUploaderWithProgressProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [sessionData, setSessionData] = useState<Session | null>(null);
  const [error, setError] = useState<FormattedError | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Validate file
  const validateFile = (file: File): ValidationError | null => {
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    const isValidType = ALLOWED_TYPES.includes(file.type) || ALLOWED_EXTENSIONS.includes(fileExtension);

    if (!isValidType) {
      return {
        type: 'extension',
        message: 'Invalid file type',
        description: `Please upload a supported audio or video file: ${ALLOWED_EXTENSIONS.join(', ')}`,
      };
    }

    if (file.size > MAX_FILE_SIZE) {
      const sizeMB = (MAX_FILE_SIZE / (1024 * 1024)).toFixed(0);
      const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
      return {
        type: 'size',
        message: 'File too large',
        description: `Your file is ${fileSizeMB}MB. Maximum size is ${sizeMB}MB.`,
      };
    }

    return null;
  };

  // Handle file upload
  const handleUpload = useCallback(
    async (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        setError({
          message: validationError.message,
          description: validationError.description,
          suggestion: 'Try selecting a different file',
          severity: 'error',
          retryable: false,
        });
        return;
      }

      setSelectedFile(file);
      setError(null);
      setUploadProgress(0);

      try {
        // Simulate file upload with progress tracking
        // In a real implementation, use XMLHttpRequest or fetch with progress event
        const session = await uploadSession(patientId, file);
        setSessionData(session);
        setUploadProgress(100);

        // Start polling for processing status
        setIsPolling(true);
        startPolling(session.id);
      } catch (err) {
        let formattedError: FormattedError;

        if (err instanceof Error) {
          if (err.message.includes('Failed to parse')) {
            formattedError = {
              message: 'Server error during upload',
              description: 'The server responded with unexpected data',
              suggestion: 'Try uploading again',
              severity: 'error',
              retryable: true,
            };
          } else {
            formattedError = formatUploadError({
              success: false,
              status: 500,
              error: err.message,
            } as FailureResult);
          }
        } else {
          formattedError = {
            message: 'Upload failed',
            description: 'An unexpected error occurred',
            suggestion: 'Try uploading again',
            severity: 'error',
            retryable: true,
          };
        }

        setError(formattedError);
        setIsPolling(false);
      }
    },
    [patientId]
  );

  // Poll for session status
  const startPolling = useCallback(
    (sessionId: string) => {
      const poll = async () => {
        try {
          const response = await fetch(`/api/sessions/${sessionId}`);
          if (!response.ok) throw new Error('Failed to fetch session');

          const data = await response.json();
          const updatedSession = data.data || data;
          setSessionData(updatedSession);

          // Stop polling when processing is complete or failed
          if (updatedSession.status === 'processed' || updatedSession.status === 'failed') {
            setIsPolling(false);

            if (updatedSession.status === 'processed') {
              if (onUploadComplete) {
                onUploadComplete(sessionId);
              } else {
                router.push(`/therapist/sessions/${sessionId}`);
              }
            }
          } else {
            // Continue polling
            pollTimeoutRef.current = setTimeout(poll, pollInterval);
          }
        } catch (err) {
          console.error('Polling error:', err);
          // Retry on error
          pollTimeoutRef.current = setTimeout(poll, pollInterval * 2);
        }
      };

      poll();
    },
    [pollInterval, onUploadComplete, router]
  );

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollTimeoutRef.current) {
        clearTimeout(pollTimeoutRef.current);
      }
    };
  }, []);

  // Drag and drop handlers
  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);

      const file = e.dataTransfer.files[0];
      if (file) {
        handleUpload(file);
      }
    },
    [handleUpload]
  );

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleUpload(file);
    }
  };

  const resetUpload = () => {
    setSelectedFile(null);
    setUploadProgress(0);
    setSessionData(null);
    setError(null);
    setIsPolling(false);
  };

  const isProcessing = uploadProgress === 100 && isPolling;
  const isComplete = sessionData?.status === 'processed';
  const isFailed = sessionData?.status === 'failed';

  return (
    <Card>
      <CardContent className="pt-6">
        {sessionData && isProcessing ? (
          // Show progress tracker during processing
          <div className="space-y-4">
            <SessionProgressTracker
              session={sessionData}
              showDescriptions={true}
              title="Session Processing Progress"
              description="Your session is being processed in the background"
            />

            {!isFailed && !isComplete && (
              <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800">
                <p className="text-sm text-blue-700 dark:text-blue-300">
                  Processing your session... This may take a few minutes depending on the audio length.
                </p>
              </div>
            )}
          </div>
        ) : (
          <>
            {/* Upload area */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() =>
                !uploadProgress && !isComplete && fileInputRef.current?.click()
              }
              className={`
                relative border-2 border-dashed rounded-lg p-8 text-center
                transition-all cursor-pointer
                ${isDragging ? 'border-primary bg-primary/5 scale-[1.02]' : 'border-border hover:border-primary/50'}
                ${uploadProgress > 0 && uploadProgress < 100 ? 'opacity-75 pointer-events-none' : ''}
                ${isComplete ? 'opacity-60 pointer-events-none' : ''}
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept={ALLOWED_EXTENSIONS.join(',')}
                onChange={handleFileSelect}
                className="hidden"
                disabled={uploadProgress > 0 || isComplete}
              />

              <div className="flex flex-col items-center gap-4">
                {uploadProgress > 0 && uploadProgress < 100 ? (
                  <>
                    {/* Upload progress */}
                    <div className="w-full max-w-xs">
                      <div className="mb-4">
                        <ProgressBar
                          value={uploadProgress}
                          showLabel={true}
                          labelPosition="inside"
                          size="md"
                        />
                      </div>
                      <div className="space-y-1">
                        <p className="text-lg font-medium">Uploading...</p>
                        {selectedFile && (
                          <p className="text-sm text-muted-foreground">
                            {selectedFile.name}
                          </p>
                        )}
                      </div>
                    </div>
                  </>
                ) : isComplete ? (
                  <>
                    {/* Upload complete */}
                    <CheckCircle2 className="w-12 h-12 text-green-600" />
                    <div className="space-y-2">
                      <p className="text-lg font-medium text-green-600">
                        Upload Complete!
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Session processing finished
                      </p>
                      {selectedFile && (
                        <p className="text-xs text-muted-foreground">
                          {selectedFile.name}
                        </p>
                      )}
                    </div>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={resetUpload}
                      className="mt-2"
                    >
                      Upload Another
                    </Button>
                  </>
                ) : (
                  <>
                    {/* Default state */}
                    <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                      {selectedFile ? (
                        <File className="w-8 h-8 text-primary" />
                      ) : (
                        <Upload className="w-8 h-8 text-primary" />
                      )}
                    </div>
                    <div className="space-y-2">
                      <p className="text-lg font-medium">
                        {selectedFile ? selectedFile.name : 'Upload Audio File'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Drag and drop or click to browse
                      </p>
                      <p className="text-xs text-muted-foreground">
                        Supported formats: {ALLOWED_EXTENSIONS.join(', ')}
                      </p>
                    </div>
                    {!selectedFile && (
                      <Button variant="secondary" type="button">
                        Select File
                      </Button>
                    )}
                  </>
                )}
              </div>

              {/* Error message */}
              {error && (
                <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md flex items-start gap-2">
                  <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
                  <div className="flex-1 text-left">
                    <p className="text-sm text-destructive font-medium">
                      {error.message}
                    </p>
                    <p className="text-xs text-destructive mt-1">
                      {error.description}
                    </p>
                  </div>
                  <button
                    onClick={() => setError(null)}
                    className="text-destructive hover:text-destructive/80 flex-shrink-0 ml-2"
                  >
                    ×
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

export type { SessionUploaderWithProgressProps };
