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
        parsing_code = await generate_parsing_code(cleaned_html, schema_map=request.schema_map, page_type=request.page_type)
        logger.info(f"Generated Code:\n{parsing_code}")
        
        # 4. Execute Code in Sandbox
        logger.info("Executing code...")
        parsed_data = execute_parsing_code(parsing_code, cleaned_html, base_url=request.url)
        
        # 5. Ensure data is always an array and determine page_type
        if not isinstance(parsed_data, list):
            parsed_data = [parsed_data]
        
        # 6. Validate and clean garbage extractions
        # Detect page type first so we know what validation rules to apply
        detected_page_type = request.page_type
        if not detected_page_type:
             if len(parsed_data) > 1:
                detected_page_type = "list"
             elif len(parsed_data) == 1 and isinstance(parsed_data[0], dict):
                has_detail_fields = any(key in parsed_data[0] for key in ["full_text", "summary"])
                detected_page_type = "detail" if has_detail_fields else "list"
             else:
                detected_page_type = "list"

        for item in parsed_data:
            if isinstance(item, dict):
                # ONLY validate full_text if it's a DETAIL page
                if detected_page_type == "detail" and "full_text" in item:
                    text = item.get("full_text", "")
                    # Remove if it's just whitespace, repeated chars, or very short
                    if len(text.strip()) < 50 or len(set(text.replace("\n", "").replace(" ", ""))) < 5:
                        logger.warning(f"Detected garbage full_text: {text[:50]}... Clearing fields.")
                        item["full_text"] = ""
                        item["summary"] = ""
                        item["images"] = []
                        item["links"] = []
                
                # Inject URL for detail pages (ensure it's always present)
                if detected_page_type == "detail" and ("full_text" in item or "summary" in item):
                     if "url" not in item or not item["url"]:
                        item["url"] = request.url

        # Check if we ended up with empty data after cleaning
        if detected_page_type == "detail" and len(parsed_data) == 1:
             # If detail page became empty/invalid, we still return the structure but maybe flag it?
             # For now, we return what we have. API consumer checks for empty fields.
             pass
        
        logger.info(f"Parsing successful. Type: {detected_page_type}")
        return ParseResponse(ok=True, page_type=detected_page_type, data=parsed_data)

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return ParseResponse(ok=False, error=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
