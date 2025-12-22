/**
 * Centralized z-index constants
 * - Ensures consistent stacking order across all components
 * - Prevents z-index conflicts
 * - Makes layer management predictable and maintainable
 */

export const Z_INDEX = {
  // Base layer (default content)
  BASE: 0,

  // Sticky elements (header)
  HEADER: 50,

  // Floating elements (dropdowns, tooltips)
  DROPDOWN: 100,
  TOOLTIP: 200,

  // Modal backdrop and content
  MODAL_BACKDROP: 1000,
  MODAL_CONTENT: 1001,

  // Fullscreen overlays (session detail, AI chat)
  FULLSCREEN: 2000,

  // Toast notifications (above everything)
  TOAST: 3000,
} as const;

export type ZIndexKey = keyof typeof Z_INDEX;
