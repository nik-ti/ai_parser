from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from models import UrlRequest, ParseResponse, ParsedContent
from fetcher import fetch_page_html, initialize_browser, close_browser
from cleaner import clean_html
from llm_client import extract_content
from cache import get_cache
import logging
import asyncio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting up: Initializing browser...")
    await initialize_browser()
    yield
    # Shutdown
    logger.info("Shutting down: Closing browser...")
    await close_browser()

app = FastAPI(title="AI Parser Microservice", lifespan=lifespan)

@app.post("/parse", response_model=ParseResponse)
async def parse_url(request: UrlRequest):
    logger.info(f"Received request to parse: {request.url}")
    
    # Check cache first
    cache = get_cache()
    cached_response = cache.get(request.url, request.page_type)
    if cached_response:
        logger.info(f"Cache HIT for {request.url}")
        return cached_response
    
    logger.info(f"Cache MISS for {request.url}, processing...")
    
    async def process_logic():
        # 1. Fetch HTML
        logger.info("Fetching HTML...")
        raw_html = await fetch_page_html(request.url)
        
        # 2. Clean and Convert to Markdown
        logger.info("Cleaning & Converting to Markdown...")
        markdown_content = clean_html(raw_html)
        
        # 3. Extract Content Directly via LLM (no code generation)
        logger.info("Extracting content via LLM...")
        parsed_data = await extract_content(markdown_content, base_url=request.url)
        
        # 4. Fallback to readability if LLM failed or returned minimal data
        if (parsed_data.get("type") == "unknown" or 
            not parsed_data.get("title") or 
            parsed_data.get("title") in ["Error extracting content", "403 - Forbidden", "nytimes.com"]):
            logger.info("LLM extraction minimal, trying readability fallback...")
            from readability_fallback import extract_with_readability
            fallback_data = extract_with_readability(raw_html, request.url)
            # Merge: prefer fallback for content, keep LLM for images if available
            if fallback_data.get("full_text"):
                parsed_data = fallback_data
                if not parsed_data.get("images") and parsed_data.get("images"):
                    parsed_data["images"] = parsed_data.get("images", [])
        
        # 5. Validation & Response Construction
        if not isinstance(parsed_data, dict):
            logger.warning(f"Unexpected type {type(parsed_data)}, using fallback...")
            parsed_data = {"type": "unknown", "items": [], "images": []}

        # Ensure type field exists
        if "type" not in parsed_data:
            parsed_data["type"] = "unknown"

        # Construct Pydantic model
        valid_keys = ParsedContent.model_fields.keys()
        filtered_data = {k: v for k, v in parsed_data.items() if k in valid_keys}
        
        return ParsedContent(**filtered_data)

    try:
        # Enforce a global timeout of 90 seconds for the entire operation
        # This accommodates LLM processing (30-40s) + page fetch + overhead
        content = await asyncio.wait_for(process_logic(), timeout=90)
        
        logger.info(f"Parsing successful. Type: {content.type}")
        response = ParseResponse(ok=True, data=content)
        
        # Cache successful response (validation happens inside cache.set)
        cache.set(request.url, response.model_dump(), request.page_type)
        
        return response

    except asyncio.TimeoutError:
        logger.error(f"Request timed out processing {request.url}")
        return ParseResponse(ok=False, error="Processing timed out (server limit)")
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return ParseResponse(ok=False, error=str(e))

@app.get("/cache/stats")
async def cache_stats():
    """Get cache statistics."""
    cache = get_cache()
    return cache.stats()

@app.post("/cache/clear")
async def clear_cache():
    """Clear all cached entries."""
    cache = get_cache()
    cache.clear()
    return {"message": "Cache cleared successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
