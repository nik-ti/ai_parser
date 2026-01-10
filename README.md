# AI Parser Microservice

A high-performance, intelligent web scraper and parser powered by Playwright and OpenAI.

## Features

-   **Intelligent Parsing**: Uses LLMs to understand page structure and extract data dynamically.
-   **Universal Support**: Handles single articles (Detail Pages) and feeds/listings (List Pages).
-   **High Performance**: 
    -   Persistent browser context (no startup overhead).
    -   Resource blocking (images/fonts/media) for fast crawling.
    -   Markdown conversion for efficient LLM processing.
-   **Content-Aware Caching**: 
    -   Always fetches fresh HTML to detect updates.
    -   Uses MD5 content hashing to skip AI processing if content hasn't changed.
    -   1-hour TTL with automatic re-extraction on parsing errors or bot-blockers.
-   **Production Ready**:
    -   Unified Pydantic Schema.
    -   Concurrency limits and safe resource management.
    -   Dockerized with FastAPI.

## Schema

The API returns a unified structure for all responses:

```json
{
  "ok": true,
  "data": {
    "type": "detail", // or "list"
    "title": "Page Title",
    "summary": "Brief summary",
    "full_text": "Full article content (markdown/text)",
    "published_date": "YYYY-MM-DD",
    "images": [
      {
        "url": "https://example.com/image.jpg",
        "alt": "Image Alt Text",
        "description": "Inferred description"
      }
    ],
    "videos": [
      "https://youtube.com/watch?v=...",
      "https://example.com/video.mp4"
    ],
    "items": [] // Populated only for list pages
  }
}
```

## Setup

1.  **Clone**:
    ```bash
    git clone https://github.com/nik-ti/ai_parser.git
    cd ai_parser
    ```

2.  **Env**:
    Create `.env`:
    ```
    OPENAI_API_KEY=sk-...
    OPENAI_BASE_URL=https://openrouter.ai/api/v1 (Optional)
    ```

3.  **Run**:
    ```bash
    docker compose up -d --build
    ```

4.  **Usage**:
    ```bash
    curl -X POST "http://localhost:8000/parse" \
         -H "Content-Type: application/json" \
         -d '{"url": "https://example.com"}'
    ```
