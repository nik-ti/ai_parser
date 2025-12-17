from playwright.async_api import async_playwright, Browser, Playwright
import logging
import asyncio

logger = logging.getLogger(__name__)

# Global browser instance
_playwright: Playwright = None
_browser: Browser = None
_browser_lock = asyncio.Lock()
_semaphore = asyncio.Semaphore(5)  # Limit concurrent page fetches

async def initialize_browser():
    """Initialize the persistent browser instance."""
    global _playwright, _browser
    
    if _browser is not None:
        return
    
    async with _browser_lock:
        if _browser is not None:  # Double-check after acquiring lock
            return
        
        logger.info("Initializing persistent browser...")
        _playwright = await async_playwright().start()
        _browser = await _playwright.chromium.launch(headless=True)
        logger.info("Browser initialized successfully")

async def close_browser():
    """Close the persistent browser instance."""
    global _playwright, _browser
    
    async with _browser_lock:
        if _browser:
            logger.info("Closing browser...")
            await _browser.close()
            _browser = None
        
        if _playwright:
            await _playwright.stop()
            _playwright = None
            logger.info("Browser closed")

async def fetch_page_html(url: str) -> str:
    """
    Fetches the fully rendered HTML of the given URL using a persistent browser.
    Blocks images/fonts/media for speed.
    """
    if _browser is None:
        await initialize_browser()
    
    async with _semaphore:
        page = None
        try:
            page = await _browser.new_page()
            
            # Block unnecessary resources for speed
            await page.route("**/*", lambda route: route.abort() 
                if route.request.resource_type in ["image", "media", "font", "stylesheet"] 
                else route.continue_())

            # domcontentloaded is usually enough for content, networkidle is too slow
            try:
                logger.info(f"Loading {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            except Exception as e:
                logger.warning(f"Timeout/Error loading {url}: {e}")
            
            # Fast scroll to trigger lazy text/content (images are blocked but structure might load)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000) 
            
            # Get content
            content = await page.content()
            return content
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise e
        finally:
            if page:
                await page.close()
