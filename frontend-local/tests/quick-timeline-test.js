/**
 * Quick Timeline Sidebar Test - Standalone Script
 * Uses Playwright API directly for faster testing
 */

const { chromium } = require('playwright');

const BASE_URL = 'http://localhost:3000/patient/dashboard-v3';

// Test results
const results = [];

function addResult(category, name, status, details = '') {
  results.push({ category, name, status, details });
  const icon = status === 'PASS' ? '[PASS]' : status === 'FAIL' ? '[FAIL]' : '[SKIP]';
  console.log(`  ${icon} ${name}${details ? ` - ${details}` : ''}`);
}

async function closeAnyOpenModals(page) {
  // Close any open modals/dialogs that might block interactions
  try {
    // Try pressing Escape multiple times to close modals
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(200);

    // Also try clicking any backdrop overlays
    const backdrop = page.locator('.fixed.inset-0.bg-black\\/30');
    if (await backdrop.count() > 0) {
      await backdrop.click({ force: true });
      await page.waitForTimeout(200);
    }
  } catch (e) {
    // Ignore errors
  }
}

async function runTests() {
  console.log('='.repeat(70));
  console.log('        TIMELINE SIDEBAR TEST REPORT');
  console.log('='.repeat(70));
  console.log(`Test Date: ${new Date().toISOString()}`);
  console.log(`Target URL: ${BASE_URL}`);
  console.log('='.repeat(70));

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  try {
    // Navigate with longer timeout
    console.log('\nNavigating to page...');
    const response = await page.goto(BASE_URL, {
      waitUntil: 'domcontentloaded',
      timeout: 60000
    });

    if (!response || response.status() !== 200) {
      console.log('\n[ERROR] Server not responding correctly');
      console.log(`Status: ${response?.status()}`);
      await browser.close();
      return;
    }

    console.log('Page loaded. Waiting for content...');

    // Wait for any element that indicates React has rendered
    await page.waitForTimeout(3000);

    // Close any initially open modals
    await closeAnyOpenModals(page);

    // Scroll timeline into view first
    await page.evaluate(() => {
      const timeline = document.querySelector('[class*="bg-white"][class*="rounded-xl"]');
      if (timeline) timeline.scrollIntoView();
    });

    // ============================================
    // 1. VISUAL TESTS
    // ============================================
    console.log('\n## 1. VISUAL TESTS\n');

    // 1.1 Timeline sidebar visibility
    const timelineTitle = await page.locator('h3:has-text("Timeline")').count();
    addResult('Visual', '1.1 Timeline sidebar visible', timelineTitle > 0 ? 'PASS' : 'FAIL');

    // 1.2 Gradient connector line - check inline style attribute
    // Note: Browser may render colors as RGB instead of hex
    const gradientStyles = await page.evaluate(() => {
      const divs = document.querySelectorAll('div');
      const withGradient = [];
      divs.forEach(d => {
        if (d.getAttribute('style') && d.getAttribute('style').includes('gradient')) {
          withGradient.push(d.getAttribute('style'));
        }
      });
      return withGradient;
    });

    if (gradientStyles.length > 0) {
      const style = gradientStyles.join(' ');
      // Check for teal (#5AB9B4 = rgb(90, 185, 180))
      const hasTeal = style.includes('#5AB9B4') || style.includes('90, 185, 180');
      // Check for lavender (#B8A5D6 = rgb(184, 165, 214))
      const hasLavender = style.includes('#B8A5D6') || style.includes('184, 165, 214');
      // Check for coral (#F4A69D = rgb(244, 166, 157))
      const hasCoral = style.includes('#F4A69D') || style.includes('244, 166, 157');

      const gradientDetails = `teal:${hasTeal}, lavender:${hasLavender}, coral:${hasCoral}`;
      addResult('Visual', '1.2 Gradient line (teal->lavender->coral)',
        (hasTeal && hasLavender && hasCoral) ? 'PASS' : 'FAIL', gradientDetails);
    } else {
      addResult('Visual', '1.2 Gradient line (teal->lavender->coral)', 'FAIL', 'No gradient element found');
    }

    // 1.3 Mood-colored dots (10px)
    const dots = await page.locator('.w-\\[10px\\].h-\\[10px\\].rounded-full').count();
    addResult('Visual', '1.3 Mood-colored dots (10px)', dots > 0 ? 'PASS' : 'FAIL', `Found ${dots} dots`);

    // 1.4 Star icons for milestones - look specifically in timeline sidebar
    const timelineSidebar = page.locator('[class*="bg-white"][class*="rounded-xl"]').filter({ hasText: 'Timeline' });
    const starsInTimeline = await timelineSidebar.locator('svg').filter({ has: page.locator('[class*="text-amber"]') }).count();
    const lucideStars = await timelineSidebar.locator('[class*="text-amber-500"]').count();
    addResult('Visual', '1.4 Star icons for milestones', lucideStars > 0 ? 'PASS' : 'FAIL', `Found ${lucideStars} stars`);

    // Check glow effect on stars by looking at style attribute
    if (lucideStars > 0) {
      const starEl = timelineSidebar.locator('svg[class*="text-amber"]').first();
      const starStyle = await starEl.getAttribute('style').catch(() => null);
      const hasGlow = starStyle?.includes('drop-shadow');
      addResult('Visual', '1.4a Star icons have glow effect', hasGlow ? 'PASS' : 'FAIL',
        hasGlow ? 'Has drop-shadow filter' : `Style: ${starStyle}`);
    }

    // 1.5 Timeline title
    const titleVisible = await page.locator('h3:has-text("Timeline")').isVisible().catch(() => false);
    addResult('Visual', '1.5 "Timeline" title displayed', titleVisible ? 'PASS' : 'FAIL');

    // ============================================
    // 2. INTERACTION TESTS
    // ============================================
    console.log('\n## 2. INTERACTION TESTS\n');

    // Close any modals before interaction tests
    await closeAnyOpenModals(page);
    await page.waitForTimeout(500);

    // Scroll to timeline area
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(500);

    // 2.1 Click shows popover
    const entryButtons = await page.locator('button[data-session-id]').count();
    addResult('Visual', '2.0 Timeline entries exist', entryButtons > 0 ? 'PASS' : 'FAIL', `Found ${entryButtons} entries`);

    if (entryButtons > 0) {
      // Make sure no modals are blocking
      await closeAnyOpenModals(page);

      const firstEntry = page.locator('button[data-session-id]').first();
      await firstEntry.click({ force: true });
      await page.waitForTimeout(500);

      const popoverVisible = await page.locator('[role="dialog"]').filter({ hasText: 'Session' }).isVisible().catch(() => false);
      addResult('Interaction', '2.1 Click entry shows popover', popoverVisible ? 'PASS' : 'FAIL');

      // 2.2 Popover position (to the LEFT)
      if (popoverVisible) {
        const entryBox = await firstEntry.boundingBox();
        const popover = page.locator('[role="dialog"]').filter({ hasText: 'View Full Session' });
        const popoverBox = await popover.boundingBox();
        if (entryBox && popoverBox) {
          const isLeft = (popoverBox.x + popoverBox.width) < (entryBox.x + 50);
          addResult('Interaction', '2.2 Popover appears to LEFT', isLeft ? 'PASS' : 'FAIL',
            `Popover right: ${Math.round(popoverBox.x + popoverBox.width)}, Entry left: ${Math.round(entryBox.x)}`);
        } else {
          addResult('Interaction', '2.2 Popover appears to LEFT', 'SKIP', 'Could not get bounding boxes');
        }
      }

      // 2.4 Click outside closes popover
      // First ensure popover is open
      if (!await page.locator('[role="dialog"]').filter({ hasText: 'View Full Session' }).isVisible().catch(() => false)) {
        await firstEntry.click({ force: true });
        await page.waitForTimeout(300);
      }

      // Click on the timeline container but outside any entry
      const timelineContainer = page.locator('[class*="bg-white"][class*="rounded-xl"]').filter({ hasText: 'Timeline' });
      const containerBox = await timelineContainer.boundingBox();
      if (containerBox) {
        await page.mouse.click(containerBox.x - 100, containerBox.y + containerBox.height / 2);
      }
      await page.waitForTimeout(400);

      // Check if timeline popover is closed (look for the specific View Full Session popover)
      const timelinePopoverGone = !(await page.locator('[role="dialog"]').filter({ hasText: 'View Full Session' }).isVisible().catch(() => false));
      addResult('Interaction', '2.4 Click outside closes popover', timelinePopoverGone ? 'PASS' : 'FAIL');

      // 2.5 ESC closes popover
      await firstEntry.click({ force: true });
      await page.waitForTimeout(300);
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);

      const popoverClosed = !(await page.locator('[role="dialog"]').filter({ hasText: 'View Full Session' }).isVisible().catch(() => false));
      addResult('Interaction', '2.5 ESC key closes popover', popoverClosed ? 'PASS' : 'FAIL');

      // 2.6 Keyboard navigation
      await closeAnyOpenModals(page);
      await firstEntry.focus();
      await page.keyboard.press('Enter');
      await page.waitForTimeout(500);
      const popoverByKeyboard = await page.locator('[role="dialog"]').filter({ hasText: 'View Full Session' }).isVisible().catch(() => false);
      addResult('Interaction', '2.6 Keyboard Enter activates', popoverByKeyboard ? 'PASS' : 'FAIL');

      // Close for next test
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);

    } else {
      addResult('Interaction', '2.1-2.6 All interaction tests', 'SKIP', 'No timeline entries found');
    }

    // 2.3 Scroll to session card
    await closeAnyOpenModals(page);
    const scrollTestEntry = page.locator('button[data-session-id="s5"]');
    if (await scrollTestEntry.count() > 0) {
      await scrollTestEntry.click({ force: true });
      await page.waitForTimeout(1000);
      const sessionCard = await page.locator('#session-s5').count() > 0;
      addResult('Interaction', '2.3 Click scrolls to session card', sessionCard ? 'PASS' : 'FAIL',
        sessionCard ? 'Card element exists with expected ID' : 'Card not found');
    } else {
      addResult('Interaction', '2.3 Click scrolls to session card', 'SKIP', 'Entry s5 not found');
    }

    // ============================================
    // 3. POPOVER CONTENT TESTS
    // ============================================
    console.log('\n## 3. POPOVER CONTENT TESTS\n');

    // Close any open modals
    await closeAnyOpenModals(page);
    await page.waitForTimeout(300);

    // Open popover for content tests
    const firstEntry = page.locator('button[data-session-id]').first();
    await firstEntry.click({ force: true });
    await page.waitForTimeout(500);

    const popover = page.locator('[role="dialog"]').filter({ hasText: 'View Full Session' });

    if (await popover.isVisible().catch(() => false)) {
      // 3.1 Session number and date
      const headerText = await popover.locator('h4').textContent().catch(() => '');
      addResult('Popover', '3.1 Session number in header', headerText.includes('Session') ? 'PASS' : 'FAIL', headerText);
      addResult('Popover', '3.1a Date in header',
        (headerText.includes('Dec') || headerText.includes('Nov') || headerText.includes('Oct')) ? 'PASS' : 'FAIL');

      // 3.2 Duration
      const popoverContent = await popover.textContent().catch(() => '');
      const hasDuration = popoverContent.includes('minutes');
      addResult('Popover', '3.2 Duration shown', hasDuration ? 'PASS' : 'FAIL');

      // 3.3 Mood indicator
      const hasMoodText = popoverContent.toLowerCase().includes('positive') ||
                          popoverContent.toLowerCase().includes('neutral') ||
                          popoverContent.toLowerCase().includes('low');
      const hasMoodDot = await popover.locator('.w-3.h-3.rounded-full').count() > 0;
      addResult('Popover', '3.3 Mood indicator', (hasMoodText || hasMoodDot) ? 'PASS' : 'FAIL');

      // 3.4 Topics section
      const hasTopics = popoverContent.toLowerCase().includes('topics');
      const hasBullets = await popover.locator('ul li').count() > 0;
      addResult('Popover', '3.4 Topics section', hasTopics ? 'PASS' : 'FAIL');
      addResult('Popover', '3.4a Topics have bullets', hasBullets ? 'PASS' : 'FAIL');

      // 3.5 Strategy section
      const hasStrategy = popoverContent.toLowerCase().includes('strategy');
      addResult('Popover', '3.5 Strategy section', hasStrategy ? 'PASS' : 'FAIL');

      // 3.7 View Full Session button
      const viewButton = await popover.locator('button:has-text("View Full Session")').count() > 0;
      addResult('Popover', '3.7 View Full Session button', viewButton ? 'PASS' : 'FAIL');
    } else {
      addResult('Popover', '3.1-3.7 All popover tests', 'SKIP', 'Could not open popover');
    }

    // Close and test milestone popover
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    // 3.6 Milestone section (test with a milestone entry)
    const milestoneEntry = page.locator('button[data-session-id="s9"]');
    if (await milestoneEntry.count() > 0) {
      await milestoneEntry.click({ force: true });
      await page.waitForTimeout(500);
      const milestonePopover = page.locator('[role="dialog"]').filter({ hasText: 'View Full Session' });
      if (await milestonePopover.isVisible().catch(() => false)) {
        const hasMilestone = await milestonePopover.locator('[class*="bg-amber"]').count() > 0;
        const hasMilestoneStar = await milestonePopover.locator('[class*="text-amber"]').count() > 0;
        const popoverText = await milestonePopover.textContent().catch(() => '');
        const hasBreakthroughText = popoverText.toLowerCase().includes('breakthrough') ||
                                    popoverText.toLowerCase().includes('milestone');
        addResult('Popover', '3.6 Milestone section (for milestones)',
          (hasMilestone || hasMilestoneStar || hasBreakthroughText) ? 'PASS' : 'FAIL');
      } else {
        addResult('Popover', '3.6 Milestone section', 'SKIP', 'Could not open milestone popover');
      }
    } else {
      addResult('Popover', '3.6 Milestone section', 'SKIP', 'Milestone entry s9 not found');
    }

    // ============================================
    // 4. STYLING TESTS
    // ============================================
    console.log('\n## 4. STYLING TESTS\n');

    // 4.1 Sticky/fixed positioning (in fixed height container)
    const fixedContainer = await page.locator('.h-\\[650px\\]').count() > 0;
    addResult('Styling', '4.1 Fixed height container (650px)', fixedContainer ? 'PASS' : 'FAIL');

    // 4.2 White background with border
    const timelineBox = page.locator('[class*="bg-white"][class*="rounded-xl"]').filter({ hasText: 'Timeline' });
    const hasWhiteBg = await timelineBox.count() > 0;
    addResult('Styling', '4.2 White background', hasWhiteBg ? 'PASS' : 'FAIL');

    if (hasWhiteBg) {
      const classes = await timelineBox.first().getAttribute('class') || '';
      const hasBorder = classes.includes('border');
      addResult('Styling', '4.2a Subtle border', hasBorder ? 'PASS' : 'FAIL');
    }

    // 4.3 Border radius (rounded-xl = 12px)
    const roundedXl = await page.locator('[class*="rounded-xl"]').filter({ hasText: 'Timeline' }).count() > 0;
    addResult('Styling', '4.3 Border radius 12px (rounded-xl)', roundedXl ? 'PASS' : 'FAIL');

    // 4.4 Hover states
    const entryClasses = await page.locator('button[data-session-id]').first().getAttribute('class') || '';
    const hasHover = entryClasses.includes('hover:');
    const hasTransition = entryClasses.includes('transition');
    addResult('Styling', '4.4 Hover classes defined', hasHover ? 'PASS' : 'FAIL');
    addResult('Styling', '4.4a Transitions defined', hasTransition ? 'PASS' : 'FAIL');

  } catch (error) {
    console.log(`\n[ERROR] Test failed: ${error.message}`);
  } finally {
    await browser.close();
  }

  // Print summary
  console.log('\n' + '='.repeat(70));
  console.log('SUMMARY');
  console.log('='.repeat(70));

  const passed = results.filter(r => r.status === 'PASS').length;
  const failed = results.filter(r => r.status === 'FAIL').length;
  const skipped = results.filter(r => r.status === 'SKIP').length;

  console.log(`  Total Tests: ${results.length}`);
  console.log(`  Passed:      ${passed}`);
  console.log(`  Failed:      ${failed}`);
  console.log(`  Skipped:     ${skipped}`);
  console.log(`  Pass Rate:   ${((passed / (results.length - skipped)) * 100).toFixed(1)}%`);
  console.log('='.repeat(70));

  // Print failed tests
  const failedTests = results.filter(r => r.status === 'FAIL');
  if (failedTests.length > 0) {
    console.log('\nFailed Tests:');
    failedTests.forEach(t => console.log(`  - ${t.name}: ${t.details}`));
  }
}

runTests().catch(console.error);
