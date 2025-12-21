import { test, expect } from '@playwright/test';

/**
 * Card Styling Investigation Tests
 *
 * Examines font families, weights, and text fitting across all dashboard cards.
 */

test.describe('Dashboard Card Styling', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/patient/dashboard-v3');
    await page.waitForLoadState('networkidle');
  });

  test('Examine compact card title fonts', async ({ page }) => {
    // Get font styles for each card title

    // Notes/Goals card
    const notesTitle = page.locator('text=Notes / Goals').first();
    const notesFontStyles = await notesTitle.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        fontFamily: styles.fontFamily,
        fontWeight: styles.fontWeight,
        fontSize: styles.fontSize,
        fontStyle: styles.fontStyle,
      };
    });
    console.log('Notes/Goals title font:', notesFontStyles);

    // To-Do card
    const todoTitle = page.locator('h2:has-text("To-Do")').first();
    const todoFontStyles = await todoTitle.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        fontFamily: styles.fontFamily,
        fontWeight: styles.fontWeight,
        fontSize: styles.fontSize,
        fontStyle: styles.fontStyle,
      };
    });
    console.log('To-Do title font:', todoFontStyles);

    // Progress Patterns (Mood Trend) card
    const progressTitle = page.locator('text=Mood Trend').first();
    const progressFontStyles = await progressTitle.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        fontFamily: styles.fontFamily,
        fontWeight: styles.fontWeight,
        fontSize: styles.fontSize,
        fontStyle: styles.fontStyle,
      };
    });
    console.log('Progress Patterns title font:', progressFontStyles);

    // Therapist Bridge card (reference - the desired font)
    const bridgeTitle = page.locator('text=Therapist Bridge').first();
    const bridgeFontStyles = await bridgeTitle.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        fontFamily: styles.fontFamily,
        fontWeight: styles.fontWeight,
        fontSize: styles.fontSize,
        fontStyle: styles.fontStyle,
      };
    });
    console.log('Therapist Bridge title font (TARGET):', bridgeFontStyles);
  });

  test('Examine expanded modal title fonts', async ({ page }) => {
    // Open Notes/Goals modal and check fonts
    await page.locator('text=Notes / Goals').first().click();
    await page.waitForTimeout(500);

    const notesModalTitle = page.locator('[role="dialog"] h2').first();
    const notesModalFontStyles = await notesModalTitle.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        fontFamily: styles.fontFamily,
        fontWeight: styles.fontWeight,
        fontSize: styles.fontSize,
      };
    });
    console.log('Notes/Goals MODAL title font:', notesModalFontStyles);

    // Close and open To-Do modal
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    await page.locator('h2:has-text("To-Do")').first().click();
    await page.waitForTimeout(500);

    const todoModalTitle = page.locator('[role="dialog"] h2').first();
    const todoModalFontStyles = await todoModalTitle.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        fontFamily: styles.fontFamily,
        fontWeight: styles.fontWeight,
        fontSize: styles.fontSize,
      };
    });
    console.log('To-Do MODAL title font:', todoModalFontStyles);

    // Close and open Therapist Bridge modal
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);

    await page.locator('text=Therapist Bridge').first().click();
    await page.waitForTimeout(500);

    const bridgeModalTitle = page.locator('[role="dialog"] h2').first();
    const bridgeModalFontStyles = await bridgeModalTitle.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      return {
        fontFamily: styles.fontFamily,
        fontWeight: styles.fontWeight,
        fontSize: styles.fontSize,
      };
    });
    console.log('Therapist Bridge MODAL title font (TARGET):', bridgeModalFontStyles);
  });

  test('Examine session cards text fitting', async ({ page }) => {
    // Take screenshots of session cards
    await page.screenshot({ path: 'test-results/session-cards-overview.png', fullPage: true });

    // Find all session cards and get their text content and dimensions
    const sessionCards = page.locator('[id^="session-"]');
    const count = await sessionCards.count();
    console.log('Number of session cards:', count);

    // Examine the December 17 card specifically
    const dec17Card = page.locator('[id="session-s10"]').first();
    if (await dec17Card.count() > 0) {
      const cardBox = await dec17Card.boundingBox();
      console.log('Dec 17 card dimensions:', cardBox);

      // Get all text elements inside the card
      const textElements = await dec17Card.evaluate((card) => {
        const texts: Array<{text: string, overflow: boolean, width: number, scrollWidth: number}> = [];
        const allText = card.querySelectorAll('p, span, h3, h4');
        allText.forEach((el) => {
          const htmlEl = el as HTMLElement;
          texts.push({
            text: htmlEl.innerText?.substring(0, 50) || '',
            overflow: htmlEl.scrollWidth > htmlEl.clientWidth,
            width: htmlEl.clientWidth,
            scrollWidth: htmlEl.scrollWidth,
          });
        });
        return texts;
      });
      console.log('Dec 17 card text elements:', textElements);

      // Screenshot the specific card
      await dec17Card.screenshot({ path: 'test-results/dec17-card.png' });
    }

    // Check first few session cards for consistency
    for (let i = 0; i < Math.min(4, count); i++) {
      const card = sessionCards.nth(i);
      const id = await card.getAttribute('id');
      const box = await card.boundingBox();
      console.log(`Card ${id} dimensions:`, box);
    }
  });

  test('Get body text fonts for comparison', async ({ page }) => {
    // Check body text fonts in each card type

    // Notes/Goals body text
    const notesBody = page.locator('.bg-gradient-to-br.from-white.to-\\[\\#FFF9F5\\] p').first();
    if (await notesBody.count() > 0) {
      const notesFontStyles = await notesBody.evaluate((el) => {
        const styles = window.getComputedStyle(el);
        return {
          fontFamily: styles.fontFamily,
          fontWeight: styles.fontWeight,
          fontSize: styles.fontSize,
        };
      });
      console.log('Notes/Goals body font:', notesFontStyles);
    }

    // To-Do body text
    const todoBody = page.locator('.rounded-lg.border.border-gray-200 span').first();
    if (await todoBody.count() > 0) {
      const todoFontStyles = await todoBody.evaluate((el) => {
        const styles = window.getComputedStyle(el);
        return {
          fontFamily: styles.fontFamily,
          fontWeight: styles.fontWeight,
          fontSize: styles.fontSize,
        };
      });
      console.log('To-Do body font:', todoFontStyles);
    }

    // Therapist Bridge body text
    const bridgeBody = page.locator('.bg-gradient-to-br.from-\\[\\#FFF5F0\\] li span').first();
    if (await bridgeBody.count() > 0) {
      const bridgeFontStyles = await bridgeBody.evaluate((el) => {
        const styles = window.getComputedStyle(el);
        return {
          fontFamily: styles.fontFamily,
          fontWeight: styles.fontWeight,
          fontSize: styles.fontSize,
        };
      });
      console.log('Therapist Bridge body font (TARGET):', bridgeFontStyles);
    }
  });
});
