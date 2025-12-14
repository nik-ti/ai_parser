import asyncio
import json
import logging
import os
from datetime import datetime
from main import app  # Import app to use the same logic, or import specific functions
from models import UrlRequest, ParseResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the logic directly to bypass running the uvicorn server for testing
from main import parse_url

async def run_test_suite(input_file: str = "test_urls.txt", output_file: str = "test_report.json"):
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} not found.")
        return

    with open(input_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    results = []
    success_count = 0
    total_count = len(urls)

    logger.info(f"Starting test suite with {total_count} URLs...")

    for i, url in enumerate(urls):
        logger.info(f"[{i+1}/{total_count}] Testing: {url}")
        
        start_time = datetime.now()
        try:
            # Create request object
            request = UrlRequest(url=url)
            
            # Call the processing logic directly
            response = await parse_url(request)
            
            duration = (datetime.now() - start_time).total_seconds()
            
            result_entry = {
                "url": url,
                "status": "success" if response.ok else "failed",
                "page_type": response.page_type,
                "data_length": len(response.data) if response.data else 0,
                "duration": duration,
                "error": response.error,
                "data": response.data # Include data for manual inspection if needed
            }
            
            if response.ok and response.data:
                # Basic validation: check if we got something useful
                 # If list, check if > 0 items. If detail, check if title/full_text exists.
                if isinstance(response.data, list) and len(response.data) > 0:
                     success_count += 1
                else:
                     result_entry["status"] = "empty_data"
            
            results.append(result_entry)
            
        except Exception as e:
            logger.error(f"Exception validation {url}: {e}")
            results.append({
                "url": url,
                "status": "exception",
                "error": str(e),
                "duration": (datetime.now() - start_time).total_seconds()
            })

    # Save detailed report
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    # Summary
    success_rate = (success_count / total_count) * 100
    summary = f"\nTest Suite Completed.\nTotal: {total_count}\nSuccess: {success_count}\nRate: {success_rate:.2f}%\nReport saved to {output_file}"
    logger.info(summary)
    
    # Also write summary to a markdown file
    with open("test_summary.md", "w") as f:
        f.write(f"# Test Suite Summary\n\n")
        f.write(f"- **Total URLs**: {total_count}\n")
        f.write(f"- **Success**: {success_count}\n")
        f.write(f"- **Success Rate**: {success_rate:.2f}%\n\n")
        f.write("## Failures/Empty\n")
        for res in results:
            if res["status"] != "success":
                f.write(f"- {res['url']} ({res['status']}): {res.get('error', 'No data')}\n")

if __name__ == "__main__":
    asyncio.run(run_test_suite())
