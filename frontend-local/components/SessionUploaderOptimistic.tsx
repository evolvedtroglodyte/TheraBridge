'use client';

import { useState, useCallback, useRef } from 'react';
import { useOptimisticUpload } from '@/hooks/useOptimisticUpload';
import { useOptimisticSessions } from '@/hooks/useOptimisticSessions';
import { useRouter } from 'next/navigation';
import { Upload, File, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';

interface SessionUploaderOptimisticProps {
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

/**
 * Enhanced SessionUploader with optimistic UI updates
 *
 * Features:
 * - Shows optimistic session immediately in the list
 * - Provides real-time upload progress
 * - Reverts optimistic state on error
 * - Seamless transition from optimistic to real session data
 *
 * @example
 * ```tsx
 * <SessionUploaderOptimistic
 *   patientId="patient-123"
 *   onUploadComplete={(sessionId) => {
 *     router.push(`/therapist/sessions/${sessionId}`);
 *   }}
 * />
 * ```
 */
export function SessionUploaderOptimistic({
  patientId,
  onUploadComplete,
}: SessionUploaderOptimisticProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Optimistic upload state management
  const { isUploading, progress, error, uploadAndOptimize, reset } = useOptimisticUpload({
    onOptimisticSessionCreated: (optimisticSession) => {
      // Immediately update sessions list with optimistic data
      mutate((sessions) => [...(sessions || []), optimisticSession], {
        revalidate: false,
      });
    },
    onUploadComplete: (realSession) => {
      // Replace optimistic session with real one
      mutate(
        (sessions) =>
          (sessions || []).map((s) =>
            s.id.startsWith('temp-') && s.audio_filename === selectedFile?.name
              ? realSession
              : s
          ),
        { revalidate: false }
      );

      if (onUploadComplete) {
        onUploadComplete(realSession.id);
      } else {
        router.push(`/therapist/sessions/${realSession.id}`);
      }
    },
    onUploadError: () => {
      // Error handling is automatic - optimistic state reverts via SWR
      setSelectedFile(null);
    },
  });

  // Session list with optimistic update support
  const { mutate } = useOptimisticSessions({ patientId });

  const validateFile = (file: File): string | null => {
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    const isValidType = ALLOWED_TYPES.includes(file.type) || ALLOWED_EXTENSIONS.includes(fileExtension);

    if (!isValidType) {
      return `Invalid file type. Please upload ${ALLOWED_EXTENSIONS.join(', ')}`;
    }

    // Max file size: 100MB
    if (file.size > 100 * 1024 * 1024) {
      return 'File size must be less than 100MB';
    }

    return null;
  };

  const handleUpload = useCallback(
    async (file: File) => {
      const validationError = validateFile(file);
      if (validationError) {
        // Show error without starting upload
        return;
      }

      setSelectedFile(file);
      await uploadAndOptimize(patientId, file);
    },
    [patientId, uploadAndOptimize]
  );

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

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
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

  // Reset error on component unmount or when dismissing
  const dismissError = useCallback(() => {
    reset();
    setSelectedFile(null);
  }, [reset]);

  const isComplete = progress === 100 && !isUploading;

  return (
    <Card>
      <CardContent className="pt-6">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !isUploading && !isComplete && fileInputRef.current?.click()}
          className={`
            relative border-2 border-dashed rounded-lg p-8 text-center
            transition-all cursor-pointer
            ${isDragging && !isUploading ? 'border-primary bg-primary/5 scale-[1.02]' : 'border-border hover:border-primary/50'}
            ${isUploading ? 'opacity-75 pointer-events-none' : ''}
            ${isComplete ? 'opacity-60 pointer-events-none' : ''}
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_EXTENSIONS.join(',')}
            onChange={handleFileSelect}
            className="hidden"
            disabled={isUploading || isComplete}
          />

          <div className="flex flex-col items-center gap-4">
            {isUploading ? (
              <>
                {/* Upload Progress */}
                <div className="w-full max-w-xs">
                  <div className="flex items-center gap-3 mb-3">
                    <Loader2 className="w-5 h-5 text-primary animate-spin flex-shrink-0" />
                    <span className="text-sm font-medium text-primary">
                      {progress < 50 ? 'Preparing file...' : 'Uploading...'}
                    </span>
                  </div>
                  {/* Progress bar */}
                  <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <p className="text-xs text-muted-foreground mt-2">{progress}% complete</p>
                </div>
                <div className="space-y-1">
                  <p className="text-lg font-medium">Uploading session...</p>
                  {selectedFile && (
                    <p className="text-sm text-muted-foreground">{selectedFile.name}</p>
                  )}
                </div>
              </>
            ) : isComplete ? (
              <>
                {/* Upload Complete */}
                <CheckCircle2 className="w-12 h-12 text-green-600" />
                <div className="space-y-2">
                  <p className="text-lg font-medium text-green-600">Upload Complete!</p>
                  <p className="text-sm text-muted-foreground">
                    Processing session in the background
                  </p>
                  {selectedFile && (
                    <p className="text-xs text-muted-foreground">{selectedFile.name}</p>
                  )}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    dismissError();
                  }}
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
                <p className="text-sm text-destructive font-medium">Upload Failed</p>
                <p className="text-xs text-destructive mt-1">{error}</p>
              </div>
              <button
                onClick={dismissError}
                className="text-destructive hover:text-destructive/80 flex-shrink-0 ml-2"
              >
                ×
              </button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export type { SessionUploaderOptimisticProps };
