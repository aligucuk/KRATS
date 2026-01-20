# utils/cache.py

import time
from typing import Any, Optional, Callable
from functools import wraps
from collections import OrderedDict
from threading import RLock
from config import settings
from .logger import get_logger

logger = get_logger(__name__)


class LRUCache:
    """Thread-safe LRU (Least Recently Used) cache"""
    
    def __init__(self, max_size: int = None, ttl_seconds: int = None):
        """Initialize cache
        
        Args:
            max_size: Maximum number of items to cache
            ttl_seconds: Time-to-live for cached items in seconds
        """
        self.max_size = max_size or settings.CACHE_MAX_SIZE
        self.ttl_seconds = ttl_seconds or settings.CACHE_TTL_SECONDS
        self.enabled = settings.ENABLE_CACHE
        
        self._cache = OrderedDict()
        self._timestamps = {}
        self._lock = RLock()
        
        logger.info(f"Cache initialized - Max size: {self.max_size}, TTL: {self.ttl_seconds}s")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        if not self.enabled:
            return None
        
        with self._lock:
            if key not in self._cache:
                return None
            
            # Check TTL
            if self._is_expired(key):
                self._delete(key)
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return self._cache[key]
    
    def set(self, key: str, value: Any) -> None:
        """Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
        """
        if not self.enabled:
            return
        
        with self._lock:
            # Update existing key
            if key in self._cache:
                self._cache.move_to_end(key)
            
            # Add new key
            self._cache[key] = value
            self._timestamps[key] = time.time()
            
            # Evict oldest if over max size
            if len(self._cache) > self.max_size:
                oldest_key = next(iter(self._cache))
                self._delete(oldest_key)
    
    def delete(self, key: str) -> bool:
        """Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False if not found
        """
        with self._lock:
            return self._delete(key)
    
    def clear(self) -> None:
        """Clear all cached items"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()
            logger.info("Cache cleared")
    
    def _delete(self, key: str) -> bool:
        """Internal delete method (not thread-safe)"""
        if key in self._cache:
            del self._cache[key]
            del self._timestamps[key]
            return True
        return False
    
    def _is_expired(self, key: str) -> bool:
        """Check if cache entry has expired"""
        if key not in self._timestamps:
            return True
        
        age = time.time() - self._timestamps[key]
        return age > self.ttl_seconds
    
    def cleanup_expired(self) -> int:
        """Remove expired entries
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            expired_keys = [
                key for key in self._cache.keys()
                if self._is_expired(key)
            ]
            
            for key in expired_keys:
                self._delete(key)
            
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        with self._lock:
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'enabled': self.enabled,
                'ttl_seconds': self.ttl_seconds
            }


def cached(ttl_seconds: int = None, key_prefix: str = ""):
    """Decorator for caching function results
    
    Args:
        ttl_seconds: Override default TTL
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable) -> Callable:
        cache = LRUCache(ttl_seconds=ttl_seconds)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return result
            
            # Execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator


# Global cache instance
global_cache = LRUCache()