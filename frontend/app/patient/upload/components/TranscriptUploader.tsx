'use client';

import { useState, useCallback } from 'react';
import { FileText, AlertCircle } from 'lucide-react';

// Font families - matching SessionCard
const fontSerif = '"Crimson Pro", Georgia, serif';
const fontSans = '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

interface TranscriptUploaderProps {
  onUploadSuccess?: (file: File) => void;
}

const ACCEPTED_DOCUMENT_TYPES = ['text/plain', 'application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
const ACCEPTED_EXTENSIONS = ['.txt', '.pdf', '.docx'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export default function TranscriptUploader({ onUploadSuccess }: TranscriptUploaderProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const validateFile = (file: File): boolean => {
    setValidationError(null);

    // Check file type
    const isValidType = ACCEPTED_DOCUMENT_TYPES.some(type => file.type === type) ||
                       ACCEPTED_EXTENSIONS.some(ext => file.name.toLowerCase().endsWith(ext));

    if (!isValidType) {
      setValidationError('Invalid file type. Please upload a text document (.txt, .pdf, .docx).');
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
      onUploadSuccess?.(file);
    }
  }, [onUploadSuccess]);

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
      onUploadSuccess?.(file);
    }
  };

  return (
    <div className="w-full max-w-[900px] mt-6 pt-6 border-t border-[#D0D0D0] dark:border-[#3a3545]">
      {/* Compact Horizontal Dropzone */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => document.getElementById('transcript-input')?.click()}
        className={`
          flex items-center gap-4 border border-dashed rounded-xl px-5 py-4 cursor-pointer transition-all duration-200
          ${isDragging
            ? 'border-[#5AB9B4] bg-white dark:border-[#a78bfa] dark:bg-[#1a1625]'
            : 'border-[#D0D0D0] hover:border-[#5AB9B4] dark:border-[#3a3545] dark:hover:border-[#a78bfa] bg-white dark:bg-[#1a1625]'
          }
          ${selectedFile ? 'border-green-500 dark:border-green-600' : ''}
        `}
      >
        <input
          id="transcript-input"
          type="file"
          accept={ACCEPTED_EXTENSIONS.join(',')}
          onChange={handleFileSelect}
          className="hidden"
        />

        {/* Icon */}
        <div className="w-10 h-10 rounded-lg bg-[#5AB9B4]/[0.12] dark:bg-[#a78bfa]/[0.15] flex items-center justify-center flex-shrink-0">
          <FileText className="h-5 w-5 text-[#5AB9B4] dark:text-[#a78bfa]" />
        </div>

        {/* Content */}
        <div className="flex-1">
          <div style={{ fontFamily: fontSerif }} className="text-[13px] font-semibold text-gray-800 dark:text-gray-200 mb-0.5">
            {selectedFile ? selectedFile.name : 'Upload Transcript'}
          </div>
          <div style={{ fontFamily: fontSerif }} className="text-[11px] text-gray-500 dark:text-gray-400">
            {selectedFile
              ? `${formatFileSize(selectedFile.size)} • Ready`
              : 'Drop file or click to browse'
            }
          </div>
        </div>

        {/* Formats */}
        <div style={{ fontFamily: fontSerif }} className="text-[10px] text-gray-400 dark:text-gray-500 flex-shrink-0">
          TXT, PDF, DOCX
        </div>
      </div>

      {/* Validation Error */}
      {validationError && (
        <div className="flex items-start gap-2 p-3 mt-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <p style={{ fontFamily: fontSerif }} className="text-xs text-red-800 dark:text-red-300">{validationError}</p>
        </div>
      )}
    </div>
  );
}
