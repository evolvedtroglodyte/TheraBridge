'use client';

/**
 * Demo Transcript Uploader
 * Allows uploading pre-selected JSON transcripts from mock-therapy-data
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import { demoApiClient } from '@/lib/demo-api-client';
import { useProcessing } from '@/contexts/ProcessingContext';

const DEMO_TRANSCRIPTS = [
  {
    filename: 'session_12_thriving.json',
    label: 'Session 12: Thriving',
    description: 'Final session showing sustained progress and thriving',
  },
  {
    filename: 'session_11_rebuilding.json',
    label: 'Session 11: Rebuilding',
    description: 'Rebuilding after coming out, strengthening resilience',
  },
];

interface DemoTranscriptUploaderProps {
  onUploadSuccess?: (sessionId: string) => void;
}

export default function DemoTranscriptUploader({ onUploadSuccess }: DemoTranscriptUploaderProps) {
  const [selectedTranscript, setSelectedTranscript] = useState(DEMO_TRANSCRIPTS[0].filename);
  const [isUploading, setIsUploading] = useState(false);
  const { startTracking } = useProcessing();

  const handleUpload = async () => {
    setIsUploading(true);

    try {
      const result = await demoApiClient.uploadDemoTranscript(selectedTranscript);

      if (result) {
        console.log('[Demo Upload] ✓ Session created:', result.session_id);

        // Start tracking processing status
        startTracking(result.session_id);

        // Notify parent component
        onUploadSuccess?.(result.session_id);
      } else {
        alert('Failed to upload demo transcript. Please try again.');
      }
    } catch (error) {
      console.error('[Demo Upload] Error:', error);
      alert('An error occurred during upload.');
    } finally {
      setIsUploading(false);
    }
  };

  const selectedInfo = DEMO_TRANSCRIPTS.find(t => t.filename === selectedTranscript);

  return (
    <div className="w-full max-w-[500px] text-center">
      {/* Section Title & Subtitle */}
      <h2 className="text-[18px] font-semibold text-gray-800 dark:text-gray-200 mb-2">
        Upload Demo Session
      </h2>
      <p className="text-[13px] text-gray-500 dark:text-gray-400 mb-6">
        Select a pre-loaded therapy transcript to showcase AI analysis
      </p>

      {/* Main Content Area */}
      <motion.div
        initial={{ y: 0 }}
        whileHover={{
          y: -2,
          transition: { duration: 0.2, ease: 'easeOut' }
        }}
        className="bg-[#F8F8F6] dark:bg-[#252030] rounded-xl px-6 py-7"
      >
        {/* Upload Icon */}
        <div className="w-[56px] h-[56px] rounded-full bg-[#5AB9B4]/[0.12] dark:bg-[#a78bfa]/[0.15] flex items-center justify-center mx-auto mb-5">
          <svg
            className="w-7 h-7 text-[#5AB9B4] dark:text-[#a78bfa]"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>

        {/* Dropdown Label */}
        <label className="block text-[12px] font-semibold text-gray-600 dark:text-gray-400 text-left mb-2">
          Select Session
        </label>

        {/* Dropdown */}
        <select
          value={selectedTranscript}
          onChange={(e) => setSelectedTranscript(e.target.value)}
          disabled={isUploading}
          className="w-full px-4 py-3 text-[14px] font-medium text-gray-800 dark:text-gray-200 bg-white dark:bg-[#1a1625] border border-gray-300 dark:border-[#3a3545] rounded-[10px] cursor-pointer appearance-none transition-all duration-200 hover:border-[#5AB9B4] dark:hover:border-[#a78bfa] focus:outline-none focus:border-[#5AB9B4] dark:focus:border-[#a78bfa] focus:shadow-[0_0_0_3px_rgba(90,185,180,0.15)] dark:focus:shadow-[0_0_0_3px_rgba(167,139,250,0.2)] disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23888' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='6 9 12 15 18 9'%3E%3C/polyline%3E%3C/svg%3E")`,
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'right 14px center',
          }}
        >
          {DEMO_TRANSCRIPTS.map((transcript) => (
            <option key={transcript.filename} value={transcript.filename}>
              {transcript.label}
            </option>
          ))}
        </select>

        {/* Session Description */}
        {selectedInfo && (
          <p className="text-[11px] text-gray-500 dark:text-gray-400 text-left mt-2 mb-5">
            {selectedInfo.description}
          </p>
        )}

        {/* Upload Button */}
        <button
          onClick={handleUpload}
          disabled={isUploading}
          className="w-full py-3.5 px-6 text-[14px] font-semibold text-white bg-[#5AB9B4] dark:bg-[#8B6AAE] hover:bg-[#4AA9A4] dark:hover:bg-[#7B5A9E] rounded-[10px] transition-all duration-200 hover:shadow-[0_4px_16px_rgba(90,185,180,0.35)] dark:hover:shadow-[0_4px_16px_rgba(139,106,174,0.35)] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-none disabled:active:scale-100"
        >
          {isUploading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                  fill="none"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              Uploading...
            </span>
          ) : (
            'Upload & Analyze'
          )}
        </button>

        {/* Info Box */}
        <div className="flex items-start gap-2.5 bg-[#5AB9B4]/[0.08] dark:bg-[#a78bfa]/[0.1] rounded-lg px-3.5 py-3 mt-4 text-left">
          <svg
            className="flex-shrink-0 w-4 h-4 text-[#5AB9B4] dark:text-[#a78bfa] mt-0.5"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          <p className="text-[11px] text-[#5AB9B4] dark:text-[#a78bfa] leading-relaxed">
            <strong className="font-semibold">Demo Mode:</strong> This will create a new session and run real AI analysis (mood, topics, breakthroughs). Processing takes ~10 seconds.
          </p>
        </div>
      </motion.div>
    </div>
  );
}
