import asyncio
import aiohttp
import time
import json
import os

URLS_FILE = "urls_to_test.txt"
API_URL = "http://localhost:8000/parse"
OUTPUT_FILE = "test_results.json"

async def test_url(session, url):
    start_time = time.time()
    try:
        print(f"Testing {url}...")
        async with session.post(API_URL, json={"url": url.strip()}, timeout=60) as response:
            data = await response.json()
            duration = time.time() - start_time
            print(f"Finished {url} in {duration:.2f}s. Status: {response.status}")
            return {
                "url": url,
                "status": response.status,
                "duration": duration,
                "result": data
            }
    except Exception as e:
        duration = time.time() - start_time
        print(f"Failed {url} in {duration:.2f}s: {e}")
        return {
            "url": url,
            "status": "error",
            "duration": duration,
            "error": str(e)
        }

async def main():
    if not os.path.exists(URLS_FILE):
        print(f"File {URLS_FILE} not found.")
        return

    with open(URLS_FILE, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"Found {len(urls)} URLs to test.")
    
    # Process in chunks to avoid overwhelming the local machine (server limits concurrency but still)
    results = []
    chunk_size = 5
    
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(urls), chunk_size):
            chunk = urls[i:i + chunk_size]
            print(f"Processing chunk {i}-{i+chunk_size}...")
            tasks = [test_url(session, url) for url in chunk]
            chunk_results = await asyncio.gather(*tasks)
            results.extend(chunk_results)
            
    with open(OUTPUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
        
    # Stats
    success_count = sum(1 for r in results if r.get("status") == 200 and r.get("result", {}).get("ok"))
    avg_duration = sum(r["duration"] for r in results) / len(results) if results else 0
    print(f"\nTest Complete.")
    print(f"Total: {len(results)}")
    print(f"Success: {success_count}")
    print(f"Avg Duration: {avg_duration:.2f}s")
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(main())
