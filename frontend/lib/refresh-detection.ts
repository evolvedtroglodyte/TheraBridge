/**
 * Refresh Detection Utility
 * Differentiates between hard refresh (Cmd+Shift+R) and simple refresh (Cmd+R)
 */

const HARD_REFRESH_FLAG = 'therapybridge_hard_refresh';

export const refreshDetection = {
  /**
   * Mark that a hard refresh should happen on next page load
   * Call this before window.location.reload(true) or in beforeunload handler
   */
  markHardRefresh() {
    if (typeof window === 'undefined') return;
    sessionStorage.setItem(HARD_REFRESH_FLAG, 'true');
  },

  /**
   * Check if current page load is from a hard refresh
   * Returns true if hard refresh, false if simple refresh
   */
  isHardRefresh(): boolean {
    if (typeof window === 'undefined') return false;

    const flag = sessionStorage.getItem(HARD_REFRESH_FLAG);

    // Clear flag after reading (one-time use)
    if (flag === 'true') {
      sessionStorage.removeItem(HARD_REFRESH_FLAG);
      return true;
    }

    return false;
  },

  /**
   * Detect if user pressed Cmd+Shift+R or Ctrl+Shift+R
   * Call this in a keydown event listener
   */
  isHardRefreshKeyCombo(event: KeyboardEvent): boolean {
    // Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows/Linux)
    const isRefreshKey = event.key === 'r' || event.key === 'R';
    const hasModifier = event.metaKey || event.ctrlKey; // Cmd or Ctrl
    const hasShift = event.shiftKey;

    return isRefreshKey && hasModifier && hasShift;
  },

  /**
   * Alternative: Detect using performance.navigation.type
   * TYPE_RELOAD (1) = simple refresh
   * TYPE_NAVIGATE (0) = hard refresh or first visit
   *
   * Note: This is deprecated but still works in most browsers
   */
  isHardRefreshViaPerformance(): boolean {
    if (typeof window === 'undefined') return false;

    // Modern API
    if (window.performance && 'navigation' in window.performance) {
      const nav = (window.performance as any).navigation;
      // type === 'reload' means simple refresh
      // type === 'navigate' means hard refresh or first visit
      return nav.type === 'navigate';
    }

    // Fallback to deprecated API
    if (window.performance && 'navigation' in window.performance) {
      const navType = (window.performance as any).navigation.type;
      // TYPE_RELOAD = 1 (simple refresh)
      // TYPE_NAVIGATE = 0 (hard refresh or first visit)
      return navType === 0;
    }

    return false;
  }
};
