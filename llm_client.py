import os
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()

# Initialize client. It will automatically use OPENAI_API_KEY env var.
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)

SYSTEM_PROMPT = """
You are an expert web scraper. The input is the **MARKDOWN** content of a webpage.
Your goal is to extract structured data into a SINGLE Python dictionary matching the `ParsedContent` schema.

Input: `markdown_content` (str)
Output: Assign the result to a variable named `parsed`.

**Schema Structure**:
```python
parsed = {
    "type": "detail" | "list" | "unknown",
    "title": "Page Title or Main Headline",
    "summary": "Brief summary of content",
    "full_text": "Full article body text (if detail page)",
    "published_date": "YYYY-MM-DD (if found)",
    "images": [
        {"url": "...", "alt": "...", "description": "..."}
    ],
    "items": [ # For list pages ONLY
        {"title": "...", "url": "...", "snippet": "...", "published_date": "..."}
    ]
}
```

**Rules**:
1. **Detect Type**:
   - If it's a single article/news post -> "detail".
   - If it's a feed/index/search results -> "list".
2. **Detail Page**:
   - Extract `full_text` (all main content).
   - Extract ALL relevant images into `images`. Exclude icons/avatars/logos.
   - `items` should be empty `[]`.
3. **List Page**:
   - Extract up to 20 items into `items`.
   - `full_text` should be None.
   - `images` can be empty or contain main feed images.
4. **Images**:
   - MUST be absolute URLs. Use `urljoin(base_url, ...)` if needed.
   - Capture `alt` text and try to infer a `description` from context.
5. **Safety**:
   - `parsed` MUST be defined.
   - Do NOT use imports (markdown, re, json are allowed if built-in, but prefer simple string ops).
   - `urljoin` is available globally.
"""

async def generate_parsing_code(markdown_snippet: str, schema_map: dict[str, str] = None, page_type: str = None) -> str:
    """
    Sends the Markdown snippet to the LLM and returns the generated Python code.
    """
    
    current_system_prompt = SYSTEM_PROMPT
    
    if page_type:
        current_system_prompt += f"\n\nCRITICAL: User specified page_type='{page_type}'. Strict enforcement."

    if schema_map:
        # Schema map is less relevant now with strict stricture, but we can add as "custom fields" if we wanted
        # For now, we stick to the core schema to satisfy "consistent schema" requirement.
        pass

    user_prompt = f"Here is the MARKDOWN content:\n\n{markdown_snippet}\n\nWrite the parsing code now."

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=[
                {"role": "system", "content": current_system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
        )
        
        code = response.choices[0].message.content.strip()
        
        # Cleanup code fences
        if code.startswith("```python"): code = code[9:]
        elif code.startswith("```"): code = code[3:]
        if code.endswith("```"): code = code[:-3]
        
        # Basic sanitization
        lines = code.split('\n')
        safe_lines = [line for line in lines if not line.strip().startswith(('import ', 'from ', 'pip '))]
        
        # Allow 'import re' or 'import json' if explicitly needed? 
        # Sandbox usually blocks them unless enabled. 
        # Better to rely on standard string ops or the pre-imported env.
        # But regex is very useful. Let's assume re is NOT available unless passed in sandbox.
        # Check sandbox.py next.
        
        return '\n'.join(safe_lines).strip()

    except Exception as e:
        raise RuntimeError(f"LLM generation failed: {e}")
