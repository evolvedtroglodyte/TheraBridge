'use client';

/**
 * ShareModal - Share chat modal for Dobby AI
 *
 * Features:
 * - Private/Public access options
 * - Create share link button
 * - Backdrop blur with grey overlay
 * - Escape key and backdrop click to close
 */

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface ShareModalProps {
  isOpen: boolean;
  onClose: () => void;
  isDark: boolean;
}

type ShareOption = 'private' | 'public';

export function ShareModal({ isOpen, onClose, isDark }: ShareModalProps) {
  const [selectedOption, setSelectedOption] = useState<ShareOption>('private');
  const [linkCopied, setLinkCopied] = useState(false);

  // Handle escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  // Handle backdrop click
  const handleBackdropClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  }, [onClose]);

  // Handle create link
  const handleCreateLink = () => {
    // Mock link creation
    const mockLink = `https://dobby.app/share/${Math.random().toString(36).substr(2, 9)}`;
    navigator.clipboard.writeText(mockLink);
    setLinkCopied(true);
    setTimeout(() => setLinkCopied(false), 2000);
  };

  if (!isOpen) return null;

  const bgColor = isDark ? 'bg-[#252030]' : 'bg-white';
  const textColor = isDark ? 'text-gray-200' : 'text-gray-800';
  const textMuted = isDark ? 'text-gray-500' : 'text-gray-500';
  const optionBg = isDark ? 'bg-[#1a1625]' : 'bg-[#F5F3F0]';
  const optionBorder = isDark ? '' : 'border border-[#E8E5E0]';
  const optionHover = isDark ? 'hover:bg-[#2a2535]' : 'hover:bg-[#EBEBEB]';
  const optionSelected = isDark ? 'bg-[#2a2535]' : 'bg-white';
  const iconBg = isDark ? 'bg-[#2a2535]' : 'bg-white';
  const accentColor = isDark ? '#8B6AAE' : '#5AB9B4';

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        onClick={handleBackdropClick}
        className={`fixed inset-0 z-[3000] flex items-center justify-center ${
          isDark
            ? 'bg-black/75 backdrop-blur-[4px]'
            : 'bg-[rgba(90,90,80,0.65)] backdrop-blur-[4px]'
        }`}
      >
        <motion.div
          initial={{ scale: 0.95 }}
          animate={{ scale: 1 }}
          exit={{ scale: 0.95 }}
          transition={{ duration: 0.2 }}
          className={`${bgColor} w-[480px] rounded-[20px] p-7 shadow-2xl`}
        >
          {/* Header */}
          <div className="flex items-start justify-between mb-6">
            <div>
              <h2 className={`font-dm text-[22px] font-semibold ${isDark ? 'text-gray-200' : 'text-[#5AB9B4]'}`}>
                Share chat
              </h2>
              <p className={`font-dm text-sm mt-1 ${textMuted}`}>
                Only messages up until now will be shared
              </p>
            </div>
            <button
              onClick={onClose}
              className={`w-8 h-8 flex items-center justify-center rounded-lg transition-colors ${
                isDark ? 'hover:bg-white/5 text-gray-400' : 'hover:bg-black/5 text-gray-500'
              }`}
            >
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          {/* Options */}
          <div className={`rounded-xl overflow-hidden mb-7 ${optionBg} ${optionBorder}`}>
            {/* Private Option */}
            <button
              onClick={() => setSelectedOption('private')}
              className={`w-full flex items-center gap-4 px-5 py-4 transition-colors ${
                selectedOption === 'private' ? optionSelected : optionHover
              }`}
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                selectedOption === 'private' ? optionBg : iconBg
              }`} style={{ color: selectedOption === 'private' ? accentColor : isDark ? '#888' : '#888' }}>
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
                  <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
                </svg>
              </div>
              <div className="flex-1 text-left">
                <div className={`font-dm text-[15px] font-semibold ${isDark ? 'text-gray-200' : 'text-[#5AB9B4]'}`}>
                  Private
                </div>
                <div className={`font-dm text-[13px] mt-0.5 ${textMuted}`}>
                  Only you have access
                </div>
              </div>
              <div className={`w-6 h-6 flex items-center justify-center transition-opacity ${
                selectedOption === 'private' ? 'opacity-100' : 'opacity-0'
              }`} style={{ color: accentColor }}>
                <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
            </button>

            {/* Public Option */}
            <button
              onClick={() => setSelectedOption('public')}
              className={`w-full flex items-center gap-4 px-5 py-4 transition-colors ${
                selectedOption === 'public' ? optionSelected : optionHover
              }`}
            >
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                selectedOption === 'public' ? optionBg : iconBg
              }`} style={{ color: selectedOption === 'public' ? accentColor : isDark ? '#888' : '#888' }}>
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10"/>
                  <line x1="2" y1="12" x2="22" y2="12"/>
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
                </svg>
              </div>
              <div className="flex-1 text-left">
                <div className={`font-dm text-[15px] font-semibold ${isDark ? 'text-gray-200' : 'text-[#5AB9B4]'}`}>
                  Public access
                </div>
                <div className={`font-dm text-[13px] mt-0.5 ${textMuted}`}>
                  Anyone with the link can view
                </div>
              </div>
              <div className={`w-6 h-6 flex items-center justify-center transition-opacity ${
                selectedOption === 'public' ? 'opacity-100' : 'opacity-0'
              }`} style={{ color: accentColor }}>
                <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
              </div>
            </button>
          </div>

          {/* Action Button */}
          <div className="flex justify-end">
            <button
              onClick={handleCreateLink}
              className={`px-6 py-3.5 rounded-xl font-dm text-[15px] font-semibold transition-all ${
                isDark
                  ? 'bg-[#8B6AAE] hover:bg-[#9B7ABE] text-white'
                  : 'bg-[#FAF8F5] hover:bg-[#F0EDE8] text-[#5AB9B4] border border-[#E5E2DE]'
              }`}
            >
              {linkCopied ? 'Link copied!' : 'Create share link'}
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
