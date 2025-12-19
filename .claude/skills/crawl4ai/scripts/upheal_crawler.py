#!/usr/bin/env python3
"""
Upheal.io Authenticated Crawler
Crawls app.upheal.io after logging in with credentials from .env file
"""

import asyncio
import json
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Load credentials from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

UPHEAL_EMAIL = os.getenv("UPHEAL_EMAIL")
UPHEAL_PASSWORD = os.getenv("UPHEAL_PASSWORD")

if not UPHEAL_EMAIL or not UPHEAL_PASSWORD:
    print("❌ Error: UPHEAL_EMAIL and UPHEAL_PASSWORD must be set in .env file")
    exit(1)


async def crawl_upheal():
    """Crawl Upheal.io with authentication"""

    # Browser config - use headless for production, headless=False for debugging
    browser_config = BrowserConfig(
        headless=False,  # Set to False to see what's happening
        viewport_width=1920,
        viewport_height=1080,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        print("🔐 Step 1: Logging in to Upheal...")

        # Step 1: Navigate to login page and perform login
        login_config = CrawlerRunConfig(
            session_id="upheal_session",
            # Wait for page to load
            page_timeout=60000,  # 60 seconds
            # Execute login JavaScript
            js_code=f"""
            // Wait for page to be ready
            await new Promise(resolve => setTimeout(resolve, 2000));

            // Find and fill email field
            const emailInput = document.querySelector('input[type="email"]') ||
                              document.querySelector('input[name="email"]') ||
                              document.querySelector('#email');
            if (emailInput) {{
                emailInput.value = '{UPHEAL_EMAIL}';
                emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                emailInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}

            // Wait a bit
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Find and fill password field
            const passwordInput = document.querySelector('input[type="password"]') ||
                                 document.querySelector('input[name="password"]') ||
                                 document.querySelector('#password');
            if (passwordInput) {{
                passwordInput.value = '{UPHEAL_PASSWORD}';
                passwordInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                passwordInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}

            // Wait a bit
            await new Promise(resolve => setTimeout(resolve, 1000));

            // Find and click login button
            const loginButton = document.querySelector('button[type="submit"]') ||
                              document.querySelector('button:contains("Sign in")') ||
                              document.querySelector('button:contains("Log in")') ||
                              document.querySelector('.login-button');
            if (loginButton) {{
                loginButton.click();
            }}

            // Wait for navigation
            await new Promise(resolve => setTimeout(resolve, 5000));
            """,
            # Wait for post-login element (adjust selector based on actual Upheal UI)
            wait_for="css:body",  # Generic wait, adjust after seeing the page
            screenshot=True,
        )

        login_result = await crawler.arun(
            url="https://app.upheal.io/login",
            config=login_config
        )

        if login_result.success:
            print(f"✅ Login page loaded: {login_result.url}")
            print(f"   Page title: {login_result.metadata.get('title', 'N/A')}")

            # Save login screenshot
            if login_result.screenshot:
                screenshot_path = "upheal_login.png"
                screenshot_data = login_result.screenshot
                # Handle both base64 string and bytes
                if isinstance(screenshot_data, str):
                    screenshot_data = base64.b64decode(screenshot_data)
                with open(screenshot_path, "wb") as f:
                    f.write(screenshot_data)
                print(f"📸 Login screenshot saved to {screenshot_path}")
        else:
            print(f"❌ Login failed: {login_result.error_message}")
            return

        # Wait a bit for login to complete
        await asyncio.sleep(3)

        print("\n📊 Step 2: Crawling dashboard...")

        # Step 2: Crawl the dashboard (reusing the session)
        dashboard_config = CrawlerRunConfig(
            session_id="upheal_session",  # Reuse the logged-in session
            page_timeout=60000,
            screenshot=True,
            # Wait for content to load
            wait_for="css:body",
            # Scroll to load dynamic content
            js_code="""
            window.scrollTo(0, document.body.scrollHeight / 2);
            await new Promise(resolve => setTimeout(resolve, 2000));
            window.scrollTo(0, document.body.scrollHeight);
            await new Promise(resolve => setTimeout(resolve, 2000));
            """,
        )

        dashboard_result = await crawler.arun(
            url="https://app.upheal.io/dashboard",
            config=dashboard_config
        )

        if dashboard_result.success:
            print(f"✅ Dashboard loaded: {dashboard_result.url}")
            print(f"   Page title: {dashboard_result.metadata.get('title', 'N/A')}")
            print(f"   Content length: {len(dashboard_result.markdown)} chars")
            print(f"   Links found: {len(dashboard_result.links.get('internal', []))} internal, {len(dashboard_result.links.get('external', []))} external")

            # Save dashboard content
            with open("upheal_dashboard.md", "w") as f:
                f.write(dashboard_result.markdown)
            print(f"💾 Dashboard content saved to upheal_dashboard.md")

            # Save dashboard screenshot
            if dashboard_result.screenshot:
                screenshot_data = dashboard_result.screenshot
                if isinstance(screenshot_data, str):
                    screenshot_data = base64.b64decode(screenshot_data)
                with open("upheal_dashboard.png", "wb") as f:
                    f.write(screenshot_data)
                print(f"📸 Dashboard screenshot saved to upheal_dashboard.png")

            # Save links for further exploration
            links_data = {
                "internal_links": dashboard_result.links.get("internal", []),
                "external_links": dashboard_result.links.get("external", []),
            }
            with open("upheal_links.json", "w") as f:
                json.dump(links_data, f, indent=2)
            print(f"🔗 Links saved to upheal_links.json")

        else:
            print(f"❌ Dashboard crawl failed: {dashboard_result.error_message}")
            return

        print("\n🔍 Step 3: Exploring discovered pages...")

        # Step 3: Crawl some interesting pages (if any were discovered)
        internal_links = dashboard_result.links.get("internal", [])

        # Filter for interesting paths (sessions, patients, notes, etc.)
        interesting_paths = [
            link for link in internal_links
            if any(keyword in link.lower() for keyword in
                   ['session', 'patient', 'note', 'calendar', 'settings', 'profile'])
        ][:5]  # Limit to 5 pages

        if interesting_paths:
            print(f"   Found {len(interesting_paths)} interesting pages to crawl...")

            for i, url in enumerate(interesting_paths, 1):
                print(f"\n   [{i}/{len(interesting_paths)}] Crawling: {url}")

                page_config = CrawlerRunConfig(
                    session_id="upheal_session",
                    page_timeout=30000,
                    screenshot=True,
                )

                page_result = await crawler.arun(url=url, config=page_config)

                if page_result.success:
                    # Generate filename from URL
                    filename = url.split("/")[-1] or "index"
                    filename = "".join(c if c.isalnum() or c in "._-" else "_" for c in filename)

                    # Save content
                    with open(f"upheal_{filename}.md", "w") as f:
                        f.write(page_result.markdown)
                    print(f"   ✅ Saved: upheal_{filename}.md ({len(page_result.markdown)} chars)")
                else:
                    print(f"   ❌ Failed to crawl: {url}")

                # Be polite, wait between requests
                await asyncio.sleep(2)
        else:
            print("   No additional interesting pages found")

        print("\n✅ Upheal crawl complete!")
        print("\n📁 Files created:")
        print("   - upheal_login.png (login screenshot)")
        print("   - upheal_dashboard.md (dashboard content)")
        print("   - upheal_dashboard.png (dashboard screenshot)")
        print("   - upheal_links.json (all discovered links)")
        if interesting_paths:
            print(f"   - upheal_*.md (content from {len(interesting_paths)} additional pages)")


if __name__ == "__main__":
    print("🚀 Upheal.io Crawler")
    print(f"📧 Using email: {UPHEAL_EMAIL}")
    print("="*60)
    asyncio.run(crawl_upheal())
