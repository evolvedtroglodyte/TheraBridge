#!/usr/bin/env python3
"""
Upheal.io Authenticated Crawler V2
Uses Playwright hooks for reliable form filling and login
"""

import asyncio
import json
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

# Load credentials from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

UPHEAL_EMAIL = os.getenv("UPHEAL_EMAIL")
UPHEAL_PASSWORD = os.getenv("UPHEAL_PASSWORD")

if not UPHEAL_EMAIL or not UPHEAL_PASSWORD:
    print("❌ Error: UPHEAL_EMAIL and UPHEAL_PASSWORD must be set in .env file")
    exit(1)


async def login_hook(page, context):
    """Hook that runs after page load to perform login"""
    print("   🔑 Filling in login form...")

    # Wait for the email input to be visible
    await page.wait_for_selector('input[placeholder="Email"]', timeout=10000)

    # Fill email field
    await page.fill('input[placeholder="Email"]', UPHEAL_EMAIL)
    print(f"   ✓ Email filled: {UPHEAL_EMAIL}")

    # Fill password field
    await page.fill('input[placeholder="Password"]', UPHEAL_PASSWORD)
    print("   ✓ Password filled")

    # Wait a moment for form validation
    await asyncio.sleep(1)

    # Click the login button
    await page.click('button:has-text("Log in")')
    print("   ✓ Login button clicked")

    # Wait for navigation after login (wait for dashboard or any post-login element)
    try:
        # Wait for either successful login or error message
        await page.wait_for_load_state('networkidle', timeout=10000)
        await asyncio.sleep(2)
        print("   ✓ Login submitted, waiting for response...")
    except Exception as e:
        print(f"   ⚠ Navigation wait: {e}")


async def crawl_upheal():
    """Crawl Upheal.io with authentication using hooks"""

    browser_config = BrowserConfig(
        headless=False,  # Keep visible to debug
        viewport_width=1920,
        viewport_height=1080,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("🔐 Step 1: Logging in to Upheal...")

        # Configure login with hook
        login_config = CrawlerRunConfig(
            session_id="upheal_session",
            page_timeout=60000,
            screenshot=True,
            # Use hooks for reliable form interaction
            hooks={
                'on_page_loaded': login_hook
            },
            # Wait for post-login navigation
            wait_for="css:body",
        )

        login_result = await crawler.arun(
            url="https://app.upheal.io/login",
            config=login_config
        )

        if login_result.success:
            print(f"✅ Page loaded: {login_result.url}")
            print(f"   Title: {login_result.metadata.get('title', 'N/A')}")

            # Save screenshot
            if login_result.screenshot:
                screenshot_data = login_result.screenshot
                if isinstance(screenshot_data, str):
                    screenshot_data = base64.b64decode(screenshot_data)
                with open("upheal_after_login.png", "wb") as f:
                    f.write(screenshot_data)
                print(f"📸 Screenshot saved to upheal_after_login.png")

            # Save content to check if we're logged in
            with open("upheal_after_login.md", "w") as f:
                f.write(login_result.markdown)
            print(f"💾 Content saved to upheal_after_login.md")

            # Check if we successfully logged in by looking at content
            if "Welcome back" in login_result.markdown and "Don't have an account" in login_result.markdown:
                print("⚠️  Still on login page - login may have failed")
                print("   Check upheal_after_login.png for details")
            else:
                print("✅ Appears to be logged in successfully!")
        else:
            print(f"❌ Failed: {login_result.error_message}")
            return

        # Wait a bit for any post-login redirects
        await asyncio.sleep(3)

        print("\n📊 Step 2: Exploring the application...")

        # Try various common URLs
        urls_to_crawl = [
            "https://app.upheal.io/",
            "https://app.upheal.io/dashboard",
            "https://app.upheal.io/sessions",
            "https://app.upheal.io/patients",
            "https://app.upheal.io/calendar",
            "https://app.upheal.io/notes",
        ]

        for url in urls_to_crawl:
            print(f"\n   Trying: {url}")

            page_config = CrawlerRunConfig(
                session_id="upheal_session",  # Reuse session
                page_timeout=30000,
                screenshot=True,
            )

            result = await crawler.arun(url=url, config=page_config)

            if result.success:
                filename_base = url.split("/")[-1] or "home"
                filename_base = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename_base)

                # Save content
                md_file = f"upheal_{filename_base}.md"
                with open(md_file, "w") as f:
                    f.write(result.markdown)

                # Save screenshot
                if result.screenshot:
                    screenshot_data = result.screenshot
                    if isinstance(screenshot_data, str):
                        screenshot_data = base64.b64decode(screenshot_data)
                    png_file = f"upheal_{filename_base}.png"
                    with open(png_file, "wb") as f:
                        f.write(screenshot_data)
                    print(f"   ✅ {result.url}")
                    print(f"      Content: {len(result.markdown)} chars → {md_file}")
                    print(f"      Screenshot → {png_file}")

                    # Save links if any
                    internal_links = result.links.get("internal", [])
                    if internal_links:
                        links_file = f"upheal_{filename_base}_links.json"
                        with open(links_file, "w") as f:
                            json.dump(internal_links, f, indent=2)
                        print(f"      Links: {len(internal_links)} → {links_file}")
            else:
                print(f"   ❌ Failed: {result.error_message}")

            # Be polite
            await asyncio.sleep(2)

        print("\n✅ Upheal exploration complete!")


if __name__ == "__main__":
    print("🚀 Upheal.io Crawler V2 (with hooks)")
    print(f"📧 Using email: {UPHEAL_EMAIL}")
    print("="*60)
    asyncio.run(crawl_upheal())
