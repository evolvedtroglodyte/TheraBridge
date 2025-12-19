#!/usr/bin/env python3
"""
Upheal Authenticated Scraper

Uses crawl4ai session management to maintain login state across requests.
Designed for accessing protected Upheal content after authentication.

Authentication Engineer (Instance I2) - Wave 1
"""
import asyncio
import os
import sys
from pathlib import Path
from typing import Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

# Add parent path to import local modules if needed
sys.path.insert(0, str(Path(__file__).parent))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Base exception for authentication errors."""
    pass


class CredentialError(AuthError):
    """Invalid or missing credentials."""
    pass


class LoginTimeoutError(AuthError):
    """Login page took too long to respond."""
    pass


class LoginFailedError(AuthError):
    """Login attempt failed (wrong credentials, account locked, etc.)."""
    pass


class AuthStatus(Enum):
    """Authentication status enum."""
    SUCCESS = "success"
    INVALID_CREDENTIALS = "invalid_credentials"
    TIMEOUT = "timeout"
    NETWORK_ERROR = "network_error"
    ELEMENT_NOT_FOUND = "element_not_found"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class AuthResult:
    """Result of authentication attempt."""
    status: AuthStatus
    session_id: Optional[str] = None
    error_message: Optional[str] = None
    user_info: Optional[dict] = None


class UphealAuthenticatedScraper:
    """
    Authenticated scraper for Upheal using crawl4ai session management.

    Handles:
    - Reading credentials from .env
    - Login form automation via JavaScript
    - Session persistence across multiple requests
    - Graceful error handling

    Usage:
        scraper = UphealAuthenticatedScraper()
        result = await scraper.login()
        if result.status == AuthStatus.SUCCESS:
            data = await scraper.fetch_protected_page("/dashboard")
    """

    # Upheal URLs
    BASE_URL = "https://app.upheal.io"
    LOGIN_URL = f"{BASE_URL}/login"
    DASHBOARD_URL = f"{BASE_URL}/dashboard"
    SESSIONS_URL = f"{BASE_URL}/sessions"

    # Default session ID for consistent state
    DEFAULT_SESSION_ID = "upheal_auth_session"

    # Login form selectors (multiple options for resilience)
    # React/modern apps often use these patterns
    LOGIN_SELECTORS = {
        # Email/username field selectors (try in order)
        'email': [
            'input[type="email"]',
            'input[name="email"]',
            'input[id="email"]',
            'input[placeholder*="email" i]',
            'input[placeholder*="Email" i]',
            '#email',
            '[data-testid="email-input"]',
        ],
        # Password field selectors
        'password': [
            'input[type="password"]',
            'input[name="password"]',
            'input[id="password"]',
            '#password',
            '[data-testid="password-input"]',
        ],
        # Submit button selectors
        'submit': [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:contains("Log in")',
            'button:contains("Login")',
            'button:contains("Sign in")',
            '[data-testid="login-button"]',
            '.login-btn',
            '#login-submit',
        ],
        # Post-login success indicators
        'dashboard': [
            '.dashboard',
            '[class*="dashboard"]',
            '.home-container',
            '.main-content',
            'nav[class*="nav"]',
            '.sidebar',
            '[data-testid="dashboard"]',
            '.sessions-list',
            '[class*="session"]',
        ],
        # Error message indicators
        'error': [
            '.error-message',
            '.alert-danger',
            '[class*="error"]',
            '[role="alert"]',
            '.toast-error',
        ]
    }

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        session_id: Optional[str] = None,
        headless: bool = True,
        verbose: bool = False
    ):
        """
        Initialize the authenticated scraper.

        Args:
            credentials_path: Path to .env file with credentials.
                             Defaults to .claude/skills/crawl4ai/.env
            session_id: Custom session ID for browser persistence.
            headless: Run browser in headless mode (default True).
            verbose: Enable verbose logging.
        """
        self.session_id = session_id or self.DEFAULT_SESSION_ID
        self.headless = headless
        self.verbose = verbose
        self._is_authenticated = False
        self._crawler: Optional[AsyncWebCrawler] = None

        # Load credentials
        self.credentials = self._load_credentials(credentials_path)

        # Browser configuration for authentication
        self.browser_config = BrowserConfig(
            headless=self.headless,
            viewport_width=1920,
            viewport_height=1080,
            verbose=self.verbose,
            # Anti-detection measures
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

    def _load_credentials(self, credentials_path: Optional[str] = None) -> dict:
        """
        Load Upheal credentials from .env file.

        Args:
            credentials_path: Custom path to credentials file.

        Returns:
            Dict with 'email' and 'password' keys.

        Raises:
            CredentialError: If credentials file not found or missing values.
        """
        # Default path: .claude/skills/crawl4ai/.env
        if credentials_path is None:
            project_root = Path(__file__).parent.parent
            credentials_path = project_root / ".claude" / "skills" / "crawl4ai" / ".env"
        else:
            credentials_path = Path(credentials_path)

        if not credentials_path.exists():
            raise CredentialError(
                f"Credentials file not found: {credentials_path}\n"
                f"Please create it with:\n"
                f"  UPHEAL_EMAIL=your@email.com\n"
                f"  UPHEAL_PASSWORD=yourpassword"
            )

        credentials = {}
        with open(credentials_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    credentials[key.strip()] = value.strip()

        email = credentials.get('UPHEAL_EMAIL')
        password = credentials.get('UPHEAL_PASSWORD')

        if not email or not password:
            raise CredentialError(
                "Missing UPHEAL_EMAIL or UPHEAL_PASSWORD in credentials file.\n"
                f"File: {credentials_path}"
            )

        logger.info(f"Loaded credentials for: {email}")
        return {'email': email, 'password': password}

    def _build_login_js(self) -> str:
        """
        Build JavaScript code to fill and submit login form.

        Uses multiple selector strategies for resilience.
        """
        email = self.credentials['email']
        password = self.credentials['password']

        # JavaScript that tries multiple selectors and provides feedback
        return f'''
        (async () => {{
            // Helper to try multiple selectors
            const findElement = (selectors) => {{
                for (const selector of selectors) {{
                    const el = document.querySelector(selector);
                    if (el) return el;
                }}
                return null;
            }};

            // Wait a moment for React/Angular to render
            await new Promise(r => setTimeout(r, 1000));

            // Find and fill email field
            const emailSelectors = {self.LOGIN_SELECTORS['email']};
            const emailField = findElement(emailSelectors);
            if (!emailField) {{
                console.error('EMAIL_FIELD_NOT_FOUND');
                return;
            }}

            // Clear and fill email using native input events for React compatibility
            emailField.focus();
            emailField.value = '';
            emailField.value = '{email}';
            emailField.dispatchEvent(new Event('input', {{ bubbles: true }}));
            emailField.dispatchEvent(new Event('change', {{ bubbles: true }}));

            // Find and fill password field
            const passwordSelectors = {self.LOGIN_SELECTORS['password']};
            const passwordField = findElement(passwordSelectors);
            if (!passwordField) {{
                console.error('PASSWORD_FIELD_NOT_FOUND');
                return;
            }}

            passwordField.focus();
            passwordField.value = '';
            passwordField.value = '{password}';
            passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
            passwordField.dispatchEvent(new Event('change', {{ bubbles: true }}));

            // Small delay before submit
            await new Promise(r => setTimeout(r, 500));

            // Find and click submit button
            const submitSelectors = {self.LOGIN_SELECTORS['submit']};
            const submitBtn = findElement(submitSelectors);
            if (submitBtn) {{
                submitBtn.click();
                console.log('LOGIN_SUBMITTED');
            }} else {{
                // Try form submit as fallback
                const form = emailField.closest('form');
                if (form) {{
                    form.submit();
                    console.log('FORM_SUBMITTED');
                }} else {{
                    console.error('SUBMIT_NOT_FOUND');
                }}
            }}
        }})();
        '''

    def _build_wait_condition(self) -> str:
        """
        Build wait condition that checks for successful login.

        Returns JS expression that returns true when dashboard is loaded
        or false if error is shown.
        """
        dashboard_selectors = self.LOGIN_SELECTORS['dashboard']
        error_selectors = self.LOGIN_SELECTORS['error']

        return f'''js:() => {{
            // Check for dashboard elements (success)
            const dashboardSelectors = {dashboard_selectors};
            for (const sel of dashboardSelectors) {{
                if (document.querySelector(sel)) return true;
            }}

            // Check URL change (many apps redirect to dashboard)
            if (window.location.pathname.includes('dashboard') ||
                window.location.pathname.includes('home') ||
                window.location.pathname.includes('sessions')) {{
                return true;
            }}

            // Check for error (fast fail)
            const errorSelectors = {error_selectors};
            for (const sel of errorSelectors) {{
                const el = document.querySelector(sel);
                if (el && el.textContent.trim().length > 0) {{
                    // Store error message for retrieval
                    window.__loginError = el.textContent.trim();
                    return true;  // Return true to stop waiting, we'll check error later
                }}
            }}

            return false;
        }}'''

    async def login(self) -> AuthResult:
        """
        Perform login to Upheal and establish authenticated session.

        Returns:
            AuthResult with status, session_id, and any error message.

        Raises:
            LoginTimeoutError: If login page doesn't respond in time.
            LoginFailedError: If credentials are rejected.
        """
        logger.info(f"Attempting login to {self.LOGIN_URL}")

        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                self._crawler = crawler

                # Configure login crawl
                login_config = CrawlerRunConfig(
                    session_id=self.session_id,
                    js_code=self._build_login_js(),
                    wait_for=self._build_wait_condition(),
                    page_timeout=60000,  # 60 seconds for login
                    screenshot=True,  # Capture for debugging
                    remove_overlay_elements=True,  # Remove cookie banners etc.
                )

                # Execute login
                result = await crawler.arun(self.LOGIN_URL, config=login_config)

                if not result.success:
                    logger.error(f"Login crawl failed: {result.error_message}")
                    return AuthResult(
                        status=AuthStatus.NETWORK_ERROR,
                        error_message=result.error_message
                    )

                # Check for login success by examining the result
                auth_result = self._check_auth_status(result)

                if auth_result.status == AuthStatus.SUCCESS:
                    self._is_authenticated = True
                    logger.info("Login successful!")
                else:
                    logger.warning(f"Login failed: {auth_result.error_message}")

                return auth_result

        except asyncio.TimeoutError:
            logger.error("Login timeout")
            return AuthResult(
                status=AuthStatus.TIMEOUT,
                error_message="Login page timed out after 60 seconds"
            )
        except Exception as e:
            logger.exception(f"Unexpected login error: {e}")
            return AuthResult(
                status=AuthStatus.UNKNOWN_ERROR,
                error_message=str(e)
            )

    def _check_auth_status(self, result) -> AuthResult:
        """
        Analyze crawl result to determine authentication status.

        Args:
            result: CrawlResult from login attempt.

        Returns:
            AuthResult with appropriate status.
        """
        html = result.html.lower() if result.html else ""
        url = result.url.lower() if hasattr(result, 'url') else ""

        # Check for successful redirect to authenticated pages
        if any(path in url for path in ['dashboard', 'home', 'sessions', 'clients']):
            return AuthResult(
                status=AuthStatus.SUCCESS,
                session_id=self.session_id,
                user_info={'email': self.credentials['email']}
            )

        # Check HTML for dashboard indicators
        dashboard_indicators = ['dashboard', 'logout', 'sign out', 'my account', 'sessions']
        if any(indicator in html for indicator in dashboard_indicators):
            return AuthResult(
                status=AuthStatus.SUCCESS,
                session_id=self.session_id,
                user_info={'email': self.credentials['email']}
            )

        # Check for error indicators
        error_indicators = [
            'invalid email or password',
            'incorrect password',
            'invalid credentials',
            'login failed',
            'authentication failed',
            'account not found',
            'wrong password',
        ]
        for indicator in error_indicators:
            if indicator in html:
                return AuthResult(
                    status=AuthStatus.INVALID_CREDENTIALS,
                    error_message=f"Login rejected: {indicator}"
                )

        # Check if still on login page
        if 'login' in url or 'sign in' in url:
            return AuthResult(
                status=AuthStatus.UNKNOWN_ERROR,
                error_message="Still on login page after submission - login may have failed silently"
            )

        # Optimistic: if we're not on login page and no errors, assume success
        return AuthResult(
            status=AuthStatus.SUCCESS,
            session_id=self.session_id,
            user_info={'email': self.credentials['email']}
        )

    async def fetch_protected_page(
        self,
        path: str,
        wait_for: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Fetch a protected page using the authenticated session.

        Args:
            path: URL path (e.g., "/dashboard" or full URL).
            wait_for: Optional CSS selector or JS condition to wait for.

        Returns:
            Tuple of (success: bool, markdown: str, error: str).
        """
        if not self._is_authenticated:
            return (False, None, "Not authenticated. Call login() first.")

        # Build full URL if needed
        if path.startswith('/'):
            url = f"{self.BASE_URL}{path}"
        elif not path.startswith('http'):
            url = f"{self.BASE_URL}/{path}"
        else:
            url = path

        logger.info(f"Fetching protected page: {url}")

        try:
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                config = CrawlerRunConfig(
                    session_id=self.session_id,
                    wait_for=wait_for or "css:body",
                    page_timeout=30000,
                )

                result = await crawler.arun(url, config=config)

                if result.success:
                    return (True, result.markdown, None)
                else:
                    return (False, None, result.error_message)

        except Exception as e:
            logger.exception(f"Error fetching protected page: {e}")
            return (False, None, str(e))

    @property
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._is_authenticated

    async def get_session_list(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Convenience method to fetch therapy sessions list."""
        return await self.fetch_protected_page(
            "/sessions",
            wait_for="css:[class*='session'], css:.sessions-list"
        )

    async def get_dashboard(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Convenience method to fetch dashboard."""
        return await self.fetch_protected_page(
            "/dashboard",
            wait_for="css:[class*='dashboard'], css:.main-content"
        )


async def test_authentication():
    """
    Test the authentication flow.

    Attempts to:
    1. Load credentials
    2. Login to Upheal
    3. Fetch a protected page (dashboard)
    """
    print("\n" + "=" * 60)
    print("UPHEAL AUTHENTICATED SCRAPER - TEST")
    print("=" * 60 + "\n")

    try:
        # Initialize scraper
        print("[1] Initializing scraper...")
        scraper = UphealAuthenticatedScraper(
            headless=True,  # Set to False to watch the browser
            verbose=False
        )
        print(f"    Credentials loaded for: {scraper.credentials['email']}")

        # Attempt login
        print("\n[2] Attempting login...")
        result = await scraper.login()

        print(f"\n    Status: {result.status.value}")
        if result.session_id:
            print(f"    Session ID: {result.session_id}")
        if result.error_message:
            print(f"    Error: {result.error_message}")
        if result.user_info:
            print(f"    User: {result.user_info}")

        if result.status == AuthStatus.SUCCESS:
            print("\n[3] Fetching protected page (dashboard)...")
            success, markdown, error = await scraper.get_dashboard()

            if success:
                print(f"    Dashboard fetched successfully!")
                print(f"    Content length: {len(markdown or '')} characters")
                if markdown:
                    print("\n    --- First 500 chars of dashboard ---")
                    print(markdown[:500])
                    print("    --- End preview ---\n")
            else:
                print(f"    Failed to fetch dashboard: {error}")
        else:
            print("\n[3] Skipping protected page fetch (not authenticated)")

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Login Status: {'SUCCESS' if result.status == AuthStatus.SUCCESS else 'FAILED'}")
        print(f"Session ID: {result.session_id or 'N/A'}")
        print(f"Is Authenticated: {scraper.is_authenticated}")
        print("=" * 60 + "\n")

        return result.status == AuthStatus.SUCCESS

    except CredentialError as e:
        print(f"\n[ERROR] Credential Error: {e}")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected Error: {e}")
        import traceback
        traceback.print_exc()
        return False


# Example usage and reusable functions
async def login() -> Tuple[AuthResult, UphealAuthenticatedScraper]:
    """
    Reusable login function that returns authenticated scraper instance.

    Returns:
        Tuple of (AuthResult, UphealAuthenticatedScraper instance).

    Example:
        result, scraper = await login()
        if result.status == AuthStatus.SUCCESS:
            success, content, _ = await scraper.fetch_protected_page("/clients")
    """
    scraper = UphealAuthenticatedScraper()
    result = await scraper.login()
    return result, scraper


if __name__ == "__main__":
    # Run test
    success = asyncio.run(test_authentication())
    sys.exit(0 if success else 1)
