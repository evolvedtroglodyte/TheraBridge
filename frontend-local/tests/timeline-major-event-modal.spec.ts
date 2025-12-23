import { test, expect } from '@playwright/test';

/**
 * Major Event Modal Tests
 *
 * Tests the major event modal functionality including:
 * - Display of event details
 * - Related session navigation
 * - Reflection add/edit
 * - Modal accessibility
 */

test.describe('Major Event Modal', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForTimeout(500);

    // Click on a major event to open modal
    const majorEventEntry = page.locator('[data-event-type="major_event"]').first();
    await majorEventEntry.click();
    await page.waitForTimeout(200);
  });

  test('modal opens when major event clicked', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();
  });

  test('modal displays title and date', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');

    // Check for event title (first major event is "Got promoted at work")
    await expect(modal.getByText('Got promoted at work')).toBeVisible();

    // Check for date
    await expect(modal.getByText('Dec 14')).toBeVisible();

    // Check for "Major Event" label
    await expect(modal.getByText('Major Event')).toBeVisible();
  });

  test('modal displays summary and context', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');

    // Check for summary section
    await expect(modal.getByText('Summary')).toBeVisible();

    // Check for context section
    await expect(modal.getByText('Context from Chat')).toBeVisible();
  });

  test('related session link is visible', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');

    // First major event has related session
    await expect(modal.getByText('View related therapy session')).toBeVisible();
  });

  test('clicking related session link navigates to session', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');

    // Click the related session link
    await modal.getByText('View related therapy session').click();

    // Modal should close and session detail should open
    await page.waitForTimeout(300);

    // Should now see session detail (not the major event modal)
    // The session detail should be visible (it's a fullscreen view)
    const sessionDetailVisible = await page.locator('text=Back to Dashboard').isVisible();
    expect(sessionDetailVisible).toBe(true);
  });

  test('modal closes on X button click', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Click close button
    await page.click('button[aria-label="Close modal"]');
    await page.waitForTimeout(200);

    await expect(modal).not.toBeVisible();
  });

  test('modal closes on backdrop click', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    // Click on backdrop (the semi-transparent overlay)
    await page.click('.fixed.inset-0.bg-black\\/30');
    await page.waitForTimeout(200);

    await expect(modal).not.toBeVisible();
  });

  test('modal closes on Escape key', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');
    await expect(modal).toBeVisible();

    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);

    await expect(modal).not.toBeVisible();
  });

  test('modal is centered on screen', async ({ page }) => {
    const modal = page.locator('[role="dialog"]');

    const box = await modal.boundingBox();
    expect(box).not.toBeNull();

    if (box) {
      const viewportSize = page.viewportSize();
      if (viewportSize) {
        const modalCenterX = box.x + box.width / 2;
        const modalCenterY = box.y + box.height / 2;
        const viewportCenterX = viewportSize.width / 2;
        const viewportCenterY = viewportSize.height / 2;

        // Allow some tolerance (50px)
        expect(Math.abs(modalCenterX - viewportCenterX)).toBeLessThan(50);
        expect(Math.abs(modalCenterY - viewportCenterY)).toBeLessThan(50);
      }
    }
  });
});

test.describe('Major Event Reflection', () => {
  test('reflection section is visible', async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForTimeout(500);

    // Click on a major event
    const majorEventEntry = page.locator('[data-event-type="major_event"]').first();
    await majorEventEntry.click();
    await page.waitForTimeout(200);

    const modal = page.locator('[role="dialog"]');
    await expect(modal.getByText('My Reflection')).toBeVisible();
  });

  test('can add reflection to event without one', async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForTimeout(500);

    // First major event (me1) has no reflection
    const majorEventEntry = page.locator('[data-event-type="major_event"]').first();
    await majorEventEntry.click();
    await page.waitForTimeout(200);

    const modal = page.locator('[role="dialog"]');

    // Should see textarea for adding reflection
    const textarea = modal.locator('textarea');
    await expect(textarea).toBeVisible();

    // Type a reflection
    await textarea.fill('This was a great achievement!');

    // Click save
    await modal.getByText('Save Reflection').click();
    await page.waitForTimeout(100);

    // Textarea should disappear and reflection should show
    await expect(modal.getByText('This was a great achievement!')).toBeVisible();
  });

  test('event with existing reflection shows edit button', async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForTimeout(500);

    // Second major event (me2) has a reflection
    const majorEventEntries = page.locator('[data-event-type="major_event"]');

    // Find the "Set boundary with mother" event which has reflection
    for (let i = 0; i < await majorEventEntries.count(); i++) {
      const entry = majorEventEntries.nth(i);
      const text = await entry.textContent();
      if (text?.includes('Set boundary')) {
        await entry.click();
        break;
      }
    }

    await page.waitForTimeout(200);

    const modal = page.locator('[role="dialog"]');

    // Should see existing reflection and edit button
    await expect(modal.getByText(/This was so hard but I did it/)).toBeVisible();
    await expect(modal.getByText('Edit')).toBeVisible();
  });

  test('can edit existing reflection', async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForTimeout(500);

    // Find and click the event with existing reflection
    const majorEventEntries = page.locator('[data-event-type="major_event"]');
    for (let i = 0; i < await majorEventEntries.count(); i++) {
      const entry = majorEventEntries.nth(i);
      const text = await entry.textContent();
      if (text?.includes('Set boundary')) {
        await entry.click();
        break;
      }
    }

    await page.waitForTimeout(200);
    const modal = page.locator('[role="dialog"]');

    // Click edit
    await modal.getByText('Edit').click();

    // Textarea should appear with existing text
    const textarea = modal.locator('textarea');
    await expect(textarea).toBeVisible();

    // Modify the reflection
    await textarea.fill('Updated reflection text');
    await modal.getByText('Save Reflection').click();

    await page.waitForTimeout(100);

    // Should show updated reflection
    await expect(modal.getByText('Updated reflection text')).toBeVisible();
  });
});
