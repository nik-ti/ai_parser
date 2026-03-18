"""
Content-aware cache for parsed content using SQLite.
Caches LLM results by content hash to save costs while ensuring fresh data is always fetched.
Uses aiosqlite for non-blocking persistence.
"""
import time
import hashlib
import logging
import json
import os
import asyncio
import aiosqlite
from typing import Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

DB_FILE = Path("/app/cache_data.sqlite")
OLD_CACHE_FILE = Path("/app/cache_data.json")

class ParseCache:
    def __init__(self, ttl_seconds: int = 3600):
        self._ttl = ttl_seconds
        self._db_initialized = False

    async def _ensure_db(self):
        """Ensure the database and table exist. Handles migration from JSON."""
        if self._db_initialized:
            return
        
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    timestamp REAL
                )
            """)
            await db.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON cache(timestamp)")
            await db.commit()
            
            # Migration from old JSON cache
            if OLD_CACHE_FILE.exists():
                logger.info("Migrating old JSON cache to SQLite...")
                try:
                    with open(OLD_CACHE_FILE, 'r') as f:
                        old_data = json.load(f)
                    
                    entries = []
                    current_time = time.time()
                    for key, val_stamp in old_data.items():
                        # Handle both [value, timestamp] and (value, timestamp) formats
                        if isinstance(val_stamp, (list, tuple)) and len(val_stamp) == 2:
                            value, timestamp = val_stamp
                            if current_time - timestamp <= self._ttl:
                                entries.append((key, json.dumps(value), timestamp))
                    
                    if entries:
                        await db.executemany(
                            "INSERT OR IGNORE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
                            entries
                        )
                        await db.commit()
                        logger.info(f"Successfully migrated {len(entries)} entries")
                    
                    # Rename old file instead of deleting to be safe
                    OLD_CACHE_FILE.rename(OLD_CACHE_FILE.with_suffix(".json.bak"))
                except Exception as e:
                    logger.error(f"Migration failed: {e}")
                    
        self._db_initialized = True

    def _make_hash(self, content: str) -> str:
        """Generate a stable hash for the markdown content."""
        return hashlib.md5(content.encode('utf-8')).hexdigest()

    def _is_valid_response(self, data: Any) -> bool:
        """Check if cached response is valid (not empty/null/error)."""
        if not data:
            return False
        
        if isinstance(data, dict):
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

    async def get(self, content: str) -> Optional[Any]:
        """Get cached response if content hash matches and not expired."""
        await self._ensure_db()
        content_hash = self._make_hash(content)
        
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT value, timestamp FROM cache WHERE key = ?", (content_hash,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    value_json, timestamp = row
                    # Check if expired
                    if time.time() - timestamp > self._ttl:
                        await db.execute("DELETE FROM cache WHERE key = ?", (content_hash,))
                        await db.commit()
                        return None
                    
                    try:
                        data = json.loads(value_json)
                        if self._is_valid_response(data):
                            return data
                        else:
                            await db.execute("DELETE FROM cache WHERE key = ?", (content_hash,))
                            await db.commit()
                            return None
                    except json.JSONDecodeError:
                        return None
        
        return None

    async def set(self, content: str, data: Any):
        """Cache response keyed by content hash."""
        if not content:
            return
            
        await self._ensure_db()
        
        if self._is_valid_response(data):
            content_hash = self._make_hash(content)
            async with aiosqlite.connect(DB_FILE) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
                    (content_hash, json.dumps(data), time.time())
                )
                
                # Cleanup expired entries occasionally (1% chance per set)
                import random
                if random.random() < 0.01:
                    await db.execute("DELETE FROM cache WHERE timestamp < ?", (time.time() - self._ttl,))
                
                await db.commit()

    async def clear(self):
        """Clear all cached entries."""
        await self._ensure_db()
        async with aiosqlite.connect(DB_FILE) as db:
            await db.execute("DELETE FROM cache")
            await db.commit()
        logger.info("Cache cleared")

    async def stats(self) -> dict:
        """Get cache statistics."""
        await self._ensure_db()
        async with aiosqlite.connect(DB_FILE) as db:
            async with db.execute("SELECT COUNT(*) FROM cache") as cursor:
                count = (await cursor.fetchone())[0]
        return {
            "total_entries": count,
            "ttl_seconds": self._ttl,
            "persistent": True
        }

# Global cache instance
_cache = ParseCache(ttl_seconds=3600)  # 1 hour TTL

def get_cache() -> ParseCache:
    """Get the global cache instance."""
    return _cache

# Global cache instance
_cache = ParseCache(ttl_seconds=3600)  # 1 hour TTL

def get_cache() -> ParseCache:
    """Get the global cache instance."""
    return _cache
