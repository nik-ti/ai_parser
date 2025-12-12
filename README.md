# AI Parser Microservice

## Overview

The **AI Parser Microservice** is an intelligent web scraping tool that turns any URL into structured data. Unlike traditional scrapers with hardcoded selectors, this service uses a Large Language Model (LLM) to dynamically analyze the HTML structure of a page and generate custom Python code to extract relevant information on the fly.

## Features

- **Dynamic Parsing**: Automatically adapts to different page structures (List pages vs. Detail pages).
- **Rendered HTML**: Uses **Playwright** to fetch pages, ensuring JavaScript-rendered content is captured.
- **Smart Cleaning**: Pre-processes HTML to remove noise (scripts, styles) and optimize for LLM context windows.
- **Sandboxed Execution**: Safely executes the generated parsing code in a restricted environment.
- **Simple API**: Exposes a single `POST /parse` endpoint.

## Technical Architecture

1.  **Fetcher**: Retrieves the fully rendered DOM using a headless browser.
2.  **Cleaner**: Strips unnecessary tags and truncates content using `BeautifulSoup`.
3.  **LLM Client**: Sends the cleaned HTML to OpenAI (GPT-4o) to generate a Python extraction script.
4.  **Sandbox**: Executes the generated script with a limited set of built-ins and variables.

## Tech Stack

-   **Language**: Python 3.8+
-   **Web Framework**: FastAPI
-   **Browser Automation**: Playwright
-   **HTML Parsing**: BeautifulSoup4
-   **LLM Integration**: OpenAI API (gpt-4o-mini)
-   **Data Validation**: Pydantic
-   **Deployment**: Docker & Docker Compose

## Installation & Setup

### Option 1: Docker (Recommended for Production)

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/nik-ti/ai_parser.git
    cd ai_parser
    ```

2.  **Create `.env` file**:
    ```bash
    echo "OPENAI_API_KEY=sk-your-key" > .env
    ```
    
    **Optional - Use OpenRouter**: To use OpenRouter (access to GPT, Claude, Gemini, etc. with one API):
    ```bash
    echo "OPENAI_BASE_URL=https://openrouter.ai/api/v1" >> .env
    ```
    Then use your OpenRouter API key as `OPENAI_API_KEY`.

3.  **Run with Docker Compose**:
    ```bash
    docker compose up -d --build
    ```
    The service runs on `http://localhost:8000`.

### Production Deployment (Caddy / Nginx)
For production, it is recommended to use a reverse proxy. We support **Caddy** out of the box for automatic HTTPS.

1.  **Install Caddy**:
    ```bash
    sudo apt install -y caddy
    ```

2.  **Configure Caddy (`/etc/caddy/Caddyfile`)**:
    ```caddy
    your-domain.com {
        reverse_proxy localhost:8000
    }
    ```

## Usage

### 1. Basic Parsing (Auto-Detect)
The system will automatically detect if the page is a list or article and extract relevant fields.

```bash
curl -X POST "http://localhost:8000/parse" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://news.ycombinator.com"}'
```

### 2. Dynamic Schema (Custom Fields)
You can enforce a specific output structure by providing a `schema_map`.

```bash
curl -X POST "http://localhost:8000/parse" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://news.aibase.com/news/23500",
       "schema_map": {
         "article_title": "The exact headline",
         "author": "Author name or null",
         "summary": "3 bullet points summary",
         "date": "Published date (YYYY-MM-DD)"
       }
     }'
```

### Response Format
```json
{
  "ok": true,
  "data": {
    "article_title": "Example News Item",
    "author": "John Doe",
    "summary": ["Point 1", "Point 2", "Point 3"],
    "date": "2023-10-27"
  }
}
```

## Troubleshooting
- **Playwright Errors**: Ensure your Docker base image matches your `requirements.txt` version (currently `v1.56.0`).
- **Empty Data**: Verify that the page content is not hidden behind a login or captcha. The system is designed for public pages.
