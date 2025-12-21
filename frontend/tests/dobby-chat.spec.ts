import { test, expect } from '@playwright/test';

/**
 * Dobby AI Chat - Fullscreen Interface Tests
 *
 * Tests for the fullscreen chat interface including:
 * - Opening/closing fullscreen mode
 * - Sidebar expand/collapse
 * - Share modal functionality
 * - Chat input and messaging
 * - Mode toggle (AI/Therapist)
 * - Dark/light mode support
 */

test.describe('Dobby Chat - Fullscreen Interface', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForLoadState('networkidle');
  });

  test.describe('Fullscreen Open/Close', () => {
    test('should open fullscreen chat when clicking expand button', async ({ page }) => {
      // Find the AI Chat card expand button
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expect(expandBtn).toBeVisible();
      await expandBtn.click();

      // Wait for fullscreen chat to appear
      await page.waitForTimeout(300);

      // Check that fullscreen container is visible
      const fullscreenChat = page.locator('.fixed.inset-0.z-\\[2000\\]');
      await expect(fullscreenChat).toBeVisible();

      // Take screenshot for visual verification
      await page.screenshot({ path: 'test-results/dobby-fullscreen-open.png', fullPage: true });
    });

    test('should allow typing in compact card without opening fullscreen', async ({ page }) => {
      // Find the input field in compact card and type
      const inputField = page.locator('input[placeholder="Ask Dobby anything..."]');
      await inputField.fill('Hello Dobby');

      // Verify input has text and fullscreen is NOT open
      await expect(inputField).toHaveValue('Hello Dobby');
      const fullscreenChat = page.locator('.fixed.inset-0.z-\\[2000\\]');
      await expect(fullscreenChat).not.toBeVisible();
    });

    test('should send message in compact card and show response', async ({ page }) => {
      // Type and send message in compact card
      const inputField = page.locator('input[placeholder="Ask Dobby anything..."]');
      await inputField.fill('Hello');

      const sendBtn = page.locator('[aria-label="Send message"]').first();
      await sendBtn.click();

      // Wait for response
      await page.waitForTimeout(1000);

      // Check that message appears in compact card (messages area visible)
      const userMessage = page.locator('text=Hello').first();
      await expect(userMessage).toBeVisible();
    });

    test('should close fullscreen chat when clicking X button', async ({ page }) => {
      // Open fullscreen first
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Find and click close button
      const closeBtn = page.locator('[aria-label="Close chat"]');
      await expect(closeBtn).toBeVisible();
      await closeBtn.click();

      await page.waitForTimeout(300);

      // Verify fullscreen is closed
      const fullscreenChat = page.locator('.fixed.inset-0.z-\\[2000\\]');
      await expect(fullscreenChat).not.toBeVisible();
    });

    test('should close fullscreen chat when pressing Escape key', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Press Escape
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);

      // Verify closed
      const fullscreenChat = page.locator('.fixed.inset-0.z-\\[2000\\]');
      await expect(fullscreenChat).not.toBeVisible();
    });
  });

  test.describe('Sidebar Functionality', () => {
    test('sidebar should start collapsed', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Check sidebar width (collapsed = 60px)
      const sidebar = page.locator('.w-\\[60px\\]').first();
      await expect(sidebar).toBeVisible();

      await page.screenshot({ path: 'test-results/dobby-sidebar-collapsed.png', fullPage: true });
    });

    test('sidebar should expand when clicking toggle button', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Find and click sidebar toggle
      const sidebarToggle = page.locator('button').filter({ has: page.locator('svg rect[x="3"][y="3"]') }).first();
      await sidebarToggle.click();
      await page.waitForTimeout(300);

      // Check for expanded sidebar (260px)
      const expandedSidebar = page.locator('.w-\\[260px\\]').first();
      await expect(expandedSidebar).toBeVisible();

      // Verify "Dobby" brand text is visible when expanded
      const brandText = page.locator('text=Dobby').first();
      await expect(brandText).toBeVisible();

      await page.screenshot({ path: 'test-results/dobby-sidebar-expanded.png', fullPage: true });
    });

    test('sidebar should show tooltips when collapsed and hovering', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Hover over new chat button
      const newChatBtn = page.locator('svg').filter({ has: page.locator('line[x1="12"][y1="5"]') }).first();
      await newChatBtn.hover();
      await page.waitForTimeout(200);

      // Check for tooltip text
      const tooltip = page.locator('text=New chat').first();
      await expect(tooltip).toBeVisible();
    });

    test('new chat button should clear conversation', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Expand sidebar to access new chat button easily
      const sidebarToggle = page.locator('button').filter({ has: page.locator('svg rect[x="3"][y="3"]') }).first();
      await sidebarToggle.click();
      await page.waitForTimeout(300);

      // Click new chat
      const newChatBtn = page.locator('text=New chat').first();
      await newChatBtn.click();

      // Verify chat is reset (welcome message visible)
      const welcomeMsg = page.locator('text=Welcome back').first();
      await expect(welcomeMsg).toBeVisible();
    });
  });

  test.describe('Share Modal', () => {
    test('should open share modal when clicking share button', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Find and click share button
      const shareBtn = page.locator('[aria-label="Share chat"]');
      await expect(shareBtn).toBeVisible();
      await shareBtn.click();
      await page.waitForTimeout(300);

      // Check share modal is visible
      const shareModal = page.locator('h2:has-text("Share chat")');
      await expect(shareModal).toBeVisible();

      await page.screenshot({ path: 'test-results/dobby-share-modal.png', fullPage: true });
    });

    test('share modal should have Private and Public options', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Open share modal
      const shareBtn = page.locator('[aria-label="Share chat"]');
      await shareBtn.click();
      await page.waitForTimeout(300);

      // Check for options
      const privateOption = page.locator('text=Private').first();
      const publicOption = page.locator('text=Public access').first();

      await expect(privateOption).toBeVisible();
      await expect(publicOption).toBeVisible();
    });

    test('share modal should close when clicking X button', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Open share modal
      const shareBtn = page.locator('[aria-label="Share chat"]');
      await shareBtn.click();
      await page.waitForTimeout(300);

      // Close modal (X button in modal)
      const closeBtn = page.locator('.fixed.inset-0.z-\\[3000\\] button').filter({ has: page.locator('svg line') }).first();
      await closeBtn.click();
      await page.waitForTimeout(300);

      // Verify modal is closed
      const shareModalTitle = page.locator('h2:has-text("Share chat")');
      await expect(shareModalTitle).not.toBeVisible();
    });

    test('share modal should close when clicking backdrop', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Open share modal
      const shareBtn = page.locator('[aria-label="Share chat"]');
      await shareBtn.click();
      await page.waitForTimeout(300);

      // Click backdrop (outside modal content)
      const backdrop = page.locator('.fixed.inset-0.z-\\[3000\\]');
      await backdrop.click({ position: { x: 50, y: 50 } });
      await page.waitForTimeout(300);

      // Verify modal is closed
      const shareModalTitle = page.locator('h2:has-text("Share chat")');
      await expect(shareModalTitle).not.toBeVisible();
    });

    test('share modal should close when pressing Escape', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Open share modal
      const shareBtn = page.locator('[aria-label="Share chat"]');
      await shareBtn.click();
      await page.waitForTimeout(300);

      // Press Escape
      await page.keyboard.press('Escape');
      await page.waitForTimeout(300);

      // Verify modal is closed
      const shareModalTitle = page.locator('h2:has-text("Share chat")');
      await expect(shareModalTitle).not.toBeVisible();
    });

    test('create share link button should show confirmation', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Open share modal
      const shareBtn = page.locator('[aria-label="Share chat"]');
      await shareBtn.click();
      await page.waitForTimeout(300);

      // Click create link button
      const createLinkBtn = page.locator('button:has-text("Create share link")');
      await createLinkBtn.click();

      // Check for confirmation message
      const confirmationMsg = page.locator('text=Link copied!');
      await expect(confirmationMsg).toBeVisible();
    });
  });

  test.describe('Chat Input and Mode Toggle', () => {
    test('should have chat input visible in fullscreen', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Check for input field (placeholder varies by mode)
      const chatInput = page.locator('textarea[placeholder*="Ask Dobby"]');
      await expect(chatInput).toBeVisible();
    });

    test('mode toggle should switch between AI and Therapist modes', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Check AI mode button is visible (the small toggle button, not the prompt button)
      const aiButton = page.locator('button').filter({ hasText: /^AI$/ }).first();
      await expect(aiButton).toBeVisible();

      // Click Therapist mode (exact match for the toggle button)
      const therapistButton = page.locator('button').filter({ hasText: /^THERAPIST$/ }).first();
      await therapistButton.click();

      // Verify mode toggle works (input placeholder changes)
      await page.waitForTimeout(100);
      const chatInput = page.locator('textarea[placeholder*="therapist"]');
      await expect(chatInput).toBeVisible();

      await page.screenshot({ path: 'test-results/dobby-therapist-mode.png', fullPage: true });
    });

    test('send button should be disabled when input is empty', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Find send button
      const sendBtn = page.locator('[aria-label="Send message"]');
      await expect(sendBtn).toBeDisabled();
    });

    test('send button should be enabled when input has text', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Type in chat input
      const chatInput = page.locator('textarea[placeholder*="Ask Dobby"]');
      await chatInput.fill('Hello Dobby!');

      // Check send button is enabled
      const sendBtn = page.locator('[aria-label="Send message"]');
      await expect(sendBtn).not.toBeDisabled();
    });

    test('should display user message after sending', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Type and send message
      const chatInput = page.locator('textarea[placeholder*="Ask Dobby"]');
      await chatInput.fill('Hello Dobby, this is a test message!');

      const sendBtn = page.locator('[aria-label="Send message"]');
      await sendBtn.click();

      // Wait for message to appear
      await page.waitForTimeout(500);

      // Check user message is displayed
      const userMessage = page.locator('text=Hello Dobby, this is a test message!');
      await expect(userMessage).toBeVisible();

      await page.screenshot({ path: 'test-results/dobby-user-message.png', fullPage: true });
    });
  });

  test.describe('Welcome View', () => {
    test('should display Dobby logo and welcome message', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Check for welcome message
      const welcomeMsg = page.locator('h1:has-text("Welcome back")');
      await expect(welcomeMsg).toBeVisible();
    });

    test('should display Dobby intro message', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Check for Dobby intro bubble
      const introBubble = page.locator('text=I\'m Dobby, your AI therapy companion');
      await expect(introBubble).toBeVisible();
    });

    test('should display suggested prompts', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Check for suggested prompts (should see at least one)
      const suggestedPrompts = page.locator('button').filter({ hasText: /Why does my mood|Help me prep|Explain the TIPP/ });
      const count = await suggestedPrompts.count();
      expect(count).toBeGreaterThan(0);
    });

    test('clicking suggested prompt should send message', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Click a suggested prompt
      const promptBtn = page.locator('button:has-text("Why does my mood drop after family visits?")');
      await promptBtn.click();

      // Wait for message to be sent
      await page.waitForTimeout(500);

      // Check user message appears (prompt auto-sends)
      const userMessage = page.locator('text=Why does my mood drop after family visits?').last();
      await expect(userMessage).toBeVisible();
    });
  });

  test.describe('Header and Branding', () => {
    test('should display Dobby branding in header', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Check for Dobby text in header
      const dobbyBrand = page.locator('span:has-text("DOBBY")').first();
      await expect(dobbyBrand).toBeVisible();
    });

    test('should display share button in header', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Find share button
      const shareBtn = page.locator('[aria-label="Share chat"]');
      await expect(shareBtn).toBeVisible();
    });

    test('share button should show tooltip on hover', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Hover over share button
      const shareBtn = page.locator('[aria-label="Share chat"]');
      await shareBtn.hover();
      await page.waitForTimeout(200);

      // Check for tooltip (Share text appears on hover)
      const tooltip = page.locator('span:has-text("Share")').first();
      await expect(tooltip).toBeVisible();
    });
  });

  test.describe('Loading States', () => {
    test('should show loading indicator when sending message', async ({ page }) => {
      // Open fullscreen
      const expandBtn = page.locator('[aria-label="Expand chat"]');
      await expandBtn.click();
      await page.waitForTimeout(300);

      // Type and send message
      const chatInput = page.locator('textarea[placeholder*="Ask Dobby"]');
      await chatInput.fill('Hello Dobby!');

      const sendBtn = page.locator('[aria-label="Send message"]');
      await sendBtn.click();

      // Check for loading state (bouncing dots)
      await page.waitForTimeout(100);

      // Take screenshot to verify loading state
      await page.screenshot({ path: 'test-results/dobby-loading-state.png', fullPage: true });
    });
  });
});

