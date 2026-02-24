from playwright.async_api import async_playwright, Browser, Playwright
import logging
import asyncio

logger = logging.getLogger(__name__)

# Global browser instance
_playwright: Playwright = None
_browser: Browser = None
_browser_lock = asyncio.Lock()
_semaphore = asyncio.Semaphore(3)  # Limit concurrent page fetches

async def initialize_browser():
    """Initialize the persistent browser instance."""
    global _playwright, _browser
    
    if _browser is not None and _browser.is_connected():
        return
    
    async with _browser_lock:
        # Double-check after acquiring lock
        if _browser is not None and _browser.is_connected():
            return
        
        # Clean up old instance if it exists but is dead
        if _browser is not None:
            logger.warning("Browser was dead, cleaning up old instance...")
            try:
                await _browser.close()
            except Exception:
                pass
            _browser = None
        
        if _playwright is not None:
            try:
                await _playwright.stop()
            except Exception:
                pass
            _playwright = None
        
        logger.info("Initializing persistent browser...")
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(
            headless=True,
            args=['--disable-dev-shm-usage', '--no-sandbox'] # Crucial for Docker
        )
        logger.info("Browser initialized successfully")

async def close_browser():
    """Close the persistent browser instance."""
    global _playwright, _browser
    
    async with _browser_lock:
        if _browser:
            logger.info("Closing browser...")
            try:
                await _browser.close()
            except Exception:
                pass
            _browser = None
        
        if _playwright:
            try:
                await _playwright.stop()
            except Exception:
                pass
            _playwright = None
            logger.info("Browser closed")

async def _ensure_browser():
    """Ensure browser is alive, restart if crashed."""
    global _browser
    if _browser is None or not _browser.is_connected():
        logger.warning("Browser is dead or not initialized, restarting...")
        await initialize_browser()

async def fetch_page_html(url: str) -> str:
    """
    Fetches the fully rendered HTML of the given URL using a persistent browser.
    Blocks images/fonts/media for speed. Auto-recovers if browser crashes.
    """
    global _browser
    
    # Ensure the browser is alive before attempting to use it
    await _ensure_browser()
    
    async with _semaphore:
        page = None
        context = None
        try:
            # Create context with realistic settings to avoid bot detection
            context = await _browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                locale='en-US',
                timezone_id='America/New_York',
                permissions=['geolocation'],
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            page = await context.new_page()
            
            # Mask automation indicators
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
            """)

            # Block unnecessary resources for speed
            await page.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
                else route.continue_())

            # domcontentloaded is usually enough for content, networkidle is too slow
            try:
                logger.info(f"Loading {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
                try:
                    await page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Timeout/Error loading {url}: {e}")
            
            # Fast scroll to trigger lazy text/content (images are blocked but structure might load)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000) 
            
            # Get content
            content = await page.content()
            return content
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            # If this was a browser crash, mark browser as dead so next call restarts it
            if "Connection closed" in str(e) or "Target closed" in str(e) or "Browser closed" in str(e):
                _browser = None
                logger.warning("Browser crash detected, will restart on next request")
            raise e
        finally:
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
            if context:
                try:
                    await context.close()
                except Exception:
                    pass
