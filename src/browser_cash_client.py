"""Browser Cash API client for managing browser sessions."""
import requests
import json
import time
import webbrowser
from typing import Optional, Dict, Any
from src.config import BROWSER_CASH_API_KEY, BROWSER_CASH_BASE_URL, MILAN_HOST

# Lazy import Playwright (only needed when using CDP)
try:
    from playwright.sync_api import sync_playwright, Browser, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = None
    Page = None


class BrowserCashClient:
    """Client for interacting with Browser Cash API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Browser Cash client.
        
        Args:
            api_key: Browser Cash API key. If not provided, uses config value.
        """
        self.api_key = api_key or BROWSER_CASH_API_KEY
        if not self.api_key:
            raise ValueError("Browser Cash API key is required. Set BROWSER_CASH_API_KEY in .env file.")
        
        self.base_url = BROWSER_CASH_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.session_id: Optional[str] = None
        self.session_data: Optional[Dict[str, Any]] = None
        self.cdp_url: Optional[str] = None
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    def start_session(self, max_retries: int = 5) -> str:
        """Start a new browser session with retry logic.

        Note: The browser runs on Browser Cash's servers and should be in headful
        (visible) mode by default. Browser visibility is controlled by Browser Cash's
        server configuration.
        
        Args:
            max_retries: Maximum number of retry attempts (default: 5)

        Returns:
            Session ID for the created session.
        """
        # If we have an existing session, try to stop it first
        if self.session_id:
            try:
                self.stop_session()
            except Exception as e:
                print(f"⚠️ Warning: Could not stop existing session: {e}")
        
        url = f"{self.base_url}/session"
        last_error = None

        # Retry loop with exponential backoff
        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempting to connect to Browser Cash API (attempt {attempt + 1}/{max_retries})...")

                # Use a new session with connection pooling for better reliability
                session = requests.Session()
                adapter = requests.adapters.HTTPAdapter(
                    max_retries=requests.adapters.Retry(
                        total=3,
                        backoff_factor=0.5,
                        status_forcelist=[500, 502, 503, 504]
                    )
                )
                session.mount('https://', adapter)
                session.mount('http://', adapter)

                response = session.post(
                    url,
                    headers=self.headers,
                    json={},
                    timeout=30  # 30 second timeout
                )

                # Debug: Print response details
                print(f"🔍 API Response Status: {response.status_code}")

                # Handle session limit error
                if response.status_code == 403:
                    error_data = response.json() if response.text else {}
                    error_msg = response.text.lower()
                    if "limit" in error_msg or "limit" in str(error_data).lower():
                        print(f"⚠️ Session limit reached!")
                        print(f"💡 Please check Browser Cash dashboard and manually stop any running sessions.")
                        print(f"💡 Or wait a few minutes for sessions to timeout.")
                        raise Exception("Session limit reached. Please stop existing sessions in Browser Cash dashboard or wait for them to timeout.")

                # Accept both 200 and 201 (Created) as success
                if response.status_code not in [200, 201]:
                    print(f"❌ Error Response: {response.text}")
                    response.raise_for_status()

                data = response.json()
                print(f"🔍 API Response Data: {data}")

                # Try different possible response formats
                self.session_id = (
                    data.get("id") or
                    data.get("session_id") or
                    data.get("sessionId") or
                    data.get("data", {}).get("id") or
                    data.get("data", {}).get("session_id")
                )

                if not self.session_id:
                    print(f"❌ Full response structure: {json.dumps(data, indent=2)}")
                    raise ValueError(f"Failed to get session ID from response. Response keys: {list(data.keys())}")

                self.session_data = data
                print(f"✅ Browser session started: {self.session_id}")

                # Wait for session to become active
                self.wait_for_active()

                return self.session_id

            except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
                last_error = e
                wait_time = min(2 ** attempt, 16)  # Exponential backoff: 1s, 2s, 4s, 8s, 16s max
                print(f"⚠️ Connection error: {type(e).__name__}: {e}")

                if attempt < max_retries - 1:
                    print(f"🔄 Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ Failed after {max_retries} attempts")
                    print(f"💡 Troubleshooting:")
                    print(f"   1. Check your internet connection")
                    print(f"   2. Verify Browser Cash API key in .env is correct")
                    print(f"   3. Check Browser Cash service status")
                    print(f"   4. Try again in a few minutes")
                    raise Exception(f"Failed to connect to Browser Cash API after {max_retries} attempts. Last error: {last_error}")

            except requests.exceptions.Timeout as e:
                last_error = e
                print(f"⚠️ Request timeout: {e}")

                if attempt < max_retries - 1:
                    wait_time = min(2 ** attempt, 16)
                    print(f"🔄 Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Browser Cash API timeout after {max_retries} attempts")

            except Exception as e:
                print(f"❌ Unexpected error: {type(e).__name__}: {e}")
                raise

        # Should never reach here, but just in case
        raise Exception(f"Failed to start session after {max_retries} attempts. Last error: {last_error}")

    def wait_for_active(self, timeout_ms: int = 20000) -> Dict[str, Any]:
        """Wait for the session to become active.
        
        Args:
            timeout_ms: Maximum time to wait in milliseconds
            
        Returns:
            Session data when active
        """
        start = time.time()
        while True:
            session_data = self.get_session()
            session = session_data.get("session", {})
            status = session.get("status")
            
            if status == "active":
                print(f"✅ Session is active")
                return session_data
            
            elapsed = (time.time() - start) * 1000
            if elapsed > timeout_ms:
                raise TimeoutError(f"Session did not become active within {timeout_ms}ms")
            
            time.sleep(1)
    
    def get_cdp_url(self) -> str:
        """Get the CDP (Chrome DevTools Protocol) URL for Playwright/Puppeteer.
        
        Returns:
            WebSocket CDP URL
        """
        if not self.session_id:
            raise ValueError("No active session. Call start_session() first.")
        
        # Get browser info from /json/version endpoint
        # Format: https://<milan-host>/v1/consumer/<SESSION_ID>/json/version
        version_url = f"https://{MILAN_HOST}/v1/consumer/{self.session_id}/json/version"
        
        try:
            response = requests.get(version_url, timeout=10)
            response.raise_for_status()
            browser_info = response.json()
            
            # Extract local CDP URL (e.g., ws://127.0.0.1/devtools/browser/...)
            local_cdp_url = browser_info.get("webSocketDebuggerUrl")
            
            if not local_cdp_url:
                raise ValueError("No webSocketDebuggerUrl in browser info")
            
            # Convert to external CDP URL
            # ws://127.0.0.1/devtools/browser/... -> wss://<milan-host>/v1/consumer/<sessionId>/devtools/browser/...
            external_cdp_url = local_cdp_url.replace(
                "ws://127.0.0.1",
                f"wss://{MILAN_HOST}/v1/consumer/{self.session_id}"
            )
            
            self.cdp_url = external_cdp_url
            print(f"✅ CDP URL: {external_cdp_url}")
            
            # Generate browser view URL for dashboard
            view_url = self.get_browser_view_url(external_cdp_url)
            print(f"👀 View browser: {view_url}")
            
            # Automatically open browser view in a new tab
            try:
                webbrowser.open(view_url)
                print(f"🌐 Opened browser view in new tab")
            except Exception as e:
                print(f"⚠️ Could not open browser automatically: {e}")
            
            return external_cdp_url
            
        except requests.exceptions.RequestException as e:
            raise ValueError(
                f"Failed to get CDP URL from {version_url}. "
                f"Error: {e}. "
                f"Please check if MILAN_HOST is correct in config (current: {MILAN_HOST})"
            )
    
    def get_browser_view_url(self, cdp_url: str) -> str:
        """Get the Browser Cash dashboard URL to view the browser session.
        
        Args:
            cdp_url: The WebSocket CDP URL
            
        Returns:
            Dashboard URL to view the browser
        """
        import urllib.parse
        encoded_url = urllib.parse.quote(cdp_url, safe='')
        return f"https://dash.browser.cash/cdp_tabs?ws={encoded_url}"
    
    def connect_playwright(self, cdp_url: str) -> Page:
        """Connect to the browser session using Playwright via CDP.
        
        Note: The browser is already running on Browser Cash's servers.
        Browser visibility (headful/headless) is controlled by Browser Cash's
        server configuration, not by this connection.
        
        Args:
            cdp_url: WebSocket CDP URL
            
        Returns:
            Playwright Page object
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is not installed. Run: pip install playwright && playwright install chromium")
        
        if not self.playwright:
            self.playwright = sync_playwright().start()
        
        # Connect to existing browser via CDP (browser is already running on Browser Cash servers)
        # The browser should be running in headful mode by default on Browser Cash
        self.browser = self.playwright.chromium.connect_over_cdp(cdp_url)
        contexts = self.browser.contexts
        if contexts:
            self.page = contexts[0].pages[0] if contexts[0].pages else None
        
        if not self.page:
            self.page = self.browser.new_page()
        
        return self.page
    
    def ensure_playwright_connected(self) -> None:
        """Ensure Playwright is connected to the browser session.
        Automatically gets CDP URL and connects if not already connected.
        """
        if self.page:
            return  # Already connected
        
        if not self.cdp_url:
            self.cdp_url = self.get_cdp_url()
        
        self.connect_playwright(self.cdp_url)
    
    def navigate(self, url: str, wait_time: int = 3) -> None:
        """Navigate to a URL using Playwright.
        Automatically connects Playwright if not already connected.
        
        Args:
            url: URL to navigate to
            wait_time: Seconds to wait after navigation for page load
        """
        self.ensure_playwright_connected()
        
        print(f"🌐 Navigating to: {url}")
        self.page.goto(url, wait_until="domcontentloaded")
        time.sleep(wait_time)
    
    def execute_script(self, script: str, retries: int = 2) -> Any:
        """Execute JavaScript in the browser session using Playwright.
        Automatically connects Playwright if not already connected.
        
        Args:
            script: JavaScript code to execute
            retries: Number of retries if execution context is destroyed
            
        Returns:
            Result of script execution
        """
        self.ensure_playwright_connected()
        
        for attempt in range(retries + 1):
            try:
                return self.page.evaluate(script)
            except Exception as e:
                error_msg = str(e)
                # Check if it's an execution context error (page navigated during execution)
                if "Execution context was destroyed" in error_msg or "Target closed" in error_msg:
                    if attempt < retries:
                        print(f"⚠️ Execution context destroyed (attempt {attempt + 1}/{retries + 1}), retrying...")
                        # Wait a bit for page to stabilize
                        import time
                        time.sleep(1)
                        # Re-ensure connection
                        self.ensure_playwright_connected()
                        continue
                    else:
                        print(f"⚠️ Execution context destroyed after {retries + 1} attempts - page may have navigated")
                        raise
                else:
                    # Other errors, don't retry
                    print(f"⚠️ Error executing script: {e}")
                    raise
        
        # Should never reach here, but just in case
        raise Exception("Failed to execute script after retries")
    
    def get_session(self) -> Dict[str, Any]:
        """Get current session information.
        
        Returns:
            Session data
        """
        if not self.session_id:
            raise ValueError("No active session. Call start_session() first.")
        
        # Session ID is passed as query parameter, not in path
        url = f"{self.base_url}/session?sessionId={self.session_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    
    def stop_session(self) -> None:
        """Stop the current browser session."""
        session_to_stop = self.session_id
        
        # Clear local state first (so we don't try to stop again)
        self.session_id = None
        self.session_data = None
        self.cdp_url = None
        
        # Close Playwright connection if open (non-blocking)
        if self.browser:
            try:
                self.browser.close()
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")
            finally:
                self.browser = None
                self.page = None
        
        # Stop Playwright (can be slow, so wrap in try/except)
        # Use a thread to avoid blocking on stop()
        if self.playwright:
            import threading
            def stop_playwright():
                try:
                    self.playwright.stop()
                except Exception as e:
                    print(f"⚠️ Error stopping Playwright (may already be stopped): {e}")
            
            # Try to stop in a non-blocking way
            stop_thread = threading.Thread(target=stop_playwright, daemon=True)
            stop_thread.start()
            # Give it a short time to complete, but don't wait forever
            stop_thread.join(timeout=2)
            if stop_thread.is_alive():
                print("⚠️ Playwright stop taking too long, continuing anyway...")
            
            self.playwright = None
        
        if not session_to_stop:
            print("⚠️ No active session to stop.")
            return
        
        # Session ID is passed as query parameter, not in path
        try:
            url = f"{self.base_url}/session?sessionId={session_to_stop}"
            response = requests.delete(url, headers=self.headers, timeout=5)
            
            if response.status_code in [200, 204]:
                print(f"🛑 Browser session stopped: {session_to_stop}")
            else:
                print(f"⚠️ Session stop returned {response.status_code}: {response.text}")
        except Exception as e:
            print(f"⚠️ Error stopping session (may already be stopped): {e}")
            # Don't raise - session might already be stopped
    
    def __enter__(self):
        """Context manager entry."""
        self.start_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_session()

