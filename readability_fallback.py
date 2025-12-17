"""
Fallback content extraction using readability-lxml.
Used when LLM extraction fails or returns minimal data.
"""
from readability import Document
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

def extract_with_readability(html_content: str, url: str) -> dict:
    """
    Extract article content using readability algorithm.
    Returns basic structured data as fallback.
    """
    try:
        doc = Document(html_content)
        
        # Get cleaned HTML
        article_html = doc.summary()
        title = doc.title()
        
        # Parse with BeautifulSoup to extract text
        soup = BeautifulSoup(article_html, 'html.parser')
        
        # Extract text
        text = soup.get_text(separator='\n', strip=True)
        
        # Extract images
        images = []
        for img in soup.find_all('img'):
            img_url = img.get('src', '')
            if img_url and not img_url.startswith('data:'):
                # Make absolute URL
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                elif img_url.startswith('/'):
                    from urllib.parse import urljoin
                    img_url = urljoin(url, img_url)
                    
                images.append({
                    "url": img_url,
                    "alt": img.get('alt', ''),
                    "description": img.get('title', img.get('alt', ''))
                })
        
        return {
            "type": "detail",
            "title": title or "Untitled",
            "summary": text[:200] + "..." if len(text) > 200 else text,
            "full_text": text,
            "published_date": None,
            "images": images[:5],  # Limit to 5 images
            "items": []
        }
        
    except Exception as e:
        logger.error(f"Readability extraction failed: {e}")
        return {
            "type": "unknown",
            "title": "Extraction failed",
            "summary": str(e),
            "full_text": None,
            "published_date": None,
            "images": [],
            "items": []
        }
