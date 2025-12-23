'use client';

import { Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { Button } from './button';

/**
 * ThemeToggle
 * A button component that toggles between light and dark themes.
 *
 * Features:
 * - Shows sun icon in light mode, moon icon in dark mode
 * - Smooth icon transitions
 * - Accessible aria labels
 * - Works with next-themes for persistent theme storage
 *
 * Usage:
 * import { ThemeToggle } from '@/components/ui/theme-toggle';
 *
 * export function Navbar() {
 *   return (
 *     <nav className="flex items-center gap-4">
 *       <ThemeToggle />
 *     </nav>
 *   );
 * }
 */
export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // Prevent hydration mismatch by only rendering after mount
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button
        variant="ghost"
        size="icon"
        disabled
        aria-label="Toggle theme"
      >
        <Sun className="h-[1.2rem] w-[1.2rem]" />
      </Button>
    );
  }

  const isDark = theme === 'dark';

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(isDark ? 'light' : 'dark')}
      aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
      className="transition-colors"
    >
      {isDark ? (
        <Moon className="h-[1.2rem] w-[1.2rem] transition-all" />
      ) : (
        <Sun className="h-[1.2rem] w-[1.2rem] transition-all" />
      )}
      <span className="sr-only">Toggle theme</span>
    </Button>
  );
}
