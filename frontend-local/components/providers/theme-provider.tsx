'use client';

import { ThemeProvider as NextThemesProvider } from 'next-themes';
import { type ReactNode } from 'react';

/**
 * ThemeProvider
 * Wraps the next-themes ThemeProvider to enable dark mode support.
 * This should be placed high in the component tree, typically in the root layout.
 *
 * Features:
 * - Automatic dark mode detection based on system preferences
 * - LocalStorage persistence of theme choice
 * - No flash of unstyled content (FOUC)
 * - Support for 'light', 'dark', and 'system' theme options
 *
 * Usage:
 * Wrap your application with this provider in layout.tsx, then use useTheme() hook
 * in any client component to access theme methods.
 *
 * Example:
 * import { useTheme } from 'next-themes';
 *
 * function MyComponent() {
 *   const { theme, setTheme } = useTheme();
 *   return <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />;
 * }
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="system"
      enableSystem
      disableTransitionOnChange
      storageKey="therapybridge-theme"
    >
      {children}
    </NextThemesProvider>
  );
}
