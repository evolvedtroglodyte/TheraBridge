import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, File, AlertCircle, CheckCircle } from 'lucide-react';
import Button from '@/components/ui/Button';
import { useFileUpload } from '@/hooks/useFileUpload';
import { formatFileSize } from '@/lib/utils';

interface FileUploaderProps {
  onUploadSuccess: (jobId: string, file: File) => void;
}

const ACCEPTED_AUDIO_TYPES = {
  'audio/mpeg': ['.mp3'],
  'audio/wav': ['.wav'],
  'audio/x-m4a': ['.m4a'],
  'audio/mp4': ['.m4a'],
  'audio/ogg': ['.ogg'],
  'audio/flac': ['.flac'],
  'audio/aac': ['.aac'],
};

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

export default function FileUploader({ onUploadSuccess }: FileUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const { upload, isUploading, error: uploadError } = useFileUpload();

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    setValidationError(null);

    if (rejectedFiles.length > 0) {
      const rejection = rejectedFiles[0];
      if (rejection.errors[0]?.code === 'file-too-large') {
        setValidationError(`File is too large. Maximum size is ${formatFileSize(MAX_FILE_SIZE)}.`);
      } else if (rejection.errors[0]?.code === 'file-invalid-type') {
        setValidationError('Invalid file type. Please upload an audio file (.mp3, .wav, .m4a, .ogg, .flac, .aac).');
      } else {
        setValidationError('File validation failed. Please try again.');
      }
      return;
    }

    if (acceptedFiles.length > 0) {
      setSelectedFile(acceptedFiles[0]);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_AUDIO_TYPES,
    maxSize: MAX_FILE_SIZE,
    multiple: false,
  });

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      console.log('[FileUploader] Starting upload...', { filename: selectedFile.name });
      const jobId = await upload(selectedFile);
      console.log('[FileUploader] Upload complete, got job ID:', jobId);
      if (jobId) {
        // Immediately navigate to processing screen
        console.log('[FileUploader] Calling onUploadSuccess callback');
        onUploadSuccess(jobId, selectedFile);
      } else {
        console.error('[FileUploader] No job ID returned from upload');
      }
    } catch (error) {
      console.error('[FileUploader] Upload failed:', error);
      // Error is already handled by useFileUpload hook
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setValidationError(null);
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
        <h2 className="text-xl font-semibold mb-6">Upload Audio File</h2>
        <div className="space-y-4">
          {/* Dropzone */}
          <div
            {...getRootProps()}
            className={`
              border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors
              ${isDragActive ? 'border-primary bg-primary/5' : 'border-gray-300 hover:border-primary'}
              ${selectedFile ? 'bg-gray-50' : ''}
            `}
          >
            <input {...getInputProps()} />
            <div className="flex flex-col items-center gap-4">
              <div className="p-4 rounded-full bg-primary/10">
                <Upload className="h-8 w-8 text-primary" />
              </div>
              <div>
                <p className="text-lg font-medium">
                  {isDragActive ? 'Drop the file here' : 'Drag & drop audio file'}
                </p>
                <p className="text-sm text-gray-500 mt-1">
                  or click to browse
                </p>
              </div>
              <p className="text-xs text-gray-400">
                Supported: MP3, WAV, M4A, OGG, FLAC, AAC (max {formatFileSize(MAX_FILE_SIZE)})
              </p>
            </div>
          </div>

          {/* Validation Error */}
          {validationError && (
            <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{validationError}</p>
            </div>
          )}

          {/* Upload Error */}
          {uploadError && (
            <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p className="text-sm text-red-800">{uploadError}</p>
            </div>
          )}

          {/* Selected File Info */}
          {selectedFile && !validationError && (
            <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <File className="h-4 w-4 text-green-600" />
                  <p className="font-medium text-green-900">{selectedFile.name}</p>
                </div>
                <p className="text-sm text-green-700 mt-1">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {selectedFile && (
            <div className="flex gap-3">
              <Button
                onClick={handleUpload}
                disabled={isUploading}
                isLoading={isUploading}
                className="flex-1"
              >
                {isUploading ? 'Uploading...' : 'Upload & Transcribe'}
              </Button>
              <Button
                onClick={handleClear}
                variant="outline"
                disabled={isUploading}
              >
                Clear
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
