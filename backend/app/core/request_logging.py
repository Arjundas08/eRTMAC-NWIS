"""
NWIS Request Logging Middleware — Structured Access Logging (Phase 09)

Provides structured JSON-formatted request logging for:
- Compliance auditing (who accessed what, when)
- Performance monitoring (latency tracking)
- Anomaly detection (unusual access patterns)
- Debugging (request/response correlation via request IDs)

All logs go to Python's standard logging framework.
In production, configure a log handler to ship to ELK/Splunk/CloudWatch.
"""

import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger("nwis.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every HTTP request with structured metadata.
    Assigns a unique request ID for correlation across services.
    """

    # Paths that produce high-volume, low-value logs
    QUIET_PATHS = {"/health", "/favicon.ico"}

    async def dispatch(self, request: Request, call_next):
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:12]
        start_time = time.monotonic()

        # Extract client info
        client_ip = request.client.host if request.client else "unknown"
        method = request.method
        path = request.url.path
        query = str(request.url.query) if request.url.query else ""

        # Attach request_id to request state for downstream use
        request.state.request_id = request_id

        try:
            response = await call_next(request)
            latency_ms = (time.monotonic() - start_time) * 1000
            status_code = response.status_code

            # Add request ID to response headers for client-side correlation
            response.headers["X-Request-ID"] = request_id

            # Log at appropriate level
            if path not in self.QUIET_PATHS:
                log_level = logging.WARNING if status_code >= 400 else logging.INFO
                logger.log(
                    log_level,
                    "request_id=%s method=%s path=%s query=%s status=%d latency_ms=%.1f client=%s",
                    request_id, method, path, query, status_code, latency_ms, client_ip
                )

            return response

        except Exception as exc:
            latency_ms = (time.monotonic() - start_time) * 1000
            logger.error(
                "request_id=%s method=%s path=%s status=500 latency_ms=%.1f client=%s error=%s",
                request_id, method, path, latency_ms, client_ip, str(exc)
            )
            raise
