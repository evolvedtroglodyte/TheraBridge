import { test, expect } from '@playwright/test';

/**
 * Font Verification Tests for Dashboard Cards
 *
 * Verifies that all dashboard cards use consistent fonts matching SessionCard:
 * - Titles: Crimson Pro, 20px, weight 600
 * - Section labels: Inter, 11px, weight 500, uppercase
 * - Body text: Crimson Pro, 14px, weight 400
 * - List items: Crimson Pro, 13px, weight 300
 */

test.describe('Dashboard Font Consistency', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    // Wait for dashboard to fully load
    await page.waitForLoadState('networkidle');
  });

  test('Your Journey card has correct title font', async ({ page }) => {
    const title = page.getByText('Your Journey').first();

    // Get computed styles
    const fontFamily = await title.evaluate(el =>
      window.getComputedStyle(el).fontFamily
    );
    const fontSize = await title.evaluate(el =>
      window.getComputedStyle(el).fontSize
    );
    const fontWeight = await title.evaluate(el =>
      window.getComputedStyle(el).fontWeight
    );

    // Verify fonts
    expect(fontFamily).toContain('Crimson Pro');
    expect(fontSize).toBe('20px');
    expect(fontWeight).toBe('600');
  });

  test('To-Do card has correct title font', async ({ page }) => {
    const title = page.getByText('To-Do', { exact: true }).first();

    const fontFamily = await title.evaluate(el =>
      window.getComputedStyle(el).fontFamily
    );
    const fontSize = await title.evaluate(el =>
      window.getComputedStyle(el).fontSize
    );
    const fontWeight = await title.evaluate(el =>
      window.getComputedStyle(el).fontWeight
    );

    expect(fontFamily).toContain('Crimson Pro');
    expect(fontSize).toBe('20px');
    expect(fontWeight).toBe('600');
  });

  test('Session Bridge card has correct title font', async ({ page }) => {
    const title = page.getByText('Session Bridge').first();

    const fontFamily = await title.evaluate(el =>
      window.getComputedStyle(el).fontFamily
    );
    const fontSize = await title.evaluate(el =>
      window.getComputedStyle(el).fontSize
    );
    const fontWeight = await title.evaluate(el =>
      window.getComputedStyle(el).fontWeight
    );

    expect(fontFamily).toContain('Crimson Pro');
    expect(fontSize).toBe('20px');
    expect(fontWeight).toBe('600');
  });

  test('Section labels have correct uppercase Inter font', async ({ page }) => {
    // Find "CURRENT FOCUS:" label in Your Journey card
    const label = page.locator('p').filter({ hasText: 'Current focus:' }).first();

    const fontFamily = await label.evaluate(el =>
      window.getComputedStyle(el).fontFamily
    );
    const fontSize = await label.evaluate(el =>
      window.getComputedStyle(el).fontSize
    );
    const fontWeight = await label.evaluate(el =>
      window.getComputedStyle(el).fontWeight
    );
    const textTransform = await label.evaluate(el =>
      window.getComputedStyle(el).textTransform
    );
    const letterSpacing = await label.evaluate(el =>
      window.getComputedStyle(el).letterSpacing
    );

    expect(fontFamily).toContain('Inter');
    expect(fontSize).toBe('11px');
    expect(fontWeight).toBe('500');
    expect(textTransform).toBe('uppercase');
    expect(letterSpacing).toBe('1px');
  });

  test('Body text uses Crimson Pro with correct weight', async ({ page }) => {
    // Find the summary text in Your Journey card
    const bodyText = page.locator('.bg-gradient-to-br.from-white p').first();

    const fontFamily = await bodyText.evaluate(el =>
      window.getComputedStyle(el).fontFamily
    );
    const fontSize = await bodyText.evaluate(el =>
      window.getComputedStyle(el).fontSize
    );
    const fontWeight = await bodyText.evaluate(el =>
      window.getComputedStyle(el).fontWeight
    );

    expect(fontFamily).toContain('Crimson Pro');
    expect(fontSize).toBe('14px');
    expect(fontWeight).toBe('400');
  });

  test('List items use Crimson Pro with font-weight 300', async ({ page }) => {
    // Find list items in Your Journey card
    const listItem = page.locator('li span').filter({ hasText: 'Reduced' }).first();

    const fontFamily = await listItem.evaluate(el =>
      window.getComputedStyle(el.parentElement!).fontFamily
    );
    const fontSize = await listItem.evaluate(el =>
      window.getComputedStyle(el.parentElement!).fontSize
    );
    const fontWeight = await listItem.evaluate(el =>
      window.getComputedStyle(el.parentElement!).fontWeight
    );

    expect(fontFamily).toContain('Crimson Pro');
    expect(fontSize).toBe('13px');
    expect(fontWeight).toBe('300');
  });

  test('Visual comparison - screenshot test', async ({ page }) => {
    // Take a screenshot of the dashboard for visual regression testing
    await expect(page).toHaveScreenshot('dashboard-fonts.png', {
      fullPage: false,
      maxDiffPixels: 100,
    });
  });
});

test.describe('Modal Font Consistency', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');
  });

  test('Modal title has correct font (24px, weight 600)', async ({ page }) => {
    // Click Your Journey card to open modal
    await page.getByText('Your Journey').first().click();

    // Wait for modal to appear
    await page.waitForSelector('[role="dialog"]', { state: 'visible' });

    // Find modal title
    const modalTitle = page.locator('[role="dialog"] h2').first();

    const fontFamily = await modalTitle.evaluate(el =>
      window.getComputedStyle(el).fontFamily
    );
    const fontSize = await modalTitle.evaluate(el =>
      window.getComputedStyle(el).fontSize
    );
    const fontWeight = await modalTitle.evaluate(el =>
      window.getComputedStyle(el).fontWeight
    );

    expect(fontFamily).toContain('Crimson Pro');
    expect(fontSize).toBe('24px');
    expect(fontWeight).toBe('600');
  });
});
