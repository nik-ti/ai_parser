import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()

# Initialize client. It will automatically use OPENAI_API_KEY env var.
client = AsyncOpenAI()

SYSTEM_PROMPT = """
You are an expert web scraper. Your goal is to write Python code to extract structured data from HTML.
You will be given a snippet of HTML from a webpage.
You must determine if it is a "List Page" (multiple items) or a "Detail Page" (single item).

Your output must be ONLY valid Python code.
The code will be executed in a sandboxed environment with the following available:
- `html_content`: The string containing the HTML.
- `BeautifulSoup`: The bs4.BeautifulSoup class.

Rules:
1. Parse `html_content` using `BeautifulSoup(html_content, 'html.parser')`.
2. Extract relevant data.
   - If List Page: Extract a list of items (title, url, snippet).
   - If Detail Page: Extract title, summary, full_text, main_image (url and alt text), and any other relevant links.
   - If Unclear: Extract a generic text summary.
3. Assign the final result to a variable named `parsed`.
4. Do NOT import any modules. `BeautifulSoup` is ALREADY IMPORTED and available as a global variable.
5. Do NOT use print().
6. Do NOT include markdown code blocks (```python ... ```). Just the code.
7. Handle potential missing elements gracefully. ALWAYS check if an element exists before acting on it.
   - BAD: `soup.find('div').text`
   - GOOD: `div = soup.find('div'); val = div.text if div else ""`

"""

async def generate_parsing_code(html_snippet: str) -> str:
    """
    Sends the HTML snippet to the LLM and returns the generated Python code.
    """
    
    user_prompt = f"Here is the HTML content:\n\n{html_snippet}\n\nWrite the parsing code now."

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini", # Switch to mini for cost efficiency
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0, # Deterministic output is better for code
        )
        
        code = response.choices[0].message.content.strip()
        
        # Strip markdown code fences if the LLM ignores the instruction
        if code.startswith("```python"):
            code = code[9:]
        elif code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]
        
        # Strip import lines to be safe against sandbox violations
        lines = code.split('\n')
        safe_lines = [line for line in lines if not line.strip().startswith(('import ', 'from '))]
        code = '\n'.join(safe_lines)
            
        return code.strip()

    except Exception as e:
        raise RuntimeError(f"LLM generation failed: {e}")
