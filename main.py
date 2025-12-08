from fastapi import FastAPI, HTTPException
from models import UrlRequest, ParseResponse
from fetcher import fetch_page_html
from cleaner import clean_html
from llm_client import generate_parsing_code
from sandbox import execute_parsing_code
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Parser Microservice")

@app.post("/parse", response_model=ParseResponse)
async def parse_url(request: UrlRequest):
    logger.info(f"Received request to parse: {request.url}")
    
    try:
        # 1. Fetch HTML
        logger.info("Fetching HTML...")
        raw_html = await fetch_page_html(request.url)
        
        # 2. Clean and Truncate
        logger.info("Cleaning HTML...")
        cleaned_html = clean_html(raw_html)
        
        # 3. Generate Code via LLM
        logger.info("Generating parsing code...")
        parsing_code = await generate_parsing_code(cleaned_html)
        logger.info(f"Generated Code:\n{parsing_code}")
        
        # 4. Execute Code in Sandbox
        logger.info("Executing code...")
        parsed_data = execute_parsing_code(parsing_code, cleaned_html)
        
        logger.info("Parsing successful.")
        return ParseResponse(ok=True, data=parsed_data)

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return ParseResponse(ok=False, error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
