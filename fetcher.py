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
    Tries networkidle first, falls back to domcontentloaded if it times out.
    """
    # Ensure browser is initialized
    if _browser is None:
        await initialize_browser()
    
    # Use semaphore to limit concurrent fetches
    async with _semaphore:
        page = None
        try:
            # Create a new page (context) for this request
            page = await _browser.new_page()
            
            # Try networkidle first (better for SPAs)
            try:
                logger.info(f"Attempting to load {url} with networkidle...")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                logger.info("Successfully loaded with networkidle")
            except Exception as e:
                # Fallback to domcontentloaded + delay
                logger.warning(f"networkidle failed for {url}: {e}. Falling back to domcontentloaded...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2000)
                logger.info("Loaded with domcontentloaded + 2s delay")
            
            # Auto-scroll to trigger lazy loading (scroll down 3 times)
            logger.info("Auto-scrolling to trigger lazy loading...")
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)  # Wait for content to load
            
            content = await page.content()
            return content
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise e
        finally:
            # Always close the page to free resources
            if page:
                await page.close()
