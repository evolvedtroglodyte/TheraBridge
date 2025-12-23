/**
 * Theme Storage Utility
 *
 * Manages theme preference using sessionStorage (resets when browser closes)
 * - Auth page always starts in light mode
 * - When toggled in auth, carries to dashboard
 * - When toggled in dashboard, persists until browser close
 */

const THEME_KEY = 'therapybridge_theme';

export type Theme = 'light' | 'dark';

/**
 * Get current theme from session storage
 * Returns 'light' as default
 */
export function getTheme(): Theme {
  if (typeof window === 'undefined') return 'light';

  const stored = sessionStorage.getItem(THEME_KEY);
  return (stored === 'dark' ? 'dark' : 'light') as Theme;
}

/**
 * Set theme in session storage
 */
export function setTheme(theme: Theme): void {
  if (typeof window === 'undefined') return;

  sessionStorage.setItem(THEME_KEY, theme);
  console.log(`🎨 Theme set to: ${theme}`);
}

/**
 * Toggle between light and dark theme
 * Returns the new theme
 */
export function toggleTheme(): Theme {
  const current = getTheme();
  const newTheme = current === 'light' ? 'dark' : 'light';
  setTheme(newTheme);
  return newTheme;
}

/**
 * Clear theme preference (returns to default light mode)
 */
export function clearTheme(): void {
  if (typeof window === 'undefined') return;

  sessionStorage.removeItem(THEME_KEY);
}
