import { test, expect } from '@playwright/test';

/**
 * Demo Button Tests
 * - Verify demo button appears on dashboard
 * - Verify click behavior (reveals "Skip to Auth")
 */

test.describe('Demo Button', () => {
  test('should show DEMO button on dashboard', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('http://localhost:3000/patient');
    await page.waitForLoadState('networkidle');

    // Check for DEMO button (it has "DEMO" text in monospace font)
    const demoButton = page.locator('button', { hasText: 'DEMO' });

    // Should be visible
    await expect(demoButton).toBeVisible();

    // Should be at the bottom center
    const buttonBox = await demoButton.boundingBox();
    expect(buttonBox).not.toBeNull();

    const viewportWidth = page.viewportSize()?.width || 1280;
    const viewportHeight = page.viewportSize()?.height || 720;

    // Button should be horizontally centered (within 100px of center)
    const buttonCenterX = buttonBox!.x + (buttonBox!.width / 2);
    const pageCenterX = viewportWidth / 2;
    expect(Math.abs(buttonCenterX - pageCenterX)).toBeLessThan(100);

    // Button should be near the bottom (within 100px)
    expect(buttonBox!.y).toBeGreaterThan(viewportHeight - 100);
  });

  test('should reveal "Skip to Auth" after clicking DEMO', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('http://localhost:3000/patient');
    await page.waitForLoadState('networkidle');

    // Click DEMO button
    const demoButton = page.locator('button', { hasText: 'DEMO' });
    await demoButton.click();

    // Wait for animation
    await page.waitForTimeout(500);

    // Skip to Auth button should now be visible
    const skipButton = page.locator('button', { hasText: 'Skip to Auth' });
    await expect(skipButton).toBeVisible();
  });

  test('should navigate to auth page when clicking "Skip to Auth"', async ({ page }) => {
    // Navigate to dashboard
    await page.goto('http://localhost:3000/patient');
    await page.waitForLoadState('networkidle');

    // Click DEMO button first
    const demoButton = page.locator('button', { hasText: 'DEMO' });
    await demoButton.click();
    await page.waitForTimeout(500);

    // Click Skip to Auth
    const skipButton = page.locator('button', { hasText: 'Skip to Auth' });
    await skipButton.click();

    // Should navigate to auth page
    await page.waitForURL('**/auth/login');
    expect(page.url()).toContain('/auth/login');
  });
});
