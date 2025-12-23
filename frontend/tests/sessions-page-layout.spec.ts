import { test, expect } from '@playwright/test';

/**
 * Sessions Page Layout Tests
 * - Verify spacing between session cards
 * - Verify pagination is centered
 * - Verify no timeline present
 */

test.describe('Sessions Page Layout', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to sessions page
    await page.goto('http://localhost:3000/patient/dashboard-v3/sessions');

    // Wait for content to load
    await page.waitForSelector('[id^="session-"]', { timeout: 10000 });
  });

  test('should have reduced spacing between session cards', async ({ page }) => {
    // Get all session cards
    const cards = page.locator('[id^="session-"]');
    const cardCount = await cards.count();

    expect(cardCount).toBeGreaterThan(1);

    // Get first two cards in same row
    const firstCard = cards.nth(0);
    const secondCard = cards.nth(1);

    const firstBox = await firstCard.boundingBox();
    const secondBox = await secondCard.boundingBox();

    expect(firstBox).not.toBeNull();
    expect(secondBox).not.toBeNull();

    // Calculate horizontal gap between cards
    const gap = secondBox!.x - (firstBox!.x + firstBox!.width);

    // Gap should be around 10px - allowing up to 3px variance due to scaling/rounding
    expect(gap).toBeGreaterThanOrEqual(7);
    expect(gap).toBeLessThanOrEqual(13);
  });

  test('should have pagination centered on page', async ({ page }) => {
    // Check if pagination exists (might not if only 1 page)
    const pagination = page.locator('nav[aria-label="Session pages"]');
    const paginationCount = await pagination.count();

    if (paginationCount > 0) {
      const paginationBox = await pagination.boundingBox();
      const mainContent = page.locator('main');
      const mainBox = await mainContent.boundingBox();

      expect(paginationBox).not.toBeNull();
      expect(mainBox).not.toBeNull();

      // Calculate center position of pagination relative to main content area
      const paginationCenter = paginationBox!.x + (paginationBox!.width / 2);
      const mainContentCenter = mainBox!.x + (mainBox!.width / 2);

      // Should be centered within the main content area (within 10px tolerance)
      expect(Math.abs(paginationCenter - mainContentCenter)).toBeLessThan(10);
    }
  });

  test('should NOT have timeline component visible', async ({ page }) => {
    // Check that TimelineSidebar is not rendered on sessions page
    const timelineSidebar = page.locator('[class*="TimelineSidebar"]');
    const timelineCount = await timelineSidebar.count();

    expect(timelineCount).toBe(0);

    // Also check for any timeline-related elements
    const timelineElements = page.locator('[class*="timeline"]');
    const timelineElementsCount = await timelineElements.count();

    // Should be 0 or very minimal
    expect(timelineElementsCount).toBeLessThanOrEqual(1);
  });

  test('should take screenshot of sessions page layout', async ({ page }) => {
    // Take full page screenshot for visual verification
    await page.screenshot({
      path: 'screenshots/sessions-page-layout.png',
      fullPage: true
    });
  });
});
