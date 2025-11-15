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
    
    def start_session(self) -> str:
        """Start a new browser session.
        
        Note: The browser runs on Browser Cash's servers and should be in headful
        (visible) mode by default. Browser visibility is controlled by Browser Cash's
        server configuration.
        
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
        response = requests.post(url, headers=self.headers, json={})
        
        # Handle session limit error
        if response.status_code == 403:
            error_data = response.json() if response.text else {}
            error_msg = response.text.lower()
            if "limit" in error_msg or "limit" in str(error_data).lower():
                print(f"⚠️ Session limit reached! Please check Browser Cash dashboard.")
                raise Exception("Session limit reached. Please stop existing sessions in Browser Cash dashboard or wait for them to timeout.")
        
        # Accept both 200 and 201 (Created) as success
        if response.status_code not in [200, 201]:
            print(f"❌ Error starting session: {response.status_code}")
            response.raise_for_status()
        
        try:
            data = response.json()
        except Exception as e:
            print(f"❌ Failed to parse JSON: {e}")
            raise
        
        # Try different possible response formats
        self.session_id = (
            data.get("id") or 
            data.get("session_id") or 
            data.get("sessionId") or
            data.get("data", {}).get("id") or
            data.get("data", {}).get("session_id")
        )
        
        if not self.session_id:
            raise ValueError(f"Failed to get session ID from response. Response keys: {list(data.keys())}")
        
        self.session_data = data
        
        # Wait for session to become active
        self.wait_for_active()
        
        return self.session_id
    
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
            
            # Generate browser view URL for dashboard
            view_url = self.get_browser_view_url(external_cdp_url)
            
            # Automatically open browser view in a new tab
            try:
                webbrowser.open(view_url)
            except Exception:
                pass  # Silently fail
            
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
        
        # Create a new Playwright instance for this thread if needed
        # Each BrowserCashClient instance should have its own Playwright instance
        # This avoids conflicts when running in parallel threads
        if not self.playwright:
            try:
                # Try to create Playwright normally
                self.playwright = sync_playwright().start()
            except RuntimeError as e:
                if "asyncio" in str(e).lower() or "event loop" in str(e).lower():
                    # If there's an asyncio conflict, create Playwright in a new thread context
                    # This happens when Playwright detects an asyncio event loop
                    import threading
                    import queue
                    
                    def create_playwright():
                        return sync_playwright().start()
                    
                    # Create Playwright in a separate thread to avoid asyncio conflicts
                    result_queue = queue.Queue()
                    def worker():
                        try:
                            pw = create_playwright()
                            result_queue.put(pw)
                        except Exception as ex:
                            result_queue.put(ex)
                    
                    thread = threading.Thread(target=worker, daemon=True)
                    thread.start()
                    thread.join(timeout=10)
                    
                    if not result_queue.empty():
                        result = result_queue.get()
                        if isinstance(result, Exception):
                            raise result
                        self.playwright = result
                    else:
                        raise RuntimeError("Failed to create Playwright instance in thread")
                else:
                    raise
        
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
    
    def navigate(self, url: str, wait_time: int = 3, retries: int = 3) -> None:
        """Navigate to a URL using Playwright with retry logic.
        Automatically connects Playwright if not already connected.
        
        Args:
            url: URL to navigate to
            wait_time: Seconds to wait after navigation for page load
            retries: Number of retry attempts for connection errors
        """
        self.ensure_playwright_connected()
        
        last_error = None
        for attempt in range(retries):
            try:
                # Add a small delay between retries to avoid rate limiting
                if attempt > 0:
                    delay = min(2 ** attempt, 10)  # Exponential backoff, max 10 seconds
                    print(f"    ⏳ Retrying navigation (attempt {attempt + 1}/{retries}) after {delay}s...")
                    time.sleep(delay)
                
                # Set user agent to look more like a real browser
                if attempt == 0:
                    self.page.set_extra_http_headers({
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    })
                
                self.page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(wait_time)
                return  # Success
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check if it's a connection error that we should retry
                if any(keyword in error_msg for keyword in ["err_connection_reset", "err_connection_refused", "net::err", "timeout"]):
                    if attempt < retries - 1:
                        continue  # Retry
                    else:
                        raise Exception(f"Failed to navigate to {url} after {retries} attempts: {e}")
                else:
                    # Non-retryable error, raise immediately
                    raise
        
        # If we get here, all retries failed
        if last_error:
            raise last_error
    
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
                        # Page may have navigated - silently retry
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
    
    
    def stop_session(self, force: bool = False) -> None:
        """Stop the current browser session.
        
        Args:
            force: If True, forcefully stop without waiting for Playwright cleanup
        """
        session_to_stop = self.session_id
        
        if not session_to_stop:
            return  # No session to stop
        
        # FIRST: Stop the remote browser session immediately (most important)
        try:
            url = f"{self.base_url}/session?sessionId={session_to_stop}"
            response = requests.delete(url, headers=self.headers, timeout=10)
            
            if response.status_code not in [200, 204]:
                # Try again if first attempt failed
                try:
                    response = requests.delete(url, headers=self.headers, timeout=5)
                except:
                    pass
        except Exception as e:
            # Even if DELETE fails, continue with cleanup
            pass
        
        # Clear local state
        self.session_id = None
        self.session_data = None
        self.cdp_url = None
        
        # Close Playwright connection if open (non-blocking)
        if self.browser:
            try:
                self.browser.close()
            except Exception:
                pass  # Silently fail - browser may already be closed
            finally:
                self.browser = None
                self.page = None
        
        # Stop Playwright (can be slow, so make it optional)
        if self.playwright and not force:
            import threading
            def stop_playwright():
                try:
                    self.playwright.stop()
                except Exception:
                    pass  # Silently fail
            
            # Try to stop in a non-blocking way with very short timeout
            stop_thread = threading.Thread(target=stop_playwright, daemon=True)
            stop_thread.start()
            stop_thread.join(timeout=0.5)
            
            self.playwright = None
        elif self.playwright and force:
            # In force mode, just clear the reference without waiting
            self.playwright = None
    
    def __enter__(self):
        """Context manager entry."""
        self.start_session()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_session()

