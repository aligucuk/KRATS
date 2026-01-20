# utils/rate_limiter.py

import time
from collections import defaultdict
from typing import Dict, Tuple
from threading import Lock
from config import settings
from .logger import get_logger
from .exceptions import RateLimitException

logger = get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self):
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.max_requests = settings.RATE_LIMIT_REQUESTS
        self.window_seconds = settings.RATE_LIMIT_WINDOW_SECONDS
        
        # Storage: {identifier: (count, window_start_time)}
        self.storage: Dict[str, Tuple[int, float]] = defaultdict(lambda: (0, time.time()))
        self.lock = Lock()
    
    def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit
        
        Args:
            identifier: Unique identifier (user_id, ip_address, etc.)
            
        Returns:
            True if within limit, False otherwise
            
        Raises:
            RateLimitException: If rate limit exceeded
        """
        if not self.enabled:
            return True
        
        with self.lock:
            current_time = time.time()
            count, window_start = self.storage[identifier]
            
            # Check if window has expired
            if current_time - window_start >= self.window_seconds:
                # Reset window
                self.storage[identifier] = (1, current_time)
                return True
            
            # Within window
            if count >= self.max_requests:
                logger.warning(f"Rate limit exceeded for {identifier}")
                raise RateLimitException(
                    f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds} seconds"
                )
            
            # Increment counter
            self.storage[identifier] = (count + 1, window_start)
            return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """Get remaining requests in current window
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Number of remaining requests
        """
        if not self.enabled:
            return self.max_requests
        
        with self.lock:
            current_time = time.time()
            count, window_start = self.storage.get(identifier, (0, current_time))
            
            # Window expired
            if current_time - window_start >= self.window_seconds:
                return self.max_requests
            
            return max(0, self.max_requests - count)
    
    def reset(self, identifier: str = None):
        """Reset rate limiter for specific identifier or all
        
        Args:
            identifier: Specific identifier to reset, or None for all
        """
        with self.lock:
            if identifier:
                if identifier in self.storage:
                    del self.storage[identifier]
            else:
                self.storage.clear()
    
    def cleanup_expired(self):
        """Remove expired entries from storage"""
        with self.lock:
            current_time = time.time()
            expired = [
                key for key, (_, window_start) in self.storage.items()
                if current_time - window_start >= self.window_seconds
            ]
            
            for key in expired:
                del self.storage[key]
            
            if expired:
                logger.debug(f"Cleaned up {len(expired)} expired rate limit entries")


# Global instance
rate_limiter = RateLimiter()