from playwright.async_api import async_playwright
import logging

logger = logging.getLogger(__name__)

async def fetch_page_html(url: str) -> str:
    """
    Fetches the fully rendered HTML of the given URL using Playwright.
    Tries networkidle first, falls back to domcontentloaded if it times out.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            
            # Try networkidle first (better for SPAs)
            try:
                logger.info(f"Attempting to load {url} with networkidle...")
                await page.goto(url, wait_until="networkidle", timeout=30000)
                logger.info("Successfully loaded with networkidle")
            except Exception as e:
                # Fallback to domcontentloaded + delay
                logger.warning(f"networkidle failed for {url}: {e}. Falling back to domcontentloaded...")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Give JS a bit more time to execute
                await page.wait_for_timeout(2000)
                logger.info("Loaded with domcontentloaded + 2s delay")
            
            content = await page.content()
            return content
        except Exception as e:
            raise e
        finally:
            await browser.close()
