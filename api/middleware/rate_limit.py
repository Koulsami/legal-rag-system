"""
Rate Limiting Middleware
Implements 100 req/min limit as per patent specifications
"""
from fastapi import Request, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
import time


# Create limiter
limiter = Limiter(key_func=get_remote_address)


def get_api_key_from_request(request: Request) -> str:
    """Extract API key from request for rate limiting"""
    api_key = request.headers.get("X-API-Key", "anonymous")
    return api_key


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware
    
    Limits requests per API key to prevent abuse
    """
    
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}  # {api_key: [(timestamp, count), ...]}
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting for health check
        if request.url.path == "/api/health":
            return await call_next(request)
        
        # Get API key
        api_key = request.headers.get("X-API-Key", "anonymous")
        current_time = time.time()
        
        # Clean old entries
        self._clean_old_entries(api_key, current_time)
        
        # Check rate limit
        if self._is_rate_limited(api_key, current_time):
            return Response(
                content='{"error": "Rate limit exceeded", "detail": "Too many requests. Limit: %d per %d seconds"}' 
                        % (self.max_requests, self.window_seconds),
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(current_time + self.window_seconds))
                }
            )
        
        # Record request
        self._record_request(api_key, current_time)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self._get_remaining(api_key, current_time)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))
        
        return response
    
    def _clean_old_entries(self, api_key: str, current_time: float):
        """Remove entries outside the time window"""
        if api_key not in self.request_counts:
            return
        
        cutoff_time = current_time - self.window_seconds
        self.request_counts[api_key] = [
            (ts, count) for ts, count in self.request_counts[api_key]
            if ts > cutoff_time
        ]
    
    def _is_rate_limited(self, api_key: str, current_time: float) -> bool:
        """Check if API key has exceeded rate limit"""
        if api_key not in self.request_counts:
            return False
        
        cutoff_time = current_time - self.window_seconds
        recent_requests = sum(
            count for ts, count in self.request_counts[api_key]
            if ts > cutoff_time
        )
        
        return recent_requests >= self.max_requests
    
    def _record_request(self, api_key: str, current_time: float):
        """Record a request for rate limiting"""
        if api_key not in self.request_counts:
            self.request_counts[api_key] = []
        
        self.request_counts[api_key].append((current_time, 1))
    
    def _get_remaining(self, api_key: str, current_time: float) -> int:
        """Get remaining requests in current window"""
        if api_key not in self.request_counts:
            return self.max_requests
        
        cutoff_time = current_time - self.window_seconds
        recent_requests = sum(
            count for ts, count in self.request_counts[api_key]
            if ts > cutoff_time
        )
        
        return max(0, self.max_requests - recent_requests)
