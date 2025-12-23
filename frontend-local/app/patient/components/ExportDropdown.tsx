'use client';

/**
 * ExportDropdown - Dropdown menu for timeline export options
 *
 * Options:
 * - Download PDF Summary (opens print dialog with styled HTML)
 * - Copy Shareable Link (copies mock URL to clipboard)
 */

import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, Link2, ChevronDown, Check, FileText } from 'lucide-react';
import { TimelineEvent } from '../lib/types';
import { exportToPdf, copyShareableLink } from '../lib/exportTimeline';

interface ExportDropdownProps {
  events: TimelineEvent[];
}

export function ExportDropdown({ events }: ExportDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Reset copy success after 2 seconds
  useEffect(() => {
    if (copySuccess) {
      const timer = setTimeout(() => setCopySuccess(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [copySuccess]);

  const handleExportPdf = async () => {
    setIsOpen(false);
    await exportToPdf(events, { title: 'My Therapy Journey' });
  };

  const handleCopyLink = async () => {
    const success = await copyShareableLink();
    if (success) {
      setCopySuccess(true);
    }
    setIsOpen(false);
  };

  return (
    <div ref={dropdownRef} className="relative">
      {/* Trigger Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 bg-gray-100 dark:bg-[#3d3548] hover:bg-gray-200 dark:hover:bg-[#4d4558] rounded-lg transition-colors"
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <Download className="w-4 h-4" />
        Export
        <ChevronDown className={`w-3 h-3 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -8, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.95 }}
            transition={{ duration: 0.15 }}
            className="absolute right-0 mt-2 w-56 bg-[#F8F7F4] dark:bg-[#2a2435] rounded-xl shadow-lg border border-[#E0DDD8] dark:border-[#3d3548] overflow-hidden z-50"
          >
            <div className="py-1">
              {/* PDF Export Option */}
              <button
                onClick={handleExportPdf}
                className="flex items-center gap-3 w-full px-4 py-3 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#3d3548]/50 transition-colors"
              >
                <FileText className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                <div>
                  <div className="font-medium">Download PDF</div>
                  <div className="text-xs text-gray-400 dark:text-gray-500">
                    Save your journey as PDF
                  </div>
                </div>
              </button>

              {/* Divider */}
              <div className="border-t border-gray-100 dark:border-[#3d3548] my-1" />

              {/* Copy Link Option */}
              <button
                onClick={handleCopyLink}
                className="flex items-center gap-3 w-full px-4 py-3 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-[#3d3548]/50 transition-colors"
              >
                {copySuccess ? (
                  <Check className="w-4 h-4 text-green-500" />
                ) : (
                  <Link2 className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                )}
                <div>
                  <div className="font-medium">
                    {copySuccess ? 'Link copied!' : 'Copy shareable link'}
                  </div>
                  <div className="text-xs text-gray-400 dark:text-gray-500">
                    Share with therapist or others
                  </div>
                </div>
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
