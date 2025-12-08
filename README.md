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
-   **LLM Integration**: OpenAI API
-   **Data Validation**: Pydantic

## Installation & Setup

1.  **Clone the repository** and navigate to the folder:
    ```bash
    cd ai_parser
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Playwright browsers**:
    ```bash
    playwright install
    ```

4.  **Set your OpenAI API Key**:
    ```bash
    export OPENAI_API_KEY="your-api-key-here"
    ```

## Usage

### Start the Server
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
