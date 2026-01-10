"""
Content-aware cache for parsed content.
Caches LLM results by content hash to save costs while ensuring fresh data is always fetched.
"""
import time
import hashlib
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ParseCache:
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds
    
    def _make_hash(self, content: str) -> str:
        """Generate a stable hash for the markdown content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def _is_valid_response(self, data: Any) -> bool:
        """Check if cached response is valid (not empty/null/error)."""
        if not data:
            return False
        
        if isinstance(data, dict):
            # If it's the wrapped ParseResponse format
            parsed_data = data.get('data') if 'data' in data else data
            
            if not parsed_data:
                return False
                
            if isinstance(parsed_data, dict):
                # Invalid if type is unknown and no content
                if parsed_data.get('type') == 'unknown' and not (parsed_data.get('full_text') or parsed_data.get('items')):
                    return False
                
                # Invalid if title is an error message or generic blocker
                title = parsed_data.get('title', '') or ''
                title_lower = title.lower()
                error_keywords = [
                    'error', 'failed', 'forbidden', '403', '404', '500', '502', '503', 
                    'access denied', 'security challenge', 'bot detection', 'captcha', 
                    'just a moment', 'checking your browser', 'enable javascript',
                    'attention required', 'not available'
                ]
                if any(err in title_lower for err in error_keywords):
                    return False
                
                return True
        
        return False
    
    def get(self, content: str) -> Optional[Any]:
        """Get cached response if content hash matches and not expired."""
        content_hash = self._make_hash(content)
        
        if content_hash in self._cache:
            data, timestamp = self._cache[content_hash]
            
            # Check if expired
            if time.time() - timestamp > self._ttl:
                del self._cache[content_hash]
                logger.info("Cache entry expired")
                return None
            
            # Check if valid response
            if self._is_valid_response(data):
                logger.info(f"Cache HIT for content hash {content_hash}")
                return data
            else:
                del self._cache[content_hash]
                return None
        
        return None
    
    def set(self, content: str, data: Any):
        """Cache response keyed by content hash."""
        if not content:
            return
            
        if self._is_valid_response(data):
            content_hash = self._make_hash(content)
            self._cache[content_hash] = (data, time.time())
            logger.info(f"Cached result for content hash {content_hash}")
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
        logger.info("Cache cleared")
    
    def stats(self) -> dict:
        """Get cache statistics."""
        return {
            "total_entries": len(self._cache),
            "ttl_seconds": self._ttl
        }

# Global cache instance
_cache = ParseCache(ttl_seconds=3600)  # 1 hour TTL

def get_cache() -> ParseCache:
    """Get the global cache instance."""
    return _cache
