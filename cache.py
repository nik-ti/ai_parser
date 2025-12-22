"""
Simple in-memory cache for parsed content.
Caches successful responses for 1 hour to reduce LLM costs and improve speed.
"""
import time
from typing import Optional, Dict, Any
import hashlib
import json

class ParseCache:
    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._ttl = ttl_seconds
    
    def _make_key(self, url: str, page_type: Optional[str] = None) -> str:
        """Generate cache key from URL and optional page_type."""
        key_data = f"{url}:{page_type or 'auto'}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_valid_response(self, data: Any) -> bool:
        """Check if cached response is valid (not empty/null/error)."""
        if not data:
            return False
        
        # Check if it's a successful response with actual data
        if isinstance(data, dict):
            parsed_data = data.get('data')
            if not parsed_data:
                return False
            
            # Check if the parsed content has meaningful data
            if isinstance(parsed_data, dict):
                # Invalid if type is unknown and no content
                if parsed_data.get('type') == 'unknown' and not parsed_data.get('full_text'):
                    return False
                
                # Invalid if title is an error message
                title = parsed_data.get('title', '')
                if any(err in title.lower() for err in ['error', 'failed', 'forbidden', '403', '404']):
                    return False
                
                return True
        
        return False
    
    def get(self, url: str, page_type: Optional[str] = None) -> Optional[Any]:
        """Get cached response if valid and not expired."""
        key = self._make_key(url, page_type)
        
        if key in self._cache:
            data, timestamp = self._cache[key]
            
            # Check if expired
            if time.time() - timestamp > self._ttl:
                del self._cache[key]
                return None
            
            # Check if valid response
            if self._is_valid_response(data):
                return data
            else:
                # Invalid cached response, remove it
                del self._cache[key]
                return None
        
        return None
    
    def set(self, url: str, data: Any, page_type: Optional[str] = None):
        """Cache response only if it's valid."""
        if self._is_valid_response(data):
            key = self._make_key(url, page_type)
            self._cache[key] = (data, time.time())
    
    def clear(self):
        """Clear all cached entries."""
        self._cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries from cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if current_time - timestamp > self._ttl
        ]
        for key in expired_keys:
            del self._cache[key]
    
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
