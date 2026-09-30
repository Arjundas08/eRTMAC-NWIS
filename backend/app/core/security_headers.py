"""
NWIS Security Headers Middleware — Production HTTP Hardening (Phase 09)

Adds security headers to all HTTP responses following OWASP best practices.
These headers protect against:
- XSS attacks (Content-Security-Policy, X-XSS-Protection)
- Clickjacking (X-Frame-Options)
- MIME-type sniffing (X-Content-Type-Options)
- Information disclosure (Server header suppression, Referrer-Policy)
- Transport layer attacks (Strict-Transport-Security for HTTPS deployments)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Injects production security headers into every HTTP response.
    Configurable for development vs. production environments.
    """

    def __init__(self, app, environment: str = "development"):
        super().__init__(app)
        self.environment = environment

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Basic XSS protection (legacy browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Restrict referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy — restrict browser features
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=()"
        )

        # Suppress server identity
        response.headers["Server"] = "NWIS"

        # Content Security Policy (relaxed for development, strict for production)
        if self.environment == "production":
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                "img-src 'self' data: blob:; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            # HSTS for HTTPS deployments
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        else:
            # Development: Allow inline scripts/styles and external CDNs
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob:;"
            )

        return response
