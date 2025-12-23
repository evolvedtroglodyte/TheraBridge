/**
 * First-Time Detection System (Hybrid Approach)
 *
 * Determines if a user is visiting for the first time or has created an account.
 * Uses localStorage for fast checks + Supabase as fallback for accuracy.
 *
 * Strategy:
 * 1. Check localStorage first (fast, works for same browser)
 * 2. If no flag, check Supabase for any users (covers new device scenario)
 * 3. Set localStorage flag after signup/login to avoid future API calls
 */

import { supabase } from './supabase';

const STORAGE_KEY = 'therapybridge_has_account';

/**
 * Check if user has ever created an account
 *
 * Returns true if:
 * - localStorage flag is set (previous signup on this device), OR
 * - Any users exist in Supabase database (signup from another device)
 */
export async function hasExistingAccount(): Promise<boolean> {
  // Step 1: Check localStorage (fast path)
  const localFlag = localStorage.getItem(STORAGE_KEY);
  if (localFlag === 'true') {
    console.log('✅ Account detected (localStorage)');
    return true;
  }

  // Step 2: Check Supabase for any users (fallback for new device)
  try {
    const { data, error } = await supabase
      .from('users')
      .select('id')
      .limit(1);

    if (error) {
      console.error('❌ Error checking for users:', error);
      return false; // Default to signup page on error
    }

    const hasUsers = data && data.length > 0;

    if (hasUsers) {
      console.log('✅ Account detected (Supabase database)');
      // Set localStorage to avoid future API calls
      setAccountFlag(true);
      return true;
    }

    console.log('🆕 First-time visitor (no accounts exist)');
    return false;
  } catch (error) {
    console.error('❌ Supabase connection error:', error);
    return false; // Default to signup page on error
  }
}

/**
 * Mark that an account has been created
 * Call this after successful signup OR login
 */
export function setAccountFlag(value: boolean = true): void {
  if (typeof window === 'undefined') return; // Skip on server

  localStorage.setItem(STORAGE_KEY, value.toString());
  console.log(`🔖 Account flag set: ${value}`);
}

/**
 * Clear the account flag
 * Only use for testing/development - never in production code
 */
export function clearAccountFlag(): void {
  if (typeof window === 'undefined') return;

  localStorage.removeItem(STORAGE_KEY);
  console.log('🗑️ Account flag cleared (dev only)');
}

/**
 * Get the raw localStorage value (for debugging)
 */
export function getAccountFlagRaw(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(STORAGE_KEY);
}
