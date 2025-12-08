import asyncio
import os
from dotenv import load_dotenv

# Load env vars
load_dotenv()

from fetcher import fetch_page_html
from cleaner import clean_html
from sandbox import execute_parsing_code
from llm_client import generate_parsing_code

# Mock LLM response for testing (Fallback)
MOCK_CODE = """
soup = BeautifulSoup(html_content, 'html.parser')
title = soup.title.string if soup.title else "No Title"
# Simulate extracting more content
full_text = "This is a simulated full text extraction from the page..."
main_image = {"url": "https://example.com/image.jpg", "alt": "Example Image"}
parsed = {
    "title": title,
    "full_text": full_text,
    "main_image": main_image,
    "mocked": True
}
"""

async def test_pipeline():
    url = "https://techcrunch.com/2025/12/05/the-new-york-times-is-suing-perplexity-for-copyright-infringement/"
    print(f"Testing pipeline with URL: {url}")

    api_key = os.getenv("OPENAI_API_KEY")
    use_real_llm = api_key and api_key != "your-key-goes-here"

    try:
        # 1. Fetch
        print("1. Fetching...")
        html = await fetch_page_html(url)
        print(f"   Fetched {len(html)} chars.")

        # 2. Clean
        print("2. Cleaning...")
        cleaned = clean_html(html)
        print(f"   Cleaned to {len(cleaned)} chars.")

        # 3. Generate Code
        if use_real_llm:
            print("3. Generating code with REAL LLM (OpenAI)...")
            code = await generate_parsing_code(cleaned)
        else:
            print("3. Mocking LLM code generation (Add OPENAI_API_KEY to .env to use real LLM)...")
            code = MOCK_CODE
        
        print(f"   Code snippet: {code[:100]}...")

        # 4. Execute
        print("4. Executing in sandbox...")
        result = execute_parsing_code(code, cleaned)
        print(f"   Result: {result}")

        print("\nSUCCESS: Pipeline verified!")

    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
