from bs4 import BeautifulSoup, Comment
from markdownify import markdownify as md

def clean_html(html_content: str, max_length: int = 100000) -> str:
    """
    Cleans the HTML by removing garbage and converting to Markdown.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove unwanted tags
    for tag in soup(["script", "style", "svg", "noscript", "iframe", "object", "embed", "meta", "link"]):
        tag.decompose()
        
    # Remove common clutter by ID/Class (Aggressive Cleaning)
    clutter_selectors = [
        "#menu", "#nav", "#header", "#sidebar", "#sidebar_right", "#header_boundary", 
        ".hidden", ".modal", ".popup", ".cookie", ".ad", ".advertisement", ".social-share",
        "div[id*='menu']", "div[class*='menu']", "div[id*='nav']", "div[class*='nav']",
        "header", "footer", "nav", "aside"
    ]
    for selector in clutter_selectors:
        for tag in soup.select(selector):
            tag.decompose()

    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Convert to Markdown (strip=['a'] means we keep links, but we might want to keep images too)
    # We want to keep: a, img, h1-h6, p, ul, ol, li, table, pre, code
    # markdownify defaults are pretty good.
    cleaned_md = md(str(soup), heading_style="ATX", strip=["script", "style"])

    # Simple truncation
    if len(cleaned_md) > max_length:
        cleaned_md = cleaned_md[:max_length] + "\n...(truncated)"

    return cleaned_md
