import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()

# Initialize client. It will automatically use OPENAI_API_KEY env var.
# For OpenRouter, set OPENAI_BASE_URL=https://openrouter.ai/api/v1
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)

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
2. IGNORE navigation links, headers, footers, and sidebars. Focus ONLY on the main content area.
3. Extract relevant data with CONSISTENT schemas:
   
   **If List Page**: Return a list of dictionaries, each with:
   - `title` (str): The item title
   - `url` (str): The item URL (absolute)
   - `snippet` (str): A brief description or preview text
   
   Example: `parsed = [{"title": "...", "url": "...", "snippet": "..."}, ...]`
   
   **If Detail Page**: Return a single dictionary with:
   - `title` (str): The article/page title
   - `summary` (str): A brief summary or meta description
   - `full_text` (str): The complete article text
   - `images` (list): Up to 3 relevant content images, each with `{"url": "...", "alt": "..."}` (exclude logos/icons)
   - `links` (list, optional): Relevant links within the article body
   
   Example: `parsed = {"title": "...", "summary": "...", "full_text": "...", "images": [...], "links": [...]}`
   
   **If Unclear**: Extract a generic text summary as a string.

4. Assign the final result to a variable named `parsed`.
5. Do NOT import any modules. `BeautifulSoup` is ALREADY IMPORTED and available as a global variable.
6. Do NOT use print().
7. Do NOT include markdown code blocks (```python ... ```). Just the code.
8. Handle potential missing elements gracefully. ALWAYS check if an element exists before acting on it.
   - BAD: `soup.find('div').text`
   - GOOD: `div = soup.find('div'); val = div.text if div else ""`
9. RESOLVE ALL RELATIVE URLs to absolute URLs.
   - You have access to `base_url` (str) and `urljoin` (function).
   - Example: `full_url = urljoin(base_url, relative_url)` if relative_url else None
   - Apply this to ALL `href` and `src` attributes you extract.

"""

async def generate_parsing_code(html_snippet: str, schema_map: dict[str, str] = None, page_type: str = None) -> str:
    """
    Sends the HTML snippet to the LLM and returns the generated Python code.
    If schema_map is provided, it instructs the LLM to extract exactly those fields.
    If page_type is provided ("list" or "detail"), it overrides auto-detection.
    """
    
    current_system_prompt = SYSTEM_PROMPT
    
    # Override page type detection if specified
    if page_type:
        if page_type == "list":
            type_instruction = "\n\nCRITICAL: This is a LIST PAGE. You MUST extract a list of items with (title, url, snippet). Do NOT treat it as a detail page."
        elif page_type == "detail":
            type_instruction = "\n\nCRITICAL: This is a DETAIL PAGE. You MUST extract title, summary, full_text, main_image (url and alt text), and relevant links. Do NOT treat it as a list page."
        else:
            type_instruction = ""
        current_system_prompt += type_instruction
    
    if schema_map:
        schema_instruction = "\n\nCRITICAL: You MUST extract the following fields. The output `parsed` variable MUST be a dictionary (or list of dicts) with these EXACT keys:\n"
        for key, desc in schema_map.items():
            schema_instruction += f"- {key}: {desc}\n"
        schema_instruction += "\nDo NOT add any other fields. If a field is missing, use an empty string or None."
        current_system_prompt += schema_instruction

    user_prompt = f"Here is the HTML content:\n\n{html_snippet}\n\nWrite the parsing code now."

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini", # Switch to mini for cost efficiency
            messages=[
                {"role": "system", "content": current_system_prompt},
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
