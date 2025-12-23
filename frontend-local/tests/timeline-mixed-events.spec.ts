import { test, expect } from '@playwright/test';

/**
 * Timeline Mixed Events Tests
 *
 * Tests the display and interaction of both sessions and major events
 * in the timeline sidebar.
 */

test.describe('Timeline Mixed Events', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    // Wait for timeline to load (mock data has 300ms delay)
    await page.waitForTimeout(500);
  });

  test('displays both session and major event entries', async ({ page }) => {
    // Check for session entries (data-event-type="session")
    const sessionEntries = page.locator('[data-event-type="session"]');
    await expect(sessionEntries).toHaveCount(10); // 10 mock sessions

    // Check for major event entries (data-event-type="major_event")
    const majorEventEntries = page.locator('[data-event-type="major_event"]');
    await expect(majorEventEntries).toHaveCount(4); // 4 mock major events
  });

  test('sessions show mood-colored dots', async ({ page }) => {
    // Find a session entry and check for mood indicator
    const sessionEntry = page.locator('[data-event-type="session"]').first();
    await expect(sessionEntry).toBeVisible();

    // The session should have a colored dot (not a diamond or star)
    const dot = sessionEntry.locator('.rounded-full');
    await expect(dot).toBeVisible();
  });

  test('sessions with milestones show amber star', async ({ page }) => {
    // Expand timeline to see milestone sessions better
    await page.click('button[aria-label="Expand timeline"]');
    await page.waitForTimeout(300);

    // Look for star icon in the expanded view
    const starIcons = page.locator('[data-event-type="session"] svg.text-amber-500');
    // We have 5 milestone sessions in mock data
    expect(await starIcons.count()).toBeGreaterThanOrEqual(1);
  });

  test('major events show purple diamond icon', async ({ page }) => {
    // Major events should have diamond icon
    const majorEventEntry = page.locator('[data-event-type="major_event"]').first();
    await expect(majorEventEntry).toBeVisible();

    // Check for purple diamond styling
    const diamond = majorEventEntry.locator('svg.text-purple-500');
    await expect(diamond).toBeVisible();
  });

  test('events are sorted chronologically (newest first)', async ({ page }) => {
    // Get all event dates in order
    const entries = page.locator('[data-event-id]');
    const count = await entries.count();

    // Collect dates
    const dates: string[] = [];
    for (let i = 0; i < Math.min(count, 5); i++) {
      const dateText = await entries.nth(i).locator('p').first().textContent();
      if (dateText) dates.push(dateText);
    }

    // Dec 17 should come before Dec 14, etc.
    expect(dates[0]).toContain('Dec 17');
  });

  test('clicking session entry opens session detail', async ({ page }) => {
    // Click on a session entry
    const sessionEntry = page.locator('[data-event-type="session"]').first();
    await sessionEntry.click();

    // Should open session detail (fullscreen modal with transcript)
    await expect(page.locator('[role="dialog"]').or(page.locator('.fixed.inset-0'))).toBeVisible();
  });

  test('clicking major event entry opens major event modal', async ({ page }) => {
    // Click on a major event entry
    const majorEventEntry = page.locator('[data-event-type="major_event"]').first();
    await majorEventEntry.click();

    // Should open major event modal
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Check for major event specific content
    await expect(modal.getByText('Major Event')).toBeVisible();
  });

  test('expanded timeline shows both event types', async ({ page }) => {
    // Click expand button
    await page.click('button[aria-label="Expand timeline"]');
    await page.waitForTimeout(300);

    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Check header text
    await expect(modal.getByText('Your Journey')).toBeVisible();
    await expect(modal.getByText(/sessions/)).toBeVisible();
    await expect(modal.getByText(/major events/)).toBeVisible();

    // Check for both event types in the list
    const sessionEntries = modal.locator('[data-event-type="session"]');
    const majorEventEntries = modal.locator('[data-event-type="major_event"]');

    expect(await sessionEntries.count()).toBeGreaterThan(0);
    expect(await majorEventEntries.count()).toBeGreaterThan(0);
  });
});
