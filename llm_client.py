import os
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()

# Initialize client
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
)

SYSTEM_PROMPT = """You are an expert web content extractor. Extract structured data from the markdown content.

**Output JSON Schema**:
{
    "type": "detail" | "list" | "unknown",
    "title": "Page title or headline",
    "summary": "Brief summary (1-2 sentences)",
    "full_text": "Complete article text (detail pages only)",
    "published_date": "YYYY-MM-DD format if found",
    "images": [{"url": "absolute URL", "alt": "alt text", "description": "context"}],
    "items": [{"title": "", "url": "", "snippet": "", "published_date": ""}]  // list pages only
}

**Rules**:
1. **Type Detection**: "detail" for single articles, "list" for feeds/indexes
2. **Detail Pages**: Extract full_text (all content), images (exclude logos/icons), items=[]
3. **List Pages**: Extract items (up to 20), full_text=null, minimal images
4. **Images**: Must be absolute URLs, capture alt + infer description from context
5. **Quality**: Prefer complete extraction over partial data

Return ONLY valid JSON matching this schema."""

async def extract_content(markdown_content: str, base_url: str) -> dict:
    """
    Directly extract structured content using LLM with JSON mode.
    Much faster than code generation approach.
    """
    # Truncate markdown to avoid token limits (keep first 8000 tokens ~32k chars)
    if len(markdown_content) > 32000:
        markdown_content = markdown_content[:32000] + "\n\n[Content truncated for processing]"
    
    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Base URL: {base_url}\n\nMarkdown Content:\n{markdown_content}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=4000
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Ensure required fields exist
        if "type" not in result:
            result["type"] = "unknown"
        if "images" not in result:
            result["images"] = []
        if "items" not in result:
            result["items"] = []
            
        return result
        
    except Exception as e:
        # Return minimal valid structure on error
        return {
            "type": "unknown",
            "title": "Error extracting content",
            "summary": str(e),
            "full_text": None,
            "published_date": None,
            "images": [],
            "items": []
        }
