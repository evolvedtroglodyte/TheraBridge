'use client';

import { useState, useCallback, useRef } from 'react';
import { uploadSession } from '@/lib/api';
import { useRouter } from 'next/navigation';
import { Upload, File, Loader2, AlertCircle } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';

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

export function SessionUploader({ patientId, onUploadComplete }: SessionUploaderProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    const isValidType = ALLOWED_TYPES.includes(file.type) || ALLOWED_EXTENSIONS.includes(fileExtension);

    if (!isValidType) {
      setError(`Invalid file type. Please upload ${ALLOWED_EXTENSIONS.join(', ')}`);
      return false;
    }

    // Max file size: 100MB
    if (file.size > 100 * 1024 * 1024) {
      setError('File size must be less than 100MB');
      return false;
    }

    return true;
  };

  const handleUpload = useCallback(async (file: File) => {
    if (!validateFile(file)) {
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const session = await uploadSession(patientId, file);
      setUploadProgress(100);

      if (onUploadComplete) {
        onUploadComplete(session.id);
      } else {
        router.push(`/therapist/sessions/${session.id}`);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      setError(errorMessage);
      setIsUploading(false);
      setUploadProgress(0);
    }
  }, [patientId, onUploadComplete, router]);

  const handleDrop = useCallback((e: React.DragEvent) => {
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

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
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
            <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md flex items-start gap-2">
              <AlertCircle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
              <p className="text-sm text-destructive text-left">{error}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
