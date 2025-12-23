import { test, expect } from '@playwright/test';

/**
 * Sessions Page Header Tests
 * - Verify TheraBridge logo is on the left
 * - Verify navigation is centered
 * - Verify routing works correctly
 */

test.describe('Sessions Page Header', () => {
  test.beforeEach(async ({ page }) => {
    // Start from dashboard
    await page.goto('http://localhost:3000/patient');
    await page.waitForLoadState('networkidle');
  });

  test('should have TheraBridge logo on the left when on sessions page', async ({ page }) => {
    // Click Sessions button to navigate
    await page.click('text=Sessions');
    await page.waitForURL('**/patient/dashboard-v3/sessions');
    await page.waitForSelector('header', { timeout: 5000 });

    // Get header
    const header = page.locator('header').first();
    const headerBox = await header.boundingBox();
    expect(headerBox).not.toBeNull();

    // Find TheraBridge logo (it contains both "THERA" and "BRIDGE" text)
    const logo = page.locator('header').locator('text=THERA').first();
    const logoBox = await logo.boundingBox();
    expect(logoBox).not.toBeNull();

    // Logo should be on the left side (within first 300px of header)
    expect(logoBox!.x).toBeLessThan(300);
  });

  test('should navigate to dashboard-v3/sessions when clicking Sessions button', async ({ page }) => {
    // Click Sessions button
    await page.click('text=Sessions');

    // Wait for navigation
    await page.waitForURL('**/patient/dashboard-v3/sessions');

    // Verify URL
    expect(page.url()).toContain('/patient/dashboard-v3/sessions');
  });

  test('should navigate back to dashboard and then back to sessions with correct URL', async ({ page }) => {
    // Navigate to sessions
    await page.click('text=Sessions');
    await page.waitForURL('**/patient/dashboard-v3/sessions');
    expect(page.url()).toContain('/patient/dashboard-v3/sessions');

    // Navigate back to dashboard
    await page.click('text=Dashboard');
    await page.waitForURL('**/patient');
    expect(page.url()).toMatch(/\/patient\/?$/);

    // Navigate to sessions again
    await page.click('text=Sessions');
    await page.waitForURL('**/patient/dashboard-v3/sessions');

    // Verify URL is still correct (not reverting to /patient/sessions)
    expect(page.url()).toContain('/patient/dashboard-v3/sessions');
    expect(page.url()).not.toContain('/patient/sessions');
  });

  test('should have sidebar with home and theme toggle on sessions page', async ({ page }) => {
    // Navigate to sessions
    await page.click('text=Sessions');
    await page.waitForURL('**/patient/dashboard-v3/sessions');

    // Check for sidebar home button (SVG with house icon)
    const homeButton = page.locator('button').filter({ has: page.locator('svg') }).first();
    expect(await homeButton.count()).toBeGreaterThan(0);

    // Check for theme toggle button
    const themeButtons = page.locator('button').filter({ has: page.locator('svg') });
    expect(await themeButtons.count()).toBeGreaterThanOrEqual(2); // At least home + theme
  });

  test('should take screenshot of sessions page with new header layout', async ({ page }) => {
    // Navigate to sessions
    await page.click('text=Sessions');
    await page.waitForURL('**/patient/dashboard-v3/sessions');
    await page.waitForSelector('header');

    // Take screenshot
    await page.screenshot({
      path: 'screenshots/sessions-page-header-layout.png',
      fullPage: true
    });
  });
});
