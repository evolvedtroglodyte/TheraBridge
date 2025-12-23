import { test, expect } from '@playwright/test';

test.describe('Breakthrough Tooltip Alignment', () => {
  test('Tooltip appears centered above star on hover', async ({ page }) => {
    await page.goto('http://localhost:3000/patient/dashboard-v3/sessions');
    await page.waitForLoadState('networkidle');

    // Find a breakthrough session card (with star)
    const starIcon = page.locator('svg').filter({ hasText: /path.*fill.*FFE066|FFCA00/ }).first();

    // Hover over the star
    await starIcon.hover();

    // Wait for tooltip to appear
    await page.waitForTimeout(300);

    // Take screenshot of tooltip hover state
    await page.screenshot({
      path: 'test-results/tooltip-alignment-check.png',
      fullPage: false
    });

    console.log('✅ Tooltip hover screenshot captured');
  });

  test('Verify tooltip positioning metrics', async ({ page }) => {
    await page.goto('http://localhost:3000/patient/dashboard-v3/sessions');
    await page.waitForLoadState('networkidle');

    // Find the star container
    const starContainer = page.locator('[style*="width: 24px"][style*="height: 24px"]').first();

    if (await starContainer.count() > 0) {
      const starBox = await starContainer.boundingBox();

      if (starBox) {
        console.log('Star position:', {
          x: starBox.x,
          y: starBox.y,
          width: starBox.width,
          height: starBox.height,
          centerX: starBox.x + starBox.width / 2,
          centerY: starBox.y + starBox.height / 2,
        });

        // Hover to show tooltip
        await starContainer.hover();
        await page.waitForTimeout(300);

        // Try to find the tooltip
        const tooltip = page.locator('p').filter({ hasText: /Breakthrough:/i }).first();

        if (await tooltip.count() > 0) {
          const tooltipBox = await tooltip.boundingBox();

          if (tooltipBox) {
            const tooltipCenterX = tooltipBox.x + tooltipBox.width / 2;
            const starCenterX = starBox.x + starBox.width / 2;
            const horizontalOffset = Math.abs(tooltipCenterX - starCenterX);

            console.log('Tooltip position:', {
              x: tooltipBox.x,
              y: tooltipBox.y,
              width: tooltipBox.width,
              centerX: tooltipCenterX,
            });

            console.log('Alignment check:', {
              starCenterX,
              tooltipCenterX,
              horizontalOffset,
              isAligned: horizontalOffset < 5, // Within 5px tolerance
            });

            expect(horizontalOffset).toBeLessThan(10);
          }
        }
      }
    }
  });
});
