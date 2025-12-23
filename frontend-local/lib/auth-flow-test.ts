/**
 * Auth Flow Testing Utilities
 *
 * These functions help you test the first-time detection + auth flow
 * without actually creating real accounts.
 *
 * Usage in browser console:
 * - window.testAuthFlow.simulateFirstVisit()
 * - window.testAuthFlow.simulateReturningUser()
 * - window.testAuthFlow.simulateNewDevice()
 * - window.testAuthFlow.getStatus()
 */

import { clearAccountFlag, setAccountFlag, getAccountFlagRaw, hasExistingAccount } from './first-time-detection';

export const authFlowTester = {
  /**
   * Simulate a first-time visitor (no localStorage flag, no users in DB)
   * Should redirect to: /auth/signup
   */
  simulateFirstVisit: () => {
    clearAccountFlag();
    console.log('🆕 Simulated first visit');
    console.log('→ Expected behavior: Redirect to /auth/signup');
    console.log('→ Reload the page to see the redirect');
  },

  /**
   * Simulate a returning user on same device (localStorage flag exists)
   * Should redirect to: /auth/login (if not logged in) or dashboard (if logged in)
   */
  simulateReturningUser: () => {
    setAccountFlag(true);
    console.log('✅ Simulated returning user (same device)');
    console.log('→ Expected behavior: Redirect to /auth/login');
    console.log('→ Reload the page to see the redirect');
  },

  /**
   * Simulate user on new device (no localStorage, but users exist in DB)
   * Should redirect to: /auth/login
   * NOTE: This requires actual users in Supabase to work
   */
  simulateNewDevice: () => {
    clearAccountFlag();
    console.log('📱 Simulated new device');
    console.log('→ Expected behavior: Check Supabase for users, then redirect to /auth/login');
    console.log('→ NOTE: Requires at least 1 user in Supabase database');
    console.log('→ Reload the page to see the redirect');
  },

  /**
   * Get current status
   */
  getStatus: async () => {
    const flagValue = getAccountFlagRaw();
    const accountExists = await hasExistingAccount();

    console.log('━━━ Current Auth Flow Status ━━━');
    console.log('localStorage flag:', flagValue || '(not set)');
    console.log('Account exists (localStorage + Supabase):', accountExists);
    console.log('Dev bypass enabled:', process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === 'true');
    console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

    return {
      localStorageFlag: flagValue,
      accountExists,
      devBypass: process.env.NEXT_PUBLIC_DEV_BYPASS_AUTH === 'true',
    };
  },

  /**
   * Test the complete flow programmatically
   */
  testFlow: async () => {
    console.log('🧪 Testing Auth Flow...\n');

    // Test 1: First visit
    console.log('Test 1: First Visit');
    clearAccountFlag();
    const test1 = await hasExistingAccount();
    console.log(`Result: ${test1 ? '❌ FAIL' : '✅ PASS'} (should be false)`);
    console.log('');

    // Test 2: After account creation
    console.log('Test 2: After Account Creation');
    setAccountFlag(true);
    const test2LocalStorage = getAccountFlagRaw();
    console.log(`localStorage: ${test2LocalStorage === 'true' ? '✅ PASS' : '❌ FAIL'} (should be 'true')`);
    console.log('');

    // Test 3: Check account exists
    console.log('Test 3: Account Detection');
    const test3 = await hasExistingAccount();
    console.log(`Result: ${test3 ? '✅ PASS' : '❌ FAIL'} (should be true)`);
    console.log('');

    // Test 4: Clear and check Supabase fallback
    console.log('Test 4: New Device (Supabase Fallback)');
    clearAccountFlag();
    const test4 = await hasExistingAccount();
    console.log(`Result: ${test4 ? '✅ PASS (Supabase detected users)' : '⚠️ No users in DB yet'}`);
    console.log('');

    console.log('🧪 Test complete!');
  },
};

// Expose to window for easy browser console access
if (typeof window !== 'undefined') {
  (window as any).testAuthFlow = authFlowTester;
  console.log('✅ Auth flow tester loaded!');
  console.log('Usage: window.testAuthFlow.getStatus()');
}

export default authFlowTester;
