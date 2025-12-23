import { test, expect } from '@playwright/test';

/**
 * Modal Positioning Investigation Tests
 *
 * These tests investigate the issue where modals appear in the bottom-right
 * corner instead of being centered with a grey backdrop.
 */

test.describe('Dashboard Modal Positioning', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    // Wait for page to fully load
    await page.waitForLoadState('networkidle');
  });

  test('To-Do card modal should be centered with backdrop', async ({ page }) => {
    // Find and click the To-Do card
    const todoCard = page.locator('text=To-Do').first();
    await todoCard.click();

    // Wait for modal to appear
    await page.waitForTimeout(500);

    // Take screenshot for visual inspection
    await page.screenshot({ path: 'test-results/todo-modal.png', fullPage: true });

    // Check for backdrop
    const backdrop = page.locator('.fixed.inset-0.bg-black\\/30');
    const backdropVisible = await backdrop.isVisible().catch(() => false);
    console.log('Backdrop visible:', backdropVisible);

    // Check modal positioning
    const modal = page.locator('[role="dialog"]').first();
    const modalBox = await modal.boundingBox();

    if (modalBox) {
      const viewport = page.viewportSize();
      console.log('Modal position:', modalBox);
      console.log('Viewport:', viewport);

      // Calculate expected center
      if (viewport) {
        const expectedCenterX = viewport.width / 2;
        const expectedCenterY = viewport.height / 2;
        const actualCenterX = modalBox.x + modalBox.width / 2;
        const actualCenterY = modalBox.y + modalBox.height / 2;

        console.log('Expected center:', { x: expectedCenterX, y: expectedCenterY });
        console.log('Actual center:', { x: actualCenterX, y: actualCenterY });

        // Check if modal is roughly centered (within 100px tolerance)
        const xDiff = Math.abs(actualCenterX - expectedCenterX);
        const yDiff = Math.abs(actualCenterY - expectedCenterY);

        console.log('Center difference:', { x: xDiff, y: yDiff });
      }
    }

    // Get computed styles of the modal
    const modalStyles = await modal.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        position: styles.position,
        top: styles.top,
        left: styles.left,
        right: styles.right,
        bottom: styles.bottom,
        transform: styles.transform,
        zIndex: styles.zIndex,
        display: styles.display,
      };
    });
    console.log('Modal computed styles:', modalStyles);
  });

  test('Notes/Goals card modal should be centered', async ({ page }) => {
    // Click the Notes/Goals card
    const notesCard = page.locator('text=Notes / Goals').first();
    await notesCard.click();

    await page.waitForTimeout(500);
    await page.screenshot({ path: 'test-results/notes-modal.png', fullPage: true });

    const modal = page.locator('[role="dialog"]').first();
    const modalStyles = await modal.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        position: styles.position,
        top: styles.top,
        left: styles.left,
        transform: styles.transform,
      };
    });
    console.log('Notes modal styles:', modalStyles);
  });

  test('Progress Patterns expand button modal should be centered', async ({ page }) => {
    // Click the expand button on Progress Patterns card
    const expandBtn = page.locator('[aria-label="Expand view"]').first();
    await expandBtn.click();

    await page.waitForTimeout(500);
    await page.screenshot({ path: 'test-results/progress-modal.png', fullPage: true });

    const modal = page.locator('[role="dialog"]').first();
    const box = await modal.boundingBox();
    console.log('Progress modal bounding box:', box);
  });

  test('Therapist Bridge card modal should be centered', async ({ page }) => {
    // Click the Therapist Bridge card
    const bridgeCard = page.locator('text=Therapist Bridge').first();
    await bridgeCard.click();

    await page.waitForTimeout(500);
    await page.screenshot({ path: 'test-results/bridge-modal.png', fullPage: true });

    const modal = page.locator('[role="dialog"]').first();
    const modalStyles = await modal.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        position: styles.position,
        top: styles.top,
        left: styles.left,
        transform: styles.transform,
      };
    });
    console.log('Bridge modal styles:', modalStyles);
  });

  test('Inspect all fixed elements on page', async ({ page }) => {
    // Click To-Do to open a modal
    const todoCard = page.locator('text=To-Do').first();
    await todoCard.click();
    await page.waitForTimeout(500);

    // Find ALL fixed position elements
    const fixedElements = await page.evaluate(() => {
      const allElements = document.querySelectorAll('*');
      const fixedItems: Array<{
        tag: string;
        classes: string;
        position: string;
        zIndex: string;
        rect: DOMRect | null;
      }> = [];

      allElements.forEach((el) => {
        const styles = window.getComputedStyle(el);
        if (styles.position === 'fixed') {
          fixedItems.push({
            tag: el.tagName,
            classes: el.className,
            position: styles.position,
            zIndex: styles.zIndex,
            rect: el.getBoundingClientRect(),
          });
        }
      });

      return fixedItems;
    });

    console.log('All fixed elements:', JSON.stringify(fixedElements, null, 2));
  });
});
