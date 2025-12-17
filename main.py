from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
from models import UrlRequest, ParseResponse, ParsedContent
from fetcher import fetch_page_html, initialize_browser, close_browser
from cleaner import clean_html
from llm_client import generate_parsing_code
from sandbox import execute_parsing_code
import logging

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
    
    try:
        # 1. Fetch HTML
        logger.info("Fetching HTML...")
        raw_html = await fetch_page_html(request.url)
        
        # 2. Clean and Convert to Markdown
        logger.info("Cleaning & Converting to Markdown...")
        markdown_content = clean_html(raw_html)
        
        # 3. Generate Code via LLM
        logger.info("Generating parsing code...")
        parsing_code = await generate_parsing_code(markdown_content, schema_map=request.schema_map, page_type=request.page_type)
        logger.info(f"Generated Code:\n{parsing_code}")
        
        # 4. Execute Code in Sandbox
        logger.info("Executing code...")
        parsed_data = execute_parsing_code(parsing_code, markdown_content, base_url=request.url)
        
        # 5. Validation & Response Construction
        if not isinstance(parsed_data, dict):
            # Fallback if LLM returned list instead of dict (should vary rarely happen with new prompt)
            logger.warning(f"Unexpected type {type(parsed_data)}, trying to wrap...")
            if isinstance(parsed_data, list):
                # Guess it's a list page
                parsed_data = {"type": "list", "items": parsed_data, "images": []}
            else:
                parsed_data = {"type": "unknown", "items": [], "images": []}

        # Ensure type field exists
        if "type" not in parsed_data:
            parsed_data["type"] = "unknown"

        # Construct Pydantic model
        # Filter out keys that aren't in the model to prevent validation errors
        valid_keys = ParsedContent.model_fields.keys()
        filtered_data = {k: v for k, v in parsed_data.items() if k in valid_keys}
        
        content = ParsedContent(**filtered_data)
        
        logger.info(f"Parsing successful. Type: {content.type}")
        return ParseResponse(ok=True, data=content)

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return ParseResponse(ok=False, error=str(e))

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return ParseResponse(ok=False, error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
