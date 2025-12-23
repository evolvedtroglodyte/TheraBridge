'use client';

import { useState, useCallback, useRef } from 'react';
import { uploadSession } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { Upload, File, Loader2 } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';
import { ErrorMessage } from './ui/error-message';
import type { FormattedError } from '@/lib/error-formatter';
import { formatUploadError } from '@/lib/error-formatter';
import type { FailureResult } from '@/lib/api-types';

interface SessionUploaderProps {
  patientId: string;
  onUploadComplete?: (sessionId: string) => void;
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

export function SessionUploader({ patientId, onUploadComplete }: SessionUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<FormattedError | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const handleUpload = useCallback(async (file: File) => {
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

    setIsUploading(true);
    setError(null);

    try {
      const session = await uploadSession(patientId, file);

      if (onUploadComplete) {
        onUploadComplete(session.id);
      } else {
        router.push(`/therapist/sessions/${session.id}`);
      }
    } catch (err) {
      // Format the error for display
      let formattedError: FormattedError;

      if (err instanceof Error) {
        // Check if it's a JSON parsing error from the upload function
        if (err.message.includes('Failed to parse')) {
          formattedError = {
            message: 'Server error during upload',
            description: 'The server responded with unexpected data',
            suggestion: 'Try uploading again',
            severity: 'error',
            retryable: true,
          };
        } else {
          // Treat as a general upload error
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
      setIsUploading(false);
    }
  }, [patientId, onUploadComplete, router]);

  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      setSelectedFile(file);
      handleUpload(file);
    }
  }, [handleUpload]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      handleUpload(file);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  return (
    <Card>
      <CardContent className="pt-6">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          className={`
            relative border-2 border-dashed rounded-lg p-8 text-center
            transition-all cursor-pointer
            ${isDragging ? 'border-primary bg-primary/5 scale-[1.02]' : 'border-border hover:border-primary/50'}
            ${isUploading ? 'opacity-60 pointer-events-none' : ''}
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_EXTENSIONS.join(',')}
            onChange={handleFileSelect}
            className="hidden"
            disabled={isUploading}
          />

          <div className="flex flex-col items-center gap-4">
            {isUploading ? (
              <>
                <Loader2 className="w-12 h-12 text-primary animate-spin" />
                <div className="space-y-2">
                  <p className="text-lg font-medium">Uploading session...</p>
                  {selectedFile && (
                    <p className="text-sm text-muted-foreground">{selectedFile.name}</p>
                  )}
                </div>
              </>
            ) : (
              <>
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

          {error && (
            <div className="mt-4">
              <ErrorMessage
                message={error.message}
                description={error.description}
                variant="inline"
                severity={error.severity}
                dismissible
                onDismiss={() => setError(null)}
              />
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export type { SessionUploaderProps };
