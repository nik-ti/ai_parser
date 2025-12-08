from playwright.async_api import async_playwright

async def fetch_page_html(url: str) -> str:
    """
    Fetches the fully rendered HTML of the given URL using Playwright.
    """
    async with async_playwright() as p:
        # Launch browser (chromium is usually sufficient)
        browser = await p.chromium.launch(headless=True)
        try:
            # Create a new page
            page = await browser.new_page()
            
            # Navigate to the URL
            # 'domcontentloaded' is faster and less prone to timeouts on heavy sites.
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Get the full HTML content
            content = await page.content()
            return content
        except Exception as e:
            raise e
        finally:
            await browser.close()
