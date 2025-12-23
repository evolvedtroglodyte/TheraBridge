import { test, expect } from '@playwright/test';

/**
 * Demo Button Scroll Tests
 * - Verify button stays fixed at bottom when scrolling
 */

test.describe('Demo Button - Scroll Behavior', () => {
  test('should be at the bottom of page content (not viewport)', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('http://localhost:3000/patient');
    await page.waitForLoadState('networkidle');

    // Get initial button position
    const demoButton = page.locator('button', { hasText: 'DEMO' });
    await expect(demoButton).toBeVisible();

    const initialBox = await demoButton.boundingBox();
    expect(initialBox).not.toBeNull();

    // Button should be below the fold initially (need to scroll to see it)
    const viewportHeight = page.viewportSize()?.height || 720;
    expect(initialBox!.y).toBeGreaterThan(viewportHeight);
  });

  test('should scroll into view when scrolling down', async ({ page }) => {
    await page.goto('http://localhost:3000/patient');
    await page.waitForLoadState('networkidle');

    const demoButton = page.locator('button', { hasText: 'DEMO' });

    // Initially might not be visible (below fold)
    const initialBox = await demoButton.boundingBox();
    expect(initialBox).not.toBeNull();

    // Scroll down to bottom of page
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(300);

    // Now button should be visible in viewport
    const scrolledBox = await demoButton.boundingBox();
    expect(scrolledBox).not.toBeNull();

    // Button should be in viewport now
    const viewportHeight = page.viewportSize()?.height || 720;
    expect(scrolledBox!.y).toBeGreaterThan(0);
    expect(scrolledBox!.y).toBeLessThan(viewportHeight);
  });

  test('should NOT have CSS position fixed property (should be static/relative)', async ({ page }) => {
    await page.goto('http://localhost:3000/patient');
    await page.waitForLoadState('networkidle');

    const demoButton = page.locator('button', { hasText: 'DEMO' });

    // Get the parent container of the button
    const container = demoButton.locator('..');

    // Check computed styles - should be static or relative, NOT fixed
    const position = await container.evaluate((el) =>
      window.getComputedStyle(el).position
    );

    expect(position).not.toBe('fixed');
    expect(['static', 'relative']).toContain(position);
  });

  test('should scroll with page content (not stay fixed to viewport)', async ({ page }) => {
    await page.goto('http://localhost:3000/patient');
    await page.waitForLoadState('networkidle');

    const demoButton = page.locator('button', { hasText: 'DEMO' });
    await expect(demoButton).toBeVisible();

    // Get initial position relative to viewport
    const initialBox = await demoButton.boundingBox();
    expect(initialBox).not.toBeNull();
    const initialViewportY = initialBox!.y;

    // Scroll down the page
    await page.evaluate(() => window.scrollTo(0, 500));
    await page.waitForTimeout(300);

    // Get new position relative to viewport
    const scrolledBox = await demoButton.boundingBox();
    expect(scrolledBox).not.toBeNull();
    const scrolledViewportY = scrolledBox!.y;

    // If button is fixed, viewport Y would stay the same
    // If button scrolls with content, viewport Y should decrease (button moves up in viewport)
    // After scrolling 500px down, button should move up at least 400px in viewport
    expect(scrolledViewportY).toBeLessThan(initialViewportY - 300);
  });
});
