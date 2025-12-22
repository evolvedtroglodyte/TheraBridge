'use client';

/**
 * ThemeContext - Dark mode state management
 * - Provides dark mode toggle functionality
 * - Persists preference to sessionStorage (shared with auth page)
 * - Applies dark class to document root
 * - Syncs with auth page theme preference
 */

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { getTheme, setTheme as saveTheme } from '@/lib/theme-storage';

interface ThemeContextType {
  isDark: boolean;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Initialize theme from sessionStorage (syncs with auth page)
  useEffect(() => {
    setMounted(true);
    const storedTheme = getTheme();
    if (storedTheme === 'dark') {
      setIsDark(true);
      document.documentElement.classList.add('dark');
    }
  }, []);

  // Apply dark class when theme changes
  useEffect(() => {
    if (!mounted) return;

    if (isDark) {
      document.documentElement.classList.add('dark');
      saveTheme('dark');
    } else {
      document.documentElement.classList.remove('dark');
      saveTheme('light');
    }
  }, [isDark, mounted]);

  const toggleTheme = useCallback(() => setIsDark(prev => !prev), []);

  // Prevent flash of wrong theme
  if (!mounted) {
    return null;
  }

  return (
    <ThemeContext.Provider value={{ isDark, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
