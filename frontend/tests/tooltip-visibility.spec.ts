import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('Dobby Mockup Tooltip Visibility', () => {
  test('light mode - tooltips are visible on hover', async ({ page }) => {
    // Load the light mode mockup
    const mockupPath = path.resolve(__dirname, '../dobby-mockup-light-collapsed.html');
    await page.goto(`file://${mockupPath}`);

    // Wait for the page to fully load
    await page.waitForLoadState('domcontentloaded');

    // Get the sidebar toggle button
    const sidebarToggle = page.locator('.sidebar-toggle').first();

    // Get the tooltip inside the sidebar toggle
    const tooltip = sidebarToggle.locator('.tooltip');

    // Before hover - tooltip should be hidden
    await expect(tooltip).toHaveCSS('opacity', '0');
    await expect(tooltip).toHaveCSS('visibility', 'hidden');

    // Hover over the sidebar toggle
    await sidebarToggle.hover();

    // After hover - tooltip should be visible
    await expect(tooltip).toHaveCSS('opacity', '1');
    await expect(tooltip).toHaveCSS('visibility', 'visible');

    // Check tooltip is not clipped - it should be within the viewport
    const tooltipBox = await tooltip.boundingBox();
    expect(tooltipBox).not.toBeNull();
    expect(tooltipBox!.x).toBeGreaterThanOrEqual(0);
    expect(tooltipBox!.y).toBeGreaterThanOrEqual(0);

    // Check tooltip is to the right of the sidebar (not clipped behind it)
    const sidebarBox = await page.locator('.sidebar').boundingBox();
    expect(tooltipBox!.x).toBeGreaterThan(sidebarBox!.x);

    console.log('Tooltip bounding box:', tooltipBox);
    console.log('Sidebar bounding box:', sidebarBox);
  });

  test('light mode - new chat button tooltip is visible', async ({ page }) => {
    const mockupPath = path.resolve(__dirname, '../dobby-mockup-light-collapsed.html');
    await page.goto(`file://${mockupPath}`);
    await page.waitForLoadState('domcontentloaded');

    const newChatBtn = page.locator('.new-chat-btn');
    const tooltip = newChatBtn.locator('.tooltip');

    // Hover and check visibility
    await newChatBtn.hover();
    await expect(tooltip).toHaveCSS('opacity', '1');
    await expect(tooltip).toHaveCSS('visibility', 'visible');

    // Verify tooltip is visible in viewport
    const tooltipBox = await tooltip.boundingBox();
    expect(tooltipBox).not.toBeNull();
    expect(tooltipBox!.width).toBeGreaterThan(0);
    expect(tooltipBox!.height).toBeGreaterThan(0);
  });

  test('light mode - chats nav item tooltip is visible', async ({ page }) => {
    const mockupPath = path.resolve(__dirname, '../dobby-mockup-light-collapsed.html');
    await page.goto(`file://${mockupPath}`);
    await page.waitForLoadState('domcontentloaded');

    const navItem = page.locator('.nav-item').first();
    const tooltip = navItem.locator('.tooltip');

    // Hover and check visibility
    await navItem.hover();
    await expect(tooltip).toHaveCSS('opacity', '1');
    await expect(tooltip).toHaveCSS('visibility', 'visible');

    // Verify tooltip is visible in viewport
    const tooltipBox = await tooltip.boundingBox();
    expect(tooltipBox).not.toBeNull();
    expect(tooltipBox!.x).toBeGreaterThanOrEqual(0);
  });

  test('dark mode - tooltips are visible on hover', async ({ page }) => {
    // Load the dark mode mockup
    const mockupPath = path.resolve(__dirname, '../dobby-mockup-dark-collapsed.html');
    await page.goto(`file://${mockupPath}`);
    await page.waitForLoadState('domcontentloaded');

    const sidebarToggle = page.locator('.sidebar-toggle').first();
    const tooltip = sidebarToggle.locator('.tooltip');

    // Hover over the sidebar toggle
    await sidebarToggle.hover();

    // After hover - tooltip should be visible
    await expect(tooltip).toHaveCSS('opacity', '1');
    await expect(tooltip).toHaveCSS('visibility', 'visible');

    // Check tooltip is not clipped
    const tooltipBox = await tooltip.boundingBox();
    expect(tooltipBox).not.toBeNull();
    expect(tooltipBox!.x).toBeGreaterThanOrEqual(0);
  });
});
