import { test, expect } from '@playwright/test';

test.describe('UI Regression Check', () => {
  test('Dashboard loads with all key components', async ({ page }) => {
    await page.goto('http://localhost:3000/patient');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for key dashboard cards
    const notesGoalsCard = page.locator('text=Your Journey').first();
    await expect(notesGoalsCard).toBeVisible();

    const todoCard = page.locator('text=To-Do').first();
    await expect(todoCard).toBeVisible();

    const sessionBridgeCard = page.locator('text=Session Bridge').first();
    await expect(sessionBridgeCard).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'test-results/dashboard-current-state.png', fullPage: true });

    console.log('✅ Dashboard loaded successfully');
  });

  test('Sessions page loads with cards', async ({ page }) => {
    await page.goto('http://localhost:3000/patient/dashboard-v3/sessions');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Check for session cards grid
    const sessionGrid = page.locator('.inline-grid');
    await expect(sessionGrid).toBeVisible();

    // Take screenshot
    await page.screenshot({ path: 'test-results/sessions-current-state.png', fullPage: true });

    console.log('✅ Sessions page loaded successfully');
  });

  test('Session card structure is correct', async ({ page }) => {
    await page.goto('http://localhost:3000/patient/dashboard-v3/sessions');
    await page.waitForLoadState('networkidle');

    // Find first session card
    const firstCard = page.locator('[id^="session-card-"]').first();
    await expect(firstCard).toBeVisible();

    // Check for "Strategies / Action Items" section
    const strategiesSection = firstCard.locator('text=Strategies / Action Items');
    await expect(strategiesSection).toBeVisible();

    // Count bullet points (should be 2: 1 strategy + 1 action)
    const bulletPoints = firstCard.locator('ul li');
    const count = await bulletPoints.count();

    console.log(`Found ${count} bullet points in session card`);
    expect(count).toBe(2);
  });
});
