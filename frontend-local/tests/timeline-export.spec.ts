import { test, expect } from '@playwright/test';

/**
 * Timeline Export Tests
 *
 * Tests the export functionality including:
 * - PDF download (opens print dialog)
 * - Shareable link copy to clipboard
 */

test.describe('Timeline Export', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForTimeout(500);

    // Open expanded timeline
    await page.click('button[aria-label="Expand timeline"]');
    await page.waitForTimeout(300);
  });

  test('export button is visible in expanded timeline', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');

    // Look for Export button
    await expect(modal.getByText('Export')).toBeVisible();
  });

  test('dropdown opens on export button click', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');

    // Click export button
    await modal.getByText('Export').click();
    await page.waitForTimeout(100);

    // Dropdown should be visible with options
    await expect(page.getByText('Download PDF')).toBeVisible();
    await expect(page.getByText('Copy shareable link')).toBeVisible();
  });

  test('PDF option triggers print dialog', async ({ page, context }) => {
    const modal = page.locator('[role="dialog"]');

    // Track new pages/popups
    const newPagePromise = context.waitForEvent('page');

    // Click export and then PDF
    await modal.getByText('Export').click();
    await page.waitForTimeout(100);
    await page.getByText('Download PDF').click();

    // Should open a new window with the PDF HTML
    const newPage = await newPagePromise;
    await newPage.waitForLoadState('domcontentloaded');

    // New page should contain the timeline content
    await expect(newPage.getByText('My Therapy Journey')).toBeVisible();
    await expect(newPage.locator('.entry')).toHaveCount(14); // 10 sessions + 4 events

    // Close the new page
    await newPage.close();
  });

  test('copy link option copies to clipboard', async ({ page, context }) => {
    const modal = page.locator('[role="dialog"]');

    // Grant clipboard permissions
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Click export and then copy link
    await modal.getByText('Export').click();
    await page.waitForTimeout(100);
    await page.getByText('Copy shareable link').click();
    await page.waitForTimeout(100);

    // Should show success state
    await expect(page.getByText('Link copied!')).toBeVisible();

    // Verify clipboard content
    const clipboardText = await page.evaluate(() => navigator.clipboard.readText());
    expect(clipboardText).toContain('therapybridge.app/share/timeline');
  });

  test('dropdown closes after selection', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');

    // Open dropdown
    await modal.getByText('Export').click();
    await page.waitForTimeout(100);
    await expect(page.getByText('Download PDF')).toBeVisible();

    // Click copy link
    await page.getByText('Copy shareable link').click();
    await page.waitForTimeout(200);

    // Dropdown should close
    await expect(page.getByText('Download PDF')).not.toBeVisible();
  });

  test('dropdown closes when clicking outside', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');

    // Open dropdown
    await modal.getByText('Export').click();
    await page.waitForTimeout(100);
    await expect(page.getByText('Download PDF')).toBeVisible();

    // Click somewhere else in the modal
    await modal.getByText('Your Journey').click();
    await page.waitForTimeout(100);

    // Dropdown should close
    await expect(page.getByText('Download PDF')).not.toBeVisible();
  });

  test('success feedback resets after delay', async ({ page, context }) => {
    const modal = page.locator('[role="dialog"]');
    await context.grantPermissions(['clipboard-read', 'clipboard-write']);

    // Copy link
    await modal.getByText('Export').click();
    await page.waitForTimeout(100);
    await page.getByText('Copy shareable link').click();
    await page.waitForTimeout(100);

    // Should show success
    await expect(page.getByText('Link copied!')).toBeVisible();

    // Wait for reset (2 seconds)
    await page.waitForTimeout(2200);

    // Open dropdown again - should show normal text
    await modal.getByText('Export').click();
    await page.waitForTimeout(100);
    await expect(page.getByText('Copy shareable link')).toBeVisible();
  });
});

test.describe('PDF Content', () => {
  test('PDF includes summary stats', async ({ page, context }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForTimeout(500);
    await page.click('button[aria-label="Expand timeline"]');
    await page.waitForTimeout(300);

    const modal = page.locator('[role="dialog"]');
    const newPagePromise = context.waitForEvent('page');

    await modal.getByText('Export').click();
    await page.waitForTimeout(100);
    await page.getByText('Download PDF').click();

    const pdfPage = await newPagePromise;
    await pdfPage.waitForLoadState('domcontentloaded');

    // Check for stats
    await expect(pdfPage.getByText('10')).toBeVisible(); // Sessions count
    await expect(pdfPage.getByText('4')).toBeVisible(); // Major events count
    await expect(pdfPage.getByText('Sessions')).toBeVisible();
    await expect(pdfPage.getByText('Major Events')).toBeVisible();

    await pdfPage.close();
  });

  test('PDF includes all timeline entries', async ({ page, context }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForTimeout(500);
    await page.click('button[aria-label="Expand timeline"]');
    await page.waitForTimeout(300);

    const modal = page.locator('[role="dialog"]');
    const newPagePromise = context.waitForEvent('page');

    await modal.getByText('Export').click();
    await page.waitForTimeout(100);
    await page.getByText('Download PDF').click();

    const pdfPage = await newPagePromise;
    await pdfPage.waitForLoadState('domcontentloaded');

    // Check for entries
    const entries = pdfPage.locator('.entry');
    await expect(entries).toHaveCount(14);

    // Check for milestone badge
    await expect(pdfPage.locator('.milestone-badge').first()).toBeVisible();

    await pdfPage.close();
  });

  test('PDF includes reflections from major events', async ({ page, context }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForTimeout(500);
    await page.click('button[aria-label="Expand timeline"]');
    await page.waitForTimeout(300);

    const modal = page.locator('[role="dialog"]');
    const newPagePromise = context.waitForEvent('page');

    await modal.getByText('Export').click();
    await page.waitForTimeout(100);
    await page.getByText('Download PDF').click();

    const pdfPage = await newPagePromise;
    await pdfPage.waitForLoadState('domcontentloaded');

    // Check for reflection (me2 has one)
    await expect(pdfPage.locator('.entry-reflection')).toHaveCount(2); // me2 and me4 have reflections

    await pdfPage.close();
  });
});
