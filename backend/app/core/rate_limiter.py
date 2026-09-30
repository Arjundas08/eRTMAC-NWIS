"""
NWIS Rate Limiter — Production Traffic Management (Phase 09)

Provides in-memory sliding-window rate limiting for API endpoints.
Designed for single-instance deployment (eRTMAC rig-side server).
For multi-instance deployments, replace with Redis-backed limiter.

ENGINEERING NOTES:
- Uses a per-IP sliding window counter with configurable window and max requests.
- Thread-safe via threading locks.
- Automatically evicts expired entries to prevent memory leaks.
- Returns standardized 429 responses with Retry-After header.
"""

import time
import threading
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class SlidingWindowRateLimiter:
    """
    Thread-safe sliding-window rate limiter.
    Tracks request timestamps per client IP and enforces configurable limits.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Args:
            max_requests: Maximum allowed requests per window per client.
            window_seconds: Duration of the sliding window in seconds.
        """
        if max_requests < 1:
            raise ValueError("max_requests must be >= 1")
        if window_seconds < 1:
            raise ValueError("window_seconds must be >= 1")

        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()
        self._last_cleanup = time.monotonic()
        self._cleanup_interval = max(window_seconds * 2, 120)  # Cleanup every 2x window or 2 minutes

    def is_allowed(self, client_id: str) -> Tuple[bool, int, int]:
        """
        Check if a request from client_id is allowed.

        Returns:
            Tuple of (allowed: bool, remaining: int, retry_after: int)
        """
        now = time.monotonic()

        with self._lock:
            # Periodic cleanup of expired entries
            if now - self._last_cleanup > self._cleanup_interval:
                self._cleanup(now)

            # Get request timestamps for this client
            timestamps = self._requests[client_id]

            # Remove expired timestamps (outside the window)
            cutoff = now - self.window_seconds
            while timestamps and timestamps[0] < cutoff:
                timestamps.pop(0)

            current_count = len(timestamps)

            if current_count >= self.max_requests:
                # Rate limit exceeded
                retry_after = int(timestamps[0] - cutoff) + 1 if timestamps else self.window_seconds
                return False, 0, max(1, retry_after)

            # Allow the request
            timestamps.append(now)
            remaining = self.max_requests - len(timestamps)
            return True, remaining, 0

    def _cleanup(self, now: float):
        """Remove all entries with no recent requests. Called under lock."""
        cutoff = now - self.window_seconds
        expired_keys = [
            key for key, timestamps in self._requests.items()
            if not timestamps or timestamps[-1] < cutoff
        ]
        for key in expired_keys:
            del self._requests[key]
        self._last_cleanup = now


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware that enforces rate limiting on all API endpoints.
    Exempts health check and documentation endpoints.
    """

    # Endpoints exempt from rate limiting
    EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}

    def __init__(self, app, max_requests: int = 200, window_seconds: int = 60):
        super().__init__(app)
        self.limiter = SlidingWindowRateLimiter(
            max_requests=max_requests,
            window_seconds=window_seconds
        )

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        # Skip rate limiting for static assets
        if request.url.path.endswith(('.html', '.css', '.js', '.png', '.jpg', '.ico', '.svg', '.woff2')):
            return await call_next(request)

        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"

        allowed, remaining, retry_after = self.limiter.is_allowed(client_ip)

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "detail": f"Too many requests. Maximum {self.limiter.max_requests} requests per {self.limiter.window_seconds}s window.",
                    "retry_after_seconds": retry_after
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(retry_after)
                }
            )

        # Process the request and add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
