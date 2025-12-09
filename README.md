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

3.  **Run with Docker Compose**:
    ```bash
    docker compose up -d --build
    ```
    The service runs on `http://localhost:8000`.

### Option 2: Local Python Setup

1.  **Clone and install dependencies**:
    ```bash
    git clone https://github.com/nik-ti/ai_parser.git
    cd ai_parser
    pip install -r requirements.txt
    playwright install
    ```

2.  **Set API Key**:
    Create a `.env` file with `OPENAI_API_KEY=sk-your-key`.

3.  **Start the Server**:
    ```bash
    uvicorn main:app --reload
    ```

### Send a Request
```bash
curl -X POST "http://localhost:8000/parse" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://news.ycombinator.com"}'
```

### Response Format
```json
{
  "ok": true,
  "data": [
    {
      "title": "Example News Item",
      "url": "https://example.com/item",
      "snippet": "50 points by user 1 hour ago"
    },
    ...
  ]
}
```
