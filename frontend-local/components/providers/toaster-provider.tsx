'use client';

import { Toaster } from 'sonner';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

/**
 * ToasterProvider
 * Wraps the Sonner toast notification system for use throughout the app.
 * Automatically adapts to the current theme (light/dark).
 * Place this in your root layout to enable toast notifications globally.
 *
 * Usage:
 * import { toast } from 'sonner';
 *
 * // Success
 * toast.success('Session uploaded successfully!');
 *
 * // Error
 * toast.error('Failed to upload session');
 *
 * // Info
 * toast.info('Processing your file...');
 *
 * // Custom
 * toast('Custom message');
 */
export function ToasterProvider() {
  const { theme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Use light theme as default to prevent hydration mismatch
  const toasterTheme = mounted ? (theme === 'dark' ? 'dark' : 'light') : 'light';

  return (
    <Toaster
      position="top-right"
      richColors
      closeButton
      theme={toasterTheme as 'light' | 'dark' | 'system'}
    />
  );
}
