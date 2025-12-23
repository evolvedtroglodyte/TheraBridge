import { test, expect } from '@playwright/test';

/**
 * Timeline Search Tests
 *
 * Tests the search functionality in the expanded timeline modal.
 */

test.describe('Timeline Search', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForTimeout(500);

    // Open expanded timeline
    await page.click('button[aria-label="Expand timeline"]');
    await page.waitForTimeout(300);
  });

  test('search bar is visible in expanded timeline', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const searchInput = modal.locator('input[placeholder*="Search"]');

    await expect(searchInput).toBeVisible();
  });

  test('typing in search filters results', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const searchInput = modal.locator('input[placeholder*="Search"]');

    // Get initial count
    const initialCount = await modal.locator('[data-event-id]').count();
    expect(initialCount).toBe(14); // 10 sessions + 4 major events

    // Search for "boundary"
    await searchInput.fill('boundary');
    await page.waitForTimeout(400); // Wait for debounce

    // Should have fewer results
    const filteredCount = await modal.locator('[data-event-id]').count();
    expect(filteredCount).toBeLessThan(initialCount);
    expect(filteredCount).toBeGreaterThan(0);
  });

  test('search finds sessions by topic', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const searchInput = modal.locator('input[placeholder*="Search"]');

    await searchInput.fill('perfectionism');
    await page.waitForTimeout(400);

    // Should find the work stress/perfectionism session
    const results = modal.locator('[data-event-id]');
    expect(await results.count()).toBeGreaterThan(0);

    // Check that result contains perfectionism
    await expect(modal.getByText(/perfectionism/i)).toBeVisible();
  });

  test('search finds sessions by strategy', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const searchInput = modal.locator('input[placeholder*="Search"]');

    await searchInput.fill('TIPP');
    await page.waitForTimeout(400);

    // Should find the DBT/TIPP session
    await expect(modal.getByText(/TIPP/i)).toBeVisible();
  });

  test('search finds major events by title', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const searchInput = modal.locator('input[placeholder*="Search"]');

    await searchInput.fill('promoted');
    await page.waitForTimeout(400);

    // Should find "Got promoted at work" event
    await expect(modal.getByText(/promoted/i)).toBeVisible();

    // Should be a major event
    const majorEvents = modal.locator('[data-event-type="major_event"]');
    expect(await majorEvents.count()).toBeGreaterThan(0);
  });

  test('search finds major events by summary', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const searchInput = modal.locator('input[placeholder*="Search"]');

    await searchInput.fill('meditation');
    await page.waitForTimeout(400);

    // Should find the meditation major event
    await expect(modal.getByText(/meditation/i)).toBeVisible();
  });

  test('clear button resets search', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const searchInput = modal.locator('input[placeholder*="Search"]');

    // Search for something
    await searchInput.fill('boundary');
    await page.waitForTimeout(400);

    const filteredCount = await modal.locator('[data-event-id]').count();

    // Click clear button
    await modal.locator('button[aria-label="Clear search"]').click();
    await page.waitForTimeout(100);

    // Search input should be empty
    await expect(searchInput).toHaveValue('');

    // Should show all results again
    const resetCount = await modal.locator('[data-event-id]').count();
    expect(resetCount).toBe(14);
    expect(resetCount).toBeGreaterThan(filteredCount);
  });

  test('empty state shows when no results', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const searchInput = modal.locator('input[placeholder*="Search"]');

    // Search for something that doesn't exist
    await searchInput.fill('xyznonexistent123');
    await page.waitForTimeout(400);

    // Should show empty state
    await expect(modal.getByText(/No results found/)).toBeVisible();
    await expect(modal.getByText('Clear search')).toBeVisible();

    // No timeline entries should be visible
    const entries = modal.locator('[data-event-id]');
    expect(await entries.count()).toBe(0);
  });

  test('clicking "Clear search" in empty state resets', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const searchInput = modal.locator('input[placeholder*="Search"]');

    // Get to empty state
    await searchInput.fill('xyznonexistent123');
    await page.waitForTimeout(400);

    // Click clear search link
    await modal.getByText('Clear search').click();
    await page.waitForTimeout(100);

    // Should show all results
    const count = await modal.locator('[data-event-id]').count();
    expect(count).toBe(14);
  });

  test('search shows result count', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const searchInput = modal.locator('input[placeholder*="Search"]');

    await searchInput.fill('boundary');
    await page.waitForTimeout(400);

    // Should show result count
    await expect(modal.getByText(/result.*for.*boundary/i)).toBeVisible();
  });

  test('search is debounced (no flicker)', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    const searchInput = modal.locator('input[placeholder*="Search"]');

    // Type quickly
    await searchInput.type('boun', { delay: 50 });

    // Should still show all results (debounce hasn't fired)
    let count = await modal.locator('[data-event-id]').count();
    expect(count).toBe(14);

    // Wait for debounce
    await page.waitForTimeout(400);

    // Now should be filtered
    count = await modal.locator('[data-event-id]').count();
    expect(count).toBeLessThan(14);
  });
});
