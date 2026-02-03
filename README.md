# AI Parser Microservice

A high-performance, intelligent web secondary-processing service that transforms any raw webpage into structured JSON. It handles JavaScript-heavy sites, cookie banners, and bot-detection challenges using an AI-native approach to content extraction.

---

## 🏗 The Parsing Pipeline: Step-by-Step

When you send a URL to the `/parse` endpoint, the system executes the following deterministic pipeline:

### 1. Advanced Fetching (`fetcher.py`)
- **Engine**: Uses **Playwright** with a persistent Chromium instance.
- **Speed Optimization**: Reuses the same browser context across requests to eliminate the 2-3s cold-start overhead of launching a browser.
- **Resource Blocking**: To save bandwidth and time, it automatically blocks images, fonts, stylesheets, and tracking scripts (3rd party analytics).
- **Navigation**: Waits for the network to be "idle" for at least 500ms to ensure client-side rendered content (React/Vue/Next.js) is fully loaded.

### 2. Semantic Cleaning (`cleaner.py`)
- **Raw to Markdown**: The massive HTML bloat of a modern webpage (often 500KB+) is converted into a compact, semantic **Markdown** string (usually 5-10KB).
- **Noise Removal**: It strips out `<script>`, `<style>`, `<nav>`, `<header>`, and `<footer>` tags that contain irrelevant navigation links.
- **Content Preservation**: It carefully keeps `<iframe>` (for videos), `<img>` (for images), and structure-rich tags like `<h1>-<h6>`, `<ul>`, and `<a>`.

### 3. Content-Aware Caching Check (`cache.py`)
- **The Hash**: We generate a unique **MD5 Fingerprint** of the cleaned Markdown content.
- **The Shortcut**: We look up this fingerprint in our persistent cache.
  - **HIT**: If the hash matches a previous entry, we **immediately return the stored JSON**. We NEVER make an AI call if the content results in the same fingerprint.
  - **MISS**: If the hash is new, the pipeline proceeds to the expensive AI step.

### 4. AI-Native Extraction (`llm_client.py`)
- **The Brain**: Markdown is sent to **GPT-4o-mini** (via OpenRouter) with a specialized system prompt.
- **JSON Mode**: The LLM is forced into `JSON Mode` to ensure the response is always a valid table/object.
- **Field Awareness**: The AI is instructed to distinguish between "Detail" pages (articles) and "List" pages (news feeds). It intelligently selects the right fields based on the page type.

### 5. Validation & Survival Fallback (`readability_fallback.py`)
- **Sanity Check**: We check if the AI's result is "trash" (e.g., if it hit a "403 Forbidden" page or a Cloudflare "Just a moment" shield).
- **Classic Algorithm**: If the AI output is empty or errorv-prone, we run a classic **Readability** algorithm (standard lxml-based content extraction) as a safety net.

---

## 🤖 How AI is Used Exactly

Unlike traditional "Regex" or "Selector-based" scrapers that break when a website changes its design, our service uses AI to **understand intent**:

1.  **Page Type Detection**: The AI looks at the structure and decides: "Is this a single story (Detail) or a list of many stories (List)?"
2.  **Schema Enforcement**: It maps unstructured website text into our strict 8-field schema (`title`, `summary`, `full_text`, etc.).
3.  **URL Normalization**: The AI identifies relative image/video paths and converts them into absolute URLs based on the base domain.
4.  **Content Summarization**: It generates a concise 1-2 sentence summary of the page, even if the site doesn't provide a meta-description.

---

## 💾 Deep-Dive: Caching Logic

The caching system is designed to be **Cost-First**. It is the primary shield that keeps your LLM bill low.

### The Problem with URL Caching
If you scrape a URL like `https://techcrunch.com/news` every 5 minutes:
- A regular URL cache would give you stale news for 1 hour.
- Disabling the cache would cost you an AI call every 5 minutes ($$$).

### Our Solution: Content Hashing
1.  **Fetch HTML**: We fetch the HTML every time (this is free/cheap).
2.  **Compare Hash**: We compare the current Markdown hash with the one in the database.
3.  **Conditional AI**: 
    - If the hash is the same, we know **nothing** on the page has changed. **We skip the AI and return the cache.**
    - Only when the hash changes (e.g., a new article is posted) do we pay for an AI call.
4.  **Persistence**: The cache is saved to a local file `cache_data.json` every 10 parses and is mounted via a Docker volume so it survives server restarts.

---

## 📊 Unified Response Schema

The API returns a unified structure for all responses:

```json
{
  "ok": true,
  "data": {
    "type": "detail",           // "detail" (article) or "list" (news feed/catalog)
    "title": "Main Headline",
    "summary": "1-2 sentence summary",
    "full_text": "Markdown-formatted body text (detail only)",
    "published_date": "YYYY-MM-DD",
    "images": [
      {
        "url": "https://...",
        "alt": "Alt text",
        "description": "Context provided by AI"
      }
    ],
    "videos": ["https://youtube.com/watch?v=...", "https://...mp4"],
    "items": [                  // Populated only for "list" pages
      {
        "title": "Entry Title",
        "url": "Entry Link",
        "snippet": "Short summary",
        "published_date": "YYYY-MM-DD"
      }
    ]
  },
  "error": null
}
```

---

## 🚀 Setup & Deployment

### Environment Variables
Create a `.env` file in the root:
```env
OPENAI_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
```

### Docker Deployment
```bash
docker compose up -d --build
```
This will mount `./cache_data.json` as a volume to ensure cache persistence.

---

## 🛠 Development & Testing
-   **`GET /cache/stats`**: Shows the total number of cached entries and if persistence is active.
-   **`POST /cache/clear`**: Wipes the entire database to force-refresh all content.
-   **`test_service.py`**: A full suite of integration tests.
-   **Timeout**: The system enforces a **90s global timeout** for every request to prevent hanging.
