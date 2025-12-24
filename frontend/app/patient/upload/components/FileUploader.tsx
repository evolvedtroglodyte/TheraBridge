'use client';

import { useState, useCallback } from 'react';
import { Upload, File, AlertCircle, CheckCircle, X } from 'lucide-react';
import { motion } from 'framer-motion';

// Font families - matching SessionCard
const fontSerif = '"Crimson Pro", Georgia, serif';
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

interface FileUploaderProps {
  onUploadSuccess: (sessionId: string, file: File) => void;
}

const ACCEPTED_AUDIO_TYPES = ['audio/mpeg', 'audio/wav', 'audio/x-m4a', 'audio/mp4', 'audio/ogg', 'audio/flac', 'audio/aac', 'audio/webm'];
const ACCEPTED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.webm'];
const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB

const MOCK_PATIENT_ID = '00000000-0000-0000-0000-000000000003';
const MOCK_THERAPIST_ID = '00000000-0000-0000-0000-000000000001';

export default function FileUploader({ onUploadSuccess }: FileUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const validateFile = (file: File): boolean => {
    setValidationError(null);

    // Check file type
    const isValidType = ACCEPTED_AUDIO_TYPES.some(type => file.type.includes(type.split('/')[1])) ||
                       ACCEPTED_EXTENSIONS.some(ext => file.name.toLowerCase().endsWith(ext));

    if (!isValidType) {
      setValidationError('Invalid file type. Please upload an audio file (.mp3, .wav, .m4a, .ogg, .flac, .aac, .webm).');
      return false;
    }

    // Check file size
    if (file.size > MAX_FILE_SIZE) {
      setValidationError(`File is too large. Maximum size is ${formatFileSize(MAX_FILE_SIZE)}.`);
      return false;
    }

    return true;
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const file = e.dataTransfer.files[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    }
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && validateFile(file)) {
      setSelectedFile(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadError(null);

    try {
      console.log('[FileUploader] Starting upload...', { filename: selectedFile.name });

      const formData = new FormData();
      formData.append('file', selectedFile);
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

      console.log('[FileUploader] Upload complete, got session ID:', data.session_id);

      // Immediately navigate to processing screen
      onUploadSuccess(data.session_id, selectedFile);
    } catch (error) {
      console.error('[FileUploader] Upload failed:', error);
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setIsUploading(false);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setValidationError(null);
    setUploadError(null);
  };

  return (
    <div className="px-8 py-8">
      {/* Section Title */}
      <h2 style={{ fontFamily: fontSerif }} className="text-[18px] font-semibold text-center mb-5 text-gray-800 dark:text-gray-200">
        Upload Audio File
      </h2>

      <div className="space-y-4">
        {/* Dropzone */}
        <motion.div
          initial={{ y: 0 }}
          whileHover={{
            y: -2,
            transition: { duration: 0.2, ease: 'easeOut' }
          }}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => document.getElementById('file-input')?.click()}
          className={`
            min-h-[280px] border-2 border-dashed rounded-xl p-9 text-center cursor-pointer transition-all duration-200 flex flex-col justify-center
            ${isDragging
              ? 'border-[#5AB9B4] bg-white dark:border-[#a78bfa] dark:bg-[#1a1625]'
              : 'border-[#D0D0D0] hover:border-[#5AB9B4] dark:border-[#3a3545] dark:hover:border-[#a78bfa] bg-white dark:bg-[#1a1625]'
            }
          `}
        >
          <input
            id="file-input"
            type="file"
            accept={ACCEPTED_EXTENSIONS.join(',')}
            onChange={handleFileSelect}
            className="hidden"
          />
          <div className="flex flex-col items-center gap-3.5">
            {/* Icon */}
            <div className="w-[52px] h-[52px] rounded-full bg-[#5AB9B4]/[0.12] dark:bg-[#a78bfa]/[0.15] flex items-center justify-center">
              <Upload className="h-[26px] w-[26px] text-[#5AB9B4] dark:text-[#a78bfa]" />
            </div>

            {/* Text */}
            <div>
              <p style={{ fontFamily: fontSerif }} className="text-[14px] font-semibold text-gray-800 dark:text-gray-200 mb-1">
                {isDragging ? 'Drop the file here' : 'Drag & drop audio file'}
              </p>
              <p style={{ fontFamily: fontSerif }} className="text-[12px] text-gray-500 dark:text-gray-400">
                or click to browse
              </p>
            </div>

            {/* Formats */}
            <p style={{ fontFamily: fontSerif }} className="text-[10px] text-gray-400 dark:text-gray-500">
              MP3, WAV, M4A, OGG, FLAC, AAC (max 100 MB)
            </p>
          </div>
        </motion.div>

          {/* Validation Error */}
          {validationError && (
            <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p style={{ fontFamily: fontSerif }} className="text-sm text-red-800">{validationError}</p>
            </div>
          )}

          {/* Upload Error */}
          {uploadError && (
            <div className="flex items-start gap-2 p-4 bg-red-50 border border-red-200 rounded-lg">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <p style={{ fontFamily: fontSerif }} className="text-sm text-red-800">{uploadError}</p>
            </div>
          )}

          {/* Selected File Info */}
          {selectedFile && !validationError && (
            <div className="flex items-start gap-3 p-4 bg-green-50 border border-green-200 rounded-lg">
              <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <File className="h-4 w-4 text-green-600" />
                  <p style={{ fontFamily: fontSerif }} className="font-medium text-green-900">{selectedFile.name}</p>
                </div>
                <p style={{ fontFamily: fontSerif }} className="text-sm text-green-700 mt-1">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          {selectedFile && (
            <div className="flex gap-3">
              <button
                onClick={handleUpload}
                disabled={isUploading}
                style={{ fontFamily: fontSerif }}
                className="flex-1 px-4 py-2 bg-[#5AB9B4] dark:bg-[#8B6AAE] text-white rounded-lg font-semibold text-[13px] hover:bg-[#4AA9A4] dark:hover:bg-[#7B5A9E] hover:shadow-[0_4px_16px_rgba(90,185,180,0.35)] dark:hover:shadow-[0_4px_16px_rgba(139,106,174,0.35)] disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
              >
                {isUploading ? 'Uploading...' : 'Upload & Transcribe'}
              </button>
              <button
                onClick={handleClear}
                disabled={isUploading}
                style={{ fontFamily: fontSerif }}
                className="px-4 py-2 border border-gray-300 dark:border-[#3a3545] rounded-lg font-medium text-[13px] hover:bg-gray-50 dark:hover:bg-[#252030] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Clear
              </button>
            </div>
          )}
        </div>
    </div>
  );
}