test.describe('Dobby Chat - Compact Card', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForLoadState('networkidle');
  });

  test('compact card should display Dobby logo with glow effect', async ({ page }) => {
    // Check for Dobby logo SVG (the geometric shape)
    const dobbyLogo = page.locator('svg').filter({ has: page.locator('polygon[points="15,55 35,35 35,65"]') }).first();
    await expect(dobbyLogo).toBeVisible();

    await page.screenshot({ path: 'test-results/dobby-compact-logo.png', fullPage: true });
  });

  test('compact card should have input field', async ({ page }) => {
    // Check for input with placeholder
    const inputField = page.locator('input[placeholder="Ask Dobby anything..."]');
    await expect(inputField).toBeVisible();
  });

  test('compact card should have fullscreen expand button', async ({ page }) => {
    // Check for expand button
    const expandBtn = page.locator('[aria-label="Expand chat"]');
    await expect(expandBtn).toBeVisible();
  });

  test('compact card should have mode toggle with AI and THERAPIST buttons', async ({ page }) => {
    // Check for AI button (text only, no emoji in new design)
    const aiButton = page.locator('button:has-text("AI")').first();
    const therapistButton = page.locator('button:has-text("THERAPIST")').first();

    await expect(aiButton).toBeVisible();
    await expect(therapistButton).toBeVisible();
  });

  test('therapist mode should show coral gradient when active', async ({ page }) => {
    // Click therapist button
    const therapistButton = page.locator('button:has-text("THERAPIST")').first();
    await therapistButton.click();

    // Wait for state update
    await page.waitForTimeout(100);

    // Take screenshot to verify coral gradient
    await page.screenshot({ path: 'test-results/dobby-therapist-coral.png', fullPage: true });
  });

  test('compact card should have character count display', async ({ page }) => {
    // Check for char count (0/500)
    const charCount = page.locator('text=/\\d+\\/500/');
    await expect(charCount).toBeVisible();
  });

  test('compact card should have send button', async ({ page }) => {
    // Check for send button (aria-label changed from "Open chat" to "Send message")
    const sendBtn = page.locator('[aria-label="Send message"]').first();
    await expect(sendBtn).toBeVisible();
  });
});
