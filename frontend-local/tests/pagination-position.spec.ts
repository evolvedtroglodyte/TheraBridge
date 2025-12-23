import { test, expect } from '@playwright/test';

/**
 * Pagination Position Investigation Tests
 *
 * Examines why pagination dots move when switching between session card pages.
 */

test.describe('Session Cards Pagination Position', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForLoadState('networkidle');
  });

  test('Compare pagination position between page 1 and page 2', async ({ page }) => {
    // Wait for page to fully load
    await page.waitForTimeout(1000);

    // Log initial scroll position
    const initialScrollY = await page.evaluate(() => window.scrollY);
    console.log('Initial scroll Y:', initialScrollY);

    // Find the pagination nav
    const paginationNav = page.locator('nav[aria-label="Session pages"]');

    // Check if pagination exists (need more than 1 page)
    const paginationExists = await paginationNav.count() > 0;
    console.log('Pagination exists:', paginationExists);

    if (!paginationExists) {
      console.log('No pagination - only 1 page of sessions');
      return;
    }

    // Get pagination position on page 1
    const page1NavBox = await paginationNav.boundingBox();
    console.log('Page 1 - Pagination position:', page1NavBox);

    // Take screenshot of page 1
    await page.screenshot({ path: 'test-results/session-grid-page1.png', fullPage: true });

    // Get the parent container (h-[650px] div wrapping SessionCardsGrid)
    const sessionGridParent = page.locator('.h-\\[650px\\]').first();
    const parentBox = await sessionGridParent.boundingBox();
    console.log('Page 1 - Parent container (650px min-height):', parentBox);

    // Get the swipe container inside
    const swipeContainer = sessionGridParent.locator('> div').first();
    const swipeBox = await swipeContainer.boundingBox();
    console.log('Page 1 - Swipe container:', swipeBox);

    // Scroll pagination into view first (simulating user who can see it)
    await paginationNav.scrollIntoViewIfNeeded();
    await page.waitForTimeout(100);

    // Log scroll before click (pagination should now be visible)
    const preClickScrollY = await page.evaluate(() => window.scrollY);
    console.log('Pre-click scroll Y:', preClickScrollY);

    // Listen for console logs
    page.on('console', msg => {
      if (msg.text().includes('[SessionCardsGrid]')) {
        console.log('BROWSER LOG:', msg.text());
      }
    });

    // Click second pagination dot to go to page 2
    const secondDot = paginationNav.locator('button').nth(1);
    await secondDot.click();
    await page.waitForTimeout(500);

    // Log scroll after click
    const postClickScrollY = await page.evaluate(() => window.scrollY);
    console.log('Post-click scroll Y:', postClickScrollY);
    console.log('Scroll changed by:', postClickScrollY - preClickScrollY);

    // Get pagination position on page 2
    const page2NavBox = await paginationNav.boundingBox();
    console.log('Page 2 - Pagination position:', page2NavBox);

    // Take screenshot of page 2
    await page.screenshot({ path: 'test-results/session-grid-page2.png', fullPage: true });

    // Get container dimensions on page 2
    const parentBox2 = await sessionGridParent.boundingBox();
    console.log('Page 2 - Parent container:', parentBox2);

    const swipeBox2 = await swipeContainer.boundingBox();
    console.log('Page 2 - Swipe container:', swipeBox2);

    // Calculate the position relative to their parent containers (not viewport)
    // The pagination should be at the SAME offset within its parent on both pages
    if (page1NavBox && page2NavBox && parentBox && parentBox2) {
      // Position relative to parent
      const page1RelativeY = page1NavBox.y - parentBox.y;
      const page2RelativeY = page2NavBox.y - parentBox2.y;

      console.log('Page 1 - Nav relative to parent:', page1RelativeY);
      console.log('Page 2 - Nav relative to parent:', page2RelativeY);

      const relativeYDiff = page2RelativeY - page1RelativeY;
      console.log('Relative Y difference:', relativeYDiff);
      console.log('Pagination SHIFTED within container:', relativeYDiff !== 0);

      // The pagination should be at the same position relative to its container
      expect(Math.abs(relativeYDiff)).toBeLessThan(2);
    }

    // Check the session cards on each page
    const sessionCards = page.locator('[id^="session-"]');
    const cardCount = await sessionCards.count();
    console.log('Cards on page 2:', cardCount);

    // Get first card height on page 2
    if (cardCount > 0) {
      const firstCard = sessionCards.first();
      const cardBox = await firstCard.boundingBox();
      console.log('First card on page 2:', cardBox);
    }
  });

  test('Verify grid maintains fixed height with fewer cards', async ({ page }) => {
    await page.waitForTimeout(1000);

    // Get the main grid area dimensions - the first .h-[650px] is SessionCardsGrid parent
    const gridArea = page.locator('.h-\\[650px\\]').first().locator('.flex-1').first();
    const pagination = page.locator('nav[aria-label="Session pages"]');

    if (await pagination.count() === 0) {
      console.log('No pagination - skipping test');
      return;
    }

    // Measure on page 1
    const gridBox1 = await gridArea.boundingBox();
    console.log('Page 1 - Grid area:', gridBox1);

    // Go to page 2
    await pagination.locator('button').nth(1).click();
    await page.waitForTimeout(500);

    // Measure on page 2
    const gridBox2 = await gridArea.boundingBox();
    console.log('Page 2 - Grid area:', gridBox2);

    if (gridBox1 && gridBox2) {
      console.log('Grid height difference:', gridBox2.height - gridBox1.height);
      // Grid should maintain same height
      expect(Math.abs(gridBox2.height - gridBox1.height)).toBeLessThan(2);
    }
  });
});
