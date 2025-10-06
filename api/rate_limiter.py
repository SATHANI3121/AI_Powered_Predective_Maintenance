"""
Rate limiting utilities for API endpoints
"""

from typing import Dict, Optional
import time
from collections import defaultdict, deque


class RateLimiter:
    """Simple in-memory rate limiter using sliding window"""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, deque] = defaultdict(deque)
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed for the given key"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        requests = self.requests[key]
        while requests and requests[0] <= window_start:
            requests.popleft()
        
        # Check if under limit
        if len(requests) < self.max_requests:
            requests.append(now)
            return True
        
        return False
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for the key"""
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        requests = self.requests[key]
        while requests and requests[0] <= window_start:
            requests.popleft()
        
        return max(0, self.max_requests - len(requests))


# Global rate limiter instance
rate_limiter = RateLimiter()

