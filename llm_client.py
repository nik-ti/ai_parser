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

SYSTEM_PROMPT = """Extract structured JSON from markdown content.

**Type Detection (CRITICAL)**:
- "list" = multiple articles/items with links (feeds, news indexes, directories)
- "detail" = single article with full content
- "unknown" = unclear structure

**Output Schema**:
{"type":"detail|list|unknown","title":"","summary":"1-2 sentences","full_text":"article text (detail only)","published_date":"YYYY-MM-DD","images":[{"url":"","alt":"","description":""}],"videos":["url"],"items":[{"title":"","url":"","snippet":"","published_date":""}]}

**Rules**:
- List pages: Extract items array (up to 20), set full_text=null
- Detail pages: Extract full_text, images, videos, set items=[]
- All URLs must be absolute
- Return ONLY valid JSON"""

async def extract_content(markdown_content: str, base_url: str) -> dict:
    """
    Directly extract structured content using LLM with JSON mode.
    Much faster than code generation approach.
    """
    # Truncate markdown to avoid token limits (keep first ~20k chars for efficiency)
    if len(markdown_content) > 20000:
        markdown_content = markdown_content[:20000] + "\n\n[Content truncated]"
    
    try:
        response = await client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "openai/gpt-4o-mini"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"URL: {base_url}\n\n{markdown_content}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=2000
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Ensure required fields exist
        if "type" not in result:
            result["type"] = "unknown"
        if "images" not in result:
            result["images"] = []
        if "videos" not in result:
            result["videos"] = []
        if "items" not in result:
            result["items"] = []
            
        # Strict validation for videos: ensure it is list[str]
        if "videos" in result and isinstance(result["videos"], list):
            cleaned_videos = []
            for v in result["videos"]:
                if isinstance(v, str):
                    cleaned_videos.append(v)
                elif isinstance(v, dict) and ("url" in v or "src" in v):
                    cleaned_videos.append(v.get("url") or v.get("src"))
            result["videos"] = cleaned_videos
        else:
            result["videos"] = []
            
        return result
        
    except Exception as e:
        # Return minimal valid structure on error
        return {
            "type": "unknown",
            "title": "Error extracting content",
            "summary": str(e),
            "full_text": None,
            "published_date": None,
            "published_date": None,
            "images": [],
            "videos": [],
            "items": []
        }
