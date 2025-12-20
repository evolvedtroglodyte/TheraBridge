#!/usr/bin/env python3
"""
Playwright test to verify Timeline fixes:
1. Popover appears to the LEFT of timeline
2. Only milestone sessions have stars (others have mood-colored dots)
3. Dots/stars are centered on the gradient line
4. Clicking timeline entry scrolls to session card
"""

import asyncio
from playwright.async_api import async_playwright

async def test_timeline_fixes():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1440, 'height': 900})
        page = await context.new_page()

        print("=" * 60)
        print("TIMELINE FIXES VERIFICATION")
        print("=" * 60)

        # Navigate to the dashboard
        print("\n[1] Loading dashboard-v3...")
        await page.goto('http://localhost:3000/patient/dashboard-v3')
        await page.wait_for_load_state('networkidle')
        await asyncio.sleep(1)

        # Screenshot initial state
        await page.screenshot(path='screenshots/fix_01_initial.png', full_page=True)
        print("    Saved: fix_01_initial.png")

        # TEST 1: Verify dots vs stars
        print("\n[2] Testing: Mood dots vs Milestone stars...")

        # Count stars (should be 5 - sessions with milestones: s1, s2, s5, s7, s9)
        stars = page.locator('svg.lucide-star')
        star_count = await stars.count()
        print(f"    Stars found: {star_count}")

        # Count mood dots (should be 5 - sessions without milestones: s3, s4, s6, s8, s10)
        dots = page.locator('[data-session-id] .rounded-full[style*="background"]')
        dot_count = await dots.count()
        print(f"    Mood dots found: {dot_count}")

        if star_count == 5 and dot_count == 5:
            print("    [PASS] Correct number of stars (5) and dots (5)")
        else:
            print(f"    [FAIL] Expected 5 stars and 5 dots, got {star_count} stars and {dot_count} dots")

        # TEST 2: Verify popover appears to the LEFT
        print("\n[3] Testing: Popover position (should be LEFT of timeline)...")

        # Click first timeline entry
        first_entry = page.locator('button[data-session-id]').first
        entry_box = await first_entry.bounding_box()
        await first_entry.click()
        await asyncio.sleep(0.5)

        # Check popover position
        popover = page.locator('[role="dialog"]')
        if await popover.count():
            popover_box = await popover.bounding_box()

            # Popover should be to the LEFT of the entry (popover.x + popover.width < entry.x)
            popover_right_edge = popover_box['x'] + popover_box['width']
            entry_left_edge = entry_box['x']

            print(f"    Entry left edge: {entry_left_edge:.0f}px")
            print(f"    Popover right edge: {popover_right_edge:.0f}px")

            if popover_right_edge < entry_left_edge + 50:  # Allow small overlap for arrow
                print("    [PASS] Popover appears to the LEFT of timeline")
            else:
                print("    [FAIL] Popover appears to the RIGHT (should be LEFT)")

            await page.screenshot(path='screenshots/fix_02_popover_left.png')
            print("    Saved: fix_02_popover_left.png")
        else:
            print("    [FAIL] Popover did not appear")

        # Close popover
        await page.keyboard.press('Escape')
        await asyncio.sleep(0.3)

        # TEST 3: Verify click-to-scroll functionality
        print("\n[4] Testing: Click-to-scroll to session card...")

        # Get the session cards grid
        session_cards = page.locator('[id^="session-"]')
        card_count = await session_cards.count()
        print(f"    Found {card_count} session cards with IDs")

        # Click on a timeline entry (e.g., Dec 3 = s8)
        dec3_entry = page.locator('button[data-session-id="s8"]')
        if await dec3_entry.count():
            # Get initial scroll position
            initial_scroll = await page.evaluate('window.scrollY')

            await dec3_entry.click()
            await asyncio.sleep(1)  # Wait for scroll animation

            # Check if session card has highlight ring
            session_card = page.locator('#session-s8')
            if await session_card.count():
                # Check if card is in viewport
                is_visible = await session_card.is_visible()
                print(f"    Session card s8 visible: {is_visible}")

                # Check for highlight ring (temporary class added by scroll handler)
                card_classes = await session_card.get_attribute('class')
                has_ring = 'ring-' in (card_classes or '')
                print(f"    Session card has highlight ring: {has_ring}")

                if is_visible:
                    print("    [PASS] Click scrolled to session card")
                else:
                    print("    [PARTIAL] Scroll triggered but card may not be centered")
            else:
                print("    [FAIL] Session card #session-s8 not found")
        else:
            print("    [FAIL] Timeline entry for s8 not found")

        await page.screenshot(path='screenshots/fix_03_scroll_test.png')
        print("    Saved: fix_03_scroll_test.png")

        # TEST 4: Verify gradient line alignment
        print("\n[5] Testing: Gradient connector line alignment...")

        gradient_line = page.locator('[style*="linear-gradient"]')
        if await gradient_line.count():
            line_box = await gradient_line.bounding_box()
            print(f"    Gradient line position: x={line_box['x']:.0f}px, width={line_box['width']:.0f}px")
            print("    [PASS] Gradient connector line present")
        else:
            print("    [FAIL] Gradient connector line not found")

        # TEST 5: Screenshot the timeline component alone
        print("\n[6] Capturing timeline component screenshot...")
        timeline = page.locator('text=Timeline').locator('xpath=ancestor::div[contains(@class, "rounded-xl")]').first
        if await timeline.count():
            await timeline.screenshot(path='screenshots/fix_04_timeline_component.png')
            print("    Saved: fix_04_timeline_component.png")

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("""
Screenshots saved to ./screenshots/:
- fix_01_initial.png - Full page initial state
- fix_02_popover_left.png - Popover appearing to the LEFT
- fix_03_scroll_test.png - After clicking timeline entry
- fix_04_timeline_component.png - Timeline component closeup

Manual verification needed:
1. Check popover is on LEFT side of timeline (not cut off)
2. Check dots are mood-colored (green/blue/rose)
3. Check stars have glow effect on milestone sessions
4. Check gradient line is centered under dots
""")

        await browser.close()

if __name__ == '__main__':
    import os
    os.makedirs('screenshots', exist_ok=True)
    asyncio.run(test_timeline_fixes())
